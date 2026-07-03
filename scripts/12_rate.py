"""Official-rate year-over-year: crude and measure-standardized at matched day-of-year,
balanced-cohort sensitivity, and post-go-live segment gain. Aggregate results only.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from hedis_outreach.rate import prep, crude_and_standardized, balanced_plans, segment_gain

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
DATA = os.environ.get("HEDIS_DATA_DIR", "data")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    ot = pd.read_parquet(os.path.join(DATA, "over_time.parquet"))
    d = prep(ot)

    res = {"matched_day": {str(day): crude_and_standardized(d, day) for day in (90, 180, 270, 350)},
           "segment_gain_post_golive": segment_gain(d)}

    bal = balanced_plans(d)
    db = d[d.payer.isin(bal)]
    res["balanced_cohort"] = {"n_plans": len(bal),
                              "matched_day_350": crude_and_standardized(db, 350)}

    with open(os.path.join(RESULTS, "official_rate_yoy.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
