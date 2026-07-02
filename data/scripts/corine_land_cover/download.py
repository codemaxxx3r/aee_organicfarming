#!/usr/bin/env python3
"""Download CORINE station-buffer land-cover shares from Earth Engine."""

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
    / "corine_land_cover"
    / "raw"
    / "corine_station_year_buffer_ni.csv"
)
ASSET_PREFIX = "COPERNICUS/CORINE/V20/100m"
SNAPSHOT_YEARS = (2006, 2012, 2018)
BUFFER_METERS = (500, 1000)
CATEGORY_CODES = {
    "urban_fabric": (111, 112),
    "industrial_commercial_transport": (121, 122, 123, 124),
    "mine_dump_construction": (131, 132, 133),
    "artificial_green": (141, 142),
    "arable_land": (211, 212, 213),
    "permanent_crops": (221, 222, 223),
    "pastures": (231,),
    "heterogeneous_agriculture": (241, 242, 243, 244),
    "forest": (311, 312, 313),
    "shrub_herbaceous": (321, 322, 323, 324),
    "open_spaces": (331, 332, 333, 334, 335),
    "wetlands": (411, 412, 421, 422, 423),
    "water": (511, 512, 521, 522, 523),
}


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
    station_collection = ee.FeatureCollection(
        [
            ee.Feature(
                ee.Geometry.Point([station["longitude"], station["latitude"]]),
                {"station_id": station["station_id"]},
            )
            for station in stations
        ]
    )
    landcover = ee.Image(f"{ASSET_PREFIX}/{year}").select("landcover")
    category_images = []
    for category, codes in CATEGORY_CODES.items():
        category_images.append(
            landcover
            .remap(list(codes), [1] * len(codes), 0)
            .rename(f"{category}_share")
        )
    valid_data = landcover.mask().unmask(0).rename("valid_data_share")
    category_image = ee.Image.cat(category_images).addBands(valid_data)

    def buffer_station(feature: object) -> object:
        return ee.Feature(
            feature.geometry().buffer(buffer_m),
            {
                "station_id": feature.get("station_id"),
                "year": year,
                "buffer_m": buffer_m,
            },
        )

    return category_image.reduceRegions(
        collection=station_collection.map(buffer_station),
        reducer=ee.Reducer.mean(),
        scale=100,
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
            f"Run UBA preprocessing before CORINE: {stations_path}"
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
    selectors.extend(f"{name}_share" for name in CATEGORY_CODES)
    selectors.append("valid_data_share")

    output.parent.mkdir(parents=True, exist_ok=True)
    output_part = output.with_suffix(".csv.part")
    chunk_part = output.with_suffix(".chunk.csv.part")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        rows = []
        for year in SNAPSHOT_YEARS:
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
                        f"CORINE returned {len(chunk_rows)} rows for "
                        f"{year}, {buffer_m} m; expected {len(stations)}"
                    )
                missing = sorted(set(selectors) - set(chunk_rows[0]))
                if missing:
                    raise ValueError(f"CORINE output is missing columns: {missing}")
                rows.extend(chunk_rows)

        expected_rows = (
            len(stations) * len(BUFFER_METERS) * len(SNAPSHOT_YEARS)
        )
        if len(rows) != expected_rows:
            raise ValueError(
                f"CORINE returned {len(rows)} rows; expected {expected_rows}"
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
        print(f"CORINE download failed: {exc}", file=sys.stderr)
        return 1

    print(f"CORINE raw extraction: {status}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
