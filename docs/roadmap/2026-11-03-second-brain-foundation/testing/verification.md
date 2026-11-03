# Verificaci?n de categor?as y plantillas

Proyecto sint?tico aislado; ninguna publicaci?n, reindexaci?n ni cambio del corpus real.

| Comprobaci?n | Resultado observado |
|---|---|
| Windows: contratos, herramienta, curaci?n, gate y taxonom?a | 403 passed, 3 skipped; antes del caso adicional B2 |
| Windows: herramienta actualizada y documentaci?n | 41 passed, 1 skipped; incluye B2 y dos regresiones de consumidores |
| Validaci?n final Linux del snapshot completo | 769 passed, 3 skipped; pytest exit 0 |
| Gate oficial de cobertura de archivos cambiados | 90,93 % frente a m?nimo 90 %; exit 0 |
| Interop | 92 archivos al d?a; exit 0 |
| Cat?logo de ejemplos de activaci?n | 60 archivos, 229 casos, 0 errores |
| Linter | 0 errores, 7 avisos preexistentes sobre nombres gen?ricos y referencias /hooks y /redmine |
| Paquete portable core | 103 archivos, 0 problemas; exportaci?n y comprobaci?n |
| Node: suite completa del instalador y runtimes | 452 passed, 16 skipped, 0 failed; npm test exit 0 |
| Manual PDF | 131 p?ginas, 34 diagramas, 30 workflows; verificador de fuentes/PDF/diagramas exit 0 |

La validaci?n final incorpora B2 (incluidos los defaults de Graphiti), D2, las precondiciones de ausencia de archivo y las dos pruebas de documentaci?n. Se comprueban por separado pytest y cobertura: ambos exit 0.

## Reproducci?n de la suite Linux

Python 3.11, pytest 9.2.0, coverage 7.16.2. Se extraen ?nicamente el ?rbol versionado y los archivos de la iniciativa a un filesystem temporal del contenedor propio de QA. No se montan configuraciones privadas ni servicios externos.

```text
python -m pytest agent-kits/shared/test_knowledge_category_contract.py skills/knowledge-category-template/scripts/test_category_template.py agent-kits/shared/test_knowledge_curation.py agent-kits/knowledge-curator/test_curator_gate.py agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_knowledge_routing.py agent-kits/shared/test_knowledge_index_canonico.py agent-kits/shared/test_knowledge_local.py agent-kits/shared/test_knowledge_portability.py agent-kits/shared/test_knowledge_portability_regressions.py agent-kits/shared/test_knowledge_portability_review_fixes.py agent-kits/shared/test_knowledge_portability_boundaries.py tests/test_knowledge_index.py tests/test_knowledge_candidates.py tests/test_knowledge_router.py tests/test_knowledge_services.py tests/test_export_interop.py tests/test_module_selection.py tests/test_rationalization_tables.py tests/test_handbook_integrity.py tests/test_knowledge_category_documentation.py -q --tb=short --junitxml=results.xml --cov=. --cov-report=json:coverage.json
python skills/unit-tests/scripts/coverage-gate.py . --min 90 --changed-only --base HEAD --runner "python -m coverage json -o coverage.json" --json
```

`HEAD` en esa copia aislada representa el ?rbol base antes de aplicar el snapshot. Se comprueban por separado el exit de pytest y el gate: una cobertura suficiente no oculta tests fallidos. La cobertura informada es la media de los cinco archivos de producci?n afectados, no una cobertura global del repositorio.

## L?mites y evidencias

- Los skips Windows incluyen la falta de permisos para crear symlinks; Linux ejecuta ese caso. Los tres skips Linux requieren la memoria local no versionada, excluida del snapshot; se validan fixtures sint?ticas, no ese corpus.
- El primer snapshot de revisi?n omiti? dos proyecciones regeneradas del curator. El ?rbol ra?z s? pasaba interop. Se corrigi? la selecci?n de archivos y se repiti? la validaci?n sobre una copia completa.
- B1 y D1 se reprodujeron con tests rojos antes de corregirse. B2 a?ade cobertura para la normalizaci?n compartida del prefijo opcional. No se relajan umbrales ni asserts.
- Revisi?n visual de p?ginas 87?89 y 98: cap?tulos, diagramas y ejemplos legibles. Revisi?n geom?trica de las 131 p?ginas: sin texto fuera de p?gina ni caracteres de reemplazo. El PDF conserva la documentaci?n t?cnica completa como anexos.
- No se acredita autenticaci?n mediante `content_origin` o `proposed_by`. La pol?tica es de flujo y los locks son cooperativos.
- No se ejecutan Kwipu, Graphiti ni ingestiones; routing y exportaci?n existentes se conservan.

## Cierre de las correcciones tras la revisi?n

La tercera ronda adversarial dej? B2/D2 abiertos. El orquestador decidi? continuar
?nicamente esa correcci?n dentro del alcance autorizado, sin reiniciar contadores
ni atribuir a los revisores una cuarta ronda. Se conservan sus hallazgos en tasks.md.
La soluci?n final compara el SHA del archivo de taxonom?a original bajo el lock,
en vez de copiar, normalizar y serializar su configuraci?n por cada candidato.
Se observaron tres tests rojos (dos variantes de Graphiti y el snapshot de bytes)
antes de la versi?n final; la suite final y el test de ausencia de archivo pasan.

Comparaci?n CPU sobre 128 documentos / 2.097.024 bytes y una taxonom?a v?lida de
262.144 bytes: tres muestras por versi?n, mediana 7,03125 s con la copia anterior
y 3,796875 s con la versi?n final. Lectura, lock y persistencia simulados; no se
presenta como tiempo de disco ni como aceptaci?n de servicios externos.

La suite Node inicialmente produjo tres fallos de terminaci?n dentro de un
contenedor sin init. Se reprodujo el fallo de deadline y se comprob? que pasa con
`docker run --init`; despu?s la suite completa pas? con `--init`. No se cambiaron
hooks, supervisores, tests ni sus umbrales para conseguir ese resultado. Los
16 skips Node se conservan conforme a las condiciones de plataforma/supervisi?n.

La exportaci?n portable final core se volvi? a generar despu?s del arreglo:
103 archivos, 0 problemas. Interop, lint, evals y verificador del PDF pasan;
los siete avisos existentes del linter siguen visibles.

## Publication catalog checks

CI run 41669934558 rejected the missing skill/command in the manifest descriptions. Before correction, the README count gate also reported 33 skills instead of 34. After correction: manifests 4/4, README counts and prose 10/10, manual copies 7/7; interop 92 up to date and handbook verification exit 0. Both canonical Claude manifests and generated Codex projections are updated; the CI workflow includes the category tool suite.
