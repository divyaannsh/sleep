import json
import urllib.request
import urllib.error
import numpy as np

def test_bp_endpoint():
    print("================ RUNNING BLOOD PRESSURE API INTEGRATION TEST ================")
    
    url = "http://127.0.0.1:7860/predict-bp"
    health_url = "http://127.0.0.1:7860/health"

    with urllib.request.urlopen(health_url) as response:
        health = json.loads(response.read().decode("utf-8"))

    bp_model = health.get("bp_model", {})
    if not bp_model.get("available"):
        print(f"[SKIP] BP model unavailable: {bp_model.get('error')}")
        return
    
    # Simulate 180-point normalized rPPG signal (sine wave + noise)
    t = np.linspace(0, 7, 180)
    signal = np.sin(2 * np.pi * 1.2 * t) + np.random.normal(0, 0.1, 180)
    # Z-score normalize
    signal = (signal - np.mean(signal)) / (np.std(signal) + 1e-9)
    
    payload = {
        "rppg_signal": signal.tolist()
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
            assert "systolic" in res_json
            assert "diastolic" in res_json
            assert 90 <= res_json["systolic"] <= 180
            assert 55 <= res_json["diastolic"] <= 110
            
            print("\n✅ Blood Pressure API Integration Test Passed!")
            
    except urllib.error.HTTPError as e:
        print(f"[ERROR] API request failed with status {e.code}: {e.read().decode('utf-8')}")
        raise e
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        raise e

if __name__ == "__main__":
    test_bp_endpoint()
