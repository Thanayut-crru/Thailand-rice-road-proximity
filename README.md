# Thailand rice-road proximity: road-class sensitivity

This reproducibility repository contains code, derived outputs, figures, and
method documentation for a sensitivity analysis of 2023 Thai rice area near
mapped roads. It does not contain or distribute the unpublished manuscript.

## Analysis scope

Eleven OpenStreetMap/Geofabrik road classes are evaluated as three cumulative
networks:

1. G1: motorway, trunk, primary, and corresponding link classes.
2. G2: G1 plus secondary, secondary_link, and tertiary.
3. G3: G2 plus residential and unclassified roads.

Every group is rasterized and dilated consistently at one and two pixels,
reported as approximately 30 and 60 m. Results measure road proximity only;
they do not establish artificial-light exposure or crop damage.

## Reproduce the analysis

1. Install Python 3.11.
2. Run `python -m pip install -r requirements.txt`.
3. Arrange external inputs as described in `data/README.md`.
4. Set `RICE_PROJECT_DATA` if the input root differs from the runner default.
5. In PowerShell, run `./run_analysis.ps1`.

Large intermediate rasters are written to `_work/` and excluded from Git.
The workflow writes CSV tables, GeoTIFF rasters, 600-DPI figures, and run
metadata to `outputs/`. To keep the repository lightweight, the 12 generated
GeoTIFFs are not committed; regenerate them with `run_analysis.ps1`. The 12
full-resolution PNG maps remain in the repository for visual review. Published
area fields are calculated in acres using
`1 km² = 247.105381467 acres`; they are not relabelled values.

## Legacy-buffer audit

The analysis does not reuse legacy buffers. A separate full-grid audit proves
that the stored legacy pair has an exact one-/two-pixel dilation relationship.
The audit tested 1,696,041,025 pixels and found zero mismatches. See
`outputs/legacy_buffer_verification.json`.

Reproduce the audit without loading the road extract:

```powershell
python scripts/verify_legacy_buffer_dilation.py `
  --buffer-1px "path/to/road_buffer_30m_30m.tif" `
  --buffer-2px "path/to/road_buffer_50m_30m.tif"
```

## Repository contents

- `scripts/`: analysis, audit, and figure-generation code.
- `tests/`: automated output-contract tests.
- `outputs/tables/`: national and regional results in calculated acres.
- `outputs/rasters/`: generated 12 road-rice fraction GeoTIFFs (not committed).
- `outputs/figures/`: summary figures and 12 committed full-resolution maps.
- `docs/`: methodology and quality-control documentation.
- `data/README.md`: external input inventory; raw data are not redistributed.
- `RESULTS.md`: concise results and interpretation boundaries.

The rice maps represent 2023, while the OSM snapshot was downloaded on
10 June 2026. This temporal mismatch must be retained when interpreting or
reusing the results.
