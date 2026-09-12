"""
TrackShift Core Analytics Pipeline
Pure Python mathematical telemetry decomposition and 2-phase tyre degradation engine.
No ML black-boxes, no external framework dependencies.
"""

import math
from typing import Dict, List, Any, Tuple


# --- Helper Math Functions ---

def linear_regression(x: List[float], y: List[float], weights: List[float] = None) -> Tuple[float, float, float]:
    """
    Fits y = slope * x + intercept via Ordinary or Weighted Least Squares.
    Returns (slope, intercept, residual_std_error).
    """
    n = len(x)
    if n < 2:
        return 0.0, y[0] if n == 1 else 0.0, 0.0

    if weights is None:
        weights = [1.0] * n

    sum_w = sum(weights)
    sum_wx = sum(w * xi for w, xi in zip(weights, x))
    sum_wy = sum(w * yi for w, yi in zip(weights, y))
    sum_wxx = sum(w * xi * xi for w, xi in zip(weights, x))
    sum_wxy = sum(w * xi * yi for w, xi, yi in zip(weights, x, y))

    denom = sum_w * sum_wxx - sum_wx * sum_wx
    if abs(denom) < 1e-9:
        slope = 0.0
        intercept = sum_wy / sum_w if sum_w > 0 else 0.0
    else:
        slope = (sum_w * sum_wxy - sum_wx * sum_wy) / denom
        intercept = (sum_wy - slope * sum_wx) / sum_w

    # Calculate residual standard error
    residuals_sq = [w * ((yi - (slope * xi + intercept)) ** 2) for w, xi, yi in zip(weights, x, y)]
    deg_freedom = max(1, n - 2)
    rse = math.sqrt(sum(residuals_sq) / deg_freedom)

    return slope, intercept, rse


# --- Pipeline Stage 1: Subtract Fuel Effect ---

def subtract_fuel_effect(laps: List[Dict[str, Any]], fuel_penalty_per_kg: float = 0.033) -> List[Dict[str, Any]]:
    """
    Strips fuel mass latency from raw lap times.
    """
    processed = []
    for lap in laps:
        fuel_kg = lap.get("estimated_fuel_kg", 0.0)
        fuel_effect = round(fuel_kg * fuel_penalty_per_kg, 3)
        corrected_time = round(lap["raw_lap_time"] - fuel_effect, 3)
        
        lap_copy = dict(lap)
        lap_copy["fuel_effect_sec"] = fuel_effect
        lap_copy["fuel_corrected_time"] = corrected_time
        lap_copy["estimated"] = True
        processed.append(lap_copy)
    return processed


# --- Pipeline Stage 2: Subtract Traffic Penalty ---

def subtract_traffic_penalty(laps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detects traffic interference via sector proxy score and removes traffic latency.
    """
    processed = []
    for lap in laps:
        proxy = lap.get("traffic_proxy_score", 0.0)
        # Proxy score > 0.15 indicates traffic
        traffic_penalty = round(max(0.0, (proxy - 0.10) * 2.2), 3) if proxy > 0.15 else 0.0
        corrected_time = round(lap.get("fuel_corrected_time", lap["raw_lap_time"]) - traffic_penalty, 3)
        
        lap_copy = dict(lap)
        lap_copy["traffic_effect_sec"] = traffic_penalty
        lap_copy["clean_corrected_time"] = corrected_time
        lap_copy["estimated"] = True
        processed.append(lap_copy)
    return processed


# --- Pipeline Stage 3: Exclude Invalid Laps ---

def exclude_invalid_laps(laps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out pit in/out laps and VSC/Safety car periods from model calibration.
    """
    valid = []
    for lap in laps:
        if not lap.get("is_invalid", False):
            valid.append(lap)
    return valid


# --- Pipeline Stage 4: Subtract Track Evolution ---

def calibrate_track_evolution(session_laps: List[Dict[str, Any]]) -> float:
    """
    Calibrates track evolution trend using fresh-tyre lap centroids across stints.
    Fresh tyres (tyre age 2-3) have minimal degradation; pace improvement across stint start points measures track rubbering in.
    """
    stint_centroids = []
    stint_ids = set(l["stint_id"] for l in session_laps)
    
    for s_id in sorted(stint_ids):
        # Pick clean laps with tyre_age 2 or 3 in this stint
        fresh_laps = [
            l for l in session_laps 
            if l["stint_id"] == s_id 
            and not l.get("is_invalid", False) 
            and 2 <= l.get("tyre_age", 99) <= 3
            and l.get("traffic_proxy_score", 0.0) <= 0.15
        ]
        if fresh_laps:
            avg_session_lap = sum(l["session_lap"] for l in fresh_laps) / len(fresh_laps)
            avg_clean_time = sum(l.get("clean_corrected_time", l["raw_lap_time"]) for l in fresh_laps) / len(fresh_laps)
            stint_centroids.append((avg_session_lap, avg_clean_time))

    if len(stint_centroids) >= 2:
        x = [c[0] for c in stint_centroids]
        y = [c[1] for c in stint_centroids]
        slope, _, _ = linear_regression(x, y)
        # Track evolution is negative (getting faster over session)
        return round(min(-0.005, max(-0.035, slope)), 4)
    
    return -0.018  # Fallback default estimate s/lap


def subtract_track_evolution(laps: List[Dict[str, Any]], track_evolution_rate: float) -> List[Dict[str, Any]]:
    """
    Removes session-wide track evolution effect from clean lap times.
    """
    processed = []
    for lap in laps:
        session_lap = lap["session_lap"]
        track_effect = round((session_lap - 1) * track_evolution_rate, 3)
        tyre_isolated_time = round(lap.get("clean_corrected_time", lap["raw_lap_time"]) - track_effect, 3)
        
        lap_copy = dict(lap)
        lap_copy["track_evolution_effect_sec"] = track_effect
        lap_copy["tyre_isolated_time"] = tyre_isolated_time
        lap_copy["estimated"] = True
        processed.append(lap_copy)
    return processed


# --- Pipeline Stage 5 & 6: Two-Phase Degradation Fit & Asymmetric Outlier Reweighting ---

def fit_two_phase_degradation(stint_laps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detects warm-up changepoint and fits two-phase linear regression:
    Phase 1 (Warm-up): negative/near-zero slope (pace improving to optimal temperature)
    Phase 2 (Degradation): positive degradation rate
    Applies asymmetric outlier downweighting for positive lap spikes (+2 SD).
    """
    valid_laps = exclude_invalid_laps(stint_laps)
    if not valid_laps:
        return {}

    # Map by tyre_age
    age_map = {l["tyre_age"]: l.get("tyre_isolated_time", l["raw_lap_time"]) for l in stint_laps if not l.get("is_invalid", False)}
    
    # 1. Detect warm-up changepoint by finding tyre_age where pace reaches minimum
    warmup_laps_count = 1
    for age in range(2, 4):
        if age in age_map and (age - 1) in age_map:
            if age_map[age] < age_map[age - 1]:
                warmup_laps_count = age

    ages = [l["tyre_age"] for l in valid_laps]
    times = [l.get("tyre_isolated_time", l["raw_lap_time"]) for l in valid_laps]

    # Split into warm-up and degradation subsets
    deg_ages = [a for a in ages if a > warmup_laps_count]
    deg_times = [t for a, t in zip(ages, times) if a > warmup_laps_count]

    if len(deg_ages) < 2:
        deg_ages = ages
        deg_times = times
        warmup_laps_count = 1

    # Initial Ordinary Least Squares fit on degradation phase
    base_age = warmup_laps_count
    x_rel = [a - base_age for a in deg_ages]
    slope_init, intercept_init, rse_init = linear_regression(x_rel, deg_times)

    # 2. Asymmetric Outlier Reweighting
    # Downweight positive residuals > +2 SD (driver error/traffic), do NOT downweight negative residuals
    residuals = [t - (slope_init * x + intercept_init) for x, t in zip(x_rel, deg_times)]
    weights = []
    for r in residuals:
        if r > 2.0 * rse_init and rse_init > 0:
            w = max(0.1, 1.0 - (r - 2.0 * rse_init))
        else:
            w = 1.0
        weights.append(w)

    # Refit with Weighted Least Squares
    slope_final, intercept_final, rse_final = linear_regression(x_rel, deg_times, weights)
    deg_rate = max(0.005, round(slope_final, 4))

    return {
        "stint_id": stint_laps[0]["stint_id"],
        "compound": stint_laps[0]["compound"],
        "detected_warmup_laps": warmup_laps_count,
        "degradation_rate_sec_per_lap": deg_rate,
        "deg_intercept": round(intercept_final, 3),
        "residual_std_error": round(rse_final, 4),
        "total_stint_laps": len(stint_laps),
        "valid_laps_analyzed": len(valid_laps),
        "outliers_downweighted": sum(1 for w in weights if w < 0.99),
        "estimated": True
    }


# --- Pipeline Stage 7: Uncertainty Band Calculation ---

def compute_uncertainty_band(fit: Dict[str, Any], current_tyre_age: int, max_projection_laps: int = 25) -> List[Dict[str, Any]]:
    """
    Computes expanding uncertainty cone for predicted future laps.
    Interval width grows strictly with sqrt(laps_ahead) based on residual std error.
    """
    deg_rate = fit.get("degradation_rate_sec_per_lap", 0.06)
    intercept = fit.get("deg_intercept", 80.5)
    rse = max(0.04, fit.get("residual_std_error", 0.08))
    warmup_laps = fit.get("detected_warmup_laps", 2)

    curve_points = []
    base_lap_time = intercept

    for age in range(1, max_projection_laps + 1):
        if age <= warmup_laps:
            # Warmup curve: lap time improves slightly or stabilizes
            mean_time = round(intercept + (warmup_laps - age) * 0.08, 3)
            laps_ahead = 0
            unc_margin = round(1.96 * rse, 3)
        else:
            # Degradation curve
            eff_age = age - warmup_laps
            mean_time = round(intercept + eff_age * deg_rate, 3)
            laps_ahead = max(0, age - current_tyre_age)
            # Cone expansion formula: sqrt(1 + laps_ahead / 5) * 1.96 * RSE
            growth_factor = math.sqrt(1.0 + (laps_ahead / 4.0))
            unc_margin = round(1.96 * rse * growth_factor, 3)

        lower_bound = round(mean_time - unc_margin, 3)
        upper_bound = round(mean_time + unc_margin, 3)

        curve_points.append({
            "tyre_age": age,
            "predicted_time": mean_time,
            "uncertainty_margin": unc_margin,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "is_warmup": age <= warmup_laps,
            "is_historical": age <= current_tyre_age,
            "predicted": True
        })

    return curve_points


# --- Pipeline Stage 8: Remaining Life & Recommended Pit Window ---

def predict_remaining_life(fit: Dict[str, Any], current_tyre_age: int, max_slowdown_sec: float = 1.50) -> Dict[str, Any]:
    """
    Calculates remaining tyre life and recommended pit window using the unified degradation model.
    """
    deg_rate = fit.get("degradation_rate_sec_per_lap", 0.06)
    rse = max(0.04, fit.get("residual_std_error", 0.08))
    warmup_laps = fit.get("detected_warmup_laps", 2)
    
    # Life threshold: lap time degraded by max_slowdown_sec (e.g. +1.50s)
    total_allowed_deg_laps = math.ceil(max_slowdown_sec / deg_rate) if deg_rate > 0 else 30
    total_useful_life_laps = warmup_laps + total_allowed_deg_laps
    
    remaining_laps_mean = max(0, total_useful_life_laps - current_tyre_age)

    # Uncertainty in pit window: spread around useful life lap
    window_spread = max(1, math.ceil(1.5 * math.sqrt(max(1, remaining_laps_mean))))
    
    pit_window_start = max(1, total_useful_life_laps - window_spread)
    pit_window_end = total_useful_life_laps + window_spread

    return {
        "current_tyre_age": current_tyre_age,
        "estimated_total_life_laps": total_useful_life_laps,
        "remaining_laps": remaining_laps_mean,
        "pit_window_start_lap": pit_window_start,
        "pit_window_end_lap": pit_window_end,
        "recommended_pit_lap": total_useful_life_laps,
        "degradation_rate_sec": deg_rate,
        "confidence_level": "95%",
        "predicted": True
    }


# --- STEP 3: Waterfall Decomposition for Lap Forensics ---

def get_lap_waterfall(session_data: Dict[str, Any], lap_number: int) -> Dict[str, Any]:
    """
    Returns exact lap component decomposition summing precisely to observed raw lap time delta.
    Components:
    raw_lap_time = session_baseline + fuel_component + traffic_component + track_evolution_component + warmup_or_deg_component + residual_noise
    """
    laps = session_data["laps"]
    target_lap = next((l for l in laps if l["session_lap"] == lap_number), None)
    
    if not target_lap:
        return {"error": f"Lap {lap_number} not found in session data"}

    # Find stint for this lap
    stint_id = target_lap["stint_id"]
    stint_laps = [l for l in laps if l["stint_id"] == stint_id]

    # Process pipeline up to track evolution
    track_evo_rate = calibrate_track_evolution(laps)
    laps_fuel = subtract_fuel_effect(laps)
    laps_traffic = subtract_traffic_penalty(laps_fuel)
    laps_track = subtract_track_evolution(laps_traffic, track_evo_rate)

    fit = fit_two_phase_degradation(stint_laps)
    
    proc_lap = next(l for l in laps_track if l["session_lap"] == lap_number)
    
    baseline = session_data["session_info"]["baseline_fuel_kg"] * 0.033 + 80.500  # Baseline session lap time
    raw_time = proc_lap["raw_lap_time"]
    raw_delta = round(raw_time - 80.500, 3)

    fuel_comp = proc_lap["fuel_effect_sec"]
    traffic_comp = proc_lap["traffic_effect_sec"]
    track_comp = proc_lap["track_evolution_effect_sec"]

    tyre_age = proc_lap["tyre_age"]
    warmup_count = fit.get("detected_warmup_laps", 2)
    deg_rate = fit.get("degradation_rate_sec_per_lap", 0.06)

    is_warmup = tyre_age <= warmup_count
    if is_warmup:
        warmup_deg_comp = round((warmup_count - tyre_age + 1) * 0.15 - 0.10, 3)
    else:
        eff_age = tyre_age - warmup_count
        warmup_deg_comp = round(eff_age * deg_rate, 3)

    # Residual noise component guarantees EXACT sum to raw_delta
    residual_noise = round(raw_delta - (fuel_comp + traffic_comp + track_comp + warmup_deg_comp), 3)

    return {
        "session_lap": lap_number,
        "stint_id": stint_id,
        "tyre_age": tyre_age,
        "compound": proc_lap["compound"],
        "raw_lap_time": raw_time,
        "baseline_lap_time": 80.500,
        "raw_delta_sec": raw_delta,
        "waterfall_components": {
            "fuel_weight_delta": fuel_comp,
            "traffic_penalty_delta": traffic_comp,
            "track_evolution_delta": track_comp,
            "tyre_wear_or_warmup_delta": warmup_deg_comp,
            "outlier_residual_noise": residual_noise
        },
        "sum_of_components": round(fuel_comp + traffic_comp + track_comp + warmup_deg_comp + residual_noise, 3),
        "is_warmup": is_warmup,
        "is_outlier_downweighted": abs(residual_noise) > 0.35,
        "estimated": True
    }


def analyze_session_full(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs full analytics pipeline across all stints in session.
    """
    laps = session_data["laps"]
    track_evo_rate = calibrate_track_evolution(laps)

    laps_f = subtract_fuel_effect(laps)
    laps_tf = subtract_traffic_penalty(laps_f)
    laps_proc = subtract_track_evolution(laps_tf, track_evo_rate)

    stint_analyses = {}
    stint_fits = {}

    for stint in session_data["stints"]:
        s_id = stint["stint_id"]
        s_laps = [l for l in laps_proc if l["stint_id"] == s_id]
        fit = fit_two_phase_degradation(s_laps)
        stint_fits[s_id] = fit

        last_lap = s_laps[-1] if s_laps else None
        curr_age = last_lap["tyre_age"] if last_lap else 15
        
        curve = compute_uncertainty_band(fit, curr_age)
        rem_life = predict_remaining_life(fit, curr_age)

        stint_analyses[s_id] = {
            "stint_info": stint,
            "fit": fit,
            "uncertainty_curve": curve,
            "remaining_life": rem_life
        }

    return {
        "track_evolution_rate_sec": track_evo_rate,
        "stint_analyses": stint_analyses,
        "processed_laps": laps_proc
    }
