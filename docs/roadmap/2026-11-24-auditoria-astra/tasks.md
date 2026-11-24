---
generacion:
  inicio: 2026-11-24T16:55:00Z
  fin: 2026-11-24T17:25:00Z
  fuente: estimado        # el planner no arrancó usage-meter: estimación a juicio (degradación sin bloqueo)
  tokens_reales: { entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0 }
  eur: null
  horas_ia: 0.5
  duracion: 30m
  ratio_usado: null
  # ventana compartida con improvement-plan.md
tasks: auditoria-astra
estado: borrador
creado: 2026-11-24
verificacion: obligatoria
changelog: Fixed
---

# Checklist de Tareas — Corrección de la auditoría astra (gpt-6.2-astra sobre `78616e2`)

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | 2026-11-24 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | n/a |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Autorización.** Ninguna todavía: el usuario pidió el plan («crea un plan con las correcciones y las tareas detalladas»), no su ejecución. Decisión pendiente del usuario: la de T-13 (opción A o B del plan). Dependencias externas: `plugin-audit-2` T-40 (en curso) bloquea T-02, T-04, T-11 y T-12.

> **Puertas comunes.** *Runtimes* (todo funciona en Claude Code, Codex y OpenCode; la cierra toda tarea que toque un agente, comando, skill, hook, el instalador o un manifiesto): `python scripts/export-interop.py --check` → exit 0 · `pytest -q tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py` → verde · `node --test tests/opencode-plugin.test.mjs tests/codex-native-install.test.mjs tests/installer.test.mjs tests/hook-runtime.test.mjs` → verde. *Tokens* (toda tarea sobre `agents/`, `commands/` o `skills/`): `pytest -q tests/test_context_footprint.py tests/test_source_snapshot.py` → verde (vía rápida ≥ 6.000; `agents/evaluator.md` ≤ 15.513 bytes en LF; `--diet-check` sin párrafos perdidos) y `docs/TOKEN-EFFICIENCY.md` + `docs/en/TOKEN-EFFICIENCY.md` al día si cambia una cifra. *Bilingüe*: todo doc con espejo en `docs/en/` (README, INSTALL, CONVENTIONS, FLOWS, observability) y los `CHANGELOG*.md` se actualizan juntos. *TDD*: cada tarea escribe primero el test RED (falla por la razón correcta; se anota `RED:` en el ledger) y después el GREEN; los tests NO leen ledgers reales de iniciativas (ver T-12). *Windows*: el entorno local es Windows; lo que solo se puede comprobar en POSIX (permisos `0600`, `umask`, `python3` sin `x`) se prueba con la imagen `python:3.11-slim` (CRLF normalizado con `git -c core.autocrlf=false archive`) antes del push. *Implementación*: Codex `gpt-6.2-sol` (esfuerzo alto) implementa y Claude Opus 5.5 (esfuerzo alto) revisa con `adversarial-review`.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Puertas que aprueban lo que no deben | 0 | 2 | 0% | 0 / 11h | 0 / 2.8h | 0 / 0.7h | 0 / 1260k |
| Fase 2 — Pérdida de datos y robustez | 0 | 3 | 0% | 0 / 20h | 0 / 4.9h | 0 / 1.22h | 0 / 2080k |
| Fase 3 — Alcance y publicación | 0 | 2 | 0% | 0 / 11h | 0 / 2.6h | 0 / 0.65h | 0 / 1090k |
| Fase 4 — Rendimiento de la consola | 0 | 1 | 0% | 0 / 7h | 0 / 1.8h | 0 / 0.45h | 0 / 750k |
| Fase 5 — Resto de Minor y deuda de pruebas | 0 | 6 | 0% | 0 / 56h | 0 / 13.8h | 0 / 3.45h | 0 / 5360k |
| **TOTAL** | **0** | **14** | **0%** | **0 / 105h** | **0 / 25.9h** | **0 / 6.47h** | **0 / 10540k** |

> Estimaciones BASE (el +20 % de contingencia está en el plan); horas IA y tokens son estimaciones aproximadas, a juicio del planner; tokens al precio de `.claude/rates.json` (Claude Opus 5.5; el precio de `gpt-6.2-sol` es ⚠️ verificar). Supervisión = 25 % de las horas IA.

---

## Fase 1 — Puertas que aprueban lo que no deben

**Estado**: borrador · **Estimado**: 11h · **Real**: — · **Coste est.**: 557.0 € · **Tokens est.**: 1260k

### T-01 — qa-gate: un verde que contradice sus propios resultados (hallazgos 1 y 6)

- **Descripción**: `agent-kits/qa/qa-gate.py` confía en `stats` aunque contradiga los `results[].status` individuales (un test `failed` con resumen de un aprobado da `VERDE`, exit 0), y una justificación de flaky cubre varias ejecuciones distintas del mismo `fichero::título` (móvil y escritorio). La auditoría los dio como Critical; la verificación los reajusta a Important (el informe de entrada lo genera Playwright, no un tercero).
- **Changelog**: La puerta de QA ya no da verde cuando un test individual falló o cuando una justificación de flaky es ambigua entre proyectos.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1.0h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 400k in / 60k out tok · 2.58 €
- **Dependencias**: ninguna
- **Tipo**: test
- **Archivos**: `agent-kits/qa/qa-gate.py`, `tests/test_qa_gate.py`, `agent-kits/qa/README.md`, `docs/agents/qa.md`
- **Runtimes**: Sin diferencia: `qa-gate.py` es un script de kit que llaman igual los tres runtimes; no toca `agents/` ni `commands/`, así que no hay regeneración de `interop/`.
- **Verificación**:
  - `python -m pytest -q tests/test_qa_gate.py -k "stats_incoherente or flaky_ambiguo or recuentos_por_test"` → `passed` (rojo antes del arreglo: el informe con un `failed` y `stats` de un aprobado devuelve VERDE)
  - `python -m pytest -q tests/test_qa_gate.py` → sin regresiones (un informe coherente sigue en VERDE)
  - `python agent-kits/qa/qa-gate.py --help` → exit 0

**Criterios de aceptación**

- [ ] Los recuentos se calculan siempre desde `results[]`; si contradicen `stats` el veredicto es NO-VERDE con el motivo «stats incoherente» y el exit de NO-VERDE.
- [ ] `stats` ausente, con tipos no numéricos o negativos se rechaza con diagnóstico, no con `TypeError`.
- [ ] La identidad de un test para flaky incluye `projectName` y la ruta de describes (`fichero::describes::título::projectName`).
- [ ] Una justificación que casa con más de una ejecución distinta se rechaza como ambigua; una justificación por proyecto sigue valiendo.
- [ ] Un informe coherente y sin flaky conserva VERDE (tests existentes intactos).

**Subtareas**

- [ ] RED: fixture del informe `failed` + `stats` de un aprobado (reproducido por la auditoría: `qa-gate.py:115-122`)
- [ ] RED: móvil y escritorio con el mismo `fichero::título`, justificación solo para móvil (`qa-gate.py:39,139-143`)
- [ ] Recuentos desde `results[]` y validación de tipos
- [ ] Identidad ampliada y rechazo de ambigüedad
- [ ] Actualizar `docs/agents/qa.md` y el README del kit

**Notas**: Grado reajustado: Important (auditoría: Critical para #1). Agrupa #1+#6 por compartir fichero y fixtures.

### T-02 — ledger-write: verdict limpio sin evidencia de las lentes y `Cerrada` obsoleta (hallazgos 2 y 18)

- **Descripción**: `ledger-write.py verdict`/`prepare` cierra una revisión como limpia con solo las casillas marcadas: acepta una sección de revisión vacía («sin veredicto») y `test_ledger_write_transitions.py:74-87` incluso espera ese cierre. Hay que exigir la tabla de criterios ✓/✗ de la Lente A y las lentes que corrieron (A y B como mínimo) antes de pasar las tareas a `completado`, y alinear `adversarial-review` §6. Además una tarea reabierta conserva la `Cerrada` de su primer cierre: la fecha debe ser la del cierre vigente.
- **Changelog**: Una revisión sin resultados de las lentes ya no cierra tareas, y la fecha de cierre refleja el último cierre.
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real —
- **Tiempo IA (ejec.)**: est. 1.8h · real —
- **Supervisión**: est. 0.45h (≈25 % IA) · real —
- **Previsión IA**: 700k in / 100k out tok · 4.42 €
- **Dependencias**: plugin-audit-2 T-40 (cierra los cambios en curso de `ledger-write.py`, `ledger-lint.py` y `task-brief.py`)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-write.md`, `agent-kits/shared/test_ledger_write_transitions.py` (líneas 74-87), `agent-kits/shared/ledger-lint.py`, `skills/adversarial-review/SKILL.md` (§6), `skills/adversarial-review/references/`, `agents/implementer.md` (línea 102), `docs/agents/implementer.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**` (regenerado: `agents/` tocados)
- **Runtimes**: Sin diferencia en el script (lo llaman los tres runtimes). La prosa de `agents/implementer.md` y la skill viajan a Codex/OpenCode vía `export-interop.py`; regenerar `interop/` y pasar las puertas de runtimes y de tokens.
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_ledger_write_transitions.py -k "verdict_sin_lentes or reabierta_actualiza_cerrada"` → `passed` (rojo antes: `prepare` con la sección «sin veredicto» devuelve las dos tareas `completado`)
  - `python -m pytest -q -n 3 agent-kits/shared/test_ledger_write_transitions.py agent-kits/shared/test_ledger_lint.py` → sin regresiones
  - `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-11-24-auditoria-astra/tasks.md` → exit 0
  - puertas de runtimes y de tokens (cabecera) → verde

**Criterios de aceptación**

- [ ] `verdict` limpio rechaza (exit ≠ 0, motivo explícito) una sección de revisión sin tabla de criterios ✓/✗ y sin resultado de las lentes aplicables (A+B mínimo; C/D si `review-lens-select` las marcó).
- [ ] El test de `test_ledger_write_transitions.py:74-87` deja de esperar el cierre sin evidencia y pasa a esperar el rechazo; existe una regresión de «revisión vacía».
- [ ] El cierre con evidencia completa sigue pasando a `completado` (flujo feliz intacto).
- [ ] `Cerrada` es la fecha del cierre vigente: se retira al reabrir y se escribe en la transición final; los cierres anteriores quedan en el registro de revisiones del ledger, no se borran.
- [ ] `adversarial-review` §6 y `agents/implementer.md:102` describen la misma regla (fuente única, sin duplicar texto largo).

**Subtareas**

- [ ] Esperar a que T-40 cierre y rebasar sobre su estado de `ledger-write.py`
- [ ] RED: revisión vacía y reapertura con `Cerrada` antigua
- [ ] Validación de evidencia en `verdict`/`prepare`
- [ ] Fecha de cierre vigente en la transición final
- [ ] Reescribir el test de las líneas 74-87
- [ ] Alinear skill, implementer y docs; regenerar `interop/`

**Notas**: Grado reajustado: #2 Important (auditoría: Critical), #18 Minor. Es la puerta que más importa de la fase 1: el cierre no puede apoyarse solo en casillas.

---

## Fase 2 — Pérdida de datos y robustez

**Estado**: borrador · **Estimado**: 20h · **Real**: — · **Coste est.**: 1011.77 € · **Tokens est.**: 2080k

### T-03 — Instalador: escritura atómica sin pérdida de datos y desinstalación de OpenCode (hallazgos 3, 10, 11 y 12)

- **Descripción**: `escribirAtomico` de `install/install.mjs` cae a escritura directa si fallan tres sustituciones en Windows (puede truncar `settings.json` y avisa después de escribir), no comprueba que la configuración no cambió entre leer y publicar (puede restaurar contenido anterior a la edición del usuario) y crea el temporal con permisos amplios en POSIX (el modo original se aplica tras el rename y un fallo de `chmod` se silencia). Además `uninstall` de OpenCode deja en `plugins` la ruta del adaptador retirado.
- **Changelog**: El instalador ya no puede dejar una configuración truncada, pisar una edición concurrente ni ampliar permisos, y al desinstalar OpenCode retira su propia entrada.
- **Estado**: borrador
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 2.5h · real —
- **Supervisión**: est. 0.62h (≈25 % IA) · real —
- **Previsión IA**: 900k in / 140k out tok · 5.89 €
- **Dependencias**: ninguna
- **Tipo**: devops
- **Archivos**: `install/install.mjs` (líneas 237-263, 2101-2122, 2293), `install/providers.mjs` (líneas 549-569), `tests/installer.test.mjs` (línea ~1011), `tests/codex-native-install.test.mjs`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/INTEROP.md`
- **Runtimes**: El instalador es multi-proveedor: Claude Code, Codex y OpenCode pasan por `escribirAtomico`; la entrada del adaptador (#12) es solo de OpenCode y se prueba además con Codex y Claude para confirmar que no se tocan. No cambia `agents/`/`commands/`/`skills/`/`hooks/`, pero se corren las puertas de runtimes (incluye `installer.test.mjs`).
- **Verificación**:
  - `node --test --test-name-pattern="escrituraDirecta|conflicto de edicion|temporal 0600|desinstala plugins" tests/installer.test.mjs` → pasan (rojo antes de cada arreglo)
  - `node --test tests/installer.test.mjs tests/codex-native-install.test.mjs` → verde
  - en Linux (`python:3.11-slim` con Node) y `umask 022`: `node --test --test-name-pattern="temporal 0600" tests/installer.test.mjs` → pasa (el caso se salta en win32 con motivo explícito)
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**

- [ ] Si fallan los reemplazos atómicos NO se escribe in situ sobre la configuración del usuario: se conserva el original, se crea un `.bak` o se informa del bloqueo con opción de reintentar, y el aviso se emite antes de cualquier escritura.
- [ ] Antes de publicar una fusión se revalida la identidad de la versión leída (tamaño/mtime/hash); si cambió, se repite la fusión o se devuelve conflicto sin pisar la edición.
- [ ] El temporal nace `0600` (`openSync` con `wx` + `fchmod`) y se comprueba antes del rename; un fallo de `chmod` avisa, no se silencia.
- [ ] El instalador registra como `json-set` con `scopedEntries` la entrada exacta que añade a `plugins` de OpenCode; `uninstall` la retira si sigue intacta y conserva las demás entradas del usuario; se actualiza el test de `installer.test.mjs:~1011`.
- [ ] `docs/INSTALL.md` y su espejo EN describen el comportamiento ante bloqueo y la desinstalación.

**Subtareas**

- [ ] RED: escritura directa tras tres fallos (#3) y aviso ordenado
- [ ] RED: edición concurrente entre lectura y publicación (#10)
- [ ] RED: temporal con `umask 022` sobre un fichero `0600` (#11, POSIX)
- [ ] RED: `uninstall` deja la ruta en `plugins` (#12)
- [ ] Implementar `escribirAtomico` seguro y guardia de identidad
- [ ] Registro `scopedEntries` y retirada en `providers.mjs`
- [ ] Docs ES/EN

**Notas**: Grados reajustados: #3 Important, #10-#12 Minor. Agrupa los cuatro por vivir en `escribirAtomico` y el manifiesto de desinstalación. Tarea grande: si el revisor lo pide, #12 se separa.

### T-04 — jira-sync: idempotencia de la creación tras un timeout (hallazgo 5)

- **Descripción**: Si Jira crea el issue de `T-01` pero se pierde la respuesta antes de guardar `issueKey` en el manifiesto, al reanudar el procedimiento vuelve a crearlo. Hay que persistir la intención antes del envío con una identidad buscable (label + resumen) y reconciliar por JQL antes de repetir el alta.
- **Changelog**: Reanudar tras un corte ya no duplica issues en Jira: se reconcilian las altas inciertas antes de crear.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Supervisión**: est. 0.3h (≈25 % IA) · real —
- **Previsión IA**: 450k in / 70k out tok · 2.94 €
- **Dependencias**: plugin-audit-2 T-40 (toca `jira-flow.py`)
- **Tipo**: backend
- **Archivos**: `skills/jira-sync/SKILL.md`, `skills/jira-sync/references/create-and-writeback.md`, `skills/jira-sync/scripts/jira-flow.py`, `skills/jira-sync/scripts/test_jira_flow.py`, `tests/test_audit_jira.py`, `docs/CUSTOMIZATION.md`
- **Runtimes**: `jira-flow.py` y la skill son idénticos en los tres runtimes (los conectores los pone cada runtime; el script no llama a red). Skill tocada: puertas de runtimes y de tokens.
- **Verificación**:
  - `python -m pytest -q skills/jira-sync/scripts/test_jira_flow.py -k "intencion_pendiente or reconciliar_alta"` → `passed` (rojo antes: un manifiesto con alta incierta genera un segundo `create`)
  - `python -m pytest -q skills/jira-sync/scripts/test_jira_flow.py tests/test_audit_jira.py` → sin regresiones
  - puertas de runtimes y de tokens (cabecera) → verde

**Criterios de aceptación**

- [ ] Antes de cada alta el manifiesto registra una intención pendiente con una identidad buscable (label + resumen estable).
- [ ] Una tarea con intención pendiente y sin `issueKey` se reconcilia por JQL (label + resumen) antes de crear; si existe, se adopta la clave; si hay varias, se pide decisión.
- [ ] El flujo sin interrupciones no cambia (idempotencia ya existente intacta) y sigue siendo opt-in de `.claude/jira.json`.
- [ ] `SKILL.md` se mantiene ≤ 200 líneas; el detalle vive en `references/`.

**Subtareas**

- [ ] RED: manifiesto con intención pendiente y sin clave
- [ ] Campo de intención y label en `jira-flow.py`
- [ ] Procedimiento de reconciliación en `create-and-writeback.md`
- [ ] Pruebas con respuesta perdida simulada

**Notas**: Grado reajustado: Minor (auditoría: Important). Depende de T-40 solo por tocar el mismo `jira-flow.py`.

### T-05 — knowledge-sync y outbox: identidad única por publicación (hallazgo 8)

- **Descripción**: Dos procesos del mismo backend pueden generar la clave `sync-<ms>` en el mismo milisegundo, uno reclama el sobre del otro y aplica sus propias `ops` en memoria, dejando el recibo asociado al lote equivocado. Clave con pid y uuid, publicación del sobre con creación exclusiva y aplicación de las `ops` del sobre realmente reclamado.
- **Changelog**: Dos publicaciones simultáneas de conocimiento al mismo backend ya no se cruzan ni asocian el recibo al lote equivocado.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Supervisión**: est. 0.3h (≈25 % IA) · real —
- **Previsión IA**: 450k in / 70k out tok · 2.94 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/knowledge-sync.py` (líneas 532-556), `agent-kits/shared/outbox.py` (línea 383), `skills/knowledge-services/scripts/test_knowledge_sync.py`, `skills/knowledge-services/scripts/test_knowledge_sync_replay.py`, `agent-kits/shared/test_outbox.py`, `skills/knowledge-services/SKILL.md`
- **Runtimes**: Scripts de kit sin dependencia de runtime. La skill `knowledge-services` solo si cambia prosa: entonces puertas de tokens y runtimes.
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_outbox.py skills/knowledge-services/scripts/test_knowledge_sync.py -k "clave_unica or creacion_exclusiva or ops_del_sobre"` → `passed` (rojo antes: dos claves iguales en el mismo milisegundo reclaman el mismo sobre)
  - `python -m pytest -q skills/knowledge-services/scripts agent-kits/shared/test_outbox.py` → sin regresiones

**Criterios de aceptación**

- [ ] La clave de sync es `sync-<ms>-<pid>-<uuid8>` y no colisiona aunque dos procesos arranquen en el mismo instante (test con reloj fijo).
- [ ] El sobre se publica con creación exclusiva; una colisión reintenta o falla de forma explícita, nunca sobrescribe.
- [ ] Las `ops` que se aplican son las del sobre efectivamente reclamado, y el recibo corresponde a ese lote.
- [ ] El replay y la dead-letter existentes siguen en verde.

**Subtareas**

- [ ] RED: reloj fijo y dos publicaciones concurrentes
- [ ] Clave nueva y creación exclusiva en `outbox.py`
- [ ] Aplicar el contenido reclamado en `knowledge-sync.py`

**Notas**: Grado reajustado: Minor (auditoría: Important).

---

## Fase 3 — Alcance y publicación

**Estado**: borrador · **Estimado**: 11h · **Real**: — · **Coste est.**: 556.07 € · **Tokens est.**: 1090k

### T-06 — scope-check: renombrados, rutas con espacios y presupuesto de llaves (hallazgos 7, 14 y 17)

- **Descripción**: `scope-check.py` descarta la ruta de origen de un renombrado (mover un fichero de una carpeta no declarada a una permitida pasa como en alcance, también con renombrados ya comiteados), no admite espacios en rutas entre acentos graves (`docs/User Guide.md` queda fuera de alcance) y expande las llaves del campo `Archivos` sin límite (20 grupos de 2 alternativas son 1.048.576 patrones).
- **Changelog**: La puerta de alcance ya no deja pasar renombrados desde fuera del alcance, acepta rutas con espacios y rechaza expansiones de llaves desproporcionadas.
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real —
- **Tiempo IA (ejec.)**: est. 1.6h · real —
- **Supervisión**: est. 0.4h (≈25 % IA) · real —
- **Previsión IA**: 600k in / 90k out tok · 3.86 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/scope-check.py` (líneas 301-348, 867, 910), `agent-kits/shared/test_scope_check.py`, `agent-kits/shared/test_scope_check_commit_selection.py`, `agent-kits/shared/test_scope_check_commit_selection_deep.py`, `agent-kits/qa/coverage-check.py` (consume los helpers de git, arista E12 de `docs/agents/CONTRACTS.md`), `docs/COMMIT-SELECTION.md`, `docs/agents/planner.md`, `docs/agents/implementer.md`
- **Runtimes**: Script de kit idéntico en los tres runtimes; `coverage-check.py` lo reutiliza, se comprueba que no se rompe la arista E12. No toca agentes ni comandos.
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_scope_check.py -k "renombrado_origen or ruta_con_espacios or presupuesto_llaves"` → `passed` (rojo antes de cada arreglo)
  - `python -m pytest -q -n 3 agent-kits/shared/test_scope_check.py agent-kits/shared/test_scope_check_commit_selection.py agent-kits/shared/test_scope_check_commit_selection_deep.py` → sin regresiones
  - `python -m pytest -q tests/test_qa_gate.py` → sin regresiones de la arista con `coverage-check.py`

**Criterios de aceptación**

- [ ] `git diff` y `git status` se invocan con `--no-renames` (o se clasifican ambos extremos), incluidos los renombrados comiteados; un movimiento desde una ruta no declarada sale como fuera de alcance.
- [ ] Una ruta con espacios entre acentos graves en `Archivos` se declara y compara exacta con el nombre que devuelve Git.
- [ ] Una entrada cuyo producto de llaves supera 1024 patrones termina con exit 2 y nombra la entrada que lo superó; antes de expandir se calcula el tamaño.
- [ ] El JSON de 15 claves de `scope-check` (contrato E6) no cambia.

**Subtareas**

- [ ] RED: renombrado cuyo origen está fuera de alcance
- [ ] RED: `docs/User Guide.md` declarado
- [ ] RED: 20 grupos de 2 alternativas
- [ ] `--no-renames` y clasificación de ambos extremos
- [ ] Parser de rutas con espacios
- [ ] Presupuesto de expansión y mensaje

**Notas**: Grados reajustados: #7 Important (CONFIRMADO+, afecta también a renombrados comiteados), #14 y #17 Minor.

### T-07 — Publicación: verificador obligatorio ausente y exports enlazados (hallazgos 13 y 22)

- **Descripción**: `scripts/release.py` omite sin fallo un verificador requerido ausente (p. ej. `export-interop.py`) y puede etiquetar con exports antiguos; `export-interop.py --check` declara al día un destino enlazado que el escritor rechaza. Ambos deben aplicar la misma regla estricta.
- **Changelog**: Una release ya no se publica si falta un verificador obligatorio y la comprobación de exports rechaza enlaces como lo hace el escritor.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1.0h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 350k in / 50k out tok · 2.21 €
- **Dependencias**: ninguna
- **Tipo**: devops
- **Archivos**: `scripts/release.py` (líneas 310-315, 528), `scripts/export-interop.py` (líneas 895-979, `_regular_export_path`), `tests/test_release.py`, `tests/test_export_interop.py`, `docs/INTEROP.md`, `docs/en/INTEROP.md`
- **Runtimes**: `export-interop.py` es el generador de los dos runtimes no nativos: se verifica que `interop/` regenerado queda idéntico (`--check`) y que la regla endurecida no rompe los árboles de Codex y OpenCode.
- **Verificación**:
  - `python -m pytest -q tests/test_release.py tests/test_export_interop.py -k "verificador_ausente or destino_enlazado"` → `passed` (rojo antes: `run_checks` omite el verificador; `--check` acepta el enlace)
  - `python -m pytest -q tests/test_release.py tests/test_export_interop.py` → sin regresiones
  - `python scripts/export-interop.py --check` → exit 0 · `python scripts/release.py --dry-run` → sin error nuevo

**Criterios de aceptación**

- [ ] En el repositorio del plugin, un verificador obligatorio ausente cuenta como fallo de `run_checks` con su nombre en el mensaje.
- [ ] `--check` aplica `_regular_export_path` (tipo, enlaces y ancestros) igual que la escritura; un export enlazado ya no se declara al día.
- [ ] `interop/` no cambia de contenido por esta tarea.

**Subtareas**

- [ ] RED: simular la ausencia de `export-interop.py` y un export como symlink
- [ ] Fallo por verificador ausente
- [ ] Reusar `_regular_export_path` en `--check`
- [ ] Nota en `docs/INTEROP.md` (+ EN)

**Notas**: Grado reajustado: ambos Minor. Un test con symlink se salta con motivo en Windows sin privilegios; confirmar en Linux.

---

## Fase 4 — Rendimiento de la consola

**Estado**: borrador · **Estimado**: 7h · **Real**: — · **Coste est.**: 354.23 € · **Tokens est.**: 750k

### T-08 — Consola: no releer ni reproyectar el ledger en cada sondeo (hallazgo 15)

- **Descripción**: La vista de detalle de la consola sondea cada 2 s y cada respuesta vuelve a leer y proyectar el ledger completo (167-296 ms; 8-15 % de un núcleo por pestaña, con 200 KiB). Hay que cachear plan y tarea por firma del ledger (como ya hace `serve_panel.py:876`) y responder a los sondeos sin cambios con una validación barata.
- **Changelog**: La consola deja de releer el ledger entero en cada sondeo y consume mucha menos CPU con varias pestañas abiertas.
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real —
- **Tiempo IA (ejec.)**: est. 1.8h · real —
- **Supervisión**: est. 0.45h (≈25 % IA) · real —
- **Previsión IA**: 650k in / 100k out tok · 4.23 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/console_service.py` (línea 44), `skills/plugin-panel/scripts/panel_data.py` (línea 445), `skills/plugin-panel/assets/control-center.js` (línea 327), `skills/plugin-panel/assets/console-plans.js` (línea 121), `tests/test_panel_console_perf.py`, `tests/test_console_service.py`, `tests/test_panel_large_roadmaps.py`, `docs/PLUGIN-PANEL.md`
- **Runtimes**: La consola es común y local; el origen de datos son ledgers y sesiones de los tres runtimes. El cambio no toca la lectura por runtime. Si cambia el `SKILL.md` de `plugin-panel`, puertas de tokens.
- **Verificación**:
  - `python -m pytest -q tests/test_panel_console_perf.py -k "cache_por_firma or sondeo_sin_cambios"` → `passed` (rojo antes: dos sondeos seguidos leen y proyectan dos veces)
  - `python -m pytest -q tests/test_console_service.py tests/test_panel_large_roadmaps.py tests/test_panel_plan_ui.py` → sin regresiones
  - `node --test tests/console-live.test.mjs` → verde

**Criterios de aceptación**

- [ ] Con el ledger sin cambios, un segundo sondeo no vuelve a leer ni proyectar (contador de lecturas = 1) y responde con una validación por firma.
- [ ] Un cambio del ledger invalida la caché y el sondeo siguiente devuelve el contenido nuevo (sin datos obsoletos).
- [ ] La caché está acotada (entradas y bytes) y no incluye rutas absolutas ni contenido sin redactar.
- [ ] Hay una medición reproducible antes/después con el ledger grande de prueba (`test_panel_large_roadmaps.py`); no se afirman cifras sin medirlas.

**Subtareas**

- [ ] RED: contador de lecturas y proyecciones por sondeo
- [ ] Caché por `firma_ledger` en `console_service.py`
- [ ] Validación barata de sondeo sin cambios en el cliente y el servicio
- [ ] Medición antes/después

**Notas**: Grado reajustado: Important. Único hallazgo de rendimiento vivo (#16 está descartado; su residuo lo cubre `plugin-audit-2` T-40).

---

## Fase 5 — Resto de Minor y deuda de pruebas

**Estado**: borrador · **Estimado**: 24h · **Real**: — · **Coste est.**: 1213.81 € · **Tokens est.**: 2510k

### T-09 — Hooks: validación de grupos en el linter y lanzador con Python no ejecutable (hallazgos 19 y 20)

- **Descripción**: `lint_plugin.py` acepta grupos de hooks inertes (`hooks: {}`) y lanza `TypeError` ante `hooks: null`; `hooks/run-hook.mjs` elige el primer `python3` del `PATH` aunque no sea ejecutable y eclipsa a un intérprete válido posterior.
- **Changelog**: El linter da un error claro ante grupos de hooks inválidos y el lanzador de hooks salta un Python no ejecutable.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1.0h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 350k in / 50k out tok · 2.21 €
- **Dependencias**: ninguna
- **Tipo**: hooks
- **Archivos**: `scripts/lint_plugin.py` (líneas 1585-1587), `tests/test_lint_plugin.py`, `hooks/run-hook.mjs` (líneas 258-268), `tests/hook-runtime.test.mjs`, `docs/observability.md`, `docs/en/observability.md`, `docs/agents/CONTRACTS.md` (fila del lanzador), `interop/**` (regenerado: `hooks/` tocados)
- **Runtimes**: `run-hook.mjs` lo usan los tres runtimes (Claude, Codex y el adaptador JS de OpenCode): se prueba con `--runtime` de cada uno y se regenera `interop/`. El caso de `python3` sin `x` solo es probable en POSIX (Linux).
- **Verificación**:
  - `python -m pytest -q tests/test_lint_plugin.py -k "grupo_hooks_invalido"` → `passed` (rojo antes: `hooks: {}` sin error y `hooks: null` con `TypeError`)
  - `node --test --test-name-pattern="python no ejecutable" tests/hook-runtime.test.mjs` → pasa en Linux (rojo antes: elige el `python3` sin `x`)
  - `python scripts/lint_plugin.py` → sin errores nuevos · puertas de runtimes (cabecera) → verde

**Criterios de aceptación**

- [ ] Un grupo cuyo `hooks` no es una lista no vacía de handlers produce un error con el evento afectado, nunca un `TypeError`.
- [ ] El lanzador descarta candidatos que no sean fichero regular con permiso de ejecución y prueba el siguiente ante un fallo de arranque.
- [ ] Los hooks siguen informando y terminando en exit 0 (invariante de `CLAUDE.md`); sin Python válido degradan en silencio.

**Subtareas**

- [ ] RED del linter con `{}`, `null` y lista vacía
- [ ] RED del lanzador con un `python3` sin `x` primero en `PATH`
- [ ] Validación de tipos y mensaje
- [ ] Selección de intérprete con reintento
- [ ] Regenerar `interop/` y docs

**Notas**: Ambos Minor. Probar #20 en Linux (verificar en `python:3.11-slim` antes de push).

### T-10 — Resolución de kits: un único preámbulo que respete `SHAREDKIT` (hallazgo 21)

- **Descripción**: `quick-implement` propaga `SHAREDKIT` al subagente pero su propia receta de resolución lo omite: con el bundle en un directorio personalizado y sin `CLAUDE_PLUGIN_ROOT` declara instalación parcial y detiene el ciclo. El problema es sistémico: hay que fijar un preámbulo único de resolución `CLAUDE_PLUGIN_ROOT` → `SHAREDKIT` → `find` en las raíces y aplicarlo a todas las recetas afectadas (`quick-implement`, `adversarial-review`, `tdd`, `dev-cycle` y trece más), con un test que lo vigile.
- **Changelog**: Las recetas del plugin resuelven sus kits desde `SHAREDKIT` cuando está definido, sin declarar una instalación parcial.
- **Estado**: borrador
- **Tiempo humano**: est. 8h · real —
- **Tiempo IA (ejec.)**: est. 2.0h · real —
- **Supervisión**: est. 0.5h (≈25 % IA) · real —
- **Previsión IA**: 800k in / 110k out tok · 4.97 €
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `skills/quick-implement/SKILL.md`, `skills/adversarial-review/SKILL.md`, `skills/tdd/SKILL.md`, `commands/dev-cycle.md`, `agent-kits/shared/kit-resolution.md` (nuevo, fuente única del preámbulo), las 13 recetas restantes que enumerará el test, `tests/test_plugin_root_resolution.py`, `docs/CONVENTIONS.md` (regla 5), `docs/en/CONVENTIONS.md`, `docs/agents/CONTRACTS.md`, `evals/cases/`, `interop/**` (regenerado: `commands/` tocados)
- **Runtimes**: Tarea transversal a los tres runtimes: el orden `CLAUDE_PLUGIN_ROOT` → `SHAREDKIT` → `find` en las seis raíces (`.claude`/`.codex`/`.opencode`, proyecto y usuario) debe valer en cada uno; `test_plugin_root_resolution.py` se amplía con un caso por runtime. Regenerar `interop/` y pasar las puertas de tokens: la fuente única evita crecer el texto repetido.
- **Verificación**:
  - `python -m pytest -q tests/test_plugin_root_resolution.py -k "sharedkit_antes_de_find"` → `passed` (rojo antes: la receta de `quick-implement` sin `CLAUDE_PLUGIN_ROOT` ni raíces convencionales falla)
  - `python -m pytest -q tests/test_plugin_root_resolution.py tests/test_export_interop.py` → verde
  - puertas de runtimes y de tokens (cabecera) → verde: la vía rápida no pierde su margen ≥ 6.000 y `--diet-check` sin párrafos perdidos

**Criterios de aceptación**

- [ ] Existe una fuente única del preámbulo; cada receta la referencia con una línea, no la copia entera.
- [ ] Con `SHAREDKIT` válido y sin `CLAUDE_PLUGIN_ROOT` ni copia en las raíces, las recetas resuelven el comando desde el kit inyectado.
- [ ] El test enumera las recetas afectadas y falla si una receta nueva resuelve sin el preámbulo.
- [ ] Los tres runtimes conservan sus raíces; el tamaño de las piezas tocadas no aumenta de forma neta (medido con `context-footprint.py`: tamaño de fichero, no consumo facturado).

**Subtareas**

- [ ] RED: el caso `SHAREDKIT`-solo para `quick-implement`
- [ ] Redactar `agent-kits/shared/kit-resolution.md`
- [ ] Inventario de las 17 recetas y sustitución mínima
- [ ] Ampliar el test y los casos de `evals/`
- [ ] Regenerar `interop/` y medir tokens

**Notas**: Grado reajustado: Minor (sistémico). La tarea más amplia en ficheros de la fase 5: si el revisor lo pide, se parte por skills / comandos.

### T-11 — usage-meter: atribución de tokens por sesión en tareas simultáneas (hallazgo 9)

- **Descripción**: Dos sesiones sobre tareas distintas del mismo checkout comparten ventana en `usage-meter.py` y ambas se imputan los eventos de las dos, publicándose como `medido`. Con `CODEX_THREAD_ID` debe contar solo esa sesión (y sus subagentes); si hay varias sesiones sin identidad, atribuir por proyecto y marcar la cobertura como parcial, también para OpenCode. El residuo de sesiones antiguas reanudadas (#16) lo corrige `plugin-audit-2` T-40, no esta tarea.
- **Changelog**: La medición de tokens ya no atribuye a una tarea los eventos de otra sesión simultánea y avisa cuando solo puede atribuir por proyecto.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Supervisión**: est. 0.3h (≈25 % IA) · real —
- **Previsión IA**: 500k in / 70k out tok · 3.13 €
- **Dependencias**: plugin-audit-2 T-40 (cierra los cambios en curso de `usage-meter.py` y el fix de #16)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/usage-meter.py` (líneas 674-700, 1132), `agent-kits/shared/test_usage_meter.py`, `agent-kits/shared/test_usage_meter_runtimes.py`, `agent-kits/shared/test_usage_meter_task_states.py`, `docs/agents/CONTRACTS.md` (arista E7)
- **Runtimes**: La arista E7 cubre Claude (transcript), Codex (`CODEX_THREAD_ID`) y OpenCode: un test por runtime con dos sesiones solapadas; sin identidad de sesión, cobertura `parcial`.
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_usage_meter_runtimes.py -k "sesiones_simultaneas"` → `passed` (rojo antes: la suma de las dos ventanas duplica los eventos solapados)
  - `python -m pytest -q -n 3 agent-kits/shared/test_usage_meter.py agent-kits/shared/test_usage_meter_runtimes.py agent-kits/shared/test_usage_meter_task_states.py` → sin regresiones
  - `python agent-kits/shared/usage-meter.py --help` → exit 0

**Criterios de aceptación**

- [ ] Con `CODEX_THREAD_ID` la ventana incluye solo los eventos de esa sesión y sus subagentes.
- [ ] Con varias sesiones y sin identidad, el resultado declara `tokens_cobertura: parcial` y atribución por proyecto, y no se publica como `completa`.
- [ ] El mismo criterio vale para OpenCode (test).
- [ ] La degradación no bloquea el ciclo (`fuente: estimado` con aviso).

**Subtareas**

- [ ] Esperar el cierre de T-40 y rebasar
- [ ] RED: dos sesiones solapadas en el mismo directorio
- [ ] Vincular la ventana a la sesión
- [ ] Cobertura parcial y aviso
- [ ] Test por runtime

**Notas**: Grado reajustado: Minor (auditoría: Important).

### T-12 — Tests desacoplados del ledger real de una iniciativa (hallazgo del orquestador)

- **Descripción**: `test_fix2_gap1_ledger_records_verification` y `test_fix2_gap6_ledger_discloses_concurrent_doc_assertion` (`agent-kits/shared/test_ledger_write_transitions.py:246-262`) y `tests/test_phase3_review_contract.py` (`ROADMAP = docs/roadmap/2026-11-10-plugin-audit-2`) leen el `tasks.md` real de `plugin-audit-2`: impiden archivar ese ledger y se romperán al cerrarlo. Hay que moverlos a fixtures sintéticos conservando lo que verifican, y trasladar los hechos de esa iniciativa a una comprobación de su cierre. Se inventarían además los otros ficheros de tests que citan ledgers reales para clasificar los que leen contenido.
- **Changelog**: Las pruebas del repo ya no dependen del ledger real de una iniciativa, de modo que cerrarla o archivarla no las rompe.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1.0h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 350k in / 50k out tok · 2.21 €
- **Dependencias**: T-02, plugin-audit-2 T-40 (mismo fichero de tests y ledger citado)
- **Tipo**: test
- **Archivos**: `agent-kits/shared/test_ledger_write_transitions.py` (líneas 246-262), `tests/test_phase3_review_contract.py`, `tests/test_no_real_ledger_coupling.py` (nuevo), `tests/fixtures/`, `CONTRIBUTING.md`
- **Runtimes**: Solo tests de prosa y scripts: sin diferencia entre runtimes; no se regenera `interop/`.
- **Verificación**:
  - `python -m pytest -q tests/test_no_real_ledger_coupling.py` → `passed` (rojo antes: la guardia detecta los tres tests que leen `docs/roadmap/2026-11-10-plugin-audit-2/tasks.md`)
  - `python -m pytest -q agent-kits/shared/test_ledger_write_transitions.py tests/test_phase3_review_contract.py` → verde también con el directorio de `plugin-audit-2` renombrado temporalmente (se simula apuntando la raíz de prueba a un directorio vacío)
  - `git grep -nE "docs/roadmap/20[0-9]{2}-[0-9]{2}-[0-9]{2}-" -- agent-kits/shared/test_ledger_write_transitions.py tests/test_phase3_review_contract.py` → sin lecturas de ledgers reales

**Criterios de aceptación**

- [ ] Los tres tests leen un fixture sintético con el mismo formato (bloque `Fix2`, recibo `reconcile`, aserción de TDD n/a) y siguen comprobando el límite de 2.500 bytes, el recibo y la divulgación.
- [ ] Los hechos propios de `plugin-audit-2` T-40 pasan a una comprobación de cierre (un paso del ledger de esa iniciativa, no una prueba permanente).
- [ ] Una guardia detecta cualquier test nuevo que lea el contenido de `tasks.md` de una iniciativa real fuera de una lista blanca revisada; los demás ficheros del inventario (~17) quedan clasificados: solo ruta/forma vs lectura de contenido.
- [ ] Archivar `docs/roadmap/2026-11-10-plugin-audit-2/` no hace fallar ninguna prueba.

**Subtareas**

- [ ] Inventario `git grep` y clasificación
- [ ] RED: guardia del acoplamiento
- [ ] Fixtures sintéticos y reescritura de los tres tests
- [ ] Comprobación de cierre de T-40
- [ ] Nota en `CONTRIBUTING.md`

**Notas**: Hallazgo del orquestador, fuera de la auditoría de astra. Los demás ficheros del inventario se migran solo si leen contenido del ledger; el resto queda en la lista blanca documentada.

### T-13 — Journal: el texto de los turnos no se persiste; solo la extracción mínima (hallazgo 4, decisión 2026-11-24)

- **Descripción**: `journal-prompt.py:279` guarda por defecto el texto de cada turno (redactado solo de secretos) en `.claude/session-prompts-<sesión>.log`, lo que contradice `docs/CONSTITUTION.md:35` aunque luego se borre. **Decisión (2026-11-24): el usuario la delegó en gpt-6.2-astra («lo que considere Astra»), que eligió una variante de la opción B: extraer en memoria en cada `UserPromptSubmit` y persistir solo decisiones y pendientes (redactados y acotados), el contador y la marca de actividad; nunca el texto crudo.** No se borra el log en `SessionEnd` porque `SessionEnd` solo encola y `replay`/`recover` lo necesitan para las sesiones huérfanas (`hooks/session-journal.sh:5-10`, `journal.py:1165-1179`).
- **Changelog**: El plugin ya no guarda el texto de los turnos: solo las decisiones y los pendientes extraídos para el journal.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.6h · real —
- **Supervisión**: est. 0.15h (≈25 % IA) · real —
- **Previsión IA**: 200k in / 30k out tok · 1.29 €
- **Dependencias**: —
- **Tipo**: hooks
- **Archivos**: `agent-kits/shared/journal-prompt.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal*.py`, `hooks/session-journal.sh`, `hooks/` (lo que llame a la captura), `docs/knowledge/adr/ADR-010-*.md` (nota de revisión), `CLAUDE.md` (párrafo de memoria técnica), `docs/observability.md`, `docs/en/observability.md`, `interop/**` (regenerado si cambian hooks)
- **Runtimes**: La captura y el cierre corren como hooks en Claude Code, Codex y el adaptador de OpenCode: probar los tres con salida 0 y regenerar `interop/`.
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_journal*.py -k "sin_texto_crudo or recover or replay or private or captura"` → `passed` (rojo antes: el log guarda el turno literal)
  - prueba de punta a punta: cierre normal, corte sin `SessionEnd` + `recover`, reanudación de una sesión huérfana, fallo de escritura y reintento → journal correcto y ningún fichero con texto crudo del usuario
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**

- [ ] La decisión consta en el changelog del plan (2026-11-24, delegada en astra).
- [ ] En cada turno, respetando `<private>` y `sesion.captura: false`, se extraen decisiones y pendientes en memoria y se guardan atómicamente solo esos campos (redactados y acotados), el contador y la marca de actividad; ningún fichero contiene el texto crudo del turno.
- [ ] `replay`, `recover` y el resumen IA opt-in consumen ese estado; la copia del primer prompt o del transcript se sustituye por un resumen basado en la iniciativa y los datos extraídos (`journal.py:1753-1755`, `:2447`).
- [ ] El estado se retira tras confirmar la escritura del journal; una sesión huérfana reanudada integra los turnos posteriores sin perder ni duplicar (`journal.py:1137-1143`); los logs heredados se convierten y se borran solo tras confirmar la conversión.
- [ ] Probado: cierre normal, corte sin `SessionEnd`, reanudación, fallo de escritura y reintento, ambos opt-outs, ausencia de texto crudo y salida 0 en los tres runtimes; ADR-010, `CLAUDE.md` y `observability` ES/EN actualizados.

**Subtareas**

- [ ] RED: tests de ausencia de texto crudo, recover y reanudación
- [ ] Captura mínima en `journal-prompt.py`
- [ ] `replay`/`recover`/resumen sobre el estado mínimo; migración de logs heredados
- [ ] Docs ES/EN, ADR-010, `CLAUDE.md`; interop

**Notas**: Grado reajustado: Minor. La estimación original (opción B) se conserva; la variante elegida puede costar algo más (revisar al empezar).

### T-14 — Registros estructurados de revisión (rediseño propuesto por gpt-6.2-astra tras T-40 de plugin-audit-2)

- **Descripción**: La regla de T-40 que compara los recuentos declarados en la cabecera de una revisión con las filas de su tabla no converge con texto libre (6 intentos: bloquea de más con filas reclasificadas o con una revisión posterior limpia, y falla abierto con recuentos en palabras). Diseño de astra: `ledger-write.py review/verdict` escriben en `tasks.md` un registro versionado por revisión (identificador, alcance explícito, resultado por tarea, IDs de hallazgos) del que se genera la tabla y sus totales; tres resultados por tarea (limpia, con hallazgos, indeterminada): una traza histórica incompleta impide aprobaciones nuevas sin cambiar el estado existente y se despeja con evidencia archivada verificable o una revisión posterior completa que cubra la tarea; `task-brief.py`, `jira-flow.py` y `reconcile` consumen esa decisión; `ledger-archive.py` conserva el resultado por tarea y un hash del detalle. Migración en seco tarea por tarea: nunca «fase cerrada ⇒ todas aprobadas».
- **Changelog**: Las revisiones se registran de forma estructurada y la aprobación de cada tarea ya no depende de interpretar la prosa de la cabecera.
- **Estado**: borrador
- **Tiempo humano**: est. 32h · real —
- **Tiempo IA (ejec.)**: est. 8h · real —
- **Supervisión**: est. 2h (≈25 % IA) · real —
- **Previsión IA**: 2500k in / 350k out tok · 16 €
- **Dependencias**: plugin-audit-2 T-40 (cerrada con el fix6); T-02 de esta iniciativa (mismo `ledger-write.py`)
- **Tipo**: scripts
- **Archivos**: `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/ledger-archive.py`, `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py`, `agent-kits/shared/ledger-write.md`, `skills/adversarial-review/SKILL.md` (§6), tests de esos scripts, `docs/CONVENTIONS.md` + `docs/en/CONVENTIONS.md`, `interop/**` (regenerado)
- **Runtimes**: Scripts de `agent-kits/shared/` que usan igual Claude Code, Codex y OpenCode; la prosa de `adversarial-review` se regenera a interop.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_ledger_write*.py tests/test_ledger_lint.py skills/jira-sync/scripts/test_jira_flow.py -k "registro_estructurado or indeterminada or reclasificada"` → `passed` (rojo antes: la aprobación depende de la prosa de la cabecera)
  - comparación en seco de la migración sobre todos los ledgers de `docs/roadmap/` → ninguna tarea pasa a aprobada sin evidencia identificable (salida pegada)
  - puertas de runtimes y tokens → verde

**Criterios de aceptación**

- [ ] El veredicto por tarea sale del registro estructurado, no de la prosa: variar la redacción de la cabecera no cambia el resultado (test).
- [ ] Una fila reclasificada de gravedad, una tabla parcial o un Critical cruzado de otra fase se tratan correctamente (tests).
- [ ] Una traza histórica incompleta deja la tarea «indeterminada»: impide aprobaciones nuevas sin bloquear para siempre; una revisión posterior completa o evidencia archivada verificable la despeja.
- [ ] writer, lint, brief y Jira dan la misma decisión con y sin kit (copias declaradas).
- [ ] Migración en seco revisada antes de aplicar; ninguna aprobación recuperada sin evidencia.

