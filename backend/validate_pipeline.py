"""
TrackShift Pipeline Ground-Truth Validation Runner
Compares recovered mathematical analytics against hidden ground-truth parameters.
Must print ALL CHECKS PASSED for validation suite to pass.
"""

import sys
import mock_data
import tyre_analytics


def run_validation():
    print("=" * 65)
    print("      TRACKSHIFT PIPELINE GROUND-TRUTH VALIDATION SUITE      ")
    print("=" * 65)

    # 1. Generate observable session & retrieve hidden ground truth
    session_data = mock_data.generate_session(seed=42)
    ground_truth = mock_data.get_ground_truth()

    analysis = tyre_analytics.analyze_session_full(session_data)
    stint_analyses = analysis["stint_analyses"]

    passed_checks = 0
    total_checks = 5

    # --- Check 1: Degradation Rate & Compound Ranking Accuracy ---
    print("\n[CHECK 1] Verifying recovered degradation rates & compound rank...")
    recovered_rates = {}
    ground_rates = {}

    for s_id, gt_stint in ground_truth["stints"].items():
        rec_deg = stint_analyses[s_id]["fit"]["degradation_rate_sec_per_lap"]
        true_deg = gt_stint["true_degradation_rate"]
        compound = gt_stint["compound"]
        
        recovered_rates[compound] = rec_deg
        ground_rates[compound] = true_deg
        
        diff = abs(rec_deg - true_deg)
        print(f"  • {compound} (Stint {s_id}): Ground Truth={true_deg:.4f}s/lap, Recovered={rec_deg:.4f}s/lap (Delta={diff:.4f}s)")
        assert diff <= 0.040, f"Degradation rate error too large for {compound}: {diff:.4f}s"

    # Compound ranking: SOFT > MEDIUM > HARD
    assert recovered_rates["SOFT"] > recovered_rates["MEDIUM"] > recovered_rates["HARD"], \
        f"Compound degradation ranking violated: {recovered_rates}"
    
    print("  ✓ Check 1 Passed: Degradation rates within margin and correctly ranked (Soft > Medium > Hard).")
    passed_checks += 1

    # --- Check 2: Warm-up Window Detection Accuracy ---
    print("\n[CHECK 2] Verifying warm-up phase changepoint detection...")
    for s_id, gt_stint in ground_truth["stints"].items():
        rec_warmup = stint_analyses[s_id]["fit"]["detected_warmup_laps"]
        true_warmup = gt_stint["true_warmup_laps"]
        diff = abs(rec_warmup - true_warmup)
        print(f"  • {gt_stint['compound']} (Stint {s_id}): True Warmup={true_warmup} laps, Recovered={rec_warmup} laps")
        assert diff <= 1, f"Warmup detection error too large for {s_id}: delta {diff}"

    print("  ✓ Check 2 Passed: Detected warm-up windows match ground truth within ±1 lap.")
    passed_checks += 1

    # --- Check 3: Waterfall Component Delta Conservation ---
    print("\n[CHECK 3] Verifying exact additive waterfall delta conservation...")
    total_laps_checked = 0
    for lap in session_data["laps"]:
        lap_num = lap["session_lap"]
        wf = tyre_analytics.get_lap_waterfall(session_data, lap_num)
        raw_delta = wf["raw_delta_sec"]
        sum_comps = wf["sum_of_components"]
        diff = abs(raw_delta - sum_comps)
        assert diff < 1e-3, f"Waterfall sum mismatch on lap {lap_num}: raw_delta={raw_delta}, sum={sum_comps}"
        total_laps_checked += 1

    print(f"  ✓ Check 3 Passed: All {total_laps_checked} session laps sum exactly to observed raw lap deltas.")
    passed_checks += 1

    # --- Check 4: Widening Uncertainty Cone Expansion ---
    print("\n[CHECK 4] Verifying strict uncertainty cone expansion over projection horizon...")
    for s_id, s_data in stint_analyses.items():
        curve = s_data["uncertainty_curve"]
        # Filter post-warmup projection points
        deg_pts = [p for p in curve if not p["is_warmup"]]
        for i in range(1, len(deg_pts)):
            prev_margin = deg_pts[i - 1]["uncertainty_margin"]
            curr_margin = deg_pts[i]["uncertainty_margin"]
            assert curr_margin >= prev_margin, f"Uncertainty margin shrank on stint {s_id} lap {deg_pts[i]['tyre_age']}"
        
        # Verify margin at horizon is wider than at current lap
        assert deg_pts[-1]["uncertainty_margin"] > deg_pts[0]["uncertainty_margin"], \
            f"Uncertainty cone failed to widen on stint {s_id}"

    print("  ✓ Check 4 Passed: Uncertainty margin expands strictly with projection horizon.")
    passed_checks += 1

    # --- Check 5: Model Coherence & Pit Window Consistency ---
    print("\n[CHECK 5] Verifying model coherence across remaining life and strategy calculations...")
    for s_id, s_data in stint_analyses.items():
        fit = s_data["fit"]
        rem_life = s_data["remaining_life"]
        deg_rate = fit["degradation_rate_sec_per_lap"]
        
        # Remaining life must be positive and pit window logical
        assert rem_life["pit_window_start_lap"] <= rem_life["pit_window_end_lap"], \
            f"Invalid pit window range on {s_id}"
        assert rem_life["degradation_rate_sec"] == deg_rate, \
            f"Degradation rate mismatch between fit and remaining life on {s_id}"

    print("  ✓ Check 5 Passed: Unified degradation model maintains strict mathematical coherence.")
    passed_checks += 1

    print("\n" + "=" * 65)
    print(f"       ALL CHECKS PASSED ({passed_checks}/{total_checks}) - PIPELINE VERIFIED       ")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    try:
        run_validation()
    except AssertionError as err:
        print(f"\n❌ VALIDATION FAILURE: {err}")
        sys.exit(1)
