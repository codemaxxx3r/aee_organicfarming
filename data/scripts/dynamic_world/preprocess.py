#!/usr/bin/env python3
"""Pivot raw Dynamic World buffer statistics to a station-year table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = (
    ROOT
    / "data"
    / "dynamic_world"
    / "raw"
    / "dynamic_world_station_year_buffer_ni.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "dynamic_world"
    / "processed"
    / "dynamic_world_station_year_ni.csv"
)
METRICS = (
    "water_share",
    "trees_share",
    "grass_share",
    "flooded_vegetation_share",
    "crops_share",
    "shrub_and_scrub_share",
    "built_share",
    "bare_share",
    "snow_and_ice_share",
    "valid_data_share",
)
BUFFER_METERS = (500, 1000)


def preprocess(path: Path) -> list[dict[str, object]]:
    records: dict[tuple[str, int], dict[str, object]] = {}
    seen: set[tuple[str, int, int]] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"station_id", "year", "buffer_m", *METRICS}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Dynamic World raw data is missing columns: {missing}")

        for row in reader:
            station_id = row["station_id"]
            year = int(float(row["year"]))
            buffer_m = int(float(row["buffer_m"]))
            if buffer_m not in BUFFER_METERS:
                raise ValueError(f"Unexpected buffer size: {buffer_m}")
            source_key = (station_id, year, buffer_m)
            if source_key in seen:
                raise ValueError(f"Duplicate Dynamic World key: {source_key}")
            seen.add(source_key)

            target = records.setdefault(
                (station_id, year),
                {"station_id": station_id, "year": year},
            )
            for metric in METRICS:
                target[f"dw_{metric}_{buffer_m}m"] = row[metric]

    columns = [
        f"dw_{metric}_{buffer_m}m"
        for buffer_m in BUFFER_METERS
        for metric in METRICS
    ]
    output = []
    for key in sorted(records):
        record = records[key]
        missing_values = [column for column in columns if column not in record]
        if missing_values:
            raise ValueError(
                f"Incomplete Dynamic World buffers for {key}: {missing_values}"
            )
        output.append(
            {
                "station_id": record["station_id"],
                "year": record["year"],
                **{column: record[column] for column in columns},
            }
        )
    return output


def write_csv(path: Path, records: list[dict[str, object]]) -> None:
    if not records:
        raise ValueError("Dynamic World preprocessing produced no records")
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
        raise FileNotFoundError(f"Dynamic World raw data not found: {args.input}")

    records = preprocess(args.input)
    write_csv(args.output, records)
    print(f"Wrote {len(records)} station-year rows")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
