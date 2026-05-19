from ultralytics import YOLO

# Incarca YOLOv8 segmentation model
model = YOLO('yolov8n-seg.pt')

# Antrenare
results = model.train(
    data='/Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/flood_yolo/data.yaml',
    epochs=50,
    imgsz=640,
    batch=8,
    name='flood_seg',
    patience=10,
    save=True,
    device='cpu'  # sau 'mps' pt Mac M1/M2
)

print("✅ Training complete!")
print(f"📁 Model saved to: runs/segment/flood_seg/weights/best.pt")
