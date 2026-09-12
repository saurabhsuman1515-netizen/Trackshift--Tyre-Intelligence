"""
TrackShift Deterministic Race Engineer Engine
Intent-based Q&A assistant grounded strictly in mathematically computed telemetry data.
NOT an LLM, NO halluncinations.
"""

import re
from typing import Dict, Any, List
import tyre_analytics


def get_example_questions() -> List[Dict[str, str]]:
    """Returns supported question patterns for UI chip recommendations."""
    return [
        {"category": "Pit Strategy", "question": "When should we pit for stint 1?"},
        {"category": "Lap Forensics", "question": "Why was lap 6 slow?"},
        {"category": "Tyre Temperature", "question": "Is the tyre still warming up on lap 2?"},
        {"category": "Uncertainty", "question": "How confident are you about lap +10?"},
        {"category": "Compound Comparison", "question": "Which compound degrades fastest?"}
    ]


def answer_race_engineer_query(query: str, session_data: Dict[str, Any], stint_id: str = "stint_1", lap_number: int = None) -> Dict[str, Any]:
    """
    Classifies user intent via keyword patterns and extracts relevant computed analytics.
    Every response cites the exact math model field it is grounded in.
    """
    q_clean = query.lower().strip()
    
    # Process full session analytics
    analysis = tyre_analytics.analyze_session_full(session_data)
    stint_analyses = analysis["stint_analyses"]
    
    # Fallback to stint_1 if stint_id invalid
    if stint_id not in stint_analyses:
        stint_id = "stint_1"
        
    stint_data = stint_analyses[stint_id]
    fit = stint_data["fit"]
    rem_life = stint_data["remaining_life"]
    unc_curve = stint_data["uncertainty_curve"]
    compound = fit.get("compound", "SOFT")

    # Extract any lap number mentioned in the query up front so every intent
    # branch below can share it (previously only set inside Intent 2).
    lap_match = re.search(r"lap\s*(\d+)", q_clean)
    mentioned_lap_num = int(lap_match.group(1)) if lap_match else None

    # Intent 1: Pit Window & Strategy
    if any(k in q_clean for k in ["pit", "stop", "box", "when to pit", "window"]):
        pit_start = rem_life["pit_window_start_lap"]
        pit_end = rem_life["pit_window_end_lap"]
        rec_lap = rem_life["recommended_pit_lap"]
        rem_laps = rem_life["remaining_laps"]
        
        answer = (
            f"For stint **{stint_id.upper()}** on **{compound}** tyres, our pit window opens at lap **{pit_start}** "
            f"and closes at lap **{pit_end}** (optimal pit lap: **{rec_lap}**).\n\n"
            f"You have approximately **{rem_laps} laps** of remaining tyre performance before exceeding the +1.50s degradation threshold."
        )
        citation = "Grounded in `predict_remaining_life()` derivation using fit degradation rate and 95% uncertainty spread."
        return {
            "query": query,
            "intent": "PIT_STRATEGY",
            "answer": answer,
            "grounding_citation": citation,
            "confidence": "HIGH",
            "estimated": True
        }

    # Intent 2: Tyre Warm-up (checked BEFORE Lap Forensics — a query like
    # "Is the tyre still warming up on lap 2?" mentions a lap number too, and
    # must not be swallowed by the generic lap-number forensics match below)
    if any(k in q_clean for k in ["warm", "heat", "temperature", "warmup", "green"]):
        warmup_laps = fit["detected_warmup_laps"]
        check_lap = mentioned_lap_num if mentioned_lap_num else 2
        is_warmup = check_lap <= warmup_laps

        status_str = "STILL WARMING UP" if is_warmup else "FULLY WARMED UP (IN DEGRADATION PHASE)"
        answer = (
            f"On lap **{check_lap}** of stint **{stint_id.upper()}** ({compound}), tyres are **{status_str}**.\n\n"
            f"Detected warm-up phase spans the first **{warmup_laps} lap(s)** of the stint before positive degradation begins."
        )
        citation = "Grounded in `fit_two_phase_degradation()` rolling slope changepoint detection."
        return {
            "query": query,
            "intent": "TYRE_WARMUP",
            "answer": answer,
            "grounding_citation": citation,
            "confidence": "HIGH",
            "estimated": True
        }

    # Intent 3: Lap Forensics / Why lap X was slow
    if mentioned_lap_num is not None or "why" in q_clean or "slow" in q_clean:
        target_lap_num = mentioned_lap_num if mentioned_lap_num is not None else (lap_number if lap_number else 6)
        waterfall = tyre_analytics.get_lap_waterfall(session_data, target_lap_num)
        
        if "error" in waterfall:
            return {
                "query": query,
                "intent": "LAP_FORENSICS",
                "answer": f"Lap {target_lap_num} was not found in this session.",
                "grounding_citation": "Grounding check failed: Lap index out of bounds.",
                "confidence": "NONE",
                "estimated": False
            }

        comps = waterfall["waterfall_components"]
        raw_delta = waterfall["raw_delta_sec"]
        main_driver = max(comps.items(), key=lambda x: abs(x[1]))
        
        driver_names = {
            "fuel_weight_delta": "Fuel Weight Latency",
            "traffic_penalty_delta": "Traffic Interference",
            "track_evolution_delta": "Track Evolution",
            "tyre_wear_or_warmup_delta": "Tyre Wear & Warm-up",
            "outlier_residual_noise": "Driver Outlier / Traffic Noise"
        }
        
        answer = (
            f"Lap **{target_lap_num}** registered a raw slowdown delta of **+{raw_delta:.3f}s** over baseline.\n\n"
            f"Decomposition break-down:\n"
            f"• **Traffic Penalty**: +{comps['traffic_penalty_delta']:.3f}s\n"
            f"• **Tyre Wear / Warm-up**: +{comps['tyre_wear_or_warmup_delta']:.3f}s\n"
            f"• **Fuel Weight**: +{comps['fuel_weight_delta']:.3f}s\n"
            f"• **Driver Error / Spike**: +{comps['outlier_residual_noise']:.3f}s\n\n"
            f"Primary factor: **{driver_names.get(main_driver[0], main_driver[0])}** ({main_driver[1]:+.3f}s)."
        )
        citation = f"Grounded in `get_lap_waterfall(session, lap_number={target_lap_num})` additive decomposition."
        return {
            "query": query,
            "intent": "LAP_FORENSICS",
            "answer": answer,
            "grounding_citation": citation,
            "confidence": "EXACT",
            "estimated": True
        }

    # Intent 4: Uncertainty / Confidence
    if any(k in q_clean for k in ["confident", "confidence", "uncertainty", "cone", "ahead", "+"]):
        horizon_match = re.search(r"\+(\d+)", q_clean)
        laps_ahead = int(horizon_match.group(1)) if horizon_match else 10
        
        target_pt = next((p for p in unc_curve if p["tyre_age"] == fit["valid_laps_analyzed"] + laps_ahead), unc_curve[-1])
        margin = target_pt["uncertainty_margin"]
        
        answer = (
            f"For **+{laps_ahead} laps** ahead (Tyre Age {target_pt['tyre_age']}), our prediction uncertainty margin is **±{margin:.3f}s**.\n\n"
            f"Predicted Pace Range: **{target_pt['lower_bound']:.3f}s** to **{target_pt['upper_bound']:.3f}s**.\n"
            f"Uncertainty expands proportional to $\\sqrt{{\\text{{laps ahead}}}}$ off residual standard error $\\sigma={fit['residual_std_error']:.3f}s$."
        )
        citation = f"Grounded in `compute_uncertainty_band()` with RSE={fit['residual_std_error']}s."
        return {
            "query": query,
            "intent": "UNCERTAINTY_CONE",
            "answer": answer,
            "grounding_citation": citation,
            "confidence": "HIGH",
            "estimated": True
        }

    # Intent 5: Compound Comparison
    if any(k in q_clean for k in ["compound", "fastest", "soft", "medium", "hard", "compare", "rate"]):
        comp_summary = []
        for s_id, s_data in stint_analyses.items():
            f = s_data["fit"]
            comp_summary.append(f"• **{f['compound']}** (Stint {s_id}): **{f['degradation_rate_sec_per_lap']:.4f}s / lap** (Warm-up: {f['detected_warmup_laps']} laps)")
        
        fastest_deg = min(stint_analyses.values(), key=lambda x: x["fit"]["degradation_rate_sec_per_lap"])["fit"]
        slowest_deg = max(stint_analyses.values(), key=lambda x: x["fit"]["degradation_rate_sec_per_lap"])["fit"]
        
        answer = (
            f"Degradation rate comparison across analyzed compounds:\n\n" +
            "\n".join(comp_summary) + "\n\n" +
            f"Highest degradation: **{slowest_deg['compound']}** ({slowest_deg['degradation_rate_sec_per_lap']:.4f}s/lap).\n" +
            f"Lowest degradation: **{fastest_deg['compound']}** ({fastest_deg['degradation_rate_sec_per_lap']:.4f}s/lap)."
        )
        citation = "Grounded in comparative `fit_two_phase_degradation()` across all session stint fits."
        return {
            "query": query,
            "intent": "COMPOUND_COMPARISON",
            "answer": answer,
            "grounding_citation": citation,
            "confidence": "EXACT",
            "estimated": True
        }

    # Honest Fallback
    return {
        "query": query,
        "intent": "UNKNOWN",
        "answer": (
            "I cannot answer that specific query yet. As a deterministic telemetry assistant, "
            "I only answer questions grounded directly in computed tyre wear, pit windows, lap forensics, or degradation uncertainty."
        ),
        "grounding_citation": "Deterministic fallback (no LLM generation permitted).",
        "confidence": "NONE",
        "estimated": False
    }
