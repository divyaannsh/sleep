import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# Try to import from model_helper
try:
    from model_helper import rPPGBPPredictor, DEVICE
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from model_helper import rPPGBPPredictor, DEVICE

class BPDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def generate_synthetic_ppg_data(num_samples=1500, seq_len=180, fps=30):
    """
    Generates high-fidelity synthetic PPG signals mapped to physiological BP targets.
    A single cardiac pulse is modeled as a sum of two Gaussians:
    one for the systolic peak, and one for the diastolic/dicrotic notch peak.
    """
    print(f"Generating {num_samples} synthetic PPG training samples...")
    X = []
    y = []

    for _ in range(num_samples):
        # 1. Sample realistic blood pressures (systolic / diastolic)
        # Class 1: Normal (120/80)
        # Class 2: Prehypertension (130/85)
        # Class 3: Stage 1 Hypertension (145/92)
        # Class 4: Stage 2 Hypertension (165/102)
        bp_class = np.random.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1])
        if bp_class == 1:
            systolic = np.random.normal(115, 5)
            diastolic = np.random.normal(75, 4)
        elif bp_class == 2:
            systolic = np.random.normal(128, 4)
            diastolic = np.random.normal(84, 3)
        elif bp_class == 3:
            systolic = np.random.normal(144, 5)
            diastolic = np.random.normal(92, 4)
        else:
            systolic = np.random.normal(168, 8)
            diastolic = np.random.normal(104, 6)

        # Ensure diastolic is always lower than systolic
        systolic = max(90, min(180, systolic))
        diastolic = max(55, min(110, diastolic))
        if diastolic >= systolic - 20:
            diastolic = systolic - 30

        # 2. Derive signal shape features from the BP values
        # Pulse amplitude (systolic - diastolic) relates to the height of the peaks
        pulse_pressure = systolic - diastolic
        amp_sys = 0.5 + 0.5 * (pulse_pressure / 70.0) # Normalized amplitude
        amp_dia = 0.2 + 0.3 * (diastolic / 110.0)

        # Heart rate dictates the cycle length
        # Higher BP is slightly correlated with higher HR
        hr = np.random.normal(72 + (systolic - 120) * 0.15, 8)
        hr = max(50, min(110, hr))
        cycle_len_seconds = 60.0 / hr
        cycle_len_frames = cycle_len_seconds * fps

        # Time delay between systolic and diastolic peaks (Pulse Transit Time indicator)
        # Higher systolic BP -> stiffer arteries -> faster transit time -> smaller delay
        peak_delay_seconds = 0.25 - 0.08 * ((systolic - 90) / 90.0)
        peak_delay_frames = peak_delay_seconds * fps

        # 3. Construct the continuous time series
        t = np.arange(seq_len)
        signal = np.zeros(seq_len)

        # Add successive cardiac pulses
        num_pulses = int(np.ceil(seq_len / cycle_len_frames)) + 1
        for p in range(-1, num_pulses):
            center_sys = p * cycle_len_frames + np.random.normal(0, 0.5) # Jitter
            center_dia = center_sys + peak_delay_frames

            # Systolic pulse (Gaussian shape)
            width_sys = cycle_len_frames * 0.12
            signal += amp_sys * np.exp(-0.5 * ((t - center_sys) / width_sys) ** 2)

            # Diastolic/Reflected pulse (Gaussian shape, wider and smaller)
            width_dia = cycle_len_frames * 0.18
            signal += amp_dia * np.exp(-0.5 * ((t - center_dia) / width_dia) ** 2)

        # 4. Add baseline breathing modulation (0.15 - 0.3 Hz) and high-frequency noise
        resp_rate = np.random.uniform(12, 20) / 60.0 # breaths/sec
        resp_mod = 0.15 * np.sin(2 * np.pi * resp_rate * (t / fps))
        signal += resp_mod

        # Baseline drift
        drift = 0.05 * np.sin(2 * np.pi * 0.02 * (t / fps))
        signal += drift

        # High frequency sensor noise
        noise = np.random.normal(0, 0.025, seq_len)
        signal += noise

        # 5. Z-score standard normalization (matches the frontend scaling step)
        sig_mean = np.mean(signal)
        sig_std = np.std(signal) if np.std(signal) > 1e-6 else 1.0
        normalized_signal = (signal - sig_mean) / sig_std

        X.append(normalized_signal)
        y.append([systolic, diastolic])

    return np.array(X), np.array(y)

def train_bp_model():
    print("================ TRUE SKIN: TRAINING BP MLP ESTIMATOR ================")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    h5_path = os.path.join(base_dir, "Blood_Pressure_Estimation_with_Webcam_using_Deep_Learning", "rPPG-BP-UKL_rppg_7s.h5")
    
    # Check if real dataset exists
    if os.path.exists(h5_path):
        print(f"✅ Found real dataset at {h5_path}. Loading real dataset...")
        try:
            import h5py
            import pandas as pd
            
            with h5py.File(h5_path, "r") as f:
                rppg = np.array(f['rppg'])       # shape e.g. (875, N) or (N, 875)
                labels = np.array(f['label'])    # shape e.g. (2, N) or (N, 2)
            
            # Transpose if needed so samples are along row axis
            if rppg.shape[0] == 875 or rppg.shape[0] == 180:
                rppg = rppg.T
            if labels.shape[0] == 2:
                labels = labels.T
                
            print(f"Loaded real dataset: rPPG shape {rppg.shape}, Labels shape {labels.shape}")
            
            # Slice first 180 samples of the signal (or downsample)
            X = rppg[:, :180]
            y = labels
            
            # Standard z-score scale
            X_normalized = []
            for i in range(len(X)):
                s = X[i]
                m = np.mean(s)
                sd = np.std(s) + 1e-9
                X_normalized.append((s - m) / sd)
            X = np.array(X_normalized)
            
        except Exception as e:
            print(f"Warning: Failed to load real HDF5 dataset: {e}. Falling back to synthetic simulation.")
            X, y = generate_synthetic_ppg_data()
    else:
        print(f"ℹ️ Real dataset not found at {h5_path}. Running high-fidelity simulation model training...")
        X, y = generate_synthetic_ppg_data()

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    train_dataset = BPDataset(X_train, y_train)
    test_dataset = BPDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    model = rPPGBPPredictor().to(DEVICE)
    print(f"Training on device: {DEVICE}")
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=15, min_lr=1e-5)
    
    epochs = 120
    train_losses = []
    val_losses = []
    
    print("\nStarting neural network training...")
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
            
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * len(batch_x)
            
        epoch_loss /= len(train_dataset)
        train_losses.append(epoch_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                preds = model(batch_x)
                loss = criterion(preds, batch_y)
                val_loss += loss.item() * len(batch_x)
        val_loss /= len(test_dataset)
        val_losses.append(val_loss)
        
        scheduler.step(val_loss)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:03d}/{epochs} - Train MSE: {epoch_loss:.2f} | Val MSE: {val_loss:.2f}")

    # Evaluate final metrics
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(DEVICE)
            preds = model(batch_x)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.numpy())
            
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    # Calculate MAE
    sys_mae = np.mean(np.abs(all_preds[:, 0] - all_targets[:, 0]))
    dia_mae = np.mean(np.abs(all_preds[:, 1] - all_targets[:, 1]))
    
    print("\n" + "=" * 50)
    print("                EVALUATION SUMMARY")
    print("=" * 50)
    print(f"  Systolic MAE:  {sys_mae:.3f} mmHg")
    print(f"  Diastolic MAE: {dia_mae:.3f} mmHg")
    
    # R2 Score calculation
    def r2_score(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1.0 - (ss_res / (ss_tot + 1e-9))
        
    print(f"  Systolic R²:   {r2_score(all_targets[:, 0], all_preds[:, 0]):.3f}")
    print(f"  Diastolic R²:  {r2_score(all_targets[:, 1], all_preds[:, 1]):.3f}")
    print("=" * 50)
    
    # Save checkpoint
    out_path = os.path.join(base_dir, "trueskin_bp.pth")
    torch.save(model.state_dict(), out_path)
    print(f"\n✅ Model weights successfully saved to: {out_path}")
    
    # Plot loss curves
    plt.figure(figsize=(8, 5))
    plt.plot(train_losses, label="Train Loss (MSE)")
    plt.plot(val_losses, label="Val Loss (MSE)")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("TrueSkin BP Model Training Loss")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join(base_dir, "artifacts", "bp_training_loss.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    plt.close()
    print(f"Loss plot saved to: {plot_path}")

if __name__ == "__main__":
    train_bp_model()
