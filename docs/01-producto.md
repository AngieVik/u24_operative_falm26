# 01 — Producto

## Problema

El operativo cubre un recinto denso de ubicaciones repartidas en varias calles paralelas.
Los avisos identifican el punto por su **nombre** («El Pimpi») o por su **número** («la
97», «la 145-146»), no por una dirección postal navegable.

Localizar ese punto a mano cuesta tiempo: los nombres no son direcciones, Google Maps no
los resuelve de forma fiable dentro del recinto, y hacerlo desde el móvil mientras se
conduce o se prepara la salida distrae al equipo.

## Objetivo

Reducir a segundos el paso «tengo el nombre de la ubicación» → «sé dónde está y salgo».

## Usuarios

- **Primario:** personal de la unidad, en su móvil, dentro del vehículo, con prisa,
  frecuentemente de noche y en un entorno ruidoso.
- **Secundario:** coordinación del operativo, que puede necesitar consultar y dictar las
  coordenadas exactas de una ubicación.

Buena parte del equipo conoce la zona. Para esos usuarios, ver el punto sobre el mapa un
segundo es suficiente para salir; no necesitan navegación asistida y les estorba.

## Escenario de referencia

1. Entra un aviso: *«asistencia en El Sarao»*.
2. El sanitario abre la aplicación desde el acceso directo del móvil.
3. Escribe `sar`. La lista se filtra al instante y muestra **El Sarao** con su calle y sus
   coordenadas.
4. Pulsa el botón de la fila. Se abre la ficha de lugar de Google Maps sobre el punto.
5. Quien conoce la zona se orienta y sale. Quien no, pulsa «Cómo llegar» dentro de Maps.

Variantes equivalentes: el aviso llega como *«la 66»* y se escribe `66`; el nombre se
teclea con una errata y la aplicación ofrece la ubicación parecida; se busca por el nombre
de la calle y aparece su recorrido completo.

## Requisitos funcionales

| ID | Requisito |
| --- | --- |
| RF-1 | Pantalla única: campo de búsqueda arriba y lista de resultados debajo. Sin menús ni navegación entre pantallas. |
| RF-2 | El campo recibe el foco al abrir. El teclado no se abre solo: ningún navegador móvil lo permite sin un gesto del usuario. Por eso el icono de lupa es permanente, como señal de dónde se escribe. |
| RF-3 | El filtrado es instantáneo a cada pulsación, sin botón de buscar y sin peticiones de red. |
| RF-4 | La búsqueda cubre **nombre**, **identificador** y **calle** en la misma caja. |
| RF-5 | Insensible a mayúsculas, tildes y diéresis: `alora` encuentra `Casa de Álora`. |
| RF-6 | Las ubicaciones con varias parcelas muestran solo la primera, pero buscar cualquiera de las parcelas agrupadas devuelve la ubicación: `CT-05` encuentra la caseta rotulada como `CT-01`. |
| RF-7 | Cada resultado muestra el identificador, el nombre, la calle y las coordenadas. |
| RF-8 | Cada fila lleva a la derecha un botón, **único elemento de la fila que abre el mapa**. Al pulsarlo se abre la ficha de lugar de Google Maps sobre las coordenadas exactas. No se lanza la navegación paso a paso: la inicia el usuario desde la propia ficha si la necesita. |
| RF-9 | Con el campo vacío se muestra el listado completo. |
| RF-10 | Si ningún resultado coincide, se indica con un mensaje claro y breve. |
| RF-11 | Existe una forma evidente de borrar la búsqueda de un toque. |
| RF-12 | Las coordenadas están **a la vista** en cada fila, legibles y dictables por radio, y **se copian al portapapeles al tocar el texto**, con confirmación visible. |
| RF-13 | **Tolerancia a erratas en el nombre.** Cuando la búsqueda literal no devuelve nada, se ofrecen las ubicaciones y calles cuyo nombre más se parece a lo tecleado, **separadas y rotuladas** como aproximadas. |
| RF-14 | **La tolerancia a erratas no se aplica nunca a los números.** Una consulta de solo dígitos se resuelve con las reglas exactas de `docs/02-datos.md`. Un número que no existe devuelve lista vacía. |
| RF-15 | Bajo el buscador se muestra el operativo en curso. |
| RF-16 | **Trazado de calles:** escribir el nombre de una calle la devuelve como primera fila, y su botón abre el recorrido completo sobre el mapa. |
| RF-17 | **La puntuación no puede dejar la pantalla vacía.** `A01` sin guion encuentra `A-01`, y `CT02` encuentra `CT-02`. |
| RF-18 | Las farolas se nombran `Farola <código>` y muestran una barra lateral por zona: A azul, B verde, C rojo y D amarillo. El código y el nombre siguen siendo buscables. |

## Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| RNF-1 | **Funciona sin cobertura.** Datos y motor de búsqueda viajan con la aplicación. Google Maps sí necesita red, y por eso las coordenadas están a la vista (RF-12). |
| RNF-2 | **Instalable** en la pantalla de inicio de Android e iOS, sin tiendas de aplicaciones. |
| RNF-3 | **Mobile-first.** Diseñada para móvil en vertical; usable en tablet y escritorio sin optimizar para ellos. |
| RNF-4 | **Legible y acertable en condiciones adversas:** de noche, en marcha, con guantes y a una mano. Los medios son decisión de diseño; el resultado se comprueba en dispositivo real. |
| RNF-5 | Arranque en frío inferior a 1 segundo en un móvil de gama media con la aplicación instalada. |
| RNF-6 | El filtrado no produce retraso perceptible al teclear, incluida la coincidencia aproximada. |
| RNF-7 | Sin cuentas de usuario, sin registro, sin seguimiento analítico, sin cookies. |
| RNF-8 | Sin claves de API de Google Maps: se usan exclusivamente Maps URLs públicas. |
| RNF-9 | Los enlaces funcionan igual en Android, iOS y navegador de escritorio con una sola URL. |
| RNF-10 | Dependencias mínimas y empotradas, fijadas a una versión concreta dentro del repositorio. |
| RNF-11 | Tema oscuro: el uso es mayoritariamente nocturno y prolongado. |
| RNF-12 | **Abrir la aplicación nunca depende de que la red conteste.** El escenario real no es «sin red» sino «red saturada», donde una petición no falla: se queda esperando. |

## Fuera de alcance

- Mapa interactivo dentro de la aplicación.
- Registro de avisos, incidencias, tiempos de respuesta o partes de asistencia.
- Cuadrantes, turnos o gestión de personal.
- Cuentas, autenticación o roles.
- Edición de ubicaciones desde la interfaz.
- Backend, base de datos o sincronización entre dispositivos.
- Geolocalización propia de la unidad dentro de la aplicación.
- Notificaciones push y analítica de uso.

## Restricciones técnicas

- Se sirve como sitio estático, sin servidor de aplicación.
- Los datos se empaquetan con la aplicación; no se piden en tiempo de ejecución.
- Sin claves de API ni secretos de ningún tipo en el cliente.
- Instalable como aplicación web progresiva: manifiesto y service worker.
- Superficie de código pequeña y legible.

## Decisiones de diseño con implicaciones

**El enlace abre la ficha de lugar, no la navegación.** El equipo, que conoce la zona,
cancelaba el navegador paso a paso para poder ver la ficha del sitio, lo que costaba más
tiempo del que ahorraba. Contrapartidas asumidas: quien necesita navegación da dos toques
más dentro de Maps, y se pierde el modo de transporte, así que «Cómo llegar» usará el
último empleado en ese móvil.

**La fila no es un enlace; solo su botón abre el mapa.** Con un listado largo, una
fila-enlace se activa sola al desplazar con el dedo. Las coordenadas sí son pulsables
porque copiar no tiene consecuencias.

**La ficha no muestra el nombre de la ubicación,** porque se abre por coordenadas y no por
un lugar registrado en Google. El nombre lo aporta la aplicación antes de salir. No se
resolverá la ubicación por texto para conseguir ese rótulo: ver el principio 4 de
`CLAUDE.md`.

**Objetivos táctiles.** WCAG 2.1 recomienda 48 px de alto de fila como mínimo para una
pulsación fiable. La implementación actual usa 72 px con un botón de 64 px de ancho por
toda la altura de la fila. Cualquier cambio que afecte a la probabilidad de abrir la
ubicación equivocada se justifica en `docs/04-convenciones.md` y se comprueba en vehículo.
