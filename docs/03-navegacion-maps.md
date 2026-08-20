# 03 — Enlaces a Google Maps

Basado en **Maps URLs**, la API de URLs públicas de Google Maps: no requiere clave, no
tiene cuota y la misma URL funciona en Android, iOS y navegador de escritorio.

Referencia: <https://developers.google.com/maps/documentation/urls/get-started>

## Ficha de una ubicación

```
https://www.google.com/maps/search/?api=1&query={LAT},{LON}
```

| Parámetro | Valor | Motivo |
| --- | --- | --- |
| `api` | `1` | Obligatorio. Identifica la versión de Maps URLs; sin él la URL no es estable. |
| `query` | `{LAT},{LON}` | Coordenadas exactas del listado. **Nunca el nombre de la ubicación.** |

No se añade nada más. En particular **no se usa `query_place_id`**, que haría falta para
que la ficha mostrara un nombre propio: exigiría resolver cada ubicación contra la base de
datos de lugares de Google, justo lo que el principio 4 prohíbe.

Se abre un mapa centrado en el punto, con el marcador sobre las coordenadas exactas y la
tarjeta inferior de Google Maps, desde la que se accede a «Cómo llegar» e «Iniciar».

## Trazado de una calle

Maps URLs **no permite dibujar**: no hay parámetro para líneas, trazados ni polilíneas. Los
únicos admitidos son `query` para buscar y `origin`, `destination`, `waypoints`,
`travelmode` y `avoid` para indicaciones.

El recorrido de una calle se consigue pidiendo una ruta entre sus dos extremos: el camino
que Google dibuja **es** la calle.

```
https://www.google.com/maps/dir/?api=1&travelmode=walking&origin={LAT1},{LON1}&destination={LAT2},{LON2}
```

Con puntos intermedios, cuando hacen falta: `&waypoints={LAT},{LON}|{LAT},{LON}`.

| Parámetro | Valor | Motivo |
| --- | --- | --- |
| `travelmode` | `walking` | **A pie, no en coche.** El recinto es peatonal: en coche Google daría un rodeo por el exterior, o no encontraría ruta. A pie el trazado sigue la calle y no respeta sentidos únicos. |
| `waypoints` | Opcional | Fuerza el trazado por donde debe ir si Google elige otro camino entre los extremos. |
| `dir_action` | No se usa | Lanzaría la navegación paso a paso; aquí solo se quiere ver el trazado. |

Diferencias con el enlace de una ubicación: abre la pantalla de indicaciones y no la ficha
de lugar, y dibuja un recorrido entre dos puntos, no un resaltado de la calle. Depende
además de que Google conozca el vial.

En la aplicación, una calle aparece **escribiendo su nombre** en el buscador, como primera
fila. No aparece con el campo vacío ni en las consultas numéricas.

## Codificación

- La coma entre latitud y longitud **no se codifica**: se envía literal.
- El signo menos de la longitud se envía literal.
- Sin espacios ni separadores de miles.

## Comportamiento por plataforma

| Plataforma | Resultado esperado |
| --- | --- |
| Android con Google Maps instalado | Se abre la aplicación nativa sobre el punto. |
| Android sin Google Maps | Se abre Maps en el navegador. |
| iOS con Google Maps instalado | Se abre la aplicación nativa de Google Maps. |
| iOS sin Google Maps | Se abre Maps en Safari. |
| Escritorio | Se abre Google Maps web centrado en el punto. |

La misma URL cubre los cinco casos. **No se implementa detección de sistema operativo ni
esquemas propietarios** (`comgooglemaps://`, `maps://`, `geo:`): añaden complejidad,
degradan cuando la aplicación no está instalada y obligarían a mantener dos caminos.

## Apertura desde la aplicación

- Enlace HTML real, no un manejador de clic con `window.open()`. Se comporta mejor en las
  capas de aplicación web instalada y permite pulsación larga para copiar o abrir en otra
  aplicación.
- `target="_blank"` con `rel="noopener noreferrer"`: la aplicación queda abierta detrás,
  lista para el siguiente aviso, sin volver a cargar.
- **Solo el botón de la derecha es el enlace. La fila no lo es.**

## Verificación antes de desplegar

Sobre dispositivo real, no solo en emulador:

1. Abrir tres ubicaciones distintas en Android con Google Maps instalado y confirmar que
   el marcador cae sobre el punto correcto, contrastando con `data.md`.
2. Repetir en iPhone, con y sin la aplicación de Google Maps instalada.
3. Comprobar el caso de longitud negativa; un fallo de codificación se manifestaría en
   todas las ubicaciones a la vez.
4. Abrir una calle y comprobar que el trazado sigue la calle y no un rodeo por fuera.
5. Desde una ficha, pulsar «Cómo llegar» y ver en qué modo de transporte queda la ruta.

Estas comprobaciones no se dan por superadas si no se han ejecutado.
