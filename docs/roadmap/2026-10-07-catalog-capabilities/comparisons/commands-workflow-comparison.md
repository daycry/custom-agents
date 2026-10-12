# Comandos, estados y continuidad — comparación ampliada

Fecha: 2026-10-10. Este pase añade 76 cuerpos completos y dos relecturas a los
18 previos: 94/94 comandos leídos. Las fichas conservan recursos y callers
pendientes; una lectura no acredita integración, despacho nativo o eficacia.
La ampliación de skills queda para después de implementar y validar comandos,
dashboard, hooks y memoria.

## Decisiones para los dueños existentes

| Capacidad | Valor que conservar | Destino propio | Aceptación pendiente |
|---|---|---|---|
| Entrada por intención | Distinguir nueva capacidad, cambio deseado, defecto, refactor y MVP; elegir el primer oracle y modo por riesgo, contrato y ambigüedad | `commands/dev-cycle.md` | Literal, paráfrasis y negativo; escenarios antes/después, regresión y baseline |
| Requisitos verificables | Fuente o supuesto explícito, hipótesis y método de validación; métricas sólo cuando existan | `agents/analyst.md` y plantilla de spec | Evitar inventar números o anticipar solución no autorizada |
| Plan por patrones reales | Rutas concretas de naming, errores, datos y pruebas por tarea; declarar ausencia de equivalente | `agents/planner.md` y plantillas | Enlace requisito→tarea→patrón→verificación, mismo slug y ledger |
| Reparación incremental | Comando real del proyecto, agrupación de fallos, cambio mínimo, rerun y parada ante repetición/empeoramiento | `agents/implementer.md`, método de depuración y ciclo | Logs y exits reales; no instalar, limpiar caches o actualizar dependencias por inferencia |
| Revisión reproducible | Base/head/rango fijados, contexto necesario, dimensiones fallidas visibles y evidencia conservada al deduplicar | Método de revisión y `agents/reviewer.md` | Revisor ausente/fallido no equivale a aprobación; publicación separada de revisión local |
| Evidencia visual | Modo solicitado/logrado: interacción, captura o código; teclado y tamaños pertinentes | `agents/qa.md`, informe y panel | Captura no prueba interacción; score no compensa función obligatoria ausente; V01–V08 siguen pendientes |
| Respuesta visible del consumidor | Decisión enviada, entregada, consumida y cambios efectivamente atendidos por IDs/versión | Dueño `plan-review.py` y panel | Crash entre ack y efectos; estado desconocido sin evidencia, sin otra cola de autoridad |
| Actividad caducable | Ownership, señales observadas con vencimiento, espera y límites de ejecución | Panel, progreso y `/work-resume` | Productores opt-in reales en tres runtimes; poll del navegador no acredita agente vivo |
| Reglas de hooks | Proponer, explicar, listar y configurar reglas declarativas mediante una interfaz común | Servicio de hooks y `/doctor` | Motor, precedencia, validación/CAS, Unicode y eventos reales; Stop no se equipara a SessionEnd |
| Memoria portable | Exportar approved con scope/manifiesto/hash; importar como candidatos revisables preservando vecinos | Servicio local de conocimiento y panel | Import/export propio pendiente; frecuencia/confianza/force no aprueban conocimiento |
| Estado de memoria | Approved, candidatos, conflictos, fuente y estado de sincronización por backend | `/doctor` y panel | Lectura realmente acotada; salud externa no condiciona disponibilidad local |
| Contexto de incidencias | Ticket→requisitos/criterios/escenarios y búsqueda acotada | `skills/jira-sync/SKILL.md` y entrada del ciclo PM | Conector y schemas vigentes, paginación, fases y read-back; ledger sigue siendo autoridad |
| Entrega y onboarding | Plantilla real, base/head exactos, dry-run/preview y conflictos conservados | Ritual de cierre, setup e instalador | Push no autoriza PR/merge/release; no rebase/force/gestor global automáticos |
| Selección para el commit | Mostrar archivos elegidos y excluidos, conservar staging ajeno y revisar el diff realmente preparado | Ritual de cierre de `commands/dev-cycle.md` | Fixture con cambios previos en el índice; no convertir una selección en permiso para publicar |
| Desviaciones y continuidad | Registrar motivo, evidencia, dueño y efecto en el plan; elegir la siguiente tarea con sus dependencias | Ledger, planificación y `/work-resume` | Mantener decisiones pendientes y no presentar una métrica desconocida como medida |
| Documentación generada | Delimitar bloques generados y vincularlos a fuentes y contratos concretos | Documentación y exportadores existentes | Preservar texto humano; detectar drift por contrato, sin usar porcentaje de líneas como criterio de corrección |

Estas son decisiones de integración, no nuevas interfaces instaladas. Se
consolidan en sus dueños antes de justificar otro comando o agente. El método
común conserva los gates humanos y los contratos específicos de cada runtime.

## Correcciones propias aplicadas en el bloque24

QA entrega veredicto, exits y evidencia; sólo escribe bajo testing. El orquestador
reabre tareas con rojo y controla los estados finales. En Fase 6, plan/tasks
pueden quedar completados antes de la retro; la spec sólo queda implementada
con documentación y retro-gate en exit 0. QA suelta muestra ese cierre pendiente.

El implementador conserva progreso y worklog de Jira, sin cerrar el issue.
`aprobado`, emitido por el orquestador con revisión sin gaps y QA verde, conserva
la transición Done. En granularidad fase también debe comprobar todas sus tareas.
Read-back previo a aprobado, selección de evidencia de revisión y confirmación
de efectos externos requieren todavía aceptación del caller propietario.

La elección humana del diseño permite aprobar design, pero su decisión se
propone por el servicio de curación. La plantilla conserva ruta pending y SHA
para Curator, o pendiente con motivo si falta el servicio. No habilita escritura
legacy ni aprobación automática de memoria. Retro también propone; Curator
juzga y el servicio persiste. Rejected terminal no se vuelve a enviar al gate.

Las instrucciones, plantilla, documentación ES/EN y diagramas reflejan estos
contratos. Ocho archivos revisados y cuatro exports generados de QA/dev-cycle
sincronizados para Codex/OpenCode; linter y export-check verdes. La revisión
estática del bloque no acepta el dispatch nativo ni la QA completa del producto.

## Contenido opcional y secuencia

Los criterios Kotlin de cancelación, lifecycle, Compose/KMP, tiempo virtual,
Flow y cobertura oficial aportan contenido específico. Se conservan para
referencias condicionales de implementación, revisión, TDD y QA, con versiones
y herramientas del proyecto. No se impone Kotest/MockK/Kover ni otro paquete.
Recursos transitivos y fixtures del stack siguen pendientes de contraste. También
se conservan criterios específicos de Python, React, Rust y Vue para referencias
futuras. Deben comprobarse contra APIs y versiones del proyecto: las reglas
generales no deben prohibir formas válidas de usar refs, estado o navegación.

Campañas aporta brief, posicionamiento aprobado y coherencia entre canales.
Tiene destino futuro concreto al retomar skills, con escritor y autorización
de publicación explícitos; el ciclo técnico no acredita ya esa especialidad.

## Límites que impiden cerrar la comparación

Los cuatro grupos leyeron 26, 17, 14 y 21 cuerpos; el segundo incluye dos relecturas.
Planificación alcanza ocho decisiones estáticas suficientes y nueve fichas
abiertas. Calidad y operaciones conservan sus fichas abiertas por recursos
transitivos, versiones, callers o aceptación real. El último grupo alcanza seis
decisiones estáticas suficientes y quince fichas abiertas. No quedan cuerpos
de comandos por leer; siguen pendientes sus recursos y la aceptación de cada
integración. Ninguna se declara integrada por similitud de nombres. Métodos,
rutas y permisos efectivos deben comprobarse por runtime.

Los informes detallados y hashes/rangos se conservan en recibos privados OWN
verificados por ROOT. Bytes y líneas describen tamaño, no tokens, latencia ni
uso. No se ejecutó código de la biblioteca comparada, modelos, clientes nativos
o backends para esta comparación. El seguimiento ejecutado y los resultados
de QA se mantienen en `../tasks.md`.
