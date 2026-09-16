---
spec: knowledge-services
estado: aprobada
creado: 2026-09-15
actualizado: 2026-09-15
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Servicios de conocimiento locales para Kwipu

> [Evaluacion](evaluation.md) · [Diseno](design.md) · [Plan](improvement-plan.md)

## Objetivo

Mantener `docs/knowledge/` como fuente de verdad versionada y anadir un Knowledge Gate local que exporte solo conocimiento aprobado a Kwipu. El plugin es la base de MUCHOS proyectos distintos (no solo de si mismo): la taxonomia de categorias y el enrutado de destino son **configuracion del proyecto consumidor**, nunca una lista fija del plugin. Kwipu sera un recuperador documental opcional; indices y exports son reconstruibles y nunca sustituyen Markdown/Git.

## Alcance

- Candidatos y aprobados bajo `docs/knowledge/`, con categorias **definidas por proyecto** en `.claude/knowledge-services/taxonomy.json` (clave, carpeta, evidencia minima requerida); sin ese fichero, el plugin usa un default minimo propio (`DECISION`, `PATTERN`, `GOTCHA`, `LESSON`, alineado con `adr/`/`gotchas/`/`lessons/` ya existentes) para no romper su propio dogfooding.
- Frontmatter validado: ID estable (prefijo configurable por proyecto), version, estado, evidencia, fuentes, relaciones y tags `clave:valor` normalizados.
- **Lista negra por defecto** (nunca memoria activa, ampliable por proyecto): chain-of-thought, conversacion cruda, TODOs, planes/progreso, logs completos, salidas enormes, codigo duplicado, errores triviales, intentos sin aprendizaje, hipotesis presentadas como hechos, opiniones, redundancias.
- **Escalera de evidencia por defecto** (`observation -> single_case -> validated_case -> multiple_validated_cases -> human_confirmed_rule`), aplicada por cualquier proyecto salvo que declare la suya.
- **Utility scoring opcional** (`taxonomy.json` -> `"utility_scoring": true`): si se activa, el candidato lleva un desglose 0-10 que SOLO ordena la cola de revision; nunca decide `approved`/`rejected` por si mismo. Apagado por defecto.
- **Destination Router configurable**: `.claude/knowledge-services/taxonomy.json` declara, por categoria, si exporta a Kwipu (`true`/`false`/`"summary"`) y si sincroniza a Graphiti (`true`/`false`) cuando esa iniciativa este activa. Sin declaracion explicita, una categoria nueva NO exporta a ningun sitio hasta que el proyecto lo decida (fail-closed).
- Agente `knowledge-curator`, unico dueno de candidatos/aprobados; `documenter` detecta y propone, nunca aprueba ni exporta.
- Exportador determinista a `.claude/knowledge-services/kwipu-export/`, con manifiesto y hashes.
- Opt-in Kwipu en `/setup`, salud/desfase en `/doctor`, y Fase 4-bis despues de QA verde y `documenter`.

## Fuera de alcance

- Graphiti, MCP registration, escritura de memoria conversacional, red desde hooks, migracion masiva y entrenamiento/Ollama.
- Convivencia con un dataset de entrenamiento propio de proyecto (tipo `training_data/`): se abordara en una iniciativa aparte.

## Criterios de aceptacion

- [ ] CA-01 - El esquema valida categorias/evidencia contra `taxonomy.json` del proyecto (o el default del plugin si no existe) y rechaza estados, IDs, tags y referencias invalidas.
- [ ] CA-02 - Candidatos, rechazados, journal, logs y derivados nunca se exportan a Kwipu.
- [ ] CA-03 - Solo el Curator puede aprobar, rechazar, pedir cambios o sustituir conocimiento.
- [ ] CA-04 - El export es idempotente, atomico y reconstruible desde `approved/`.
- [ ] CA-05 - Setup y doctor gestionan Kwipu como capacidad opcional y degradable.
- [ ] CA-06 - La curacion sucede solo despues de QA/documentacion y no altera cierres sin candidatos.
- [ ] CA-07 - Interop, contratos y documentacion ES/EN permanecen sincronizados.
- [ ] CA-08 - Esta entrega no implementa Graphiti.
- [ ] CA-09 - Una categoria sin enrutado declarado en `taxonomy.json` no exporta a ningun backend (fail-closed), y el plugin sigue funcionando con su taxonomia default si el proyecto no configura nada.
- [ ] CA-10 - Con `utility_scoring` activo, el score nunca decide un estado por si solo: un test mutante que fuerce `utility=10` sobre un candidato sin evidencia sigue en `pending`/`rejected`.

## Decisiones confirmadas (usuario, 2026-09-15/16)

1. El proyecto consumidor ya es el limite de aislamiento: no hay `projects/<project_id>/`.
2. Kwipu consulta conocimiento aprobado; Graphiti queda para una iniciativa posterior.
3. El Curator es un agente especializado posterior a QA y `documenter`.
4. Taxonomia y enrutado de destino son configuracion por proyecto (`.claude/knowledge-services/taxonomy.json`), no una lista fija del plugin — el plugin es base de multiples proyectos con dominios distintos.
5. El utility scoring es opt-in, apagado por defecto, y nunca decide un estado por si mismo.
6. La convivencia con un dataset de entrenamiento propio de proyecto se trata en otra iniciativa; no forma parte de esta entrega.