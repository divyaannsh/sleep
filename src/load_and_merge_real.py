import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

CLASSES = ["acne", "eczema", "psoriasis", "fungal_infection", "rosacea", "none_of_these"]
RAW_DIR = "data/raw"
OUTPUT_DIR = "data/processed"

def get_skin_tone_bucket(scale):
    try:
        val = int(scale)
        if val in [1, 2]:
            return "light"
        elif val in [3, 4]:
            return "medium"
        elif val in [5, 6]:
            return "dark"
    except (ValueError, TypeError):
        pass
    return "unknown"

# DermNet EXACT folder-name to TrueSkin 6-class schema mapping
# These match the real folder names inside data/raw/dermnet/train/ and test/
DERMNET_LABEL_MAP = {
    # acne — "Acne and Rosacea Photos" maps to BOTH acne AND rosacea
    # Handled specially in the loader below
    "acne and rosacea photos": "acne",  # default; rosacea split handled separately
    # eczema
    "eczema photos": "eczema",
    "atopic dermatitis photos": "eczema",
    "poison ivy photos and other contact dermatitis": "eczema",
    # psoriasis — "Psoriasis pictures Lichen Planus and related diseases" contains
    # BOTH psoriasis and lichen planus/sebderm files. Handled by filename keyword
    # matching in the loader below (same approach as Acne and Rosacea Photos).
    "psoriasis pictures lichen planus and related diseases": "psoriasis",  # default; overridden per-file below
    # fungal infections
    "tinea ringworm candidiasis and other fungal infections": "fungal_infection",
    "nail fungus and other nail disease": "fungal_infection",
    # none_of_these (skin cancers and other conditions)
    "actinic keratosis basal cell carcinoma and other malignant lesions": "none_of_these",
    "melanoma skin cancer nevi and moles": "none_of_these",
    "seborrheic keratoses and other benign tumors": "none_of_these",
    "warts molluscum and other viral infections": "none_of_these",
    "vascular tumors": "none_of_these",
    "vasculitis photos": "none_of_these",
    "light diseases and disorders of pigmentation": "none_of_these",
    "lupus and other connective tissue diseases": "none_of_these",
    "urticaria hives": "none_of_these",
    "bullous disease photos": "none_of_these",
    "cellulitis impetigo and other bacterial infections": "none_of_these",
    "exanthems and drug eruptions": "none_of_these",
    "hair loss photos alopecia and other hair diseases": "none_of_these",
    "herpes hpv and other stds photos": "none_of_these",
    "scabies lyme disease and other infestations and bites": "none_of_these",
    "systemic disease": "none_of_these",
}

# Folders that contain MIXED classes — split by subfolder or filename heuristic
# "Acne and Rosacea Photos" contains both; we label by subfolder if present
ACNE_ROSACEA_FOLDER = "acne and rosacea photos"

# "Psoriasis pictures Lichen Planus and related diseases" is a flat mixed folder.
# Filename inspection shows ~695 psoriasis files + ~710 lichen planus/sebderm files.
# We split by filename keyword exactly like the acne/rosacea flat-folder logic.
PSORIASIS_LICHEN_FOLDER = "psoriasis pictures lichen planus and related diseases"

def process_datasets():
    print("================ LOADING REAL RAW DATASETS ================")
    records = []
    
    # 1. Process DermNet (folder-per-class structure, ~19,500 images)
    dermnet_dir = os.path.join(RAW_DIR, "dermnet")
    dermnet_count = 0
    if os.path.exists(dermnet_dir):
        # DermNet extracts into train/ and test/ subdirectories
        search_roots = []
        for sub in ["train", "test", "."]:
            candidate = os.path.join(dermnet_dir, sub)
            if os.path.isdir(candidate):
                search_roots.append(candidate)
        
        for root_dir in search_roots:
            for class_folder in os.listdir(root_dir):
                class_path = os.path.join(root_dir, class_folder)
                if not os.path.isdir(class_path):
                    continue
                
                # Normalize: lowercase (keep spaces, match our key format)
                folder_key = class_folder.lower().strip()

                # Special case: "Psoriasis pictures Lichen Planus and related diseases"
                # is a flat mixed folder. ~50% psoriasis, ~50% lichen planus/sebderm.
                # Split by filename keyword instead of treating the whole folder as one label.
                if folder_key == PSORIASIS_LICHEN_FOLDER:
                    for img_file in sorted(os.listdir(class_path)):
                        if not img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            continue
                        fname_lower = img_file.lower()
                        if "psoriasis" in fname_lower or "psori" in fname_lower:
                            mapped_label = "psoriasis"
                        else:
                            # Lichen planus, sebderm, LSA, acne outliers, etc.
                            mapped_label = "none_of_these"
                        records.append({
                            "image_path": os.path.join(class_path, img_file),
                            "dataset": "dermnet",
                            "raw_label": class_folder,
                            "mapped_label": mapped_label,
                            "skin_tone_raw": None,
                            "skin_tone_bucket": "unknown"
                        })
                        dermnet_count += 1
                    continue

                # Special case: "Acne and Rosacea Photos" contains both classes.
                # Check for sub-folders; if flat, split by filename keyword.
                if folder_key == ACNE_ROSACEA_FOLDER:
                    img_files = [f for f in os.listdir(class_path)
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    # Check if there are named subfolders (Acne / Rosacea)
                    subfolders = [d for d in os.listdir(class_path)
                                  if os.path.isdir(os.path.join(class_path, d))]
                    if subfolders:
                        for sf in subfolders:
                            sf_label = "acne" if "acne" in sf.lower() else "rosacea"
                            sf_path = os.path.join(class_path, sf)
                            for img_file in os.listdir(sf_path):
                                if not img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                                    continue
                                records.append({
                                    "image_path": os.path.join(sf_path, img_file),
                                    "dataset": "dermnet",
                                    "raw_label": f"{class_folder}/{sf}",
                                    "mapped_label": sf_label,
                                    "skin_tone_raw": None,
                                    "skin_tone_bucket": "unknown"
                                })
                                dermnet_count += 1
                    else:
                        # Flat folder: classify by filename keyword instead of
                        # alphabetical-half splitting. DermNet filenames mostly
                        # encode the real condition, but with typos and
                        # abbreviations — keyword list expanded from manual
                        # inspection of actual folder contents.
                        #
                        # Rosacea keywords:
                        #   "rhnophyma" — known DermNet misspelling of rhinophyma
                        #   "rosglab"   — abbreviation for "rosacea glabella"
                        #   "vessel"    — visible facial vessels (rosacea-adjacent)
                        # Acne keywords:
                        #   "comedone"  — blackheads/whiteheads, clinical acne subtype
                        # Catch-all → none_of_these:
                        #   perioraldermatitis, sebderm, hidradenitis, fordyce spots,
                        #   sebaceous-gland close-ups, and anything unrecognised
                        #   (e.g. "Forest-2.jpg") — don't guess, don't mislabel.
                        for img_file in sorted(img_files):
                            fname_lower = img_file.lower()
                            if any(kw in fname_lower for kw in
                                    ["rosacea", "rhinophyma", "rhnophyma",
                                     "rosglab", "vessel"]):
                                mapped_label = "rosacea"
                            elif any(kw in fname_lower for kw in
                                    ["acne", "comedone"]):
                                mapped_label = "acne"
                            else:
                                mapped_label = "none_of_these"
                            records.append({
                                "image_path": os.path.join(class_path, img_file),
                                "dataset": "dermnet",
                                "raw_label": class_folder,
                                "mapped_label": mapped_label,
                                "skin_tone_raw": None,
                                "skin_tone_bucket": "unknown"
                            })
                            dermnet_count += 1
                    continue
                
                # Standard class folder: look up in label map
                mapped_label = DERMNET_LABEL_MAP.get(folder_key, "none_of_these")
                
                for img_file in os.listdir(class_path):
                    if not img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        continue
                    img_path = os.path.join(class_path, img_file)
                    records.append({
                        "image_path": img_path,
                        "dataset": "dermnet",
                        "raw_label": class_folder,
                        "mapped_label": mapped_label,
                        "skin_tone_raw": None,
                        "skin_tone_bucket": "unknown"
                    })
                    dermnet_count += 1
        
        print(f"Loaded {dermnet_count} valid images from DermNet dataset.")
    else:
        print("[WARNING] DermNet dataset not found at data/raw/dermnet.")
        print("         Run: .venv/bin/python3 src/download_datasets.py")

    # 2. Process HAM10000
    # Images are in HAM10000_images_part_1 and HAM10000_images_part_2 (from Kaggle download)
    ham_csv = os.path.join(RAW_DIR, "ham10000", "HAM10000_metadata.csv")
    # Build a fast lookup: image_id -> actual file path across all part folders
    ham_img_lookup = {}
    for part_folder in ["HAM10000_images_part_1", "HAM10000_images_part_2", "images"]:
        part_path = os.path.join(RAW_DIR, "ham10000", part_folder)
        if os.path.exists(part_path):
            for fname in os.listdir(part_path):
                if fname.lower().endswith('.jpg'):
                    img_id = fname.replace('.jpg', '').replace('.JPG', '')
                    ham_img_lookup[img_id] = os.path.join(part_path, fname)
    print(f"  HAM10000 image lookup built: {len(ham_img_lookup)} images found across part folders.")
    
    if os.path.exists(ham_csv):
        df_ham = pd.read_csv(ham_csv)
        ham_count = 0
        for _, row in df_ham.iterrows():
            img_id = row["image_id"]
            img_path = ham_img_lookup.get(img_id)
            
            if img_path and os.path.exists(img_path):
                dx_raw = str(row["dx"]).lower()
                # All HAM10000 map to none_of_these
                mapped_label = "none_of_these"
                
                records.append({
                    "image_path": img_path,
                    "dataset": "ham10000",
                    "raw_label": dx_raw,
                    "mapped_label": mapped_label,
                    "skin_tone_raw": None,
                    "skin_tone_bucket": "unknown" # HAM10000 lacks skin tone
                })
                ham_count += 1
        print(f"Loaded {ham_count} valid images from HAM10000 dataset.")
    else:
        print("[WARNING] HAM10000 dataset metadata not found at data/raw/ham10000/HAM10000_metadata.csv")

    # 3. Process Fitzpatrick17k
    fitz_csv = os.path.join(RAW_DIR, "fitzpatrick17k", "fitzpatrick17k.csv")
    fitz_img_dir = os.path.join(RAW_DIR, "fitzpatrick17k", "images")
    if os.path.exists(fitz_csv):
        df_fitz = pd.read_csv(fitz_csv)
        fitz_count = 0
        for _, row in df_fitz.iterrows():
            img_id = row["md5hash"]
            img_path = os.path.join(fitz_img_dir, f"{img_id}.jpg")
            
            if os.path.exists(img_path):
                label_raw = str(row["label"]).lower()
                
                # Mapping logic
                mapped_label = "none_of_these"
                if "acne" in label_raw:
                    mapped_label = "acne"
                elif "eczema" in label_raw or "atopic dermatitis" in label_raw or "dermatitis" in label_raw:
                    mapped_label = "eczema"
                elif "psoriasis" in label_raw:
                    mapped_label = "psoriasis"
                elif "tinea" in label_raw or "fungal" in label_raw or "candidiasis" in label_raw:
                    mapped_label = "fungal_infection"
                elif "rosacea" in label_raw:
                    mapped_label = "rosacea"
                    
                scale = row["fitzpatrick_scale"]
                skin_tone = get_skin_tone_bucket(scale)
                
                records.append({
                    "image_path": img_path,
                    "dataset": "fitzpatrick17k",
                    "raw_label": label_raw,
                    "mapped_label": mapped_label,
                    "skin_tone_raw": scale,
                    "skin_tone_bucket": skin_tone
                })
                fitz_count += 1
        print(f"Loaded {fitz_count} valid images from Fitzpatrick17k dataset.")
    else:
        print("[WARNING] Fitzpatrick17k metadata not found at data/raw/fitzpatrick17k/fitzpatrick17k.csv")
        print("         Run: .venv/bin/python3 src/download_datasets.py")

    if len(records) == 0:
        print("\n[ERROR] No valid dataset images loaded. Please verify data/raw/ file structure and download images.")
        return
        
    df_unified = pd.DataFrame(records)
    
    # ------------------ CLASS BALANCE & BIASED AUDIT REPORT ------------------
    print("\n================ DATA BALANCE & DISTRIBUTION REPORT ================")
    print(f"Total Combined Unified Samples: {len(df_unified)}")
    
    # Class balance
    class_counts = df_unified["mapped_label"].value_counts()
    print("\nClass Balance:")
    for cls in CLASSES:
        count = class_counts.get(cls, 0)
        pct = (count / len(df_unified)) * 100
        print(f"  - {cls}: {count} samples ({pct:.2f}%)")
        
    thin_classes = [cls for cls in CLASSES if class_counts.get(cls, 0) < 50]
    if thin_classes:
        print(f"\n[WARNING] Thin data coverage (<50 samples) on target conditions: {thin_classes}")
    
    # Contributions by dataset
    print("\nDataset Contributions per Class:")
    contrib = pd.crosstab(df_unified["mapped_label"], df_unified["dataset"])
    print(contrib)
    
    # Skin tone breakdown
    print("\nSkin Tone Bucket Distribution:")
    tone_counts = df_unified["skin_tone_bucket"].value_counts()
    for bucket in ["light", "medium", "dark", "unknown"]:
        count = tone_counts.get(bucket, 0)
        pct = (count / len(df_unified)) * 100
        print(f"  - {bucket.capitalize()}: {count} samples ({pct:.2f}%)")
    print("====================================================================")
    
    # Stratified Train/Test Split
    print("\nCreating stratified train/test split...")
    df_unified["stratify_key"] = df_unified["mapped_label"] + "_" + df_unified["skin_tone_bucket"]
    
    # Clean up single-element keys to avoid train_test_split error
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
    
    # Save processed CSV splits
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    train_path = os.path.join(OUTPUT_DIR, "train_split.csv")
    test_path = os.path.join(OUTPUT_DIR, "test_split.csv")
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"\nStratified splits saved:")
    print(f"  - Train Split: {train_path} ({len(train_df)} samples)")
    print(f"  - Test Split: {test_path} ({len(test_df)} samples)")

if __name__ == "__main__":
    process_datasets()
