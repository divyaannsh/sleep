import os
import cv2
import numpy as np
from sleep_apnea_screener import estimate_neck_circumference

def run_calibration_test():
    print("================ RUNNING NECK CALIBRATION TESTS ================")
    
    # 1. Generate a synthetic test image with a card and a neck
    # Image size: 640x640
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Draw a simulated card (white rectangle) at coordinates: x=50, y=50, w=100, h=63 (aspect ratio ~1.58)
    # This will be used for contour detection test as well
    cv2.rectangle(img, (50, 50), (150, 113), (255, 255, 255), -1) # White filled rectangle

    
    # Draw a simulated neck (green vertical rectangle representing throat width of 120 pixels)
    # from x=200 to x=320
    cv2.rectangle(img, (200, 200), (320, 500), (0, 255, 0), -1) # Green filled rectangle
    
    # Save the synthetic image
    test_img_path = "data/test_calibration.jpg"
    os.makedirs("data", exist_ok=True)
    cv2.imwrite(test_img_path, img)
    print(f"Created synthetic test image at {test_img_path}")
    
    # 2. Test manual coordinate passing:
    # Card width in pixels: 100
    # Neck width in pixels: 120
    # Formula: neck_width_cm = (120 / 100) * 8.56 = 10.272 cm
    # neck_circumference = 10.272 * pi = 32.27 cm
    circ, err = estimate_neck_circumference(
        test_img_path,
        card_coords=[50, 50, 100, 63],
        neck_coords=[200, 320]
    )
    
    print(f"Manual Coordinates Test:")
    print(f"  - Estimated Neck Circumference: {circ} cm")
    print(f"  - Error Status: {err}")
    
    assert circ is not None, "Circumference should not be None"
    assert abs(circ - 32.27) < 0.1, f"Expected ~32.27, got {circ}"
    
    # 3. Test automatic card contour detection:
    circ_auto, err_auto = estimate_neck_circumference(
        test_img_path,
        card_coords=None, # Trigger auto card detection
        neck_coords=[200, 320]
    )
    
    print(f"Automatic Card Detection Test:")
    print(f"  - Estimated Neck Circumference: {circ_auto} cm")
    print(f"  - Error Status: {err_auto}")
    
    assert circ_auto is not None, "Auto-detected card circumference should not be None"
    assert abs(circ_auto - 32.27) < 0.5, f"Expected ~32.27, got {circ_auto}"
    
    # Clean up test image
    if os.path.exists(test_img_path):
        os.remove(test_img_path)
        print(f"Cleaned up {test_img_path}")
        
    print("✅ All neck calibration tests passed successfully!")

if __name__ == "__main__":
    run_calibration_test()
