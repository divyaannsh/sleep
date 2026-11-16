"""
TrueSkin v1 — Real Dataset Acquisition Script
==============================================

This script sets up the data/raw directory structure and fetches
all available datasets for TrueSkin training.

DATASET SUMMARY:
  1. DermNet          — 19,500 images, 23 skin disease classes (via Kaggle)
  2. HAM10000         — 10,015 images, skin lesion cancer/benign (via Kaggle)
  3. Fitzpatrick 17k  — 16,577 metadata rows, images fetched from the CSV URLs

KAGGLE SETUP (required for DermNet + HAM10000):
  Step 1: Create a Kaggle account at https://www.kaggle.com
  Step 2: Go to Account > API > Create New Token — this downloads kaggle.json
  Step 3: Run these commands in your terminal:
            mkdir -p ~/.kaggle
            cp ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
            chmod 600 ~/.kaggle/kaggle.json
  Step 4: Install the Kaggle CLI:
            .venv/bin/pip install kaggle
  Step 5: Run this script again:
            .venv/bin/python3 src/download_datasets.py
"""

import os
import sys
import zipfile
import urllib.request
import urllib.error
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import subprocess

DATA_RAW_DIR = "data/raw"

def create_dirs():
    os.makedirs(os.path.join(DATA_RAW_DIR, "ham10000", "images"), exist_ok=True)
    os.makedirs(os.path.join(DATA_RAW_DIR, "dermnet"), exist_ok=True)
    os.makedirs(os.path.join(DATA_RAW_DIR, "fitzpatrick17k", "images"), exist_ok=True)
    print(f"Directory structure initialized in {DATA_RAW_DIR}")

def check_kaggle():
    """Check if kaggle CLI is installed and credentials are set up."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "kaggle", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass
    
    # Check if kaggle package is importable
    try:
        import kaggle  # noqa: F401
        return True
    except ImportError:
        pass
    
    return False

def kaggle_download(dataset_slug, dest_dir, unzip=True):
    """Download a Kaggle dataset to dest_dir."""
    os.makedirs(dest_dir, exist_ok=True)
    cmd = [
        sys.executable, "-m", "kaggle", "datasets", "download",
        "-d", dataset_slug,
        "-p", dest_dir
    ]
    if unzip:
        cmd.append("--unzip")
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode == 0

def setup_dermnet():
    """
    Downloads the DermNet dataset from Kaggle (19,500 images, 23 conditions).
    Requires Kaggle CLI to be set up.
    Dataset slug: shubhamgoel27/dermnet
    """
    print("\n--- SETTING UP DERMNET (19,500 images, 23 skin conditions) ---")
    
    dest = os.path.join(DATA_RAW_DIR, "dermnet")
    
    # Check if already downloaded
    existing = [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))]
    if existing:
        print(f"  DermNet data already present ({len(existing)} folders). Skipping.")
        return True
    
    if not check_kaggle():
        print_kaggle_setup_instructions()
        print("\n  [SKIP] Kaggle CLI not found. DermNet download skipped.")
        print("  Once Kaggle is set up, re-run this script or manually run:")
        print("    .venv/bin/python3 -m kaggle datasets download -d shubhamgoel27/dermnet -p data/raw/dermnet --unzip")
        return False
    
    print("  Downloading DermNet from Kaggle (~500MB, may take several minutes)...")
    success = kaggle_download("shubhamgoel27/dermnet", dest, unzip=True)
    
    if success:
        print("  ✅ DermNet downloaded successfully.")
    else:
        print("  [ERROR] DermNet download failed. Check Kaggle credentials.")
    return success

def setup_ham10000():
    """
    Downloads HAM10000 from Kaggle (10,015 images + metadata CSV).
    Dataset slug: kmader/skin-cancer-mnist-ham10000
    """
    print("\n--- SETTING UP HAM10000 (10,015 images, skin lesion dataset) ---")
    
    dest = os.path.join(DATA_RAW_DIR, "ham10000")
    metadata_path = os.path.join(dest, "HAM10000_metadata.csv")
    
    if os.path.exists(metadata_path):
        print(f"  HAM10000 metadata already present. Skipping.")
        return True
    
    if not check_kaggle():
        print_kaggle_setup_instructions()
        print("\n  [SKIP] Kaggle CLI not found. HAM10000 download skipped.")
        print("  Once Kaggle is set up, re-run this script or manually run:")
        print("    .venv/bin/python3 -m kaggle datasets download -d kmader/skin-cancer-mnist-ham10000 -p data/raw/ham10000 --unzip")
        return False
    
    print("  Downloading HAM10000 from Kaggle (~2.5GB, may take 10-20 minutes)...")
    success = kaggle_download("kmader/skin-cancer-mnist-ham10000", dest, unzip=True)
    
    if success:
        # Move images to a consistent location if needed
        ham_images_dest = os.path.join(dest, "images")
        os.makedirs(ham_images_dest, exist_ok=True)
        
        # HAM10000 Kaggle zip extracts into HAM10000_images_part1 and part2 folders
        for part_folder in ["HAM10000_images_part1", "HAM10000_images_part2"]:
            part_path = os.path.join(dest, part_folder)
            if os.path.exists(part_path):
                for img_file in os.listdir(part_path):
                    src = os.path.join(part_path, img_file)
                    dst = os.path.join(ham_images_dest, img_file)
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                shutil.rmtree(part_path, ignore_errors=True)
                print(f"  Moved {part_folder} -> {ham_images_dest}")
        
        print("  ✅ HAM10000 downloaded and organized.")
    else:
        print("  [ERROR] HAM10000 download failed. Check Kaggle credentials.")
    return success

def setup_fitzpatrick(max_images=500):
    """
    Downloads Fitzpatrick17k metadata CSV and attempts to download images
    from the source URLs in the CSV (with graceful failure handling).
    Note: Many URLs in this CSV are from external medical sites that may
    block scraping. Successful downloads are used; failures are skipped.
    """
    print("\n--- SETTING UP FITZPATRICK 17K ---")
    csv_url = "https://raw.githubusercontent.com/mattgroh/fitzpatrick17k/main/fitzpatrick17k.csv"
    csv_dest = os.path.join(DATA_RAW_DIR, "fitzpatrick17k", "fitzpatrick17k.csv")
    img_dest_dir = os.path.join(DATA_RAW_DIR, "fitzpatrick17k", "images")
    
    # Download CSV if not already present
    if not os.path.exists(csv_dest):
        print(f"  Downloading Fitzpatrick17k metadata CSV...")
        try:
            urllib.request.urlretrieve(csv_url, csv_dest)
            print(f"  ✅ CSV downloaded to {csv_dest}")
        except Exception as e:
            print(f"  [ERROR] Failed to download Fitzpatrick17k CSV: {e}")
            return
    else:
        print(f"  Fitzpatrick17k CSV already present. Skipping CSV download.")
    
    df = pd.read_csv(csv_dest)
    print(f"  Loaded Fitzpatrick17k CSV with {len(df)} rows.")
    
    # Check how many images already downloaded
    existing_imgs = [f for f in os.listdir(img_dest_dir) if f.endswith('.jpg')] if os.path.exists(img_dest_dir) else []
    print(f"  Already downloaded: {len(existing_imgs)} images.")
    
    if len(existing_imgs) >= max_images:
        print(f"  Already have {len(existing_imgs)} images. Skipping download.")
        return
    
    # Filter to target conditions
    target_conditions = ["acne", "eczema", "psoriasis", "tinea", "rosacea", "dermatitis"]
    df_targets = df[df["label"].str.lower().str.contains('|'.join(target_conditions), na=False)]
    print(f"  Found {len(df_targets)} target condition rows.")
    
    remaining_to_download = max_images - len(existing_imgs)
    existing_hashes = set(f.replace('.jpg', '') for f in existing_imgs)
    
    urls_to_download = []
    for _, row in df_targets.iterrows():
        img_id = str(row["md5hash"])
        if img_id in existing_hashes:
            continue
        url = row["url"]
        out_path = os.path.join(img_dest_dir, f"{img_id}.jpg")
        urls_to_download.append((url, out_path))
        if len(urls_to_download) >= remaining_to_download:
            break
    
    print(f"  Attempting to download {len(urls_to_download)} images (success rate varies by host availability)...")
    
    def download_single_image(url_out):
        url, out = url_out
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response, open(out, 'wb') as out_file:
                out_file.write(response.read())
            return True
        except Exception:
            return False
    
    downloaded = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_single_image, item): item for item in urls_to_download}
        for future in as_completed(futures):
            if future.result():
                downloaded += 1
                if downloaded % 25 == 0:
                    print(f"  Progress: {downloaded} downloaded, {failed} failed...")
            else:
                failed += 1
    
    print(f"  Fitzpatrick17k: {downloaded} downloaded, {failed} failed (external host availability varies).")
    total_now = len([f for f in os.listdir(img_dest_dir) if f.endswith('.jpg')])
    print(f"  Total available: {total_now} images.")

def print_kaggle_setup_instructions():
    """Print clear instructions for setting up Kaggle CLI."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          KAGGLE CLI SETUP — REQUIRED FOR REAL DATA           ║
╠══════════════════════════════════════════════════════════════╣
║  1. Create a free account at https://www.kaggle.com          ║
║  2. Go to: Account > Settings > API > Create New Token       ║
║     This downloads kaggle.json to your Downloads folder.     ║
║  3. Run these commands:                                      ║
║     mkdir -p ~/.kaggle                                       ║
║     cp ~/Downloads/kaggle.json ~/.kaggle/kaggle.json         ║
║     chmod 600 ~/.kaggle/kaggle.json                          ║
║  4. Install Kaggle CLI:                                      ║
║     .venv/bin/pip install kaggle                             ║
║  5. Re-run this script:                                      ║
║     .venv/bin/python3 src/download_datasets.py              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def print_status_report():
    """Print a summary of what's currently available in data/raw."""
    print("\n" + "="*60)
    print("DATASET AVAILABILITY REPORT")
    print("="*60)
    
    # DermNet
    dermnet_path = os.path.join(DATA_RAW_DIR, "dermnet")
    dermnet_dirs = [d for d in os.listdir(dermnet_path) if os.path.isdir(os.path.join(dermnet_path, d))] if os.path.exists(dermnet_path) else []
    dermnet_imgs = sum(len([f for f in os.listdir(os.path.join(dermnet_path, d)) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]) for d in dermnet_dirs if os.path.exists(os.path.join(dermnet_path, d)))
    status_d = "✅ Ready" if dermnet_imgs > 100 else "❌ Not downloaded"
    print(f"  DermNet:          {status_d} ({dermnet_imgs} images across {len(dermnet_dirs)} folders)")
    
    # HAM10000
    ham_meta = os.path.join(DATA_RAW_DIR, "ham10000", "HAM10000_metadata.csv")
    ham_images = os.path.join(DATA_RAW_DIR, "ham10000", "images")
    ham_img_count = len([f for f in os.listdir(ham_images) if f.lower().endswith('.jpg')]) if os.path.exists(ham_images) else 0
    status_h = "✅ Ready" if os.path.exists(ham_meta) and ham_img_count > 100 else ("⚠️ Metadata only" if os.path.exists(ham_meta) else "❌ Not downloaded")
    print(f"  HAM10000:         {status_h} ({ham_img_count} images)")
    
    # Fitzpatrick17k
    fitz_csv = os.path.join(DATA_RAW_DIR, "fitzpatrick17k", "fitzpatrick17k.csv")
    fitz_images = os.path.join(DATA_RAW_DIR, "fitzpatrick17k", "images")
    fitz_img_count = len([f for f in os.listdir(fitz_images) if f.lower().endswith('.jpg')]) if os.path.exists(fitz_images) else 0
    status_f = "✅ Ready" if fitz_img_count > 50 else ("⚠️ CSV only" if os.path.exists(fitz_csv) else "❌ Not downloaded")
    print(f"  Fitzpatrick17k:   {status_f} ({fitz_img_count} images)")
    
    total = dermnet_imgs + ham_img_count + fitz_img_count
    print(f"\n  TOTAL IMAGES AVAILABLE: {total:,}")
    
    if total > 500:
        print("\n  ✅ Sufficient data to run load_and_merge_real.py!")
        print("  Next step: .venv/bin/python3 src/load_and_merge_real.py")
    elif total > 0:
        print("\n  ⚠️ Some data available but limited. Consider downloading more.")
        print("  You can still run: .venv/bin/python3 src/load_and_merge_real.py")
    else:
        print("\n  ❌ No real data available yet. Set up Kaggle CLI and re-run.")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("TrueSkin v1 — Real Dataset Download Script")
    print("="*60)
    
    max_fitz = 500  # Fitzpatrick17k images to attempt (URL success rate ~30-50%)
    if len(sys.argv) > 1:
        try:
            max_fitz = int(sys.argv[1])
        except ValueError:
            pass
    
    create_dirs()
    
    # Step 1: DermNet via Kaggle (primary skin condition dataset)
    setup_dermnet()
    
    # Step 2: HAM10000 via Kaggle (none_of_these / skin cancer)
    setup_ham10000()
    
    # Step 3: Fitzpatrick17k via direct URL scraping (best-effort)
    setup_fitzpatrick(max_images=max_fitz)
    
    # Print availability report
    print_status_report()
