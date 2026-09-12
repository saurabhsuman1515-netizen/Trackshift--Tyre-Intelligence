# TrackShift — F1 Tyre Degradation Intelligence System

> **F1 Single-Car Session Telemetry Analytics Engine & Interactive Dot-Matrix UI**

TrackShift is a telemetry intelligence platform built to isolate true F1 tyre degradation from raw lap times by stripping away fuel weight latency, traffic interference, and session-wide track evolution — returning honest, expanding uncertainty cones rather than bare point predictions.

---

## 🚀 Key Features & Signature UI

1. **Interactive Moving Dot F1 Car Canvas (`F1CarParticleCanvas`)**:
   - An interactive HTML5 canvas featuring over 380 glowing telemetry particles floating and dynamically morphing into an **F1 Racing Car contour (RB20)** with aerodynamic particle streams.
   - Particles react to mouse hover repulsion and dynamically adapt their glow hue to the selected compound (Red for Soft, Yellow for Medium, White for Hard).

2. **Hero Overview & Honest Uncertainty**:
   - Side-by-side comparison of **RAW SLOWDOWN** vs **TRUE DEGRADATION**.
   - Explicit `ESTIMATED` / `PREDICTED` badges on every analytical figure.

3. **Two-Phase Warm-up & Degradation Model**:
   - Detects initial warm-up changepoint (pace improving for 1-3 laps) before fitting linear degradation.
   - Downweights positive lap time outliers (> +2 SD) while keeping clean and fast laps.

4. **Widening Uncertainty Cone**:
   - Confidence bounds expand proportional to $\sqrt{\text{laps ahead}}$ using residual standard error ($\sigma$).

5. **Lap Forensics Additive Decomposition**:
   - Waterfall chart breaking down any lap into Fuel, Traffic, Track Evolution, Tyre Wear, and Residual Noise, summing strictly to the observed delta.

6. **Strategy Simulator & Deterministic Race Engineer**:
   - Simulates Stay Out vs Pit Now vs Pit in N Laps.
   - Deterministic Q&A assistant grounded in computed telemetry data with zero LLM hallucinations.

---

## 🛠️ Project Structure

```
trackshift/
├── backend/
│   ├── mock_data.py          # Synthetic session generator (ground truth hidden)
│   ├── tyre_analytics.py     # Pure 2-phase analytics pipeline & uncertainty engine
│   ├── race_engineer.py      # Deterministic Q&A pattern matcher (grounded in data)
│   ├── api.py                # FastAPI routes for overview, degradation, forensics, strategy
│   ├── main.py               # FastAPI entry point & CORS configuration
│   ├── validate_pipeline.py  # Hidden ground-truth accuracy validation runner
│   └── requirements.txt      # fastapi, uvicorn, pydantic, numpy, scipy
└── frontend/
    ├── index.html            # Application entry & Google Fonts
    ├── package.json          # React + Vite + Chart.js + Axios
    ├── vite.config.js        # Dev server & API proxy config
    └── src/
        ├── index.css         # Dark F1 design system (obsidian black, carbon, neon red/cyan)
        ├── main.jsx          # React entry point
        ├── App.jsx           # Tab routing & main layout
        ├── api.js            # Axios client for backend API
        ├── components/
        │   ├── F1CarParticleCanvas.jsx  # Moving dot-matrix F1 car morphing canvas
        │   ├── Navbar.jsx               # Navigation bar & stint selector
        │   ├── KPIRow.jsx               # Telemetry stats & honesty badges
        │   ├── UncertaintyConeChart.jsx # Chart.js curve with widening confidence band
        │   ├── WaterfallChart.jsx       # Lap pace delta decomposition chart
        │   ├── PitStrategyCard.jsx      # Strategy options comparison cards
        │   └── ChatWindow.jsx           # Deterministic Race Engineer interface
        └── pages/
            ├── OverviewPage.jsx         # Hero "Raw vs True", KPI row, & F1 dot car
            ├── DegradationPage.jsx      # Curve, warm-up marker, & compound table
            ├── LapForensicsPage.jsx     # Single-lap waterfall breakdown
            ├── StrategyPage.jsx         # Pit-window strategy simulator
            └── RaceEngineerPage.jsx     # Structured Q&A assistant
```

---

## 🧪 Validation & Ground-Truth Verification

Run the automated test suite to verify pipeline accuracy against hidden session parameters:

```bash
cd backend
python3 validate_pipeline.py
```

Output:
```
=================================================================
       ALL CHECKS PASSED (5/5) - PIPELINE VERIFIED       
=================================================================
```

---

## 🏃 Quick Start Guide

### 1. Launch Backend Server (Port 8000)
```bash
cd backend
pip install -r requirements.txt
python3 main.py
```
*Swagger API Docs available at:* `http://localhost:8000/docs`

### 2. Launch Frontend Dev Server (Port 3000)
```bash
cd frontend
npm install
npm run dev
```
*Open application in browser:* `http://localhost:3000`
