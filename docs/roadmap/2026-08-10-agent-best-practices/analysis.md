# Estrategias de los agentes top aplicadas a `custom-agents`

**Fecha:** 2026-08-10 · **Base analizada:** plugin v1.8.0 (agents/, commands/, skills/, agent-kits/, hooks/, CLAUDE.md, CONVENTIONS.md)

He contrastado el plugin con las cuatro referencias que marcan el estado del arte: la colección **wshobson/agents** (los "pro" por lenguaje: `rust-pro`, `cpp-pro`, etc., ~75 agentes en producción), **VoltAgent/awesome-claude-code-subagents** (100+ especialistas, entre ellos su `cpp-pro`), **obra/superpowers** (la metodología de desarrollo empaquetada como skills) y las **buenas prácticas oficiales de Anthropic** para Claude Code. El resultado es una buena noticia: el plugin ya aplica varias de las estrategias top mejor que muchas colecciones famosas. Pero hay seis estrategias contrastadas que no aplica y que darían una mejora real.

## Lo que el plugin ya hace al nivel de los mejores

Antes de las mejoras, lo que no hay que tocar. La **delimitación negativa de rol** ("no estimas, eso es evaluator; no planificas, eso es planner") está en cada agente y es más disciplinada que en wshobson o VoltAgent, donde los especialistas a menudo se solapan. La **externalización del formato a plantillas** (agent-kits con resolución de ruta en runtime) es exactamente la "progressive disclosure" que predica superpowers, aplicada al formato de salida. Los **guardrails delegados a script** (`lib-guardrail.sh` en nemesis y qa) siguen la recomendación oficial de Anthropic de que lo innegociable se imponga con código determinista, no con texto en el prompt. Y las **puertas go/no-go con máquina de estados** en `/dev-cycle` y `/pm-cycle` son el patrón "sequential + review & validation" que wshobson implementa en sus workflows. En orquestación, el plugin no tiene nada que envidiar.

## Las seis estrategias que faltan

### 1. Model tiering — la estrategia más rentable y la más ausente

Es la seña de identidad de wshobson/agents: cada agente declara su modelo según la complejidad de su tarea (15 en Haiku para trabajo mecánico, 45 en Sonnet para desarrollo estándar, 15 en Opus para análisis crítico: security-auditor, architect-review, incident-responder). **Ninguno de los 8 agentes del plugin declara `model`**, pese a que CONVENTIONS.md §4 ya lo contempla como campo válido. Todos heredan el modelo de la sesión, así que `pdfy` (orquestar una conversión a PDF) cuesta lo mismo que `nemesis` (auditoría de seguridad en 8 dimensiones).

Propuesta de asignación, siguiendo el criterio de wshobson:

| Agente | Modelo propuesto | Razón |
|---|---|---|
| pdfy | `haiku` | Orquestación mecánica de una skill; cero razonamiento |
| documenter, qa, implementer | `sonnet` | Trabajo de desarrollo estándar, guiado por plantillas y ledger |
| analyst, planner | `sonnet` (o `inherit`) | Conversación dirigida y estructura; las plantillas hacen el trabajo pesado |
| evaluator, nemesis | `opus` (o `inherit`) | Estimación calibrada y auditoría de seguridad: los dos casos que wshobson reserva a Opus |

Es un cambio de una línea por fichero, sin riesgo funcional, con impacto directo en coste y latencia.

### 2. Tools mínimos: que la restricción sea mecánica, no semántica

Anthropic recomienda que cada subagente declare solo las herramientas que necesita; el `security-reviewer` de ejemplo de la doc oficial declara `Read, Grep, Glob, Bash` y nada más. En el plugin, evaluator, planner y qa son agentes que **por diseño no tocan el código** — y sin embargo declaran `Write, Edit` y se autolimitan con frases como "No toques el código". La restricción vive en el prompt, donde un contexto largo puede diluirla, en lugar de vivir en el toolset, donde es imposible saltársela.

Matiz importante: estos agentes sí escriben *sus artefactos* (evaluation.md, planes, informes), así que `Write` deben conservarlo. Pero `Edit` sobre código fuente no lo necesitan evaluator ni planner (editan sus propios .md, que pueden reescribir con Write), y conviene revisar agente a agente qué es imprescindible. `pdfy` ya lo hace bien (sin `Edit`, coherente con "no toques el original") — es cuestión de extender ese criterio.

### 3. DoD explícita y verificable: "evidence over claims"

Es el principio central de superpowers (su skill `verification-before-completion` impide cerrar una tarea sin evidencia) y la recomendación #1 de la guía oficial: *"dale a Claude una comprobación que pueda ejecutar; que muestre evidencia en vez de afirmar éxito"*. En el plugin la definition-of-done es textual y cualitativa ("no marques completado con tests fallando", "estado global verde") sin una sección estructurada que el agente deba recorrer antes de cerrar.

La mejora concreta: añadir a cada agente una sección final `## ANTES DE CERRAR (DoD)` con 3-5 comprobaciones ejecutables y la obligación de mostrar la evidencia (salida del comando, ruta del artefacto generado, checkbox marcado en tasks.md). Por ejemplo, para implementer: "1) pega la salida del test runner; 2) confirma que cada T-XX tocado tiene su checkbox actualizado en tasks.md; 3) confirma que no hay ficheros fuera del alcance del plan en `git status`". Para qa ya existe `results.json` — basta definir el umbral de "verde" de forma explícita (0 failed, 0 flaky sin justificar). Esto convierte el juicio subjetivo del LLM en un checklist auditable, que es exactamente lo que hace que las sesiones desatendidas de superpowers funcionen.

### 4. Revisión adversarial con contexto fresco entre implementer y qa

Superpowers hace revisión en dos etapas tras cada tarea: primero conformidad con la spec, después calidad del código — siempre con un subagente nuevo, porque *"un contexto fresco mejora la revisión: el modelo no está sesgado hacia el código que acaba de escribir"* (guía oficial, patrón Writer/Reviewer). En la cadena del plugin, quien verifica es `qa`, pero qa verifica **comportamiento E2E**, no revisa el diff contra el plan. Nadie comprueba que implementer implementó *lo que decía el plan y solo eso*.

La mejora: un paso de revisión (en `/dev-cycle`, entre Fase 3 y qa) que lance un subagente con contexto limpio y este prompt-tipo: "Revisa el diff de la iniciativa contra improvement-plan.md y tasks.md: cada requisito implementado, cada criterio de aceptación con su test, nada fuera de alcance. Reporta gaps, no preferencias de estilo". Puede ser un agente nuevo (`reviewer`) o simplemente un paso del command que use un subagente genérico — la segunda opción es más barata y no engorda el plugin. Importante incluir la advertencia de la doc oficial: pedirle solo gaps de corrección/requisitos, no sugerencias, para evitar sobre-ingeniería.

### 5. Descriptions optimizadas para el enrutado (y solo para eso)

Las colecciones top tratan la description como lo que es: la señal de enrutado que Claude lee para auto-delegar. Cortas, orientadas a triggers, sin detalle de implementación. En el plugin hay una inconsistencia clara: analyst, implementer, qa, documenter y pdfy cierran con frases-gatillo ("Úsalo cuando el usuario diga…"), pero **evaluator, planner y nemesis no las tienen**, y evaluator/planner gastan la description en rutas y nombres de plantilla (`docs/roadmap/<fecha>-<slug>/`, `agent-kits/evaluator/templates/`) que no ayudan a enrutar. No es casual que los commands tengan que decretar "invoca a los agentes por nombre; no dependas de la auto-delegación": la auto-delegación falla en parte porque esas tres descriptions no compiten bien.

La mejora: reescribir las tres al patrón de las otras cinco (qué hace en una frase + "Úsalo cuando el usuario diga X, Y, Z"), moviendo el detalle de rutas al cuerpo del prompt. wshobson añade además "Use PROACTIVELY when…" en los agentes que quiere que salten solos — útil para nemesis ("PROACTIVAMENTE cuando el usuario mencione seguridad, vulnerabilidades, auditoría").

### 6. DRY entre agentes: extraer lo duplicado a fragmentos compartidos

Hay tres duplicaciones literales que van a derivar tarde o temprano: la tabla de parámetros de estimación (tarifa 50 €/h, supervisión ~25%, margen 20%…) copiada en evaluator §1 y planner §1; el párrafo "Sincronizar con Confluence (opt-in)" casi idéntico en evaluator, planner, qa y documenter; y las tablas de transición de estados repetidas en dev-cycle, pm-cycle y CONVENTIONS §7. El día que cambie el ratio de supervisión o un nombre de estado habrá que tocar 3-4 ficheros y alguno se quedará atrás.

La mejora sigue la convención que el plugin ya usa: mover cada bloque a un fichero único (p. ej. `agent-kits/shared/estimation-defaults.md`, `agent-kits/shared/confluence-optin.md`, la tabla de estados solo en CONVENTIONS) y que los agentes lo referencien con la misma resolución `find` que ya usan para sus kits. Menos prompt inline además acorta los agentes largos (documenter 148 líneas, nemesis 173), en línea con el consejo oficial de que los prompts sobrecargados hacen que las reglas importantes se pierdan.

## Arreglos puntuales detectados por el camino

Verificados directamente sobre los ficheros: **planner.md tiene dos pasos "P7"** (línea 85 "Volcado a Jira" y línea 87 "Sincronizar con Confluence") — renumerar a P7/P8 y el actual P8 a P9. Y **nemesis.md referencia secciones "§6, §11, §14, §17" de un system prompt base** que no viaja con el plugin; en una instalación ajena esas referencias apuntan a nada y conviene inlinear lo esencial o eliminarlas. Adicionalmente, el grafo `dependencies` del frontmatter es documental y nada lo valida: un chequeo en CI (ya tenéis CI y `release.py`) que verifique que los agentes/skills/kits referenciados existen y que las descriptions cumplen el patrón de triggers costaría poco y evitaría deriva — es el equivalente al "linter de plugin" que las colecciones grandes acaban montando.

## Estrategias que evalué y descarto (por ahora)

El "communication protocol" JSON de VoltAgent (el agente pide contexto con un payload estructurado antes de trabajar) queda cubierto por vuestras secciones `ENTRADA/SALIDA — INVARIANTE`, que hacen lo mismo con menos ceremonia. El TDD estricto RED-GREEN-REFACTOR de superpowers es valioso pero es una decisión de metodología de los proyectos donde se use el plugin, no del plugin — y `/dev-cycle` ya delega en superpowers cuando está instalado, que es la integración correcta. Y los few-shot largos dentro del prompt (estilo VoltAgent) los suple mejor vuestro ejemplo completo `docs/examples/ci4-forms-emails/` — bastaría que evaluator y planner lo citen como referencia de salida en una línea.

## Orden recomendado

**Quick wins (una sesión, riesgo nulo):** model tiering (#1), fix del doble P7, descriptions de evaluator/planner/nemesis (#5), referencias §§ de nemesis. **Segundo bloque (medio día):** tools mínimos (#2), secciones DoD (#3), extracción de duplicados (#6). **Tercer bloque (requiere diseño):** paso de revisión adversarial en /dev-cycle (#4) y linter de plugin en CI. Todo es acumulativo y ningún cambio rompe compatibilidad con instalaciones existentes.

## Fuentes

- [Best practices for Claude Code — doc oficial](https://code.claude.com/docs/en/best-practices) (verificación ejecutable, subagentes de revisión con contexto fresco, tools mínimos, prompts concisos)
- [wshobson/agents — colección de subagentes production-ready](https://github.com/wshobson/agents) ([README detallado](https://openaitx.github.io/projects/wshobson/agents/README-en.html)) (model tiering Haiku/Sonnet/Opus, descriptions con triggers, patrones de orquestación)
- [VoltAgent/awesome-claude-code-subagents — cpp-pro](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/02-language-specialists/cpp-pro.md) (checklists de verificación, fases de workflow, integración con otros agentes)
- [obra/superpowers](https://github.com/obra/superpowers) (evidence over claims, verificación antes de cerrar, revisión en dos etapas con subagente fresco, progressive disclosure)
