# Evidencia de remediación

Estado: pruebas dirigidas verdes; revisión y CI pendientes. Sin publicación npm/release.

## T-01 — vistas

RED previo: Edge real, tres vistas, tres onerror ejecutados; 0 passed/3 failed. Tras DOM seguro y renderer JSON: 9 passed en Edge sin skips y 9 tests del renderer correctos. Caso adicional de delimitadores literales observó RED (ValueError) y se corrigió. Servicios reales no usados; sólo fixture MCP. No se acredita aislamiento del host Cowork.

## T-02 — PDF

RED previo: 7 fallos de la CLI real con navegador sustituido por fixture, por sandbox desactivado y ausencia de política JS/red. GREEN: 7 pruebas de política y 5 de salida atómica. Conversión adicional real con dependencias existentes, copia aislada del script y Chromium con sandbox predeterminado: exit 0, 1 página, 32023 bytes; texto y acentos presentes; SCRIPT_CHANGED ausente; aviso de recurso remoto bloqueado. No se instaló ni modificó ninguna dependencia del usuario.

## T-03 — CI

TDD n/a: configuración/prosa; contratos de regresión escritos y observados rojos (5 fallos previos). GREEN: permisos, SHA, secretos por paso y paridad manual validados. Los pins se comprobaron en metadatos oficiales el 2026-11-06. No se ejecutó el workflow de publicación ni llamadas headless de pago.

## T-04 — herramientas

RED previo del contrato: el instalador seleccionaba /releases/latest al ejecutar. GREEN inicial: 13 pruebas offline; final: 17; integridad incorrecta, archivo ajeno/modificado, archivos inseguros/enlaces/ambigüedad, plataforma ausente, raíz dentro de Git/enlace cuando el SO lo permite, scripts y pip aislado con hashes. Caso adicional de quoting observado rojo y corregido: los argumentos que no son rutas conservan sus barras literales. Descargas para obtener pins: sólo metadatos/archivos upstream leídos, nunca ejecutados. No se instalaron herramientas reales. Catálogo y requirements son configuración revisada, TDD n/a.

## Puertas locales

- Python: tests/test_nemesis_tools.py, test_artifact_renderer.py, test_ci_security.py, test_ci_manual_copy.py, test_skill_size.py, test_ci_skill_suites.py: 85 passed (final).
- Node final: artifact-dom-security, to-pdf-security y to-pdf-atomic: 24 passed, 0 failed, 0 skipped (9 Edge + 3 JQL real-script + 12 PDF/atómicos).
- check-handbook: PDF, fuentes LF, workflows y diagramas coinciden.
- evals/check: 229 casos, 60 piezas, 0 errores; no llamadas al modelo.
- export-interop --check: 92 ficheros al día; no se tocaron agentes/comandos/hooks canónicos.
- scope-check --base facad5f: 36 archivos dentro del alcance, ninguno excluido ni fuera; antes del commit del plan advirtió ausencia de línea base de criterios.
- review-lens-select --base facad5f: A+B+C; C por workflows e innerHTML; D no aplica.

El verde global requiere la revisión y la CI de referencia de esta revisión exacta.

## Revisión y comprobaciones finales locales

Tres intentos A+B+C: A-01, B1 y B2 corregidos con regresiones dedicadas; tercer intento sin Critical/Important. Minor de referencia CONFIG_FILE corregido después de observar su test ampliado rojo; 27 tests de renderer/tools pasan. Apoyo Claude CLI: revisión recibida, hallazgos verificados, sin ejecución de servicios ni herramientas. Claude-04 ya estaba corregido, Claude-05/06 corregidos tras RED documentado. No hay hallazgos aceptados pendientes; no implica garantía de ausencia de malware.

Pins de source testssl/sqlmap/nikto: los tres archivos leídos coinciden con sus SHA del lock; extracción validada en memoria, 94/643/80 archivos regulares respectivamente, sin instalar ni ejecutar. Conversión PDF real ya documentada arriba, sin excepciones unsafe.

Linter sobre snapshot público bb5ca20 sin informes privados/descargas: 0 errores, 17 avisos existentes. El primer intento sobre checkout con evidencia ignorada recorrió copias históricas del paquete y dio 142 errores; no fue aceptado como verde ni motivó relajar reglas. La CI opera desde el checkout público y es la referencia final para el linter.

Interop final: 92 ficheros al día tras actualizar la instrucción canónica de nemesis. Ledger-lint: 0 incoherencias y 0 avisos; scope final: 44 archivos, ninguno excluido/fuera ni criterios alterados. Sin umbrales relajados ni tests omitidos nuevos.

Referencia CI en progreso: https://github.com/daycry/custom-agents/actions/runs/42194828544 (head 2bbfbc9). No se acredita completa hasta obtener resultado.
