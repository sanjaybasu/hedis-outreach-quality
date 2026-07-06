"""Care-team per-patient identification time absorbed by automated outreach, with
sensitivity. 2 minutes per reached patient (identification steps only). Aggregate output.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from hedis_outreach.burden import estimate, MIN_PER_PATIENT

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
DATA = os.environ.get("HEDIS_DATA_DIR", "data")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    rr = pd.read_parquet(os.path.join(DATA, "autosms_reach_response.parquet"))
    reached = (rr.dropna(subset=["measure"]).groupby("measure").reached.sum().astype(int).to_dict())

    base = estimate(reached)
    out = {
        "reached_by_measure": reached,
        "min_per_patient": MIN_PER_PATIENT,
        "base": base,
        "sensitivity": {
            "times_minus_25pct": estimate(reached, time_multiplier=0.75),
            "times_plus_25pct": estimate(reached, time_multiplier=1.25),
        },
    }
    with open(os.path.join(RESULTS, "burden.json"), "w") as f:
        json.dump(out, f, indent=2)

    b = base
    print(f"Per-patient identification time: {b['min_per_patient']} min")
    for m, r in sorted(b["by_measure"].items(), key=lambda kv: -kv[1]["hours"]):
        print(f"  {m:6} reached={r['reached']:5}  {r['hours']:6.1f} h")
    print(f"\nTotal: {b['total_hours']} h  ({b['total_fte_year']} FTE-year); "
          f"{b['hours_per_1000_gaps']} h per 1,000 open gaps")
    print(f"Sensitivity +/-25%: {out['sensitivity']['times_minus_25pct']['total_hours']}"
          f" - {out['sensitivity']['times_plus_25pct']['total_hours']} h")


if __name__ == "__main__":
    main()
