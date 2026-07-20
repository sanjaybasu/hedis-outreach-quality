"""Figure: event-study of the earlier-vs-later autoSMS DiD on HEDIS gap closure.
Reads results/activation_did.json (aggregate only; no PHI). Plots the pooled
gate-passing event study (all cohorts) with 95% member-clustered bootstrap CIs,
and overlays the balanced-cohort event study (cohorts observed through the +4-month
horizon) as a differential-follow-up robustness check.

Output: figures/figure2_did_eventstudy.png (300 dpi).
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OUT = os.environ.get("FIG_OUT", os.path.join(HERE, "..", "figures"))
os.makedirs(OUT, exist_ok=True)

BLUE, GREEN = "#2a6ddb", "#1a7a3c"

d = json.load(open(os.path.join(RES, "activation_did.json")))
main = d["pooled_gatepassing"]
bal = d.get("pooled_balanced_cohort")

def series(block):
    es = block["event_time_pp"]
    xs = sorted(int(k) for k in es)
    ys = [es[str(x)] for x in xs]
    ci = block.get("event_time_ci", {})
    lo = [ci.get(str(x), [None, None])[0] for x in xs]
    hi = [ci.get(str(x), [None, None])[1] for x in xs]
    return xs, ys, lo, hi

xs, ys, lo, hi = series(main)

fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=300)
# pre-contact shaded region (months at and before -1 test parallel trends)
ax.axvspan(min(xs) - 0.5, -0.5, color="#f0f0f2", zorder=0)
ax.axhline(0, color="#999999", lw=1, zorder=1)
ax.axvline(0, color="#999999", lw=1, ls=":", zorder=1)
# main: all cohorts, with CI band
if all(v is not None for v in lo + hi):
    ax.fill_between(xs, lo, hi, color=BLUE, alpha=0.18, zorder=2, label="95% CI (all cohorts)")
ax.plot(xs, ys, "-o", color=BLUE, lw=2.4, ms=6, zorder=4, label="All cohorts")
# balanced-cohort overlay
if bal:
    bx, by, _, _ = series(bal)
    ax.plot(bx, by, "--s", color=GREEN, lw=2.0, ms=5, zorder=3,
            label=f"Balanced cohorts (observed ≥{bal['E_horizon']} mo)")

ax.set_xlabel("Months relative to first contact", fontsize=15)
ax.set_ylabel("Effect on cumulative gap closure (percentage points)", fontsize=14)
ax.set_title("Effect of being contacted on HEDIS gap closure\n"
             "identified measures (adults' access, well-care visits, breast-cancer screening)",
             fontsize=15, pad=12)
ax.set_xticks(xs)
ax.tick_params(labelsize=12)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.legend(fontsize=12, frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "figure2_did_eventstudy.png"), bbox_inches="tight")
plt.close(fig)
print("wrote figure2_did_eventstudy.png to", OUT)
print("main avg_post:", main["avg_post_ATT_pp"], main["avg_post_ATT_ci"],
      "| month4:", main.get("point_at_month4_pp"), "| maxpre:", main["max_pretrend_pp"],
      "| M:", main["honest_did_M_breakdown"])
if bal:
    print("balanced avg_post:", bal["avg_post_ATT_pp"], bal["avg_post_ATT_ci"],
          "| month4:", bal.get("point_at_month4_pp"), "| maxpre:", bal["max_pretrend_pp"])
