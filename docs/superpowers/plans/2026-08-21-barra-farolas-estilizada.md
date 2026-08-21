# Barra estilizada para farolas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sustituir la barra lateral de altura completa por un indicador de 4 × 40 px, centrado y redondeado.

**Architecture:** La fila `.row.farola` seguirá recibiendo su color mediante `--farola-color`. Un pseudoelemento `::before`, posicionado de forma absoluta, dibujará el indicador sin participar en el flujo ni cambiar la alineación del contenido.

**Tech Stack:** HTML, CSS y pruebas unitarias con `unittest` de Python.

**Spec:** `docs/superpowers/specs/2026-08-21-barra-farolas-estilizada-design.md`

## Global Constraints

- Modificar únicamente `src/template.html` y la prueba estática correspondiente en `tests/test_build.py`.
- Mantener los colores semánticos existentes.
- No modificar `data.md`, el modelo generado ni el comportamiento de búsqueda.
- No modificar `dist/` ni compilar el proyecto. `dist/index.html` ya contiene un
  cambio externo previo a esta ejecución y debe conservarse byte a byte.
- No crear commits.

---

### Task 1: Indicador lateral estilizado

**Files:**
- Modify: `tests/test_build.py`
- Modify: `src/template.html:129-137`

**Interfaces:**
- Consumes: la clase `farola` y la variable CSS `--farola-color` ya asignadas a cada fila.
- Produces: `.row.farola::before`, un indicador decorativo de 4 × 40 px que no altera el flujo.

- [x] **Step 1: Añadir la prueba estática que define el nuevo contrato visual**

```python
def test_farola_bar_is_centered_short_and_rounded(self):
    template = build.TEMPLATE.read_text(encoding="utf-8")

    self.assertIn(".row.farola::before{", template)
    self.assertIn("width:4px;height:40px", template)
    self.assertIn("top:50%", template)
    self.assertIn("transform:translateY(-50%)", template)
    self.assertIn("border-radius:999px", template)
    self.assertNotIn("border-inline-start:4px solid var(--farola-color)", template)
```

- [x] **Step 2: Ejecutar la prueba para comprobar que falla con la barra actual**

Run: `$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest discover -s tests -p test_build.py -k farola_bar -v`

Expected: `FAIL` porque `.row.farola::before` aún no existe.

- [x] **Step 3: Sustituir el borde completo por el pseudoelemento**

```css
.row.farola{
  position:relative;
  box-sizing:border-box;
}
.row.farola::before{
  content:"";
  position:absolute;
  inset-inline-start:0;top:50%;
  width:4px;height:40px;
  border-radius:999px;
  background:var(--farola-color);
  transform:translateY(-50%);
  pointer-events:none;
}
```

La eliminación del borde devuelve automáticamente el comienzo del contenido a `var(--pad)`, heredado de `.row`, y conserva la alineación de todas las filas.

- [x] **Step 4: Ejecutar la prueba específica y confirmar que pasa**

Run: `$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest discover -s tests -p test_build.py -k farola_bar -v`

Expected: `OK`, una prueba ejecutada.

- [x] **Step 5: Ejecutar toda la suite**

Run: `$env:PYTHONDONTWRITEBYTECODE='1'; py -3 -m unittest discover -s tests -v`

Expected: todas las pruebas terminan en `OK`.

- [x] **Step 6: Revisar alcance y formato sin compilar**

Run: `git diff --check`

Expected: salida sin errores de espacios en blanco; los avisos de conversión LF/CRLF no son errores.

Run antes y después: `(Get-FileHash -Algorithm SHA256 dist/index.html).Hash`

Expected: el hash final coincide exactamente con el inicial.

Run: `git diff -- src/template.html tests/test_build.py`

Expected: únicamente la prueba del contrato visual y la sustitución del borde por el pseudoelemento.
