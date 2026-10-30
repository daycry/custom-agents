# QA de la arquitectura modular y el manual

Base de la iniciativa:707d4ad. Implementación: e6fcac2; ajustes de contratos y
entrega:74bb5c7,189b7b9,7241e0e. El cierre documental incluye la edición definitiva
del PDF y los recibos. No se publica una versión ni se prueba una cuenta remota.

## Resultado por entorno

| Comprobación | Resultado observado | Alcance |
|---|---|---|
| Node Windows, suite completa | 464 passed, 0 failed, 2 skipped, 1 TODO; exit 0 | 467 casos; el TODO de arranque SessionEnd ya existía |
| Cobertura oficial Node | 96,59% líneas | install/install.mjs 96,40%; install/modules.mjs 100%; 90% mínimo |
| Pytest Linux, snapshot inicial instrumentado | 9931 passed, 17 failed, 57 skipped; 82 subtests | 10087 casos; se conserva el resultado rojo |
| Pytest Linux, overlay actual afectado | 983 passed, 2 skipped; exit 0 | Consola, copias, split, exports, manifiestos, panel, índice, selección, router, adapters, propiedad e instalación |
| Cobertura oficial Python changed-only | 91,55%; exit 0 | Media de los cinco archivos cambiados, mínimo 90%, ninguno sin datos; detalle en coverage.json |
| Node Linux, suite completa con init | 451 passed, 0 failed, 16 skipped; exit 0 | 467 casos; init recolecta descendientes de fixtures |
| Timeout TLS sin cobertura | 1 passed | Límite original de 0,28 s conservado |
| Coste lineal redactor sin cobertura, tras cleanup propio | 1 passed | Límite original de 1,5 s conservado; fallos previos documentados abajo |
| PDF | 39 páginas, 18 workflows; revisión completa | Navegación, enlaces, límites, glifos y hashes; pdf-qa.md |

El gate Python usa la media por archivo definida por coverage-gate.py, no exige
90% individual: doctor 93,36; router 93,88; selector 98,84; export 94,61; Jira-flow 77,05.
El global del informe es 94,78%, distinto del 91,55% de código cambiado. La cobertura
Node es de líneas; no se presenta como cobertura de ramas. Los cinco archivos Python
coinciden byte a byte tras normalizar LF con los del snapshot instrumentado;
las nuevas regresiones CLI amplían esa misma medida, sin mezclar código distinto.

## Trazabilidad de los fallos iniciales

| Casos | Causa comprobada y resolución |
|---|---|
| 1 copia de workflow | El empaquetador privado normalizó .yml pero no .MANUAL-COPY; HEAD archivado conserva los bytes reales. Regresión actual verde. Sin cambio del workflow de CI. |
| 4 consola | Faltaba registrar el CLI nuevo y su contrato JSON ASCII. Modo y exención explícita comprobados bajo cp1252/ascii; no se añadió un skip. |
| 1 imports declarados | Rango descriptivo se quedaba antes de importsys; ampliado 36-45. No se relaja la comparación de código. |
| 4 split de dev-cycle | Snapshot anterior al mapa explícito de cinco sustituciones autorizadas. Baseline histórico intacto; todos los demás párrafos, gates y recetas exactos. |
| 1 OpenCode | Expectativa literal antigua del documenter; actualizada solo la frase del proveedor al puerto neutro, conservando permisos/esquema. |
| 1 export portable | Snapshot anterior a la nueva referencia interaction.md; archivo incluido en la entrega actual y check real verde. |
| 1 marketplace | Description Claude desincronizada; igualada al manifiesto canónico. |
| 1 panel | Test exigía la sintaxis && antigua; ahora comprueba éxito del dashboard y archivo opcional antes de llamar al renderer. |
| 1 índice | Snapshot anterior a la fila de la iniciativa; fila dentro de la tabla y suite verde. |
| 2 tiempo | TLS pasa sin instrumentación. Redactor falló primero bajo cobertura y luego por un margen pequeño sin ella; detalles abajo. |

La primera suite Node Linux tuvo tres fallos de supervisión en un contenedor sin
init: deadline/proceso y dos efectos de teardown no observados. Se repitió la suite
completa en el mismo fixture con --init:0 fallos. Los casos y plazos se conservaron.

La primera exportación del informe de cobertura perdió la configuración relative_files
y produjo un informe sin datos útiles. No se tomó ese0% como medida del código.
Se conservó la base oficial de coverage.py y se regeneró con relative_files=True;
el gate oficial y el inventario de archivos acreditan el resultado indicado.

## Incidencias de las comprobaciones adicionales de Windows

Un barrido adicional de 114 scripts standalone terminó con 108 exit 0 y 6 incidencias.
No se presenta como una suite Windows completamente verde:

- code-context-build: los mismos nueve fallos se reprodujeron en 707d4ad con idénticos
  nombres de caso; no hay cambios de ese componente en esta iniciativa.
- graphiti-model: el launcher unittest devuelve 5 por no recoger tests; mismo resultado
  en 707d4ad. La suite pytest real se incluye en Linux/CI.
- hooks-shell, mermaid y su wrapper standalone: timeout privado de 180 s. No se alteró
  ese presupuesto ni se sustituyó el test por una aprobación.
- training-data-services: una comparación de doctor observó primero timeout del probe
  nativo y después versión habilitada; no un fallo del store o de la modularización.

Tras el timeout del wrapper quedó un proceso propio de test_mermaid_blocks.py.
Se verificaron ruta, padre y hora de creación correlacionada con su log antes de
terminarlo; se confirmó su salida. El test de coste del redactor se repitió después,
en un fixture aislado de 2 CPU, y pasó sin cambiar fuente ni límite. Los fallos locales
anteriores(1,501 s y 1,655 s) no se borran ni se convierten en evidencia verde.

El TODO preexistente de SessionEnd Windows midió mediana 2025 ms frente a 1500 ms;
el runner lo clasifica TODO y sale 0. No se reabre la optimización cancelada.

## Pruebas de proveedor y límites del producto

No se enviaron tareas, comentarios, transiciones, documentos o worklogs a un
proveedor real. El router solo declara bindings. Atlassian requiere herramientas,
identidad, permisos y recibos reales; Redmine/wiki son contratos de referencia que
el proyecto adapta y prueba. Ollama queda diferido por decisión del usuario.
Los perfiles parciales soportan copia Claude y export portable; los bundles nativos
siguen completos y OpenCode parcial se rechaza antes de escribir.

## CI y puerta de entrega

La [CI del código validado](https://github.com/daycry/custom-agents/actions/runs/41144112195) está verde sobre
7241e0e. Resultado de la suite completa: **9993 passed, 38 skipped, 1 warning, 82 subtests passed in 719.14s (0:11:59)**.
Pasaron también suites standalone, benchmark SessionEnd, interop, Node, sintaxis,
JSON y coherencia de versión. El cierre documental solo añade evidencia, roadmap
y el ajuste del hash de fuente del PDF; se comprueba además la CI del HEAD publicado
antes de entregar. Su enlace definitivo queda en la PR22, sin otro commit circular.

`results.json` es una proyección explícita de comprobaciones ejecutadas por los
runners oficiales, no un reporte Playwright ni una suite E2E inventada.
`qa-gate.py` evalúa esa proyección; los conteos nativos separados están en validation.json.

No hay UI nueva: la revisión visual corresponde al PDF; no se inventa una ejecución
Playwright. Los conteos de distintos comandos/plataformas son observaciones separadas,
no una cifra deduplicada de pruebas únicas. Logs y transcripciones privados no se publican.
