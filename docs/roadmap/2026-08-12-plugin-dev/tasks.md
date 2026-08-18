---
generacion:               # vía rápida MEDIDA (usage-meter)
  inicio: 2026-08-12T20:33:43Z
  fin: 2026-08-12T20:43:33Z
  fuente: medido
  tokens_reales: { entrada: 40, salida: 16104, cache_creacion: 33031, cache_lectura: 2091654 }
  eur: 1.52                  # verificado con rates-verify (Opus 4.8; incluye caché) el 2026-08-18
  horas_ia: 0.1
  duracion: 6m                 
  ratio_usado: 479326       # calibrado (mediana de CALIBRATION.md; re-derivado en la retro del 2026-08-18)
---

# Checklist de Tareas — plugin-dev (vía rápida: meta-skill de desarrollo del plugin)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-12 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Origen:** equivalente nativo al *writing-skills* de superpowers, generalizado a TODO el plugin (agentes, skills, comandos, kits, hooks). Estimación gruesa: ~2,5 h base. Nota de medición: la ventana cubre la sesión principal; el consumo de los 2 subagentes de revisión puede no estar íntegro en la transcripción medida.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Meta-skill plugin-dev | 2 | 2 | 100% | 0 / 2,5h | 0,10 (medido) / 0,8h | 0 / 0,25h | 49k (medido) / 250k |
| **TOTAL** | **2** | **2** | **100%** | **0 / 2,5h** | **0,10 (medido) / 0,8h** | **0 / 0,25h** | **49k (medido) / 250k** |

---

## Fase 1 — Meta-skill plugin-dev

**Estado**: completado · **Estimado**: 2,5h · **Real**: — · **Coste est.**: ~130 € · **Tokens est.**: 250k

### T-01 — Skill `plugin-dev` (SKILL.md + plantillas)

- **Descripción**: Skill compartida `skills/plugin-dev/` con el proceso canónico para crear/modificar piezas del plugin: árbol de decisión de tipo de pieza (agente/comando/skill/kit privado/fragmento shared/hook), reglas de nombre y colisiones (citando `GENERIC_NAME_TOKENS` real del linter), frontmatter obligatorio (model tiering, tools mínimos, `dependencies`), 5 reglas de cuerpo (determinismo en scripts con tests+exit codes, degradación sin bloquear, resolución `find` de rutas, DRY vía `agent-kits/shared/`, no reinventar — con las rutas REALES de los scripts existentes), validación TDD-ish en orden estricto (test primero → linter → suites con la MISMA invocación que la CI → auto-revisión adversarial), tabla de doc obligatoria por tipo de pieza y anti-patrones vistos en revisiones reales. Plantillas rellenables: `templates/agent.template.md` (comentarios en línea propia — el parser del linter no tolera inline en claves de nivel 0; verificado rellenándola contra `parse_frontmatter`), `templates/skill.template.md`, `templates/command.template.md` (con frontmatter `description`/`argument-hint` y `$ARGUMENTS`, como los 8 comandos reales).
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,16h (medido, ventana completa)
- **Supervisión**: est. 0,2h · real —
- **Archivos**: `skills/plugin-dev/SKILL.md`, `skills/plugin-dev/templates/*.template.md`

**Criterios de aceptación**
- [x] Frontmatter con disparadores; nombre por función sin colisiones (linter sin errores nuevos)
- [x] El paso de validación funciona TAL CUAL está escrito (suites-script + pytest de shared, igual que la CI) — verificado ejecutándolo
- [x] Un agente creado rellenando la plantilla pasa el parser del linter (verificado empíricamente)
- [x] Ninguna afirmación factual sobre el repo es falsa (rutas de scripts, tokens genéricos del linter, hooks PostToolUse) — verificado por la revisión

### T-02 — Documentación y cierre

- **Descripción**: Fila en "Skills compartidas" de `docs/README.md` (usuaria: sesiones de trabajo sobre el propio repo; ningún agente la declara como dependencia — coherente con el grafo), fila en la tabla de skills de `CLAUDE.md`, entrada en `CHANGELOG.md` `[Sin publicar]`, ledger + fila en `docs/roadmap/README.md`, medición usage-meter cerrada sin huérfanos.
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real — (incluido en la ventana de T-01)
- **Supervisión**: est. 0,05h · real —
- **Archivos**: `docs/README.md`, `CLAUDE.md`, `CHANGELOG.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-08-12-plugin-dev/tasks.md`

**Criterios de aceptación**
- [x] La skill cumple sus PROPIAS obligaciones del Paso 4 (docs/README + CLAUDE.md + CHANGELOG; FLOWS no aplica — no cambia ningún flujo)
- [x] Revisión de dos lentes superada: 7 hallazgos (2 críticos: invocación pytest que no recogía tests; comentarios inline que rompían el linter en la plantilla de agente) corregidos y re-verificados
- [x] Linter sin errores nuevos + 6 suites del repo + 45 tests pytest en verde tras las correcciones
