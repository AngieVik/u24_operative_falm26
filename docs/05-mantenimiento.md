# 05 — Mantenimiento

## Actualizar ubicaciones

### 1. Editar la tabla adecuada

`data.md` puede contener varias tablas bajo un mismo título. El build las lee todas y
toma el grupo de la columna `group`, no del título Markdown.

Usa uno de estos dos encabezados, sin variantes:

```text
parcel | trade_name | legal_name | group | activity_type | coords
parcel | name | group | coords
```

Las filas de `-` pueden separar bloques visualmente. No cambies los encabezados ni
añadas una columna solamente a determinadas filas.

### 2. Usar un grupo válido

Los valores canónicos son: `Atracciones`, `Habilidad`, `Casetas`, `Restauración`,
`Bebidas Espirituosas`, `Repostería`, `Puntos de Interes`, `Aseos Publicos`, `Acceso` y
`Puntos de Referencia`. También se admite `Accesos` como equivalente de `Acceso`.
Su correspondencia con los códigos del menú está documentada en
`docs/02-datos.md`.

No crees un grupo para una subcategoría: usa `activity_type` para distinguir, por ejemplo,
atracciones infantiles, tiros, multijuegos o tipos de restauración.

### 3. Separar marca, titular y actividad

- `trade_name`: marca confirmada.
- `legal_name`: titular o razón social oficial.
- `activity_type`: actividad concreta.

Si el titular es una persona y no hay marca, deja `trade_name` vacío. La actividad será
el nombre público y la persona solo aparecerá al abrir el detalle. No inventes una marca.

### 4. Conservar parcelas agrupadas

La parcela o el conjunto completo es la clave de conciliación. Separa varias parcelas
con comas y mantén una sola fila cuando corresponden al mismo negocio. La aplicación
muestra la primera y busca todas.

### 5. Mantener coordenadas

Escribe latitud y longitud con seis decimales y punto decimal. Se admite `lat,lon` o
`lat, lon`; el build publica el formato sin espacios. Contrasta el botón del mapa con
`data.md`, no de memoria ni a partir del dibujo de un plano.

## Plano orientativo

`src/minimap.svg` contiene una copia del plano aportado y el bloque de metadatos
`u24-georeference`. La geometría original se conserva; el archivo del escritorio no
se modifica. Las farolas se dibujan a partir de las mismas filas de `data.md` que usa
el listado, sin mantener una segunda tabla de coordenadas.

La transformación afín convierte latitud y longitud en metros locales y después en
unidades del SVG. Procede del ajuste a centros de parcelas, revisado visualmente con
las farolas en sus cruces. Es orientativa, no una calibración topográfica certificada.
Cambiar una ubicación en `data.md` actualiza automáticamente su punto al compilar.
No ajustes el GPS para hacerlo encajar con un rótulo antiguo del plano.

Si se sustituye el plano o cambia su geometría, escala, origen o `viewBox`, hay que
revisar también la calibración. Comprueba referencias repartidas entre norte, sur,
este y oeste. El build se detiene si falta la calibración o es inválida; si una
ubicación cae fuera del papel, avisa y omite solo su minimapa, sin mover el punto.

El SVG se empotra como imagen aislada, retirando información del editor pero sin
alterar sus formas. Se cachea con el HTML y cambia la versión del service worker.
No requiere librerías, teselas, API ni descargas adicionales al abrir un detalle.

## Calles opcionales

El encabezado es:

```text
street | map_path
```

La tabla puede quedar vacía. Cada fila contiene el nombre y una línea SVG absoluta
(`M`, `L`, `Q`, `C`, `Z`) dentro del plano; consulta `docs/02-datos.md` para la sintaxis.
No añadas coordenadas GPS ni destinos de Maps: estas entradas solo se previsualizan.
Si cambias el plano, revisa también estos trazados. La rotonda exterior del Acebo y
su conexión son referencias esquemáticas confirmadas visualmente por el usuario.

## Verificar y compilar

Desde la raíz:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
$env:PYTHONDONTWRITEBYTECODE='1'; python scripts/build.py
```

Después sirve `dist/` por HTTP para comprobar la interacción y el service worker:

```powershell
python -m http.server 4173 --directory dist
```

Comprueba al menos:

1. menú inicial con diez grupos de ubicaciones más Calles, códigos correctos y pines grises;
2. entrada en cada grupo y vuelta mediante la flecha de la cabecera, sin fila `...`;
3. búsqueda por todas las parcelas de una fila agrupada;
4. búsqueda por actividad y grupo;
5. ausencia de nombres personales en la lista y la búsqueda;
6. detalle, cierre, copia de coordenadas y enlace de mapa independiente;
7. versión `u24-<hash>` renovada en `dist/sw.js`;
8. plano legible en pantalla estrecha, con pin correcto en centro y extremos;
9. scroll sobre el minimapa sin mover la cabecera ni desplazar el plano;
10. recarga sin conexión después de una primera carga completa, abriendo detalles
    que no se hubieran consultado antes;
11. calles buscables por los nombres de feria y policiales, con su trazado completo
    sin pin, coordenadas copiables ni enlace GPS; rotonda exterior al oeste de la puerta;
12. flecha estable durante el scroll y retorno desde búsqueda al menú con la consulta vacía.

## Tipografía, operativo y publicación

Si aparece un carácter sin cobertura, regenera el subconjunto y repite las pruebas:

```powershell
python -m pip install fonttools brotli
python scripts/subset-fonts.py
python scripts/build.py
```

- Rótulo del operativo: `OPERATIVO` en `scripts/build.py`.
- Metadatos: `src/template.html` y `src/manifest.webmanifest`.
- Emblema: `src/logo.svg`.
- Iconos: `icons/`.

La versión del service worker la calcula el build. `netlify.toml` publica `dist/`, por lo
que se versionan juntos los datos, el código, las pruebas, la documentación y los
artefactos generados. No se hace push ni despliegue sin autorización explícita.
