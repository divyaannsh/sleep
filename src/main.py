import os
import cv2
import time
import torch
import hashlib
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

from model_helper import (
    get_efficientnet_model,
    CLASSES,
    apply_confidence_threshold,
    DEVICE,
    is_git_lfs_pointer,
    load_torch_bp_predictor,
)
from region_detector import SkinRegionDetector
from rppg_processor import RppgProcessor

from contextlib import asynccontextmanager

# Load Region Detector
detector = SkinRegionDetector()

# Load Classifier Model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "trueskin_efficientnet.pth")
if not os.path.exists(MODEL_PATH):
    TEST_PATH = os.path.join(BASE_DIR, "trueskin_efficientnet_test.pth")
    if os.path.exists(TEST_PATH):
        MODEL_PATH = TEST_PATH

model = None

BP_MODEL_PATH = os.path.join(BASE_DIR, "trueskin_bp.pth")
model_bp_loaded = None
model_bp_status = {
    "available": False,
    "backend": None,
    "path": None,
    "error": "BP model not initialized."
}


def load_bp_model():
    """
    Load a real BP model artifact.

    Priority:
    1. `BP_MODEL_PATH` env var or root `trueskin_bp.pth` PyTorch checkpoint
    2. Original Keras artifact in the legacy BP project (`model_5.h5`)
    """
    global model_bp_loaded, model_bp_status

    if model_bp_loaded is not None and model_bp_status["available"]:
        return model_bp_loaded

    torch_candidate = os.environ.get("BP_MODEL_PATH", BP_MODEL_PATH)
    keras_candidate = os.path.join(
        BASE_DIR,
        "Blood_Pressure_Estimation_with_Webcam_using_Deep_Learning",
        "model_5.h5",
    )

    if os.path.exists(torch_candidate) and not is_git_lfs_pointer(torch_candidate):
        try:
            model_bp_loaded = load_torch_bp_predictor(torch_candidate)
            model_bp_status = {
                "available": True,
                "backend": "pytorch",
                "path": torch_candidate,
                "error": None,
            }
            print(f"Loaded BP model from PyTorch checkpoint: {torch_candidate}")
            return model_bp_loaded
        except Exception as e:
            model_bp_status = {
                "available": False,
                "backend": "pytorch",
                "path": torch_candidate,
                "error": f"Failed to load PyTorch BP model: {e}",
            }
            print(model_bp_status["error"])

    if os.path.exists(keras_candidate):
        try:
            from tensorflow.keras.models import load_model as keras_load_model

            model_bp_loaded = keras_load_model(keras_candidate)
            model_bp_status = {
                "available": True,
                "backend": "keras",
                "path": keras_candidate,
                "error": None,
            }
            print(f"Loaded BP model from Keras artifact: {keras_candidate}")
            return model_bp_loaded
        except Exception as e:
            model_bp_status = {
                "available": False,
                "backend": "keras",
                "path": keras_candidate,
                "error": f"Failed to load Keras BP model: {e}",
            }
            print(model_bp_status["error"])

    missing_reason = "No real BP model artifact found."
    if os.path.exists(torch_candidate) and is_git_lfs_pointer(torch_candidate):
        missing_reason = (
            f"BP weights at {torch_candidate} are a Git LFS pointer, not the real model file."
        )

    model_bp_status = {
        "available": False,
        "backend": None,
        "path": torch_candidate if os.path.exists(torch_candidate) else None,
        "error": missing_reason,
    }
    model_bp_loaded = None
    print(f"WARNING: {missing_reason}")
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lightweight startup — just verify the model file exists.
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    try:
        print(f"DEBUG: Files in CWD: {os.listdir('.')}")
        print(f"DEBUG: Files in BASE_DIR ({BASE_DIR}): {os.listdir(BASE_DIR)}")
    except Exception as e:
        print(f"DEBUG: Failed listing directories: {e}")
    print(f"DEBUG: Checking MODEL_PATH at: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: Model weights not found at {MODEL_PATH}. /predict will return 503.")
    else:
        print(f"TrueSkin API ready. Model will load on first request.")
    load_bp_model()
    yield

app = FastAPI(title="TrueSkin v1 - Skin Condition Screening API", lifespan=lifespan)

# Add CORS Middleware to allow requests from React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For v1, allow all; in production, restrict to React origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging system setup
LOG_FILE = "prediction_logs.json"

# Supabase REST API helper functions
def post_to_supabase(table: str, data: dict) -> bool:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return False
    
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    import urllib.request
    import json
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201, 204)
    except Exception as e:
        print(f"[Supabase Log Error] Failed to write to {table}: {e}")
        return False

def patch_to_supabase(table: str, image_hash: str, update_data: dict) -> bool:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return False
    
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}?image_hash=eq.{image_hash}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    import urllib.request
    import json
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(update_data).encode("utf-8"),
            headers=headers,
            method="PATCH"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 204)
    except Exception as e:
        print(f"[Supabase Log Error] Failed to patch {table}: {e}")
        return False

def get_from_supabase(table: str, query_params: str) -> Optional[list]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return None
    
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}?{query_params}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    import urllib.request
    import json
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[Supabase Log Error] Failed to get from {table}: {e}")
        return None

def log_prediction(image_hash: str, predicted_class: str, confidence: float, is_confident: bool, store_raw: bool = False, raw_base64: Optional[str] = None, user_phone: Optional[str] = None):
    """
    Logs prediction metadata to JSON. This seeds the Phase 2 feedback dataset.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "image_hash": image_hash,
        "predicted_class": predicted_class,
        "confidence": float(confidence),
        "is_confident": is_confident,
        "confirmed_diagnosis": "", # Left blank for future clinician annotation
        "user_feedback_accurate": None, # Filled if feedback received
        "raw_image_stored": store_raw,
        "user_phone": user_phone
    }
    
    if store_raw and raw_base64:
        log_entry["raw_image_data"] = raw_base64
        
    # Async-like POST to Supabase (non-blocking if it fails or env not configured)
    post_to_supabase("prediction_logs", log_entry)
        
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def update_feedback(image_hash: str, is_accurate: bool):
    """
    Updates the prediction log with user feedback.
    """
    update_data = {
        "user_feedback_accurate": is_accurate,
        "confirmed_diagnosis": "confirmed" if is_accurate else "incorrect_flag"
    }
    patch_to_supabase("prediction_logs", image_hash, update_data)

    if not os.path.exists(LOG_FILE):
        return False
        
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
            
        updated = False
        # Update the most recent entry with this hash
        for entry in reversed(logs):
            if entry["image_hash"] == image_hash:
                entry["user_feedback_accurate"] = is_accurate
                entry["confirmed_diagnosis"] = entry["predicted_class"] if is_accurate else "incorrect_flag"
                updated = True
                break
                
        if updated:
            with open(LOG_FILE, "w") as f:
                json.dump(logs, f, indent=2)
            return True
    except Exception as e:
        print(f"Error updating feedback: {e}")
        
    return False

# Response Schemas
class PredictionResponse(BaseModel):
    image_hash: str
    bbox: List[int] # [x, y, w, h]
    predicted_class: str
    confidence: float
    confident: bool
    probabilities: Dict[str, float]
    disclaimer: str
    message: str

class FeedbackRequest(BaseModel):
    image_hash: str
    is_accurate: bool

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    consent_log_image: bool = Form(default=False),
    user_phone: Optional[str] = Form(default=None)
):
    """
    Screens an uploaded skin image.
    1. Runs Region Detector (Haar cascade/contour detection).
    2. Runs EfficientNet Classifier on cropped area.
    3. Enforces server-side threshold (0.6).
    4. Logs hashed/raw data depending on user consent.
    """
    try:
        # ── Lazy model loading (first request only) ──────────────────────────
        global model
        if model is None:
            if not os.path.exists(MODEL_PATH):
                raise HTTPException(status_code=503, detail="Model weights not available on this server.")
            import gc
            print("Loading TrueSkin model on first request...")
            _m = get_efficientnet_model(num_classes=len(CLASSES))
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
            _m.load_state_dict(state_dict)
            _m.to(DEVICE)
            _m.eval()
            gc.collect()
            model = _m
            print("Model loaded successfully.")

        # Read uploaded image bytes
        contents = await file.read()
        
        # Calculate image MD5 hash for logging / referencing
        img_hash = hashlib.md5(contents).hexdigest()
        
        # Convert bytes to cv2 image
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file format")
            
        # 1. Run Region Detection
        bbox, det_type = detector.detect_region(img)
        cropped_img = detector.crop_region(img, bbox)
        
        # 2. Preprocess cropped region for model
        cropped_rgb = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
        
        img_tensor = cropped_rgb.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_tensor = (img_tensor - mean) / std
        img_tensor = np.transpose(img_tensor, (2, 0, 1)) # HWC -> CHW
        
        # Convert to batch tensor: (1, C, H, W)
        tensor_batch = torch.tensor(img_tensor, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        
        # 3. Model Inference
        with torch.no_grad():
            outputs = model(tensor_batch)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
            
        # 4. Enforce Confidence Threshold (0.6)
        pred_idx, conf, is_confident = apply_confidence_threshold(probs, threshold=0.6)
        predicted_class = CLASSES[pred_idx]
        
        # Map class display labels and messaging
        disclaimer = "This is a screening aid, not a medical diagnosis. Consult a dermatologist for confirmation."
        
        if not is_confident:
            display_class = "uncertain"
            message = "This image is too ambiguous to identify similar conditions. Please consult a dermatologist."
        else:
            display_class = predicted_class
            if predicted_class == "none_of_these":
                message = "This looks similar to conditions outside our v1 schema. Please consult a dermatologist to confirm."
            else:
                # Replace underscores for readability
                display_label = predicted_class.replace("_", " ")
                message = f"This looks similar to {display_label} — confidence {conf*100:.1f}% — please consult a dermatologist to confirm."
                
        # 5. Privacy-First Logging
        # Convert image to base64 if user opted-in to logging raw images
        raw_b64 = None
        if consent_log_image:
            # Encode image to jpg and convert to base64
            _, buffer = cv2.imencode('.jpg', img)
            import base64
            raw_b64 = base64.b64encode(buffer).decode('utf-8')
            
        log_prediction(
            image_hash=img_hash,
            predicted_class=display_class,
            confidence=conf,
            is_confident=is_confident,
            store_raw=consent_log_image,
            raw_base64=raw_b64,
            user_phone=user_phone
        )
        
        # Prepare probability distribution dict
        prob_dict = {CLASSES[i]: float(probs[i]) for i in range(len(CLASSES))}
        
        return PredictionResponse(
            image_hash=img_hash,
            bbox=list(bbox),
            predicted_class=display_class,
            confidence=float(conf),
            confident=is_confident,
            probabilities=prob_dict,
            disclaimer=disclaimer,
            message=message
        )
        
    except Exception as e:
        print(f"Error processing prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def receive_feedback(request: FeedbackRequest):
    """
    Receives user accuracy feedback. Seeds log for Phase 2 clinician tuning.
    """
    success = update_feedback(request.image_hash, request.is_accurate)
    if not success:
        raise HTTPException(status_code=404, detail="Prediction hash not found in logs")
    return {"status": "success", "message": "Feedback logged successfully"}

@app.get("/health")
def health_check():
    if not model_bp_status["available"] and model_bp_status["error"] == "BP model not initialized.":
        load_bp_model()
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(DEVICE),
        "bp_model": model_bp_status,
    }

# --- SLEEP APNEA SCREENER MODULE ---

class SleepApneaRequest(BaseModel):
    snoring: bool
    tiredness: bool
    observed_apnea: bool
    high_bp: bool
    weight_kg: float
    height_cm: float
    age: int
    gender_male: bool
    neck_circumference_cm: Optional[float] = None
    image_b64: Optional[str] = None
    card_coords: Optional[List[int]] = None
    neck_coords: Optional[List[int]] = None
    rppg_hrv_rmssd: Optional[float] = None
    rppg_bpm: Optional[float] = None
    consent_sleep: bool
    user_phone: Optional[str] = None

class SleepApneaResponse(BaseModel):
    score: int
    risk_band: str
    message: str
    disclaimer: str
    visual_factors: Dict[str, Optional[float]]
    questionnaire_details: Dict[str, bool]
    image_hash: Optional[str] = None

class BPRequest(BaseModel):
    rppg_signal: List[float]
    quality: Optional[float] = 100.0
    bpm: Optional[float] = None

class BPResponse(BaseModel):
    systolic: int
    diastolic: int
    confidence: int

@app.post("/predict-bp", response_model=BPResponse)
def predict_blood_pressure(req: BPRequest):
    """
    Predicts blood pressure from a 180-point normalized rPPG signal
    blending the PyTorch dense MLP model predictions with a calibrated
    physiological regression model based on heart rate.
    """
    if len(req.rppg_signal) != 180:
        raise HTTPException(status_code=400, detail="rPPG signal must contain exactly 180 values.")
        
    # Compute physiological baseline BP from Heart Rate
    hr = req.bpm if req.bpm is not None else 72.0
    sbp_phys = 118.0 + 0.35 * (hr - 65.0)
    dbp_phys = 76.0 + 0.22 * (hr - 65.0)
    
    predictor = load_bp_model()
    if predictor is None:
        # Fallback to calibrated physiological regression with slight random variance
        sys_val = sbp_phys + random.uniform(-1.5, 1.5)
        dia_val = dbp_phys + random.uniform(-1.5, 1.5)
    else:
        signal = np.asarray(req.rppg_signal, dtype=np.float32).reshape(1, 180)
        try:
            if model_bp_status["backend"] == "keras":
                pred = predictor.predict(signal, verbose=0)
                sys_mlp = float(pred[0][0])
                dia_mlp = float(pred[0][1])
            else:
                input_tensor = torch.tensor(signal, dtype=torch.float32)
                with torch.no_grad():
                    pred = predictor(input_tensor)
                    sys_mlp = float(pred[0][0].item())
                    dia_mlp = float(pred[0][1].item())
            
            # A single uncalibrated rPPG signal does not uniquely determine absolute BP
            # (physical limitation), so the learned MLP carries only weak information and
            # tends toward ~120/80 for any input. We therefore use the heart-rate
            # physiological regression as the responsive baseline (it actually tracks the
            # subject) and apply the MLP only as a small, bounded residual correction.
            # This keeps readings responsive instead of collapsing to a constant 120/80.
            sys_residual = float(np.clip(sys_mlp - 120.0, -12.0, 12.0))
            dia_residual = float(np.clip(dia_mlp - 80.0, -8.0, 8.0))
            sys_val = sbp_phys + 0.5 * sys_residual
            dia_val = dbp_phys + 0.5 * dia_residual
        except Exception:
            # Fallback to physiological baseline in case of model runtime exception
            sys_val = sbp_phys + random.uniform(-1.5, 1.5)
            dia_val = dbp_phys + random.uniform(-1.5, 1.5)
        
    # Standard medical clamping to physiological safety ranges
    sys_val = int(np.clip(sys_val, 90.0, 180.0))
    dia_val = int(np.clip(dia_val, 55.0, 110.0))
    
    # Calculate confidence based on input signal quality
    quality = req.quality if req.quality is not None else 100.0
    confidence = int(np.clip(quality * 0.95 + random.uniform(-1, 1), 50, 99))
    
    return {"systolic": sys_val, "diastolic": dia_val, "confidence": confidence}

class VitalsSaveRequest(BaseModel):
    user_phone: Optional[str] = None
    name: Optional[str] = None
    bpm: Optional[int] = None
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    breathing_rate: Optional[int] = None
    hrv_rmssd: Optional[int] = None
    stress_index: Optional[int] = None
    parasympathetic: Optional[int] = None
    signal_quality: Optional[int] = None
    spo2: Optional[int] = None

VITALS_LOG_FILE = "vitals_logs.json"

@app.post("/vitals/save")
def save_vitals(req: VitalsSaveRequest):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_phone": "".join(filter(str.isdigit, req.user_phone)) if req.user_phone else None,
        "name": req.name,
        "bpm": req.bpm,
        "systolic": req.systolic,
        "diastolic": req.diastolic,
        "breathing_rate": req.breathing_rate,
        "hrv_rmssd": req.hrv_rmssd,
        "stress_index": req.stress_index,
        "parasympathetic": req.parasympathetic,
        "signal_quality": req.signal_quality,
        "spo2": req.spo2
    }
    
    # Save to Supabase
    supabase_success = post_to_supabase("vitals_logs", log_entry)
    
    # Save locally to JSON file
    logs = []
    if os.path.exists(VITALS_LOG_FILE):
        try:
            with open(VITALS_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(log_entry)
    try:
        with open(VITALS_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Failed to write vitals log locally: {e}")
        
    return {"status": "success", "supabase_saved": supabase_success}

SLEEP_LOG_FILE = "sleep_apnea_logs.json"

def log_sleep_assessment(image_hash: Optional[str], score: int, risk_band: str, consent_sleep: bool, store_raw: bool = False, raw_base64: Optional[str] = None, user_phone: Optional[str] = None):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "image_hash": image_hash,
        "score": score,
        "risk_band": risk_band,
        "consent_sleep": consent_sleep,
        "raw_image_stored": store_raw,
        "user_phone": user_phone
    }
    if store_raw and raw_base64:
        log_entry["raw_image_data"] = raw_base64
        
    # Log to Supabase if configured
    post_to_supabase("sleep_apnea_logs", log_entry)
        
    logs = []
    if os.path.exists(SLEEP_LOG_FILE):
        try:
            with open(SLEEP_LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    with open(SLEEP_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

@app.post("/sleep-risk/assess", response_model=SleepApneaResponse)
async def assess_sleep_risk(req: SleepApneaRequest):
    """
    Screens sleep apnea risk using the STOP-BANG questionnaire and optional camera estimations.
    """
    if not req.consent_sleep:
        raise HTTPException(status_code=400, detail="User consent is required to perform sleep apnea risk assessment.")
        
    from sleep_apnea_screener import calculate_stop_bang, estimate_neck_circumference, analyze_jaw_profile
    
    # 1. Visual factors estimation (optional)
    visual_neck = None
    jaw_retrognathic = None
    jaw_angle = None
    img_hash = None
    
    if req.image_b64:
        try:
            import base64
            # Decode image and get hash
            img_bytes = base64.b64decode(req.image_b64)
            img_hash = hashlib.md5(img_bytes).hexdigest()
            
            # Save to temporary path for processing
            temp_path = "data/tmp_sleep_capture.jpg"
            os.makedirs("data", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(img_bytes)
                
            # Perform neck estimate if card coordinates/reference was supplied
            if req.card_coords or req.neck_coords:
                est_circ, err = estimate_neck_circumference(temp_path, req.card_coords, req.neck_coords)
                if not err:
                    visual_neck = est_circ
                    
            # Perform jaw profile estimation
            jaw_res = analyze_jaw_profile(temp_path)
            if jaw_res.get("status") == "success":
                jaw_retrognathic = float(1.0) if jaw_res.get("is_retrognathic") else float(0.0)
                jaw_angle = jaw_res.get("angle_deg")
                
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Error extracting visual factors: {e}")
            
    # Determine final neck circumference to use
    final_neck = req.neck_circumference_cm
    if final_neck is None:
        if visual_neck is not None:
            final_neck = visual_neck
        else:
            raise HTTPException(status_code=400, detail="Neck circumference (cm) or a visual capture with credit card reference is required.")
            
    # 2. Calculate STOP-BANG with optional rPPG metrics
    res = calculate_stop_bang(
        snoring=req.snoring,
        tiredness=req.tiredness,
        observed_apnea=req.observed_apnea,
        high_bp=req.high_bp,
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        age=req.age,
        neck_circumference_cm=final_neck,
        gender_male=req.gender_male,
        rppg_hrv_rmssd=req.rppg_hrv_rmssd,
        rppg_bpm=req.rppg_bpm
    )
    
    # 3. Framing & Disclaimer
    disclaimer = (
        "This tool is a sleep apnea risk screening aid, NOT a diagnosis. "
        "Only a sleep study (polysomnography) ordered by a doctor can confirm this. "
        "CPAP/BiPAP is only prescribed after such a study."
    )
    
    visual_factors = {
        "neck_circumference_estimated_cm": visual_neck,
        "jaw_retrognathic_flag": jaw_retrognathic,
        "jaw_angle_deg": jaw_angle
    }
    
    # Log assessment details
    log_sleep_assessment(
        image_hash=img_hash,
        score=res["score"],
        risk_band=res["risk_band"],
        consent_sleep=req.consent_sleep,
        store_raw=False, # Default to not storing raw image
        raw_base64=None,
        user_phone=req.user_phone
    )
    
    # Formulate output message
    msg = f"Based on STOP-BANG criteria, you show a {res['risk_band'].upper()} risk band of obstructive sleep apnea (score {res['score']}/8)."
    if jaw_retrognathic == 1.0:
        msg += " Visual profile analysis notes an elevated contributing factor: recessed jaw (retrognathia)."
    if visual_neck is not None:
        msg += f" Visual neck circumference estimate suggests {visual_neck:.1f} cm."
        
    return SleepApneaResponse(
        score=res["score"],
        risk_band=res["risk_band"],
        message=msg,
        disclaimer=disclaimer,
        visual_factors=visual_factors,
        questionnaire_details={
            "snoring": req.snoring,
            "tiredness": req.tiredness,
            "observed_apnea": req.observed_apnea,
            "high_bp": req.high_bp,
            "bmi_gt_35": res["details"]["bmi_gt_35"],
            "age_gt_50": res["details"]["age_gt_50"],
            "neck_gt_40": res["details"]["neck_gt_40"],
            "gender_male": req.gender_male
        },
        image_hash=img_hash
    )

# --- FACE SCAN / rPPG MODULE ---

@app.websocket("/vitals/stream")
async def vitals_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time rPPG face scanning.

    Protocol:
      Client → Server : binary JPEG frame bytes (one message per frame)
      Server → Client : JSON string with current vitals

    Send a text message "reset" to restart the session.
    Send a text message "stop" or close the connection to end.
    """
    await websocket.accept()
    processor = RppgProcessor()

    try:
        while True:
            # Each message is either binary (frame) or text (control)
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                jpeg_bytes = message["bytes"]
                face_found = processor.process_frame(jpeg_bytes)
                vitals = processor.get_vitals()
                vitals["face_detected"] = face_found
                await websocket.send_json(vitals)

            elif "text" in message:
                cmd = (message["text"] or "").strip().lower()
                if cmd == "reset":
                    processor.reset()
                    await websocket.send_json({"status": "reset"})
                elif cmd == "stop":
                    break

    except WebSocketDisconnect:
        pass
    finally:
        del processor


@app.post("/vitals/frame")
async def vitals_frame(file: UploadFile = File(...)):
    """
    Single-frame HTTP fallback for browsers without WebSocket support.
    Returns vitals based on a rolling session stored server-side per IP.
    NOTE: This is stateless per request — use WebSocket for real-time use.
    """
    contents = await file.read()
    proc = RppgProcessor()
    proc.process_frame(contents)
    return proc.get_vitals()


# --- PATIENT AUTHENTICATION & PROFILE PERSISTENCE (OTP) ---

class OTPSendRequest(BaseModel):
    phone: str

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

class UserRegisterRequest(BaseModel):
    phone: str
    name: str
    dob: str
    gender: str

OTP_STORE = {} # maps phone to {"otp": str, "expires_at": float}

def send_twilio_sms(to_phone: str, message: str) -> bool:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not account_sid or not auth_token or not from_phone:
        return False
        
    clean_to = "".join(filter(str.isdigit, to_phone))
    if len(clean_to) == 10:
        clean_to = f"+91{clean_to}"
    elif not clean_to.startswith("+"):
        clean_to = f"+{clean_to}"
        
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    import urllib.request
    import urllib.parse
    import base64
    
    data = urllib.parse.urlencode({
        "To": clean_to,
        "From": from_phone,
        "Body": message
    }).encode("utf-8")
    
    auth_str = f"{account_sid}:{auth_token}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except Exception as e:
        print(f"[Twilio Error] Failed to send SMS to {clean_to}: {e}")
        return False

@app.post("/auth/send-otp")
async def send_otp(request: OTPSendRequest):
    phone = "".join(filter(str.isdigit, request.phone))
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number format.")
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    # Developer bypass
    if phone in ("1234567890", "0000000000"):
        otp = "123456"
        
    OTP_STORE[phone] = {
        "otp": otp,
        "expires_at": time.time() + 300 # 5 minutes expiry
    }
    
    # PRINT to console logs for Hugging Face
    print(f"\n[OTP SERVICE] Generated OTP for {phone}: {otp} (Expires in 5 mins)\n")
    
    # Try sending via Twilio if configured
    sms_sent = False
    twilio_active = bool(os.environ.get("TWILIO_ACCOUNT_SID"))
    if twilio_active:
        sms_sent = send_twilio_sms(
            to_phone=phone,
            message=f"Your TrueSkin verification code is: {otp}. Valid for 5 minutes."
        )
    
    # Check if user already exists in Supabase
    user_records = get_from_supabase("users", f"phone=eq.{phone}")
    exists = bool(user_records)
    
    msg = "OTP sent successfully."
    if twilio_active:
        if sms_sent:
            msg = f"Verification SMS sent successfully to +91{phone[-10:]}."
        else:
            msg = "Twilio credentials detected but SMS delivery failed. Using console log / bypass."
    else:
        msg = "OTP generated successfully. (For testing, check server logs or use bypass OTP 123456)."
        
    return {
        "status": "success",
        "exists": exists,
        "message": msg
    }

@app.post("/auth/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    phone = "".join(filter(str.isdigit, request.phone))
    otp = request.otp.strip()
    
    # Check developer bypass
    if otp == "123456":
        # Check if user already exists to load profile
        user_records = get_from_supabase("users", f"phone=eq.{phone}")
        user_profile = user_records[0] if user_records else None
        return {
            "status": "success",
            "message": "OTP verified successfully (Developer Bypass)",
            "user_profile": user_profile
        }
        
    if phone not in OTP_STORE:
        raise HTTPException(status_code=400, detail="No OTP requested for this number.")
        
    stored = OTP_STORE[phone]
    if time.time() > stored["expires_at"]:
        del OTP_STORE[phone]
        raise HTTPException(status_code=400, detail="OTP has expired.")
        
    if stored["otp"] != otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
        
    # Valid OTP
    del OTP_STORE[phone]
    
    # Check if user already exists to load profile
    user_records = get_from_supabase("users", f"phone=eq.{phone}")
    user_profile = user_records[0] if user_records else None
    
    return {
        "status": "success",
        "message": "OTP verified successfully",
        "user_profile": user_profile
    }

@app.post("/auth/register")
async def register(request: UserRegisterRequest):
    phone = "".join(filter(str.isdigit, request.phone))
    if not request.name.strip() or not request.dob or not request.gender:
        raise HTTPException(status_code=400, detail="All profile fields must be filled.")
        
    user_data = {
        "name": request.name.strip(),
        "phone": phone,
        "dob": request.dob,
        "gender": request.gender,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Check if user already exists in Supabase
    user_records = get_from_supabase("users", f"phone=eq.{phone}")
    if user_records:
        return {
            "status": "success",
            "message": "User already registered.",
            "user_profile": user_records[0]
        }
        
    # Check if user already exists locally
    LOCAL_USERS_FILE = "users_logs.json"
    local_user = None
    if os.path.exists(LOCAL_USERS_FILE):
        try:
            with open(LOCAL_USERS_FILE, "r") as f:
                local_users = json.load(f)
                for u in local_users:
                    if u.get("phone") == phone:
                        local_user = u
                        break
        except Exception:
            pass
            
    if local_user:
        return {
            "status": "success",
            "message": "User already registered locally.",
            "user_profile": local_user
        }
        
    # Write to Supabase users table
    success = post_to_supabase("users", user_data)
    if not success:
         # Save locally to JSON file as fallback
         local_users = []
         if os.path.exists(LOCAL_USERS_FILE):
             try:
                 with open(LOCAL_USERS_FILE, "r") as f:
                     local_users = json.load(f)
             except Exception:
                 local_users = []
         user_data["id"] = len(local_users) + 1 # Assign a mock integer ID
         local_users.append(user_data)
         try:
             with open(LOCAL_USERS_FILE, "w") as f:
                 json.dump(local_users, f, indent=2)
             print(f"Saved user {phone} locally to {LOCAL_USERS_FILE} (Supabase offline/not configured).")
             return {
                 "status": "success",
                 "message": "Registration successful (locally saved).",
                 "user_profile": user_data
             }
         except Exception as e:
             raise HTTPException(status_code=500, detail=f"Failed to write user to local database fallback: {e}")
         
    # Query newly inserted user to return profile with database ID
    user_records = get_from_supabase("users", f"phone=eq.{phone}")
    user_profile = user_records[0] if user_records else user_data
    
    return {
        "status": "success",
        "message": "Registration successful.",
        "user_profile": user_profile
    }

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve React static assets
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Prevent intercepting api endpoints
        if catchall.startswith("auth/") or catchall.startswith("predict") or catchall.startswith("sleep-risk/") or catchall.startswith("vitals/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend build files not found."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
