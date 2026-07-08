#!/usr/bin/env node
/**
 * to-pdf.mjs — convierte .md / .html / .docx a PDF con aspecto moderno.
 * Tubería: (markdown-it | mammoth | passthrough) -> HTML -> inyecta tema CSS -> Chromium headless (puppeteer) -> PDF.
 *
 * Uso:
 *   node to-pdf.mjs <entrada.(md|markdown|html|htm|docx)> [--out salida.pdf] [--theme theme.css] [--title "Título"]
 *
 * Notas:
 *   - Requiere que las dependencias (markdown-it, mammoth, puppeteer) estén instaladas
 *     junto a este script (node_modules en el mismo directorio).
 *   - Si no se pasa --out, escribe junto a la entrada con extensión .pdf.
 *   - Si no se pasa --theme, usa theme.css contiguo a este script (si existe).
 */
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, extname, basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import MarkdownIt from 'markdown-it';
import mammoth from 'mammoth';
import puppeteer from 'puppeteer';

const __dirname = dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') args.out = argv[++i];
    else if (a === '--theme') args.theme = argv[++i];
    else if (a === '--title') args.title = argv[++i];
    else args._.push(a);
  }
  return args;
}

async function toBodyHtml(input) {
  const ext = extname(input).toLowerCase();
  if (ext === '.md' || ext === '.markdown') {
    const md = new MarkdownIt({ html: true, linkify: true, typographer: true });
    return md.render(await readFile(input, 'utf8'));
  }
  if (ext === '.html' || ext === '.htm') {
    const html = await readFile(input, 'utf8');
    const m = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    return m ? m[1] : html;
  }
  if (ext === '.docx') {
    const { value } = await mammoth.convertToHtml({ path: input });
    return value;
  }
  throw new Error(`Formato no soportado: "${ext}". Usa .md, .markdown, .html, .htm o .docx.`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const input = args._[0];
  if (!input) {
    console.error('Uso: node to-pdf.mjs <archivo.(md|html|docx)> [--out salida.pdf] [--theme theme.css] [--title "Título"]');
    process.exit(1);
  }
  if (!existsSync(input)) {
    console.error(`No existe la entrada: ${input}`);
    process.exit(1);
  }

  const out = args.out || input.replace(/\.[^.]+$/, '') + '.pdf';
  const themePath = args.theme || join(__dirname, 'theme.css');
  const theme = existsSync(themePath) ? await readFile(themePath, 'utf8') : '';
  const title = args.title || basename(input).replace(/\.[^.]+$/, '');

  const body = await toBodyHtml(input);
  const doc = `<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>${title}</title><style>${theme}</style></head>
<body><main class="doc">${body}</main></body>
</html>`;

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--font-render-hinting=none'] });
  try {
    const page = await browser.newPage();
    await page.setContent(doc, { waitUntil: 'networkidle0' });
    await page.pdf({
      path: out,
      format: 'A4',
      printBackground: true,
      margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' },
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate:
        '<div style="width:100%;font-size:8px;color:#9aa0a6;padding:0 16mm;text-align:right;">' +
        '<span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    });
    console.log(`OK -> ${out}`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e && e.message ? e.message : e);
  process.exit(1);
});
