# Road-class sensitivity methodology

## Question

How much do national and regional rice-road proximity estimates change when
local road classes are added to the road network?

## Cumulative scenarios

1. **G1 major:** motorway, trunk, primary and their link classes.
2. **G2 expanded:** G1 plus secondary, secondary_link and tertiary.
3. **G3 all 11:** G2 plus residential and unclassified.

The scenarios are cumulative. Differences G2−G1 and G3−G2 measure the
incremental area introduced by the added road classes after accounting for
overlapping buffers.

## Spatial calculation

For every group, road centrelines are rasterized independently with
`all_touched=True` on the same native GCD-Rice EPSG:4326 grid (nominal 30 m).
Circular binary dilation uses radii of 1 and 2 pixels, reported as approximately
30 and 60 m. Because the grid is geographic, both values are nominal rather
than exact metric buffers. Legacy buffer rasters are not reused in the analysis.

An independent raster audit nevertheless resolves the legacy distance label.
On the integer grid, `disk(2) = disk(1) ⊕ disk(1)`. Across the complete
55,111 × 30,775 grid, the stored nominal 50-m raster was exactly equal to
`binary_dilation(stored nominal 30-m raster, disk(1))`: all 1,696,041,025 pixels
matched (`extra = 0`, `missing = 0`). Thus, the stored legacy pair encodes the
same one-/two-pixel dilation relationship. Its “50 m” label denotes the
two-pixel setting (~60 m on the nominal 30-m grid), not a verified exact 50-m
metric radius. The executable audit and machine-readable result are provided in
`scripts/verify_legacy_buffer_dilation.py` and
`outputs/legacy_buffer_verification.json`.

For every scenario and rice season:

`road_rice_30m = (rice == 1) AND (road_buffer == 1)`

The binary raster is aggregated to the VIIRS reference grid using average
resampling. Latitude-adjusted target-cell area is calculated from the geographic
grid and converted to acres using `1 km² = 247.105381467 acres`. All published
area tables use the calculated acre values.

## Interpretation boundary

The result measures proximity to mapped roads. It does not establish that a
road is illuminated or that rice experienced artificial light at night. The
August 2023 SVDNB file supplies only the common ~500 m grid in this analysis.

## Temporal limitation

The rice maps represent 2023, while the OSM snapshot was downloaded on
2026-06-10. Results can include roads added or remapped after 2023 and therefore
must be described as a sensitivity analysis using a 2026 road snapshot.
