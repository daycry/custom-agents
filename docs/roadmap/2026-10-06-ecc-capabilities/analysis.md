---
estado: borrador
creado: 2026-10-06
actualizado: 2026-10-06
fuente: https://github.com/affaan-m/ECC
revision_fuente: ef648e01899ba3e8dc6371642deaaf64b4477775
version_fuente: 2.2.3
---

# Capacidades de ECC que podemos incorporar a custom agents

> Decisión del usuario, 2026-10-06: los futuros packs deben contemplar PHP/CodeIgniter 4,
> Python y frontend/React. Paquetes, skills, agentes, herramientas, hooks y workflows de ECC
> quedan documentados para una fase posterior; no se implementan en el trabajo actual.

ECC ofrece oportunidades para ampliar custom-agents en especialización técnica, investigación previa, evaluación de resultados y operación de hooks. La recomendación es incorporar capacidades seleccionadas dentro de nuestros agentes y puertas actuales. El catálogo completo añadiría responsabilidades duplicadas y un coste de contexto y mantenimiento que todavía no hemos medido.

Esta propuesta se basa en ECC 2.2.3, revisión `ef648e01899ba3e8dc6371642deaaf64b4477775`, y en el árbol local de custom-agents 1.22.0. Es análisis de código y documentación; no acredita ejecución en vivo de sus integraciones. ECC no se ha instalado ni se han ejecutado sus instaladores, hooks o servicios.

## Qué aporta ECC y qué tenemos cubierto

ECC contiene 68 definiciones de agentes y 293 carpetas de skills en la revisión consultada. Combina instrucciones, scripts, adaptadores de runtimes e integraciones externas. Una skill documentada no implica que su ejecutable o servicio externo venga incluido ni que todas las plataformas tengan la misma capacidad. Su [README](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/README.md) distingue el soporte por plataforma.

Nuestro diferencial actual es el ciclo presupuestado con ledger canónico, roles sin solapes, revisión por lentes, puertas deterministas, memoria curada, Jira/Confluence y medición de coste. ECC aporta especialmente amplitud de conocimiento técnico y mecanismos de operación. La integración debe conservar ese diferencial.

| Área | Situación en custom-agents | Oportunidad |
|---|---|---|
| Planificar, implementar, revisar y probar | Ciclo completo con dueños y puertas definidos | Mantener la cadena; incorporar técnicas dentro de los roles existentes |
| TDD, cobertura, contratos API y seguridad del código | Skills y scripts propios | Aprovechar ejemplos por tecnología; evitar nuevos agentes con el mismo oficio |
| Memoria persistente | Journal durable, búsqueda local, Knowledge Gate y backends declarados | Capturar correcciones y patrones como candidatos con procedencia |
| Especialización | Personas en cascada entregadas; nacimiento de piezas pendiente | Paquetes por stack y selección por proyecto |
| Evals | Activación, expectativas textuales y presencia de artefactos | Medir resolución real de tareas, repetibilidad y coste |
| Hooks | Scripts informativos y guardia de implementer; interop parcial | Contratos por runtime, ejecución portable y diagnóstico de fallos |
| Calidad del catálogo | Lint estructural, dependencias, tamaños y activación | Medir utilidad, redundancia, vigencia y coste de carga |

Fuentes locales: [roles](../../agents/ROLES.md), [contratos](../../agents/CONTRACTS.md), [índice](../../README.md), [evals](../../../evals/README.md), [especialización](../../SPECIALIZATION.md).

## Prioridades propuestas

Las prioridades expresan orden de adopción. No son presupuestos de implementación: cada iniciativa necesitará alcance, evaluación y tareas propias o una ampliación explícita de una existente.

### 1. Operación fiable de hooks

**Prioridad inmediata.** ECC dispone de un lanzador que distingue Node y shell, comprueba candidatos de shell, trata Windows de forma explícita y evita reenviar el payload crudo por stdout. Además tiene perfiles de hooks `minimal`, `standard` y `strict`, con desactivación por identificador. Fuentes: [bootstrap](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/scripts/hooks/plugin-hook-bootstrap.js), [flags](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/scripts/lib/hook-flags.js).

**Aplicación:** resolver intérpretes y rutas por plataforma; validar timeout, evento y formato de salida en el exportador; registrar fallo y duración con datos redactados; mostrar en `/doctor` la diferencia entre hook registrado y hook ejecutado. La captura de SessionEnd sigue siendo breve y la materialización sigue en replay.

**Aceptación:** SessionEnd exportado a Codex con máximo 3 s; pruebas de captura real de envelope y retoma; Windows con rutas con espacios y payload Unicode; ausencia de Python con degradación visible; ninguna copia íntegra del prompt o del resultado de herramientas en logs de diagnóstico.

El límite de 3 s está confirmado en la [documentación oficial de hooks](https://learn.chatgpt.com/docs/hooks), consultada el 2026-10-06. Nuestro export actual conserva los 5 s de Claude. La elección de `bash`/`python3` requiere además pruebas de entorno; cambiar solo el timeout no demuestra que el hook se ejecute correctamente.

**Destino:** arreglo de hooks solicitado y, después, propuesta `hooks-gate-hardening`. No incorporar un deny global: nuestra guardia tiene alcance de agente.

### 2. Investigación antes de diseñar o construir

**Prioridad alta.** [search-first](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/search-first/SKILL.md) compara soluciones existentes en el repo, registros de paquetes, MCP, skills y GitHub antes de elegir adoptar, extender o construir. Declara los canales no disponibles.

**Aplicación:** skill compartida invocada por `analyst` o `architect` ante integraciones, dependencias y utilidades nuevas. Entrega opciones con compatibilidad, mantenimiento, licencia, dependencias y evidencia; `architect` conserva la decisión de diseño. El modo breve evita convertir cada cambio pequeño en una investigación extensa.

**Aceptación:** comparación con enlaces y versiones; decisión explicada; distinción entre solución ausente y canal sin acceso; ninguna dependencia instalada por el mero hecho de investigar. Ejemplo: antes de escribir un cliente de integración, comprobar si el conector disponible ya cubre el contrato.

### 3. Paquetes técnicos por stack

**Prioridad alta; mayor ampliación de capacidades prácticas.** ECC tiene conocimiento específico de Laravel, Django, FastAPI, React, Vue, PostgreSQL, Docker, Kubernetes y otros stacks. Sus [manifiestos de perfiles](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/manifests/install-profiles.json) permiten seleccionar módulos.

**Aplicación:** paquetes opt-in con patrones, seguridad, pruebas y referencias oficiales. Primer piloto pequeño: escoger uno de los stacks que realmente usemos. PHP/CodeIgniter, Python y frontend son candidatos, no una selección confirmada. Para CodeIgniter haría falta material propio: los patrones Laravel no son intercambiables.

**Aceptación:** un pack funciona con `implementer`, `reviewer` y `qa`; se carga solo ante la tarea correspondiente; tiene casos positivos y negativos; su versión y actualización son explícitas. No crear un `python-reviewer` que compita con nuestro `reviewer`: aportar una skill y una persona de dominio.

**Destino:** ampliar `project-specialization` y el instalador tras definir el contrato de packs. Mantener los formatos de fuente canónica y traducción generada.

### 4. Evaluación de resultados de agentes

**Prioridad alta.** [eval-harness](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/eval-harness/SKILL.md) distingue capacidad y regresión, con evaluadores deterministas, humanos o de modelo. [agent-eval](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/agent-eval/SKILL.md) propone comparar agentes por resultado, coste, tiempo y consistencia; depende de una herramienta externa.

**Aplicación:** extender nuestros evals con tareas pequeñas sobre fixtures y commit fijo: implementar una función, corregir un defecto, conservar una restricción y resolver un caso de borde. Juzgar el producto con pruebas y diffs permitidos. Registrar también modelo, versión del prompt, runtime, permisos y coste disponible.

**Aceptación:** detectar una degradación funcional aunque la skill se active; repetir cada caso y comparar con una baseline; fallo del ejecutor separado de fallo del agente; presupuesto máximo explícito para las ejecuciones que consumen tokens.

Las ejecuciones en worktrees proporcionan separación de archivos, no contención de procesos o red. El [framework ejecutable de ECC](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/docs/architecture/eval-harness-frameworks.md) ofrece herramientas offline; la ejecución de candidatos y su promoción siguen deshabilitadas. Diseñar nuestro piloto con ese límite presente.

**Destino:** `evals/`, reutilizando casos Gold y separación por familia de `training-data-services` cuando corresponda. Un caso Gold no debe convertirse simultáneamente en entrenamiento y benchmark.

### 5. Aprendizaje desde correcciones y patrones repetidos

**Prioridad media, después de estabilizar captura y especialización.** [continuous-learning-v2](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/continuous-learning-v2/SKILL.md) conserva observaciones por proyecto, deriva comportamientos atómicos y permite agruparlos en skills. El observador está desactivado por defecto en su configuración.

**Aplicación:** detectar candidatos desde correcciones del usuario, resolución de errores y casos aprobados. Guardar desencadenante, acción, procedencia, frecuencia y contraejemplos. `knowledge-curator` sigue siendo el único que aprueba conocimiento; `/specialize` puede convertir conocimiento aprobado en una pieza activable.

**Aceptación:** separación entre proyectos; redacción y opt-out antes de capturar; trazabilidad hasta las observaciones; corrección o retirada de una regla errónea. La frecuencia y la puntuación del modelo no equivalen a probabilidad de verdad. La promoción a doctrina compartida requiere evidencia y aprobación.

**Destino:** `dev-cycle-dataset`, Knowledge Gate y especialización; evitar una segunda base de memoria con autoridad distinta.

### 6. Auditoría de utilidad del catálogo

**Prioridad media.** [skill-stocktake](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/skill-stocktake/SKILL.md) revisa vigencia, redundancia y utilidad, y propone conservar, mejorar, actualizar, fusionar o retirar. Su evaluación combina checklist y juicio del modelo.

**Aplicación:** complementar nuestro lint con un inventario determinista de referencias, tamaños, uso observado y resultados de evals. Dejar el juicio semántico en un informe revisable y acotado. Las cifras de uso no prueban calidad ni justifican retirar una capacidad infrecuente de alto valor.

**Aceptación:** cada propuesta cita un solape o una carencia concreta; las modificaciones se distinguen de las recomendaciones; una retirada comprueba dependencias y rutas generadas; el modo incremental reevalúa solo lo cambiado.

### 7. Seguridad de la configuración de agentes

**Prioridad media.** [security-scan](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/security-scan/SKILL.md) usa AgentShield para analizar instrucciones, permisos, configuración MCP y hooks, además de secretos e inyección.

**Aplicación:** una dimensión de `nemesis` dedicada al entorno del agente: procedencia de plugins, permisos amplios, comandos interpolados, transporte de datos y puntos donde contenido del proyecto se convierte en instrucciones. Evaluar AgentShield como dependencia opcional frente a extender los checks existentes.

**Aceptación:** un conjunto de configuraciones maliciosas y legítimas mide detección y falsos positivos; cobertura por runtime declarada; el score agregado no sustituye hallazgos reproducibles. No constituye una garantía de aislamiento de un plugin instalado.

### 8. Recuperación progresiva con presupuesto

**Prioridad media, después de brief-budget.** [iterative-retrieval](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/iterative-retrieval/SKILL.md) propone refinar la búsqueda en ciclos acotados. [context-budget](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/context-budget/SKILL.md) inventaría agentes, skills, reglas y MCP para detectar consumo de contexto.

**Aplicación:** cuando un subagente devuelve `NEEDS_CONTEXT`, resolver la carencia concreta, añadir evidencia pertinente y volver a despachar con límite de intentos y tamaño. Extender `/doctor` con estimación de carga por pieza y medidas del runtime cuando existan.

**Aceptación:** una tarea recupera el fichero que necesita sin recibir el repo entero; respeta restricciones del brief y separación de proyectos; distingue bytes, caracteres, tokens estimados y tokens medidos. Las heurísticas de ECC para estimar tokens no deben etiquetarse como facturación ni contexto activo real.

## Ideas de segunda etapa

**Revisión visual de planes.** [plan-canvas](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/plan-canvas/SKILL.md) ofrece anotaciones sobre artefactos locales y devolución de feedback en JSON. Puede enriquecer `project-dashboard`; no necesita otra iniciativa de dashboard. Una anotación debe conservar su vínculo con la versión del plan y un estado de aprobación explícito.

**Formato y typecheck en lote.** El [hook stop-format-typecheck](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/scripts/hooks/stop-format-typecheck.js) acumula archivos y agrupa ejecuciones por proyecto. Podemos adoptar la agrupación en nuestras puertas de `implementer`/`qa`. Activar ediciones automáticas al final de un turno exige que entren en el alcance y se vuelvan a verificar.

**Salud MCP.** ECC tiene un [check de salud](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/scripts/hooks/mcp-health-check.js). Su código distingue alcanzabilidad HTTP de contrato MCP; un HTTP 401/404 puede demostrar que un servidor responde sin demostrar que la integración funcione. Nuestro registro de capacidades debe conservar salud, autenticación, herramientas requeridas y resultado de operación como señales distintas.

**Operaciones y contenido.** Los módulos de research, business, documentación y multimedia amplían el dominio del producto. Incorporarlos cuando haya un caso de uso concreto y herramientas accesibles; el piloto técnico anterior tiene una integración más directa con nuestro flujo actual.

## Qué conviene conservar de nuestra arquitectura

Mantener el ledger como fuente del progreso, el Knowledge Gate como puerta de aprobación y las traducciones de interop como artefactos generados. Integrar capacidades dentro del rol que decide hoy cada responsabilidad. La especialización aporta conocimiento y herramientas pertinentes; no crea otro dueño de pruebas, revisión, arquitectura o documentación.

Separar el catálogo de skills del control-plane Rust de `ecc2/`, que su [README](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/ecc2/README.md) describe como alpha. Sus sesiones y observabilidad son referencias para nuestro dashboard, no una dependencia inmediata. Su [roadmap](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/docs/ROADMAP.md) reconoce solapes en el catálogo y trabajo pendiente de contención y evaluaciones operativas.

Si se incorpora código o texto de ECC, conservar procedencia, revisión fuente y atribución exigida por su [licencia MIT](https://github.com/affaan-m/ECC/blob/ef648e01899ba3e8dc6371642deaaf64b4477775/LICENSE). Revisar por separado licencias, servicios y condiciones de cada dependencia sugerida.

## Orden de ejecución propuesto

1. Corregir y verificar los hooks solicitados; completar `brief-budget`.
2. Cerrar `plugin-refactor` y entregar el nacimiento de piezas de `project-specialization`.
3. Añadir investigación previa y pilotar un pack técnico seleccionado por uso real.
4. Ampliar evals con resultados y repetibilidad; usar el dataset con separación train/benchmark.
5. Proponer aprendizaje desde correcciones, auditoría de catálogo y seguridad de configuración.
6. Integrar recuperación progresiva y revisión visual en las iniciativas existentes cuando sus contratos estén listos.

El orden mantiene las tareas ya autorizadas y evita que la ampliación dependa de un mecanismo de carga que aún no está terminado. `dev-cycle-dataset` conserva su iniciativa; la relación con evals y aprendizaje se define al evaluar estos deltas.

## Relación con el análisis anterior

[ideas-externas de 2026-09-04](../2026-09-04-ideas-externas/analysis.md) estudió un espejo congelado de Everything Claude Code. Sus observaciones siguen siendo evidencia de aquella revisión, pero sus cifras y diagnósticos no describen ECC 2.2.3. En particular, el árbol actual tiene inyección de contexto por stdout en SessionStart, observación y CLI de aprendizaje por proyecto, perfiles de instalación y un framework offline de evaluaciones. Esta comparación actualiza las oportunidades sin reescribir el documento histórico.

Estado de esta propuesta: análisis preparado. No se ha aprobado una spec, calculado un presupuesto ni implementado una capacidad nueva.
