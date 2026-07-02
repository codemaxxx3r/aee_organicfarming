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


def merge(
    uba_path: Path,
    dynamic_world_path: Path | None,
) -> tuple[list[str], list[dict[str, str]], int]:
    uba_columns, uba_rows = read_csv(uba_path)
    index_unique(uba_rows, uba_path)
    if dynamic_world_path is None:
        return uba_columns, uba_rows, 0

    dynamic_columns, dynamic_rows = read_csv(dynamic_world_path)
    dynamic_index = index_unique(dynamic_rows, dynamic_world_path)
    covariate_columns = [
        column for column in dynamic_columns if column not in KEY_COLUMNS
    ]
    unexpected_keys = sorted(set(dynamic_index) - {row_key(row) for row in uba_rows})
    if unexpected_keys:
        print(
            "Ignoring "
            f"{len(unexpected_keys)} Dynamic World station-years without nitrate data"
        )

    matched = 0
    output = []
    for row in uba_rows:
        covariates = dynamic_index.get(row_key(row))
        if covariates is not None:
            matched += 1
        output.append(
            row
            | {
                column: covariates.get(column, "") if covariates else ""
                for column in covariate_columns
            }
        )
    return uba_columns + covariate_columns, output, matched


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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-missing-dynamic-world",
        action="store_true",
        help="Create an UBA-only panel when Dynamic World is not processed yet.",
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
        print("Dynamic World is missing; creating an UBA-only panel")
        dynamic_world = None

    columns, records, matched = merge(args.uba, dynamic_world)
    write_csv(args.output, columns, records)
    print(f"Wrote {len(records)} panel rows")
    if dynamic_world is not None:
        print(f"Matched {matched} rows with Dynamic World")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
