from pathlib import Path
import json
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class OutputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "outputs" / "tables" / "road_type_sensitivity_national.csv"
        cls.df = pd.read_csv(path)

    def test_national_results_are_nested_and_bounded(self):
        self.assertTrue(self.df["exposure_proportion"].between(0, 1).all())
        for _, part in self.df.groupby(["rice_type", "radius_px"]):
            ordered = part.set_index("group").loc[
                ["G1_major", "G2_plus_secondary_tertiary", "G3_all_11"]
            ]
            self.assertTrue(ordered["road_proximity_rice_area_acres"].is_monotonic_increasing)

    def test_all_groups_use_one_consistent_buffer_method(self):
        metadata = json.loads((ROOT / "outputs" / "run_metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(metadata["used_existing_all_buffers"])
        self.assertTrue(metadata["all_groups_rebuilt_consistently"])
        self.assertEqual(
            metadata["buffer_method"],
            "circular binary dilation in raster space on the EPSG:4326 rice grid",
        )
        self.assertEqual(metadata["radius_info"]["2"]["requested_buffer_m"], 60)

    def test_acre_conversion(self):
        self.assertIn("road_proximity_rice_area_acres", self.df.columns)
        self.assertNotIn("road_proximity_rice_area_km2", self.df.columns)
        self.assertNotIn("road_proximity_rice_area_rai", self.df.columns)

    def test_archived_buffer_audit_is_exact(self):
        audit = json.loads(
            (ROOT / "outputs" / "legacy_buffer_verification.json").read_text(encoding="utf-8")
        )
        self.assertTrue(audit["exact_match"])
        self.assertEqual(audit["mismatch_pixels"], 0)
        self.assertEqual(audit["extra_pixels"], 0)
        self.assertEqual(audit["missing_pixels"], 0)
        self.assertEqual(audit["pixel_count"], 1_696_041_025)
        self.assertEqual(audit["tile_count"], 432)


if __name__ == "__main__":
    unittest.main()
