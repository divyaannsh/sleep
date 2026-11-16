import os
import cv2
import numpy as np

class SkinRegionDetector:
    def __init__(self):
        # Load OpenCV Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            print("[WARNING] Haar cascade for face detection could not be loaded.")

    def detect_region(self, image):
        """
        Accepts a BGR image.
        Returns:
            bbox: (x, y, w, h) bounding box of the region of interest.
            detection_type: string indicating "face", "lesion_contour", or "fallback".
        """
        h, w, _ = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 1. Try face detection first
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
        if len(faces) > 0:
            # Return the largest face found
            largest_face = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
            x, y, fw, fh = largest_face
            # Expand bounding box slightly for safety
            pad_x = int(fw * 0.1)
            pad_y = int(fh * 0.1)
            nx = max(0, x - pad_x)
            ny = max(0, y - pad_y)
            nw = min(w - nx, fw + 2 * pad_x)
            nh = min(h - ny, fh + 2 * pad_y)
            return (int(nx), int(ny), int(nw), int(nh)), "face"

        # 2. Try lesion detection using color/contour segmentation
        # Convert to HSV to find non-standard skin tones or lesion colors (reds, dark patches)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Red lesions (like acne, eczema, psoriasis, rosacea, tinea) usually fall in these HSV ranges:
        # Note: HSV red wraps around 0 and 180
        lower_red1 = np.array([0, 40, 40])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 40, 40])
        upper_red2 = np.array([180, 255, 255])
        
        # Dark lesions (like melanoma, nevi)
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([180, 255, 100]) # Low value (brightness)

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)
        
        mask = cv2.bitwise_or(mask_red1, mask_red2)
        mask = cv2.bitwise_or(mask, mask_dark)
        
        # Clean up mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours of the lesion
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            # Filter contours by size to ignore tiny spots/noise
            valid_contours = [c for c in contours if cv2.contourArea(c) > 50]
            if len(valid_contours) > 0:
                # Merge bounding boxes of all valid contours to capture the whole affected region
                x_min, y_min = w, h
                x_max, y_max = 0, 0
                for c in valid_contours:
                    cx, cy, cw, ch = cv2.boundingRect(c)
                    x_min = min(x_min, cx)
                    y_min = min(y_min, cy)
                    x_max = max(x_max, cx + cw)
                    y_max = max(y_max, cy + ch)
                
                # Expand bounding box slightly (20% padding)
                bx = max(0, x_min - int((x_max - x_min) * 0.1))
                by = max(0, y_min - int((y_max - y_min) * 0.1))
                bw = min(w - bx, (x_max - x_min) + int((x_max - x_min) * 0.2))
                bh = min(h - by, (y_max - y_min) + int((y_max - y_min) * 0.2))
                return (int(bx), int(by), int(bw), int(bh)), "lesion_contour"

        # 3. Fallback to center 70% region
        cx, cy = w // 2, h // 2
        bw = int(w * 0.7)
        bh = int(h * 0.7)
        bx = cx - bw // 2
        by = cy - bh // 2
        return (int(bx), int(by), int(bw), int(bh)), "fallback"

    def crop_region(self, image, bbox):
        """
        Crops the region of interest from the image and resizes to 224x224.
        """
        x, y, w, h = bbox
        crop = image[y:y+h, x:x+w]
        if crop.size == 0:
            # If crop is invalid, return original image resized
            return cv2.resize(image, (224, 224))
        return cv2.resize(crop, (224, 224))


