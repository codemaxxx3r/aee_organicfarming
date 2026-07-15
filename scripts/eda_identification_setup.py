#!/usr/bin/env python3
"""Classical EDA for organic-farming growth and nitrate pollution."""

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
import numpy as np
import pandas as pd


PANEL_PATH = ROOT / "data" / "dataset" / "gw_nitrate_panel_ni.csv"
COUNTY_PATH = (
    ROOT
    / "data"
    / "regionalstatistik"
    / "processed"
    / "regionalstatistik_county_year_ni.csv"
)
FIGURE_DIR = ROOT / "figures" / "identification_eda"
RESULTS_DIR = ROOT / "results" / "identification_eda"

RED = "#C50E1F"
GREEN = "#43CF4F"
BLUE = "#3098D0"
TEAL = "#35B8BE"
DARK = "#3F3936"
GRID = "#DDD8D2"

BASELINE_YEARS = (2012, 2015)
EXPOSURE_YEARS = (2016, 2020)


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 14,
            "axes.labelsize": 14,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 13,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.9)
    ax.grid(axis="x", color=GRID, linewidth=0.65, alpha=0.55)
    ax.tick_params(axis="both", length=0, colors=DARK)
    for spine in ax.spines.values():
        spine.set_visible(False)


def mean_between(
    frame: pd.DataFrame,
    value_col: str,
    start: int,
    end: int,
) -> pd.Series:
    return (
        frame.loc[frame["year"].between(start, end)]
        .groupby("district_code")[value_col]
        .mean()
    )


def fit_line(data: pd.DataFrame, x_col: str, y_col: str) -> tuple[float, float, float]:
    clean = data[[x_col, y_col]].dropna()
    slope, intercept = np.polyfit(clean[x_col], clean[y_col], 1)
    correlation = clean[x_col].corr(clean[y_col])
    return slope, intercept, correlation


def build_district_eda(panel: pd.DataFrame, county: pd.DataFrame) -> pd.DataFrame:
    organic = county[county["year"].isin(EXPOSURE_YEARS)].pivot(
        index=["district_code", "district_name"],
        columns="year",
        values="reg_organic_area_share",
    )
    organic.columns = [f"organic_share_{year}" for year in organic.columns]
    eda = organic.reset_index()
    eda["organic_growth_2016_2020"] = (
        eda["organic_share_2020"] - eda["organic_share_2016"]
    )
    eda["organic_growth_pp"] = 100 * eda["organic_growth_2016_2020"]
    eda["organic_share_2020_pct"] = 100 * eda["organic_share_2020"]

    district_year = (
        panel.groupby(["district_code", "district_name", "year"], as_index=False)
        .agg(
            nitrate_mg_l=("nitrate_mg_l", "mean"),
            stations=("station_id", "nunique"),
        )
    )
    station_counts = (
        panel.groupby("district_code")["station_id"]
        .nunique()
        .rename("station_count")
    )
    nitrate_means = pd.DataFrame(
        {
            "nitrate_baseline_2012_2015": mean_between(
                district_year,
                "nitrate_mg_l",
                *BASELINE_YEARS,
            ),
            "nitrate_2016_2020": mean_between(
                district_year,
                "nitrate_mg_l",
                *EXPOSURE_YEARS,
            ),
            "nitrate_2020": district_year[district_year["year"] == 2020]
            .set_index("district_code")["nitrate_mg_l"],
        }
    )
    eda = eda.merge(nitrate_means.reset_index(), on="district_code", how="left")
    eda = eda.merge(station_counts.reset_index(), on="district_code", how="left")
    eda["nitrate_change_2016_2020_vs_baseline"] = (
        eda["nitrate_2016_2020"] - eda["nitrate_baseline_2012_2015"]
    )

    pretrend_rows = []
    for district_code, group in district_year[
        district_year["year"].between(*BASELINE_YEARS)
    ].groupby("district_code"):
        if group["year"].nunique() >= 3:
            pretrend_rows.append(
                {
                    "district_code": district_code,
                    "baseline_nitrate_slope_2012_2015": np.polyfit(
                        group["year"],
                        group["nitrate_mg_l"],
                        1,
                    )[0],
                }
            )
    eda = eda.merge(pd.DataFrame(pretrend_rows), on="district_code", how="left")

    eligible = eda["organic_growth_2016_2020"].notna()
    low_cutoff = eda.loc[eligible, "organic_growth_2016_2020"].quantile(0.25)
    high_cutoff = eda.loc[eligible, "organic_growth_2016_2020"].quantile(0.75)
    eda["organic_growth_group"] = "middle growth"
    eda.loc[~eligible, "organic_growth_group"] = "missing organic share"
    eda.loc[
        eligible & (eda["organic_growth_2016_2020"] <= low_cutoff),
        "organic_growth_group",
    ] = "low organic-growth districts"
    eda.loc[
        eligible & (eda["organic_growth_2016_2020"] >= high_cutoff),
        "organic_growth_group",
    ] = "high organic-growth districts"
    return eda


def plot_group_trajectory(
    panel: pd.DataFrame,
    eda: pd.DataFrame,
    output: Path,
) -> pd.DataFrame:
    groups = eda[["district_code", "organic_growth_group"]]
    district_year = (
        panel.groupby(["district_code", "year"], as_index=False)["nitrate_mg_l"]
        .mean()
        .merge(groups, on="district_code", how="left")
    )
    selected = district_year[
        district_year["organic_growth_group"].isin(
            ["high organic-growth districts", "low organic-growth districts"]
        )
    ]
    trajectory = (
        selected.groupby(["organic_growth_group", "year"])["nitrate_mg_l"]
        .agg(mean="mean", median="median", districts="count")
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.0), constrained_layout=True)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.axvspan(2016, 2020, color=GREEN, alpha=0.12, linewidth=0)

    colors = {
        "high organic-growth districts": GREEN,
        "low organic-growth districts": BLUE,
    }
    for group, data in trajectory.groupby("organic_growth_group"):
        ax.plot(
            data["year"],
            data["mean"],
            marker="o",
            markersize=7.5,
            markeredgecolor="#FFFFFF",
            markeredgewidth=1.5,
            linewidth=3.0,
            color=colors[group],
            label=group,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Mean nitrate concentration (mg/L)")
    ax.set_xticks(range(2012, 2021))
    ax.set_xlim(2011.5, 2020.5)
    ax.text(2016.1, ax.get_ylim()[1] * 0.93, "Organic-growth window", fontsize=12, color=DARK)
    ax.legend(frameon=False, loc="best")
    clean_axes(ax)
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return trajectory


def plot_scatter(
    eda: pd.DataFrame,
    x_col: str,
    y_col: str,
    output: Path,
    xlabel: str,
    ylabel: str,
    color: str,
) -> float:
    data = eda.dropna(subset=[x_col, y_col])
    slope, intercept, correlation = fit_line(data, x_col, y_col)
    x_line = np.linspace(data[x_col].min(), data[x_col].max(), 100)
    y_line = intercept + slope * x_line

    fig, ax = plt.subplots(figsize=(9.8, 6.0), constrained_layout=True)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    sizes = 34 + 8 * data["station_count"].fillna(1)
    ax.scatter(
        data[x_col],
        data[y_col],
        s=sizes,
        color=color,
        alpha=0.58,
        edgecolor="#FFFFFF",
        linewidth=0.8,
        label="Districts",
    )
    ax.plot(
        x_line,
        y_line,
        color=RED,
        linewidth=3.0,
        label=f"Linear fit (r = {correlation:.2f})",
    )
    if y_col.startswith("nitrate_change"):
        ax.axhline(0, color=DARK, linewidth=1.0, alpha=0.75)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, loc="best")
    clean_axes(ax)
    fig.savefig(output, dpi=220)
    plt.close(fig)
    return correlation


def write_summary(
    eda: pd.DataFrame,
    growth_change_corr: float,
    level_corr: float,
    output: Path,
) -> None:
    eligible = eda.dropna(subset=["organic_growth_2016_2020"])
    high = eda[eda["organic_growth_group"] == "high organic-growth districts"]
    low = eda[eda["organic_growth_group"] == "low organic-growth districts"]
    high_pretrend = high["baseline_nitrate_slope_2012_2015"].mean()
    low_pretrend = low["baseline_nitrate_slope_2012_2015"].mean()
    high_baseline = high["nitrate_baseline_2012_2015"].mean()
    low_baseline = low["nitrate_baseline_2012_2015"].mean()

    text = f"""# Classical Identification EDA

## Setup

- Unit of comparison: Landkreis. Organic farming is measured at district level,
  so nitrate is aggregated from stations to district-year means.
- Exposure distinction: high vs. low growth in organic agricultural area share
  from 2016 to 2020.
- Pre-trend period: 2012-2015.
- Main descriptive outcome: mean nitrate in 2016-2020 minus mean nitrate in
  2012-2015.

## Descriptive Findings

- Eligible districts with observed organic shares: {len(eligible)}.
- Mean organic farming share increased from
  {100 * eligible['organic_share_2016'].mean():.2f}% in 2016 to
  {100 * eligible['organic_share_2020'].mean():.2f}% in 2020.
- High-growth districts: {len(high)}. Low-growth districts: {len(low)}.
- Baseline nitrate mean, 2012-2015: {high_baseline:.2f} mg/L in high-growth
  districts and {low_baseline:.2f} mg/L in low-growth districts.
- Baseline nitrate slope, 2012-2015: {high_pretrend:.2f} mg/L per year in
  high-growth districts and {low_pretrend:.2f} mg/L per year in low-growth
  districts.
- Correlation between organic growth and nitrate change: {growth_change_corr:.2f}.
- Correlation between 2020 organic share and 2020 nitrate level: {level_corr:.2f}.

## Interpretation

The change-on-change EDA shows a negative descriptive relationship: districts
with stronger organic farming growth tend to have lower nitrate changes over
2016-2020 relative to the 2012-2015 baseline. This is suggestive, not causal.
The pre-trend check is not clean enough for a simple binary Difference-in-
Differences design, because high- and low-growth districts already differ in
their baseline nitrate dynamics. The safer next step is a continuous exposure
model with station and year fixed effects, not a strict treatment/control event
study.
"""
    output.write_text(text, encoding="utf-8")


def main() -> int:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    configure_style()

    panel = pd.read_csv(PANEL_PATH, dtype={"district_code": str})
    county = pd.read_csv(COUNTY_PATH, dtype={"district_code": str})
    for frame in (panel, county):
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    panel["nitrate_mg_l"] = pd.to_numeric(panel["nitrate_mg_l"], errors="coerce")
    county["reg_organic_area_share"] = pd.to_numeric(
        county["reg_organic_area_share"],
        errors="coerce",
    )

    eda = build_district_eda(panel, county)
    eda.to_csv(RESULTS_DIR / "district_identification_eda.csv", index=False)

    trajectory = plot_group_trajectory(
        panel,
        eda,
        FIGURE_DIR / "nitrate_trajectory_by_organic_growth_group.png",
    )
    trajectory.to_csv(
        RESULTS_DIR / "nitrate_trajectory_by_organic_growth_group.csv",
        index=False,
    )

    growth_change_corr = plot_scatter(
        eda,
        "organic_growth_pp",
        "nitrate_change_2016_2020_vs_baseline",
        FIGURE_DIR / "organic_growth_vs_nitrate_change_2016_2020.png",
        "Organic farming share change, 2016-2020 (percentage points)",
        "Nitrate change: 2016-2020 minus 2012-2015 (mg/L)",
        TEAL,
    )
    level_corr = plot_scatter(
        eda,
        "organic_share_2020_pct",
        "nitrate_2020",
        FIGURE_DIR / "organic_share_2020_vs_nitrate_2020.png",
        "Organic farming share in 2020 (%)",
        "Nitrate concentration in 2020 (mg/L)",
        BLUE,
    )
    write_summary(
        eda,
        growth_change_corr,
        level_corr,
        RESULTS_DIR / "summary.md",
    )

    print(RESULTS_DIR / "summary.md")
    print(FIGURE_DIR / "nitrate_trajectory_by_organic_growth_group.png")
    print(FIGURE_DIR / "organic_growth_vs_nitrate_change_2016_2020.png")
    print(FIGURE_DIR / "organic_share_2020_vs_nitrate_2020.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
