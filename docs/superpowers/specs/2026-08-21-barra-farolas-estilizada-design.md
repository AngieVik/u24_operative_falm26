# Diseño: barra estilizada para farolas

## Objetivo

Refinar el indicador cromático de las farolas para que no ocupe toda la altura
del cajón y tenga un acabado más discreto y profesional.

## Diseño aprobado

- Sustituir el borde lateral completo por un pseudoelemento decorativo `::before`.
- Mantener 4 px de ancho y limitar la altura a 40 px.
- Centrar la barra verticalmente en la fila.
- Redondear completamente ambos extremos.
- Conservar los colores semánticos actuales: A azul, B verde, C rojo y D amarillo.
- Mantener sin cambios la alineación del código y el nombre, el espaciado de la
  fila, el área táctil y el comportamiento de búsqueda.

## Alcance técnico

El cambio se limita al CSS de `.row.farola` en `src/template.html`. La fila se
usará como contenedor de posicionamiento y su pseudoelemento tomará el color de
`--farola-color`. No se modificarán el HTML generado, el modelo de datos ni
`data.md`.

## Verificación

- Comprobar estáticamente que el pseudoelemento mide 4 × 40 px, está centrado y
  tiene extremos redondeados.
- Ejecutar las pruebas existentes para confirmar que la clasificación y la
  búsqueda de las farolas no cambian.
- Revisar el diff y confirmar que `dist/` permanece intacto.
- No compilar el proyecto.
