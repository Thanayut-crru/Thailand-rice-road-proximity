# Quality control

- All 12 final fraction rasters have CRS EPSG:4326 and shape 3,588 × 2,014.
- Every raster value is within [0, 1].
- Estimates increase monotonically from G1 to G2 to G3 for both rice seasons
  and both radii.
- Run metadata records `used_existing_all_buffers: false` and
  `all_groups_rebuilt_consistently: true`.
- G1, G2 and G3 are all rebuilt from road centrelines with the same
  `all_touched=True` rasterization and circular 1-/2-pixel dilation.
- The optional archived project-buffer audit tested 1,696,041,025 pixels in
  432 tiles and found `mismatch = 0`, `extra = 0`, and `missing = 0` for
  `B2 == binary_dilation(B1, disk(1))`. The archived rasters are used only to
  document workflow consistency, not as a prior publication or external
  validation dataset.
- National totals are calculated across the complete Thailand-window raster.
  Regional sums can differ slightly because polygon rasterization excludes
  boundary-edge cells; this limitation is retained from the original workflow.
