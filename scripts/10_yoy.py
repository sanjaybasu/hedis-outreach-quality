"""Year-over-year HEDIS closure for the WA+VA contractual cohort, 2023-2025.

Reports pooled and by-state closure, the patient-clustered 2023->2025 change with a
bootstrap CI, and a balanced-cohort sensitivity (plans contractual in every year).
Writes aggregate results only.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hedis_outreach import io
from hedis_outreach.yoy import analyze, cohort

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    gap = io.load("gap")
    res = analyze(gap)

    df = cohort(gap)
    d25 = df[df.year == "2025"]
    by_measure = (d25.groupby("measure_abbreviation").closed
                  .agg(["size", "mean"]).sort_values("size", ascending=False).head(12))
    res["by_measure_2025"] = {k: {"n": int(r["size"]), "closure": round(float(r["mean"]), 4)}
                              for k, r in by_measure.iterrows()}

    with open(os.path.join(RESULTS, "yoy_closure.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({k: res[k] for k in ["cohort", "pooled", "by_state",
                                          "change_2023_2025", "balanced_cohort"]}, indent=2))


if __name__ == "__main__":
    main()
