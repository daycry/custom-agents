---
id: ADR-016
titulo: El código que se repite entre piezas se DECLARA en un registro versionado y lo guarda UN test de identidad; no se vendoriza ni se importa un módulo común
estado: propuesta
fecha: 2026-09-10
iniciativa: plugin-refactor
---

# ADR-016: Un registro de copias declaradas + un test de identidad, en vez de un módulo común

## Contexto

Las piezas de este plugin (`agents/`, `skills/`, `agent-kits/`, `scripts/`, `tests/`) tienen que poder **viajar sueltas**: una skill instalada sola en Codex u OpenCode no tiene necesariamente `agent-kits/shared/` al lado. Por eso el mismo código aparece varias veces a propósito, y el `analysis.md` §5 de la iniciativa `plugin-refactor` dejó la disyuntiva abierta («copias declaradas» vs «módulo vendorizado») para que la decidiera `architect`; la evaluación la convirtió en **condición del go** — no se abre `C-03` sin este diseño (`evaluation.md:371`) — y `CA-05` de la spec admitía tres desenlaces: registro comparado por un test, eliminación o vendorizado por el empaquetador.

El recon del repo (2026-09-10) cambió el diagnóstico: el problema **no es la duplicación**, es que hoy conviven **cuatro mecanismos distintos** para el mismo problema, con cuatro grados de garantía y ningún registro que los liste:

- **A** — bloque replicado literal entre centinelas `# --8<--` (`celdas_md` en `scripts/lint_plugin.py:546-566` ↔ `agent-kits/shared/doctor.py:644-664` ↔ `agent-kits/shared/knowledge-find.py:244-264`; criterio del índice de knowledge; criterio de consola), con **test de identidad byte a byte** (`tests/test_knowledge_index.py:198-214`, `tests/test_console_encoding.py:801-804`).
- **B** — canónico cargado por ruta + constante de respaldo local (`REVISION_HDR_PATTERN` de `agent-kits/shared/ledger-lint.py:179` → `agent-kits/shared/task-brief.py:576` y `skills/jira-sync/scripts/jira-flow.py:231`), con **test de comparación de cadenas**.
- **C** — canónico cargado por ruta + **función** de respaldo local (`glob_to_regex`, `piezas()`), **sin ningún guardarraíl**.
- **D** — copia independiente sin carga por ruta (`sin_vallas` en `agent-kits/shared/ledger-lint.py:101` ↔ `skills/changelog-sync/scripts/changelog-sync.py:120`), con test **conductual**, no de identidad (`skills/changelog-sync/scripts/test_changelog_sync.py:940` compara la salida de las dos copias sobre un corpus: **una divergencia que no cambie ese resultado pasa**).

O sea: lo que hoy está **declarado** (en docstrings y comentarios) no está **guardado**, y `ADR-011` («un rol, un dueño») prohíbe justamente dejar implícito un solape de este tipo. El recon también vació la premisa de portabilidad que sostenía al vendorizado (ver alternativas).

## Decisión

Un **registro versionado** —`agent-kits/shared/copias.json`, JSON, una entrada por **unidad compartida**— lista su sitio canónico, sus N sitios copia, el mecanismo (bloque entre centinelas · constante · función) y los **centinelas o el rango** que delimitan el bloque en cada sitio. **UN solo test** recorre el registro y afirma **identidad byte a byte tras normalizar `\r\n` → `\n`**; ese test **falla** (exit code), no avisa. `scripts/lint_plugin.py` da error cuando encuentra en el árbol un bloque idéntico no registrado (marcador `--8<--` o nombre `_*_FALLBACK` sin fila en el registro) — **esa comprobación es parte inseparable de la decisión**: sin ella esto es el statu quo con un JSON encima.

Los cuatro mecanismos se absorben en uno: **C** pasa a tener guardarraíl, **D** pasa de conductual a identidad, **A** y **B** se registran sin cambiar una línea de su texto. Los dos pares que el detector de duplicados cuenta pero **no son código compartido** (bloques de `import` y la cabecera `Uso:`/`Exit:` del docstring) se declaran como no-código y salen del recuento.

Decisiones de detalle cerradas aquí:

- **Formato**: JSON en `agent-kits/shared/` (viaja con el kit por las tres vías de instalación; `install/providers.mjs:22` lleva `agent-kits/` entero). *Descartado*: YAML (dependencia externa) y declararlo en prosa dentro de cada docstring (es exactamente lo que hay hoy y lo que ha fallado).
- **Comparación byte a byte tras normalizar `\r\n` → `\n`**, no comparación de AST ni de texto «equivalente». *Descartado*: comparar bytes crudos — en Windows `core.autocrlf` da un falso positivo por finales de línea (`GOT-007`, mismo motivo por el que el hash de `ADR-014` normaliza).
- **El test falla, no avisa**: guardarraíl determinista con exit code, patrón `ledger-lint`/`qa-gate`. *Descartado*: aviso en el linter — un aviso que nadie lee reproduce la garantía de hoy (`glob_to_regex`: cero).

## Alternativas descartadas

- **O2 — módulo común `_comun.py` vendorizado por el empaquetador dentro de cada pieza.** *A favor:* es la única que hace que un arreglo se haga **en un solo sitio** y que el paquete portable de solo-skills lleve el código sin depender de `agent-kits/`. *En contra:* el recon la vació — `install/providers.mjs:22` (`PAYLOAD_COMUN = ["skills", "agent-kits", "hooks"]`) ya copia `agent-kits/` **entero** a los tres runtimes y `scripts/export-interop.py:26-33` **no traduce ni copia** skills, así que el vendorizado solo aportaría en el `dist/` de «solo skills»; y ahí antes hay que tapar un defecto propio del exportador (`scripts/export-skills.py:399` cierra solo sobre los `.md`: un `_comun.py` citado únicamente desde un `.py` **no viajaría**). Además escribe un fichero generado dentro de carpetas editadas a mano, que es la forma exacta de `GOT-003`, y retirar los respaldos locales convierte un «degrada con aviso» en un fallo duro. Coste **L**: +4,0 h humanas y +0,5 h IA sobre el registro, ~+245 € con margen (`evaluation.md:157`, `:347`).
- **O3 — copias generadas dentro del propio repo (`sync-copias.py` + `--check` como puerta de CI, patrón `export-interop.py`/`LES-012`).** *A favor:* mismo beneficio de «un arreglo, un sitio» que O2 sin tocar empaquetadores ni runtime, y toda pieza sigue siendo standalone por construcción. *En contra ahora:* es un **superconjunto** de esta decisión (necesita el mismo registro como entrada) y añade un generador más, con su `--check` y una séptima puerta a `release.py`, para un problema que un test de identidad ya resuelve. **Queda como la evolución natural de este ADR**: el día en que las copias empiecen a editarse a menudo, se le enchufa `copias.json` como entrada y no hay nada que rehacer. Hoy no se editan a menudo (la rotación está en los hotspots, no en los bloques compartidos).
- **Módulo común importado por ruta relativa (la «O3» del `analysis.md` §5).** Rompe el standalone: una skill copiada sola no tiene `agent-kits/shared/` al lado. Cae por **veto**, no por comparación — requisito multi-runtime del usuario (2026-09-09) y `docs/INTEROP.md`. Que `providers.mjs` lleve `agent-kits/` entero no la reabre: eso solo cubre la vía del instalador oficial, no la copia manual de una skill ni el paquete `dist/`.
- **Eliminar las copias** (tercer desenlace que admitía `CA-05`). Solo aplicaría a los dos pares que no son código, y ahí no hay nada que eliminar: se declaran como no-código. Para las cinco unidades reales, eliminar significa que una pieza pierda una capacidad cuando viaja sola.

## Consecuencias

Lo que hoy está **declarado** pasa a estar **guardado**: un mecanismo en vez de cuatro, con exit code. Es barato (**S**) y **reversible en un gesto** —borrar el JSON, el test y la comprobación del linter deja el árbol byte a byte como estaba: ningún fichero generado, ninguna puerta nueva en `release.py`, ningún punto de carga reescrito—, y no cierra O3, que lo reutiliza entero.

Se renuncia a «un arreglo, un sitio»: corregir un bloque compartido sigue obligando a tocar sus N sitios, y el test lo detecta en **CI**, no al editar. El **7,6 % de duplicado no baja** con ninguna de las tres opciones, y eso está **fuera de objetivo por decisión de la spec** (`spec.md` §7): la señal del §8 es «0 bloques accidentales sin declarar», así que la `Verificación` de `C-03` se escribe sobre el registro y el test, **no** sobre `code-health --baseline`.

**El alcance de `C-03` se encoge**: de «copias accidentales → declaradas o eliminadas» a «unificar cuatro mecanismos de guardarraíl en uno». No hay copias accidentales — dos de los cuatro pares son el patrón «canónico por ruta + respaldo local» ya declarado en su docstring y los otros dos no son código.

**Riesgo asumido, dicho en voz alta:** un registro incompleto da **falsa seguridad**. Por eso el aviso del linter sobre bloques idénticos ≥ N líneas no registrados es parte de la decisión y no un adorno; y por eso su alcance (qué detecta y qué no: es heurística por marcador y por nombre, no exhaustiva) tiene que quedar escrito **dentro** del propio registro.

`copias.json` (build-time, bloques de código fuente en git) **no es** `.claude/pieces.json` de `ADR-014` (runtime, ficheros generados en el proyecto consumidor): dominios y dueños distintos, no se funden. Ningún ADR `aceptada` se contradice; `ADR-014` y `ADR-015` solo se citan como precedente.

## Estado

`propuesta` — opción O1 elegida por el usuario en la puerta de diseño (2026-09-10). Pasa a `aceptada` cuando la revisión de dos lentes valide la implementación de `C-03`; a `obsoleta` si una decisión posterior la reemplaza (candidata conocida: O3, las copias generadas en el árbol).
