# Ubicaciones con privacidad y desplegable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adaptar la aplicación al esquema enriquecido de `data.md`, completar los datos oficiales disponibles y mostrar detalles en un único desplegable inline sin exponer nombres personales en la lista ni en el buscador.

**Architecture:** `scripts/build.py` reconocerá cada tabla por sus encabezados y normalizará todos los esquemas a un modelo común antes de generar el JSON empotrado. La privacidad se resolverá durante el build: el navegador recibirá un nombre público y campos de detalle separados, mientras el índice excluirá nombres personales. `src/template.html` seguirá siendo una aplicación autocontenida y añadirá un desplegable accesible creado bajo demanda dentro de la fila.

**Tech Stack:** Python 3 estándar, Markdown como fuente de datos, HTML/CSS/JavaScript sin framework, Fuse.js empotrado, `unittest`, service worker existente y comprobación final en navegador local.

**Spec:** `docs/superpowers/specs/2026-08-24-ubicaciones-privacidad-desplegable-design.md`

## Global Constraints

- `data.md` modificado por el usuario es la fuente principal; no restaurar ni sustituir sus cambios por versiones anteriores.
- `LISTADO PARCELAS OCUPADAS 2026.pdf` solo aporta titular, razón social, actividad y parcela oficiales.
- `plano-recinto-ferial-2026.pdf` solo contrasta parcela y ubicación general; no reemplaza coordenadas precisas por estimaciones visuales.
- No inventar nombres comerciales ni convertir nombres personales en `trade_name`.
- Los nombres personales solo aparecen al desplegar una ubicación y nunca forman parte de `search`, `flat`, `nameSearch`, textos iniciales ni etiquetas accesibles de la lista.
- Mantener Puntos de Interés y Farolas con `parcel | name | type | coords` y Calles con `street | start | end | waypoints`.
- Mantener la aplicación autocontenida, sin dependencias nuevas ni peticiones de red para buscar.
- Preservar el indicador de farolas, la primera parcela visible, todas las parcelas agrupadas buscables y el versionado automático del service worker.
- Generar `dist/` al final de esta tarea.
- No realizar commit, push ni despliegue. Los pasos de commit habituales de la metodología se sustituyen por puntos de revisión de diff.

## File Structure

- Modify: `scripts/build.py` — lectura dinámica de tablas, modelo normalizado, privacidad, búsqueda y ensamblado.
- Modify: `tests/test_build.py` — pruebas unitarias del parser, reglas de nombre público, privacidad, grupos, datos y contrato estático del desplegable.
- Modify: `data.md` — completar `legal_name` y `activity_type` desde las fuentes oficiales, preservando los nombres comerciales confirmados.
- Modify: `src/template.html` — lista pública, detalle inline, copia de coordenadas, cierre exclusivo y estilos accesibles.
- Modify: `docs/02-datos.md` — contrato de los tres esquemas admitidos y reglas de privacidad/búsqueda.
- Modify: `docs/04-convenciones.md` — modelo generado y responsabilidades entre build e interfaz.
- Modify: `docs/05-mantenimiento.md` — procedimiento para actualizar titulares, actividades y nombres comerciales.
- Generate: `dist/index.html`, `dist/sw.js` — salida compilada y versión de caché nueva.
- Read only: `C:/Users/devil/Desktop/f_alm26/LISTADO PARCELAS OCUPADAS 2026.pdf`.
- Read only: `C:/Users/devil/Desktop/f_alm26/plano-recinto-ferial-2026.pdf`.

---

### Task 1: Parser dinámico y modelo público/privado

**Files:**
- Modify: `tests/test_build.py`
- Modify: `scripts/build.py:124-235`
- Modify: `scripts/build.py:365-395`
- Modify: `scripts/build.py:488-525`

**Interfaces:**
- Consumes: secciones Markdown producidas por `read_sections()` y encabezados literales de `data.md`.
- Produces: `read_sections() -> dict[str, {"title": str, "rows": list[tuple[int, list[str]]]}]`.
- Produces: `build_locations(sections: dict) -> list[dict]` con claves `id`, `label`, `display`, `marker`, `numbers`, `name`, `group`, `tradeName`, `legalName`, `activityType`, `isPersonalLegalName`, `street`, `lat`, `lon`, `search`, `flat` y `nameSearch`.
- Produces: `is_public_legal_name(value: str) -> bool` y `choose_public_name(...) -> str`.

- [ ] **Step 1: Añadir fixtures pequeños para los dos esquemas de ubicación**

Añadir a `tests/test_build.py`:

```python
BUSINESS_HEADERS = ["parcel", "trade_name", "legal_name", "activity_type", "coords"]
GENERAL_HEADERS = ["parcel", "name", "type", "coords"]


def section(title, headers, *rows):
    return {
        build.normalize(title): {
            "title": title,
            "rows": [(1, headers)] + [(index + 2, row) for index, row in enumerate(rows)],
        }
    }
```

- [ ] **Step 2: Escribir pruebas fallidas de prioridad y privacidad**

Añadir pruebas que construyan ubicaciones reales mediante `build.build_locations()`:

```python
def test_trade_name_has_priority_over_company(self):
    locations = build.build_locations(section(
        "Casetas", BUSINESS_HEADERS,
        ["CJ-01", "Arena", "Byblos Almería, S.L.", "Juvenil", "36.835720,-2.429620"],
    ))
    self.assertEqual(locations[0]["name"], "Arena")
    self.assertIn("byblos almeria", locations[0]["search"])


def test_company_is_public_fallback(self):
    locations = build.build_locations(section(
        "Restauración", BUSINESS_HEADERS,
        ["RT-03", "", "Donaelia, S.L.", "Mesón", "36.836216,-2.430316"],
    ))
    self.assertEqual(locations[0]["name"], "Donaelia, S.L.")
    self.assertFalse(locations[0]["isPersonalLegalName"])


def test_person_is_private_and_activity_is_public(self):
    locations = build.build_locations(section(
        "Habilidad", BUSINESS_HEADERS,
        ["H-07", "", "Carbajo Gordillo, Vicente Manuel", "Dardos", "36.835387,-2.430832"],
    ))
    location = locations[0]
    self.assertEqual(location["name"], "Dardos")
    self.assertTrue(location["isPersonalLegalName"])
    for key in ("search", "flat", "nameSearch"):
        self.assertNotIn("carbajo", location[key])
    self.assertEqual(location["legalName"], "Carbajo Gordillo, Vicente Manuel")
```

- [ ] **Step 3: Escribir pruebas fallidas de grupo, esquema reducido y parcelas agrupadas**

```python
def test_group_and_activity_are_searchable(self):
    locations = build.build_locations(section(
        "Casetas", BUSINESS_HEADERS,
        ["CT-01, CT-02", "Caseta CSIF", "", "Tradicional", "36.837934,-2.431370"],
    ))
    location = locations[0]
    self.assertEqual(location["display"], "CT-01")
    self.assertIn("ct-02", location["search"])
    self.assertIn("caseta tradicional", location["search"])
    self.assertIn("casetas", location["search"])


def test_general_location_schema_remains_supported(self):
    locations = build.build_locations(section(
        "Farolas", GENERAL_HEADERS,
        ["A1", "Farola A1", "Punto de Referencia", "36.832943,-2.431212"],
    ))
    location = locations[0]
    self.assertEqual(location["name"], "Farola A1")
    self.assertEqual(location["activityType"], "Punto de Referencia")
    self.assertEqual(location["marker"], "blue")
```

- [ ] **Step 4: Ejecutar las pruebas enfocadas y confirmar el rojo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest `
  tests.test_build.LocationDisplayTests.test_trade_name_has_priority_over_company `
  tests.test_build.LocationDisplayTests.test_company_is_public_fallback `
  tests.test_build.LocationDisplayTests.test_person_is_private_and_activity_is_public `
  tests.test_build.LocationDisplayTests.test_group_and_activity_are_searchable `
  tests.test_build.LocationDisplayTests.test_general_location_schema_remains_supported -v
```

Expected: FAIL porque `read_sections()` todavía no expone título/filas y `build_locations()` todavía espera filas de cuatro columnas.

- [ ] **Step 5: Implementar la lectura por esquema**

En `scripts/build.py`:

```python
BUSINESS_HEADERS = ("parcel", "trade_name", "legal_name", "activity_type", "coords")
GENERAL_HEADERS = ("parcel", "name", "type", "coords")
STREET_HEADERS = ("street", "start", "end", "waypoints")

PUBLIC_LEGAL_RE = re.compile(
    r"(?:\bgrupo\b|\basociaci[oó]n\b|\bpartido\b|\bsindical\b|"
    r"\bayuntamiento\b|\borganizaci[oó]n\b|\bsociedad\b|"
    r"\bs\s*\.?\s*l\s*\.?(?:\s*u\s*\.?)?|\bs\s*\.?\s*a\s*\.?)",
    re.IGNORECASE,
)
```

Modificar `read_sections()` para conservar `title` y `rows`. Añadir una función que normalice el encabezado y rechace cualquier tabla no vacía que no coincida exactamente con uno de los tres contratos. Las secciones declaradas sin filas se conservan y se omiten sin error.

- [ ] **Step 6: Implementar las reglas de nombre y búsqueda**

```python
def is_public_legal_name(value):
    return bool(value and PUBLIC_LEGAL_RE.search(value))


def choose_public_name(trade_name, legal_name, activity_type, fallback, parcel):
    # En el esquema general, fallback es el nombre descriptivo y tiene prioridad
    # sobre type. En el esquema comercial, fallback siempre llega vacío.
    if fallback:
        return fallback
    if trade_name:
        return trade_name
    if is_public_legal_name(legal_name):
        return legal_name
    return activity_type or parcel


def group_search_terms(group, activity_type):
    terms = [group, activity_type]
    if normalize(group) == "casetas":
        terms.extend(("caseta", "casetas", f"caseta {activity_type}"))
    return " ".join(term for term in terms if term)
```

`build_locations()` debe iterar las secciones excepto `calles`, omitir secciones sin filas, mapear cada fila según su encabezado y construir `search`, `flat` y `nameSearch` únicamente con parcela, nombre público, nombre comercial, razón social pública, actividad, grupo e indicación. En el esquema general se pasa `name` como `fallback`, por lo que `Farola A1` sigue siendo el nombre público y `Punto de Referencia` queda como actividad/tipo. `legalName` se conserva siempre para el detalle.

- [ ] **Step 7: Adaptar validaciones y `main()`**

- `main()` llama a `build_locations(secciones)`.
- Calles consume `secciones["calles"]["rows"]` y descarta el encabezado `street`.
- `check_charset()` incluye todos los campos que el desplegable puede mostrar, incluido `legalName`.
- `check_coherence()` usa `loc["name"]`, que ya es el nombre público.
- Los mensajes de error mencionan `parcel` y el título de la sección.

- [ ] **Step 8: Ejecutar las pruebas enfocadas y confirmar el verde**

Run: el mismo comando del Step 4.

Expected: PASS para las cinco pruebas.

- [ ] **Step 9: Adaptar las pruebas heredadas al nuevo constructor**

Reemplazar fixtures antiguos de cuatro celdas por `section(...)`, sustituir accesos a `secciones["ubicaciones"]` por `build.build_locations(build.read_sections())` y conservar literalmente las expectativas de farolas, primera parcela, búsqueda completa y versión de caché.

- [ ] **Step 10: Punto de revisión sin commit**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
git diff --check
git diff -- scripts/build.py tests/test_build.py
```

Expected: todas las pruebas del modelo en PASS; el diff solo afecta parser y pruebas.

---

### Task 2: Conciliación completa de `data.md` con las fuentes oficiales

**Files:**
- Modify: `data.md`
- Modify: `tests/test_build.py`
- Read only: `C:/Users/devil/Desktop/f_alm26/LISTADO PARCELAS OCUPADAS 2026.pdf`
- Read only: `C:/Users/devil/Desktop/f_alm26/plano-recinto-ferial-2026.pdf`

**Interfaces:**
- Consumes: `build.read_sections()` y `build.build_locations()` de Task 1.
- Produces: filas comerciales completas y auditables sin cambiar coordenadas por estimaciones del plano.

- [ ] **Step 1: Extraer y revisar visualmente las fuentes PDF**

Usar el Python empaquetado de Codex con `pdfplumber` para extraer tablas del listado y Poppler para renderizar las páginas relevantes bajo `tmp/pdfs/`. Inspeccionar visualmente las páginas que contienen Atracciones, Habilidad, Casetas, Restauración, Repostería y Puestos Tradicionales. El plano solo se usa para comprobar que cada familia de parcelas ocupa la zona esperada.

- [ ] **Step 2: Construir la conciliación por conjunto canónico de parcelas**

Normalizar cada referencia oficial reemplazando `y`, `+` y rangos explícitos por una lista ordenada de códigos. La clave de unión es el conjunto de parcelas, no el texto del nombre. Aplicar estas reglas:

1. `trade_name`: conservar el valor de `data.md`; completar solo cuando el documento o evidencia previa lo identifique expresamente como nombre del negocio.
2. `legal_name`: usar el campo oficial `Autorizado`, `Titular` o equivalente.
3. `activity_type`: conservar las categorías operativas `Adulto`, `Espectáculo`, `Infantil`, `Tradicional` y `Juvenil`; para Habilidad, Restauración y Repostería usar la actividad específica oficial.
4. Si una parcela de `data.md` no aparece en el listado vigente, conservarla y no inventar titular; registrar el caso en el resumen de verificación.
5. Si el plano y el listado discrepan, prevalece el listado para identidad y `data.md` para coordenadas.

- [ ] **Step 3: Escribir primero las pruebas de calidad que deben fallar**

Añadir pruebas de dataset:

```python
def test_current_dataset_uses_new_headers_only(self):
    sections = build.read_sections()
    for key, section_data in sections.items():
        headers = tuple(build.normalize(value) for value in section_data["rows"][0][1])
        self.assertIn(headers, {
            build.BUSINESS_HEADERS,
            build.GENERAL_HEADERS,
            build.STREET_HEADERS,
        })


def test_known_private_and_company_rows_follow_public_name_rules(self):
    locations = {loc["label"]: loc for loc in build.build_locations(build.read_sections())}
    self.assertEqual(locations["H-07"]["name"], "Dardos")
    self.assertNotIn("carbajo", locations["H-07"]["search"])
    self.assertEqual(locations["RT-03"]["name"], "Donaelia, S.L.")
    self.assertEqual(locations["CT-25, CT-26, CT-27, CT-28"]["name"], "Paripé")
    self.assertEqual(locations["CJ-14, CJ-15"]["name"], "Taray Aguadulce, S.L.")
```

Mantener y adaptar `test_occupied_2026_parcels_are_searchable` para recorrer todas las secciones. Añadir una aserción que ninguna ubicación comercial quede sin `tradeName`, `legalName` y `activityType` simultáneamente.

- [ ] **Step 4: Ejecutar las pruebas de dataset y confirmar el rojo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest `
  tests.test_build.LocationDisplayTests.test_current_dataset_uses_new_headers_only `
  tests.test_build.LocationDisplayTests.test_known_private_and_company_rows_follow_public_name_rules `
  tests.test_build.LocationDisplayTests.test_occupied_2026_parcels_are_searchable -v
```

Expected: FAIL en las filas cuyo `legal_name` o actividad aún no esté conciliado.

- [ ] **Step 5: Completar `data.md` sección por sección**

Aplicar la conciliación en este orden para facilitar la revisión del diff:

1. Atracciones: completar titulares legales oficiales sin mover los nombres de atracción fuera de `trade_name`.
2. Habilidad: mantener personas en `legal_name` y actividades concretas en `activity_type`.
3. Casetas: conservar marcas conocidas y completar titulares oficiales, incluyendo `Byblos Almería, S.L.` para CJ-01, `Taray Aguadulce, S.L.` para CJ-14/CJ-15 y `Tinglao Almería, S.L.` para Paripé CT-25 a CT-28 cuando la fuente lo confirme.
4. Restauración y Repostería: separar estrictamente marca, titular y actividad; no mostrar personas como marca.
5. Puntos de Interés y Farolas: no ampliar su esquema reducido.

- [ ] **Step 6: Ejecutar validaciones de datos y confirmar el verde**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
git diff --check
```

Expected: PASS; las 226 referencias oficiales continúan buscables y cada fila conserva coordenadas válidas.

- [ ] **Step 7: Punto de revisión sin commit**

Revisar `git diff -- data.md` y documentar en el resumen de trabajo: coincidencias oficiales, filas conservadas sin titular oficial y cualquier incoherencia literal de los PDF. No modificar los PDF.

---

### Task 3: Desplegable inline accesible y exclusivo

**Files:**
- Modify: `tests/test_build.py`
- Modify: `src/template.html:123-210`
- Modify: `src/template.html:326-635`

**Interfaces:**
- Consumes: claves generadas por Task 1: `name`, `label`, `group`, `tradeName`, `legalName`, `activityType`, `street`, `lat`, `lon`.
- Produces: `detail(loc) -> HTMLElement`, `openDetail(li, button, loc)`, `closeDetail({restoreFocus: bool})` y una única variable de estado `expanded`.

- [ ] **Step 1: Escribir el contrato estático fallido del desplegable**

Añadir una prueba que compruebe los elementos de accesibilidad y las funciones que conectan el comportamiento:

```python
def test_inline_detail_contract_is_present(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")
    self.assertIn("function detail(loc)", template)
    self.assertIn("function openDetail(", template)
    self.assertIn("function closeDetail(", template)
    self.assertIn("aria-expanded", template)
    self.assertIn("aria-controls", template)
    self.assertIn("prefers-reduced-motion:reduce", template)
```

Esta prueba solo protege el contrato estructural; el comportamiento real se valida en navegador en Task 4.

- [ ] **Step 2: Ejecutar la prueba y confirmar el rojo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest `
  tests.test_build.LocationDisplayTests.test_inline_detail_contract_is_present -v
```

Expected: FAIL porque las funciones y atributos todavía no existen.

- [ ] **Step 3: Cambiar la cabecera visible de cada fila**

En `row(loc)`:

- mantener `span.num` con `loc.display`;
- sustituir `span.nom` por `button.nom.detail-toggle` con `type="button"`, `aria-expanded="false"` y un `aria-controls` único derivado de `loc.id`;
- mostrar únicamente `loc.name` en el botón;
- retirar coordenadas y titular del contenido inicial;
- mantener `a.go` como enlace independiente y construir su `aria-label` solo con `loc.name`, `loc.label` y `loc.street`.

- [ ] **Step 4: Crear el detalle bajo demanda**

`detail(loc)` crea un contenedor `div.detail` con `id="detail-" + loc.id`. Añade filas etiquetadas únicamente para valores presentes:

```javascript
[
  ['Parcela', loc.label],
  ['Nombre comercial', loc.tradeName],
  ['Titular / razón social', loc.legalName],
  ['Actividad', loc.activityType],
  ['Grupo', loc.group],
  ['Indicación', loc.street]
]
```

Añadir al final `button.co` con `dataset.coords = loc.lat + ',' + loc.lon`. No concatenar `legalName` en atributos, IDs ni textos accesibles de la cabecera.

- [ ] **Step 5: Implementar exclusividad y cierres**

Mantener:

```javascript
let expanded = null;
```

- `openDetail()` cierra el activo, crea el detalle, marca la fila y actualiza `aria-expanded`.
- `closeDetail()` elimina el detalle, limpia la clase y restaura opcionalmente el foco.
- El clic en el mismo botón alterna abierto/cerrado.
- El clic en otro botón sustituye el abierto.
- Un listener de `document` cierra cuando el objetivo no pertenece a la fila expandida.
- `update()` llama a `closeDetail({restoreFocus:false})` antes de reemplazar resultados.
- Escape cierra primero el detalle; solo limpia la consulta cuando no hay detalle abierto.
- El listener de copia existente continúa delegando sobre `.co` dentro del detalle y usa `TEXT.copied`/`LABEL.copied`.

- [ ] **Step 6: Añadir estilos operativos y movimiento reducido**

- `.detail-toggle` hereda tipografía y color del nombre, elimina apariencia de botón y conserva foco visible.
- `.row.expanded` mantiene la cabecera y permite que `.detail` ocupe `grid-column:1 / -1`.
- `.detail` usa fondo ligeramente elevado, borde superior sutil, espaciado compacto y una animación de entrada de 140–180 ms.
- Las etiquetas son pequeñas y apagadas; los valores son legibles.
- `.co` conserva área táctil mínima y confirmación en color de acento.
- Dentro de `prefers-reduced-motion:reduce`, no se ejecuta la animación.

- [ ] **Step 7: Ejecutar prueba enfocada y suite completa**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest `
  tests.test_build.LocationDisplayTests.test_inline_detail_contract_is_present -v
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 8: Punto de revisión sin commit**

Run:

```powershell
git diff --check
git diff -- src/template.html tests/test_build.py
```

Confirmar que la lista no contiene `legalName` antes de abrir el detalle y que el enlace de mapa permanece independiente.

---

### Task 4: Documentación, build y verificación de extremo a extremo

**Files:**
- Modify: `docs/02-datos.md`
- Modify: `docs/04-convenciones.md`
- Modify: `docs/05-mantenimiento.md`
- Generate: `dist/index.html`
- Generate: `dist/sw.js`

**Interfaces:**
- Consumes: modelo, datos y UI completados en Tasks 1–3.
- Produces: documentación coherente y artefacto estático listo para commit manual.

- [ ] **Step 1: Actualizar el contrato documental**

- `docs/02-datos.md`: documentar encabezados admitidos, grupo derivado de sección, prioridad del nombre público y exclusión de personas del índice.
- `docs/04-convenciones.md`: documentar las nuevas claves JSON y que el detalle se crea bajo demanda.
- `docs/05-mantenimiento.md`: explicar cómo distinguir `trade_name`, `legal_name` y `activity_type`, y advertir que nombres personales no se copian a `trade_name`.

- [ ] **Step 2: Ejecutar la suite completa antes del build**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
```

Expected: todas las pruebas en PASS, sin `__pycache__` nuevo.

- [ ] **Step 3: Generar `dist/`**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python scripts/build.py
```

Expected: salida `OK`, ubicaciones generadas, caracteres cubiertos, referencias de `dist/` válidas y `dist/sw.js` con una versión `u24-<12 hex>` sin `__APP_VERSION__`.

- [ ] **Step 4: Servir la aplicación localmente**

Run:

```powershell
python -m http.server 4173 --directory dist
```

Mantener el proceso en una sesión de terminal y abrir `http://127.0.0.1:4173/` con la herramienta de navegador.

- [ ] **Step 5: Verificar comportamiento y privacidad en navegador**

Ejecutar estos casos reales:

1. Estado inicial: la fila H-07 muestra `Dardos`; `Carbajo Gordillo, Vicente Manuel` no aparece en `document.body.innerText`.
2. Buscar `Carbajo Gordillo`: cero coincidencias.
3. Buscar `Dardos`: aparece H-07.
4. Pulsar `Dardos`: se abre el detalle y entonces aparece el titular, la actividad y las coordenadas.
5. Pulsar `Dardos` de nuevo: se cierra.
6. Abrir H-07 y después H-08: H-07 se cierra y H-08 se abre.
7. Pulsar fuera: el detalle activo se cierra.
8. Abrir un detalle y cambiar la consulta: el detalle se cierra.
9. Pulsar coordenadas: se anuncia `Coordenadas copiadas`.
10. Buscar `caseta tradicional`, `caseta juvenil` y `casetas`: aparecen únicamente los grupos esperados.
11. Buscar `CT-28`: aparece la fila pública `CT-25 | Paripé`.
12. Activar el icono de mapa: el enlace contiene las coordenadas correctas y no activa el desplegable.
13. Navegar por teclado: foco visible, Enter/Espacio alternan y Escape cierra restaurando el foco.

- [ ] **Step 6: Verificar salida compilada y caché**

Run:

```powershell
Select-String -LiteralPath dist/index.html -Pattern 'Paripé','Taray Aguadulce','function detail'
Select-String -LiteralPath dist/sw.js -Pattern "const CACHE = 'u24-[0-9a-f]{12}'"
Select-String -LiteralPath dist/sw.js -SimpleMatch '__APP_VERSION__'
```

Expected: los tres primeros patrones están presentes; la última búsqueda no devuelve resultados.

- [ ] **Step 7: Verificación final y entrega sin commit**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests -v
git diff --check
git status --short
git diff --stat
```

Revisar el diff completo. Deben aparecer únicamente `data.md`, parser, plantilla, pruebas, documentación aprobada y archivos generados de `dist/`. Detener el servidor local. Informar recuento de pruebas, versión de caché, archivos modificados, datos no resueltos y que no se realizó commit, push ni despliegue.
