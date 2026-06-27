import os
import csv
import logging
from glob import glob
from ultralytics import YOLO

# Centralized logging for Computer Vision tasks
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yolo_detection.log"),
        logging.StreamHandler()
    ]
)

def determine_classification(detected_objects):
    """
    Applies business logic mapping arrays to specific strategic buckets:
    - promotional: person + product/container
    - product_display: bottle/container/cup, no person
    - lifestyle: person, no product/container
    - other: neither detected
    """
    # Define common object labels associated with medical, cosmetic, or general products
    product_labels = {'bottle', 'cup', 'bowl', 'vase', 'box', 'can'}
    
    has_person = 'person' in detected_objects
    has_product = any(obj in product_labels for obj in detected_objects)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"

def run_object_detection():
    # 1. Paths configuration matching your directory tree layout
    image_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw/images")) 
    output_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/yolo_detections.csv"))
    
    valid_extensions = ['**/*.jpg', '**/*.jpeg', '**/*.png', '**/*.webp']
    image_paths = []
    for ext in valid_extensions:
        image_paths.extend(glob(os.path.join(image_base_dir, ext), recursive=True))
        
    if not image_paths:
        logging.warning(f"No images found to process in: {image_base_dir}")
        return

    logging.info(f"Discovered {len(image_paths)} images across channel subfolders.")

    try:
        logging.info("Loading lightweight yolov8n.pt model...")
        model = YOLO("yolov8n.pt")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to load YOLO model: {str(e)}")
        return

    # 3. Setup CSV Writer with the explicit category column added
    csv_header = ["image_name", "channel_folder", "detected_objects", "confidence_scores", "primary_object", "image_category"]
    
    try:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)

            # 4. Process Images Iteration Loop
            for img_path in image_paths:
                img_name = os.path.basename(img_path)
                channel_folder = os.path.basename(os.path.dirname(img_path))
                logging.info(f"Processing detection on [{channel_folder}]: {img_name}")

                try:
                    results = model(img_path, verbose=False)
                    
                    detected_objects = []
                    confidence_scores = []
                    
                    for r in results:
                        for box in r.boxes:
                            class_id = int(box.cls[0])
                            label = model.names[class_id]
                            confidence = float(box.conf[0])
                            
                            detected_objects.append(label)
                            confidence_scores.append(f"{confidence:.2f}")

                    # Compute classification category using the business logic rule
                    image_category = determine_classification(detected_objects)
                    
                    primary_object = detected_objects[0] if detected_objects else "none"
                    objects_str = ",".join(detected_objects) if detected_objects else "none"
                    conf_str = ",".join(confidence_scores) if confidence_scores else "0.00"

                    # Commit to local dataset matrix
                    writer.writerow([img_name, channel_folder, objects_str, conf_str, primary_object, image_category])
                    logging.info(f"Saved inference: {img_name} -> Category: {image_category} | Found: [{objects_str}]")

                except Exception as img_err:
                    logging.error(f"Failed processing image {img_name}: {str(img_err)}")
                    continue

        logging.info(f"SUCCESS: Detection matrix fully categorized at {output_csv}")

    except IOError as io_err:
        logging.error(f"File System Write Interruption: {str(io_err)}")

if __name__ == "__main__":
    run_object_detection()