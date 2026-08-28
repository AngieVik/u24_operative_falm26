# 02 — Datos

## Fuente de verdad

`data.md` es la única fuente editable. El build lee el archivo completo y reconoce cada
tabla por su encabezado literal. Puede haber varias tablas bajo un mismo título Markdown:
el título solo organiza el documento y no determina el grupo de una ubicación.

Se admiten exactamente estos esquemas:

```text
parcel | trade_name | legal_name | group | activity_type | coords
parcel | name | group | coords
street | map_path
```

Un encabezado distinto, una fila con otro número de columnas o un grupo desconocido
detienen el build e indican la línea afectada. Una fila formada únicamente por `-` es un
separador visual y se omite. La tabla de calles puede estar vacía.

## Columnas de ubicaciones

| Columna | Contenido |
| ------- | --------- |
| `parcel` | Parcela o conjunto completo de parcelas, separadas por comas. |
| `trade_name` | Marca o nombre comercial confirmado. Nunca se rellena con una persona. |
| `legal_name` | Titular o razón social oficial; puede ser una persona. |
| `name` | Nombre público de una ubicación general. |
| `group` | Grupo operativo explícito de la fila. |
| `activity_type` | Actividad concreta del negocio. |
| `coords` | Coordenadas `lat,lon`, con seis decimales y punto decimal. |

Los diez valores admitidos en `group`, con su código de menú, son:

| Código | Grupo |
| ------ | ----- |
| `A` | Atracciones |
| `H` | Habilidad |
| `C` | Casetas |
| `RT` | Restauración |
| `B` | Bebidas espirituosas |
| `R` | Repostería |
| `PI` | Puntos de interés |
| `AP` | Aseos públicos |
| `Acc` | Acceso |
| `F` | Puntos de referencia |

El orden de esta tabla es también el orden del menú. Las diferencias de mayúsculas y
tildes se normalizan para validar el valor, pero en `data.md` se conserva la escritura
canónica anterior. Se admite también `Accesos`, usado en el catálogo actual, como
equivalente de `Acceso`, sin crear otro grupo.

## Nombre público y privacidad

En una fila comercial, el nombre público se obtiene por este orden:

1. `trade_name`;
2. `legal_name`, solo si es inequívocamente una empresa u organización;
3. `activity_type`;
4. `parcel`.

Un `legal_name` personal se conserva para el detalle, pero no se añade a los índices de
búsqueda ni a la fila cerrada. La clasificación es conservadora: ante la duda, el titular
se trata como persona.

En el esquema general, `name` es el nombre público y `group` actúa también como actividad.
Para las filas del grupo `Puntos de Referencia` cuyo nombre es `Farola`, el build genera
`Farola <parcel>` y conserva el indicador de color asociado al prefijo.

## Parcelas agrupadas

La etiqueta completa se conserva en el modelo y en la búsqueda. La lista solo muestra la
primera: `CT-01, CT-02, CT-03` se presenta como `CT-01`, pero `CT03` sigue encontrando la
misma ubicación. No se deben dividir filas que representan un único negocio.

## Búsqueda

El índice literal incluye parcela completa, nombre público, marca, razón social pública,
actividad, grupo y código de menú. Se normalizan mayúsculas, diacríticos, comillas y
espacios. Un segundo índice elimina puntuación, de modo que `RT20` encuentra `RT-20`.

La coincidencia aproximada se limita a nombres y solo se usa cuando no hay coincidencias
literales. Los nombres personales quedan fuera de todos los índices antes de generar el
HTML.

## Calles

El esquema `street | map_path` define líneas orientativas en las unidades de dibujo
del `viewBox` de `src/minimap.svg`. No son coordenadas GPS, rutas navegables ni nuevas
ubicaciones. El esquema anterior de extremos GPS se ha retirado.

`map_path` empieza por `M x y` y admite las órdenes absolutas `L x y`,
`Q cx cy x y`, `C c1x c1y c2x c2y x y` y `Z`, siempre con sus parámetros completos,
separados por espacios y sin comas.
El build rechaza nombres vacíos o duplicados, órdenes incompletas, trazados sin longitud
y puntos fuera del plano. Una tabla vacía no añade el grupo Calles.

Las 13 calles solicitadas siguen el plano arquitectónico. Las referencias policiales
se mantienen como entradas buscables: Galán de Noche coincide con Paseo de Almería;
Acebo enlaza Ciudad Jardín y Nueva Andalucía con la rotonda exterior. La Rotonda del
Acebo está fuera de la puerta de Ciudad Jardín, según la captura del usuario del
28/08/2026, no en A7. Su contorno y el enlace exterior son esquemáticos.

El encuadre contiene toda la línea con margen y mantiene, como mínimo, el contexto de
una ficha de ubicación. En los bordes se desplaza el encuadre hacia el papel para
aprovechar el contexto; una calle larga se ve más alejada, nunca recortada. Solo la
calle seleccionada se resalta; las farolas siguen como referencias. Los nombres
completos siguen disponibles en el detalle accesible del mapa y en la búsqueda.

## Coordenadas y validación

- `data.md` mantiene seis decimales y latitud antes que longitud.
- El lector tolera espacios alrededor de la coma y el modelo los elimina.
- Coordenadas duplicadas, mal formadas o geográficamente imposibles detienen el build.
- Una ubicación anómalamente alejada genera un aviso para revisión humana.
- Las coordenadas no se deducen de un plano; se contrastan con la fuente operativa.

El detalle copia exactamente `lat,lon` y anuncia la confirmación mediante la región activa.
