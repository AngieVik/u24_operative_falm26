# Diseño: identificación visual de farolas

## Objetivo

Diferenciar las 23 farolas recién incorporadas de las parcelas y del resto de
ubicaciones, conservando sus códigos y coordenadas.

## Datos

- Cada nombre pasa del código aislado al formato literal `Farola <código>`:
  `A8` se convierte en `Farola A8`, `B8` en `Farola B8`, etc.
- El identificador de ubicación permanece sin cambios (`A8`, `B8`, etc.).
- Las coordenadas y las direcciones vacías permanecen sin cambios.
- Tanto el código como el nombre completo continúan formando parte del índice
  de búsqueda.

## Nomenclatura de color

| Prefijo | Color semántico | Valor visual |
| --- | --- | --- |
| `A` | Azul | `#3B82F6` |
| `B` | Verde | `#22C55E` |
| `C` | Rojo | `#EF4444` |
| `D` | Amarillo | `#FACC15` |

Los códigos y el texto `Farola` siguen visibles. El color refuerza la
clasificación, pero no es la única forma de distinguirla.

## Presentación

- Cada fila de farola recibe una única barra vertical continua de 4 px en el
  borde izquierdo del cajón.
- La barra ocupa toda la altura de la fila y queda a la izquierda tanto del
  código como del nombre.
- El relleno izquierdo se compensará para que el código y el nombre mantengan
  la misma alineación que el resto de ubicaciones.
- No se aplicará fondo teñido, animación ni ningún otro tratamiento visual.
- Las ubicaciones que no sean farolas conservarán exactamente su aspecto.

## Flujo de datos

1. `data.md` conserva el código, el nombre `Farola <código>` y las coordenadas.
2. `scripts/build.py` deriva el color semántico solo para una ubicación cuyo
   código empiece por `A`, `B`, `C` o `D` y cuyo nombre sea exactamente
   `Farola <código>`.
3. La ubicación generada incluye un marcador de color independiente de
   `label`, `display`, `search` y `flat`.
4. `src/template.html` convierte ese marcador en una clase CSS segura y pinta
   la barra lateral correspondiente.

## Validación

- Prueba unitaria de los cuatro colores y de una ubicación que no debe recibir
  marcador.
- Comprobación de los 23 nombres literales y sus coordenadas.
- Comprobación de que buscar el código o `Farola <código>` sigue encontrando el
  mismo registro.
- Ejecución de los validadores internos de formato, unicidad, coherencia
  geográfica y cobertura tipográfica.
- No se compilará ni se modificará `dist/`; la comprobación visual final queda
  para la compilación posterior del usuario.
