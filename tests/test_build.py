import unittest

from scripts import build


class LocationDisplayTests(unittest.TestCase):
    def test_grouped_parcels_show_first_but_keep_all_searchable(self):
        full_label = "CT-01, CT-02, CT-03, CT-04, CT-05"
        locations = build.build_locations(
            [(1, [full_label, "Caseta CSIF", "", "36.837934,-2.431370"])]
        )

        location = locations[0]
        self.assertEqual(location["display"], "CT-01")
        self.assertEqual(location["label"], full_label)
        self.assertIn("ct-05", location["search"])
        self.assertIn("ct05", location["flat"])

    def test_grouped_parcels_with_y_show_first(self):
        full_label = "CJ-02, CJ-03 y CJ-04"
        locations = build.build_locations(
            [(1, [full_label, "Descaro", "", "36.835594,-2.429621"])]
        )

        self.assertEqual(locations[0]["display"], "CJ-02")

    def test_single_parcel_keeps_its_label(self):
        locations = build.build_locations(
            [(1, ["CJ-01", "Arena", "", "36.835720,-2.429620"])]
        )

        self.assertEqual(locations[0]["display"], "CJ-01")


if __name__ == "__main__":
    unittest.main()
