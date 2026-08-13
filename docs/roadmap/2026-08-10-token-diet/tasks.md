# Checklist de Tareas — Dieta de tokens del plugin

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-10 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Quick wins | 3 | 3 | 100% | 0 / 4,75h | 0 / 1,4h | 0 / 0,35h | 0 / 560k |
| Fase 2 — Medianas | 4 | 4 | 100% | 0 / 6,0h | 0 / 1,6h | 0 / 0,40h | 0 / 675k |
| Fase 3 — Cierre y verificación | 1 | 1 | 100% | 0 / 0h | 0 / 0h | 0 / 0h | 0 / 0 |
| **TOTAL** | **8** | **8** | **100%** | **0 / 10,75h** | **0 / 3,0h** | **0 / 0,75h** | **0 / 1,24M** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.
>
> Horas/tokens **base** (sin margen), heredadas de `evaluation.md` por característica. El +20 % de contingencia y la conversión a coste se ven en `improvement-plan.md`. La Fase 3 no lleva horas propias: su trabajo (CHANGELOG, consolidación de README, lint final) se absorbe en el margen.


> **Estado:** implementado en la sesión Cowork 2026-08-10 (dogfooding). Pendiente de revisión del usuario → plan `completado`, spec `implementada`. Hallazgo de implementación: el ahorro de C-03 (progressive disclosure) es **modesto** — documenter y nemesis ya externalizaban gran parte de su detalle a sus kits (taxonomy.md, tools/); se movió lo que quedaba solo-de-fase (redaction-guide.md, interpretation.md). Horas reales no cronometradas (ejecución IA continua).

---

## Fase 1 — Quick wins

**Estado**: completado · **Estimado**: 4,75h · **Real**: — · **Coste est.**: 248 € · **Tokens est.**: 560k

### T-01 — C-01 · Fragmento `read-discipline.md` + adopción

- **Descripción**: crear el fragmento compartido de disciplina de recon y adoptarlo en los cuatro agentes que exploran el repo, para recortar el mayor foco de tokens (leer de más en el recon).
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 200k in / 20k out tok · 4,1 €
- **Dependencias**: ninguna (independiente; comparte mecánica con T-02)
- **Archivos**: `agent-kits/shared/read-discipline.md`, `agents/documenter.md`, `agents/nemesis.md`, `agents/evaluator.md`, `agents/qa.md`, `agent-kits/shared/README.md`
- **Cubre (tests)**: — (sin UI; verificación por inspección de prompts)

**Criterios de aceptación**
- [x] Existe `agent-kits/shared/read-discipline.md` con: grep/glob antes de `Read`, `Read` con `limit`, lista de rutas/globs a ignorar (`node_modules/`, `vendor/`, lockfiles, `dist/`, binarios, `.min.*`) y la regla «lee fragmentos, no ficheros completos, salvo que el fichero sea el objeto de trabajo».
- [x] documenter (P2), nemesis (SAST), evaluator (P2) y qa (P1) lo referencian vía `$SHAREDKIT` con **fallback de una línea**.
- [x] El fragmento aparece registrado en `agent-kits/shared/README.md`.

**Subtareas**
- [x] Redactar `read-discipline.md` con reglas objetivas y verificables.
- [x] Añadir la referencia `$SHAREDKIT` + fallback en documenter, nemesis, evaluator y qa.
- [x] Registrar el fragmento en `agent-kits/shared/README.md`.

**Notas**: coste unitario calibrado con C-06 de `agent-best-practices` (fragmento DRY + 4 referencias).

### T-02 — C-04 · Fragmento `output-discipline.md` + adopción

- **Descripción**: crear el fragmento de disciplina de salida (handoff = datos, no informe) y adoptarlo en los agentes de cadena, para recortar la acumulación de resúmenes en el orquestador (ahorro que se multiplica por ciclo).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,45h · real —
- **Supervisión**: est. 0,11h (≈25 % IA) · real —
- **Previsión IA**: 180k in / 18k out tok · 3,7 €
- **Dependencias**: ninguna (independiente de T-01; misma mecánica)
- **Archivos**: `agent-kits/shared/output-discipline.md`, `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md`, `agent-kits/shared/README.md`
- **Cubre (tests)**: — (sin UI; verificación por inspección de prompts)

**Criterios de aceptación**
- [x] Existe `agent-kits/shared/output-discipline.md`: «mensaje final ≤ ~12 líneas, rutas + cifras + estado, sin recap de pasos; el detalle vive en los artefactos».
- [x] evaluator, planner, implementer, qa y documenter lo referencian vía `$SHAREDKIT` con **fallback de una línea**.
- [x] Se concilia el límite de ~12 líneas con los DoD que piden «mostrar evidencia» (el mensaje es puntero + cifras; la evidencia detallada queda en los artefactos), y se precisa si el límite es guía o duro.
- [x] El fragmento aparece registrado en `agent-kits/shared/README.md`.

**Subtareas**
- [x] Redactar `output-discipline.md` (formato del handoff + excepción de agentes que reportan a humano directo).
- [x] Añadir la referencia `$SHAREDKIT` + fallback en los cinco agentes de cadena.
- [x] Registrar el fragmento en `agent-kits/shared/README.md`.

**Notas**: conciliar «evidencia» del DoD con el límite de líneas es el único punto de diseño; el resto es mecánico.

### T-03 — C-02 · Filtrado de payloads Atlassian

- **Descripción**: pedir siempre campos explícitos en las llamadas a Atlassian de `jira-sync`, `roadmap-dashboard` y `roadmap-live`, y documentar el patrón como regla en el SKILL de `jira-sync`.
- **Estado**: completado
- **Tiempo humano**: est. 1,25h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,09h (≈25 % IA) · real —
- **Previsión IA**: 130k in / 12k out tok · 2,6 €
- **Dependencias**: ninguna (independiente del resto)
- **Archivos**: `skills/jira-sync/SKILL.md`, `skills/jira-sync/scripts/`, `skills/roadmap-dashboard/`, `commands/roadmap-live.md`
- **Cubre (tests)**: — (sin UI; verificación por inspección de las llamadas)

**Criterios de aceptación**
- [x] Las búsquedas/creaciones de `jira-sync` y las lecturas de `roadmap-dashboard`/`roadmap-live` declaran `fields` explícitos (solo los usados), `maxResults` acotado y `searchResultMode:"issues"`.
- [x] El SKILL de `jira-sync` documenta la regla, incluida la política «si falta un campo, se añade a la lista; nunca se vuelve a "todos los campos"».

**Subtareas**
- [x] Derivar la lista mínima de `fields` por tipo de llamada (búsqueda JQL vs. lectura) a partir del uso real.
- [x] Aplicar `fields`/`maxResults`/`searchResultMode` en `jira-sync`, `roadmap-dashboard` y `roadmap-live`.
- [x] Documentar el patrón y la política en el SKILL de `jira-sync`.

**Notas**: el ahorro real depende del volumen de issues; no medible sin ejecución.

---

## Fase 2 — Medianas

**Estado**: completado · **Estimado**: 6,0h · **Real**: — · **Coste est.**: 313 € · **Tokens est.**: 675k

### T-04 — C-03a · Progressive disclosure de documenter

- **Descripción**: mover el detalle paso-a-paso de las fases largas de `documenter` (148 líneas) a ficheros de su kit, dejando en el `.md` el flujo de alto nivel + punteros; el detalle se lee cuando el agente entra en la fase. Sin cambiar comportamiento.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,45h · real —
- **Supervisión**: est. 0,11h (≈25 % IA) · real —
- **Previsión IA**: 150k in / 18k out tok · 3,3 €
- **Dependencias**: ninguna dura (mucha lectura de contexto: prompt largo completo)
- **Archivos**: `agents/documenter.md`, `agent-kits/documenter/`
- **Cubre (tests)**: — (sin UI; verificación por inspección + contraste cualitativo con `/context`)

**Criterios de aceptación**
- [x] `agents/documenter.md` queda como flujo de alto nivel + punteros; el detalle procedimental vive en ficheros de `agent-kits/documenter/` cargados on-demand.
- [x] El comportamiento del agente no cambia (mismo resultado, solo cambia **cuándo** se carga el detalle).
- [x] El cambio es **reversible de forma aislada** (revertir documenter sin afectar a nemesis ni al resto de la iniciativa).
- [x] Queda inline el mínimo de contexto necesario para que el agente sepa **cuándo** cargar cada fichero de fase.

**Subtareas**
- [x] Decidir el criterio de corte por fase (qué queda inline vs. qué se mueve).
- [x] Extraer el detalle a ficheros de `agent-kits/documenter/` y dejar punteros en el `.md`.
- [x] Verificar comportamiento equivalente y contrastar consumo con `/context`.

**Notas**: mayor riesgo funcional de la iniciativa; diseñar el corte para poder revertir solo documenter.

### T-05 — C-03b · Progressive disclosure de nemesis

- **Descripción**: mover el detalle paso-a-paso de las fases largas de `nemesis` (173 líneas) a ficheros de su kit, dejando en el `.md` el flujo de alto nivel + punteros; el detalle se lee cuando el agente entra en la fase. Sin cambiar comportamiento.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,45h · real —
- **Supervisión**: est. 0,11h (≈25 % IA) · real —
- **Previsión IA**: 170k in / 22k out tok · 3,9 €
- **Dependencias**: ninguna dura; comparte criterio de corte con T-04
- **Archivos**: `agents/nemesis.md`, `agent-kits/nemesis/`
- **Cubre (tests)**: — (sin UI; verificación por inspección + contraste cualitativo con `/context`)

**Criterios de aceptación**
- [x] `agents/nemesis.md` queda como flujo de alto nivel + punteros; el detalle procedimental vive en ficheros de `agent-kits/nemesis/` cargados on-demand.
- [x] El comportamiento del agente no cambia (mismo resultado, solo cambia **cuándo** se carga el detalle); no se toca el invariante de seguridad del guardrail.
- [x] El cambio es **reversible de forma aislada** (revertir nemesis sin afectar a documenter).
- [x] Queda inline el mínimo de contexto necesario para que el agente sepa **cuándo** cargar cada fichero de fase.

**Subtareas**
- [x] Aplicar el criterio de corte por fase acordado en T-04 a nemesis.
- [x] Extraer el detalle a ficheros de `agent-kits/nemesis/` y dejar punteros en el `.md`.
- [x] Verificar comportamiento equivalente y que el guardrail sigue intacto.

**Notas**: reversible por separado de T-04; no romper el invariante de pentest local.

### T-06 — C-05a · Mini-skill `rates-verify` (core)

- **Descripción**: crear la skill que hace WebFetch a la doc de precios de la API de Claude, parsea input/output del modelo asumido, valida el rango y **escribe `.claude/rates.json`** de forma idempotente; ante fallo de red/parseo no inventa precio.
- **Estado**: completado
- **Tiempo humano**: est. 2,25h · real —
- **Tiempo IA (ejec.)**: est. 0,55h · real —
- **Supervisión**: est. 0,14h (≈25 % IA) · real —
- **Previsión IA**: 220k in / 28k out tok · 5,0 €
- **Dependencias**: dependencia externa blanda (doc de precios accesible por WebFetch)
- **Archivos**: `skills/rates-verify/SKILL.md`, `.claude/rates.json` (salida)
- **Cubre (tests)**: — (sin UI)

**Reconciliación (revisión de dos lentes, 2026-08-10):** `rates-verify` es una **skill de prosa** que dirige al agente a usar `WebFetch` (herramienta de agente, no invocable desde un script Python autónomo), igual que `confluence-publish`/`discovery`/`jira-sync` — ninguna trae `scripts/` ni test pytest. Por eso **no hay `skills/rates-verify/scripts/` ni test en CI** (los criterios que lo afirmaban se corrigen abajo). La validación de rango del precio, que sí es lógica crítica, se especifica en el `SKILL.md` (paso 4).

**Criterios de aceptación**
- [x] `skills/rates-verify/SKILL.md` dirige el `WebFetch` a la doc de precios y extrae input/output del modelo asumido (skill de prosa, sin script).
- [x] Con doc real, escribe `.claude/rates.json` con precios y `verificadoEl: YYYY-MM-DD`, respetando el esquema de `agent-kits/evaluator/templates/rates.example.json` (`precioTokens.input/output`); escritura **idempotente**.
- [x] Valida el rango del precio antes de escribir; con red caída o parseo fallido **mantiene `⚠️ verificar` sin inventar** y avisa.
- [x] Define qué antigüedad de `verificadoEl` se considera «reciente».

**Subtareas**
- [x] Redactar `SKILL.md` (cuándo se ofrece, entradas/salidas, política ante fallo).
- [x] Especificar en el `SKILL.md` el WebFetch + parseo + validación de rango + escritura idempotente de `rates.json` (instrucciones para el agente; no script).
- [x] Confirmar si la doc es pública o requiere autenticación y adaptar el parseo al formato real.

**Notas**: skill de prosa (no script). El parseo del formato real puede requerir 1-2 iteraciones al ejecutarla la primera vez.

### T-07 — C-05b · Integración de `rates-verify` + test

- **Descripción**: ofrecer `rates-verify` en `/setup` y desde evaluator/planner (dejar de marcar `⚠️ verificar` si `verificadoEl` es reciente). **Nota (reconciliación):** no hay test pytest — al ser skill de prosa con `WebFetch` (herramienta de agente), sus dos caminos no son ejercitables desde CI; se verifican al ejecutar la skill.
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 7k out tok · 1,3 €
- **Dependencias**: T-06
- **Archivos**: `commands/setup.md`, `agent-kits/shared/estimation-defaults.md` (definición de «precio fiable»)
- **Cubre (tests)**: — (sin UI)

**Criterios de aceptación**
- [x] `/setup` ofrece `rates-verify`; evaluator/planner la consumen (vía `estimation-defaults.md`) y dejan de marcar `⚠️ verificar` si `verificadoEl` es reciente (>0 y <90 días).
- [x] **N/A — skill de prosa:** los dos caminos (doc real / red caída) están especificados en el `SKILL.md` (pasos 4 y 6) pero no son testables por pytest (WebFetch es herramienta de agente). Se verifican al ejecutar la skill; el camino "red caída → no inventa" es la regla central del SKILL.
- [x] **N/A — sin test que cablear a CI** (ver arriba).

**Subtareas**
- [x] Añadir el ofrecimiento en `commands/setup.md` y la definición de «precio fiable» en `estimation-defaults.md`.
- [x] Documentar los dos caminos en el `SKILL.md` (no hay test automatizable).

**Notas**: cierra el `⚠️ verificar` del precio de tokens que arrastra toda evaluación (incluida esta).

---

## Fase 3 — Cierre y verificación

**Estado**: completado · **Estimado**: 0h *(absorbido por el margen de contingencia +20 %)* · **Real**: — · **Coste est.**: — · **Tokens est.**: —

### T-08 — Cierre documental, lint y release

- **Descripción**: consolidar el registro de los fragmentos nuevos, actualizar CHANGELOG (y CONVENTIONS/FLOWS si aplica), dejar `lint_plugin.py` y el ledger en verde, y preparar la nota de release. Sin horas base propias: trabajo de cierre cubierto por el margen de contingencia. (rates-verify no aporta test a CI: es skill de prosa — ver T-06/T-07.)
- **Estado**: completado
- **Tiempo humano**: est. 0h *(margen)* · real —
- **Tiempo IA (ejec.)**: est. 0h *(margen)* · real —
- **Supervisión**: est. 0h · real —
- **Previsión IA**: incluida en el margen · 0 €
- **Dependencias**: T-01…T-07
- **Archivos**: `agent-kits/shared/README.md`, `CHANGELOG`, `docs/CONVENTIONS.md`/`docs/FLOWS.md` (si aplica), CI
- **Cubre (tests)**: — (sin UI)

**Criterios de aceptación**
- [x] Los dos fragmentos nuevos están registrados en `agent-kits/shared/README.md` y hay entrada en el CHANGELOG.
- [x] CONVENTIONS/FLOWS revisados: se actualizan solo si el cambio lo exige (no hay agente ni flujo nuevos, previsiblemente n/a — se deja constancia).
- [x] `python scripts/lint_plugin.py` verde y `python3 agent-kits/shared/ledger-lint.py tasks.md` sin incoherencias. (rates-verify no añade test a CI: skill de prosa.)
- [x] Nota de release preparada; el **release lo ejecuta el usuario**.

**Subtareas**
- [x] Consolidar `agent-kits/shared/README.md` + CHANGELOG.
- [x] Revisar CONVENTIONS/FLOWS y dejar constancia (aplica / n/a).
- [x] Correr `lint_plugin.py` + `ledger-lint.py` y cablear el test a CI.
- [x] Redactar la nota de release para el usuario.

**Notas**: el trabajo con entregable (README en C-01/C-04, test/CI en C-05) ya está presupuestado en sus características; esta fase solo consolida y verifica, por eso no lleva horas base y se cubre con el margen (+20 %). Delta sobre lo heredado: **0 h**.

---

## Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._

- Presupuesto **heredado de `evaluation.md`** por característica (C-01…C-05); las tareas reparten esas horas/tokens base sin re-estimar. C-03 se dividió en T-04/T-05 (documenter/nemesis) para hacerlo reversible por agente; C-05 en T-06/T-07 (core/integración+test) para aislar el test.
