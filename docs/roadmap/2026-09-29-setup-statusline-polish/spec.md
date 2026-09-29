---
spec: setup-statusline-polish
descripcion: Pulido de /setup, statusline y puertas tras las iniciativas de conocimiento — iniciativa en curso en la statusline, ruta y coste correctos, dashboard que vuelve a leer las evaluaciones, tests deterministas, alta segura del proyecto en Kwipu y nombre de proyecto único
estado: aprobada
riesgo: medio             # piloto de sdd-proporcional: el punto 7 escribe en la config del stack del usuario (solo añade, con confirmación)
creado: 2026-09-29
actualizado: 2026-09-29
evaluacion: evaluation.md
design: n/a
plan: pendiente
generacion:
  inicio: 2026-09-29T18:47:03Z
  fin: 2026-09-29T18:49:02Z
  fuente: estimado        # el meter degradó: carpeta de transcripciones no disponible
  horas_ia: 0.3
  duracion: 2m
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
---

# setup-statusline-polish — pulido de setup, statusline y puertas

> **Evaluación:** [`evaluation.md`](evaluation.md) (en-revision · go condicionado · ≈ 2.729 € de referencia humana, ≈ 266 € ejecutando con agentes)
> **Plan de implementación:** pendiente

> **Terminología:** *stack* = carpeta local del stack de grafos de conocimiento del usuario (`<stack>/`). *Iniciativa en curso* = la iniciativa en la que se trabaja ahora, distinta de «activa» (cualquier ledger no completado). `id_prefix` = clave de `taxonomy.json` que prefija los `knowledge_id`.

## Contexto y objetivo

Tras `knowledge-services`, `graphiti-memory`, `training-data-services` y `session-end-durable-capture` quedan defectos pequeños y un hueco de onboarding. Los defectos degradan la visibilidad diaria (statusline, dashboard) o las puertas (cobertura, tests inestables). El hueco: dar de alta un proyecto en Kwipu es hoy un paso manual sobre `projects.yaml`, y el nombre del proyecto (`id_prefix`) se decide en silencio. Objetivo: cerrar los 9 puntos siguientes en una sola iniciativa de riesgo medio, sin ampliar el alcance de ninguna capacidad.

Fuentes: decisiones del usuario 2026-09-28/29; `statusline/roadmap-statusline.sh`; `commands/setup.md` (5-bis, 5-sexies); `skills/roadmap-dashboard/scripts/build_dashboard.py`; `skills/unit-tests/scripts/coverage-gate.py`; `skills/knowledge-services/`.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Señal de «iniciativa en curso» | **Marcador abierto de `usage-meter` en `.claude/usage-state.json`; si no hay, el `tasks.md` modificado más recientemente** | Ya existe, es local y no exige que el usuario declare nada |
| Formato statusline | **`📋 4 activas · ▶ <slug> T-06/11 55%`**; con una sola activa, sin cambios | No añade ruido cuando no hay ambigüedad |
| Ruta de scripts (`find`) | **Excluir rutas bajo `~/.claude/jobs` y cualquier temporal; preferir plugin instalado o proyecto** | Un temporal viejo gana hoy por orden de `find` |
| Alta en Kwipu | **Script stdlib determinista, solo añade; nunca modifica ni borra entradas** | Es config del usuario: el riesgo se acota por construcción |
| YAML no reconocido | **No escribe; imprime el bloque para pegar a mano** | Sin dependencia de un parser YAML completo |
| Nombre de proyecto | **`id_prefix` explícito, propuesto desde el slug de la carpeta; de él derivan el nombre en `projects.yaml` y el `group_id` de Graphiti; sobrescribible** | Un solo origen del nombre evita divergencias entre backends |
| Test de tiempos | **Reloj inyectado o contador de operaciones en lugar de techo en segundos** | Determinista bajo carga |
| Fixtures de conocimiento | **`evals/fixtures/project` o `tests/fixtures/`** | `docs/knowledge/` ya no se versiona |

## Arquitectura y componentes

Se reutilizan `usage-meter.py` (marcador abierto), `knowledge-schema.py` (`id_prefix` por defecto), `knowledge-sync.py`, los backends `markdown_export` y `graphiti`, y `outbox.py`. Lo nuevo es un script de alta de proyecto en Kwipu bajo `skills/knowledge-services/scripts/`, con sus tests. El resto son correcciones sobre piezas existentes. Todo cambio en `agents/`, `commands/` u `hooks/` regenera `interop/` con `export-interop.py`.

## Flujo (paso a paso) — puntos 7 y 8, `/setup` 5-sexies

1. `/setup` propone el `id_prefix` (slug de la carpeta), valida su forma y lo guarda en `taxonomy.json`.
2. El script lee `<stack>/kwipu/config/projects.yaml` y el `export_dir` de `taxonomy.json`.
3. Si el YAML no tiene una forma reconocida: no escribe, imprime el bloque a pegar a mano y termina.
4. Si existe un proyecto con ese nombre que apunta a otra carpeta: no escribe, muestra el conflicto y pide otro nombre.
5. Si ya existe con la misma `root`: no hace nada (idempotente).
6. Si no existe: muestra la vista previa del bloque, pide confirmación, crea copia de seguridad y **añade** el bloque.
7. Imprime los comandos exactos de `build_view` y de reinicio de contenedores; **no los ejecuta**.

## Alcance

- **Dentro (esta iteración):**
  1. Statusline: iniciativa en curso con varias activas.
  2. Statusline y `/setup` 5-bis: el `find` nunca elige un temporal bajo `~/.claude/jobs`.
  3. Statusline: coste correcto (sin `$0,00` por coma decimal o redondeo).
  4. `coverage-gate.py`: el chequeo de `pytest_cov` deja de dar «no disponible» falso por su timeout de 15 s.
  5. `build_dashboard.py`: vuelve a leer coste y esfuerzo de las evaluaciones de 5 iniciativas.
  6. `test_backend_markdown_export` (`…tiempos_200_upserts…`) determinista.
  7. Script de alta en `projects.yaml` (solo añade) y su enganche en `/setup` 5-sexies.
  8. `id_prefix` elegible en `/setup`, con derivación de nombre de proyecto y `group_id`, y sus avisos.
  9. Derivados: (a) la línea kwipu de `/doctor` respeta su `tope_ms`; (b) ~20 tests de `test_knowledge_find`/`test_knowledge_index` pasan a fixture.
- **Fuera (siguientes specs):**
  - Ejecutar `build_view`, reiniciar contenedores o tocar `kwipu-data`.
  - Modificar o borrar entradas existentes de `projects.yaml`.
  - Migrar los `knowledge_id` ya exportados al renombrar (solo se avisa).
  - Borrar o reasignar episodios existentes en Graphiti.
  - Rediseñar la statusline más allá de la línea de iniciativa.
  - Cambiar el formato de `evaluation.md` (se adapta el lector, no la plantilla).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| `usage-state.json` ausente o corrupto | Recurre al `tasks.md` más reciente; sin ninguno, línea actual sin cambios |
| `projects.yaml` ausente, ilegible o de forma desconocida | No escribe; imprime el bloque y sale con un código distinto de 0 documentado |
| Fallo de la copia de seguridad | No escribe |
| Usuario no confirma | No escribe; exit 0 |
| `id_prefix` con forma inválida | Rechaza y vuelve a preguntar; no guarda |
| Renombrar con conocimiento ya exportado | Aviso: cambian los `knowledge_id`; no migra |
| `group_id` con episodios de otro origen | Aviso antes de la primera sincronización; no bloquea |
| Sin `python3` o herramientas opcionales | Degrada con aviso; nunca bloquea el ciclo |

## Modelo de amenaza y escala

**Activos:** `projects.yaml` (config del stack del usuario, fuera del repo), `taxonomy.json` y las copias de seguridad.

| Amenaza | Mitigación |
|---|---|
| Corromper o pisar config ajena | Solo añade; copia de seguridad previa; escritura atómica (temporal + reemplazo); vista previa + confirmación |
| Duplicar o secuestrar un proyecto existente | Conflicto de nombre con otra `root` → no escribe; misma `root` → no-op |
| Inyección vía `id_prefix` o `root` (saltos de línea, `:`, `#`, comillas) | Validación estricta de forma (`^[a-z0-9][a-z0-9-]*$`) y de `root` antes de emitir; salida escapada |
| Ruta fuera del stack (`..`, absoluta inesperada) | Normalización y comprobación de que el destino es el `projects.yaml` del stack indicado |
| Datos personales en ficheros versionados | Ejemplos con `<stack>/…`; sin usuario, correo ni empresa |
| Hooks o statusline con red | No hacen red |

**Escala:** un usuario, un `projects.yaml` de decenas de entradas, un `taxonomy.json`. La única concurrencia posible son dos `/setup` simultáneos; la escritura atómica y la relectura justo antes de escribir lo cubren. La statusline se ejecuta a cada refresco: el escaneo de iniciativas debe costar milisegundos (solo `docs/roadmap/*/tasks.md`, sin recorrer `docs/`).

**Riesgo `medio`:** escribe fuera del repo, pero solo añade, con confirmación y copia de seguridad.

## Criterios de aceptación

- [ ] [GWT] CA-01 — Dado 4 iniciativas activas y un marcador de `usage-meter` abierto para `training-data-services`, Cuando se renderiza la statusline, Entonces muestra `📋 4 activas · ▶ training-data-services T-06/11 55%`.
- [ ] [GWT] CA-02 — Dado varias activas y ningún marcador abierto, Cuando se renderiza la statusline, Entonces marca en curso la de `tasks.md` modificado más recientemente.
- [ ] [GWT] CA-03 — Dado una sola activa, Cuando se renderiza, Entonces la salida es idéntica a la actual (sin `▶`).
- [ ] [GWT] CA-04 — Dado una copia vieja del script bajo `~/.claude/jobs` y otra en el plugin instalado, Cuando el `find` de la statusline o el de `/setup` 5-bis resuelven la ruta, Entonces devuelven la del plugin o proyecto, nunca la temporal.
- [ ] [GWT] CA-05 — Dado un coste de sesión de 0,42 con locale de coma decimal, Cuando se renderiza, Entonces muestra `$0.42`, no `$0,00`; un coste positivo menor de 0,01 no se muestra como cero engañoso.
- [ ] [GWT] CA-06 — Dado `pytest_cov` instalado y un arranque lento del intérprete, Cuando corre `coverage-gate.py`, Entonces no informa «no disponible»; solo lo hace si el módulo falta de verdad (exit 2 con aviso, nunca un % inventado).
- [ ] [GWT] CA-07 — Dadas las 5 `evaluation.md` afectadas, Cuando corre `build_dashboard.py`, Entonces cada una aporta coste y esfuerzo no nulos, y hay un test con una fila de cada variante de etiqueta (`Tiempo humano`, `Coste humano a N EUR/h` y las históricas).
- [ ] CA-08 — El test de 200 upserts no depende del reloj: pasa igual con la máquina cargada y falla si la operación deja de ser lineal (aserción sobre número de operaciones o reloj inyectado). Se verifica ejecutándolo 20 veces en bucle sin fallos.
- [ ] [GWT] CA-09 — Dado un `projects.yaml` reconocido sin el proyecto, Cuando se ejecuta el script y el usuario confirma, Entonces existe copia de seguridad, se añade exactamente un bloque con `root` = `export_dir` de `taxonomy.json` y el resto del fichero queda byte a byte igual.
- [ ] [GWT] CA-10 — Dado el mismo proyecto ya presente con la misma `root`, Cuando se ejecuta de nuevo, Entonces no cambia nada (idempotente) y lo dice.
- [ ] [GWT] CA-11 — Dado un YAML de forma no reconocida, Cuando se ejecuta, Entonces no escribe y muestra el bloque para pegar a mano.
- [ ] [GWT] CA-12 — Dado un proyecto homónimo que apunta a OTRA carpeta, Cuando se ejecuta, Entonces no escribe, muestra el conflicto y pide otro nombre.
- [ ] CA-13 — Sin confirmación, o con fallo de la copia de seguridad, no se escribe nada. El script no ejecuta `build_view` ni reinicia contenedores: imprime los comandos exactos.
- [ ] [GWT] CA-14 — Dado un `taxonomy.json` sin `id_prefix`, Cuando corre `/setup`, Entonces propone el slug de la carpeta, valida la forma y guarda el valor; el nombre del proyecto en `projects.yaml` y el `group_id` de Graphiti lo heredan salvo sobrescritura explícita.
- [ ] CA-15 — Avisos sin bloqueo: `group_id` con episodios de otro origen antes de la primera sincronización; renombrar con conocimiento ya exportado advierte del cambio de `knowledge_id`. Cada aviso tiene test.
- [ ] CA-16 — Con carga simulada (servidor lento), la línea kwipu de `/doctor` no supera su `tope_ms` más un margen fijo y documentado; test con reloj o servidor simulado.
- [ ] CA-17 — Los ~20 tests de `test_knowledge_find` y `test_knowledge_index` pasan en un clon limpio sin `docs/knowledge/` (fixture versionado, sin datos personales).
- [ ] CA-18 — `python scripts/lint_plugin.py`, `python evals/check.py`, `export-interop.py --check` y las suites de `tests/` en verde (comparando el conjunto de rojos preexistentes en Windows); replicado en Linux antes de publicar.
- [ ] CA-19 — Docs EN/ES actualizadas (`docs/en/`, README y CHANGELOG bilingües, `docs/agents` si aplica) y sin datos personales en lo versionado.

## Pruebas

Tests unitarios con stdlib por punto: statusline con `usage-state.json` y `tasks.md` sintéticos; script de alta con YAML de formas conocidas, desconocidas y en conflicto; dashboard con fixtures de cada variante de etiqueta; gate con `pytest_cov` simulado lento. Los criterios `[GWT]` se traducen 1:1 a tests con el mismo ID CA-XX. Sin UI: qa en modo sin UI.

## Referencias

- `statusline/roadmap-statusline.sh` (`find` de `progress-report.py`); `commands/setup.md` 5-bis y 5-sexies.
- `skills/roadmap-dashboard/scripts/build_dashboard.py`: `_scan_leer_eval` busca las filas `Coste` y `Esfuerzo humano`. Las evaluaciones recientes usan `Tiempo humano` y `Coste humano a N EUR/h`, así que el lector devuelve `None`.
- `skills/unit-tests/scripts/coverage-gate.py` (`timeout=15` en la comprobación `import pytest, pytest_cov`).
- `agent-kits/shared/knowledge-schema.py` (`_con_id_prefix_por_defecto`).
- `skills/knowledge-services/scripts/test_backend_markdown_export.py`; ADR-018.

## Decisiones confirmadas (revisión del usuario · 2026-09-29)

1. Los 9 puntos entran en esta iniciativa, riesgo `medio`. **Confirmado.**
2. Iniciativa en curso: marcador abierto de `usage-meter`; si no hay, `tasks.md` más reciente. **Confirmado.**
3. El alta en Kwipu solo añade, con vista previa, confirmación y copia de seguridad; no ejecuta `build_view` ni reinicia contenedores. **Confirmado.**
4. `id_prefix` propuesto desde el slug de la carpeta; de él derivan proyecto y `group_id`, sobrescribibles. **Confirmado.**

## Supuestos

- La causa del punto 5 son solo las etiquetas de fila (`Coste`/`Esfuerzo humano` frente a `Tiempo humano`/`Coste humano a N EUR/h`); se confirma al implementar leyendo las 5 evaluaciones.
- `projects.yaml` tiene una forma de lista o mapa de proyectos con nombre y `root`. La forma exacta es incógnita hasta ver el fichero real: el script reconoce formas concretas y rechaza el resto.
- El `$0,00` viene de la coma decimal en `printf` bajo locale o del redondeo; se reproduce antes de arreglar.
- Detectar «episodios de otro origen» en Graphiti puede requerir consultar el servicio; sin conexión, el aviso degrada a «no verificado».
- El exceso de la línea kwipu de `/doctor` viene del coste de `_urlopen_local`; se confirma con medición.
