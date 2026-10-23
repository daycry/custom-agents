# Memoria desde comandos y dashboard: contratos y siguiente entrega

Revisión dirigida del 2026-10-09 sobre fuentes públicas propias. La prioridad del
usuario es comandos, dashboard y memoria; las nuevas skills permanecen aplazadas.
El [ledger](../tasks.md) conserva el progreso y la
[dirección de memoria](../operational-priorities.md) conserva las decisiones previas.

La revisión documental del bloque 15
no ejecutó consultas, benchmarks, hooks, imports ni operaciones de memoria.
El bloque 16 implementa el snapshot y la consulta local sobre fixtures propias;
la calidad de recuperación y selección de componentes siguen sin medir.
No leyó configuración, memoria o credenciales del consumidor ni conectó servicios.
Leer funciones y contratos no acredita utilidad, aprobación humana o fiabilidad nativa.
T-07, T-11 y T-13 permanecen abiertas.

## Qué conserva cada dueño

El journal conserva continuidad episódica. La memoria curada conserva conocimiento
del proyecto. Los backends publican o recuperan proyecciones opcionales del corpus
aprobado. El dashboard presenta sus resultados; no crea otro almacén de tareas o memoria.

| Operación y dueño actual | Lectura | Escritura local | Red | Límite para la integración |
|---|---|---|---|---|
| `progress-report.py resume` y `journal.py select_entries` | Ledger y journal seleccionados con lector acotado | No | No | La retoma distingue estado actual e historial; no acredita actividad de agentes. |
| `knowledge-find.py` sin `--intent` | Snapshot acotado legado/aprobado; consulta, relaciones o entrada por ID | Puede reconstruir SQLite por defecto, solo con corpus completo | No | Declara `corpus_read`; una lectura parcial no se sirve desde caché como completa. |
| `knowledge-find.py --view` y panel servido | Proyección común de consulta, entrada y relaciones | No | No | `knowledge-view.py` valida selectores y acota lectura/salida; acción explícita, sin caché o backend. |
| `knowledge-find.py --intent` | Consulta autorizada por backend; respaldo local con motivo | Puede reconstruir la caché local | Posible | La autorización de lectura y el fallo del backend permanecen explícitos. |
| `journal.py status` | Cola, backoff, último dead-letter y recuperación en dry-run | No según su contrato | No | Un resultado degradado no demuestra salud aunque traiga ceros o campos `ok`. |
| `journal.py candidatas` | Decisiones y pendientes de entradas del journal | No | No | Recorre el journal y propone por repetición; no aprueba ni mide calidad. |
| `code-context.py` | Grafo existente y disponibilidad de fuentes citadas | No | No | Contexto estructural no aprobado, cobertura desconocida y vigencia sin verificar. |
| `curator-gate.py` | Candidato, taxonomía e índice aprobado | No: el agente realiza movimientos | No | Valida forma y evidencia declarada; el Curator decide el juicio. |
| `knowledge-sync.py --outbox-status` | Cola del backend solicitado | No | No | No necesita cargar configuración ni invocar funciones del adaptador. |
| `knowledge-sync.py --check` | Salud y verificación del backend habilitado | No publicación ni drenaje | Posible | Verificar sin escritura no equivale a operación offline. |
| `knowledge-sync.py --dry-run` | Entradas aprobadas y plan del adaptador | No apply ni drenaje | Posible según adaptador | No prometer ausencia de red para un contrato extensible. |
| `knowledge-sync.py` sin modo | Corpus aprobado, plan y cola propia | Sí, staging y publicación mediante adaptador | Posible | Solo entra conocimiento permitido por routing. |
| `knowledge-sync.py --rebuild` | Todas las entradas enrutadas del backend | Sí, reconstruye la proyección | Posible | En Graphiti borra el grupo propio antes de republicar; no es una consulta. |

Fuentes: [retoma](../../../../commands/work-resume.md),
[lector local](../../../../agent-kits/shared/local-read.py),
[router](../../../../agent-kits/shared/knowledge-find.py),
[journal](../../../../agent-kits/shared/journal.py),
[contexto estructural](../../../../agent-kits/shared/code-context.py),
[curador](../../../agents/knowledge-curator.md),
[gate](../../../../agent-kits/knowledge-curator/curator-gate.py),
[sincronización](../../../../skills/knowledge-services/scripts/knowledge-sync.py) y
[contrato de adaptadores](../../../../skills/knowledge-services/backends/README.md).

La tabla describe los caminos leídos, no concede permisos a un endpoint web.
Los adaptadores de terceros pueden ejecutar código; el futuro servidor no los
importará por descubrir una declaración o actualizar una vista.

## Hallazgos documentales del bloque 15

| Hallazgo | Función y líneas leídas | Decisión |
|---|---|---|
| Consulta local puede leer todo el corpus y reconstruir caché | `knowledge-find.py`: `ficheros_corpus`, 483–510; `_ficheros_approved`, 512–533; `construir_indice`, 702–728; `abrir_corpus`, 731–748. `knowledge-local.py`: `build_index`, 255–327. | No ejecutar esa ruta en polling pasivo. Corregir presupuestos y lectura antes de ofrecer consulta explícita desde web. |
| Estado degradado del journal incluye ceros y valores `ok` | `journal.py`: `status`, 881–928. Sin módulo outbox, devuelve esos valores y un aviso. | Presentar desconocido o degradado; no inferir salud de contadores de fallback. |
| Candidatas recorren el journal completo | `journal.py`: `entradas`, 1581–1600; `candidatas`, 2082–2114. | Seleccionar y acotar antes de exponer la acción. Mantener propuesta y fuentes; Jaccard y repetición no acreditan eficacia. |
| El panel actual muestra presencia de artefactos | `build_panel.py`: campos `approved_directory` y `graphify_artifact`, línea 419 del bloque 14. | La presencia no demuestra aprobación del corpus, conexión, publicación ni recuperación eficaz. |
| La reconciliación es interna al adaptador Graphiti | `graphiti.py`: `_reconciliar_publicado`, 1844–1892; recuperación de `.pending` en `apply`, 1391–1398. | No crear una acción pública que llame al helper privado. Usar el dueño `knowledge-sync.py` para operaciones soportadas. |
| La documentación mezclaba autoría de propuestas y aprobación | `docs/agents/knowledge-curator.md`: §4 y §5. | Documenter/usuario proponen; Curator decide y mueve candidatos, y escribe aprobados. El gate valida sin mover. |

Estas líneas corresponden a la base 21092c2 inspeccionada en el bloque 15. Las
funciones identifican el contrato cuando otros cambios desplazan su ubicación.
La corrección de §5 aclara documentación; no añade enforcement ni otro productor.

## Cómo encajan los servicios y el contexto estructural

Kwipu conserva la proyección documental. `markdown_export.py` publica y verifica;
no expone `consultar` ni `puede_leer`. Su consulta pertenece al stack externo.

Graphiti conserva la lectura opcional. El router exige intent declarado, backend
habilitado, grupo efectivo y `puede_leer` con `puede: true` exacto.
`graphiti.py puede_leer` exige modo `read`, salud sana y verificación completa.
Una verificación incompleta no autoriza consultas. Un rechazo o fallo sirve
memoria local con el motivo, sin afirmar que el conocimiento no exista.

Referencias de función: `knowledge-find.py consultar_intent`, 1286–1388;
`graphiti.py puede_leer`, 1684–1714; `verify`, 1894–1991.
Los [contratos existentes](../../../agents/CONTRACTS.md) E16, E18 y E25 conservan
la autoridad de publicación, lectura enrutada y recuperación local de aprobados.

Graphify aporta contexto de código mediante un grafo previamente generado.
`code-context.py query_graph` exige citas AST, acota colecciones y redacciona salida.
Declara `coverage: unknown`, `freshness: unverified` y
`knowledge_status: unapproved-context`. El consumidor comprueba la fuente vigente
antes de aplicar una relación. Este contexto complementa la memoria gobernada.

`graphiti.py rebuild`, 1588–1613, escribe una marca pendiente, llama `clear_graph`
con el grupo propio y después republica. Un fallo puede dejar el grupo sin completar.
La UI futura distinguirá reconstrucción, sincronización, verificación y consulta.
No presentará reconstrucción como remedio automático al cargar el panel.

## Bloque 16: consulta local explícita y acotada

`knowledge-view.py` comparte snapshot acotado, aprobación local y parsers/ranking/
relaciones existentes. `knowledge-find.py --view` y el panel servido usan su salida;
la CLI ordinaria también cierra la lectura íntegra anterior. No añade otra memoria.
El polling de progreso no ejecuta búsquedas, replay ni operaciones externas.

La consulta conserva las tres capas existentes: aciertos compactos, relaciones y
entrada seleccionada por ID. Conserva ID completo, versión del conocimiento,
estado, evidencia disponible y ruta. Distinguirá conocimiento aprobado, propuestas,
entradas obsoletas e historial sin promoverlos por aparecer en un resultado.

Los presupuestos se aplican antes de leer: 256 entradas, 128 archivos, 256 KiB por
archivo, 2 MiB acumulados y profundidad ocho. Salida de 20 resultados/relaciones y
64 KiB JSON; cuerpo solo al pedir Ver, hasta 12.000 caracteres. Ausencia, corpus
incompleto, archivo ilegible, fallo y colisión tienen estados explícitos.

La salida destinada al panel aplica el redactor canónico y una proyección mínima.
Una ruta o un hash son identificadores de procedencia; no prueban autenticidad ni
aprobación. Los cuerpos solo viajarán tras selección explícita y con límites declarados.

| Criterio de aceptación | Evidencia requerida |
|---|---|
| Consulta local sin efectos | Fixture propia: cero red, cero escrituras y corpus/configuración intactos. |
| Lectura acotada | Fixtures grandes, muchos archivos, enlaces y archivos ilegibles; presupuesto y parcialidad visibles. |
| Autoridad conservada | Legado, aprobado, propuesta y obsoleto; IDs completos, versiones, evidencia y colisiones comprobados. |
| Capas equivalentes | Consulta, relaciones y show usan criterios compartidos; una colisión no selecciona el primer ID. |
| Panel seguro y usable | Selección explícita, redacción, escape HTML, navegación por teclado y ausencia de consultas automáticas. |
| Respaldo local visible | Backend simulado caído, no autorizado o incompleto; motivo y fuente local conservados. |
| Utilidad de recuperación medida | Conjunto de preguntas con respuestas y fuentes esperadas, errores obsoletos o de otro proyecto, omisiones y latencia observada. |

La última fila exige medición de recuperación, además de pruebas de contrato.
Primero medirá la base local. Un experimento Graphiti posterior usará las mismas
preguntas y un servicio explícitamente habilitado para medir utilidad, contexto y
coste real. Las fixtures o esquemas no justificarán una migración por sí solos.

La consulta y sus pruebas de contrato no sustituyen esa medición ni cierran captura nativa.
No cambia los permisos de memoria, activa servicios o da por terminado T-07/T-11/T-13.
