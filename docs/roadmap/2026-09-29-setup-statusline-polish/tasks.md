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
| **Diseño** | [`design.md`](./design.md) (aprobado, O1; decisión de T-09) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Desbloqueo (2026-09-30).** T-09 cerró el diseño (O1, validado por el usuario): T-12 y T-13 ya están implementadas.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Estabilizar la suite (tests deterministas) | 2 | 2 | 100% | 0 / 4.8h | 0 / 0.99h | 0 / 0.25h | 0 / 475k |
| Fase 2 — Quick wins de visibilidad y puertas | 5 | 5 | 100% | 0 / 14.4h | 0 / 3.42h | 0 / 0.85h | 0 / 1639k |
| Fase 3 — `/doctor`: tope estricto de la línea kwipu | 1 | 1 | 100% | 0 / 3.6h | 0 / 0.72h | 0 / 0.18h | 0 / 345k |
| Fase 4 — ADR de diseño y `id_prefix` / `group_id` | 3 | 3 | 100% | 0 / 14.0h | 0 / 4.10h | 0 / 1.02h | 0 / 1965k |
| Fase 5 — Alta segura en `projects.yaml` | 2 | 2 | 100% | 0 / 14.4h | 0 / 4.50h | 0 / 1.12h | 0 / 2157k |
| Fase 6 — Cierre, documentación y réplica en Linux | 0 | 1 | 0% | 0 / 3.6h | 0 / 0.90h | 0 / 0.23h | 0 / 431k |
| **TOTAL** | **13** | **14** | **93%** | **0 / 54.8h** | **0 / 14.63h** | **0 / 3.66h** | **0 / 7013k** |

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
- **Archivos**: `tests/test_knowledge_find.py`, `tests/test_knowledge_index.py`, `evals/fixtures/project/docs/knowledge/`, `tests/fixtures/`, `.gitattributes` (nota fix1 #14: el corpus fijo se extrae siempre en LF)
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

**Estado**: completado · **Estimado**: 14.0h · **Real**: — · **Coste est.**: 726 € · **Tokens est.**: 1965k

### T-09 — ADR - Enmienda a ADR-018 / PAT-001 / constitución §4: alta que solo añade en `projects.yaml`

- **Descripción**: Tarea de DISEÑO previa a C-07, a cargo del agente `architect`: ADR nueva `propuesta` (enmienda a ADR-018, PAT-001 y constitución §4) que autorice SOLO AÑADIR un bloque en el `projects.yaml` del stack, con vista previa, confirmación y copia de seguridad, y que resuelva la tensión de la escritura atómica (reemplazo) sobre un fichero que el plugin no creó. Debe fijar: forma(s) de YAML reconocidas (con la muestra anonimizada de `<stack>/kwipu/config/projects.yaml`), `root` absoluta o relativa, y código de salida de «forma no reconocida». Si no se acepta, C-07 se reduce a imprimir el bloque (-8 h humanas, -3 h IA). No estaba en la evaluación (+2 h humanas, +0,5 h IA declaradas).
- **Changelog**: Nueva decisión de diseño que autoriza dar de alta el proyecto en Kwipu añadiendo un bloque, sin modificar lo existente.
- **Estado**: completado
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
  - Salida real (2026-09-30, orquestador): `design.md` → `estado: aprobado` y `opcion_elegida: "O1"` (validada por el usuario, «sí a todo»); sin placeholders `{{`; ADR-021 `propuesta` en `docs/knowledge/adr/` con su fila en el índice (memoria local, no versionada); la decisión versionada es la sección «Decisión» de `design.md`

**Criterios de aceptación**

- [x] ADR `propuesta` aceptada por el usuario antes de arrancar T-12 y T-13 (puerta).
- [x] Fija las formas de `projects.yaml` reconocidas a partir de una muestra anonimizada (sin datos personales).
- [x] Declara el contrato de escritura: solo añade, vista previa, confirmación, copia de seguridad, atómica.
- [x] Índice `docs/knowledge/README.md` actualizado (recordatorio: `docs/knowledge/` es solo local, no se versiona).

**Subtareas**

- [x] Recabar muestra anonimizada de `projects.yaml`.
- [x] Opciones de encaje con trade-offs.
- [x] Validar con el usuario.
- [x] Escribir ADR + índice.

**Notas**: Criterio de la spec: Condiciones 1 y 2 de la evaluación.

### T-10 — C-08a - `id_prefix` elegible y derivación de nombre y `group_id` (solo instalaciones nuevas)

- **Descripción**: `/setup` propone el `id_prefix` (slug de la carpeta), valida `^[a-z0-9][a-z0-9-]*$` y lo guarda en `taxonomy.json`. Decisión del usuario: el `group_id` derivado de `id_prefix` se aplica SOLO a instalaciones nuevas (sin `group_id` efectivo previo); las que ya tienen un `group_id` implícito lo conservan y reciben un aviso. La derivación vive en UN solo sitio, consumido por `knowledge-schema.py` y `graphiti.py` (hoy 33 líneas duplicadas). Un test fija que una instalación con `id_prefix` distinto de la carpeta no cambia de `group_id`. Hotspot `knowledge-schema.py`: solo esta tarea lo toca.
- **Changelog**: Los proyectos nuevos eligen su nombre (`id_prefix`) en `/setup`; los ya existentes conservan su grupo de Graphiti.
- **Estado**: completado
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

- **Evidencia**:
  RED: 16 tests `-k "CA_14 or CA_15"` fallaron con `AttributeError: module 'knowledge_schema' has no attribute 'preparar_id_prefix'` contra el código anterior · 2026-09-30
  GREEN: `pytest -q agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_capabilities.py skills/knowledge-services/scripts/test_backend_graphiti.py tests/test_graphiti_security.py` -> 432 passed, 2 subtests passed; `export-interop.py --check` -> 50 ficheros al día.
  Diseño: `knowledge-schema.py` gana `id_prefix_valido`, `proponer_id_prefix`, `instalacion_previa` y `preparar_id_prefix` (CLI `--setup-id-prefix [--id-prefix X] [--aplicar]`, JSON, exit 0/2). Nueva = sin manifiesto de Graphiti, sin backend graphiti activo y sin `group_id` explícito: `--aplicar` escribe `id_prefix` y `group_id = id_prefix` en la config; previa: solo `id_prefix`, el `group_id` sigue derivándose de la carpeta y se avisa. La derivación al cargar (bloque `group_id por defecto COMPARTIDO`) NO cambia.
  Nota: `graphiti.py` no contiene derivación de `group_id` (lo recibe ya resuelto en `cfg`); las dos copias vivas del bloque (schema y `knowledge-find.py`) siguen declaradas en `copias.json` y vigiladas por `tests/test_copias_declaradas.py` (99 passed junto a export-interop y router). Se deja como está: fusionarlas rompería la autosuficiencia del hook `SessionStart` (sin capacidad de red). `Archivos` real: `knowledge-schema.py`, su test, `capabilities.py` (texto del `setup_step`), `commands/setup.md`, `interop/**`.

**Criterios de aceptación**

- [x] CA-14: sin `id_prefix`, `/setup` propone el slug, valida la forma y lo guarda; nombre de proyecto y `group_id` de instalaciones NUEVAS lo heredan salvo sobrescritura.
- [x] Instalación con `group_id` implícito previo: lo conserva y recibe aviso (test).
- [x] Una única función de derivación consumida por `knowledge-schema.py` y `graphiti.py` (sin duplicado). DESVIACIÓN declarada (ver Evidencia): `graphiti.py` no deriva `group_id`; la única derivación viva sigue siendo el bloque replicado y vigilado por `copias.json` (schema + `knowledge-find.py`), sin copia nueva.
- [x] `id_prefix` inválido: rechaza y vuelve a preguntar; no guarda.
- [x] `interop/` regenerado.

**Subtareas**

- [x] Test rojo de compatibilidad del `group_id`.
- [x] Extraer derivación única.
- [x] Paso de `/setup` con validación.
- [x] Actualizar consumidores (`capabilities`, `knowledge-find`, `doctor`).
- [x] Regenerar `interop/`.

**Notas**: Criterio de la spec: CA-14 (+ decisión: solo instalaciones nuevas). Decisión del usuario 2026-09-29: derivación desde `id_prefix` solo en instalaciones nuevas.

### T-11 — C-08b - Avisos: renombrado con conocimiento exportado y `group_id` con episodios de otro origen

- **Descripción**: Dos avisos sin bloqueo, cada uno con test (CA-15). (1) Renombrar `id_prefix` con conocimiento ya exportado: avisa de que cambian los `knowledge_id`, no migra. (2) `group_id` con episodios de otro origen antes de la primera sincronización, decisión 2c: primero el estado local (manifiesto publicado / `outbox`), después consulta al servidor solo si responde (loopback, opt-in, con el tope de red del adaptador); sin conexión degrada a «no verificado». Se suma el aviso de T-10 (instalación con `group_id` implícito conservado).
- **Changelog**: `/setup` avisa cuando renombrar un proyecto cambia sus identificadores o cuando un grupo de Graphiti ya contiene datos de otro origen.
- **Estado**: completado
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

- **Evidencia**:
  RED: 17 tests nuevos (`-k "CA_15 or aviso"`) fallaron contra el código anterior con `AttributeError: module has no attribute 'estado_grupo'` (graphiti) y `unrecognized arguments: --avisos-grupo` (knowledge-sync) · 2026-09-30
  GREEN: `pytest -q agent-kits/shared/test_knowledge_schema.py skills/knowledge-services/scripts/test_backend_graphiti.py skills/knowledge-services/scripts/test_knowledge_sync.py -k "aviso or CA_15"` -> 27 passed; `export-interop.py --check` -> 50 ficheros al día.
  Diseño: (1) renombrar `id_prefix` con conocimiento exportado = aviso en `preparar_id_prefix` (T-10) que lee SOLO manifiestos locales (`graphiti-manifest*.json`, `manifest*.json` del `export_dir` de markdown-export); no migra. (2) `graphiti.estado_grupo(cfg, consultar_servidor)` (función OPCIONAL del contrato) + `knowledge-sync.py --avisos-grupo [--consultar-servidor]`: estado local primero (manifiesto propio -> `propio`; de otro `group_id` -> `otro_origen`), servidor solo con opt-in, solo hosts `localhost/127.0.0.1/::1`, `get_episodes` de 1 episodio con el tope de red del cliente MCP; caído/ilegible/`mode: off`/no loopback -> `no_verificado`. Siempre exit 0. La puerta CA-05 de `tests/test_graphiti_security.py` (`_FLAGS_SOLO_LECTURA`) marcó rojo la mención de `--avisos-grupo` en `commands/setup.md` (`invoca --backend sin ningun flag de solo lectura`): se añade el flag a la lista (no escribe en el grafo) y un test que lo fija -> 64 passed. `Archivos` real: además `skills/knowledge-services/backends/README.md`, `commands/setup.md`, `tests/test_graphiti_security.py` (ya declarado en T-10), `interop/**`; sin cambios en `knowledge-schema.py` respecto a T-10.

**Criterios de aceptación**

- [x] Renombrar con conocimiento ya exportado advierte del cambio de `knowledge_id` y no migra (CA-15).
- [x] `group_id` con episodios de otro origen: aviso antes de la primera sincronización; primero estado local, luego servidor si responde; sin servidor -> «no verificado» (CA-15).
- [x] Ningún aviso bloquea (exit 0); solo hay red en la consulta opt-in acotada a loopback.
- [x] Cada aviso tiene su test.

**Subtareas**

- [x] Definir el «estado local» que identifica el origen.
- [x] Aviso 1 (renombrado).
- [x] Aviso 2 (local -> servidor -> no verificado).
- [x] Enganche en `/setup` y regenerar `interop/`.

**Notas**: Criterio de la spec: CA-15 (decisión 2c).

---

## Fase 5 — Alta segura en `projects.yaml`

**Estado**: completado · **Estimado**: 14.4h · **Real**: — · **Coste est.**: 748 € · **Tokens est.**: 2157k

### T-12 — C-07a - Script de alta en `projects.yaml` (solo añade)

- **Descripción**: Script stdlib nuevo `skills/knowledge-services/scripts/kwipu-project-add.py` y sus tests. Implementa el flujo de la spec (pasos 2-7) según la forma y el contrato fijados por la ADR de T-09: reconoce formas concretas y rechaza el resto (no escribe, imprime el bloque y sale con el código documentado); homónimo con otra `root` -> conflicto; misma `root` -> no-op; si no existe: vista previa, confirmación, copia de seguridad (su fallo aborta), escritura atómica con relectura justo antes; valida `id_prefix` (`^[a-z0-9][a-z0-9-]*$`) y `root` contra inyección y `..`; comprueba que el destino es el `projects.yaml` del stack indicado; imprime los comandos de `build_view` y de reinicio sin ejecutarlos. Validación solo sobre copias en temporales; la ejecución real la lanza el usuario. Ejemplos con `<stack>/…`, sin datos personales.
- **Changelog**: Nuevo script que da de alta el proyecto en Kwipu añadiendo un bloque, con vista previa, confirmación y copia de seguridad.
- **Estado**: completado
- **Prioridad**: Alta
- **Tiempo humano**: est. 9.0h · real —
- **Tiempo IA (ejec.)**: est. 2.80h · real —
- **Supervisión**: est. 0.70h (≈25 % IA) · real —
- **Previsión IA**: 1154k in / 188k out tok · 17.66 €
- **Dependencias**: T-09 (ADR aceptada), T-11
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/kwipu-project-add.py`, `skills/knowledge-services/scripts/test_kwipu_project_add.py`, `skills/knowledge-services/references/kwipu-adapter.md`, `skills/knowledge-services/SKILL.md`, `evals/cases/skill-knowledge-services.json`, `tests/test_console_encoding.py`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 -m pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py` -> passed con CA-09..CA-13 (mismo ID en el nombre del test)
  - `python3 -m pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py -k byte_a_byte` -> passed (resto del fichero idéntico)
  - `grep -nE "subprocess|os\.system" skills/knowledge-services/scripts/kwipu-project-add.py` -> sin coincidencias (`build_view` solo dentro de cadenas impresas)

- **Evidencia**:
  RED: `pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py` falló con `FileNotFoundError` (colección: `kwipu-project-add.py` no existe) · 2026-09-30. Nota honesta: el borrador del script se escribió antes que los tests; el rojo se obtuvo retirando el script y ejecutando la suite completa, y después se ajustaron 3 tests (`--nombre=-x` por argparse, ASCII en nombres de test, mutante del prefijo) y un bug real que el test destapó (`_crear_copia` borraba la copia con el fichero aún abierto: `PermissionError` en Windows).
  GREEN: `pytest -q skills/knowledge-services/scripts/test_kwipu_project_add.py` -> 96 passed, 2 skipped (enlaces simbólicos: sin privilegio en Windows; corren en Linux). `-k byte_a_byte` -> 8 passed (LF, CRLF, sin EOL final, sin hijos, comentario, sangría 4, claves entre comillas). `grep -nE "subprocess|os\.system" skills/knowledge-services/scripts/kwipu-project-add.py` -> sin coincidencias (exit 1). Cobertura del script (coverage.py, todo el fichero es diff): 96 %. `lint_plugin` 0 errores; `evals/check` 0 errores (145 casos); `test_graphiti_security` + `test_skill_size` 85 passed; `skills/knowledge-services` + `test_console_encoding` 835 passed, 3 skipped.
  Diseño O1 tal cual: solo añade (`O_APPEND`, un solo `write`, relectura, `ftruncate` al tamaño previo si algo no cuadra); comprobaciones de fichero regular, sin enlaces ni `nlink > 1`, misma identidad y `sha256` que la vista previa; copia `projects.yaml.bak-<AAAAMMDDTHHMMSSZ>` con `O_EXCL` y sufijo `-N`; exit 0/1/2/3/4; nombre = `id_prefix`; `root` = `export_dir` relativa a `kwipu/config/` (debe quedar dentro del proyecto; se crea si no existe); no importa `subprocess`. Ninguna prueba toca un `projects.yaml` real (todo en `tmp_path`, YAML sintéticos + la muestra anonimizada del diseño).
  Réplica en Linux (`python:3.11-slim`, `-m 2g`, `.sh` en LF, `git init`): `test_kwipu_project_add.py` -> 98 passed (los 2 tests de enlaces corren) como root y como usuario no root; cobertura del script 97 %. Sacó a la luz `tests/test_console_encoding.py` (410 passed tras el arreglo): el script imprime no ASCII y exige su modo de arranque en `MODOS` (taxonomía inválida -> exit 2 con tilde); hasta que el script estuvo versionado el test no lo veía en Windows.

**Criterios de aceptación**

- [x] CA-09: YAML reconocido sin el proyecto + confirmación -> copia de seguridad, exactamente un bloque añadido con `root` = `export_dir`, resto byte a byte igual.
- [x] CA-10: mismo proyecto y `root` -> no cambia nada y lo dice.
- [x] CA-11: forma no reconocida -> no escribe, imprime el bloque, exit distinto de 0 documentado.
- [x] CA-12: homónimo con otra `root` -> no escribe, muestra el conflicto, pide otro nombre.
- [x] CA-13: sin confirmación o con fallo de la copia -> no escribe; no ejecuta `build_view` ni reinicia contenedores.
- [x] Entradas inyectadas (saltos de línea, `:`, `#`, comillas, `..`) rechazadas con test.

**Subtareas**

- [x] Reconocedor de formas (según la ADR).
- [x] Validaciones de `id_prefix` y `root`.
- [x] Copia + escritura atómica + relectura.
- [x] Tests de mutantes (nunca modificar ni borrar entradas).
- [x] Referencias en la skill.

**Notas**: Criterio de la spec: CA-09..CA-13.

### T-13 — C-07b - Enganche en `/setup` 5-sexies

- **Descripción**: `/setup` 5-sexies propone el `id_prefix` (T-10), invoca el script de alta con el `export_dir` de `taxonomy.json`, muestra la vista previa, pide confirmación y muestra los comandos de `build_view` y de reinicio que debe ejecutar el usuario (no los ejecuta). Degrada con aviso sin `python3`. Añade a `docs/agents/CONTRACTS.md` la arista nueva `/setup` -> script de alta.
- **Changelog**: `/setup` ofrece dar de alta el proyecto en Kwipu con confirmación y sin tocar lo ya existente.
- **Estado**: completado
- **Prioridad**: Media
- **Tiempo humano**: est. 5.4h · real —
- **Tiempo IA (ejec.)**: est. 1.70h · real —
- **Supervisión**: est. 0.42h (≈25 % IA) · real —
- **Previsión IA**: 701k in / 114k out tok · 10.72 €
- **Dependencias**: T-12
- **Tipo**: docs
- **Archivos**: `commands/setup.md`, `docs/agents/CONTRACTS.md`, `skills/knowledge-services/SKILL.md`, `docs/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `evals/cases/command-setup.json`, `interop/**`
- **Cubre (tests)**: — (sin UI)
- **Verificación**:
  - `python3 scripts/export-interop.py --check` -> exit 0
  - `python3 scripts/lint_plugin.py` -> exit 0 sin avisos nuevos de rutas citadas
  - lectura: `commands/setup.md` 5-sexies enumera los pasos 1-7 de la spec, deja explícito que NO ejecuta `build_view` ni reinicia contenedores, y cita `<stack>/…`

- **Evidencia**:
  Verificación: `python3 scripts/export-interop.py --check` -> `50 ficheros al día` (exit 0, tras regenerar y revertir los cambios solo de fin de línea de `.agents/plugins/marketplace.json` y `.codex-plugin/plugin.json`); `python3 scripts/lint_plugin.py` -> 0 errores, 3 avisos (los de «nombre genérico» previos; el aviso de ruta citada que apareció al añadir la fila a `docs/README.md` se corrigió citando la ruta completa); `python3 evals/check.py` -> 0 errores (146 casos, +1 positivo `setup-alta-kwipu`); `pytest -q tests/test_graphiti_security.py tests/test_export_interop.py tests/test_skill_size.py tests/test_lint_plugin.py` -> 109 passed (la puerta CA-05 no marca el script nuevo: la mención de `commands/setup.md` es `kwipu-project-add.py`, no `knowledge-sync.py --backend graphiti`). Lectura: `commands/setup.md` 5-sexies enumera los pasos 1-7 de la spec (nombre/`root` -> vista previa -> exit 0/4/3/2 -> confirmación -> `--apply --esperado` con copia -> comandos impresos -> degradación sin `python3`), dice explícitamente que NO ejecuta `build_view` ni reinicia contenedores, y cita `<stack>/…` (la ruta no se guarda en `taxonomy.json`). Fila E25 nueva en `CONTRACTS.md` (E20 en la rama; renumerada a E25 al integrar master, que ya usaba E20-E24) con su Puerta (`test_kwipu_project_add.py`). Fallos de la suite en Windows fuera de alcance y previos a este cambio: `test_confluence_scope::test_hook_still_marks_pending_for_regular_docs` y `test_hooks_shell::test_mark_docs_pending_marca_con_docs_y_no_con_security_scan` (verificado con `git stash`).

**Criterios de aceptación**

- [x] 5-sexies invoca el script y respeta CA-13 (imprime, no ejecuta).
- [x] Fila nueva en `CONTRACTS.md` con Puerta (el linter no avisa).
- [x] Sin rutas ni datos personales en lo versionado.
- [x] `interop/` regenerado y `evals/cases/command-setup.json` al día.

**Subtareas**

- [x] Editar 5-sexies.
- [x] Fila de la arista en `CONTRACTS.md`.
- [x] Regenerar `interop/`.
- [x] Casos de eval.

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


## Nota del orquestador — cierre de las Fases 1-3 (2026-09-30)

- **Medición.** El marcador `setup-statusline-polish/F1-F3` duró 1h 1m de reloj. El meter degradó (`fuente: estimado`, sin transcripciones legibles desde este worktree), así que no hay tokens ni € medidos para estas fases.
- **Cobertura (riesgo `medio`).** El gate de fichero entero (`coverage-gate.py --changed-only --base origin/master --min 80`) da 52,91 %: mide los ficheros enteros que toca el diff y no ve los CLI lanzados como subproceso. La cobertura de las **líneas añadidas** por el diff es 91,1 % (`doctor.py` 16/18, `progress-report.py` 33/39, `build_dashboard.py` 19/20, `coverage-gate.py` 24/24). **Decisión:** para riesgo medio se acepta la medida sobre las líneas del diff. Queda como mejora de `sdd-proporcional` (C-04): que el perfil de rigor defina la cobertura de riesgo medio sobre las líneas del diff y que `coverage-gate.py` la calcule.
- **`scope-check`.** Sale con exit 1 por ficheros que no son del implementer: los artefactos de la cadena (`spec.md`, `evaluation.md`, `improvement-plan.md`, `docs/roadmap/README.md`). Los dos manifiestos que marcaba (`.agents/plugins/marketplace.json` y `.codex-plugin/plugin.json`) no tienen diff frente a `origin/master`, así que era ruido de la base. Los 49 ficheros del implementer están en alcance.
- **Linux.** La pasada completa se repite en el cierre (T-14), después de integrar `origin/master`, que ya incluye el PR #15.

## Revisión de dos lentes — intento 1: T-01..T-13 — 18 gaps (0 Critical, 7 Important, 11 Minor), lentes A+B+C (riesgo `medio`: A+B más C, porque T-12 escribe en la configuración del stack del usuario), rango `5a08d45...98a8506`

Lo que ya queda verificado, por lente:

- **Lente A.** CA-01…CA-16 ✓ con la evidencia relanzada (CA-08 con una sola ejecución). T-12 cumple el diseño O1: solo añade, vista previa con `sha256`, copia `.bak` con `O_EXCL`, exits 0-4 y comandos impresos pero no ejecutados. Interop al día. Cobertura de las **líneas del diff 94,0 %** (612/651). Puertas: lint 0 errores, evals 0, interop 50, `ledger-lint` 0/0. CA-18/CA-19 quedan para T-14.
- **Lente B** (Windows y Linux):
  - kwipu acepta y rechaza las formas previstas, con idempotencia, `--esperado` obsoleto, CRLF y stack vía UNC en otra unidad.
  - Las instalaciones antiguas no cambian de grupo.
  - Statusline: activas, marcador, locale de coma y `jobs` ✓.
  - `coverage-gate` distingue `disponible`/`ausente`/`no_verificado` ✓.
  - El dashboard lee las 20 evaluaciones reales ✓.
  - El hilo daemon de `/doctor` no escribe nada (AST) ✓.
- **Lente C** (Linux sin root, junction real en Windows):
  - No hay `subprocess` ni `os.system`, y no se siguen enlaces al leer.
  - El TOCTOU entre la vista previa y `--apply` está cubierto con `sha256` + `fstat`.
  - La copia `.bak` nunca pisa (hay 3 symlinks plantados que no se siguen).
  - Probé la inyección de YAML por nombre, `root` y `export_dir` con `#`, `: `, anclas, comillas, U+2028 y U+202E: no crea claves nuevas.
  - `--avisos-grupo` es opt-in y no manda credenciales.
  - El hilo daemon no deja efectos.
  - No hay datos personales.

| # | Grado | Gap | Tarea | Corrección | Evidencia | Lente |
|---|---|---|---|---|---|---|
| 1 | **Important** | La reversión trunca a `len(previo)` **por ruta**, sin comprobar la identidad del fichero ni que lo que sobra sea exactamente su bloque (`kwipu-project-add.py:341,364-369`). Así borra bytes ajenos, y eso choca con la constitución §4 y con `design.md` §4.3. Escenarios dentro del modelo: dos `/setup` simultáneos (el truncado de B borra el bloque de A, que ya se había dado por «añadido»); un editor que guarda por rename entre el `write` y la relectura (se pierde la edición); otro escritor que añade después. CWE-367. **Arbitraje:** truncar solo si (a) el descriptor abierto conserva la identidad previa (`fstat`, `samestat`), (b) el tamaño es exactamente `len(previo)+len(bloque)` y (c) los bytes a partir de `len(previo)` son byte a byte el bloque propio. El truncado se hace por el descriptor, nunca por ruta. Si no se cumple, NO toca el fichero: sale con exit 1, «el fichero cambió durante la escritura: revísalo a mano (copia en `<bak>`)», y nombra el estado real (su bloque presente o no). Tests: dos `/setup` intercalados (los dos bloques quedan y ninguno se borra), rename entre `write` y relectura, y otro escritor que añade | T-12 | corregido (fix1): `escribir_anadiendo` abre `O_RDWR\|O_APPEND\|O_NOFOLLOW` y `_verificar_o_revertir` decide SOLO por el descriptor. Trunca por `ftruncate(fd)` unicamente si (a) identidad descriptor = lectura previa = ruta (la ruta no se reemplazó), (b) tamaño exacto `len(previo)+len(lo propio)`, (c) cola byte a byte = lo que ESTE proceso escribió y prefijo igual (condición adicional, más estricta). Si no: no toca nada, exit 1, «el fichero cambió durante la escritura: revísalo a mano (copia en <bak>) · tu bloque SÍ/NO está en el fichero» y `bloque_presente` en el JSON. Escritura corta: «lo propio» son los `n` bytes que informó `write` (se revierten solo esos). | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_1_dos_setup_intercalados_no_borran_ningun_bloque` → `AssertionError: el bloque de B (ya añadido) se borró`; `test_fix1_1_otro_escritor_que_anade_despues_no_se_borra` → `AssertionError: un byte ajeno borrado`; `test_fix1_1_editor_que_guarda_por_rename…` skip en Windows (no se reemplaza un fichero abierto), en Linux (`python:3.11-slim`, usuario no root) contra `95932dc` → `AssertionError: se perdió la edición del usuario`. GREEN: `test_kwipu_project_add.py` 138 passed, 4 skipped (Windows); Linux 5/5 de rename/enlaces y suites de la iniciativa 1414 passed, 1 skipped, 1 failed (`test_progress_line_ruta_windows_con_backslashes`, que también falla en `95932dc`). **Mutante** (copia aislada, `PYTHONDONTWRITEBYTECODE=1`): condición de truncado `st_size == base+len(propio) and cola == propio` → `cola.startswith(propio)` ⇒ MUERE: `1 failed, 137 passed` (`test_fix1_1_otro_escritor_que_anade_despues_no_se_borra`). | C |
| 2 | **Important** | La clave del proyecto se emite sin comillas y `NOMBRE_RE` admite nombres que YAML no lee como texto: `2024`, `yes`, `on`, `true`, `null`, `0x1f`, `0b101` (`kwipu-project-add.py:42,281`). El `id_prefix` sale del slug de la carpeta, así que una carpeta `2048` lo produce sin que el usuario haga nada. Kwipu lee entonces `2024` como int y `build_view` aborta la vista entera. **Arbitraje:** un nombre válido empieza por letra y no es una palabra reservada de YAML 1.1 (`y/n/yes/no/on/off/true/false/null/~`, sin distinguir mayúsculas). `validar_nombre` rechaza el resto con exit 2 y propone una alternativa. `proponer_id_prefix` (T-10) nunca propone uno inválido: antepone `p-` si hace falta. Tests: todos los literales anteriores + la carpeta `2048` | T-12/T-10 | corregido (fix1): `kwipu-project-add.py` `NOMBRE_RE = ^[a-z][a-z0-9-]*$` + `YAML_RESERVADAS` (y/n/yes/no/on/off/true/false/null/~, sin mayúsculas); `validar_nombre` sale con 2 y propone `--nombre p-<slug>`. `knowledge-schema.proponer_id_prefix` antepone `p-` si el slug no es texto YAML (`2048` → `p-2048`). `id_prefix_valido` no cambia (el `id_prefix` sigue admitiendo dígitos; solo la clave de `projects.yaml` los rechaza). | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_2_nombre_que_yaml_no_lee_como_texto_se_rechaza[2024…null]` (14) → `assert (0 == 2)`; `test_fix1_2_carpeta_2048_sin_id_prefix…` → exit 0; `test_fix1_2_la_propuesta_siempre_es_texto_en_yaml` → `assert '2048' == 'p-2048'` (y 0x1f, yes, on, null, n, 2024). GREEN en las dos suites. | B |
| 3 | **Important** | En una instalación nueva, `proponer_id_prefix` cae a `"ca"` y lo escribe como `group_id` explícito. Dos proyectos cuya carpeta tiene nombre no ASCII (`知識`, `проект`) comparten así el grupo remoto y se mezcla su memoria, lo que prohíbe `_con_group_id_por_defecto` (gaps #3/#23) (`knowledge-schema.py:932,1034`). **Arbitraje:** el valor por defecto sin slug ASCII pasa a `p-<8 hex del sha256 de la ruta absoluta normalizada del proyecto>`, determinista y distinto por proyecto. Se muestra al usuario, que puede cambiarlo. Tests: `知識` y `проект` dan valores distintos y estables, y ninguno es `ca` | T-10 | corregido (fix1): `proponer_id_prefix` sin slug ASCII → `p-<8 hex del sha256 de normcase(realpath(root))>`, determinista y distinto por ruta; `preparar_id_prefix` lo muestra como `propuesta` y, en instalación nueva, lo escribe como `group_id` (el usuario puede cambiarlo con `--id-prefix`). | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_3_carpetas_no_ascii_dan_group_id_distintos…` y `test_fix1_3_mismo_nombre_no_ascii_en_rutas_distintas…` → `assert ('ca' != 'ca')`; `test_CA_14_carpeta_sin_alfanumericos_no_propone_ca` → `assert 'ca' != 'ca'`. GREEN: `test_knowledge_schema.py` 146 passed. | B |
| 4 | **Important** | El paso de avisos de `/setup` llama a `knowledge-sync.py` por una ruta relativa del repo (`python3 skills/knowledge-services/scripts/…`, `commands/setup.md:84` y su copia en interop), sin el `find` de la regla 5. En un proyecto consumidor no existe y el aviso CA-15 no aparece nunca. Además fija `--backend graphiti`, cuando el id del backend lo elige el proyecto. **Arbitraje:** resolver el script con el `find` de seis raíces (regla 5, excluyendo `*/.claude/jobs/*`). `knowledge-sync.py --avisos-grupo` sin `--backend` recorre todos los backends de `type: graphiti` declarados y sale siempre con exit 0. Test de que `setup.md` no contiene ninguna invocación `python3 skills/…` + el test de la iteración | T-11 | corregido (fix1): `/setup` localiza `knowledge-sync.py` con el `find` de seis raíces (con `! -path '*/.claude/jobs/*'`) y lo llama como `"$KSYNC" --avisos-grupo [--consultar-servidor]`, sin `--backend`. `knowledge-sync.py`: `--backend` deja de ser `required`; sin él solo vale `--avisos-grupo` (resto → exit 2) y recorre TODOS los backends declarados cuyo adaptador define `estado_grupo` (hoy solo el de `type: graphiti`; el núcleo sigue sin nombrar backends, gap #77), siempre exit 0. Interop regenerado. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_4_avisos_grupo_sin_backend_*` (2) y `test_fix1_4_sin_backend_fuera_de_avisos_grupo…` → `SystemExit: 2` (`the following arguments are required: --backend`); `test_fix1_4_setup_no_invoca_scripts_por_ruta_relativa_del_repo` → `match='python3 skills/'`. GREEN: `test_knowledge_sync.py` 41 passed; `export-interop --check` 50 al día. | A + B |
| 5 | **Important** | La fila de `knowledge-services` en `docs/README.md` ya incluye el alta en Kwipu, pero su espejo `docs/en/README.md:107` no. Incumple la constitución §3 («en el mismo cambio»). **Arbitraje:** espejo EN en este cambio, más un test (o una comprobación de lint) de que la fila EN nombra `kwipu-project-add.py` | T-13 | corregido (fix1): la fila `knowledge-services` de `docs/en/README.md` nombra el alta en `projects.yaml` (`kwipu-project-add.py`, solo añade, vista previa, `sha256`, `.bak`, exit 0-4, sin `build_view`), espejo de la ES. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_5_la_fila_en_del_readme_nombra_el_alta_en_kwipu` → `AssertionError: docs/en/README.md`. GREEN. | A |
| 6 | **Important** | El diff contradice una ADR `aceptada`: ADR-018 §2 dice «No hay `projects.yaml`». Su enmienda, ADR-021, sigue `propuesta`; ADR-018 no tiene la nota «enmendada por ADR-021»; y no existe la candidata PAT-001 v2. **Arbitraje (orquestador, memoria local):** `knowledge-curator` pasa ADR-021 a `aceptada` (la validó el usuario con «sí a todo», 2026-09-30), añade la nota de enmienda a ADR-018 y aprueba PAT-001 v2 (excepción: solo `kwipu-project-add.py` desde `/setup`). Como `docs/knowledge/` es solo local, la decisión versionada sigue siendo la sección «Decisión» de `design.md` | T-09 | corregido (orquestador, curación local 2026-09-30): ADR-021 `aceptada (validada: usuario, 2026-09-30)`; ADR-018 con la nota «enmendada por ADR-021»; PAT-001 v2 aprobada por `knowledge-curator` (excepción: solo `kwipu-project-add.py` desde `/setup` 5-sexies añade un bloque marcado) | `curator-gate.py --decision approve --category PATTERN` → `errores: []`, exit 0; `knowledge-index.py` → `8 entrada(s), sin errores`; memoria local (`docs/knowledge/` no se versiona): la decisión versionada es la sección «Decisión» de `design.md` | A |
| 7 | **Important** | Si falla el `fsync` del append, o la relectura lanza `OSError`, la excepción se salta la verificación y el truncado. El bloque queda escrito, pero se informa `escrito: false`, estado `nuevo` y exit 1, y el siguiente `/setup` dice `presente` (`kwipu-project-add.py:358-359,498-499`). Reporta un estado falso. **Arbitraje:** tras cualquier `OSError` posterior al `write`, se ejecuta la misma verificación y el truncado seguro de #1, y se informa el estado real. Test con `fsync` que lanza EIO | T-12 | corregido (fix1): el `write` y el `fsync` van dentro de un `try`; cualquier `OSError` posterior al `write` pasa por la misma verificación y el truncado seguro de #1, y se informa el estado real (`escrito` = `bloque_presente`). Si no se puede truncar, «no se pudo revertir… tu bloque SÍ está» con `escrito: true`. Un `OSError` antes del `write` (abrir, `fstat`) sigue siendo «no se ha tocado». | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_7_fsync_con_eio_tras_escribir_informa_el_estado_real` → `AssertionError: el bloque quedó escrito`; `test_fix1_7_estado_real_si_no_se_puede_revertir` → falla (sin `bloque_presente`, `escrito: false` con el bloque en el fichero). GREEN. | B |
| 8 | Minor | La consulta «solo loopback» de `--avisos-grupo` solo valida el endpoint inicial. Las redirecciones 307/308 se revalidan con `allow_remote=False`, que admite redes privadas (`graphiti.py:2027-2033,400`). Un 307 hacia `172.17.0.2` recibe el `initialize` y el `get_episodes` con el `group_id`. CWE-918. **Arbitraje:** en el modo «solo loopback», cada salto se revalida contra loopback; un redirect fuera de loopback da «no verificado». Test con dos servidores | T-11 | corregido (fix1): `_validar_host(..., solo_loopback=True)` exige loopback en TODAS las IPs; `_post_json`/`ClienteMCP` lo propagan a cada salto 307/308 y `estado_grupo` lo usa. Un redirect fuera de loopback lanza `HostNoPermitido` → «no verificado». El resto de llamadas no cambia. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_8_redireccion_fuera_de_loopback_da_no_verificado_y_no_envia_nada` (dos servidores; IP privada 10.1.2.3 por caché DNS, conexión desviada a un servidor local que cuenta) → `Lists differ: [b'{"jsonrpc": "2.0", "id": 1, "method": …'] != []` (el destino privado recibió el `initialize`). GREEN: `test_backend_graphiti.py` 209 passed. | C |
| 9 | Minor | El texto de `projects.yaml` sale crudo a la terminal en modo texto: claves entre comillas con ESC, BEL o C1 en los mensajes de conflicto o duplicado (`kwipu-project-add.py:228,306,310,444`). `validar_root` (`:260`) solo filtra C0: con U+202E el bloque que se muestra para confirmar se ve invertido, y con NEL (U+0085) PyYAML pliega el valor. CWE-150/451. **Arbitraje:** todo texto que venga de `projects.yaml` o de la entrada se escapa en modo texto con el helper de escapado del plugin. `validar_root` rechaza también `Cc`/`Cf`/`Zl`/`Zp` (la regla de `case_schema.validar_config`, #153/#173). Tests con los literales | T-12 | corregido (fix1): `_escapar` (mismo criterio que `_sanear_detalle` —C0, C1, ESC, bidi, separadores— pero sin recortar y con el escape visible, `\x1b`/`\u202e`, porque se muestran rutas que hay que poder copiar) en todo el modo texto: mensaje, destino, copia, comandos y errores de uso. `validar_root` rechaza Cc/Cf/Zl/Zp (salvo ZWNJ/ZWJ, regla de `case_schema`, #153/#173). Desviación: no se reutiliza `_sanear_detalle` tal cual porque recorta a 200 y cambia caracteres por espacios, lo que falsearía la ruta de la copia. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_9_validar_root_rechaza_cc_cf_zl_zp[U+202E, U+0085, U+2028, U+2029, U+200B, U+FEFF, U+00AD, U+009B]` → `DID NOT RAISE Uso`; `test_fix1_9_texto_de_projects_yaml_se_escapa_en_la_terminal` → `assert ('\x1b' not in 'estado: no-…')`; `test_fix1_9_la_ruta_de_la_entrada_se_escapa…` → U+202E crudo. GREEN. | C (A) |
| 10 | Minor | `nlink == 1` solo se comprueba al leer: el `fstat` previo al `write` (`:353-357`) no lo repite, y la escritura se abre sin `O_NOFOLLOW`. Un enlace duro creado en medio también recibe el bloque. CWE-367. **Arbitraje:** abrir con `O_NOFOLLOW` y repetir `nlink == 1` junto con la identidad en el `fstat` previo al `write`. Test | T-12 | corregido (fix1): la escritura se abre con `O_NOFOLLOW` (donde existe) y el `fstat` previo al `write` repite identidad, tamaño, `nlink == 1` y fichero regular; el éxito también exige `nlink == 1`. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_10_enlace_duro_creado_antes_de_escribir_no_recibe_el_bloque` → el fichero y el enlace recibieron `  # x`. `test_fix1_10_la_escritura_no_sigue_un_enlace_simbolico` (identidad forzada a «igual») solo corre con `O_NOFOLLOW`: en Linux contra `95932dc` → `assert True is False` (escribió a través del enlace). GREEN en Windows y Linux. | C |
| 11 | Minor | Una clave `root` escrita de otra forma en un proyecto existente (`"root":` entre comillas o `root :`) no se reconoce: su `root` queda `None` y el conflicto por misma `root` no salta, así que acaba habiendo un segundo proyecto sobre la misma carpeta (`kwipu-project-add.py:240`). **Arbitraje:** reconocer `root`, `"root"` y `'root'` con espacios opcionales antes de `:`. Cualquier otra forma de la clave `root` dentro de un proyecto es **forma no reconocida** (exit 3). Tests | T-12 | corregido (fix1): `_ROOT_CLAVE_RE` reconoce `root`, `"root"` y `'root'` con espacios antes de `:`; `_ROOT_DUDOSA_RE` convierte en forma no reconocida (exit 3) tabulador antes de `:`, `root:` pegado al valor, clave compleja `?` y clave entre comillas con escapes. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_11_clave_root_con_comillas_o_espacios_se_reconoce` (5) → exit 0 (escribía un segundo proyecto sobre la misma carpeta) en vez de 4; `test_fix1_11_otra_forma_de_la_clave_root_es_forma_no_reconocida` (5) → exit 0 en vez de 3. GREEN. | B (C) |
| 12 | Minor | El `find` de `KPA` en 5-sexies no excluye `*/.claude/jobs/*` (`commands/setup.md:~94`), así que reintroduce el patrón que corrige T-06. **Arbitraje:** añadir `! -path '*/.claude/jobs/*'`, más un test de que todo `find` de `commands/setup.md` lo lleva | T-13 | corregido (fix1): los cuatro `find` de seis raíces de `commands/setup.md` (los dos `SHAREDKIT`, `KPA` y el nuevo `KSYNC`) llevan `! -path '*/.claude/jobs/*'`; interop regenerado. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_12_todo_find_de_setup_excluye_los_temporales_de_jobs` → lista con los `find` sin la exclusión (`SHAREDKIT=…`, `KPA=…`). GREEN (2 passed con el de 5-bis). | A (B) |
| 13 | Minor | `--apply` sin `--esperado` sale con exit 1 (E/S), cuando el diseño reserva el 2 para uso (`kwipu-project-add.py:485-487`; test en `:348`; `design.md:171-172`). **Arbitraje:** exit 2 con mensaje de uso; ajustar el test | T-12 | corregido (fix1): `--apply` sin `--esperado` → exit 2 con «--apply exige --esperado <sha256 de la vista previa>»; hash distinto sigue en exit 1. Test `test_ca13_sin_esperado_o_con_hash_distinto` ajustado y docstring de códigos actualizado. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_13_apply_sin_esperado_es_error_de_uso` → `assert (1 == 2)`. GREEN. | A |
| 14 | Minor | CA-17 falla en Windows: el corpus fijo se extrae con CRLF (`core.autocrlf=true`) y `test_ca04_show_adr012` falla. La evidencia de T-02 («0 failed») no se reproduce en un clon de Windows. **Arbitraje:** `.gitattributes` con `tests/fixtures/knowledge-corpus/** text eol=lf`, y el test normaliza al leer | T-02 | corregido (fix1): `.gitattributes` con `tests/fixtures/knowledge-corpus/** text eol=lf` (el corpus son 27 `.md`); la fixture `real` copia el corpus normalizando a LF y CA-17 lee lo esperado normalizado (`_leer_en_lf`). `.gitattributes` añadido al `Archivos` de T-02. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres` → `AssertionError: assert '---\n\nid: A…' == '---\nid: ADR…'` (corpus extraído con CRLF). GREEN en esa misma copia CRLF con el test nuevo: 1 passed. Quedan rojos en Windows `test_show_imprime_la_entrada_completa_tal_cual` y `test_show_json_envuelve…`: previos a fix1 (su fixture `proyecto` escribe con `write_text`), fuera de esta fila. | A |
| 15 | Minor | Ledger y cadena desfasados: la fila TOTAL dice 11/14 cuando las fases suman 13; «Diseño: n/a» sigue en la cabecera; el aviso «Bloqueo por ADR» sigue puesto; la Fase 4 figura como «borrador» con 3/3 hechas; `improvement-plan.md:22` dice «borrador». **Arbitraje (orquestador):** corregirlo y dejar la cabecera del ledger enlazada a `design.md` | — | corregido (orquestador, `95932dc`): cabecera enlazada a `design.md`, aviso de bloqueo sustituido por el desbloqueo, TOTAL 13/14, estados de fase al día, plan `en-progreso` | `ledger-lint` 0/0 | A |
| 16 | Minor | El modelo de amenazas de la spec dice «escritura atómica (temporal + reemplazo)», que es la O2 descartada (`spec.md:100`). **Arbitraje (orquestador):** sincronizar con O1 (bloque añadido al final, copia de seguridad y truncado seguro) | — | corregido (orquestador, `95932dc`): el modelo de amenazas y la escala de la spec describen O1 (bloque añadido al final, confirmación atada al `sha256`, truncado que solo retira el bloque propio) | lectura de `spec.md` §Modelo de amenaza | A |
| 17 | Minor | Constitución §1 (TDD): en T-12 el script se escribió antes que los tests (declarado), y el RED salió de retirar el script, que da un error de colección y no un rojo de comportamiento. **Arbitraje:** no se reescribe la historia. Lo recoge la retro como lección; los tests de fix1 sí llevan un RED de comportamiento | T-12 | diferido (backlog #17: lección para la retro; los tests de fix1 llevan RED de comportamiento) | — | A |
| 18 | Minor | `knowledge-schema.py:1036` abre el temporal con un nombre predecible (`.<pid>.tmp`) y sigue enlaces. Es config del propio proyecto, dentro del modelo con poco impacto. **Arbitraje:** temporal con `O_EXCL` y nombre aleatorio (`mkstemp` en el mismo directorio), reemplazo y retirada si falla | T-10 | corregido (fix1): `preparar_id_prefix` escribe en `tempfile.mkstemp(prefix='.taxonomy.', suffix='.tmp', dir=…)` (nombre aleatorio, `O_EXCL`, no sigue enlaces), conserva los permisos del fichero reemplazado (`mkstemp` crea 0600), `os.replace` y retira el temporal si falla. | RED contra `95932dc` (copia extraida con `git -c core.autocrlf=true archive`, tests nuevos copiados encima, 2026-09-30): `test_fix1_18_temporal_no_predecible_ni_sigue_lo_plantado` (directorio plantado en `taxonomy.json.<pid>.tmp`) → `{'ok': False, …}`. GREEN. | C (B) |

**Decisión del orquestador (2026-09-30)**
- Se hace una ronda `fix1` (implementer, marcador `setup-statusline-polish/fix1`) con #1-#5, #7-#14 y #18.
- El orquestador corrige #6 (curación local), #15 y #16. #17 va a la retro.
- Después, intento 2 con las lentes B y C (y A sobre la documentación), dentro del tope de 3.


**Nota del orquestador (2026-09-30) sobre fix1:** se aceptan las tres desviaciones declaradas: en #1 el prefijo también debe ser igual antes de truncar, que es más estricto; en #4 se recorren los adaptadores que definen `estado_grupo`, porque el núcleo no puede nombrar un backend (gap #77); en #9 se usa un `_escapar` sin recortar. `scope-check --base 5a08d45` marca como fuera de alcance cinco artefactos de la cadena (`design.md`, `evaluation.md`, `improvement-plan.md`, `spec.md` y `docs/roadmap/README.md`), todos editados por el orquestador en #15/#16: se aceptan como excepción declarada.

## Revisión de dos lentes — intento 2: fix1 — #1-#5, #7-#14 y #18 CERRADOS; 6 gaps NUEVOS (0 Critical, 2 Important, 4 Minor), lentes B+C, rango `95932dc...a8148b9` (fix1)

Qué verificaron las lentes:

- **Lente B.** Con un probe propio: 53 comprobaciones en Windows y en UNC, 58 en Linux sin root.
  - #1 cerrado en los tres casos: dos `/setup` intercalados, rename entre el `write` y la relectura, y otro escritor.
  - Cerrados también #2, #3, #4 (con 7 casos de `--avisos-grupo`), #7, #11 y #13.
  - El camino normal (vista previa → `--apply` → re-pasada idempotente, también con CRLF, sin EOL final y en UNC) no tiene regresiones.
  - Suites en Linux: 1530 passed; el único rojo es el de entorno de master.
- **Lente C.** En Linux sin root:
  - Cerrados #1, #8 (se revalida cada salto), #9 (recorrido exhaustivo de los 0x110000 code points por `_escapar`), #10 (enlace duro y ELOOP) y #18 (55 symlinks plantados que no se siguen).
  - Sin `--consultar-servidor` no hay red.
  - No hay datos personales.

**Fusión:** B-G1 = C-N1 → #19; la nota fuera de lente de C sobre `validar_root` → #20; C-N2 → #21; C-N3 → #22; B-G2 → #23; B-G3 → #24.

| # | Grado | Gap | Tarea | Corrección | Evidencia | Lente |
|---|---|---|---|---|---|---|
| 19 | **Important** | Si el `write` lanza, se asume que pudo escribir el bloque entero (`propios=[b"", bloque]`), así que se trunca el bloque idéntico de otro `/setup` que ya salió con «añadido» (`kwipu-project-add.py:433,453-459`). Se borran bytes ajenos y B informa de un estado falso. Reproducido en Windows, UNC y Linux: A pasa su `fstat`, B completa y sale con exit 0, y entonces el `write` de A lanza ENOSPC. CWE-367. **Arbitraje:** con `n is None`, `propios=[b""]` (en POSIX, un `write` que falla no escribió nada). Si el `write` lanzó, nunca se trunca. Test con el escenario literal | T-12 | corregido (fix2): `_verificar_o_revertir` con `n is None` (el `write` lanzó) usa `propios=[b]`: nunca trunca. Si al final queda un bloque idéntico (el de otro `/setup`), no se toca: exit 1 «el fichero cambió durante la escritura … · tu bloque SÍ está» y `bloque_presente: true`; si no escribió nada, «no se llegó a añadir nada». | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_19_write_que_lanza_no_trunca_el_bloque_identico_de_otro_setup` (A pasa `fstat`; B completa con el mismo bloque y sale `ok`; después `_os_write` de A lanza ENOSPC) → `AssertionError: se truncó el bloque que B ya había dado por añadido` (`0 == 1` bloques). GREEN: `test_kwipu_project_add.py` 147 passed, 4 skipped. **Mutante** (copia aislada, `PYTHONDONTWRITEBYTECODE=1`): volver a `[b, bloque_bytes]` ⇒ MUERE: `test_fix2_19_…` falla (sin mutante la copia solo falla en `test_fix1_5`, que necesita `docs/`, fuera de la copia). | B + C |
| 20 | **Important** | `validar_root` acepta U+FFFE/U+FFFF (Cn) y sustitutos sueltos (Cs). Con los primeros, PyYAML da `ReaderError` sobre el `projects.yaml` resultante y la vista entera del stack deja de funcionar, no solo este proyecto. Con los segundos, `.encode("utf-8")` revienta al aplicar, cuando la copia ya existe. **Arbitraje:** `validar_root` rechaza también las categorías `Cn` y `Cs` (y cualquier carácter que no codifique a UTF-8 estricto). Test con los tres literales | T-12 | corregido (fix2): `_caracter_prohibido_root` rechaza también las categorías `Cn` y `Cs` y cualquier carácter que no codifique a UTF-8 estricto (`_utf8_estricto`); mensaje de `Uso` actualizado. ZWJ/ZWNJ y el texto no ASCII normal siguen valiendo. | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_20_validar_root_rechaza_cn_cs_y_no_utf8[a￾b, a￿b, a\ud800b]` → `Failed: DID NOT RAISE Uso` (3). GREEN, y `test_fix2_20_validar_root_sigue_admitiendo_texto_normal` en verde. | C (fuera de lente) |
| 21 | Minor | En `--json`, el texto que viene de `projects.yaml` sale sin escapar C1 ni bidi, porque `json.dumps` solo escapa C0 (`kwipu-project-add.py:569`). CWE-150. **Arbitraje:** `ensure_ascii=True` en la salida `--json`. Test | T-12 | corregido (fix2): la salida `--json` usa `ensure_ascii=True`: C1 y bidi salen como `\uXXXX`. | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_21_json_escapa_c1_y_bidi_de_projects_yaml` → `assert '\x9b' not in …` (la clave `x\x9b‮y` de `projects.yaml` salía cruda en `mensaje`). GREEN: salida ASCII pura y `json.loads` recupera el texto. | C |
| 22 | Minor | El recorrido de `--avisos-grupo` sin `--backend` imprime el id del backend sin sanear (`knowledge-sync.py:350`). **Arbitraje:** el id pasa por el mismo saneado que los avisos (`_sanear_causa`). Test con un ESC | T-11 | corregido (fix2): `knowledge-sync.py` imprime el id del backend de `--avisos-grupo` pasado por `_sanear_causa`. | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_22_avisos_grupo_sanea_el_id_del_backend` (id `mem\x1b[2Jx‮`) → `assert '\x1b' not in …` (el id salía crudo). GREEN: `test_knowledge_sync.py` en verde. | C |
| 23 | Minor | `commands/setup.md:96` (y sus copias en interop) sigue documentando que exit 1 significa «deshace solo lo añadido». Tras fix1 también puede significar «no se toca nada, tu bloque SÍ está, revísalo a mano». **Arbitraje:** documentar los dos significados de exit 1 y que el campo que manda es `bloque_presente`. Regenerar interop | T-13 | corregido (fix2): `commands/setup.md` paso 5 documenta los dos significados de la salida 1 ((a) se revirtió y el bloque NO está; (b) el fichero cambió, no se toca nada y el bloque puede SÍ estar: revisar a mano con la `.bak`) y que manda `bloque_presente`. Interop regenerado (solo `setup.md` de Codex y OpenCode; revertidos los cambios de solo fin de línea). | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_23_setup_documenta_los_dos_significados_de_exit_1` → `AssertionError: ('commands', 'setup.md')` (`'bloque_presente' in …`). GREEN en las tres copias; `export-interop --check` 50 al día. | B |
| 24 | Minor | `/setup` acepta un `id_prefix` que empieza por dígito o que es palabra reservada de YAML (`id_prefix_valido` no se alineó con la regla de #2), y el paso de Kwipu solo dice «Salida 2: corrígelos». **Arbitraje:** `id_prefix_valido` aplica la misma regla que el nombre de #2 (empieza por letra, sin palabras reservadas). `setup.md` indica pasar `--nombre <propuesta>` si el `id_prefix` no vale como nombre. Tests | T-10/T-13 | corregido (fix2): `knowledge-schema.id_prefix_valido` aplica la regla del nombre de #2: `ID_PREFIX_RE = ^[a-z][a-z0-9-]*$` y fuera las reservadas de YAML 1.1 (sin distinguir mayúsculas); el error de `preparar_id_prefix` lo explica. `setup.md` paso 3: si la salida 2 es por el nombre, repetir con `--nombre <propuesta>` (también en el `--apply`). | RED contra `f74a45a` (tests nuevos sobre el código de `f74a45a`, Windows, 2026-09-30): `test_fix2_24_id_prefix_valido_rechaza_lo_que_yaml_no_lee_como_texto[2048, 0x1f, 0b101, 1abc, yes, on, true, null, y, n, off, false]` → `assert not True` (12); `test_fix2_24_preparar_id_prefix_rechaza_un_id_prefix_numerico` → `ok` True; `test_fix2_24_setup_indica_pasar_nombre_si_el_id_prefix_no_vale` → `AssertionError: ('commands', 'setup.md')`. GREEN: `test_knowledge_schema.py` en verde. | B |

**Decisión del orquestador (2026-09-30):** 2 Important locales y baratos (#19 es una línea; #20 es la regla de `validar_root`) ⇒ micro-ronda `fix2` sobre #19-#24 e **intento 3** (el último) con la Lente B y la C.
