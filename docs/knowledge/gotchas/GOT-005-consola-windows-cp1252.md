---
id: GOT-005
tipo: gotcha
area: Scripts / consola y codificación
estado: aceptada (validada: usuario, 2026-09-03)
fuente: docs/roadmap/2026-09-03-windows-console/tasks.md (T-01/T-02/T-04/T-05, traceback del usuario en PowerShell)
---

## Los tres streams y el proceso padre: en cp1252 revienta el que NO reconfiguró, y el que revienta es el hijo del PIPE, no la consola

- **Síntoma:** el usuario ejecuta `python scripts/release.py 1.16.0` en PowerShell (Windows español)
  y el release aborta. En la traza, quien falla es `lint_plugin.py`:
  `File "...\scripts\lint_plugin.py", line 596, in main / print(f"\u26a0\ufe0f  {w}")` →
  `File "C:\...\Lib\encodings\cp1252.py", line 19, in encode` →
  `UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1`. Y, en cascada,
  `release.py` presentó el crash como `changelog-sync --check: PENDIENTE` — deuda de notas
  inexistente. Reproducible en cualquier SO: `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py`.
- **Síntoma 2 (el mismo bug por `stdin`, encontrado al revisar T-01):** el hook `PreToolUse` del
  `implementer` deja de denegar EN SILENCIO en cuanto el contenido que se va a escribir lleva un
  emoji o un `—`. Medido: `PYTHONIOENCODING=cp1252` + payload
  `{"tool_name":"Write","tool_input":{"file_path":"docs/roadmap/2026-09-03-x/spec.md","content":"👍 ok"}}`
  → stdout **vacío**, exit 0 y en stderr `guardrail-check: error interno (UnicodeDecodeError(…)) — se
  permite`; el MISMO payload sin emoji → `permissionDecision: deny` correcto. La causa: el payload se
  leía con `sys.stdin.read()`, que usa el codec del locale, y el `except Exception` que existe para
  «un guardrail roto nunca bloquea» convertía el error de codificación en un **allow**.
- **Síntoma 3 (el lado PADRE, regresión introducida por el propio arreglo):** un script que LANZA a
  otro y lee su salida con `capture_output=True, text=True` **sin `encoding=`** revienta en consola
  cp1252 justo donde antes daba su veredicto. Medido en `task-brief.py` → `ledger-lint.py`, en el
  camino caliente de `/dev-cycle`: antes exit 2 con `❌ ledger inválido — arregla tasks.md antes de
  despachar`; después `UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 0` (el primer
  byte de `❌` = `E2 9D 8C`, que es con lo que empieza la salida del hijo), exit 1 y traceback
  crudo. Es consecuencia directa de arreglar el lado hijo: desde entonces los hijos escriben UTF-8
  SIEMPRE, así que decodificarlos con el codec del locale ya no funciona nunca.
- **Síntoma 4 (el que LEE no se ve en su fuente):** un `.py` **100 % ASCII** revienta igual si lee
  `stdin`, porque ahí no manda el fuente sino el **payload**. Medido en
  `agent-kits/nemesis/tools/pick_asset.py`, que hacía `json.load(sys.stdin)` sobre el JSON de una
  release de GitHub (cuyo `body` trae las notas con emojis: 🐛 = `F0 9F 90 9B` con el byte `0x90`,
  👍 con `0x8D`, ninguno definido en cp1252): `PYTHONIOENCODING=cp1252 … pick_asset.py linux amd64`
  → `bad json: 'charmap' codec can't decode byte 0x81 in position 19: character maps to <undefined>`
  y **exit 1**. Y otra vez el crash disfrazado de veredicto: `install-tools.sh` manda ese stderr al
  log, ve la URL vacía y anuncia `[!!] <tool>: no release asset for <os>/<arch>` con
  `record … failed no-asset`. Un fallo de codificación presentado como «este proyecto no publica
  binario para tu plataforma». Era la 28.ª pieza versionada y la única sin snippet: el criterio de
  la ronda anterior solo miraba ficheros con no-ASCII en el fuente, o sea solo el lado que ESCRIBE.
- **Síntoma 5 (la misma clase en shell):** los `python3 -c` en línea de `hooks/` y `statusline/`
  leen el payload del hook y componen su JSON sin reconfigurar nada. Bajo cp1252 revientan en cuanto
  el texto trae un byte que ese codec no define — `❌` (`0x9D`), `⚠️` (con el selector de variación,
  `0x8F`), `👍` (`0x8D`) — y el `2>/dev/null || true` con el que el hook degrada se lo traga.
  Medido en `progress-line.sh` con una fase llamada «consola ❌ rota»: stdout **vacío** antes, y el
  `{"systemMessage": …}` íntegro después. No es mojibake: los bytes que cp1252 sí define (`📋`, `·`)
  hacen ida y vuelta idénticos; lo que se pierde es la línea entera, en silencio.
- **Causa raíz:** dos, encadenadas. **(1)** La consola no es la culpable: en Python ≥ 3.6 una consola
  Windows real usa `WriteConsoleW` y los emojis salen bien — de hecho `release.py` imprimió sus
  propias líneas con `⚠️` sin problema. El que revienta es el **proceso hijo**, porque `release.py`
  lanza los checks con `subprocess.run(..., capture_output=True)`: con stdout a un **pipe** Python
  no usa la API de consola y cae al `locale.getpreferredencoding()`, que en un Windows español es
  **cp1252**, un charmap sin emojis. Cualquier script del plugin puede ser ese hijo (los agentes y
  las skills los invocan así), de modo que el arreglo tiene que estar en cada script, no en el
  terminal ni en una variable de entorno del usuario. **(2)** El crash salió con **exit 1**, el mismo
  exit que el veredicto legítimo «hay entradas pendientes», así que el orquestador lo tradujo a
  `PENDIENTE`: un fallo de entorno disfrazado de deuda de proceso.
- **Qué hacer en su lugar:** **(a)** en todo script que **imprima símbolos** o **lea de `sys.stdin`**,
  reconfigurar los **tres** streams a nivel de módulo, **antes de leer o imprimir nada** (no dentro de
  `main()`: hay scripts que imprimen desde funciones sueltas o al importarse). Los dos motivos son
  independientes y el segundo **no se ve en el fuente** (síntoma 4); esa es exactamente la regla que
  vigilan el linter y la suite, ni más ni menos:

  ```python
  # Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
  for _s in (sys.stdin, sys.stdout, sys.stderr):
      try: _s.reconfigure(encoding="utf-8", errors="replace")
      except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)
  ```

  `sys.stdin` entra porque es exactamente el mismo bug por el stream que faltaba (síntoma 2). El
  `except` cubre los tres casos reales y medidos: stream **ya leído** (`UnsupportedOperation: It is
  not possible to set the encoding or newline of stream after the first read`), `sys.stdin` **`None`**
  (`pythonw.exe`) y stream sin el método (el `capsys` de pytest). «Medido» significa medido sobre un
  script REAL con los tres estados y con su mutación: quitarle el `except` al snippet de
  `ledger-lint.py` lo tumba en los tres casos (`UnsupportedOperation` · `AttributeError` ×2), y eso
  es lo que prueba `test_el_mismo_arranque_sin_except_revienta`. En un `.sh` no hay fichero donde
  pegar el snippet: el `python3 -c` en línea que lea `stdin` o imprima símbolos lleva delante
  `PYTHONIOENCODING=utf-8:replace` (síntoma 5).

  Se replica **LITERAL** en cada script y no se factoriza a un módulo común: los scripts del plugin
  son **standalone** (el paquete portable los copia sueltos y los agentes los invocan con
  `python3 <ruta>`, sin `PYTHONPATH`), así que el `import` compartido sería justo la dependencia que
  el paquete portable no puede satisfacer. **(b) No basta con la salida propia: el proceso PADRE
  también tiene que decodificar bien.** Quien capture a un hijo en modo texto le pasa
  `encoding="utf-8", errors="replace"` — nunca `text=True` a secas—, porque los scripts del plugin
  escriben UTF-8 siempre y el codec del locale ya no sirve para leerlos. Y lo mismo para el que LEE
  un payload por `stdin`: ese es el otro extremo de la misma tubería. Este es el aprendizaje que
  faltaba en la primera ronda y que causó los dos fallos críticos: **arreglar solo el lado que
  escribe deja el bug intacto en el lado que lee, y encima lo mueve al padre.** **(c)** Quien EJECUTA
  un check ajeno no puede tratar su exit code como veredicto sin más: un `Traceback` en stderr, o un
  exit que no es 0 ni 1, es «no se pudo ejecutar» y merece su propio mensaje (y bloquear), no el
  veredicto negativo del check.
- **Matices medidos (para no sobre-corregir):** `reconfigure(encoding="utf-8")` **gana a
  `PYTHONIOENCODING`**, así que la salida sale en UTF-8 íntegro y `errors="replace"` no llega a
  dispararse: los emojis **no** degradan a `?` (bytes reales del pipe: `342 234 205` = `E2 9C 85` =
  `✅`). Por eso **no** se añadió un modo ASCII: solo cubriría la consola Windows *legacy*
  (`PYTHONLEGACYWINDOWSSTDIO=1` o `cmd.exe` con codepage antiguo), donde UTF-8 se ve como mojibake
  (`âœ…`) y no como `?`. Otro matiz: un script puede quedar protegido **de rebote** si importa por
  ruta a otro que sí lleva el snippet (medido: `lint_plugin.py` sin snippet seguía saliendo 0 porque
  ejecuta `evals/check.py`; borrando `evals/` volvía el crash) — por eso la comprobación estática
  del linter y del test no es redundante con la ejecución. Y un tercero: **la comprobación estática
  tiene que ser ESTRUCTURAL, no un `grep` de subcadena**. Medido: con `CONSOLE_MARK in data`, un
  script con el snippet dentro de `main()` (y un `print` de símbolos a nivel de módulo antes) o con
  la marca solo citada en un docstring daba **0 avisos** y reventaba igual bajo cp1252. Hoy se
  comprueba con `ast`: la llamada tiene que estar en una sentencia de nivel de módulo y antes de
  cualquier otra que no sea el docstring o un import. Y el cuarto, el que cerró T-05: **el criterio
  de a QUIÉN se le exige no puede salir solo del fuente**. «Tiene bytes no ASCII» es el criterio del
  lado que escribe; el que lee se detecta por usar `sys.stdin` (con `ast`, para que una mención en un
  comentario no cuente), porque su riesgo lo trae el payload. Con el criterio viejo, 27 de 28 piezas
  llevaban el snippet y la que faltaba era justo un lector.
- **Evidencia / fuente:** [`docs/roadmap/2026-09-03-windows-console/tasks.md`](../../roadmap/2026-09-03-windows-console/tasks.md)
  (T-01, T-02, T-04 y T-05, con el traceback del usuario y las mediciones); regla en
  [`docs/CONVENTIONS.md`](../../CONVENTIONS.md) (regla 8) y en
  [`skills/plugin-dev/SKILL.md`](../../../skills/plugin-dev/SKILL.md) (Paso 2, regla 6); vigilancia en
  `scripts/lint_plugin.py` (`lint_console_encoding` para el lado propio y `lint_subprocess_encoding`
  para el lado padre, ambas estructurales) y prueba bajo `cp1252`/`ascii` en
  `tests/test_console_encoding.py`, que replica LITERAL el mismo criterio y lo compara con el del
  linter.

`estado: aceptada (validada: usuario, 2026-09-03)`
