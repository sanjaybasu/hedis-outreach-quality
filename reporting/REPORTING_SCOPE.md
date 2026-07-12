# Reporting scope: manuscript vs. full analysis

This repository is the full, honest analysis record. The *Learning Health Systems*
manuscript reports a deliberately scoped subset of it. This note documents the difference
so the two never drift.

## What the repository contains (unchanged)

- **All six outreach measures:** AAP, WCV, BCS-E, CCS, EED, and **GSD (glycemic status)**.
  See `results/reaim_funnel.json`, `results/burden.json`,
  `results/autosms_closure_by_measure.json`.
- **Both comparison designs for closure:**
  - the naive contacted-vs-uncontacted / matched comparison
    (`results/autosms_matched_closure.json`, `results/autosms_matched_comparator.json`,
    `results/autosms_closure_nondropped.json`), and
  - the target-trial earlier-vs-later difference-in-differences
    (`results/activation_did.json`, `results/autosms_riskset_closure.json`).

Nothing here has been removed. This is the reproducibility record.

## What the manuscript reports (scoped subset)

- **Five measures** (AAP, WCV, BCS-E, CCS, EED). **GSD is excluded from the reported
  paper** because its closure effect could not be identified (pre-contact trends did not
  match), so it would contribute reach/burden rows without an effect estimate. GSD data
  remain here in full.
- **One design.** The manuscript presents the **target-trial earlier-vs-later** design as
  the method. The naive contacted-vs-uncontacted comparison is retained in this repository
  but is no longer presented as a headline contrast in the paper.

## Reported (five-measure) headline numbers

| Quantity | Reported value |
|---|---|
| Members reached | 12,092 |
| Members replied (reply rate) | 2,107 (17.4%) |
| Care-team time absorbed | 403 hours (~0.19 FTE-years); ~33 h per 1,000 open gaps; ±25% → 302–504 h |
| Closure effect (identified measures) | 7.6 pp (95% CI 7.0–8.3); 11.7 pp by four months |
| By measure | AAP 9.3, WCV 6.5, BCS-E 3.2 pp |

Full six-measure totals (incl. GSD: reached 13,014; replied 2,311/17.8%; 433.8 h/0.21 FTE)
are in `results/*.json`.

## Figures in this folder

`reporting/figures/` holds the manuscript-final figures (five reported measures).
`make_manuscript_figures.py` regenerates the two bar charts (aggregate values only; no PHI).
The full six-measure figures are produced by `scripts/50_figures.py` from `results/*.json`.
