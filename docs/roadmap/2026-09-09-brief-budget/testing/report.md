# Verificación de brief-budget — 2026-10-06

Veredicto: verde respecto a la spec ajustada; sin UI. La excepción de contrato irreducible es explícita y no permite delegar una tarea excesiva sin dividirla. No se afirma que todo el corpus quepa siempre en 10.000 caracteres.

## Evidencia ejecutada

- Suite final: `python -m pytest agent-kits/shared/test_task_brief.py tests/test_export_interop.py tests/test_hooks_config.py --cov ... -q` → **110 passed** (80 brief, 27 exportación, 3 configuración).
- Validación ampliada previa: brief/export/configuración/consola/copias → **574 passed**; tras ella se corrigieron los casos de frontera del brief y se repitió su suite final. Consola y copias permanecen sin cambios.
- Hooks: `node --test tests/hook-runtime.test.mjs tests/opencode-plugin.test.mjs` → **21 passed**. Suite Node ampliada previa: **124 passed**; las nuevas regresiones del runtime se validaron después por separado.
- Cobertura oficial coverage.py/pytest-cov de archivos Python cambiados: **94,45%** de media, mínimo configurado 90%; `task-brief.py` **97,10%**, `export-interop.py` **91,80%**. El gate changed-only con base HEAD devuelve exit 0, sin avisos. Esta métrica no incluye JavaScript ni Bash, que tienen pruebas de integración separadas.
- `lint_plugin.py`: 0 errores, 3 avisos preexistentes por nombres genéricos. `evals/check.py`: 41 piezas, 149 casos, 0 errores. `export-interop.py --check`: 50 archivos al día. Identidad de copias y consola incluidas en la validación ampliada. Ambos ledgers pasan ledger-lint sin incoherencias ni avisos.
- Revisión independiente: siete Important detectados y corregidos en tres intentos; último intento A/B sin gaps pendientes. Detalle y RED en tasks.md.
- Scope coordinado: unión de ambos ledgers autorizados, base HEAD, sin archivos fuera de alcance ni exclusiones de usuario. ECC solo documentado. Settings locales ajenos conservados.

## Medición real de las 22 tareas de referencia

Invocación normal con constitución real, memoria local y TDD configurado. Variante de referencia: mismo comando con `--constitucion <archivo inexistente>`; se muestra aparte para no confundirla con el comportamiento normal. Se cuentan caracteres Unicode del stdout completo, incluido el salto final, no bytes de wc -c. La ruta usada es relativa al repositorio.

| Tarea | Normal | Sin constitución | Acción en contexto normal |
|---|---|---|---|
| T-01 | 9998 | 7524 | cabe |
| T-02 | 10496 | 8122 | dividir: mínimo 10496 |
| T-03 | 10450 | 8077 | dividir: mínimo 10450 |
| T-04 | 9998 | 7084 | cabe |
| T-05 | 9998 | 7574 | cabe |
| T-06 | 10733 | 8213 | dividir: mínimo 10733 |
| T-07 | 9129 | 6097 | cabe |
| T-08 | 10145 | 7735 | dividir: mínimo 10145 |
| T-09 | 9436 | 6404 | cabe |
| T-10 | 10362 | 7840 | dividir: mínimo 10362 |
| T-11 | 9471 | 6439 | cabe |
| T-12 | 9634 | 6602 | cabe |
| T-13 | 9794 | 6762 | cabe |
| T-14 | 11166 | 8793 | dividir: mínimo 11166 |
| T-15 | 9353 | 6321 | cabe |
| T-16 | 10155 | 7638 | dividir: mínimo 10155 |
| T-17 | 11096 | 8723 | dividir: mínimo 11096 |
| T-18 | 10152 | 7594 | dividir: mínimo 10152 |
| T-19 | 9278 | 6246 | cabe |
| T-20 | 9800 | 6768 | cabe |
| T-21 | 8732 | 5700 | cabe |
| T-22 | 10766 | 8298 | dividir: mínimo 10766 |

Resultado normal: **12/22 caben**, **10/22 declaran un mínimo protegido excesivo**; máximo **11.166**. Sin constitución: **22/22 caben**, máximo **8.793**. Los 10 casos normales requieren dividir la tarea; no se ocultó su aviso ni se recortaron criterios o notas vigentes. El corpus completo de tests incluye constitución normal, diseño presente/ausente y memoria de 2.400 caracteres para comprobar el margen bajo carga.

## Límites de la validación

No se ha ejecutado una conversación real con un modelo en Claude, Codex u OpenCode. qa-gate.py espera resultados Playwright y no aplica a este cambio sin UI; no se fabrica results.json. Los contratos del runtime se validan con payloads y procesos reales. El presupuesto histórico se conserva; no hay medición de tokens/euros compatible con esta sesión Codex, por lo que no se inventa una calibración económica.

Puertas de cierre: retro-gate de brief-budget y hooks-runtime exit 0, retro presente y fila de calibración sin medición nueva. Generador instalado probado en ambas cachés: brief3500 caracteres, criterio y contrato de retorno presentes.
