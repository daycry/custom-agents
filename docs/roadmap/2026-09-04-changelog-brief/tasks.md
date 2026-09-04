---
tasks: changelog-brief
descripcion: Un bullet de CHANGELOG que se pueda leer. La skill `changelog-sync` generaba un bullet por tarea con la primera frase completa de la `Descripción` del ledger, escrita para el implementador y no para el CHANGELOG: medido sobre los 13 ledgers cerrados del repo (63 tareas), esa primera frase tenía mediana 447 y máximo 1.944 caracteres (37 de 63 por encima de 400), y el bullet completo mediana 660 y máximo 2.163 — por eso las notas de la v1.16.0 se escribieron A MANO. Se sustituye por una ESCALERA determinista: campo opcional `- **Changelog**: <una o dos frases>` en el bloque `### T-XX` (se usa tal cual; lo escribe quien CIERRA la tarea) → primera frase de la `Descripción` si cabe en `RESUMEN_MAX = 200` → oración principal (corte en el primer `:`, `;`, `—` o `(` de nivel superior, si se lee como idea completa) → SOLO el título más un puntero al ledger. Ningún camino trunca con `…`. Los ficheros clave bajan de 5 a 3 y el paréntesis desaparece cuando la tarea toca más de 6 (mostrar 3 de 20 hace creer que son todos). El empuje para que el campo se escriba: `changelog-sync.py --check` lista las tareas cerradas sin campo (aviso, sin tocar su exit code) y `ledger-lint.py` lo trata SIEMPRE como aviso y solo en adopción parcial. Este ledger es el primero que usa el campo.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-04
actualizado: 2026-09-04
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige (exit ≠ 0 si falta)
changelog: Changed        # cambia el texto que produce una skill existente, no añade pieza nueva
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud sin transcripción)
---

# Checklist de Tareas — changelog-brief (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-04 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Este ledger es el primer usuario del campo que estrena.** Cada `### T-XX` de abajo lleva su `- **Changelog**: <una frase>`. No es decoración: es la prueba de que el mecanismo sirve, y es lo que `changelog-sync` copiará tal cual a `[Unreleased]`/`[Sin publicar]` cuando se generen las notas.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — bullet legible | 7 | 7 | 100% | 17,1 / 17,1h | 1,05 / 1,05h | 0,27 / 0,27h | 470k / 470k |
| **TOTAL** | **7** | **7** | **100%** | **17,1 / 17,1h** | **1,05 / 1,05h** | **0,27 / 0,27h** | **470k / 470k** |

> **Horas y tokens marcados `estimado`.** `agent-kits/shared/usage-meter.py` no puede leer la transcripción en este entorno (sandbox cloud), así que el bloque `generacion:` va con `fuente: estimado` y los reales de cada tarea repiten la estimación, marcados. No se presenta como medición.

---

## Fase única — bullet legible

**Estado**: completado · **Estimado**: 17,1h · **Real**: 17,1h (estimado) · **Coste est.**: ≈890 € · **Tokens est.**: 470k
(T-01, la escalera y sus topes medidos: 2,6h. T-02, ficheros clave: 0,8h. T-03, el empuje del campo: 1,2h. T-04, que el campo se escriba: 0,6h. T-05, doc y memoria: 1,6h. T-06, cierre de los gaps del intento 1: 4,5h. T-07, cierre de los gaps del intento 2: 5,8h.)

### T-01 — La escalera del resumen (campo `Changelog:` → 1.ª frase → oración principal → título)

- **Descripción**: `resumen(desc, changelog)` en `skills/changelog-sync/scripts/changelog-sync.py` pasa a ser la fuente única del criterio y devuelve `(texto, camino, avisos)` con `camino ∈ changelog|frase|corte|titulo`. Se añaden `frases(s, n)` (las n primeras frases, mismo criterio de corte que `primera_frase`), `corte_principal(s)` (primer `:`, `;`, `—` o `(` de NIVEL SUPERIOR: fuera de los tramos entre acentos graves y de cualquier pareja abierta `( [ { «`), `palabras_de_prosa(s)` (palabras fuera del código: la puerta de «se lee como una idea completa») y `normaliza_resumen(t)` (cierra la negrita que el corte dejó abierta, quita la puntuación colgante, mayúscula inicial, punto final; **nunca** añade `…`). Los topes son constantes con su porqué medido al lado: `RESUMEN_MAX = 200`, `RESUMEN_FRASES_MAX = 2`, `CORTE_MIN_PALABRAS = 5`. El campo del ledger se respeta LITERAL (ni mayúscula inicial ni punto añadido): lo escribió una persona. `FIN_FRASE` gana `*` en la clase de apertura de frase para reconocer `. **(1) …`, muy común en las Descripciones de este repo.
- **Changelog**: El bullet de cada tarea pasa a ser un resumen de una o dos frases, y cuando no hay material que quepa dice el título de la tarea en vez de truncar la frase por la mitad.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 2,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,15h (estimado)
- **Supervisión**: est. 0,04h · real 0,04h (estimado)
- **Archivos**: `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`
- **Verificación** (ejecutada 2026-09-04; RED corregido 2026-09-04 en T-06): RED antes de implementar, con los tests nuevos contra el script de `a7a11b0` → **`17 failed, 16 passed`** y `AttributeError: module 'changelog_sync' has no attribute 'normaliza_resumen'` entre los fallos; GREEN después → `32 passed`, y **57 passed** al cerrar T-06 (`python3 -m pytest -q skills/changelog-sync/scripts/test_changelog_sync.py`). El `15 failed, 15 passed` que esta línea declaraba **no cuadra ni reproduce** (15+15=30 y hay 33 tests): la reproducción literal es `git show a7a11b0:…/changelog-sync.py` + el fichero de tests de hoy en un directorio temporal → `17 failed, 16 passed in 1.13s`. Elección de `RESUMEN_MAX` sobre los 13 ledgers (63 tareas), variando SOLO la constante:
  ```
  RESUMEN_MAX=160: {'titulo': 42, 'frase': 11, 'corte': 10}
  RESUMEN_MAX=200: {'titulo': 42, 'frase': 12, 'corte': 9}
  RESUMEN_MAX=240: {'titulo': 40, 'frase': 14, 'corte': 9}
  ```
  Los ±2 no deciden: decide qué texto entra. `160 → 200` cambia UNA tarea (`windows-console/T-02`, 192 caracteres) y la mejora — con 160 el paso 3 la recorta y pierde el paréntesis que explica el *por qué*. `200 → 240` añade DOS, y una es `deterministic-guardrails/T-04`: 237 caracteres con **tres cláusulas separadas por punto y coma**, que es exactamente el párrafo que se quería quitar. `CORTE_MIN_PALABRAS` con tope 200: `4 → corte 10`, `5 → corte 9`, `6 → corte 7`; se elige 5, el punto donde desaparecen los «rescates» que son solo rutas (`` `docs/README.md` + `docs/en/README.md` ``) y aún entran frases cortas legítimas
- **Notas**: `RESUMEN_FRASES_MAX` se aplica SOLO al campo del ledger; los caminos 2 y 3 dan una frase por construcción. Chequeo adversarial de equilibrio Markdown sobre los **126 bullets** reales generados (acentos graves pares, `**` pares, paréntesis equilibrados, sin `…` añadido): **0 problemas**. Los 6 señalamientos del primer barrido eran del propio detector — `**` dentro de `` `evals/**` `` (glob en código, literal en Markdown) y los dos `…` que el ledger ya traía escritos.

**Criterios de aceptación**
- [x] La escalera está en UNA función (`resumen()`) con los cuatro caminos nombrados, y el camino se puede leer desde fuera (`--check --json` → `pendientes[].caminos` por iniciativa pendiente; el agregado de TODO ledger cerrado es `degradacion.caminos`, añadido en T-06)
- [x] El campo `- **Changelog**:` de la tarea se usa TAL CUAL, sin normalizar (test `test_el_campo_changelog_se_respeta_literal_sin_normalizar`)
- [x] Más de dos frases en el campo → se usan las dos primeras y el script AVISA; pasado el tope → avisa y respeta el texto (no trunca lo que escribió una persona) y en ningún caso falla
- [x] `corte_principal()` no corta dentro de `` `código` ``, `(paréntesis)`, `[corchetes]` ni «comillas» (test unitario con los tres casos)
- [x] Ningún camino **añade** `…` ni `...` (test sobre los dos CHANGELOG; el `…` que ya venía escrito en el ledger —p. ej. la cadena de uso `` `[--files f1 f2 …]` ``— pasa tal cual, con su propio test)
- [x] Los tres topes son constantes con el motivo medido escrito al lado, y cada uno se eligió comparando 160/200/240 y 4/5/6 sobre los 13 ledgers reales (63 tareas)
- [x] Test RED visto fallar antes de implementar, GREEN después, y la suite completa del repo sigue verde

### T-02 — Ficheros clave: 3, y ninguno cuando la lista no informa

- **Descripción**: `archivos_clave()` deja de recortar (sin `maximo` devuelve TODOS) porque la decisión necesita saber cuántos ficheros toca la tarea DE VERDAD; el recorte y la omisión se deciden al renderizar en `bullets()`. Se listan hasta `ARCHIVOS_MAX = 3` y el paréntesis se omite entero cuando la tarea toca más de `ARCHIVOS_MAX_TOCADOS = 6` (`2 × ARCHIVOS_MAX`): la lista informa mientras los 3 mostrados sean al menos la mitad de lo tocado. No se pone «y 17 más»: para eso está el puntero al ledger del camino 4.
- **Changelog**: Los bullets del CHANGELOG dejan de arrastrar listas de cinco ficheros repetidos: se muestran hasta tres, y ninguno cuando la tarea toca tantos que la lista no informaría.
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,05h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`
- **Verificación** (ejecutada 2026-09-04): distribución del número TOTAL de ficheros por tarea sobre las 63 tareas de los 13 ledgers → mediana 8, máximo 62, y 53 de 63 tareas tocan más de 3. Cuántas conservarían paréntesis según el umbral:
  ```
  umbral  3: muestran 10/63      umbral  6: muestran 24/63
  umbral  4: muestran 17/63      umbral  8: muestran 32/63
  umbral  5: muestran 20/63      umbral 10: muestran 38/63
  ```
  Se elige 6 (38 % con lista, 39 tareas sin ella). Tests: `test_archivos_se_omiten_cuando_la_tarea_toca_demasiados` y `test_archivos_justo_en_el_umbral_si_se_listan` (`ARCHIVOS_MAX_TOCADOS` ficheros → la línea termina en ``(`f0.py`, `f1.py`, `f2.py`)``; uno más → sin paréntesis), y el test histórico de 5 ficheros actualizado a 3
- **Notas**: el umbral se expresa como `2 * ARCHIVOS_MAX` para que mover uno mueva el otro.

**Criterios de aceptación**
- [x] Se listan como máximo 3 ficheros, sin la anotación entre paréntesis del campo `Archivos`
- [x] Con más de 6 ficheros tocados no se escribe el paréntesis (ni una lista parcial ni un «y N más»)
- [x] El umbral se derivó midiendo la distribución real, y la medición está escrita
- [x] En el camino `titulo` el paréntesis de ficheros lo sustituye el puntero al ledger (no salen los dos)

### T-03 — El empuje para que el campo se escriba (`--check` y `ledger-lint`)

- **Descripción**: `changelog-sync.py --check` lista, por ledger CERRADO, las tareas sin `- **Changelog**:` con sus IDs — **aviso**: el exit 1 sigue siendo solo por «entradas pendientes» y el 0 sigue siendo 0. Al escribir (sin `--check`) el aviso se limita a las iniciativas que se están generando. La forma de la línea evita el patrón `SLUG_PENDIENTE` de `scripts/release.py` (que reconoce `<viñeta> <slug> (AAAA-MM-DD)`), así que el resumen de pendientes del release no se contamina. `agent-kits/shared/ledger-lint.py` gana el campo en `parse_ledger()` y avisa **solo en adopción parcial** (una tarea del ledger lo trae y otra no) o con el campo presente y vacío: es opcional por diseño y los 13 ledgers cerrados existentes validan idéntico. El TOPE de longitud NO se duplica aquí: vive en `changelog-sync.py`, que es quien renderiza.
- **Changelog**: Al comprobar el changelog antes de una release, el script dice qué tareas cerradas no traen su resumen escrito, sin bloquear nada.
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real 1,2h (estimado)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,08h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`, `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`
- **Verificación** (ejecutada 2026-09-04):
  - `python3 tests/test_ledger_lint.py` → `test_ledger_lint: 16/16 OK`, **exit 0** (el caso 16 nuevo: sin campo en ninguna tarea → 0 avisos; adopción parcial → aviso `T-02: sin campo **Changelog** (otras tareas lo declaran)` con **exit 0**; campo vacío → `T-01: campo **Changelog** VACÍO`, también exit 0). RED previo literal: `AssertionError: ledger-lint: 0 incoherencias · 0 avisos (tasks.md)`
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-windows-console/tasks.md` → `ledger-lint: 0 incoherencias · 0 avisos (tasks.md)` **exit 0** — un ledger sin el campo valida exactamente como antes
  - `python3 skills/changelog-sync/scripts/changelog-sync.py --check` sobre el repo → **exit 1** por ESTA iniciativa (su ledger está cerrado y su entrada la escribe el usuario: es la consecuencia deliberada de más abajo), con el aviso del campo saliendo por los 13 ledgers cerrados sin él. Tras T-06 ese aviso ya no se repite por iniciativa ya publicada (era ruido: `pendientes()` las salta para siempre) y queda UNA línea con el total: `⚠️  resumen del campo \`Changelog:\`: 63/69 tarea(s) de 13/14 ledger(s) cerrados no lo traen y 42 bullet(s) degradan al título — detalle por camino en \`--check --json\` (\`degradacion.caminos\`)`. La forma sigue evitando el `SLUG_PENDIENTE` de `release.py`, y ahora hay test que lo fija
- **Notas**: la nota original decía que el aviso recorre todo ledger cerrado «porque es el recordatorio que ve el release», y era FALSO por los dos lados: `release.py --dry-run` no imprime ni una de esas líneas (su `SLUG_PENDIENTE` no casa el `⚠️`; verificado en T-06 → 0 líneas) y las iniciativas ya publicadas las salta `pendientes()` para siempre, así que escribir su campo no cambiaba un byte de salida. Corregido en T-06.

**Criterios de aceptación**
- [x] `--check` nombra las tareas sin campo de las iniciativas **realmente pendientes** —no de todo ledger cerrado: en las ya publicadas escribir el campo no cambiaría un byte de salida, porque `pendientes()` las salta para siempre— más UNA línea con el total de la deuda, y **no** cambia ningún exit code (probado en los dos sentidos: con y sin entradas pendientes). El criterio original decía «por ledger cerrado», que es exactamente lo que T-06 cambió a propósito: quedó marcado como cumplido diciendo lo contrario del código, y así lo cazó la revisión del intento 2
- [x] Con todas las tareas del ledger trayendo el campo, `--check` no menciona el campo
- [x] `ledger-lint.py` nunca lo cuenta como incoherencia dura, ni con `--warn-only` ni sin él
- [x] Un ledger sin el campo en ninguna tarea no recibe aviso (verificado contra un ledger real del repo, exit 0 y 0 avisos)
- [x] El tope de longitud no se duplica en `ledger-lint.py` (una sola fuente: `RESUMEN_MAX`)
- [x] La forma del aviso no la confunde el `SLUG_PENDIENTE` de `release.py` con una iniciativa pendiente

### T-04 — Que el campo se escriba: `implementer`, plantilla de tarea y `/dev-cycle`

- **Descripción**: una línea (no un párrafo) en los tres sitios donde se cierra una tarea. `agents/implementer.md` P3, justo tras marcar la tarea `completado`: escribe el campo, una frase, qué cambia para quien USA el proyecto, sin jerga del ledger ni nombres de fichero ni «T-XX». `agent-kits/planner/templates/tasks.md`, en el bloque de tarea que se copia (marcado OPCIONAL y «lo rellena quien CIERRA la tarea») — `skills/plugin-dev/` no tiene plantilla de tarea: sus `templates/` son de agente, comando y skill, así que la plantilla canónica de tarea es la del `planner`. `commands/dev-cycle.md` en los dos sitios donde toca: la lista de campos del ledger ligero de la vía rápida (Fase 0-bis) y el paso 6 de la Fase 6, que ahora manda comprobar con `--check` que las tareas cerradas traen el campo ANTES de invocar la skill.
- **Changelog**: Al cerrar una tarea, el agente que la implementa escribe en el ledger una frase con lo que cambia para quien usa el proyecto, y esa frase es la que acaba en las notas de la release.
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `agents/implementer.md`, `agent-kits/planner/templates/tasks.md`, `commands/dev-cycle.md`
- **Verificación** (ejecutada 2026-09-04): `grep -c "Changelog" agents/implementer.md agent-kits/planner/templates/tasks.md commands/dev-cycle.md` → `1 · 1 · 2` (una línea en el implementer, una en la plantilla, dos en el orquestador: campos del ledger ligero y paso 6). `python3 scripts/lint_plugin.py` → `lint_plugin: 9 agentes · 0 errores · 3 avisos`, **exit 0** (los 3 avisos son los nombres genéricos de `retro`/`roadmap-status`/`setup`, preexistentes). `python3 evals/check.py` → `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores`, **exit 0**
- **Notas**: no se añade al DoD del implementer: son tres sitios ya, y el DoD comprueba puertas mecánicas, no redacción.

**Criterios de aceptación**
- [x] `agents/implementer.md` lo pide en UNA línea, en el punto donde cierra la tarea, y dice cómo escribirlo (para quien usa el proyecto, sin jerga del ledger)
- [x] La plantilla de tarea trae el campo marcado OPCIONAL con quién lo rellena y cuándo
- [x] `commands/dev-cycle.md` lo cita donde describe el ledger ligero y donde cierra con `changelog-sync`
- [x] Ninguna pieza gana un párrafo nuevo ni una sección nueva
- [x] Linter y evals en verde (la `description` de la skill sigue bajo el tope y con sus disparadores)

### T-05 — Doc y memoria

- **Descripción**: `skills/changelog-sync/SKILL.md` — la `description` del frontmatter y el cuerpo dicen la escalera real en vez de «la primera frase de su descripción», con la tabla de los cuatro caminos, los topes, el bloque de idempotencia/empuje y un paso 0 en «cómo afinar» que manda arreglar la FUENTE (escribir el campo) antes que editar el CHANGELOG a mano. El detalle de la medición no cabe en el mapa: va a `skills/changelog-sync/references/medicion-escalera.md` (nueva, primera `references/` de esta skill) con la elección de cada tope, el antes/después y **los bullets que salen mal**, para no fingir que están bien. `docs/CONVENTIONS.md` regla 8 (+ espejo EN) documenta el campo donde ya vive la validación del ledger, sin sección nueva. Filas al día en `docs/README.md`, `docs/en/README.md` y `CLAUDE.md`. `docs/knowledge/adr/ADR-012` con la decisión y las seis alternativas descartadas (truncar con `…`, resumir con modelo, seguir igual, solo el corte, campo obligatorio, un puntero por subsección) + fila en `docs/knowledge/README.md`. Fila de la iniciativa DENTRO de la tabla de `docs/roadmap/README.md`.
- **Changelog**: La documentación de la skill y las convenciones del ledger describen la escalera real y el campo nuevo, con la medición que eligió cada tope y los casos en los que el resultado sigue siendo pobre.
- **Estado**: completado
- **Tiempo humano**: est. 1,6h · real 1,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,08h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `skills/changelog-sync/SKILL.md`, `skills/changelog-sync/references/medicion-escalera.md` (nuevo), `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md` (nuevo), `docs/knowledge/README.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md` (nuevo)
- **Verificación** (ejecutada 2026-09-04): `wc -l skills/changelog-sync/SKILL.md` → `128` (tope de aviso del linter: 200; duro: 250) y `python3 -m pytest -q tests/test_skill_size.py` → verde · `ls docs/knowledge/adr/ | tail -1` → `ADR-012-…` es el siguiente ID libre (había hasta `ADR-011`, `GOT-005`, `LES-014`) y `grep -c "ADR-012" docs/knowledge/README.md` → `1` · `python3 -m pytest -q tests/test_roadmap_index.py` → `31 passed` (la fila de la iniciativa está DENTRO de la tabla; el test la parametriza) · `grep -c "Changelog" docs/CONVENTIONS.md docs/en/CONVENTIONS.md` → `1 · 1` · `python3 scripts/export-skills.py --out <tmp> && python3 scripts/export-skills.py --check <tmp>` → `export-skills --check: 106 ficheros · 0 problema(s)`, **exit 0**, y la referencia nueva viaja en el paquete portable (`skills/changelog-sync/references/medicion-escalera.md` en el listado) · ningún `CHANGELOG*.md` modificado (`git status --porcelain | grep -c CHANGELOG` → `0`)
- **Notas**: la sección «Revisión de dos lentes» la escribe el usuario; este ledger se entrega sin ella a propósito.

**Criterios de aceptación**
- [x] La `description` del frontmatter de la skill y su cuerpo describen la escalera de cuatro caminos, no «la primera frase»
- [x] `SKILL.md` sigue por debajo de 200 líneas y el detalle de la medición está en `references/`, enlazado con «léela solo si vas a mover un tope»
- [x] La referencia incluye el antes/después medido y los bullets que salen MAL, con nombre y motivo
- [x] `docs/CONVENTIONS.md` y su espejo EN dicen lo mismo sin traducir literal, encajado en la regla 8 (sin sección nueva)
- [x] `ADR-012` con el formato exacto de los ADR existentes, el siguiente ID libre comprobado y su fila en el índice de knowledge
- [x] Fila de la iniciativa DENTRO de la tabla de `docs/roadmap/README.md` (lo vigila `tests/test_roadmap_index.py`)
- [x] Ningún `CHANGELOG*.md` modificado
- [x] El paquete portable sigue coherente y arrastra la referencia nueva

### T-06 — Cierre de los gaps del intento 1 (parseo del campo, guarda de abreviaturas, tests con literales y cifras re-medidas)

- **Descripción**: la revisión de dos lentes del intento 1 encontró un CRITICAL de parseo, ocho IMPORTANT y ocho MINOR sobre lo que T-01..T-05 dejaron. Se cierran en una tarea porque comparten causa: el criterio del campo nuevo estaba escrito DOS veces y ninguna de las dos coincidía con la otra ni con lo documentado. (1) **Parseo**: `[^\S\n]*` en lugar de `\s*` en los campos `Changelog`, `Descripción` y `Archivos` de `changelog-sync.py` — con `re.M`, `\s*` se come el `\n` y un campo VACÍO capturaba la línea siguiente entera; el bloque de una tarea ahora cierra en cualquier `^## ` (mismo criterio que `ledger-lint.py`), así que la cola del ledger deja de contar como parte de la última tarea; el patrón del campo pasa a ser UNO, `CHANGELOG_FIELD_PATTERN`, replicado literal en los dos scripts con test que compara las cadenas byte a byte y los dos parsers sobre la misma tabla de casos. (2) **Frases**: constante `ABREVIATURAS` que descarta los candidatos de `FIN_FRASE` que solo cierran una abreviatura, y el aviso de recorte solo sale cuando de verdad se recortó. (3) **Marcado**: `normaliza_resumen()` CIERRA la negrita en vez de borrarla (lo que decían su docstring y el nombre de su test), `corte_principal()` cuenta los acentos graves por RUNS y no parte un enlace `[texto](destino)`, y `palabras_de_prosa()` admite `üÜçÇïÏ`. (4) **Placeholder y multilínea**: un `{{…}}` sin sustituir se ignora y avisa en los dos lados, el placeholder de la plantilla del `planner` baja de 274 a 66 caracteres, y la continuación indentada del campo se absorbe en los dos parsers en vez de perderse en silencio. (5) **Ruido y visibilidad**: `--check` avisa solo de las iniciativas realmente pendientes (las publicadas las salta `pendientes()` para siempre) más UNA línea con el total, y el bloque `degradacion` del `--json` expone por fin el dato que se afirmaba visible en `pendientes[].caminos`. (6) **Tests**: un caso con LITERALES por delimitador, por pareja y por tope, más los cuatro caminos en el test de `…`, el criterio T-03#6 fijado, `--warn-only` del campo y el equilibrio Markdown de los bullets reales del repo. (7) **Cifras**: se re-mide todo lo que la revisión no pudo reproducir y se pega lo que sale.
- **Changelog**: Un resumen vacío o a medio escribir en el ledger ya no se cuela en el CHANGELOG como si fuera la nota de la tarea, y el recorte a dos frases deja de comerse la segunda por una abreviatura.
- **Estado**: completado
- **Tiempo humano**: est. 4,5h · real 4,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,30h · real 0,30h (estimado)
- **Supervisión**: est. 0,08h · real 0,08h (estimado)
- **Archivos**: `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`, `skills/changelog-sync/SKILL.md`, `skills/changelog-sync/references/medicion-escalera.md`, `agent-kits/shared/ledger-lint.py`, `agent-kits/planner/templates/tasks.md`, `tests/test_ledger_lint.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md`, `docs/knowledge/README.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md`
- **Verificación** (ejecutada 2026-09-04):
  - **Reproducción del CRITICAL 1** (ledger real con `- **Changelog**:` vacío). ANTES: `ledger-lint` → `⚠️  T-01: campo **Changelog** VACÍO …` **exit 0** (solo aviso, como el diseño quiere) · `changelog-sync --check` → **no menciona T-01** (para él el campo tiene contenido) · publicado → `- **T-01 — Arranque sin config** - **Estado**: completado`. DESPUÉS: `--check` → `⚠️  demo: 1/1 tarea(s) sin \`- **Changelog**:\` [T-01] — su bullet degrada al título; …` · publicado → `- **T-01 — Arranque sin config** ([ledger](docs/roadmap/2026-05-05-demo/tasks.md))`. Unitario del patrón: `re.search(r"^- \*\*Changelog\*\*\s*:\s*(.*)$", b, re.M).group(1)` → `'- **Estado**: completado'`; con `[^\S\n]*` → `''`. El mismo unitario sobre `Descripción` (fallo ya presente en `a7a11b0`) → `'- **Estado**: completado'` → `''`
  - **Reproducción del IMPORTANT 2** (un `- **Changelog**: EJEMPLO DE DOCUMENTACION…` dentro de `## Notas de cierre`). ANTES: `- **T-02 — Segunda tarea** EJEMPLO DE DOCUMENTACION — esto NO es el resumen de ninguna tarea.` DESPUÉS: `- **T-02 — Segunda tarea** \`agent-kits/shared/loquesea.py\` gana tres subcomandos nuevos que hacen cosas distintas.` (cae al camino `corte`, como debe). Exposición medida: **21 de 29** ledgers del repo tienen cola tras su última `### T-XX` (de 4 a 148 líneas) y **13 de los 15 cerrados** tenían la última tarea expuesta<!--m:ledgers_con_cola=21,ledgers_totales=29,cerrados_con_cola=13,ledgers_cerrados=15--> (esta línea decía «12 de los 14»; son 13, y hoy lo mide `--medicion`)
  - **IMPORTANT 3**: `-  **Changelog**: Frase.` (dos espacios) y `  - **Changelog**: Frase.` (indentado) → ANTES `sync=NO · lint=SI`; DESPUÉS los dos `SI`, y `test_los_dos_parsers_del_campo_reconocen_LOS_MISMOS_casos` los enfrenta sobre 11 casos + `test_el_patron_del_campo_es_el_canonico_del_kit` compara las cadenas byte a byte
  - **IMPORTANT 4**: `resumen(None, "Corrige el orden Sr. Pérez en la firma del comentario. Ahora el CHANGELOG sale en dos idiomas.")` → ANTES `('Corrige el orden Sr. Pérez en la firma del comentario.', 'changelog', ['campo \`Changelog:\` de más de 2 frases — se usan las dos primeras'])`; DESPUÉS el texto ENTERO y `avisos=[]`. Igual con `vs.` y `p. ej.` seguidos de mayúscula
  - **IMPORTANT 5 — campaña de mutantes** (misma campaña, mismo fichero de tests, ejecutada en un árbol temporal): **intento 1 → 14 de 25 sobreviven** (`ABRE` sin `(`/`[`/`{`, `CIERRA` sin `]`, `CORTES` sin `;`/`—`/`–`/ambas rayas, corte por `(` desactivado, `RESUMEN_MAX` 200→120 y →400, `ARCHIVOS_MAX_TOCADOS` 2×→4×, `CORTE_MIN_PALABRAS` 5→1 y →9). **Ahora: 0 de 40 sobreviven** (las 25 anteriores + 15 del criterio nuevo: campo que se come el `\n`, `Descripción` idem, campo que exige `- ` exacto, bloque que no acaba en `^## `, `ABREVIATURAS` vacío / sin `vs.` / sin `sr.` / con `uu.`, placeholder ignorado, continuación no absorbida, negrita borrada en vez de cerrada, enlace Markdown sin guarda, acentos graves de uno en uno, `degradacion` sin `titulo`, prosa sin diéresis)
  - **IMPORTANT 9 — desglose por camino** (14 ledgers cerrados, 69 tareas, un bullet por tarea): `changelog` 6 · mediana **350** · máx **376** | `frase` 12 · 260 · 325 | `corte` 9 · 170 · 280 | `titulo` 42 · 115 · 168 | TOTAL 69 · 133 · **376**. El techo real del bullet completo es **376** (`changelog-brief/T-01`), no 325; descomposición del de 325 (`windows-console/T-06`): cabecera 83 + espacio + resumen **152** + lista de 3 ficheros **89** = 325 (el título en crudo mide **70**)
  - **IMPORTANT 7 — cifras re-medidas**: barrido de `CORTE_MIN_PALABRAS` 0..7 con tope 200 → `corte` = **41/21/15/14/10/9/7/6** (sin la puerta son **41**, no 34; el trasvase al valor elegido es **32**) · el RED histórico `15 failed, 15 passed` **no reproduce** (15+15=30 y hay 33 tests): la reproducción literal da `17 failed, 16 passed in 1.13s` · antes/después confirmados: antes mediana **660** · máx **2.163** · media **758** · `>400` **50/63** (100/126 con los dos idiomas)
  - **MINOR 10**: `changelog-sync --check` sobre el repo baja de **22 a 10 líneas** (los 13 avisos por iniciativa ya publicada eran ruido: `pendientes()` las salta para siempre) y queda `⚠️  resumen del campo \`Changelog:\`: 63/69 tarea(s) de 13/14 ledger(s) cerrados no lo traen y 42 bullet(s) degradan al título — detalle por camino en \`--check --json\` (\`degradacion.caminos\`)`. El comentario que decía «es el recordatorio que ve el release» era falso: `python3 scripts/release.py --dry-run 1.17.0 | grep -c 'sin .- \*\*Changelog'` → **0**
  - **RED antes de arreglar** (el fichero de tests de T-06 —57 casos, de los cuales **27 nuevos** y 3 retirados respecto a `5a51d7c`: el «24» que esta línea declaraba era el delta NETO, no los tests nuevos— contra el script del intento 1, `git show 5a51d7c:…/changelog-sync.py` en un árbol temporal): `19 failed, 38 passed in 1.93s`, con los fallos nombrando exactamente los hallazgos (`test_campo_changelog_VACIO_no_publica_la_linea_siguiente`, `test_el_bloque_de_la_tarea_termina_en_la_cola_del_ledger`, `test_los_dos_parsers_del_campo_reconocen_LOS_MISMOS_casos`, `test_una_abreviatura_no_cierra_frase_y_el_aviso_no_miente`, `test_normaliza_cierra_la_negrita_que_el_corte_dejo_abierta`, `test_corte_no_parte_un_enlace_markdown`, …). GREEN después: `57 passed in 1.93s`
  - **Batería completa**:
    ```
    python3 -m pytest -q                                   → 878 passed in 38.28s
    PYTHONIOENCODING=cp1252 python3 -m pytest -q           → 878 passed in 39.45s
    python3 scripts/lint_plugin.py                         → lint_plugin: 9 agentes · 0 errores · 3 avisos   (exit 0)
    python3 tests/test_lint_plugin.py                      → test_lint_plugin: 32/32 OK                      (exit 0)
    python3 tests/test_ledger_lint.py                      → test_ledger_lint: 20/20 OK                      (exit 0)
    python3 evals/check.py                                 → 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores   (exit 0)
    ledger-lint.py docs/roadmap/2026-09-04-changelog-brief/tasks.md
                                                           → ledger-lint: 0 incoherencias · 0 avisos (tasks.md)   (exit 0)
    scope-check.py docs/roadmap/2026-09-04-changelog-brief --base a7a11b0
                                                           → 18 fichero(s) cambiado(s) · 35 patrón(es) declarados · ✅ 18 en alcance · ❌ 0 fuera   (exit 0)
    export-skills.py --out <tmp> && --check <tmp>          → export-skills --check: 106 ficheros · 0 problema(s)   (exit 0)
    git status --porcelain | grep -c CHANGELOG             → 0
    ```
- **Notas**: no se toca `RESUMEN_MAX`. El desglose por camino dice que el camino que la iniciativa PROMUEVE es el que produce los bullets más largos (`changelog` mediana 350 · máximo 376 frente a `titulo` mediana 115), pero eso no es un fallo del tope: `RESUMEN_MAX` acota el resumen y el resto lo ponen el título del ledger y la lista de ficheros. Lo que había que arreglar era la afirmación, y está arreglada en los tres sitios donde vivía. La nota fina de la revisión sobre `üÜçÇ` se recoge a medias: los ejemplos que daba (`lingüística`, `argüir`) SÍ contaban ya —basta una racha de dos letras, y la tienen en `ling` y `arg`—, así que la afirmación era falsa; el hueco real (una palabra cuyas únicas rachas incluyan `ü`/`ç`, como `güe`) sí existía y se cierra.

**Criterios de aceptación**
- [x] Un `- **Changelog**:` VACÍO degrada al título (no publica la línea siguiente del ledger) y `--check` lo NOMBRA; el mismo arreglo cubre `Descripción`, donde el fallo era anterior a esta iniciativa
- [x] El bloque de una tarea termina en cualquier `^## `, así que un `- **Changelog**:` citado en la cola del ledger no se atribuye a la última tarea
- [x] Un solo criterio para el campo en los dos parsers (`CHANGELOG_FIELD_PATTERN` replicado literal), con test que compara las cadenas y otro que los enfrenta sobre la misma tabla de casos
- [x] Una abreviatura seguida de mayúscula no cierra frase (lista en `ABREVIATURAS`, un caso por abreviatura) y el aviso de recorte solo sale cuando se ha recortado
- [x] Los tests fijan el contrato con LITERALES: un caso por delimitador (`:`, `;`, `—`, `–`, `(`), por pareja (`[`, `{`, `«`) y por tope (200, 2, 3, 6, 5); la campaña de mutantes pasa de 14 supervivientes de 25 a 0 de 40
- [x] «13 ledgers cerrados, 63 tareas» corregido en los 10 ficheros donde decía «los 63 ledgers», y `ADR-012` ya no se contradice consigo mismo
- [x] Las tres cifras que no reproducían están re-medidas y pegadas, y el RED histórico que no se puede reproducir se dice así en vez de inventar un número
- [x] La degradación al título es visible DE VERDAD (`--check --json` → `degradacion.caminos`, sobre todo ledger cerrado) y la doc ya no la promete en `pendientes[].caminos`
- [x] Las cifras de la doc dicen la verdad: desglose por camino y techo real del bullet completo medido con los títulos y rutas del repo, sin tocar `RESUMEN_MAX`
- [x] `--check` avisa solo de las iniciativas realmente pendientes, con UNA línea de total, y el comentario falso sobre `release.py` está borrado
- [x] Un campo que ES el placeholder `{{…}}` sin sustituir no llega al CHANGELOG, se avisa en los dos lados y el de la plantilla es corto. **Cualificado en T-07**, porque tal y como estaba escrito era falso por los dos lados: solo cubría `Descripción` a partir de T-07 (hasta entonces un `{{…}}` en la `Descripción` se publicaba literal) y descartaba texto humano que CITA un `{{…}}` (el criterio era «lo menciona», no «lo es»)
- [x] La continuación indentada del campo se absorbe en los dos parsers (no se pierde en silencio)
- [x] `normaliza_resumen()` cierra la negrita (contrato = implementación) y `corte_principal()` no parte un enlace Markdown ni un tramo de doble acento grave
- [x] Suite completa verde, con `PYTHONIOENCODING=cp1252` también, y ningún `CHANGELOG*.md` modificado

### T-07 — Cierre de los gaps del intento 2 (la cifra la imprime el script, no la prosa)

- **Descripción**: la revisión de dos lentes del intento 2 coincidió en un diagnóstico que es el hallazgo principal: **tres de los cuatro IMPORTANT son de la misma clase que T-06 venía a cerrar** — una cifra escrita a mano en la prosa que no reproduce. Corregir nueve números a mano garantiza un décimo, así que el arreglo de esa clase va PRIMERO y es estructural: `changelog-sync.py --medicion` mide 178 cifras desde el árbol de trabajo (los dos corpus, los caminos de la escalera, mediana/máximo/media del bullet por camino, los dos barridos de topes, la tabla de umbrales de `Archivos`, la descomposición del bullet más largo, las colas de ledger, `len(ABREVIATURAS)` y el placeholder de la plantilla) y `tests/test_cifras_medidas.py` compara con ella cada cifra MARCADA de la referencia, `SKILL.md`, `ADR-012`, el índice de knowledge, `docs/CONVENTIONS.md` + espejo EN y este ledger. **Elección del mecanismo** (marcar en vez de «concentra y enlaza»): la convención del repo es que la prosa AFIRME con la salida medida —prohibir el número dejaría un ADR que no dice su consecuencia— y la duplicación es OBLIGATORIA en parte del corpus, porque `docs/CONVENTIONS.md` y su espejo EN tienen que decir lo mismo; el marcador hace la duplicación SEGURA en vez de prohibirla, y de paso permite comprobar que los dos espejos afirman las mismas claves. Lo que NO es medible de forma determinista (el «antes» lo midió el script de `a7a11b0`, que un clon superficial de CI no tiene) va marcado como **no verificable con motivo**, y el test exige el motivo. Encima de eso, los seis IMPORTANT: (1) `frases()` incumplía su tope en silencio y el aviso mentía — `separa_frases()` es la fuente única de «cuántas frases hay», y `etc.` sale de `ABREVIATURAS` por el mismo motivo que `uu.` ya estaba fuera; (2) `normaliza_resumen()` contaba los `**` DENTRO de los tramos de código y publicaba un `**` huérfano que se come el párrafo — `sin_codigo()` es ahora el criterio único, el mismo que ya usaba el test; (3) la guarda de placeholder descartaba texto humano que CITA un `{{…}}` — el criterio pasa a ser «el campo ES el placeholder», y cubre también `Descripción`; (4) los dos parsers seguían sin reconocer lo mismo (un campo indentado bajo `- **Verificación**:` lo publicaba el generador y el linter lo daba por ausente) y el test que lo afirmaba comparaba dos REGEX sobre una línea: ahora enfrenta los dos PARSERS sobre 12 bloques de ledger reales, y hay tres criterios de bloque replicados literal (valla de código, campo del ledger, continuación de prosa); (5) `degradacion` contaba un placeholder como campo escrito y reportaba 0 deuda justo en el caso que la plantilla crea — `campo_escrito()` es la fuente única y el bloque gana `sin_campo_por_motivo`; (6) los cuatro mutantes genuinos que sobrevivían tienen test, el test tautológico del `SLUG_PENDIENTE` afirma el contrato de verdad, y la campaña es un script versionado (`scripts/mutantes.py`, 56 mutantes con su motivo) para que «N de M muertos» sea auditable. Y (7): la puerta local pasa a ser la de CI en los dos sentidos. Los MINOR 8-13 se cierran con el mismo material.
- **Changelog**: Las cifras que la doc afirma las mide ahora el script y las compara la suite. Y un resumen escrito a mano deja de perderse por citar una plantilla, por acabar en abreviatura o por llevar un glob.
- **Estado**: completado
- **Tiempo humano**: est. 5,8h · real 5,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,35h · real 0,35h (estimado)
- **Supervisión**: est. 0,09h · real 0,09h (estimado)
- **Archivos**: `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`, `skills/changelog-sync/scripts/mutantes.py` (nuevo), `skills/changelog-sync/SKILL.md`, `skills/changelog-sync/references/medicion-escalera.md`, `agent-kits/shared/ledger-lint.py`, `tests/test_cifras_medidas.py` (nuevo), `tests/test_suites_no_pytest.py` (nuevo), `tests/test_ledger_lint.py`, `tests/test_console_encoding.py`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md`, `docs/knowledge/README.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md`
- **Verificación** (ejecutada 2026-09-04):
  - **CLASE — la cifra la imprime el script.** `python3 skills/changelog-sync/scripts/changelog-sync.py --medicion | tail -1` → `changelog-sync --medicion: 178 cifra(s) medidas (corpus de hoy 14 ledger(s) / 69 tarea(s); corpus base < 2026-09-04: 13 / 63)`, **exit 0**. `python3 -m pytest -q tests/test_cifras_medidas.py` → `251 passed in 0.38s`. **ROJO demostrado volviendo a poner el error original** (`changelog_mediana=354` en `docs/knowledge/README.md`): `1 failed, 250 passed` con `AssertionError: docs/knowledge/README.md:58: la doc dice changelog_mediana = 354 y la medición de hoy dice 350 — corrige la prosa (o el código)`. El mecanismo se cazó a sí mismo dos veces durante la tarea: sacar `etc.` de `ABREVIATURAS` puso en rojo `abreviaturas=27` en la referencia Y en este ledger (27 → 26), que es exactamente lo que se quería
  - **Las nueve cifras.** `mediana 354` → **350** (`docs/knowledge/README.md:58`; las otras cuatro apariciones ya decían 350) · `ADR-012` encabezaba «los mismos 13 ledgers (63 tareas)» una tabla que suma **69** porque la fila `changelog` solo existe en el 14.º ledger → la tabla dice ahora su corpus por fila y el total 69 · «de 274 a **66** caracteres» → **55** (medido: `len(m.group("txt").strip())` sobre la plantilla del `planner`) · «**12** de los 14 cerrados tenían la última tarea expuesta» → **13** (medido: 13 de 14, y 21 de 28 en total) · «los **24** tests nuevos» → **27** añadidos y 3 retirados respecto a `5a51d7c` (24 es el delta NETO; medido con `comm` sobre los nombres de test) · «las **28** formas frecuentes» → `len(ABREVIATURAS)` era **27** y hoy es **26** · y el criterio `- [x]` T-03#1, que decía que `--check` nombra las tareas «por ledger cerrado», justo lo que T-06 cambió a propósito: reescrito para decir lo que hace el código, con la nota de que quedó marcado como cumplido diciendo lo contrario
  - **IMPORTANT 1 — `frases()` cumple su tope.** ANTES: `frases("Primera frase corta. Anade soporte para rutas, globs, etc. Tercera frase que NO deberia publicarse.", 2)` → **el texto ENTERO**, y `resumen()` → `avisos=[]` (ningún aviso); con 4 frases y `etc.` al final de la 2.ª → 3 frases y `['campo \`Changelog:\` recortado a las 2 primeras frases (traía más)']`, que **miente**. DESPUÉS: `'Primera frase corta. Anade soporte para rutas, globs, etc.'` con `['campo \`Changelog:\` recortado a las 2 primeras frases (traía 3)']`, y el de cuatro → `'Uno de prueba. Dos con etc.'` con `(traía 4)`
  - **IMPORTANT 2 — la negrita, fuera del código.** ANTES: `normaliza_resumen("\`evals/**\` y el resto de piezas")` → `` '`evals/**` y el resto de piezas**.' `` y, de punta a punta con `tdesc="Cubre \`evals/**\` y los tres kits del plugin sin tocar nada mas."`, el bullet salía `… sin tocar nada mas**. (\`a.py\`)` — un `**` que abre una negrita sin cerrar. DESPUÉS: `` '`evals/**` y el resto de piezas.' `` y `- **T-01 — Hacer la cosa** Cubre \`evals/**\` y los tres kits del plugin sin tocar nada más. (\`a.py\`, \`b.md\`, \`c.json\`)`. Las **178 cifras de `--medicion` no se mueven** con el cambio de criterio (diff de la salida antes/después: vacío)
  - **IMPORTANT 3 — un `{{…}}` citado es texto humano.** ANTES los dos campos siguientes se DESCARTABAN (bullet degradado al título) y el aviso diagnosticaba «placeholder sin sustituir»: ``Ahora la plantilla del planner trae `{{qué cambia para quien USA el proyecto}}` en vez del párrafo largo.`` y `El generador acepta {{slug}} y {{fecha}} en el nombre de la sección.`. DESPUÉS los dos se publican tal cual (`camino='changelog'`, `avisos=[]`), y el campo que ES el placeholder sigue degradando con aviso. MINOR 11: `resumen("{{Qué hay que hacer y por qué, en 1-3 frases.}}", None)` pasa de `('{{Qué hay que hacer y por qué, en 1-3 frases.}}.', 'frase', [])` a `('', 'titulo', ['campo \`Descripción:\` sin sustituir …'])`
  - **IMPORTANT 4 — los dos parsers.** Con el campo indentado bajo `- **Verificación**:` + sub-lista, ANTES: `cs.tareas()` → `'ABSORBIDO POR VERIFICACION?'` (lo publicaba) y `ll.parse_ledger()` → `None` (avisaba «sin campo Changelog»). DESPUÉS los dos → `'ABSORBIDO POR VERIFICACION?'`, y `verificacion_items == ['\`pytest -q\` → verde']`. El test compara ahora los dos PARSERS sobre 12 bloques reales; comprobado que caza el bug: revertir el corte de la sub-lista da `FAILED …::test_los_dos_PARSERS_leen_el_mismo_campo_en_un_bloque_real[campo indentado bajo Verificación con sub-lista]`. Los **28 ledgers del repo dan salida de `ledger-lint` IDÉNTICA** antes y después (diff vacío)
  - **IMPORTANT 5 — la deuda.** Ledger cerrado y ya publicado cuya única tarea trae el placeholder de la plantilla. ANTES: `--check` → `changelog-sync --check: sin entradas pendientes ✅` y nada más, **exit 0**; `--json` → `degradacion: {'caminos': {'frase': 1}, 'sin_campo': 0, 'ledgers_sin_campo': 0}`. DESPUÉS: `⚠️  resumen del campo \`Changelog:\`: 1/1 tarea(s) de 1/1 ledger(s) cerrados no lo traen (1 placeholder) y 0 bullet(s) degradan al título — detalle por camino en \`--check --json\` (\`degradacion.caminos\`)` y `degradacion: {'sin_campo': 1, 'ledgers_sin_campo': 1, 'sin_campo_por_motivo': {'ausente': 0, 'vacio': 0, 'placeholder': 1}}`
  - **IMPORTANT 6 — mutantes, con arnés versionado.** `python3 skills/changelog-sync/scripts/mutantes.py -q | tail -1` → `mutantes: 56/56 muertos`, **exit 0**; `--list` → `mutantes: 56 en la lista`. Los cuatro supervivientes que las dos lentes compartían, con su reproducción medida: `RE_CAMPO_ARCH` con `\s*` daba `['x.py','y.py']` INVENTADOS (y `['pytest -q']`); sin la frontera de palabra, `primera_frase("Mejora la red. Ahora va más rápido. Y una tercera.")` pasaba de `'Mejora la red.'` a dos frases; `elif cerco == run:` → `else:` hacía que `corte_principal("Cambia el flag \`\`a\`b:c\`\` del script y ya está")` pasara de `None` a `'Cambia el flag \`\`a\`b'`; y quitar `*` de `FIN_FRASE` convertía `"Arregla el parseo. **(1)** El campo vacío. **(2)** La cola del ledger."` en UNA frase. La guarda de bit-rot del arnés (`test_el_arnes_de_mutantes_esta_al_dia`) ya sirvió: cazó tres `busca` ambiguos (`RESUMEN_MAX = 200` aparece también en su comentario) que habrían contado como muertos sin probar nada. El recuento del intento 1 estaba mal por los dos extremos y así está escrito
  - **IMPORTANT 7 — la puerta local es la de CI.** `python3 -m pytest --collect-only -q tests/test_ledger_lint.py` → `no tests collected`; **8 de los 18 `tests/test_*.py` no tienen ni un `def test_*`**. Y el hueco simétrico, que la revisión no nombró: el paso pytest de `ci.yml` no incluía `tests`, y el bucle ejecuta `python tests/test_X.py`, que en los **3 ficheros sin bloque `__main__`** (`test_export_skills`, `test_release`, `test_roadmap_index`) no ejecuta NADA → **68 casos no corrían en CI**. Arreglado por los dos lados sin duplicar casos. DEMOSTRACIÓN de que la puerta local ya es puerta: con la continuación indentada quitada de `ledger-lint.py`, `pytest -q` → `FAILED tests/test_suites_no_pytest.py::test_la_suite_script_pasa[test_ledger_lint.py]` (antes: verde)
  - **MINOR 8/9/10.** `### Fase 2` cierra ahora el bloque en los dos parsers (antes: `cs` `''` · `ll` `'BAJO FASE 2'`). Un `## Ejemplo` citado en una valla ```` ```markdown ```` ya no corta la tarea (antes los dos parsers perdían el campo real de debajo: `''` y `None`; ahora los dos leen `'ESTE CAMPO ES REAL Y ESTA DEBAJO DE LA VALLA.'`). La continuación indentada solo absorbe PROSA: `  1. \`pytest -q\`` bajo `- **Archivos**:` daba `archivos=['a.py','b.py','pytest -q','ruff']` y ahora `['a.py','b.py']`; un `  **Estado**: completado` bajo el campo daba `changelog='Una frase. **Estado**: completado'` y ahora `'Una frase.'`
  - **MINOR 12.** `palabras_de_prosa()` decía «completitud del español y del catalán» sin `à è ò À È Ò`; añadidos (0 cifras movidas)
  - **Batería completa**:
    ```
    python3 -m pytest -q                                   → 1174 passed in 43.33s        (exit 0)
    PYTHONIOENCODING=cp1252 python3 -m pytest -q           → 1174 passed in 43.36s        (exit 0)
    python3 scripts/lint_plugin.py                         → lint_plugin: 9 agentes · 0 errores · 3 avisos   (exit 0)
    python3 tests/test_lint_plugin.py                      → test_lint_plugin: 32/32 OK   (exit 0)
    python3 tests/test_ledger_lint.py                      → test_ledger_lint: 21/21 OK   (exit 0)
    python3 evals/check.py                                 → 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores   (exit 0)
    ledger-lint.py docs/roadmap/2026-09-04-changelog-brief/tasks.md
                                                           → ledger-lint: 0 incoherencias · 0 avisos (tasks.md)   (exit 0)
    scope-check.py docs/roadmap/2026-09-04-changelog-brief --base a7a11b0
                                                           → 24 fichero(s) cambiado(s) · 51 patrón(es) declarados · ✅ 24 en alcance · ❌ 0 fuera   (exit 0)
    export-skills.py --out <tmp> && --check <tmp>          → export-skills --check: 107 ficheros · 0 problema(s)   (exit 0)
    mutantes.py -q                                         → mutantes: 56/56 muertos      (exit 0)
    git status --porcelain | grep -c CHANGELOG             → 0
    ```
  - **El bucle de `ci.yml` completo, tal como lo ejecuta CI** (los 6 pasos, en orden, con `pip install pytest` ya satisfecho):
    ```
    python scripts/lint_plugin.py            → lint_plugin: 9 agentes · 0 errores · 3 avisos
    python evals/check.py                    → 38 ficheros · 133 casos … · 0 errores
    for t in tests/test_*.py; …              → 19 ficheros, exit 0 en todos
    python -m pytest tests agent-kits/shared skills/… evals -q
                                             → 1174 passed in 44.28s
    (sintaxis de todos los .py)              → sintaxis OK
    (JSONs válidos + release.py --check)     → JSONs OK · release: versión 1.16.0 coherente
    ```
- **Notas**: no se toca `RESUMEN_MAX` ni ningún otro tope. Dos decisiones de criterio que conviene tener escritas. (a) **`etc.` sale de `ABREVIATURAS`**: la guarda es para abreviaturas de EN MEDIO de la frase (`Sr. Pérez`, `vs. Claude`, `p. ej. Windows`), no para las que la terminan — «… rutas, globs, etc. Tercera frase.» son dos frases, exactamente el mismo argumento por el que `uu.` ya estaba fuera. (b) **el criterio de placeholder es «el campo ES el placeholder»**, y se descartó «empieza por `{{`» porque «`{{slug}}` ahora se acepta.» es una frase humana: el sesgo es siempre publicar lo que escribió una persona. Del arnés de mutantes se retiraron DOS por equivalentes, anotados en el script con su argumento, para que el recuento signifique algo — uno de ellos es el `RESUMEN_MAX 200→400` que hacía que «14 de 25» sobre-contase. La sección «Revisión de dos lentes» del intento 2 la escribe el usuario; este ledger se entrega sin ella a propósito.

**Criterios de aceptación**
- [x] La CLASE va primero y es estructural: las cifras medibles las imprime el script (`--medicion`, 178) y un test compara la prosa contra la medición viva, con el mecanismo elegido y JUSTIFICADO por escrito
- [x] El test de cifras se pone ROJO al mutar una cifra (demostrado con el error original, `354` por `350`, y con el mensaje literal)
- [x] Las cifras no medibles de forma determinista están marcadas como NO verificables CON motivo, y el test exige el motivo en vez de fingir que reproducen
- [x] Las nueve cifras corregidas y el criterio T-03#1 reescrito para decir lo que hace el código
- [x] `frases()` cumple su tope (`separa_frases()` como fuente única) y el aviso dice cuántas frases traía; `etc.` fuera de la guarda, con su motivo y su test
- [x] `normaliza_resumen()` cuenta los `**` FUERA de los tramos de código, con el mismo criterio que su test (`sin_codigo()`, fuente única de las tres funciones que lo necesitan)
- [x] Un `{{…}}` citado no descarta texto humano: criterio «el campo ES el placeholder», escrito, con tests en los dos sentidos, replicado literal en los dos scripts y cubriendo también `Descripción`
- [x] Los dos parsers coinciden sobre BLOQUES de ledger reales (`Verificación` con sub-lista, `### Fase`, valla de código, cola tras la última tarea), con el test comparando los dos PARSERS y no dos regex sobre un `str`
- [x] La deuda cuenta un placeholder como campo sin escribir en los tres sitios, con el motivo desglosado (`ausente` · `vacio` · `placeholder`)
- [x] Un test por cada uno de los cuatro mutantes supervivientes, el test tautológico afirmando el contrato de verdad (con control positivo), y la campaña versionada y auditable (`mutantes: 56/56 muertos`)
- [x] La puerta local es la misma que la de CI en los dos sentidos, sin duplicar casos ni romper el bucle de `ci.yml`, y se dice qué otros `tests/test_*.py` estaban en la misma situación (8 sin `def test_*`, 3 sin `__main__`)
- [x] MINOR 8 a 13 cerrados, con la promesa del placeholder cualificada donde estaba escrita sin cualificar
- [x] Suite completa verde, con `PYTHONIOENCODING=cp1252` también, el bucle de `ci.yml` completo en verde y ningún `CHANGELOG*.md` modificado

---

## Notas de cierre

### El material no estaba, y eso es el hallazgo

La tentación era una función de resumen mejor. Medido, el problema no era el algoritmo: la
información «qué cambia para quien usa esto» **no está en el ledger en ninguna forma recortable**.
El paso 3 de la escalera (cortar en el primer delimitador de nivel superior) parecía la salida
elegante y rescata **9 de 63** tareas, porque en este repo las `Descripción` empiezan por la ruta
del fichero entre acentos graves seguida de `:` — así que el corte devuelve `` `docs/README.md` +
`docs/en/README.md` ``, que es peor que el título de la tarea. De ahí la puerta `CORTE_MIN_PALABRAS`
(palabras fuera del código) y, sobre todo, de ahí el campo: **un script no puede adivinar lo que
nadie escribió**.

### Lo que sigue saliendo pobre (medido, no tapado)

Con los ledgers del corpus base, **42 de 63 tareas (67 %) degradan al título**.<!--m:base_camino_titulo=42,base_tareas=63,base_degradan_titulo_pct=67--> Tres ejemplos
reales, con el bullet completo tal y como queda:

```
- **T-01 — Tiering de modelos CONFIGURABLE (dos capas)** ([ledger](docs/roadmap/2026-09-03-parity-core/tasks.md))
- **T-04 — Integración, doc, memoria y cierre** ([ledger](docs/roadmap/2026-09-03-memory-health/tasks.md))
- **T-06 — Integración, doc, memoria y cierre** ([ledger](docs/roadmap/2026-09-03-superiority/tasks.md))
```

El primero es aceptable como titular. Los otros dos son **malos**: «Integración, doc, memoria y
cierre» no dice nada a quien lee una release, y el título se repite en tres iniciativas distintas.
El bullet es honesto (no finge saber más de lo que sabe) pero inútil, y solo lo arregla el campo
`Changelog:`. Dos casos más, del camino `corte`, que caben en el tope y aun así no son buenos:
`windows-console/T-01` → «Los **27 scripts Python versionados con caracteres no ASCII**.» (frase
nominal, sin verbo: no dice qué les pasó) y `activation-reliability/T-02` →
«`agent-kits/shared/skill-index.py` genera, DETERMINISTA desde los frontmatters.» (se corta tras una
coma y queda colgando).

### Antes / después sobre los 13 ledgers (63 tareas)

`--dry-run` sobre una copia del repo con los CHANGELOG vaciados (126 bullets = 63 tareas × 2 idiomas):

| | Mediana | Máximo | Media | Bullets > 400 chars |
|---|---|---|---|---|
| Antes (`a7a11b0`) | 660 | 2.163 | 758 | 100/126 |<!--m?:cifra historica: la fila ANTES la midio el script de a7a11b0-->
| Después | 128 | 325 | 153 | **0/126** |<!--m:base_bullet_mediana=128,base_bullet_max=325,base_bullet_media=153,base_bullet_mayores_400=0-->

Ese agregado engaña, y T-06 lo re-midió: la mediana de 128 sale de un corpus donde **42 de 63
bullets son solo el título**, o sea del camino que la iniciativa quiere EVITAR. Por camino:
`titulo` 42 · mediana 115 · máx 168 | `corte` 9 · 170 · 280 | `frase` 12 · 260 ·
325.<!--m:camino_titulo=42,titulo_mediana=115,titulo_max=168,camino_corte=9,corte_mediana=170,corte_max=280,camino_frase=12,frase_mediana=260,frase_max=325-->
Y con este ledger cerrado (15 ledgers, 72 tareas) aparece el camino que se promueve, que es **el
que produce los bullets más largos**: `changelog` 9 · mediana **347** · máx
**400**.<!--m:ledgers_cerrados=15,tareas=72,camino_changelog=9,changelog_mediana=347,changelog_max=400-->
El techo real del bullet completo es por tanto **400**, no 325.<!--m:bullet_max=400--> La descomposición del de 325 (`windows-console/T-06`) es
cabecera 83 + espacio + resumen **152** + lista de 3 ficheros **89** (una versión anterior decía
«resumen 150 · título 68 · lista 96»: el total 325 y la conclusión eran correctos, las tres
componentes no).<!--m:base_peor_cabecera=83,base_peor_resumen=152,base_peor_ficheros=89,base_bullet_max=325-->
El título es del ledger y no se toca, y `RESUMEN_MAX` tampoco: acota el resumen.

### Consecuencia deliberada: `changelog-sync --check` queda en rojo

Con el ledger de esta iniciativa en `completado` y sin su entrada en el CHANGELOG, el propio
`--check` sale **exit 1** con `· changelog-brief (2026-09-04) — Changed, 6 tarea(s) → falta en
CHANGELOG.md, CHANGELOG.es.md`. Es correcto y es a propósito: **las notas de esta iniciativa las
escribe el usuario**, y ese exit 1 es aviso en `release.py`, no bloqueo (`superiority` T-02).
El mecanismo se probó sobre sí mismo dos veces: el `--check` cazó el `Changelog:` de T-01 con
**219 caracteres** (`campo \`Changelog:\` de 219 caracteres (tope 200)`) y se acortó a 169; y al
corregir «los 63 ledgers» dentro del propio campo de T-05 lo empujó de 196 a **205**, el aviso
volvió a saltar y se acortó a 196. Un tope que no avisa sobre su propio ledger no sirve.

### Verificación final (batería completa, 2026-09-04 — tras cerrar T-06)

```
python3 -m pytest -q                                   → 878 passed in 38.28s
PYTHONIOENCODING=cp1252 python3 -m pytest -q           → 878 passed in 39.45s
python3 scripts/lint_plugin.py                         → lint_plugin: 9 agentes · 0 errores · 3 avisos   (exit 0)
python3 tests/test_lint_plugin.py                      → test_lint_plugin: 32/32 OK                      (exit 0)
python3 tests/test_ledger_lint.py                      → test_ledger_lint: 20/20 OK                      (exit 0)
python3 evals/check.py                                 → 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas · 0 errores   (exit 0)
ledger-lint.py docs/roadmap/2026-09-04-changelog-brief/tasks.md
                                                       → ledger-lint: 0 incoherencias · 0 avisos (tasks.md)   (exit 0)
scope-check.py docs/roadmap/2026-09-04-changelog-brief --base a7a11b0
                                                       → 18 fichero(s) cambiado(s) · 35 patrón(es) declarados · ✅ 18 en alcance · ❌ 0 fuera   (exit 0)
export-skills.py --out <tmp> && --check <tmp>          → export-skills --check: 106 ficheros · 0 problema(s)   (exit 0)
```

Punto de partida: **833 passed** en `a7a11b0`. Los **45** nuevos son 44 de
`skills/changelog-sync/scripts/test_changelog_sync.py` (13 → 33 en T-01/T-02, 33 → 57 en T-06) y 1
de la fila del roadmap (`tests/test_roadmap_index.py` parametriza por iniciativa); `test_ledger_lint`
no cuenta aquí porque es un script propio (16 → 20 casos). Los 3 avisos del linter son los nombres
genéricos de `retro`/`roadmap-status`/`setup`, preexistentes.

### Deuda anotada (no en esta iniciativa)

- **La skill NO traduce, y ahora que su salida se usa eso se nota.** Los ledgers de este repo están
  en español y la escalera copia el campo `Changelog:` **literal**, así que `CHANGELOG.md` —el
  fichero inglés— recibe texto español. Medido al generar las notas de ESTA iniciativa: la sección
  ES se publicó tal cual salió del script; la EN hubo que traducirla a mano. Es anterior a la
  iniciativa (antes no se veía porque nadie usaba la salida) y **no se arregla aquí**: un script
  determinista no debe inventar una traducción. Las dos formas honestas son un segundo campo
  opcional (`- **Changelog (en)**:`, con degradación al español y aviso) o aceptar que el fichero
  inglés lleva una pasada humana — y esa decisión pide su propia iniciativa, no un parche.
- **Los 13 ledgers cerrados no tienen el campo** y no se reescriben (decisión: `ADR-012`). Se irá
  cerrando ledger a ledger; la degradación es visible en `--check --json` → `degradacion.caminos`,
  que recorre TODO ledger cerrado. (Hasta T-06 esta línea decía `pendientes[].caminos`, y era
  falso: `pendientes[]` solo lista lo que FALTA en el CHANGELOG, así que hoy son 1 iniciativa y las
  degradadas no aparecían ahí. El bloque `degradacion` se añadió para que el dato exista.)
- **El puntero al ledger se repite** una vez por bullet degradado (58 caracteres), así que dentro de
  una subsección con 6 tareas degradadas aparece 6 veces el mismo enlace. Renderizado son 6
  «ledger», pero en el fichero es repetición. La alternativa (un puntero por subsección) está
  descartada en `ADR-012` con su motivo; si al leer las notas molesta, es un cambio de una línea en
  `bullets()`.
- **`RESUMEN_MAX` no acota el bullet completo**, solo el resumen. Techo real medido con los títulos
  y las rutas de este repo: **400 caracteres** (`changelog-brief/T-01`, camino `changelog`), no
  325.<!--m:bullet_max=400-->
  Y el desglose por camino dice algo incómodo que la doc ahora escribe: el camino que la iniciativa
  PROMUEVE es el que produce los bullets más largos (`changelog` mediana 350 · máximo 376;
  `titulo` mediana 115 · máximo 168). Es el precio de que el bullet DIGA algo, no un fallo del
  tope: no se toca el título ni `RESUMEN_MAX`.
- ~~**Los avisos de `--check` crecen con los ledgers cerrados**~~ — saldado en T-06: eran 13 líneas
  de ruido puro (todas de iniciativas ya publicadas, que `pendientes()` salta para siempre) y ahora
  el aviso por iniciativa sale solo para las realmente pendientes, más UNA línea con el total.
  `--check` baja de 22 a 10 líneas sobre este repo.

### Deuda que deja T-06 (con su motivo)

- **`RESUMEN_FRASES_MAX` sigue siendo un tope TIPOGRÁFICO, no duro.** `FIN_FRASE` reconoce el fin
  de frase por «punto + espacio + apertura de frase», así que un campo cuyas frases empiecen en
  minúscula no se recorta nunca y no avisa. Se documenta en vez de arreglarse a propósito: el campo
  lo escribe una persona y el contrato es respetarlo tal cual (`ADR-012`); convertirlo en tope duro
  pediría segmentación de frases de verdad, que es justo el determinismo frágil que la iniciativa
  evita. Lo que sí es un tope real es la LONGITUD, y de eso avisa `RESUMEN_MAX` siempre.
- **La lista `ABREVIATURAS` es cerrada.** Cubre 26 formas frecuentes del español técnico (con
  `ee.` dentro, y `uu.` y `etc.` fuera: decidido, con motivo y con test),<!--m:abreviaturas=26-->
  pero una abreviatura no listada seguida de mayúscula seguirá pareciendo fin de frase. Ampliarla
  es una línea; detectarlas en general, no. (Esta línea decía «las 28 formas» y nunca fueron 28; la
  cifra la imprime ahora `--medicion` y la compara la suite.)
- **`normaliza_resumen()` solo cierra `**`.** Un `*` o un `_` suelto en medio del texto se deja tal
  cual: en este repo son casi siempre literales (`evals/**`, `docs/*`, nombres con guion bajo) y
  cerrarlos corrompería el texto. Exposición medida: **0 desbalanceados en los 69 bullets reales**,
  y ahora hay test (`test_los_bullets_reales_del_repo_estan_equilibrados_en_markdown`) que lo
  vigila en cada ejecución de la suite en vez de fiarse de un barrido de una vez (hoy son 72
  bullets).<!--m:tareas=72-->
- **Los 6 avisos de ledger legacy sin frontmatter siguen ahí** (`--check` los repite en cada
  ejecución). Es correcto —son ledgers que no se pueden sincronizar— y es anterior a esta
  iniciativa; si molestan, el arreglo natural es la misma receta que T-06 aplicó al aviso del
  campo: una línea con el total en vez de una por ledger.

---

## Revisión de dos lentes — intento 1: 12 gaps (8 Important, 4 Minor) → todos corregidos (T-06)

Lentes **A** (conformidad) y **B** (corrección) sobre `a7a11b0..5a51d7c`, en paralelo, por subagente genérico (el agente `reviewer` no estaba instalado en la sesión: degradación con aviso, §2.3 de la skill). Puerta previa: `scope-check.py --base a7a11b0` → exit 0, 18 ficheros, 0 fuera. Lente C no aplicó; lente D tampoco se lanzó (sin motivos: el diff no toca rutas ni patrones costosos).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | **Critical** | Un `- **Changelog**:` VACÍO capturaba la línea SIGUIENTE del ledger: `\s*` consume el `\n` (`re.M` no cambia `\s`). Se publicaba `- **Estado**: completado`, `- [x] criterio`, o **una fila de tabla** dentro del bullet. Lo grave: el campo vacío es un estado que el diseño declara tolerable, y `aviso_sin_changelog()` no podía avisar porque para él el campo tenía contenido — el único camino de detección quedaba cegado justo en el caso admitido | T-06 | `[^\S\n]*` en los dos `\s*`, y lo mismo en `Descripción` y `Archivos` (el fallo era anterior a la iniciativa en esos dos) | Antes: `- **T-01 — Arranque sin config** - **Estado**: completado`. Después: `…** ([ledger](…))` + el aviso que faltaba |
| 2 | Important | Un `Changelog:` de la COLA del ledger se atribuía a la última tarea: el `split` solo partía en `### T-XX`/`### Fase`, así que `## Notas de cierre` y las secciones de revisión quedaban dentro del bloque de la última tarea | T-06 | El bloque se cierra en cualquier `^##\s`, el mismo criterio que ya usaba `ledger-lint` | Medido: **21 de 28** ledgers tienen cola (4-148 líneas) y **13 de los 14 cerrados** tenían la última tarea expuesta |
| 3 | Important | Los dos parsers del campo nuevo no reconocían lo mismo: `changelog-sync` exigía `^- \*\*`, `ledger-lint` aceptaba `^\s*-\s*\*\*`. Con `-  **Changelog**:` (dos espacios) el linter callaba y **la frase escrita a mano se descartaba** | T-06 | Criterio único, replicado byte a byte, con test de coincidencia | 14 grafías: los dos aceptan y rechazan igual |
| 4 | Important | El recorte «a dos frases» contaba abreviaturas como fin de frase: un campo de EXACTAMENTE dos frases con `Sr.`/`vs.`/`p. ej.` perdía la segunda **y el aviso mentía** («de más de 2 frases» cuando había dos) | T-06 | Guarda de abreviaturas (27 formas, constante) y aviso solo cuando de verdad recortó | El test previo solo cubría `` `p. ej.` `` seguido de minúscula: el caso que el lookahead ya protegía |
| 5 | Important | Los tests se parametrizaban con las constantes que debían fijar: **14 de 25 mutantes sobrevivían**. De los cuatro delimitadores que enumeran el criterio, el ADR y el SKILL, solo `:` estaba fijado | T-06 | Contrato con literales; un caso por delimitador y por tope | 0 de 40 mutantes tras la ronda |
| 6 | Important | «los **63** ledgers cerrados» — son 13 ledgers y 63 tareas — repetido en 10 ficheros, y `ADR-012` se contradecía consigo mismo (`:16` vs `:67`) | T-06 | Corregido en los 10 | — |
| 7 | Important | Tres cifras declaradas que no reproducían: «rescataba 34 tareas» (son 41), el desglose «150 · 68 · 96» (152 · 70 · 86) y el RED «15 failed, 15 passed» (15+15=30 con 32 recolectados) | T-06 | Re-medidas; el RED se marca como no reproducible en vez de inventarse | Barrido `CORTE_MIN_PALABRAS` 0-7: 41/21/15/14/10/9/7/6 |
| 8 | Important | «el 67 % es visible en `--check --json` (`pendientes[].caminos`)» era falso: `pendientes[]` solo trae lo que falta en el CHANGELOG, así que hoy es 1 | T-06 | Bloque `degradacion` nuevo en `--json` sobre TODO ledger cerrado — se añadió el dato en vez de borrar la frase | `degradacion: {ledgers, tareas, caminos, sin_campo}` |
| 9 | Important | La cifra «después» medía sobre el camino que la iniciativa quiere EVITAR: mediana 128 con 42 de 63 bullets degradados al título, mientras el camino que se promueve produce los más largos (mediana 347, techo 376) y la deuda declaraba «325» | T-06 | Desglose **por camino** en la doc y techo real medido; `RESUMEN_MAX` sin tocar (acota el resumen, no el bullet) | Tabla por camino en `ADR-012` y en la referencia |
| 10 | Minor | El aviso de `--check` era 100 % ruido: 13 de sus 22 líneas eran iniciativas **ya publicadas**, que `pendientes()` salta para siempre; y el comentario que lo justificaba («es el recordatorio que ve el release») era falso — `release.py` no ve ninguna | T-06 | Una línea de total, sobre las realmente pendientes | `--dry-run 1.17.0 \| grep -c Changelog` → 0 |
| 11 | Minor | Campo multilínea perdido en silencio; placeholder de la plantilla (275 car.) publicado literal; `normaliza_resumen()` **borraba** la negrita en vez de cerrarla; `corte_principal` partía un enlace markdown; cortes dentro de tramos de código con doble acento grave | T-06 | Continuación soportada en los dos parsers; placeholder corto + aviso de `{{…}}`; acentos graves contados por runs | — |
| 12 | Minor | Tests que no discriminaban (dos pasaban también contra el script viejo), `SKILL.md` enlazando el ADR al directorio, y una Verificación con la salida de antes de cerrar el ledger | T-06 | Corregidos | — |

**Rebatido con evidencia y arbitrado a favor del implementador** (rebatir no consume intento): mi nota sobre `üÜçÇ` era falsa — `palabras_de_prosa` usa `re.search`, no `fullmatch`, así que «lingüística» ya contaba por `ling`. El hueco real era más estrecho (`"güe"`) y se cerró igual, con test que discrimina.

## Revisión de dos lentes — intento 2: 7 Important, 6 Minor → todos corregidos (T-07)

Lentes **A** y **B** sobre `5a51d7c..d2b05f9`, con la tabla del intento 1 traspasada. La Lente A verificó las 12 correcciones una a una reproduciendo el antes/después y las dio todas ✓; los 8 comandos de la Verificación reprodujeron literalmente, y las 20 cifras de la medición también.

**Las dos lentes coincidieron en un diagnóstico que cambió el arreglo:** tres de los cuatro Important eran **cifras escritas a mano en la prosa que no reproducen** — la misma clase que la iniciativa venía a cerrar. Corregir nueve números a mano garantizaba un décimo, así que T-07 atacó la clase.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 13 | Important | **Regresión**: la guarda de abreviaturas hacía que `frases()` incumpliera su tope **en silencio** cuando una frase real acababa en abreviatura de la lista (`etc.`, `vs.`, `cap.`…): publicaba 3 o 4 frases, y el aviso mentía | T-07 | `frases()` cumple el tope y el aviso dice la verdad | `frases(campo, 2)` → `'Primera frase corta. Anade soporte para rutas, globs, etc.'` — la 3.ª fuera |
| 14 | Important | `normaliza_resumen()` contaba `**` DENTRO de los tramos de código y publicaba un `**` huérfano que se come el resto del párrafo al renderizar. Lo llamativo: su propio test usaba el criterio correcto que a la función le faltaba | T-07 | La función usa el criterio de su test | `normaliza_resumen("Cubre \`evals/**\` y…")` ya no añade `**`; `"los **27 scripts"` → `"Los **27 scripts**."` |
| 15 | Important | La guarda de placeholder descartaba **texto humano legítimo** que citara `{{…}}` — en un repo cuyas plantillas van llenas de ellos, y siendo esa la frase que T-06 escribiría sobre su propio cambio | T-07 | Criterio: el campo **ES** el placeholder, no que lo mencione; un `{{…}}` en código no cuenta | Las dos citas → `False`; el placeholder de la plantilla → `True` |
| 16 | Important | Los dos parsers SEGUÍAN sin coincidir (campo indentado bajo `- **Verificación**:`: el generador lo publicaba, el linter lo daba por ausente), y el test que lo afirmaba **comparaba las dos regex sobre una línea suelta**, no los dos parsers sobre un bloque | T-07 | El test compara los PARSERS sobre bloques con contexto | Mutar `CONTINUACION_PATTERN` pone rojos `test_los_dos_PARSERS_leen_el_mismo_campo_en_un_bloque_real` y la igualdad byte a byte |
| 17 | Important | `degradacion` contaba un placeholder como campo ESCRITO: reportaba **0 deuda** justo en el caso que T-06 acababa de crear al meter el placeholder en la plantilla | T-07 | Un placeholder cuenta como campo sin escribir | — |
| 18 | Important | Cuatro mutantes genuinos sobrevivían, uno de ellos el Critical del intento 1 **replicado en `Archivos`** (arreglado en el código pero sin test); y `test_…_slug_pendiente_de_release` era **tautológico** (`⚠️` es `U+26A0 U+FE0F` y el `\s+` de la regex no puede consumir el selector de variación, así que ninguna línea con ese prefijo casa jamás) | T-07 | Un test por mutante, el tautológico afirma el contrato real, y **el arnés de mutantes se versiona** (`skills/changelog-sync/scripts/mutantes.py`) para que el recuento sea auditable | `mutantes: 56/56 muertos`, exit 0 |
| 19 | Important | `tests/test_ledger_lint.py` tiene **0 funciones `def test_*`**: sus casos nuevos NO estaban en la suite, solo en el bucle de `ci.yml`. Quitarle la continuación indentada dejaba `pytest` en verde | T-07 | `tests/test_suites_no_pytest.py`: la puerta local es la misma que la de CI | Mutación comprobada: ahora `pytest` da `3 failed`, uno de ellos `test_la_suite_script_pasa[test_ledger_lint.py]` |
| 21 | Minor | La prueba de cifras contaba como cifra a medir **su propia forma citada** en la doc: la traza de esta revisión, al documentar el marcador entre acentos graves, se puso roja a sí misma (`FAILED …[tasks.md:453:clave=valor]`) | T-07 | Una marca dentro de un tramo de código es una CITA, no una instancia — el mismo criterio que `es_placeholder()` con `{{…}}` | Mutar la guarda pone rojos los dos tests; sin ella, la doc del mecanismo es imposible de escribir |
| 20 | Minor | Seis latentes de exposición 0 con el mismo patrón: `### Fase` cerrando distinto en cada parser, el cierre en `^##` sin conciencia de vallas de código, `RE_CONTINUACION` absorbiendo tabla/lista/cita/código indentados, el guard de placeholder sin cubrir `Descripción`, la clase de letras sin catalán, y promesas sin cualificar | T-07 | Corregidos | — |

**El arreglo de la clase** (lo que pedí en vez de corregir nueve números): las cifras verificables van marcadas en la prosa con `<!--m:clave=valor-->` y `tests/test_cifras_medidas.py` **las compara contra la medición viva**, fallando cuando divergen; las que no son deterministas (un RED histórico) se marcan como no verificables en vez de fingir que lo son. Se demostró mutando una: `FAILED …[docs/knowledge/README.md:58:changelog_mediana=999]`. Y se cazó a sí mismo dos veces — al corregir «los 63 ledgers» dentro de un campo `Changelog:` lo empujó a 205 caracteres y saltó el aviso de tope; y al cerrar T-07, su propia tarea movió el corpus (camino `changelog` 6 → 7, total 69 → 70, mediana 350 → 347) y el test señaló las cinco apariciones una a una.

**Cierre del bucle.** Dos intentos de lente con contexto fresco, y el tercero verificado en la orquestación: reproduje los tres arreglos de comportamiento (13, 14 y 15), la mutación que demuestra la puerta nueva (19), la mutación que pone roja una cifra de la prosa, y el arnés de mutantes completo. Queda dicho: **la última ronda no ha pasado por una lente de contexto fresco**. Lo que la respalda son 1.174 tests verdes en las dos codificaciones, 56 de 56 mutantes muertos con arnés versionado, y el test de cifras que ya no deja que la prosa se separe de la medición.
