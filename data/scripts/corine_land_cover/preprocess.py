#!/usr/bin/env python3
"""Interpolate CORINE buffer shares between 2006, 2012, and 2018."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = (
    ROOT
    / "data"
    / "corine_land_cover"
    / "raw"
    / "corine_station_year_buffer_ni.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "corine_land_cover"
    / "processed"
    / "corine_station_year_ni.csv"
)
SNAPSHOT_YEARS = (2006, 2012, 2018)
BUFFER_METERS = (500, 1000)
BASE_METRICS = (
    "urban_fabric_share",
    "industrial_commercial_transport_share",
    "mine_dump_construction_share",
    "artificial_green_share",
    "arable_land_share",
    "permanent_crops_share",
    "pastures_share",
    "heterogeneous_agriculture_share",
    "forest_share",
    "shrub_herbaceous_share",
    "open_spaces_share",
    "wetlands_share",
    "water_share",
    "valid_data_share",
)
DERIVED_METRICS = ("artificial_total_share", "agriculture_total_share")
ALL_METRICS = BASE_METRICS + DERIVED_METRICS


def add_derived_metrics(values: dict[str, float]) -> dict[str, float]:
    return values | {
        "artificial_total_share": sum(
            values[name]
            for name in (
                "urban_fabric_share",
                "industrial_commercial_transport_share",
                "mine_dump_construction_share",
                "artificial_green_share",
            )
        ),
        "agriculture_total_share": sum(
            values[name]
            for name in (
                "arable_land_share",
                "permanent_crops_share",
                "pastures_share",
                "heterogeneous_agriculture_share",
            )
        ),
    }


def read_snapshots(
    path: Path,
) -> dict[tuple[str, int], dict[int, dict[str, float]]]:
    snapshots: dict[tuple[str, int], dict[int, dict[str, float]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"station_id", "year", "buffer_m", *BASE_METRICS}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"CORINE raw data is missing columns: {missing}")

        for row in reader:
            station_id = row["station_id"]
            year = int(float(row["year"]))
            buffer_m = int(float(row["buffer_m"]))
            if year not in SNAPSHOT_YEARS:
                raise ValueError(f"Unexpected CORINE snapshot year: {year}")
            if buffer_m not in BUFFER_METERS:
                raise ValueError(f"Unexpected CORINE buffer size: {buffer_m}")
            key = (station_id, buffer_m)
            if year in snapshots.setdefault(key, {}):
                raise ValueError(f"Duplicate CORINE key: {key + (year,)}")
            values = {metric: float(row[metric]) for metric in BASE_METRICS}
            snapshots[key][year] = add_derived_metrics(values)

    for key, years in snapshots.items():
        missing_years = sorted(set(SNAPSHOT_YEARS) - set(years))
        if missing_years:
            raise ValueError(f"Missing CORINE snapshots for {key}: {missing_years}")
    return snapshots


def interpolate(
    snapshots: dict[tuple[str, int], dict[int, dict[str, float]]],
) -> list[dict[str, object]]:
    stations = sorted({station_id for station_id, _ in snapshots})
    records = []
    for station_id in stations:
        for year in range(SNAPSHOT_YEARS[0], SNAPSHOT_YEARS[-1] + 1):
            lower_year = max(value for value in SNAPSHOT_YEARS if value <= year)
            upper_year = min(value for value in SNAPSHOT_YEARS if value >= year)
            weight = (
                0.0
                if lower_year == upper_year
                else (year - lower_year) / (upper_year - lower_year)
            )
            record: dict[str, object] = {
                "station_id": station_id,
                "year": year,
                "clc_temporal_method": (
                    "snapshot" if lower_year == upper_year else "linear_interpolation"
                ),
                "clc_lower_year": lower_year,
                "clc_upper_year": upper_year,
                "clc_interpolation_weight": f"{weight:.10g}",
            }
            for buffer_m in BUFFER_METERS:
                values_lower = snapshots[(station_id, buffer_m)][lower_year]
                values_upper = snapshots[(station_id, buffer_m)][upper_year]
                for metric in ALL_METRICS:
                    value = values_lower[metric] + weight * (
                        values_upper[metric] - values_lower[metric]
                    )
                    record[f"clc_{metric}_{buffer_m}m"] = f"{value:.10g}"
            records.append(record)
    return records


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    if not records:
        raise ValueError("CORINE preprocessing produced no records")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"CORINE raw data not found: {args.input}")

    snapshots = read_snapshots(args.input)
    records = interpolate(snapshots)
    write_csv(args.output, records)
    print(f"Wrote {len(records)} annual station-year rows")
    print(f"Years: {SNAPSHOT_YEARS[0]}-{SNAPSHOT_YEARS[-1]}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
