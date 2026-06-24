#!/usr/bin/env python
"""Road-class sensitivity analysis for Thailand rice-road proximity.

The workflow reproduces the original raster-space method while separating the
11 OSM/Geofabrik fclass values into three cumulative road-network scenarios.
It deliberately calls the result a road-proximity proxy, not observed light.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from rasterio.warp import Resampling, reproject
from scipy.ndimage import binary_dilation
from shapely.geometry import box


GROUPS = {
    "G1_major": [
        "motorway", "trunk", "primary",
        "motorway_link", "trunk_link", "primary_link",
    ],
    "G2_plus_secondary_tertiary": [
        "motorway", "trunk", "primary", "secondary", "tertiary",
        "motorway_link", "trunk_link", "primary_link", "secondary_link",
    ],
    "G3_all_11": [
        "motorway", "trunk", "primary", "secondary", "tertiary",
        "motorway_link", "trunk_link", "primary_link", "secondary_link",
        "residential", "unclassified",
    ],
}

GROUP_LABELS = {
    "G1_major": "Major roads + links",
    "G2_plus_secondary_tertiary": "+ Secondary and tertiary",
    "G3_all_11": "+ Residential and unclassified (all 11)",
}

RADIUS_INFO = {
    1: {"requested_buffer_m": 30, "effective_radius_m": 30},
    2: {"requested_buffer_m": 60, "effective_radius_m": 60},
}

KM2_TO_ACRE = 247.105381467


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--roads", required=True, help="Geofabrik roads shapefile/ZIP or filtered GeoJSON")
    p.add_argument("--rice-major", required=True)
    p.add_argument("--rice-minor", required=True)
    p.add_argument("--viirs-ref", required=True, help="VIIRS raster used only as the target grid")
    p.add_argument("--boundary", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--work", required=True, help="Large temporary rasters; do not commit")
    p.add_argument("--osm-snapshot", default="2026-06-10")
    p.add_argument("--tile-size", type=int, default=2048)
    return p.parse_args()


def sql_in(values: list[str]) -> str:
    return "fclass IN (" + ",".join(f"'{x}'" for x in values) + ")"


def get_viirs_grid(viirs_ref: Path, boundary: Path):
    bounds = gpd.read_file(boundary).total_bounds
    minx, miny, maxx, maxy = bounds
    with rasterio.open(viirs_ref) as ref:
        win = from_bounds(minx - 0.05, miny - 0.05, maxx + 0.05, maxy + 0.05, ref.transform)
        win = win.round_offsets().round_lengths()
        return ref.window_transform(win), (int(win.height), int(win.width)), ref.crs


def pixel_area_km2(transform, shape):
    rows = np.arange(shape[0])
    lats = transform.f + (rows + 0.5) * transform.e
    height_km = abs(transform.e) * 110.574
    width_km = abs(transform.a) * 111.320 * np.cos(np.radians(lats))
    return (height_km * width_km)[:, None] * np.ones(shape[1], dtype=np.float32)


def iter_windows(height: int, width: int, tile_size: int):
    for row in range(0, height, tile_size):
        for col in range(0, width, tile_size):
            yield Window(col, row, min(tile_size, width - col), min(tile_size, height - row))


def expanded_window(win: Window, radius: int, height: int, width: int) -> Window:
    c0 = max(0, int(win.col_off) - radius)
    r0 = max(0, int(win.row_off) - radius)
    c1 = min(width, int(win.col_off + win.width) + radius)
    r1 = min(height, int(win.row_off + win.height) + radius)
    return Window(c0, r0, c1 - c0, r1 - r0)


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return (x * x + y * y <= radius * radius)


def load_roads(roads_path: str, classes: list[str]) -> gpd.GeoDataFrame:
    print(f"Loading {len(classes)} road classes...")
    roads = pyogrio.read_dataframe(roads_path, columns=["fclass"], where=sql_in(classes))
    roads = roads[roads.geometry.notna()].reset_index(drop=True)
    if roads.crs is None:
        roads = roads.set_crs("EPSG:4326")
    elif roads.crs.to_epsg() != 4326:
        roads = roads.to_crs(4326)
    print(f"  loaded {len(roads):,} segments")
    return roads


def write_group_buffers(roads: gpd.GeoDataFrame, rice_path: Path, group: str,
                        work: Path, tile_size: int) -> dict[int, Path]:
    paths = {r: work / f"buffer_{group}_r{r}px.tif" for r in RADIUS_INFO}
    with rasterio.open(rice_path) as rice:
        profile = rice.profile.copy()
        profile.update(dtype="uint8", count=1, nodata=None, compress="deflate",
                       predictor=2, tiled=True, blockxsize=512, blockysize=512)
        writers = {r: rasterio.open(path, "w", **profile) for r, path in paths.items()}
        sindex = roads.sindex
        structures = {r: disk(r) for r in RADIUS_INFO}
        windows = list(iter_windows(rice.height, rice.width, tile_size))
        try:
            for n, core in enumerate(windows, start=1):
                halo = expanded_window(core, max(RADIUS_INFO), rice.height, rice.width)
                bounds = rasterio.windows.bounds(halo, rice.transform)
                ids = sindex.query(box(*bounds), predicate="intersects")
                if len(ids):
                    geoms = roads.geometry.iloc[ids]
                    line = rasterize(
                        ((geom, 1) for geom in geoms),
                        out_shape=(int(halo.height), int(halo.width)),
                        transform=rasterio.windows.transform(halo, rice.transform),
                        fill=0, dtype="uint8", all_touched=True,
                    )
                else:
                    line = np.zeros((int(halo.height), int(halo.width)), dtype=np.uint8)

                r0 = int(core.row_off - halo.row_off)
                c0 = int(core.col_off - halo.col_off)
                r1 = r0 + int(core.height)
                c1 = c0 + int(core.width)
                for radius, writer in writers.items():
                    dilated = binary_dilation(line.astype(bool), structure=structures[radius])
                    writer.write(dilated[r0:r1, c0:c1].astype("uint8"), 1, window=core)
                if n % 50 == 0 or n == len(windows):
                    print(f"  {group}: {n}/{len(windows)} tiles")
        finally:
            for writer in writers.values():
                writer.close()
    return paths


def road_rice_fraction(rice_path: Path, buffer_path: Path, temp_path: Path,
                       target_transform, target_shape, target_crs, tile_size: int):
    with rasterio.open(rice_path) as rice, rasterio.open(buffer_path) as buf:
        if rice.shape != buf.shape or rice.transform != buf.transform:
            raise ValueError("Rice and buffer grids do not match")
        profile = rice.profile.copy()
        profile.update(dtype="uint8", count=1, nodata=None, compress="deflate",
                       predictor=2, tiled=True, blockxsize=512, blockysize=512)
        with rasterio.open(temp_path, "w", **profile) as out:
            for win in iter_windows(rice.height, rice.width, tile_size):
                r = rice.read(1, window=win)
                b = buf.read(1, window=win)
                out.write(((r == 1) & (b == 1)).astype("uint8"), 1, window=win)

    dest = np.zeros(target_shape, dtype=np.float32)
    with rasterio.open(temp_path) as src:
        reproject(
            source=rasterio.band(src, 1), destination=dest,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=target_transform, dst_crs=target_crs,
            resampling=Resampling.average, dst_nodata=0,
        )
    return np.clip(dest, 0, 1)


def rice_fraction(rice_path: Path, target_transform, target_shape, target_crs):
    dest = np.zeros(target_shape, dtype=np.float32)
    with rasterio.open(rice_path) as src:
        reproject(
            source=rasterio.band(src, 1), destination=dest,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=target_transform, dst_crs=target_crs,
            resampling=Resampling.average, dst_nodata=0,
        )
    return np.clip(dest, 0, 1)


def zonal_sums(values: np.ndarray, boundaries: gpd.GeoDataFrame, transform) -> dict[str, float]:
    out = {}
    for region in sorted(boundaries["region_5"].dropna().unique()):
        mask = rasterize(
            ((g, 1) for g in boundaries.loc[boundaries["region_5"] == region, "geometry"]),
            out_shape=values.shape, transform=transform, fill=0, dtype="uint8",
        )
        out[region] = float(values[mask == 1].sum())
    out["National"] = float(values.sum())
    return out


def write_viirs_raster(path: Path, values: np.ndarray, transform, crs):
    profile = {
        "driver": "GTiff", "height": values.shape[0], "width": values.shape[1],
        "count": 1, "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": -9999.0, "compress": "deflate", "predictor": 3,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values.astype("float32"), 1)


def plot_national(df: pd.DataFrame, output: Path):
    nat = df[df.region_5 == "National"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    colors = ["#355C7D", "#6C8EBF", "#C06C84"]
    for ax, rice_type in zip(axes, ["major", "minor"]):
        sub = nat[nat.rice_type == rice_type]
        x = np.arange(2)
        width = 0.24
        for i, group in enumerate(GROUPS):
            vals = []
            for radius in [1, 2]:
                row = sub[(sub.group == group) & (sub.radius_px == radius)].iloc[0]
                vals.append(row.exposure_proportion * 100)
            ax.bar(x + (i - 1) * width, vals, width, color=colors[i], label=GROUP_LABELS[group])
        ax.set_xticks(x, ["1 px (~30 m)", "2 px (~60 m)"])
        ax.set_title("Major rice" if rice_type == "major" else "Minor rice")
        ax.set_ylabel("Rice area near roads (%)")
        ax.grid(axis="y", alpha=0.25)
    axes[1].legend(fontsize=8, loc="upper left")
    fig.suptitle("Sensitivity of rice-road proximity to included OSM road classes")
    fig.tight_layout()
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main():
    args = parse_args()
    roads_path = args.roads
    rice_paths = {"major": Path(args.rice_major), "minor": Path(args.rice_minor)}
    output = Path(args.output)
    work = Path(args.work)
    tables = output / "tables"
    figures = output / "figures"
    rasters = output / "rasters"
    for p in [work, tables, figures, rasters]:
        p.mkdir(parents=True, exist_ok=True)

    target_transform, target_shape, target_crs = get_viirs_grid(Path(args.viirs_ref), Path(args.boundary))
    area = pixel_area_km2(target_transform, target_shape)
    boundaries = gpd.read_file(args.boundary).to_crs(target_crs)

    # Segment counts are part of the audit trail.
    attrs = pyogrio.read_dataframe(roads_path, columns=["fclass"],
                                   read_geometry=False, where=sql_in(GROUPS["G3_all_11"]))
    counts = attrs["fclass"].value_counts().rename_axis("fclass").reset_index(name="segment_count")
    counts["share_percent"] = counts.segment_count / counts.segment_count.sum() * 100
    counts.to_csv(tables / "road_class_counts.csv", index=False)
    del attrs, counts
    gc.collect()

    # Rebuild every cumulative group with the same rasterization and dilation
    # method. This keeps G1/G2/G3 comparisons apples-to-apples.
    buffer_paths: dict[str, dict[int, Path]] = {}
    roads_g2 = load_roads(roads_path, GROUPS["G2_plus_secondary_tertiary"])
    for group in ["G1_major", "G2_plus_secondary_tertiary"]:
        subset = roads_g2[roads_g2.fclass.isin(GROUPS[group])].copy()
        buffer_paths[group] = write_group_buffers(subset, rice_paths["major"], group, work, args.tile_size)
    del subset, roads_g2
    gc.collect()

    roads_g3 = load_roads(roads_path, GROUPS["G3_all_11"])
    buffer_paths["G3_all_11"] = write_group_buffers(
        roads_g3, rice_paths["major"], "G3_all_11", work, args.tile_size)
    del roads_g3
    gc.collect()

    total_area = {}
    for rice_type, rice_path in rice_paths.items():
        rf = rice_fraction(rice_path, target_transform, target_shape, target_crs)
        total_area[rice_type] = rf * area

    rows = []
    for group, radii in buffer_paths.items():
        for radius, buffer_path in radii.items():
            for rice_type, rice_path in rice_paths.items():
                tmp = work / f"road_rice_30m_{rice_type}_{group}_r{radius}px.tif"
                frac = road_rice_fraction(rice_path, buffer_path, tmp, target_transform,
                                          target_shape, target_crs, args.tile_size)
                out_raster = rasters / f"road_rice_fraction_{rice_type}_{group}_r{radius}px.tif"
                write_viirs_raster(out_raster, frac, target_transform, target_crs)
                exp_area = frac * area
                total_z = zonal_sums(total_area[rice_type], boundaries, target_transform)
                exp_z = zonal_sums(exp_area, boundaries, target_transform)
                for region in total_z:
                    total = total_z[region]
                    exposed = exp_z[region]
                    info = RADIUS_INFO[radius]
                    rows.append({
                        "region_5": region, "rice_type": rice_type,
                        "group": group, "group_label": GROUP_LABELS[group],
                        "road_classes": ";".join(GROUPS[group]),
                        "radius_px": radius,
                        "requested_buffer_m": info["requested_buffer_m"],
                        "effective_radius_m_approx": info["effective_radius_m"],
                        "total_rice_area_acres": total * KM2_TO_ACRE,
                        "road_proximity_rice_area_acres": exposed * KM2_TO_ACRE,
                        "exposure_proportion": exposed / total if total else np.nan,
                    })

    result = pd.DataFrame(rows).sort_values(["rice_type", "radius_px", "region_5", "group"])
    result.to_csv(tables / "road_type_sensitivity_by_region.csv", index=False, encoding="utf-8-sig")

    nat = result[result.region_5 == "National"].copy()
    nat["incremental_area_acres"] = nat.groupby(["rice_type", "radius_px"])[
        "road_proximity_rice_area_acres"].diff().fillna(nat.road_proximity_rice_area_acres)
    nat["incremental_percentage_points"] = nat.groupby(["rice_type", "radius_px"])[
        "exposure_proportion"].diff().fillna(nat.exposure_proportion) * 100
    nat.to_csv(tables / "road_type_sensitivity_national.csv", index=False, encoding="utf-8-sig")
    plot_national(result, figures / "road_type_sensitivity_national.png")

    metadata = {
        "rice_year": 2023,
        "osm_snapshot": args.osm_snapshot,
        "temporal_mismatch_warning": "OSM snapshot post-dates the 2023 rice maps.",
        "viirs_reference": Path(args.viirs_ref).name,
        "viirs_role": "target grid only; no radiance is used in this road-proximity analysis",
        "buffer_method": "circular binary dilation in raster space on the EPSG:4326 rice grid",
        "used_existing_all_buffers": False,
        "all_groups_rebuilt_consistently": True,
        "groups": GROUPS,
        "radius_info": RADIUS_INFO,
    }
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Completed. Results: {output}")


if __name__ == "__main__":
    main()
