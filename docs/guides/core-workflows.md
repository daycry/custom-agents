# 2. Workflows detallados del core

Cada workflow indica quién lo inicia, quién actúa, qué necesita y qué deja. Las
skills se activan según el trabajo; una lista de skills aplicables no implica
precargar todas. Los agentes se despachan con los IDs reales del runtime.

## W-01. Preparar un proyecto

**Disparador:** un responsable quiere empezar a usar el producto en un repositorio.
**Comandos:** `/setup`, y `/doctor` para el diagnóstico previo o final.
**Agente:** el hilo que ejecuta el comando; no hace falta un agente nuevo de onboarding.
**Skills:** `rates-verify` y `unit-tests` si el usuario elige sus opciones.
**Tools:** lectura/escritura local; consultas oficiales para tarifas cuando se solicitan.

| Paso | Actor y acción | Entrada/configuración | Salida o puerta |
|---|---|---|---|
| 1 | Orquestador identifica el proyecto y la instalación | Raíz explícita y runtime | Scope correcto; no se toma configuración de otro proyecto |
| 2 | `/doctor` revisa lo existente si ya hubo configuración | Bundle y `.claude/` del proyecto | Informe de problemas y acciones; no reconfigura por sí solo |
| 3 | Usuario confirma parámetros económicos | Plantilla de rates y tarifa/jornada/supervisión | `.claude/rates.json`; precios sin verificar se señalan |
| 4 | Usuario elige funciones externas o ninguna | Seguimiento, documentación u otras funciones | `.claude/integrations.json` con bindings o lista vacía |
| 5 | Adaptador define sus preferencias, sin publicar | Destino, granularidad, permisos, estados | Settings del proveedor; credenciales fuera de Git |
| 6 | Usuario elige disciplina y criterios permanentes | TDD, worktrees, subagentes, constitución | `.claude/dev.json` y constitución si se aprueba |
| 7 | Orquestador muestra opciones de observabilidad/modelos | Opciones del setup y runtime | Solo se modifican las elecciones aceptadas |
| 8 | Se valida la configuración y se resume | Router de integraciones y doctor | Configurado; conectividad/permisos siguen sin verificar hasta comprobarlos |

**Ejemplo de petición:** «Configura este proyecto para trabajo local, TDD y cobertura;
de momento no conectes herramientas externas». El resultado no incluye cuentas,
publicaciones, nuevas tareas remotas ni servidores MCP instalados automáticamente.
Una configuración corrupta se revisa; no se borra para volver a preguntar todo.

## W-02. Pasar de una idea a una decisión de producto

**Disparador:** «Necesitamos aprobación de solicitudes; prepara la propuesta».
**Comando:** `/pm-cycle <objetivo>`.
**Agentes:** analyst opcional, evaluator y architect opcional tras el go.
**Skills:** `research-first` si se compara una solución; `code-health` para evidencia
de deuda; `rates-verify` cuando proceda. Contexto de stack y memoria bajo demanda.
**Tools:** búsqueda y lectura del repositorio, scripts de estimación/medición,
escritura de documentos; navegación oficial cuando haga falta investigar.

| Paso | Responsable | Trabajo y artefacto | Decisión/handoff |
|---|---|---|---|
| 1 | Orquestador | Reutiliza o crea la carpeta de iniciativa | No duplica una iniciativa ya existente |
| 2 | Analyst, si hay ambigüedad | Aclara usuarios, permisos, alcance, exclusiones y criterios; produce spec | El usuario revisa requisitos verificables |
| 3 | Evaluator | Lee código y requisitos; prepara evaluación de esfuerzo, coste, tokens, complejidad y riesgos | `evaluation.md` en revisión; cifras estimadas identificadas |
| 4 | Usuario | Decide go, revisar o no-go | Spec aprobada/evaluación completada, iteración o cancelación trazada |
| 5 | Architect, si se elige diseño | Compara opciones y sus consecuencias; usuario elige | `design.md` aprobado y decisión enlazada |
| 6 | Orquestador | Resume decisión y ofrece `/dev-cycle` sobre la misma carpeta | El ciclo PM termina aquí; no implementa automáticamente |

Para el ejemplo, la spec debe aclarar quién puede aprobar, qué ocurre con una
solicitud ya resuelta, qué auditoría se guarda y cómo se comprueba un rechazo sin
motivo. «Pantalla de aprobación» no basta como criterio de aceptación.

**Integraciones:** un contenedor externo solo se prepara si el usuario lo pide y
existe un adaptador compatible con `plan.container`. No se crean todas las tareas
durante la evaluación. `docs.changed` puede proyectar documentación aprobada según
el binding y su política; no sustituye la puerta go/no-go.

## W-03. Seleccionar capacidades y planificar

**Disparador:** se aprueba ejecutar una iniciativa.
**Comandos:** `/work-context` para reconocer el proyecto; `/dev-cycle <iniciativa>`
para recorrer el ciclo. Si la spec/evaluación ya están aprobadas se reutilizan.
**Agente:** planner, con el diseño elegido cuando exista.
**Skills:** `stack-practices`, `backend-practices`, `frontend-quality`,
`delivery-practices`, `api-contract`, `dependency-upgrade` o `research-first`,
según los manifiestos y el objetivo; `roadmap-dashboard` para datos de cartera.

| Paso | Componente | Trabajo concreto | Salida y comprobación |
|---|---|---|---|
| 1 | Contexto compartido | Inspecciona manifiestos/versiones y área de tarea | IDs y procedencia de capacidades pertinentes |
| 2 | `project-pieces.py` | Inventaría agentes, skills, personas, tools y MCP declarados | Referencias de extensiones; disponibilidad aún sin verificar |
| 3 | Planner | Traduce criterios a fases y tareas `T-XX` | `improvement-plan.md` y `tasks.md` en la misma carpeta |
| 4 | Planner | Fija descripción, tipo, archivos, aceptación y verificación por tarea | Scope concreto y comprobable; estimaciones identificadas |
| 5 | Planner | Registra capacidades/extensiones elegidas y escenarios | Implementer, reviewer y QA comparten el mismo contrato |
| 6 | Scripts del ledger | Validan estructura y coherencia del plan | `ledger-lint.py` sin errores antes de ejecutar |
| 7 | Usuario/orquestador | Revisa el plan y sus dependencias | Se aprueba el trabajo que se va a ejecutar |
| 8 | Adaptador opcional | Recibe `plan.created`/`plan.export` | Vista previa de tarea/fase y destino; creación solo autorizada |

Ejemplo de desglose: Fase 1, permisos y modelo; Fase 2, API y UI; Fase 3, verificación
y documentación. Cada tarea conserva su aceptación aunque se elija una tarjeta
remota por fase. La herramienta externa no reduce ese detalle del ledger.

## W-04. Implementar, revisar y comprobar una tarea

**Disparador:** plan aprobado y una tarea lista para empezar.
**Comando:** `/dev-cycle` coordina; no se ejecutan review/QA como si fueran el mismo rol.
**Agentes:** implementer, revisores independientes y qa.
**Skills:** `tdd` cuando está activado; guías seleccionadas del stack;
`adversarial-review`, `unit-tests` y `debug-root-cause` cuando corresponde.
**Tools:** editor, shell, runner oficial del proyecto, scripts de ledger/medición/gates;
Playwright para E2E aplicable, sin inventar pruebas visuales donde no hay UI.

| Paso | Dueño | Acción | Evidencia y efecto externo opcional |
|---|---|---|---|
| 1 | Orquestador | Selecciona tarea y brief acotado; aplica modo normal/lite y delegación elegida | Scope, persona, capacidades y extensiones de esa tarea |
| 2 | Implementer | Marca en-progreso y abre medición | `tasks.md`; evento `task.started` |
| 3 | Implementer + skill TDD | Observa un test rojo antes del código cuando TDD aplica | Caso, fallo y fecha; no cuenta un fallo del fixture como rojo del producto |
| 4 | Implementer | Implementa y ejecuta la verificación declarada | Comando y resultado real, archivos y mediciones; `task.implemented` |
| 5 | Skill de revisión | Comprueba scope y selecciona lentes A/B y C/D condicionales | Lente A: conformidad; B: defectos; C: seguridad; D: rendimiento |
| 6 | Revisores | Inspeccionan con contexto fresco y aportan escenarios/evidencia | Hallazgos graduados; no editan el código que revisan |
| 7 | Skill de revisión | Arbitra hallazgos y rebates, registra intento | Veredictos por criterio; `review.completed` o `review.gaps` |
| 8 | Implementer | Corrige hallazgos válidos con regresión dedicada | Nuevo cambio revisable; no descarta feedback sin evidencia |
| 9 | QA | Ejecuta pruebas aplicables y runner/gate oficial | `testing/`, conteo, capturas si aplica y resultado de `qa-gate.py` |
| 10 | QA | Devuelve veredicto al orquestador | `task.qa-passed` o `task.qa-failed`; no mueve por sí solo a Done |
| 11 | Orquestador | Comprueba revisión sin gaps y QA verde | Permite el cierre local; emite `task.done` con evidencia |

El implementer puede terminar su parte y actualizar el ledger según su contrato,
pero eso no equivale a la aceptación final de entrega. La puerta del orquestador
comprueba ambos veredictos antes de proyectar Done. Los estados permitidos del
ledger no se amplían a mano para imitar cada columna de un tablero externo.

**Si hay fallos:** el ciclo de corrección es acotado. Tras tres rojos de QA, se
ejecuta una pasada de `debug-root-cause`, con reproducción, aislamiento, hipótesis
contrastada y propuesta. Se presenta el diagnóstico y se decide continuar,
replanificar o cancelar. No se baja cobertura ni se falsea el gate para cerrar.

**Si falla la integración:** se conserva el resultado local y se informa de la
operación externa pendiente. No se repite una creación/comentario incierto sin
buscar primero si el proveedor lo recibió. Un problema del tablero no convierte
una revisión roja en verde ni obliga a repetir una prueba ya válida sin motivo.

## W-05. Cerrar una fase y entregar la iniciativa

**Disparador:** las tareas de una fase tienen su evidencia y gates requeridos.
**Comando:** cierre de `/dev-cycle`; `/retro` para el aprendizaje previsto por el ritual.
**Agentes:** implementer verifica la fase; documenter mantiene documentación;
knowledge-curator juzga propuestas de conocimiento cuando existen.
**Skills:** `changelog-sync`, `roadmap-dashboard`, `knowledge-services` solo con opt-in;
`to-pdf` cuando se pide un documento y el módulo/herramienta están disponibles.

| Paso | Dueño | Trabajo | Resultado o puerta |
|---|---|---|---|
| 1 | Implementer/orquestador | Verifica criterios de la fase y resumen de progreso | Ledger coherente; ninguna tarea oculta sin resolver |
| 2 | Implementer | Emite `phase.completed` | Documentación publicable de la fase, una vez por revisión |
| 3 | Documenter | Actualiza los documentos dueños de los cambios | Índices, guías y ejemplos consistentes con el producto |
| 4 | Changelog-sync | Genera notas desde tareas cerradas | Cambios de usuario; no inventa alcance o número de versión |
| 5 | Productores/curator | Proponen y juzgan conocimiento con evidencia | Candidatos separados de approved; sin promoción automática |
| 6 | Orquestador | Verifica rama, cambios propios y pruebas antes de Git | Commits y PR según el flujo aprobado del proyecto |
| 7 | Usuario/CI | Revisión de entrega y comprobaciones requeridas | No se confunde push con CI verde o despliegue |
| 8 | Retro | Compara estimado/real, fallos y decisiones | `retro.md` y calibración con datos ausentes explícitos |
| 9 | Orquestador | Cierra estados solo con el ritual satisfecho | Plan completado/spec implementada según el contrato |

Publicar una release o desplegar son operaciones propias, sujetas al flujo del
repositorio. Pedir un PDF o cerrar tareas no autoriza por sí solo una release.
La publicación externa de docs excluye evidencias sensibles según la política
del adaptador; adjuntar un PDF es otra operación, no un efecto implícito.

## W-06. Hacer un cambio pequeño por la vía rápida

**Disparador:** cambio definido y acotado que no requiere descubrimiento/diseño.
**Entrada:** skill `quick-implement` o vía rápida de `/dev-cycle`.
**Agentes:** implementer, revisión y QA; documenter solo cuando el flujo lo requiere.
**Skills:** las de implementación y calidad de W-04, sin omitir TDD elegido.

El orquestador crea un ledger ligero con una fase, tareas mínimas, criterios y
verificaciones. Omite spec/evaluación/plan extensos; mantiene revisión adversarial
y QA. Se usa el mismo circuito de evidencias y eventos externos. Un cambio con
requisitos inciertos o varias decisiones estructurales vuelve al ciclo ordinario.
No se selecciona esta vía para ahorrar una prueba obligatoria.

## W-07. Consultar cartera, desviaciones y retomar trabajo

| Necesidad y comando | Actor/skill | Lee o produce | Límite y siguiente paso |
|---|---|---|---|
| `/pm-backlog` | Rol PM; datos de `roadmap-dashboard` | Evaluaciones y prioridades de cartera | Priorizar no implementa ni cancela tareas en silencio |
| `/roadmap-status` | `roadmap-dashboard` y `plugin-panel` si está disponible | Ledgers locales; resumen/panel | Snapshot local, no despacho ni procesos vivos |
| `/roadmap-brief` | `roadmap-dashboard`; PDF opcional | Resumen ejecutivo y presupuesto | Fuente y fecha visibles; no inventa mediciones |
| `/roadmap-metrics` | `roadmap-dashboard` | Estimado frente a real | Datos ausentes se conservan; tiempo de reloj no es esfuerzo IA |
| `/roadmap-live` | Adaptador de seguimiento con `task.read` | Estado remoto consultado en ese momento | No modifica el ledger ni promete polling constante |
| `/spec-drift` | Comando de comparación | Spec, plan, código y evidencia | Presenta desviaciones; no reescribe el alcance aprobado por sí solo |
| `/work-resume` | Compositor de progreso e historial | Ledger actual, revisiones y sesión seleccionada | La historia no sustituye el estado actual; selección ambigua se aclara |
| `/plugin-catalog` | `plugin-panel`, módulo de catálogo opcional | Bundle y extensiones, conflictos/procedencia | Declarado no significa cargado ni conectado |

Al retomar, indica la carpeta o slug de la iniciativa. El orquestador recupera
el ledger vigente y las decisiones asociadas, comprueba qué sigue abierto y
continúa desde ahí. No crea otra iniciativa ni reactiva tareas canceladas por
el mero hecho de encontrar un mensaje histórico que decía «continúa».
