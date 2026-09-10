---
id: GOT-010
tipo: gotcha
area: usage-meter / coste de generación medido
estado: propuesta (hallazgo del evaluator de plugin-refactor, hueco E7, verificado por el orquestador, 2026-09-10)
fuente: docs/roadmap/2026-09-10-usage-meter-transcripts/tasks.md (T-01); 28 tests de agent-kits/shared/test_usage_meter.py con `--transcript-dir`
---

## La función que localiza y suma las transcripciones tenía cobertura cero, y sus dos fallos (clave mal codificada, glob no recursivo) eran silenciosos por diseño

- **Síntoma:** en esta máquina, `usage-meter.py close` nunca devolvía `fuente: "medido"` — siempre avisaba
  «carpeta de transcripciones no disponible», por más marcadores `start`/`close` que se ejecutaran. Once
  artefactos generados en las sesiones del 2026-09-09 y 2026-09-10 quedaron con `generacion.fuente:
  estimado`, alimentando `CALIBRATION.md` (y de ahí al `evaluator`) con juicio en vez de tokens reales.
  Corregido ese primer fallo, apareció un segundo, más grave porque NO degradaba: `close` sí encontraba
  carpeta y devolvía `fuente: "medido"`, pero contaba solo el 56,4 % de los tokens facturables reales —
  midiendo con confianza una cifra falsa.
- **Causa raíz (dos patas, ninguna de ellas la hipótesis inicial del implementer):**
  1. **Clave de carpeta mal codificada.** `_project_transcript_dir()` (extraída luego a `_encode_cwd()`)
     codificaba el `cwd` con `re.sub(r"[/\\.:]", "-", cwd)`, una regla que solo cubre barras, puntos y dos
     puntos. Claude Code, al nombrar la carpeta de transcripciones en `~/.claude/projects/`, convierte
     **todo carácter no alfanumérico** en `-` (verificado contra las carpetas reales de esta máquina). Con
     un `cwd` como `C:\Users\...\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents`
     (espacios de sobra), la clave vieja no coincidía con la carpeta real y la búsqueda fallaba siempre.
  2. **Glob no recursivo ignora los subagentes.** Con la clave ya corregida, `_snapshot_offsets` y
     `_sum_usage_window` seguían usando `Path(tdir).glob("*.jsonl")` (no recursivo), y Claude Code escribe
     los transcripts de los subagentes en `<sesión>/subagents/**/*.jsonl` (a veces varios niveles de
     profundidad) — nunca intercalados en el `.jsonl` principal. Medido en esta máquina: 5 de 41 ficheros
     vistos, 43,6 % de los tokens facturables sin contar. **Descartado por la revisión:** que la causa
     fuera «el JSONL del subagente no se vuelca hasta acabar el turno» (hipótesis inicial del implementer)
     — falsa: un `agent-*.jsonl` real creció +2.431 bytes en 20 s con el turno en curso, es decir, se
     escribe en caliente igual que el principal; lo que fallaba era que nadie lo iba a mirar.
  Ambos fallos comparten la misma forma: son silenciosos porque el script degrada «como debe» (fallo 1,
  `fuente: estimado`) o ni siquiera degrada (fallo 2, `fuente: medido` con una cifra incompleta) — no hay
  ningún error visible que los delate.
- **Qué hacer en su lugar:** cuando una función resuelve una dependencia de entorno (aquí, "¿dónde viven —y
  cuáles son TODAS— las transcripciones de este proyecto?") y **todos** los tests existentes la esquivan
  inyectando un flag equivalente (`--transcript-dir` apuntando a una carpeta plana de fixture), esa función
  queda sin probar aunque la suite esté en verde, y ninguno de sus fallos internos (clave, alcance del
  glob) se detecta aunque el resultado final "parezca" correcto. La lección es una sola: **la función de
  localización/lectura de transcripciones no tenía ningún test sin inyección**, y por eso sus dos fallos
  pasaron desapercibidos pese a que el script "funcionaba" en ambos casos (degradando primero, mintiendo
  después). No basta con "los tests pasan"; hay que preguntarse qué camino del código NUNCA se ejecuta en
  ningún test, y si la fixture de ese test reproduce la FORMA real de los datos (aquí: subcarpetas, no solo
  ficheros sueltos).
- **Evidencia:** `agent-kits/shared/usage-meter.py:95` (`_encode_cwd`, `re.sub(r"[^A-Za-z0-9]", "-", cwd)`)
  y `agent-kits/shared/usage-meter.py:175-267` (`_snapshot_offsets`/`_sum_usage_window`, búsqueda
  recursiva con `rglob` tras el arreglo de T-03 de `usage-meter-transcripts`); los 28 tests
  preexistentes de `agent-kits/shared/test_usage_meter.py` con `--transcript-dir` (ninguno con subcarpetas);
  los once artefactos con `generacion.fuente: estimado` fechados 2026-09-09/2026-09-10 en `docs/roadmap/*/`;
  carpetas reales de `~/.claude/projects/` en esta máquina usadas como oráculo (p. ej.
  `C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents`); medición real
  de la carpeta de subagentes (`<sesión>/subagents/agent-*.jsonl`, +2.431 bytes en 20 s con el turno en
  curso); nuevos tests en `agent-kits/shared/test_usage_meter.py` (`test_project_transcript_dir_*`,
  `test_encoding_*`, `test_close_sin_transcript_dir_usa_localizacion_real`, `test_subagentes_*`).
