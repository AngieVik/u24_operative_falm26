# 01 — Producto

## Problema y objetivo

El operativo reúne muchas ubicaciones próximas y sin una dirección postal útil. Los
avisos suelen identificar el destino por su nombre o por su parcela. La aplicación
reduce a segundos el paso de recibir esa referencia a verla situada en Google Maps.

## Usuarios

- Personal operativo que consulta desde el móvil, con prisa y a menudo de noche.
- Coordinación, que puede necesitar localizar una parcela o dictar sus coordenadas.

## Flujo principal

1. Se abre la aplicación y aparece el menú de grupos.
2. Se entra en un grupo o se escribe un nombre, parcela, actividad o grupo.
3. Se abre el detalle si hace falta más información.
4. El botón derecho abre Google Maps en las coordenadas exactas.
5. La fila `...` vuelve al menú de grupos.

## Requisitos funcionales

| ID | Requisito |
| -- | --------- |
| RF-1 | Pantalla única con cabecera fija y lista desplazable. |
| RF-2 | Búsqueda instantánea y local, sin botón ni petición de red. |
| RF-3 | La búsqueda cubre nombre público, parcela, actividad y grupo. También admite la parcela sin guion: `A01` encuentra `A-01`. |
| RF-4 | La búsqueda ignora mayúsculas y diacríticos. |
| RF-5 | Con el campo vacío se muestran los diez grupos operativos definidos por los datos. Cada fila conserva la geometría de una ubicación y usa un pin gris decorativo. |
| RF-6 | Pulsar un grupo muestra sus ubicaciones; la última fila `...` vuelve al menú. Cualquier consulta no vacía busca globalmente. |
| RF-7 | La fila cerrada muestra parcela y nombre público. Pulsar el nombre abre un detalle con los campos disponibles y las coordenadas copiables. |
| RF-8 | El botón derecho es el único elemento que abre Google Maps y no inicia por sí mismo la navegación paso a paso. |
| RF-9 | Las filas con varias parcelas muestran la primera, pero todas siguen siendo buscables. |
| RF-10 | Si no hay coincidencias, se muestra un mensaje breve y existe un control para borrar la consulta. |
| RF-11 | Si no hay coincidencia literal, puede ofrecerse una coincidencia aproximada por nombre, separada y rotulada como tal. |
| RF-12 | Las farolas se nombran `Farola <código>` y mantienen su indicador de color por zona. |
| RF-13 | Si se configuran recorridos de calles, buscar su nombre los muestra antes que las ubicaciones y su botón abre el trazado. |
| RF-14 | El detalle incluye un plano orientativo estático con el destino señalado y las farolas como referencias. Funciona sin conexión y no permite arrastrar, ampliar ni navegar. |

## Requisitos no funcionales

- La aplicación, sus datos y la búsqueda funcionan sin cobertura; Google Maps necesita
  conexión.
- Es instalable como PWA, sin cuentas, analítica, cookies, backend ni claves de API.
- Es mobile-first, de tema oscuro y usable con una mano.
- El arranque no depende de una respuesta de red.
- Las dependencias de ejecución se empotran y versionan en el repositorio.

## Fuera de alcance

- Mapa interactivo o navegación dentro de la aplicación.
- Registro de avisos, partes, tiempos, turnos o personal.
- Edición de ubicaciones desde la interfaz.
- Geolocalización de la unidad, autenticación, sincronización o notificaciones.

## Decisiones de interfaz

La ficha de Google se abre mediante coordenadas, por lo que el nombre fiable lo aporta
la aplicación. La fila completa no es un enlace: el nombre controla el detalle y el
botón derecho abre el mapa, evitando activaciones accidentales durante el desplazamiento.

El minimapa usa el plano aportado, con fondo gris claro opaco y un encuadre amplio.
Es una ayuda para reconocer el entorno, no una medición topográfica ni una ruta.
La posición procede de las coordenadas del catálogo; el dibujo no confirma qué negocio
ocupa cada parcela. Si un punto queda fuera del plano, conserva su detalle y enlace GPS
pero no muestra un minimapa engañoso.

Los tamaños reales están definidos en `src/template.html`. Cualquier cambio de tamaño
o interacción debe comprobarse en un móvil, sin documentar medidas distintas de las que
usa el código.
