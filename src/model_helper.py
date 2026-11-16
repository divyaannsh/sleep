import os

import numpy as np
import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0

# Define target classes
CLASSES = ["acne", "eczema", "psoriasis", "fungal_infection", "rosacea", "none_of_these"]

# Select device
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")

def get_efficientnet_model(num_classes=6):
    """
    Instantiates the EfficientNet-B0 architecture.
    We pass weights=None because we load our own trained weights at runtime.
    """
    model = efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

def apply_confidence_threshold(probs, threshold=0.6):
    """
    Applies confidence threshold.
    Returns: (predicted_class_index, confidence, is_confident)
    """
    top_idx = np.argmax(probs)
    top_conf = probs[top_idx]
    
    if top_conf < threshold:
        # Return index 5 which corresponds to 'none_of_these'
        return 5, top_conf, False
    return top_idx, top_conf, True

class rPPGBPPredictor(nn.Module):
    """
    Exact PyTorch replica of the 9-layer dense MLP model structure used in the
    Blood Pressure Estimation deep learning project.
    Takes 180 normalized rPPG signal samples and outputs [Systolic, Diastolic] BP.
    """
    def __init__(self):
        super(rPPGBPPredictor, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(180, 96),
            nn.ReLU(),
            nn.Linear(96, 84),
            nn.ReLU(),
            nn.Linear(84, 72),
            nn.ReLU(),
            nn.Linear(72, 60),
            nn.ReLU(),
            nn.Linear(60, 48),
            nn.ReLU(),
            nn.Linear(48, 36),
            nn.ReLU(),
            nn.Linear(36, 24),
            nn.ReLU(),
            nn.Linear(24, 12),
            nn.ReLU(),
            nn.Linear(12, 2)
        )
        
        # Initialize weights to small variance and biases to produce clinically normal BP ranges
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.normal_(layer.weight, mean=0.0, std=0.005)
                nn.init.constant_(layer.bias, 0.0)
        
        # Calibrate output layer to baseline normal BP (120/80 mmHg)
        with torch.no_grad():
            self.network[-1].bias.copy_(torch.tensor([120.0, 80.0], dtype=torch.float32))

    def forward(self, x):
        return self.network(x)


def is_git_lfs_pointer(path: str) -> bool:
    """
    Detect tiny Git LFS pointer files so we do not mistake them for real weights.
    """
    if not os.path.exists(path) or os.path.getsize(path) > 1024:
        return False
    try:
        with open(path, "r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
        return first_line == "version https://git-lfs.github.com/spec/v1"
    except Exception:
        return False


def load_torch_bp_predictor(weights_path: str):
    """
    Load the PyTorch BP replica using a real checkpoint file.
    """
    model = rPPGBPPredictor()
    try:
        state_dict = torch.load(weights_path, map_location="cpu")
    except Exception:
        # PyTorch >=2.6 changed default torch.load behavior; retry for trusted local files.
        state_dict = torch.load(weights_path, map_location="cpu", weights_only=False)
    model.load_state_dict(state_dict)
    model.eval()
    return model
