#!/usr/bin/env python3
"""Genera dist/, la carpeta que se publica, a partir de data.md y src/.

Uso:  python3 scripts/build.py

dist/ contiene exactamente lo que la aplicacion necesita y nada mas: el resto
del repositorio no se publica. Ante cualquier dato invalido el proceso se
detiene con un mensaje concreto; nunca omite nada en silencio.

Documentacion: docs/02-datos.md y docs/04-convenciones.md.
"""

import base64
import hashlib
import json
import math
import re
import shutil
import statistics
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

# ── Configuracion del operativo ───────────────────────────────────────────────

# Rotulo que aparece bajo el buscador.
OPERATIVO = "Feria de Almería 2026"

# ──────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data.md"
SRC = ROOT / "src"
TEMPLATE = SRC / "template.html"
MANIFEST = SRC / "manifest.webmanifest"
SERVICE_WORKER = SRC / "sw.js"
FONTS = SRC / "fonts"
LOGO = SRC / "logo.svg"
MINIMAP = SRC / "minimap.svg"
CHARSET = FONTS / "charset.txt"
VENDOR = SRC / "vendor" / "fuse.basic.min.js"
ICONS = ROOT / "icons"

DIST = ROOT / "dist"
OUTPUT = DIST / "index.html"

FONT_WEIGHTS = (400, 500, 700)

# Se copian tal cual a dist/. El service worker se versiona al ensamblarlo.
COPY_ROOT = ("manifest.webmanifest",)
COPY_ICONS = (
    "icon-192.png",
    "icon-512.png",
    "icon-maskable-192.png",
    "icon-maskable-512.png",
    "apple-touch-icon.png",
    "favicon-32.png",
    "favicon-16.png",
)

# Coherencia geografica: las coordenadas se validan entre si, no contra un lugar
# concreto. Un error de transcripcion en la latitud desplaza el punto decenas de
# kilometros; una coordenada de otra provincia, cientos.
FAR_AWAY_KM = 25     # detiene el proceso
OUTLIER_FACTOR = 4   # avisa, si ademas supera el minimo de abajo
OUTLIER_MIN_M = 500

# Longitud de calle habitual, en metros. Solo para avisar.
STREET_LENGTH_USUAL = (20, 5000)

COORDS_RE = re.compile(r"^(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)$")
FAROLA_LABEL_RE = re.compile(r"^[A-D]\d+$")
SECTION_RE = re.compile(r"^#{1,6}\s+(.*)$")
TABLE_FIRST_COLUMNS = {"parcel", "street"}

BUSINESS_HEADERS = (
    "parcel",
    "trade_name",
    "legal_name",
    "group",
    "activity_type",
    "coords",
)
GENERAL_HEADERS = ("parcel", "name", "group", "coords")
STREET_HEADERS = ("street", "start", "end", "waypoints")
LOCATION_HEADERS = {BUSINESS_HEADERS, GENERAL_HEADERS}
SUPPORTED_HEADERS = LOCATION_HEADERS | {STREET_HEADERS}

PUBLIC_LEGAL_RE = re.compile(
    r"(?:\bgrupo\b|\basoc\.?\b|\basociaci[oó]n\b|\bpartido\b|\bsindical\b|"
    r"\bayuntamiento\b|\borganizaci[oó]n\b|\bsociedad\b|\bclub\b|"
    r"\bs\s*\.?\s*l\s*\.?(?:\s*u\s*\.?)?(?!\w)|"
    r"\bs\s*\.?\s*a\s*\.?(?!\w))",
    re.IGNORECASE,
)

FAROLA_COLORS = {
    "A": "blue",
    "B": "green",
    "C": "red",
    "D": "yellow",
}

# Menú operativo. `group` ya viene consolidado en cada fila de data.md; este
# catálogo solo fija el código corto y el rótulo corregido que se muestran.
NAVIGATION_GROUPS = (
    ("A", "Atracciones", "atracciones"),
    ("H", "Habilidad", "habilidad"),
    ("C", "Casetas", "casetas"),
    ("RT", "Restauración", "restauracion"),
    ("B", "Bebidas espirituosas", "bebidas espirituosas"),
    ("R", "Repostería", "reposteria"),
    ("PI", "Puntos de interés", "puntos de interes"),
    ("AP", "Aseos públicos", "aseos publicos"),
    ("Acc", "Acceso", "acceso"),
    ("F", "Puntos de referencia", "puntos de referencia"),
)
NAVIGATION_BY_SOURCE = {
    source: (code, name)
    for code, name, source in NAVIGATION_GROUPS
}

# Bloque de textos visibles de la plantilla y cadenas que contiene.
UI_TEXT_RE = re.compile(r"const TEXT = \{(.*?)\n\};", re.S)
UI_STRING_RE = re.compile(r"'((?:[^'\\]|\\.)*)'")

def fail(msg):
    sys.exit(f"ERROR: {msg}")


def normalize(text):
    """Minusculas, sin tildes, comillas normalizadas, espacios colapsados."""
    text = text.lower().replace("‘", "'").replace("’", "'")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def flatten(text):
    """Solo letras y digitos: sin espacios, barras, guiones ni apostrofos.

    Permite que un separador de mas o de menos no deje la pantalla vacia.
    """
    return re.sub(r"[^a-z0-9]", "", normalize(text))


def haversine(a, b):
    """Metros entre dos puntos."""
    radio = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radio * math.asin(math.sqrt(h))


# ── Lectura de data.md ────────────────────────────────────────────────────────


def read_tables():
    """Lee todas las tablas completas, aunque compartan título Markdown."""
    tables = []
    title = ""
    current = None

    for lineno, raw in enumerate(DATA.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()

        heading = SECTION_RE.match(line)
        if heading:
            title = heading.group(1).strip()
            current = None
            continue

        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if not any(cells) or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if all(not cell or cell == "-" for cell in cells):
            continue

        first = normalize(cells[0])
        if first in TABLE_FIRST_COLUMNS:
            headers = tuple(normalize(cell) for cell in cells)
            if headers not in SUPPORTED_HEADERS:
                fail(
                    f"data.md linea {lineno}, seccion {title!r}: "
                    f"encabezado no admitido {headers!r}"
                )
            current = {
                "title": title,
                "line": lineno,
                "headers": headers,
                "rows": [],
            }
            tables.append(current)
            continue

        if current is None:
            fail(f"data.md linea {lineno}: hay una fila antes de su encabezado")
        current["rows"].append((lineno, cells))

    return tables


def farola_marker(label, name):
    """Color semantico de una farola valida; vacio para cualquier otra ubicacion."""
    if not FAROLA_LABEL_RE.fullmatch(label) or name != f"Farola {label}":
        return ""
    return FAROLA_COLORS[label[0]]


def is_public_legal_name(value):
    """Una razon social u organizacion puede mostrarse y buscarse publicamente."""
    return bool(value and PUBLIC_LEGAL_RE.search(value))


def choose_public_name(trade_name, legal_name, activity_type, fallback, parcel):
    """Elige el rotulo publico sin convertir un nombre personal en indice."""
    if fallback:
        return fallback
    if trade_name:
        return trade_name
    if is_public_legal_name(legal_name):
        return legal_name
    return activity_type or parcel


def group_search_terms(group, activity_type):
    terms = [group, activity_type]
    normalized_group = normalize(group)
    if normalized_group == "casetas":
        terms.extend(("caseta", "casetas", f"caseta {activity_type}"))
    elif normalized_group.startswith("casetas "):
        terms.extend(("caseta", "casetas", "caseta " + group.split(" ", 1)[1]))
    return " ".join(term for term in terms if term)


def navigation_group(group):
    """Código y nombre del menú; conserva grupos sintéticos en tests aislados."""
    return NAVIGATION_BY_SOURCE.get(normalize(group), (group, group))


def check_navigation_groups(locations):
    """El dataset real no puede publicar grupos fuera del menú operativo."""
    unknown = sorted(
        {
            location["group"]
            for location in locations
            if normalize(location["group"]) not in NAVIGATION_BY_SOURCE
        }
    )
    if unknown:
        fail("grupos sin código de menú: " + ", ".join(unknown))


def street_rows(tables):
    return [
        row
        for table in tables
        if table["headers"] == STREET_HEADERS
        for row in table["rows"]
    ]


def build_locations(tables):
    locations = []
    for table in tables:
        headers = table["headers"]
        if headers == STREET_HEADERS:
            continue

        for lineno, cells in table["rows"]:
            if len(cells) != len(headers):
                fail(
                    f"data.md linea {lineno}, seccion {table['title']!r}: se esperaban "
                    f"{len(headers)} columnas, hay {len(cells)}"
                )

            values = dict(zip(headers, cells))
            label = values["parcel"]
            group = values["group"]
            coords = values["coords"]
            if not label:
                fail(f"data.md linea {lineno}: parcela vacia")
            if not group:
                fail(f"data.md linea {lineno}, parcela {label!r}: grupo vacio")

            match = COORDS_RE.match(coords)
            if not match:
                fail(f"data.md linea {lineno}: coordenadas invalidas {coords!r}")
            lat, lon = match.group(1), match.group(2)
            menu_code, menu_name = navigation_group(group)

            if headers == BUSINESS_HEADERS:
                trade_name = values["trade_name"]
                legal_name = values["legal_name"]
                activity_type = values["activity_type"]
                fallback = ""
            else:
                trade_name = ""
                legal_name = ""
                activity_type = group
                fallback = values["name"]
                if (
                    normalize(group) == "puntos de referencia"
                    and normalize(fallback) == "farola"
                ):
                    activity_type = fallback
                    fallback = f"Farola {label}"

            name = choose_public_name(
                trade_name, legal_name, activity_type, fallback, label
            )
            personal_legal_name = bool(
                legal_name and not is_public_legal_name(legal_name)
            )
            public_legal_name = "" if personal_legal_name else legal_name
            street = ""

            searchable = " ".join(
                value
                for value in (
                    label,
                    name,
                    trade_name,
                    public_legal_name,
                    group_search_terms(group, activity_type),
                    menu_code,
                    menu_name,
                    street,
                )
                if value
            )

            locations.append(
                {
                    "id": f"loc-{len(locations):03d}",
                    "label": label,
                    "display": compact_label(label),
                    "marker": farola_marker(label, name),
                    "name": name,
                    "group": group,
                    "menuCode": menu_code,
                    "menuName": menu_name,
                    "tradeName": trade_name,
                    "legalName": legal_name,
                    "activityType": activity_type,
                    "isPersonalLegalName": personal_legal_name,
                    "street": street,
                    "lat": lat,
                    "lon": lon,
                    "search": normalize(searchable),
                    "flat": flatten(searchable),
                    "nameSearch": normalize(" ".join((name, trade_name))),
                }
            )
    return locations


def compact_label(label):
    """Muestra la primera parcela y conserva la etiqueta completa para buscar."""
    if "," in label:
        return label.split(",", 1)[0].strip()
    return label


def build_streets(rows, centro):
    """Calles con sus dos extremos. La seccion puede estar vacia."""
    streets, incompletas, avisos, vistas = [], [], [], set()

    for lineno, cells in rows:
        if len(cells) not in (3, 4):
            fail(f"data.md linea {lineno}: se esperaban 3 o 4 columnas, hay {len(cells)}")

        name, start, end = cells[0], cells[1], cells[2]
        waypoints = cells[3] if len(cells) == 4 else ""

        if name in vistas:
            fail(f"data.md linea {lineno}: la calle {name!r} esta repetida")
        vistas.add(name)

        if not start or not end:
            incompletas.append(name)
            continue

        lat1, lon1 = parse_point(start, f"linea {lineno}, inicio", centro)
        lat2, lon2 = parse_point(end, f"linea {lineno}, fin", centro)
        if (lat1, lon1) == (lat2, lon2):
            fail(f"data.md linea {lineno}: inicio y fin son el mismo punto")

        largo = haversine((float(lat1), float(lon1)), (float(lat2), float(lon2)))
        if not STREET_LENGTH_USUAL[0] <= largo <= STREET_LENGTH_USUAL[1]:
            avisos.append(f"{name}: {largo:.0f} m entre extremos, comprueba las coordenadas")

        puntos = []
        for i, punto in enumerate(p.strip() for p in waypoints.split(";") if p.strip()):
            plat, plon = parse_point(
                punto, f"linea {lineno}, punto intermedio {i + 1}", centro
            )
            puntos.append(f"{plat},{plon}")

        streets.append(
            {
                "name": name,
                "search": normalize(name),
                "flat": flatten(name),
                "start": f"{lat1},{lon1}",
                "end": f"{lat2},{lon2}",
                "waypoints": puntos,
                "count": 0,
                "length": round(largo),
            }
        )

    return streets, incompletas, avisos


def parse_point(value, donde, centro):
    match = COORDS_RE.match(value)
    if not match:
        fail(f"data.md {donde}: coordenadas invalidas {value!r}")
    d = haversine((float(match.group(1)), float(match.group(2))), centro)
    if d > FAR_AWAY_KM * 1000:
        fail(f"data.md {donde}: {value} esta a {d / 1000:.0f} km de las ubicaciones")
    return match.group(1), match.group(2)


# ── Validaciones ──────────────────────────────────────────────────────────────


def check_unique_coordinates(locations):
    coords = {(loc["lat"], loc["lon"]) for loc in locations}
    if len(coords) != len(locations):
        fail("hay coordenadas duplicadas")


def check_coherence(locations):
    """Coherencia geografica del listado consigo mismo.

    Detiene el proceso ante lo imposible. Con lo raro pero posible -- una
    ubicacion apartada del resto -- solo avisa: quien decide si es correcto es
    quien conoce el operativo.
    """
    centro = (
        statistics.median(float(loc["lat"]) for loc in locations),
        statistics.median(float(loc["lon"]) for loc in locations),
    )
    medidas = [
        (haversine((float(loc["lat"]), float(loc["lon"])), centro), loc)
        for loc in locations
    ]

    lejos = [(d, loc) for d, loc in medidas if d > FAR_AWAY_KM * 1000]
    if lejos:
        d, loc = max(lejos, key=lambda x: x[0])
        fail(
            f"{loc['name']!r} ({loc['lat']},{loc['lon']}) esta a {d / 1000:.0f} km "
            f"del resto del listado.\n"
            f"       Con {len(lejos)} punto(s) asi, lo mas probable es que haya una "
            "coordenada mal copiada."
        )

    mediana = statistics.median(d for d, _ in medidas) or 1.0
    raros = [
        (d, loc)
        for d, loc in medidas
        if d > OUTLIER_MIN_M and d > mediana * OUTLIER_FACTOR
    ]
    return centro, mediana, sorted(raros, key=lambda x: -x[0])


def ui_texts(template):
    """Texto que la aplicacion pinta: el de la plantilla fuera de <script> y
    <style>, mas las cadenas del objeto TEXT. Los atributos quedan fuera: un
    aria-label lo lee un lector de pantalla, no lo dibuja la tipografia."""
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", template, flags=re.S)
    html = re.sub(r"<[^>]*>", " ", html)

    bloque = UI_TEXT_RE.search(template)
    if not bloque:
        fail("la plantilla no declara el objeto TEXT con los textos visibles")

    return " ".join([html] + UI_STRING_RE.findall(bloque.group(1)))


def check_charset(locations, streets, template):
    """La tipografia va subconjuntada a los caracteres que la aplicacion
    necesita. Ante uno nuevo el navegador pintaria un cuadrado vacio, asi que
    el proceso se detiene antes de publicarlo."""
    if not CHARSET.exists():
        fail(f"falta {CHARSET.relative_to(ROOT)}, necesario para validar la fuente")

    cubiertos = set(CHARSET.read_text(encoding="utf-8"))

    usados = set(OPERATIVO) | set(ui_texts(template))
    for loc in locations:
        for key in (
            "display",
            "name",
            "group",
            "tradeName",
            "legalName",
            "activityType",
            "street",
        ):
            usados |= set(loc[key])
        usados |= set(loc["lat"]) | set(loc["lon"])
    for street in streets:
        usados |= set(street["name"])

    faltan = sorted(
        c for c in usados if c not in cubiertos and c.isprintable() and not c.isspace()
    )
    if faltan:
        detalle = ", ".join(f"{c!r} (U+{ord(c):04X})" for c in faltan)
        fail(
            "la fuente no cubre estos caracteres: "
            + detalle
            + "\n       Regenera el subconjunto con scripts/subset-fonts.py."
        )
    return len(usados)


# ── Ensamblado ────────────────────────────────────────────────────────────────


def project_minimap_point(lat, lon, calibration):
    """Pasa GPS a unidades del SVG; nunca modifica las coordenadas operativas."""
    origin_lat, origin_lon = calibration["origin_lat_lon"]
    lat_scale, lon_scale = calibration["metres_per_degree"]
    east = (float(lon) - origin_lon) * lon_scale
    north = (float(lat) - origin_lat) * lat_scale
    return [
        round(a * east + b * north + c, 3)
        for a, b, c in calibration["svg_units_per_local_metre"]
    ]


def minimap_viewbox(point, bounds):
    """Encuadre amplio con margen para el pin completo en los bordes del papel."""
    left, top, full_width, full_height = bounds
    width, height = min(150, full_width), min(120, full_height)
    padding = 12
    x = max(left - padding, min(point[0] - width / 2, left + full_width + padding - width))
    y = max(top - padding, min(point[1] - height / 2, top + full_height + padding - height))
    return [round(x, 3), round(y, 3), width, height]


def build_minimap(locations):
    """Un solo plano empotrado; posiciones y farolas derivadas de data.md."""
    if not MINIMAP.exists():
        fail(f"falta el plano {MINIMAP}")
    try:
        root = ET.parse(MINIMAP).getroot()
        metadata = root.find(".//*[@id='u24-georeference']")
        if metadata is None:
            raise ValueError("falta la calibración u24-georeference")
        calibration = json.loads(metadata.text)
        origin_lat, origin_lon = calibration["origin_lat_lon"]
        lat_scale, lon_scale = calibration["metres_per_degree"]
        (a, b, c), (d, e, f) = calibration["svg_units_per_local_metre"]
        bounds = [float(value) for value in root.attrib["viewBox"].split()]
        left, top, width, height = bounds
        numbers = [origin_lat, origin_lon, lat_scale, lon_scale, a, b, c, d, e, f, *bounds]
        if not all(math.isfinite(value) for value in numbers):
            raise ValueError("valores no finitos")
        if min(width, height, lat_scale, lon_scale) <= 0 or a * e == b * d:
            raise ValueError("dimensiones o transformación degeneradas")
    except (ET.ParseError, ValueError, KeyError, TypeError) as error:
        fail(f"plano o calibración inválidos en {MINIMAP.name}: {error}")

    for loc in locations:
        point = project_minimap_point(loc["lat"], loc["lon"], calibration)
        inside = left <= point[0] <= left + width and top <= point[1] <= top + height
        loc["mapPoint"] = point if inside else None
        loc["mapView"] = minimap_viewbox(point, bounds) if inside else None
        if not inside:
            print(f"    AVISO  {loc['label']}: fuera del plano, sin minimapa; conserva su enlace GPS")

    # Retira información del editor, no geometría. El SVG sigue aislado como imagen
    # para que sus IDs y estilos no interfieran con la interfaz ni con el emblema.
    svg_namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    for parent in root.iter():
        for child in list(parent):
            if not child.tag.startswith("{" + svg_namespace + "}") or child.tag == "{" + svg_namespace + "}metadata":
                parent.remove(child)
        for key in list(parent.attrib):
            if key.startswith("{") and not key.startswith(("{http://www.w3.org/1999/xlink}", "{http://www.w3.org/XML/1998/namespace}")):
                del parent.attrib[key]
        if parent.text and not parent.text.strip():
            parent.text = None
        parent.tail = None
    image = base64.b64encode(ET.tostring(root, encoding="utf-8")).decode("ascii")
    return {"image": "data:image/svg+xml;base64," + image, "bounds": bounds}


def read_logo():
    """Emblema empotrado en linea, para que index.html siga siendo
    autocontenido y no dependa de una peticion de red."""
    if not LOGO.exists():
        fail(f"falta el logotipo {LOGO.relative_to(ROOT)}")
    svg = LOGO.read_text(encoding="utf-8").strip()
    if not svg.startswith("<svg"):
        fail(f"{LOGO.relative_to(ROOT)} no empieza por <svg")
    return svg.replace(
        "<svg", '<svg class="mark" role="img" aria-label="Emblema U24"', 1
    )


def read_vendor():
    """Fuse.js, empotrada como el resto: la busqueda funciona sin cobertura."""
    if not VENDOR.exists():
        fail(
            f"falta {VENDOR.relative_to(ROOT)}\n"
            "       Descargalo con: npm pack fuse.js@7.5.0\n"
            "       y copia dist/fuse.basic.min.cjs a esa ruta."
        )
    code = VENDOR.read_text(encoding="utf-8").strip()
    if "module.exports" not in code:
        fail(
            f"{VENDOR.relative_to(ROOT)} no exporta como modulo CommonJS: "
            "la plantilla lo envuelve esperando module.exports"
        )
    return code


def read_fonts():
    fonts = {}
    for weight in FONT_WEIGHTS:
        path = FONTS / f"roboto-{weight}.woff2"
        if not path.exists():
            fail(f"falta la fuente {path.relative_to(ROOT)}")
        fonts[weight] = base64.b64encode(path.read_bytes()).decode("ascii")
    return fonts


def render_service_worker(html):
    """Incrusta una version determinista que cambia con cada app distinta."""
    marker = "__APP_VERSION__"
    source = SERVICE_WORKER.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    if marker not in source:
        fail(f"{SERVICE_WORKER.relative_to(ROOT)} no contiene el marcador {marker}")

    payload = "\0".join((html, manifest, source)).encode("utf-8")
    version = hashlib.sha256(payload).hexdigest()[:12]
    return source.replace(marker, version)


def assemble_dist(html):
    """Reconstruye dist/ desde cero, para que un archivo retirado del proyecto
    no siga publicandose por inercia."""
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "icons").mkdir(parents=True)

    OUTPUT.write_text(html, encoding="utf-8", newline="\n")
    (DIST / "sw.js").write_text(
        render_service_worker(html), encoding="utf-8", newline="\n"
    )

    for name in COPY_ROOT:
        origen = SRC / name
        if not origen.exists():
            fail(f"falta {origen.relative_to(ROOT)}")
        shutil.copy2(origen, DIST / name)

    for name in COPY_ICONS:
        origen = ICONS / name
        if not origen.exists():
            fail(f"falta {origen.relative_to(ROOT)}")
        shutil.copy2(origen, DIST / "icons" / name)


def check_dist_references():
    """Todo lo que dist/ referencia debe existir dentro de dist/."""
    referencias = set()
    for nombre in ("index.html", "manifest.webmanifest", "sw.js"):
        contenido = (DIST / nombre).read_text(encoding="utf-8")
        referencias |= set(re.findall(r'["\'](\./)?(icons/[\w.-]+)["\']', contenido))

    faltan = [ref for _, ref in referencias if not (DIST / ref).exists()]
    if faltan:
        fail("dist/ referencia archivos que no contiene: " + ", ".join(sorted(faltan)))
    return len(referencias)


def main():
    for path in (DATA, TEMPLATE):
        if not path.exists():
            fail(f"no se encuentra {path}")

    template = TEMPLATE.read_text(encoding="utf-8")
    tables = read_tables()

    locations = build_locations(tables)
    if not locations:
        fail("data.md no tiene ninguna fila de ubicacion")
    check_navigation_groups(locations)
    check_unique_coordinates(locations)
    centro, mediana, raros = check_coherence(locations)

    filas_calles = street_rows(tables)
    streets, sin_coords, avisos = build_streets(filas_calles, centro)

    n_chars = check_charset(locations, streets, template)
    minimap = build_minimap(locations)

    markers = ["__LOCATIONS__", "__STREETS__", "__MINIMAP__", "__OPERATIVO__", "__LOGO__", "__FUSE__"]
    markers += [f"__FONT_{w}__" for w in FONT_WEIGHTS]
    for marker in markers:
        if marker not in template:
            fail(f"la plantilla no contiene el marcador {marker}")

    vendor = read_vendor()
    html = template.replace(
        "__LOCATIONS__", json.dumps(locations, ensure_ascii=False, separators=(",", ":"))
    )
    html = html.replace(
        "__STREETS__", json.dumps(streets, ensure_ascii=False, separators=(",", ":"))
    )
    html = html.replace("__OPERATIVO__", OPERATIVO)
    html = html.replace("__MINIMAP__", json.dumps(minimap, separators=(",", ":")))
    html = html.replace("__LOGO__", read_logo())
    html = html.replace("__FUSE__", vendor)
    for weight, b64 in read_fonts().items():
        html = html.replace(f"__FONT_{weight}__", b64)

    restantes = [m for m in markers if m in html]
    if restantes:
        fail("marcadores sin sustituir: " + ", ".join(restantes))

    assemble_dist(html)
    n_refs = check_dist_references()

    report(
        locations,
        streets,
        centro,
        mediana,
        raros,
        avisos,
        sin_coords,
        vendor,
        n_chars,
        n_refs,
    )


def report(locations, streets, centro, mediana, raros, avisos, sin_coords,
           vendor, n_chars, n_refs):
    calles = sorted({loc["street"] for loc in locations if loc["street"]})
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    n_files = sum(1 for f in DIST.rglob("*") if f.is_file())
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()[:8]

    print(f"OK  {len(locations)} ubicaciones -> {OUTPUT.relative_to(ROOT)}")
    print(f"    {OPERATIVO} · {date.today():%d.%m.%y} · data.md {digest}")
    print(f"    {len(calles)} calles configuradas")
    print(f"    centro {centro[0]:.6f},{centro[1]:.6f} · mediana al centro {mediana:.0f} m")

    if streets:
        detalle = ", ".join(f"{s['name']} ({s['length']} m)" for s in streets)
        print(f"    trazado en {len(streets)}: {detalle}")

    if sin_coords:
        print(f"    AVISO  calles sin coordenadas, no se publican: {', '.join(sin_coords)}")
    for aviso in avisos:
        print(f"    AVISO  {aviso}")
    for d, loc in raros:
        print(
            f"    AVISO  {loc['name']} esta a {d:.0f} m del centro,"
            f" {d / mediana:.0f} veces la mediana. Comprueba que es correcto."
        )

    print(f"    fuente: {n_chars} caracteres, todos cubiertos")
    print(f"    Fuse.js {len(vendor) / 1024:.1f} KB · emblema {LOGO.stat().st_size / 1024:.1f} KB")
    print(f"    index.html {OUTPUT.stat().st_size / 1024:.1f} KB")
    print(f"    dist/: {n_files} archivos, {total / 1024:.1f} KB, {n_refs} referencias OK")


if __name__ == "__main__":
    main()
