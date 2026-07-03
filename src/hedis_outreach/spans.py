"""Gap-status volatility from the open-gap span history (measurement-integrity check).

The span table is a slowly-changing-dimension history filtered to open-gap spans: one row
per open-gap episode per member-gap, with valid_from/valid_until. A member-gap with more
than one span therefore closed and reopened at least once. This quantifies how unstable a
single cross-sectional closure snapshot is, corroborating the decision to evaluate the
payer-scored official rate at a matched day-of-year rather than a naive gap-open flag.

Limitation: reopening reflects volatility from any cause (re-qualification in a new
measurement year, claim reversal, or eligibility restatement/reattribution); this table
cannot isolate reattribution, which would require the eligibility/attribution history.
"""
from __future__ import annotations
import pandas as pd


def churn(spans: pd.DataFrame) -> dict:
    per_id = spans.groupby("id").size()
    n_ids = int(per_id.shape[0])
    n_spans = int(len(spans))
    multi = int((per_id > 1).sum())
    reopen_events = n_spans - n_ids  # spans beyond the first per member-gap
    return {
        "n_member_gaps": n_ids,
        "n_open_spans": n_spans,
        "member_gaps_multi_span": multi,
        "pct_member_gaps_reopened": round(multi / n_ids, 4),
        "reopen_events": int(reopen_events),
        "pct_spans_are_reopenings": round(reopen_events / n_spans, 4),
        "max_spans_per_member_gap": int(per_id.max()),
        "note": "open-gap spans only; reopening = volatility (not isolated reattribution)",
    }
