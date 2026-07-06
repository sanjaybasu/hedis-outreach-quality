"""Care-team per-patient identification time absorbed by automated outreach.

The alternative to automated outreach is manual outreach by care-team staff, who must
locate each patient from the gap list before making contact: look up name, date of birth,
and medical-record number; search the record; confirm identity; and open the relevant tab
-- about 2 minutes per patient. Automating outreach absorbs this per-patient identification
time for the reached population; it does not replace clinical chart review or the scheduling
that responding members receive. Reported in hours, full-time-equivalent-years, and per
1,000 open gaps.
"""
from __future__ import annotations

# Per-patient identification steps performed before manual contact, for every measure (seconds)
STEPS = {"lookup_name_dob_mrn": 30, "search_record": 60,
         "confirm_identity": 15, "open_relevant_tab": 15}   # total 120 s = 2.0 min
MIN_PER_PATIENT = sum(STEPS.values()) / 60.0                 # 2.0


def estimate(reached_by_measure: dict, fte_hours_year: int = 2080,
             time_multiplier: float = 1.0) -> dict:
    """reached_by_measure: {measure -> members reached}. Returns identification time absorbed."""
    ppm = MIN_PER_PATIENT * time_multiplier
    rows, total = {}, 0
    for meas, n in reached_by_measure.items():
        rows[meas] = {"reached": int(n), "hours": round(n * ppm / 60.0, 1)}
        total += int(n)
    tot_hours = total * ppm / 60.0
    return {
        "by_measure": rows,
        "min_per_patient": round(ppm, 3),
        "total_reached": total,
        "total_hours": round(tot_hours, 1),
        "total_fte_year": round(tot_hours / fte_hours_year, 3),
        "hours_per_1000_gaps": round(tot_hours / total * 1000, 1) if total else None,
        "assumptions": {"steps_sec": STEPS, "min_per_patient": round(ppm, 3),
                        "fte_hours_year": fte_hours_year, "time_multiplier": time_multiplier,
                        "note": "identification time only; excludes clinical verification and scheduling"},
    }
