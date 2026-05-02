"""
Chart generators. Each function returns a BytesIO PNG buffer
ready to be embedded into a pptx slide.
"""
from __future__ import annotations
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from theme import C_BLUE, C_AMBER, C_GREEN, C_GRAY, C_BG, C_TEXT, C_DIM

plt.rcParams.update({
    "figure.facecolor":  C_BG,
    "axes.facecolor":    C_BG,
    "axes.edgecolor":    C_DIM,
    "axes.labelcolor":   C_TEXT,
    "xtick.color":       C_TEXT,
    "ytick.color":       C_TEXT,
    "text.color":        C_TEXT,
    "grid.color":        "#1E3050",
    "grid.linewidth":    0.8,
    "font.family":       "DejaVu Sans",
})


def _buf(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                facecolor=fig.get_facecolor(), dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Slide 6 — Node-type keyword density by corpus tier
# ---------------------------------------------------------------------------
def node_density_chart() -> BytesIO:
    node_types  = ["Component", "Interface", "Requirement", "Decision",
                   "Objective", "Risk", "Assumption"]
    github      = [3.69, 1.98, 2.86, 0.88, 0.41, 0.33, 0.08]
    stackoverflow = [7.83, 4.60, 2.58, 0.37, 0.61, 0.11, 0.07]
    postmortems = [5.05, 2.59, 0.37, 0.12, 0.00, 0.00, 0.00]

    x = np.arange(len(node_types))
    bw = 0.26

    fig, ax = plt.subplots(figsize=(9, 4.2))

    b1 = ax.bar(x - bw,   github,       bw, label="GitHub Issues",    color=C_BLUE,  alpha=0.92)
    b2 = ax.bar(x,         stackoverflow, bw, label="Stack Overflow",  color=C_AMBER, alpha=0.92)
    b3 = ax.bar(x + bw,   postmortems,  bw, label="Post-mortems",     color=C_GREEN, alpha=0.80)

    # value labels on bars
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            if h > 0.05:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.08,
                        f"{h:.2f}", ha="center", va="bottom",
                        fontsize=7.5, color=C_TEXT)

    ax.set_xticks(x)
    ax.set_xticklabels(node_types, fontsize=10)
    ax.set_ylabel("Hits per 1,000 words", fontsize=11)
    ax.set_ylim(0, 9.5)
    ax.yaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)

    legend = ax.legend(fontsize=10, framealpha=0.15,
                       labelcolor=C_TEXT, edgecolor=C_DIM,
                       loc="upper right")

    ax.tick_params(axis="both", which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(C_DIM)

    fig.tight_layout(pad=0.6)
    return _buf(fig)


# ---------------------------------------------------------------------------
# Slide 7 — Hedge signal (left) + Dependency verbs (right)
# ---------------------------------------------------------------------------
def hedge_chart() -> BytesIO:
    categories = ["Epistemic\nModal", "Conditional", "Confidence\nQualifier", "Scope\nHedge"]
    counts     = [203, 64, 29, 24]
    colors     = [C_BLUE, C_AMBER, C_GREEN, C_GRAY]

    fig, ax = plt.subplots(figsize=(4.2, 3.6))

    bars = ax.barh(categories[::-1], counts[::-1],
                   color=colors[::-1], alpha=0.92, height=0.55)

    for bar, val in zip(bars, counts[::-1]):
        ax.text(val + 3, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=11, color=C_TEXT, fontweight="bold")

    ax.set_xlabel("Sentence hits", fontsize=10)
    ax.set_xlim(0, 240)
    ax.xaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(C_DIM)
    ax.set_title("Hedge Signal (Assumption proxy)", fontsize=11,
                 color=C_TEXT, pad=8)

    fig.tight_layout(pad=0.5)
    return _buf(fig)


def dependency_chart() -> BytesIO:
    verbs  = ["uses", "calls", "requires", "depends on",
              "extends", "wraps", "imports from"]
    counts = [58, 51, 33, 12, 6, 3, 2]
    colors = [C_BLUE if i < 4 else C_AMBER for i in range(len(verbs))]

    fig, ax = plt.subplots(figsize=(4.2, 3.6))

    bars = ax.barh(verbs[::-1], counts[::-1],
                   color=colors[::-1], alpha=0.92, height=0.55)

    for bar, val in zip(bars, counts[::-1]):
        ax.text(val + 0.8, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=11, color=C_TEXT, fontweight="bold")

    ax.set_xlabel("Occurrences", fontsize=10)
    ax.set_xlim(0, 70)
    ax.xaxis.grid(True, linestyle="--")
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(C_DIM)
    ax.set_title("Dependency Verb Signal (Edge proxy)", fontsize=11,
                 color=C_TEXT, pad=8)

    # legend: blue = strong signal, amber = emerging
    p1 = mpatches.Patch(color=C_BLUE,  label="Strong signal (top 4)")
    p2 = mpatches.Patch(color=C_AMBER, label="Emerging signal")
    ax.legend(handles=[p1, p2], fontsize=8.5, framealpha=0.15,
              edgecolor=C_DIM, loc="lower right")

    fig.tight_layout(pad=0.5)
    return _buf(fig)
