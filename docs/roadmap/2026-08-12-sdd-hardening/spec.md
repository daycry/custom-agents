---
spec: sdd-hardening
descripcion: Cerrar los gaps del plugin frente a los motores SDD y monitores externos — constitución del proyecto consumidor, /spec-drift (deriva spec↔código), criterios Given/When/Then opcionales, TDD y worktrees opt-in, skill debug-root-cause, compatibilidad con monitores externos, cadena nativa SIEMPRE por defecto (motor SDD externo solo bajo petición explícita) y desarrollo por subagentes de contexto fresco opt-in — autosuficiencia sin depender de referencia externas
estado: implementada      # borrador | aprobada | implementada | obsoleta
creado: 2026-08-12
actualizado: 2026-08-12
evaluacion: evaluation.md
plan: improvement-plan.md
generacion:               # MEDIDO por usage-meter.py (primera spec con medición real end-to-end)
  inicio: 2026-08-12T07:47:37Z
  fin: 2026-08-12T07:49:09Z
  fuente: medido
  tokens_reales: { entrada: 4, salida: 6276, cache_creacion: 8331, cache_lectura: 754285 }
  eur: 0.54                  # verificado con rates-verify (Opus 4.8; incluye caché) el 2026-08-18
  horas_ia: 0.03
  duracion: 2m                 
  ratio_usado: 479326       # calibrado (mediana de CALIBRATION.md; re-derivado en la retro del 2026-08-18)
---

# SDD hardening — completar el plugin para ser autosuficiente (sin motores SDD externos)

> **Evaluación:** [`evaluation.md`](evaluation.md) — 8 características (ampliada 2026-08-12 ×2: autosuficiencia + 4 mecánicas de subagentes) · 18,5 h base (22,2 h con margen), ~1.150 €, ~1,76 M tokens; veredicto **go** (condición ligera: E2E de juguete para drift y puerta constitucional).
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) — 5 fases · 13 tareas · 19,25 h base (23,1 h con margen) · ~1.195 €.

> **Terminología:** «constitución» = fichero de principios permanentes del proyecto consumidor que todos los agentes leen antes de trabajar (concepto de GitHub Spec Kit, `/speckit.constitution`). «drift» = deriva entre lo que una spec `implementada` dice y lo que el código hace hoy (Spec Kit `/analyze`). «G/W/T» = criterios de aceptación en formato Given/When/Then. «Modo B» = cadena nativa de `/dev-cycle` (sin superpowers). «monitor externo» = herramienta de observabilidad de sesiones vía hooks (p. ej. hoangsonww/Claude-Code-Agent-Monitor).

## Contexto y objetivo

El análisis comparativo (2026-08-12) contra superpowers, GitHub Spec Kit / LiorCohen-sdd y Claude-Code-Agent-Monitor concluyó que el plugin **ya es un plugin SDD** (cadena spec→evaluación→plan→tasks con criterios, ledger canónico, revisión contra spec, puerta económica y calibración — estas dos últimas, únicas nuestras), pero le faltan seis piezas que esos ecosistemas sí tienen. Esta iniciativa las cierra: dos de gobernanza (constitución, drift), una de calidad de specs (G/W/T), dos de disciplina de ingeniería en Modo B (TDD/worktrees opt-in, debugging sistemático) y una de ecosistema (compatibilidad con monitores externos). Principio rector: **no duplicar superpowers** — cuando está instalado (Modo A), su TDD/worktrees/debugging mandan; los nuestros son el fallback opt-in del Modo B.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Dónde vive la constitución | **`docs/CONSTITUTION.md` del proyecto consumidor**, creada/ofrecida por `/setup` (guiado, opt-in) con plantilla en `agent-kits/shared/templates/` | `docs/` es donde el plugin escribe la documentación del consumidor; `/setup` ya es el onboarding de una pasada |
| Quién la lee | **Todos los agentes que escriben** (analyst, evaluator, planner, implementer, qa, documenter) vía fragmento compartido `agent-kits/shared/constitution-check.md` (fuente única, patrón confluence-optin) | DRY: una regla, un fragmento; si falta el fichero, se sigue sin él (opt-in, nunca bloquea) |
| Qué contiene | Principios **permanentes**: estándares de código, decisiones arquitectónicas fijadas/vetadas, convenciones del equipo, restricciones de seguridad. NO estado, NO backlog (eso ya vive en el roadmap) | Igual que Spec Kit: separar lo perenne (constitución) de lo transaccional (specs) |
| Comando de drift | **`/spec-drift [slug]`** (nuevo command, solo lectura): sin slug revisa TODAS las specs `implementada`; con slug, esa. Lanza subagentes de contexto fresco (patrón lente A) que comparan spec+criterios contra el código ACTUAL y emiten drift por criterio: `vigente ✓ / derivado ✗ / no verificable` | Reutiliza el patrón de revisión existente; es el `/speckit.analyze` que falta. Solo lectura: informar, no corregir |
| Salida del drift | **`docs/roadmap/DRIFT.md`** agregado (fecha de análisis + tabla por spec/criterio + veredicto) y resumen conversacional; ofrece abrir iniciativa con `/pm-cycle` para lo derivado | El drift detectado se convierte en trabajo por el cauce normal, no en parches directos |
| G/W/T en criterios | **Opcional, no obligatorio**: la plantilla de spec ofrece las dos formas (checkbox libre actual y bloque `Dado/Cuando/Entonces`); los criterios G/W/T se marcan `[GWT]` y qa los traduce a bloques E2E con mapeo directo criterio→test | Compatibilidad total con specs existentes; el valor es la traducibilidad a tests (mejora la cobertura criterios↔tests de qa-strict), no la ceremonia |
| TDD en Modo B | **Opt-in por config** `.claude/dev.json` → `tdd: true|false` (default `false`; `/setup` lo pregunta). Con `tdd: true`, el implementer sigue RED-GREEN-REFACTOR: test que falla ANTES del código, evidencia del rojo, luego verde, luego refactor. Con `false`, comportamiento actual | Cambio de hábito grande: debe ser elección del equipo, no imposición. En Modo A manda el TDD de superpowers (no se duplica) |
| Worktrees en Modo B | **Opt-in en la misma config** (`worktree: true|false`, default `false`): el implementer trabaja en un worktree de git aislado por iniciativa (`git worktree add`) y lo limpia al cerrar; si el repo no lo soporta (sin git, git viejo), aviso y rama normal | Aislamiento sin ensuciar el árbol principal; degradación limpia |
| Debugging sistemático | **Nueva skill compartida `debug-root-cause`** (4 fases: reproducir mínimamente → aislar la causa con evidencia → formular hipótesis y probarla → fix + test de regresión). La invoca `/dev-cycle` AUTOMÁTICAMENTE cuando el bucle qa→implementer llega al 3.er rojo (antes de parar y preguntar), y a demanda del usuario | Justo donde hoy el bucle acotado se rinde; convierte "parar y preguntar" en "diagnóstico con evidencia y LUEGO preguntar" |
| Monitor externo | **Documentación de compatibilidad**, no implementación: nota en `docs/` (coexistencia de hooks — los nuestros son PostToolUse no bloqueantes, los del monitor son suyos; no chocan), posicionamiento (usage-meter = coste por artefacto con significado de negocio; monitor = actividad de sesión en vivo) y enlace | Es un producto entero (servidor+UI); reimplementarlo dentro del plugin sería reinventar. Preferencia del usuario: no reinventar lo que ya existe |
| Constitución y revisión | La **lente A** de la revisión de dos lentes añade la constitución (si existe) a sus entradas: un diff que viole un principio constitucional es gap de corrección | La constitución sin enforcement es un póster; con la lente A es una puerta |
| Medición | Esta iniciativa **nace medida**: usage-meter por artefacto (primera con `fuente: medido` end-to-end) | Dogfooding de coste-generacion |
| Preferencia de motor (AMPLIACIÓN 2026-08-12) | **La cadena nativa es SIEMPRE el defecto de `/dev-cycle`**, esté o no superpowers instalado. Superpowers pasa a usarse SOLO si el usuario lo pide explícitamente ("usa superpowers", argumento `--superpowers`). Se invierte la detección actual (que delegaba en él al detectarlo) | Decisión del usuario: "la idea es que este plugin tenga las mejores funcionalidades de superpowers, sin depender de superpowers". Con esta iniciativa la cadena nativa queda a la par; la delegación automática ya no se justifica |
| Subagentes de contexto fresco (AMPLIACIÓN 2026-08-12) | **Opt-in `subagentes: true` en `.claude/dev.json`** (default `false`): cada `T-XX` la implementa un **subagente de contexto FRESCO** (Task tool) que recibe SOLO lo necesario (tarea + criterios + extracto del plan + constitución si existe); el orquestador `/dev-cycle` integra el resultado, marca el ledger y mantiene las puertas (dos lentes + qa) exactamente igual | La pieza estrella de superpowers que faltaba: el contexto fresco evita que los sesgos y el ruido de tareas anteriores contaminen la siguiente. Nativo, sin dependencia |

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | Constitución del proyecto consumidor | Plantilla `CONSTITUTION.template.md` en el kit shared (secciones: principios de código, arquitectura fijada/vetada, convenciones, seguridad); `/setup` ofrece crearla guiada (opt-in, idempotente); fragmento `constitution-check.md` en shared: "si existe `docs/CONSTITUTION.md`, léela antes de trabajar y respétala; cítala cuando condicione una decisión"; los 6 agentes que escriben lo referencian; la lente A la usa como entrada de revisión |
| C-02 | `/spec-drift` — deriva spec↔código | Nuevo `commands/spec-drift.md`: recorre specs `implementada` (todas o por slug), lanza subagentes de contexto fresco por spec (lote máx. 3 en paralelo) que verifican cada criterio de aceptación contra el código actual; salida `docs/roadmap/DRIFT.md` (tabla por spec/criterio: vigente/derivado/no-verificable + evidencia fichero:línea) + resumen; ofrece `/pm-cycle` para lo derivado. Solo lectura del código; escribe únicamente DRIFT.md |
| C-03 | Criterios Given/When/Then opcionales | Plantilla de spec con la variante G/W/T documentada (`- [ ] [GWT] Dado… Cuando… Entonces…`); analyst/discovery la ofrecen cuando el criterio describe comportamiento observable; qa: los criterios `[GWT]` se traducen a bloques E2E con mapeo 1:1 y `coverage-check.py` los reconoce (el ID del criterio aparece en el test-plan) |
| C-04 | TDD + worktrees opt-in en Modo B | `.claude/dev.json` (nuevo, creado por `/setup`): `{tdd: false, worktree: false}`. Prosa en `agents/implementer.md` y `commands/dev-cycle.md`: con `tdd: true`, RED-GREEN-REFACTOR por tarea con evidencia del rojo en el ledger; con `worktree: true`, `git worktree add ../<slug> -b <rama>` al arrancar y limpieza al cerrar (degradación a rama normal con aviso si no hay soporte). En Modo A no aplica (manda superpowers). Solo Modo B |
| C-05 | Skill `debug-root-cause` | `skills/debug-root-cause/SKILL.md`: método de 4 fases con evidencia obligatoria por fase (reproducción mínima → aislamiento → hipótesis probada → fix + test de regresión); prohibido "arreglar a ciegas" (cambiar código sin hipótesis probada). `/dev-cycle`: al 3.er rojo de qa, ANTES de parar y preguntar, ejecuta la skill y presenta el diagnóstico con la pregunta. Invocable a demanda ("depura esto a fondo") |
| C-06 | Compatibilidad con monitores externos | `docs/observability.md`: qué mide el plugin (usage-meter: coste por artefacto/tarea) vs qué mide un monitor de sesión (Agent-Monitor: actividad en vivo vía hooks); verificación de coexistencia de hooks (los nuestros PostToolUse no bloqueantes); cómo instalar ambos; enlace desde README e INSTALL |
| C-07 | Cadena nativa siempre por defecto | Invertir la preferencia de `/dev-cycle`: la cadena nativa (antes "Modo B") es EL modo por defecto en todos los casos; superpowers solo bajo petición explícita del usuario (o `--superpowers`), y entonces aplican las reglas de coexistencia actuales (ledger canónico, transiciones las aplica el orquestador). Actualizar `commands/dev-cycle.md`, `CLAUDE.md`, `docs/FLOWS.md` (diagrama 3) y la doc del command. Sin dependencia dura en ningún caso |
| C-08 | Desarrollo por subagentes de contexto fresco (opt-in, con las mecánicas del ciclo de superpowers) | `subagentes: true|false` en `.claude/dev.json` (default `false`, lo pregunta `/setup`): con `true`, `/dev-cycle` despacha cada `T-XX` a un subagente fresco. **Cuatro mecánicas adoptadas del ciclo de superpowers (confirmadas 2026-08-12):** (1) **brief determinista** — nuevo script `agent-kits/shared/task-brief.py` (+tests) extrae de `tasks.md`/`improvement-plan.md` el brief exacto de la tarea (descripción + criterios + sección de arquitectura + su fase + constitución si existe); el orquestador NO redacta el brief a mano; (2) **brief-only** — el subagente trabaja solo con el brief y los ficheros que este referencia, sin explorar el repo entero (dieta de tokens); (3) **estados ricos de retorno** — el subagente reporta `DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED`: `NEEDS_CONTEXT` fuerza re-despacho con el contexto pedido (no inventar), `BLOCKED` escala al orquestador, `DONE_WITH_CONCERNS` pasa las dudas a la revisión; (4) **revisor persistente con severidades** — en el bucle de corrección re-evalúa el MISMO subagente revisor (conserva lo ya juzgado; coherente con la traza `--attempt`) y los gaps se gradúan `Critical / Important / Minor` (Critical/Important obligan corrección; Minor se anota). El orquestador valida contra criterios, marca el ledger y conserva TODAS las puertas (dos lentes, qa-gate, medición por tarea). Re-despacho acotado: 1 con gap/contexto; 2.º fallo → flujo normal con aviso. Combinable con `tdd`/`worktree` |

## Alcance

- **Dentro (esta iteración):** C-01 … C-08 (C-07 y C-08 añadidas en la ampliación del 2026-08-12).
- **Fuera (siguientes specs):**
  - Reimplementar un dashboard de sesión en tiempo real (servidor+UI) — se documenta el monitor externo, no se clona.
  - Fusionar/auto-corregir drift detectado (`/spec-drift` solo informa; la corrección va por `/pm-cycle`).
  - G/W/T obligatorio o migración de specs existentes al formato.
  - TDD en Modo A (superpowers ya lo trae; no se toca).
  - Constitución multi-fichero o jerárquica (una sola `docs/CONSTITUTION.md` por proyecto en esta iteración).
  - **Perfiles de dominio para el subagente de C-08** (persona frontend/backend/db/devops según el tipo de tarea, al estilo wshobson/agents o LiorCohen-sdd): anotado como **spec borrador en el backlog** (`2026-08-12-subagent-personas`) para priorizar con `/pm-backlog`. Decisión del usuario (2026-08-12).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| No existe `docs/CONSTITUTION.md` | Los agentes siguen sin ella (opt-in); `/setup` la ofrece; nunca bloquea |
| `/spec-drift` sin specs `implementada` | Lo dice y termina; no inventa análisis |
| Criterio no verificable contra código (p. ej. criterio de proceso) | Veredicto `no verificable` explícito, no ✓ regalado ni ✗ alarmista |
| `tdd: true` pero la tarea no produce código testeable (docs, prosa) | El implementer lo declara y salta el ciclo RED-GREEN para esa tarea con nota en el ledger |
| `worktree: true` sin git o git sin soporte | Aviso + rama normal (degradación, no bloqueo) |
| 3.er rojo de qa con `debug-root-cause` también fallido | Se presenta el diagnóstico parcial (qué se descartó, qué hipótesis quedan) y SE PREGUNTA — igual que hoy, pero con evidencia |
| Hooks del monitor externo ausentes/rotos | Irrelevante para el plugin: cero dependencia; la doc lo deja claro |
| `dev.json` corrupto o con valores raros | Defaults (`tdd: false, worktree: false`) + aviso; mismo patrón que el resto de configs |

## Pruebas

- `coverage-check.py`: caso nuevo — criterio `[GWT]` con su ID en test-plan.md se reconoce como cubierto; sin él, como no cubierto (tests existentes siguen verdes).
- `/spec-drift` (manual, E2E de juguete): spec `implementada` de juguete con un criterio que el código cumple y otro que no → DRIFT.md marca ✓/✗ correctamente y el no verificable como tal.
- Constitución (manual): con una `docs/CONSTITUTION.md` que vete algo concreto, la lente A detecta un diff que lo viola.
- TDD (manual): con `tdd: true`, el ledger de una tarea de juguete muestra la evidencia del rojo antes del verde.
- `lint_plugin.py` verde (skill y command nuevos con frontmatter/dependencias correctos).
- Esta iniciativa completa con bloques `generacion:` `fuente: medido` en sus 4 artefactos (primera medida end-to-end).

## Referencias

- Análisis comparativo (2026-08-12): [obra/superpowers](https://github.com/obra/superpowers) · [GitHub Spec Kit](https://www.fundesk.io/spec-driven-development-github-spec-kit-guide) · [LiorCohen/sdd](https://github.com/LiorCohen/sdd) · [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor).
- Internas: revisión de dos lentes (qa-strict C-06), `coverage-check.py`, `/setup`, patrón de fragmentos shared, iniciativa coste-generacion (medición).
- preferencias del usuario (memoria del proyecto) — no reinventar lo existente, opt-ins persistentes, no hardcodear, degradación sin bloquear.

## Decisiones confirmadas (conversación con el usuario · 2026-08-12)

1. Abordar la **iniciativa completa** (gaps 1-6), no solo el subconjunto barato. **Confirmado** (eligió "Iniciativa completa" frente a "sdd-hardening reducida").
2. Interés explícito en **valorar SDD**: la valoración concluyó que el plugin ya es SDD y se endurece, no se añade desde cero. **Presentado y aceptado como base de la spec.**
3. **Autosuficiencia** ("que este plugin tenga las mejores funcionalidades de superpowers, sin depender de superpowers"): cadena nativa SIEMPRE por defecto — superpowers solo bajo petición explícita. **Confirmado dos veces** (repregunta incluida). → C-07.
4. **Desarrollo por subagentes de contexto fresco** como opt-in nativo. **Confirmado dos veces.** → C-08.
5. **Las 4 mecánicas del ciclo de subagentes de superpowers** dentro de C-08 (task-brief determinista, brief-only, estados ricos, revisor persistente con severidades). **Confirmado dos veces** (repregunta incluida). Los **perfiles de dominio** → backlog, no esta iniciativa. **Confirmado dos veces.**

## Supuestos

- Sin dependencia de superpowers en NINGÚN caso: todo lo de esta iniciativa es nativo. Si superpowers está instalado Y el usuario pide usarlo explícitamente, aplican las reglas de coexistencia (ledger canónico, transiciones del orquestador) y no se ejecutan dos TDD/reviews a la vez.
- La constitución del proyecto consumidor cabe en un fichero razonable (~1-2 páginas); si el equipo escribe un tomo, el coste de tokens es suyo (se avisa en la plantilla).
- `/spec-drift` sobre specs de PROSA (como las de este plugin) tiene verificabilidad limitada — el veredicto `no verificable` existe para eso.
- `git worktree` disponible en git ≥2.5 (2015); la degradación cubre lo demás.
