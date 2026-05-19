from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
from torchvision import models, transforms
from PIL import Image
import io
import base64
from ultralytics import YOLO
import httpx


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


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    results = yolo(image)[0]
    boxes = results.boxes

     # DEBUG: Afișează clasele detectate cu ID-uri
    detected_classes = {}
    class_counts = {}
    for box in boxes:
        cls_id = int(box.cls[0])
        cls_name = results.names[cls_id]
        detected_classes[cls_id] = cls_name
        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

    print("Clase detectate:")
    for cls_name, count in class_counts.items():
        cls_id = [k for k, v in detected_classes.items() if v == cls_name][0]
        print(f"  {cls_name} (ID: {cls_id}): {count}")
    # results = yolo.model.names


    # print(f"Total clase: {len(results)}\n")
    # for class_id, class_name in sorted(results.items()):
    #     print(f"{class_id:3d}: {class_name}")

    # Dimensiuni medii estimate per obiect (în m²)
    area_map = {
        0: 0.7,  # person
        2: 12,  # car
        3: 2,  # motorcycle
        5: 30,  # bus
        7: 25,  # truck
        15: 0.3,  # bird
        16: 0.5,  # cat
        17: 0.8,  # dog
        56: 1.5,  # chair
        57: 2,  # couch
        58: 1,  # potted plant
        60: 2.5,
        90: 5,  #car
        257: 100, #house
        553: 2, #tree
    }

    cars = sum(1 for box in boxes if int(box.cls[0]) in [2, 5, 7])
    people = sum(1 for box in boxes if int(box.cls[0]) == 0)

    estimated_area_m2 = sum(area_map.get(int(box.cls[0]), 1) for box in boxes)

    total_area = 0
    if len(boxes) > 0:
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            total_area += (x2 - x1) * (y2 - y1)
        img_area = image.width * image.height
        area_percent = (total_area / img_area) * 100
    else:
        area_percent = 0

    return {
        "cars": cars,
        "people": people,
        "area_percent": round(area_percent, 2),
        "estimated_area_m2": round(estimated_area_m2, 1),
        "objects_detected": len(boxes),
        "detected_classes": detected_classes,
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


@app.get("/")
def root():
    return {"status": "running", "model": "disaster_detection"}
