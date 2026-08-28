# 04 — Convenciones

## Idioma y nombres

- Documentación e interfaz: español de España.
- Código: identificadores en inglés; comentarios en español cuando expliquen una decisión.
- Datos editables: `snake_case`; modelo JavaScript generado: `camelCase`.
- Términos principales: `location`, `parcel`, `tradeName`, `legalName`,
  `activityType`, `group`, `search`, `flat` y `nameSearch`.

## Estructura y responsabilidades

```text
data.md                  Fuente de verdad editable
scripts/build.py         Lectura, validación, privacidad y generación
src/template.html        Aplicación HTML/CSS/JS autocontenida
src/minimap.svg          Plano original y calibración para orientación
src/sw.js                Plantilla del service worker
tests/test_build.py      Contratos de datos, modelo, interfaz y caché
dist/                    Artefactos generados que se publican
docs/                    Producto, contratos y mantenimiento
```

- `data.md` conserva parcelas, nombres, grupos, actividades y coordenadas.
- `scripts/build.py` reconoce los tres esquemas exactos, lee todas las tablas, valida los
  diez grupos y genera los índices sin nombres personales.
- `src/template.html` renderiza la interfaz y nunca se rellena manualmente con datos.
- `src/minimap.svg` conserva la geometría del plano y su transformación GPS → SVG.
  No es otro catálogo: los puntos y las farolas se calculan desde `data.md` en el build.
- `dist/` se regenera; sus archivos no son fuente editable.

## Interfaz

- Mobile-first, tema oscuro y una columna máxima de 600 px.
- La cabecera queda fuera del área desplazable; solo `main` desplaza la lista.
- Con el buscador vacío aparecen los diez grupos de ubicaciones, seguidos de `CL · Calles`
  cuando hay trazados. La flecha de la cabecera vuelve desde un grupo o búsqueda al menú,
  borra la consulta, cierra el detalle y reinicia el desplazamiento de la lista.
- La fila de grupo mantiene las mismas columnas que una ubicación y usa un pin gris.
- La parcela visible ocupa una columna fija; las parcelas agrupadas muestran la primera.
- El nombre abre el detalle y el icono derecho abre Google Maps.
- Solo puede haber un detalle abierto. Se cierra al repetir el nombre, abrir otro, pulsar
  fuera, cambiar la búsqueda o pulsar Escape.
- El detalle muestra únicamente campos con valor e incluye las coordenadas copiables.
- Debajo aparece el minimapa estático sobre fondo claro, con un pin de destino y las
  farolas. No captura gestos ni añade controles; Google Maps conserva su botón separado.
- Las calles no son ubicaciones: su detalle solo muestra el plano con la línea resaltada,
  sin pin de destino, coordenadas ni enlace. La columna derecha es decorativa y gris.
  Sus trazados viven exclusivamente en `data.md`, en unidades SVG, sin modificar el plano.
- Las farolas conservan su barra semántica lateral.

Las medidas y estilos vigentes están en `src/template.html`; la documentación no debe
duplicarlos como constantes normativas porque se desactualizan con facilidad.

## Accesibilidad y privacidad

- El listado usa `ul`/`li` y el detalle `dl`/`dt`/`dd`.
- El botón del nombre mantiene `aria-expanded` y `aria-controls`.
- El enlace de mapa se etiqueta con información pública.
- La región activa anuncia resultados y la copia de coordenadas.
- Los nombres personales pueden existir en el JSON para el detalle, pero no en el texto
  inicial, las etiquetas accesibles de la fila ni los índices de búsqueda.

## Validaciones y dependencias

Detienen el build los esquemas desconocidos, filas incompletas, grupos no catalogados,
coordenadas inválidas o duplicadas, incoherencia geográfica extrema, caracteres sin
cobertura, marcadores de plantilla pendientes y referencias ausentes en `dist/`.

La aplicación no añade dependencias de ejecución remotas: Fuse.js, fuentes, emblema,
plano y datos se empotran en `index.html`. El plano se incluye una sola vez y solo se
crea la vista del detalle abierto. Cualquier dependencia nueva o cambio del flujo de
mapa requiere aprobación explícita.
