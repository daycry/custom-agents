# Comparación operativa de paneles y comandos

Lectura estática del corpus fijado en
`ef648e01899ba3e8dc6371642deaaf64b4477775`, realizada en paralelo el
2026-10-08. Se han leído las tres entradas de dashboard, recursos relacionados
y 18 cuerpos de los 94 comandos. Quedan 76 cuerpos de comandos por leer y
dependencias de este bloque por contrastar. **Cero fichas globales cerradas y
cero integraciones entregadas por esta comparación.** Las nuevas skills siguen
aplazadas. El código del corpus no se ha ejecutado.

[panel-reading-evidence.json](panel-reading-evidence.json) y
[command-reading-evidence.json](command-reading-evidence.json) conservan IDs,
hashes, tamaños, rangos y límites. Los nombres y rutas originales permanecen
en el mapa privado. Leer un cuerpo no demuestra carga, permisos ni eficacia.
Tokens y latencia no se han medido con una fuente compatible.

Los hashes propios de doctor y journal describen el snapshot leído antes del
bloque de cierre e instalación, conservado en Git y en las fixtures privadas.
No describen sus cuerpos finales: el estado nativo de doctor y la captura
canónica posterior se documentan en [contracts.md](../contracts.md) y
[terminal-qa-evidence.json](../terminal-qa-evidence.json). Las propuestas de
esta lectura siguen pendientes; los hashes históricos no se sobrescriben.

## Funciones útiles para el panel propio

| Fuente | Contrato leído | Comparación y destino propuesto |
|---|---|---|
| R-8ab9d88e012a | Explorador de archivos de piezas, configuración y lanzamiento de terminal | Mantener el HTML autónomo de plugin-panel. Evitar dependencia de escritorio e inventarios de ejemplo que parecen reales cuando faltan fuentes |
| R-7b761940e6db | Catálogo web local con búsqueda, categorías, enlaces directos, recientes, idioma y tema | Ampliar navegación y filtros del panel propio conservando procedencia, conflictos y redacción central. No exportar cuerpos ejecutables, argumentos MCP ni configuración privada |
| R-ec2c637e28f7 | Readiness de una entrega concreta y cola de plataforma | Conservar procedencia, vigencia y estado «sin comprobar» en una proyección de doctor. La presencia de archivos o frases de historial no acredita readiness funcional |
| R-2169b7ad85cf / R-eb81734c4b22 y recursos de estado/acciones | Grafo de proyectos, sesiones y trabajo con base de datos y acciones mutables | Proyectar ledger y journal existentes en lectura. Mantener el dashboard de roadmap como vista de iniciativas; no crear otra base de tareas ni botones de claim/move en el catálogo |
| R-64efaae5166e y recursos de observación | Tasas de ejecución, fallos, propuestas y versiones por ventanas de 7/30 días | Separar observaciones reales de inventario. Mostrar n/a cuando no hay datos; posponer tasas de éxito hasta disponer de observación opt-in compatible y validada |

El panel actual ya agrupa handlers por evento y muestra función, activación y
timeout declarado. Sus lectores conservan procedencia y conflictos y declaran
que la disponibilidad en sesión no está medida. Una ampliación debe reutilizar
[build_panel.py](../../../../skills/plugin-panel/scripts/build_panel.py),
[doctor.py](../../../../agent-kits/shared/doctor.py) y sus contratos, sin
duplicar diagnósticos dentro de la UI.

La proyección propuesta necesita fuente, scope, fecha de comprobación,
resultado, límites y remedio. Debe distinguir declaración, habilitación,
instalación, carga y ejecución observada. Ausencia de evidencia es desconocido.
El catálogo portable excluye prompts, transcripciones, comandos completos,
credenciales y memoria privada. Los enlaces y filtros deben probar teclado,
foco, movimiento reducido, metadatos hostiles e IDs inexistentes.

Hay tres límites concretos que no se trasladarán: el navegador de origen
oculta env pero publica cuerpos y argumentos; el escritorio inventa piezas
de respaldo; el resumen de salud cuenta como saludables piezas sin ninguna
observación. Las ventanas solapadas y una sola ejecución tampoco prueban una
tendencia. La captura de observaciones necesita aislamiento, retención y
concurrencia antes de alimentar gráficas.

## Comandos: consolidar responsabilidades existentes

| IDs leídos | Valor concreto | Destino y condición |
|---|---|---|
| C001 | Responder una pregunta lateral manteniendo la tarea activa | Criterios de conversación del workflow; ningún comando persistente nuevo por defecto |
| C004 | Anclas SHA y comparación de archivos, tests y cobertura entre checkpoints Git | Conservar baselines y artefactos verificables en ledger/QA. No confundir con el checkpoint de prompts del journal, añadir otro log ni hacer stash/commit automático; recurso de verificación y política clear pendientes |
| C006 | Deducción de snapshots acumulativos antes de sumar coste | Ampliar informes de usage-meter/roadmap-metrics con fuente, ventana y calibración; no crear otro log global ni confundir estimación con medida |
| C030 | Findings deterministas con rutas y remedios | Consolidar sobre doctor; rechazar score por número de agentes, hooks o palabras presentes como medida de calidad |
| C047 | Razón, confianza y fallback en selección de modelo | Complementar model-tier tras verificar su implementación completa; conservar overrides y modelos realmente disponibles |
| C079 / C085 / C087 | Handoff con decisiones, fallos, bloqueos, siguiente paso y selección de sesión | Diseñar una fachada de contexto sobre journal y ledger actuales. Separar hechos comprobados, citas y propuestas; no copiar un almacén global de sesiones |
| C074 | Exponer manualmente un formatter ya declarado | Decisión provisional hasta leer handler y contratos de herramientas. No imponer formatter, stack ni instalación automática |
| C042 / C043 | Alcance, solapes, procedencia y revisión de aprendizaje | Conservar criterios en knowledge-curator; generación de skills aplazada y ninguna promoción automática |
| C065 / C066 / C072 | Observaciones por proyecto, promoción y retirada | Dependencias pendientes. No trasladar umbrales de confianza ni borrado por edad a doctrina aprobada |
| C052 / C061 / C078 | Fases, planes y limpieza de código | Comparación provisional: leer wrappers, agentes y callers antes de consolidar con pm/dev-cycle y code-health; evitar backend fijo, rollback ajeno y confirmaciones nuevas en cada fase |
| C090 | Salud de ejecución y fallos recurrentes | Reutilizar la comparación de observación del panel; posponer gráficas hasta contar con datos compatibles, sin declarar salud por inventario |

El motor de C030 comprueba población, presencia y texto, incluyendo la mera
cadena PreToolUse. Sus resultados son reproducibles, pero no demuestran
guardias activas. La prueba nativa de Codex ha confirmado por separado que
enabled=true puede coexistir con un plugin sin instalar.

C085 guarda encabezados que el parser de C087 no reconoce; una sesión válida
puede mostrar cero tareas. C087 también selecciona el ID parcial más reciente
sin resolver ambigüedad y su reemplazo de aliases en Windows elimina el destino
antes del rename. No se copiarán esos contratos ni otro escritor de memoria.

La fachada de handoff propuesta debe validar selección explícita sin
sustitución silenciosa, colisiones entre proyectos/worktrees, estados vacíos
o corruptos, rutas obsoletas y export acotado/redactado. Escenarios de activación
propuestos: «retoma la sesión» / «continúa lo pendiente»; negativo vecino
«aprueba esta lección como doctrina», que corresponde a knowledge-curator.
Para diagnóstico: «qué falla y cómo lo arreglo»; una auditoría de
vulnerabilidades del producto corresponde a nemesis. Son escenarios estáticos,
sin prueba de routing nativo ejecutada.

## Qué falta antes de implementar

La entrada de readiness conserva pendiente su dependencia de plataforma.
El control operativo requiere contrastar servicios Rust, almacenamiento y
consumidores. Las fichas de sesiones requieren path-safety y la lectura
completa de los lectores propios. Coste, formatter, workflow y observaciones
mantienen pendientes sus recursos concretos. Los manifiestos distinguen
lectura parcial y completa; ninguna propuesta cierra esas dependencias.

T-08 debe fijar destino y dueño de cada ampliación. Después se aplican RED,
pruebas de comportamiento, exports y docs bilingües pertinentes, revisión y
QA. La secuencia propuesta es diagnóstico de lectura, navegación verificable,
handoff sobre memoria canónica y, finalmente, analítica con medición compatible.
