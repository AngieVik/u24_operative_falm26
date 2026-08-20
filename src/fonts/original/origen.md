# Roboto original — procedencia

Estos son los archivos **originales** de los que derivan los `.woff2` subconjuntados de
`src/fonts/`. No se modifican. Están en el repositorio a propósito: sin ellos no se puede
regenerar el subconjunto, y usar una descarga cualquiera de Roboto cambiaría el aspecto de
la aplicación sin avisar.

| Dato | Valor |
| --- | --- |
| Familia | Roboto |
| Versión | **2.138** (2017) — la clásica estática, no la variable 3.x |
| `fontRevision` | 2.13800048828125 |
| `unitsPerEm` | 2048 |
| Origen | <https://github.com/googlefonts/roboto/releases/download/v2.138/roboto-unhinted.zip> |
| Licencia | Apache 2.0 — texto completo en `LICENSE.txt` |

Pesos conservados: los tres que usa la aplicación.

| Archivo | SHA-256 |
| --- | --- |
| `Roboto-Regular.ttf` | `f3edb8058e523f5612bfd99d0745e661568ad85e1b6217bc62f786fabae624c6` |
| `Roboto-Medium.ttf` | `b398bb9c791ddb08f1063d9c874f98e8aadb99132043b2d272a9276cf90c465a` |
| `Roboto-Bold.ttf` | `2ca2b3bfc2c2d43fa8f2b7227982d735fd537ecf113a4c56cc2d292bcc3106c8` |

## Por qué esta versión y no otra

Google Fonts sirve hoy Roboto 3.x en formato variable, con dibujo y métricas distintos.
Regenerar el subconjunto desde ahí cambiaría el interlineado y el ancho de los nombres sin
que nadie lo notase hasta verlo en un móvil. Por eso el original vive en el repositorio y
el script comprueba la versión antes de usarlo.

## Cómo regenerar

```
pip install fonttools brotli
python3 scripts/subset-fonts.py
```

El script toma estos archivos por defecto, comprueba que siguen siendo la versión 2.138 y
aborta si no lo son. Después hay que ejecutar `python3 scripts/build.py`.
