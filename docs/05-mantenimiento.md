# 05 — Mantenimiento

Procedimiento para actualizar los datos y publicar. Escrito para hacerlo del tirón, sin
tener que leer el resto de la documentación.

## Actualizar el listado

### 1. Editar `data.md`

Las ubicaciones van bajo el título **Ubicaciones**, con sus cuatro columnas:
`ubication_number`, `name`, `adress`, `coords`. Las coordenadas se escriben `lat,lon`, sin
espacio y con punto decimal.

No hace falta que caigan en ningún sitio concreto: la compilación comprueba que son
coherentes entre sí, no contra un lugar declarado. Tampoco hay un número de filas esperado.

### 2. Revisar la sección **Calles**

Los nombres deben coincidir **exactamente** con los de la columna `adress`. Si el recinto no
tiene calles que trazar, la sección puede quedar sin filas: la aplicación funciona igual,
sin trazados.

### 3. Revisar `STREET_FIXES`

En `scripts/build.py`. Corrige erratas concretas del origen. Si alguna ya no aparece en
`data.md`, la compilación lo avisa y esa entrada se puede borrar.

### 4. Compilar

```
python3 scripts/build.py
```

Se detiene con un mensaje concreto ante cualquier dato inválido, indicando la línea.

### 5. Leer los avisos

La salida no solo dice `OK`. También señala, sin detenerse, lo que conviene revisar:

- Ubicaciones muy alejadas del grueso del listado. Puede ser correcto —un punto en otra
  parte de la ciudad— o una coordenada mal copiada. Lo decide quien conoce el operativo.
- Calles con una distancia rara entre extremos, o sin coordenadas.
- Correcciones de errata que ya no corresponden a ninguna fila.

### 6. Comprobar antes de publicar

- Abrir `dist/index.html` y buscar varias ubicaciones del listado nuevo.
- Comprobar en un **móvil real** que el enlace abre la ficha en el punto correcto,
  contrastando contra `data.md` y no de memoria.
- Si hay calles, comprobar que el trazado dibuja la calle y no un rodeo.

## Regenerar la tipografía

La fuente va subconjuntada a los caracteres que la aplicación necesita. Si el listado nuevo
trae uno que no cubre —un nombre con un símbolo que antes no se usaba—, la compilación se
detiene y lo indica.

```
pip install fonttools brotli
python3 scripts/subset-fonts.py
python3 scripts/build.py
```

El script toma los originales de `src/fonts/original/` y se detiene si la versión no es la
esperada. Ver `src/fonts/original/origen.md`.

## Cambiar el rótulo del operativo

`OPERATIVO`, en el bloque de configuración del principio de `scripts/build.py`. Es el texto
que aparece bajo el buscador.

## Cambiar la marca

El nombre de la unidad y su emblema aparecen en varios sitios, y ninguno detiene la
compilación: se publicaría con la marca antigua sin aviso.

| Dónde | Qué |
| --- | --- |
| `src/template.html` | `<title>`, `meta description`, `apple-mobile-web-app-title` |
| `src/manifest.webmanifest` | `name`, `short_name`, `description` |
| `scripts/build.py` | el `aria-label` del emblema, en `read_logo()` |
| `src/sw.js` | el nombre de la caché, `CACHE` |
| `src/logo.svg` | el emblema que se empotra |
| `icons/` | los siete iconos que se publican, y `logo/` como original |

## Publicar

`dist/` se commitea: no se ejecuta ninguna compilación en el despliegue, así que lo
publicado es lo que haya en el repositorio. Hay que commitear `dist/` junto con los cambios
que la generaron.
