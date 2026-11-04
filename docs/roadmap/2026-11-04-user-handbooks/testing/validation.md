# Validación de los manuales

Fecha: 2026-11-04. Incremento documental sobre `950fde8`. Sin cambios de runtime, modelos, suscripciones o preferencias privadas.

## Contenido y ediciones

Dos fuentes españolas: `docs/guides/subscription-efficiency.md` y `docs/guides/quality-playbook.md`. Sus PDF son independientes del manual operativo anterior. Los índices existentes en inglés y español enlazan las nuevas guías e identifican su idioma.

La primera guía tiene 15 capítulos; la segunda, 16. Incluyen rutinas, prompts copiables, criterios de decisión, ejemplos y glosarios. El ejemplo de portal interno recorre requisitos, evaluación, diseño opcional, tareas, implementación, revisión, QA y entrega. Hay ejemplos adicionales de errores, UI, publicación y memoria. Ningún ejemplo utiliza datos reales de una organización.

Los manifiestos de cada PDF registran SHA-256 del PDF y de su Markdown normalizado a LF, más las fuentes de los diagramas. Los tests comprueban que una edición no queda silenciosamente desactualizada. No prueban que toda afirmación de un proveedor vaya a seguir siendo válida en el futuro.

| Comprobación | Resultado |
|---|---|
| Enlaces locales de ambos manuales | 24 válidos, 0 rotos |
| `pytest tests/test_user_handbooks.py tests/test_roadmap_index.py -q --tb=short` | 70 passed |
| `scripts/lint_plugin.py` | 0 errores, 16 avisos |
| `evals/check.py` | 60 piezas, 229 casos, 0 errores |
| `scripts/export-interop.py --check` | 92 ficheros al día |
| `scripts/check-handbook.py` | Manual operativo anterior y sus fuentes/diagramas coinciden |
| `ledger-lint.py` | Sin incoherencias tras usar estados válidos |
| `git diff --check` | Exit 0 |

Los nueve avisos nuevos del linter son comandos nativos de proveedor citados y enlazados en la guía (`/usage`, `/status`, `/context`, `/model`, `/effort`, `/compact`, `/mcp`, `/fast` y `/fork`). No son comandos nuevos del plugin. La pasada final registra el número actualizado; no se relaja el linter para ocultarlos. Los siete avisos previos no se modifican.

## Verificación visual y de contenido

ReportLab genera los PDF con Arial, cuerpo 11,2 pt, tablas 9,5 pt y prompts monoespaciados de 9 pt. Los diagramas provienen de los bloques Mermaid del Markdown. PyMuPDF renderizó todas las páginas y extrajo el texto de su área útil; PIL compuso contact sheets.

Se contrastó cada párrafo, celda y línea de código de la fuente con la extracción, normalizando puntuación y espacios. No se usa este método para certificar el contenido textual de una imagen: los diagramas se contrastan por hash y visualmente. Se revisaron diagramas, tablas de comandos, páginas de glosario, portadas, índices y páginas finales a escala de lectura. Se corrigieron los diagramas horizontales ilegibles y los saltos que dejaban párrafos aislados.

Resultados finales en [pdf-validation.json](pdf-validation.json): uso eficiente, 19 páginas, 3 diagramas, 317 bloques presentes; resultados de calidad, 25 páginas, 5 diagramas, 494 bloques presentes. Sin omisiones detectadas ni cajas de texto fuera del área permitida. Los enlaces PDF a otros documentos del repositorio apuntan a `master`; estarán disponibles allí cuando se integre la PR. Los Markdown se pueden usar desde esta rama.

Los renders y herramientas de autoría permanecen como temporales ignorados. Las fuentes, PDF, manifiestos y resultados de validación se versionan. No se ha inspeccionado el corpus privado ni ejecutado un benchmark pagado para prometer ahorro de cuota.
