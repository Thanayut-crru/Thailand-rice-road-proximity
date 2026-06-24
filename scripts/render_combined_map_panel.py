#!/usr/bin/env python
"""Render the six manuscript map panels as one figure with one shared scale."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[1]

PANELS = [
    ("major", "G1_major", 1, "Major rice\nG1 major roads | 1 px (~30 m)"),
    ("major", "G3_all_11", 1, "Major rice\nG3 all classes | 1 px (~30 m)"),
    ("minor", "G1_major", 1, "Minor rice\nG1 major roads | 1 px (~30 m)"),
    ("minor", "G3_all_11", 1, "Minor rice\nG3 all classes | 1 px (~30 m)"),
    ("major", "G3_all_11", 2, "Major rice\nG3 all classes | 2 px (~60 m)"),
    ("minor", "G3_all_11", 2, "Minor rice\nG3 all classes | 2 px (~60 m)"),
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--rasters", default=str(ROOT / "outputs" / "rasters"))
    p.add_argument("--boundary", required=True)
    p.add_argument("--output", default=str(ROOT / "outputs" / "figures" / "combined_map_panel.png"))
    p.add_argument("--svg-output", default=str(ROOT / "outputs" / "figures" / "combined_map_panel.svg"))
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument(
        "--vmax-percentile",
        type=float,
        default=99.0,
        help="Common upper color limit estimated from positive values across all panels.",
    )
    return p.parse_args()


def raster_path(raster_dir: Path, rice: str, group: str, radius: int) -> Path:
    return raster_dir / f"road_rice_fraction_{rice}_{group}_r{radius}px.tif"


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
    records = []
    positives = []
    for rice, group, radius, title in PANELS:
        path = raster_path(raster_dir, rice, group, radius)
        if not path.exists():
            raise FileNotFoundError(path)
        data, extent, crs = read_raster(path)
        records.append((data, extent, crs, title))
        valid = data[np.isfinite(data) & (data > 0)]
        if valid.size:
            positives.append(valid)

    if not positives:
        raise RuntimeError("No positive raster values found")
    vmax = float(np.percentile(np.concatenate(positives), args.vmax_percentile))
    if vmax <= 0:
        vmax = 1.0

    boundary = gpd.read_file(args.boundary).to_crs(records[0][2])

    fig, axes = plt.subplots(2, 3, figsize=(14.2, 8.6), facecolor="white", sharex=True, sharey=True)
    axes = axes.ravel()
    image = None
    for idx, (ax, (data, extent, crs, title)) in enumerate(zip(axes, records), start=1):
        masked = np.ma.masked_where(~np.isfinite(data) | (data <= 0), data)
        image = ax.imshow(masked, extent=extent, origin="upper", cmap="OrRd",
                          vmin=0, vmax=vmax, interpolation="nearest")
        boundary.boundary.plot(ax=ax, color="#303030", linewidth=0.28)
        ax.set_title(f"({chr(64 + idx)}) {title}", fontsize=9.8, fontweight="bold", pad=7)
        row = (idx - 1) // 3
        col = (idx - 1) % 3
        ax.set_xlabel("Longitude" if row == 1 else "", fontsize=8)
        ax.set_ylabel("Latitude" if col == 0 else "", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal")

    fig.subplots_adjust(left=0.055, right=0.905, top=0.875, bottom=0.08, wspace=0.02, hspace=0.24)
    cbar = fig.colorbar(image, ax=axes, fraction=0.026, pad=0.012)
    cbar.set_label(
        f"Road-rice fraction within VIIRS pixel\nshared scale, 0 to P{args.vmax_percentile:g} = {vmax:.3f}",
        fontsize=9,
    )
    cbar.ax.tick_params(labelsize=8)
    fig.suptitle("Rice-road proximity fraction maps with a common color scale",
                 fontsize=14, fontweight="bold", y=0.965)
    output = Path(args.output)
    svg_output = Path(args.svg_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=args.dpi, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    fig.savefig(svg_output, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    print(f"Created {output}")
    print(f"Created {svg_output}")


if __name__ == "__main__":
    main()
