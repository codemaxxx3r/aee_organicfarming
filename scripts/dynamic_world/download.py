#!/usr/bin/env python3
"""Download Dynamic World station-year-buffer statistics from Earth Engine."""

from __future__ import annotations

import argparse
import csv
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

import certifi


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STATIONS = (
    ROOT
    / "data"
    / "uba_nitrate_report_2024"
    / "processed"
    / "uba_nitrate_station_year_ni.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "dynamic_world"
    / "raw"
    / "dynamic_world_station_year_buffer_ni.csv"
)
DYNAMIC_WORLD_ASSET = "GOOGLE/DYNAMICWORLD/V1"
CLASS_NAMES = (
    "water",
    "trees",
    "grass",
    "flooded_vegetation",
    "crops",
    "shrub_and_scrub",
    "built",
    "bare",
    "snow_and_ice",
)
BUFFER_METERS = (500, 1000)
START_YEAR = 2016
END_YEAR = 2022


def read_stations(path: Path) -> list[dict[str, object]]:
    stations: dict[str, dict[str, object]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            station_id = row["station_id"]
            stations[station_id] = {
                "station_id": station_id,
                "longitude": float(row["lon_etrs89"]),
                "latitude": float(row["lat_etrs89"]),
            }
    if not stations:
        raise ValueError("No stations found in the processed UBA table")
    return list(stations.values())


def build_feature_collection(
    ee: object,
    stations: list[dict[str, object]],
    year: int,
    buffer_m: int,
) -> object:
    station_features = [
        ee.Feature(
            ee.Geometry.Point([station["longitude"], station["latitude"]]),
            {"station_id": station["station_id"]},
        )
        for station in stations
    ]
    station_collection = ee.FeatureCollection(station_features)
    study_area = station_collection.geometry().bounds().buffer(max(BUFFER_METERS))
    collection = ee.ImageCollection(DYNAMIC_WORLD_ASSET).filterBounds(study_area)
    annual_probabilities = (
        collection
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .select(list(CLASS_NAMES))
        .mean()
    )
    annual_label = (
        annual_probabilities
        .toArray()
        .arrayArgmax()
        .arrayGet([0])
    )
    class_shares = ee.Image.cat(
        [
            annual_label.eq(index).rename(f"{class_name}_share")
            for index, class_name in enumerate(CLASS_NAMES)
        ]
    )
    valid_data = (
        annual_probabilities
        .select(CLASS_NAMES[0])
        .mask()
        .unmask(0)
        .rename("valid_data_share")
    )
    annual_land_cover = class_shares.addBands(valid_data)

    def buffer_station(feature: object) -> object:
        return ee.Feature(
            feature.geometry().buffer(buffer_m),
            {
                "station_id": feature.get("station_id"),
                "year": year,
                "buffer_m": buffer_m,
            },
        )

    buffers = station_collection.map(buffer_station)
    return annual_land_cover.reduceRegions(
        collection=buffers,
        reducer=ee.Reducer.mean(),
        scale=10,
        tileScale=4,
    )


def download(
    stations_path: Path,
    output: Path,
    overwrite: bool,
    ee_project: str | None,
) -> str:
    if output.exists() and not overwrite:
        return "exists"
    if not stations_path.exists():
        raise FileNotFoundError(
            f"Run UBA preprocessing before Dynamic World: {stations_path}"
        )

    try:
        import ee
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Install Earth Engine with: python3 -m pip install -r requirements.txt"
        ) from exc

    try:
        ee.Initialize(project=ee_project)
    except Exception as exc:
        raise RuntimeError(
            "Run 'earthengine authenticate' and pass --ee-project."
        ) from exc

    stations = read_stations(stations_path)
    selectors = ["station_id", "year", "buffer_m"]
    selectors.extend(f"{name}_share" for name in CLASS_NAMES)
    selectors.append("valid_data_share")

    output.parent.mkdir(parents=True, exist_ok=True)
    output_part = output.with_suffix(".csv.part")
    chunk_part = output.with_suffix(".chunk.csv.part")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        rows = []
        for year in range(START_YEAR, END_YEAR + 1):
            for buffer_m in BUFFER_METERS:
                print(f"Requesting {year}, {buffer_m} m buffer...", flush=True)
                features = build_feature_collection(
                    ee,
                    stations,
                    year,
                    buffer_m,
                )
                try:
                    url = features.getDownloadURL(
                        filetype="CSV",
                        selectors=selectors,
                        filename=f"{output.stem}_{year}_{buffer_m}m",
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"Earth Engine request failed for {year}, "
                        f"{buffer_m} m: {exc}"
                    ) from exc

                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "aee-organicfarming-data-pipeline/0.1"
                    },
                )
                with urllib.request.urlopen(
                    request,
                    timeout=300,
                    context=ssl_context,
                ) as response:
                    with chunk_part.open("wb") as handle:
                        while chunk := response.read(1024 * 1024):
                            handle.write(chunk)

                with chunk_part.open(encoding="utf-8", newline="") as handle:
                    chunk_rows = list(csv.DictReader(handle))
                if len(chunk_rows) != len(stations):
                    raise ValueError(
                        f"Dynamic World returned {len(chunk_rows)} rows for "
                        f"{year}, {buffer_m} m; expected {len(stations)}"
                    )
                missing = sorted(set(selectors) - set(chunk_rows[0]))
                if missing:
                    raise ValueError(
                        f"Dynamic World output is missing columns: {missing}"
                    )
                rows.extend(chunk_rows)

        expected_rows = (
            len(stations)
            * len(BUFFER_METERS)
            * (END_YEAR - START_YEAR + 1)
        )
        if len(rows) != expected_rows:
            raise ValueError(
                f"Dynamic World returned {len(rows)} rows; expected {expected_rows}"
            )

        with output_part.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=selectors)
            writer.writeheader()
            writer.writerows(rows)
        output_part.replace(output)
    finally:
        output_part.unlink(missing_ok=True)
        chunk_part.unlink(missing_ok=True)

    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations", type=Path, default=DEFAULT_STATIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--ee-project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        help="Google Cloud project registered for Earth Engine.",
    )
    args = parser.parse_args()

    try:
        status = download(
            args.stations,
            args.output,
            overwrite=args.overwrite,
            ee_project=args.ee_project,
        )
    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
        urllib.error.URLError,
        TimeoutError,
    ) as exc:
        print(f"Dynamic World download failed: {exc}", file=sys.stderr)
        return 1

    print(f"Dynamic World raw extraction: {status}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
