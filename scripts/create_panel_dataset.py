#!/usr/bin/env python3
"""Merge processed source tables into the final analysis panel."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_UBA = (
    ROOT
    / "data"
    / "uba_nitrate_report_2024"
    / "processed"
    / "uba_nitrate_station_year_ni.csv"
)
DEFAULT_DYNAMIC_WORLD = (
    ROOT
    / "data"
    / "dynamic_world"
    / "processed"
    / "dynamic_world_station_year_ni.csv"
)
DEFAULT_CORINE = (
    ROOT
    / "data"
    / "corine_land_cover"
    / "processed"
    / "corine_station_year_ni.csv"
)
DEFAULT_REGIONALSTATISTIK = (
    ROOT
    / "data"
    / "regionalstatistik"
    / "processed"
    / "regionalstatistik_station_year_ni.csv"
)
DEFAULT_OUTPUT = ROOT / "data" / "dataset" / "gw_nitrate_panel_ni.csv"
KEY_COLUMNS = ("station_id", "year")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        missing = sorted(set(KEY_COLUMNS) - set(fieldnames))
        if missing:
            raise ValueError(f"{path} is missing key columns: {missing}")
        return fieldnames, list(reader)


def row_key(row: dict[str, str]) -> tuple[str, int]:
    return row["station_id"], int(float(row["year"]))


def index_unique(
    rows: list[dict[str, str]],
    source: Path,
) -> dict[tuple[str, int], dict[str, str]]:
    index: dict[tuple[str, int], dict[str, str]] = {}
    for row in rows:
        key = row_key(row)
        if key in index:
            raise ValueError(f"Duplicate station-year key in {source}: {key}")
        index[key] = row
    return index


def merge_covariates(
    base_columns: list[str],
    base_rows: list[dict[str, str]],
    covariate_path: Path,
    label: str,
) -> tuple[list[str], list[dict[str, str]], int]:
    covariate_source_columns, covariate_rows = read_csv(covariate_path)
    covariate_index = index_unique(covariate_rows, covariate_path)
    covariate_columns = [
        column
        for column in covariate_source_columns
        if column not in KEY_COLUMNS
    ]
    overlapping = sorted(set(base_columns) & set(covariate_columns))
    if overlapping:
        raise ValueError(f"{label} columns already exist in panel: {overlapping}")
    base_keys = {row_key(row) for row in base_rows}
    unexpected_keys = sorted(set(covariate_index) - base_keys)
    if unexpected_keys:
        print(
            f"Ignoring {len(unexpected_keys)} {label} station-years "
            "without nitrate data"
        )

    matched = 0
    output = []
    for row in base_rows:
        covariates = covariate_index.get(row_key(row))
        if covariates is not None:
            matched += 1
        output.append(
            row
            | {
                column: covariates.get(column, "") if covariates else ""
                for column in covariate_columns
            }
        )
    return base_columns + covariate_columns, output, matched


def merge(
    uba_path: Path,
    dynamic_world_path: Path | None,
    corine_path: Path | None,
    regionalstatistik_path: Path | None,
) -> tuple[list[str], list[dict[str, str]], dict[str, int]]:
    columns, rows = read_csv(uba_path)
    index_unique(rows, uba_path)
    matched = {}
    if dynamic_world_path is not None:
        columns, rows, matched["Dynamic World"] = merge_covariates(
            columns,
            rows,
            dynamic_world_path,
            "Dynamic World",
        )
    if corine_path is not None:
        columns, rows, matched["CORINE"] = merge_covariates(
            columns,
            rows,
            corine_path,
            "CORINE",
        )
    if regionalstatistik_path is not None:
        columns, rows, matched["Regionalstatistik"] = merge_covariates(
            columns,
            rows,
            regionalstatistik_path,
            "Regionalstatistik",
        )
    return columns, rows, matched


def write_csv(
    path: Path,
    columns: list[str],
    records: list[dict[str, str]],
) -> None:
    if not records:
        raise ValueError("Panel merge produced no records")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uba", type=Path, default=DEFAULT_UBA)
    parser.add_argument(
        "--dynamic-world",
        type=Path,
        default=DEFAULT_DYNAMIC_WORLD,
    )
    parser.add_argument("--corine", type=Path, default=DEFAULT_CORINE)
    parser.add_argument(
        "--regionalstatistik",
        type=Path,
        default=DEFAULT_REGIONALSTATISTIK,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-missing-dynamic-world",
        action="store_true",
        help="Create the panel without Dynamic World when it is not processed yet.",
    )
    parser.add_argument(
        "--allow-missing-corine",
        action="store_true",
        help="Create the panel without CORINE when it is not processed yet.",
    )
    parser.add_argument(
        "--allow-missing-regionalstatistik",
        action="store_true",
        help="Create the panel without Regionalstatistik when it is not processed.",
    )
    args = parser.parse_args()

    if not args.uba.exists():
        raise FileNotFoundError(f"Processed UBA data not found: {args.uba}")
    dynamic_world = args.dynamic_world
    if not dynamic_world.exists():
        if not args.allow_missing_dynamic_world:
            raise FileNotFoundError(
                f"Processed Dynamic World data not found: {dynamic_world}"
            )
        print("Dynamic World is missing; creating the panel without Dynamic World")
        dynamic_world = None

    corine = args.corine
    if not corine.exists():
        if not args.allow_missing_corine:
            raise FileNotFoundError(f"Processed CORINE data not found: {corine}")
        print("CORINE is missing; creating the panel without CORINE")
        corine = None

    regionalstatistik = args.regionalstatistik
    if not regionalstatistik.exists():
        if not args.allow_missing_regionalstatistik:
            raise FileNotFoundError(
                "Processed Regionalstatistik data not found: "
                f"{regionalstatistik}"
            )
        print(
            "Regionalstatistik is missing; creating the panel without it"
        )
        regionalstatistik = None

    columns, records, matched = merge(
        args.uba,
        dynamic_world,
        corine,
        regionalstatistik,
    )
    write_csv(args.output, columns, records)
    print(f"Wrote {len(records)} panel rows")
    for label, count in matched.items():
        print(f"Matched {count} rows with {label}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
