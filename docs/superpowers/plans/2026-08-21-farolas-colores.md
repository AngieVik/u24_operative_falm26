# Identificación visual de farolas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renombrar las 23 ubicaciones como `Farola <código>` y distinguir cada fila con una barra lateral semántica según su prefijo A/B/C/D, sin afectar las parcelas ni la búsqueda.

**Architecture:** `data.md` mantiene los nombres y coordenadas; `scripts/build.py` deriva un marcador semántico validado y lo incorpora al objeto de ubicación; `src/template.html` traduce ese marcador a una clase CSS y a una barra continua en el borde izquierdo. La búsqueda continúa usando `label`, `name`, `search` y `flat`, por lo que admite tanto el código como el nombre completo.

**Tech Stack:** Python 3 estándar, `unittest`, Markdown, HTML, CSS y JavaScript sin dependencias nuevas.

**Spec:** `docs/superpowers/specs/2026-08-21-farolas-colores-design.md`

## Global Constraints

- Los 23 identificadores y sus coordenadas no cambian.
- Los nombres usan exactamente `Farola <código>`.
- A = azul `#3B82F6`; B = verde `#22C55E`; C = rojo `#EF4444`; D = amarillo `#FACC15`.
- Una única barra vertical continua de 4 px ocupa el borde izquierdo de toda la fila.
- La barra no desplaza el código ni el nombre respecto a las demás ubicaciones.
- Solo las farolas reciben marcador; las parcelas y demás ubicaciones conservan su aspecto.
- El color no es la única señal: el código y el texto `Farola` permanecen visibles.
- No se añaden dependencias, no se compila, no se modifica `dist/` y no se crea ningún commit sin autorización expresa.

---

### Task 1: Derivar el marcador semántico de una farola

**Files:**
- Modify: `tests/test_build.py`
- Modify: `scripts/build.py:69-78,152-188`

**Interfaces:**
- Consumes: `label: str` y `name: str` de cada fila de `data.md`.
- Produces: `farola_marker(label: str, name: str) -> str` y la propiedad `marker` del objeto de ubicación con uno de `blue`, `green`, `red`, `yellow` o cadena vacía.

- [ ] **Step 1: Escribir las pruebas fallidas de clasificación**

Añadir a `LocationDisplayTests`:

```python
    def test_farola_marker_follows_code_prefix(self):
        cases = {
            "A8": "blue",
            "B8": "green",
            "C7": "red",
            "D3": "yellow",
        }

        for label, expected_marker in cases.items():
            with self.subTest(label=label):
                location = build.build_locations(
                    [(1, [label, f"Farola {label}", "", "36.839427,-2.431177"])]
                )[0]
                self.assertEqual(location["marker"], expected_marker)
                self.assertIn(f"farola {label.lower()}", location["search"])
                self.assertIn(label.lower(), location["flat"])

    def test_non_farola_does_not_receive_marker(self):
        location = build.build_locations(
            [(1, ["A-01", "Montaña Jet Star", "", "36.834454,-2.430808"])]
        )[0]

        self.assertEqual(location["marker"], "")
```

- [ ] **Step 2: Ejecutar las pruebas y confirmar el rojo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
```

Expected: las dos pruebas nuevas fallan con `KeyError: 'marker'`; las tres pruebas existentes continúan pasando.

- [ ] **Step 3: Implementar la clasificación mínima**

Añadir cerca de las expresiones regulares de `scripts/build.py`:

```python
FAROLA_LABEL_RE = re.compile(r"^[A-D]\d+$")
FAROLA_COLORS = {
    "A": "blue",
    "B": "green",
    "C": "red",
    "D": "yellow",
}
```

Añadir antes de `build_locations`:

```python
def farola_marker(label, name):
    """Color semantico de una farola valida; vacio para cualquier otra ubicacion."""
    if not FAROLA_LABEL_RE.fullmatch(label) or name != f"Farola {label}":
        return ""
    return FAROLA_COLORS[label[0]]
```

Incorporar la propiedad sin modificar los campos de búsqueda:

```python
                "marker": farola_marker(label, name),
```

- [ ] **Step 4: Ejecutar la suite y confirmar el verde**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
```

Expected: 5 pruebas, 5 aprobadas.

---

### Task 2: Renombrar y validar las 23 farolas reales

**Files:**
- Modify: `tests/test_build.py`
- Modify: `data.md:117-139`

**Interfaces:**
- Consumes: las 23 filas con etiquetas `A8` a `C1` ya existentes.
- Produces: nombres exactos `Farola <código>` con etiquetas y coordenadas intactas.

- [ ] **Step 1: Escribir la prueba fallida del conjunto real**

Añadir a `LocationDisplayTests`:

```python
    def test_farola_dataset_keeps_codes_coordinates_and_expected_markers(self):
        expected = {
            "A8": ("36.839427", "-2.431177", "blue"),
            "B8": ("36.839061", "-2.430659", "green"),
            "A7": ("36.837703", "-2.431197", "blue"),
            "B7": ("36.837688", "-2.430670", "green"),
            "C7": ("36.837517", "-2.430173", "red"),
            "A6": ("36.836735", "-2.431184", "blue"),
            "B6": ("36.836732", "-2.430665", "green"),
            "C6": ("36.836734", "-2.429810", "red"),
            "A5": ("36.836337", "-2.431245", "blue"),
            "A4": ("36.835837", "-2.431208", "blue"),
            "B4": ("36.835825", "-2.430450", "green"),
            "C4": ("36.835837", "-2.429779", "red"),
            "A3": ("36.835113", "-2.431211", "blue"),
            "B3": ("36.835111", "-2.430444", "green"),
            "C3": ("36.835109", "-2.429785", "red"),
            "D3": ("36.835109", "-2.429147", "yellow"),
            "A2": ("36.834292", "-2.431228", "blue"),
            "B2": ("36.834266", "-2.430445", "green"),
            "C2": ("36.834269", "-2.429797", "red"),
            "D2": ("36.834265", "-2.428882", "yellow"),
            "A1": ("36.832943", "-2.431212", "blue"),
            "B1": ("36.832815", "-2.430459", "green"),
            "C1": ("36.832799", "-2.429789", "red"),
        }
        sections = build.read_sections()
        rows = build.drop_header(sections["ubicaciones"], "ubication_number")
        by_label = {location["label"]: location for location in build.build_locations(rows)}

        for label, (lat, lon, marker) in expected.items():
            with self.subTest(label=label):
                location = by_label[label]
                self.assertEqual(location["name"], f"Farola {label}")
                self.assertEqual((location["lat"], location["lon"]), (lat, lon))
                self.assertEqual(location["marker"], marker)
                self.assertIn(label.lower(), location["search"])
                self.assertIn(f"farola {label.lower()}", location["search"])
```

- [ ] **Step 2: Ejecutar la prueba y confirmar el rojo**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
```

Expected: falla al comparar `A8` con `Farola A8`; el fallo demuestra que la prueba observa los datos reales.

- [ ] **Step 3: Cambiar solo los nombres de las 23 filas**

En `data.md`, conservar primera, tercera y cuarta columna y sustituir únicamente la segunda:

```markdown
| A8 | Farola A8 | | 36.839427,-2.431177 |
| B8 | Farola B8 | | 36.839061,-2.430659 |
```

Aplicar el mismo patrón literal a las 23 filas, hasta:

```markdown
| C1 | Farola C1 | | 36.832799,-2.429789 |
```

- [ ] **Step 4: Ejecutar la suite y confirmar el verde**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
```

Expected: 6 pruebas, 6 aprobadas.

---

### Task 3: Pintar una única barra en el borde de la fila

**Files:**
- Modify: `src/template.html:123-136,425-434`

**Interfaces:**
- Consumes: `loc.marker` producido por `build_locations`.
- Produces: clases `farola farola-blue|green|red|yellow` en el `<li>` y una barra de 4 px mediante CSS.

- [ ] **Step 1: Definir los colores y la geometría de la barra**

Añadir después de `.row`:

```css
.row.farola{
  box-sizing:border-box;
  border-inline-start:4px solid var(--farola-color);
  padding-inline-start:calc(var(--pad) - 4px);
}
.row.farola-blue{--farola-color:#3B82F6}
.row.farola-green{--farola-color:#22C55E}
.row.farola-red{--farola-color:#EF4444}
.row.farola-yellow{--farola-color:#FACC15}
```

La resta de 4 px mantiene el código en la posición horizontal existente. No modificar `.num`, `.nom`, `.txt`, `.co`, `.go` ni el fondo de `.row`.

- [ ] **Step 2: Aplicar la clase solo cuando exista un marcador validado**

En `row(loc)`, inmediatamente después de `li.className = 'row';`, añadir:

```javascript
  if (loc.marker) li.classList.add('farola', 'farola-' + loc.marker);
```

`loc.marker` solo puede contener los cuatro valores generados por Python; las demás ubicaciones reciben cadena vacía y no cambian de clase.

- [ ] **Step 3: Revisar el contrato estático sin compilar**

Run:

```powershell
rg -n -F -e '.row.farola{' -e '.row.farola-blue' -e '.row.farola-green' -e '.row.farola-red' -e '.row.farola-yellow' -e "li.classList.add('farola', 'farola-' + loc.marker)" src\template.html
```

Expected: seis coincidencias: bloque base, cuatro colores y asignación de clase. La verificación visual en navegador queda pendiente hasta que el usuario compile.

---

### Task 4: Documentar el contrato operativo

**Files:**
- Modify: `docs/01-producto.md:43-61`
- Modify: `docs/02-datos.md:16-47`

**Interfaces:**
- Consumes: comportamiento implementado en las tareas 1-3.
- Produces: documentación que permite mantener los nombres, colores y búsqueda sin leer el código.

- [ ] **Step 1: Añadir el requisito funcional**

En la tabla de requisitos de `docs/01-producto.md`, añadir una fila:

```markdown
| RF-18 | Las farolas se nombran `Farola <código>` y muestran una barra lateral por zona: A azul, B verde, C rojo y D amarillo. El código y el nombre siguen siendo buscables. |
```

- [ ] **Step 2: Documentar el campo derivado**

En la tabla de campos de `docs/02-datos.md`, añadir:

```markdown
| `marker` | texto | derivado | Color semántico de una farola: `blue`, `green`, `red`, `yellow` o vacío para cualquier otra ubicación. |
```

Después de `Parcelas agrupadas`, añadir un apartado `### Farolas` con este contenido:

```markdown
Las farolas usan los códigos A1–A8, B1–B4/B6–B8, C1–C4/C6–C7 y D2–D3,
con el nombre literal `Farola <código>`.
El prefijo determina su barra lateral: A azul, B verde, C rojo y D amarillo.
El marcador visual no sustituye al texto y no altera `label`, `search` ni `flat`.
```

---

### Task 5: Verificación integral sin compilar

**Files:**
- Verify: `data.md`
- Verify: `scripts/build.py`
- Verify: `src/template.html`
- Verify: `tests/test_build.py`
- Verify: `docs/01-producto.md`
- Verify: `docs/02-datos.md`

**Interfaces:**
- Consumes: todos los cambios anteriores.
- Produces: evidencia fresca de integridad y una lista explícita de verificaciones pendientes.

- [ ] **Step 1: Ejecutar toda la suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
```

Expected: 6 pruebas, 6 aprobadas, sin errores ni advertencias.

- [ ] **Step 2: Ejecutar los validadores internos de solo lectura**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -c 'import scripts.build as b; s=b.read_sections(); rows=b.drop_header(s.get("ubicaciones", []), "ubication_number"); locs=b.build_locations(rows); b.check_unique(locs); center, median, outliers=b.check_coherence(locs); sr=b.drop_header(s.get("calles", []), "street"); streets, missing, warnings=b.build_streets(sr, locs, center); chars=b.check_charset(locs, streets, b.TEMPLATE.read_text(encoding="utf-8")); farolas=[x for x in locs if x["marker"]]; assert len(locs)==131; assert len(farolas)==23; assert not sr; assert not outliers; assert {x["marker"] for x in farolas}=={"blue","green","red","yellow"}; print("locations=131"); print("farolas=23"); print("streets=0"); print("outliers=0"); print("markers=blue,green,red,yellow"); print("charset="+str(chars))'
```

Expected: 131 ubicaciones, 23 farolas, cero calles, cero valores atípicos y los cuatro marcadores presentes.

- [ ] **Step 3: Revisar el diff y el alcance**

Run:

```powershell
git diff -- data.md scripts/build.py src/template.html tests/test_build.py docs/01-producto.md docs/02-datos.md
git status --short
```

Confirmar que no cambian coordenadas, direcciones, parcelas, dependencias ni archivos bajo `dist/`. No crear commit.

- [ ] **Step 4: Informar la comprobación pendiente**

Indicar expresamente en la entrega que no se compiló ni se verificó visualmente el HTML generado. La próxima compilación del usuario actualizará `dist/index.html`; después debe comprobarse en móvil que la barra ocupa toda la fila, mantiene alineados los textos y distingue los cuatro colores sobre el fondo oscuro.
