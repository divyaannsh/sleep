"""
apply_tagging_sample.py  —  STEP 3b tool (run AFTER manually filling tagging_sample.csv)

Usage:
    PYTHONPATH=src .venv/bin/python3 apply_tagging_sample.py

Reads tagging_sample.csv (which you filled in with fitzpatrick_tone values 1-6
or "unsure"), merges those labels into the tagged subset of the test split, and
prints the skin-tone bucket accuracy breakdown on just that tagged subset.

Output is clearly labeled as a directional estimate on ~300 images — not the
full dataset, not statistically definitive.
"""

import os
import torch
import pandas as pd
import numpy as np
import albumentations as A
from torch.utils.data import DataLoader

from classifier import SkinLesionDataset, get_efficientnet_model, evaluate_model
from data_pipeline import CLASSES

MODEL_PATH   = "trueskin_efficientnet.pth"
TEST_SPLIT   = "data/processed/test_split.csv"
TAGGING_CSV  = "tagging_sample.csv"

FITZPATRICK_TO_BUCKET = {
    1: "light", 2: "light",
    3: "medium", 4: "medium",
    5: "dark",  6: "dark",
}


def main():
    # ── Validation ───────────────────────────────────────────────────────────
    for path in [MODEL_PATH, TEST_SPLIT, TAGGING_CSV]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required file not found: {path}\n"
                "Make sure you have run sample_for_tagging.py and filled in "
                "the fitzpatrick_tone column before running this script."
            )

    # ── Load tagging sample ──────────────────────────────────────────────────
    tag_df = pd.read_csv(TAGGING_CSV)
    filled = tag_df[tag_df["fitzpatrick_tone"].notna() &
                    (tag_df["fitzpatrick_tone"].astype(str).str.strip() != "")]
    print(f"Tagging CSV: {len(tag_df)} rows total, {len(filled)} with tone filled in.")

    if len(filled) == 0:
        print("[ERROR] No rows have fitzpatrick_tone filled in. "
              "Open tagging_sample.csv and add values (1-6 or 'unsure') before re-running.")
        return

    # ── Map Fitzpatrick values to buckets ────────────────────────────────────
    def to_bucket(val):
        try:
            i = int(str(val).strip())
            return FITZPATRICK_TO_BUCKET.get(i, "unknown")
        except (ValueError, TypeError):
            return "unknown"  # covers "unsure" or blank

    filled = filled.copy()
    filled["skin_tone_bucket"] = filled["fitzpatrick_tone"].apply(to_bucket)

    tone_counts = filled["skin_tone_bucket"].value_counts()
    print("\nSkin-tone bucket distribution in tagged sample:")
    for bucket, count in tone_counts.items():
        print(f"  - {bucket}: {count}")

    # ── Merge with test split (inner join on image_path) ────────────────────
    test_df = pd.read_csv(TEST_SPLIT)
    merged  = test_df.merge(
        filled[["image_path", "skin_tone_bucket"]],
        on="image_path",
        how="inner",
        suffixes=("_orig", ""),
    )
    print(f"\nMatched {len(merged)} tagged images found in test split.")

    if len(merged) == 0:
        print("[ERROR] No overlap between tagging_sample.csv image_path and "
              "test_split.csv — check that paths match exactly.")
        return

    # Overwrite skin_tone_bucket column with manually tagged values
    if "skin_tone_bucket_orig" in merged.columns:
        merged = merged.drop(columns=["skin_tone_bucket_orig"])

    # ── Run inference on tagged subset ───────────────────────────────────────
    from model_helper import DEVICE
    test_transform = A.Compose([A.Resize(224, 224)])
    dataset = SkinLesionDataset(merged, transform=test_transform, is_train=False)
    loader  = DataLoader(dataset, batch_size=16, shuffle=False)

    model = get_efficientnet_model(num_classes=len(CLASSES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)

    print("Running inference on tagged subset...")
    y_true, y_pred, _, _ = evaluate_model(model, loader)

    # ── Skin-tone accuracy breakdown ─────────────────────────────────────────
    tone_labels = merged["skin_tone_bucket"].tolist()
    df_eval = pd.DataFrame({"true": y_true, "pred": y_pred, "skin_tone": tone_labels})

    print("\n" + "=" * 68)
    print("  DIRECTIONAL SKIN-TONE READ — manually tagged sample")
    print(f"  N = {len(merged)} images  |  NOT representative of full dataset.")
    print("  Do NOT treat these numbers as definitive bias measurements.")
    print("=" * 68)
    for bucket in ["light", "medium", "dark", "unknown"]:
        sub = df_eval[df_eval["skin_tone"] == bucket]
        if len(sub) > 0:
            correct = (sub["true"] == sub["pred"]).sum()
            acc = correct / len(sub)
            print(f"  {bucket.capitalize():<8} skin tone: "
                  f"{acc*100:.1f}%  ({correct}/{len(sub)} correct)")
        else:
            print(f"  {bucket.capitalize():<8} skin tone: no samples tagged")
    print("=" * 68)
    print("\nReview these numbers and report back before proceeding to Phase 3.")


if __name__ == "__main__":
    main()
