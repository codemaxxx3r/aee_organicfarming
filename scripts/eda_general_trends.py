#!/usr/bin/env python3
"""Create general EDA trend graphics for nitrate and organic farming."""

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
REGIONALSTATISTIK_PATH = (
    ROOT
    / "data"
    / "regionalstatistik"
    / "processed"
    / "regionalstatistik_county_year_ni.csv"
)
FIGURE_DIR = ROOT / "figures" / "general_eda"
RESULTS_DIR = ROOT / "results" / "general_eda"

RED = "#C50E1F"
GREEN = "#43CF4F"
DARK = "#3F3936"
GRID = "#DDD8D2"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 14,
            "axes.labelsize": 14,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 14,
        }
    )


def summarize(
    data: pd.DataFrame,
    value_col: str,
    unit_col: str,
    year_min: int,
    year_max: int,
) -> pd.DataFrame:
    subset = data.loc[
        data["year"].between(year_min, year_max),
        ["year", unit_col, value_col],
    ].dropna()
    summary = (
        subset.groupby("year")[value_col]
        .agg(
            mean="mean",
            median="median",
            q25=lambda values: values.quantile(0.25),
            q75=lambda values: values.quantile(0.75),
            n_units="count",
        )
        .reset_index()
    )
    unit_counts = (
        subset.groupby("year")[unit_col]
        .nunique()
        .rename("n_unique_units")
        .reset_index()
    )
    return summary.merge(unit_counts, on="year", how="left")


def clean_axes(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.9)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", length=0, colors=DARK)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_trend(
    summary: pd.DataFrame,
    output: Path,
    color: str,
    ylabel: str,
    xlabel: str,
    y_multiplier: float = 1.0,
) -> None:
    years = summary["year"].to_numpy()
    mean = summary["mean"].to_numpy() * y_multiplier
    q25 = summary["q25"].to_numpy() * y_multiplier
    q75 = summary["q75"].to_numpy() * y_multiplier

    fig, ax = plt.subplots(figsize=(10.5, 5.8), constrained_layout=True)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.fill_between(
        years,
        q25,
        q75,
        color=color,
        alpha=0.18,
        linewidth=0,
        label="25th-75th percentile",
    )
    ax.plot(
        years,
        mean,
        color=color,
        linewidth=3.2,
        marker="o",
        markersize=7.5,
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label="Mean",
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(years)
    ax.legend(frameon=False, loc="best")
    clean_axes(ax)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_point_cloud(
    data: pd.DataFrame,
    summary: pd.DataFrame,
    output: Path,
    value_col: str,
    year_min: int,
    year_max: int,
    color: str,
    ylabel: str,
    xlabel: str,
    y_multiplier: float = 1.0,
) -> None:
    rng = np.random.default_rng(20260715)
    subset = data.loc[
        data["year"].between(year_min, year_max),
        ["year", value_col],
    ].dropna()
    x = subset["year"].to_numpy(dtype=float)
    y = subset[value_col].to_numpy(dtype=float) * y_multiplier
    jittered_x = x + rng.uniform(-0.18, 0.18, size=len(subset))

    fig, ax = plt.subplots(figsize=(10.5, 5.8), constrained_layout=True)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    ax.scatter(
        jittered_x,
        y,
        s=21,
        color=color,
        alpha=0.24,
        edgecolors="none",
        label="Observations",
    )
    ax.plot(
        summary["year"],
        summary["mean"] * y_multiplier,
        color=color,
        linewidth=3.2,
        marker="o",
        markersize=7.5,
        markeredgecolor="#FFFFFF",
        markeredgewidth=1.5,
        label="Mean",
    )

    ax.set_xlim(year_min - 0.55, year_max + 0.55)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(year_min, year_max + 1))
    ax.legend(frameon=False, loc="best")
    clean_axes(ax)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> int:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    configure_style()

    panel = pd.read_csv(PANEL_PATH)
    regional = pd.read_csv(REGIONALSTATISTIK_PATH)

    nitrate_summary = summarize(
        panel,
        value_col="nitrate_mg_l",
        unit_col="station_id",
        year_min=2012,
        year_max=2022,
    )
    organic_summary = summarize(
        regional,
        value_col="reg_organic_area_share",
        unit_col="district_code",
        year_min=2010,
        year_max=2020,
    )

    nitrate_summary.to_csv(
        RESULTS_DIR / "nitrate_trend_2012_2022.csv",
        index=False,
    )
    organic_summary.to_csv(
        RESULTS_DIR / "organic_area_share_trend_2010_2020.csv",
        index=False,
    )

    plot_trend(
        nitrate_summary,
        FIGURE_DIR / "nitrate_trend_2012_2022.png",
        color=RED,
        ylabel="Nitrate concentration (mg/L)",
        xlabel="Year",
    )
    plot_trend(
        organic_summary,
        FIGURE_DIR / "organic_area_share_trend_2010_2020.png",
        color=GREEN,
        ylabel="Organic farming share (%)",
        xlabel="Year",
        y_multiplier=100,
    )
    plot_point_cloud(
        panel,
        nitrate_summary,
        FIGURE_DIR / "nitrate_point_cloud_2012_2022.png",
        value_col="nitrate_mg_l",
        year_min=2012,
        year_max=2022,
        color=RED,
        ylabel="Nitrate concentration (mg/L)",
        xlabel="Year",
    )
    plot_point_cloud(
        regional,
        organic_summary,
        FIGURE_DIR / "organic_area_share_point_cloud_2010_2020.png",
        value_col="reg_organic_area_share",
        year_min=2010,
        year_max=2020,
        color=GREEN,
        ylabel="Organic farming share (%)",
        xlabel="Year",
        y_multiplier=100,
    )

    print(FIGURE_DIR / "nitrate_trend_2012_2022.png")
    print(FIGURE_DIR / "organic_area_share_trend_2010_2020.png")
    print(FIGURE_DIR / "nitrate_point_cloud_2012_2022.png")
    print(FIGURE_DIR / "organic_area_share_point_cloud_2010_2020.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
