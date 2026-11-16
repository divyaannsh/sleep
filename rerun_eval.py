# rerun_eval.py
# Re-evaluates the already-trained TrueSkin model to recover the
# skin-tone bucket breakdown (and full per-class report) without retraining.

import os
import pandas as pd
import albumentations as A
from torch.utils.data import DataLoader
import torch

from classifier import (
    SkinLesionDataset,
    get_efficientnet_model,
    evaluate_model,
    report_metrics,
    DEVICE,
)
from data_pipeline import CLASSES

MODEL_PATH = "trueskin_efficientnet.pth"
TEST_SPLIT = "data/processed/test_split.csv"

def main():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Couldn't find {MODEL_PATH} — make sure you're running this "
            f"from the same directory where training saved the weights."
        )
    if not os.path.exists(TEST_SPLIT):
        raise FileNotFoundError(
            f"Couldn't find {TEST_SPLIT} — make sure the processed real "
            f"dataset split is still in place."
        )

    print(f"Loading test split from {TEST_SPLIT}...")
    test_df = pd.read_csv(TEST_SPLIT)
    print(f"  - Test set size: {len(test_df)}")

    test_transform = A.Compose([A.Resize(224, 224)])
    test_dataset = SkinLesionDataset(test_df, transform=test_transform, is_train=False)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    print(f"Loading model weights from {MODEL_PATH}...")
    model = get_efficientnet_model(num_classes=len(CLASSES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model = model.to(DEVICE)

    print("Running evaluation on test set...")
    y_true, y_pred, y_probs, skin_tones = evaluate_model(model, test_loader)

    # This prints AND saves classification_report.csv + confusion_matrix.png,
    # and prints the skin-tone bucket breakdown to terminal.
    report_metrics(y_true, y_pred, skin_tones, output_dir="artifacts")

    # Also save skin-tone breakdown to a file this time, since the original
    # report_metrics() only prints it and doesn't persist it anywhere.
    df_eval = pd.DataFrame({"true": y_true, "pred": y_pred, "skin_tone": skin_tones})
    rows = []
    for bucket in ["light", "medium", "dark", "unknown"]:
        bucket_data = df_eval[df_eval["skin_tone"] == bucket]
        if len(bucket_data) > 0:
            correct = (bucket_data["true"] == bucket_data["pred"]).sum()
            acc = correct / len(bucket_data)
            rows.append({"skin_tone": bucket, "accuracy": acc, "correct": correct, "total": len(bucket_data)})
        else:
            rows.append({"skin_tone": bucket, "accuracy": None, "correct": 0, "total": 0})

    skin_tone_df = pd.DataFrame(rows)
    skin_tone_df.to_csv("artifacts/skin_tone_breakdown.csv", index=False)
    print("\nSaved skin-tone breakdown to artifacts/skin_tone_breakdown.csv")

if __name__ == "__main__":
    main()
