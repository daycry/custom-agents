---
spec: plugin-optimization
descripcion: Optimizar el plugin en tres frentes medidos (latencia síncrona de hooks, tokens fijos y bajo demanda, y viabilidad con modelos locales de 9B-32B vía OpenCode/Codex) con un benchmark reproducible antes y después de cada cambio
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-10-27
actualizado: 2026-10-27
evaluacion: evaluation.md
design: n/a
plan: improvement-plan.md
generacion:
  fuente: estimado
  nota: "spec creada por el evaluator dentro de la misma ventana medida que evaluation.md (un solo marcador); su coste va incluido en el bloque generacion: de la evaluación y no se cuenta dos veces"
---

# Optimización del plugin: hooks, tokens y modelos locales

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) · [`tasks.md`](tasks.md)

> **Terminología:**
> - **Espera síncrona:** tiempo que el usuario espera porque un hook bloquea la herramienta o el turno (PreToolUse, PostToolUse sin `async`, SessionStart, UserPromptSubmit, statusline).
> - **Fijo por sesión:** tokens que el runtime inyecta en cada sesión antes de que el usuario pida nada (descriptions de agentes/skills/comandos + índice de SessionStart).
> - **Bajo demanda:** tokens que un comando o agente lee al ejecutarse (p. ej. `commands/dev-cycle.md` entero en la vía rápida).
> - **Rol protegido:** agente cuya identidad nativa activa el guard de PreToolUse (`implementer`, `architect`; `agent-kits/shared/native-guardrail.py` `PROTECTED`, ADR-023).
> - **Tramo de modelo local:** clase 8-9B, 14B y 32B (≥ 64k de contexto) servidos por Ollama a través de OpenCode o Codex.

## Contexto y objetivo

Tres auditorías del 2026-10-27 midieron el coste real del plugin `custom-agents` v2.0.0 en una máquina Windows + OneDrive con 2,8 GB libres (en un equipo sano los arranques de proceso son ~10-15× más baratos; las proporciones se mantienen). El problema que resuelve esta iniciativa:

1. **Rendimiento:** en Windows cada hook encadena `node run-hook.mjs` → `runtime-supervisor.py` (Job Object) → hook, y al salir lanza OTRO Python (`runtime-supervisor.py close`) (`hooks/run-hook.mjs:226-240`, `stop()` en cada `exit`). Resultado medido ≈ 6 min de espera síncrona por sesión de ~200 llamadas a herramientas. La partida mayor es el guard nativo: 2,3 s de mediana en CADA Bash/Edit aunque la sesión principal no sea un rol protegido (la comprobación de identidad está en Python, `native-guardrail.py:256-270`, no en node).
2. **Tokens:** ~10.200 tokens fijos por sesión; 25 de 52 descriptions pasan de 600 caracteres (exceso medido 7.584 caracteres ≈ 2.100 tokens) y en sesiones reales 13 skills aparecen sin descripción porque se desborda el presupuesto del listado, con lo que no se auto-disparan. `commands/dev-cycle.md` pesa 55 KB (~15,4k tokens; la Fase 2 sola ocupa las líneas 74-374) y `quick-implement` lo lee entero. `agent-kits/shared/knowledge-check.md` (9,4k caracteres, de los que ~7k son la «Consulta de la memoria gobernada») lo leen 8 agentes.
3. **Modelos locales:** un modelo de 8-14B no cabe hoy en la vía rápida: `dev-cycle.md` (15k tokens) supera el `num_ctx` por defecto (4-8k) y se trunca en silencio; los formatos exactos en español que vigila `ledger-lint` provocan bucles de reintento; `model-tier.py` rechaza ids que no sean `claude-*` (`MODELOS_ALIAS` + `MODEL_ID_RE`, líneas 43-49) y `export-interop.py` no emite `model` para Codex/OpenCode (solo `model_reasoning_effort`, línea 464), así que todos los roles heredan el modelo de la sesión.

**Objetivo:** reducir la espera síncrona de los hooks, los tokens fijos y bajo demanda, y hacer posible la vía rápida con un modelo local de 32B (los de 8-9B quedan limitados a comandos de lectura), sin debilitar ninguna puerta (identidad exacta del guard, revisión, qa-gate) y midiendo antes y después con un benchmark reproducible.

Fuentes: auditorías del orquestador del 2026-10-27 (hallazgos verificados en el prompt de `/pm-cycle`); scripts de medición de la auditoría (`t.sh`: mediana de N ejecuciones por hook con un payload JSON; `m.py`: tamaño de descriptions y cuerpos), en el scratchpad de la sesión, NO versionados.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Orden de los frentes | **Por tramos: F1 (quick wins medibles) → F2 (reestructuración) → F3 (modelos locales)** | F1 evita procesos innecesarios y publica el ahorro observado, sin prometer un porcentaje mínimo; F2 y F3 tocan contratos y conviene revalidarlos al abrir cada fase (CALIBRATION, project-specialization) |
| Medición | **Benchmark reproducible versionado (C-00) como primera tarea y criterio de aceptación de cada característica de rendimiento/tokens** | Sin línea base medida no se puede aceptar un «más rápido»; los scripts de la auditoría no están en el repo |
| Prefiltro del guard | **Comparación de identidad exacta en node contra `native-roles.json`; si el mapa no se puede leer o validar, se lanza Python como hoy** | Elimina el arranque de Python fuera de rol protegido sin abrir una vía de omisión: la decisión de deny sigue en Python (ADR-023) |
| Descriptions | **Tope de 600 caracteres con aviso del linter a 600 (hoy 1.200), conservando los literales de `evals/cases/`** | `evals/check.py` exige que los literales casen con la description real |
| `dev-cycle.md` | **Núcleo + `references/` por fase bajo demanda (patrón ADR-008)** | Ahorra 6-8k tokens en la vía rápida y es requisito para modelos de contexto corto |
| Modelos locales | **Ids no Claude admitidos por `model-tier.py` y emitidos por `export-interop.py` solo donde el runtime los entiende; formatos de ledger escritos por script (`ledger-write.py`)** | Quita al modelo la carga de escribir formatos exactos y deja de forzar el modelo de sesión |
| Hooks | **Siguen informando y saliendo con exit 0; los timeouts no convierten un fallo en bloqueo** | Constitución §2 y regla de hooks del repo |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Aviso de description larga | `scripts/lint_plugin.py` `DESC_WARN_CHARS` | 1.200 | **600** |
| Timeout de SessionStart | `hooks/hooks.json` `SessionStart[].hooks[].timeout` | sin definir | **definido (valor a fijar con el benchmark; propuesta 15 s)** |
| Rol protegido del guard | `agent-kits/shared/native-roles.json` + `PROTECTED` de `native-guardrail.py` | `implementer`, `architect` | sin cambios |
| Modelo por agente | `.claude/dev.json` `modelos.<agente>.model` | alias Claude o `claude-*` | **también ids de proveedor local (formato a decidir en el plan)** |
| Perfil de ejecución | `.claude/dev.json` `perfil` | no existe | **`lite` (opt-in)** |
| Statusline | `statusline/roadmap-statusline.sh` | 3 llamadas a `python3` | **1 llamada, caché por mtime del ledger** |

## Arquitectura y componentes

- **Reutiliza:** `hooks/run-hook.mjs` (filtros de ruta ya en node), `hooks/runtime-supervisor.py`, `agent-kits/shared/native-guardrail.py`, `progress-report.py`, `ledger-lint.py`, `skill-index.py` (ya con caché), `knowledge-find.py`, `model-tier.py`, `scripts/export-interop.py`, `scripts/lint_plugin.py`, `evals/check.py`, `agent-kits/shared/doctor.py`.
- **Nuevo:** benchmark de hooks y tokens (`scripts/` o `agent-kits/shared/`, con tests), `session-context` en un único proceso Python, hook de ledger fusionado, `ledger-write.py`, perfil `lite`, aviso de contexto corto en `/doctor`.
- **Generado (no se edita a mano):** `interop/`, `.codex-plugin/`, `.agents/plugins/` — se regeneran con `export-interop.py` en cada característica que toque agentes, comandos o hooks.

## Flujo (paso a paso)

1. C-00 fija la línea base (mediana por hook y tokens fijos/bajo demanda) en esta máquina y la deja reproducible.
2. F1: cada característica mide antes/después con el benchmark y documenta la diferencia en el ledger.
3. Cierre de F1: CHANGELOG doble, docs espejo, `export-interop.py --check`, release vía `scripts/release.py`.
4. Antes de abrir F2 y F3: revalidar el plan contra `master` (+0,5 h por fase).
5. F2 y F3 repiten el ciclo medir → cambiar → medir → revisar → release.

## Alcance

- **Dentro (esta iteración):**
  - F1: C-00 benchmark · C-01 descriptions ≤ 600 · C-02 prefiltro del guard en node · C-03 statusline con una llamada Python · C-04 timeout de SessionStart y arranque aislado de la captura de prompts · C-05 temporales sqlite huérfanos.
  - F2: C-06 `session-context` en un único Python · C-07 fusión `ledger-lint-warn` + `progress-line` · C-08 `mark-docs-pending` en node · C-09 `dev-cycle.md` núcleo + fases bajo demanda · C-10 memoria gobernada condicional en `knowledge-check.md`.
  - F2 opcional: C-15 cierre del Job Object sin segundo Python en salida limpia (con spike previo) · C-16 `review-lens-select` con una lectura por fichero · C-17 resolución del kit shared una vez por fichero · C-18 `skill-index` solo con nombres en Claude Code.
  - F3: C-11 ids no Claude en `dev.json` + `model` en interop · C-12 `ledger-write.py` · C-13 perfil `lite` · C-14 aviso de contexto corto en `/doctor` + mínimos por tramo en `docs/INTEROP.md` (+ EN).
- **Fuera (siguientes specs):**
  - Reescribir los hooks en otro lenguaje o sustituir el supervisor de Job Object por un binario nativo.
  - Afinar o entrenar modelos locales; benchmark de calidad de modelos (esto mide viabilidad de contexto y formatos, no calidad).
  - Cambiar los umbrales de la revisión de dos lentes o del qa-gate para los modelos pequeños.
  - Verificar el modelo concreto «Qwen 3.5 9B» (no verificado en la auditoría).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| `native-roles.json` ilegible o inválido en el prefiltro de node | Se lanza Python como hoy y emite su diagnóstico (`role-map-unavailable`); nunca se omite el guard por error de lectura |
| Payload sin `agent_type`/`agent` | Igual que hoy: no es rol protegido → continuar; el prefiltro no lanza Python |
| SessionStart supera el timeout | El runtime corta el hook; el contexto de retoma se pierde en esa sesión, el turno sigue; el benchmark registra el caso |
| Proceso de `knowledge-find.py` matado a mitad de construir el índice | El siguiente arranque limpia los temporales viejos (`*.tmp` y `*.tmp-journal` de PIDs no vivos o con antigüedad) |
| Modelo local con `num_ctx` menor que el mínimo del tramo | `/doctor` lo avisa (⚠️) con el comando que lo arregla; nunca bloquea |
| `ledger-write.py` recibe una tarea inexistente o un formato inválido | Exit distinto de 0 con mensaje; no escribe nada parcial |

## Criterios de aceptación

- [ ] Existe un benchmark reproducible versionado que da la mediana por hook (≥ 10 ejecuciones, payloads fixture) y los tokens fijos por sesión; la línea base de esta máquina queda registrada en la iniciativa.
- [x] [GWT] CA-01 — Dada una sesión principal sin rol protegido, cuando se ejecuta un Bash o un Edit, el hook PreToolUse no arranca ningún proceso Python. La entrega incluye una comparación versionada antes/después, con al menos diez muestras por variante y runtime, calentamiento descartado, control de arranque de Node y declaración de dispersión y fallos. F1 no exige un porcentaje mínimo de reducción de la mediana; informa de la mejora que la medición permita acreditar.

Ajuste aprobado por el usuario el 2026-10-29 («adelante», «adelante con el plan»): véase la [decisión y evidencia](testing/f1-performance-adjustment-proposal.md). El 80 % queda como objetivo de investigación posterior, sujeto a viabilidad y revalidación de alcance y coste; no se atribuye a una tarea existente de F2. La estabilidad de T-01 y las puertas de T-07 se conservan.
- [ ] [GWT] CA-02 — Dado un subagente `implementer` o `architect` con identidad nativa exacta, Cuando intenta una operación prohibida por los guardrails, Entonces el guard la deniega igual que antes (suites de guard en verde sin cambiar expectativas).
- [ ] [GWT] CA-03 — Dado un `native-roles.json` corrupto, Cuando se ejecuta cualquier herramienta vigilada, Entonces se emite el diagnóstico actual y no se pierde la comprobación.
- [ ] Ninguna description de agente, skill o comando pasa de 600 caracteres; `lint_plugin.py` avisa a 600; `evals/check.py` en verde; los tokens fijos bajan al menos ~2.000 frente a la línea base.
- [ ] [GWT] CA-04 — Dado el statusline activado, Cuando se refresca sin cambios en el ledger, Entonces lanza como máximo un proceso Python, sirve desde caché y no usa el alias `python3` de WindowsApps.
- [ ] `hooks/hooks.json` declara timeout en SessionStart; `test_hooks_config.py` lo vigila.
- [ ] [GWT] CA-05 — Dado temporales `knowledge-index.sqlite.<pid>.tmp` (+ `-journal`) de procesos muertos, Cuando se reconstruye el índice, Entonces se eliminan y no se acumulan nuevos tras una muerte forzada.
- [ ] [GWT] CA-06 — Dado un SessionStart, Cuando se ejecuta `session-context`, Entonces lanza un único proceso Python (más el supervisor en Windows) y su salida es idéntica a la actual por runtime.
- [ ] [GWT] CA-07 — Dado un Edit sobre `tasks.md`, Cuando corre el PostToolUse, Entonces el ledger se parsea una sola vez y salen los mismos mensajes que con los dos hooks separados.
- [ ] `quick-implement` y la vía rápida de `/dev-cycle` no cargan las fases que no usan; ahorro medido ≥ 6k tokens; `test_skill_size.py --diet-check` (o equivalente para comandos) con 0 párrafos perdidos; `export-interop.py --check` en verde.
- [ ] La sección de memoria gobernada de `knowledge-check.md` solo se lee cuando el proyecto la tiene activa; ahorro medido por ciclo registrado.
- [ ] [GWT] CA-08 — Dado `dev.json` con un id de modelo local en `modelos.<agente>`, Cuando se resuelve el tier y se exporta interop, Entonces `model-tier.py` lo acepta y los agentes de Codex/OpenCode llevan su `model`.
- [ ] [GWT] CA-09 — Dado una tarea del ledger, Cuando se marca con `ledger-write.py` (estado, evidencia `RED:`, cabecera de revisión), Entonces `ledger-lint` pasa sin avisos y el formato es exactamente el canónico.
- [ ] [GWT] CA-10 — Dado un runtime con un modelo local de contexto menor que el mínimo del tramo, Cuando se ejecuta `/doctor`, Entonces muestra ⚠️ con el arreglo, sin red salvo hosts locales y sin bloquear.
- [ ] Docs espejo ES/EN y los dos CHANGELOG actualizados en cada fase; `interop/` regenerado; release por fase con `scripts/release.py`.

## Pruebas

- Benchmark (C-00) con tests del propio script (parseo de payloads, mediana, salida JSON) y ejecución manual en esta máquina antes/después; se pega la tabla en el ledger.
- Suites existentes que cubren lo tocado: `tests/hook-*.test.mjs`, `tests/test_hook_supervisor.py`, `tests/test_hook_launcher_security.py`, `tests/test_hooks_config.py`, `tests/test_hooks_shell.py`, `agent-kits/shared/test_guardrail_check.py`, `tests/test_export_interop.py`, `tests/test_skill_size.py`, `tests/test_lint_plugin.py`, `evals/check.py`; las 6 suites que citan `dev-cycle.md` y la que cita `knowledge-check.md`.
- Tests nuevos: paridad node/Python del prefiltro (tabla de identidades), statusline con caché, limpieza de temporales, `session-context` monoproceso (salida idéntica por runtime), hook de ledger fusionado, `ledger-write.py`, `model-tier.py` con ids locales, `/doctor` con contexto corto.
- Verificación en Linux (python:3.11-slim, réplica de `ci.yml`) antes de cada push.

## Referencias

- `hooks/run-hook.mjs:60-110` (lista de hooks, emisión del guard) y `:180-330` (supervisor y cierre en Windows).
- `agent-kits/shared/native-guardrail.py:256-300` (`evaluate`: identidad exacta y PROTECTED) y `agent-kits/shared/native-roles.json`.
- `hooks/hooks.json` (SessionStart sin `timeout`; PostToolUse con tres hooks síncronos).
- `hooks/session-context.sh` (315 líneas, 12 invocaciones de `python3`), `statusline/roadmap-statusline.sh:34,72,79`.
- `agent-kits/shared/knowledge-find.py:804-830` (`construir_indice`: temporal por PID; el `-journal` no se borra).
- `agent-kits/shared/model-tier.py:43-49`, `scripts/export-interop.py:464`, `scripts/lint_plugin.py:108,112`.
- `commands/dev-cycle.md` (546 líneas, 55.117 bytes; Fase 2 líneas 74-374), `agent-kits/shared/knowledge-check.md` (9.399 bytes).
- ADR-008 (SKILL.md corto con references), ADR-009 (tiering en dos capas), ADR-023 (guardias por identidad nativa).
- `docs/roadmap/CALIBRATION.md` (ratio vigente 531.798,5 tok/h; retros de panel-redesign y project-specialization).

## Supuestos

- **Hecho técnico:** el guard decide la identidad en Python después de arrancar el supervisor — `agent-kits/shared/native-guardrail.py:267-270`; node lo lanza para todo Bash/Edit — `hooks/run-hook.mjs:194-203`.
- **Hecho técnico:** en Windows, al salir el hijo se lanza un segundo Python `runtime-supervisor.py close` — `hooks/run-hook.mjs:233-240` y `:316`.
- **Hecho técnico:** SessionStart no declara `timeout` — `hooks/hooks.json` bloque `SessionStart`.
- **Hecho técnico:** 25 de 52 descriptions superan 600 caracteres; exceso 7.584 — medido con un script sobre `agents/`, `commands/`, `skills/*/SKILL.md` el 2026-10-27.
- **Hecho técnico:** `construir_indice` borra el `.tmp` en `finally` pero no su `-journal`, y un proceso matado por el Job Object no llega al `finally` — `knowledge-find.py:825-830`; hay 20 parejas huérfanas en `.claude/`.
- **Hecho técnico (de la auditoría, no re-medido aquí):** medianas de 2,3 s (guard), 14-22 s (SessionStart), 9,8 s (statusline), 6-8 s + 6-7,5 s (ledger), 3,6-4,6 s (mark-docs), 2,6 s (captura de prompt), 38 s (`review-lens-select` con 1.081 ficheros).
- **Restricción de negocio (supuesto hasta confirmar):** el objetivo para modelos locales es la vía rápida con 32B y ≥ 64k de contexto; 8-9B solo lectura — la confirmaría el usuario.
- **Restricción de negocio (supuesto hasta confirmar):** el perfil `lite` no puede quitar la revisión ni el qa-gate, solo reducir paralelismo y tamaño de contexto — la confirmaría el usuario.
- **Restricción de negocio (supuesto hasta confirmar):** cada fase se publica en su propia release — la confirmaría el usuario.
