---
name: to-pdf
description: >
  Convierte archivos a PDF con aspecto moderno. Soporta Markdown (.md/.markdown),
  HTML (.html/.htm) y Word (.docx). Tubería HTML/CSS renderizada con Chromium
  headless (puppeteer) y un tema CSS moderno. Úsala cuando el usuario diga
  "convertir a PDF", "pasar a PDF", "exportar a PDF", "genera un PDF de",
  "markdown a pdf", "html a pdf", "word a pdf", "docx a pdf".
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# to-pdf — conversión a PDF con aspecto moderno

Convierte `.md`, `.html` y `.docx` a PDF. Motor: cada entrada se transforma a HTML
(`markdown-it` para Markdown, `mammoth` para Word, passthrough para HTML), se le inyecta
un **tema CSS moderno** y se renderiza con **Chromium headless** vía `puppeteer`.

## Requisitos
- **Node.js** (v18+). Comprueba con `node --version`. Si no está, avisa al usuario (no lo instales tú).
- Las dependencias (`markdown-it`, `mammoth`, `puppeteer`) se instalan **fuera del repo**, en
  `~/.claude/tool-cache/to-pdf/`. `puppeteer` descarga Chromium (~150 MB) en la primera instalación.

## Paso 0 — localizar la skill (scope proyecto/usuario/plugin)
```bash
PDFSKILL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*skills/to-pdf' 2>/dev/null | head -1)"
```

## Paso 1 — preparar el entorno (idempotente; PIDE PERMISO antes de instalar)
El motor vive en una carpeta escribible fuera del repo/plugin (los plugins se instalan en solo-lectura):
```bash
CACHE="$HOME/.claude/tool-cache/to-pdf"
mkdir -p "$CACHE"
cp "$PDFSKILL/scripts/"*.mjs "$PDFSKILL/scripts/package.json" "$PDFSKILL/assets/theme.css" "$CACHE/"
```
Si `"$CACHE/node_modules"` no existe, **detente y pide permiso** al usuario (avisa: instala
`puppeteer` + `markdown-it` + `mammoth` y descarga Chromium, ~150 MB). Solo si acepta:
```bash
( cd "$CACHE" && npm install --no-audit --no-fund )
```

## Paso 2 — convertir
```bash
node "$CACHE/to-pdf.mjs" "<ENTRADA>" --out "<SALIDA.pdf>" --title "<Título opcional>"
# El tema por defecto es "$CACHE/theme.css". Puedes pasar otro con --theme "<ruta.css>".
```
- Si omites `--out`, escribe el PDF junto a la entrada (misma ruta, extensión `.pdf`).
- Para **varios ficheros**, repite el comando por cada entrada (o itera con un bucle).

## Paso 3 — entregar
Confirma la(s) ruta(s) del PDF generado. Si alguna conversión falla, muestra el error concreto
(formato no soportado, Node ausente, dependencias sin instalar) y cómo resolverlo.

## Notas
- **Formatos:** `.md`, `.markdown`, `.html`, `.htm`, `.docx`. Otros → error explícito.
- **HTML de entrada:** si trae `<body>`, se usa su contenido; si es un fragmento, se usa tal cual.
- **DOCX:** `mammoth` extrae HTML semántico (títulos, listas, tablas, negritas); imágenes embebidas se incrustan. El maquetado exacto de Word no se reproduce al 100 %: prioriza estructura + el tema moderno.
- **Personalizar estilo:** edita/duplica `theme.css` y pásalo con `--theme`.

## Política de ejecución y recursos

Por defecto Chromium conserva su sandbox, JavaScript está desactivado y el render no carga recursos web ni archivos locales referenciados por el documento. Los recursos data/blob embebidos siguen disponibles. Un recurso bloqueado produce un aviso; revisa el PDF antes de entregarlo.

- `--allow-js`: permite scripts sólo para documentos de confianza, por ejemplo gráficos HTML.
- `--allow-origin https://assets.example.com`: permite recursos de ese origen HTTPS exacto; repite el flag para otros orígenes. Rutas, credenciales y parámetros no se admiten.
- `--unsafe-no-sandbox`: excepción explícita para un entorno aislado donde Chromium no pueda iniciar con sandbox; se muestra un aviso. No se usa automáticamente al fallar.

La política de recursos del render no sustituye el aislamiento del sistema al ejecutar JavaScript autorizado. El tema CSS se inserta como texto de estilo, el título se escapa y la salida atómica sigue conservando el PDF anterior si falla la conversión.
