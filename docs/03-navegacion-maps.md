# 03 — Enlaces a Google Maps

Basado en **Maps URLs**, la API de URLs públicas de Google Maps: no requiere clave, no tiene cuota y la misma URL funciona en Android, iOS y navegador de escritorio.

Referencia: <https://developers.google.com/maps/documentation/urls/get-started>

## Ficha de una ubicación

```
https://www.google.com/maps/search/?api=1&query={LAT},{LON}
```

| Parámetro | Valor         | Motivo                                                                        |
| --------- | ------------- | ----------------------------------------------------------------------------- |
| `api`     | `1`           | Obligatorio. Identifica la versión de Maps URLs; sin él la URL no es estable. |
| `query`   | `{LAT},{LON}` | Coordenadas exactas del listado. **Nunca el nombre de la ubicación.**         |

No se añade nada más. En particular **no se usa `query_place_id`**, que haría falta para que la ficha mostrara un nombre propio: exigiría resolver cada ubicación contra la base de datos de lugares de Google, justo lo que el principio 4 prohíbe.

Se abre un mapa centrado en el punto, con el marcador sobre las coordenadas exactas y la tarjeta inferior de Google Maps, desde la que se accede a «Cómo llegar» e «Iniciar».

## Calles: solo previsualización local

Las calles no abren Google Maps ni solicitan rutas a pie. Se consultan desde el grupo
Calles o escribiendo su nombre. Pulsar el nombre despliega el plano orientativo con
una línea SVG resaltada y las farolas como referencias, sin pin de destino.

La columna derecha es un icono de trazado gris decorativo: no es un enlace. El detalle
no contiene coordenadas copiables. Los nombres policiales Galán de Noche, Acebo y
Rotonda del Acebo se resuelven localmente con el mismo catálogo de trazados.

Esta distinción evita que una línea dibujada para orientación se presente como una
ubicación GPS o como un itinerario calculado por Google. Las fichas de negocios y
farolas conservan su botón de Maps con sus coordenadas originales.

## Codificación

- La coma entre latitud y longitud **no se codifica**: se envía literal.
- El signo menos de la longitud se envía literal.
- Sin espacios ni separadores de miles.

## Comportamiento por plataforma

| Plataforma                        | Resultado esperado                            |
| --------------------------------- | --------------------------------------------- |
| Android con Google Maps instalado | Se abre la aplicación nativa sobre el punto.  |
| Android sin Google Maps           | Se abre Maps en el navegador.                 |
| iOS con Google Maps instalado     | Se abre la aplicación nativa de Google Maps.  |
| iOS sin Google Maps               | Se abre Maps en Safari.                       |
| Escritorio                        | Se abre Google Maps web centrado en el punto. |

La misma URL cubre los cinco casos. **No se implementa detección de sistema operativo ni esquemas propietarios** (`comgooglemaps://`, `maps://`, `geo:`): añaden complejidad, degradan cuando la aplicación no está instalada y obligarían a mantener dos caminos.

## Apertura desde la aplicación

- Enlace HTML real, no un manejador de clic con `window.open()`. Se comporta mejor en las capas de aplicación web instalada y permite pulsación larga para copiar o abrir en otra aplicación.
- `target="_blank"` con `rel="noopener noreferrer"`: la aplicación queda abierta detrás, lista para el siguiente aviso, sin volver a cargar.
- **Solo el botón de la derecha es el enlace. La fila no lo es.**

## Verificación antes de desplegar

Sobre dispositivo real, no solo en emulador:

1. Abrir tres ubicaciones distintas en Android con Google Maps instalado y confirmar que el marcador cae sobre el punto correcto, contrastando con `data.md`.
2. Repetir en iPhone, con y sin la aplicación de Google Maps instalada.
3. Comprobar el caso de longitud negativa; un fallo de codificación se manifestaría en todas las ubicaciones a la vez.
4. Abrir una calle y comprobar que solo se ve el minimapa local con su línea, sin enlace externo.
5. Desde una ficha, pulsar «Cómo llegar» y ver en qué modo de transporte queda la ruta.

Estas comprobaciones no se dan por superadas si no se han ejecutado.
