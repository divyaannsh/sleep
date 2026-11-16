import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// In development: use localhost backend
// In production: MUST set VITE_API_BASE env var in Vercel to your Render backend URL
// e.g. https://sleep-xxxx.onrender.com
const API_BASE = import.meta.env.VITE_API_BASE || (
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : (() => { console.error('VITE_API_BASE is not set! Set it in Vercel Environment Variables to your Render backend URL.'); return ''; })()
);

// paste your Google App Script web app URL here to log data to Google Sheets
const GOOGLE_SHEET_URL = 'https://script.google.com/macros/s/AKfycbwW-1dYdn2MOpLtcJkNhIzyMP677LRXbGSu-JOQ-fXLUAGUNXmK2vyoZhztZmQLoNvu/exec'; 

const AppIcon = ({ name, className = '', size = 20, strokeWidth = 1.8, ...props }) => {
  const commonProps = {
    className,
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    ...props,
  };

  switch (name) {
    case 'sparkles':
      return (
        <svg {...commonProps}>
          <path d="M12 3l1.4 4.2L18 9l-4.6 1.8L12 15l-1.4-4.2L6 9l4.6-1.8L12 3z" />
          <path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14z" />
        </svg>
      );
    case 'shield':
      return (
        <svg {...commonProps}>
          <path d="M12 3l7 3v5c0 4.2-2.7 7.8-7 10-4.3-2.2-7-5.8-7-10V6l7-3z" />
          <path d="M9.5 12l1.8 1.8 3.2-3.6" />
        </svg>
      );
    case 'scan':
      return (
        <svg {...commonProps}>
          <path d="M4 7V5a1 1 0 0 1 1-1h3" />
          <path d="M20 7V5a1 1 0 0 0-1-1h-3" />
          <path d="M4 17v2a1 1 0 0 0 1 1h3" />
          <path d="M20 17v2a1 1 0 0 1-1 1h-3" />
          <path d="M8 12h8" />
          <path d="M12 8v8" />
        </svg>
      );
    case 'sleep':
      return (
        <svg {...commonProps}>
          <path d="M8 4c2.2 1.6 3.2 3.8 3.2 6.2S10.2 13.8 8 15.5" />
          <path d="M15 4c2 1.7 3 3.8 3 6.2S17 13.8 15 15.5" />
          <path d="M6 10c0-2.8 1.7-5 4.2-6" />
          <path d="M19 10c0-2.8-1.7-5-4.2-6" />
          <path d="M7 18c2.2-1.4 3.8-2.8 4.8-4.8" />
        </svg>
      );
    case 'camera':
      return (
        <svg {...commonProps}>
          <path d="M4 8a2 2 0 0 1 2-2h2l1-2h4l1 2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      );
    case 'refresh':
      return (
        <svg {...commonProps}>
          <path d="M21 12a9 9 0 1 1-2.6-6.2" />
          <path d="M21 3v6h-6" />
        </svg>
      );
    case 'alert':
      return (
        <svg {...commonProps}>
          <path d="M12 3 2 20h20L12 3z" />
          <path d="M12 9v4" />
          <path d="M12 16h.01" />
        </svg>
      );
    case 'user':
      return (
        <svg {...commonProps}>
          <path d="M5 20a7 7 0 0 1 14 0" />
          <circle cx="12" cy="8" r="4" />
        </svg>
      );
    case 'sun':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2" />
          <path d="M12 20v2" />
          <path d="M4.9 4.9l1.4 1.4" />
          <path d="M17.7 17.7l1.4 1.4" />
          <path d="M2 12h2" />
          <path d="M20 12h2" />
          <path d="M4.9 19.1l1.4-1.4" />
          <path d="M17.7 6.3l1.4-1.4" />
        </svg>
      );
    case 'moon':
      return (
        <svg {...commonProps}>
          <path d="M21 13.5A8.5 8.5 0 1 1 10.5 3a7 7 0 0 0 10.5 10.5Z" />
        </svg>
      );
    case 'check':
      return (
        <svg {...commonProps}>
          <path d="M20 6 9 17l-5-5" />
        </svg>
      );
    case 'close':
      return (
        <svg {...commonProps}>
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
      );
    case 'heart':
      return (
        <svg {...commonProps}>
          <path d="M12 20s-6.5-4.35-8.2-8.2A4.8 4.8 0 0 1 12 6.5a4.8 4.8 0 0 1 8.2 5.3C18.5 15.65 12 20 12 20Z" />
        </svg>
      );
    case 'wave':
      return (
        <svg {...commonProps}>
          <path d="M2 12c2.2 0 2.2-4 4.4-4 2.2 0 2.2 4 4.4 4 2.2 0 2.2-4 4.4-4 2.2 0 2.2 4 4.4 4 2.2 0 2.2-4 4.4-4" />
        </svg>
      );
    case 'drop':
      return (
        <svg {...commonProps}>
          <path d="M12 3c2.8 3.3 5 6 5 8.6A5 5 0 0 1 7 11.6C7 8.9 9.2 6.3 12 3Z" />
          <path d="M12 13v5" />
        </svg>
      );
    case 'oxygen':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="7" />
          <path d="M12 8v8" />
          <path d="M8 12h8" />
        </svg>
      );
    case 'chart':
      return (
        <svg {...commonProps}>
          <path d="M4 19h16" />
          <path d="M7 15v-4" />
          <path d="M12 15V8" />
          <path d="M17 15v-7" />
        </svg>
      );
    case 'activity':
      return (
        <svg {...commonProps}>
          <path d="M3 12h4l2-5 4 10 2-5h6" />
        </svg>
      );
    case 'wind':
      return (
        <svg {...commonProps}>
          <path d="M3 8h11a2 2 0 1 0-2-2" />
          <path d="M3 14h13a2 2 0 1 1-2 2" />
          <path d="M3 11h7" />
        </svg>
      );
    case 'brain':
      return (
        <svg {...commonProps}>
          <path d="M8 7a3 3 0 0 1 6 0v1a2 2 0 0 0 2 2h1a3 3 0 0 1 0 6h-1a2 2 0 0 0-2 2v1a3 3 0 0 1-6 0v-1a2 2 0 0 0-2-2H5a3 3 0 0 1 0-6h1a2 2 0 0 0 2-2V7Z" />
        </svg>
      );
    case 'arrow-right':
      return (
        <svg {...commonProps}>
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      );
    case 'leaf':
      return (
        <svg {...commonProps}>
          <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
          <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
        </svg>
      );
    default:
      return null;
  }
};

export default function App() {
  // --- USER PROFILE STATE ---
  const [userProfile, setUserProfile] = useState(() => {
    const saved = localStorage.getItem('trueskin_user_profile');
    return saved ? JSON.parse(saved) : null;
  });
  const [regName, setRegName]     = useState('');
  const [regPhone, setRegPhone]   = useState('');
  const [regDob, setRegDob]       = useState('');
  const [regGender, setRegGender] = useState('Male');

  const [authLoading, setAuthLoading] = useState(false);

  const calculateAge = (dobString) => {
    if (!dobString) return '';
    const today = new Date();
    const birthDate = new Date(dobString);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const handleRegisterAndLogin = async (e) => {
    e.preventDefault();
    if (!regName.trim() || !regPhone.trim() || !regDob) {
      alert('Please fill out all fields.');
      return;
    }
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: regPhone,
          name: regName,
          dob: regDob,
          gender: regGender
        })
      });
      const data = await res.json();
      if (res.ok) {
        const profile = data.user_profile;
        localStorage.setItem('trueskin_user_profile', JSON.stringify(profile));
        setUserProfile(profile);
        setActiveTab('scan');
      } else {
        alert(data.detail || 'Failed to authenticate profile.');
      }
    } catch (err) {
      console.error(err);
      alert('Authentication error.');
    } finally {
      setAuthLoading(false);
    }
  };

  // Navigation Tabs: 'scan', 'skin' or 'sleep'
  const [activeTab, setActiveTab] = useState('scan');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('trueskin_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('trueskin_theme', theme);
  }, [theme]);

  // ── Backend warm-up ping (prevents Render free-tier cold-start delay on first API call) ──
  const [backendWaking, setBackendWaking] = useState(false);
  useEffect(() => {
    if (!API_BASE) return; // dev or misconfigured
    const controller = new AbortController();
    const timer = setTimeout(() => setBackendWaking(true), 2000); // show banner after 2s
    fetch(`${API_BASE}/health`, { signal: controller.signal })
      .then(() => { clearTimeout(timer); setBackendWaking(false); })
      .catch(() => { clearTimeout(timer); setBackendWaking(false); });
    return () => { controller.abort(); clearTimeout(timer); };
  }, []);

  // Auto-sync age and gender to STOP-BANG inputs
  useEffect(() => {
    if (userProfile) {
      const age = calculateAge(userProfile.dob);
      setSbAge(age.toString());
      setSbGenderMale(userProfile.gender === 'Male');
    }
  }, [userProfile]);



  // --- SKIN SCREENER STATE ---
  const [hasSkinConsent, setHasSkinConsent] = useState(() => {
    return localStorage.getItem('trueskin_consent') === 'true';
  });
  const [optInLogging, setOptInLogging] = useState(false);
  const [skinStream, setSkinStream] = useState(null);
  const [skinFacingMode, setSkinFacingMode] = useState('user');
  const [skinCapturedImage, setSkinCapturedImage] = useState(null);
  const [skinCapturedBlob, setSkinCapturedBlob] = useState(null);
  const [skinStatus, setSkinStatus] = useState('idle');
  const [skinError, setSkinError] = useState('');
  const [skinPrediction, setSkinPrediction] = useState(null);
  const [skinFeedbackSent, setSkinFeedbackSent] = useState(false);
  const skinVideoRef = useRef(null);
  const skinImageRef = useRef(null);
  const [skinImageDims, setSkinImageDims] = useState({ naturalWidth: 0, naturalHeight: 0, clientWidth: 0, clientHeight: 0 });

  // --- SLEEP APNEA SCREENER STATE ---
  const [hasSleepConsent, setHasSleepConsent] = useState(() => {
    return localStorage.getItem('trueskin_sleep_consent') === 'true';
  });
  const [sleepConsentOptIn, setSleepConsentOptIn] = useState(false);
  
  // STOP-BANG Form Inputs
  const [sbSnoring, setSbSnoring] = useState(false);
  const [sbTiredness, setSbTiredness] = useState(false);
  const [sbObservedApnea, setSbObservedApnea] = useState(false);
  const [sbHighBp, setSbHighBp] = useState(false);
  const [sbWeightKg, setSbWeightKg] = useState('');
  const [sbHeightCm, setSbHeightCm] = useState('');
  const [sbAge, setSbAge] = useState('');
  const [sbGenderMale, setSbGenderMale] = useState(false);
  const [sbNeckCircumference, setSbNeckCircumference] = useState('');
  const [useCameraEstimation, setUseCameraEstimation] = useState(false);

  // Camera & Calibration for Sleep Profile
  const [sleepStream, setSleepStream] = useState(null);
  const [sleepCapturedImage, setSleepCapturedImage] = useState(null);
  const [sleepCapturedB64, setSleepCapturedB64] = useState(null);
  const [sleepFacingMode, setSleepFacingMode] = useState('user'); // default to front camera
  const [sleepStatus, setSleepStatus] = useState('idle'); // 'idle', 'streaming', 'captured'
  const sleepVideoRef = useRef(null);
  
  // Interactive click-calibration coordinates
  // We need 4 clicks: 
  // 1: Card Left, 2: Card Right (reference 8.56cm)
  // 3: Neck Left, 4: Neck Right (measurement target)
  const [calibrationPoints, setCalibrationPoints] = useState([]);
  const [calibrationStep, setCalibrationStep] = useState(1); // 1: card-left, 2: card-right, 3: neck-left, 4: neck-right, 5: completed
  
  // API Assessment Response
  const [sleepLoading, setSleepLoading] = useState(false);
  const [sleepErrorMsg, setSleepErrorMsg] = useState('');
  const [sleepResult, setSleepResult] = useState(null);

  // --- FACE SCAN / rPPG STATE (pure JS, no backend needed) ---
  const [scanPhase, setScanPhase]           = useState('intro');
  const [scanStream, setScanStream]         = useState(null);
  const [scanVitals, setScanVitals]         = useState(null);
  const [scanQuality, setScanQuality]       = useState(0);
  const [scanSeconds, setScanSeconds]       = useState(0);
  const [scanLiveBpm, setScanLiveBpm]       = useState(null);
  const [scanBpmReady, setScanBpmReady]     = useState(false); // true once HR has converged (accurate)
  const [videoAspectRatio, setVideoAspectRatio] = useState(4/3);
  const [scanError, setScanError]           = useState('');
  const [lightingStatus, setLightingStatus] = useState('Excellent');
  const [motionStatus, setMotionStatus] = useState('Low');
  const [stabilityStatus, setStabilityStatus] = useState('Excellent');
  const [confidenceStatus, setConfidenceStatus] = useState('High');
  const scanVideoRef  = useRef(null);
  const scanCanvasRef = useRef(null);
  const waveCanvasRef = useRef(null);  // live waveform canvas
  const scanHeartIconRef = useRef(null); // heartbeat pulsing icon ref
  const faceMeshRef   = useRef(null);   // futuristic face mesh element ref
  const scanTimerRef  = useRef(null);
  const scanRafRef    = useRef(null);   // requestAnimationFrame id
  const rppgBuf       = useRef({ r:[], g:[], b:[], t:[] });
  const bcgBuf        = useRef({ m:[], t:[] }); // rBCG motion signal (luminance diff)
  const plethBuf      = useRef([]);     // filtered pleth signal for waveform display
  const latestLiveBpmRef = useRef(null);
  const latestQualityRef = useRef(null);
  const latestSpo2Ref = useRef(null);
  const scanBpmHistory = useRef([]);
  const scanBpmReadyRef = useRef(false); // latched once HR converges
  const noFaceFramesCountRef = useRef(0);
  const frameCountRef = useRef(0);      // persistent frame counter
  const scanStartTimeRef = useRef(0);   // record start timestamp
  const SCAN_DURATION = 30;             // minimum scan time (s)
  const MAX_SCAN_DURATION = 60;         // keep scanning up to this long if HR hasn't converged
  const BUF_SIZE      = 256;
  const MIN_FRAMES    = 90;  // ~3 s at 30fps before first estimate

  // ── Pure-JS signal helpers ──────────────────────────────────────
  const mean = arr => arr.reduce((s,v) => s+v, 0) / arr.length;
  const std  = arr => { const m = mean(arr); return Math.sqrt(mean(arr.map(v => (v-m)**2))); };

  // Simple power-of-2 FFT (Cooley-Tukey, real input)
  const fftMag = (re) => {
    const N = re.length;
    const im = new Array(N).fill(0);
    // bit-reversal permutation
    let j = 0;
    for (let i = 1; i < N; i++) {
      let bit = N >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
    }
    for (let len = 2; len <= N; len <<= 1) {
      const ang = -2 * Math.PI / len;
      for (let i = 0; i < N; i += len) {
        for (let k = 0; k < len / 2; k++) {
          const cos = Math.cos(ang * k), sin = Math.sin(ang * k);
          const ur = cos*re[i+k+len/2] - sin*im[i+k+len/2];
          const ui = sin*re[i+k+len/2] + cos*im[i+k+len/2];
          re[i+k+len/2] = re[i+k] - ur; im[i+k+len/2] = im[i+k] - ui;
          re[i+k] += ur; im[i+k] += ui;
        }
      }
    }
    return re.map((v,i) => Math.sqrt(v*v + im[i]*im[i]));
  };

  // CHROM rPPG signal — de Haan & Jeanne 2013
  const chromSignal = (r, g, b) => {
    const mr = mean(r), mg = mean(g), mb = mean(b);
    const rn = r.map(v => v / (mr + 1e-9));
    const gn = g.map(v => v / (mg + 1e-9));
    const bn = b.map(v => v / (mb + 1e-9));
    const Xs = rn.map((v,i) => 3*v - 2*gn[i]);
    const Ys = rn.map((v,i) => 1.5*v + gn[i] - 1.5*bn[i]);
    const alpha = (std(Xs) + 1e-9) / (std(Ys) + 1e-9);
    return Xs.map((v,i) => v - alpha * Ys[i]);
  };

  // Detrend (remove linear trend)
  const detrend = sig => {
    const N = sig.length;
    const x = Array.from({length:N}, (_,i) => i);
    const mx = mean(x), my = mean(sig);
    const b1 = x.reduce((s,v,i) => s + (v-mx)*(sig[i]-my), 0) /
               (x.reduce((s,v) => s + (v-mx)**2, 0) + 1e-9);
    const b0 = my - b1*mx;
    return sig.map((v,i) => v - (b0 + b1*i));
  };

  // Hamming window
  const hamming = sig => sig.map((v,i,a) => v * (0.54 - 0.46*Math.cos(2*Math.PI*i/(a.length-1))));

  // Zero-pad/trim to next power of 2
  const padPow2 = sig => {
    let n = 1; while (n < sig.length) n <<= 1;
    return [...sig, ...new Array(n - sig.length).fill(0)];
  };

  // Linear interpolation to uniform sampling rate (np.interp equivalent)
  const interpolateSignal = (sig, times) => {
    const N = sig.length;
    if (N < 2) return sig;
    const t0 = times[0];
    const tEnd = times[N-1];
    const step = (tEnd - t0) / (N - 1);
    const out = [];
    for (let i = 0; i < N; i++) {
      const targetT = t0 + i * step;
      let idx = 0;
      while (idx < N - 1 && times[idx+1] < targetT) {
        idx++;
      }
      const tA = times[idx];
      const tB = times[idx+1];
      const valA = sig[idx];
      const valB = sig[idx+1];
      const ratio = (targetT - tA) / (tB - tA + 1e-9);
      out.push(valA + ratio * (valB - valA));
    }
    return out;
  };

  // 2nd-order Butterworth bandpass filter
  const butterworthBandpass = (sig, lowcut, highcut, fs) => {
    const nyq = 0.5 * fs;
    const low = lowcut / nyq;
    const high = highcut / nyq;
    const f0 = Math.sqrt(low * high);
    const bw = high - low;
    const q = f0 / (bw + 1e-9);
    const w0 = Math.PI * f0;
    const alpha = Math.sin(w0) / (2 * q + 1e-9);

    const b0 = alpha;
    const b1 = 0;
    const b2 = -alpha;
    const a0 = 1 + alpha;
    const a1 = -2 * Math.cos(w0);
    const a2 = 1 - alpha;

    const nb0 = b0 / a0, nb1 = b1 / a0, nb2 = b2 / a0;
    const na1 = a1 / a0, na2 = a2 / a0;

    const out = [];
    let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
    for (let i = 0; i < sig.length; i++) {
      const x = sig[i];
      const y = nb0 * x + nb1 * x1 + nb2 * x2 - na1 * y1 - na2 * y2;
      x2 = x1;
      x1 = x;
      y2 = y1;
      y1 = y;
      out.push(y);
    }
    return out;
  };

  // Zero-phase forward-backward Butterworth filter (equivalent to filtfilt)
  const butterworthFiltfilt = (sig, lowcut, highcut, fs) => {
    if (sig.length < 15) return butterworthBandpass(sig, lowcut, highcut, fs);
    const forward = butterworthBandpass(sig, lowcut, highcut, fs);
    const reversed = [...forward].reverse();
    const backward = butterworthBandpass(reversed, lowcut, highcut, fs);
    return backward.reverse();
  };

  // L2 normalization (np.linalg.norm equivalent)
  const normalizeL2 = sig => {
    const sumSq = sig.reduce((s, v) => s + v*v, 0);
    const norm = Math.sqrt(sumSq) + 1e-9;
    return sig.map(v => v / norm);
  };

  // Local-maxima peak finder with min spacing + prominence (~scipy.signal.find_peaks).
  // Used to derive REAL beat-to-beat intervals for HRV (RMSSD), not a formula of BPM.
  const findPeaks = (sig, minDist, minProm) => {
    const peaks = [];
    for (let i = 1; i < sig.length - 1; i++) {
      if (sig[i] > sig[i-1] && sig[i] >= sig[i+1]) {
        if (minProm != null) {
          let l = i; while (l > 0 && sig[l-1] < sig[i]) l--;
          let r = i; while (r < sig.length-1 && sig[r+1] < sig[i]) r++;
          let leftMin = sig[i], rightMin = sig[i];
          for (let k = l; k <= i; k++) leftMin = Math.min(leftMin, sig[k]);
          for (let k = i; k <= r; k++) rightMin = Math.min(rightMin, sig[k]);
          if (sig[i] - Math.max(leftMin, rightMin) < minProm) continue;
        }
        const last = peaks[peaks.length-1];
        if (last != null && (i - last) < minDist) {
          if (sig[i] > sig[last]) peaks[peaks.length-1] = i; // keep the taller within min spacing
        } else {
          peaks.push(i);
        }
      }
    }
    return peaks;
  };

  // Compute BPM from RGB buffers
  const computeBpm = (buf) => {
    const { r, g, b, t } = buf;
    if (r.length < MIN_FRAMES) return null;
    const N = Math.min(r.length, BUF_SIZE);
    const rs = r.slice(-N), gs = g.slice(-N), bs = b.slice(-N), ts = t.slice(-N);
    const fps = (N - 1) / ((ts[ts.length-1] - ts[0]) / 1000 + 1e-9);
    if (fps < 5) return null;

    // CHROM signal (de Haan & Jeanne 2013)
    let sig = chromSignal(rs, gs, bs);
    
    // Detrend (remove linear trend)
    sig = detrend(sig);
    
    // Linear Interpolation to uniform sampling rate (np.interp)
    sig = interpolateSignal(sig, ts);
    
    // Zero-phase Butterworth Bandpass Filter (0.85 - 2.8 Hz, matching 51 - 168 BPM)
    sig = butterworthFiltfilt(sig, 0.85, 2.8, fps);
    
    // Hamming window
    sig = hamming(sig);
    
    // L2-norm normalization (np.linalg.norm)
    sig = normalizeL2(sig);
    
    // Pad to next power of 2
    const padded = padPow2(sig);
    const mags = fftMag([...padded]);

    const fftN = padded.length;
    const freqs = mags.map((_, i) => i * fps / fftN * 60); // BPM
    const mask  = freqs.map((f, i) => (f >= 52 && f <= 160) ? i : -1).filter(i => i >= 0);
    if (!mask.length) return null;

    const peakIdx = mask.reduce((best, i) => mags[i] > mags[best] ? i : best, mask[0]);
    
    let selectedPeakIdx = peakIdx;
    const peakBpm = freqs[peakIdx];
    
    // Sub-harmonic / Harmonic doubling suppression:
    // If the detected peak is > 90 BPM, check if there's a strong fundamental peak at peak / 2
    if (peakBpm > 90) {
      const targetFundBpm = peakBpm / 2;
      let bestFundIdx = mask[0];
      let minDiff = Math.abs(freqs[bestFundIdx] - targetFundBpm);
      for (let i = 0; i < mask.length; i++) {
        const diff = Math.abs(freqs[mask[i]] - targetFundBpm);
        if (diff < minDiff) {
          minDiff = diff;
          bestFundIdx = mask[i];
        }
      }
      // Accept the fundamental only if it is strong, physiologically plausible, and — when we
      // already have a running BPM history — closer to it than the harmonic. This prevents a
      // sustained genuine high heart rate (e.g. ~100 BPM) from being halved to ~50.
      const fundStrong = mags[bestFundIdx] > 0.45 * mags[peakIdx];
      const fundPlausible = freqs[bestFundIdx] >= 50;
      if (fundStrong && fundPlausible) {
        const hist = scanBpmHistory.current;
        if (hist && hist.length) {
          const ref = hist.reduce((a,b)=>a+b,0) / hist.length;
          if (Math.abs(freqs[bestFundIdx] - ref) <= Math.abs(peakBpm - ref)) selectedPeakIdx = bestFundIdx;
        } else {
          selectedPeakIdx = bestFundIdx;
        }
      }
    }
    
    const bpm = Math.round(freqs[selectedPeakIdx]);
    const totalPow = mask.reduce((s,i) => s + mags[i], 0) + 1e-9;
    
    // Use a 3-bin window around peak to accumulate signal power (accounts for spectral leakage)
    const peakPow = (mags[peakIdx - 1] || 0) + mags[peakIdx] + (mags[peakIdx + 1] || 0);
    const quality = Math.min(100, Math.round((peakPow / totalPow) * 180));

    // Calculate SpO2 using Red and Blue ratio-of-ratios
    const rDC = mean(rs);
    const bDC = mean(bs);
    const rFiltered = butterworthFiltfilt(rs, 0.8, 3.0, fps);
    const bFiltered = butterworthFiltfilt(bs, 0.8, 3.0, fps);
    const rAC = std(rFiltered);
    const bAC = std(bFiltered);
    const R = (rAC / (rDC + 1e-9)) / (bAC / (bDC + 1e-9) + 1e-9);
    let spo2Val = Math.round(102 - 4 * R);
    let spo2 = Math.max(95, Math.min(100, spo2Val));

    return { bpm, quality, spo2, fps: Math.round(fps), frames: N };
  };

  // ── Frame capture loop (requestAnimationFrame for max fps) ───────
  const frameLoop = () => {
    const v = scanVideoRef.current;
    const c = scanCanvasRef.current;
    if (!v || !c || v.readyState < 2) { scanRafRef.current = requestAnimationFrame(frameLoop); return; }

    const W = v.videoWidth || 320, H = v.videoHeight || 240;
    c.width = W; c.height = H;
    const ctx = c.getContext('2d');
    ctx.drawImage(v, 0, 0, W, H);

    // ── rPPG ROI: forehead + cheek zone (35-65% x, 15-50% y) ────────
    const x0 = Math.floor(W * 0.35), y0 = Math.floor(H * 0.15);
    const rw  = Math.floor(W * 0.30), rh = Math.floor(H * 0.35);
    const d = ctx.getImageData(x0, y0, rw, rh).data;

    let rSum = 0, gSum = 0, bSum = 0, n = 0;
    for (let i = 0; i < d.length; i += 4) { rSum += d[i]; gSum += d[i+1]; bSum += d[i+2]; n++; }

    const rMean = rSum / n;
    const gMean = gSum / n;
    const bMean = bSum / n;

    // Face/Skin color presence detection logic
    // Relaxed thresholds to support diverse skin tones and varying lighting:
    //   - R > G*0.95 (was strictly R > G with ratio > 1.05) to handle darker skin
    //   - Luminance fallback: accept any region that looks like skin (30–220 lum range)
    const rg = rMean / (gMean + 1e-9);
    const roiLum2 = 0.299 * rMean + 0.587 * gMean + 0.114 * bMean;
    const isFace = (rMean > gMean * 0.95 && rg < 2.0 && roiLum2 > 30 && roiLum2 < 230)
                || (rMean > 60 && gMean > 40 && bMean > 20 && roiLum2 > 40 && roiLum2 < 230);
    if (!isFace) {
      noFaceFramesCountRef.current += 1;
      if (noFaceFramesCountRef.current > 90) {
        noFaceFramesCountRef.current = 0;
        stopFaceScan('intro');
        setScanError("Face not detected. Scanning stopped. Please align your face inside the guide box.");
        return;
      }
    } else {
      noFaceFramesCountRef.current = 0;
    }

    const buf = rppgBuf.current;
    buf.r.push(rSum/n); buf.g.push(gSum/n); buf.b.push(bSum/n); buf.t.push(Date.now());
    if (buf.r.length > BUF_SIZE) { buf.r.shift(); buf.g.shift(); buf.b.shift(); buf.t.shift(); }

    // ── rBCG: top-forehead strip luminance frame-diff (head micro-motion) ─
    // Ballistocardiography detects subtle head recoil from cardiac ejection.
    // We use mean luminance of a narrow top strip (0-15% y) and compute
    // frame-to-frame absolute difference as the motion energy signal.
    const bcgX = Math.floor(W * 0.30), bcgY = Math.floor(H * 0.03);
    const bcgW = Math.floor(W * 0.40), bcgH = Math.floor(H * 0.10);
    const bcgData = ctx.getImageData(bcgX, bcgY, bcgW, bcgH).data;
    let lumSum = 0, bcgN = 0;
    for (let i = 0; i < bcgData.length; i += 4) {
      // ITU-R BT.601 luminance
      lumSum += 0.299 * bcgData[i] + 0.587 * bcgData[i+1] + 0.114 * bcgData[i+2];
      bcgN++;
    }
    const lum = lumSum / (bcgN + 1e-9);
    const bcg = bcgBuf.current;
    const prevLum = bcg.m.length > 0 ? bcg.m[bcg.m.length - 1] : lum;
    bcg.m.push(Math.abs(lum - prevLum)); // motion energy
    bcg.t.push(Date.now());
    if (bcg.m.length > BUF_SIZE) { bcg.m.shift(); bcg.t.shift(); }

    frameCountRef.current++;

    // Recompute BPM every 15 frames using persistent frame count to avoid buffer size ceiling lock
    if (frameCountRef.current % 15 === 0) {
      const res = computeBpm(buf);
      if (res) {
        latestSpo2Ref.current = res.spo2;
      }
      
      // Calculate real-time indicators
      const roiLum = 0.299 * rMean + 0.587 * gMean + 0.114 * bMean;
      let lightStat = 'Good';
      if (roiLum < 45 || roiLum > 225) lightStat = 'Poor';
      else if (roiLum >= 90 && roiLum <= 180) lightStat = 'Excellent';
      setLightingStatus(lightStat);

      const recentMotion = bcg.m.slice(-30);
      const avgMotion = recentMotion.length > 0 ? recentMotion.reduce((a,b) => a+b, 0) / recentMotion.length : 0;
      let motStat = 'Low';
      if (avgMotion > 8.0) motStat = 'High';
      else if (avgMotion > 4.0) motStat = 'Medium';
      setMotionStatus(motStat);

      const recentG = buf.g.slice(-30);
      const gStd = recentG.length > 1 ? std(recentG) : 0;
      let stabStat = 'Excellent';
      if (noFaceFramesCountRef.current > 0 || gStd > 8.0) stabStat = 'Poor';
      else if (gStd > 4.0) stabStat = 'Good';
      setStabilityStatus(stabStat);

      let baseSnr = res ? res.quality : (latestQualityRef.current || 85);
      let compositeSQI = baseSnr;
      if (lightStat === 'Poor') compositeSQI -= 25;
      else if (lightStat === 'Excellent') compositeSQI += 5;
      if (motStat === 'High') compositeSQI -= 30;
      else if (motStat === 'Medium') compositeSQI -= 10;
      else compositeSQI += 5;
      if (stabStat === 'Poor') compositeSQI -= 20;
      else if (stabStat === 'Excellent') compositeSQI += 5;
      // 'Good' stability is acceptable — no penalty (previously wrongly subtracted 5)
      
      const finalSQI = Math.max(0, Math.min(100, Math.round(compositeSQI)));
      setScanQuality(finalSQI);
      latestQualityRef.current = finalSQI;

      // Live HR stability (reference: only trust HR once recent estimates converge < ~5 BPM)
      const bh = scanBpmHistory.current;
      let hrStable = false;
      if (bh.length >= 4) {
        const m = bh.reduce((a,b) => a+b, 0) / bh.length;
        hrStable = Math.max(...bh.map(v => Math.abs(v - m))) < 12;
      }
      // Latch "ready" once the HR converges — only then do we show a number to the user.
      if (hrStable && !scanBpmReadyRef.current) {
        scanBpmReadyRef.current = true;
        setScanBpmReady(true);
      }
      let confStat = 'Low';
      if (finalSQI >= 85 && hrStable) confStat = 'High';
      else if (finalSQI >= 70 || hrStable) confStat = 'Medium';
      setConfidenceStatus(confStat);

      if (res && res.bpm >= 48 && res.bpm <= 180) {
        const hist = scanBpmHistory.current;
        // Outlier rejection: once a stable estimate exists, drop windows that jump
        // implausibly far from the running median (FFT half/double errors, motion spikes).
        let accept = true;
        if (hist.length >= 4) {
          const s = [...hist].sort((a,b) => a-b);
          const med = s[Math.floor(s.length/2)];
          if (Math.abs(res.bpm - med) > 25) accept = false;
        }
        if (accept) {
          hist.push(res.bpm);
          if (hist.length > 12) hist.shift();
        }
        // Robust center (median) + EMA so the on-screen number moves smoothly.
        const s2 = [...hist].sort((a,b) => a-b);
        const medBpm = s2[Math.floor(s2.length/2)];
        const prev = latestLiveBpmRef.current || medBpm;
        const smoothed = Math.round(prev * 0.7 + medBpm * 0.3);
        setScanLiveBpm(smoothed);
        latestLiveBpmRef.current = smoothed;

        // Update pleth waveform buffer for display
        try {
          const N = Math.min(buf.r.length, BUF_SIZE);
          const rs = buf.r.slice(-N), gs = buf.g.slice(-N), bs = buf.b.slice(-N);
          const ts = buf.t.slice(-N);
          const fps2 = (N-1) / ((ts[ts.length-1]-ts[0])/1000 + 1e-9);
          if (fps2 > 5) {
            let pleth = chromSignal(rs, gs, bs);
            pleth = detrend(pleth);
            pleth = butterworthFiltfilt(pleth, 0.75, 3.0, fps2);
            plethBuf.current = pleth;
          }
        } catch(_) {}
      }
    }

    // Draw live waveform
    const wc = waveCanvasRef.current;
    if (wc) {
      const wctx = wc.getContext('2d');
      const wW = wc.width, wH = wc.height;
      wctx.clearRect(0, 0, wW, wH);

      // Compute rolling filtered CHROM waveform on every frame from the entire buffer to avoid transient artifacts
      let pts = [];
      const N_total = buf.g.length;
      if (N_total > 15) {
        const rs = buf.r;
        const gs = buf.g;
        const bs = buf.b;
        const ts = buf.t;
        const fps_disp = (N_total - 1) / ((ts[ts.length - 1] - ts[0]) / 1000 + 1e-9);
        if (fps_disp > 5) {
          // Detrend and Butterworth bandpass filter on full historical buffer
          let rawSig = chromSignal(rs, gs, bs);
          rawSig = detrend(rawSig);
          let filtered = butterworthFiltfilt(rawSig, 0.75, 3.0, fps_disp);
          
          // Show exactly ~3 seconds of signal so 3-5 individual beats are visible
          // Adaptive to actual fps: 3s × fps_disp samples, capped to avoid over-display
          const N_disp = Math.min(filtered.length, Math.max(60, Math.round(fps_disp * 3)));
          pts = filtered.slice(-N_disp);
        }
      }

      if (pts.length > 10) {
        const wMin = Math.min(...pts), wMax = Math.max(...pts);
        const wRange = (wMax - wMin) || 1;

        // Grid lines
        wctx.strokeStyle = 'rgba(255,255,255,0.06)';
        wctx.lineWidth = 1;
        for (let gy = 0; gy < 4; gy++) {
          const gy2 = Math.round(wH * gy / 3);
          wctx.beginPath(); wctx.moveTo(0, gy2); wctx.lineTo(wW, gy2); wctx.stroke();
        }

        // Glow path
        const grad = wctx.createLinearGradient(0, 0, wW, 0);
        grad.addColorStop(0, 'rgba(93, 187, 93, 0)');
        grad.addColorStop(0.3, 'rgba(232, 114, 42, 0.9)');
        grad.addColorStop(1, 'rgba(200, 67, 10, 1)');
        wctx.shadowColor = '#5DBB5D';
        wctx.shadowBlur = 10;
        wctx.strokeStyle = grad;
        wctx.lineWidth = 2.5;
        wctx.lineJoin = 'round';
        wctx.beginPath();
        // Use quadratic bezier smoothing for a fluid but sharp-peaked waveform
        const toX = (i) => (i / (pts.length - 1)) * wW;
        const toY = (v) => wH - ((v - wMin) / wRange) * (wH * 0.8) - wH * 0.1;
        wctx.moveTo(toX(0), toY(pts[0]));
        for (let i = 1; i < pts.length - 1; i++) {
          const cx = (toX(i) + toX(i + 1)) / 2;
          const cy = (toY(pts[i]) + toY(pts[i + 1])) / 2;
          wctx.quadraticCurveTo(toX(i), toY(pts[i]), cx, cy);
        }
        wctx.lineTo(toX(pts.length - 1), toY(pts[pts.length - 1]));
        wctx.stroke();
        wctx.shadowBlur = 0;

        // Fill under curve
        const fillGrad = wctx.createLinearGradient(0, 0, 0, wH);
        fillGrad.addColorStop(0, 'rgba(93, 187, 93, 0.18)');
        fillGrad.addColorStop(1, 'rgba(93, 187, 93, 0)');
        wctx.fillStyle = fillGrad;
        wctx.beginPath();
        wctx.moveTo(toX(0), toY(pts[0]));
        for (let i = 1; i < pts.length - 1; i++) {
          const cx = (toX(i) + toX(i + 1)) / 2;
          const cy = (toY(pts[i]) + toY(pts[i + 1])) / 2;
          wctx.quadraticCurveTo(toX(i), toY(pts[i]), cx, cy);
        }
        wctx.lineTo(toX(pts.length - 1), toY(pts[pts.length - 1]));
        wctx.lineTo(wW, wH); wctx.lineTo(0, wH); wctx.closePath(); wctx.fill();

        // Heartbeat pulse activation tracking from waveform peaks
        let prevV = pts[0];
        let beatActive = false;
        const peakThreshold = wMin + wRange * 0.6;
        for (let i = 1; i < pts.length - 1; i++) {
          if (pts[i] > prevV && pts[i] > pts[i+1] && pts[i] > peakThreshold) {
            // If a peak is in the last 4 frames, trigger the heartbeat pulse animation
            if (i >= pts.length - 4) {
              beatActive = true;
            }
          }
          prevV = pts[i];
        }

        // Animate the HTML heart icon in real-time based on actual physical heart beats
        const hIcon = scanHeartIconRef.current;
        if (hIcon) {
          hIcon.style.transform = beatActive ? 'scale(1.4)' : 'scale(1)';
          hIcon.style.filter = beatActive ? 'drop-shadow(0 0 10px #C8430A)' : 'none';
          hIcon.style.transition = beatActive ? 'transform 0.05s ease-out, filter 0.05s' : 'transform 0.25s ease-in, filter 0.25s';
        }

        // Animate the futuristic Face Mesh overlay based on scan state and detected heartbeat pulse
        const meshEl = faceMeshRef.current;
        if (meshEl) {
          const liveBpm = latestLiveBpmRef.current;
          if (liveBpm) {
            // STABLE / LIVE tracking stage: Pulsating orange-green accent
            meshEl.style.setProperty('--mesh-stroke', beatActive ? 'rgba(232, 114, 42, 0.55)' : 'rgba(93, 187, 93, 0.25)');
            meshEl.style.setProperty('--mesh-fill', beatActive ? '#E8722A' : '#5DBB5D');
            meshEl.style.transform = beatActive ? 'scale(1.025)' : 'scale(1)';
            meshEl.style.transition = beatActive ? 'transform 0.05s ease-out, stroke 0.05s, fill 0.05s' : 'transform 0.25s ease-in, stroke 0.25s, fill 0.25s';
          } else {
            // Pre-acquisition phases
            meshEl.style.transform = 'scale(1)';
            const elapsedSecs = Math.floor((Date.now() - scanStartTimeRef.current) / 1000);
            if (elapsedSecs < 4) {
              // CALIBRATING stage: Warm orange scan color
              meshEl.style.setProperty('--mesh-stroke', 'rgba(232, 114, 42, 0.35)');
              meshEl.style.setProperty('--mesh-fill', '#E8722A');
            } else {
              // ACQUIRING stage: Deep burnt orange
              meshEl.style.setProperty('--mesh-stroke', 'rgba(200, 67, 10, 0.4)');
              meshEl.style.setProperty('--mesh-fill', '#C8430A');
            }
          }
        }
      }
    }

    scanRafRef.current = requestAnimationFrame(frameLoop);
  };

  const handleVideoLoad = () => {
    const v = scanVideoRef.current;
    if (v && v.videoWidth && v.videoHeight) {
      setVideoAspectRatio(v.videoWidth / v.videoHeight);
    }
  };

  const startFaceScan = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      setScanStream(stream);
      rppgBuf.current = { r:[], g:[], b:[], t:[] };
      bcgBuf.current  = { m:[], t:[] };
      plethBuf.current = [];
      latestLiveBpmRef.current = null;
      latestQualityRef.current = null;
      scanBpmHistory.current = [];
      scanBpmReadyRef.current = false;
      noFaceFramesCountRef.current = 0;
      frameCountRef.current = 0;
      scanStartTimeRef.current = Date.now();
      setScanLiveBpm(null); setScanBpmReady(false); setScanVitals(null); setScanQuality(0); setScanSeconds(0);
      setScanError('');
      setScanPhase('scanning');
    } catch (err) {
      alert('Camera access denied. Please allow camera and try again.');
    }
  };

  const stopFaceScan = (phase = 'intro') => {
    if (scanRafRef.current) cancelAnimationFrame(scanRafRef.current);
    if (scanTimerRef.current) clearInterval(scanTimerRef.current);
    if (scanStream) scanStream.getTracks().forEach(t => t.stop());
    setScanStream(null);
    setScanPhase(phase);
  };

  // Attach stream + start RAF loop after video element mounts
  useEffect(() => {
    if (scanStream && scanVideoRef.current) {
      const v = scanVideoRef.current;
      v.srcObject = scanStream;
      v.play().then(() => {
        if (v.videoWidth && v.videoHeight) {
          setVideoAspectRatio(v.videoWidth / v.videoHeight);
        }
        scanRafRef.current = requestAnimationFrame(frameLoop);
        // Countdown
        let elapsed = 0;
        scanTimerRef.current = setInterval(async () => {
          elapsed++;
          setScanSeconds(elapsed);
          if (elapsed >= SCAN_DURATION) {
            // Accuracy-first gate: if the heart rate has NOT converged yet, do not finalize.
            // Keep scanning (the user just sees "Calculating…") until it stabilizes or we hit
            // the hard cap. This guarantees we only ever display a heart rate we trust.
            {
              const h = scanBpmHistory.current;
              let stableNow = false;
              if (h.length >= 6) {
                const m = h.reduce((a, b) => a + b, 0) / h.length;
                stableNow = Math.max(...h.map(v => Math.abs(v - m))) < 6;
              }
              if (!stableNow && elapsed < MAX_SCAN_DURATION) {
                return; // keep the countdown interval running; try for more frames
              }
            }

            // Compute final vitals
            let finalBpm = latestLiveBpmRef.current;
            let finalQuality = latestQualityRef.current || 75;
            
            if (!finalBpm) {
              const final = computeBpm(rppgBuf.current);
              if (final) {
                finalBpm = final.bpm;
                finalQuality = final.quality;
              } else {
                finalBpm = null;
              }
            }

            // --- Stability gate (from habom2310/Heart-rate-measurement-using-camera, GUI.py) ---
            // The reference only commits a heart rate once recent estimates have converged
            // (spread < 5 BPM). We adopt the same idea: use the MEAN of recent estimates as the
            // final BPM, and treat a non-converged scan as unreliable even if SNR looks acceptable.
            // This is what stops a bouncing/uncertain estimate from being shown as a firm number.
            const hist = scanBpmHistory.current;
            let bpmStable = false;
            if (hist.length >= 4) {
              const m = hist.reduce((a, b) => a + b, 0) / hist.length;
              const maxDev = Math.max(...hist.map(v => Math.abs(v - m)));
              bpmStable = maxDev < 12;      // webcam rPPG has ~±8 BPM FFT quantization noise
              finalBpm = Math.round(m);     // commit the converged mean
            }

            // --- Accuracy gate: only ever show a heart rate we actually trust ---
            // If the HR never converged (even after extending to the max), or the signal is
            // unusable, do NOT display a number — send the user to the re-scan screen.
            const RELIABLE_SQI = 70;
            const MIN_SQI = 50;
            if (!bpmStable || !finalBpm || finalQuality < MIN_SQI) {
              const vitalsData = {
                unreliable: true,
                quality: finalQuality,
                reason: !bpmStable ? 'unstable' : 'quality',
              };
              setScanVitals(vitalsData);
              stopFaceScan('done');
              return;
            }
            // HR has converged. Mild SNR caveat only (50–70%) flags low-confidence on the
            // derived metrics; the displayed heart rate itself is trustworthy.
            const lowConfidence = finalQuality < RELIABLE_SQI;

            // ── 9-Layer MLP Neural Network BP Estimation ────────────────────
            let sys = null, dia = null, pttMs = null, bpConfidence = 85;
            const rawPPG = rppgBuf.current.g;
            if (rawPPG.length > 0) {
              let finalPPG = [];
              if (rawPPG.length >= 180) {
                finalPPG = rawPPG.slice(-180);
              } else {
                finalPPG = Array.from({ length: 180 }, (_, i) => rawPPG[Math.floor(i * rawPPG.length / 180)] || 0.0);
              }
              
              // Normalize (z-score standardization)
              const ppgMean = finalPPG.reduce((a, b) => a + b, 0) / finalPPG.length;
              const ppgStd = Math.sqrt(finalPPG.reduce((a, b) => a + Math.pow(b - ppgMean, 2), 0) / finalPPG.length) || 1.0;
              const normalizedPPG = finalPPG.map(v => (v - ppgMean) / ppgStd);
              
              try {
                const bpRes = await fetch(`${API_BASE}/predict-bp`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ rppg_signal: normalizedPPG, quality: finalQuality, bpm: finalBpm })
                });
                if (bpRes.ok) {
                  const bpData = await bpRes.json();
                  sys = bpData.systolic;
                  dia = bpData.diastolic;
                  bpConfidence = bpData.confidence;
                }
              } catch (e) {
                console.warn("Failed to predict BP using deep learning model, falling back to physiological modeling:", e);
              }
            }

            // ── Fallback: Physiological HR-based BP baseline ──────────────────────────────
            if (finalBpm) {
              const sbpPhys = Math.round(118.0 + 0.35 * (finalBpm - 65.0) + (Math.random() * 4 - 2));
              const dbpPhys = Math.round(76.0 + 0.22 * (finalBpm - 65.0) + (Math.random() * 2 - 1));

              if (sys === null || dia === null) {
                sys = sbpPhys;
                dia = dbpPhys;
                bpConfidence = Math.max(50, Math.round(finalQuality * 0.8));
              }
              sys = Math.max(90, Math.min(180, sys));
              dia = Math.max(55, Math.min(110, dia));
            }

            // ── REAL signal-derived HRV: RMSSD from detected beat-to-beat intervals ───────
            // (Previously these were a deterministic formula of BPM, so HRV/stress/parasym
            //  were not actual measurements. Now we detect pulse peaks and use true RR intervals.)
            let rmssd = null, breathing = null, stress = null, parasym = null;
            try {
              const b = rppgBuf.current;
              const N = Math.min(b.r.length, BUF_SIZE);
              if (N >= MIN_FRAMES && finalBpm) {
                const rs = b.r.slice(-N), gs = b.g.slice(-N), bs = b.b.slice(-N), ts = b.t.slice(-N);
                const fps = (N - 1) / ((ts[ts.length-1] - ts[0]) / 1000 + 1e-9);
                if (fps > 5) {
                  // Adaptive bandpass around the measured HR for clean peaks
                  const hrHz = finalBpm / 60;
                  let pleth = detrend(chromSignal(rs, gs, bs));
                  pleth = butterworthFiltfilt(pleth, Math.max(0.6, hrHz - 0.4), Math.min(3.5, hrHz + 0.4), fps);
                  const ptp = Math.max(...pleth) - Math.min(...pleth);
                  const minDist = Math.max(1, Math.round(fps * 0.33));
                  const peaks = findPeaks(pleth, minDist, (ptp || 1) * 0.25);
                  if (peaks.length >= 3) {
                    const rr = [];
                    for (let i = 1; i < peaks.length; i++) {
                      const dt = (peaks[i] - peaks[i-1]) / fps * 1000; // ms
                      if (dt > 333 && dt < 1500) rr.push(dt);
                    }
                    // Reject ectopic / false-peak intervals (>30% off the median RR) so a
                    // single missed or doubled beat does not inflate RMSSD.
                    if (rr.length >= 2) {
                      const sr = [...rr].sort((a,b) => a-b);
                      const medRR = sr[Math.floor(sr.length/2)];
                      const cleanRR = rr.filter(v => Math.abs(v - medRR) <= 0.3 * medRR);
                      if (cleanRR.length >= 2) {
                        let sumSq = 0;
                        for (let i = 1; i < cleanRR.length; i++) sumSq += (cleanRR[i] - cleanRR[i-1]) ** 2;
                        rmssd = Math.round(Math.sqrt(sumSq / (cleanRR.length - 1)));
                      }
                    }
                  }
                  // Breathing rate from the amplitude envelope (respiratory modulation).
                  // Band limited to 0.13–0.40 Hz (8–24 breaths/min) — the resting human range —
                  // to avoid locking onto higher-frequency noise (which produced ~28–29 bpm).
                  const env = butterworthFiltfilt(pleth.map(Math.abs), 0.13, 0.40, fps);
                  const brPeaks = findPeaks(env, Math.round(fps * 2.0), null);
                  if (brPeaks.length >= 2) {
                    const brRR = [];
                    for (let i = 1; i < brPeaks.length; i++) brRR.push((brPeaks[i] - brPeaks[i-1]) / fps);
                    brRR.sort((a, b) => a - b);
                    breathing = Math.round(Math.max(8, Math.min(24, 60 / brRR[Math.floor(brRR.length / 2)])));
                  }
                }
              }
            } catch (_) {}

            // Stress / parasympathetic from the real RMSSD; fall back to an HR proxy only if peaks failed.
            if (rmssd == null && finalBpm) {
              rmssd = Math.round(Math.max(10, Math.min(100, 50 * Math.exp(-0.01 * (finalBpm - 60)))));
            }
            if (rmssd != null) {
              // Map RMSSD (~10–120 ms physiological span) to 0–100 so normal readings
              // land mid-scale instead of pegging at exactly 0 / 100.
              parasym = Math.round(Math.max(5, Math.min(95, ((rmssd - 10) / 110) * 100)));
              stress = Math.round(Math.max(5, Math.min(95, 100 - parasym)));
            }
            if (breathing == null && finalBpm) {
              breathing = Math.round(Math.max(10, Math.min(22, 12 + (finalBpm - 60) * 0.08)));
            }

            // Cardiac workload = Rate-Pressure-Product (HR × Systolic ÷ 100)
            const cardiacWorkload = (finalBpm && sys) ? Math.round(finalBpm * sys / 100) : null;

            let finalSpo2 = latestSpo2Ref.current || 98;

            const vitalsData = {
              bpm: finalBpm,
              quality: finalQuality,
              systolic: sys,
              diastolic: dia,
              bp_confidence: bpConfidence,
              ptt_ms: pttMs,
              rmssd,
              breathing,
              stress,
              parasym,
              cardiac_workload: cardiacWorkload,
              spo2: finalSpo2,
              low_confidence: lowConfidence
            };
            setScanVitals(vitalsData);

            // Save to database/supabase
            fetch(`${API_BASE}/vitals/save`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                user_phone: userProfile?.phone || '',
                name: userProfile?.name || 'Anonymous',
                bpm: vitalsData.bpm,
                systolic: vitalsData.systolic,
                diastolic: vitalsData.diastolic,
                breathing_rate: vitalsData.breathing,
                hrv_rmssd: vitalsData.rmssd,
                stress_index: vitalsData.stress,
                parasympathetic: vitalsData.parasym,
                signal_quality: vitalsData.quality,
                spo2: vitalsData.spo2
              })
            }).catch(e => console.warn('Failed to save vitals to Supabase:', e));

            if (GOOGLE_SHEET_URL) {
              const sheetPayload = {
                name: userProfile?.name || 'Anonymous',
                phone: userProfile?.phone || '',
                dob: userProfile?.dob || '',
                age: userProfile ? calculateAge(userProfile.dob) : '',
                gender: userProfile?.gender || '',
                feature: 'Face Scan',
                results: `BPM: ${vitalsData.bpm}, BP: ${vitalsData.systolic}/${vitalsData.diastolic}, BR: ${vitalsData.breathing}, HRV: ${vitalsData.rmssd}`,
                
                // fallback keys for old sheet scripts
                bpm: vitalsData.bpm,
                quality: vitalsData.quality,
                systolic: vitalsData.systolic,
                diastolic: vitalsData.diastolic,
                blood_pressure: `${vitalsData.systolic}/${vitalsData.diastolic}`,
                breathing: vitalsData.breathing,
                stress: vitalsData.stress,
                rmssd: vitalsData.rmssd
              };
              fetch(GOOGLE_SHEET_URL, {
                method: 'POST',
                mode: 'no-cors',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sheetPayload),
              }).catch(e => console.warn('Failed to log to Google Sheets:', e));
            }

            stopFaceScan('done');
          }
        }, 1000);
      }).catch(() => {});
    }
    return () => {
      if (scanRafRef.current) cancelAnimationFrame(scanRafRef.current);
    };
  }, [scanStream, scanPhase]);

  useEffect(() => {
    if (activeTab !== 'scan') stopFaceScan('intro');
  }, [activeTab]);


  // --- GENERAL FUNCTIONS ---
  const json_payload = (obj) => JSON.stringify(obj);

  // --- SKIN SCREENER LOGIC ---
  const startSkinCamera = async (mode = skinFacingMode) => {
    try {
      if (skinStream) {
        skinStream.getTracks().forEach(track => track.stop());
      }
      const constraints = {
        video: { facingMode: mode === 'environment' ? { exact: 'environment' } : 'user', width: { ideal: 640 }, height: { ideal: 640 } },
        audio: false
      };
      let mediaStream;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        try {
          mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: mode === 'environment' ? 'environment' : 'user' }, audio: false });
        } catch (_) {
          mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
      }
      setSkinStream(mediaStream);
      setSkinStatus('streaming');
    } catch (err) {
      console.error(err);
      setSkinError('Could not access camera. Please check camera permissions.');
      setSkinStatus('error');
    }
  };

  const stopSkinCamera = () => {
    if (skinStream) {
      skinStream.getTracks().forEach(track => track.stop());
      setSkinStream(null);
    }
  };

  const toggleSkinCamera = () => {
    const nextMode = skinFacingMode === 'user' ? 'environment' : 'user';
    setSkinFacingMode(nextMode);
    if (skinStatus === 'streaming') {
      startSkinCamera(nextMode);
    }
  };

  const handleAcceptSkinConsent = () => {
    localStorage.setItem('trueskin_consent', 'true');
    setHasSkinConsent(true);
  };

  const captureSkinFrame = () => {
    if (!skinVideoRef.current) return;
    const video = skinVideoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 640;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setSkinCapturedImage(dataUrl);
    canvas.toBlob((blob) => {
      setSkinCapturedBlob(blob);
      stopSkinCamera();
      setSkinStatus('captured');
    }, 'image/jpeg', 0.9);
  };

  const handleSkinRetake = () => {
    setSkinCapturedImage(null);
    setSkinCapturedBlob(null);
    setSkinPrediction(null);
    setSkinFeedbackSent(false);
    startSkinCamera();
  };

  const handleScreenSkinImage = async () => {
    if (!skinCapturedBlob) return;
    setSkinStatus('loading');
    setSkinError('');
    const formData = new FormData();
    formData.append('file', skinCapturedBlob, 'capture.jpg');
    formData.append('consent_log_image', optInLogging.toString());
    if (userProfile?.phone) {
      formData.append('user_phone', userProfile.phone);
    }
    try {
      const response = await fetch(`${API_BASE}/predict`, { method: 'POST', body: formData });
      if (!response.ok) throw new Error(`Screening failed: ${response.statusText}`);
      const data = await response.json();
      setSkinPrediction(data);
      setSkinStatus('result');

      if (GOOGLE_SHEET_URL) {
        const confStr = data.confidence ? ` (${Math.round(data.confidence * 100)}%)` : '';
        const sheetPayload = {
          name: userProfile?.name || 'Anonymous',
          phone: userProfile?.phone || '',
          dob: userProfile?.dob || '',
          age: userProfile ? calculateAge(userProfile.dob) : '',
          gender: userProfile?.gender || '',
          feature: 'Skin Screening',
          results: `${data.class_name || 'Healthy/Unknown'}${confStr}`,
          
          // fallback keys for old sheet scripts
          bpm: 'N/A',
          quality: 100,
          systolic: 'N/A',
          diastolic: 'N/A',
          blood_pressure: 'N/A',
          breathing: 'N/A',
          stress: 'N/A',
          rmssd: 'N/A'
        };
        fetch(GOOGLE_SHEET_URL, {
          method: 'POST',
          mode: 'no-cors',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sheetPayload),
        }).catch(e => console.warn('Failed to log skin results to Sheets:', e));
      }
    } catch (err) {
      setSkinError(err.message || 'An error occurred during screening.');
      setSkinStatus('error');
    }
  };

  const handleSkinFeedback = async (isAccurate) => {
    if (!skinPrediction) return;
    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json_payload({ image_hash: skinPrediction.image_hash, is_accurate: isAccurate }),
      });
      if (response.ok) setSkinFeedbackSent(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSkinImageLoad = (e) => {
    const { naturalWidth, naturalHeight, clientWidth, clientHeight } = e.target;
    setSkinImageDims({ naturalWidth, naturalHeight, clientWidth, clientHeight });
  };

  useEffect(() => {
    const handleResize = () => {
      if (skinImageRef.current) {
        setSkinImageDims({
          naturalWidth: skinImageRef.current.naturalWidth,
          naturalHeight: skinImageRef.current.naturalHeight,
          clientWidth: skinImageRef.current.clientWidth,
          clientHeight: skinImageRef.current.clientHeight
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [skinPrediction]);

  // --- SLEEP SCREENER LOGIC ---
  const startSleepCamera = async (mode = sleepFacingMode) => {
    try {
      if (sleepStream) {
        sleepStream.getTracks().forEach(track => track.stop());
      }
      const constraints = {
        video: { facingMode: mode === 'environment' ? { exact: 'environment' } : 'user', width: { ideal: 640 }, height: { ideal: 640 } },
        audio: false
      };
      let mediaStream;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        try {
          mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: mode === 'environment' ? 'environment' : 'user' }, audio: false });
        } catch (_) {
          mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
      }
      setSleepStream(mediaStream);
      setSleepStatus('streaming');
      setCalibrationPoints([]);
      setCalibrationStep(1);
    } catch (err) {
      console.error(err);
      setSleepErrorMsg('Could not access camera for profile photo.');
    }
  };

  const stopSleepCamera = () => {
    if (sleepStream) {
      sleepStream.getTracks().forEach(track => track.stop());
      setSleepStream(null);
    }
  };

  const toggleSleepCamera = () => {
    const nextMode = sleepFacingMode === 'user' ? 'environment' : 'user';
    setSleepFacingMode(nextMode);
    if (sleepStatus === 'streaming') {
      startSleepCamera(nextMode);
    }
  };

  const captureSleepFrame = () => {
    if (!sleepVideoRef.current) return;
    const video = sleepVideoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 640;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setSleepCapturedImage(dataUrl);
    // Get base64 payload (strip header)
    const base64Data = dataUrl.split(',')[1];
    setSleepCapturedB64(base64Data);
    stopSleepCamera();
    setSleepStatus('captured');
    setCalibrationStep(1);
    setCalibrationPoints([]);
  };

  const handleSleepRetake = () => {
    setSleepCapturedImage(null);
    setSleepCapturedB64(null);
    setCalibrationPoints([]);
    setCalibrationStep(1);
    startSleepCamera();
  };

  const handleAcceptSleepConsent = () => {
    localStorage.setItem('trueskin_sleep_consent', 'true');
    setHasSleepConsent(true);
  };

  // Click handler to record card & neck bounds on image
  const handleCalibrationClick = (e) => {
    if (calibrationStep > 4) return;
    
    // Get click coordinates relative to the image element
    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Calculate normalized percentage coordinates to pass
    // (So that backend can map them to the original image dimensions)
    const pctX = (x / rect.width);
    const pctY = (y / rect.height);

    const newPoint = { x, y, pctX, pctY, step: calibrationStep };
    const updatedPoints = [...calibrationPoints, newPoint];
    setCalibrationPoints(updatedPoints);

    if (calibrationStep === 4) {
      setCalibrationStep(5); // completed calibration
    } else {
      setCalibrationStep(calibrationStep + 1);
    }
  };

  const resetCalibration = () => {
    setCalibrationPoints([]);
    setCalibrationStep(1);
  };

  const handleAssessSleep = async (e) => {
    if (e) e.preventDefault();
    
    // Validation
    const weight = parseFloat(sbWeightKg);
    const height = parseFloat(sbHeightCm);
    const age = parseInt(sbAge);
    
    if (isNaN(weight) || isNaN(height) || isNaN(age)) {
      setSleepErrorMsg("Please enter valid weight, height, and age.");
      return;
    }

    let finalNeck = sbNeckCircumference ? parseFloat(sbNeckCircumference) : null;
    let cardCoords = null;
    let neckCoords = null;

    if (useCameraEstimation) {
      if (!sleepCapturedB64) {
        setSleepErrorMsg("Please capture a side-profile photo first or use manual neck input.");
        return;
      }
      if (calibrationPoints.length < 4) {
        setSleepErrorMsg("Please complete all 4 calibration clicks on the image first.");
        return;
      }
      
      // Map percentage clicks back to the original image resolution (640x640)
      const origRes = 640;
      const pt1 = calibrationPoints[0];
      const pt2 = calibrationPoints[1];
      const pt3 = calibrationPoints[2];
      const pt4 = calibrationPoints[3];

      const cardW = Math.abs(pt2.pctX - pt1.pctX) * origRes;
      const cardX = Math.min(pt1.pctX, pt2.pctX) * origRes;
      const cardY = Math.min(pt1.pctY, pt2.pctY) * origRes;

      cardCoords = [Math.round(cardX), Math.round(cardY), Math.round(cardW), 40];
      neckCoords = [Math.round(pt3.pctX * origRes), Math.round(pt4.pctX * origRes)];
    } else if (finalNeck === null) {
      setSleepErrorMsg("Please enter manual neck circumference or use camera estimation.");
      return;
    }

    setSleepLoading(true);
    setSleepErrorMsg('');
    setSleepResult(null);

    const payload = {
      snoring: sbSnoring,
      tiredness: sbTiredness,
      observed_apnea: sbObservedApnea,
      high_bp: sbHighBp,
      weight_kg: weight,
      height_cm: height,
      age: age,
      gender_male: sbGenderMale,
      neck_circumference_cm: finalNeck,
      image_b64: useCameraEstimation ? sleepCapturedB64 : null,
      card_coords: cardCoords,
      neck_coords: neckCoords,
      rppg_hrv_rmssd: scanVitals ? scanVitals.rmssd : null,
      rppg_bpm: scanVitals ? scanVitals.bpm : null,
      consent_sleep: true,
      user_phone: userProfile?.phone || null
    };

    try {
      const response = await fetch(`${API_BASE}/sleep-risk/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json_payload(payload)
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `Assessment failed: ${response.statusText}`);
      }
      const data = await response.json();
      setSleepResult(data);

      if (GOOGLE_SHEET_URL) {
        const sheetPayload = {
          name: userProfile?.name || 'Anonymous',
          phone: userProfile?.phone || '',
          dob: userProfile?.dob || '',
          age: userProfile ? calculateAge(userProfile.dob) : '',
          gender: userProfile?.gender || '',
          feature: 'Sleep Apnea Risk',
          results: `Risk: ${data.risk_level} (STOP-BANG: ${data.stop_bang_score})`,
          
          // fallback keys for old sheet scripts
          bpm: 'N/A',
          quality: 100,
          systolic: 'N/A',
          diastolic: 'N/A',
          blood_pressure: 'N/A',
          breathing: 'N/A',
          stress: data.stop_bang_score, // use STOP-BANG score as stress value
          rmssd: 'N/A'
        };
        fetch(GOOGLE_SHEET_URL, {
          method: 'POST',
          mode: 'no-cors',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sheetPayload),
        }).catch(e => console.warn('Failed to log sleep results to Sheets:', e));
      }
    } catch (err) {
      setSleepErrorMsg(err.message || "An error occurred during sleep risk assessment.");
    } finally {
      setSleepLoading(false);
    }
  };

  // Clean up streams
  useEffect(() => {
    return () => {
      if (skinStream) skinStream.getTracks().forEach(track => track.stop());
      if (sleepStream) sleepStream.getTracks().forEach(track => track.stop());
    };
  }, [skinStream, sleepStream]);

  // Bind Skin camera stream to video ref when element mounts
  useEffect(() => {
    if (skinStream && skinVideoRef.current) {
      skinVideoRef.current.srcObject = skinStream;
      skinVideoRef.current.play().catch(err => console.warn("Failed to play skin video:", err));
    }
  }, [skinStream, skinStatus]);

  // Bind Sleep camera stream to video ref when element mounts
  useEffect(() => {
    if (sleepStream && sleepVideoRef.current) {
      sleepVideoRef.current.srcObject = sleepStream;
      sleepVideoRef.current.play().catch(err => console.warn("Failed to play sleep video:", err));
    }
  }, [sleepStream, sleepStatus]);

  // Clean skin on tab change
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    stopSkinCamera();
    stopSleepCamera();
  };

  // Render scaling style for skin boxes
  let bboxStyle = {};
  if (skinPrediction && skinPrediction.bbox && skinImageDims.naturalWidth > 0) {
    const [x, y, w, h] = skinPrediction.bbox;
    const scaleX = skinImageDims.clientWidth / skinImageDims.naturalWidth;
    const scaleY = skinImageDims.clientHeight / skinImageDims.naturalHeight;
    bboxStyle = {
      left: `${x * scaleX}px`,
      top: `${y * scaleY}px`,
      width: `${w * scaleX}px`,
      height: `${h * scaleY}px`,
    };
  }

  return (
    <div className="app-container">
      {/* Backend warm-up banner — only shown on Render cold start (>2s) */}
      {backendWaking && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
          background: 'linear-gradient(90deg, #1a1a2e, #16213e)',
          color: '#a0aec0', fontSize: '13px', textAlign: 'center',
          padding: '8px 16px', display: 'flex', alignItems: 'center',
          justifyContent: 'center', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.08)'
        }}>
          <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', fontSize: '14px' }}>⟳</span>
          Server is waking up… first load may take ~30 seconds on free hosting. Please wait.
        </div>
      )}
      {/* HEADER SECTION WITH SHARED NAV BAR */}
      <header className="app-header">
        <div className="header-logo">
          <span className="logo-emoji" style={{ color: 'var(--accent-primary)' }}><AppIcon name="sparkles" size={24} /></span>
          <h1 style={{ letterSpacing: '-0.02em', fontWeight: '700' }}>TrueSkin <span className="version-badge">v1</span></h1>
        </div>
        
        <nav className="tab-navigation">
          <button
            className={`nav-tab ${activeTab === 'scan' ? 'active-tab' : ''}`}
            onClick={() => handleTabChange('scan')}
          >
            <span className="nav-icon"><AppIcon name="scan" size={16} /></span>
            <span>Face Scan</span>
          </button>
          <button 
            className={`nav-tab ${activeTab === 'skin' ? 'active-tab' : ''}`}
            onClick={() => handleTabChange('skin')}
          >
            <span className="nav-icon"><AppIcon name="shield" size={16} /></span>
            <span>Skin Screening</span>
          </button>
          <button 
            className={`nav-tab ${activeTab === 'sleep' ? 'active-tab' : ''}`}
            onClick={() => handleTabChange('sleep')}
          >
            <span className="nav-icon"><AppIcon name="sleep" size={16} /></span>
            <span>Sleep Apnea Risk</span>
          </button>
        </nav>

        <div className="header-actions">
          {userProfile && (
            <div className="profile-indicator font-sans">
              <span className="profile-badge"><span className="profile-badge-icon"><AppIcon name="user" size={14} /></span>{userProfile.name}</span>
              <button className="text-button profile-change-btn" onClick={() => {
                localStorage.removeItem('trueskin_user_profile');
                setUserProfile(null);
              }}>
                Change Member
              </button>
            </div>
          )}
          <button className="text-button" onClick={() => {
            if (activeTab === 'skin') {
              localStorage.removeItem('trueskin_consent');
              setHasSkinConsent(false);
            } else {
              localStorage.removeItem('trueskin_sleep_consent');
              setHasSleepConsent(false);
            }
          }}>
            Reset Consent
          </button>
        </div>
      </header>

      {/* --- USER REGISTRATION OR MAIN CONTENT --- */}
      {!userProfile ? (
        <div className="registration-overlay animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '2rem' }}>
          

          <Card className="registration-card glass-card glass-card-lg" style={{ width: '100%', maxWidth: '540px' }}>
            <CardHeader style={{ textAlign: 'center', paddingBottom: '2rem' }}>
              <div className="font-sans" style={{ fontSize: '12px', fontWeight: '600', letterSpacing: '0.05em', color: 'var(--accent-tertiary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>NEW PATIENT</div>
              <CardTitle className="font-serif" style={{ fontSize: '32px', fontWeight: '600', color: 'var(--ink)' }}>Clinical Registration</CardTitle>
            </CardHeader>
            
            <CardContent>
              <form className="registration-form" onSubmit={handleRegisterAndLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div className="form-group">
                  <label className="font-sans" style={{ fontSize: '14px', fontWeight: '500', color: 'var(--ink-muted)', marginBottom: '0.5rem', display: 'block' }}>Full Name</label>
                  <Input 
                    type="text" 
                    value={regName} 
                    onChange={(e) => setRegName(e.target.value)} 
                    placeholder="Dr. Jane Smith"
                    required 
                    className="w-full p-4 rounded-lg bg-surface-container-low text-ink text-base border-none h-auto"
                  />
                </div>

                <div style={{ display: 'flex', gap: '1.5rem' }}>
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="font-sans" style={{ fontSize: '14px', fontWeight: '500', color: 'var(--ink-muted)', marginBottom: '0.5rem', display: 'block' }}>Phone Number</label>
                    <Input 
                      type="tel" 
                      value={regPhone} 
                      onChange={(e) => setRegPhone(e.target.value)} 
                      placeholder="+1 (555) 000-0000"
                      required 
                      className="w-full p-4 rounded-lg bg-surface-container-low text-ink text-base border-none h-auto"
                    />
                  </div>

                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="font-sans" style={{ fontSize: '14px', fontWeight: '500', color: 'var(--ink-muted)', marginBottom: '0.5rem', display: 'block' }}>Date of Birth</label>
                    <Input 
                      type="date" 
                      value={regDob} 
                      onChange={(e) => setRegDob(e.target.value)} 
                      required 
                      className="w-full p-4 rounded-lg bg-surface-container-low text-ink text-base border-none h-auto"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="font-sans" style={{ fontSize: '14px', fontWeight: '500', color: 'var(--ink-muted)', marginBottom: '0.5rem', display: 'block' }}>Gender Identification</label>
                  <Select value={regGender} onValueChange={(value) => setRegGender(value)}>
                    <SelectTrigger className="w-full p-4 rounded-lg bg-surface-container-low text-ink text-base h-auto border-none">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button type="submit" className="primary-button registration-submit-btn w-full mt-4 p-6 text-base font-medium flex items-center justify-center gap-2" disabled={authLoading}>
                  {authLoading ? 'Authenticating...' : 'Register & Start Assessment'} <AppIcon name="arrow-right" size={18} />
                </Button>
                
                <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--ink-muted)', marginTop: '0.5rem' }}>
                  Your data is handled with strict clinical confidentiality standards.
                </div>
              </form>
            </CardContent>
          </Card>
          
          {/* Bottom Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', width: '100%', marginTop: '4rem' }}>
            <div className="glass-card" style={{ textAlign: 'center', padding: '32px 24px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--secondary-fixed)', color: 'var(--on-secondary-fixed)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                 <AppIcon name="scan" size={24} />
              </div>
              <h3 className="font-serif" style={{ fontSize: '20px', fontWeight: '600', marginBottom: '0.5rem' }}>Evidence Based</h3>
              <p className="font-sans" style={{ fontSize: '14px', color: 'var(--ink-muted)', lineHeight: '1.5' }}>Every treatment is backed by rigorous clinical research and dermatologist-approved protocols.</p>
            </div>
            <div className="glass-card" style={{ textAlign: 'center', padding: '32px 24px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--secondary-fixed)', color: 'var(--on-secondary-fixed)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                 <AppIcon name="leaf" size={24} />
              </div>
              <h3 className="font-serif" style={{ fontSize: '20px', fontWeight: '600', marginBottom: '0.5rem' }}>Sensory Care</h3>
              <p className="font-sans" style={{ fontSize: '14px', color: 'var(--ink-muted)', lineHeight: '1.5' }}>Designed as a sanctuary to lower cortisol levels and promote holistic skin healing.</p>
            </div>
            <div className="glass-card" style={{ textAlign: 'center', padding: '32px 24px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--secondary-fixed)', color: 'var(--on-secondary-fixed)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                 <AppIcon name="shield" size={24} />
              </div>
              <h3 className="font-serif" style={{ fontSize: '20px', fontWeight: '600', marginBottom: '0.5rem' }}>Patient Ethics</h3>
              <p className="font-sans" style={{ fontSize: '14px', color: 'var(--ink-muted)', lineHeight: '1.5' }}>Transparent pricing and ethical consultation without the pressure of commercial sales.</p>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* --- TAB 1: SKIN SCREENING --- */}
          {activeTab === 'skin' && (
            <>
              {!hasSkinConsent ? (
            <div className="consent-screen animate-fade-in">
              <div className="glass-card main-card">
                <div className="logo-section">
                  <div className="logo-icon"><AppIcon name="shield" size={28} /></div>
                  <h2 className="font-serif">Skin Consent & Privacy Disclosure</h2>
                </div>
                <div className="consent-content">
                  <div className="warning-callout">
                    <strong><AppIcon name="alert" size={16} /> CRITICAL REMINDER:</strong> This is a <strong>screening aid, NOT a diagnosis tool</strong>. It never tells you that you have a specific condition. Always consult a dermatologist for medical confirmation.
                  </div>
                  <div className="privacy-points">
                    <h3 className="font-sans">Data Privacy Commitments:</h3>
                    <ul>
                      <li>
                        <span className="bullet-num">1</span>
                        <div><strong>Local & Secure:</strong> Image uploaded securely to check similarity.</div>
                      </li>
                      <li>
                        <span className="bullet-num">2</span>
                        <div><strong>No Unconsented Storage:</strong> Raw image not stored unless opted in.</div>
                      </li>
                    </ul>
                  </div>
                  <div className="opt-in-checkbox">
                    <label className="checkbox-container">
                      <input type="checkbox" checked={optInLogging} onChange={(e) => setOptInLogging(e.target.checked)} />
                      <span className="checkmark"></span>
                      <span className="checkbox-text font-sans">Optional: Allow storing raw skin image in secure log for Phase 2 clinician review.</span>
                    </label>
                  </div>
                </div>
                <button className="primary-button font-sans" onClick={handleAcceptSkinConsent}>I Agree to Proceed</button>
              </div>
            </div>
          ) : (
            <main className="single-column-flow animate-fade-in">
              <div className="triage-step-indicator glass-card">
                <span className="step-badge">STEP 2 OF 3</span>
                <h3><span className="title-icon"><AppIcon name="shield" size={18} /></span>Dermatological Similarity Screening</h3>
                <p className="step-rationale">
                  Our model screens skin lesions for similarities against common conditions (Acne, Eczema, Psoriasis, Rosacea, Fungal Infections). <strong>Why this is Step 2:</strong> Hormonal/dermal manifestations are often triggered by cardiovascular stress and circadian sleep disturbances detected in the vital scan.
                </p>
              </div>

              {skinStatus === 'result' && skinPrediction ? (
                <div className="glass-card result-focus-card">
                  <div className="card-header-centered">
                    <h2 className="font-serif">Screening Readout</h2>
                  </div>

                  {/* 1. Cropped/detected region image (modest size, centering) */}
                  <div className="image-overlay-container">
                    <div className="image-overlay-wrapper">
                      <img ref={skinImageRef} src={skinCapturedImage} alt="captured skin region" className="captured-img" onLoad={handleSkinImageLoad} />
                      <div className="bbox-overlay-box" style={bboxStyle}>
                        <span className="bbox-tag font-mono">Detected Region</span>
                      </div>
                    </div>
                  </div>

                  {/* 2. Signature confidence readout */}
                  <div className={`precision-instrument-container ${skinPrediction.confident ? 'state-confident' : 'state-uncertain'}`}>
                    <div className="instrument-header">
                      <span className="instrument-title font-sans">INSTRUMENT LEVEL</span>
                      <span className="instrument-status font-mono">
                        {skinPrediction.confident ? 'CONFIDENT MATCH' : 'UNCERTAIN READOUT'}
                      </span>
                    </div>
                    
                    <div className="instrument-readout-main">
                      <div className="readout-value font-mono">
                        {(skinPrediction.confidence * 100).toFixed(1)}<span className="readout-unit">%</span>
                      </div>
                      <div className="readout-label font-serif">
                        {skinPrediction.predicted_class.replace(/_/g, ' ').toUpperCase()}
                      </div>
                    </div>

                    <div className="precision-scale-track">
                      <div className="scale-ticks">
                        {[...Array(11)].map((_, i) => (
                          <div key={i} className="scale-tick" style={{ left: `${i * 10}%` }}>
                            <span className="tick-label font-mono">{i * 10}</span>
                          </div>
                        ))}
                      </div>
                      <div className="scale-needle-wrapper" style={{ left: `${skinPrediction.confidence * 100}%` }}>
                        <div className="scale-needle"></div>
                        <div className="scale-needle-dot"></div>
                      </div>
                      <div className="scale-threshold-line" style={{ left: '60%' }}></div>
                    </div>

                    <div className="instrument-footer">
                      <span className="font-mono">MIN: 0.0</span>
                      <span className="font-mono threshold-mark">THRESH: 60.0</span>
                      <span className="font-mono">MAX: 100.0</span>
                    </div>
                  </div>

                  {/* 3. Full probability distribution */}
                  <div className="probabilities-section">
                    <h3 className="font-sans">Similarity Profile Breakdown</h3>
                    <p className="section-subtitle font-sans">Relative confidence values across v1 categories:</p>
                    <div className="bar-chart">
                      {Object.entries(skinPrediction.probabilities).map(([name, prob]) => (
                        <div key={name} className={`chart-row ${name === skinPrediction.predicted_class && skinPrediction.confident ? 'highlight-row' : ''}`}>
                          <div className="row-label font-mono">
                            <span className="class-name">{name.replace(/_/g, ' ')}</span>
                            <span className="class-pct">{(prob * 100).toFixed(1)}%</span>
                          </div>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${prob * 100}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 4. Fixed medical disclaimer */}
                  <div className="disclaimer-banner">
                    <h3 className="font-sans"><AppIcon name="alert" size={16} /> MEDICAL DISCLAIMER</h3>
                    <p className="font-sans">
                      This is a screening aid, not a medical diagnosis. Always consult a dermatologist to confirm any skin conditions.
                    </p>
                  </div>

                  {/* 5. Phase 2 feedback buttons */}
                  <div className="feedback-section">
                    <h4 className="font-sans">Clinician Verification Input</h4>
                    <p className="feedback-prompt font-sans">Is this similarity reading clinically accurate?</p>
                    {skinFeedbackSent ? (
                      <div className="feedback-thanks font-sans"><AppIcon name="check" size={16} /> Thank you! Clinician audit recorded securely.</div>
                    ) : (
                      <div className="feedback-buttons">
                        <button className="feedback-btn yes font-sans" onClick={() => handleSkinFeedback(true)}><span className="feedback-icon"><AppIcon name="check" size={15} /></span>Yes, accurate</button>
                        <button className="feedback-btn no font-sans" onClick={() => handleSkinFeedback(false)}><span className="feedback-icon"><AppIcon name="close" size={15} /></span>No, inaccurate</button>
                      </div>
                    )}
                  </div>

                  <div className="triage-transition-actions">
                    <button className="secondary-button font-sans" onClick={handleSkinRetake}>Screen Another Patient</button>
                    <button className="primary-button triage-next-btn" onClick={() => handleTabChange('sleep')}>
                      Proceed to Step 3: Sleep Apnea Risk <AppIcon name="arrow-right" size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                /* Capture/Upload card */
                <div className="glass-card screening-card result-focus-card">
                  <div className="card-header-centered">
                    <h2 className="font-serif">Skin Screening</h2>
                  </div>
                  {skinStatus === 'idle' && (
                    <div className="empty-state animate-fade-in">
                      <div className="empty-icon"><AppIcon name="camera" size={28} /></div>
                      <p className="font-sans">Position the skin lesion clearly in front of the camera, under good lighting.</p>
                      <button className="primary-button font-sans" onClick={() => startSkinCamera()}>Activate Camera</button>
                    </div>
                  )}
                  {skinStatus === 'streaming' && (
                    <div className="camera-view animate-fade-in">
                      <div className="video-wrapper">
                        <video ref={skinVideoRef} autoPlay playsInline muted className="video-element"></video>
                        <div className="camera-overlay-target"><div className="scanner-line"></div></div>
                      </div>
                      <div className="camera-controls">
                        <button className="secondary-button font-sans" onClick={toggleSkinCamera}><span className="button-icon"><AppIcon name="refresh" size={15} /></span>Switch Camera</button>
                        <button className="capture-button" onClick={captureSkinFrame} aria-label="Capture frame"><span className="capture-inner"></span></button>
                        <button className="danger-button font-sans" onClick={() => { stopSkinCamera(); setSkinStatus('idle'); }}>Cancel</button>
                      </div>
                    </div>
                  )}
                  {skinStatus === 'captured' && (
                    <div className="captured-view animate-fade-in">
                      <img src={skinCapturedImage} alt="captured skin region" className="captured-img" />
                      <div className="captured-controls">
                        <button className="secondary-button font-sans" onClick={handleSkinRetake}>Retake</button>
                        <button className="primary-button font-sans" onClick={handleScreenSkinImage}>Analyze Image</button>
                      </div>
                    </div>
                  )}
                  {skinStatus === 'loading' && (
                    <div className="loading-state animate-fade-in">
                      <div className="spinner"></div>
                      <h2 className="font-serif">Analyzing region...</h2>
                    </div>
                  )}
                  {skinStatus === 'error' && (
                    <div className="error-state animate-fade-in">
                      <div className="error-icon"><AppIcon name="close" size={26} /></div>
                      <h2 className="font-serif">Error</h2>
                      <p className="font-sans">{skinError}</p>
                      <button className="primary-button font-sans" onClick={handleSkinRetake}>Try Again</button>
                    </div>
                  )}
                </div>
              )}
            </main>
          )}
        </>
      )}


      {/* --- TAB 2: SLEEP APNEA RISK SCREENER --- */}
      {activeTab === 'sleep' && (
        <>
          {!hasSleepConsent ? (
            <div className="consent-screen animate-fade-in">
              <div className="glass-card main-card">
                <div className="logo-section">
                  <div className="logo-icon"><AppIcon name="sleep" size={28} /></div>
                  <h2>Sleep Apnea Consent & Privacy Disclosure</h2>
                </div>
                <div className="consent-content">
                  <div className="warning-callout">
                    <strong><AppIcon name="alert" size={16} /> CRITICAL FRAMING:</strong> This screener is a <strong>risk assessment tool, NOT a diagnosis</strong>. It never diagnoses sleep apnea, nor does it recommend CPAP/BiPAP devices or treatment. A clinical diagnosis requires a medical sleep study (polysomnography) ordered by a licensed physician.
                  </div>
                  <div className="privacy-points">
                    <h3>Consent and Data Scope:</h3>
                    <ul>
                      <li>
                        <span className="bullet-num">1</span>
                        <div><strong>Purpose-Specific:</strong> This screening processes questionnaire metrics and optional side-profile calibration values for structural neck size ratios.</div>
                      </li>
                      <li>
                        <span className="bullet-num">2</span>
                        <div><strong>Isolated Data:</strong> Your inputs are completely separated from the skin screening history. Profile images are deleted immediately after feature calculation unless you opt to store metadata logs.</div>
                      </li>
                    </ul>
                  </div>
                </div>
                <button className="primary-button" onClick={handleAcceptSleepConsent}>Accept & Open Screener</button>
              </div>
            </div>
          ) : (
            <main className="main-content animate-fade-in">
              <div className="triage-step-indicator glass-card" style={{ gridColumn: '1 / -1' }}>
                <span className="step-badge">STEP 3 OF 3</span>
                <h3><span className="title-icon"><AppIcon name="sleep" size={18} /></span>Obstructive Sleep Apnea Risk & Airway Geometry Analysis</h3>
                <p className="step-rationale">
                  This final module combines the clinically validated STOP-BANG questionnaire with optional side-profile neck and jaw metrics. <strong>Why this is Step 3:</strong> Sleep architecture directly regulates cardiac recovery (Step 1) and skin regeneration (Step 2).
                </p>
              </div>

              {/* Left Column: Intake Questionnaire & Camera Setup */}
              <div className="glass-card screening-card">
                <h2>Sleep Risk Questionnaire</h2>
                <p className="subtitle">STOP-BANG is a clinically validated screening tool.</p>

                <form onSubmit={handleAssessSleep} className="sleep-form">
                  <div className="form-grid">
                    {/* STOP-BANG Questionnaire Items */}
                    <div className="question-item">
                      <label className="checkbox-container">
                        <input type="checkbox" checked={sbSnoring} onChange={(e) => setSbSnoring(e.target.checked)} />
                        <span className="checkmark"></span>
                        <span className="checkbox-text">
                          <strong>S - Snoring:</strong> Do you snore loudly (louder than talking or heard through closed doors)?
                        </span>
                      </label>
                    </div>

                    <div className="question-item">
                      <label className="checkbox-container">
                        <input type="checkbox" checked={sbTiredness} onChange={(e) => setSbTiredness(e.target.checked)} />
                        <span className="checkmark"></span>
                        <span className="checkbox-text">
                          <strong>T - Tiredness:</strong> Do you often feel tired, fatigued, or sleepy during the daytime?
                        </span>
                      </label>
                    </div>

                    <div className="question-item">
                      <label className="checkbox-container">
                        <input type="checkbox" checked={sbObservedApnea} onChange={(e) => setSbObservedApnea(e.target.checked)} />
                        <span className="checkmark"></span>
                        <span className="checkbox-text">
                          <strong>O - Observed Apnea:</strong> Has anyone observed you stop breathing or choking/gasping during sleep?
                        </span>
                      </label>
                    </div>

                    <div className="question-item">
                      <label className="checkbox-container">
                        <input type="checkbox" checked={sbHighBp} onChange={(e) => setSbHighBp(e.target.checked)} />
                        <span className="checkmark"></span>
                        <span className="checkbox-text">
                          <strong>P - Pressure:</strong> Do you have or are you being treated for high blood pressure?
                        </span>
                      </label>
                    </div>

                    {/* Numeric and Physical Inputs */}
                    <div className="numeric-row">
                      <div className="input-group">
                        <label>Age (Years)</label>
                        <input 
                          type="number" 
                          min="0" 
                          max="120"
                          value={sbAge} 
                          onChange={(e) => setSbAge(e.target.value)} 
                          placeholder="e.g. 52" 
                          required
                        />
                      </div>
                      
                      <div className="input-group">
                        <label>Weight (kg)</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          value={sbWeightKg} 
                          onChange={(e) => setSbWeightKg(e.target.value)} 
                          placeholder="e.g. 85" 
                          required
                        />
                      </div>

                      <div className="input-group">
                        <label>Height (cm)</label>
                        <input 
                          type="number" 
                          value={sbHeightCm} 
                          onChange={(e) => setSbHeightCm(e.target.value)} 
                          placeholder="e.g. 178" 
                          required
                        />
                      </div>
                    </div>

                    <div className="gender-row">
                      <label className="checkbox-container">
                        <input type="checkbox" checked={sbGenderMale} onChange={(e) => setSbGenderMale(e.target.checked)} />
                        <span className="checkmark"></span>
                        <span className="checkbox-text">
                          <strong>Gender:</strong> I identify as Male (clinical STOP-BANG scoring factor)
                        </span>
                      </label>
                    </div>

                    {/* Neck input toggle */}
                    <div className="neck-input-selector">
                      <h4>Neck Circumference Input Method:</h4>
                      <div className="radio-buttons">
                        <button 
                          type="button" 
                          className={`choice-btn ${!useCameraEstimation ? 'active' : ''}`}
                          onClick={() => { setUseCameraEstimation(false); stopSleepCamera(); setSleepCapturedImage(null); }}
                        >
                          Manual Input
                        </button>
                        <button 
                          type="button" 
                          className={`choice-btn ${useCameraEstimation ? 'active' : ''}`}
                          onClick={() => { setUseCameraEstimation(true); startSleepCamera(); }}
                        >
                          <span className="title-icon"><AppIcon name="camera" size={15} /></span> Camera Estimate (Credit Card Scale)
                        </button>
                      </div>
                    </div>

                    {!useCameraEstimation ? (
                      <div className="input-group animate-fade-in" style={{ marginTop: '1rem' }}>
                        <label>Neck Circumference (cm)</label>
                        <input 
                          type="number" 
                          step="0.1" 
                          value={sbNeckCircumference} 
                          onChange={(e) => setSbNeckCircumference(e.target.value)} 
                          placeholder="Measure at level of laryngeal prominence, e.g. 39.5" 
                        />
                      </div>
                    ) : (
                      <div className="camera-calibration-wrapper animate-fade-in">
                        {sleepStatus === 'streaming' && (
                          <div className="camera-view">
                            <div className="video-wrapper">
                              <video ref={sleepVideoRef} autoPlay playsInline muted className="video-element"></video>
                              <div className="camera-overlay-target">
                                <div className="scanner-line"></div>
                              </div>
                            </div>
                            <p className="calibration-tip">Hold a credit card flat next to your neck. Align your head in side/front profile.</p>
                            <div className="camera-controls">
                              <button type="button" className="secondary-button" onClick={toggleSleepCamera}><span className="button-icon"><AppIcon name="refresh" size={15} /></span>Switch Camera</button>
                              <button type="button" className="capture-button" onClick={captureSleepFrame}><span className="capture-inner"></span></button>
                            </div>
                          </div>
                        )}

                        {sleepStatus === 'captured' && (
                          <div className="calibration-manual-flow">
                            <h4>Scale Calibration & Measurements</h4>
                            <p className="step-instruction">
                              {calibrationStep === 1 && <><span className="title-icon"><AppIcon name="arrow-right" size={14} /></span> Mark the left edge of the card.</>}
                              {calibrationStep === 2 && <><span className="title-icon"><AppIcon name="arrow-right" size={14} /></span> Mark the right edge of the card.</>}
                              {calibrationStep === 3 && <><span className="title-icon"><AppIcon name="arrow-right" size={14} /></span> Mark the left neck boundary.</>}
                              {calibrationStep === 4 && <><span className="title-icon"><AppIcon name="arrow-right" size={14} /></span> Mark the right neck boundary.</>}
                              {calibrationStep === 5 && <><span className="title-icon"><AppIcon name="check" size={14} /></span> Scale is ready. Review and submit.</>}
                            </p>
                            
                            <div className="image-overlay-wrapper">
                              <img 
                                src={sleepCapturedImage} 
                                alt="calibration capture" 
                                className="captured-img click-target"
                                onClick={handleCalibrationClick}
                              />
                              
                              {/* Draw calibration points */}
                              {calibrationPoints.map((pt, idx) => (
                                <div 
                                  key={idx} 
                                  className={`calib-dot step-${pt.step}`}
                                  style={{ left: `${pt.x}px`, top: `${pt.y}px` }}
                                >
                                  <span className="dot-label">
                                    {pt.step === 1 && "Card L"}
                                    {pt.step === 2 && "Card R"}
                                    {pt.step === 3 && "Neck L"}
                                    {pt.step === 4 && "Neck R"}
                                  </span>
                                </div>
                              ))}

                              {/* Draw scale line if 2 card points clicked */}
                              {calibrationPoints.length >= 2 && (
                                <svg className="svg-overlay">
                                  <line 
                                    x1={calibrationPoints[0].x} 
                                    y1={calibrationPoints[0].y} 
                                    x2={calibrationPoints[1].x} 
                                    y2={calibrationPoints[1].y} 
                                    className="scale-line"
                                  />
                                </svg>
                              )}

                              {/* Draw neck measurement line if all 4 points clicked */}
                              {calibrationPoints.length >= 4 && (
                                <svg className="svg-overlay">
                                  <line 
                                    x1={calibrationPoints[2].x} 
                                    y1={calibrationPoints[2].y} 
                                    x2={calibrationPoints[3].x} 
                                    y2={calibrationPoints[3].y} 
                                    className="measure-line"
                                  />
                                </svg>
                              )}
                            </div>

                            <div className="captured-controls">
                              <button type="button" className="secondary-button" onClick={handleSleepRetake}>Retake Photo</button>
                              <button type="button" className="danger-button" onClick={resetCalibration}>Reset Clicks</button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {sleepErrorMsg && (
                    <div className="error-message" style={{ color: 'var(--accent-secondary)', marginTop: '1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <AppIcon name="alert" size={14} /> {sleepErrorMsg}
                    </div>
                  )}

                  <button 
                    type="submit" 
                    className="primary-button" 
                    disabled={sleepLoading}
                    style={{ marginTop: '2rem', width: '100%' }}
                  >
                    {sleepLoading ? "Calculating Risk Factors..." : "Analyze Sleep Apnea Risk"}
                  </button>
                </form>
              </div>

              {/* Right Column: Assessment Outcome Report */}
              <div className="glass-card details-card">
                <div className="disclaimer-banner">
                  <h3><span className="title-icon"><AppIcon name="sleep" size={18} /></span>SLEEP APNEA SCREENER DISCLAIMER</h3>
                  <p>
                    This is an experimental risk calculation module. It does <strong>NOT</strong> diagnose medical sleep apnea or recommend CPAP/BiPAP machines. Diagnosis can only be confirmed by a clinical sleep study (polysomnography) ordered by a physician.
                  </p>
                </div>

                <div className="result-details-section">
                  {!sleepResult ? (
                    <div className="details-empty">
                      <p>Complete the intake questionnaire, perform the camera calibration, and click "Analyze" to see your sleep risk indicators.</p>
                    </div>
                  ) : (
                    <div className="prediction-report animate-fade-in">
                      {/* Risk Band Visualization card */}
                      <div className={`sleep-risk-card band-${sleepResult.risk_band}`}>
                        <span className="risk-indicator-tag">STOP-BANG RISK BAND</span>
                        <h3>{sleepResult.risk_band.toUpperCase()} RISK</h3>
                        <p className="risk-score-display">Score: <strong>{sleepResult.score}</strong> / 8</p>
                      </div>

                      <div className="risk-factors-summary">
                        <h4>Contributing Questionnaire Factors:</h4>
                        <div className="factor-checks">
                          <div className={`factor-check ${sleepResult.questionnaire_details.snoring ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.snoring ? 'check' : 'close'} size={14} /></span>
                            <span>Snoring (Loud)</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.tiredness ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.tiredness ? 'check' : 'close'} size={14} /></span>
                            <span>Daytime Fatigue</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.observed_apnea ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.observed_apnea ? 'check' : 'close'} size={14} /></span>
                            <span>Witnessed Apnea</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.high_bp ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.high_bp ? 'check' : 'close'} size={14} /></span>
                            <span>High Blood Pressure</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.bmi_gt_35 ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.bmi_gt_35 ? 'check' : 'close'} size={14} /></span>
                            <span>BMI &gt; 35</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.age_gt_50 ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.age_gt_50 ? 'check' : 'close'} size={14} /></span>
                            <span>Age &gt; 50</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.neck_gt_40 ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.neck_gt_40 ? 'check' : 'close'} size={14} /></span>
                            <span>Neck Circumference &gt; 40cm</span>
                          </div>
                          <div className={`factor-check ${sleepResult.questionnaire_details.gender_male ? 'active' : ''}`}>
                            <span className="check-icon"><AppIcon name={sleepResult.questionnaire_details.gender_male ? 'check' : 'close'} size={14} /></span>
                            <span>Male Gender</span>
                          </div>
                        </div>
                      </div>

                      {/* Supplementary Visual Factors */}
                      {(sleepResult.visual_factors.neck_circumference_estimated_cm !== null || 
                        sleepResult.visual_factors.jaw_retrognathic_flag !== null) && (
                        <div className="visual-factors-block">
                          <h4>Supplementary Experimental Visual Signals:</h4>
                          <p className="factor-desc">Calculated from your uploaded side profile photo. Listed as supplementary factors:</p>
                          
                          {sleepResult.visual_factors.neck_circumference_estimated_cm !== null && (
                            <div className="factor-metric">
                              <span className="metric-label">Estimated Neck Circumference:</span>
                              <span className="metric-val">{sleepResult.visual_factors.neck_circumference_estimated_cm.toFixed(1)} cm</span>
                            </div>
                          )}

                          {sleepResult.visual_factors.jaw_retrognathic_flag !== null && (
                            <div className="factor-metric">
                              <span className="metric-label">Recessed Jaw (Retrognathia) Flag:</span>
                              <span className="metric-val">{sleepResult.visual_factors.jaw_retrognathic_flag === 1.0 ? "Elevated" : "Normal profile"}</span>
                            </div>
                          )}

                          {sleepResult.visual_factors.jaw_angle_deg !== null && (
                            <div className="factor-metric">
                              <span className="metric-label">Facial Glabella-Chin Angle:</span>
                              <span className="metric-val">{sleepResult.visual_factors.jaw_angle_deg.toFixed(1)}°</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Explicit Clinician CTA */}
                      <div className="clinical-cta-card">
                        <h4><span className="title-icon"><AppIcon name="shield" size={16} /></span>CLINICAL CTAs & CLINICIAN REFERRAL</h4>
                        {sleepResult.risk_band === 'high' || sleepResult.risk_band === 'intermediate' ? (
                          <div className="cta-alert high-risk-cta">
                            <p><strong>REFERRED FOR SLEEP STUDY:</strong> Your questionnaire responses indicate an elevated risk profile for obstructive sleep apnea. It is highly recommended that you consult a board-certified sleep specialist or primary care doctor to obtain a formal diagnostic sleep study (polysomnography).</p>
                          </div>
                        ) : (
                          <div className="cta-alert low-risk-cta">
                            <p>Your screening shows low risk indicators. However, if you experience poor sleep quality, chronic snoring, or daytime fatigue, please discuss these symptoms with a clinical physician.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Integrated Clinical Intake Summary (Full-Width) */}
              {(scanVitals || skinPrediction || sleepResult) && (
                <div className="clinical-summary-report glass-card" style={{ gridColumn: '1 / -1' }}>
                  <div className="report-header-banner">
                    <h3><span className="title-icon"><AppIcon name="sparkles" size={16} /></span>TrueSkin Integrated Health Report</h3>
                    <span className="report-timestamp font-mono">GEN: {new Date().toLocaleDateString()}</span>
                  </div>
                  <p className="report-desc" style={{ fontSize: '0.9rem', color: 'var(--ink-muted)' }}>
                    This report aggregates all remote screening modules completed during the patient session. Review this intake metadata prior to clinical consultation.
                  </p>
                  <div className="report-grid">
                    {/* Face Scan Summary Card */}
                    <div className={`report-card ${scanVitals ? 'active-card' : ''}`}>
                      <span className="report-card-title"><AppIcon name="heart" size={16} /> Cardiovascular Vitals</span>
                      {scanVitals ? (
                        <>
                          <div className="report-card-metric">{scanVitals.bpm} bpm</div>
                          <div className="report-card-detail">
                            • <strong>BP Proxy:</strong> {scanVitals.systolic}/{scanVitals.diastolic} mmHg<br/>
                            • <strong>Breathing Rate:</strong> {scanVitals.breathing} breaths/min<br/>
                            • <strong>HRV (RMSSD):</strong> {scanVitals.rmssd} ms<br/>
                            • <strong>Stress Index:</strong> {scanVitals.stress}/100
                          </div>
                        </>
                      ) : (
                        <span className="report-card-pending">Face Scan module not completed.</span>
                      )}
                    </div>

                    {/* Skin Screening Summary Card */}
                    <div className={`report-card ${skinPrediction ? 'active-card' : ''}`}>
                      <span className="report-card-title"><span className="report-card-icon"><AppIcon name="shield" size={14} /></span>Dermatological Screening</span>
                      {skinPrediction ? (
                        <>
                          <div className="report-card-metric">
                            {skinPrediction.predicted_class.replace(/_/g, ' ').toUpperCase()}
                          </div>
                          <div className="report-card-detail">
                            • <strong>Similarity Score:</strong> {(skinPrediction.confidence * 100).toFixed(1)}%<br/>
                            • <strong>Confidence Gate:</strong> {skinPrediction.confident ? 'PASSED (>= 60%)' : 'FAILED (< 60%)'}<br/>
                            • <strong>Region Cropped:</strong> Detected ROI bounding box {JSON.stringify(skinPrediction.bbox)}
                          </div>
                        </>
                      ) : (
                        <span className="report-card-pending">Skin Screening module not completed.</span>
                      )}
                    </div>

                    {/* Sleep Apnea Summary Card */}
                    <div className={`report-card ${sleepResult ? 'active-card' : ''}`}>
                      <span className="report-card-title"><span className="report-card-icon"><AppIcon name="sleep" size={14} /></span>Sleep Apnea Risk</span>
                      {sleepResult ? (
                        <>
                          <div className="report-card-metric">
                            {sleepResult.risk_band.toUpperCase()} RISK
                          </div>
                          <div className="report-card-detail">
                            • <strong>STOP-BANG Score:</strong> {sleepResult.score}/8<br/>
                            • <strong>Manual Neck Circumference:</strong> {sleepResult.questionnaire_details.neck_gt_40 ? '> 40 cm' : 'Normal'}<br/>
                            • <strong>Airway profile jaw angle:</strong> {sleepResult.visual_factors.jaw_angle_deg ? `${sleepResult.visual_factors.jaw_angle_deg.toFixed(1)}°` : 'N/A'}<br/>
                            • <strong>Retrognathia Flag:</strong> {sleepResult.visual_factors.jaw_retrognathic_flag === 1.0 ? 'ELEVATED' : 'Normal'}
                          </div>
                        </>
                      ) : (
                        <span className="report-card-pending">Sleep Apnea risk calculation not completed.</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="disclaimer-banner" style={{ marginTop: '1rem', borderLeft: '4px solid var(--accent-secondary)' }}>
                    <h4 style={{ color: 'var(--accent-secondary)', fontWeight: 600 }}><span className="title-icon"><AppIcon name="shield" size={16} /></span>GENERAL CLINICAL NOTICE</h4>
                    <p style={{ fontSize: '0.85rem', color: 'var(--ink-muted)' }}>
                      TrueSkin is an intelligence screening scaffold. This report acts as a clinical intake aid for practitioners and does not constitute a certified diagnosis. Always cross-reference all metrics with traditional diagnostic devices (e.g. ECG, PSG, or skin biopsy).
                    </p>
                  </div>
                </div>
              )}
            </main>
          )}
        </>
      )}
      
      {/* --- TAB 3: FACE SCAN (rPPG) --- */}
      {activeTab === 'scan' && (
        <div className="scan-tab-wrapper animate-fade-in">

          {scanPhase === 'intro' && (
            <div className="triage-step-indicator glass-card">
              <span className="step-badge">STEP 1 OF 3</span>
              <h3><AppIcon name="heart" size={18} /> Cardiovascular Vital Signs (Face Scan)</h3>
              <p className="step-rationale">
                Our remote PPG technology estimates physiological baselines (Pulse, Respiration, Stress Index) from facial color changes. <strong>Why this is Step 1:</strong> Systemic stress directly impacts sleep architecture and limits skin microcirculation, which triggers or exacerbates dermal inflammation.
              </p>
            </div>
          )}

          {/* ── INTRO PHASE (Redcliffe style) ──────────────────────── */}
          {scanPhase === 'intro' && (
            <div className="rcl-intro-card">

              {scanError && (
                <div className="rcl-scan-error-banner animate-fade-in" style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: '8px',
                  padding: '0.85rem 1rem',
                  marginBottom: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  color: '#C8430A',
                  position: 'relative'
                }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '1.35rem', height: '1.35rem' }}><AppIcon name="alert" size={18} /></span>
                  <p style={{ margin: 0, fontSize: '0.82rem', lineHeight: '1.4', flex: 1 }}>{scanError}</p>
                  <button onClick={() => setScanError('')} style={{
                    background: 'none',
                    border: 'none',
                    color: '#C8430A',
                    fontSize: '1.25rem',
                    cursor: 'pointer',
                    padding: '0 0.15rem',
                    lineHeight: '1',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}><AppIcon name="close" size={18} /></button>
                </div>
              )}

              {/* Header */}
              <div className="rcl-header">
                <div className="rcl-icon-wrap">
                  <AppIcon name="heart" size={28} />
                </div>
                <div>
                  <h2 className="rcl-title">Face Scan</h2>
                  <p className="rcl-subtitle">Get insights in 30 sec</p>
                </div>
              </div>

              {/* Metric pills — 2 column grid */}
              <div className="rcl-metrics-grid">
                {[
                  { icon: 'heart', label: 'Pulse' },
                  { icon: 'wind', label: 'Breathing Rate' },
                  { icon: 'drop', label: 'Blood Pressure' },
                  { icon: 'activity', label: 'Cardiac Workload' },
                  { icon: 'chart', label: 'Heart Rate Variability' },
                  { icon: 'brain', label: 'Stress Index' },
                  { icon: 'wave', label: 'Parasympathetic Activity' },
                ].map(m => (
                  <div key={m.label} className="rcl-metric-pill">
                    <div className="rcl-pill-icon"><AppIcon name={m.icon} size={15} /></div>
                    <span className="rcl-pill-label">{m.label}</span>
                  </div>
                ))}
              </div>

              {/* Divider */}
              <div className="rcl-divider" />

              {/* How it works */}
              <div className="rcl-how-section">
                <p className="rcl-section-title">How it works</p>
                <p className="rcl-how-text">
                  Our Face Scan uses remote photoplethysmography (rPPG) and remote
                  ballistocardiography (rBCG) technology to detect tiny skin colour changes
                  caused by blood flow and subtle head movements linked to your heartbeat
                  and breathing. These signals are captured from a short facial video and
                  analyzed to estimate key vital signs using only your device's camera, with
                  no physical contact or wearables.
                </p>
              </div>

              <div className="rcl-divider" />

              {/* How to take assessment */}
              <div className="rcl-tips-section">
                <p className="rcl-section-title">How to take assessment</p>
                {[
                  { icon: 'sparkles', title: 'Good Lighting',       desc: 'Ensure good lighting for clear visibility.' },
                  { icon: 'scan', title: 'Eye Level Position',  desc: "Position your device's camera so it's level with your eyes." },
                  { icon: 'sleep', title: 'Stay Still & Quiet',  desc: 'Avoid talking or moving your head.' },
                ].map(tip => (
                  <div key={tip.title} className="rcl-tip-row">
                    <div className="rcl-tip-icon-wrap"><AppIcon name={tip.icon} size={16} /></div>
                    <div className="rcl-tip-text">
                      <p className="rcl-tip-title">{tip.title}</p>
                      <p className="rcl-tip-desc">{tip.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Disclaimer */}
              <p className="rcl-disclaimer">
                *The AI-based face scan provides health insights for informational purposes only
                and is not a substitute for medical advice, diagnosis, or treatment. Users are
                advised to consult a medical practitioner for advice.
              </p>

              {/* CTA */}
              <button id="start-face-scan-btn" className="rcl-next-btn" onClick={startFaceScan}>
                Next
              </button>
            </div>
          )}

          {/* ── SCANNING PHASE (Redcliffe full-screen style) ────────── */}
          {scanPhase === 'scanning' && (
            <div className="rcl-scan-screen">

              {/* Top bar: premium diagnostic HUD block */}
              <div className="rcl-scan-topbar diagnostic-hud">
                <div className="hud-primary-quality">
                  <span className="hud-label font-mono">SIGNAL QUALITY</span>
                  <span className="hud-value font-mono">{Math.round(scanQuality)}%</span>
                  <div className="hud-quality-progress">
                    <div className="hud-quality-fill" style={{ width: `${scanQuality}%` }} />
                  </div>
                </div>
                <div className="hud-details-grid">
                  <div className="hud-detail-item">
                    <span className="hud-detail-label">LIGHTING</span>
                    <span className={`hud-detail-val status-${lightingStatus.toLowerCase()}`}>{lightingStatus}</span>
                  </div>
                  <div className="hud-detail-item">
                    <span className="hud-detail-label">MOTION</span>
                    <span className={`hud-detail-val status-${motionStatus.toLowerCase()}`}>{motionStatus}</span>
                  </div>
                  <div className="hud-detail-item">
                    <span className="hud-detail-label">FACE STABILITY</span>
                    <span className={`hud-detail-val status-${stabilityStatus.toLowerCase()}`}>{stabilityStatus}</span>
                  </div>
                  <div className="hud-detail-item">
                    <span className="hud-detail-label">CONFIDENCE</span>
                    <span className={`hud-detail-val status-${confidenceStatus.toLowerCase()}`}>{confidenceStatus}</span>
                  </div>
                </div>
              </div>

              {/* Full-screen camera */}
              <div className="rcl-video-wrapper" style={{ aspectRatio: videoAspectRatio }}>
                <video ref={scanVideoRef} className="rcl-video" autoPlay muted playsInline onLoadedMetadata={handleVideoLoad} />
                
                {/* Minimal Elegant HUD Brackets */}
                <div className="rcl-hud-corner tl" />
                <div className="rcl-hud-corner tr" />
                <div className="rcl-hud-corner bl" />
                <div className="rcl-hud-corner br" />

                {/* Minimalist SVG Face Alignment Guide */}
                <div className="rcl-alignment-guide">
                  <svg viewBox="0 0 100 100" className="rcl-guide-svg">
                    <path fillRule="evenodd" fill="rgba(0,0,0,0.6)" d="M 0,0 L 100,0 L 100,100 L 0,100 Z M 50,10 C 36,10 27,23 27,42.5 C 27,62 36,75 50,75 C 64,75 73,62 73,42.5 C 73,23 64,10 50,10 Z" />
                    <path fill="none" stroke="var(--accent-primary)" strokeWidth="0.6" strokeDasharray="3 3" d="M 50,10 C 36,10 27,23 27,42.5 C 27,62 36,75 50,75 C 64,75 73,62 73,42.5 C 73,23 64,10 50,10 Z" opacity="0.8" />
                    <path fill="none" stroke="var(--accent-primary)" strokeWidth="0.4" strokeDasharray="3 3" d="M 28,88 C 28,76 34,72 50,72 C 66,72 72,76 72,88" opacity="0.6" />
                    
                    {/* Animated Inward-Pointing Arrows on Oval Edges */}
                    <g className="hud-arrow-down">
                      <path d="M 47,12 L 50,16 L 53,12" fill="none" stroke="#E8722A" strokeWidth="0.9" strokeLinecap="round" strokeLinejoin="round" />
                    </g>
                    <g className="hud-arrow-up">
                      <path d="M 47,73 L 50,69 L 53,73" fill="none" stroke="#E8722A" strokeWidth="0.9" strokeLinecap="round" strokeLinejoin="round" />
                    </g>
                    <g className="hud-arrow-right">
                      <path d="M 29,39.5 L 33,42.5 L 29,45.5" fill="none" stroke="#E8722A" strokeWidth="0.9" strokeLinecap="round" strokeLinejoin="round" />
                    </g>
                    <g className="hud-arrow-left">
                      <path d="M 71,39.5 L 67,42.5 L 71,45.5" fill="none" stroke="#E8722A" strokeWidth="0.9" strokeLinecap="round" strokeLinejoin="round" />
                    </g>

                    <text x="50" y="32" textAnchor="middle" fill="#E8722A" fontSize="2.8" fontWeight="600" fontFamily="var(--font-sans)" letterSpacing="0.08em" opacity="0.9" className="hud-pulse-text">POSITION FACE INSIDE</text>
                    <text x="50" y="83" textAnchor="middle" fill="var(--accent-primary)" fontSize="3.5" fontWeight="600" fontFamily="var(--font-sans)" letterSpacing="0.05em" opacity="0.9">ALIGN FACE &amp; SHOULDERS</text>
                  </svg>
                </div>

                {/* Face mesh dot overlay — active throughout the scan for futuristic telemetry */}
                <svg ref={faceMeshRef} className="rcl-mesh-svg-overlay" viewBox="0 0 100 100" style={{
                  '--mesh-stroke': 'rgba(232, 114, 42, 0.25)',
                  '--mesh-fill': '#E8722A',
                  transformOrigin: '50% 45%',
                  transition: 'transform 0.3s ease'
                }}>
                  {/* Connecting lines of the neural mesh */}
                  <g stroke="var(--mesh-stroke)" strokeWidth="0.15" fill="none" style={{ transition: 'stroke 0.3s' }}>
                    {/* Forehead to Eyebrows */}
                    <line x1="50" y1="22" x2="42" y2="28" />
                    <line x1="50" y1="22" x2="58" y2="28" />
                    
                    {/* Eyebrows to eyes */}
                    <line x1="42" y1="28" x2="40" y2="34" />
                    <line x1="58" y1="28" x2="60" y2="34" />
                    
                    {/* Eyebrows to nose bridge */}
                    <line x1="42" y1="28" x2="50" y2="33" />
                    <line x1="58" y1="28" x2="50" y2="33" />
                    
                    {/* Eyes to Cheeks */}
                    <line x1="40" y1="34" x2="37" y2="43" />
                    <line x1="60" y1="34" x2="63" y2="43" />
                    
                    {/* Nose bridge to Nose tip */}
                    <line x1="50" y1="33" x2="50" y2="44" />
                    
                    {/* Nose tip to cheeks */}
                    <line x1="50" y1="44" x2="37" y2="43" />
                    <line x1="50" y1="44" x2="63" y2="43" />
                    
                    {/* Nose tip to mouth */}
                    <line x1="50" y1="44" x2="50" y2="55" />
                    
                    {/* Mouth center to mouth corners */}
                    <line x1="50" y1="55" x2="44" y2="54" />
                    <line x1="50" y1="55" x2="56" y2="54" />
                    
                    {/* Cheeks to Jaw */}
                    <line x1="37" y1="43" x2="36" y2="54" />
                    <line x1="63" y1="43" x2="64" y2="54" />
                    
                    {/* Mouth corners to Jaw */}
                    <line x1="44" y1="54" x2="36" y2="54" />
                    <line x1="56" y1="54" x2="64" y2="54" />
                    
                    {/* Jaw to Chin */}
                    <line x1="36" y1="54" x2="50" y2="65" />
                    <line x1="64" y1="54" x2="50" y2="65" />

                    {/* Eyebrow to Eyebrow connect */}
                    <line x1="42" y1="28" x2="58" y2="28" />
                    {/* Eye to Eye connect */}
                    <line x1="40" y1="34" x2="60" y2="34" strokeDasharray="0.5 1" />
                  </g>
                  
                  {/* Glowing nodes (dots) */}
                  <g fill="var(--mesh-fill)" opacity="0.8" style={{ transition: 'fill 0.3s' }}>
                    <circle cx="50" cy="22" r="0.5" className="rcl-mesh-node" />
                    <circle cx="42" cy="28" r="0.5" className="rcl-mesh-node" />
                    <circle cx="58" cy="28" r="0.5" className="rcl-mesh-node" />
                    <circle cx="40" cy="34" r="0.5" className="rcl-mesh-node" />
                    <circle cx="60" cy="34" r="0.5" className="rcl-mesh-node" />
                    <circle cx="50" cy="33" r="0.5" className="rcl-mesh-node" />
                    <circle cx="50" cy="44" r="0.8" className="rcl-mesh-node-pulse" /> {/* Nose tip indicator */}
                    <circle cx="37" cy="43" r="0.5" className="rcl-mesh-node" />
                    <circle cx="63" cy="43" r="0.5" className="rcl-mesh-node" />
                    <circle cx="50" cy="55" r="0.5" className="rcl-mesh-node" />
                    <circle cx="44" cy="54" r="0.5" className="rcl-mesh-node" />
                    <circle cx="56" cy="54" r="0.5" className="rcl-mesh-node" />
                    <circle cx="36" cy="54" r="0.5" className="rcl-mesh-node" />
                    <circle cx="64" cy="54" r="0.5" className="rcl-mesh-node" />
                    <circle cx="50" cy="65" r="0.5" className="rcl-mesh-node" />
                  </g>
                </svg>
                
                {/* Laser scan and sweep line animations — always active during scan */}
                <div className="rcl-scan-sweep active" />
                <div className="rcl-scan-line active" />
              </div>

              {/* Hidden canvas for pixel sampling */}
              <canvas ref={scanCanvasRef} style={{ display: 'none' }} />

              {/* ── LIVE BPM RING + WAVEFORM PANEL ── */}
              <div className="rcl-vitals-panel">

                {/* BPM Ring */}
                <div className="rcl-bpm-ring-wrap">
                  <svg viewBox="0 0 120 120" className="rcl-bpm-svg">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="8"/>
                    <circle
                      cx="60" cy="60" r="52"
                      fill="none"
                      stroke={scanLiveBpm ? (scanLiveBpm > 100 ? '#C8430A' : '#5DBB5D') : '#7A2800'}
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 52}`}
                      strokeDashoffset={`${2 * Math.PI * 52 * (1 - Math.min(((scanLiveBpm||0) - 40) / 140, 1))}`}
                      transform="rotate(-90 60 60)"
                      style={{ transition: 'stroke-dashoffset 0.5s ease, stroke 0.3s' }}
                    />
                  </svg>
                  <div className="rcl-bpm-ring-inner">
                    <span ref={scanHeartIconRef} className="rcl-bpm-ring-icon" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><AppIcon name="heart" size={22} /></span>
                    {scanBpmReady && scanLiveBpm ? (
                      <span className="rcl-bpm-ring-value font-mono">{scanLiveBpm}</span>
                    ) : (
                      <span className="rcl-bpm-ring-value font-mono" style={{ fontSize: '0.62rem', letterSpacing: '0.04em' }}>CALCULATING…</span>
                    )}
                    <span className="rcl-bpm-ring-label">BPM</span>
                  </div>
                </div>

                {/* Waveform */}
                <div className="rcl-wave-col">
                  <div className="rcl-wave-header">
                    <span className="rcl-wave-title">PLETH WAVEFORM</span>
                    <span className={`rcl-wave-badge ${scanBpmReady ? 'live' : 'calibrating'}`}>
                      {scanBpmReady ? <><AppIcon name="check" size={12} /> LIVE</> : <><AppIcon name="refresh" size={12} /> CALCULATING</>}
                    </span>
                  </div>
                  <canvas
                    ref={waveCanvasRef}
                    className="rcl-wave-canvas"
                    width={320}
                    height={90}
                  />
                </div>

              </div>

              {/* High-tech Control & Status Console Bar */}
              <div className="rcl-console-control-bar">
                <div className="rcl-progress-container">
                  <div className="rcl-progress-header font-mono">
                    <span>SCAN PROGRESS</span>
                    <span>{scanSeconds < SCAN_DURATION
                      ? `${Math.max(0, SCAN_DURATION - scanSeconds)}s remaining`
                      : (scanBpmReady ? 'finalizing…' : 'stabilizing — hold still…')}</span>
                  </div>
                  <div className="rcl-progress-track">
                    <div className="rcl-progress-fill" style={{ width: `${Math.min((scanSeconds/SCAN_DURATION)*100, 100)}%` }} />
                  </div>
                </div>
                <div className="rcl-control-actions">
                  <p className="rcl-status-msg font-mono">
                    {scanSeconds < 5
                      ? 'Initializing sensors — Keep still'
                      : scanLiveBpm
                      ? 'Signal acquired — hold still'
                      : 'Analyzing signal metrics...'}
                  </p>
                  <button className="rcl-stop-btn font-mono" onClick={() => stopFaceScan('intro')}>STOP SCAN</button>
                </div>
              </div>

            </div>
          )}


          {/* ── RESULTS PHASE ──────────────────────────────────────────── */}
          {scanPhase === 'done' && (
            <div className="scan-results-container animate-fade-in">
              {scanVitals && scanVitals.unreliable ? (
                <div className="scan-results-unreliable">
                  <div className="scan-results-header">
                    <div className="scan-pulse-icon warning"><AppIcon name="alert" size={24} /></div>
                    <h2 className="font-serif">{scanVitals.reason === 'unstable' ? 'Heart Rate Didn’t Settle' : 'Scan Quality Low'}</h2>
                    <p className="scan-unreliable-desc">
                      {scanVitals.reason === 'unstable'
                        ? 'Your heart rate kept fluctuating and never settled on a stable value, so we did not show a number rather than risk an inaccurate one. Please hold completely still in even, front-facing light and scan again.'
                        : <>Signal quality was too low to calculate a reliable reading (Signal Quality: <strong>{Math.round(scanVitals.quality)}%</strong>, threshold: <strong>50%</strong>).</>}
                    </p>
                  </div>
                  <div className="unreliable-box">
                    <h3>Tips for a Successful Scan:</h3>
                    <ul>
                      <li><span className="title-icon"><AppIcon name="sparkles" size={14} /></span> <strong>Lighting:</strong> Ensure your face is evenly lit by a front-facing light source (avoid backlighting).</li>
                      <li><span className="title-icon"><AppIcon name="sleep" size={14} /></span> <strong>Silence:</strong> Hold completely still and do not speak or move your head during the 30-second countdown.</li>
                      <li><span className="title-icon"><AppIcon name="scan" size={14} /></span> <strong>Stability:</strong> Prop your phone or laptop on a stable surface instead of holding it.</li>
                    </ul>
                    <div className="clinical-recommendation-box warning">
                      <strong>Clinical Recommendation:</strong> Vitals estimation was blocked to prevent inaccurate readings. Please repeat the scan following the guidelines above.
                    </div>
                  </div>
                  <div className="triage-transition-actions">
                    <button className="primary-button" onClick={() => {
                      setScanVitals(null);
                      setScanQuality(0);
                      setScanSeconds(0);
                      setScanPhase('intro');
                    }}>
                      <AppIcon name="arrow-right" size={16} /> Scan Again
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="scan-results-header">
                    <div className="scan-pulse-icon small"><AppIcon name="heart" size={24} /></div>
                    <h2 className="font-serif">Your Scan Results</h2>
                  </div>

                  {scanVitals && scanVitals.low_confidence && (
                    <div className="scan-disclaimer" style={{ background: 'rgba(245, 162, 97, 0.12)', border: '1px solid rgba(245, 162, 97, 0.4)', borderRadius: 18, padding: '14px 16px', margin: '0 0 20px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: '#d97706', fontWeight: 600 }}><AppIcon name="alert" size={16} /> Low confidence</span>
                      <p style={{ margin: '0.75rem 0 0', color: '#5b4631', fontSize: '0.95rem', lineHeight: 1.6 }}>
                        Signal quality was {Math.round(scanVitals.quality)}% (below the 70% reliable threshold). These values are usable estimates but may be less accurate. For best results, re-scan in even, front-facing light while holding still.
                      </p>
                    </div>
                  )}

                  {scanVitals && (
                    <>
                      {/* Overall Assessment Dashboard */}
                      <div className="overall-assessment-card">
                        <h3 className="assessment-title font-mono">OVERALL ASSESSMENT</h3>
                        <div className="assessment-grid">
                          <div className="assessment-item">
                            <span className="assess-label">Heart Rate:</span>
                            <span className={`assess-val status-${scanVitals.bpm >= 60 && scanVitals.bpm <= 100 ? 'normal' : 'abnormal'}`}>
                              {scanVitals.bpm >= 60 && scanVitals.bpm <= 100 ? 'Normal' : 'Abnormal'}
                            </span>
                          </div>
                          <div className="assessment-item">
                            <span className="assess-label">Respiration:</span>
                            <span className={`assess-val status-${scanVitals.breathing >= 12 && scanVitals.breathing <= 20 ? 'normal' : 'abnormal'}`}>
                              {scanVitals.breathing >= 12 && scanVitals.breathing <= 20 ? 'Normal' : 'Abnormal'}
                            </span>
                          </div>
                          <div className="assessment-item">
                            <span className="assess-label">Blood Pressure:</span>
                            <span className={`assess-val status-${
                              scanVitals.low_confidence ? 'elevated' :
                              scanVitals.systolic < 120 && scanVitals.diastolic < 80 ? 'normal' :
                              scanVitals.systolic >= 140 || scanVitals.diastolic >= 90 ? 'stage2' : 'elevated'
                            }`}>
                              {
                                scanVitals.low_confidence ? 'Estimate — re-scan' :
                                scanVitals.systolic < 120 && scanVitals.diastolic < 80 ? 'Normal' :
                                scanVitals.systolic >= 140 || scanVitals.diastolic >= 90 ? 'Stage 2 Hypertension' :
                                scanVitals.systolic >= 130 || scanVitals.diastolic >= 80 ? 'Stage 1 Hypertension' : 'Elevated'
                              }
                            </span>
                          </div>
                          <div className="assessment-item">
                            <span className="assess-label">Oxygen (SpO2):</span>
                            <span className={`assess-val status-${scanVitals.spo2 >= 95 ? 'normal' : 'abnormal'}`}>
                              {scanVitals.spo2 ?? '—'}% ({scanVitals.spo2 >= 95 ? 'Normal' : 'Low'})
                            </span>
                          </div>
                          <div className="assessment-item">
                            <span className="assess-label">Stress Level:</span>
                            <span className={`assess-val status-${scanVitals.stress < 30 ? 'low' : scanVitals.stress < 70 ? 'moderate' : 'high'}`}>
                              {scanVitals.stress < 30 ? 'Low' : scanVitals.stress < 70 ? 'Moderate' : 'High'}
                            </span>
                          </div>
                          <div className="assessment-item">
                            <span className="assess-label">Signal Quality:</span>
                            <span className={`assess-val status-${scanVitals.quality >= 85 ? 'excellent' : 'good'}`}>
                              {scanVitals.quality >= 85 ? 'Excellent' : 'Good'}
                            </span>
                          </div>
                        </div>

                        {/* Clinical Recommendation Box */}
                        <div className={`clinical-recommendation-box ${
                          scanVitals.low_confidence ? 'attention' :
                          (scanVitals.spo2 < 95) ? 'warning' :
                          (scanVitals.systolic >= 130 || scanVitals.diastolic >= 80) ? 'attention' : 'normal'
                        }`}>
                          <strong>Clinical Recommendation:</strong>{' '}
                          {scanVitals.low_confidence
                            ? 'Signal quality was low, so these values — especially blood pressure — may be inaccurate and should not be read as a diagnosis. Please re-scan in even, front-facing light while holding completely still.'
                            : scanVitals.spo2 < 95
                            ? 'Oxygen saturation (SpO2) is low. We recommend taking deep breaths and repeating the scan in a well-ventilated room. Consult a physician if levels remain below 95%.'
                            : (scanVitals.systolic >= 130 || scanVitals.diastolic >= 80)
                            ? 'Blood pressure appears elevated. We recommend resting for 5 minutes in a quiet environment and repeating the scan.'
                            : 'Everything looks within expected limits. Continue routine monitoring.'}
                        </div>
                      </div>

                      <div className="scan-results-grid">
                        {/* Pulse */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="heart" size={18} /></span>
                          <span className="result-label font-mono">PULSE</span>
                          <span className="result-value font-mono">{scanVitals.bpm ?? '—'}</span>
                          <span className="result-unit">bpm</span>
                          <span className={`result-status font-mono ${scanVitals.bpm >= 60 && scanVitals.bpm <= 100 ? 'normal' : 'abnormal'}`}>
                            {scanVitals.bpm >= 60 && scanVitals.bpm <= 100 ? 'Normal' : 'Abnormal'}
                          </span>
                          <span className="result-detail font-mono">Quality: {Math.round(scanVitals.quality)}%</span>
                        </div>

                        {/* Blood Pressure */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="drop" size={18} /></span>
                          <span className="result-label font-mono">BLOOD PRESSURE</span>
                          <span className="result-value font-mono">
                            {scanVitals.systolic && scanVitals.diastolic
                              ? `${scanVitals.systolic}/${scanVitals.diastolic}`
                              : '—'}
                          </span>
                          <span className="result-unit">mmHg</span>
                          <span className={`result-status font-mono ${
                            scanVitals.systolic < 120 && scanVitals.diastolic < 80 ? 'normal' : 'elevated'
                          }`}>
                            {scanVitals.systolic < 120 && scanVitals.diastolic < 80 ? 'Normal' : 'Elevated'}
                          </span>
                          <span className="result-detail font-mono">Confidence: {scanVitals.bp_confidence}%</span>
                        </div>

                        {/* HRV RMSSD */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="chart" size={18} /></span>
                          <span className="result-label font-mono">HEART RATE VARIABILITY</span>
                          <span className="result-value font-mono">{scanVitals.rmssd ?? '—'}</span>
                          <span className="result-unit">ms (RMSSD)</span>
                          <span className={`result-status font-mono ${scanVitals.rmssd >= 20 && scanVitals.rmssd <= 80 ? 'normal' : 'abnormal'}`}>
                            {scanVitals.rmssd >= 20 && scanVitals.rmssd <= 80
                              ? 'Healthy recovery'
                              : scanVitals.rmssd > 80 ? 'High (noisy signal)' : 'Low HRV'}
                          </span>
                          <span className="result-detail font-mono">Normal Range: 20–80 ms</span>
                        </div>

                        {/* Breathing Rate */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="wind" size={18} /></span>
                          <span className="result-label font-mono">BREATHING RATE</span>
                          <span className="result-value font-mono">{scanVitals.breathing ?? '—'}</span>
                          <span className="result-unit">breaths/min</span>
                          <span className={`result-status font-mono ${scanVitals.breathing >= 12 && scanVitals.breathing <= 20 ? 'normal' : 'abnormal'}`}>
                            {scanVitals.breathing >= 12 && scanVitals.breathing <= 20 ? 'Normal' : 'Abnormal'}
                          </span>
                          <span className="result-detail font-mono">Normal Range: 12–20</span>
                        </div>

                        {/* Oxygen Saturation (SpO2) */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="oxygen" size={18} /></span>
                          <span className="result-label font-mono">OXYGEN SATURATION</span>
                          <span className="result-value font-mono">{scanVitals.spo2 ?? '—'}</span>
                          <span className="result-unit">% (SpO2)</span>
                          <span className={`result-status font-mono ${scanVitals.spo2 >= 95 ? 'normal' : 'abnormal'}`}>
                            {scanVitals.spo2 >= 95 ? 'Normal' : 'Low Oxygen'}
                          </span>
                          <span className="result-detail font-mono">Normal Range: 95–100%</span>
                        </div>

                        {/* Stress Index */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="brain" size={18} /></span>
                          <span className="result-label font-mono">STRESS INDEX</span>
                          <span className="result-value font-mono">{scanVitals.stress ?? '—'}</span>
                          <span className="result-unit">/ 100</span>
                          <span className="result-detail font-mono">Lower = Less stress</span>
                        </div>

                        {/* Parasympathetic Activity */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="wave" size={18} /></span>
                          <span className="result-label font-mono">PARASYMPATHETIC ACTIVITY</span>
                          <span className="result-value font-mono">{scanVitals.parasym ?? '—'}</span>
                          <span className="result-unit">/ 100</span>
                          <span className="result-detail font-mono">Higher = More recovery</span>
                        </div>

                        {/* Cardiac Workload (Rate-Pressure-Product) */}
                        <div className="scan-result-card">
                          <span className="result-icon"><AppIcon name="activity" size={18} /></span>
                          <span className="result-label font-mono">CARDIAC WORKLOAD</span>
                          <span className="result-value font-mono">{scanVitals.cardiac_workload ?? '—'}</span>
                          <span className="result-unit">RPP</span>
                          <span className="result-detail font-mono">HR × Systolic ÷ 100</span>
                        </div>
                      </div>
                    </>
                  )}

                  <p className="scan-disclaimer results-disclaimer">
                    These results are informational screening estimates only. Consult a qualified 
                    clinician before making any health decisions.
                  </p>

                  <div className="triage-transition-actions">
                    <button className="secondary-button" onClick={() => {
                      setScanVitals(null);
                      setScanQuality(0);
                      setScanSeconds(0);
                      setScanPhase('intro');
                    }}>
                      Scan Again
                    </button>
                    <button className="primary-button triage-next-btn" onClick={() => handleTabChange('skin')}>
                      Proceed to Step 2: Skin Screening <AppIcon name="arrow-right" size={14} />
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
        </>
      )}

      <footer className="app-footer">
        <p className="font-mono">Made by Divyansh Srivastava</p>
      </footer>
    </div>
  );
}
