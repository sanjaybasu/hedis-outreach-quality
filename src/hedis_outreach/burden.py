"""Care-team burden absorbed by automated (autoSMS) HEDIS outreach.

The manual alternative to automated first-touch outreach is a care coordinator working
a gap list by hand: for each patient, look them up, confirm identity, open the record,
and verify the measure-specific status. Care-team-provided standard time estimates for
that per-patient chart-review/data-entry task are encoded below (seconds). Multiplying by
the number of members the automation reached gives the manual-equivalent labor the
automation absorbed in one measurement year.

Distinct from the AI appointment-maker's scheduling time (WCV RCT): this is the
record-review/verification burden of working a gap, not the scheduling touch.

GROUNDED measures have per-patient times supplied directly by the care team. MAPPED
measures (no direct time) are set conservatively by analogy to a grounded step and are
flagged so they can be reported separately.
"""
from __future__ import annotations

# Common steps performed for every HEDIS measure (seconds)
COMMON = {"lookup_sheet_name_dob_mrn": 30, "search_record": 60,
          "confirm_mrn": 15, "open_relevant_tab": 15}          # = 120 s
COMMON_SEC = sum(COMMON.values())

# Measure-specific verification steps (seconds). grounded=True => supplied directly.
SPECIFIC = {
    "AMM":   {"sec": 45 + 60,  "grounded": True,  "note": "document episode+Rx; scan 12wk MH follow-up"},
    "AMR":   {"sec": 120,      "grounded": True,  "note": "controller/total medication ratio"},
    "WCV":   {"sec": 60 + 15,  "grounded": True,  "note": "review visits tab; stratify age band"},
    "BCS-E": {"sec": 60,       "grounded": True,  "note": "verify mammogram date"},
    "CCS":   {"sec": 60 + 120, "grounded": True,  "note": "verify pap date; verify HPV+Pap results"},
    "IMM1":  {"sec": 240 + 30, "grounded": True,  "note": "registry lookup + 1 immunization (Combo panels far longer)"},
    # mapped by analogy (no direct time supplied) -- conservative, flagged
    "AAP":   {"sec": 60,       "grounded": False, "note": "verify ambulatory visit (analogy: WCV visit review)"},
    "EED":   {"sec": 60,       "grounded": False, "note": "verify eye-exam date (analogy: verify-date)"},
    "GSD":   {"sec": 60,       "grounded": False, "note": "verify HbA1c value from labs (analogy: verify-date)"},
}


def per_patient_minutes(measure: str) -> float:
    return round((COMMON_SEC + SPECIFIC[measure]["sec"]) / 60.0, 3)


def estimate(reached_by_measure: dict, fte_hours_year: int = 2080,
             time_multiplier: float = 1.0) -> dict:
    """reached_by_measure: {HEDIS measure -> members reached}. Returns burden absorbed."""
    rows, tot_min, grounded_min = {}, 0.0, 0.0
    for meas, n in reached_by_measure.items():
        if meas not in SPECIFIC:
            continue
        ppm = per_patient_minutes(meas) * time_multiplier
        minutes = n * ppm
        g = SPECIFIC[meas]["grounded"]
        rows[meas] = {"reached": int(n), "min_per_patient": round(ppm, 3),
                      "hours": round(minutes / 60.0, 1), "grounded": g}
        tot_min += minutes
        if g:
            grounded_min += minutes
    return {
        "by_measure": rows,
        "total_hours": round(tot_min / 60.0, 1),
        "total_fte_year": round(tot_min / 60.0 / fte_hours_year, 3),
        "grounded_only_hours": round(grounded_min / 60.0, 1),
        "grounded_only_fte_year": round(grounded_min / 60.0 / fte_hours_year, 3),
        "assumptions": {"common_steps_sec": COMMON_SEC, "fte_hours_year": fte_hours_year,
                        "time_multiplier": time_multiplier,
                        "note": "care-team standard time estimates; grounded vs analogy-mapped separated"},
    }
