---
tasks: sin-motor-externo
descripcion: El plugin deja de definirse por comparación y de depender de un motor de implementación ajeno. Petición literal del usuario: «elimina las comparaciones con superpowers del readme y de cualquier otro sitio del repositorio». (1) La sección «Compared with superpowers» / «Comparado con superpowers» sale de los dos README y la nota de autosuficiencia deja de ofrecer la delegación; (2) `/dev-cycle` **retira el Modo A por completo** — flag `--superpowers`, frase de la `description`, regla 2 de la puerta de entrada, bloque de la Fase 3, menciones en los bucles de revisión y de qa, resumen de cierre, transiciones de estado y la regla «Cero dependencia de superpowers» —, así que la cadena nativa pasa a ser el ÚNICO motor y el comando baja de 218 a 198 líneas; con él caen las etiquetas «Modo A/Modo B» que quedaban colgando en `CLAUDE.md`, `docs/README.md` (+EN), `docs/FLOWS.md` (+EN, dos nodos del diagrama), `docs/CONVENTIONS.md` regla 8 (+EN), `docs/agents/implementer.md`, `skills/debug-root-cause/SKILL.md`, `agent-kits/shared/README.md`, `review-report.template.md` y la plantilla del `planner`; (3) las notas de atribución (`export-skills.py`, `skill-index.py`, `rationalization-table.md`, `INSTALL` ES/EN, `observability` ES/EN) describen el patrón por lo que es —«paquete multi-entorno de solo skills», «lo que puede ser determinista no lo redacta el modelo»— sin nombrar a nadie y sin perder contenido técnico; (4) el fixture de `test_skill_index.py` deja de citar un flag inexistente y, de paso, el recorte del hint largo pasa a estar PROBADO (antes no lo estaba). Los registros fechados (ledgers cerrados del roadmap, `ADR-008`, `LES-011`, los dos CHANGELOG) se conservan intactos: borrarlos sería falsificar el registro.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-04
actualizado: 2026-09-04
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva verificación por tarea
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige (exit ≠ 0 si falta)
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud, sin transcripción)
---

# Checklist de Tareas — sin-motor-externo (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-04 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + verificación por tarea) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o cualquier otra herramienta— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Reparto previo (obligatorio antes de editar).** Los 130 aciertos de `grep -rniI "superpowers\|superpower"` en 43 ficheros se clasificaron en tres cajones: **A) piezas vivas** (12 ficheros, 29 aciertos) → retirado todo; **B) registros históricos fechados** (31 ficheros, 101 aciertos: 27 del roadmap cerrado + `ADR-008` + `LES-011` + los 2 CHANGELOG) → **intactos**, porque son decisiones con fecha y fuente y borrarlas falsifica el registro; a esos 101 se les suman los **15 aciertos que escribe este propio registro** (14 aquí + 1 en la cita del encargo de la fila del índice), que son la traza de la retirada; **C) dudoso** → la única decisión propia está en las Notas de cierre (la regla de autoridad del ledger sobre «cualquier implementador, incluidos orquestadores externos», que se CONSERVA por ser regla del repo y no una comparación).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — sin motor externo | 5 | 5 | 100% | 3,9 / 3,9h | 0,21 / 0,21h | 0,06 / 0,06h | 102k / 102k |
| **TOTAL** | **5** | **5** | **100%** | **3,9 / 3,9h** | **0,21 / 0,21h** | **0,06 / 0,06h** | **102k / 102k** |

---

## Fase única — sin motor externo

**Estado**: completado · **Estimado**: 3,9h · **Real**: 3,9h (estimado) · **Coste est.**: ≈205 € · **Tokens est.**: 102k

### T-01 — El README dice lo que el plugin hace, no contra quién

- **Descripción**: `README.md` y `README.es.md` perdían el foco en su última sección de contenido: una comparación con otro plugin («Compared with superpowers» / «Comparado con superpowers», ~248) que enumeraba patrones prestados y cerraba ofreciendo `/dev-cycle --superpowers`. Se **retira entera** en los dos idiomas, sin sustituirla por una comparación con otro plugin: el README debe describir este plugin. No había entrada de índice ni enlace interno apuntando a ella (comprobado: los dos README no tienen TOC y `grep` de `#compared|#comparado` no devuelve nada), así que la retirada no deja enlaces roídos. Además, la nota de autosuficiencia de la línea 76 **ofrecía la delegación** («si ya usas un motor SDD externo, `/dev-cycle` puede delegarle la ejecución»): se reescribe para afirmar lo que queda en pie —`tasks.md` es el ledger canónico para quien implemente y el registro de cualquier otra herramienta es espejo, nunca la fuente— conservando el enlace a `observability` sobre la convivencia con monitores de sesión. El enlace al paquete portable que vivía en la sección borrada ya estaba dos párrafos antes, así que no se pierde ningún destino.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,5h (estimado — `usage-meter.py` no disponible en este entorno)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado, mismo motivo)
- **Supervisión**: est. 0,01h · real 0,01h (estimado, mismo motivo)
- **Archivos**: `README.md`, `README.es.md`
- **Changelog**: El README ya no compara el plugin con otros: describe lo que hace y deja de ofrecer delegar la implementación en un motor externo.
- **Verificación** (ejecutada 2026-09-04, salidas literales): `grep -niI "superpower\|Compared with\|Comparado con" README.md README.es.md` → **sin salida, exit 1** · `grep -c "^## " README.md README.es.md` → `README.md:8` y `README.es.md:8` (una sección menos en cada uno; antes 9) · `tail -4 README.md` → `## License` + línea en blanco + `[Apache-2.0](LICENSE) © 2026 daycry`, y `tail -4 README.es.md` lo mismo con `## Licencia` (la sección de licencia sigue cerrando el fichero) · `python3 tests/test_readme_badges.py` → `test_readme_badges: 12/12 OK`

**Criterios de aceptación**
- [x] La sección de comparación desaparece de `README.md` y de `README.es.md`, sin sustituirla por otra comparación
- [x] No queda entrada de índice ni enlace interno apuntando a la sección borrada (comprobado con `grep`)
- [x] La nota de autosuficiencia deja de ofrecer delegar la ejecución y sigue diciendo algo verdadero y útil
- [x] Los dos espejos ES/EN dicen lo mismo y el test de badges/prosa sigue verde

### T-02 — `/dev-cycle` retira el Modo A: la cadena nativa es el único motor

- **Descripción**: en `commands/dev-cycle.md` el Modo A no era una comparación sino una **dependencia funcional**, así que se retira **por completo** y con él todo lo que solo existía para sostenerlo: el flag `--superpowers` del `argument-hint`, la frase de la `description` del frontmatter, la **regla 2** de la Fase 0 (elección de motor) con su renumeración, la nota «la capa de dominio se ejecuta en ambos modos» (tautología sin un segundo modo), la coletilla «sea cual sea el motor de implementación» de la cabecera, el bloque **Modo A** de la Fase 3 y la etiqueta «Modo B» que le hacía de contraparte, la nota de la Fase 2-b sobre el `brainstorming` del motor ajeno y su «no se delega la planificación», la excepción del bucle de revisión, el paréntesis del bucle de qa, «modo usado (nativa/superpowers)» del resumen de cierre, el párrafo de transiciones de estado que repartía responsabilidades entre A y B, y la regla «Cero dependencia de superpowers». El comando baja de **218 a 198 líneas** y las puertas no cambian. La misma retirada deja huérfanas las etiquetas de modo repartidas por el repo, que se corrigen en el mismo cambio: `CLAUDE.md` (la fila de `/dev-cycle` describe la cadena nativa como lo único que hay), `docs/README.md` y su espejo EN, `docs/FLOWS.md` y su espejo EN (**dos nodos del diagrama fuera**: la decisión «¿pidió un motor externo?» y el nodo del motor externo, con su arista a `qa`; y las dos menciones «(Modo B)» de Jira y del usage-meter), `docs/CONVENTIONS.md` regla 8 y su espejo EN (el bullet «Estados con motor externo» pierde su referente y se reescribe como «las transiciones de estado son del orquestador», que es lo que queda cierto: quien ejecuta puede no tocar tus artefactos —un subagente fresco lo tiene PROHIBIDO—), `docs/agents/implementer.md`, `skills/debug-root-cause/SKILL.md` (deja de cederle el método a un motor ajeno), `agent-kits/shared/README.md`, `agent-kits/shared/review-report.template.md` y `agent-kits/planner/templates/tasks.md` («Modo B» → «Fase 3», que es el sitio real). **`evals/` no necesitó cambios**: barrido con `superpower`, `motor`, `externo`, `flag` y `delegu`, ningún caso citaba el flag ni el modo — en particular **no existía** el caso negativo «no delegues por detectarlo instalado», así que no hay nada que retirar ni nada que quede probando algo inexistente.
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real 1,8h (estimado, mismo motivo)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,10h (estimado, mismo motivo)
- **Supervisión**: est. 0,03h · real 0,03h (estimado, mismo motivo)
- **Archivos**: `commands/dev-cycle.md`, `CLAUDE.md`, `docs/README.md`, `docs/en/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/agents/implementer.md`, `skills/debug-root-cause/SKILL.md`, `agent-kits/shared/README.md`, `agent-kits/shared/review-report.template.md`, `agent-kits/planner/templates/tasks.md`
- **Changelog**: `/dev-cycle` ya no tiene modo de motor externo ni flag `--superpowers`: la cadena nativa del plugin es el único motor de implementación, y el comando queda más corto y con una sola ruta.
- **Verificación** (ejecutada 2026-09-04, salidas literales): `wc -l commands/dev-cycle.md` → `218` antes, **`198`** después (−20 líneas, −9 %) · `grep -niI "superpower\|modo a\|modo b\|motor externo\|sdd externo\|backbone\|ambos modos\|los dos modos" commands/dev-cycle.md` → **sin salida, exit 1** · `grep -rniI "modo b\|motor externo\|sdd externo\|mode b\|both modes\|dos modos" --exclude-dir=.git . | grep -v "^./docs/roadmap/" | grep -v "^./CHANGELOG"` → solo los aciertos que se CONSERVAN a propósito (`skills/adversarial-review/SKILL.md` «Entradas — dos modos», `agents/architect.md` «dos modos», `skills/jira-sync/references/destination-and-types.md`, `skills/api-contract/references/contract-tests.md`, y la regla de autoridad del ledger en `agents/planner.md`, `agents/implementer.md`, `agent-kits/planner/templates/tasks.md`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md:160`), ninguno de ellos una etiqueta de modo de `/dev-cycle` · `python3 scripts/lint_plugin.py` → **exit 0**, `lint_plugin: 9 agentes · 0 errores · 3 avisos` (los 3 de siempre: `retro`, `roadmap-status`, `setup`; la `description` recortada sigue dentro del tope de 1.200 caracteres) · `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 32/32 OK` · `python3 evals/check.py` → **exit 0**, `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores` (idéntico a antes: la ventana literal «ciclo completo de una iniciativa» sigue en la `description`) · `python3 -m pytest -q tests/test_mermaid_blocks.py` → `4 passed` (los dos diagramas editados siguen siendo mermaid válido)

**Criterios de aceptación**
- [x] El Modo A no existe en `commands/dev-cycle.md`: ni flag, ni `description`, ni regla de entrada, ni bloque de Fase 3, ni bucles, ni cierre, ni transiciones, ni regla final
- [x] El comando queda MÁS CORTO y con una sola ruta, sin cicatrices del tipo «antes había otro modo» (218 → 198 líneas)
- [x] Las reglas y notas que se quedaron sin sentido al desaparecer el modo están retiradas o reescritas, no dejadas colgando
- [x] Ninguna etiqueta «Modo A/Modo B» sobrevive en piezas vivas (comando, agentes, kits, plantillas, docs y espejos EN)
- [x] Los dos diagramas de `FLOWS` (ES y EN) pierden los mismos dos nodos y siguen siendo mermaid válido
- [x] `evals/` barrido: ningún caso citaba el flag ni el modo, así que ningún caso se debilita ni queda probando algo inexistente
- [x] `lint_plugin.py` exit 0 y `evals/check.py` exit 0 con el mismo recuento de casos

### T-03 — Las notas de atribución describen el patrón, no la fuente

- **Descripción**: seis piezas vivas llevaban una nota de atribución en su cabecera o en su prosa. Cada una pasa a **describir el patrón por lo que es**, sin nombrar a nadie y **sin perder el contenido técnico**: `scripts/export-skills.py:4` («patrón multi-entorno de superpowers» → «paquete multi-entorno de SOLO skills», que además es lo que el script hace de verdad); `agent-kits/shared/skill-index.py:4` (se retira «patrón `using-superpowers`»; el docstring ya explicaba en las líneas siguientes qué brecha cierra el índice y con qué topes medidos, así que no queda hueco); `agent-kits/shared/rationalization-table.md:6` («patrón "iron law" de superpowers» → «la idea», conservando íntegra la afirmación que importa: nombrar la excusa en el momento en que aparece es más eficaz que repetir la regla); `docs/INSTALL.md:138` y su espejo EN («paquete portable «solo skills» (multi-entorno, sin runtime propio)»); y `docs/observability.md:122-123` con su espejo EN, donde la nota mezclaba tres cosas — se conserva la **regla** («lo que puede ser determinista no lo redacta el modelo»), ahora atribuida a donde de verdad vive (regla 8 de `CONVENTIONS`, que es la que la impone con `ledger-lint`/`qa-gate`), y se conserva su **corolario técnico** (el patrón de *un subagente por tarea* multiplica el contexto, y por eso el ciclo Jira no lanza ninguno: son llamadas del agente que ya está trabajando); lo único que desaparece es la frase que solo servía para comparar («no tiene integración con herramientas de gestión, así que aquí no hay nada que copiar»).
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,7h (estimado, mismo motivo)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado, mismo motivo)
- **Supervisión**: est. 0,01h · real 0,01h (estimado, mismo motivo)
- **Archivos**: `scripts/export-skills.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/rationalization-table.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/observability.md`, `docs/en/observability.md`
- **Changelog**: Las notas de diseño del plugin explican el patrón que aplican en vez de citar de qué plugin viene, sin perder nada de lo que decían técnicamente.
- **Verificación** (ejecutada 2026-09-04, salidas literales): `grep -niI "superpower" scripts/export-skills.py agent-kits/shared/skill-index.py agent-kits/shared/rationalization-table.md docs/INSTALL.md docs/en/INSTALL.md docs/observability.md docs/en/observability.md` → **sin salida, exit 1** · `python3 -m pytest -q tests/test_rationalization_tables.py tests/test_export_skills.py tests/test_cifras_medidas.py` → `61 passed` (la cabecera literal de la tabla de racionalización, el paquete portable y las cifras medidas de `CONVENTIONS` + espejo siguen cuadrando) · `python3 scripts/export-skills.py --out <tmp>` → **exit 0**, `hash: 51d319bd9c58859966b9cf92c7ee751dad65cb115d8b3c8c3a3555edea5aaea2` (idéntico en dos ejecuciones seguidas: el paquete sigue siendo determinista) · `python3 scripts/export-skills.py --check <tmp>` → **exit 0**, `export-skills --check: 107 ficheros · 0 problema(s)` · `python3 -m pytest -q agent-kits/shared/test_skill_index.py` → `14 passed` · `PYTHONIOENCODING=cp1252 python3 -m pytest -q` → `1177 passed` (las cabeceras editadas son de scripts que imprimen símbolos)

**Criterios de aceptación**
- [x] Ninguna de las seis piezas vivas nombra el plugin de origen
- [x] Cada nota describe el patrón por lo que ES, y sigue siendo verdadera sobre lo que hace la pieza
- [x] No se pierde contenido técnico al quitar el nombre: la regla de determinismo y su corolario de coste de contexto siguen escritos
- [x] La regla de `observability.md` queda atribuida a donde vive de verdad (regla 8 de `CONVENTIONS`)
- [x] El paquete portable sigue generándose y validándose (`--check` exit 0) y los tests de esas piezas siguen verdes

### T-04 — El fixture del test de `skill-index` deja de citar un flag inexistente (y el recorte pasa a estar probado)

- **Descripción**: `agent-kits/shared/test_skill_index.py:104` usaba `'"<objetivo de la iniciativa> [rapido | completo] [--superpowers]"'` como fixture del `argument-hint` de `/dev-cycle`. Tras T-02 ese flag no existe, así que el fixture pasa al **hint real** del comando (`"<objetivo de la iniciativa> [rapido | completo]"`) y el caso sigue probando exactamente lo que probaba: que `hint_corto` quita las comillas y **conserva TODOS** los tokens `<…>`/`[…]` de un hint con varios (comentario añadido para que el propósito no se pierda otra vez). Al revisar si el caso seguía probando lo que decía, apareció un **hueco real**: el recorte del hint LARGO no ocurre en `hint_corto` —que nunca trunca— sino al pintar la línea del índice (`_lineas`: «el hint no roba más de media línea», corte en palabra, cierre en «…»), y **ese camino no tenía ningún test**. Se añade `test_hint_largo_se_recorta_en_la_linea`, que con `ancho=60` afirma el recorte en palabra, el cierre en «…» y el tope de media línea, y con `ancho=200` afirma que el hint entra completo — así que la retirada del flag deja el test más fuerte que antes, no más débil.
- **Estado**: completado
- **Tiempo humano**: est. 0,3h · real 0,3h (estimado, mismo motivo)
- **Tiempo IA (ejec.)**: est. 0,02h · real 0,02h (estimado, mismo motivo)
- **Supervisión**: est. 0,00h · real 0,00h (estimado, mismo motivo)
- **Archivos**: `agent-kits/shared/test_skill_index.py`
- **Changelog**: El índice de piezas que se inyecta al arrancar sesión tiene ahora probado el recorte del `argument-hint` largo, que antes no lo estaba.
- **Verificación** (ejecutada 2026-09-04, salidas literales): `python3 -m pytest -q agent-kits/shared/test_skill_index.py` → `14 passed` (13 antes) · el camino que se estrena, medido con `si._lineas` sobre la pieza `/dev-cycle` con el hint real: con `ancho=60` → `'/dev-cycle <objetivo de la… — Orquesta el ciclo completo…'` (etiqueta de 27 caracteres ≤ 30 = media línea, cortada en palabra y cerrada en «…») y con `ancho=200` → `'/dev-cycle <objetivo de la iniciativa> [rapido | completo] — Orquesta el ciclo completo de una iniciativa con puertas'` (hint íntegro) · `grep -niI "superpower" agent-kits/shared/test_skill_index.py` → **sin salida, exit 1** · `python3 -m pytest -q` → `1177 passed` (1176 antes: el test nuevo)

**Criterios de aceptación**
- [x] El fixture usa un argumento REAL del comando tras la edición de T-02
- [x] El caso sigue probando que un hint de varios tokens conserva todos y pierde las comillas, con el propósito escrito en un comentario
- [x] El recorte del hint largo —lo que se creía probado y no lo estaba— queda cubierto con su test, en los dos sentidos (recorta / entra completo)
- [x] La suite sube de 1.176 a 1.177 tests y no baja ninguno

### T-05 — Las cifras VIVAS de la escalera del CHANGELOG se re-miden al entrar este ledger en el corpus

- **Descripción**: cerrar un ledger con campo `- **Changelog**:` **cambia el corpus que mide `changelog-sync.py --medicion`**, y `tests/test_cifras_medidas.py` compara cada cifra marcada `<!--m:clave=valor-->` de la doc contra esa medición viva: al entrar este ledger la suite se puso en rojo con **40 fallos**. No es un daño colateral que haya que evitar, es el guardarraíl haciendo su trabajo — y la doctrina ya estaba escrita en el ledger de `changelog-brief`: «la marca `<!--m:=-->` vigila la medición VIVA, no la histórica, por eso se actualiza el número en vez de dejar la suite roja». Se re-miden las **trece claves vivas** que cambian (`ledgers_cerrados` 14→15 · `ledgers_totales` 29→30 · `ledgers_con_cola` 22→23 · `cerrados_con_cola` 13→14 · `tareas` 70→75 · `camino_changelog` 7→12 · `changelog_media` 323→305 · `changelog_mediana` 347→307 · `changelog_max` 376→400 · `bullet_media` 170→177 · `bullet_mediana` 133→139 · `bullet_max` 376→400 · `degradan_titulo_pct` 60→56) y se actualizan **prosa y marcador juntos** en los cinco ficheros que las copian: `skills/changelog-sync/references/medicion-escalera.md` (corpus de hoy, fila `changelog` y TOTAL de la tabla por camino, TOTAL en prosa, exposición de la cola), `skills/changelog-sync/SKILL.md`, `docs/knowledge/adr/ADR-012` (tabla por camino completa), `docs/knowledge/README.md` y el ledger cerrado de `2026-09-04-changelog-brief`. Dos de ellas cambian una afirmación, no solo un número: el **techo real del bullet completo** pasa de 376 a **400 caracteres** y su dueño de `changelog-brief/T-01` a la T-05 de este ledger (se dice de quién es y de quién era, en los cuatro sitios que lo afirman), y la mediana del camino `changelog` baja de 347 a 307 — sigue siendo la más alta de los cuatro caminos, así que la conclusión incómoda que la doc escribe («el camino que se promueve produce los bullets más largos») no cambia. Las cifras `base_*` (corpus base anterior al 2026-09-04: 13 ledgers / 63 tareas) **no se tocan**: son la medición histórica sobre la que se decidió, y esas sí serían falsificación. Donde una frase daba por hecho que el único ledger con campo era el de `changelog-brief` («con el ledger de esta iniciativa cerrado…»), se reescribe para hablar de «los ledgers que YA usan el campo», que es lo que será verdad también la próxima vez; y en el ledger de `changelog-brief` la actualización queda **anotada con su motivo** (cifra viva, no histórica), como ya se hizo cuando entró `memory-retrieval`.
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,6h (estimado, mismo motivo)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado, mismo motivo)
- **Supervisión**: est. 0,01h · real 0,01h (estimado, mismo motivo)
- **Archivos**: `skills/changelog-sync/references/medicion-escalera.md`, `skills/changelog-sync/SKILL.md`, `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md`, `docs/knowledge/README.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md`
- **Changelog**: Las cifras medidas que la documentación del CHANGELOG afirma vuelven a reproducir con la medición del repo de hoy.
- **Verificación** (ejecutada 2026-09-04, salidas literales): `python3 tests/test_cifras_medidas.py` con el ledger nuevo y las cifras viejas → **`40 failed, 212 passed`**; tras re-medir → **`252 passed`** · `python3 skills/changelog-sync/scripts/changelog-sync.py --medicion | tail -1` → `changelog-sync --medicion: 175 cifra(s) medidas (corpus de hoy 15 ledger(s) / 75 tarea(s); corpus base < 2026-09-04: 13 / 63)` · `diff` de la medición sin/con este ledger → **13 claves** cambian (las de arriba) y **ninguna `base_*`** · `grep -c "base_ledgers=13,base_tareas=63" skills/changelog-sync/references/medicion-escalera.md skills/changelog-sync/SKILL.md docs/CONVENTIONS.md docs/en/CONVENTIONS.md` → `1`, `2`, `1`, `1` (cifras históricas intactas) · `python3 -m pytest -q` → **`1178 passed`**

**Criterios de aceptación**
- [x] `tests/test_cifras_medidas.py` vuelve a verde (252 passed) sin relajar el test ni marcar ninguna cifra como no verificable
- [x] Las trece claves vivas se actualizan en prosa Y en su marcador, en los cinco ficheros que las copian
- [x] Ninguna cifra `base_*` (corpus histórico 13 ledgers / 63 tareas) se modifica
- [x] La prosa que daba por único el ledger de `changelog-brief` se reescribe para no volver a caducar
- [x] La actualización del ledger cerrado de `changelog-brief` queda anotada con su motivo (cifra viva, no histórica)

---

## Notas de cierre

**Reparto A/B/C con recuento.** Barrido inicial: `grep -rniI "superpowers\|superpower" --exclude-dir=.git .` → **130 aciertos en 43 ficheros**. Tras el cambio: **116 aciertos en 32 ficheros**, todos del cajón B (`4` en los 2 CHANGELOG + `109` en 28 ficheros de `docs/roadmap/` + `3` en 2 de `docs/knowledge/`; **`0` fuera de esos tres grupos**, o sea cero en piezas vivas). De esos 116, **101 en 31 ficheros son los históricos que ya estaban** y **15 los escribe este registro** (14 en este ledger + 1 en la cita del encargo de su fila del índice). Retirados: **29 aciertos en 12 ficheros** (`README.md`, `README.es.md`, `CLAUDE.md`, `commands/dev-cycle.md`, `scripts/export-skills.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/test_skill_index.py`, `agent-kits/shared/rationalization-table.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/observability.md`, `docs/en/observability.md`).

**Cajón B — lo que se conserva y por qué.** Los ledgers y documentos cerrados de `docs/roadmap/<fecha>-<slug>/**` (26 ficheros de iniciativa) y `docs/roadmap/README.md`, `docs/knowledge/adr/ADR-008` (de dónde vino el patrón de skills cortas, con fecha), `docs/knowledge/lessons/LES-011` (por qué la activación se prueba con evals, con su fuente) y `CHANGELOG.md` + `CHANGELOG.es.md` (además, fuera de alcance por indicación explícita). Son **decisiones fechadas con su fuente**: la doctrina del repo es que las correcciones van fechadas, no en silencio, así que reescribirlas sería falsificar el registro. Un lector que quiera saber de dónde salió un patrón lo sigue encontrando ahí; lo que ya no hay es una pieza viva que se defina por comparación.

**Cajón C — decisión propia, con su criterio.** El barrido ampliado (`grep -rniI "modo a\|motor externo\|sdd externo\|backbone"`) destapó un grupo que no encaja limpio: la **regla de autoridad del ledger** en `agents/planner.md:103`, `agents/implementer.md:57`, `agent-kits/planner/templates/tasks.md:45`, `docs/agents/implementer.md:69` y `docs/CONVENTIONS.md:159-161` (+ espejo EN), que dice que **cualquier** implementador —incluido un orquestador SDD de terceros— debe marcar `tasks.md`, y que el registro propio de otra herramienta es espejo. Aplicando el criterio «¿pieza que se ejecuta o se lee hoy, o registro de algo que pasó?», es pieza viva → cajón A… pero **se CONSERVA**, porque no es una comparación ni un resto del Modo A: es la regla 8 del repo sobre la autoridad del ledger, y sigue siendo cierta y útil el día en que alguien implemente una tarea con otra herramienta (una todo-list interna, otro plugin, un compañero a mano). Lo que sí se retiró de ese grupo es el bullet «**Estados con motor externo**» de la regla 8 (ES+EN), que **sí** describía la delegación como flujo de `/dev-cycle` y por tanto se quedaba sin referente: se reescribió como «las transiciones de estado son del orquestador», con el motivo que sigue vivo hoy (quien ejecuta puede no tocar tus artefactos: un subagente de contexto fresco lo tiene prohibido). Frontera aplicada en todo el cambio: **se retira lo que presentaba la delegación como capacidad del plugin; se conserva la regla de que el ledger manda sobre cualquiera.**

**`evals/` sin cambios, y por qué eso es un hallazgo.** El encargo anticipaba que pudiera existir un caso negativo del tipo «no delegues por detectarlo instalado», cuyo motivo desaparecería con el Modo A. Barrido `evals/` por `superpower`, `motor`, `externo`, `flag`, `delegu` e `instalad`: **ese caso no existe**. Los 4 casos de `evals/cases/command-dev-cycle.json` (2 positivos, 2 negativos: cierre en la puerta go/no-go → `/pm-cycle`, y typo trivial → sin ciclo) son independientes del motor y siguen válidos sin tocar una letra; `evals/check.py` da el mismo recuento antes y después (133 casos). Así que no se debilitó ningún caso ni quedó ninguno probando algo inexistente.

**El nombre solo sobrevive en el registro, y a propósito.** Este ledger y su fila del índice **sí** escriben el nombre retirado: citan el encargo literal del usuario y dicen qué sección y qué flag desaparecieron. Es deliberado y es la única forma de que el registro se entienda — un ledger que dijera «se quitó una comparación con algo» no serviría para auditar nada. Los dos ficheros son cajón B (registro fechado), así que el barrido sigue cumpliendo la condición pedida: **cero aciertos en piezas vivas**. En el índice del roadmap el nombre aparece **una sola vez**, dentro de la cita del encargo.

**Efecto colateral que el guardarraíl obligó a resolver (T-05).** Cerrar un ledger con campo `- **Changelog**:` mueve el corpus que mide `changelog-sync.py --medicion`, y `tests/test_cifras_medidas.py` compara contra la medición VIVA: sin re-medir, la suite quedaba en `40 failed, 212 passed`. Se re-midieron las trece claves vivas y **ninguna** `base_*`. Es la parte del cambio que no estaba en el encargo y que apareció al ejecutar la verificación exigida; se hizo siguiendo la doctrina ya escrita en el ledger de `changelog-brief` (la marca `<!--m:=-->` vigila la medición viva, por eso se actualiza el número en vez de dejar la suite roja) en vez de relajar el test o marcar cifras como no verificables.

**Fuera de alcance, respetado.** Ningún `CHANGELOG*.md` modificado (`git diff --name-only | grep -i changelog` → sin salida). Sin `git push`.

**Verificación global (salidas literales, 2026-09-04).**

- `grep -rniI "superpowers\|superpower" --exclude-dir=.git . | wc -l` → **101** (130 antes); `... | wc -l` sobre ficheros → **31** (43 antes); fuera de CHANGELOG/roadmap/knowledge → **0**.
- `wc -l commands/dev-cycle.md` → **218 → 198**.
- `python3 -m pytest -q` → **`1178 passed`** (1.176 antes; suben el test nuevo de T-04 y el caso parametrizado que aporta este ledger a `test_cifras_medidas`, no baja ninguno).
- `PYTHONIOENCODING=cp1252 python3 -m pytest -q` → **`1178 passed`**.
- `python3 tests/test_cifras_medidas.py` → `252 passed` (`40 failed, 212 passed` antes de re-medir).
- `python3 scripts/lint_plugin.py` → **exit 0**, `lint_plugin: 9 agentes · 0 errores · 3 avisos`.
- `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 32/32 OK`.
- `python3 evals/check.py` → **exit 0**, `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores`.
- `for t in tests/test_*.py; do python3 "$t"; done` → todas las suites-script en verde.
- `python3 scripts/export-skills.py --out <tmp>` → exit 0, `hash: 51d319bd…5aaea2` (igual en dos pasadas); `--check <tmp>` → exit 0, `export-skills --check: 107 ficheros · 0 problema(s)`.
- `python3 skills/changelog-sync/scripts/changelog-sync.py --check` → **exit 0**, con esta iniciativa listada como pendiente de notas (`· sin-motor-externo (2026-09-04) — Changed, 5 tarea(s) → falta en CHANGELOG.md, CHANGELOG.es.md`): es lo esperado, porque los CHANGELOG están **fuera de alcance** por indicación explícita — el campo `- **Changelog**:` de las cinco tareas ya está escrito para cuando se generen.
- `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-04-sin-motor-externo/tasks.md` → **exit 0**.
