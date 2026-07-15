#!/usr/bin/env python3
"""Create a timeline graphic for source availability in the nitrate panel."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MPLCONFIGDIR = ROOT / ".matplotlib-cache"
MPLCONFIGDIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


FIGURE_DIR = ROOT / "figures" / "data_timeline"
FIGURE_PATH = FIGURE_DIR / "data_availability_timeline_2006_2022.png"

START_YEAR = 2010
END_YEAR = 2022
MAIN_START = 2012
MAIN_END = 2020

ROWS = [
    {
        "label": "UBA nitrate",
        "kind": "continuous",
        "start": 2012,
        "end": 2022,
        "color": "#C50E1F",
    },
    {
        "label": "Regionalstatistik",
        "kind": "snapshots",
        "snapshots": [2010, 2016, 2020],
        "color": "#43CF4F",
    },
    {
        "label": "Dynamic World",
        "kind": "continuous",
        "start": 2016,
        "end": 2022,
        "color": "#3098D0",
    },
    {
        "label": "CORINE Land Cover",
        "kind": "snapshots",
        "snapshots": [2012, 2018],
        "color": "#35B8BE",
    },
]


def add_span(ax: plt.Axes, y: float, start: int, end: int, color: str) -> None:
    ax.add_patch(
        Rectangle(
            (start, y - 0.18),
            end - start,
            0.36,
            facecolor=color,
            edgecolor="none",
            alpha=0.88,
            zorder=2,
        )
    )


def main() -> int:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 14,
            "axes.titlesize": 18,
            "axes.labelsize": 14,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
        }
    )

    fig, ax = plt.subplots(figsize=(13, 6.8), constrained_layout=True)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.axvspan(
        MAIN_START,
        MAIN_END,
        color="#DDF3DF",
        alpha=0.92,
        zorder=0,
    )
    y_positions = list(range(len(ROWS)))[::-1]
    for row, y in zip(ROWS, y_positions, strict=True):
        color = row["color"]

        if row["kind"] == "snapshots":
            snapshots = row["snapshots"]
            for left, right in zip(snapshots, snapshots[1:], strict=False):
                ax.plot(
                    [left, right],
                    [y, y],
                    color=color,
                    linewidth=2.2,
                    alpha=0.88,
                    solid_capstyle="round",
                    zorder=3,
                )
            for snap in snapshots:
                ax.scatter(
                    snap,
                    y,
                    s=210,
                    color=color,
                    edgecolor="#FFFFFF",
                    linewidth=2.2,
                    zorder=4,
                )
        else:
            add_span(ax, y, row["start"], row["end"], color)

    ax.set_xlim(START_YEAR - 0.2, END_YEAR + 0.7)
    ax.set_ylim(-0.75, len(ROWS) - 0.05)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([row["label"] for row in ROWS])
    ax.set_xticks(range(START_YEAR, END_YEAR + 1, 2))
    ax.set_xlabel("Year")

    for tick in ax.get_yticklabels():
        tick.set_fontweight("bold")

    ax.grid(axis="x", color="#D7D0C7", linewidth=0.8, alpha=0.75)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="both", length=0, colors="#49413D")
    for spine in ax.spines.values():
        spine.set_visible(False)

    legend_y = -0.57
    ax.scatter(2009.0, legend_y, s=135, color="#49413D", edgecolor="#FFFFFF")
    ax.text(2009.35, legend_y, "year availability", va="center", fontsize=14, color="#49413D")
    ax.plot([2012.9, 2014.15], [legend_y, legend_y], color="#49413D", linewidth=2.2)
    ax.text(2014.45, legend_y, "interpolation", va="center", fontsize=14, color="#49413D")
    ax.plot([2016.8, 2018.1], [legend_y, legend_y], color="#49413D", linewidth=7)
    ax.text(2018.4, legend_y, "continuous annual coverage", va="center", fontsize=14, color="#49413D")

    fig.savefig(FIGURE_PATH, dpi=220)
    print(FIGURE_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
