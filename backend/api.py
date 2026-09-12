"""
TrackShift FastAPI API Layer
Exposes analytical engine & telemetry data.
Pure orchestration layer calling tyre_analytics, mock_data, and race_engineer.
"""

import math

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import mock_data
import tyre_analytics
import race_engineer

router = APIRouter()

# Global session state container
CURRENT_SESSION = mock_data.generate_session()


class StrategyRequest(BaseModel):
    stint_id: str = "stint_1"
    pit_in_n_laps: int = 5
    target_stint_laps: int = 25


class AskRequest(BaseModel):
    query: str
    stint_id: str = "stint_1"
    lap_number: Optional[int] = None


@router.get("/meta")
def get_metadata():
    """Returns session header info & simulation mode flag."""
    return {
        "mode": "SIMULATION MODE",
        "session_info": CURRENT_SESSION["session_info"],
        "stints_summary": CURRENT_SESSION["stints"],
        "total_laps": len(CURRENT_SESSION["laps"]),
        "estimated": True
    }


@router.get("/stints")
def get_stints():
    """Returns all stints in current session."""
    return {"stints": CURRENT_SESSION["stints"]}


@router.post("/session/regenerate")
def regenerate_session(seed: Optional[int] = 42):
    """Regenerates synthetic session data."""
    global CURRENT_SESSION
    CURRENT_SESSION = mock_data.generate_session(seed=seed)
    return {"message": "Session data regenerated successfully", "seed": seed}


@router.get("/overview")
def get_overview(stintId: str = "stint_1"):
    """
    Hero Overview metric cards comparing RAW SLOWDOWN vs TRUE DEGRADATION,
    plus overall stint KPIs and remaining tyre life.
    """
    laps = CURRENT_SESSION["laps"]
    stint_laps = [l for l in laps if l["stint_id"] == stintId]
    if not stint_laps:
        stintId = "stint_1"
        stint_laps = [l for l in laps if l["stint_id"] == stintId]

    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    stint_ana = analysis["stint_analyses"][stintId]
    fit = stint_ana["fit"]
    rem_life = stint_ana["remaining_life"]

    valid_stint_laps = [l for l in stint_laps if not l.get("is_invalid", False)]
    first_lap = valid_stint_laps[0]
    last_lap = valid_stint_laps[-1]

    raw_slowdown = round(last_lap["raw_lap_time"] - first_lap["raw_lap_time"], 3)
    true_deg_rate = fit.get("degradation_rate_sec_per_lap", 0.06)
    stint_deg_total = round(true_deg_rate * (len(valid_stint_laps) - fit.get("detected_warmup_laps", 2)), 3)

    return {
        "stint_id": stintId,
        "compound": fit.get("compound", "SOFT"),
        "hero_comparison": {
            "raw_slowdown_sec": raw_slowdown,
            "raw_slowdown_label": "RAW SLOWDOWN (Uncorrected)",
            "true_degradation_total_sec": stint_deg_total,
            "true_degradation_rate_per_lap": true_deg_rate,
            "true_degradation_label": "TRUE DEGRADATION (Fuel & Track Stripped)",
            "isolated_fuel_correction": round(first_lap["estimated_fuel_kg"] * 0.033 - last_lap["estimated_fuel_kg"] * 0.033, 3)
        },
        "kpis": {
            "compound": fit.get("compound", "SOFT"),
            "current_tyre_age": last_lap["tyre_age"],
            "degradation_rate_sec": true_deg_rate,
            "uncertainty_band_margin": round(1.96 * fit.get("residual_std_error", 0.08), 3),
            "remaining_life_laps": rem_life["remaining_laps"],
            "recommended_pit_window": f"Lap {rem_life['pit_window_start_lap']} - {rem_life['pit_window_end_lap']}",
            "warmup_laps": fit.get("detected_warmup_laps", 2)
        },
        "estimated": True
    }


@router.get("/degradation")
def get_degradation(stintId: str = "stint_1"):
    """
    Degradation curve data, widening uncertainty band points,
    warm-up window markers, and cross-compound comparison table.
    """
    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    if stintId not in analysis["stint_analyses"]:
        stintId = "stint_1"

    stint_ana = analysis["stint_analyses"][stintId]
    
    # Soft vs Medium vs Hard comparison table
    comparison_table = []
    for s_id, s_data in analysis["stint_analyses"].items():
        f = s_data["fit"]
        r = s_data["remaining_life"]
        comparison_table.append({
            "stint_id": s_id,
            "compound": f["compound"],
            "degradation_rate_sec_per_lap": f["degradation_rate_sec_per_lap"],
            "detected_warmup_laps": f["detected_warmup_laps"],
            "residual_std_error": f["residual_std_error"],
            "remaining_laps": r["remaining_laps"],
            "recommended_pit_lap": r["recommended_pit_lap"]
        })

    return {
        "stint_id": stintId,
        "fit": stint_ana["fit"],
        "uncertainty_curve": stint_ana["uncertainty_curve"],
        "warmup_laps": stint_ana["fit"]["detected_warmup_laps"],
        "comparison_table": comparison_table,
        "estimated": True
    }


@router.get("/laps")
def get_laps(stintId: Optional[str] = None):
    """Returns lap records, optionally filtered by stintId."""
    laps = CURRENT_SESSION["laps"]
    if stintId:
        laps = [l for l in laps if l["stint_id"] == stintId]
    return {"laps": laps}


@router.get("/degradation-curve")
def get_degradation_curve(stintId: str = "stint_1"):
    """Returns prediction uncertainty points for stint."""
    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    if stintId not in analysis["stint_analyses"]:
        stintId = "stint_1"
    return {"uncertainty_curve": analysis["stint_analyses"][stintId]["uncertainty_curve"], "predicted": True}


@router.get("/compare")
def get_compare():
    """Returns cross-compound degradation comparison."""
    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    table = []
    for s_id, s_data in analysis["stint_analyses"].items():
        f = s_data["fit"]
        r = s_data["remaining_life"]
        table.append({
            "stint_id": s_id,
            "compound": f["compound"],
            "degradation_rate_sec_per_lap": f["degradation_rate_sec_per_lap"],
            "detected_warmup_laps": f["detected_warmup_laps"],
            "residual_std_error": f["residual_std_error"],
            "remaining_laps": r["remaining_laps"],
            "recommended_pit_lap": r["recommended_pit_lap"]
        })
    return {"compounds": table, "estimated": True}


@router.get("/remaining-life")
def get_remaining_life(stintId: str = "stint_1"):
    """Returns remaining tyre life and recommended pit window."""
    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    if stintId not in analysis["stint_analyses"]:
        stintId = "stint_1"
    return analysis["stint_analyses"][stintId]["remaining_life"]


@router.get("/lap-forensics")
def get_lap_forensics(lapNumber: int = 6):
    """Returns additive waterfall decomposition for specified lap."""
    res = tyre_analytics.get_lap_waterfall(CURRENT_SESSION, lapNumber)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.post("/strategy")
def simulate_strategy(req: StrategyRequest):
    """
    Simulates three strategy choices: Stay Out vs Pit Now vs Pit in N Laps.
    Calculates total stint time delta with uncertainty range.
    """
    analysis = tyre_analytics.analyze_session_full(CURRENT_SESSION)
    stint_id = req.stint_id if req.stint_id in analysis["stint_analyses"] else "stint_1"
    stint_data = analysis["stint_analyses"][stint_id]
    
    fit = stint_data["fit"]
    deg_rate = fit.get("degradation_rate_sec_per_lap", 0.06)
    rse = max(0.04, fit.get("residual_std_error", 0.08))
    
    current_laps = fit["valid_laps_analyzed"]
    target_total = req.target_stint_laps
    remaining_total = max(1, target_total - current_laps)
    
    pit_loss_sec = 21.5  # Pit stop time loss in seconds

    # 1. Stay Out Option: run remaining laps on degraded tyres
    stay_out_deg_loss = round(sum((current_laps + i) * deg_rate for i in range(1, remaining_total + 1)), 2)
    stay_out_unc = round(1.96 * rse * math.sqrt(remaining_total), 2)
    
    # 2. Pit Now Option: pay pit loss, fresh tyres (zero deg for remaining)
    pit_now_time_delta = round(pit_loss_sec + sum(i * 0.04 for i in range(1, max(1, remaining_total))), 2)
    pit_now_unc = round(1.96 * rse * 0.5, 2)
    
    # 3. Pit in N Laps Option
    n = min(req.pit_in_n_laps, remaining_total - 1)
    before_pit_deg = sum((current_laps + i) * deg_rate for i in range(1, n + 1))
    after_pit_laps = max(0, remaining_total - n)
    after_pit_deg = sum(i * 0.04 for i in range(1, after_pit_laps + 1))
    pit_in_n_time_delta = round(pit_loss_sec + before_pit_deg + after_pit_deg, 2)
    pit_in_n_unc = round(1.96 * rse * math.sqrt(n + 1), 2)

    return {
        "stint_id": stint_id,
        "compound": fit["compound"],
        "simulation_horizon_laps": remaining_total,
        "options": [
            {
                "id": "stay_out",
                "title": "Option A: Stay Out",
                "action": "Do not pit; extend current stint",
                "projected_time_delta_sec": stay_out_deg_loss,
                "uncertainty_margin_sec": stay_out_unc,
                "lower_bound_sec": round(stay_out_deg_loss - stay_out_unc, 2),
                "upper_bound_sec": round(stay_out_deg_loss + stay_out_unc, 2),
                "recommendation": "RISKY" if stay_out_deg_loss > pit_now_time_delta else "VIABLE",
                "predicted": True
            },
            {
                "id": "pit_now",
                "title": "Option B: Pit Now",
                "action": "Box this lap for fresh tyres",
                "projected_time_delta_sec": pit_now_time_delta,
                "uncertainty_margin_sec": pit_now_unc,
                "lower_bound_sec": round(pit_now_time_delta - pit_now_unc, 2),
                "upper_bound_sec": round(pit_now_time_delta + pit_now_unc, 2),
                "recommendation": "OPTIMAL" if pit_now_time_delta < stay_out_deg_loss and pit_now_time_delta <= pit_in_n_time_delta else "ALTERNATIVE",
                "predicted": True
            },
            {
                "id": "pit_in_n",
                "title": f"Option C: Pit in {n} Laps",
                "action": f"Box on lap {current_laps + n}",
                "projected_time_delta_sec": pit_in_n_time_delta,
                "uncertainty_margin_sec": pit_in_n_unc,
                "lower_bound_sec": round(pit_in_n_time_delta - pit_in_n_unc, 2),
                "upper_bound_sec": round(pit_in_n_time_delta + pit_in_n_unc, 2),
                "recommendation": "BALANCED",
                "predicted": True
            }
        ]
    }


@router.post("/ask")
def ask_race_engineer(req: AskRequest):
    """Deterministic Race Engineer Q&A endpoint."""
    return race_engineer.answer_race_engineer_query(
        query=req.query,
        session_data=CURRENT_SESSION,
        stint_id=req.stint_id,
        lap_number=req.lap_number
    )


@router.get("/ask/examples")
def get_ask_examples():
    """Returns example recognized Race Engineer question chips."""
    return {"examples": race_engineer.get_example_questions()}


@router.get("/demo")
def get_demo_summary():
    """Quick validation state summary."""
    return {
        "status": "OPERATIONAL",
        "mode": "SIMULATION MODE",
        "active_stints": len(CURRENT_SESSION["stints"]),
        "total_laps_loaded": len(CURRENT_SESSION["laps"]),
        "analytics_ready": True
    }
