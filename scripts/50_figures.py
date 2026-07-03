"""Publication figures from aggregate results (no PHI).

Figure 1: RE-AIM reach and member response by measure.
Figure 2: Care-team manual-chart-review burden absorbed by measure (grounded vs mapped).

Reads results/{reaim_funnel,burden}.json. Output dir via FIG_OUT (default ./figures).
"""
import os
import sys
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
OUT = os.environ.get("FIG_OUT", os.path.join(HERE, "..", "figures"))
os.makedirs(OUT, exist_ok=True)

BLUE, GREY, TEAL = "#1f6feb", "#9aa4b2", "#117733"


def _load(name):
    return json.load(open(os.path.join(RESULTS, name)))


def fig_reaim():
    d = _load("reaim_funnel.json")
    ms = [m for m in d if m != "_total"]
    ms.sort(key=lambda m: d[m]["reached"], reverse=True)
    reached = [d[m]["reached"] for m in ms]
    responded = [d[m]["responded"] for m in ms]
    rates = [d[m]["response_rate"] for m in ms]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = range(len(ms))
    ax.barh(y, reached, color=GREY, label="Reached")
    ax.barh(y, responded, color=BLUE, label="Responded")
    for i, (r, rt) in enumerate(zip(reached, rates)):
        ax.text(r + max(reached) * 0.01, i, f"{rt*100:.1f}%", va="center", fontsize=9)
    ax.set_yticks(list(y)); ax.set_yticklabels(ms)
    ax.invert_yaxis()
    ax.set_xlabel("Members (2025)")
    ax.set_title("autoSMS reach and member response by HEDIS measure\n"
                 f"Total reached 13,014; overall reply rate {d['_total']['response_rate']*100:.1f}%",
                 fontsize=11)
    ax.legend(loc="lower right", frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = os.path.join(OUT, "figure1_reaim_reach_response.png")
    fig.savefig(p, dpi=300); plt.close(fig)
    return p


def fig_burden():
    d = _load("burden.json")
    bm = d["base"]["by_measure"]
    ms = sorted(bm, key=lambda m: bm[m]["hours"], reverse=True)
    hours = [bm[m]["hours"] for m in ms]
    colors = [TEAL if bm[m]["grounded"] else GREY for m in ms]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = range(len(ms))
    ax.barh(y, hours, color=colors)
    for i, m in enumerate(ms):
        ax.text(hours[i] + max(hours) * 0.01, i,
                f"{hours[i]:.0f} h ({bm[m]['min_per_patient']:.2f} min/pt)", va="center", fontsize=8)
    ax.set_yticks(list(y)); ax.set_yticklabels(ms)
    ax.invert_yaxis()
    ax.set_xlabel("Care-team hours absorbed (2025)")
    gf = d["base"]["grounded_only_hours"]; tot = d["base"]["total_hours"]
    ax.set_title("Manual chart-review burden absorbed by autoSMS reach\n"
                 f"Grounded floor {gf:.0f} h; full cohort {tot:.0f} h (~{d['base']['total_fte_year']:.2f} FTE-year)",
                 fontsize=11)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=TEAL, label="Grounded (direct time)"),
                       Patch(color=GREY, label="Analogy-mapped")],
              loc="lower right", frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = os.path.join(OUT, "figure2_burden_absorbed.png")
    fig.savefig(p, dpi=300); plt.close(fig)
    return p


if __name__ == "__main__":
    for p in (fig_reaim(), fig_burden()):
        print("wrote", p)
