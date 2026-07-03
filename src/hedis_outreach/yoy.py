"""Year-over-year HEDIS gap closure on the contractual cohort.

Primary cohort is WA and VA over complete measurement years 2023-2025. Year 2026 is
excluded as incomplete. Ohio is contractual only from 2025 (no baseline) and is excluded.
Payer identities are mapped to state internally and are not reported.

Inference is clustered at the patient level because patients contribute multiple gaps.
A balanced-cohort analysis (health plans contractual in every year) isolates within-plan
change from the 2025 plan expansion.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .io import as_bool

STATE = {"UHCWA": "WA", "CHPW": "WA", "ABHVA": "VA", "SHPVA": "VA", "UHCOH": "OH"}
PRIMARY_STATES = ("WA", "VA")
YEARS = ("2023", "2024", "2025")


def prepare(gap: pd.DataFrame) -> pd.DataFrame:
    df = gap.copy()
    df["state"] = df["payer"].map(STATE)
    df["closed"] = (~as_bool(df["open"])).astype(float)
    df["is_contractual"] = as_bool(df["contractual"])
    df["year"] = df["measure_year"].astype(str)
    return df


def cohort(gap: pd.DataFrame, states=PRIMARY_STATES, years=YEARS) -> pd.DataFrame:
    df = prepare(gap)
    return df[df.is_contractual & df.state.isin(states) & df.year.isin(years)].copy()


def _rates(frame: pd.DataFrame) -> dict:
    return {y: {"n": int(v.closed.size), "closure": round(float(v.closed.mean()), 4)}
            for y, v in frame.groupby("year")}


def balanced_plans(df: pd.DataFrame, years=YEARS) -> set:
    # health plans with contractual gaps in every study year
    per = df.groupby("payer").year.nunique()
    return set(per[per == len(years)].index)


def cluster_boot_diff(df: pd.DataFrame, y0: str, y1: str, reps: int = 500, seed: int = 42):
    # patient-clustered bootstrap CI for closure(y1) - closure(y0)
    sub = df[df.year.isin([y0, y1])]
    a = pd.DataFrame({
        "pid": sub.patient_id.values,
        "y0": (sub.year.values == y0).astype(float),
        "y1": (sub.year.values == y1).astype(float),
        "c": sub.closed.values,
    })
    a["c0"] = a.c * a.y0
    a["c1"] = a.c * a.y1
    t = a.groupby("pid")[["y0", "y1", "c0", "c1"]].sum()
    N0, N1, C0, C1 = t.y0.values, t.y1.values, t.c0.values, t.c1.values
    K = len(t)
    rng = np.random.default_rng(seed)
    diffs = np.empty(reps)
    for i in range(reps):
        idx = rng.integers(0, K, K)
        diffs[i] = C1[idx].sum() / max(N1[idx].sum(), 1) - C0[idx].sum() / max(N0[idx].sum(), 1)
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


def analyze(gap: pd.DataFrame) -> dict:
    df = cohort(gap)
    bal = balanced_plans(df)
    dfb = df[df.payer.isin(bal)]
    res = {
        "cohort": {"states": list(PRIMARY_STATES), "years": list(YEARS), "n_gaps": int(len(df))},
        "pooled": _rates(df),
        "by_state": {s: _rates(df[df.state == s]) for s in PRIMARY_STATES},
        "change_2023_2025": {
            "point": round(float(df[df.year == "2025"].closed.mean() - df[df.year == "2023"].closed.mean()), 4),
            "ci95_cluster_boot": cluster_boot_diff(df, "2023", "2025"),
        },
        "balanced_cohort": {
            "n_plans": len(bal),
            "rates": _rates(dfb),
            "change_2023_2025_point": round(float(dfb[dfb.year == "2025"].closed.mean() - dfb[dfb.year == "2023"].closed.mean()), 4),
            "change_2023_2025_ci95": cluster_boot_diff(dfb, "2023", "2025"),
        },
    }
    return res
