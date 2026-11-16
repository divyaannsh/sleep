"""
rPPG Processor — TrueSkin Face Scan Module
==========================================
Adapted from: Heart-rate-measurement-using-camera/process.py
(CHROM algorithm — de Haan & Jeanne, 2013)

Uses MediaPipe Face Mesh instead of dlib so no extra model files
are needed beyond what is already in requirements.txt.

Metrics computed:
  - Heart Rate (BPM) via FFT + peak-interval fusion
  - HRV RMSSD (ms)
  - Breathing Rate (BPM) — estimated from slow amplitude modulation of pleth
  - Stress Index — derived from RMSSD (higher RMSSD = lower stress)
  - Parasympathetic Activity — RMSSD-based proxy
  - Signal Quality (0-100 %)
"""

import cv2
import numpy as np
import time
import base64
from typing import Optional, Tuple, Dict, Any
from scipy import signal
from scipy.signal import find_peaks

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False


# ── ROI landmark indices (MediaPipe 468-point mesh) ───────────────────────────
# Left cheek cluster  (~landmark 234, 93, 132, 58, 172)
# Right cheek cluster (~landmark 454, 323, 361, 288, 397)
# Forehead cluster    (~landmark 10, 338, 297, 332, 284)
_LEFT_CHEEK_IDX  = [234, 93, 132, 58, 172, 136, 150]
_RIGHT_CHEEK_IDX = [454, 323, 361, 288, 397, 365, 379]
_FOREHEAD_IDX    = [10, 338, 297, 332, 284, 251, 389]


class RppgProcessor:
    """
    Stateful rPPG processor for one user session.
    Call `process_frame(jpeg_bytes)` once per camera frame.
    Read `get_vitals()` to get current estimates.
    Call `reset()` to start a new session.
    """

    BUFFER_SIZE = 256      # ~8-9 s @30 fps — fine FFT resolution
    MIN_FRAMES  = 60       # Need at least 2 s before first estimate

    def __init__(self):
        self._init_mp()
        self.reset()

    # ── MediaPipe setup ───────────────────────────────────────────────────────
    def _init_mp(self):
        if not _MP_AVAILABLE:
            self.face_mesh = None
            return
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    # ── Reset / init buffers ──────────────────────────────────────────────────
    def reset(self):
        self.r_buffer:  list[float] = []
        self.g_buffer:  list[float] = []
        self.b_buffer:  list[float] = []
        self.times:     list[float] = []
        self.t0         = time.time()
        self.bpm        = 0.0
        self.bpms:      list[float] = []
        self.rmssd      = 0.0
        self.breathing  = 0.0
        self.stress_idx = 0.0
        self.parasym    = 0.0
        self.quality    = 0.0          # 0-100
        self.spo2       = 98.0         # 90-100
        self.pleth      = np.array([])
        self.peak_indices = np.array([], dtype=int)
        self._frame_count = 0
        self.fps        = 0.0
        self.smooth_landmarks = None
        self.use_filtfilt = False

    # ── Public API ────────────────────────────────────────────────────────────
    def process_frame(self, jpeg_bytes: bytes) -> bool:
        """
        Accept a JPEG frame (bytes), run MediaPipe face mesh,
        extract ROI RGB, update buffers and recompute vitals.

        Returns True if a face was found, False otherwise.
        """
        self._frame_count += 1

        # decode
        nparr = np.frombuffer(jpeg_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return False

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]

        if self.face_mesh is None:
            return False

        results = self.face_mesh.process(frame_rgb)
        if not results.multi_face_landmarks:
            return False

        landmarks = results.multi_face_landmarks[0].landmark

        # EMA Landmark Smoothing to reduce jitter
        raw_coords = np.array([[l.x, l.y, l.z] for l in landmarks])
        if self.smooth_landmarks is None or len(self.smooth_landmarks) != len(raw_coords):
            self.smooth_landmarks = raw_coords
        else:
            self.smooth_landmarks = 0.8 * self.smooth_landmarks + 0.2 * raw_coords

        # Dynamic ROI based on face width (12% of total face width, so pad = 6% on each side)
        face_xs = [self.smooth_landmarks[i][0] for i in range(len(landmarks))]
        face_width_px = (max(face_xs) - min(face_xs)) * w
        dynamic_pad = max(4, min(int(face_width_px * 0.06), 40))

        def roi_patch(idx_list):
            """Extract pixel patch around a cluster of landmarks."""
            xs = [int(self.smooth_landmarks[i][0] * w) for i in idx_list]
            ys = [int(self.smooth_landmarks[i][1] * h) for i in idx_list]
            cx, cy = int(np.mean(xs)), int(np.mean(ys))
            x1 = max(0, cx - dynamic_pad); x2 = min(w, cx + dynamic_pad)
            y1 = max(0, cy - dynamic_pad); y2 = min(h, cy + dynamic_pad)
            patch = frame[y1:y2, x1:x2]
            return patch if patch.size > 0 else None

        patches = [
            roi_patch(_LEFT_CHEEK_IDX),
            roi_patch(_RIGHT_CHEEK_IDX),
            roi_patch(_FOREHEAD_IDX),
        ]

        r_vals, g_vals, b_vals = [], [], []
        for p in patches:
            if p is None or p.size == 0:
                continue
            r_vals.append(float(np.mean(p[:, :, 2])))
            g_vals.append(float(np.mean(p[:, :, 1])))
            b_vals.append(float(np.mean(p[:, :, 0])))

        if not r_vals:
            return False

        r_val = float(np.mean(r_vals))
        g_val = float(np.mean(g_vals))
        b_val = float(np.mean(b_vals))

        L = len(self.r_buffer)

        # outlier guard — replace sudden jumps (motion / lighting spikes) with the
        # recent channel mean. Matches the artifact rejection in
        # habom2310/Heart-rate-measurement-using-camera. NOTE: the values must be
        # written back to the names that get appended below, otherwise the clamp
        # is a no-op (previous bug: reassigning a loop-local copy did nothing).
        if L > 20:
            mu_r = float(np.mean(self.r_buffer[-20:]))
            mu_g = float(np.mean(self.g_buffer[-20:]))
            mu_b = float(np.mean(self.b_buffer[-20:]))
            if abs(r_val - mu_r) > 15: r_val = mu_r
            if abs(g_val - mu_g) > 15: g_val = mu_g
            if abs(b_val - mu_b) > 15: b_val = mu_b

        self.times.append(time.time() - self.t0)
        self.r_buffer.append(r_val)
        self.g_buffer.append(g_val)
        self.b_buffer.append(b_val)

        # rolling trim
        if L >= self.BUFFER_SIZE:
            self.r_buffer    = self.r_buffer[-self.BUFFER_SIZE:]
            self.g_buffer    = self.g_buffer[-self.BUFFER_SIZE:]
            self.b_buffer    = self.b_buffer[-self.BUFFER_SIZE:]
            self.times       = self.times[-self.BUFFER_SIZE:]
            self.bpms        = self.bpms[-(self.BUFFER_SIZE // 2):]
            L = self.BUFFER_SIZE

        if L >= self.MIN_FRAMES:
            self._compute_vitals(L)

        return True

    def get_vitals(self) -> Dict[str, Any]:
        """Return current estimates (or 0/None if not ready yet)."""
        ready = len(self.bpms) > 0
        # Report a temporally-smoothed BPM (median of recent windows) instead of the
        # last instantaneous estimate, so a single noisy window does not show to the user.
        bpm_out = float(np.median(self.bpms[-10:])) if ready else None
        return {
            "ready":       ready,
            "bpm":         round(bpm_out, 1)        if ready else None,
            "rmssd":       round(self.rmssd, 1)     if ready else None,
            "breathing":   round(self.breathing, 1) if ready else None,
            "stress":      round(self.stress_idx, 1)if ready else None,
            "parasym":     round(self.parasym, 1)   if ready else None,
            "quality":     round(self.quality, 1),
            "spo2":        round(self.spo2, 1)      if ready else None,
            "frames":      self._frame_count,
            "fps":         round(self.fps, 1),
        }

    def final_post_process(self):
        """Run zero-phase filtering post-processing on final buffer data for maximum accuracy."""
        self.use_filtfilt = True
        L = len(self.r_buffer)
        if L >= self.MIN_FRAMES:
            self._compute_vitals(L)

    # ── Internal signal processing ────────────────────────────────────────────
    def _chrom_signal(self, r, g, b):
        """CHROM rPPG — de Haan & Jeanne 2013."""
        r = np.array(r, dtype=np.float64)
        g = np.array(g, dtype=np.float64)
        b = np.array(b, dtype=np.float64)
        rn = r / (np.mean(r) + 1e-9)
        gn = g / (np.mean(g) + 1e-9)
        bn = b / (np.mean(b) + 1e-9)
        Xs = 3.0 * rn - 2.0 * gn
        Ys = 1.5 * rn + gn - 1.5 * bn
        alpha = (np.std(Xs) + 1e-9) / (np.std(Ys) + 1e-9)
        return Xs - alpha * Ys

    def _pos_signal(self, r, g, b):
        """POS rPPG — Wang et al. 2016."""
        r = np.array(r, dtype=np.float64)
        g = np.array(g, dtype=np.float64)
        b = np.array(b, dtype=np.float64)
        rn = r / (np.mean(r) + 1e-9)
        gn = g / (np.mean(g) + 1e-9)
        bn = b / (np.mean(b) + 1e-9)
        S1 = rn - gn
        S2 = rn + gn - 2.0 * bn
        alpha = np.std(S1) / (np.std(S2) + 1e-9)
        return S1 + alpha * S2

    def _calculate_signal_quality(self, sig, L):
        """Calculates peak spectral ratio SNR (0-100) for rPPG signal quality."""
        even_times   = np.linspace(self.times[0], self.times[-1], L)
        detrended    = signal.detrend(sig)
        interpolated = np.interp(even_times, self.times, detrended)
        windowed     = np.hamming(L) * interpolated
        norm         = windowed / (np.linalg.norm(windowed) + 1e-9)
        raw          = np.fft.rfft(norm * 30)
        fft_amp      = np.abs(raw) ** 2
        freqs        = float(self.fps) / L * np.arange(L // 2 + 1)
        freqs_bpm    = 60.0 * freqs
        idx = np.where((freqs_bpm > 52) & (freqs_bpm < 160))
        if len(idx[0]) == 0:
            return 0.0, freqs_bpm, fft_amp, 0
        local_fft   = fft_amp[idx]
        idx2        = int(np.argmax(local_fft))
        abs_idx2    = int(idx[0][idx2])
        
        # Harmonic doubling suppression:
        # If the detected peak is > 90 BPM, check if there's a strong fundamental peak at peak / 2.
        # Guarded so we do NOT halve a genuine high heart rate: the half-rate candidate is only
        # accepted when it is physiologically plausible AND (no history yet, or it is closer to the
        # recent running BPM than the full-rate peak). This adds hysteresis so a sustained real
        # tachycardia (e.g. ~100 BPM) is not reported as ~50.
        peak_bpm = freqs_bpm[abs_idx2]
        if peak_bpm > 90:
            target_fund = peak_bpm / 2.0
            mask_indices = idx[0]
            best_fund_idx = mask_indices[0]
            min_diff = abs(freqs_bpm[best_fund_idx] - target_fund)
            for m_idx in mask_indices:
                diff = abs(freqs_bpm[m_idx] - target_fund)
                if diff < min_diff:
                    min_diff = diff
                    best_fund_idx = m_idx

            fund_strong = fft_amp[best_fund_idx] > 0.45 * fft_amp[abs_idx2]
            fund_plausible = freqs_bpm[best_fund_idx] >= 50.0
            if fund_strong and fund_plausible:
                if self.bpms:
                    ref = float(np.median(self.bpms[-10:]))
                    if abs(freqs_bpm[best_fund_idx] - ref) <= abs(peak_bpm - ref):
                        abs_idx2 = int(best_fund_idx)
                else:
                    abs_idx2 = int(best_fund_idx)

        total_power = np.sum(local_fft) + 1e-9
        peak_power  = fft_amp[abs_idx2]
        quality = float(np.clip((peak_power / total_power) * 200, 0, 100))
        return quality, freqs_bpm, fft_amp, abs_idx2

    def _butter_bandpass(self, lowcut, highcut, fs, order=3):
        nyq  = 0.5 * fs
        low  = max(1e-4, min(lowcut / nyq,  0.9999))
        high = max(low + 1e-4, min(highcut / nyq, 0.9999))
        b, a = signal.butter(order, [low, high], btype='band')
        return b, a

    def _bandpass(self, data, low, high, fs, order=3):
        b, a = self._butter_bandpass(low, high, fs, order)
        if getattr(self, 'use_filtfilt', False) and len(data) > 3 * max(len(b), len(a)):
            return signal.filtfilt(b, a, data)
        return signal.lfilter(b, a, data)

    def _compute_rmssd(self, peaks, fps):
        if len(peaks) < 3:
            return 0.0
        rr_ms = np.diff(peaks) / fps * 1000.0
        successive = np.diff(rr_ms)
        return float(np.sqrt(np.mean(successive ** 2))) if len(successive) else 0.0

    def _estimate_breathing(self, pleth, fps):
        """Breathing rate from envelope (amplitude modulation) of pleth signal."""
        if len(pleth) < int(fps * 4):
            return 0.0
        envelope = np.abs(signal.hilbert(pleth))
        # breathing typically 0.15–0.5 Hz (9–30 breaths/min)
        br_signal = self._bandpass(envelope, 0.15, 0.5, fps, order=2)
        peaks, _ = find_peaks(br_signal, distance=int(fps * 1.5))
        if len(peaks) < 2:
            return 0.0
        rr_s = np.diff(peaks) / fps
        br = 60.0 / float(np.median(rr_s))
        return float(np.clip(br, 6.0, 40.0))

    def _compute_vitals(self, L):
        """Full pipeline: CHROM/POS comparison → FFT → peak BPM → Adaptive BP filtering → HRV → breathing → quality."""
        self.fps = float(L) / (self.times[-1] - self.times[0] + 1e-9)
        if self.fps < 1.0:
            return

        chrom = self._chrom_signal(self.r_buffer, self.g_buffer, self.b_buffer)
        pos = self._pos_signal(self.r_buffer, self.g_buffer, self.b_buffer)

        # Compare CHROM vs POS SNR/Quality and select the best signal
        chrom_q, chrom_freqs, chrom_fft, chrom_idx2 = self._calculate_signal_quality(chrom, L)
        pos_q, pos_freqs, pos_fft, pos_idx2 = self._calculate_signal_quality(pos, L)

        if pos_q > chrom_q:
            selected_sig = pos
            self.quality = pos_q
            freqs_bpm = pos_freqs
            fft_amp = pos_fft
            idx2 = pos_idx2
        else:
            selected_sig = chrom
            self.quality = chrom_q
            freqs_bpm = chrom_freqs
            fft_amp = chrom_fft
            idx2 = chrom_idx2

        local_freqs = freqs_bpm[np.where((freqs_bpm > 52) & (freqs_bpm < 160))]
        local_fft   = fft_amp[np.where((freqs_bpm > 52) & (freqs_bpm < 160))]

        if len(local_fft) == 0:
            return

        # Sub-bin parabolic interpolation
        if 0 < idx2 < len(fft_amp) - 1:
            y0, y1, y2 = fft_amp[idx2-1], fft_amp[idx2], fft_amp[idx2+1]
            denom = 2*y1 - y0 - y2
            delta = 0.5 * (y2 - y0) / (denom + 1e-12)
            bin_w = freqs_bpm[1] - freqs_bpm[0] if len(freqs_bpm) > 1 else 0
            fft_bpm = freqs_bpm[idx2] + delta * bin_w
        else:
            fft_bpm = freqs_bpm[idx2]

        # First pass broad bandpass (0.7 to 3.5 Hz)
        pleth = self._bandpass(selected_sig, 0.7, 3.5, self.fps, order=3)
        if len(pleth) >= 9:
            pleth = signal.savgol_filter(pleth, window_length=9, polyorder=2)
        self.pleth = pleth

        # Peak detection
        min_dist   = max(1, int(self.fps * 0.33))
        amp_range  = np.ptp(pleth) if np.ptp(pleth) > 0 else 1.0
        prominence = amp_range * 0.25
        pks, _     = find_peaks(pleth, distance=min_dist, prominence=prominence)
        self.peak_indices = pks.astype(int)

        # Peak-interval BPM
        peak_bpm = 0.0
        if len(pks) >= 3:
            rr_s     = np.diff(pks) / self.fps
            valid_rr = rr_s[(rr_s > 0.33) & (rr_s < 1.5)]
            if len(valid_rr) >= 2:
                peak_bpm = 60.0 / float(np.median(valid_rr))

        # Fuse FFT + peak
        if 48 < peak_bpm < 180:
            self.bpm = 0.4 * fft_bpm + 0.6 * peak_bpm
        else:
            self.bpm = fft_bpm

        # Second pass: Adaptive bandpass filtering around the estimated HR
        if 48 < self.bpm < 180:
            hr_hz = self.bpm / 60.0
            adaptive_low = max(0.6, hr_hz - 0.4)
            adaptive_high = min(3.5, hr_hz + 0.4)
            
            pleth = self._bandpass(selected_sig, adaptive_low, adaptive_high, self.fps, order=3)
            if len(pleth) >= 9:
                pleth = signal.savgol_filter(pleth, window_length=9, polyorder=2)
            self.pleth = pleth
            
            pks, _ = find_peaks(pleth, distance=min_dist, prominence=np.ptp(pleth) * 0.25 if np.ptp(pleth) > 0 else 0.1)
            self.peak_indices = pks.astype(int)

        self.bpms.append(self.bpm)

        # HRV RMSSD
        self.rmssd = self._compute_rmssd(pks, self.fps)

        # Breathing rate
        self.breathing = self._estimate_breathing(pleth, self.fps)

        # Stress index (inverse of RMSSD, scaled 0-100)
        self.stress_idx = float(np.clip(100 - (self.rmssd / 80.0) * 100, 0, 100))

        # Parasympathetic activity
        self.parasym = float(np.clip((self.rmssd / 80.0) * 100, 0, 100))

        # SpO2 estimation using Red and Blue ratio-of-ratios
        if len(self.r_buffer) >= 30 and len(self.b_buffer) >= 30:
            r_dc = np.mean(self.r_buffer)
            b_dc = np.mean(self.b_buffer)
            
            r_ac_sig = self._bandpass(self.r_buffer, 0.7, 3.5, self.fps, order=3)
            b_ac_sig = self._bandpass(self.b_buffer, 0.7, 3.5, self.fps, order=3)
            
            r_ac = np.std(r_ac_sig)
            b_ac = np.std(b_ac_sig)
            
            R = (r_ac / (r_dc + 1e-9)) / (b_ac / (b_dc + 1e-9) + 1e-9)
            spo2_val = 102.0 - 4.0 * R
            self.spo2 = float(np.clip(spo2_val, 95.0, 100.0))
        else:
            self.spo2 = 98.0
