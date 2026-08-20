# 04 — Convenciones

## Idioma

- **Documentación y textos de interfaz:** español de España.
- **Código:** identificadores, nombres de archivo, ramas y mensajes de commit en inglés.
- **Comentarios:** español, y solo cuando expliquen el *porqué*. Nada que repita lo que el
  código ya dice, ni anotaciones de lo que se probó o se descartó.

## Estructura

```
├── netlify.toml                 Despliegue. publish = "dist"
├── CLAUDE.md                    Instrucciones permanentes
├── data.md                      Fuente de verdad. Solo lectura.
│
├── dist/                        ← LO ÚNICO QUE SE PUBLICA. Generado.
│   ├── index.html
│   ├── manifest.webmanifest
│   ├── sw.js
│   └── icons/
│
├── src/
│   ├── template.html            Plantilla: HTML, CSS y JS
│   ├── manifest.webmanifest     Manifiesto PWA
│   ├── sw.js                    Service worker
│   ├── logo.svg                 Emblema optimizado que se empotra
│   ├── vendor/
│   │   └── fuse.basic.min.js    Fuse.js. Única dependencia externa.
│   └── fonts/
│       ├── roboto-*.woff2       Roboto subconjuntada. Derivado.
│       ├── charset.txt          Cobertura real, para validar la compilación
│       └── original/            Roboto completa, licencia y procedencia
│
├── icons/                       Biblioteca de iconos. Se publican siete.
├── logo/                        Originales de marca. No se sirven.
│
├── scripts/
│   ├── build.py                 data.md + src/ → dist/
│   └── subset-fonts.py          Regenera la fuente y charset.txt
└── docs/
```

### Solo se publica `dist/`

`netlify.toml` apunta a `dist/`, y `build.py` la reconstruye desde cero en cada ejecución:
borra la carpeta y copia únicamente los archivos declarados. Un archivo retirado del
proyecto deja de publicarse automáticamente, y uno nuevo no aparece en internet salvo que
se añada de forma explícita.

Esto mantiene fuera de la web los datos de origen, la documentación, las plantillas, los
scripts y los originales de marca. No contienen secretos, pero son material interno de un
dispositivo de emergencias.

`dist/` **se commitea**: no se ejecuta ninguna compilación en el despliegue, así que lo
publicado es lo que haya en el repositorio.

### Validaciones de la compilación

Detienen el proceso:

- Número de columnas y formato de coordenadas en ambas tablas de `data.md`.
- Coordenadas y números de ubicación sin duplicar.
- Coherencia geográfica del listado consigo mismo: ver `docs/02-datos.md`.
- Calles cuyo nombre no aparece en las ubicaciones, repetidas, o con ambos extremos en el
  mismo punto.
- **Cobertura tipográfica:** todo carácter que la aplicación vaya a pintar debe existir en
  `src/fonts/charset.txt`. Cubre los datos y los rótulos de la interfaz. Sin esto, un
  carácter nuevo se publicaría como un cuadrado vacío sin que nadie se enterase.
- Marcadores `__…__` sin sustituir en la salida.
- Referencias a iconos que no existan dentro de `dist/`.

Avisan sin detener el proceso: ubicaciones muy alejadas del grueso del listado, calles con
una longitud rara entre extremos, calles sin coordenadas y correcciones de errata que ya no
corresponden a ninguna fila.

Los atributos HTML quedan fuera de la validación tipográfica a propósito: un `aria-label` lo
lee un lector de pantalla, no lo dibuja la fuente.

### Nada atado a un lugar ni a un tamaño

Lo que dependa del operativo va en el bloque de configuración del principio de `build.py` y
en ningún otro sitio. Una validación que obligue a declarar dónde está el recinto, o cuántas
ubicaciones tiene, es una traba: las comprobaciones se escriben en relación a los propios
datos.

### Originales frente a derivados

`logo/` guarda los originales de marca tal como se entregaron y **no se modifican**. Lo que
consume la aplicación son derivados: `src/logo.svg` y los iconos de `icons/`. Si cambia la
marca, se sustituye el original y se regeneran los derivados; nunca al revés.

La misma regla rige la tipografía: los `.woff2` de `src/fonts/` derivan de los originales de
`src/fonts/original/`, que están en el repositorio para que regenerarlos no dependa de lo
que cada uno se descargue. `subset-fonts.py` comprueba la versión y se detiene si no es la
esperada, porque otra distinta cambiaría las métricas y el dibujo sin avisar. Detalle en
`src/fonts/original/origen.md`.

### Dependencias externas

Una sola: **Fuse.js**, en `src/vendor/`, con la versión fijada. La compilación no descarga
nada. Para actualizarla, `npm pack fuse.js@<version>` y copiar `dist/fuse.basic.min.cjs`
sobre `src/vendor/fuse.basic.min.js`; después hay que volver a pasar las pruebas, porque los
parámetros de coincidencia están calibrados sobre esa versión.

## Nomenclatura

| Elemento | Convención | Ejemplo |
| --- | --- | --- |
| Variables y funciones | `camelCase` | `normalizeSearchTerm` |
| Constantes de módulo | `SCREAMING_SNAKE_CASE` | `FUZZY_MAX_SCORE` |
| Archivos de código | `kebab-case` | `subset-fonts.py` |
| Campos de datos | `camelCase` | `lat`, `numbers`, `nameSearch` |

Vocabulario del dominio, de uso obligatorio:

| Concepto | Término en código |
| --- | --- |
| Punto del listado | `location` |
| Etiqueta visible del identificador | `label` / `display` |
| Números expandidos | `numbers` |
| Cadena normalizada de búsqueda | `search` / `flat` / `nameSearch` |
| Término tecleado | `query` |
| Coincidencia literal / aproximada | `exact` / `approx` |

## Estilo de código

- Sangría de 2 espacios, comillas simples, punto y coma al final de sentencia.
- Sin abstracciones anticipadas: solución directa, y refactor solo ante duplicado real.
- Nada de dependencias para lo que la plataforma ya resuelve.
- Los textos visibles se declaran en el objeto `TEXT` de la plantilla, no dispersos por el
  código: es lo que permite validar la cobertura tipográfica.

## Interfaz

El diseño visual es libre. Lo que sigue son las decisiones vigentes y el motivo por el que
se tomaron, para que quien las cambie sepa qué estaban resolviendo.

- **Mobile-first en vertical.** Se diseña para 360 px de ancho y se deja crecer. A partir de
  600 px el contenido se centra en una columna.
- **Tema oscuro.** El uso es nocturno y prolongado.
- **Jerarquía de la fila:** identificador (acento, ancho fijo, cifras tabulares), nombre
  (elemento principal), calle y coordenadas.
- **Contrastes medidos**, no estimados: texto principal 17,1:1; calle 7,1:1; rótulos
  secundarios 6,2:1; identificador 12,2:1.
- **Al mapa solo se llega por el botón de la derecha.** Filas de 72 px, botón de 64 px de
  ancho por toda la altura de la fila. Añadir otro elemento pulsable, o convertir la fila en
  enlace, exige acuerdo expreso del responsable.
- **Tocar las coordenadas las copia**, sin icono: la confirmación cambia el texto entero a
  «Copiado» durante 1,4 s. El relleno que le da 32 px de objetivo táctil se compensa con
  márgenes negativos, de modo que la caja ocupa en el flujo lo mismo que una línea de texto.
- **La fila de calle se ve igual que las demás.** La distinguen su segunda línea y el icono
  de recorrido del botón, no el color.
- **Sin líneas de separación.** Lo que agrupa las tres líneas de una ubicación es la
  proximidad, y por eso las distancias están calculadas, no elegidas a ojo:

  | Distancia | Valor |
  | --- | --- |
  | Hueco óptico entre las líneas de una misma ubicación | **6,5 px**, idéntico en los dos |
  | Hueco entre bloques de ubicaciones distintas | **13,75 px** |
  | Aire sobre y bajo el bloque, dentro de la fila | 6,875 px, simétrico |

  Cambiar una obliga a recalcular la otra: la proporción entre ambas es la que hace de
  separador.
- **Altura de línea en píxeles, no proporcional.** El hueco que se ve es el margen más el
  aire interno de cada caja, `(altura de línea − tamaño) / 2`. Con `line-height` proporcional
  ese aire varía con cada tamaño de letra y los huecos dejan de cuadrar.
- **Las coincidencias aproximadas van rotuladas y al final.**
- **Sin animaciones de transición** que retrasen la respuesta. El filtrado es instantáneo y
  debe parecerlo.
- El campo de búsqueda usa `inputmode` adecuado y no activa autocorrección ni
  autocapitalización, que estorban al teclear nombres propios y números.

## Accesibilidad

- HTML semántico: el listado es una lista, cada resultado es un enlace.
- Cada enlace tiene un nombre accesible que identifica la ubicación completa —nombre,
  identificador y calle—, no un genérico «navegar».
- El resultado del filtrado se anuncia mediante una región activa, indicando si lo que se
  ofrece son coincidencias aproximadas.
- Navegable por teclado de principio a fin, aunque el uso previsto sea táctil.
- Respeta `prefers-reduced-motion`.

## Rendimiento

- Sin peticiones de red en el arranque más allá del propio `index.html`.
- Todo empotrado: datos, motor de búsqueda, tipografía y emblema.
- Presupuesto orientativo: menos de 150 KB en la carga inicial, sin comprimir.

## Control de versiones

- Rama principal `main`, ramas cortas e integración rápida.
- Mensajes de commit en inglés, imperativo, con prefijo de tipo: `feat:`, `fix:`, `docs:`,
  `refactor:`, `chore:`, `test:`.
- Un commit, un cambio con sentido propio. No se mezclan formateo y lógica.
- `data.md` solo cambia en commits `chore(data):` dedicados, nunca junto a código.

## Pruebas

Cobertura selectiva: se prueba lo que puede fallar en silencio y llevar a la unidad a la
ubicación equivocada. Se ejecutan sobre `dist/index.html` ya construido, en un navegador
real sin interfaz, que es la única forma de comprobar a la vez el motor, el DOM y los
enlaces. Las del service worker necesitan además servirlo por HTTP.

Obligatorio:

- Conversión de `data.md`: recuento, validación de coordenadas, expansión de rangos,
  abreviatura de etiquetas y corrección de erratas.
- Normalización: tildes, mayúsculas, comillas tipográficas.
- Coincidencia exacta: `7` no devuelve la 74 por delante de la 7; `67` encuentra `66-67-68`;
  un número inexistente devuelve lista vacía y **no** ofrece aproximadas.
- Coincidencia aproximada: una errata de una letra encuentra su ubicación y aparece bajo el
  rótulo de aproximadas; una consulta literal con resultados no muestra ese rótulo; un
  término de menos de tres caracteres no dispara el motor.
- Búsqueda sin separadores: `A01` encuentra `A-01`, y `CT02` encuentra `CT-02`.
- Calles: aparecen como primera fila, sin identificador y con su recuento; sus URLs
  contrastadas contra `data.md`; no aparecen en consultas numéricas ni con dos caracteres.
- URLs y coordenadas mostradas: todas contrastadas una a una contra `data.md`.
- Copiado: el texto copiado es exactamente `lat, lon`, aparece la confirmación y vuelve sola.
- Invariantes de interfaz: la fila no es un enlace, no hay líneas de rejilla y la fila de
  calle no va en un color distinto.
- Service worker: con la red saturada la aplicación abre desde caché y no espera a la red;
  sin cobertura sigue abriendo; con red normal responde la red, no el límite.

La validación visual es manual, sobre dispositivo real, siguiendo la lista de
`docs/03-navegacion-maps.md`.

## Definición de terminado

1. Cumple los requisitos que le corresponden de `docs/01-producto.md`.
2. Pasa las pruebas obligatorias.
3. Se ha comprobado en un móvil real, no solo en el navegador de escritorio.
4. No ha ampliado el alcance ni ha añadido dependencias sin justificar.
