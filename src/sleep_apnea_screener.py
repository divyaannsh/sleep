import os
import cv2
import numpy as np
import math
import urllib.request

try:
    import mediapipe as mp
except ImportError:
    mp = None

# Constants
CARD_WIDTH_CM = 8.56  # ISO/IEC 7810 standard credit card width
CARD_HEIGHT_CM = 5.40 # standard height
FACE_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = "src/face_landmarker.task"

def download_model_if_needed():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading MediaPipe Face Landmarker model from {FACE_LANDMARKER_MODEL_URL}...")
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        try:
            urllib.request.urlretrieve(FACE_LANDMARKER_MODEL_URL, MODEL_PATH)
            print("Model downloaded successfully.")
        except Exception as e:
            print(f"Failed to download MediaPipe model task file: {e}")
            raise e

def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100.0
    return weight_kg / (height_m ** 2)

def calculate_stop_bang(snoring, tiredness, observed_apnea, high_bp, weight_kg, height_cm, age, neck_circumference_cm, gender_male, rppg_hrv_rmssd=None, rppg_bpm=None):
    """
    Computes the STOP-BANG score (0 to 8), incorporates rPPG physiological signals (HRV/HR), and returns the risk band.
    """
    bmi = calculate_bmi(weight_kg, height_cm)
    
    # Calculate binary scores
    s_score = 1 if snoring else 0
    t_score = 1 if tiredness else 0
    o_score = 1 if observed_apnea else 0
    p_score = 1 if high_bp else 0
    b_score = 1 if bmi > 35 else 0
    a_score = 1 if age > 50 else 0
    n_score = 1 if neck_circumference_cm > 40 else 0
    g_score = 1 if gender_male else 0
    
    total_score = s_score + t_score + o_score + p_score + b_score + a_score + n_score + g_score
    
    # Analyze physiological signals from rPPG
    physio_warning = False
    physio_notes = []
    
    if rppg_hrv_rmssd is not None:
        # Clinically, sleep apnea leads to chronically reduced vagal tone and depressed HRV (RMSSD < 25 ms)
        if rppg_hrv_rmssd < 25.0:
            physio_warning = True
            physio_notes.append(f"Depressed Heart Rate Variability (RMSSD: {rppg_hrv_rmssd:.1f} ms) indicates autonomic system stress.")
            
    if rppg_bpm is not None:
        # Chronically elevated resting heart rate (> 80 bpm) is frequently observed in sleep apnea patients
        if rppg_bpm > 80.0:
            physio_warning = True
            physio_notes.append(f"Elevated resting heart rate (BPM: {rppg_bpm:.1f}) indicates potential sympathetic dominance.")
            
    # Risk bands and messages
    if total_score <= 2:
        risk_band = "low"
        if physio_warning:
            risk_band = "intermediate"  # Elevate risk due to physiological markers
            message = "Low questionnaire risk, but elevated to Intermediate Risk due to physiological rPPG markers: " + " ".join(physio_notes)
        else:
            message = "Low risk of obstructive sleep apnea."
    elif total_score <= 4:
        risk_band = "intermediate"
        if physio_warning:
            message = "Intermediate risk of obstructive sleep apnea. Supported by physiological markers: " + " ".join(physio_notes)
        else:
            message = "Intermediate risk of obstructive sleep apnea."
    else:
        risk_band = "high"
        if physio_warning:
            message = "High risk of obstructive sleep apnea. Supported by physiological markers: " + " ".join(physio_notes)
        else:
            message = "High risk of obstructive sleep apnea."
        
    return {
        "score": total_score,
        "risk_band": risk_band,
        "message": message,
        "details": {
            "snoring": bool(snoring),
            "tiredness": bool(tiredness),
            "observed_apnea": bool(observed_apnea),
            "high_bp": bool(high_bp),
            "bmi": float(bmi),
            "bmi_gt_35": bool(bmi > 35),
            "age": int(age),
            "age_gt_50": bool(age > 50),
            "neck_circumference_cm": float(neck_circumference_cm),
            "neck_gt_40": bool(neck_circumference_cm > 40),
            "gender_male": bool(gender_male),
            "rppg_hrv_rmssd": float(rppg_hrv_rmssd) if rppg_hrv_rmssd is not None else None,
            "rppg_bpm": float(rppg_bpm) if rppg_bpm is not None else None,
            "physio_notes": physio_notes
        }
    }

def estimate_neck_circumference(image_path, card_coords=None, neck_coords=None):
    """
    Estimates the neck circumference by comparing neck pixel width to a reference card object.
    
    card_coords: list [x, y, w, h] of the reference card in pixels
    neck_coords: list [left_x, right_x] or similar of the neck in pixels
    """
    if not os.path.exists(image_path):
        return None, "Image file not found"
        
    img = cv2.imread(image_path)
    if img is None:
        return None, "Failed to load image"
        
    h, w, _ = img.shape
    
    # 1. Scale calibration (pixels per cm)
    if card_coords is not None:
        # User-supplied card coordinates
        _, _, card_w_px, _ = card_coords
        pixels_per_cm = card_w_px / CARD_WIDTH_CM
    else:
        # Fallback: Search for a card-shaped contour (aspect ratio ~1.58)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_contour_w = None
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:
                x, y, cw, ch = cv2.boundingRect(approx)
                aspect_ratio = float(cw) / ch if ch > 0 else 0
                if 1.4 <= aspect_ratio <= 1.8 and cw > w * 0.08:
                    best_contour_w = cw
                    break
                elif 0.5 <= aspect_ratio <= 0.7 and ch > h * 0.08:
                    best_contour_w = ch
                    break
                    
        if best_contour_w is not None:
            pixels_per_cm = best_contour_w / CARD_WIDTH_CM
        else:
            return None, "Reference object (card) not detected. Please specify card coordinates."
            
    # 2. Neck width extraction
    if neck_coords is not None:
        # User-supplied neck width in pixels
        neck_w_px = abs(neck_coords[1] - neck_coords[0])
    else:
        # Fallback using modern MediaPipe Tasks API
        if mp is None:
            return None, "MediaPipe is not installed. Manual neck coordinates required."
            
        try:
            download_model_if_needed()
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
            options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
            
            with vision.FaceLandmarker.create_from_options(options) as landmarker:
                mp_image = mp.Image.create_from_file(image_path)
                detection_result = landmarker.detect(mp_image)
                
                if not detection_result.face_landmarks:
                    return None, "No face detected for landmark-based neck width estimation"
                    
                landmarks = detection_result.face_landmarks[0]
                pt_left = landmarks[365]
                pt_right = landmarks[136]
                
                lx, ly = int(pt_left.x * w), int(pt_left.y * h)
                rx, ry = int(pt_right.x * w), int(pt_right.y * h)
                
                jaw_w_px = math.sqrt((lx - rx)**2 + (ly - ry)**2)
                neck_w_px = jaw_w_px * 0.92
        except Exception as e:
            return None, f"Landmark neck detection error: {e}"
            
    # 3. Calculate absolute circumference
    neck_w_cm = neck_w_px / pixels_per_cm
    neck_circ_cm = neck_w_cm * math.pi
    
    return float(neck_circ_cm), None

def analyze_jaw_profile(image_path):
    """
    Estimates if the jaw is retrognathic (recessed) from a side profile image.
    Uses modern MediaPipe Tasks API.
    """
    if mp is None:
        return {"status": "skipped", "reason": "MediaPipe is not installed"}
        
    if not os.path.exists(image_path):
        return {"status": "error", "reason": "Image file not found"}
        
    img = cv2.imread(image_path)
    if img is None:
        return {"status": "error", "reason": "Failed to load image"}
        
    h, w, _ = img.shape
    
    try:
        download_model_if_needed()
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(base_options=base_options, num_faces=1)
        
        with vision.FaceLandmarker.create_from_options(options) as landmarker:
            mp_image = mp.Image.create_from_file(image_path)
            detection_result = landmarker.detect(mp_image)
            
            if not detection_result.face_landmarks:
                return {"status": "skipped", "reason": "No face detected in profile image"}
                
            landmarks = detection_result.face_landmarks[0]
            
            # Glabella (forehead center): 9, Subnasale (nose base): 2, Pogonion (chin tip): 199 or 152
            p_forehead = landmarks[9]
            p_nose = landmarks[2]
            p_chin = landmarks[199]
            
            fx, fy = p_forehead.x * w, p_forehead.y * h
            nx, ny = p_nose.x * w, p_nose.y * h
            cx, cy = p_chin.x * w, p_chin.y * h
            
            # 1. Profile angle calculation
            v_forehead = np.array([fx - nx, fy - ny])
            v_chin = np.array([cx - nx, cy - ny])
            
            norm_forehead = v_forehead / np.linalg.norm(v_forehead)
            norm_chin = v_chin / np.linalg.norm(v_chin)
            
            dot_product = np.dot(norm_forehead, norm_chin)
            dot_product = np.clip(dot_product, -1.0, 1.0)
            angle_rad = np.arccos(dot_product)
            angle_deg = np.degrees(angle_rad)
            
            is_retrognathic = angle_deg < 162.0
            
            return {
                "status": "success",
                "angle_deg": float(angle_deg),
                "is_retrognathic": bool(is_retrognathic),
                "explanation": f"Facial profile angle is {angle_deg:.1f} degrees. A lower angle indicates a recessed jaw profile (retrognathia)."
            }
    except Exception as e:
        return {"status": "error", "reason": f"Face Landmarker execution failed: {e}"}
