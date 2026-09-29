---
generacion:
  inicio: 2026-09-29T20:47:59Z
  fin: 2026-09-29T20:59:00Z
  fuente: estimado        # el meter degradó: carpeta de transcripciones no disponible  # ventana compartida con improvement-plan.md
  tokens_reales: null     # sin medición; estimación a juicio
  eur: null
  horas_ia: 0.18          # estimado = duración de reloj; no derivado de tokens
  duracion: 11m
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint
riesgo: medio              # piloto de sdd-proporcional
estado: en-progreso
---

# Checklist de Tareas — setup-statusline-polish (pulido de setup, statusline y puertas)

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-29 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | n/a (la ADR de T-09 cubre el encaje de C-07) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Bloqueo por ADR.** T-12 y T-13 (C-07) están **bloqueadas por T-09** (ADR de `architect`). No se implementan hasta que el usuario acepte la ADR.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Estabilizar la suite (tests deterministas) | 2 | 2 | 100% | 0 / 4.8h | 0 / 0.99h | 0 / 0.25h | 0 / 475k |
| Fase 2 — Quick wins de visibilidad y puertas | 5 | 5 | 100% | 0 / 14.4h | 0 / 3.42h | 0 / 0.85h | 0 / 1639k |
| Fase 3 — `/doctor`: tope estricto de la línea kwipu | 1 | 1 | 100% | 0 / 3.6h | 0 / 0.72h | 0 / 0.18h | 0 / 345k |
| Fase 4 — ADR de diseño y `id_prefix` / `group_id` | 0 | 3 | 0% | 0 / 14.0h | 0 / 4.10h | 0 / 1.02h | 0 / 1965k |
| Fase 5 — Alta segura en `projects.yaml` (bloqueada por la ADR) | 0 | 2 | 0% | 0 / 14.4h | 0 / 4.50h | 0 / 1.12h | 0 / 2157k |
| Fase 6 — Cierre, documentación y réplica en Linux | 0 | 1 | 0% | 0 / 3.6h | 0 / 0.90h | 0 / 0.23h | 0 / 431k |
| **TOTAL** | **8** | **14** | **57%** | **0 / 54.8h** | **0 / 14.63h** | **0 / 3.66h** | **0 / 7013k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.

---

## Fase 1 — Estabilizar la suite (tests deterministas)

**Estado**: completado · **Estimado**: 4.8h · **Real**: — · **Coste est.**: 246 € · **Tokens est.**: 475k

### T-01 — C-06 - Test de 200 upserts sin reloj

- **Descripción**: Sustituir `assertLess(t_sin_cambios, 10.0)` de `test_tiempos_200_upserts...` por una aserción sobre operaciones (0 `os.replace` y 0 escrituras en la pasada estable, con `mock`). La propiedad real es la linealidad, no los segundos.
- **Changelog**: El test de 200 upserts del exportador Markdown deja de fallar según la carga de la máquina.
- **Estado**: completado
- **Prioridad**: Alta
- **Tiempo humano**: est. 1.2h · real —
- **Tiempo IA (ejec.)**: est. 0.27h · real —
- **Supervisión**: est. 0.07h (≈25 % IA) · real —
- **Previsión IA**: 111k in / 18k out tok · 1.70 €
- **Dependencias**: ninguna
- **Tipo**: test
- **Archivos**: `skills/knowledge-services/scripts/test_backend_markdown_export.py`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `for i in $(seq 20); do python3 -m pytest -q skills/knowledge-services/scripts/test_backend_markdown_export.py -k 200_upserts || break; done` -> 20 ejecuciones, 0 fallos (CA-08)
  - mutante: reescribir un fichero por upsert en la pasada estable y `python3 -m pytest -q skills/knowledge-services/scripts/test_backend_markdown_export.py -k 200_upserts` -> rojo; sin el mutante -> verde

- **Evidencia**:
  RED: test_tiempos_200_upserts_* con mutante (os.replace extra en la rama sin_cambios) falló (1 failed) · 2026-09-29
  GREEN: bucle de 20 ejecuciones de -k 200_upserts -> 0 fallos; 1 passed sin mutante. La pasada estable hace 2 os.replace (solo manifest*), constante, sin techo en segundos.

**Criterios de aceptación**

- [x] El test ya no contiene ningún techo en segundos.
- [x] Falla con el mutante de un `os.replace` por fichero en la pasada estable (evidencia pegada).
- [x] 20 ejecuciones seguidas en verde (CA-08).

**Subtareas**

- [x] Localizar el test (líneas ~1132-1149) y contar `os.replace` con `mock.patch`.
- [x] Escribir el mutante y comprobar el rojo.
- [x] Bucle de 20 ejecuciones.

**Notas**: Criterio de la spec: CA-08.

### T-02 — C-09b - Tests de conocimiento sobre fixture versionado

- **Descripción**: Los ~20 tests de `tests/test_knowledge_find.py` y `tests/test_knowledge_index.py` que leen el `docs/knowledge/` real (ya no versionado) pasan a `evals/fixtures/project/docs/knowledge/` u otro fixture bajo `tests/fixtures/`. Las cifras de línea base se reformulan contra el fixture sin perder lo que prueban. Fixture sin datos personales.
- **Changelog**: Las pruebas de búsqueda e índice de conocimiento funcionan en un clon limpio, sin la memoria local.
- **Estado**: completado
- **Prioridad**: Alta
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 0.72h · real —
- **Supervisión**: est. 0.18h (≈25 % IA) · real —
- **Previsión IA**: 297k in / 48k out tok · 4.54 €
- **Dependencias**: ninguna
- **Tipo**: test
- **Archivos**: `tests/test_knowledge_find.py`, `tests/test_knowledge_index.py`, `evals/fixtures/project/docs/knowledge/`, `tests/fixtures/`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q tests/test_knowledge_find.py tests/test_knowledge_index.py` -> 0 failed en un árbol sin `docs/knowledge/` (CA-17)
  - `grep -rniE "@[a-z0-9-]+\.(com|tv|es)|C:\\Users|/home/[a-z]" evals/fixtures/project/docs/knowledge tests/fixtures` -> sin coincidencias

- **Evidencia**:
  RED: en un árbol sin docs/knowledge/ (git archive de HEAD) 20 tests de tests/test_knowledge_find.py y test_knowledge_index.py se SALTABAN (SKIPPED "no hay docs/knowledge/ real"): no verificaban nada en clon limpio · 2026-09-29
  Migrados (20): find -> test_ca01_area_estimacion_*, test_ca02_consola_windows_cp1252_*, test_todas_las_entradas_reales_*, test_area_inexistente_sobre_el_corpus_real_*, test_real_tokens_por_hora_*, test_real_de_y_pato_*, test_ca03_related_adr010_*, test_ca04_show_adr012_*, test_enrutado_sobre_el_corpus_real_devops_* (+ los de la fixture `real` de 6 parametrizaciones en L676: 6 saltos) ; index -> test_el_indice_real_es_biyectivo_*, test_las_cifras_del_corpus_de_hoy, test_para_los_adr_el_area_*, test_quitar_una_fila_*, test_vaciar_el_area_*.
  Fixture: tests/fixtures/knowledge-corpus/docs/knowledge/ (26 entradas sintéticas: 12 ADR, 5 GOT, 9 LES; sin datos personales). Cifras reformuladas: total del corpus 32 -> 26 (>= 26).

**Criterios de aceptación**

- [x] Los ~20 tests afectados pasan con `docs/knowledge/` ausente (CA-17).
- [x] Ningún test lee `docs/knowledge/` de la raíz del repo.
- [x] El fixture no contiene datos personales (rutas relativas, `<stack>/…`).
- [x] Notas lista el conjunto exacto de tests migrados (cierra la incógnita de los «~20»).

**Subtareas**

- [x] Enumerar los tests que dependen de `docs/knowledge/` real.
- [x] Ampliar el fixture con las entradas mínimas.
- [x] Reformular las cifras de línea base.
- [x] Ejecutar en árbol sin `docs/knowledge/`.

**Notas**: Criterio de la spec: CA-17.

---

## Fase 2 — Quick wins de visibilidad y puertas

**Estado**: completado · **Estimado**: 14.4h · **Real**: — · **Coste est.**: 742 € · **Tokens est.**: 1639k

### T-03 — C-03 - Statusline: coste correcto

- **Descripción**: Reproducir el `$0,00` (coma decimal en `printf '%.2f'` bajo locale; redondeo) y arreglarlo con `LC_NUMERIC=C`; un coste positivo < 0,01 se muestra `<$0.01`, nunca como cero. Sin red ni subprocesos extra.
- **Changelog**: La statusline muestra el coste de la sesión correctamente con cualquier locale.
- **Estado**: completado
- **Prioridad**: Alta
- **Tiempo humano**: est. 1.2h · real —
- **Tiempo IA (ejec.)**: est. 0.27h · real —
- **Supervisión**: est. 0.07h (≈25 % IA) · real —
- **Previsión IA**: 111k in / 18k out tok · 1.70 €
- **Dependencias**: ninguna
- **Tipo**: hooks
- **Archivos**: `statusline/roadmap-statusline.sh`, `tests/test_hooks_shell.py`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q tests/test_hooks_shell.py -k statusline_coste` -> passed (0,42 con locale de coma -> `$0.42`; 0,004 -> `<$0.01`) (CA-05)
  - `bash -n statusline/roadmap-statusline.sh` -> exit 0

- **Evidencia**:
  RED: test_statusline_coste_con_locale_de_coma_decimal_sigue_siendo_punto (LC_ALL=de_DE.utf8) falló con `0,00` en vez de `$0.42`; test_statusline_coste_pequeno_positivo_[0.004 y 0.0001] fallaron con `$0.00` · 2026-09-29
  GREEN: `pytest tests/test_hooks_shell.py -k statusline` -> 9 passed; `bash -n statusline/roadmap-statusline.sh` -> exit 0. Sin locale de coma instalado (CI mínimo) el test de locale se omite con aviso.

**Criterios de aceptación**

- [x] Con coste 0,42 y locale de coma decimal la salida contiene `$0.42` (CA-05).
- [x] Un coste positivo menor de 0,01 no se muestra como `$0.00`.
- [x] Si el locale de coma no existe en CI, el test lo simula o se omite con aviso (no falla en falso).

**Subtareas**

- [x] Test rojo que reproduce el defecto.
- [x] Aplicar `LC_NUMERIC=C` y el formato `<$0.01`.
- [x] Comprobar salida idéntica en el resto de casos.

**Notas**: Criterio de la spec: CA-05.

### T-04 — C-04 - coverage-gate: sin falso «no disponible»

- **Descripción**: `herramienta_disponible` trata `TimeoutExpired` igual que un `ImportError`. Separarlos: el timeout se reintenta (timeout mayor) y, si persiste, queda «no verificado»; solo un import fallido real da «no disponible» (exit 2 con aviso). Nunca un % inventado.
- **Changelog**: El gate de cobertura ya no dice «no disponible» por un arranque lento de Python.
- **Estado**: completado
- **Prioridad**: Alta
- **Tiempo humano**: est. 1.8h · real —
- **Tiempo IA (ejec.)**: est. 0.45h · real —
- **Supervisión**: est. 0.11h (≈25 % IA) · real —
- **Previsión IA**: 185k in / 30k out tok · 2.84 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `skills/unit-tests/scripts/coverage-gate.py`, `skills/unit-tests/scripts/test_coverage_gate.py`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q skills/unit-tests/scripts/test_coverage_gate.py` -> passed, con casos nuevos: timeout simulado + módulo presente -> no «no disponible»; módulo ausente -> exit 2 (CA-06)

- **Evidencia**:
  RED: test_timeout_con_modulo_presente_reintenta_* y test_timeout_persistente_es_no_verificado_* fallaron con AttributeError: module 'coverage_gate' has no attribute 'sondear_herramienta' (el código anterior trataba TimeoutExpired como ImportError) · 2026-09-29
  GREEN: `pytest -q skills/unit-tests/scripts/test_coverage_gate.py` -> 23 passed, 5 failed; los 5 rojos (test_min_0_*, test_min_100_*, test_changed_only_* x2, test_json_y_md_*) son PREEXISTENTES en Windows (idénticos con el código anterior: 5 failed, 17 passed); los 6 tests nuevos pasan.
  Semántica: import fallido real -> exit 2 «no disponible»; timeout -> 1 reintento (15s -> 60s); persistente -> exit 2 «no verificado»; nunca un % inventado.

**Criterios de aceptación**

- [x] Con `pytest_cov` presente y un arranque lento simulado no informa «no disponible» (CA-06).
- [x] Si el módulo falta de verdad: exit 2 y aviso, sin porcentaje.
- [x] Un timeout persistente se informa como «no verificado», distinto de «no disponible».

**Subtareas**

- [x] Tests rojos (timeout simulado; módulo ausente).
- [x] Separar excepciones en `herramienta_disponible` (líneas ~150-158).
- [x] Reintento acotado.

**Notas**: Criterio de la spec: CA-06.

### T-05 — C-05 - Dashboard: leer las evaluaciones con las dos familias de etiquetas

- **Descripción**: `_scan_leer_eval` acepta `Coste`/`Esfuerzo humano` (histórico) y `Tiempo humano`/`Coste humano a N EUR/h`/`Coste humano (N EUR/h)`, y recurre a `estado:` del frontmatter cuando no hay fila `Estado`. CA-07 revisado: `graphiti-memory` no tiene tabla de coste; el lector devuelve nulo para coste y esfuerzo con un aviso explícito que nombra la evaluación (no parsea prosa ni reescribe el registro). Ojo con «1,300 EUR» (coma de miles): no reutilizar `_num()` a ciegas.
- **Changelog**: El dashboard vuelve a mostrar coste y esfuerzo de las evaluaciones recientes y avisa cuando una no tiene tabla.
- **Estado**: completado
- **Prioridad**: Media
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 0.90h · real —
- **Supervisión**: est. 0.23h (≈25 % IA) · real —
- **Previsión IA**: 371k in / 60k out tok · 5.68 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`, `tests/test_dashboard.py`, `skills/roadmap-dashboard/SKILL.md`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q tests/test_dashboard.py` -> passed, con un caso por variante de etiqueta (`Tiempo humano`, `Coste humano a N EUR/h`, `Coste humano (N EUR/h)`, histórica) (CA-07)
  - `python3 skills/roadmap-dashboard/scripts/build_dashboard.py --json` sobre este repo -> 4 de las 5 evaluaciones afectadas con coste y esfuerzo no nulos; `graphiti-memory` nulo con aviso nominal

- **Evidencia**:
  RED: `python tests/test_dashboard.py` -> FALLO: variante Tiempo humano: esperado '39.5h (33h base +20%)', obtenido None · 2026-09-29
  GREEN: `python tests/test_dashboard.py` -> OK (3 iniciativas, 1 aviso esperado). Variantes cubiertas: histórica, `Tiempo humano`, `Coste humano a N EUR/h`, `Coste humano (N EUR/h)`, estado por frontmatter, sin tabla (nulo + aviso nominal).
  build_dashboard.py --root docs/roadmap --json: knowledge-services, training-data-services y setup-statusline-polish con coste y esfuerzo no nulos y eval_estado=completado; graphiti-memory nulo + aviso «2026-09-15-graphiti-memory: evaluation.md presente pero no se leyeron coste, esfuerzo». (Hoy 3 de las 4 con tabla son afectadas por las etiquetas nuevas; las históricas ya se leían.) El aviso «no se leyeron eval_estado…» desapareció.

**Criterios de aceptación**

- [x] Cada variante de etiqueta tiene su test (CA-07 revisado).
- [x] Las 4 evaluaciones con tabla aportan coste y esfuerzo no nulos; `graphiti-memory` da nulo + aviso nominal, sin excepción.
- [x] El estado se lee del frontmatter si no hay fila `Estado`; el aviso «no se leyeron eval_estado…» desaparece.
- [x] «1,300 EUR» (coma de miles) no se lee como 1,3.

**Subtareas**

- [x] Fixtures de cada variante.
- [x] Alias de etiquetas y lectura de frontmatter.
- [x] Aviso nominal para evaluaciones sin tabla.
- [x] Comprobar contra las 5 evaluaciones reales (solo lectura).

**Notas**: Criterio de la spec: CA-07 (revisado). Reescritura de CA-07 propuesta en el plan (sincronizar `spec.md`).

### T-06 — C-02 - `find` que nunca elige temporales bajo `~/.claude/jobs`

- **Descripción**: Excluir `*/.claude/jobs/*` y temporales de los `find ... | head -1` de la statusline y de `/setup` 5-bis, prefiriendo plugin instalado o proyecto. Un `HOME` falso con dos copias fija el criterio. Las otras ~74 apariciones del patrón quedan como deuda anotada (fuera de alcance; iniciativa propia con helper común).
- **Changelog**: La statusline y `/setup` dejan de resolver rutas a copias temporales antiguas del plugin.
- **Estado**: completado
- **Prioridad**: Media
- **Tiempo humano**: est. 3.0h · real —
- **Tiempo IA (ejec.)**: est. 0.72h · real —
- **Supervisión**: est. 0.18h (≈25 % IA) · real —
- **Previsión IA**: 297k in / 48k out tok · 4.54 €
- **Dependencias**: ninguna
- **Tipo**: hooks
- **Archivos**: `statusline/roadmap-statusline.sh`, `commands/setup.md`, `tests/test_hooks_shell.py`, `docs/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `evals/cases/command-setup.json`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q tests/test_hooks_shell.py -k jobs_temporal` -> passed (con copias en `$HOME/.claude/jobs/x/` y en el plugin, gana el plugin) (CA-04)
  - `python3 scripts/export-interop.py --check` -> exit 0

- **Evidencia**:
  RED: test_statusline_find_jobs_temporal_* devolvió `copia-vieja-jobs` en vez de `plugin-instalado`; test_setup_5bis_find_jobs_temporal_* devolvió `.../.claude/jobs/x/statusline/roadmap-statusline.sh` · 2026-09-29
  GREEN: `pytest tests/test_hooks_shell.py -k "jobs_temporal or statusline"` -> 11 passed; `export-interop.py` regenerado (interop/{codex,opencode} setup) y `export-interop.py --check` -> 50 ficheros al día (exit 0).
  Deuda anotada (fuera de alcance): ~74 apariciones más del patrón `find ... | head -1` en agents/, commands/, skills/, hooks/ (iniciativa propia con helper común).

**Criterios de aceptación**

- [x] Con una copia vieja bajo `~/.claude/jobs` y otra en el plugin, la statusline y el `find` de 5-bis devuelven la del plugin o proyecto (CA-04).
- [x] `interop/` regenerado (`commands/setup.md` tocado).
- [x] La deuda de las ~74 apariciones restantes queda anotada en Notas.

**Subtareas**

- [x] Test con `HOME` falso.
- [x] Ajustar `find` en el script y en 5-bis.
- [x] Regenerar `interop/`.
- [x] Anotar la deuda.

**Notas**: Criterio de la spec: CA-04. Deuda anotada: ~74 apariciones más del patrón `find ... | head -1` en `agents/`, `commands/`, `skills/`, `hooks/`; iniciativa propia con helper común.

### T-07 — C-01 - Statusline: iniciativa en curso con varias activas

- **Descripción**: Con 2+ ledgers activos la línea pasa a `📋 N activas · ▶ <slug> T-XX/YY NN%`. La iniciativa en curso sale del marcador abierto de `usage-meter` (lectura directa de `.claude/usage-state.json`, sin lanzar `usage-meter.py`; claves `<slug>/<artefacto>` y `docs/roadmap/<fecha>-<slug>/…`) y, si no hay, del `tasks.md` modificado más reciente. Un marcador de spec o evaluación sin ledger no muestra progreso (comportamiento fijado por test). La lógica va en `progress-report.py` con tests, no en bash; escaneo solo de `docs/roadmap/*/tasks.md`; una sola activa = salida idéntica.
- **Changelog**: La statusline marca en qué iniciativa se está trabajando cuando hay varias activas.
- **Estado**: completado
- **Prioridad**: Media
- **Tiempo humano**: est. 4.8h · real —
- **Tiempo IA (ejec.)**: est. 1.08h · real —
- **Supervisión**: est. 0.27h (≈25 % IA) · real —
- **Previsión IA**: 445k in / 72k out tok · 6.81 €
- **Dependencias**: ninguna
- **Tipo**: hooks
- **Archivos**: `statusline/roadmap-statusline.sh`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/test_progress_report.py`, `tests/test_hooks_shell.py`, `docs/observability.md`, `docs/en/observability.md`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_progress_report.py tests/test_hooks_shell.py -k "en_curso or statusline"` -> passed con CA-01, CA-02 y CA-03 (mismo ID en el nombre del test)
  - `python3 agent-kits/shared/progress-report.py --help` -> exit 0 (sin regresión de CLI)

- **Evidencia**:
  RED: `pytest agent-kits/shared/test_progress_report.py -k en_curso` -> 9 failed, 1 passed (falta iniciativa_en_curso); statusline_ca01/ca02/en_curso_corrupto fallaron con el script anterior (3 failed) · 2026-09-29
  GREEN: `pytest tests/test_hooks_shell.py agent-kits/shared/test_progress_report.py -k "en_curso or statusline"` -> 24 passed; `python3 agent-kits/shared/progress-report.py --help` -> exit 0.
  CA-01/CA-02/CA-03 (test_*_ca01/ca02/ca03_*): marcador abierto con las dos formas de clave, tasks.md más reciente sin marcador, una activa = salida idéntica sin ▶. Selección en `progress-report.py` (`iniciativa_en_curso`, pura); `active --json` añade la clave solo con 2+ activas; la statusline sólo formatea. Sin subprocesos ni red nuevos.
  Nota: la salida con 2+ activas sin en-curso resoluble conserva «📋 N iniciativas activas»; con en-curso, «📋 N activas · ▶ …».
  Fallo preexistente en Windows (no de esta tarea): test_session_con_activas_bloque_acotado (separador de ruta).

**Criterios de aceptación**

- [x] CA-01: 4 activas + marcador abierto de `training-data-services` -> `📋 4 activas · ▶ training-data-services T-06/11 55%`.
- [x] CA-02: sin marcador, marca la de `tasks.md` más reciente.
- [x] CA-03: una sola activa -> salida idéntica a la actual, sin `▶`.
- [x] `usage-state.json` ausente o corrupto -> recurre al `tasks.md` más reciente; sin ninguno, línea actual.
- [x] Sin red y sin subprocesos nuevos por refresco.

**Subtareas**

- [x] Función pura de selección en `progress-report.py`.
- [x] Extraer slug de las dos formas de clave.
- [x] Enganche en el script bash.
- [x] Actualizar `docs/observability.md` (+ EN).

**Notas**: Criterio de la spec: CA-01, CA-02, CA-03.

---

## Fase 3 — `/doctor`: tope estricto de la línea kwipu

**Estado**: completado · **Estimado**: 3.6h · **Real**: — · **Coste est.**: 185 € · **Tokens est.**: 345k

### T-08 — C-09a - `/doctor`: línea kwipu con `tope_ms` estricto

- **Descripción**: Decisión 3a: tope estricto con timeout duro. Ejecutar la sonda kwipu en un hilo `daemon` con `join(timeout)` y abandonarlo si no termina (sin escrituras a medias), de modo que la línea no supere `tope_ms` + un margen fijo documentado. Medir antes la fuente del exceso (`_urlopen_local`, DNS, arranque del adaptador). Hotspot: tarea aislada, sin paralelizar con otras sobre `doctor.py`.
- **Changelog**: `/doctor` ya no se demora más de su tope al consultar el servidor de conocimiento.
- **Estado**: completado
- **Prioridad**: Media
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 0.72h · real —
- **Supervisión**: est. 0.18h (≈25 % IA) · real —
- **Previsión IA**: 297k in / 48k out tok · 4.54 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/agents/CONTRACTS.md`, `skills/knowledge-services/backends/README.md`, `agent-kits/shared/capabilities.py`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_doctor.py -k tope_ms` -> passed (servidor simulado lento: duración <= `tope_ms` + margen) (CA-16)
  - `python3 agent-kits/shared/doctor.py --json` -> exit 0 o 1 sin traceback; línea kwipu presente

- **Evidencia**:
  Medición previa (fuente del exceso): adaptador simulado con blackhole TCP local, tope_ms=2000 -> `_linea_capacidad_backend` tardó 4.02 s = health() + verify() secuenciales, cada uno respetando su timeout. No es DNS ni el arranque del adaptador.
  RED: test_ca16_tope_ms_estricto_backend_lento_no_pasa_de_tope_mas_margen falló (NameError/duración 4 s > tope+margen) contra el código anterior · 2026-09-29
  GREEN: `pytest agent-kits/shared/test_doctor.py -k "tope_ms or ca16"` -> 6 passed; suite completa test_doctor.py -> 150 passed + 1 nuevo E17 tras documentar; `python3 agent-kits/shared/doctor.py --json` -> exit 0, sin traceback, línea «kwipu (backend)» presente.
  Diseño: hilo daemon + join(tope_ms + CAPACIDAD_MARGEN_MS=500). Margen documentado en E17 (CONTRACTS.md), backends/README.md y el código. El hilo abandonado es de solo lectura (health/verify).

**Criterios de aceptación**

- [x] Con servidor simulado lento la línea kwipu termina en <= `tope_ms` + margen fijo documentado (CA-16).
- [x] El hilo abandonado es `daemon` y no deja escrituras a medias.
- [x] El margen está documentado en E17 de `CONTRACTS.md` y en el código.
- [x] Se mide (y se pega) la fuente del exceso antes del arreglo.

**Subtareas**

- [x] Medir con reloj/servidor simulado.
- [x] Sonda en hilo con `join(timeout)`.
- [x] Test con servidor lento.
- [x] Actualizar E17.

**Notas**: Criterio de la spec: CA-16.

---

## Fase 4 — ADR de diseño y `id_prefix` / `group_id`

**Estado**: borrador · **Estimado**: 14.0h · **Real**: — · **Coste est.**: 726 € · **Tokens est.**: 1965k

### T-09 — ADR - Enmienda a ADR-018 / PAT-001 / constitución §4: alta que solo añade en `projects.yaml`

- **Descripción**: Tarea de DISEÑO previa a C-07, a cargo del agente `architect`: ADR nueva `propuesta` (enmienda a ADR-018, PAT-001 y constitución §4) que autorice SOLO AÑADIR un bloque en el `projects.yaml` del stack, con vista previa, confirmación y copia de seguridad, y que resuelva la tensión de la escritura atómica (reemplazo) sobre un fichero que el plugin no creó. Debe fijar: forma(s) de YAML reconocidas (con la muestra anonimizada de `<stack>/kwipu/config/projects.yaml`), `root` absoluta o relativa, y código de salida de «forma no reconocida». Si no se acepta, C-07 se reduce a imprimir el bloque (-8 h humanas, -3 h IA). No estaba en la evaluación (+2 h humanas, +0,5 h IA declaradas).
- **Changelog**: Nueva decisión de diseño que autoriza dar de alta el proyecto en Kwipu añadiendo un bloque, sin modificar lo existente.
- **Estado**: borrador
- **Prioridad**: Crítica
- **Tiempo humano**: est. 2.0h · real —
- **Tiempo IA (ejec.)**: est. 0.50h · real —
- **Supervisión**: est. 0.12h (≈25 % IA) · real —
- **Previsión IA**: 206k in / 34k out tok · 3.15 €
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `docs/knowledge/adr/`, `docs/knowledge/README.md`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - lectura: la ADR existe en `docs/knowledge/adr/` con `estado: propuesta`, cita ADR-018, PAT-001 y §4, y fija forma de YAML, `root` y exit code
  - `grep -n "ADR-0" docs/knowledge/README.md` -> la fila de la ADR nueva en el índice

**Criterios de aceptación**

- [ ] ADR `propuesta` aceptada por el usuario antes de arrancar T-12 y T-13 (puerta).
- [ ] Fija las formas de `projects.yaml` reconocidas a partir de una muestra anonimizada (sin datos personales).
- [ ] Declara el contrato de escritura: solo añade, vista previa, confirmación, copia de seguridad, atómica.
- [ ] Índice `docs/knowledge/README.md` actualizado (recordatorio: `docs/knowledge/` es solo local, no se versiona).

**Subtareas**

- [ ] Recabar muestra anonimizada de `projects.yaml`.
- [ ] Opciones de encaje con trade-offs.
- [ ] Validar con el usuario.
- [ ] Escribir ADR + índice.

**Notas**: Criterio de la spec: Condiciones 1 y 2 de la evaluación.

### T-10 — C-08a - `id_prefix` elegible y derivación de nombre y `group_id` (solo instalaciones nuevas)

- **Descripción**: `/setup` propone el `id_prefix` (slug de la carpeta), valida `^[a-z0-9][a-z0-9-]*$` y lo guarda en `taxonomy.json`. Decisión del usuario: el `group_id` derivado de `id_prefix` se aplica SOLO a instalaciones nuevas (sin `group_id` efectivo previo); las que ya tienen un `group_id` implícito lo conservan y reciben un aviso. La derivación vive en UN solo sitio, consumido por `knowledge-schema.py` y `graphiti.py` (hoy 33 líneas duplicadas). Un test fija que una instalación con `id_prefix` distinto de la carpeta no cambia de `group_id`. Hotspot `knowledge-schema.py`: solo esta tarea lo toca.
- **Changelog**: Los proyectos nuevos eligen su nombre (`id_prefix`) en `/setup`; los ya existentes conservan su grupo de Graphiti.
- **Estado**: borrador
- **Prioridad**: Media
- **Tiempo humano**: est. 7.0h · real —
- **Tiempo IA (ejec.)**: est. 2.10h · real —
- **Supervisión**: est. 0.53h (≈25 % IA) · real —
- **Previsión IA**: 866k in / 141k out tok · 13.25 €
- **Dependencias**: T-08 (orden; hotspots separados)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`, `tests/test_graphiti_security.py`, `agent-kits/shared/knowledge-find.py`, `commands/setup.md`, `docs/agents/knowledge-curator.md`, `skills/knowledge-services/backends/README.md`, `docs/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `evals/cases/command-setup.json`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_capabilities.py skills/knowledge-services/scripts/test_backend_graphiti.py tests/test_graphiti_security.py` -> passed, con CA-14 y el test de `group_id` conservado (`id_prefix` != carpeta -> mismo `group_id`)
  - `python3 scripts/export-interop.py --check` -> exit 0

**Criterios de aceptación**

- [ ] CA-14: sin `id_prefix`, `/setup` propone el slug, valida la forma y lo guarda; nombre de proyecto y `group_id` de instalaciones NUEVAS lo heredan salvo sobrescritura.
- [ ] Instalación con `group_id` implícito previo: lo conserva y recibe aviso (test).
- [ ] Una única función de derivación consumida por `knowledge-schema.py` y `graphiti.py` (sin duplicado).
- [ ] `id_prefix` inválido: rechaza y vuelve a preguntar; no guarda.
- [ ] `interop/` regenerado.

**Subtareas**

- [ ] Test rojo de compatibilidad del `group_id`.
- [ ] Extraer derivación única.
- [ ] Paso de `/setup` con validación.
- [ ] Actualizar consumidores (`capabilities`, `knowledge-find`, `doctor`).
- [ ] Regenerar `interop/`.

**Notas**: Criterio de la spec: CA-14 (+ decisión: solo instalaciones nuevas). Decisión del usuario 2026-09-29: derivación desde `id_prefix` solo en instalaciones nuevas.

### T-11 — C-08b - Avisos: renombrado con conocimiento exportado y `group_id` con episodios de otro origen

- **Descripción**: Dos avisos sin bloqueo, cada uno con test (CA-15). (1) Renombrar `id_prefix` con conocimiento ya exportado: avisa de que cambian los `knowledge_id`, no migra. (2) `group_id` con episodios de otro origen antes de la primera sincronización, decisión 2c: primero el estado local (manifiesto publicado / `outbox`), después consulta al servidor solo si responde (loopback, opt-in, con el tope de red del adaptador); sin conexión degrada a «no verificado». Se suma el aviso de T-10 (instalación con `group_id` implícito conservado).
- **Changelog**: `/setup` avisa cuando renombrar un proyecto cambia sus identificadores o cuando un grupo de Graphiti ya contiene datos de otro origen.
- **Estado**: borrador
- **Prioridad**: Media
- **Tiempo humano**: est. 5.0h · real —
- **Tiempo IA (ejec.)**: est. 1.50h · real —
- **Supervisión**: est. 0.38h (≈25 % IA) · real —
- **Previsión IA**: 618k in / 101k out tok · 9.46 €
- **Dependencias**: T-10
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/scripts/knowledge-sync.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`, `skills/knowledge-services/scripts/test_knowledge_sync.py`, `agent-kits/shared/test_knowledge_schema.py`, `commands/setup.md`, `skills/knowledge-services/SKILL.md`, `docs/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_knowledge_schema.py skills/knowledge-services/scripts/test_backend_graphiti.py skills/knowledge-services/scripts/test_knowledge_sync.py -k "aviso or CA_15"` -> passed (renombrado con export; episodios de otro origen local; servidor caído -> «no verificado»)
  - `python3 scripts/export-interop.py --check` -> exit 0

**Criterios de aceptación**

- [ ] Renombrar con conocimiento ya exportado advierte del cambio de `knowledge_id` y no migra (CA-15).
- [ ] `group_id` con episodios de otro origen: aviso antes de la primera sincronización; primero estado local, luego servidor si responde; sin servidor -> «no verificado» (CA-15).
- [ ] Ningún aviso bloquea (exit 0); solo hay red en la consulta opt-in acotada a loopback.
- [ ] Cada aviso tiene su test.

**Subtareas**

- [ ] Definir el «estado local» que identifica el origen.
- [ ] Aviso 1 (renombrado).
- [ ] Aviso 2 (local -> servidor -> no verificado).
- [ ] Enganche en `/setup` y regenerar `interop/`.

**Notas**: Criterio de la spec: CA-15 (decisión 2c).

---

## Fase 5 — Alta segura en `projects.yaml` (bloqueada por la ADR)

**Estado**: borrador · **Estimado**: 14.4h · **Real**: — · **Coste est.**: 748 € · **Tokens est.**: 2157k

### T-12 — C-07a - Script de alta en `projects.yaml` (solo añade)

- **Descripción**: Script stdlib nuevo `skills/knowledge-services/scripts/kwipu-project-add.py` y sus tests. Implementa el flujo de la spec (pasos 2-7) según la forma y el contrato fijados por la ADR de T-09: reconoce formas concretas y rechaza el resto (no escribe, imprime el bloque y sale con el código documentado); homónimo con otra `root` -> conflicto; misma `root` -> no-op; si no existe: vista previa, confirmación, copia de seguridad (su fallo aborta), escritura atómica con relectura justo antes; valida `id_prefix` (`^[a-z0-9][a-z0-9-]*$`) y `root` contra inyección y `..`; comprueba que el destino es el `projects.yaml` del stack indicado; imprime los comandos de `build_view` y de reinicio sin ejecutarlos. Validación solo sobre copias en temporales; la ejecución real la lanza el usuario. Ejemplos con `<stack>/…`, sin datos personales.
- **Changelog**: Nuevo script que da de alta el proyecto en Kwipu añadiendo un bloque, con vista previa, confirmación y copia de seguridad.
- **Estado**: borrador
- **Prioridad**: Alta
- **Tiempo humano**: est. 9.0h · real —
- **Tiempo IA (ejec.)**: est. 2.80h · real —
- **Supervisión**: est. 0.70h (≈25 % IA) · real —
- **Previsión IA**: 1154k in / 188k out tok · 17.66 €
- **Dependencias**: T-09 (ADR aceptada), T-11 · **BLOQUEADA por T-09 (ADR)**
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/kwipu-project-add.py`, `skills/knowledge-services/scripts/test_kwipu_project_add.py`, `skills/knowledge-services/references/kwipu-adapter.md`, `skills/knowledge-services/SKILL.md`, `evals/cases/skill-knowledge-services.json`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py` -> passed con CA-09..CA-13 (mismo ID en el nombre del test)
  - `python3 -m pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py -k byte_a_byte` -> passed (resto del fichero idéntico)
  - `grep -nE "subprocess|os\.system" skills/knowledge-services/scripts/kwipu-project-add.py` -> sin coincidencias (`build_view` solo dentro de cadenas impresas)

**Criterios de aceptación**

- [ ] CA-09: YAML reconocido sin el proyecto + confirmación -> copia de seguridad, exactamente un bloque añadido con `root` = `export_dir`, resto byte a byte igual.
- [ ] CA-10: mismo proyecto y `root` -> no cambia nada y lo dice.
- [ ] CA-11: forma no reconocida -> no escribe, imprime el bloque, exit distinto de 0 documentado.
- [ ] CA-12: homónimo con otra `root` -> no escribe, muestra el conflicto, pide otro nombre.
- [ ] CA-13: sin confirmación o con fallo de la copia -> no escribe; no ejecuta `build_view` ni reinicia contenedores.
- [ ] Entradas inyectadas (saltos de línea, `:`, `#`, comillas, `..`) rechazadas con test.

**Subtareas**

- [ ] Reconocedor de formas (según la ADR).
- [ ] Validaciones de `id_prefix` y `root`.
- [ ] Copia + escritura atómica + relectura.
- [ ] Tests de mutantes (nunca modificar ni borrar entradas).
- [ ] Referencias en la skill.

**Notas**: Criterio de la spec: CA-09..CA-13.

### T-13 — C-07b - Enganche en `/setup` 5-sexies

- **Descripción**: `/setup` 5-sexies propone el `id_prefix` (T-10), invoca el script de alta con el `export_dir` de `taxonomy.json`, muestra la vista previa, pide confirmación y muestra los comandos de `build_view` y de reinicio que debe ejecutar el usuario (no los ejecuta). Degrada con aviso sin `python3`. Añade a `docs/agents/CONTRACTS.md` la arista nueva `/setup` -> script de alta.
- **Changelog**: `/setup` ofrece dar de alta el proyecto en Kwipu con confirmación y sin tocar lo ya existente.
- **Estado**: borrador
- **Prioridad**: Media
- **Tiempo humano**: est. 5.4h · real —
- **Tiempo IA (ejec.)**: est. 1.70h · real —
- **Supervisión**: est. 0.42h (≈25 % IA) · real —
- **Previsión IA**: 701k in / 114k out tok · 10.72 €
- **Dependencias**: T-12 · **BLOQUEADA por T-09 (ADR)**
- **Tipo**: docs
- **Archivos**: `commands/setup.md`, `docs/agents/CONTRACTS.md`, `skills/knowledge-services/SKILL.md`, `docs/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `evals/cases/command-setup.json`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 scripts/export-interop.py --check` -> exit 0
  - `python3 scripts/lint_plugin.py` -> exit 0 sin avisos nuevos de rutas citadas
  - lectura: `commands/setup.md` 5-sexies enumera los pasos 1-7 de la spec, deja explícito que NO ejecuta `build_view` ni reinicia contenedores, y cita `<stack>/…`

**Criterios de aceptación**

- [ ] 5-sexies invoca el script y respeta CA-13 (imprime, no ejecuta).
- [ ] Fila nueva en `CONTRACTS.md` con Puerta (el linter no avisa).
- [ ] Sin rutas ni datos personales en lo versionado.
- [ ] `interop/` regenerado y `evals/cases/command-setup.json` al día.

**Subtareas**

- [ ] Editar 5-sexies.
- [ ] Fila de la arista en `CONTRACTS.md`.
- [ ] Regenerar `interop/`.
- [ ] Casos de eval.

**Notas**: Criterio de la spec: CA-13.

---

## Fase 6 — Cierre, documentación y réplica en Linux

**Estado**: borrador · **Estimado**: 3.6h · **Real**: — · **Coste est.**: 186 € · **Tokens est.**: 431k

### T-14 — Cierre - Docs EN/ES, lint, suites y réplica en Linux

- **Descripción**: Documentación bilingüe (`docs/en/`, README y CHANGELOG EN/ES), regeneración de `interop/`, lint, evals, suites (comparando el conjunto de rojos preexistentes en Windows) y réplica en Linux (contenedor `python:3.11-slim`, normalizando CRLF de los `.sh`). Sin datos personales en lo versionado. Medir el multiplicador de revisión real para calibrar `sdd-proporcional` (anotar en `/retro`).
- **Changelog**: Documentación EN/ES y verificación completa (lint, evals, suites y réplica en Linux) de esta mejora.
- **Estado**: borrador
- **Prioridad**: Alta
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 0.90h · real —
- **Supervisión**: est. 0.23h (≈25 % IA) · real —
- **Previsión IA**: 371k in / 60k out tok · 5.68 €
- **Dependencias**: T-01..T-13
- **Tipo**: docs
- **Archivos**: `docs/README.md`, `docs/en/README.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `README.md`, `README.es.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 scripts/lint_plugin.py` -> exit 0
  - `python3 evals/check.py` -> exit 0
  - `python3 scripts/export-interop.py --check` -> exit 0
  - `python3 -m pytest -q tests agent-kits skills` -> conjunto de rojos == conjunto preexistente en Windows; 0 rojos en Linux (contenedor)
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-29-setup-statusline-polish/tasks.md` -> 0 errores / 0 avisos
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-29-setup-statusline-polish` -> exit 0

**Criterios de aceptación**

- [ ] CA-18 y CA-19 cumplidos (lint, evals, interop, suites, réplica Linux).
- [ ] Docs EN y ES actualizadas en el mismo cambio.
- [ ] Sin datos personales en ficheros versionados (`grep` de rutas de usuario y correo vacío).
- [ ] Ninguna referencia a `docs/knowledge/` como versionado.

**Subtareas**

- [ ] Docs y CHANGELOG (`changelog-sync`).
- [ ] Lint + evals + interop.
- [ ] Suites Windows (conjunto de rojos).
- [ ] Réplica Linux.

**Notas**: Criterio de la spec: CA-18, CA-19.

