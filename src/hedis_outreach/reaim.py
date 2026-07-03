"""RE-AIM reach and response funnel for autoSMS HEDIS outreach.

Reach = members sent an outgoing automated message for a measure. Response = members
who replied. Closure-among-reached is a descriptive funnel endpoint (not the causal
contrast, which is confounded by outreach targeting). RCT campaigns excluded.
"""
from __future__ import annotations
import pandas as pd
from .io import as_bool
from .outreach import STATE, CAMPAIGN_TO_GAP


def funnel(reach_response: pd.DataFrame, gap: pd.DataFrame,
           autosms_members: pd.DataFrame) -> dict:
    rr = reach_response.dropna(subset=["measure"]).groupby("measure")[["reached", "responded"]].sum()
    rr["response_rate"] = (rr.responded / rr.reached).round(4)

    # closure among reached members (descriptive), excluding archived gaps
    g = gap.copy()
    g["closed"] = (~as_bool(g["open"])).astype(float)
    g["contract"] = as_bool(g["contractual"]); g["drop"] = as_bool(g["dropped"])
    g["state"] = g["payer"].map(STATE); g["yr"] = g["measure_year"].astype(str)
    g = g[g.contract & ~g["drop"] & g.state.isin(("WA", "VA")) & (g.yr == "2025")
          & g.measure_abbreviation.isin(CAMPAIGN_TO_GAP.values())]
    reached_ids = autosms_members.groupby(autosms_members.measure.map(CAMPAIGN_TO_GAP)) \
        .member_ident.apply(set).to_dict()

    out = {}
    for meas in rr.index:
        ids = reached_ids.get(meas, set())
        gm = g[(g.measure_abbreviation == meas) & (g.patient_id.isin(ids))]
        out[meas] = {"reached": int(rr.loc[meas, "reached"]),
                     "responded": int(rr.loc[meas, "responded"]),
                     "response_rate": float(rr.loc[meas, "response_rate"]),
                     "closure_among_reached": round(float(gm.closed.mean()), 4) if len(gm) else None}
    out["_total"] = {"reached": int(rr.reached.sum()), "responded": int(rr.responded.sum()),
                     "response_rate": round(float(rr.responded.sum() / rr.reached.sum()), 4)}
    return out
