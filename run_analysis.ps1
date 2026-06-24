$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultDataRoot = [System.Text.Encoding]::UTF8.GetString(
  [System.Convert]::FromBase64String("RDpc4Lin4Li04LiI4Lix4LiiXDI1NjnguILguYnguLLguKc="))
$DataRoot = if ($env:RICE_PROJECT_DATA) { $env:RICE_PROJECT_DATA } else { $DefaultDataRoot }
$Boundary = "$DataRoot\raw\boundaries\thailand_provinces_with_regions_5.geojson"

python "$Root\scripts\road_type_sensitivity.py" `
  --roads "zip://$DataRoot\processed2\roads\thailand-latest-free.shp.zip!gis_osm_roads_free_1.shp" `
  --rice-major "$DataRoot\raw\paddy\Classified-Rice-THA-Major-2023-v1.tif" `
  --rice-minor "$DataRoot\raw\paddy\Classified-Rice-THA-Minor-2023-v1.tif" `
  --viirs-ref "$DataRoot\raw\2023\SVDNB_npp_202308.tif" `
  --boundary $Boundary `
  --output "$Root\outputs" `
  --work "$Root\_work"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python "$Root\scripts\render_raster_maps.py" --boundary $Boundary --dpi 600
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python "$Root\scripts\render_combined_map_panel.py" --boundary $Boundary --dpi 600
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python "$Root\scripts\draw_sensitivity_flowchart.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python "$Root\scripts\plot_summary_figures.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m unittest discover -s "$Root\tests" -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
