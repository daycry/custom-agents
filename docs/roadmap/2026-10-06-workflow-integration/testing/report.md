# Verificación de la integración nativa

Estado técnico: verificado, 2026-10-06. Base de revisión: `2059b7a`.
La publicación se registra separadamente en [tasks.md](../tasks.md).
No acredita importación completa del catálogo ni eficacia general de agentes.

## Puertas ejecutadas sobre la implementación final

| Puerta | Resultado observado |
|---|---|
| Linux, snapshot público sobre filesystem nativo (Python 3.11, Node 22) | 3903 passed, 29 skipped, 8 subtests passed; 1 aviso histórico de marcador vivo; 456,09 s |
| Node Linux, tres suites | 131 passed, 3 skipped por plataforma, 0 failed; 17,99 s |
| Node Windows, tres suites | 134 passed, 0 failed/skipped; 258,83 s |
| Consola Windows | 459 passed, cp1252 y ASCII; 116,19 s |
| Panel Python Windows | 26 passed, 1 skipped por privilegio de symlink |
| Panel Edge / qa-gate | P-01…P-07: 7 passed, 0 failed/flaky/skipped; 15,3 s; qa-gate VERDE, exit 0 |
| Cobertura del código Python del diff | coverage-gate exit 0, umbral 90 %, resultado 96,29 % sobre cinco archivos, sin avisos ni archivos sin datos |
| Linter | 10 agentes, 0 errores, 3 avisos de nombres genéricos preexistentes |
| Evals de activación | 51 archivos, 179 casos (109 positivos, 70 negativos), 0 errores |
| Export de interoperabilidad | 54 archivos al día, --check exit 0; también en snapshot Linux |
| release.py --check | Metadatos 1.22.0 y secciones publicadas coherentes; exit 0 en Linux; no se crea release |
| Revisión independiente final A+B+C+D | 0 Critical/Important/Minor; [intento 3](review-attempt3.md) conserva correcciones de [intento 2](review-attempt2.md) |

El snapshot contiene archivos públicos del índice con sus modos Git y finales LF
declarados para shell, excluye settings y memoria privada del usuario. La advertencia
histórica no procede de esta iniciativa. Los skips Linux corresponden a plataformas
o capacidades ausentes, no casos fallidos ocultos. Los grupos se solapan; no se
suman para anunciar un total único.

## Cobertura de producción afectada

| Archivo | Porcentaje |
|---|---:|
| capability-route.py | 98,25 |
| code-context.py | 97,83 |
| task-brief.py | 96,83 |
| report_outcomes.py | 94,48 |
| build_panel.py | 94,05 |

Runner real: pytest sobre tests/test_cloud_paths.py, test_capability_route.py,
test_code_context.py, test_outcome_evals.py, test_native_python_compat.py,
test_plugin_panel.py, test_copias_declaradas.py y shared/test_task_brief.py,
con pytest-cov sobre shared, plugin-panel/scripts y outcome-evals/scripts.
La puerta usa --changed-only --base 2059b7a --min 90. El porcentaje global de
esa ejecución acotada no es cobertura global del repositorio.

## Aceptación de la spec

| Criterio | Evidencia |
|---|---|
| 1. Decisiones y comparación trazables | 455 decisiones en capability-decisions.json y catalog-decisions.md; 18 adaptaciones delimitadas; no revisión funcional profunda de todas las piezas |
| 2. Selector y registro seguros | Tests de catálogo, manifiestos, límites, redacción y guard CLOUD; sin ejecutar código del consumidor |
| 3. Consolidación y retirada | Stack-practices absorbe tres guías; mapas, referencias, evals y bajas comprobados por suites y revisión |
| 4. Workflow compartido | Fragmento único, diez roles y ambos ciclos; rutas generadas al día, sin duplicar gates |
| 5. Brief e índice acotados | Suites completas de task-brief y skill-index; información protegida y límites mantenidos |
| 6. Panel, fuentes y documentación | Siete escenarios Edge, plantilla empaquetada, documentos ES/EN y exports; inventario no equivale a ejecución |
| 7. Resultados y memoria | JUnit observado, ausencia de métricas explícita; piloto AST real separado de memoria aprobada |
| 8. Gaps y puertas de calidad | Regresiones RED registradas; tres intentos, cero gaps finales; cobertura ≥90 % y Windows/Linux/Edge verdes |

## Panel y extensiones propias

P-01 inventario real y hooks agrupados; P-02 búsqueda/filtro; P-03 responsabilidades
y guías nativas; P-04 móvil 390 px sin desborde; P-05 nombres y funciones de hooks;
P-06 menú, teclado e historial; P-07 selección de seis etapas y apertura del rol.
Capturas finales móvil y escritorio inspeccionadas visualmente.

Prueba local adicional con raíz temporal: un agente y una skill propios aparecen;
Read/Bash declarados se resumen; una configuración MCP no crea inventario MCP ni
roles de workflow. Es el límite actual, documentado en
[integración por fases](../../../INTEGRATION-ROADMAP.md). No se han implementado
todavía el inventario multi-raíz/multi-runtime ni la adopción de extensiones.

## Regresiones y límites

RED y fixes: CLOUD (48 fallos), selector frontend por rendimiento Python, hash
de grafo con BOM, arranque de consola, parser TOML opcional, secretos antes de
JSON, colisión redactada, enteros negativos extremos, caché AST, agrupación y
metadatos de hooks, menú e historial, etapas y plantilla ausente. Historial en
tasks.md y review-attempt1.md. El [oráculo Windows](timeout-oracle.md) mide PID
vivo tras retornar; no prueba terminación instantánea al vencer el timeout.

Compatibilidad Python 3.9/3.10: ausencia de tomllib simulada y comprobación
sintáctica; no se ejecutaron esos intérpretes. Evals de activación no son evals
de eficacia. El [piloto estructural](structural-pilot.md) extrae 9 nodos y 8
relaciones de fixtures propias; no es un benchmark de recuperación ni sustituye
Markdown, journal, Knowledge Gate o backends existentes. La propuesta GOT-016
permanece local, ignorada y sin aprobación de conocimiento.

Evidencias privadas: scratchpad/.venv/linux-final2-output/linux-pytest.xml y
linux-checks.log, node-windows-final2.log, console-final2.xml y
panel-preview/workflow-results.json y capturas. No se incorporan logs privados
ni transcripciones a la distribución.
