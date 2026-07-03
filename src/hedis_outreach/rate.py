"""Official HEDIS rate (numerator/denominator) year-over-year.

Uses the daily over_time table. Matched day-of-year removes maturity differences across
years; measure standardization to a fixed measure mix removes measure-composition shift;
a balanced (stable-plan) cohort is reported as a sensitivity. This is the payer-scored
rate and is the primary estimand (the internal gap-open flag is not comparable).
"""
from __future__ import annotations
import pandas as pd

STATE = {"UHCWA": "WA", "CHPW": "WA", "ABHVA": "VA", "SHPVA": "VA", "UHCOH": "OH"}
PRIMARY_STATES = ("WA", "VA")
YEARS = (2023, 2024, 2025)


def prep(ot: pd.DataFrame) -> pd.DataFrame:
    d = ot.copy()
    for c in ["denominator", "numerator", "day_of_year", "measure_year"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["state"] = d["payer"].map(STATE)
    d["contract"] = d["is_contractual"].astype(str).str.lower().isin(["true", "t", "1", "yes"])
    return d[d.contract & d.state.isin(PRIMARY_STATES) & d.measure_year.isin(YEARS)].copy()


def _rate_by_measure(d: pd.DataFrame, day: int, window: int = 3) -> pd.DataFrame:
    sub = d[d.day_of_year.between(day - window, day + window)]
    g = (sub.groupby(["measure_year", "measure_abv"])
         .agg(num=("numerator", "sum"), den=("denominator", "sum")).reset_index())
    g["rate"] = g.num / g.den.clip(lower=1)
    return g


def crude_and_standardized(d: pd.DataFrame, day: int) -> dict:
    g = _rate_by_measure(d, day)
    crude = {int(y): round(float(v.num.sum() / max(v.den.sum(), 1)), 4) for y, v in g.groupby("measure_year")}
    # fixed weights: pooled denominator per measure across all years
    w = g.groupby("measure_abv").den.sum()
    w = w / w.sum()
    std = {}
    for y, v in g.groupby("measure_year"):
        vr = v.set_index("measure_abv").rate
        common = w.index.intersection(vr.index)
        std[int(y)] = round(float((w[common] * vr[common]).sum() / w[common].sum()), 4)
    return {"crude": crude, "standardized": std}


def balanced_plans(d: pd.DataFrame) -> set:
    per = d.groupby("payer").measure_year.nunique()
    return set(per[per == len(YEARS)].index)


def segment_gain(d: pd.DataFrame, d0: int = 188, d1: int = 350, window: int = 3) -> dict:
    # within-year closure gain over the post-go-live window, by year (proto-ITS:
    # a larger 2025 gain than 2023/2024 over the same window signals acceleration)
    out = {}
    for y in YEARS:
        dy = d[d.measure_year == y]
        r0 = _pool(dy, d0, window)
        r1 = _pool(dy, d1, window)
        out[int(y)] = {"day%d" % d0: r0, "day%d" % d1: r1,
                       "gain": round(r1 - r0, 4) if (r0 is not None and r1 is not None) else None}
    return out


def _pool(dy: pd.DataFrame, day: int, window: int) -> float | None:
    sub = dy[dy.day_of_year.between(day - window, day + window)]
    if not len(sub):
        return None
    return round(float(sub.numerator.sum() / max(sub.denominator.sum(), 1)), 4)
