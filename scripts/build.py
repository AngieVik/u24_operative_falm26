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
FONTS = SRC / "fonts"
LOGO = SRC / "logo.svg"
CHARSET = FONTS / "charset.txt"
VENDOR = SRC / "vendor" / "fuse.basic.min.js"
ICONS = ROOT / "icons"

DIST = ROOT / "dist"
OUTPUT = DIST / "index.html"

FONT_WEIGHTS = (400, 500, 700)

# Se copian tal cual a dist/. Lo que no este aqui no se publica.
COPY_ROOT = ("manifest.webmanifest", "sw.js")
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

COORDS_RE = re.compile(r"^(-?\d+\.\d+),(-?\d+\.\d+)$")
NUMERIC_LABEL_RE = re.compile(r"^\d+(-\d+)*$")
FAROLA_LABEL_RE = re.compile(r"^[A-D]\d+$")
SECTION_RE = re.compile(r"^#{1,6}\s+(.*)$")

FAROLA_COLORS = {
    "A": "blue",
    "B": "green",
    "C": "red",
    "D": "yellow",
}

# Bloque de textos visibles de la plantilla y cadenas que contiene.
UI_TEXT_RE = re.compile(r"const TEXT = \{(.*?)\n\};", re.S)
UI_STRING_RE = re.compile(r"'((?:[^'\\]|\\.)*)'")

# Erratas del origen. data.md no se modifica: se corrigen aqui.
STREET_FIXES = {}


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


def read_sections():
    """Devuelve las filas de cada tabla, agrupadas por titulo de seccion.

    Las dos tablas tienen cuatro columnas, asi que lo que las distingue es el
    encabezado que las precede, no su forma.
    """
    secciones, actual = {}, None

    for lineno, raw in enumerate(DATA.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()

        titulo = SECTION_RE.match(line)
        if titulo:
            actual = normalize(titulo.group(1))
            secciones.setdefault(actual, [])
            continue

        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].startswith("---") or not any(cells):
            continue
        if actual is None:
            fail(f"data.md linea {lineno}: hay una tabla antes del primer titulo")

        secciones[actual].append((lineno, cells))

    return secciones


def drop_header(rows, first_column):
    """Descarta la fila de cabecera, reconocida por su primera celda."""
    if rows and normalize(rows[0][1][0]) == first_column:
        return rows[1:]
    return rows


def farola_marker(label, name):
    """Color semantico de una farola valida; vacio para cualquier otra ubicacion."""
    if not FAROLA_LABEL_RE.fullmatch(label) or name != f"Farola {label}":
        return ""
    return FAROLA_COLORS[label[0]]


def build_locations(rows):
    locations = []
    for index, (lineno, cells) in enumerate(rows):
        if len(cells) != 4:
            fail(f"data.md linea {lineno}: se esperaban 4 columnas, hay {len(cells)}")

        label, name, street, coords = cells
        if not label or not name:
            fail(f"data.md linea {lineno}: identificador o nombre vacio")

        match = COORDS_RE.match(coords)
        if not match:
            fail(f"data.md linea {lineno}: coordenadas invalidas {coords!r}")
        lat, lon = match.group(1), match.group(2)

        street = STREET_FIXES.get(street, street)

        # Los rangos son enumeraciones, no intervalos: se parten por "-".
        numbers = (
            [int(n) for n in label.split("-")] if NUMERIC_LABEL_RE.match(label) else []
        )

        locations.append(
            {
                "id": f"loc-{index:03d}",
                "label": label,
                "display": compact_label(label, numbers),
                "marker": farola_marker(label, name),
                "numbers": numbers,
                "name": name,
                "street": street,
                "lat": lat,
                "lon": lon,
                "search": normalize(f"{name} {label} {street}"),
                "flat": flatten(f"{name} {label} {street}"),
                "nameSearch": normalize(name),
            }
        )
    return locations


def compact_label(label, numbers):
    """Etiqueta abreviada para la columna de identificador, de ancho fijo.

    Las parcelas alfanumericas agrupadas por comas muestran solo la primera;
    la etiqueta completa se conserva aparte para la busqueda.

    A partir de tres numeros se abrevia como intervalo (180-181-…-186 ->
    180–186), y solo si son consecutivos: en caso contrario se muestra la
    etiqueta completa en lugar de mentir sobre los numeros que abarca.
    """
    if "," in label:
        return label.split(",", 1)[0].strip()
    if len(numbers) < 3:
        return label
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        return label
    return f"{numbers[0]}–{numbers[-1]}"


def build_streets(rows, locations, centro):
    """Calles con sus dos extremos. La seccion puede estar vacia."""
    conocidas = {}
    for loc in locations:
        conocidas[loc["street"]] = conocidas.get(loc["street"], 0) + 1

    streets, incompletas, avisos, vistas = [], [], [], set()

    for lineno, cells in rows:
        if len(cells) not in (3, 4):
            fail(f"data.md linea {lineno}: se esperaban 3 o 4 columnas, hay {len(cells)}")

        name, start, end = cells[0], cells[1], cells[2]
        waypoints = cells[3] if len(cells) == 4 else ""

        if name not in conocidas:
            fail(
                f"data.md linea {lineno}: la calle {name!r} no aparece en las ubicaciones.\n"
                "       El nombre debe coincidir exactamente."
            )
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
                "count": conocidas[name],
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


def check_unique(locations):
    coords = {(loc["lat"], loc["lon"]) for loc in locations}
    if len(coords) != len(locations):
        fail("hay coordenadas duplicadas")

    seen = {}
    for loc in locations:
        for n in loc["numbers"]:
            if n in seen:
                fail(f"el numero {n} aparece en {seen[n]!r} y en {loc['label']!r}")
            seen[n] = loc["label"]
    return seen


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
        usados |= set(loc["display"]) | set(loc["name"]) | set(loc["street"])
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


def assemble_dist(html):
    """Reconstruye dist/ desde cero, para que un archivo retirado del proyecto
    no siga publicandose por inercia."""
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "icons").mkdir(parents=True)

    OUTPUT.write_text(html, encoding="utf-8", newline="\n")

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
    secciones = read_sections()

    filas_ubicaciones = drop_header(secciones.get("ubicaciones", []), "ubication_number")
    if not filas_ubicaciones:
        fail("data.md no tiene ninguna fila bajo el titulo «Ubicaciones»")

    locations = build_locations(filas_ubicaciones)
    numbers = check_unique(locations)
    centro, mediana, raros = check_coherence(locations)

    filas_calles = drop_header(secciones.get("calles", []), "street")
    streets, sin_coords, avisos = build_streets(filas_calles, locations, centro)

    n_chars = check_charset(locations, streets, template)

    markers = ["__LOCATIONS__", "__STREETS__", "__OPERATIVO__", "__LOGO__", "__FUSE__"]
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
    html = html.replace("__LOGO__", read_logo())
    html = html.replace("__FUSE__", vendor)
    for weight, b64 in read_fonts().items():
        html = html.replace(f"__FONT_{weight}__", b64)

    restantes = [m for m in markers if m in html]
    if restantes:
        fail("marcadores sin sustituir: " + ", ".join(restantes))

    assemble_dist(html)
    n_refs = check_dist_references()

    report(locations, streets, numbers, centro, mediana, raros, avisos, sin_coords,
           filas_ubicaciones, vendor, n_chars, n_refs)


def report(locations, streets, numbers, centro, mediana, raros, avisos, sin_coords,
           filas, vendor, n_chars, n_refs):
    calles = sorted({loc["street"] for loc in locations})
    sin_numero = [loc["label"] for loc in locations if not loc["numbers"]]
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    n_files = sum(1 for f in DIST.rglob("*") if f.is_file())
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()[:8]

    print(f"OK  {len(locations)} ubicaciones -> {OUTPUT.relative_to(ROOT)}")
    print(f"    {OPERATIVO} · {date.today():%d.%m.%y} · data.md {digest}")
    print(f"    {len(numbers)} numeros, {len(calles)} calles, {len(sin_numero)} sin numero")
    print(f"    centro {centro[0]:.6f},{centro[1]:.6f} · mediana al centro {mediana:.0f} m")

    if streets:
        detalle = ", ".join(f"{s['name']} ({s['length']} m)" for s in streets)
        print(f"    trazado en {len(streets)}: {detalle}")

    # Una correccion de errata que ya no corresponde a ninguna fila es
    # configuracion muerta: no rompe nada, pero engana al que la lea.
    crudas = {cells[2] for _, cells in filas}
    for errata in STREET_FIXES:
        if errata not in crudas:
            print(f"    AVISO  STREET_FIXES corrige {errata!r}, que ya no esta en data.md")
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
