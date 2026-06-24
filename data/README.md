# Data inputs

Raw inputs are intentionally not committed because the national rasters and
OSM extract exceed normal GitHub limits and remain subject to their source
licences. Set `RICE_PROJECT_DATA` to the project data root, or edit
`run_analysis.ps1`.

## 1. Rice maps

Source: **Global Crop Dataset–Rice (GCD-Rice)**, Science Data Bank.

- Dataset page: <https://www.scidb.cn/en/detail?dataSetId=68ea15cf08d7469f8c1a653f5589701a>
- Persistent DOI: <https://doi.org/10.57760/sciencedb.21665>
- Country: Thailand (`THA`)
- Year: 2023
- Working grid: EPSG:4326, nominal 30 m

Download the Thailand 2023 country files and retain these filenames:

- `raw/paddy/Classified-Rice-THA-Major-2023-v1.tif`
- `raw/paddy/Classified-Rice-THA-Minor-2023-v1.tif`

SHA-256 checksums of the files used for the archived results:

```text
4D324E97AA720E1BF059BED5B0B781D6F5EEDADE07D0E10F83830EC4773D6FA0  Classified-Rice-THA-Major-2023-v1.tif
42B35423B87682DF73A973323E85EEE96F9B3E76301BBD62EB876452E0DAE823  Classified-Rice-THA-Minor-2023-v1.tif
```

The files were retrieved from the GCD-Rice Science Data Bank record on
3 June 2026. Cite the dataset DOI rather than this repository when reusing
the rice maps.

## 2. VIIRS reference grid

- Expected path: `raw/2023/SVDNB_npp_202308.tif`
- Product: EOG VIIRS Monthly Cloud-free Day/Night Band Composite, Version 1
- Satellite/platform: Suomi NPP
- Month: August 2023
- Band used to create the local file: monthly average radiance
- CRS: EPSG:4326
- Native resolution: 15 arc-second, approximately 500 m at the Equator
- Global coverage: 180°W–180°E and 65°S–75°N
- Role in this analysis: target grid geometry only

- Product description:
  <https://eogdata.mines.edu/products/vnl/>
- EOG non-tiled monthly download page (free account/sign-in required):
  <https://eogdata.mines.edu/nighttime_light/monthly_notile/>
- Google Earth Engine catalogue and alternative access:
  <https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMCFG>
- Earth Engine collection ID:
  `NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG`

The local filename `SVDNB_npp_202308.tif` is a shortened project filename for
the August 2023 global monthly composite. Its raster dimensions
(86,401 × 33,601), 0.0041666667° cell size, and geographic extent match the
EOG non-tiled 15 arc-second global product. Users reproducing the workflow may
download the August 2023 average-radiance layer from EOG, or export the
`avg_rad` band for August 2023 from the Earth Engine collection, and save it
under the expected local filename.

No radiance threshold or artificial-light exposure calculation is performed
in this road-proximity sensitivity analysis.

## 3. Administrative boundary

- Expected path:
  `raw/boundaries/thailand_provinces_with_regions_5.geojson`
- Required attributes: province geometry and the five-region grouping used by
  the regional summaries

Document the original boundary provider, version, licence, and any region
field added locally before applying this workflow to a new copy.

## 4. Roads

- Expected path: `processed2/roads/thailand-latest-free.shp.zip`
- Source: OpenStreetMap data distributed by Geofabrik
- Download page: <https://download.geofabrik.de/asia/thailand.html>
- Snapshot used for archived results: 10 June 2026

The analysis therefore combines 2023 rice maps with a 2026 road snapshot.
This temporal mismatch must be disclosed when interpreting results.

## Optional archived-buffer audit

Pre-existing project buffer rasters are not inputs to the sensitivity
analysis. They are optional inputs only for the independent full-grid audit in
`scripts/verify_legacy_buffer_dilation.py`:

- `processed2/roads/road_buffer_30m_30m.tif`
- `processed2/roads/road_buffer_50m_30m.tif`

The audit documents that the archived second raster is exactly one additional
one-pixel dilation of the first. These rasters are not treated as a prior
publication or as an external validation dataset.
