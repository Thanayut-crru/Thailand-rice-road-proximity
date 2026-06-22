#!/usr/bin/env python
"""Verify whether a legacy two-pixel buffer is dilation of its one-pixel buffer.

The comparison is streamed in tiles, so it does not require loading either
national raster or the source road layer into memory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import binary_dilation


def parse_args():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--buffer-1px", required=True)
    parser.add_argument("--buffer-2px", required=True)
    parser.add_argument("--tile-size", type=int, default=2048)
    parser.add_argument(
        "--output",
        default=str(root / "outputs" / "legacy_buffer_verification.json"),
    )
    return parser.parse_args()


def windows(height: int, width: int, size: int):
    for row in range(0, height, size):
        for col in range(0, width, size):
            yield Window(col, row, min(size, width - col), min(size, height - row))


def halo(core: Window, height: int, width: int) -> Window:
    col0 = max(0, int(core.col_off) - 1)
    row0 = max(0, int(core.row_off) - 1)
    col1 = min(width, int(core.col_off + core.width) + 1)
    row1 = min(height, int(core.row_off + core.height) + 1)
    return Window(col0, row0, col1 - col0, row1 - row0)


def main():
    args = parse_args()
    one_path = Path(args.buffer_1px)
    two_path = Path(args.buffer_2px)
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)

    mismatch = extra = missing = one_count = two_count = 0
    tile_count = 0
    with rasterio.open(one_path) as one, rasterio.open(two_path) as two:
        if one.shape != two.shape or one.transform != two.transform or one.crs != two.crs:
            raise ValueError("The two legacy rasters do not share one grid")

        for core in windows(one.height, one.width, args.tile_size):
            expanded = halo(core, one.height, one.width)
            b1 = one.read(1, window=expanded) == 1
            observed = two.read(1, window=core) == 1
            expected_halo = binary_dilation(b1, structure=structure)
            row0 = int(core.row_off - expanded.row_off)
            col0 = int(core.col_off - expanded.col_off)
            expected = expected_halo[
                row0:row0 + int(core.height), col0:col0 + int(core.width)
            ]

            delta = expected != observed
            mismatch += int(delta.sum())
            extra += int((observed & ~expected).sum())
            missing += int((expected & ~observed).sum())
            one_count += int(one.read(1, window=core).astype(bool).sum())
            two_count += int(observed.sum())
            tile_count += 1

        result = {
            "test": "B2 == binary_dilation(B1, disk(1))",
            "mathematical_identity": "disk(2) on Z^2 == disk(1) Minkowski-sum disk(1)",
            "buffer_1px": one_path.name,
            "buffer_2px": two_path.name,
            "shape_rows_cols": [one.height, one.width],
            "pixel_count": one.height * one.width,
            "tile_size": args.tile_size,
            "tile_count": tile_count,
            "crs": str(one.crs),
            "pixel_size_degrees": [abs(one.transform.a), abs(one.transform.e)],
            "mismatch_pixels": mismatch,
            "extra_pixels": extra,
            "missing_pixels": missing,
            "buffer_1px_positive_pixels": one_count,
            "buffer_2px_positive_pixels": two_count,
            "positive_pixel_ratio_b2_over_b1": two_count / one_count,
            "exact_match": mismatch == 0,
            "interpretation": (
                "The stored legacy B2 raster is exactly the one-pixel binary dilation "
                "of stored B1 on the shared EPSG:4326 grid. Its legacy 50 m label "
                "therefore corresponds to the two-pixel setting (approximately 60 m), "
                "not an independently verified exact metric radius."
            ),
        }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if mismatch:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
