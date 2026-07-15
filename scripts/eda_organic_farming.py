#!/usr/bin/env python3
"""Explore organic-farming shares and candidate exposure groups."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "aee-organicfarming-matplotlib"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_PANEL = ROOT / "data" / "dataset" / "gw_nitrate_panel_ni.csv"
DEFAULT_COUNTY = (
    ROOT
    / "data"
    / "regionalstatistik"
    / "processed"
    / "regionalstatistik_county_year_ni.csv"
)
DEFAULT_MAPPING = (
    ROOT
    / "data"
    / "regionalstatistik"
    / "processed"
    / "station_county_mapping.csv"
)
DEFAULT_RESULTS = ROOT / "results" / "organic_farming_eda"
DEFAULT_FIGURES = ROOT / "figures" / "organic_farming_eda"
SNAPSHOT_YEARS = (2010, 2016, 2020)
BASELINE_YEARS = (2012, 2015)
LATE_YEARS = (2019, 2022)


def numeric(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")


def pretrend_slopes(nitrate: pd.DataFrame) -> pd.Series:
    slopes = {}
    baseline = nitrate[nitrate["year"].between(*BASELINE_YEARS)]
    for district_code, group in baseline.groupby("district_code"):
        if group["year"].nunique() >= 3:
            slopes[district_code] = np.polyfit(
                group["year"],
                group["nitrate_mg_l"],
                1,
            )[0]
    return pd.Series(slopes, name="baseline_nitrate_slope")


def standardised_mean_difference(
    treatment: pd.Series,
    control: pd.Series,
) -> float:
    treatment = treatment.dropna()
    control = control.dropna()
    pooled_sd = np.sqrt((treatment.var(ddof=1) + control.var(ddof=1)) / 2)
    if not np.isfinite(pooled_sd) or pooled_sd == 0:
        return np.nan
    return (treatment.mean() - control.mean()) / pooled_sd


def build_district_summary(
    panel: pd.DataFrame,
    county: pd.DataFrame,
    mapping: pd.DataFrame,
) -> tuple[pd.DataFrame, float, float]:
    sampled_codes = set(mapping["district_code"])
    snapshots = county[
        county["district_code"].isin(sampled_codes)
        & county["year"].isin((2016, 2020))
    ].pivot(
        index=["district_code", "district_name"],
        columns="year",
        values=[
            "reg_organic_area_share",
            "reg_organic_farm_share",
            "reg_agricultural_area_ha",
        ],
    )
    snapshots.columns = [
        f"{column}_{year}" for column, year in snapshots.columns
    ]
    summary = snapshots.reset_index()
    summary["organic_area_change_2016_2020"] = (
        summary["reg_organic_area_share_2020"]
        - summary["reg_organic_area_share_2016"]
    )
    summary["organic_area_change_pp"] = (
        100 * summary["organic_area_change_2016_2020"]
    )
    summary["organic_area_relative_change"] = (
        summary["organic_area_change_2016_2020"]
        / summary["reg_organic_area_share_2016"]
    )

    nitrate = (
        panel.groupby(["district_code", "year"], as_index=False)[
            "nitrate_mg_l"
        ]
        .mean()
    )
    baseline_nitrate = (
        nitrate[nitrate["year"].between(*BASELINE_YEARS)]
        .groupby("district_code")["nitrate_mg_l"]
        .mean()
        .rename("baseline_nitrate_mean")
    )
    late_nitrate = (
        nitrate[nitrate["year"].between(*LATE_YEARS)]
        .groupby("district_code")["nitrate_mg_l"]
        .mean()
        .rename("late_nitrate_mean")
    )
    summary = summary.merge(
        baseline_nitrate.reset_index(),
        on="district_code",
        how="left",
    )
    summary = summary.merge(
        late_nitrate.reset_index(),
        on="district_code",
        how="left",
    )
    summary = summary.merge(
        pretrend_slopes(nitrate)
        .rename_axis("district_code")
        .reset_index(),
        on="district_code",
        how="left",
    )
    summary["nitrate_change_late_minus_baseline"] = (
        summary["late_nitrate_mean"] - summary["baseline_nitrate_mean"]
    )
    station_counts = (
        mapping.groupby("district_code")["station_id"]
        .nunique()
        .rename("station_count")
    )
    summary = summary.merge(
        station_counts.reset_index(),
        on="district_code",
        how="left",
    )

    eligible = summary["organic_area_change_2016_2020"].notna()
    low_cutoff = summary.loc[
        eligible,
        "organic_area_change_2016_2020",
    ].quantile(0.25)
    high_cutoff = summary.loc[
        eligible,
        "organic_area_change_2016_2020",
    ].quantile(0.75)
    summary["candidate_group"] = "middle_exposure"
    summary.loc[~eligible, "candidate_group"] = "missing_organic_share"
    summary.loc[
        eligible
        & (
            summary["organic_area_change_2016_2020"]
            <= low_cutoff
        ),
        "candidate_group",
    ] = "low_growth_comparison"
    summary.loc[
        eligible
        & (
            summary["organic_area_change_2016_2020"]
            >= high_cutoff
        ),
        "candidate_group",
    ] = "high_growth_exposure"
    return summary, low_cutoff, high_cutoff


def yearly_summary(
    county: pd.DataFrame,
    sampled_codes: set[str],
) -> pd.DataFrame:
    sampled = county[county["district_code"].isin(sampled_codes)]
    return (
        sampled.groupby(["year", "regio_temporal_method"])
        .agg(
            districts=("district_code", "nunique"),
            observed_districts=("reg_organic_area_share", "count"),
            organic_area_share_mean=("reg_organic_area_share", "mean"),
            organic_area_share_median=("reg_organic_area_share", "median"),
            organic_area_share_q25=(
                "reg_organic_area_share",
                lambda values: values.quantile(0.25),
            ),
            organic_area_share_q75=(
                "reg_organic_area_share",
                lambda values: values.quantile(0.75),
            ),
            organic_farm_share_mean=("reg_organic_farm_share", "mean"),
        )
        .reset_index()
    )


def group_balance(summary: pd.DataFrame) -> pd.DataFrame:
    selected = summary[
        summary["candidate_group"].isin(
            ["high_growth_exposure", "low_growth_comparison"]
        )
    ]
    treatment = selected[
        selected["candidate_group"] == "high_growth_exposure"
    ]
    control = selected[
        selected["candidate_group"] == "low_growth_comparison"
    ]
    variables = {
        "organic_area_share_2016": "reg_organic_area_share_2016",
        "organic_farm_share_2016": "reg_organic_farm_share_2016",
        "agricultural_area_ha_2016": "reg_agricultural_area_ha_2016",
        "baseline_nitrate_mean_2012_2015": "baseline_nitrate_mean",
        "baseline_nitrate_slope_2012_2015": "baseline_nitrate_slope",
    }
    records = []
    for label, column in variables.items():
        records.append(
            {
                "variable": label,
                "high_growth_mean": treatment[column].mean(),
                "low_growth_mean": control[column].mean(),
                "difference": treatment[column].mean()
                - control[column].mean(),
                "standardised_mean_difference": standardised_mean_difference(
                    treatment[column],
                    control[column],
                ),
                "high_growth_n": treatment[column].count(),
                "low_growth_n": control[column].count(),
            }
        )
    return pd.DataFrame(records)


def nitrate_trajectory(
    panel: pd.DataFrame,
    summary: pd.DataFrame,
) -> pd.DataFrame:
    groups = summary[["district_code", "candidate_group"]]
    district_year = (
        panel.groupby(["district_code", "year"], as_index=False)[
            "nitrate_mg_l"
        ]
        .mean()
        .merge(groups, on="district_code", how="left")
    )
    selected = district_year[
        district_year["candidate_group"].isin(
            ["high_growth_exposure", "low_growth_comparison"]
        )
    ]
    return (
        selected.groupby(["candidate_group", "year"])["nitrate_mg_l"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(
            columns={
                "mean": "district_weighted_nitrate_mean",
                "std": "district_nitrate_sd",
                "count": "district_count",
            }
        )
    )


def plot_snapshots(
    county: pd.DataFrame,
    sampled_codes: set[str],
    output: Path,
) -> None:
    values = [
        county[
            (county["district_code"].isin(sampled_codes))
            & (county["year"] == year)
        ]["reg_organic_area_share"].dropna()
        * 100
        for year in SNAPSHOT_YEARS
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.boxplot(values, tick_labels=[str(year) for year in SNAPSHOT_YEARS])
    for index, series in enumerate(values, start=1):
        jitter = np.linspace(-0.08, 0.08, len(series))
        ax.scatter(
            np.full(len(series), index) + jitter,
            series,
            s=14,
            alpha=0.55,
            color="#2f6f4e",
        )
    ax.set_ylabel("Organic agricultural area (%)")
    ax.set_xlabel("Agricultural census snapshot")
    ax.set_title("Organic area shares across sampled districts")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_growth(summary: pd.DataFrame, output: Path) -> None:
    colors = {
        "high_growth_exposure": "#b13f2f",
        "low_growth_comparison": "#286a9b",
        "middle_exposure": "#9a9a9a",
        "missing_organic_share": "#d8d8d8",
    }
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for group, data in summary.groupby("candidate_group"):
        ax.scatter(
            100 * data["reg_organic_area_share_2016"],
            data["organic_area_change_pp"],
            label=group.replace("_", " "),
            color=colors[group],
            s=38,
            alpha=0.85,
        )
    selected = summary[
        summary["candidate_group"] == "high_growth_exposure"
    ]
    for _, row in selected.iterrows():
        ax.annotate(
            row["district_name"],
            (
                100 * row["reg_organic_area_share_2016"],
                row["organic_area_change_pp"],
            ),
            fontsize=6.5,
            xytext=(3, 3),
            textcoords="offset points",
        )
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_xlabel("Organic area share in 2016 (%)")
    ax.set_ylabel("Change from 2016 to 2020 (percentage points)")
    ax.set_title("Candidate exposure groups are not baseline-balanced")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_nitrate(trajectory: pd.DataFrame, output: Path) -> None:
    colors = {
        "high_growth_exposure": "#b13f2f",
        "low_growth_comparison": "#286a9b",
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for group, data in trajectory.groupby("candidate_group"):
        ax.plot(
            data["year"],
            data["district_weighted_nitrate_mean"],
            marker="o",
            linewidth=1.8,
            color=colors[group],
            label=group.replace("_", " "),
        )
    ax.axvline(
        2016,
        color="#555555",
        linestyle="--",
        linewidth=1,
        label="classification baseline",
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean nitrate (mg/L), districts equally weighted")
    ax.set_title("Nitrate trajectories for candidate exposure groups")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def write_summary(
    path: Path,
    district_summary: pd.DataFrame,
    balance: pd.DataFrame,
    low_cutoff: float,
    high_cutoff: float,
) -> None:
    eligible = district_summary[
        district_summary["organic_area_change_2016_2020"].notna()
    ]
    treatment = district_summary[
        district_summary["candidate_group"] == "high_growth_exposure"
    ]
    control = district_summary[
        district_summary["candidate_group"] == "low_growth_comparison"
    ]
    correlation = eligible[
        [
            "organic_area_change_2016_2020",
            "nitrate_change_late_minus_baseline",
        ]
    ].corr().iloc[0, 1]
    smd = balance.set_index("variable")["standardised_mean_difference"]
    text = f"""# Organic Farming EDA

## Main findings

- Organic-area shares are available for {len(eligible)} of the 40 sampled
  districts. Five districts are suppressed or missing.
- The mean district share increased from
  {100 * eligible['reg_organic_area_share_2016'].mean():.2f}% in 2016 to
  {100 * eligible['reg_organic_area_share_2020'].mean():.2f}% in 2020.
- Every eligible district recorded a positive increase. There is therefore no
  genuinely untreated or never-treated district.
- The descriptive correlation between 2016-2020 organic-area growth and the
  change in district nitrate means from 2012-2015 to 2019-2022 is
  {correlation:.2f}. This is not a causal estimate.

## Candidate groups

For exploratory plots only:

- `high_growth_exposure`: change of at least
  {100 * high_cutoff:.2f} percentage points, {len(treatment)} districts and
  {int(treatment['station_count'].sum())} stations.
- `low_growth_comparison`: change of at most
  {100 * low_cutoff:.2f} percentage points, {len(control)} districts and
  {int(control['station_count'].sum())} stations.

These are intensity groups, not identified treatment and control groups.
Treatment is assigned at Landkreis level, so inference must be clustered by
Landkreis rather than monitoring station.

## Why binary DiD is not yet credible

- There is no observed policy adoption date or exogenous treatment event.
- All eligible districts increase organic farming.
- The annual Regionalstatistik values between 2016 and 2020 are interpolated
  from two census snapshots and cannot support an annual event study.
- Baseline balance is weak: the standardised mean difference is
  {smd['organic_area_share_2016']:.2f} for the 2016 organic-area share and
  {smd['agricultural_area_ha_2016']:.2f} for agricultural area.
- The baseline nitrate-trend SMD is
  {smd['baseline_nitrate_slope_2012_2015']:.2f}, which does not establish
  parallel trends with only nine districts per group.

## Recommended next model

Use organic-area share as a continuous Landkreis-level exposure in a
station-and-year fixed-effects model, cluster standard errors by Landkreis, and
restrict the primary window to observed census years or explicitly label
interpolated exposure. A binary DiD should wait for a defensible external
policy/adoption date.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--county", type=Path, default=DEFAULT_COUNTY)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES)
    args = parser.parse_args()

    panel = pd.read_csv(args.panel, dtype={"district_code": str})
    county = pd.read_csv(args.county, dtype={"district_code": str})
    mapping = pd.read_csv(args.mapping, dtype={"district_code": str})
    numeric(
        panel,
        ["nitrate_mg_l"],
    )
    numeric(
        county,
        [
            "reg_organic_area_share",
            "reg_organic_farm_share",
            "reg_agricultural_area_ha",
        ],
    )

    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)

    district_summary, low_cutoff, high_cutoff = build_district_summary(
        panel,
        county,
        mapping,
    )
    yearly = yearly_summary(county, set(mapping["district_code"]))
    balance = group_balance(district_summary)
    trajectory = nitrate_trajectory(panel, district_summary)
    candidates = district_summary[
        district_summary["candidate_group"].isin(
            ["high_growth_exposure", "low_growth_comparison"]
        )
    ]

    district_summary.to_csv(
        args.results_dir / "district_organic_change_2016_2020.csv",
        index=False,
    )
    candidates.to_csv(
        args.results_dir / "candidate_exposure_groups.csv",
        index=False,
    )
    yearly.to_csv(args.results_dir / "yearly_organic_summary.csv", index=False)
    balance.to_csv(args.results_dir / "candidate_group_balance.csv", index=False)
    trajectory.to_csv(
        args.results_dir / "candidate_group_nitrate_trajectory.csv",
        index=False,
    )
    write_summary(
        args.results_dir / "summary.md",
        district_summary,
        balance,
        low_cutoff,
        high_cutoff,
    )

    plot_snapshots(
        county,
        set(mapping["district_code"]),
        args.figures_dir / "organic_share_snapshots.png",
    )
    plot_growth(
        district_summary,
        args.figures_dir / "organic_growth_vs_baseline.png",
    )
    plot_nitrate(
        trajectory,
        args.figures_dir / "candidate_group_nitrate_trajectories.png",
    )

    print(f"Eligible districts: {district_summary['organic_area_change_2016_2020'].notna().sum()}")
    print(f"High-growth districts: {len(candidates[candidates['candidate_group'] == 'high_growth_exposure'])}")
    print(f"Low-growth districts: {len(candidates[candidates['candidate_group'] == 'low_growth_comparison'])}")
    print(args.results_dir / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
