"""Regenerate the manuscript-final Figures 1 and 3 (five reported measures; no PHI).

Figures are numbered in order of first citation in the manuscript:
Figure 1 (file figure1_reach_response.png): reach and member response by measure.
Figure 3 (file figure3_burden_absorbed.png): manual per-patient identification time absorbed.

These reproduce the manuscript-final figures for the five REPORTED measures. Values match
CANONICAL_NUMBERS.md. The authoritative full pipeline for all six measures (including GSD)
and both comparison designs lives in the companion code repo:
    ../../../packaging/hedis-outreach-quality/  (scripts/50_figures.py, results/*.json)

Figure 2 (file figure2_did_eventstudy.png, the event study) is unaffected by the five-measure
scope and is not regenerated here.

Run:  python make_manuscript_figures.py     (writes PNGs into this directory)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

GREY, BLUE, GREEN = "#9a9aa2", "#2a6ddb", "#1a7a3c"

# Reported five measures, ordered by reach (descending). Source: CANONICAL_NUMBERS.md
REACH = [("WCV", 4754, 1090), ("AAP", 4575, 558), ("BCS-E", 1435, 204),
         ("CCS", 909, 162), ("EED", 419, 93)]
# Care-team hours absorbed, ordered by hours (descending).
HOURS = [("WCV", 158.5), ("AAP", 152.5), ("BCS-E", 47.8), ("CCS", 30.3), ("EED", 14.0)]


def _despine(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def figure2():
    labels = [m for m, _, _ in REACH]
    reached = [r for _, r, _ in REACH]
    replied = [p for _, _, p in REACH]
    rate = [f"{p / r * 100:.1f}%" for r, p in zip(reached, replied)]
    tot_r, tot_p = sum(reached), sum(replied)
    y = list(range(len(labels)))[::-1]
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.barh(y, reached, color=GREY, label="Reached", zorder=2)
    ax.barh(y, replied, color=BLUE, label="Replied", zorder=3)
    for yi, n, lab in zip(y, reached, rate):
        ax.text(n + 60, yi, lab, va="center", ha="left", fontsize=17)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=16)
    ax.set_xlabel("Members (2025)", fontsize=17)
    ax.set_xlim(0, max(reached) * 1.14)
    ax.tick_params(axis="x", labelsize=14)
    ax.set_title(f"Reach and member response by HEDIS measure\n"
                 f"Total reached {tot_r:,}; overall reply rate {tot_p / tot_r * 100:.1f}%",
                 fontsize=19, pad=14)
    ax.legend(loc="lower right", fontsize=16, frameon=False)
    _despine(ax); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figure1_reach_response.png"), bbox_inches="tight")
    plt.close(fig)


def figure3():
    labels = [m for m, _ in HOURS]
    hours = [h for _, h in HOURS]
    total = sum(hours)
    y = list(range(len(labels)))[::-1]
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.barh(y, hours, color=GREEN, zorder=2)
    for yi, h in zip(y, hours):
        ax.text(h + 1.5, yi, f"{round(h)} h", va="center", ha="left", fontsize=17)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=16)
    ax.set_xlabel("Care-team hours absorbed (2025)", fontsize=17)
    ax.set_xlim(0, max(hours) * 1.12)
    ax.tick_params(axis="x", labelsize=14)
    ax.set_title(f"Manual per-patient identification time absorbed\n"
                 f"Total {round(total)} hours (~{total / 2080:.2f} FTE-years); "
                 f"~{round(total / (sum(r for _, r, _ in REACH) / 1000))} hours per 1,000 open gaps",
                 fontsize=19, pad=14)
    _despine(ax); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "figure3_burden_absorbed.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    figure2()
    figure3()
    print("Wrote figure1_reach_response.png and figure3_burden_absorbed.png to", OUT)
