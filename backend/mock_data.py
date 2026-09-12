"""
TrackShift Synthetic Data Generator with Hidden Ground Truth
Generates single-car F1 practice/session telemetry data with hidden underlying metrics.
Uses standard library random/math for zero-dependency portability.
"""

import random
import math

# Ground Truth Definition Constants (Hidden from analytics pipeline)
GROUND_TRUTH = {
    "session_total_laps": 52,
    "baseline_pace": 80.500,  # 1:20.500 baseline lap time in seconds
    "initial_fuel_kg": 110.0,
    "final_fuel_kg": 2.0,
    "fuel_time_penalty_per_kg": 0.033,  # ~0.033s slower per kg of fuel
    "true_track_evolution_rate": -0.018,  # Track gains grip: ~0.018s faster per session lap
    "stints": {
        "stint_1": {
            "stint_id": "stint_1",
            "compound": "SOFT",
            "start_lap": 1,
            "end_lap": 17,
            "true_degradation_rate": 0.092,  # s/lap
            "true_warmup_laps": 2,           # Laps 1-2 improve (-0.12s/lap) before degrading
            "true_traffic_laps": [6, 12],
            "traffic_penalties": {6: 1.45, 12: 2.10},
            "invalid_laps": {1: "OUT_LAP", 17: "IN_LAP"}
        },
        "stint_2": {
            "stint_id": "stint_2",
            "compound": "MEDIUM",
            "start_lap": 18,
            "end_lap": 35,
            "true_degradation_rate": 0.058,  # s/lap
            "true_warmup_laps": 2,
            "true_traffic_laps": [24, 30],
            "traffic_penalties": {24: 0.95, 30: 1.80},
            "invalid_laps": {18: "OUT_LAP", 27: "VIRTUAL_SAFETY_CAR", 35: "IN_LAP"}
        },
        "stint_3": {
            "stint_id": "stint_3",
            "compound": "HARD",
            "start_lap": 36,
            "end_lap": 52,
            "true_degradation_rate": 0.038,  # s/lap
            "true_warmup_laps": 3,           # Hard tyre takes 3 laps to warm up
            "true_traffic_laps": [42, 48],
            "traffic_penalties": {42: 1.20, 48: 0.85},
            "invalid_laps": {36: "OUT_LAP", 52: "IN_LAP"}
        }
    }
}


def generate_session(seed: int = 42) -> dict:
    """
    Generates observable telemetry data for the session.
    Guaranteed NOT to contain any keys prefixed with 'true_' or hidden ground-truth variables.
    """
    random.seed(seed)

    gt = GROUND_TRUTH
    total_laps = gt["session_total_laps"]
    fuel_per_lap = (gt["initial_fuel_kg"] - gt["final_fuel_kg"]) / (total_laps - 1)

    laps_data = []

    for stint_key, stint in gt["stints"].items():
        compound = stint["compound"]
        start_lap = stint["start_lap"]
        end_lap = stint["end_lap"]
        warmup_count = stint["true_warmup_laps"]
        deg_rate = stint["true_degradation_rate"]
        traffic_map = stint["traffic_penalties"]
        invalid_map = stint["invalid_laps"]

        for session_lap in range(start_lap, end_lap + 1):
            tyre_age = session_lap - start_lap + 1

            # 1. Fuel effect across the session
            current_fuel = gt["initial_fuel_kg"] - (session_lap - 1) * fuel_per_lap
            fuel_penalty = current_fuel * gt["fuel_time_penalty_per_kg"]

            # 2. Track evolution (session wide improvement)
            track_evolution_delta = (session_lap - 1) * gt["true_track_evolution_rate"]

            # 3. Warm-up vs Degradation effect
            if tyre_age <= warmup_count:
                # Warm-up phase: tyre gains temperature and grip
                warmup_deg_delta = (warmup_count - tyre_age + 1) * 0.15 - 0.10
            else:
                # Degradation phase: linear degradation starting after warm-up
                effective_deg_laps = tyre_age - warmup_count
                warmup_deg_delta = effective_deg_laps * deg_rate

            # 4. Traffic penalty
            traffic_penalty = traffic_map.get(session_lap, 0.0)

            # 5. Invalid lap flag
            invalid_flag = invalid_map.get(session_lap, None)
            if invalid_flag == "OUT_LAP":
                out_lap_penalty = 12.5
            elif invalid_flag == "IN_LAP":
                out_lap_penalty = 8.0
            elif invalid_flag == "VIRTUAL_SAFETY_CAR":
                out_lap_penalty = 22.0
            else:
                out_lap_penalty = 0.0

            # 6. Random noise: small symmetric noise + occasional POSITIVE spike (driver error/snap)
            normal_noise = random.gauss(0, 0.04)
            positive_spike = random.expovariate(1.0 / 0.12) if random.random() < 0.15 else 0.0
            noise = normal_noise + positive_spike

            # Raw observed lap time
            raw_time = (
                gt["baseline_pace"]
                + fuel_penalty
                + track_evolution_delta
                + warmup_deg_delta
                + traffic_penalty
                + out_lap_penalty
                + noise
            )

            # Sector proxy noise for traffic score computation in pipeline
            traffic_proxy_score = round(min(1.0, traffic_penalty / 2.0 + max(0, noise * 0.2)), 3)

            lap_record = {
                "session_lap": session_lap,
                "stint_id": stint["stint_id"],
                "tyre_age": tyre_age,
                "compound": compound,
                "raw_lap_time": round(float(raw_time), 3),
                "estimated_fuel_kg": round(float(current_fuel), 2),
                "traffic_proxy_score": traffic_proxy_score,
                "is_invalid": invalid_flag is not None,
                "invalid_reason": invalid_flag,
                "sector_1": round(float(raw_time * 0.28 + random.gauss(0, 0.02)), 3),
                "sector_2": round(float(raw_time * 0.42 + random.gauss(0, 0.02)), 3),
                "sector_3": round(float(raw_time * 0.30 + random.gauss(0, 0.02)), 3),
            }
            laps_data.append(lap_record)

    return {
        "session_info": {
            "driver": "VER 01",
            "car": "RB20",
            "circuit": "Silverstone Circuit",
            "session_type": "FP2",
            "total_laps": total_laps,
            "baseline_fuel_kg": gt["initial_fuel_kg"]
        },
        "stints": [
            {"stint_id": "stint_1", "compound": "SOFT", "laps_count": 17, "start_lap": 1, "end_lap": 17},
            {"stint_id": "stint_2", "compound": "MEDIUM", "laps_count": 18, "start_lap": 18, "end_lap": 35},
            {"stint_id": "stint_3", "compound": "HARD", "laps_count": 17, "start_lap": 36, "end_lap": 52}
        ],
        "laps": laps_data
    }


def get_ground_truth() -> dict:
    """
    Returns the hidden ground truth parameters.
    ONLY to be imported by validate_pipeline.py for automated verification.
    """
    return GROUND_TRUTH
