# 02 — Datos

## Fuente de verdad

`data.md`, en la raíz del proyecto. Contiene dos tablas, cada una bajo su título de
sección: **Ubicaciones** y **Calles**. Las dos tienen cuatro columnas, así que lo que las
distingue al leerlas es el título que las precede, no su forma.

**`data.md` no se edita desde el código.** Todas las correcciones y transformaciones
descritas aquí se aplican durante la compilación, dejando el origen intacto. Si se detecta
un error real en los datos, se comunica al responsable; no se corrige por iniciativa
propia.

## Ubicaciones

Cuatro columnas: `ubication_number`, `name`, `adress`, `coords`.

| Campo | Tipo | Origen | Notas |
| --- | --- | --- | --- |
| `id` | texto | derivado | Identificador estable, del índice de fila: `loc-000`, `loc-001`… |
| `label` | texto | `ubication_number` | Etiqueta completa tal cual aparece: `CT-01, CT-02, CT-03, CT-04, CT-05`. |
| `display` | texto | derivado | Etiqueta visible abreviada: una agrupación por comas muestra solo su primera parcela. |
| `numbers` | lista de enteros | `ubication_number` | Números expandidos para la búsqueda. Vacía para etiquetas no numéricas. |
| `name` | texto | `name` | Nombre tal cual, con tildes y mayúsculas originales. |
| `street` | texto | `adress` | Calle, con las erratas corregidas. Puede quedar vacía mientras no exista una relación fiable. |
| `lat` / `lon` | texto | `coords` | Coordenadas literales, con sus decimales. Se muestran en pantalla. |
| `search` | texto | derivado | `name` + `label` + `street` normalizados. Filtrado literal. |
| `flat` | texto | derivado | Lo mismo, dejando solo letras y dígitos. |
| `nameSearch` | texto | derivado | Solo `name` normalizado. Filtrado aproximado. |

### Identificador estable

`label` no es único: puede haber varias filas `S/N`. El identificador se genera a partir
del índice de fila, y es estable mientras no cambie el orden de `data.md`, que se conserva
deliberadamente porque refleja el recorrido físico de cada calle.

### Parcelas agrupadas

Cuando una ubicación ocupa varias parcelas separadas por comas, `display` contiene solo
la primera para evitar que el identificador desborde la columna. `label`, `search` y `flat`
conservan la relación completa: `CT-01, CT-02, CT-03, CT-04, CT-05` se muestra como
`CT-01`, pero una búsqueda de `CT-05` sigue encontrando esa ubicación.

### Etiquetas no numéricas

Entradas como `S/N` o `169BIS` tienen `numbers` vacío: solo se encuentran escribiendo
texto. Se mantienen porque son puntos de referencia útiles para dar acceso a la unidad.

Si el nombre de una entrada es literalmente «Sin nombre conocido», se muestra tal cual: es
el dato de origen, no una ausencia. Su valor operativo está en la etiqueta y en las
coordenadas.

### Rangos de números

Una ubicación puede ocupar varias parcelas: `1-2`, `32-33-34`, `180-181-182-183-184-185-186`.
El rango se expande a números individuales para que buscar cualquiera de ellos la
encuentre, pero **se conserva la etiqueta completa original**, que es la que aparece
rotulada sobre el terreno.

Los rangos son **enumeraciones, no intervalos**: `1-2` significa «1 y 2», no «de la 1 a la
2». La expansión se hace partiendo por `-`, nunca generando el intervalo.

La etiqueta abreviada sí resume a partir de tres números, y solo si son consecutivos; en
caso contrario se muestra completa, para no mentir sobre los números que abarca.

### Corrección de erratas

Las erratas conocidas del origen se corrigen en el mapa `STREET_FIXES` de
`scripts/build.py`. Una corrección que ya no corresponda a ninguna fila se avisa durante la
compilación: no rompe nada, pero engaña a quien la lea.

## Calles

Cuatro columnas: `street`, `start`, `end`, `waypoints`.

```markdown
| street                       | start               | end                 | waypoints |
| ---------------------------- | ------------------- | ------------------- | --------- |
| C/ Paseo de la Feria | 36.832769,-2.431239 | 36.839517,-2.431191 |           |
```

| Columna | Obligatoria | Contenido |
| --- | --- | --- |
| `street` | Sí | Nombre **idéntico** al de la columna `adress` de las ubicaciones. Es lo que relaciona cada calle con sus puntos. |
| `start` / `end` | Sí | Coordenadas de cada extremo, `lat,lon`. |
| `waypoints` | No | Puntos intermedios, `lat,lon` separados por `;`. Solo hacen falta si Google traza el camino por otro sitio. |

La sección puede quedar vacía: sin ella la aplicación funciona igual, sin trazados. Las
filas sin coordenadas se omiten y se informan durante la compilación, para poder rellenar
la tabla por partes.

Los extremos definen el tramo que se dibuja. Si el vial arranca antes o sigue más allá, esa
parte no aparece; afinarlo es cambiar dos números y recompilar.

**Verificación pendiente en campo:** si Google Maps no tiene una calle registrada como
camino transitable, la ruta a pie no la seguirá y la trazará por fuera del recinto. Hay que
comprobarlo en un móvil real. Si el trazado se desvía, la columna `waypoints` lo corrige.

## Formato de las coordenadas

- Se conservan los decimales del origen, sin redondear.
- Se escriben `lat,lon`, sin espacio y con punto decimal, latitud primero.
- Nunca se reformatean por localización: el separador decimal es siempre el punto, aunque
  la interfaz esté en español. Por eso se guardan como texto y no como número.
- En pantalla se muestran con un espacio tras la coma, que es como se dictan.

## Índice de búsqueda

El filtrado no se hace sobre los campos originales, sino sobre campos precalculados:

1. Concatenar nombre, etiqueta y calle.
2. Pasar a minúsculas.
3. Descomponer en Unicode NFD y eliminar los diacríticos combinantes.
4. Normalizar comillas tipográficas y espacios múltiples.

El término tecleado se normaliza igual antes de comparar, también antes de entregárselo al
motor aproximado: Fuse.js no elimina tildes por su cuenta.

**Búsqueda sin espacios.** Además se precalcula `flat`: lo mismo dejando solo letras y
dígitos. El término se aplana igual antes de comparar. Es lo que permite que `A01`
encuentre `A-01` y que `CT02` encuentre `CT-02`. No sustituye a la
coincidencia aproximada: `flat` es exacto y resuelve el problema de la puntuación, no el de
las erratas.

## Reglas de coincidencia

El comportamiento depende de si el término es **solo dígitos** o no. Los dos modos son
excluyentes.

### Término numérico

1. Número **exacto** presente en `numbers`.
2. Número que **empieza por** el término: `7` → `70`, `71`, `73`… Necesario para que la
   lista se estreche mientras se teclea.
3. `nameSearch` que **contiene** el término, para nombres que llevan cifras.

Queda **prohibida la coincidencia por subcadena y la aproximada sobre el número**: escribir
`39` no puede devolver la `139`, ni `7` la `17`. Llevar la unidad a la ubicación equivocada
es el único fallo grave que esta aplicación puede cometer, y una subcadena lo provoca en
silencio. Un número inexistente devuelve **lista vacía**, que es información útil: ese punto
no existe.

Una consulta numérica nunca cae al motor aproximado ni devuelve calles.

### Término de texto

1. `search` que **empieza por** el término.
2. `search` que **contiene** el término.
3. `flat` que **contiene** el término aplanado, para los que no hayan entrado por 1 ni 2.
4. Si nada de lo anterior devuelve resultados: **coincidencia aproximada** sobre los
   nombres de ubicación y de calle.

Las calles se buscan por `flat`, con un mínimo de 3 caracteres, y se muestran delante.

### Coincidencia aproximada

Motor: Fuse.js. Parámetros en `src/template.html`:

| Parámetro | Valor | Motivo |
| --- | --- | --- |
| `keys` | `nameSearch` / `search` | Solo nombres. El identificador tiene su propia rama exacta y no entra aquí. |
| `threshold` | `0.4` | Tolera la errata de una o dos letras sin abrir la mano a cualquier cosa. |
| `ignoreLocation` | `true` | La errata puede estar en cualquier parte del nombre. |
| `minMatchCharLength` | `2` | Por encima, una errata parte la coincidencia en fragmentos cortos y el acierto se pierde. |
| `includeScore` | `true` | Necesario para ordenar por parecido y aplicar el corte. |

Y tres límites propios:

| Límite | Valor | Motivo |
| --- | --- | --- |
| Longitud mínima del término | 3 caracteres | Por debajo, cualquier nombre se parece a la consulta. |
| Corte de puntuación | `score <= 0.6` | Por encima ya no es una errata, es otra palabra. |
| Máximo de resultados | 8 | La lista aproximada se lee entera de un vistazo o no sirve. |

**Solo actúa como respaldo.** Mientras la búsqueda literal devuelva algo, la lista es la de
siempre: nada de ruido añadido a una consulta que ya funciona.

### Orden y presentación

Calles primero. Después, exacto → prefijo → contiene → aplanado, conservando dentro de cada
grupo el orden original de `data.md`. Las aproximadas van **siempre al final**, tras un
rótulo que las identifica como tales y ordenadas por parecido. La interfaz nunca presenta
una coincidencia aproximada como si fuera literal.

## Coherencia geográfica

Durante la compilación se comprueba que las coordenadas son consistentes **entre sí**, no
contra un lugar concreto: el proceso no sabe ni tiene por qué saber dónde está el recinto.

Se toma como centro la **mediana** de latitudes y longitudes —no la media, para que una
coordenada disparatada no arrastre el centro y siga destacando— y se mide la distancia de
cada punto a ese centro.

| Situación | Efecto |
| --- | --- |
| Un punto a más de **25 km** del centro | **Detiene la compilación.** A esa distancia ya no pertenece al mismo operativo. |
| Un punto a más de **500 m** y a más de **4 veces** la mediana | **Avisa** y continúa. Puede ser correcto. |

Un error de transcripción en la latitud desplaza el punto decenas de kilómetros y una
coordenada de otra provincia, cientos: ambos se detienen. Un desvío de pocos metros no lo
detecta ninguna comprobación automática, y por eso el destino se contrasta contra `data.md`
en las pruebas.

## Proceso de compilación

`scripts/build.py` lee `data.md`, aplica las normalizaciones descritas aquí y genera
`dist/`. Se detiene con un mensaje concreto ante cualquier dato inválido y avisa, sin
detenerse, de lo que conviene revisar pero no puede decidir por su cuenta.

Actualizar el listado: ver `docs/05-mantenimiento.md`.
