import base64
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from scripts import build


BUSINESS_HEADERS = [
    "parcel",
    "trade_name",
    "legal_name",
    "group",
    "activity_type",
    "coords",
]
GENERAL_HEADERS = ["parcel", "name", "group", "coords"]


def table(title, headers, *rows):
    return [
        {
            "title": title,
            "line": 1,
            "headers": tuple(headers),
            "rows": [(index + 2, row) for index, row in enumerate(rows)],
        }
    ]


def single_business(
    parcel, trade_name, legal_name, group, activity_type, coords
):
    return build.build_locations(
        table(
            "Prueba",
            BUSINESS_HEADERS,
            [parcel, trade_name, legal_name, group, activity_type, coords],
        )
    )[0]


def single_general(parcel, name, group, coords):
    return build.build_locations(
        table("Prueba", GENERAL_HEADERS, [parcel, name, group, coords])
    )[0]


class LocationDisplayTests(unittest.TestCase):
    def test_trade_name_has_priority_over_company(self):
        locations = build.build_locations(
            table(
                "Ubicaciones",
                BUSINESS_HEADERS,
                [
                    "CJ-01",
                    "Arena",
                    "Byblos Almería, S.L.",
                    "Casetas",
                    "Caseta Juvenil",
                    "36.835720,-2.429620",
                ],
            )
        )

        self.assertEqual(locations[0]["name"], "Arena")
        self.assertIn("byblos almeria", locations[0]["search"])

    def test_company_is_public_fallback(self):
        locations = build.build_locations(
            table(
                "Ubicaciones",
                BUSINESS_HEADERS,
                [
                    "RT-03",
                    "",
                    "Donaelia, S.L.",
                    "Restauración",
                    "Generales",
                    "36.836216,-2.430316",
                ],
            )
        )

        self.assertEqual(locations[0]["name"], "Donaelia, S.L.")
        self.assertFalse(locations[0]["isPersonalLegalName"])

    def test_person_is_private_and_activity_is_public(self):
        locations = build.build_locations(
            table(
                "Ubicaciones",
                BUSINESS_HEADERS,
                [
                    "H-07",
                    "",
                    "Carbajo Gordillo, Vicente Manuel",
                    "Habilidad",
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
                    "H-01",
                    "",
                    legal_name,
                    "Habilidad",
                    "Actividad",
                    "36.835387,-2.430832",
                )
                self.assertTrue(location["isPersonalLegalName"])
                self.assertEqual(location["name"], "Actividad")
                self.assertNotIn(build.normalize(legal_name), location["search"])

    def test_group_and_activity_are_searchable(self):
        locations = build.build_locations(
            table(
                "Ubicaciones",
                BUSINESS_HEADERS,
                [
                    "CT-01, CT-02",
                    "Caseta CSIF",
                    "",
                    "Casetas",
                    "Caseta Tradicional",
                    "36.837934,-2.431370",
                ],
            )
        )
        location = locations[0]

        self.assertEqual(location["display"], "CT-01")
        self.assertIn("ct-02", location["search"])
        self.assertIn("caseta tradicional", location["search"])
        self.assertIn("casetas", location["search"])

    def test_group_comes_from_the_row_not_the_markdown_heading(self):
        location = build.build_locations(
            table(
                "Título editorial cualquiera",
                BUSINESS_HEADERS,
                [
                    "RT-02",
                    "",
                    "Titular privado",
                    "Bebidas Espirituosas",
                    "Mojitos",
                    "36.836155,-2.430647",
                ],
            )
        )[0]

        self.assertEqual(location["group"], "Bebidas Espirituosas")
        self.assertEqual(
            (location["menuCode"], location["menuName"]),
            ("B", "Bebidas espirituosas"),
        )

    def test_reader_consumes_every_table_and_skips_visual_separators(self):
        source = """# Datos

## Ubicaciones

| parcel | trade_name | legal_name | group | activity_type | coords |
| --- | --- | --- | --- | --- | --- |
| A-01 | Jet | Empresa, S.L. | Atracciones | Adultos | 36.834454,-2.430808 |
| - | - | - | - | - | - |
| H-01 | | Persona | Habilidad | Tiro | 36.834880,-2.431289 |

| parcel | name | group | coords |
| --- | --- | --- | --- |
| D3 | Farola | Puntos de Referencia | 36.835109,-2.429147 |

## Calles

| street | map_path |
| --- | --- |
"""
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data.md"
            data.write_text(source, encoding="utf-8")
            with patch.object(build, "DATA", data):
                tables = build.read_tables()

        self.assertEqual([item["headers"] for item in tables], [
            build.BUSINESS_HEADERS,
            build.GENERAL_HEADERS,
            build.STREET_HEADERS,
        ])
        locations = build.build_locations(tables)
        self.assertEqual([location["label"] for location in locations], ["A-01", "H-01", "D3"])

    def test_navigation_group_mapping(self):
        expected = {
            "Atracciones": ("A", "Atracciones"),
            "Habilidad": ("H", "Habilidad"),
            "Casetas": ("C", "Casetas"),
            "Restauración": ("RT", "Restauración"),
            "Bebidas Espirituosas": ("B", "Bebidas espirituosas"),
            "Repostería": ("R", "Repostería"),
            "Puntos de Interes": ("PI", "Puntos de interés"),
            "Aseos Publicos": ("AP", "Aseos públicos"),
            "Acceso": ("Acc", "Acceso"),
            "Accesos": ("Acc", "Acceso"),
            "Puntos de Referencia": ("F", "Puntos de referencia"),
        }

        for source_group, navigation_group in expected.items():
            with self.subTest(source_group=source_group):
                self.assertEqual(
                    build.navigation_group(source_group), navigation_group
                )

    def test_current_dataset_navigation_groups(self):
        locations = build.build_locations(build.read_tables())
        groups = list(
            dict.fromkeys(
                (location["menuCode"], location["menuName"])
                for location in locations
            )
        )
        expected = [
            ("A", "Atracciones"),
            ("H", "Habilidad"),
            ("C", "Casetas"),
            ("RT", "Restauración"),
            ("B", "Bebidas espirituosas"),
            ("R", "Repostería"),
            ("PI", "Puntos de interés"),
            ("AP", "Aseos públicos"),
            ("Acc", "Acceso"),
            ("F", "Puntos de referencia"),
        ]

        self.assertEqual(groups, expected)
        try:
            build.check_navigation_groups(locations)
        except SystemExit as error:
            self.fail(str(error))

        by_label = {location["label"]: location for location in locations}
        self.assertEqual(by_label["P-06"]["menuCode"], "RT")
        for label in ("RT-02", "RT-20", "MJ-01"):
            with self.subTest(label=label):
                self.assertEqual(by_label[label]["menuCode"], "B")

    def test_general_location_schema_derives_farola_name(self):
        locations = build.build_locations(
            table(
                "Ubicaciones",
                GENERAL_HEADERS,
                [
                    "A1",
                    "Farola",
                    "Puntos de Referencia",
                    "36.832943,-2.431212",
                ],
            )
        )
        location = locations[0]

        self.assertEqual(location["name"], "Farola A1")
        self.assertEqual(location["activityType"], "Farola")
        self.assertEqual(location["marker"], "blue")

    def test_general_location_uses_explicit_group(self):
        location = build.build_locations(
            table(
                "Ubicaciones",
                GENERAL_HEADERS,
                ["PV", "Punto Violeta", "Puntos de Interes", "36.834327,-2.429903"],
            )
        )[0]

        self.assertEqual(location["name"], "Punto Violeta")
        self.assertEqual(location["group"], "Puntos de Interes")
        self.assertEqual(location["activityType"], "Puntos de Interes")

    def test_location_dataset_uses_supported_charset(self):
        tables = build.read_tables()
        locations = build.build_locations(tables)
        street_rows = build.street_rows(tables)
        streets = build.build_streets(street_rows, [0, 0, 210, 297])

        try:
            covered = build.check_charset(
                locations, streets, build.TEMPLATE.read_text(encoding="utf-8")
            )
        except SystemExit as error:
            self.fail(str(error))

        self.assertGreater(covered, 0)

    def test_unique_coordinate_validation_accepts_the_current_dataset(self):
        locations = build.build_locations(build.read_tables())

        self.assertIsNone(build.check_unique_coordinates(locations))

    def test_occupied_2026_parcels_match_dataset(self):
        expected_numbers = {
            "A": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24),
            "CH": (1, 2, 3, 4),
            "CJ": tuple(number for number in range(1, 29) if number not in {14, 15, 19, 20}),
            "CT": (1, 2, 3, 4, 5, 8, 9, 15, 16, 17, 18, 19, 20, 21, 25, 26, 27, 28),
            "E": (2, 4, 5, 6, 7, 8, 9, 10, 11, 12),
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
        tables = build.read_tables()
        locations = build.build_locations(tables)
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
            "Casetas",
            "Caseta Tradicional",
            "36.837934,-2.431370",
        )
        self.assertEqual(location["display"], "CT-01")
        self.assertEqual(location["label"], full_label)
        self.assertIn("ct-05", location["search"])
        self.assertIn("ct05", location["flat"])

    def test_grouped_parcels_with_y_show_first(self):
        full_label = "CJ-02, CJ-03 y CJ-04"
        location = single_business(
            full_label,
            "Descaro",
            "",
            "Casetas",
            "Caseta Juvenil",
            "36.835594,-2.429621",
        )

        self.assertEqual(location["display"], "CJ-02")

    def test_single_parcel_keeps_its_label(self):
        location = single_business(
            "CJ-01",
            "Arena",
            "",
            "Casetas",
            "Caseta Juvenil",
            "36.835720,-2.429620",
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
                    "Farola",
                    "Puntos de Referencia",
                    "36.839427,-2.431177",
                )
                self.assertEqual(location["marker"], expected_marker)
                self.assertIn(f"farola {label.lower()}", location["search"])
                self.assertIn(label.lower(), location["flat"])

    def test_non_farola_does_not_receive_marker(self):
        location = single_business(
            "A-01",
            "Montaña Jet Star",
            "",
            "Atracciones",
            "Adultos",
            "36.834454,-2.430808",
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
        tables = build.read_tables()
        by_label = {
            location["label"]: location
            for location in build.build_locations(tables)
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
        tables = build.read_tables()

        self.assertEqual(
            [item["headers"] for item in tables],
            [build.BUSINESS_HEADERS, build.GENERAL_HEADERS, build.STREET_HEADERS],
        )
        self.assertEqual(len(build.build_locations(tables)), 232)

    def test_known_private_and_company_rows_follow_public_name_rules(self):
        locations = {
            loc["label"]: loc
            for loc in build.build_locations(build.read_tables())
        }

        self.assertEqual(locations["H-07"]["name"], "Dardos")
        self.assertNotIn("carbajo", locations["H-07"]["search"])
        self.assertEqual(locations["RT-03"]["name"], "Donaelia, S.L.")
        self.assertEqual(
            locations["CT-25, CT-26, CT-27, CT-28"]["name"], "Paripé"
        )
        self.assertNotIn("CJ-14, CJ-15", locations)
        self.assertFalse(any(loc["name"] == "Palo Loco" for loc in locations.values()))

    def test_every_business_location_has_public_context(self):
        for location in build.build_locations(build.read_tables()):
            if location["group"] in {
                "Puntos de Interes",
                "Aseos Publicos",
                "Acceso",
                "Puntos de Referencia",
            }:
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
            for loc in build.build_locations(build.read_tables())
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
            "RT-04": "Generales",
            "RT-06": "Pinchos morunos",
            "RT-10": "Pinchos morunos",
            "RT-30": "Generales",
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

    def test_back_control_is_an_accessible_header_button(self):
        class HeaderParser(HTMLParser):
            in_header = False
            back = None

            def handle_starttag(self, tag, attrs):
                if tag == "header":
                    self.in_header = True
                attributes = dict(attrs)
                if attributes.get("id") == "back":
                    self.back = (tag, attributes, self.in_header)

            def handle_endtag(self, tag):
                if tag == "header":
                    self.in_header = False

        parser = HeaderParser()
        parser.feed(build.TEMPLATE.read_text(encoding="utf-8"))
        self.assertIsNotNone(parser.back)
        tag, attrs, in_header = parser.back
        self.assertEqual(tag, "button")
        self.assertTrue(in_header)
        self.assertEqual(attrs.get("type"), "button")
        self.assertEqual(attrs.get("aria-label"), "Volver a los grupos")

    def test_operational_group_row_matches_location_geometry(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn(
            "groups.set(loc.menuCode, {code:loc.menuCode, name:loc.menuName});",
            template,
        )
        self.assertIn(
            "LOCATIONS.filter(loc => loc.menuCode === groupCode)", template
        )
        self.assertIn("num.className = 'num';", template)
        self.assertIn("num.textContent = group.code;", template)
        self.assertIn("button.className = 'nom group-toggle';", template)
        self.assertIn("txt.className = 'txt';", template)
        self.assertIn("disabledMap.className = 'go group-map-disabled';", template)
        self.assertIn("disabledMap.setAttribute('aria-hidden', 'true');", template)
        self.assertIn(".go.group-map-disabled{color:var(--faint);pointer-events:none}", template)
        self.assertIn("function pinIcon()", template)
        self.assertEqual(template.count("pill.append(pinIcon());"), 2)
        self.assertNotIn("group-count", template)

    def test_header_stays_outside_the_scroll_container(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("html{height:100%;background:var(--bg)}", template)
        self.assertIn("height:100vh;height:100dvh;", template)
        self.assertIn(
            "display:grid;grid-template-rows:auto minmax(0,1fr);overflow:hidden;",
            template,
        )
        self.assertIn(
            "main{min-height:0;overflow-y:auto;overscroll-behavior-y:contain;",
            template,
        )
        self.assertNotIn("position:sticky", template)

    def test_nonempty_query_keeps_global_search(self):
        template = build.TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("activeGroup = null;", template)
        self.assertIn("render(search(v));", template)

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


class StreetTests(unittest.TestCase):
    def test_paths_have_searchable_names_but_no_gps_destination(self):
        streets = build.build_streets(
            [(10, ["c/Galán de Noche", "M 20 30 L 100 30"])], [0, 0, 210, 297]
        )
        self.assertEqual(len(streets), 1)
        street = streets[0]
        self.assertIn("galan de noche", street["search"])
        self.assertIn("galandenoche", street["flat"])
        self.assertEqual(street["mapPath"], "M 20 30 L 100 30")
        self.assertEqual(street["mapView"], [-12, -12, 150, 120])
        for field in ("lat", "lon", "start", "end", "waypoints", "mapPoint"):
            self.assertNotIn(field, street)

    def test_long_street_fits_entire_view_with_context(self):
        street = build.build_streets(
            [(1, ["Paseo", "M 75 10 L 75 265"])], [0, 0, 210, 297]
        )[0]
        x, y, width, height = street["mapView"]
        self.assertLessEqual(x, 63)
        self.assertLessEqual(y, -2)
        self.assertGreaterEqual(x + width, 87)
        self.assertGreaterEqual(y + height, 277)
        self.assertAlmostEqual(width / height, 5 / 4)

    def test_curves_and_closed_external_roundabout_are_supported(self):
        path = "M 49 79 C 49 72 39 72 39 79 C 39 86 49 86 49 79 Z"
        street = build.build_streets([(1, ["Rotonda del Acebo", path])], [0, 0, 210, 297])[0]
        self.assertEqual(street["mapPath"], path)

    def test_short_streets_at_edges_keep_context_inside_the_map(self):
        for path in ("M 46 8 L 72 8", "M 20 290 L 80 290", "M 205 200 L 205 250"):
            with self.subTest(path=path):
                street = build.build_streets([(1, ["Borde", path])], [0, 0, 210, 297])[0]
                x, y, width, height = street["mapView"]
                self.assertGreaterEqual(x, -12)
                self.assertGreaterEqual(y, -12)
                self.assertLessEqual(x + width, 222)
                self.assertLessEqual(y + height, 309)

    def test_malformed_svg_separators_are_rejected(self):
        for path in ("M,20,30 L40,,50", "M 20 30, L40 50", "M 20 30 L 40 50,", "M 20 30 L 40,,50"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(SystemExit, "trazado SVG inválido"):
                    build.build_streets([(12, ["Prueba", path])], [0, 0, 210, 297])

    def test_invalid_paths_fail_instead_of_silently_omitting_streets(self):
        for path in ("", "M 20 30", "M 20 30 L 20 30", "L 20 30 L 40 50", "M 20 30 L 40", "M 20 30 Q 40 50", "M 20 30 A 3 3 0 0 1 40 50", "M 20 30 L NaN 50", "M 20 30 L 999 999", '<script>alert(1)</script>'):
            with self.subTest(path=path):
                with self.assertRaises(SystemExit):
                    build.build_streets([(12, ["Prueba", path])], [0, 0, 210, 297])

    def test_empty_names_duplicate_names_and_extra_columns_fail(self):
        for rows in (
            [(1, ["", "M 20 30 L 40 50"])],
            [(1, ["Prueba", "M 20 30 L 40 50", "extra"])],
            [(1, ["Cañada", "M 20 30 L 40 50"]), (2, ["CANADA", "M 20 30 L 40 50"])],
        ):
            with self.subTest(rows=rows):
                with self.assertRaises(SystemExit):
                    build.build_streets(rows, [0, 0, 210, 297])

    def test_catalog_contains_requested_streets_and_police_references(self):
        streets = build.build_streets(build.street_rows(build.read_tables()), [0, 0, 210, 297])
        by_name = {street["name"]: street for street in streets}
        self.assertEqual(set(by_name), {
            "c/Cabo de Gata", "c/El Alquián", "c/La Cañada", "c/Barrio Alto",
            "c/Los Almendros", "c/Piedras Redondas", "c/La Chanca-Pescadería",
            "c/Paseo de Almería", "c/Paseo de la Feria", "c/Casco Histórico",
            "c/Nueva Andalucía", "c/Ciudad Jardín", "c/500 viviendas-Tagarete",
            "c/Galán de Noche", "c/Acebo", "Rotonda del Acebo",
        })
        self.assertEqual(by_name["c/Galán de Noche"]["mapPath"], by_name["c/Paseo de Almería"]["mapPath"])
        # La rotonda señalada está al oeste de la puerta (x~60), no en A7 (x~76).
        numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", by_name["Rotonda del Acebo"]["mapPath"])]
        self.assertLess(max(numbers[::2]), 55)
        self.assertGreater(min(numbers[1::2]), 65)
        self.assertLess(max(numbers[1::2]), 90)


class MinimapTests(unittest.TestCase):
    def test_projection_keeps_latitude_and_longitude_axes_in_order(self):
        calibration = {
            "origin_lat_lon": [0, 0],
            "metres_per_degree": [1, 1],
            "svg_units_per_local_metre": [[2, 3, 10], [5, -7, 100]],
        }

        self.assertEqual(build.project_minimap_point("2", "3", calibration), [22, 101])

    def test_current_farolas_land_on_the_reviewed_intersections(self):
        locations = build.build_locations(build.read_tables())
        build.build_minimap(locations)
        by_label = {location["label"]: location for location in locations}
        expected = {
            "A8": [76.507, 8.361],
            "A1": [74.593, 261.460],
            "B4": [98.972, 148.876],
            "C7": [107.914, 82.798],
            "D2": [148.201, 209.584],
        }
        for label, point in expected.items():
            with self.subTest(label=label):
                self.assertEqual(by_label[label]["mapPoint"], point)

    def test_minimap_generation_does_not_change_operational_coordinates(self):
        locations = build.build_locations(build.read_tables())
        before = [(loc["lat"], loc["lon"]) for loc in locations]

        build.build_minimap(locations)

        self.assertEqual([(loc["lat"], loc["lon"]) for loc in locations], before)
        self.assertTrue(all(loc["mapPoint"] is not None for loc in locations))

    def test_viewport_keeps_context_and_marker_visible_at_map_edges(self):
        for point, expected in (
            ([80, 150], [5, 90, 150, 120]),
            ([76.5, 8.4], [1.5, -12, 150, 120]),
            ([148.2, 266.9], [72, 189, 150, 120]),
        ):
            with self.subTest(point=point):
                self.assertEqual(build.minimap_viewbox(point, [0, 0, 210, 297]), expected)

    def test_edge_viewport_leaves_room_for_the_whole_pin_not_only_its_tip(self):
        for point in ([76.507, 8.361], [0, 0], [210, 297]):
            with self.subTest(point=point):
                x, y, width, height = build.minimap_viewbox(point, [0, 0, 210, 297])
                self.assertLessEqual(x, point[0] - 5)
                self.assertLessEqual(y, point[1] - 11)
                self.assertGreaterEqual(x + width, point[0] + 5)
                self.assertGreaterEqual(y + height, point[1] + 1)

    def test_outside_point_is_not_moved_to_a_false_position(self):
        location = single_general("X", "Fuera", "Acceso", "36.850000,-2.431000")

        build.build_minimap([location])

        self.assertIsNone(location["mapPoint"])
        self.assertIsNone(location["mapView"])
        self.assertEqual(location["lat"], "36.850000")

    def test_map_is_self_contained_and_excludes_diagnostic_overlays(self):
        config = build.build_minimap(build.build_locations(build.read_tables()))
        prefix, content = config["image"].split(",", 1)
        self.assertEqual(prefix, "data:image/svg+xml;base64")
        root = ET.fromstring(base64.b64decode(content))
        self.assertEqual(root.get("viewBox"), "0 0 210 297")
        self.assertIsNone(root.find(".//*[@id='farolas-nota']"))
        self.assertIsNone(root.find(".//*[@id='u24-georeference']"))
        self.assertIsNone(root.find(".//*[@id='referencias-farolas']"))
        for element in root.iter():
            if element.tag.endswith("}image"):
                href = element.get("{http://www.w3.org/1999/xlink}href", element.get("href", ""))
                self.assertTrue(href.startswith("data:image/"))

    def test_missing_calibration_stops_build_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 297"/>', encoding="utf-8")
            with patch.object(build, "MINIMAP", path):
                with self.assertRaisesRegex(SystemExit, "calibraci"):
                    build.build_minimap([])


if __name__ == "__main__":
    unittest.main()
