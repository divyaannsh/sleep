import os
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
import seaborn as sns
import albumentations as A


from data_pipeline import load_unified_dataset, get_data_split_and_report, get_phone_camera_augmentations, CLASSES, SKIN_TONE_BUCKETS

# ── Class-weighting softening knob ──────────────────────────────────────────
# 1.0  = full balanced weights (default, strong correction for rare classes)
# 0.5  = square-root softening (reduces overcorrection if none_of_these recall
#        collapses below ~70% after a full-weight run)
# 0.0  = flat weights (equivalent to unweighted CrossEntropyLoss)
WEIGHT_SOFTENING = 0.5
from region_detector import SkinRegionDetector

# Select device: Mac MPS, CUDA, or CPU
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

print(f"Using device: {DEVICE}")

class SkinLesionDataset(Dataset):
    def __init__(self, dataframe, transform=None, is_train=True):
        self.df = dataframe.reset_index(drop=True)
        self.transform = transform
        self.is_train = is_train
        self.detector = SkinRegionDetector()
        
        # Class to index mapping
        self.class_to_idx = {cls: idx for idx, cls in enumerate(CLASSES)}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = row["image_path"]
        label_str = row["mapped_label"]
        skin_tone = row["skin_tone_bucket"]
        
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            # Fallback to black image if path is broken
            img = np.zeros((224, 224, 3), dtype=np.uint8)
        
        # Stage 1: Region Detection (Crop region of interest)
        bbox, _ = self.detector.detect_region(img)
        cropped_img = self.detector.crop_region(img, bbox)
        
        # Convert BGR to RGB (required for Albumentations and PyTorch Models)
        cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
        
        # Stage 2: Apply Augmentations
        if self.transform:
            augmented = self.transform(image=cropped_img)
            cropped_img = augmented["image"]
            
        # Normalize and convert to FloatTensor: (C, H, W)
        # Manually normalize since we aren't using torchvision transforms
        img_tensor = cropped_img.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_tensor = (img_tensor - mean) / std
        img_tensor = np.transpose(img_tensor, (2, 0, 1)) # HWC -> CHW
        
        target = self.class_to_idx[label_str]
        
        return {
            "image": torch.tensor(img_tensor, dtype=torch.float32),
            "label": torch.tensor(target, dtype=torch.long),
            "skin_tone": skin_tone,
            "raw_path": img_path
        }

def get_efficientnet_model(num_classes=6):
    """
    Loads pretrained EfficientNet-B0 and replaces the head for transfer learning.
    """
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    # Freeze all feature extraction layers initially
    for param in model.parameters():
        param.requires_grad = False
        
    # Replace final linear classification layer
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

def train_epoch(model, dataloader, optimizer, criterion):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for batch in dataloader:
        images = batch["image"].to(DEVICE)
        labels = batch["label"].to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels).item()
        total += labels.size(0)
        
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

def evaluate_model(model, dataloader):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    all_skin_tones = []
    
    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(DEVICE)
            labels = batch["label"]
            skin_tones = batch["skin_tone"]
            
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            _, preds = torch.max(outputs, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs)
            all_skin_tones.extend(skin_tones)
            
    return np.array(all_labels), np.array(all_preds), np.array(all_probs), all_skin_tones

def report_metrics(y_true, y_pred, skin_tones, output_dir="artifacts"):
    """
    Reports per-class metrics, skin-tone bias metrics, and generates confusion matrix.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Per-class metrics
    report = classification_report(
        y_true, y_pred, 
        target_names=CLASSES, 
        labels=list(range(len(CLASSES))), 
        output_dict=True,
        zero_division=0
    )
    
    df_report = pd.DataFrame(report).transpose()
    df_report.to_csv(os.path.join(output_dir, "classification_report.csv"))
    
    print("\n================ EVALUATION METRICS REPORT ================")
    print("\nPer-Class Classification Report:")
    print(df_report.round(3))
    
    # 2. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASSES))))
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=CLASSES, yticklabels=CLASSES, cmap='Blues')
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))
    plt.close()
    print(f"\nConfusion matrix saved to artifacts/confusion_matrix.png")
    
    # 3. Skin-tone bucket analysis
    df_eval = pd.DataFrame({
        "true": y_true,
        "pred": y_pred,
        "skin_tone": skin_tones
    })
    
    # Compute accuracy per skin tone bucket
    print("\nAccuracy broken down by Skin-Tone Bucket:")
    for bucket in ["light", "medium", "dark", "unknown"]:
        bucket_data = df_eval[df_eval["skin_tone"] == bucket]
        if len(bucket_data) > 0:
            correct = (bucket_data["true"] == bucket_data["pred"]).sum()
            acc = correct / len(bucket_data)
            print(f"  - {bucket.capitalize()} Skin Tone: {acc*100:.2f}% accuracy ({correct}/{len(bucket_data)} samples)")
        else:
            print(f"  - {bucket.capitalize()} Skin Tone: No samples present in test split")
    print("==========================================================")
    
    return df_report

def apply_confidence_threshold(probs, threshold=0.6):
    """
    Applies the server-side confidence threshold.
    If the max probability is below the threshold, labels it as 'none_of_these' or returns uncertainty.
    """
    top_idx = np.argmax(probs)
    top_conf = probs[top_idx]
    
    if top_conf < threshold:
        # Return index 5 which corresponds to 'none_of_these' (unclear / uncertain)
        return 5, top_conf, False
    return top_idx, top_conf, True

def get_class_weights(train_df, classes):
    """
    Computes inverse-frequency class weights from the training split so
    CrossEntropyLoss penalizes mistakes on rare classes (psoriasis, acne,
    rosacea) more heavily, instead of letting the model coast on
    none_of_these dominance.

    Watch after retraining: if none_of_these recall collapses (model starts
    seeing psoriasis everywhere), soften with weights ** 0.5 instead of
    removing weighting entirely.
    """
    labels = train_df["mapped_label"].values
    class_indices = np.array([classes.index(l) for l in labels])

    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(len(classes)),
        y=class_indices,
    )
    # Apply softening exponent so caller can reduce overcorrection without
    # rewriting the function (e.g. WEIGHT_SOFTENING=0.5 → weights**0.5).
    weights = weights ** WEIGHT_SOFTENING

    print(f"\nComputed class weights (balanced, softening={WEIGHT_SOFTENING}):")
    for cls, w in zip(classes, weights):
        print(f"  - {cls}: {w:.3f}")

    return torch.tensor(weights, dtype=torch.float32)


def run_training_loop(base_dir="data", model_path="trueskin_efficientnet.pth"):
    processed_train = "data/processed/train_split.csv"
    processed_test = "data/processed/test_split.csv"
    
    if os.path.exists(processed_train) and os.path.exists(processed_test):
        print("Found processed real datasets. Loading directly...")
        train_df = pd.read_csv(processed_train)
        test_df = pd.read_csv(processed_test)
        print(f"  - Loaded Train Set Size: {len(train_df)}")
        print(f"  - Loaded Test Set Size: {len(test_df)}")
    else:
        print("Processed real datasets not found. Falling back to unified mock dataset loader...")
        df = load_unified_dataset(base_dir)
        train_df, test_df = get_data_split_and_report(df)

    
    # Augmentations for train, only standard transforms/resize for test
    train_transform = get_phone_camera_augmentations()
    test_transform = A.Compose([
        A.Resize(224, 224)
    ])
    
    train_dataset = SkinLesionDataset(train_df, transform=train_transform, is_train=True)
    test_dataset = SkinLesionDataset(test_df, transform=test_transform, is_train=False)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
    
    # Load Model
    model = get_efficientnet_model(num_classes=len(CLASSES))
    model = model.to(DEVICE)

    # Compute inverse-frequency class weights so rare classes (psoriasis,
    # rosacea, acne) are penalized more heavily than none_of_these.
    class_weights = get_class_weights(train_df, CLASSES).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # Stage 1: Train Head only (Warm-up)
    optimizer = optim.Adam(model.classifier.parameters(), lr=1e-3)
    print("\nStage 1: Training Classification Head (Base layers frozen)...")
    for epoch in range(2):
        loss, acc = train_epoch(model, train_loader, optimizer, criterion)
        print(f"  Epoch {epoch+1}/2 - Loss: {loss:.4f}, Accuracy: {acc*100:.2f}%")
        
    # Stage 2: Fine-tune entire model
    print("\nStage 2: Fine-tuning entire network (Base layers unfrozen)...")
    for param in model.parameters():
        param.requires_grad = True
        
    optimizer = optim.Adam(model.parameters(), lr=1e-5) # Very small learning rate for fine-tuning
    for epoch in range(3):
        loss, acc = train_epoch(model, train_loader, optimizer, criterion)
        print(f"  Epoch {epoch+1}/3 - Loss: {loss:.4f}, Accuracy: {acc*100:.2f}%")
        
    # Save model weights
    torch.save(model.state_dict(), model_path)
    print(f"\nModel saved to {model_path}")
    
    # Evaluate
    print("\nEvaluating model on stratified test set...")
    y_true, y_pred, y_probs, skin_tones = evaluate_model(model, test_loader)

    # Report metrics (saves classification_report.csv + confusion_matrix.png)
    df_after = report_metrics(y_true, y_pred, skin_tones)

    # ── BEFORE vs AFTER recall comparison ───────────────────────────────────
    # Hardcoded BEFORE numbers from the unweighted baseline run.
    # Update these if you ever reset the baseline.
    BEFORE = {
        "acne":            {"recall": 0.278, "precision": 0.508, "f1": 0.360},
        "eczema":          {"recall": 0.317, "precision": 0.442, "f1": 0.369},
        "psoriasis":       {"recall": 0.028, "precision": 0.303, "f1": 0.052},
        "fungal_infection":{"recall": 0.361, "precision": 0.594, "f1": 0.449},
        "rosacea":         {"recall": 0.191, "precision": 0.379, "f1": 0.254},
        "none_of_these":   {"recall": 0.941, "precision": 0.792, "f1": 0.860},
    }
    WATCH_CLASSES = ["psoriasis", "acne", "rosacea", "none_of_these"]

    print("\n" + "=" * 60)
    print("  STEP 1 — BEFORE vs AFTER (class-weighted loss)")
    print(f"  Weight softening exponent: {WEIGHT_SOFTENING}")
    print("=" * 60)
    print(f"  {'Class':<20} {'Recall BEF':>10} {'Recall AFT':>10}  {'Δ':>7}  {'Flag'}")
    print("  " + "-" * 56)
    overcorrect_flag = False
    for cls in WATCH_CLASSES:
        before_r = BEFORE[cls]["recall"]
        after_r  = float(df_after.loc[cls, "recall"]) if cls in df_after.index else float("nan")
        delta    = after_r - before_r
        flag = ""
        if cls == "none_of_these" and after_r < 0.70:
            flag = "⚠️  OVERCORRECTION — none_of_these recall < 70%"
            overcorrect_flag = True
        elif cls != "none_of_these" and after_r < before_r:
            flag = "⬇  regression"
        elif cls != "none_of_these" and after_r >= before_r + 0.10:
            flag = "✅ meaningful gain"
        print(f"  {cls:<20} {before_r:>10.3f} {after_r:>10.3f}  {delta:>+7.3f}  {flag}")
    print("=" * 60)
    if overcorrect_flag:
        print("  ACTION NEEDED: none_of_these recall < 70%.")
        print("  Re-run with WEIGHT_SOFTENING = 0.5 to soften class weights.")
    else:
        print("  none_of_these recall is acceptable. Review psoriasis/acne/")
        print("  rosacea gains above before proceeding to Step 2.")
    print("=" * 60)
    
    # Test confidence thresholding logic
    print("\nTesting Confidence Thresholding Logic:")
    # Confident output sample (highest prob)
    confident_idx = np.argmax([max(p) for p in y_probs])
    conf_probs = y_probs[confident_idx]
    pred_idx, conf, is_confident = apply_confidence_threshold(conf_probs, threshold=0.6)
    print(f"  - Confident Sample Prob Distribution: {conf_probs.round(3)}")
    print(f"    Raw Top Class: {CLASSES[np.argmax(conf_probs)]} ({max(conf_probs):.2f})")
    print(f"    Threshold Result: class={CLASSES[pred_idx]} (conf={conf:.2f}, confident={is_confident})")
    
    # Ambiguous output sample (close to uniform distribution)
    ambiguous_probs = np.array([0.2, 0.15, 0.25, 0.15, 0.15, 0.10]) # Max is 0.25, below 0.60
    pred_idx_amb, conf_amb, is_confident_amb = apply_confidence_threshold(ambiguous_probs, threshold=0.6)
    print(f"  - Ambiguous Sample Prob Distribution: {ambiguous_probs.round(3)}")
    print(f"    Raw Top Class: {CLASSES[np.argmax(ambiguous_probs)]} ({max(ambiguous_probs):.2f})")
    print(f"    Threshold Result: class={CLASSES[pred_idx_amb]} (conf={conf_amb:.2f}, confident={is_confident_amb} - Uncertain)")

if __name__ == "__main__":
    run_training_loop()
