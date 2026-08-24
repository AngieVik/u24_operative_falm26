# 04 — Convenciones

## Idioma y nombres

- Documentación y textos de interfaz: español de España.
- Código: identificadores en inglés y comentarios en español cuando expliquen el porqué.
- Datos de origen: `snake_case`; modelo generado para JavaScript: `camelCase`.
- Términos de dominio: `location`, `parcel`, `tradeName`, `legalName`,
  `activityType`, `group`, `search`, `flat` y `nameSearch`.

## Estructura

```text
data.md                  Fuente de verdad editable
scripts/build.py         Parser, validación, privacidad y generación
src/template.html        Aplicación HTML/CSS/JS autocontenida
src/sw.js                Plantilla del service worker versionado
tests/test_build.py      Contratos del modelo, datos, UI y caché
dist/                    Único contenido publicado; generado
docs/                    Contratos y mantenimiento
```

`dist/` se reconstruye desde cero. El despliegue no compila: para publicar cambios deben
commitearse los artefactos generados junto con sus fuentes.

## Responsabilidades

### `data.md`

Conserva el dato literal: parcela, marca, titular, actividad y coordenadas. Los nombres
personales pertenecen únicamente a `legal_name`; no se duplican en `trade_name`.

### `scripts/build.py`

- reconoce tablas por encabezado exacto;
- deriva el grupo del título de sección;
- elige el nombre público;
- clasifica el titular como público o personal;
- construye índices sin nombres personales;
- valida coordenadas, caracteres y referencias;
- genera una versión determinista de caché para cada aplicación distinta.

### `src/template.html`

Renderiza solo `display`, `name` y el enlace de mapa en la fila cerrada. El detalle se
crea bajo demanda al pulsar el nombre; hasta entonces el titular no forma parte del
contenido visible ni accesible.

## Interfaz

- Mobile-first, tema oscuro y una columna máxima de 600 px.
- La parcela visible mantiene ancho fijo; una agrupación muestra solo la primera.
- El nombre público es un botón de detalle con foco visible.
- El icono derecho abre Google Maps y no alterna el detalle.
- Solo puede existir un detalle abierto.
- Pulsar el mismo nombre, otro nombre, fuera de la fila o cambiar la búsqueda cierra el
  detalle anterior.
- Escape cierra el detalle y devuelve el foco al nombre.
- El detalle muestra únicamente campos con valor y contiene el botón de coordenadas.
- La entrada usa una animación breve; `prefers-reduced-motion` la desactiva.
- Las farolas conservan la barra semántica de 4 x 40 px centrada en la cabecera.

## Accesibilidad y privacidad

- El listado usa `ul`/`li`; el detalle usa `dl`, `dt` y `dd`.
- El botón de nombre mantiene `aria-expanded` y `aria-controls`.
- El enlace de mapa se etiqueta solo con nombre público, parcela e indicación pública.
- Las etiquetas iniciales nunca concatenan `legalName`.
- La región activa anuncia resultados y copia de coordenadas.
- Toda la interacción funciona con teclado.

La privacidad se aplica al crear el modelo de búsqueda, no solo en la presentación. Un
nombre personal puede existir en el JSON de datos porque debe mostrarse al abrir el
detalle, pero no está en ningún índice ni en el texto inicial de la página.

## Validaciones del build

Detienen el proceso:

- encabezados o número de columnas no admitidos;
- parcela vacía o coordenadas inválidas/duplicadas;
- incoherencia geográfica extrema;
- caracteres visibles no cubiertos por la fuente;
- marcadores de plantilla sin sustituir;
- referencias de `dist/` ausentes.

Las pruebas protegen además las parcelas oficiales, los nombres públicos conocidos, la
exclusión de personas, las farolas, el contrato del desplegable y el cambio automático de
versión de caché.

## Dependencias y alcance

La app no añade dependencias de ejecución. Fuse.js, fuentes, emblema y datos se empotran
en `index.html`; el arranque y la búsqueda funcionan sin cobertura. Cualquier nueva
dependencia o cambio del flujo de mapa requiere aprobación explícita.
