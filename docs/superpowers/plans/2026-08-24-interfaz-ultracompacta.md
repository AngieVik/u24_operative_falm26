# Interfaz ultracompacta de ubicaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar a la app existente la lista ultracompacta aprobada, con filas cerradas de 38 px y coordenadas copiables cuyo texto visible no cambia.

**Architecture:** Se conserva la aplicación estática actual y su generación desde `data.md`. El cambio se limita al contrato visual y de interacción de `src/template.html`, respaldado por pruebas estáticas en `tests/test_build.py`; después se regenera `dist/` con el constructor existente.

**Tech Stack:** HTML5, CSS, JavaScript sin dependencias, Python `unittest`, generador `scripts/build.py`.

**Spec:** `docs/superpowers/specs/2026-08-24-ubicaciones-privacidad-desplegable-design.md`

## Global Constraints

- La ubicación cerrada se presenta en una sola línea: `parcela | nombre | mapa`.
- La fila cerrada mide exactamente 38 px; el buscador y el logotipo miden 34 px; el botón visible de mapa mide 28 px.
- La lista es plana, sin tarjetas ni huecos verticales entre resultados.
- El amarillo corporativo es `#FFC72C`; no se añade naranja.
- Las coordenadas muestran únicamente `latitud, longitud`, pero copian `latitud,longitud` al pulsarlas.
- Copiar no cambia el texto visible de las coordenadas.
- Solo puede existir un detalle abierto; se conservan cierre exterior, cierre al repetir pulsación, sustitución al abrir otro y cierre con Escape.
- Los nombres personales siguen sin aparecer ni ser buscables fuera del detalle.
- Las farolas conservan los colores semánticos y usan una barra de 4 x 22 px.
- No se añaden dependencias, React, Tailwind ni shadcn/ui.
- No se modifican `data.md`, el parser ni las reglas de búsqueda.
- No se hace commit, push ni despliegue sin autorización expresa del usuario.

---

## Mapa de archivos

- `src/template.html`: estilos de cabecera, buscador, filas, detalle y botón de mapa; texto y comportamiento de copia de coordenadas.
- `tests/test_build.py`: contratos estáticos que fijan dimensiones, ausencia de espaciado sobrante y copia sin mutación visual.
- `dist/index.html`: salida generada que incorpora la plantilla y los datos actuales.
- `dist/sw.js`: salida generada cuya versión de caché cambia con el HTML compilado.
- `docs/superpowers/specs/2026-08-24-ubicaciones-privacidad-desplegable-design.md`: fuente normativa; no requiere más cambios durante la ejecución salvo contradicción descubierta.

### Task 1: Fijar y aplicar la densidad ultracompacta

**Files:**
- Modify: `tests/test_build.py`
- Modify: `src/template.html`

**Interfaces:**
- Consumes: clases existentes `.bar`, `.mark`, `.field`, `.row`, `.num`, `.nom`, `.detail`, `.go`, `.pill` y variantes `.farola-*`.
- Produces: el mismo DOM y las mismas clases con nuevas dimensiones; JavaScript y generador continúan consumiéndolos sin cambios de firma.

- [ ] **Step 1: Escribir primero los contratos visuales que deben fallar**

Sustituir `test_farola_bar_is_centered_short_and_rounded` y añadir el contrato compacto:

```python
def test_compact_layout_contract_is_present(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")

    required = (
        "grid-template-columns:36px minmax(0,1fr)",
        ".bar .mark{flex:none;width:34px;height:34px;display:block}",
        "#q{\n  display:block;width:100%;height:34px",
        "grid-template-columns:56px minmax(0,1fr) 38px",
        "min-height:38px",
        "width:28px;height:28px",
        "border-bottom:1px solid var(--rule)",
    )
    for rule in required:
        with self.subTest(rule=rule):
            self.assertIn(rule, template)

    self.assertNotIn("min-height:72px", template)
    self.assertNotIn("width:40px;height:40px", template)


def test_farola_bar_is_centered_short_and_rounded(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")

    self.assertIn(".row.farola::before{", template)
    self.assertIn("width:4px;height:22px", template)
    self.assertIn("top:50%", template)
    self.assertIn("transform:translateY(-50%)", template)
    self.assertIn("border-radius:999px", template)
    self.assertIn(".row.expanded.farola::before{top:19px}", template)
```

- [ ] **Step 2: Ejecutar únicamente los contratos nuevos y comprobar el fallo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest tests.test_build.LocationDisplayTests.test_compact_layout_contract_is_present tests.test_build.LocationDisplayTests.test_farola_bar_is_centered_short_and_rounded -v
```

Expected: FAIL porque la plantilla todavía contiene fila de 72 px, buscador de 54 px, botón visible de 40 px y barra de farola de 40 px.

- [ ] **Step 3: Aplicar el CSS compacto mínimo en la plantilla existente**

Actualizar los bloques correspondientes de `src/template.html` con estos valores, conservando tokens, estructura y estados existentes:

```css
.bar{
  display:grid;grid-template-columns:36px minmax(0,1fr);
  align-items:center;gap:8px;padding:5px 10px 4px;
}
.bar .mark{flex:none;width:34px;height:34px;display:block}
.sub{
  margin:2px 1px 0;padding:0;
  font-size:8px;font-weight:500;letter-spacing:.075em;
  color:var(--faint);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.field{border-radius:8px}
.field .lead{left:9px;width:15px;height:15px}
#q{
  display:block;width:100%;height:34px;padding:0 31px 0 32px;
  background:none;border:0;outline:none;border-radius:8px;
  font-family:inherit;font-size:14px;font-weight:500;color:var(--text);
}
#clear{right:2px;width:28px;height:28px}
#clear .ico{width:15px;height:15px}

.row{
  display:grid;grid-template-columns:56px minmax(0,1fr) 38px;
  align-items:center;column-gap:0;min-height:38px;
  padding:0 7px 0 12px;border-bottom:1px solid var(--rule);
  -webkit-user-select:none;user-select:none;-webkit-touch-callout:none;
}
.row.farola::before{width:4px;height:22px}
.row.expanded.farola::before{top:19px}
.num{
  width:auto;font-size:12px;font-weight:700;
  font-variant-numeric:tabular-nums;letter-spacing:.02em;
  color:var(--accent);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.nom{
  display:block;font-size:13.5px;line-height:18px;font-weight:500;
  letter-spacing:.005em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.detail-toggle{width:100%;padding:9px 0;margin:-9px 0}
.go{width:38px;align-self:stretch;display:grid;place-items:center}
.pill{
  display:grid;place-items:center;width:28px;height:28px;border-radius:7px;
  background:var(--accent-soft);border:1px solid var(--accent-line);
}
.pill .ico{width:14px;height:14px}
.detail{
  grid-column:1 / -1;width:auto;margin:0 8px 6px 68px;padding:0 8px 8px;
  background:rgba(255,255,255,.018);border-top:1px solid var(--border);
  border-radius:0;animation:detail-in 160ms ease-out both;
}
.detail-fields{display:grid;gap:4px;margin:0;padding-top:7px}
.detail-item{grid-template-columns:88px minmax(0,1fr);gap:8px}
.detail-item dt{font-size:9px;line-height:14px}
.detail-item dd{font-size:11px;line-height:14px}
```

- [ ] **Step 4: Ejecutar los contratos compactos y comprobar que pasan**

Run: el mismo comando del Step 2.

Expected: dos pruebas PASS.

- [ ] **Step 5: Revisar el diff de la tarea**

Run:

```powershell
git diff -- src/template.html tests/test_build.py
git diff --check -- src/template.html tests/test_build.py
```

Expected: solo cambian dimensiones y estilos relacionados; `git diff --check` no informa errores. No crear commit sin autorización.

### Task 2: Copiar coordenadas sin texto auxiliar ni mutación visible

**Files:**
- Modify: `tests/test_build.py`
- Modify: `src/template.html`

**Interfaces:**
- Consumes: `detail(loc)`, `copyText(text)`, `LABEL.copy`, `LABEL.copied` y la región de estado `meta` existentes.
- Produces: botón `.co` cuyo `textContent` visible es `latitud, longitud` y cuyo `data-coords` conserva `latitud,longitud` para el portapapeles.

- [ ] **Step 1: Cambiar el contrato del detalle antes de tocar JavaScript**

Actualizar `test_inline_detail_contract_is_present` y añadir un contrato explícito:

```python
def test_inline_detail_contract_is_present(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")

    self.assertIn("function detail(loc)", template)
    self.assertIn("function openDetail(", template)
    self.assertIn("function closeDetail(", template)
    self.assertIn("aria-expanded", template)
    self.assertIn("aria-controls", template)
    self.assertIn("prefers-reduced-motion:reduce", template)


def test_coordinates_copy_without_visible_instruction_or_text_mutation(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")

    self.assertIn(
        "coordinates.textContent = loc.lat + ', ' + loc.lon;", template
    )
    self.assertIn("coordinates.dataset.coords = loc.lat + ',' + loc.lon;", template)
    self.assertIn("copyText(btn.dataset.coords).then(() => {", template)
    self.assertIn("meta.textContent = LABEL.copied;", template)
    self.assertNotIn("TEXT.coordinates + ': '", template)
    self.assertNotIn("coordinates.dataset.label", template)
    self.assertNotIn("btn.textContent = TEXT.copied", template)
    self.assertNotIn("btn.dataset.label || btn.dataset.coords", template)
```

- [ ] **Step 2: Ejecutar el nuevo contrato y comprobar el fallo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest tests.test_build.LocationDisplayTests.test_coordinates_copy_without_visible_instruction_or_text_mutation -v
```

Expected: FAIL porque el detalle todavía antepone `Coordenadas:` y cambia temporalmente el botón a `Copiado`.

- [ ] **Step 3: Reducir el texto visible y mantener la copia existente**

En `detail(loc)`, usar exactamente:

```javascript
coordinates.dataset.coords = loc.lat + ',' + loc.lon;
coordinates.textContent = loc.lat + ', ' + loc.lon;
coordinates.setAttribute('aria-label', LABEL.copy + loc.name);
```

En el manejador de `.co`, mantener el mecanismo de copia y la confirmación accesible, sin cambiar el botón:

```javascript
copyText(btn.dataset.coords).then(() => {
  meta.textContent = LABEL.copied;
}).catch(() => {});
```

Eliminar `coordinates.dataset.label`, el temporizador de restauración, la clase `.done` y cualquier asignación a `btn.textContent` dentro del manejador de copia.

- [ ] **Step 4: Ejecutar los contratos de detalle y copia**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest tests.test_build.LocationDisplayTests.test_inline_detail_contract_is_present tests.test_build.LocationDisplayTests.test_coordinates_copy_without_visible_instruction_or_text_mutation -v
```

Expected: dos pruebas PASS.

- [ ] **Step 5: Revisar el diff de la tarea**

Run:

```powershell
git diff -- src/template.html tests/test_build.py
git diff --check -- src/template.html tests/test_build.py
```

Expected: el índice de búsqueda, el enlace de mapa, los datos y las reglas de privacidad permanecen intactos. No crear commit sin autorización.

### Task 3: Regenerar y verificar la aplicación completa

**Files:**
- Modify (generated): `dist/index.html`
- Modify (generated): `dist/sw.js`
- Verify: `src/template.html`
- Verify: `tests/test_build.py`

**Interfaces:**
- Consumes: plantilla compacta y datos actuales mediante `scripts/build.py`.
- Produces: `dist/` listo para revisión y posterior commit del usuario.

- [ ] **Step 1: Ejecutar toda la suite sin crear bytecode**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest discover -s tests -v
```

Expected: todas las pruebas PASS.

- [ ] **Step 2: Regenerar la distribución con el constructor existente**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; py -3 scripts/build.py
```

Expected: build completado, mismo número de ubicaciones válidas que antes del cambio y `dist/index.html`/`dist/sw.js` actualizados. Si Windows informa que `dist` está en uso, cerrar únicamente el servidor local que esté sirviendo esa carpeta y repetir.

- [ ] **Step 3: Repetir la suite sobre el estado generado**

Run: el comando del Step 1.

Expected: todas las pruebas PASS tras regenerar `dist/`.

- [ ] **Step 4: Verificar la experiencia en navegador local**

Comprobar a 390–430 px de ancho:

1. Cada fila cerrada mide 38 px y contiene una sola línea.
2. La búsqueda mide 34 px y no presenta borde amarillo permanente.
3. Abrir un nombre integra el detalle bajo esa fila y cierra cualquier otro.
4. Pulsar fuera y Escape cierran el detalle.
5. Las coordenadas visibles contienen solo `latitud, longitud`.
6. Pulsarlas copia `latitud,longitud` sin modificar el texto visible.
7. El botón de mapa sigue abriendo Google Maps sin expandir la fila.
8. Una farola de cada familia A/B/C/D conserva su color semántico y una barra corta centrada.
9. Comparar visualmente la app con `.superpowers/brainstorm/1130-1787584486/content/compact-elegant-v6.html` en el mismo ancho.

Expected: el flujo coincide con la propuesta aprobada y no hay cortes, tarjetas, naranja ni huecos verticales entre filas.

- [ ] **Step 5: Revisión final del alcance**

Run:

```powershell
git diff --check
git status --short
git diff -- src/template.html tests/test_build.py dist/index.html dist/sw.js
```

Expected: sin errores de whitespace; solo aparecen los archivos previstos más los cambios previos del usuario, que deben preservarse. No hacer commit, push ni despliegue sin autorización expresa.
