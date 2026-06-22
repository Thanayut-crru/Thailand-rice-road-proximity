# Results

## Main finding

The pooled 11-class estimate is driven mainly by the addition of `residential`
and `unclassified` roads. The analysis therefore cannot be interpreted as an
estimate for major illuminated roads alone.

All G1, G2 and G3 results below were rebuilt from road centrelines with the same
`all_touched=True` rasterization and circular 1-/2-pixel dilation. No legacy
buffer raster was reused. A separate full-grid audit explains why G3 totals are
identical to the earlier pooled run: the stored legacy nominal 50-m raster equals
one additional `disk(1)` dilation of the stored nominal 30-m raster at every one
of 1,696,041,025 pixels. The legacy “50 m” label therefore represents the same
two-pixel (~60 m) setting, not a verified exact 50-m metric radius.

| Rice | Radius | G1 major roads | G2 + secondary/tertiary | G3 all 11 |
|---|---:|---:|---:|---:|
| Major | 1 px (~30 m) | 0.40% | 2.63% | 11.80% |
| Major | 2 px (~60 m) | 0.64% | 4.21% | 17.63% |
| Minor | 1 px (~30 m) | 0.38% | 1.89% | 10.12% |
| Minor | 2 px (~60 m) | 0.62% | 3.34% | 17.20% |

For the all-11-class network, affected-proxy areas are 2,761,432 acres (major,
1 px), 4,125,876 acres (major, 2 px), 377,428 acres (minor, 1 px), and 641,899
acres (minor, 2 px). “Affected” here means inside the road-proximity mask; it
does not establish measured light exposure or crop damage.

At 1 pixel, adding residential and unclassified roads contributes an additional
2,145,671 acres for major rice and 306,971 acres for minor rice. These increments
are 77.7% and 81.3%, respectively, of the final all-11-class proximity area.

At 2 pixels, the same addition contributes 3,141,580 acres for major rice and
517,414 acres for minor rice, or 76.1% and 80.6% of the final estimates.

## Road-data composition

The filtered road layer contains 1,607,087 segments. Residential roads account
for 84.17% and unclassified roads for 7.24% of segments. Together they represent
91.40% of included segments. Segment counts do not measure road length, but they
explain why the pooled network is dominated by local-road mapping.

## Interpretation

The result is strong evidence of sensitivity to road-class inclusion, not
evidence that local roads illuminate rice fields. Lighting status is absent from
the OSM inputs. A defensible paper should present G1/G2/G3 as sensitivity
scenarios and reserve “ALAN exposure” for analyses that use measured radiance or
validated lighting information.

Detailed national and regional estimates are in `outputs/tables/`.
