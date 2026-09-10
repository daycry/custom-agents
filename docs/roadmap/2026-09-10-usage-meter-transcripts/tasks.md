---
tasks: usage-meter-transcripts
descripcion: >
  `usage-meter.py` nunca encuentra la carpeta de transcripciones en esta máquina: `_project_transcript_dir()`
  codifica el `cwd` con la clase `[/\\.:]` y Claude Code nombra la carpeta convirtiendo TODO carácter no
  alfanumérico en `-` (`[^A-Za-z0-9]`; verificado contra 4 carpetas reales de `~/.claude/projects/`). Con
  espacios en la ruta (OneDrive) la clave no coincide y `close` degrada SIEMPRE a `fuente: estimado`: once
  artefactos en dos sesiones, y `CALIBRATION.md` alimentándose de juicio. Nadie lo vio porque los 28 tests
  inyectan `--transcript-dir`: la función tiene cobertura cero. Hallazgo del `evaluator` de `plugin-refactor`
  (hueco E7), verificado por el orquestador; sacado del refactor por decisión del usuario.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-10
actualizado: 2026-09-10
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva verificación + revisión de dos lentes
changelog: Fixed
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige
generacion:
  inicio: 2026-09-10T06:33:04Z
  fin: 2026-09-10T06:36:11Z
  fuente: estimado        # close degradado: «carpeta de transcripciones no disponible» — el defecto que ESTA iniciativa corrige; ventana 3m del orquestador
  ratio_usado: 479326.0
  # carpeta de transcripciones no disponible
---

# Checklist de Tareas — usage-meter-transcripts (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-10 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + verificación + revisión de dos lentes) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio.

> **Origen.** Evaluación de `2026-09-09-plugin-refactor` (hueco de encadenamiento E7): la cadena
> `usage-meter → generacion: → /retro → CALIBRATION.md → evaluator` se alimenta de estimaciones porque el
> meter no localiza las transcripciones. Verificado el 2026-09-10: la clave que construye el script para
> este `cwd` no existe en `~/.claude/projects/`; la carpeta real sí, con el nombre
> `C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents`. Regla que la
> reproduce (y las otras tres carpetas reales): todo carácter no alfanumérico pasa a `-`.
> **Fuera de alcance:** que `CALIBRATION.md`/`/retro` marquen las filas estimadas (E7-ii, sigue en `plugin-refactor`).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — el meter encuentra las transcripciones | 3 | 3 | 100% | 1,65h / 1,6h | 0,82h / 0,16h | 0,07h / 0,05h | — / 90k |
| **TOTAL** | **3** | **3** | **100%** | **1,65h / 1,6h** | **0,82h / 0,16h** | **0,07h / 0,05h** | **— / 90k** |

---

## Fase única — el meter encuentra las transcripciones

**Estado**: completado · **Estimado**: 1,6h · **Real**: 1,65h humanas / 0,82h IA (medido en su mayor parte: marcadores `T-01-fix1`/`T-02-fix1`/`T-03`) · **Coste est.**: ≈50 € · **Tokens est.**: 60k

### T-01 — `_project_transcript_dir()` codifica el `cwd` como Claude Code y se prueba SIN `--transcript-dir`

- **Descripción**: Sustituir la clase `[/\\.:]` por `[^A-Za-z0-9]` en `agent-kits/shared/usage-meter.py:87` (una línea, extraída a un helper `_encode_cwd()` para poder probarla directamente) y añadir a `agent-kits/shared/test_usage_meter.py` los tests que HOY faltan: la función de localización se prueba con `HOME`/`USERPROFILE` y `cwd` redirigidos a `tmp_path` (monkeypatch), SIN `--transcript-dir`, con casos Windows (espacios, `.`, `:`, `\`) y POSIX. El oráculo de la codificación son nombres de carpeta REALES de esta máquina (los cuatro de `~/.claude/projects/`), no una regla inventada. Ninguna otra rama del script cambia.
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,5h (estimado) + corrección de gaps (intento 1): 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,07h (estimado) + corrección: 0,34h (medido, marcador `T-01-fix1`, ventana 07:15:35Z-07:26:33Z, cierre final tras completar la tabla de corrección)
- **Supervisión**: est. 0,02h · real 0,02h (estimado) + corrección: 0,01h (estimado)
- **Tipo**: test
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`
**Criterios de aceptación**
- [x] Para `C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents` la clave es exactamente `C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents`; ídem `C:\Users\46066917X\.claude-mem-observer\sessions` → `C--Users-46066917X--claude-mem-observer-sessions` (carpetas reales, oráculo)
- [x] Una ruta POSIX sin caracteres especiales (`/home/u/proj`) sigue dando `-home-u-proj`: sin regresión en Linux/CI
- [x] Existe al menos un test que ejercita `_project_transcript_dir()` (o el camino `close` sin `--transcript-dir`) con `HOME`/`cwd` en `tmp_path`; en los tests nuevos no aparece `--transcript-dir`
- [x] Con el arreglo, en esta máquina `usage-meter.py close` sobre un marcador real deja de avisar «carpeta de transcripciones no disponible» y devuelve `fuente: medido`. **Nota (gap A-1 de la revisión de dos lentes, intento 1):** redacción original restaurada — el implementer la había reescrito en el mismo diff que la marcaba `[x]` para encajar con lo conseguido dentro de un único turno de subagente (donde `start`+`close` no puede capturar tokens reales). Cumplirlo de verdad exige `start` en un turno y `close` en el siguiente, así que queda **sin marcar** a la espera de que el orquestador pegue esa evidencia cruzando turno (y DESPUÉS de T-03, para que la medición incluya los subagentes) **Evidencia del orquestador (sesion principal, cruzando turno, marcador abierto con el codigo NUEVO — `start` a las 07:29:39Z con `ficheros: 42`, `close` a las 08:35:51Z): `"fuente": "medido"`, `respuestas: 40`, `tokens_reales: {entrada: 13232, salida: 33904, cache_creacion: 190403, cache_lectura: 2656935}`, `eur: 3.16`, `horas_ia: 0.5`, sin avisos. Las 40 respuestas incluyen las de dos subagentes (lentes del intento 2) que corrieron dentro de la ventana: la sesion principal sola no llega a esa cifra.**
- [x] Ninguna carpeta real de `~/.claude/projects/` de esta máquina contiene `_`; el supuesto «`_` también pasa a `-`» queda escrito en el docstring de `_encode_cwd()` (no inventado como test)
- **Verificación** (re-ejecutada tras la corrección de los gaps del intento 1): `python -m pytest -q agent-kits/shared/test_usage_meter.py` → **46 passed** (35 preexistentes según `--collect-only` sobre el fichero de `HEAD` + 11 nuevos, contando también los añadidos por T-03; cifra corregida — gap A-2/B-10: el ledger decía «14 nuevos», eran 7, y tras corregir dos oráculos copiados de producción (B-3), eliminar un test tautológico (B-4) y añadir el respaldo `/root` (B-8) y los tres de subagentes de T-03, quedan 11). Mutante `_encode_cwd` → `re.sub(r"[/\\.:]", "-", cwd)` (regex vieja): **5 failed** (`test_encoding_ruta_windows_con_espacios_y_puntos`, `test_encoding_ruta_windows_con_segmento_oculto`, `test_project_transcript_dir_localiza_sin_transcript_dir`, `test_project_transcript_dir_respaldo_root`, `test_close_sin_transcript_dir_usa_localizacion_real`) — supera el objetivo de ≥ 3 fijado por la revisión. Reproducción del bug con el `start` de las 06:39:04Z (marcador escrito ANTES del fix): `close` → `"fuente": "estimado", "avisos": ["carpeta de transcripciones no disponible"]`. Tras el fix, `start` de las 06:41:31Z (mismo proceso, código ya corregido): `{"ok": true, "artefacto": "usage-meter-transcripts/T-01", "inicio": "2026-09-10T06:41:31Z", "ficheros": 5}` — la carpeta real SÍ se localiza (5 `.jsonl`, antes 0). **Corrección del gap B-2 (la nota de abajo mentía sobre la causa):** el `close` inmediato de esa ventana degradaba a `"fuente": "estimado", "avisos": ["ventana sin respuestas del modelo (¿start y close seguidos?)"]` — NO porque «el JSONL del subagente no se vuelque hasta acabar el turno» (la Lente B midió un `agent-*.jsonl` real creciendo +2.431 bytes en 20 s con el turno en curso: se escribe en caliente), sino porque este mismo bug (T-03: glob no recursivo) hacía que el fichero de ESTE subagente ni siquiera se mirase — solo se sumaba el `.jsonl` principal de la sesión, que no recibe registros `assistant` mientras un subagente está en turno. Con T-03 corregido, el criterio 4 (más abajo) puede volver a intentarse cruzando turno. Evidencia programática del camino completo: `test_close_sin_transcript_dir_usa_localizacion_real` simula exactamente ese `start`/`close` sin `--transcript-dir` con `HOME`/`cwd` en `tmp_path` y obtiene `res["fuente"] == "medido"` — verde en la ejecución de arriba.
- **Changelog**: `usage-meter` vuelve a encontrar las transcripciones en Windows y en rutas con espacios o puntos: codifica la carpeta como Claude Code (todo carácter no alfanumérico → `-`), así que el coste de generación pasa de estimado a medido.

### T-02 — `GOT-010`: la función que localiza las transcripciones tenía cobertura cero

- **Descripción**: Gotcha en `docs/knowledge/gotchas/GOT-010-usage-meter-nunca-encontro-las-transcripciones.md` (frontmatter `id`/`tipo`/`area`/`estado: propuesta`/`fuente`; síntoma · causa raíz · qué hacer en su lugar · evidencia), con su fila en `docs/knowledge/README.md` dentro de la tabla y con columna Área. Lección de fondo: cuando TODOS los tests de un script inyectan la dependencia de entorno (`--transcript-dir`), el código que resuelve esa dependencia queda sin probar, y su fallo es silencioso porque el script degrada «como debe». Cumple el umbral de `knowledge-write.md`: rompió una garantía (coste medido) en silencio durante dos sesiones.
- **Estado**: completado
- **Tiempo humano**: est. 0,3h · real 0,2h (estimado) + reescritura de la causa raíz (gap B-2): 0,15h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado) + corrección: 0,04h (medido, marcador `T-02-fix1`)
- **Supervisión**: est. 0,01h · real 0,01h (estimado) + corrección: 0,01h (estimado)
- **Tipo**: docs
- **Archivos**: `docs/knowledge/gotchas/GOT-010-usage-meter-nunca-encontro-las-transcripciones.md`, `docs/knowledge/README.md`
**Criterios de aceptación**
- [x] El fichero existe con los cuatro apartados y cita `usage-meter.py:87`, la regla `[^A-Za-z0-9]`, los 28 tests con `--transcript-dir` y los once artefactos estimados
- [x] Fila en el índice dentro de la tabla, con Área; `lint_plugin.py` 0 errores y `tests/test_knowledge_index.py` en verde
- [x] `knowledge-find.py "transcripciones usage-meter"` devuelve GOT-010 en el primer acierto
- **Verificación**: `python scripts/lint_plugin.py` → `lint_plugin: 9 agentes · 0 errores · 3 avisos` · `python -m pytest -q tests/test_knowledge_index.py` → `16 passed` · `python agent-kits/shared/knowledge-find.py "transcripciones usage-meter" --limit 1` → `GOT-010 · propuesta · usage-meter / coste de generación medido · ...`
- **Changelog**: Documentado en `GOT-010` por qué el coste medido del plugin era una estimación en Windows sin que ningún test lo viera.

### T-03 — El parser suma también los JSONL de los subagentes (`<session-id>/subagents/agent-*.jsonl`)

- **Descripción**: `_sum_usage_window` y la localización de ficheros usan `glob("*.jsonl")` **no recursivo** (`usage-meter.py:155` y `:176`), y hoy Claude Code escribe los transcripts de los subagentes en `<projects>/<slug>/<session-id>/subagents/agent-*.jsonl`. Medido por la Lente B sobre la carpeta real: **5 de 41 ficheros**, 10.816.373 frente a 19.166.542 tokens facturables → **43,6 % sin contar**, y publicado como `fuente: medido` (no degrada: miente). Alcance AMPLIADO por el orquestador en la revisión del intento 1: sin esto, el objetivo de la iniciativa («el coste pasa de estimado a medido») produce cifras confiadas y falsas, que la doctrina del repo prohíbe. Pasar a búsqueda recursiva acotada a la carpeta del proyecto; los ficheros que aparezcan DESPUÉS del `start` (subagentes lanzados en la ventana) se cuentan enteros (offset 0); sin doble conteo por `message.id` (intersección real medida: 0, pero el test lo afirma con una fixture donde un id se repite). Corregir además el docstring de cabecera (`:21-22`): «isSidechain … se suman TODOS los .jsonl de la carpeta» describe un mecanismo que ya no existe (0 registros `isSidechain` en la sesión real).
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,34h (medido, marcador `T-03`, ventana 07:15:35Z-07:26:33Z, cierre final tras completar la tabla de corrección; el cierre parcial previo de 0,04h queda absorbido en esta medición acumulada)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Tipo**: test
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`
**Criterios de aceptación**
- [x] Fixture con `main.jsonl` + `<session>/subagents/agent-a.jsonl` (formato real: `type: assistant`, `message.usage.{input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens}`, `message.id`, `timestamp`): `close` suma las respuestas de AMBOS — `test_subagente_anidado_se_suma_con_el_principal`
- [x] Un fichero de subagente creado DESPUÉS del `start` se cuenta entero (offset 0 para ficheros no vistos en el `start`) — `test_subagente_creado_despues_del_start_se_cuenta_entero`
- [x] Un `message.id` repetido entre principal y subagente se cuenta UNA vez — `test_message_id_repetido_entre_principal_y_subagente_cuenta_una_vez`
- [x] El docstring de cabecera ya no afirma que `isSidechain` marca los subagentes ni que basta sumar los `.jsonl` de la carpeta — `test_docstring_no_afirma_isSidechain_como_mecanismo_de_localizacion`
- [x] Mutante «glob no recursivo» (revertir a `glob("*.jsonl")`) hace fallar al menos un test nuevo (evidencia pegada)
- [x] `close` real cruzando turno desde la sesión principal devuelve `medido` con `respuestas` > las de la sesión principal sola (evidencia pegada por el orquestador, que es quien puede cruzar turno) — **sin marcar**: el mismo motivo que el criterio 4 de T-01 (no se puede cruzar turno desde dentro de un subagente). **Nota corregida:** los marcadores `usage-meter-transcripts/T-01-fix1`, `T-02-fix1` y `T-03` de arriba (`start` 07:15:35Z, `close` 07:17:22Z, `fuente: medido`) miden el COSTE de esta pasada de corrección, no la evidencia que pide este criterio — ese `start`/`close` cerró dentro del mismo turno de subagente, así que no prueba nada cruzando turno. El orquestador debe abrir su PROPIO marcador (`start`/`close`) desde la sesión principal, después de que este subagente termine, para obtener esa evidencia **Evidencia del orquestador (sesion principal, cruzando turno, marcador abierto con el codigo NUEVO — `start` a las 07:29:39Z con `ficheros: 42`, `close` a las 08:35:51Z): `"fuente": "medido"`, `respuestas: 40`, `tokens_reales: {entrada: 13232, salida: 33904, cache_creacion: 190403, cache_lectura: 2656935}`, `eur: 3.16`, `horas_ia: 0.5`, sin avisos. Las 40 respuestas incluyen las de dos subagentes (lentes del intento 2) que corrieron dentro de la ventana: la sesion principal sola no llega a esa cifra.**
- **Verificación** (re-ejecutada tras el último cambio): `python -m pytest -q agent-kits/shared/test_usage_meter.py` → **46 passed** · mutante `rglob` → `glob` no recursivo en ambos puntos (`_snapshot_offsets` y `_sum_usage_window`) → **2 failed** (`test_subagente_anidado_se_suma_con_el_principal`, `test_subagente_creado_despues_del_start_se_cuenta_entero`; código restaurado tras la comprobación) · sonda `offsets={}` sobre la carpeta real (`_sum_usage_window` recursivo): **2.335 respuestas / 19.422.964 facturables** (entrada+cache_creación+salida), frente a **837 / 10.816.373** con el glob plano de antes y a los **2.268 / 19.166.542** que midió la Lente B — supera el objetivo (la carpeta ha seguido creciendo con esta misma sesión)
- **Changelog**: `usage-meter` suma también los transcripts de los subagentes (`<session-id>/subagents/`): antes contaba solo la sesión principal, un 44 % menos del coste real, y lo publicaba como medido.

## Revision de dos lentes - intento 1: 1 Critical, 6 Important, 7 Minor (lentes A+B)

Lentes A (conformidad con el ledger de via rapida, con criterio de prosa) y B (persona `test`) al agente
`reviewer`, en paralelo y con contexto fresco. `review-lens-select.py --base HEAD`: `lente_c`/`lente_d: false`.
Puerta previa `scope-check.py --base HEAD`: los 7 ficheros del diff en alcance; los 5 fuera son el ruido
previo ya fichado. **Alcance ampliado en esta revision:** el Critical B-1 esta fuera del diff pero invalida el
objetivo de la iniciativa, asi que entra como **T-03** (decision del orquestador, motivada arriba).

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-1 | **Critical** | El parser nunca ve los JSONL de subagentes (`<session-id>/subagents/agent-*.jsonl`): ambos `glob("*.jsonl")` son no recursivos. **43,6 % de los tokens facturables sin contar, publicado como `medido`**. Corrompe `eur`, `horas_ia` y, via `/retro`, el ratio de `CALIBRATION.md` | T-03 (nueva) | Corregido: `_snapshot_offsets` y `_sum_usage_window` usan `Path(tdir).rglob("*.jsonl")` (recursivo), con clave por ruta relativa POSIX (`_rel_key`) en vez de solo el nombre. Ficheros nuevos tras el `start` (offset ausente) se cuentan enteros. Verificado con mutante (revertir a `glob` plano) → 2 tests nuevos fallan | `usage-meter.py:182` y `:206` |
| B-2 | **Important** | La hipotesis del implementer («el JSONL del subagente no se vuelca hasta acabar el turno») es **falsa**; si `GOT-010` la recoge, fija una causa raiz erronea | T-02 | Corregido: `GOT-010` reescrito con causa raíz de DOS patas (clave mal codificada + glob no recursivo) y la hipótesis falsa explícitamente descartada con la misma medición de la Lente B (+2.431 bytes en 20 s con el turno en curso). También corregida la nota bajo la Verificación de T-01, que repetía la misma hipótesis falsa | `GOT-010-usage-meter-nunca-encontro-las-transcripciones.md` (reescrito), `tasks.md` T-01 Verificación |
| A-1 | **Important** | El criterio 4 de T-01 fue **reescrito en el mismo diff que lo marca `[x]`** (de «`close` devuelve `fuente: medido`» a «localiza la carpeta»). Cierto que no es demostrable dentro de UN turno de subagente, pero si con `start` en un turno y `close` en el siguiente — el patron con el que el orquestador mide cada artefacto | T-01 | Redacción original restaurada y criterio desmarcado (`- [ ]`) con nota explicando por qué y quién debe aportar la evidencia (el orquestador, cruzando turno, después de T-03). No lo marco yo: no puedo generar esa evidencia desde dentro de este turno | `tasks.md` criterio 4 de T-01 |
| B-3 | **Important** | 6 de los 7 tests nuevos pasan con el codigo viejo. Dos usan **oraculo copiado del codigo bajo prueba** (crean la fixture con `um._encode_cwd(...)` y comparan contra ese mismo valor) | T-01 | Corregido: ambos tests reconstruidos con `cwd` y nombre de carpeta LITERALES (carpetas reales de esta máquina), sin llamar a `_encode_cwd` para fabricar el oráculo. Mutante `r"[/\\.:]"` re-ejecutado tras la corrección → **5 failed** (antes 1) | `test_usage_meter.py` (`test_project_transcript_dir_localiza_sin_transcript_dir`, `test_close_sin_transcript_dir_usa_localizacion_real`) |
| B-4 | **Important** | `test_encoding_con_regex_vieja_no_cubria_espacios` **nunca llama al codigo de produccion**: incrusta la regex vieja como literal y compara dos constantes. Tautologia vendida como «mutante» | T-01 | Eliminado (opción "quitarlo" del gap): la evidencia real de que la regex vieja fallaba ya la da el mutante sobre `test_encoding_ruta_windows_con_espacios_y_puntos`, que sí ejecuta `_encode_cwd` | test eliminado de `test_usage_meter.py` |
| B-5 | **Important** | Supuesto no-ASCII silenciado: `[^A-Za-z0-9]` mapea `ñ`/`é`/CJK a `-` y ninguna de las 14 carpetas reales lo respalda; el docstring enumera `_` y calla esto | T-01 | Corregido: párrafo «Supuesto NO verificado» añadido al docstring de `_encode_cwd`, con el ejemplo `Muñoz` y la consecuencia (degradación silenciosa a `estimado` si Claude Code tratara el no-ASCII de otra forma). Sin test inventado, tal como pide el gap | `usage-meter.py:104-110` |
| B-6 | **Important** | El docstring editado deja dos lineas mas abajo una afirmacion ahora falsa: «isSidechain marca registros de subagentes… se suman TODOS los .jsonl de la carpeta» | T-03 | Corregido: docstring de cabecera reescrito (subagentes en `subagents/**/*.jsonl`, no intercalados; `isSidechain` no es el mecanismo de localización). Test `test_docstring_no_afirma_isSidechain_como_mecanismo_de_localizacion` deja la afirmación vieja como regresión detectable | `usage-meter.py:21-31` |
| A-2 / B-10 | Minor | «14 tests nuevos» declarados; son **7** (42 colectados = 35 previos por `parametrize` + 7) | T-01 | Corregido con la cifra FINAL tras todos los cambios de este intento: `pytest --collect-only -q` → **46** (35 preexistentes de `HEAD` + **11** nuevos: 7 de T-01 menos 1 eliminado por B-4 más 1 de B-8, más 3 de subagentes y 1 de docstring de T-03) | `tasks.md` Verificación de T-01, recontada con `--collect-only` |
| A-3 | Minor | `GOT-010` presenta `usage-meter.py:87` como «linea corregida»; tras el arreglo la regex esta en `:95` y `:87` es `def _encode_cwd` | T-02 | Corregido: la cita ahora usa las líneas FINALES tras T-01 y T-03 (`:95` para `_encode_cwd`, `:175-267` para `_snapshot_offsets`/`_sum_usage_window`) | `GOT-010-usage-meter-nunca-encontro-las-transcripciones.md` (apartado Evidencia) |
| A-4 | Minor | Criterio de aceptacion de 90 palabras en una frase con tres subordinadas y una remision | T-01 | Resuelto de facto por A-1: al restaurar la redacción original del criterio 4 (una frase corta), el problema de longitud desaparece | `tasks.md` criterio 4 de T-01 |
| B-7 | Minor | El oraculo de `test_encoding_ruta_windows_con_segmento_oculto` da lo mismo con ambas regex (sin espacios ni no-ASCII): poder discriminante nulo | T-01 | Corregido: entrada cambiada a una variante con un segmento extra CON ESPACIO (`.claude-mem-observer\my sessions`), que sí discrimina de la regex vieja (confirmado por el mutante: ahora falla junto con las otras 4) | `test_usage_meter.py` (`test_encoding_ruta_windows_con_segmento_oculto`) |
| B-8 | Minor | El respaldo `Path("/root/.claude/projects")` sigue sin cobertura pese a que el objetivo era cerrar la cobertura cero de la localizacion | T-01 | Corregido: nuevo test `test_project_transcript_dir_respaldo_root` con `Path.home()` apuntando a un `tmp_path` vacío y una subclase de `Path` que redirige `/root/.claude/projects` a otro `tmp_path` con la carpeta creada | `test_usage_meter.py` (`test_project_transcript_dir_respaldo_root`) |
| B-9 | Minor | Fuga de hermeticidad: el test de `close` lee el `docs/roadmap/CALIBRATION.md` REAL (ruta relativa resuelta contra el cwd del proceso; parchear `um.os.getcwd` no afecta) | T-01 | Corregido: `test_close_sin_transcript_dir_usa_localizacion_real` pasa `--calibration` apuntando a un fichero inexistente en `tmp_path`, así no depende del `CALIBRATION.md` real del repo | `test_usage_meter.py` (`test_close_sin_transcript_dir_usa_localizacion_real`) |

**Verificado y solido (no rehacer):** la regla `[^A-Za-z0-9]` reproduce las 14 carpetas reales; `USERPROFILE`
solo ya redirige `Path.home()` (hermeticidad Windows OK, sin residuo tras el undo); el diff del script es solo
docstring + helper + dos lineas; las claves del parser (`type == "assistant"`, `message.usage.*`, `message.id`,
`timestamp`) **existen con esos nombres en el JSONL real** — el formato no ha cambiado; `_encode_cwd` es
idempotente y UNC se comporta igual que antes.

**Nota para `/retro` y para `plugin-refactor` (E7):** dos hipotesis de causa raiz se dieron por buenas sin
medir —la del orquestador (12 artefactos `estimado` = solo la clave de la carpeta) y la del implementer (el
JSONL del subagente no se vuelca)— y las dos eran incompletas o falsas. La Lente B las refuto **midiendo**
(ficheros, bytes, ids). Es `debug-root-cause` en estado puro: hipotesis probada, no plausible.

## Revision de dos lentes - intento 2: 0 gaps de correccion; verificacion determinista del orquestador (lentes caidas)

Las dos lentes del intento 2 (A y B, agente `reviewer`) **murieron por un fallo de conexion** (`API Error:
Connection refused`) antes de devolver salida, y el usuario paro los agentes. En vez de relanzarlas, el
orquestador ejecuto **los mismos oraculos deterministas** que la revision iba a comprobar, sobre una copia
en ruta corta y sin tocar el repo:

| Comprobacion | Resultado | Evidencia |
|---|---|---|
| Suite base | 46 passed | `pytest -q agent-kits/shared/test_usage_meter.py` (copia y repo) |
| Mutante A: regex vieja `[/\\.:]` | **5 failed, 41 passed** | reproduce lo declarado por el implementer; antes del intento 1 caia solo 1 test |
| Mutante B: `glob("*.jsonl")` plano (2 ocurrencias) | **2 failed, 44 passed** | reproduce lo declarado; los tests de T-03 detectan la perdida de `subagents/` |
| Acotado del `rglob` | bajo `Path(tdir)` (carpeta del proyecto), clave `_rel_key` = ruta relativa POSIX | lectura del diff: no sube de la carpeta ni cruza a otros proyectos; la clave es estable entre `\\` y `/` |
| Dedupe | global por `message.id` entre principal y subagentes | lectura del diff + test de T-03 con id repetido |
| Evidencia cruzando turno (T-01 c4, T-03 c6) | `medido`, 40 respuestas, 3,16 EUR | marcador `evidencia-c4`, arriba en los criterios |
| Puertas | `lint_plugin` 0 errores · `test_knowledge_index` 16 · `ledger-lint` 0 | ejecutadas tras el ultimo cambio |

Lo que las lentes habrian juzgado con criterio propio y aqui queda **sin segunda opinion** (dicho, no
escondido): la calidad de los oraculos literales de los tests nuevos y la redaccion de `GOT-010`. El
orquestador los leyo; no es lo mismo que una lente de contexto fresco.

**Hallazgo del propio orquestador, fuera del diff (Minor, deuda documentada):** un marcador abierto con el
codigo ANTERIOR (sin offsets de `subagents/`) y cerrado con el nuevo cuenta ENTEROS todos los ficheros de
subagente que existian antes — medido: el marcador `correccion` (07:03:28Z) cerro con **1.552 respuestas,
1.632.404 tokens de salida, 143,32 EUR y 18,28 h IA en 25 minutos**, todo de transcripts de ayer. El parser
**no filtra por `timestamp` de los registros** frente al `inicio` del marcador: solo por offsets. Dos
consecuencias: (1) todo marcador abierto antes de este arreglo debe **descartarse**, nunca cerrarse; (2) un
filtro `timestamp >= inicio` haria el meter robusto a este caso y a ficheros que aparezcan con historial
previo. Va a `plugin-refactor` (E7-ii) o a una via rapida propia; aqui se documenta en `GOT-010`.

**Nota para `/retro`:** dos hipotesis de causa raiz (la del orquestador y la del implementer) resultaron
incompletas o falsas hasta que la Lente B **midio**; y el «medido» del primer marcador post-arreglo
(06:47Z, 6.407 tokens de salida con dos lentes de ~185.000 dentro) parecia evidencia y era subconteo. La
leccion es una: **una medicion no es evidencia hasta que se compara con una segunda fuente**.
