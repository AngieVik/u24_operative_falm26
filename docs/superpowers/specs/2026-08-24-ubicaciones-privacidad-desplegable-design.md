# Ubicaciones: esquema enriquecido, privacidad de presentación y desplegable

Fecha: 2026-08-24

## Objetivo

Adaptar la aplicación al nuevo esquema de `data.md` para distinguir parcela,
nombre comercial, titular o razón social y tipo de actividad. La lista debe
seguir siendo rápida para el uso operativo, permitir búsquedas por parcela,
actividad y grupo, y evitar que los nombres de personas aparezcan o puedan
buscarse antes de que el usuario despliegue deliberadamente una ubicación.

La protección es de presentación, no criptográfica: el nombre personal forma
parte de la aplicación porque debe poder consultarse en el desplegable.

## Fuentes y límites

- `data.md` modificado por el usuario es la fuente principal y se preserva.
- `LISTADO PARCELAS OCUPADAS 2026.pdf` se usa para completar titulares,
  razones sociales y tipos de actividad.
- `plano-recinto-ferial-2026.pdf` se usa para contrastar parcelas y ubicación
  general. No sustituye coordenadas precisas por estimaciones visuales.
- No se inventan nombres comerciales.
- Las tablas de Puntos de Interés y Farolas mantienen el esquema reducido
  `parcel | name | type | coords`.
- No se realizan commit, push ni despliegue dentro de esta tarea.

## Esquemas admitidos

### Ubicaciones comerciales

Columnas:

- `parcel`
- `trade_name`
- `legal_name`
- `activity_type`
- `coords`

### Ubicaciones generales

Columnas:

- `parcel`
- `name`
- `type`
- `coords`

### Calles

Columnas:

- `street`
- `start`
- `end`
- `waypoints`

El parser reconoce las tablas por sus encabezados, no por una posición fija ni
por un único título de sección. El título Markdown de la sección se conserva
como grupo de búsqueda.

## Modelo normalizado

Cada ubicación generada contiene, según disponibilidad:

- `parcel`: etiqueta completa de parcela o parcelas;
- `display`: primera parcela que se presenta en la lista;
- `group`: título de la sección de origen;
- `tradeName`: nombre comercial;
- `legalName`: titular o razón social;
- `activityType`: actividad;
- `publicName`: texto que se muestra inicialmente;
- `isPersonalLegalName`: clasificación conservadora del nombre legal;
- `coords`, `lat` y `lon`;
- campos normalizados de búsqueda.

Los campos ausentes se representan como cadenas vacías, no como valores
inventados.

## Regla de nombre público

El nombre inicial se decide en este orden:

1. `trade_name` cuando exista;
2. `legal_name` únicamente cuando sea claramente una sociedad, empresa,
   asociación, administración u organización;
3. `activity_type`;
4. `name` para ubicaciones generales;
5. `parcel` como último recurso de seguridad.

La clasificación es deliberadamente conservadora. Si un `legal_name` puede
corresponder a una persona, se considera personal y no puede convertirse en
nombre público. En casos dudosos se muestra la actividad.

Ejemplos obligatorios:

- `I-24 | Rodeo infantil`
- `H-07 | Dardos`
- una caseta con `trade_name` muestra el nombre comercial;
- una ubicación sin nombre comercial cuyo titular sea una sociedad claramente
  identificada puede mostrar la razón social.

## Privacidad y búsqueda

El índice de búsqueda incluye:

- parcela completa y todas las parcelas de una agrupación;
- nombre comercial;
- razón social únicamente cuando no sea personal;
- tipo de actividad;
- grupo de la sección;
- nombre y tipo de las ubicaciones generales.

Un nombre legal clasificado como personal no se incorpora a ningún campo de
búsqueda, ni al texto plano auxiliar, ni a etiquetas accesibles de la fila.

Las casetas incorporan términos de categoría que permiten localizar al menos:

- `caseta`
- `casetas`
- `caseta tradicional`
- `caseta juvenil`

Los términos se derivan del grupo y de la actividad, sin modificar los datos
de origen.

## Lista y enlace al mapa

La vista inicial conserva esta estructura operativa:

`parcela | nombre público | botón de mapa`

- Las agrupaciones muestran solamente su primera parcela en la lista, aunque
  todas permanecen buscables.
- Cada ubicación cerrada ocupa una sola línea de 38 px de altura.
- El nombre público funciona como control de expansión.
- El botón de mapa sigue abriendo la navegación y no expande la ubicación.
- Los nombres personales no aparecen en el contenido inicial ni en atributos
  accesibles de la fila.

## Densidad y estilo visual

- La cabecera utiliza un logotipo de 34 px y un buscador de 34 px de altura.
- La lista es plana, sin tarjetas individuales ni huecos verticales entre
  resultados. Una línea neutra de 1 px separa las filas.
- La fila cerrada distribuye 56 px para la parcela, el espacio flexible para
  el nombre y 38 px para la acción de mapa.
- El botón visible de mapa mide 28 px y queda centrado dentro de su columna.
- El texto del nombre permanece en una línea y usa elipsis cuando no cabe.
- El amarillo corporativo `#FFC72C` se reserva para parcela, coordenadas y
  acciones. No se introduce naranja ni otro color de acento.
- Las farolas conservan su color semántico mediante una barra lateral corta,
  centrada y redondeada de 4 x 22 px, compatible con la nueva fila de 38 px.
- El detalle abierto queda integrado en el fondo de la lista, sin una tarjeta
  flotante ni bordes que produzcan cortes visuales.

## Desplegable inline

El detalle se abre dentro de la propia fila, inmediatamente bajo su cabecera.

- Pulsar el nombre abre el detalle.
- Pulsar de nuevo el mismo nombre lo cierra.
- Abrir otra ubicación cierra la anterior.
- Pulsar fuera de la ubicación abierta la cierra.
- Cambiar la consulta de búsqueda cierra el detalle activo.
- Escape cierra el detalle y devuelve el foco al control que lo abrió.
- Solo puede existir un detalle abierto a la vez.

El control usa `aria-expanded` y `aria-controls`. La transición es breve y se
desactiva con `prefers-reduced-motion`.

El detalle solo muestra campos con valor:

- parcela completa;
- nombre comercial;
- titular o razón social;
- tipo de actividad;
- grupo;
- indicación o dirección cuando exista;
- coordenadas.

El nombre legal personal se inserta en el DOM del detalle únicamente después
de la expansión.

## Coordenadas

Las coordenadas aparecen dentro del detalle como un control copiable.

- El texto visible contiene únicamente `latitud, longitud`; no muestra
  `Coordenadas`, `copiar`, iconos ni instrucciones auxiliares.
- Al pulsarlas se copia el texto `latitud,longitud` sin alteraciones.
- La copia no cambia el texto visible ni añade una confirmación dentro del
  detalle. El estado accesible puede anunciarse mediante la región de estado
  existente sin alterar la línea de coordenadas.
- El fallo de `navigator.clipboard` no rompe el desplegable; se utiliza el
  mecanismo alternativo compatible con la aplicación actual.

## Migración de datos

- Se conservan los `trade_name` ya identificados en `data.md`.
- Los titulares y razones sociales oficiales se incorporan a `legal_name`.
- Las actividades oficiales se incorporan o corrigen en `activity_type`.
- Los nombres personales no se trasladan a `trade_name`.
- Los nombres comerciales no confirmados permanecen vacíos.
- Las diferencias entre el listado oficial y el plano se documentan y no se
  resuelven inventando datos.

## Validación y errores

El build falla con un mensaje concreto cuando:

- una tabla de ubicaciones usa un esquema desconocido;
- falta parcela, coordenadas o toda posibilidad de nombre público;
- una coordenada no tiene formato o rango válido;
- una ubicación comercial carece simultáneamente de nombre comercial, nombre
  legal y actividad;
- quedan marcadores de plantilla sin sustituir.

Se mantienen los controles geográficos, de duplicados, caracteres y
referencias de `dist/` ya existentes.

## Pruebas y aceptación

La implementación sigue TDD. Deben existir pruebas que fallen antes del cambio
y pasen después para demostrar:

1. prioridad de `trade_name`;
2. uso de una empresa como respaldo público;
3. uso de `activity_type` cuando `legal_name` es personal;
4. exclusión total del nombre personal del índice de búsqueda;
5. búsqueda por grupo y actividad, incluidas casetas tradicionales y juveniles;
6. primera parcela visible y todas las agrupadas buscables;
7. compatibilidad de Puntos de Interés y Farolas con su esquema reducido;
8. expansión, contracción, sustitución y cierre exterior del detalle;
9. copia de coordenadas;
10. enlace independiente al mapa.

La verificación final incluye:

- pruebas unitarias completas;
- build de `dist/`;
- `git diff --check`;
- comprobación en navegador local, incluyendo interacción táctil equivalente,
  teclado, cierre exterior y búsqueda;
- revisión del diff para confirmar que no se modificaron archivos ajenos.
