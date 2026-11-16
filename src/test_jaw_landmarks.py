import os
from sleep_apnea_screener import analyze_jaw_profile

def run_landmark_test():
    print("================ RUNNING JAW LANDMARK STANDALONE TEST ================")
    
    # Path to the generated face profile image
    image_path = "/Users/divyanshsrivastava/.gemini/antigravity/brain/4a89a66b-af97-4da8-ad64-f6fba822794a/face_profile_1782031378664.png"
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Test image not found at {image_path}")
        return
        
    print(f"Analyzing jaw profile on image: {image_path}")
    result = analyze_jaw_profile(image_path)
    
    print("\nExtraction Result:")
    for key, value in result.items():
        print(f"  - {key}: {value}")
        
    assert result["status"] == "success", "Landmark extraction should be successful"
    print("\n✅ Jaw landmark extraction test passed successfully!")

if __name__ == "__main__":
    run_landmark_test()
