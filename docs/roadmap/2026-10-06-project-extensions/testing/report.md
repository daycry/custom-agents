# Verificación de extensiones propias

Estado técnico: verificado, 2026-10-07. Base de la fase: `b067099`;
baseline revisado: `87772c1`. La publicación se registra por separado en
[tasks.md](../tasks.md). Los resultados se solapan y no se suman como un total.

## Puertas ejecutadas

| Puerta | Resultado observado |
|---|---|
| Windows, lector/panel/briefs/distribución/consola del baseline | 698 passed, 2 skipped; 210,58 s |
| Windows, delta YAML posterior | 239 passed, 2 skipped; 77,09 s |
| Linux, suite pública completa del baseline, Python 3.11/Node 22 | 4023 passed, 29 skipped, 8 subtests passed; 432,17 s |
| Linux, delta YAML con lectores/briefs/panel/distribución/consola | 702 passed, 1 skipped; 33,03 s |
| Node Windows, hooks e instaladores | 134 passed, 0 failed/skipped; 248,28 s |
| Node Linux, hooks e instaladores | 131 passed, 3 skipped, 0 failed |
| Panel Edge, extensiones P-01…P-04 | 4 passed, 0 failed/skipped; 22,5 s; qa-gate VERDE |
| Panel Edge, regresiones del bundle | 7 passed, 0 failed; 15,1 s |
| Cobertura ejecutable del diff de producción | 92,16 %, 741/804 líneas; umbral ≥90 % |
| Linter | 0 errores, 3 avisos históricos de nombres genéricos |
| Evals de activación | 182 casos, 112 positivos/70 negativos, 51 archivos, 0 errores |
| Export de interoperabilidad | 54 archivos al día; también comprobado en Linux tras el delta |
| Release check | Metadatos 1.22.0 coherentes; no se publica una release |
| Cierre documental Windows, sin suite release | 557 passed, 1 aviso histórico; 25,96 s |
| Release Windows, fixtures finales | 27 passed, 0 failed; 62,39 s |
| Cierre público Linux antes del último ajuste de identidad | 552 passed, 1 aviso histórico; 17,23 s |
| Release Linux después del último ajuste de identidad | 27 passed, 0 failed; 3,86 s |

El snapshot Linux incluye archivos públicos con sus modos Git y finales LF
declarados para shell. Excluye settings del usuario y evidencia privada. El
baseline completo precede al pequeño delta YAML; este se verifica por separado
en sus consumidores afectados, sin presentar la suite anterior como ejecutada
después de la corrección. No se modifica código JavaScript tras las suites Node.
Los skips son por plataforma o capacidades ausentes; no son fallos ocultos.

La cobertura se calcula sobre líneas ejecutables añadidas frente a `b067099`
en project-pieces.py, task-brief.py y build_panel.py, excluyendo archivos de tests.
Por archivo: lector 635/695, brief 41/41, panel 65/68. No es cobertura global
del repositorio. El informe posterior al delta conserva el mismo resultado.

## Aceptación de la spec

| Criterio | Evidencia de implementación y verificación |
|---|---|
| 1. Descubrimiento nativo y acotado | Tests de Markdown/TOML/JSON/JSONC, tres runtimes, raíces personales/expresas y cadena de paquetes; directorios excedidos se rechazan completos |
| 2. Identidad, fuentes y conflictos | IDs, raíces opacas, duplicados, nombres por filename y namespace command/skill Claude; panel identifica el alias que colisiona |
| 3. Propiedad O1 sin otro registro | Esquema completo, hashes LF, corrupción y destinos huérfanos; el lector no escribe ni adopta piezas |
| 4. Selección y personas | Hasta 20 IDs explícitos, revalidación, bajas/otros runtimes, referencias ≤1000 caracteres y persona proyecto→catálogo→sin persona |
| 5. Panel y disponibilidad | P-01…P-04, conteos separados, búsqueda/filtros, fuente/propiedad/conflictos, definición MCP inválida y desactivación; disponibilidad sin verificar |
| 6. Privacidad y ausencia de ejecución | Fixtures con efectos prohibidos nunca ejecutadas, configuraciones intactas; args anidados excluidos, redacción previa, límites y guard de enlaces |
| 7. Flujo, distribución y docs | Fragmento común y consumidores, exports al día, pruebas portables, guías ES/EN y evals |
| 8. Calidad y entrega | RED/GREEN reales, cobertura ≥90 %, Windows/Linux/Edge, revisiones registradas, retro y comprobación remota en el ledger |

## Revisión y regresiones

El ciclo inicial A+B+D termina en tres intentos sin gaps pendientes ni deuda
aceptada. C no aplica por selector. Corrige cinco Important y un Minor en el
primer pase; el segundo aporta evidencia nueva de identidad dentro del conflicto
ya señalado. El tercero revalida nombres, aliases, panel, límites y exports.

QA descubre después una lista MCP YAML válida sin sangría que se omitía. El
baseline se conserva en `87772c1`; T-02 se reabre y se corrige con tres casos RED
reales. El delta tiene un ciclo de revisión A+B independiente, con selector
C=false/D=false. Su resultado se recoge en el ledger; no reinicia el ciclo
anterior ni cuenta el defecto como deuda aceptada.

El cierre documental adicional encuentra tres supuestos de Linux en tests de
release que no habían cambiado en esta fase. Se aíslan bytes LF/CRLF y config
Git del repo temporal, se espera la ruta nativa y se prohíbe inferir identidad.
La revisión de ese delta de tests A+B detecta un Important adicional: config Git
heredada mediante GIT_CONFIG_COUNT. Se reproduce y añade una regresión antes
del filtro de GIT_CONFIG*. El intento 2 conserva los asserts originales y
termina sin gaps ni deuda. Las suites finales de release pasan en ambos sistemas;
scripts/release.py no cambia. La evidencia previa con fallos permanece registrada.

El escenario Edge P-01 inicialmente buscaba el primer code de la tarjeta; la
tarjeta también contiene el alias del conflicto. Se corrige solo el selector
del test para comprobar la fuente dentro de details. Producto y requisito no
cambian. El siguiente pase tiene cuatro escenarios verdes, sin retries.

La descripción multilineal pasa de 5,552–13,244 s para 524032 bytes a 0,18 s;
el CLI con 16 archivos tarda 6,941 s. El tercer revisor mide crecimiento lineal
con 250/500/1000 skills. Son fixtures sintéticas, no un benchmark de MCP vivos.

## Alcance y límites

Las pruebas de Edge verifican fixtures propias de los tres runtimes, secretos,
no ejecución, configuraciones intactas, móvil/teclado y ausencia de red. Las
capturas de escritorio y móvil se inspeccionan visualmente. No acreditan conexión
MCP ni que sesiones reales de Claude/OpenCode hayan cargado cada declaración.
La ejecución nativa sigue siendo responsabilidad del cargador y de los permisos
de la sesión; el plugin reconoce referencias y contrasta disponibilidad al usar.

No se entregan generación/adopción de piezas ni el resto de especialización.
La revisión funcional profunda del catálogo y la comprobación del alcance real
de guardias por runtime pertenecen a la fase 3. El benchmark de memoria pertenece
a la fase 4. El piloto AST no sustituye la memoria gobernada.

Evidencias privadas: extensions-gates-v5.xml, extensions-indentless-red.xml,
extensions-indentless-green.xml, extensions-coverage-v6.json,
extensions-linux-v2/linux-pytest.xml, extensions-linux-v3/linux-pytest.xml y
panel-preview/extensions-results.json, workflow-results.json y capturas. No se
publican logs privados ni transcripciones. Veredictos y publicación: [ledger](../tasks.md).

Evidencias del cierre: extensions-docs-final-green.xml,
extensions-release-portable-green3.xml, extensions-closure-linux-v2/linux-pytest.xml
y extensions-release-linux-final/linux-pytest.xml. Los XML que contienen los RED
previos no se sustituyen ni se interpretan por su nombre.
