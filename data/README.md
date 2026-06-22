# Data inputs

Raw inputs are intentionally not committed because the national rasters and OSM
extract exceed normal GitHub limits. Set `RICE_PROJECT_DATA` to the project data
root, or edit `run_analysis.ps1`.

Expected inputs:

- `raw/paddy/Classified-Rice-THA-Major-2023-v1.tif`
- `raw/paddy/Classified-Rice-THA-Minor-2023-v1.tif`
- `raw/2023/SVDNB_npp_202308.tif` (target grid only)
- `raw/boundaries/thailand_provinces_with_regions_5.geojson`
- `processed2/roads/thailand-latest-free.shp.zip`

The analysis uses a Geofabrik/OSM snapshot downloaded on 2026-06-10 with 2023
rice maps. This temporal mismatch must be disclosed when interpreting results.

Legacy buffer rasters from `processed2` are not inputs to the sensitivity
analysis. They are optional inputs only for the independent full-grid audit in
`scripts/verify_legacy_buffer_dilation.py`:

- `processed2/roads/road_buffer_30m_30m.tif`
- `processed2/roads/road_buffer_50m_30m.tif`

The audit proves that the stored second raster is exactly one additional
one-pixel dilation of the first. It does not require the 679-MB road extract.
