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

    def test_farola_marker_follows_code_prefix(self):
        cases = {
            "A8": "blue",
            "B8": "green",
            "C7": "red",
            "D3": "yellow",
        }

        for label, expected_marker in cases.items():
            with self.subTest(label=label):
                location = build.build_locations(
                    [(1, [label, f"Farola {label}", "", "36.839427,-2.431177"])]
                )[0]
                self.assertEqual(location["marker"], expected_marker)
                self.assertIn(f"farola {label.lower()}", location["search"])
                self.assertIn(label.lower(), location["flat"])

    def test_non_farola_does_not_receive_marker(self):
        location = build.build_locations(
            [(1, ["A-01", "Montaña Jet Star", "", "36.834454,-2.430808"])]
        )[0]

        self.assertEqual(location["marker"], "")

    def test_farola_dataset_keeps_codes_coordinates_and_expected_markers(self):
        expected = {
            "A8": ("36.839427", "-2.431177", "blue"),
            "B8": ("36.839061", "-2.430659", "green"),
            "A7": ("36.837703", "-2.431197", "blue"),
            "B7": ("36.837688", "-2.430670", "green"),
            "C7": ("36.837517", "-2.430173", "red"),
            "A6": ("36.836735", "-2.431184", "blue"),
            "B6": ("36.836732", "-2.430665", "green"),
            "C6": ("36.836734", "-2.429810", "red"),
            "A5": ("36.836337", "-2.431245", "blue"),
            "A4": ("36.835837", "-2.431208", "blue"),
            "B4": ("36.835825", "-2.430450", "green"),
            "C4": ("36.835837", "-2.429779", "red"),
            "A3": ("36.835113", "-2.431211", "blue"),
            "B3": ("36.835111", "-2.430444", "green"),
            "C3": ("36.835109", "-2.429785", "red"),
            "D3": ("36.835109", "-2.429147", "yellow"),
            "A2": ("36.834292", "-2.431228", "blue"),
            "B2": ("36.834266", "-2.430445", "green"),
            "C2": ("36.834269", "-2.429797", "red"),
            "D2": ("36.834265", "-2.428882", "yellow"),
            "A1": ("36.832943", "-2.431212", "blue"),
            "B1": ("36.832815", "-2.430459", "green"),
            "C1": ("36.832799", "-2.429789", "red"),
        }
        sections = build.read_sections()
        rows = build.drop_header(sections["ubicaciones"], "ubication_number")
        by_label = {
            location["label"]: location for location in build.build_locations(rows)
        }

        for label, (lat, lon, marker) in expected.items():
            with self.subTest(label=label):
                location = by_label[label]
                self.assertEqual(location["name"], f"Farola {label}")
                self.assertEqual((location["lat"], location["lon"]), (lat, lon))
                self.assertEqual(location["marker"], marker)
                self.assertIn(label.lower(), location["search"])
                self.assertIn(f"farola {label.lower()}", location["search"])

    def test_farola_bar_is_centered_short_and_rounded(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(".row.farola::before{", template)
        self.assertIn("width:4px;height:40px", template)
        self.assertIn("top:50%", template)
        self.assertIn("transform:translateY(-50%)", template)
        self.assertIn("border-radius:999px", template)
        self.assertNotIn(
            "border-inline-start:4px solid var(--farola-color)", template
        )


if __name__ == "__main__":
    unittest.main()
