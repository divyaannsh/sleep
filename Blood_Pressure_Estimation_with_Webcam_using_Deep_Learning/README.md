# Blood Pressure Estimation using Deep Learning (rPPG & MLP)

This directory contains the professionalized research project for estimating blood pressure using deep learning techniques (rPPG signal extraction & 9-layer dense MLP network). 

As part of the TrueSkin Clinical Intelligence integration, the signal processing pipeline and model architecture developed here have been ported and fully integrated into the main **TrueSkin Face Scan** module.

---

## 📂 Restructured Directory Layout
The folder structure has been cleaned of redundant duplicate files and organized according to modern web application best practices:

```
├── app.py                      # Flask API serving the demonstration interface
├── static/                     # Static assets served by the Flask application
│   ├── heartbeat.js            # Core rPPG signal extraction & filtering class
│   ├── index.js                # Frontend page controller & video handling
│   ├── style.css               # Styling variables and layout rules
│   ├── haarcascade_frontalface_alt.xml # OpenCV Haar Cascade xml moved to static
│   └── img/                    # Vector illustrations and diagnostic icons
├── templates/                  # Flask HTML templates
│   └── index.html              # Main application GUI layout
├── LICENSE                     # License terms
└── README.md                   # This file
```

---

## ⚡ Key Improvements
1. **Redundancy Cleanup**: Removed duplicate scripts and page files from the root directory. All source files now live in dedicated `static/`, `templates/`, or `static/img/` directories.
2. **Flask Serving Fixes**: Configured paths to load `haarcascade_frontalface_alt.xml` dynamically from the Flask `/static` context, resolving silent load errors when running the application.
3. **TrueSkin Integration**:
   - The exact **9-layer dense Multi-Layer Perceptron (MLP)** neural network model architecture has been replicated in the TrueSkin backend (`src/model_helper.py`) using **PyTorch**.
   - The face scanning interface (`frontend/src/App.jsx`) now extracts, z-score normalizes, and submits a 180-frame green-channel rPPG signal to the backend `/predict-bp` endpoint.
   - Includes a cross-correlation-based Pulse Transit Time (PTT) algorithm as a robust physiological fallback.

---

## 🚀 Execution Instructions

1. **Demonstration Server**:
   Ensure you have dependencies installed, then run the Flask app:
   ```bash
   python app.py
   ```
2. **View Demo**:
   Open [http://localhost:5000](http://localhost:5000) in your browser.
