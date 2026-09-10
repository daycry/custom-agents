---
design: plugin-refactor
titulo: Cómo comparten código los scripts de un plugin cuyas piezas viajan sueltas
estado: aprobado
creado: 2026-09-10
actualizado: 2026-09-10
spec: spec.md
evaluacion: evaluation.md
plan: pendiente
adr: docs/knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md   # `propuesta`; pasa a `aceptada` con la revisión de dos lentes de C-03
opcion_elegida: O1      # elegida por el usuario en la puerta de diseño (2026-09-10)
validada_por_usuario: 2026-09-10
generacion:            # ACUMULADO de las dos pasadas (P1 opciones 08:45:49-08:56:26Z · P2 elección + ADR 09:21:55-09:30:46Z)
  inicio: 2026-09-10T08:45:49Z
  fin: 2026-09-10T09:30:46Z
  fuente: medido       # `usage-meter.py close` en verde en las dos pasadas (transcripciones ya visibles en esta máquina tras la vía rápida `usage-meter-transcripts`)
  tokens_reales: { entrada: 415, salida: 82119, cache_creacion: 259635, cache_lectura: 12543382, respuestas: 70 }
  eur: 9.16            # P1 5.45 + P2 3.71
  horas_ia: 0.71       # P1 0.44 + P2 0.27
  duracion: 42m        # 26m (P1) + 16m (P2)
  ratio_usado: 479326
  ratio_origen: CALIBRATION.md (mediana de 6)
---

# Diseño — Cómo comparten código los scripts de un plugin cuyas piezas viajan sueltas

> **Spec:** [`spec.md`](spec.md) (`aprobada`) · **Evaluación:** [`evaluation.md`](evaluation.md) (`completado`, go condicionado) · **Plan:** pendiente (lo crea el `planner`) · **ADR:** [`ADR-016`](../../knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md) (`propuesta`)

| | |
|---|---|
| **Estado** | `aprobado` — opción validada por el usuario |
| **Opción elegida** | **O1** — registro de copias declaradas + un test único, con la comprobación del linter sobre bloques idénticos no registrados |
| **Validada por el usuario** | 2026-09-10 |

> **Aviso de numeración.** La **O3 de este documento NO es la O3 del `analysis.md` §5**. La O3 del
> análisis (módulo común importado por ruta relativa) queda **descartada** y se recoge como tal en la §4.
> La O3 de aquí es una opción nueva salida del recon: copias **generadas dentro del repo**.

## 1. Contexto y restricciones

La spec `aprobada` separa el refactor en dos bloques y deja **una** decisión fuera: la del `analysis.md`
§5. La evaluación la convierte en arista del grafo — su go es **condicionado** «a llevar el §5 a
`architect` antes de abrir C-03» (`evaluation.md:371`), y C-03 («copias accidentales → declaradas o
eliminadas», 4,0 h con O1, +4,0 h con O2) está bloqueada hasta que este diseño esté `aprobado`. El
criterio de aceptación que cuelga de aquí es CA-05 (`spec.md:161`), que admite tres desenlaces:
registro comparado por UN test, eliminación, o vendorizado por el empaquetador.

El recon de hoy sobre el repo **corrige dos premisas del análisis** y cambia el peso de las opciones.

**Corrección 1 — no hay copias «accidentales»: hay cuatro mecanismos distintos sin registro.** Los
cuatro pares que el §2 clasifica como accidentales no lo son. Dos ya son el patrón «canónico por ruta +
respaldo local», declarado en su propio docstring; los otros dos no son código compartido, sino bloques
de `import` y la cabecera `Uso:`/`Exit:` del docstring que el detector de shingles cuenta como
duplicado. Estado real, verificado fichero a fichero:

| Mecanismo | Unidades compartidas y sitios reales | Guardarraíl hoy |
|---|---|---|
| **A** — bloque replicado literal entre marcadores `# --8<--` | `criterio de consola` (`scripts/lint_plugin.py:109-305` ↔ `tests/test_console_encoding.py:43-239`) · `celdas_md` (`scripts/lint_plugin.py:546-566` ↔ `agent-kits/shared/doctor.py:644-664` ↔ `agent-kits/shared/knowledge-find.py:244-264`) · `criterio del índice de knowledge` (`scripts/lint_plugin.py:569-655` ↔ `agent-kits/shared/doctor.py:667-753`) | **Test de identidad byte a byte** (`tests/test_console_encoding.py:801-804`, `tests/test_knowledge_index.py:198-203` y `:208-214`) |
| **B** — canónico cargado por ruta + constante de respaldo local | `REVISION_HDR_PATTERN` (`agent-kits/shared/ledger-lint.py:179`) → `agent-kits/shared/task-brief.py:576` y `skills/jira-sync/scripts/jira-flow.py:231` | **Test que compara las cadenas** (`agent-kits/shared/test_task_brief.py:1102`, `skills/jira-sync/scripts/test_jira_flow.py:361-364`) |
| **C** — canónico cargado por ruta + **función** de respaldo local | `glob_to_regex` (`skills/confluence-publish/scripts/confluence-scope.py:121`) → `agent-kits/shared/scope-check.py:46-77` y `skills/adversarial-review/scripts/review-lens-select.py:99-131` · `piezas()` (`evals/check.py:108`) → `scripts/lint_plugin.py:905` (carga en `:864-865`) | **Ninguno** |
| **D** — copia independiente, sin carga por ruta | `sin_vallas` (`agent-kits/shared/ledger-lint.py:101` ↔ `skills/changelog-sync/scripts/changelog-sync.py:120`) | **Test conductual**, no de identidad (`skills/changelog-sync/scripts/test_changelog_sync.py:931-944`: compara `VALLA_PATTERN`, `CAMPO_LEDGER_PATTERN`, `CONTINUACION_PATTERN` y la salida sobre un corpus) |
| — | `scripts/export-skills.py:36-43` ↔ `skills/jira-sync/scripts/jira-flow.py:83-90` (bloque de `import` + reconfiguración de consola) · `skills/code-health/scripts/code-health.py:27-40` ↔ `skills/dependency-upgrade/scripts/deps-inventory.py:29-40` (docstring `Uso:`/`Exit:` + `import`) | n/a — **no es código compartido** |

**Corrección 2 — el matiz del análisis del 2026-09-10 se pasa de largo con `sin_vallas`.** El análisis
afirma que ningún test relaciona `ledger-lint.py` con `changelog-sync.py`. Sí lo hay:
`skills/changelog-sync/scripts/test_changelog_sync.py:940` ejecuta las dos copias sobre el mismo corpus
y exige la misma salida. Lo que falta no es un test, es un test de **identidad**: dos implementaciones
que hoy coinciden pueden divergir en un caso que el corpus no cubre. El diagnóstico del análisis
(«diverge en silencio») sigue en pie; la causa es más fina.

**Corrección 3 — la premisa de portabilidad de O2 es más estrecha de lo que parece.** Verificado en los
tres empaquetadores:

- `scripts/export-interop.py:26-33` — «Las `skills/` **NO se copian** / **NO se traducen**»: el
  manifiesto apunta a `./skills/`. Este exportador **no tiene nada que vendorizar**.
- `install/providers.mjs:22` — `PAYLOAD_COMUN = ["skills", "agent-kits", "hooks"]`: el instalador `npx`
  copia `agent-kits/` **entero** a los tres runtimes (`docs/INTEROP.md:64`). Por la vía oficial de
  instalación, un `_comun.py` en `agent-kits/shared/` **ya está** junto a las skills, sin vendorizar nada.
- `scripts/export-skills.py:399` — `fragmentos_shared(root, textos_md)` parte **solo de los `.md`**. El
  cierre transitivo sobre nombres `.py` (`:172-176`) solo alcanza lo citado desde un `.md`. Un
  `_comun.py` referenciado únicamente desde el `.py` de una skill **no viajaría** en el paquete portable.

Es decir: el hueco real de portabilidad es **uno** (el paquete «solo skills» de `dist/`, ignorado por
git), no tres, y hoy se tapa con el respaldo local de los mecanismos B y C.

**Restricciones que fijan el espacio de soluciones**

- **Multi-runtime, no negociable** (requisito del usuario del 2026-09-09; `docs/INTEROP.md`): las skills
  viajan enteras y sin traducir. Ninguna opción puede hacer que una pieza instalada sola deje de
  funcionar. Esto **veta** el `import` por ruta relativa sin respaldo — la O3 del análisis.
- **Contratos congelados** (`analysis.md` §6.2): flags de CLI, exit codes, forma de los `--json` y
  `REVISION_HDR_PATTERN`. El bloque (a) no cambia comportamiento (`spec.md:129`).
- **Solo stdlib**; el guardarraíl es un script o un test con exit code, nunca prosa (regla de
  determinismo de `CLAUDE.md`).
- **Sin constitución en el repo** (`docs/CONSTITUTION.md` no existe): no hay principio que vetar ni citar.
- **ADR vigentes que acotan:** `ADR-008` (skills cortas — nada de esto engorda un `SKILL.md`),
  `ADR-011` («un rol, un dueño», aplicado aquí al **mecanismo**: cuatro para el mismo problema es el
  solape que el ADR prohíbe dejar implícito), `LES-013` (una capacidad que dos piezas necesitan no
  justifica una pieza nueva), `LES-012` (`--check` como puerta de CI y de `release.py`, precedente de
  `export-interop.py`), `GOT-003` (un generador que escribe dentro del árbol que espeja necesita
  nombres reservados y comprobar que el destino es suyo). Ninguno se reabre.
- **Presupuesto de la evaluación:** C-03 = 4,0 h con O1; **+4,0 h humanas y +0,5 h IA (~+245 € con
  margen) con O2** (`evaluation.md:157`, `:347`).

## 2. Opciones (2-3)

### O1 — Registro de copias declaradas + un test único

Un registro versionado (p. ej. `agent-kits/shared/copias.json`) lista cada **unidad compartida**: su
sitio canónico, sus sitios copia, el mecanismo (bloque `--8<--`, constante, función) y el guardarraíl
exigido. **Un** test recorre el registro y afirma identidad byte a byte para los bloques y los
literales; `scripts/lint_plugin.py` falla si aparece en el árbol un marcador `--8<--` o un
`_*_FALLBACK` que no esté registrado. La copia la sigue haciendo una persona; el test la recuerda.

Absorbe los cuatro mecanismos actuales en uno solo: C pasa a tener guardarraíl, D pasa de conductual a
identidad, A y B se registran sin cambiar una línea de su texto. Los dos pares que no son código
(`import` + docstring) se declaran como tales y salen del recuento.

| Criterio | Valoración |
|---|---|
| Complejidad | **Baja-Media** — el mecanismo existe tres veces (`tests/test_knowledge_index.py`, `tests/test_console_encoding.py`); lo nuevo es el registro, generalizar el test y una comprobación de «copia sin registrar» en el linter. Cero cambios en empaquetadores y cero en runtime |
| Riesgo | **Bajo** — el 7,6 % de duplicado **no baja** y hay que explicarlo (`spec.md` §7 dice que no es el objetivo, pero el número queda a la vista); un arreglo sigue obligando a tocar N sitios, y el test lo detecta en CI, no al editar; la detección de copias nuevas sin registrar es heurística (marcador o nombre), no exhaustiva |
| Coste relativo | **S** |
| Reversibilidad | **Alta** — un JSON, un test y una comprobación del linter. Borrarlos deja el árbol exactamente como hoy; ningún artefacto generado, ninguna puerta nueva de `release.py` |

### O2 — Módulo común vendorizado por el empaquetador

`agent-kits/shared/_comun.py` es la fuente de verdad. `scripts/export-skills.py` lo copia **dentro de
cada pieza** al empaquetar y `--check` verifica que la copia empaquetada coincide; en el árbol de
trabajo los scripts lo resuelven por ruta con el patrón `importlib.util.spec_from_file_location` que ya
usan cinco veces. Los respaldos locales de los mecanismos B y C desaparecen: el módulo siempre está.

El recon rebaja su premisa: `export-interop.py` no copia skills y `providers.mjs` ya lleva
`agent-kits/` entero, así que el vendorizado solo aporta en el paquete `dist/` de «solo skills», y
exige antes tapar el hueco de `export-skills.py:399` (hoy solo escanea `.md`).

| Criterio | Valoración |
|---|---|
| Complejidad | **Alta** — tocar el empaquetador (escaneo de `.py`, copia dentro de cada pieza, `--check` nuevo), reescribir cinco puntos de carga, retirar los respaldos y decidir el nombre reservado del fichero generado dentro de `skills/*/scripts/` |
| Riesgo | **Medio-Alto** — escribe un fichero generado dentro de carpetas editadas a mano: es la forma exacta del fallo de `GOT-003` (nombre reservado + comprobar que el destino es suyo) y del aviso de `ADR-015` (nada de cambio de modo silencioso), aquí sin la red del registro de `ADR-014` (que no existe todavía: `agent-kits/shared/pieces-registry.py` está pendiente en F2 de `project-specialization`). Retirar el respaldo local convierte «degrada con aviso» en «falla» si el vendorizado no llegó |
| Coste relativo | **L** — la evaluación lo cuantifica: +4,0 h humanas y +0,5 h IA sobre O1 (`evaluation.md:157`) |
| Reversibilidad | **Media-Baja** — una vez que `--check` es puerta de CI y de `release.py`, volver atrás es retirar una puerta y re-copiar a mano los cinco sitios; los paquetes ya publicados llevan la copia dentro |

### O3 — Copias generadas dentro del repo («vendorizado en el árbol»)

<!-- Recordatorio: esta O3 es la variante nueva, no la O3 descartada del analysis.md §5. -->

El bloque canónico vive una sola vez en `agent-kits/shared/`. Un `sync-copias.py` lo **escribe** en cada
sitio marcado con `# --8<--` dentro del propio repo, y `--check` es puerta de CI y de `release.py`
— literalmente el patrón de `scripts/export-interop.py` (`LES-012`). Nada cambia al empaquetar ni en
runtime: el árbol ya está siempre vendorizado, toda pieza sigue siendo standalone por construcción y el
arreglo se hace en un sitio.

Es un superconjunto de O1: necesita el mismo registro como entrada. La duplicación sigue en el repo
(el 7,6 % tampoco baja), pero deja de mantenerse a mano.

| Criterio | Valoración |
|---|---|
| Complejidad | **Media** — un generador y su `--check`; sin tocar empaquetadores, sin resolución en runtime, sin retirar respaldos. Los marcadores `--8<--` que necesita ya existen en cinco ficheros |
| Riesgo | **Medio** — un generador que escribe **dentro de ficheros fuente editados a mano** (`GOT-003`): un marcador mal cerrado pisa código real. Mitigable porque escribe solo entre los dos centinelas y nunca crea ni borra ficheros, pero exige el `assert` defensivo del precedente. Añade una puerta más a `release.py`, que ya tiene seis |
| Coste relativo | **M** |
| Reversibilidad | **Media** — borrar el generador deja las copias escritas y válidas (el árbol queda como en O1); lo irreversible barato es la puerta de CI |

## 3. Criterios de decisión

1. **Portabilidad multi-runtime: veto, no criterio.** Una opción que rompa una pieza instalada sola
   queda fuera sin comparar nada (requisito del usuario, `docs/INTEROP.md`).
2. **Coste de la vuelta atrás por delante del coste de construcción.** Mismo orden que usó el
   `design.md` de `project-specialization` (`ADR-014`). Esta iniciativa es un refactor con cero cambio
   de comportamiento: un mecanismo que luego haya que deshacer cuesta más que el que hay que construir.
3. **Un solo mecanismo (`ADR-011`).** Hoy hay cuatro para el mismo problema. La opción elegida debe
   **absorber** a los otros tres, no ser el quinto.
4. **Guardarraíl determinista con exit code.** Tres de las cuatro mecánicas tienen test y una no: la
   prueba de que la declaración en prosa no basta.
5. **Contratos congelados (`analysis.md` §6.2).** Ninguna opción toca flags, exit codes, formas `--json`
   ni `REVISION_HDR_PATTERN`.
6. **El % de duplicado NO es el criterio.** El objetivo medible del §8 es «0 bloques accidentales sin
   declarar», no bajar el 7,6 % (`spec.md` §7). Ninguna de las tres opciones lo baja de forma apreciable.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: O1** — es la única que cumple el criterio 3 (un mecanismo) al precio
del criterio 2 (vuelta atrás casi gratis), y el recon vació el argumento que sostenía a O2. Las razones,
ancladas a los criterios:

- **Criterio 2.** O1 son un JSON, un test y una comprobación del linter: se borran y el árbol queda
  idéntico. O2 deja una puerta en `release.py`, copias dentro de paquetes publicados y cinco puntos de
  carga reescritos.
- **Criterio 3.** El problema medido no es duplicación: son **cuatro mecanismos** para el mismo
  problema, dos de ellos sin guardarraíl (`glob_to_regex`, `piezas()`) y uno con guardarraíl
  conductual (`sin_vallas`). Eso lo arregla un registro, no un módulo.
- **Criterio 6.** Ninguna opción baja el 7,6 %. Pagar +4,0 h y una puerta nueva por un porcentaje que
  la propia spec declara fuera de objetivo es comprar el criterio equivocado.
- **Premisa de O2 caída.** `export-interop.py` no copia skills (`:26-33`), `providers.mjs` ya lleva
  `agent-kits/` entero (`:22`): el vendorizado solo aporta en el paquete `dist/` de solo-skills, y ese
  hueco (`export-skills.py:399` escanea únicamente `.md`) es un defecto propio del exportador que
  conviene arreglar **con cualquiera de las tres opciones**.
- **O1 no cierra O3.** El registro de O1 es exactamente la entrada que O3 necesita. Elegir O1 hoy deja
  el generador a un paso, cuando y si las copias empiezan a cambiar a menudo. Hoy no lo hacen: la
  rotación está en los hotspots, no en los bloques compartidos.

**Cuándo cambiaría la recomendación:** si el usuario da prioridad a «un arreglo, un sitio» por encima
de la vuelta atrás, la opción es **O3**, no O2 — mismo beneficio, sin tocar empaquetadores ni runtime.
O2 solo gana si el paquete portable `dist/` pasa a ser un canal de distribución de primera y las piezas
tienen que viajar sin `agent-kits/`.

**Opción elegida: O1 — registro de copias declaradas + un test único.** La valida el usuario el **2026-09-10** en
la puerta de diseño, con una condición que forma parte de la opción: **la comprobación de `scripts/lint_plugin.py`
sobre bloques idénticos no registrados es inseparable de O1** — sin ella, esto es el statu quo con un JSON encima.
Decisión registrada en [`ADR-016`](../../knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md)
(`propuesta`).

**Decisiones de detalle cerradas con la elección**

| Decisión | Cerrada así | Alternativa descartada |
|---|---|---|
| Formato y sitio del registro | JSON en `agent-kits/shared/copias.json` (viaja con el kit por las tres vías de instalación); **una entrada por bloque** con sus N rutas y los **centinelas o el rango** que lo delimitan en cada sitio | YAML (dependencia fuera de stdlib) y seguir declarándolo en prosa dentro de cada docstring — que es justo lo que hay hoy y lo que ha fallado |
| Cómo se compara | **Byte a byte tras normalizar `\r\n` -> `\n`** | Comparar bytes crudos: en Windows `core.autocrlf` da un falso positivo por finales de línea (`GOT-007`; el hash de `ADR-014` normaliza por lo mismo). También descartado comparar AST o «texto equivalente» |
| Qué pasa al divergir | El test **falla** con exit code — guardarraíl determinista, patrón `ledger-lint`/`qa-gate` | Avisar: un aviso que nadie lee reproduce la garantía que hoy tiene `glob_to_regex` (ninguna) |

**Consecuencia sobre la spec (la aplica el `planner`; aquí no se toca `spec.md` más allá del enlace):** `C-03`
**se encoge** — de «copias accidentales → declaradas o eliminadas» a «unificar cuatro mecanismos de
guardarraíl en uno». No hay copias accidentales: dos de los cuatro pares son el patrón «canónico por
ruta + respaldo local» ya declarado en su docstring y los otros dos no son código. Y ninguna de las tres opciones
baja el 7,6 % de duplicado, que la propia spec deja **fuera de objetivo** (§7): la `Verificación` de `C-03` se
escribe sobre el registro y el test, no sobre `code-health --baseline`.

**Opciones descartadas — motivo y lo que tenían a favor:**

- **O2 — módulo común `_comun.py` vendorizado por el empaquetador.** *A favor:* es la única que hace que un arreglo
  se haga **en un solo sitio**, y la única que llevaría el código compartido dentro del paquete portable sin depender
  de `agent-kits/`. *Por qué no:* el recon la vació — `install/providers.mjs:22` (`PAYLOAD_COMUN = ["skills",
  "agent-kits", "hooks"]`) ya copia `agent-kits/` **entero** a los tres runtimes y `scripts/export-interop.py:26-33`
  no traduce ni copia skills, así que solo aportaría en el `dist/` de solo-skills; y ahí antes hay que tapar
  `scripts/export-skills.py:399` (cierra solo sobre los `.md`: un `_comun.py` citado desde un `.py` **no viajaría**).
  Encima escribe un fichero generado dentro de carpetas editadas a mano (`GOT-003`) y retirar los respaldos locales
  convierte «degrada con aviso» en fallo duro. Coste **L**: +4,0 h humanas, +0,5 h IA, ~+245 € (`evaluation.md:157`).
- **O3 — copias generadas dentro del árbol (`sync-copias.py` + `--check`).** *A favor:* el mismo «un arreglo, un
  sitio» que O2 **sin** tocar empaquetadores ni runtime, con toda pieza standalone por construcción y el precedente
  de `export-interop.py` (`LES-012`). *Por qué no ahora:* es un **superconjunto de O1** —necesita el mismo registro
  como entrada— y añade un generador que escribe dentro de ficheros fuente más una séptima puerta a `release.py`,
  para un problema que el test de identidad ya resuelve. **Queda como la evolución natural de O1**: el día en que las
  copias se editen a menudo se le enchufa `copias.json` como entrada y no hay nada que rehacer. Hoy no se editan a
  menudo — la rotación está en los hotspots, no en los bloques compartidos.
- **Módulo común importado por ruta relativa (la «O3» del `analysis.md` §5).** Rompe el standalone: una
  skill instalada sola en Codex u OpenCode no tiene `agent-kits/shared/` al lado. Choca con el requisito
  multi-runtime y con `docs/INTEROP.md`. Cae por el criterio 1 (veto), y el recon **no aporta evidencia
  nueva** que la reabra: `providers.mjs` sí lleva `agent-kits/` entero, pero solo por la vía del
  instalador oficial — la copia manual de una sola skill y el paquete `dist/` siguen sin él.
- **Eliminar las copias** (tercer desenlace que admite CA-05). Solo aplica a las dos que no son código
  (`import` y docstring), y ahí no hay nada que eliminar: se declaran como no-código y salen del
  recuento. Para las cinco unidades reales, eliminar significaría que una pieza pierda una capacidad.

## 5. Impacto en módulos y ficheros

Rutas reales, con la opción que las toca. O1 no modifica ningún fichero de producción salvo los
comentarios de declaración.

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `agent-kits/shared/copias.json` | Registro de las 5 unidades compartidas + las 2 declaradas no-código: canónico, copias, mecanismo, guardarraíl (O1, O3) | **Nuevo** |
| `tests/test_copias_declaradas.py` | Test único que recorre el registro: identidad byte a byte de bloques y literales (O1, O3). Absorbe el criterio de `tests/test_knowledge_index.py:198-214` y `tests/test_console_encoding.py:801-804` sin borrarlos | **Nuevo** |
| `scripts/lint_plugin.py` | Comprobación «marcador `--8<--` o `_*_FALLBACK` sin fila en el registro» → error (O1, O3) | Modificado |
| `agent-kits/shared/scope-check.py:46-77` · `skills/adversarial-review/scripts/review-lens-select.py:99-131` | Mecanismo **C sin guardarraíl** → registrado; el respaldo local pasa a bloque `--8<--` comparable (O1, O3) · con O2, se retira el respaldo y se carga `_comun.py` | Modificado |
| `evals/check.py:108` · `scripts/lint_plugin.py:864-865,905` | Misma operación sobre `piezas()`/`_piezas_local()` (mecanismo C sin guardarraíl) | Modificado |
| `agent-kits/shared/ledger-lint.py:101` · `skills/changelog-sync/scripts/changelog-sync.py:120` | `sin_vallas`: de test conductual a identidad — o unificación al mecanismo B (canónico + respaldo). **Pregunta abierta 2** | Modificado |
| `agent-kits/shared/ledger-lint.py:179` · `agent-kits/shared/task-brief.py:576` · `skills/jira-sync/scripts/jira-flow.py:231` | Mecanismo **B** (E9 del §8-bis): se registra, el texto no cambia | Modificado (comentario) |
| `scripts/lint_plugin.py:109-305,546-566,569-655` · `agent-kits/shared/doctor.py:644-664,667-753` · `agent-kits/shared/knowledge-find.py:244-264` · `tests/test_console_encoding.py:43-239` | Mecanismo **A**: se registran; el texto no cambia | Modificado (comentario) |
| `scripts/export-skills.py:399` (`fragmentos_shared`) | Cerrar sobre los `.py` de las skills, no solo sobre los `.md`. Defecto propio del exportador: **imprescindible con O2**, recomendable con O1/O3 | Modificado |
| `scripts/export-skills.py` · `scripts/export-interop.py` · `install/providers.mjs` | **Solo con O2**: vendorizado de `_comun.py` dentro de cada pieza + `--check` | Modificado |
| `agent-kits/shared/_comun.py` | **Solo con O2**: fuente de verdad de las unidades compartidas | Nuevo |
| `scripts/sync-copias.py` | **Solo con O3**: generador que escribe entre centinelas + `--check`; nueva puerta en `scripts/release.py` | Nuevo |
| `docs/agents/ROLES.md` (vecindad) | El §8-bis pide la matriz de contratos junto a `ROLES.md`; el registro de copias es su gemelo para el código. **Pregunta abierta 3** | Sin cambio en este diseño |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Con O1 el 7,6 % de duplicado **no baja** y se lee como refactor fallido | **Alta** | Medio | La señal del §8 es «0 bloques accidentales sin declarar», no el porcentaje (`spec.md` §7). El `planner` debe redactar la `Verificación` de C-03 sobre el registro y el test, **no** sobre `code-health --baseline` |
| El registro nace y se queda atrás: alguien añade una copia sin registrarla | Media | Alto (vuelve el problema de hoy) | La comprobación del linter sobre marcadores y nombres `_*_FALLBACK` es la puerta; es heurística, así que su alcance debe quedar escrito en el registro (qué detecta y qué no) |
| Con O2/O3, el generador pisa código real dentro de un fichero editado a mano (`GOT-003`) | Media | **Alto** | Nombre reservado (los centinelas `--8<--` ya lo son), escritura solo entre marcadores, `assert` defensivo y prohibición de crear o borrar ficheros — el patrón de `assert_safe_stage_target()` |
| Con O2, retirar el respaldo local convierte una degradación en un fallo duro | Media | Alto | No retirar los respaldos hasta que `--check` cubra los tres canales de instalación; hoy solo cubriría uno |
| C-03 se abre antes de que este diseño esté `aprobado` | Media | Alto | Condición 1 del go (`evaluation.md:371`): el `planner` pone C-03 detrás de `design.md` `aprobado` como arista del grafo, no como tarea abierta |
| **Segundo registro en el repo**: `copias.json` (build-time, código fuente) frente a `.claude/pieces.json` de `ADR-014` (runtime, piezas generadas) | Media | Medio | Son dominios distintos (bloques de código en git vs. ficheros generados en el proyecto consumidor) y dueños distintos. El ADR de esta decisión debe decirlo explícitamente para que nadie los funda; `ADR-014` está `propuesta` y su script no existe aún |
| La decisión desborda el presupuesto de la evaluación si sale O2 | Baja (si sale O1) / Alta (si sale O2) | Medio | El delta está presupuestado: +4,0 h humanas, +0,5 h IA, ~+245 € con margen (`evaluation.md:347`). Si el usuario elige O2 o O3, `/dev-cycle` debe aplicar ese delta sin re-evaluar el resto |

Ningún ADR `aceptada` se contradice. `ADR-014` y `ADR-015` están en `propuesta` y solo se citan como
precedente.

## 7. Preguntas abiertas

1. **`sin_vallas`: dos copias registradas o una canónica con respaldo (mecanismo B)?** La evaluación ya
   la marcó como incógnita (`evaluation.md:163`). El recon añade el dato que faltaba: hoy tiene test
   **conductual**, no de identidad.
2. **Relación con la matriz de contratos del §8-bis.** El registro de copias y la matriz pieza→pieza
   responden a la misma pregunta desde dos lados. Si van en el mismo sitio (`docs/agents/`) o cada uno
   en el suyo lo decide C-06, no este diseño.
3. **El hueco de `export-skills.py:399`** (solo escanea `.md`) es un defecto verificado hoy, ajeno a la
   decisión. ¿Entra en C-03, abre tarea propia en el bloque (b) o va por `quick-implement`? Con O2 no es
   opcional.
4. **Los dos pares no-código** (`import` + docstring `Uso:`/`Exit:`): ¿se declaran como excluidos en el
   registro, o el detector de `code-health.py` aprende a no contarlos? Toca C-04/C-07, no C-03.

> **Cerrada en esta pasada:** «dónde vive el registro y quién lo comprueba» — la fija la elección de O1 (§4): `agent-kits/shared/copias.json` como registro, `tests/test_copias_declaradas.py` como test único de identidad y la comprobación de «bloque idéntico no registrado» en `scripts/lint_plugin.py`. Al `planner` le queda abrir C-03 sobre esa forma, no elegirla.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-10 | Diseño creado (`borrador`); tres opciones presentadas al usuario (O1 registro · O2 vendorizado al empaquetar · O3 generado en el árbol), recomendación O1. Recon: los cuatro pares «accidentales» del §2 no lo son (dos son mecanismo C sin guardarraíl, dos no son código); `sin_vallas` sí tiene test, pero conductual; la premisa de portabilidad de O2 se estrecha a un solo canal (`dist/`) |
| 2026-09-10 | **Pasada 2 — el usuario elige O1** (registro de copias declaradas + un test único), con la comprobación del linter sobre bloques idénticos no registrados como parte inseparable de la opción. Estado `borrador` → `aprobado`; `opcion_elegida: O1`; `ADR-016` escrito como `propuesta` y enlazado desde `spec.md`. Cerradas tres decisiones de detalle (formato del registro, comparación byte a byte con `\r\n` -> `\n` normalizado, el test falla y no avisa) y la pregunta abierta 1. O2 y O3 pasan a la lista de descartadas con lo que tenían a favor; O3 queda anotada como evolución natural de O1 |
