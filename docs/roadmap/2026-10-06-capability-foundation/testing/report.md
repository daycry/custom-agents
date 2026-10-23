# Validación de la primera integración catálogo de referencia

Fecha: 2026-10-06. Base del diff: `0d9ce74`. Se valida nuestra implementación;
catálogo de referencia y Graphify se inspeccionaron como fuentes, sin ejecutar sus servicios.

## Contratos y cobertura

La suite de panel, racionalizaciones, tamaño de skills e índice del roadmap
ejecutó **97 passed, 1 skipped** en Windows/Python 3.13. La omisión corresponde
a creación de symlinks sin privilegios. El contrato NTFS de junction sí se
ejecutó y verifica que no se lea el directorio externo.

La suite del panel en Linux/Python 3.11 ejecutó **14 passed, 1 skipped**. Allí
se ejecuta el symlink real; solo se omite el contrato específico de Windows.
La imagen de desarrollo ejecutó una copia de tres fuentes públicas del plugin,
montada en solo lectura; el contenedor del ensayo se elimina al terminar.

`coverage-gate.py . --changed-only --base 0d9ce74 --min 90` con el runner oficial
pytest-cov devuelve **exit 0**, cobertura del único script de producción cambiado
**92,11 %**. No incluye prosa ni tests en el denominador.

El primer RED del panel, los RED de ruta OpenCode/lista YAML y el RED de junction
se conservan en el ledger. El pase adversarial añadió un RED de dos casos
para secretos entrecomillados y PEM largos; se redactan antes de resumir/serializar. Los tests cubren redacción de metadatos, exclusión de
cuerpos privados, escape HTML, fuentes ausentes/malformadas, presencia sin salud,
redactor ausente y protección de salidas ajenas.

## Navegador

El fichero [panel-ui.spec.cjs](panel-ui.spec.cjs) ejecutó los cuatro casos del
[test-plan](../test-plan.md) en Edge/Playwright: **4 passed, 0 failed, 0 flaky,
0 skipped**. `qa-gate.py` sobre el JSON real devuelve **VERDE**.

P-01 verifica el total de tarjetas y ausencia de errores JavaScript; P-02,
búsqueda; P-03, filtro y restablecimiento; P-04, viewport de 390×844 sin desborde.
El viewport de escritorio es 1440×1000. Se inspeccionó visualmente la captura
móvil generada por P-04. JSON, HTML generado y captura quedan fuera de Git.

Para repetir: instalar `@playwright/test` en un entorno de desarrollo aislado;
generar el HTML con `build_panel.py --html <ruta>`; establecer `PANEL_HTML` a esa
ruta absoluta y `PANEL_SCREENSHOT` a la captura de salida; ejecutar este spec con
el runner Playwright y su reporter JSON. `NODE_PATH` debe resolver esa instalación.

## Metadatos y exports

- `evals/check.py`: **47 ficheros, 167 casos, 0 errores** (101 positivos/66 negativos).
- `export-interop.py --check`: **exit 0, 52 ficheros al día** para Codex y OpenCode.
- Índice de sesión: **14 passed**, conservando sus límites de contexto.
- Después de versionar el script, cuatro casos de la suite de consola exigieron
  registrar su arranque en `MODOS`. Se añadió `--json` sin cambiar producción:
  **8 passed** en los casos específicos del panel, sin skips.
- Puerta completa posterior al registro: **917 passed, 0 failed, 0 skipped**
  (cifras medidas, índice del roadmap, consola e insignias del README). Un aviso
  histórico sobre un marcador citado en plugin-refactor, sin errores nuevos.
- Validator de skill-creator: las cinco skills nuevas válidas.
- Exportaciones y consola UTF-8: **469 passed** (`test_export_interop.py` y
  `test_console_encoding.py`), sin omisiones.
- `lint_plugin.py`: **0 errores**, tres avisos genéricos ya existentes.
- `scope-check.py --base 0d9ce74 --json`: **exit 0**, sin archivos fuera de alcance,
  sin avisos ni exclusiones de usuario. `.claude/settings.json` es un archivo
  preexistente del usuario y queda fuera del cambio.
- Selector adversarial: **A+B**; C y D no activadas por las heurísticas actuales.

El catálogo real contiene 10 agentes, 24 skills, 13 comandos, 9 herramientas
declaradas y 7 definiciones de hooks globales. Estos son conteos de fuentes;
no son medición de ejecución ni de calidad.

## Límites

La revisión adversarial A+B encontró dos Important en el intento 1, reproducidos
y corregidos. El intento 2 validó ambas correcciones sin gaps nuevos: **0 Critical,
0 Important, 0 Minor pendientes**. El HTML se regeneró tras el arreglo de redacción
y Playwright repitió los cuatro casos con qa-gate VERDE.
El intento 3 revisó el registro UTF-8 y el cierre documental sin gaps nuevos;
el código de producción permaneció igual al aprobado en el intento 2.

El piloto Graphify sigue definido en [comparison.md](../comparison.md), pendiente
de ejecución. No se afirma mejora de recuperación ni equivalencia de sus
benchmarks con nuestros proyectos. No se ha migrado memoria ni instalado MCP,
observadores o skills de los upstream. La validación se centra en el diff; no
repite la suite completa ya registrada al cerrar plugin-refactor.
