#!/usr/bin/env python3
"""Download current BKG Landkreis boundaries required for the spatial join."""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

import certifi


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = (
    ROOT
    / "data"
    / "administrative_boundaries"
    / "raw"
    / "vg250_krs_ni.geojson"
)
WFS_URL = "https://sgx.geodatenzentrum.de/wfs_vg250"
PARAMETERS = {
    "SERVICE": "WFS",
    "VERSION": "2.0.0",
    "REQUEST": "GetFeature",
    "TYPENAMES": "vg250:vg250_krs",
    "OUTPUTFORMAT": "application/json",
    "SRSNAME": "EPSG:4326",
    "CQL_FILTER": "sn_l='03'",
}


def download(output: Path, overwrite: bool) -> str:
    if output.exists() and not overwrite:
        return "exists"

    output.parent.mkdir(parents=True, exist_ok=True)
    output_part = output.with_suffix(".geojson.part")
    request = urllib.request.Request(
        f"{WFS_URL}?{urllib.parse.urlencode(PARAMETERS)}",
        headers={"User-Agent": "aee-organicfarming-data-pipeline/0.1"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(
            request,
            timeout=120,
            context=context,
        ) as response:
            with output_part.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)

        data = json.loads(output_part.read_text(encoding="utf-8"))
        features = data.get("features", [])
        district_codes = {
            feature.get("properties", {}).get("ags")
            for feature in features
        }
        if len(features) < 45 or len(district_codes - {None}) != 45:
            raise ValueError(
                "Expected 45 Niedersachsen districts in the BKG boundary data"
            )
        output_part.replace(output)
    finally:
        output_part.unlink(missing_ok=True)

    return "downloaded"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    status = download(args.output, overwrite=args.overwrite)
    print(f"BKG Landkreis boundaries: {status}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
