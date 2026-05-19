import os
import cv2
import numpy as np
from pathlib import Path
import shutil

# Mapare culori -> clase
COLOR_MAP = {
    (173, 216, 230): 0,  # Light blue - flood
    (255, 0, 0): 1,      # Red - buildings
    (0, 255, 0): 2,      # Green - plants
    (188, 143, 143): 3,  # Sage - people
    (255, 165, 0): 4,    # Orange - vehicles
    (0, 0, 139): 5       # Dark blue - sky
}

CLASS_NAMES = ['flood', 'building', 'plant', 'person', 'vehicle', 'sky']

def rgb_to_class(mask):
    """Converteste mask RGB in clase"""
    class_mask = np.zeros(mask.shape[:2], dtype=np.uint8)
    for color, class_id in COLOR_MAP.items():
        # Toleranta pt culori (~10 in fiecare canal)
        match = np.all(np.abs(mask - color) < 20, axis=-1)
        class_mask[match] = class_id
    return class_mask

def mask_to_polygons(mask, class_id):
    """Extrage poligoane din mask pentru o clasa"""
    binary = (mask == class_id).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    polygons = []
    for contour in contours:
        if len(contour) > 2:  # Min 3 puncte
            polygon = contour.squeeze()
            if len(polygon.shape) == 2:
                polygons.append(polygon)
    return polygons

def convert_dataset(src_images, src_annotations, dst_path):
    """Converteste dataset-ul in format YOLO segmentation"""
    dst_path = Path(dst_path)
    (dst_path / 'images' / 'train').mkdir(parents=True, exist_ok=True)
    (dst_path / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
    
    image_folders = sorted(os.listdir(src_images))
    
    for folder in image_folders:
        img_folder = os.path.join(src_images, folder)
        ann_folder = os.path.join(src_annotations, folder)
        
        if not os.path.isdir(img_folder):
            continue
            
        images = sorted([f for f in os.listdir(img_folder) if f.endswith(('.jpg', '.png'))])
        
        for img_name in images:
            img_path = os.path.join(img_folder, img_name)
            ann_path = os.path.join(ann_folder, img_name)
            
            if not os.path.exists(ann_path):
                continue
                
            # Citeste imaginea si masca
            img = cv2.imread(img_path)
            mask_img = cv2.imread(ann_path)
            
            if img is None or mask_img is None:
                continue
                
            h, w = img.shape[:2]
            
            # Converteste masca in clase
            class_mask = rgb_to_class(mask_img)
            
            # Genereaza YOLO labels
            label_lines = []
            for class_id in range(len(CLASS_NAMES)):
                polygons = mask_to_polygons(class_mask, class_id)
                
                for poly in polygons:
                    if len(poly) < 3:
                        continue
                    # Normalizeaza coordonatele
                    normalized = poly.astype(float)
                    normalized[:, 0] /= w
                    normalized[:, 1] /= h
                    
                    # Format YOLO: class_id x1 y1 x2 y2 ...
                    coords = ' '.join([f'{x:.6f} {y:.6f}' for x, y in normalized])
                    label_lines.append(f'{class_id} {coords}')
            
            # Salveaza
            if label_lines:
                new_name = f"{folder}_{img_name}"
                shutil.copy(img_path, dst_path / 'images' / 'train' / new_name)
                
                label_name = os.path.splitext(new_name)[0] + '.txt'
                with open(dst_path / 'labels' / 'train' / label_name, 'w') as f:
                    f.write('\n'.join(label_lines))
                    
                print(f'Processed: {new_name}')

if __name__ == '__main__':
    base = '/Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/Flood Amateur Video for Semantic Segmentation Dataset/flood_dataset'
    
    convert_dataset(
        src_images=f'{base}/images',
        src_annotations=f'{base}/annotations',
        dst_path='/Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/flood_yolo'
    )
    
    # Creaza data.yaml
    yaml_content = f"""path: /Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/flood_yolo
train: images/train
val: images/train

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    
    with open('/Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/flood_yolo/data.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("\n✅ Dataset conversion complete!")
    print("📁 Location: /Users/nicanormihaila/Desktop/Dizertatie sem 3/Datasets/flood_yolo")
