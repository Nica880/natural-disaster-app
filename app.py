from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
from torchvision import models, transforms
from PIL import Image
import io
import base64
from pathlib import Path
from ultralytics import YOLO
import httpx

from model.fire_pipeline import FirePipeline


app = FastAPI()

# Storage pentru rezultatele file_api
file_api_results = {"data": None}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
checkpoint = torch.load("model/disaster_model.pth", map_location="cpu")
classes = checkpoint["classes"]

model = models.resnet18()
model.fc = torch.nn.Linear(model.fc.in_features, len(classes))
model.load_state_dict(checkpoint["model"])
model.eval()

# yolo = YOLO('yolov8n.pt')
# ...existing code...
yolo = YOLO("yolov8n-oiv7.pt")
yolo_flood = YOLO("runs/segment/flood_seg/weights/best.pt")

# Fire pipeline loads lazily — the trained weights may not exist yet.
try:
    fire_pipeline: FirePipeline | None = FirePipeline()
    print("Fire pipeline loaded.")
except FileNotFoundError as e:
    fire_pipeline = None
    print(f"Fire pipeline unavailable: {e}")

transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

@app.post("/file_api")
async def file_api(file: UploadFile = File(...)):
    print(f"Received file: {file.filename}")
    
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(img_tensor)
        probs = torch.nn.functional.softmax(output, dim=1)[0]
        pred_idx = probs.argmax().item()
    
    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    result = {
        "class": classes[pred_idx],
        "confidence": float(probs[pred_idx]),
        "probabilities": {classes[i]: float(probs[i]) for i in range(len(classes))},
        "image": f"data:image/jpeg;base64,{image_base64}"
    }
    
    file_api_results["data"] = result
        
    return {"status": "success", "detail": "File processed", "result": result}


@app.get("/file_api_results")
async def get_file_api_results():
    return file_api_results["data"] or {"message": "No data yet"}


    # return {
    #     "class": classes[pred_idx],
    #     "confidence": float(probs[pred_idx]),
    #     "probabilities": {classes[i]: float(probs[i]) for i in range(len(classes))},
    # }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(img_tensor)
        probs = torch.nn.functional.softmax(output, dim=1)[0]
        pred_idx = probs.argmax().item()

    return {
        "class": classes[pred_idx],
        "confidence": float(probs[pred_idx]),
        "probabilities": {classes[i]: float(probs[i]) for i in range(len(classes))},
    }


# Open Images V7 class IDs (the model is yolov8n-oiv7.pt) with per-class
# real-world footprint priors in m². Verified against yolo.names — see
# scripts/inspect_oiv7_classes.py if you need to extend this.
OIV7_AREA_PRIORS_M2 = {
    381: 0.7,   # Person
    90:  12,    # Car
    73:  30,    # Bus
    558: 25,    # Truck
    564: 18,    # Van
    342: 2,     # Motorcycle
    42:  1.5,   # Bicycle
    52:  20,    # Boat
    257: 100,   # House
    70:  150,   # Building
    354: 250,   # Office building
    553: 12,    # Tree
    364: 15,    # Palm tree
    530: 6,     # Tent
    6:   25,    # Ambulance
}
OIV7_VEHICLE_IDS = {90, 73, 558, 564, 342, 42, 52, 223, 6}  # cars, bus, truck, van, moto, bike, boat, golf cart, ambulance
OIV7_PERSON_IDS = {381}
OIV7_BUILDING_IDS = {70, 257, 354}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    results = yolo(image)[0]
    boxes = results.boxes

    class_counts: dict[str, int] = {}
    vehicles = people = buildings = 0
    estimated_area_m2 = 0.0
    total_box_area_px = 0.0

    for box in boxes:
        cls_id = int(box.cls[0])
        cls_name = results.names[cls_id]
        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        total_box_area_px += (x2 - x1) * (y2 - y1)

        if cls_id in OIV7_VEHICLE_IDS:
            vehicles += 1
        if cls_id in OIV7_PERSON_IDS:
            people += 1
        if cls_id in OIV7_BUILDING_IDS:
            buildings += 1
        estimated_area_m2 += OIV7_AREA_PRIORS_M2.get(cls_id, 0)

    img_area_px = image.width * image.height
    area_percent = (total_box_area_px / img_area_px) * 100 if img_area_px else 0

    return {
        "vehicles": vehicles,
        "people": people,
        "buildings": buildings,
        "area_percent": round(area_percent, 2),
        "estimated_area_m2": round(estimated_area_m2, 1),
        "objects_detected": len(boxes),
        "class_counts": class_counts,
    }


@app.post("/flood_analysis")
async def flood_analysis(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    results = yolo_flood(image)[0]

    flood_area_percent = 0
    class_counts = {}

    # Verifică dacă există măști și boxes
    if results.masks is not None and results.boxes is not None:
        img_area = image.width * image.height

        # Calculează zona inundată și numără obiectele
        for i, (mask, cls_id) in enumerate(zip(results.masks.data, results.boxes.cls)):
            cls_name = results.names[int(cls_id)]
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            if cls_name == "flood":
                flood_area_percent += (mask.sum() / img_area).item() * 100

    return {
        "flood_area_percent": round(flood_area_percent, 2),
        "flood_area_m2": round(flood_area_percent * 100, 1),  # Estimare: 1% ≈ 100m²
        "buildings": class_counts.get("building", 0),
        "vehicles": class_counts.get("vehicle", 0),
        "people": class_counts.get("person", 0),
        "plants": class_counts.get("plant", 0),
        "total_objects": len(results.boxes) if results.boxes else 0,
    }


@app.post("/fire_analysis")
async def fire_analysis(file: UploadFile = File(...)):
    if fire_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Fire model not loaded. Train it via notebooks/train_fire_yolo.ipynb and place fire.pt in model/.",
        )
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    report = fire_pipeline.analyze(image)
    return report.to_dict()


@app.get("/")
def root():
    return {
        "status": "running",
        "models": {
            "classifier": "resnet18",
            "generic_detector": "yolov8n-oiv7",
            "flood_segmenter": "yolov8n-seg (flood)",
            "fire_detector": "yolov8s (D-Fire)" if fire_pipeline else "not_loaded",
        },
    }
