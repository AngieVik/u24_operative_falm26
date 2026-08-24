# 02 — Datos

## Fuente de verdad

`data.md`, en la raíz del proyecto, es la fuente editable. Cada tabla se interpreta por
sus encabezados literales y el grupo se toma del título Markdown que la precede. Una
sección declarada puede quedar sin filas.

El build admite exactamente tres esquemas:

```text
parcel | trade_name | legal_name | activity_type | coords
parcel | name | type | coords
street | start | end | waypoints
```

Un encabezado distinto detiene la compilación con la línea y la sección afectadas. No se
mezclan columnas de distintos esquemas.

## Ubicaciones comerciales

El esquema comercial se usa en Atracciones, Habilidad, Casetas, Restauración y
Repostería.

| Columna | Contenido |
| --- | --- |
| `parcel` | Parcela o conjunto de parcelas completo. |
| `trade_name` | Marca o nombre comercial confirmado. Nunca se rellena con un nombre personal. |
| `legal_name` | Titular o razón social oficial. Puede ser una persona. |
| `activity_type` | Actividad concreta o categoría operativa. |
| `coords` | Coordenadas `lat,lon`, sin espacio y con punto decimal. |

### Nombre público

La lista muestra un único nombre, calculado durante el build con esta prioridad:

1. `trade_name`;
2. `legal_name` cuando es inequívocamente una empresa u organización;
3. `activity_type`;
4. `parcel` como último recurso.

La detección de razón social es conservadora. Reconoce formas societarias y términos de
organización; cualquier titular ambiguo se trata como persona.

### Privacidad y búsqueda

Un `legal_name` personal:

- no se añade a `search`, `flat` ni `nameSearch`;
- no aparece en la fila cerrada ni en sus etiquetas accesibles;
- no se renderiza como contenido visible o accesible hasta que se abre el detalle;
- sí se conserva en el modelo para mostrarlo dentro del detalle.

El índice público se compone de parcela completa, nombre público, nombre comercial,
razón social pública, actividad y grupo. En Casetas también se añaden las expresiones
`caseta`, `casetas`, `caseta tradicional` o `caseta juvenil`, según corresponda.

## Ubicaciones generales

Puntos de Interés y Farolas usan `parcel | name | type | coords`. En este esquema `name`
es siempre el nombre público y `type` se publica como actividad/tipo. No hay
`trade_name` ni `legal_name` implícitos.

## Modelo generado

Cada ubicación que recibe la plantilla incluye:

| Campo | Contenido |
| --- | --- |
| `id` | Identificador de renderizado `loc-000`, `loc-001`… |
| `label` | `parcel` completa y sin abreviar. |
| `display` | Primera parcela visible cuando hay varias. |
| `marker` | Color semántico de farola o cadena vacía. |
| `numbers` | Números expandidos de etiquetas puramente numéricas. |
| `name` | Nombre público calculado. |
| `group` | Título de la sección de origen. |
| `tradeName` | Nombre comercial original. |
| `legalName` | Titular o razón social original, también si es personal. |
| `activityType` | Actividad o tipo. |
| `isPersonalLegalName` | Clasificación de privacidad aplicada por el build. |
| `street` | Indicación, actualmente vacía en los esquemas vigentes. |
| `lat` / `lon` | Coordenadas literales. |
| `search` / `flat` | Índices literales públicos. |
| `nameSearch` | Índice aproximado público. |

## Parcelas agrupadas

`label` conserva todas las parcelas y `display` solo muestra la primera. Por ejemplo,
`CT-25, CT-26, CT-27, CT-28` se presenta como `CT-25`; buscar cualquiera de las cuatro
parcelas encuentra la misma ubicación.

No se deben dividir filas agrupadas si corresponden al mismo negocio: se perdería la
relación entre parcelas y aparecerían duplicados visuales.

## Farolas

Las farolas mantienen el nombre literal `Farola <código>`. El prefijo determina la barra
lateral: A azul, B verde, C rojo y D amarillo. El indicador es visual; no modifica la
parcela ni la búsqueda.

## Calles

El esquema `street | start | end | waypoints` define recorridos. La sección puede quedar
vacía. `start` y `end` son `lat,lon`; `waypoints` admite puntos intermedios separados por
`;`.

Cuando existan calles, su nombre debe coincidir con la indicación usada por las
ubicaciones relacionadas. Las filas incompletas se omiten con aviso.

## Normalización de búsqueda

`search` pasa a minúsculas, elimina diacríticos, normaliza comillas y colapsa espacios.
`flat` elimina además todo lo que no sea letra o dígito, por lo que `CT28` encuentra
`CT-28`. La coincidencia aproximada de Fuse.js solo usa `nameSearch` y solo entra cuando
no existe coincidencia literal.

Los nombres personales quedan fuera de los tres campos antes de serializar el modelo de
búsqueda. No se intenta ocultarlos con CSS ni filtrarlos después en el navegador.

## Coordenadas y validación

- Se conservan todos los decimales del origen.
- El formato es `lat,lon`, latitud primero.
- Coordenadas duplicadas o mal formadas detienen el build.
- Un punto a más de 25 km del centro mediano detiene el build.
- Un punto a más de 500 m y cuatro veces la mediana genera un aviso.
- El plano sirve para contraste general; no se derivan coordenadas precisas de su dibujo.

El detalle muestra las coordenadas y permite copiarlas. El botón copia exactamente
`lat,lon` y anuncia la confirmación mediante la región activa.

## Fuentes oficiales

El listado municipal aporta titular, actividad y parcela. `data.md` conserva los nombres
comerciales confirmados y las coordenadas operativas. Si una fila no aparece en el listado
vigente, no se inventa titular: se mantiene la marca o actividad disponible y se registra
la ausencia durante la revisión.

Actualizar el listado: ver `docs/05-mantenimiento.md`.
