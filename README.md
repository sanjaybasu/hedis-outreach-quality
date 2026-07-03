# hedis-outreach-quality

Code for a descriptive, hybrid effectiveness–implementation study of **automated
text-message ("autoSMS") outreach** as a strategy for closing HEDIS care gaps in
Medicaid managed care. Outreach messages contact members with open care gaps and offer
*human* scheduling assistance (not automated scheduling). The study characterizes
**reach** and **member response**, the **care-team manual-chart-review burden absorbed**
by automation, and the (modest, confounded) association with **gap closure**, using the
RE-AIM framework and StaRI reporting.

The analysis is framed around the intervention class (automated outreach) and the
measurement problem (attribution churn in Medicaid HEDIS), not any single organization.
No managed-care organization is named; results describe states and plan counts only.

## Contribution

- **Reach and response (RE-AIM):** distinct members reached per measure and reply rate
  (`reaim.py`), the well-powered implementation core.
- **Care-team burden absorbed (headline):** manual-equivalent chart-review labor absorbed
  by automated first-touch outreach, from an explicit per-measure time schedule with
  grounded-vs-analogy-mapped separation and ±25% sensitivity (`burden.py`).
- **Honest closure measurement:** operational gap-closure reconciled to the payer-scored
  official rate (`rate.py`); within-campaign / designed-A/B contrasts for the effectiveness
  question (`outreach.py`); naive year-over-year change (`yoy.py`) reported as a
  measurement caveat, since eligibility restatement (reattribution) removes members from
  the year-end scored denominator and biases raw comparisons.

Closure findings are descriptive/associational; outreach is directed at open, harder-to-close
gaps (confounding by indication), so no causal closure effect is claimed.

## Layout

```
src/hedis_outreach/   analysis modules: io, yoy, rate, outreach, reaim, burden
sql/                  extraction queries (hedis_gap, over_time, spans, funnel)
scripts/              entry points that write aggregate results/
results/              aggregate outputs only (rates, counts, hours) — no patient data
```

## Reproducibility and data

Patient-level data are Medicaid protected health information and are **not** included in
this repository. The `sql/` queries define the extraction against the source HEDIS schema;
scripts read the extracted tables from a local `data/` directory that is git-ignored.
Only aggregate results (rates, counts, hours) are retained under `results/`.

To reproduce with access to the source schema and extracted parquet tables in `HEDIS_DATA_DIR`:

```
pip install -r requirements.txt
HEDIS_DATA_DIR=/path/to/data python scripts/10_yoy.py     # year-over-year gap closure
HEDIS_DATA_DIR=/path/to/data python scripts/12_rate.py    # official-rate YoY (std, balanced cohort)
HEDIS_DATA_DIR=/path/to/data python scripts/40_burden.py  # care-team burden absorbed + sensitivity
```

Reach/response and closure-comparator outputs (`reaim.py`, `outreach.py`) require the
engagement-platform extracts described in `sql/`.

## Study context

Conducted within Waymark, a community-based provider organization providing free medical
and social services to patients receiving Medicaid. Determined quality improvement and
exempt from human-subjects review by WCG IRB.

## License

MIT. See LICENSE.
