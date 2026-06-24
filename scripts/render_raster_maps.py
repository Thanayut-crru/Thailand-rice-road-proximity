#!/usr/bin/env python
"""Render every VIIRS-grid sensitivity raster as a publication PNG map."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio


PATTERN = re.compile(
    r"road_rice_fraction_(major|minor)_(G1_major|G2_plus_secondary_tertiary|G3_all_11)_r([12])px\.tif$"
)

GROUP_LABELS = {
    "G1_major": "G1: Major roads + links",
    "G2_plus_secondary_tertiary": "G2: + Secondary and tertiary",
    "G3_all_11": "G3: All 11 road classes",
}


def parse_args():
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser()
    p.add_argument("--rasters", default=str(root / "outputs" / "rasters"))
    p.add_argument("--boundary", required=True)
    p.add_argument("--output", default=str(root / "outputs" / "figures" / "raster_maps"))
    p.add_argument("--dpi", type=int, default=600)
    return p.parse_args()


def read_raster(path: Path):
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
        return data, extent, src.crs


def main():
    args = parse_args()
    raster_dir = Path(args.rasters)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(raster_dir.glob("*.tif")):
        match = PATTERN.match(path.name)
        if match:
            rice, group, radius = match.groups()
            records.append((path, rice, group, int(radius)))
    if len(records) != 12:
        raise RuntimeError(f"Expected 12 rasters, found {len(records)}")

    boundaries = gpd.read_file(args.boundary)
    cache = {}
    # One common scale per rice type and radius allows fair G1/G2/G3 comparison.
    scales = {}
    for path, rice, group, radius in records:
        data, extent, crs = read_raster(path)
        cache[path] = (data, extent, crs)
        positive = data[np.isfinite(data) & (data > 0)]
        scales.setdefault((rice, radius), []).append(positive)
    for key, arrays in scales.items():
        values = np.concatenate(arrays)
        scales[key] = float(np.percentile(values, 99)) if len(values) else 1.0

    for path, rice, group, radius in records:
        data, extent, crs = cache[path]
        boundary = boundaries.to_crs(crs)
        masked = np.ma.masked_where(~np.isfinite(data) | (data <= 0), data)
        fig, ax = plt.subplots(figsize=(6.2, 8.2), facecolor="white")
        image = ax.imshow(masked, extent=extent, origin="upper", cmap="OrRd",
                          vmin=0, vmax=scales[(rice, radius)], interpolation="nearest")
        boundary.boundary.plot(ax=ax, color="#303030", linewidth=0.35)
        rice_label = "Major rice" if rice == "major" else "Minor rice"
        effective = 30 if radius == 1 else 60
        ax.set_title(
            f"Rice–Road Proximity Fraction — {rice_label}\n"
            f"{GROUP_LABELS[group]} | radius {radius} px (~{effective} m)",
            fontsize=11, fontweight="bold", pad=10,
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
        cbar.set_label("Road–rice fraction within VIIRS pixel")
        fig.text(0.5, 0.025,
                 "Road proximity is a spatial proxy; it is not measured artificial light at night.",
                 ha="center", fontsize=7.5, color="#9E4242", style="italic")
        fig.savefig(output / f"{path.stem}.png", dpi=args.dpi,
                    bbox_inches="tight", pad_inches=0.20, facecolor="white")
        plt.close(fig)
        print(f"Rendered {path.stem}.png")


if __name__ == "__main__":
    main()
