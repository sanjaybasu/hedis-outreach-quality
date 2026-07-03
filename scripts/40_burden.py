"""Care-team manual-equivalent burden absorbed by autoSMS reach, with sensitivity.

Reads the reach funnel (members reached per measure) and applies the care-team time
schedule. Reports grounded-only and full-cohort estimates plus +/-25% and a GSD-high
variant. Aggregate results only (no PHI).
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from hedis_outreach.burden import estimate, per_patient_minutes, SPECIFIC

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
DATA = os.environ.get("HEDIS_DATA_DIR", "data")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    rr = pd.read_parquet(os.path.join(DATA, "autosms_reach_response.parquet"))
    reached = (rr.dropna(subset=["measure"]).groupby("measure").reached.sum().astype(int).to_dict())

    base = estimate(reached)
    out = {
        "reached_by_measure": reached,
        "per_patient_minutes": {m: per_patient_minutes(m) for m in reached if m in SPECIFIC},
        "base": base,
        "sensitivity": {
            "times_minus_25pct": estimate(reached, time_multiplier=0.75),
            "times_plus_25pct": estimate(reached, time_multiplier=1.25),
            "fte_1872_direct_hours": {  # 0.9*2080 productive-hours convention
                "total_fte_year": round(base["total_hours"] / 1872, 3),
                "grounded_only_fte_year": round(base["grounded_only_hours"] / 1872, 3)},
        },
    }
    with open(os.path.join(RESULTS, "burden.json"), "w") as f:
        json.dump(out, f, indent=2)

    print("Per-patient manual chart-review minutes by measure:")
    for m in reached:
        if m in SPECIFIC:
            g = "grounded" if SPECIFIC[m]["grounded"] else "MAPPED"
            print(f"  {m:6} {per_patient_minutes(m):5.2f} min  ({g})  reached={reached[m]}")
    b = out["base"]
    print(f"\nGrounded-only (WCV/BCS-E/CCS): {b['grounded_only_hours']} h "
          f"({b['grounded_only_fte_year']} FTE-yr)")
    print(f"Full cohort (all reached):     {b['total_hours']} h "
          f"({b['total_fte_year']} FTE-yr)")
    print(f"Sensitivity +/-25%: {out['sensitivity']['times_minus_25pct']['total_hours']}"
          f" - {out['sensitivity']['times_plus_25pct']['total_hours']} h")


if __name__ == "__main__":
    main()
