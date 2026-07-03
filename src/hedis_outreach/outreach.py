"""AutoSMS outreach exposure and its association with HEDIS gap closure.

Exposure: a gap's member received an outgoing automated (autoSMS) campaign message for
the same measure in the measurement year. RCT participants (well-child-visit trial
campaigns) are excluded from the well-child measure. Descriptive/associational.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .io import as_bool

STATE = {"UHCWA": "WA", "CHPW": "WA", "ABHVA": "VA", "SHPVA": "VA", "UHCOH": "OH"}
# campaign measure token -> HEDIS gap measure abbreviation
CAMPAIGN_TO_GAP = {"AAP": "AAP", "CCS": "CCS", "EED": "EED", "BCS": "BCS-E",
                   "DIABETES": "GSD", "WCV": "WCV"}
RCT_PCP = {"2025-05-29-wcv-pcp-null-va", "2025-05-29-wcv-pcp-populated-va"}


def is_rct(campaign: str) -> bool:
    return ("rct" in campaign.lower()) or (campaign in RCT_PCP)


def prep_gaps(gap: pd.DataFrame, year: str = "2025") -> pd.DataFrame:
    g = gap.copy()
    g["state"] = g["payer"].map(STATE)
    g["closed"] = (~as_bool(g["open"])).astype(float)
    g["contract"] = as_bool(g["contractual"])
    g["year"] = g["measure_year"].astype(str)
    keep = list(CAMPAIGN_TO_GAP.values())
    return g[g.contract & g.state.isin(("WA", "VA")) & (g.year == year)
             & g.measure_abbreviation.isin(keep)].copy()


def analyze(gap: pd.DataFrame, autosms: pd.DataFrame, year: str = "2025") -> dict:
    a = autosms.copy()
    a["rct"] = a.campaign.map(is_rct)
    a["gap_measure"] = a.measure.map(CAMPAIGN_TO_GAP)
    rct_members = set(a.loc[a.rct, "member_ident"])
    exposed = a[~a.rct].groupby("gap_measure").member_ident.apply(set).to_dict()

    g = prep_gaps(gap, year)
    out = {}
    for meas in sorted(g.measure_abbreviation.unique()):
        gm = g[g.measure_abbreviation == meas].copy()
        if meas == "WCV":
            gm = gm[~gm.patient_id.isin(rct_members)]      # remove trial participants
        gm["autosms"] = gm.patient_id.isin(exposed.get(meas, set()))
        e, n = gm[gm.autosms], gm[~gm.autosms]
        out[meas] = {"n_gaps": int(len(gm)),
                     "autosms": {"n": int(len(e)),
                                 "closure": round(float(e.closed.mean()), 4) if len(e) else None},
                     "not_outreached": {"n": int(len(n)),
                                        "closure": round(float(n.closed.mean()), 4) if len(n) else None},
                     "diff_pp": round(float((e.closed.mean() - n.closed.mean()) * 100), 1)
                     if len(e) and len(n) else None}
    return out
