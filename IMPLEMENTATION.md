# TrackShift Implementation & Telemetry Analytics Methodology

This document details the mathematical algorithms and implementation mechanics behind TrackShift.

---

## 1. Mathematical Pipeline Architecture

Raw lap times in Formula 1 practice and race sessions are noisy and heavily confounded:
$$\text{Raw Lap Time} = \text{Baseline Pace} + \text{Fuel Latency} + \text{Track Evolution} + \text{Traffic Penalty} + \text{Warm-up/Degradation} + \epsilon$$

TrackShift isolates tyre degradation through a strict sequential decomposition pipeline (`backend/tyre_analytics.py`):

### Stage 1: Fuel Mass Correction
Fuel is consumed linearly across the session:
$$\text{Fuel}_{\text{kg}}(L) = 110.0 - (L - 1) \times \left(\frac{110 - 2}{L_{\text{total}} - 1}\right)$$
$$\text{Lap}_{\text{fuel\_corrected}} = \text{Lap}_{\text{raw}} - \left(\text{Fuel}_{\text{kg}}(L) \times 0.033\text{s/kg}\right)$$

### Stage 2: Traffic Penalty Removal
Sector proxy scores are evaluated per lap. Laps with traffic proxy $> 0.15$ are corrected for traffic latency:
$$\text{Penalty}_{\text{traffic}} = \max\left(0, (\text{Proxy} - 0.10) \times 2.2\right)$$

### Stage 3: Track Rubbering-In Calibration
Track evolution is calibrated using fresh-tyre lap centroids (tyre age 2-3) across different stints in the session. Because fresh tyres have $\approx 0$ degradation, the lap time delta across stint start points measures pure track rubbering-in ($\approx -0.018\text{s/lap}$):
$$\text{Lap}_{\text{isolated}} = \text{Lap}_{\text{clean}} - (L_{\text{session}} - 1) \times \text{Rate}_{\text{evolution}}$$

### Stage 4: Two-Phase Warm-up & Degradation Model
F1 tyres experience an initial warm-up phase (1-3 laps) where tyre temperature rises and pace improves before linear degradation begins.
1. **Changepoint Detection**: Finds local minimum in pace for tyre age $\le 3$.
2. **Phase 1 (Warm-up)**: Modeled with negative slope / stabilizing curve.
3. **Phase 2 (Degradation)**: Linear regression fitted on post-warmup laps.

### Stage 5: Asymmetric Outlier Reweighting
Drivers aim for consistent lap times. Anomalous slowdowns are caused by lockups or minor traffic, whereas anomalous quick laps rarely happen. Therefore:
- Residuals $> +2 \cdot \text{RSE}$ are downweighted ($w = 1.0 - (r - 2\sigma)$).
- Negative residuals (fast laps) retain full weight ($w = 1.0$).

### Stage 6: Expanding Uncertainty Cone
For predicted future laps $N$ ahead of current tyre age, prediction uncertainty expands according to:
$$\text{Margin}(N) = 1.96 \times \text{RSE} \times \sqrt{1 + \frac{N}{4}}$$

---

## 2. Interactive F1 Dot Particle Matrix (`F1CarParticleCanvas`)

The Overview hero section implements a custom HTML5 Canvas rendering **380+ floating telemetry particles**.
- **Geometry**: Mathematically defines target coordinates for an F1 car silhouette (nose cone, front wing, halo cockpit, sidepods, rear wing, wheels).
- **Physics**: Particles experience spring forces toward target shape points, spring damping ($0.90$), and mouse repulsion vector forces ($F \propto (70 - d)$).
- **Aerostream**: A subset of particles streams horizontally across the canvas following sinusoidal air-flow curves.
- **Compound Reactivity**: Glow colors adapt dynamically to active compound selection (`#FF1801` Soft, `#FFD700` Medium, `#FFFFFF` Hard).

---

## 3. Ground-Truth Validation Methodology

To ensure analytical integrity without leaking ground truth into model fitting:
- `mock_data.py` generates synthetic telemetry with hidden known parameters (`true_degradation_rate`, `true_warmup_laps`, `true_track_evolution_rate`).
- `tyre_analytics.py` receives ONLY observable fields (`raw_lap_time`, `estimated_fuel_kg`, `traffic_proxy_score`).
- `validate_pipeline.py` imports `get_ground_truth()` independently to assert that recovered degradation rates match ground truth within $0.04\text{s/lap}$, warm-up windows match within $\pm 1$ lap, and waterfall components sum to observed deltas with zero discrepancy.
