# Evidencia de remediación

Estado: pruebas dirigidas verdes; revisión y CI pendientes. Sin publicación npm/release.

## T-01 — vistas

RED previo: Edge real, tres vistas, tres onerror ejecutados; 0 passed/3 failed. Tras DOM seguro y renderer JSON: 9 passed en Edge sin skips y 9 tests del renderer correctos. Caso adicional de delimitadores literales observó RED (ValueError) y se corrigió. Servicios reales no usados; sólo fixture MCP. No se acredita aislamiento del host Cowork.

## T-02 — PDF

RED previo: 7 fallos de la CLI real con navegador sustituido por fixture, por sandbox desactivado y ausencia de política JS/red. GREEN: 7 pruebas de política y 5 de salida atómica. Conversión adicional real con dependencias existentes, copia aislada del script y Chromium con sandbox predeterminado: exit 0, 1 página, 32023 bytes; texto y acentos presentes; SCRIPT_CHANGED ausente; aviso de recurso remoto bloqueado. No se instaló ni modificó ninguna dependencia del usuario.

## T-03 — CI

TDD n/a: configuración/prosa; contratos de regresión escritos y observados rojos (5 fallos previos). GREEN: permisos, SHA, secretos por paso y paridad manual validados. Los pins se comprobaron en metadatos oficiales el 2026-11-06. No se ejecutó el workflow de publicación ni llamadas headless de pago.

## T-04 — herramientas

RED previo del contrato: el instalador seleccionaba /releases/latest al ejecutar. GREEN: 13 pruebas offline; integridad incorrecta, archivo ajeno/modificado, archivos inseguros/enlaces/ambigüedad, plataforma ausente, raíz dentro de Git/enlace cuando el SO lo permite, scripts y pip aislado con hashes. Caso adicional de quoting observado rojo y corregido: los argumentos que no son rutas conservan sus barras literales. Descargas para obtener pins: sólo metadatos/archivos upstream leídos, nunca ejecutados. No se instalaron herramientas reales. Catálogo y requirements son configuración revisada, TDD n/a.

## Puertas locales

- Python: tests/test_nemesis_tools.py, test_artifact_renderer.py, test_ci_security.py, test_ci_manual_copy.py, test_skill_size.py, test_ci_skill_suites.py: 80 passed.
- Node: artifact-dom-security, to-pdf-security y to-pdf-atomic: 21 passed, 0 failed, 0 skipped.
- check-handbook: PDF, fuentes LF, workflows y diagramas coinciden.
- evals/check: 229 casos, 60 piezas, 0 errores; no llamadas al modelo.
- export-interop --check: 92 ficheros al día; no se tocaron agentes/comandos/hooks canónicos.
- scope-check --base facad5f: 36 archivos dentro del alcance, ninguno excluido ni fuera; antes del commit del plan advirtió ausencia de línea base de criterios.
- review-lens-select --base facad5f: A+B+C; C por workflows e innerHTML; D no aplica.

El verde global requiere la revisión y la CI de referencia de esta revisión exacta.
