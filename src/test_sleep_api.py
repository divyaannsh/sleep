import base64
import json
import urllib.request
import urllib.error
import os

def test_sleep_apnea_endpoint():
    print("================ RUNNING SLEEP APNEA API INTEGRATION TEST ================")
    
    url = "http://localhost:8000/sleep-risk/assess"
    image_path = "/Users/divyanshsrivastava/.gemini/antigravity/brain/4a89a66b-af97-4da8-ad64-f6fba822794a/face_profile_1782031378664.png"
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Face profile image not found at {image_path}. Skip visual factors API test.")
        return
        
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    payload = {
        "snoring": True,
        "tiredness": True,
        "observed_apnea": False,
        "high_bp": True,
        "weight_kg": 95.0,
        "height_cm": 178.0,
        "age": 52,
        "gender_male": True,
        "neck_circumference_cm": None, # Force estimation via photo!
        "image_b64": img_b64,
        "card_coords": [50, 50, 120, 75], # Simulated card coordinates in pixel space
        "neck_coords": [180, 290],       # Simulated neck boundary in pixel space
        "consent_sleep": True
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            print("\nAPI Response:")
            print(json.dumps(res_json, indent=2))
            
            # Assertions
            assert "score" in res_json
            assert "risk_band" in res_json
            assert "disclaimer" in res_json
            assert "visual_factors" in res_json
            assert res_json["visual_factors"]["neck_circumference_estimated_cm"] is not None
            assert "questionnaire_details" in res_json
            
            print("\n✅ Sleep Apnea API Integration Test Passed!")
            
    except urllib.error.HTTPError as e:
        print(f"[ERROR] API request failed with status {e.code}: {e.read().decode('utf-8')}")
        raise e
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        raise e

if __name__ == "__main__":
    test_sleep_apnea_endpoint()
