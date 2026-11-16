import os
import cv2
import numpy as np
import pandas as pd
import albumentations as A
from sklearn.model_selection import train_test_split
from collections import Counter

# Define target classes
CLASSES = ["acne", "eczema", "psoriasis", "fungal_infection", "rosacea", "none_of_these"]

# Define skin tone buckets based on Fitzpatrick Scale
SKIN_TONE_BUCKETS = {
    "light": [1, 2],
    "medium": [3, 4],
    "dark": [5, 6]
}

def get_skin_tone_bucket(fitzpatrick_val):
    try:
        val = int(fitzpatrick_val)
        if val in SKIN_TONE_BUCKETS["light"]:
            return "light"
        elif val in SKIN_TONE_BUCKETS["medium"]:
            return "medium"
        elif val in SKIN_TONE_BUCKETS["dark"]:
            return "dark"
    except (ValueError, TypeError):
        pass
    return "unknown"

def generate_mock_datasets(base_dir="data", num_samples=300):
    """
    Generates mock datasets with realistic metadata and visual patterns to represent
    HAM10000, DDI, and Fitzpatrick17k when the real datasets are not present.
    """
    print("Generating simulated datasets...")
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Fitzpatrick17k Mock
    fitz_dir = os.path.join(base_dir, "fitzpatrick17k")
    fitz_img_dir = os.path.join(fitz_dir, "images")
    os.makedirs(fitz_img_dir, exist_ok=True)
    
    # Labels in Fitzpatrick17k we want to map
    fitz_labels = [
        "acne vulgaris", "eczema", "psoriasis", 
        "tinea corporis", "rosacea", 
        "basal cell carcinoma", "seborrheic keratosis" # maps to none_of_these
    ]
    
    fitz_data = []
    for i in range(num_samples // 3):
        img_id = f"fitz_{i:04d}"
        label = np.random.choice(fitz_labels)
        scale = np.random.randint(1, 7) # Fitzpatrick scale 1-6
        img_path = os.path.join(fitz_img_dir, f"{img_id}.jpg")
        
        # Create image
        img = create_synthetic_image(label, scale)
        cv2.imwrite(img_path, img)
        
        fitz_data.append({
            "md5hash": img_id,
            "label": label,
            "fitzpatrick_scale": scale,
            "three_partition_label": "non-neoplastic" if label not in ["basal cell carcinoma"] else "malignant"
        })
    pd.DataFrame(fitz_data).to_csv(os.path.join(fitz_dir, "fitzpatrick17k.csv"), index=False)

    # 2. HAM10000 Mock
    ham_dir = os.path.join(base_dir, "HAM10000")
    ham_img_dir = os.path.join(ham_dir, "images")
    os.makedirs(ham_img_dir, exist_ok=True)
    
    ham_dxs = ["nv", "mel", "bcc", "bkl", "akiec", "vasc", "df"]
    ham_data = []
    for i in range(num_samples // 3):
        img_id = f"ISIC_{i:07d}"
        dx = np.random.choice(ham_dxs)
        # HAM10000 is mostly light to medium skins, but let's randomly assign 1-4 for simulation
        scale = np.random.randint(1, 5)
        img_path = os.path.join(ham_img_dir, f"{img_id}.jpg")
        
        img = create_synthetic_image("none_of_these", scale)
        cv2.imwrite(img_path, img)
        
        ham_data.append({
            "lesion_id": f"HAM_{i:07d}",
            "image_id": img_id,
            "dx": dx,
            "dx_type": "histo",
            "age": np.random.randint(18, 80),
            "sex": np.random.choice(["male", "female"]),
            "localization": "back"
        })
    pd.DataFrame(ham_data).to_csv(os.path.join(ham_dir, "HAM10000_metadata.csv"), index=False)

    # 3. DDI Mock
    ddi_dir = os.path.join(base_dir, "ddi")
    ddi_img_dir = os.path.join(ddi_dir, "images")
    os.makedirs(ddi_img_dir, exist_ok=True)
    
    ddi_labels = ["melanoma", "nevus", "seborrheic keratosis"]
    ddi_data = []
    for i in range(num_samples // 3):
        img_id = f"ddi_{i:04d}"
        label = np.random.choice(ddi_labels)
        # DDI is stratified into F1-2 and F5-6
        scale = np.random.choice([1, 2, 5, 6])
        img_path = os.path.join(ddi_img_dir, f"{img_id}.png")
        
        img = create_synthetic_image("none_of_these", scale)
        cv2.imwrite(img_path, img)
        
        ddi_data.append({
            "image_id": img_id,
            "label": label,
            "skin_tone": 12 if scale in [1, 2] else 56
        })
    pd.DataFrame(ddi_data).to_csv(os.path.join(ddi_dir, "ddi_metadata.csv"), index=False)
    print("Mock datasets generated successfully.")

def create_synthetic_image(label, scale):
    """
    Creates a simulated skin image based on skin-tone scale and skin condition label.
    """
    # Define skin tone base colors (BGR)
    if scale in [1, 2]:
        # Light: soft pinkish/beige
        bg_color = [190, 220, 245]
    elif scale in [3, 4]:
        # Medium: olive/golden brown
        bg_color = [110, 160, 210]
    else:
        # Dark: deep brown
        bg_color = [30, 55, 90]
        
    # Start with base skin tone background (224x224)
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    img[:, :] = bg_color
    
    # Add subtle skin texture noise
    noise = np.random.normal(0, 3, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    label_lower = label.lower()
    
    # Draw characteristic skin lesions (simulated)
    center = (112, 112)
    if "acne" in label_lower:
        # Acne: multiple small red spots with yellow centers
        for _ in range(np.random.randint(5, 12)):
            cx = np.random.randint(60, 160)
            cy = np.random.randint(60, 160)
            r = np.random.randint(3, 7)
            # Red halo
            cv2.circle(img, (cx, cy), r, (40, 40, 200), -1)
            # Yellow pus center
            cv2.circle(img, (cx, cy), max(1, r - 2), (150, 240, 240), -1)
            
    elif "eczema" in label_lower or "dermatitis" in label_lower:
        # Eczema: red patches with dry/irregular borders
        for _ in range(np.random.randint(2, 5)):
            cx = np.random.randint(80, 140)
            cy = np.random.randint(80, 140)
            # Draw fuzzy irregular spot
            mask = np.zeros((224, 224), dtype=np.uint8)
            cv2.circle(mask, (cx, cy), np.random.randint(15, 30), 255, -1)
            # Blur mask to make border irregular
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
            # Apply red color overlay where mask is active
            img[mask > 50] = np.clip(img[mask > 50].astype(np.int16) + [-20, -20, 60], 0, 255).astype(np.uint8)
            
    elif "psoriasis" in label_lower:
        # Psoriasis: pinkish patches with silvery-white flakes
        cx, cy = center
        r = np.random.randint(25, 45)
        # Pink base
        mask = np.zeros((224, 224), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)
        mask = cv2.GaussianBlur(mask, (11, 11), 0)
        img[mask > 50] = np.clip(img[mask > 50].astype(np.int16) + [-10, -30, 80], 0, 255).astype(np.uint8)
        # Silver flakes overlay
        for _ in range(np.random.randint(20, 40)):
            fx = np.random.randint(cx - r + 5, cx + r - 5)
            fy = np.random.randint(cy - r + 5, cy + r - 5)
            # Silvery flake (light gray/white)
            cv2.circle(img, (fx, fy), np.random.randint(1, 4), (220, 220, 220), -1)
            
    elif "tinea" in label_lower or "fungal" in label_lower:
        # Fungal (Tinea / Ringworm): circular red ring with clearer center
        cx, cy = center
        r = np.random.randint(30, 50)
        # Red ring
        cv2.circle(img, (cx, cy), r, (50, 50, 180), np.random.randint(3, 8))
        # Add some slight red scales along the ring
        for angle in range(0, 360, 15):
            rad = np.deg2rad(angle)
            rx = int(cx + r * np.cos(rad) + np.random.randint(-4, 4))
            ry = int(cy + r * np.sin(rad) + np.random.randint(-4, 4))
            cv2.circle(img, (rx, ry), np.random.randint(2, 5), (60, 60, 190), -1)
            
    elif "rosacea" in label_lower:
        # Rosacea: flushing center with tiny red vessels
        cx, cy = center
        # Large soft reddish center
        mask = np.zeros((224, 224), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), np.random.randint(40, 60), 255, -1)
        mask = cv2.GaussianBlur(mask, (25, 25), 0)
        img[mask > 50] = np.clip(img[mask > 50].astype(np.int16) + [-30, -30, 70], 0, 255).astype(np.uint8)
        # Red capillaries
        for _ in range(np.random.randint(4, 8)):
            sx = np.random.randint(cx - 20, cx + 20)
            sy = np.random.randint(cy - 20, cy + 20)
            ex = sx + np.random.randint(-15, 15)
            ey = sy + np.random.randint(-15, 15)
            cv2.line(img, (sx, sy), (ex, ey), (40, 40, 190), 1)
            
    else:
        # Unclear / None of these: either clean skin, or a dark benign/malignant lesion (e.g. nevus, melanoma)
        if np.random.rand() > 0.5:
            # Nevus: brown circular spot
            cx = np.random.randint(80, 140)
            cy = np.random.randint(80, 140)
            r = np.random.randint(5, 15)
            cv2.circle(img, (cx, cy), r, (15, 30, 50), -1) # Dark brown spot
        else:
            # Melanoma: irregular dark spot
            cx = np.random.randint(80, 140)
            cy = np.random.randint(80, 140)
            # Irregular contour drawing
            points = []
            for angle in range(0, 360, 45):
                rad = np.deg2rad(angle)
                r = np.random.randint(10, 22)
                px = int(cx + r * np.cos(rad))
                py = int(cy + r * np.sin(rad))
                points.append([px, py])
            pts = np.array(points, dtype=np.int32)
            cv2.fillPoly(img, [pts], (10, 25, 45))
            
    # Add a bounding box annotator boundary for testing region detectors (optional, we can compute it on the fly)
    return img

def load_unified_dataset(base_dir="data"):
    """
    Loads HAM10000, DDI, and Fitzpatrick17k, applies mapping, and returns a unified DataFrame.
    If datasets are not present, it generates simulated ones.
    """
    fitz_csv = os.path.join(base_dir, "fitzpatrick17k", "fitzpatrick17k.csv")
    ham_csv = os.path.join(base_dir, "HAM10000", "HAM10000_metadata.csv")
    ddi_csv = os.path.join(base_dir, "ddi", "ddi_metadata.csv")
    
    if not (os.path.exists(fitz_csv) and os.path.exists(ham_csv) and os.path.exists(ddi_csv)):
        print("One or more datasets missing. Generating mock datasets...")
        generate_mock_datasets(base_dir)
        
    records = []
    
    # 1. Load Fitzpatrick17k
    df_fitz = pd.read_csv(fitz_csv)
    for _, row in df_fitz.iterrows():
        label_raw = str(row["label"]).lower()
        
        # Map label
        mapped_label = "none_of_these"
        if "acne" in label_raw:
            mapped_label = "acne"
        elif "eczema" in label_raw or "atopic dermatitis" in label_raw or "dermatitis" in label_raw:
            mapped_label = "eczema"
        elif "psoriasis" in label_raw:
            mapped_label = "psoriasis"
        elif "tinea" in label_raw or "fungal" in label_raw:
            mapped_label = "fungal_infection"
        elif "rosacea" in label_raw:
            mapped_label = "rosacea"
            
        fitzpatrick_scale = row["fitzpatrick_scale"]
        skin_tone = get_skin_tone_bucket(fitzpatrick_scale)
        
        img_path = os.path.join(base_dir, "fitzpatrick17k", "images", f"{row['md5hash']}.jpg")
        
        records.append({
            "image_path": img_path,
            "dataset": "fitzpatrick17k",
            "raw_label": label_raw,
            "mapped_label": mapped_label,
            "skin_tone_raw": fitzpatrick_scale,
            "skin_tone_bucket": skin_tone
        })
        
    # 2. Load HAM10000
    df_ham = pd.read_csv(ham_csv)
    for _, row in df_ham.iterrows():
        dx_raw = str(row["dx"]).lower()
        # All HAM10000 DX map to none_of_these
        mapped_label = "none_of_these"
        
        # HAM10000 lacks skin tone data, default to unknown
        skin_tone = "unknown"
        img_path = os.path.join(base_dir, "HAM10000", "images", f"{row['image_id']}.jpg")
        
        records.append({
            "image_path": img_path,
            "dataset": "HAM10000",
            "raw_label": dx_raw,
            "mapped_label": mapped_label,
            "skin_tone_raw": None,
            "skin_tone_bucket": skin_tone
        })
        
    # 3. Load DDI
    df_ddi = pd.read_csv(ddi_csv)
    for _, row in df_ddi.iterrows():
        label_raw = str(row["label"]).lower()
        # DDI is melanoma, nevus, seborrheic keratosis -> none_of_these
        mapped_label = "none_of_these"
        
        # DDI skin tone is 12 (F1-F2 -> light) or 56 (F5-F6 -> dark)
        skin_tone_raw = row["skin_tone"]
        if skin_tone_raw == 12:
            skin_tone = "light"
        elif skin_tone_raw == 56:
            skin_tone = "dark"
        else:
            skin_tone = "unknown"
            
        img_path = os.path.join(base_dir, "ddi", "images", f"{row['image_id']}.png")
        
        records.append({
            "image_path": img_path,
            "dataset": "ddi",
            "raw_label": label_raw,
            "mapped_label": mapped_label,
            "skin_tone_raw": skin_tone_raw,
            "skin_tone_bucket": skin_tone
        })
        
    df_unified = pd.DataFrame(records)
    return df_unified

def get_data_split_and_report(df_unified):
    """
    Generates class balance and skin tone distribution reports.
    Performs a stratified train/test split BEFORE data augmentation.
    """
    print("\n--- UNIFIED DATASET REPORT ---")
    print(f"Total Unified Samples: {len(df_unified)}")
    
    # Class balance
    class_counts = df_unified["mapped_label"].value_counts()
    print("\nClass Balance:")
    for cls in CLASSES:
        count = class_counts.get(cls, 0)
        pct = (count / len(df_unified)) * 100
        print(f"  - {cls}: {count} samples ({pct:.2f}%)")
        
    thin_classes = [cls for cls in CLASSES if class_counts.get(cls, 0) < 15]
    if thin_classes:
        print(f"\n[WARNING] Thin data coverage (<15 samples) for: {thin_classes}")
    else:
        print("\nAll classes have sufficient data representation for v1.")
        
    # Dataset contributions
    print("\nDataset Contributions per Class:")
    contrib = pd.crosstab(df_unified["mapped_label"], df_unified["dataset"])
    print(contrib)
    
    # Skin tone breakdown
    print("\nSkin Tone Bucket Distribution:")
    tone_counts = df_unified["skin_tone_bucket"].value_counts()
    for bucket, count in tone_counts.items():
        pct = (count / len(df_unified)) * 100
        print(f"  - {bucket}: {count} samples ({pct:.2f}%)")
        
    # Stratified split based on label and skin tone (where possible)
    # We combine mapped_label and skin_tone_bucket to perform stratification
    df_unified["stratify_key"] = df_unified["mapped_label"] + "_" + df_unified["skin_tone_bucket"]
    
    # If any stratify key has size 1, replace it with label only to prevent train_test_split failure
    key_counts = df_unified["stratify_key"].value_counts()
    rare_keys = key_counts[key_counts < 2].index
    if len(rare_keys) > 0:
        df_unified.loc[df_unified["stratify_key"].isin(rare_keys), "stratify_key"] = df_unified["mapped_label"]
        
    train_df, test_df = train_test_split(
        df_unified,
        test_size=0.2,
        stratify=df_unified["stratify_key"],
        random_state=42
    )
    
    print(f"\nStratified Split Done:")
    print(f"  - Train Set Size: {len(train_df)}")
    print(f"  - Test Set Size: {len(test_df)}")
    
    return train_df, test_df

def get_phone_camera_augmentations():
    """
    Builds an augmentation pipeline simulating phone camera conditions:
    brightness/contrast shifts, motion blur, compression artifacts, and white balance shifts.
    """
    return A.Compose([
        # Random brightness and contrast shifts (simulates different lighting)
        A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.25, p=0.7),
        # Color shifts (simulates different phone sensor white balance calibrations)
        A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=20, p=0.6),
        # Motion blur (simulates hand shakes when clicking pictures)
        A.OneOf([
            A.MotionBlur(blur_limit=(3, 7)),
            A.Blur(blur_limit=5),
        ], p=0.4),
        # JPEG compression artifacts (simulates web uploads/compression)
        A.ImageCompression(quality_range=(35, 80), p=0.6),
        # Random resized crop (simulates capturing from different distances/scales)
        A.RandomResizedCrop(size=(224, 224), scale=(0.75, 1.0), ratio=(0.9, 1.1), p=0.5),
        # Final resize to model size
        A.Resize(224, 224)
    ])

def test_pipeline_visualization(sample_image_path, output_dir="artifacts"):
    """
    Saves a side-by-side comparison of a raw skin image and its phone-camera augmented version
    for visual sanity checking.
    """
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(sample_image_path)
    if img is None:
        print(f"Could not load image at {sample_image_path} for visualization.")
        return
        
    augmentor = get_phone_camera_augmentations()
    # albumentations expects RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    augmented = augmentor(image=img_rgb)["image"]
    
    # Convert back to BGR for saving
    augmented_bgr = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)
    img_resized = cv2.resize(img, (224, 224))
    
    comparison = np.hstack((img_resized, augmented_bgr))
    
    # Label the images
    cv2.putText(comparison, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(comparison, "Phone-Augmented", (234, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    out_path = os.path.join(output_dir, "phone_camera_augmentation_comparison.png")
    cv2.imwrite(out_path, comparison)
    print(f"Visual sanity check image saved to {out_path}")
    return out_path

if __name__ == "__main__":
    # If run directly, test and print report
    df = load_unified_dataset()
    train_df, test_df = get_data_split_and_report(df)
    
    # Test augmentation visualization
    sample_img = df.iloc[0]["image_path"]
    test_pipeline_visualization(sample_img)
