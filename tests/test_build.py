import re
import unittest

from scripts import build


BUSINESS_HEADERS = ["parcel", "trade_name", "legal_name", "activity_type", "coords"]
GENERAL_HEADERS = ["parcel", "name", "type", "coords"]


def section(title, headers, *rows):
    return {
        build.normalize(title): {
            "title": title,
            "rows": [(1, headers)]
            + [(index + 2, row) for index, row in enumerate(rows)],
        }
    }


def single_business(parcel, trade_name, legal_name, activity_type, coords):
    return build.build_locations(
        section(
            "Prueba",
            BUSINESS_HEADERS,
            [parcel, trade_name, legal_name, activity_type, coords],
        )
    )[0]


def single_general(parcel, name, location_type, coords):
    return build.build_locations(
        section("Prueba", GENERAL_HEADERS, [parcel, name, location_type, coords])
    )[0]


class LocationDisplayTests(unittest.TestCase):
    def test_trade_name_has_priority_over_company(self):
        locations = build.build_locations(
            section(
                "Casetas",
                BUSINESS_HEADERS,
                [
                    "CJ-01",
                    "Arena",
                    "Byblos Almería, S.L.",
                    "Juvenil",
                    "36.835720,-2.429620",
                ],
            )
        )

        self.assertEqual(locations[0]["name"], "Arena")
        self.assertIn("byblos almeria", locations[0]["search"])

    def test_company_is_public_fallback(self):
        locations = build.build_locations(
            section(
                "Restauración",
                BUSINESS_HEADERS,
                ["RT-03", "", "Donaelia, S.L.", "Mesón", "36.836216,-2.430316"],
            )
        )

        self.assertEqual(locations[0]["name"], "Donaelia, S.L.")
        self.assertFalse(locations[0]["isPersonalLegalName"])

    def test_person_is_private_and_activity_is_public(self):
        locations = build.build_locations(
            section(
                "Habilidad",
                BUSINESS_HEADERS,
                [
                    "H-07",
                    "",
                    "Carbajo Gordillo, Vicente Manuel",
                    "Dardos",
                    "36.835387,-2.430832",
                ],
            )
        )
        location = locations[0]

        self.assertEqual(location["name"], "Dardos")
        self.assertTrue(location["isPersonalLegalName"])
        for key in ("search", "flat", "nameSearch"):
            self.assertNotIn("carbajo", location[key])
        self.assertEqual(location["legalName"], "Carbajo Gordillo, Vicente Manuel")

    def test_personal_names_containing_sa_are_not_companies(self):
        for legal_name in (
            "Simarro Cano, Santiago",
            "Santiago Cortés, Eva",
            "María Sandra Crespillo Durán",
            "Sanz Vallejo, María del Mar",
        ):
            with self.subTest(legal_name=legal_name):
                location = single_business(
                    "H-01", "", legal_name, "Actividad", "36.835387,-2.430832"
                )
                self.assertTrue(location["isPersonalLegalName"])
                self.assertEqual(location["name"], "Actividad")
                self.assertNotIn(build.normalize(legal_name), location["search"])

    def test_group_and_activity_are_searchable(self):
        locations = build.build_locations(
            section(
                "Casetas",
                BUSINESS_HEADERS,
                [
                    "CT-01, CT-02",
                    "Caseta CSIF",
                    "",
                    "Tradicional",
                    "36.837934,-2.431370",
                ],
            )
        )
        location = locations[0]

        self.assertEqual(location["display"], "CT-01")
        self.assertIn("ct-02", location["search"])
        self.assertIn("caseta tradicional", location["search"])
        self.assertIn("casetas", location["search"])

    def test_general_location_schema_remains_supported(self):
        locations = build.build_locations(
            section(
                "Farolas",
                GENERAL_HEADERS,
                [
                    "A1",
                    "Farola A1",
                    "Punto de Referencia",
                    "36.832943,-2.431212",
                ],
            )
        )
        location = locations[0]

        self.assertEqual(location["name"], "Farola A1")
        self.assertEqual(location["activityType"], "Punto de Referencia")
        self.assertEqual(location["marker"], "blue")

    def test_location_dataset_uses_supported_charset(self):
        sections = build.read_sections()
        locations = build.build_locations(sections)
        center, _, _ = build.check_coherence(locations)
        _, street_rows = build.table_headers(sections["calles"], "calles")
        streets, _, _ = build.build_streets(street_rows, locations, center)

        try:
            covered = build.check_charset(
                locations, streets, build.TEMPLATE.read_text(encoding="utf-8")
            )
        except SystemExit as error:
            self.fail(str(error))

        self.assertGreater(covered, 0)

    def test_occupied_2026_parcels_match_dataset(self):
        expected_numbers = {
            "A": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24),
            "CH": (1, 2, 3, 4),
            "CJ": tuple(number for number in range(1, 29) if number not in {19, 20}),
            "CT": (1, 2, 3, 4, 5, 8, 9, 15, 16, 17, 18, 19, 20, 21, 25, 26, 27, 28),
            "E": (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12),
            "H": (1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 32, 33, 34, 35, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47),
            "I": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32),
            "MJ": (1,),
            "P": (6,),
            "PT": (1,),
            "R": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 34, 35, 36, 37, 38, 39, 40, 41, 43, 45, 49, 50, 51, 53),
            "RT": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 19, 20, 21, 22, 23, 24, 25, 30, 32),
            "VN": (1, 2, 3, 4),
        }
        expected = {
            f"{prefix}-{number:02d}"
            for prefix, numbers in expected_numbers.items()
            for number in numbers
        }
        sections = build.read_sections()
        locations = build.build_locations(sections)
        present = {
            f"{prefix.upper()}-{int(number):02d}"
            for location in locations
            for prefix, number in re.findall(
                r"\b(A|E|I|H|R|RT|CH|VN|MJ|P|PT|CJ|CT)-(\d+)\b",
                location["label"],
                re.IGNORECASE,
            )
        }

        self.assertEqual(present, expected)

    def test_grouped_parcels_show_first_but_keep_all_searchable(self):
        full_label = "CT-01, CT-02, CT-03, CT-04, CT-05"
        location = single_business(
            full_label,
            "Caseta CSIF",
            "",
            "Tradicional",
            "36.837934,-2.431370",
        )
        self.assertEqual(location["display"], "CT-01")
        self.assertEqual(location["label"], full_label)
        self.assertIn("ct-05", location["search"])
        self.assertIn("ct05", location["flat"])

    def test_grouped_parcels_with_y_show_first(self):
        full_label = "CJ-02, CJ-03 y CJ-04"
        location = single_business(
            full_label, "Descaro", "", "Juvenil", "36.835594,-2.429621"
        )

        self.assertEqual(location["display"], "CJ-02")

    def test_single_parcel_keeps_its_label(self):
        location = single_business(
            "CJ-01", "Arena", "", "Juvenil", "36.835720,-2.429620"
        )

        self.assertEqual(location["display"], "CJ-01")

    def test_farola_marker_follows_code_prefix(self):
        cases = {
            "A8": "blue",
            "B8": "green",
            "C7": "red",
            "D3": "yellow",
        }

        for label, expected_marker in cases.items():
            with self.subTest(label=label):
                location = single_general(
                    label,
                    f"Farola {label}",
                    "Punto de Referencia",
                    "36.839427,-2.431177",
                )
                self.assertEqual(location["marker"], expected_marker)
                self.assertIn(f"farola {label.lower()}", location["search"])
                self.assertIn(label.lower(), location["flat"])

    def test_non_farola_does_not_receive_marker(self):
        location = single_business(
            "A-01", "Montaña Jet Star", "", "Adulto", "36.834454,-2.430808"
        )

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
        by_label = {
            location["label"]: location
            for location in build.build_locations(sections)
        }

        for label, (lat, lon, marker) in expected.items():
            with self.subTest(label=label):
                location = by_label[label]
                self.assertEqual(location["name"], f"Farola {label}")
                self.assertEqual((location["lat"], location["lon"]), (lat, lon))
                self.assertEqual(location["marker"], marker)
                self.assertIn(label.lower(), location["search"])
                self.assertIn(f"farola {label.lower()}", location["search"])

    def test_current_dataset_uses_new_headers_only(self):
        sections = build.read_sections()

        for key, section_data in sections.items():
            if not section_data["rows"]:
                continue
            headers = tuple(
                build.normalize(value) for value in section_data["rows"][0][1]
            )
            self.assertIn(
                headers,
                {
                    build.BUSINESS_HEADERS,
                    build.GENERAL_HEADERS,
                    build.STREET_HEADERS,
                },
                key,
            )

    def test_known_private_and_company_rows_follow_public_name_rules(self):
        locations = {
            loc["label"]: loc
            for loc in build.build_locations(build.read_sections())
        }

        self.assertEqual(locations["H-07"]["name"], "Dardos")
        self.assertNotIn("carbajo", locations["H-07"]["search"])
        self.assertEqual(locations["RT-03"]["name"], "Donaelia, S.L.")
        self.assertEqual(
            locations["CT-25, CT-26, CT-27, CT-28"]["name"], "Paripé"
        )
        self.assertEqual(
            locations["CJ-14, CJ-15"]["name"], "Caseta Juvenil"
        )

    def test_every_business_location_has_public_context(self):
        for location in build.build_locations(build.read_sections()):
            if location["group"] in {"Puntos de Interes", "Farolas"}:
                continue
            with self.subTest(parcel=location["label"]):
                self.assertTrue(
                    location["tradeName"]
                    or location["legalName"]
                    or location["activityType"]
                )

    def test_official_owners_are_present_for_reconciled_rows(self):
        locations = {
            loc["label"]: loc
            for loc in build.build_locations(build.read_sections())
        }
        attraction_parcels = {
            loc["label"]
            for loc in locations.values()
            if loc["group"] == "Atracciones"
        }
        caseta_parcels = {
            loc["label"]
            for loc in locations.values()
            if loc["group"] == "Casetas"
            and loc["label"] != "CM"
        }

        for parcel in attraction_parcels | caseta_parcels:
            with self.subTest(parcel=parcel):
                self.assertTrue(locations[parcel]["legalName"])

        expected = {
            "CH-01": "Moreno García, Francisco",
            "CH-03": "Churrería Hnos. Manzano, S.L.",
            "VN-03": "Almeripark Ocio y Eventos, S.L.",
            "RT-10": "El Kentafi Azirar, Mohamed",
            "RT-20": "Marcos Amador Gómez",
            "RT-30": "Haro Jiménez, Sonia Lucía",
        }
        for parcel, legal_name in expected.items():
            with self.subTest(parcel=parcel):
                self.assertEqual(locations[parcel]["legalName"], legal_name)

        expected_activities = {
            "CH-01": "Churrería",
            "VN-03": "Vinos",
            "RT-04": "General",
            "RT-06": "Pinchos morunos",
            "RT-10": "Pinchos morunos",
            "RT-30": "Restauración",
        }
        for parcel, activity_type in expected_activities.items():
            with self.subTest(parcel=parcel):
                self.assertEqual(
                    locations[parcel]["activityType"], activity_type
                )

    def test_compact_layout_contract_is_present(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        required = (
            "grid-template-columns:36px minmax(0,1fr)",
            ".bar .mark{flex:none;width:34px;height:34px;display:block}",
            "#q{\n  display:block;width:100%;height:34px",
            "grid-template-columns:56px minmax(0,1fr) 38px",
            "min-height:38px",
            "width:28px;height:28px",
            "border-bottom:1px solid var(--rule)",
        )
        for rule in required:
            with self.subTest(rule=rule):
                self.assertIn(rule, template)

        self.assertNotIn("min-height:72px", template)
        self.assertNotIn("width:40px;height:40px", template)

    def test_name_focus_uses_a_neutral_compact_outline(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            "outline:1px solid #565B61;outline-offset:-1px;border-radius:4px",
            template,
        )
        self.assertNotIn(
            ".detail-toggle:focus-visible{\n"
            "  outline:2px solid var(--accent)",
            template,
        )

    def test_farola_bar_is_centered_short_and_rounded(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(".row.farola::before{", template)
        self.assertIn("width:4px;height:22px", template)
        self.assertIn("top:50%", template)
        self.assertIn("transform:translateY(-50%)", template)
        self.assertIn("border-radius:999px", template)
        self.assertIn(".row.expanded.farola::before{top:19px}", template)

    def test_inline_detail_contract_is_present(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("function detail(loc)", template)
        self.assertIn("function openDetail(", template)
        self.assertIn("function closeDetail(", template)
        self.assertIn("aria-expanded", template)
        self.assertIn("aria-controls", template)
        self.assertIn("prefers-reduced-motion:reduce", template)

    def test_coordinates_copy_without_visible_instruction_or_text_mutation(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            "coordinates.textContent = loc.lat + ', ' + loc.lon;", template
        )
        self.assertIn(
            "coordinates.dataset.coords = loc.lat + ',' + loc.lon;", template
        )
        self.assertIn("copyText(btn.dataset.coords).then(() => {", template)
        self.assertIn("meta.textContent = LABEL.copied;", template)
        self.assertNotIn("TEXT.coordinates + ': '", template)
        self.assertNotIn("coordinates.dataset.label", template)
        self.assertNotIn("btn.textContent = TEXT.copied", template)
        self.assertNotIn("btn.dataset.label || btn.dataset.coords", template)

    def test_service_worker_cache_version_changes_with_compiled_app(self):
        old_worker = build.render_service_worker("<html>datos antiguos</html>")
        new_worker = build.render_service_worker("<html>datos nuevos</html>")
        cache_pattern = re.compile(r"const CACHE = 'u24-([0-9a-f]{12})';")

        old_match = cache_pattern.search(old_worker)
        new_match = cache_pattern.search(new_worker)

        self.assertIsNotNone(old_match)
        self.assertIsNotNone(new_match)
        self.assertNotEqual(old_match.group(1), new_match.group(1))
        self.assertNotIn("__APP_VERSION__", old_worker)
        self.assertNotIn("__APP_VERSION__", new_worker)


if __name__ == "__main__":
    unittest.main()
