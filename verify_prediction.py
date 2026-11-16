# verify_prediction.py
# Verification utility to inspect model predictions and cropped ROIs on individual skin images.
#
# Usage:
#   PYTHONPATH=src .venv/bin/python verify_prediction.py path/to/image.jpg

import os
import sys
import cv2
import torch
import numpy as np

# Adjust python path programmatically to import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from model_helper import get_efficientnet_model, CLASSES, apply_confidence_threshold, DEVICE
from region_detector import SkinRegionDetector

MODEL_PATH = "trueskin_efficientnet.pth"

def main():
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=src .venv/bin/python verify_prediction.py <path_to_image>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
        
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model weights '{MODEL_PATH}' not found.")
        sys.exit(1)
        
    print(f"Loading image from {image_path}...")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not decode image.")
        sys.exit(1)
        
    print("Initializing Region Detector...")
    detector = SkinRegionDetector()
    bbox, det_type = detector.detect_region(img)
    print(f"Detected bounding box [x, y, w, h]: {bbox} (Type: {det_type})")
    
    cropped_img = detector.crop_region(img, bbox)
    
    # Save cropped debug image
    os.makedirs("artifacts", exist_ok=True)
    debug_crop_path = "artifacts/debug_cropped.png"
    cv2.imwrite(debug_crop_path, cropped_img)
    print(f"Saved cropped Region of Interest (ROI) to: {debug_crop_path}")
    
    # Preprocess cropped region
    cropped_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
    img_tensor = cropped_rgb.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_tensor = (img_tensor - mean) / std
    img_tensor = np.transpose(img_tensor, (2, 0, 1)) # HWC -> CHW
    tensor_batch = torch.tensor(img_tensor, dtype=torch.float32).unsqueeze(0).to(DEVICE)
    
    print(f"Loading model weights from {MODEL_PATH} on {DEVICE}...")
    model = get_efficientnet_model(num_classes=len(CLASSES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()
    
    print("Running model inference...")
    with torch.no_grad():
        outputs = model(tensor_batch)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
        
    pred_idx, conf, is_confident = apply_confidence_threshold(probs, threshold=0.6)
    predicted_class = CLASSES[pred_idx]
    
    print("\n" + "="*50)
    print("                 MODEL SCREENING REPORT")
    print("="*50)
    print(f"Raw similarity profile:")
    for cls_name, prob in zip(CLASSES, probs):
        print(f"  - {cls_name:<20}: {prob * 100:.2f}%")
    print("-"*50)
    print(f"Top class predicted: {CLASSES[np.argmax(probs)]} ({probs[np.argmax(probs)]*100:.2f}%)")
    print(f"Passes confidence threshold (>= 60.0%): {is_confident}")
    print(f"Routed result: {predicted_class.upper()} (Confidence: {conf*100:.2f}%)")
    print("="*50)

if __name__ == "__main__":
    main()
