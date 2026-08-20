#!/usr/bin/env python3
"""Regenera src/fonts/ : Roboto subconjuntada a los caracteres que la app usa.

Uso:  pip install fonttools brotli
      python3 scripts/subset-fonts.py [/ruta/a/otros/TTF]

Sin argumentos toma los originales de src/fonts/original/, que viven en el
repositorio para que esto no dependa de lo que cada uno tenga en su maquina.
Ver src/fonts/original/origen.md.

Hay que ejecutarlo cuando `scripts/build.py` avisa de que la fuente no cubre
algun caracter de los datos o de los rotulos.

Produce:
  src/fonts/roboto-{400,500,700}.woff2
  src/fonts/charset.txt   <- lo que build.py usa para validar

La alternativa a subconjuntar seria empotrar Roboto completa (~350 KB por peso)
o servirla desde Google Fonts. Lo primero dispara el arranque; lo segundo rompe
el funcionamiento sin cobertura, que es requisito.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data.md"
OUT = ROOT / "src" / "fonts"
ORIGINAL = OUT / "original"
TEMPLATE = ROOT / "src" / "template.html"

WEIGHTS = {400: "Regular", 500: "Medium", 700: "Bold"}

# Version de los originales conservados en src/fonts/original/. Con otra, el
# dibujo y las metricas cambian y la aplicacion se ve distinta sin avisar.
EXPECTED_REVISION = 2.138

# Todo lo que la interfaz puede pintar y no sale de data.md: rotulos, mensajes,
# y el repertorio latino basico por seguridad ante nombres futuros.
UI_TEXT = (
    "ubicacion ubicaciones resultados quiza buscabas Copiado "
    "Sin coincidencias Comprueba el numero o escribe menos letras del nombre "
    "Nombre o numero Recorrido de la calle "
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "áéíóúüñçÁÉÍÓÚÜÑÇàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛ"
    # La elipsis la dibuja el navegador al truncar un nombre largo
    # (text-overflow), no aparece en ningun texto del codigo.
    "¡!¿?.,;:·-–—…_/()[]{}'\"“”‘’&+*%#@=<>|~^ "
)


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def check_revision(path):
    from fontTools.ttLib import TTFont

    revision = round(TTFont(path)["head"].fontRevision, 3)
    if revision != EXPECTED_REVISION:
        fail(
            f"{path.name} es la version {revision}, no la {EXPECTED_REVISION}.\n"
            "       Regenerar con otra version cambia las metricas y el dibujo.\n"
            "       Ver src/fonts/original/origen.md."
        )


def data_chars():
    """Todas las celdas de data.md se pintan en pantalla, en las dos tablas."""
    chars = set()
    for line in DATA.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4 or cells[0].startswith("---"):
            continue
        for cell in cells:
            chars |= set(cell)
    return chars


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGINAL
    if not src.is_dir():
        fail(f"no se encuentra el directorio de originales {src}")

    chars = set(UI_TEXT) | data_chars()
    chars = {c for c in chars if c.isprintable()}
    text = "".join(sorted(chars))

    print(f"Originales: {src}")
    for weight, name in WEIGHTS.items():
        origen = src / f"Roboto-{name}.ttf"
        if not origen.exists():
            fail(f"no se encuentra {origen}")
        check_revision(origen)

        destino = OUT / f"roboto-{weight}.woff2"
        subprocess.run(
            [
                sys.executable, "-m", "fontTools.subset", str(origen),
                f"--text={text}", "--flavor=woff2",
                "--layout-features=kern,liga", "--no-hinting", "--desubroutinize",
                f"--output-file={destino}",
            ],
            check=True,
        )
        print(f"  {destino.relative_to(ROOT)}  {destino.stat().st_size / 1024:.1f} KB")

    # charset.txt = interseccion real de los tres pesos, leida de los woff2.
    from fontTools.ttLib import TTFont

    cobertura = None
    for weight in WEIGHTS:
        font = TTFont(OUT / f"roboto-{weight}.woff2")
        puntos = set()
        for table in font["cmap"].tables:
            puntos |= set(table.cmap.keys())
        cobertura = puntos if cobertura is None else (cobertura & puntos)

    charset = "".join(sorted(chr(c) for c in cobertura if chr(c).isprintable()))
    (OUT / "charset.txt").write_text(charset, encoding="utf-8")
    print(f"  src/fonts/charset.txt  {len(charset)} caracteres")

    faltan = sorted(c for c in chars if c not in charset and not c.isspace())
    if faltan:
        fail(
            "el subconjunto no ha cubierto: "
            + ", ".join(f"{c!r} (U+{ord(c):04X})" for c in faltan)
            + "\n       Roboto 2.138 no tiene glifo para esos caracteres."
        )

    print("\nAhora ejecuta: python3 scripts/build.py")


if __name__ == "__main__":
    main()
