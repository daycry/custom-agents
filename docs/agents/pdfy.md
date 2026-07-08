# Documentación del agente `pdfy`

Agente que **convierte archivos a PDF con aspecto moderno**. Acepta **Markdown**, **HTML** y **Word (.docx)**. Orquesta la skill compartida `to-pdf`, que hace la conversión real.

---

## 1. Qué hace y cómo

La tubería (en la skill `to-pdf`): cada entrada se transforma a HTML —`markdown-it` para Markdown, `mammoth` para `.docx`, passthrough para HTML— se le inyecta un **tema CSS moderno** y se renderiza a PDF con **Chromium headless** (`puppeteer`). El resultado tiene tipografía cuidada, tablas con estilo, bloques de código, numeración de páginas y buen paginado (evita cortar tablas/código).

| Entrada | Cómo se procesa |
|---------|-----------------|
| `.md` / `.markdown` | `markdown-it` → HTML |
| `.html` / `.htm` | se usa el `<body>` (o el fragmento tal cual) |
| `.docx` | `mammoth` → HTML semántico (títulos, listas, tablas, negritas, imágenes) |

---

## 2. Requisitos y dependencias

- **Node.js** (v18+) en la máquina. Si no está, el agente avisa (no lo instala él).
- Las dependencias (`markdown-it`, `mammoth`, `puppeteer`) se instalan **fuera del repo**, en `~/.claude/tool-cache/to-pdf/`. `puppeteer` descarga Chromium (~150 MB) la primera vez. El agente **pide permiso antes de instalar**, igual que `nemesis` con su toolkit.

---

## 3. Salida

Por defecto el PDF se escribe **junto al original** (misma ruta, extensión `.pdf`). Se puede indicar otra carpeta de salida (p. ej. `docs/exports/`). Convierte **uno o varios** ficheros en una misma invocación.

---

## 4. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente pdfy con README.md`
- `pdfy, convierte a PDF docs/informe.docx`
- `pasa a PDF estos ficheros: a.md, b.html, c.docx`
- `exporta este markdown a PDF` (si pegas el contenido, lo guarda y lo convierte)

La primera vez confirma qué convertir, dónde guardarlo y, si falta el motor, pide permiso para instalarlo.

---

## 5. Personalizar el estilo

El aspecto lo define `skills/to-pdf/assets/theme.css` (tipografía, colores, márgenes, cabecera/pie). Para un look distinto, edita o duplica ese CSS y pásalo con `--theme <ruta.css>`. Al ser una **skill compartida**, otros agentes del bundle pueden reutilizar `to-pdf` para exportar sus salidas a PDF.

---

## 6. Límites

Reproduce **estructura**, no el maquetado exacto de Word: un `.docx` muy diseñado no saldrá idéntico, pero sí bien estructurado y con el tema moderno. Formatos fuera de `.md/.html/.docx` se rechazan con un mensaje claro.
