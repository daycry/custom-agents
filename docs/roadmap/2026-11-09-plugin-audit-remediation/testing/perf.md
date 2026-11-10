# Rendimiento de procesos — medidas antes y después (Fase 3, CA-05)

[Ledger](../tasks.md) · [Auditoría](auditoria-2026-11-09.md)

## Método común

- **Máquina:** Windows 11 (10.0.26300), Intel de 12 hilos, 31,8 GB, Python 3.13.0, Node 23.8.0. Equipo compartido y con carga variable: los tiempos son orientativos y se comparan solo dentro de una misma tanda.
- **Código:** «antes» = `git archive` del commit de partida de la tarea; «después» = la misma copia con los ficheros de la tarea. Las dos se ejecutan desde el scratchpad, nunca sobre el repo.
- **Datos:** copias del roadmap y de la memoria del repo (`docs/roadmap`, `docs/knowledge`, `.claude/usage-state.json`, `.claude/dev.json`). `p68` = el roadmap real (68 iniciativas); `p345` = el mismo más 277 copias antiguas (345 carpetas, como en la auditoría).
- **Repeticiones:** una de calentamiento (descartada) y 5 medidas, cada una en un proceso nuevo, como un hook real. Se da la **mediana**.
- **Misma salida:** cada medida guarda el SHA-256 de la salida funcional; las cifras solo se aceptan si el SHA es igual antes y después.
- **Tiempos y recuentos van por separado:** los recuentos (aperturas de ficheros con un `sys.addaudithook` sobre el evento `open`, procesos con la contabilidad de un Job Object) son deterministas; los tiempos no.

## T-13 — SessionStart en una pasada (H-28, H-40)

`compose` de `hooks/session-context.py` en proceso (arnés `compose_child.py`: carga el hook, compone `startup` y cuenta aperturas).

### Recuentos (deterministas)

| Medida | p68 antes | p68 después | p345 antes | p345 después |
|---|---|---|---|---|
| Aperturas de `tasks.md` | 107 | 68 | 132 | 125 |
| Ledgers distintos abiertos | 70 | 68 | 129 | 125 |
| Máximo de aperturas de un mismo ledger | 3 | 1 | 3 | 1 |
| Aperturas de `usage-state.json` | 2 | 1 | 2 | 1 |
| Lecturas del corpus de `docs/knowledge` (memoria con 2 consultas) | 2 | 1 | 2 | 1 |
| Procesos lanzados | 0 | 0 | 0 | 0 |

### Tiempo de `compose` (mediana de 5, segundos)

| Datos | Antes | Después | Antes, state migrado | Después, state migrado |
|---|---|---|---|---|
| p68 | 2,23 | 1,14 | 1,97 | 1,17 |
| p345 | 2,66 | 1,31 | 2,54 | 1,72 |

Series: p68 antes 2,12 / 2,16 / 2,35 / 2,23 / 3,10 → después 2,06 / 1,09 / 1,14 / 1,67 / 1,05; p345 antes 2,85 / 2,25 / 2,66 / 2,25 / 3,71 → después 2,20 / 1,26 / 2,07 / 1,31 / 1,24.

**Misma salida:** SHA `71063a71866c` (p68, 4.534 caracteres) y `0228031a11bb` (p345, 4.243) antes y después, con el state original y con el migrado.

### `usage-state.json` (H-40)

| Medida | Antes | Después |
|---|---|---|
| Tamaño (copia del repo, 226 marcadores, 225 cerrados) | 4.007.683 B | 134.997 B |
| Offsets guardados | 41.357 | 537 |
| `json.load` (mediana de 7) | 36,9 ms | 2,0 ms |
| Migración única de los cerrados (al siguiente `start`/`close`) | — | 2,4 s, una vez |

En el repo real, el primer `close` con el código nuevo dejó el fichero en 103.374 B.

**Misma medida:** re-cerrar con los offsets completos y con los podados da los mismos tokens en los marcadores reales `plugin-audit-remediation/T-07` y `T-12` (324 → 3 offsets cada uno; arnés `equiv.py`). La regla conserva el offset de un transcript que tenía registros dentro de la tolerancia de 60 s antes del `start`, el único caso en que cambia la medida. La primera versión, que podaba solo por fecha de modificación, contaba 4 respuestas de más en T-12: por eso no se usó.

## T-14 — Menos procesos por hook (H-29, H-30, H-31)

`node hooks/run-hook.mjs <hook>` lanzado desde un arnés que entra en un Job Object (`count_procs.py`): la contabilidad del job da cuántos procesos nacen del evento (lanzador incluido; el Python del `.venv` cuenta 2: redirector y real; `node -e ""` solo cuenta 1). Proyecto `p68`. «Antes» = commit faed5b5; «después» = el mismo con los ficheros de T-14.

### Recuentos (deterministas)

| Evento | Procesos antes | Procesos después |
|---|---|---|
| SubagentStop (`subagent-progress.sh`) | 26 | 4 |
| UserPromptSubmit (`user-prompt-capture.sh`) | 7 | 4 |
| SessionEnd (`session-journal.sh`) | 7 | 4 |

### Tiempo por evento (mediana de 5, segundos)

| Evento | Antes | Después |
|---|---|---|
| SubagentStop | 2,76 | 1,26 |
| UserPromptSubmit | 1,36 | 0,99 |
| SessionEnd | 1,08 | 0,91 |

**Misma salida:** la primera emisión de SubagentStop es idéntica antes y después (cuatro líneas `📋 …` de las iniciativas activas); después, las repeticiones sin cambios salen vacías (debounce con `.claude/.progress-last`). UserPromptSubmit y SessionEnd no emiten nada en ninguno de los dos casos. `scripts/bench-session-end.py`: p95 19,45 ms, p99 24,25 ms (umbrales 100/300 ms).

## T-15 — Panel y consola sin bloqueos (H-32, H-33, H-34)

En proceso (`t15_measure.py`): `serve_panel.create_server` sobre `p68` con un servidor efímero en el puerto 0 y la consola (`console_service.Service`) con un reloj simulado y un `discover` doble que cuenta los CLI que se lanzarían. «Antes» = commit 544b50d.

### Recuentos (deterministas)

| Medida | Antes | Después |
|---|---|---|
| Recálculos del progreso en 10 sondeos sin cambios | 10 | 0 |
| Cargas de `console_transport.py` en 10 llamadas a `runtimes` | 10 | 1 |
| CLI lanzados en 120 s de sondeo cada 2 s desde Inicio | 24 | 0 |
| CLI lanzados en 120 s de sondeo cada 2 s desde Sesiones (sin cambios) | 24 | 12 |

### Tiempos (segundos)

| Medida | Antes | Después |
|---|---|---|
| `api/progress` sin cambios (mediana de 10 sondeos) | 0,638 | 0,018 |
| `api/progress` tras cambiar un ledger (mediana de 5) | 0,639 | 0,022 |
| Portada pedida durante ese recálculo (mediana de 5) | 0,583 | 0,005 |
| 10 llamadas a `runtimes` (total) | 1,24 | 0,21 |

**Misma salida:** la proyección del progreso tiene el mismo SHA (`a4495396d688`, sin `observed_at`) antes y después.

## T-16 — Scripts de las puertas (H-35 a H-39)

Cada ejecución en un proceso nuevo (`t16_measure.py`), calentamiento + 3, mediana; SHA de la salida en cada caso. «Antes» = commit 722e80f; las dos versiones se midieron sobre el mismo estado del repo (scope-check lee el diff). code-health se mide sobre una copia fija del árbol del repo.

| Script | Antes (s) | Después (s) | Salida |
|---|---|---|---|
| `scope-check.py` de esta iniciativa (`--base master --json`) | 1,69 | 0,94 | igual (`c8040d09bdbf`) |
| `ledger-archive.py` en seco del ledger de 519 KB | 2,70 | 1,16 | igual (`22735ab2ca19`) |
| `ledger-lint.py` del mismo ledger | 0,21 | 0,21 | igual (`581acf0799e1`) |
| `code-health.py` del árbol del repo | 11,79 | 6,59 | igual (`488220a74023`) |
| `task-brief.py` de T-16 | 1,12 | 1,12 | igual (`46d70212b924`) |
| Barra de estado, 7 turnos con el coste cambiando (mediana por refresco) | 1,49 | 0,62 | igual (`3dfebc8547c6`) |

| Recuento | Antes | Después |
|---|---|---|
| `os.path.isdir` en `clasificar` (40 ficheros × 4 patrones, test) | 126 | ≤ 4 |
| Procesos que lanza `task-brief.py` | 3 | 2 |
| Pythons de la barra de estado en 7 turnos | 7 | 1 |

`ledger-lint` no cambia de forma apreciable: lo caro del caso de la auditoría (5,6 s con 507 KB) era el archivado. El proceso que sigue lanzando `task-brief.py` es la consulta de memoria (`knowledge-find.py`).

## Revisión de dos lentes, intento 1: medidas nuevas (2026-11-10)

Mismo método que arriba; solo cambian estas cifras.

| Medida | Antes | Después | Nota |
|---|---|---|---|
| Migración única de `usage-state.json` (copia del repo) | 2,4 s | 1,23 s | D2: un transcript abierto cada vez y un `stat` por fichero; mismos 537 offsets y mismos tokens al re-cerrar T-07 y T-12 |
| Procesos por SubagentStop con un Python normal (sin `.venv`) | 22 | 3 | A3: `node -e ""` cuenta 1; el `.venv` añade un redirector por Python |
| Procesos por UserPromptSubmit / SessionEnd con un Python normal | 5 / 5 | 3 / 3 | A3 |
| Paso del lint en `task-brief.py`, aislado (mediana de 5) | 0,410 s (subproceso) | 0,014 s (en proceso) | A1: el brief completo sigue en ~1,1 s porque lo domina la consulta de memoria (`knowledge-find.py`, subproceso) |
| Barra de estado, 7 turnos con el coste cambiando | 7 Pythons | 1 Python (0,76 s por refresco, máquina cargada) | D1/B2: cada campo dentro de su grupo; misma salida (`3dfebc8547c6`) |
