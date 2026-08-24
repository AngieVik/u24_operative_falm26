# 05 — Mantenimiento

## Actualizar ubicaciones

### 1. Elegir la sección correcta

El título Markdown se convierte en grupo de búsqueda. Usa grupos operativos concretos,
por ejemplo Atracciones, Habilidad, Casetas, Restauración, Repostería, Puntos de Interés
y Farolas.

### 2. Usar el esquema correspondiente

Negocios:

```text
parcel | trade_name | legal_name | activity_type | coords
```

Puntos generales y farolas:

```text
parcel | name | type | coords
```

Calles:

```text
street | start | end | waypoints
```

No cambies los encabezados ni añadas una columna solo a una fila.

### 3. Separar marca, titular y actividad

- `trade_name`: nombre público del negocio, solo si está confirmado.
- `legal_name`: titular o razón social del documento oficial.
- `activity_type`: lo que hace el negocio o su categoría operativa.

Si el titular es una persona y no hay marca, deja `trade_name` vacío. La lista mostrará la
actividad y el nombre personal quedará únicamente en el detalle, fuera de la búsqueda.

Si no existe nombre comercial conocido, no lo inventes. Para una empresa puede mostrarse
su razón social; para una persona se usa la actividad.

### 4. Conciliar por parcela

La parcela, o el conjunto completo de parcelas, es la clave frente al listado oficial.
Conserva los nombres comerciales ya confirmados y completa `legal_name` y
`activity_type` desde el documento vigente.

En filas agrupadas incluye todas las parcelas en `parcel`, separadas por comas. La app
mostrará la primera y buscará todas.

Si una fila no aparece en el listado, conserva los datos operativos existentes y anótala
para revisión de campo. No derives coordenadas precisas del plano.

### 5. Coordenadas

Escribe `lat,lon`, sin espacio y con punto decimal. Conserva todos los decimales. Antes de
publicar, contrasta el botón de mapa con `data.md`, no de memoria.

## Verificar y compilar

Desde la raíz:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
$env:PYTHONDONTWRITEBYTECODE='1'; python scripts/build.py
```

Lee también los avisos del build. Después sirve `dist/` por HTTP para comprobar el service
worker y la interacción:

```powershell
python -m http.server 4173 --directory dist
```

Comprueba como mínimo:

1. búsqueda por cada parcela de una agrupación;
2. búsqueda por actividad y grupo;
3. nombre personal ausente en la lista y en la búsqueda;
4. titular visible solo al abrir el detalle;
5. exclusividad y cierre exterior del detalle;
6. copia de coordenadas;
7. enlace de mapa independiente;
8. versión `u24-<hash>` nueva en `dist/sw.js`.

## Regenerar la tipografía

Si aparece un carácter no cubierto, el build se detiene. Regenera el subconjunto y vuelve
a probar:

```powershell
python -m pip install fonttools brotli
python scripts/subset-fonts.py
python scripts/build.py
```

## Cambiar el operativo o la marca

- Rótulo del operativo: `OPERATIVO` en `scripts/build.py`.
- Metadatos: `src/template.html` y `src/manifest.webmanifest`.
- Emblema: `src/logo.svg`.
- Iconos publicados: `icons/`.

La versión del service worker no se edita a mano: el build la calcula a partir del HTML,
manifiesto y plantilla del worker.

## Publicar

`netlify.toml` publica `dist/`. El build no se ejecuta en Netlify, por lo que hay que
commitear los archivos de `dist/` junto con `data.md`, código, pruebas y documentación.
No hagas push o despliegue sin autorización explícita.
