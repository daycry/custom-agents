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
estado: en-progreso       # borrador | en-progreso | completado | cancelado
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
| **Estado** | en-progreso |
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
| Fase única — el meter encuentra las transcripciones | 0 | 2 | 0% | — / 1,0h | — / 0,10h | — / 0,03h | — / 60k |
| **TOTAL** | **0** | **2** | **0%** | **— / 1,0h** | **— / 0,10h** | **— / 0,03h** | **— / 60k** |

---

## Fase única — el meter encuentra las transcripciones

**Estado**: en-progreso · **Estimado**: 1,0h · **Real**: — · **Coste est.**: ≈50 € · **Tokens est.**: 60k

### T-01 — `_project_transcript_dir()` codifica el `cwd` como Claude Code y se prueba SIN `--transcript-dir`

- **Descripción**: Sustituir la clase `[/\\.:]` por `[^A-Za-z0-9]` en `agent-kits/shared/usage-meter.py:87` (una línea) y añadir a `agent-kits/shared/test_usage_meter.py` los tests que HOY faltan: la función de localización se prueba con `HOME` y `cwd` redirigidos a `tmp_path` (monkeypatch), SIN `--transcript-dir`, con casos Windows (espacios, `.`, `:`, `\`) y POSIX. El oráculo de la codificación son nombres de carpeta REALES de esta máquina (los cuatro de `~/.claude/projects/`), no una regla inventada. Ninguna otra rama del script cambia.
- **Estado**: en-progreso
- **Tiempo humano**: est. 0,7h · real —
- **Tiempo IA (ejec.)**: est. 0,07h · real —
- **Supervisión**: est. 0,02h · real —
- **Tipo**: test
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`
**Criterios de aceptación**
- [ ] Para `C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents` la clave es exactamente `C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents`; ídem `C:\Users\46066917X\.claude-mem-observer\sessions` → `C--Users-46066917X--claude-mem-observer-sessions` (carpetas reales, oráculo)
- [ ] Una ruta POSIX sin caracteres especiales (`/home/u/proj`) sigue dando `-home-u-proj`: sin regresión en Linux/CI
- [ ] Existe al menos un test que ejercita `_project_transcript_dir()` (o el camino `close` sin `--transcript-dir`) con `HOME`/`cwd` en `tmp_path`; en los tests nuevos no aparece `--transcript-dir`
- [ ] Con el arreglo, en esta máquina `usage-meter.py close` sobre un marcador real deja de avisar «carpeta de transcripciones no disponible» y devuelve `fuente: medido` (evidencia pegada en la Verificación)
- [ ] Si `~/.claude/projects/` de esta máquina contiene alguna carpeta con `_`, el test lo cubre; si no, el supuesto «`_` también pasa a `-`» queda escrito en el docstring de la función
- **Verificación**: `python -m pytest -q agent-kits/shared/test_usage_meter.py` → todo verde (≥ 30 tests, ≥ 2 nuevos) · `python agent-kits/shared/usage-meter.py start --artefacto usage-meter-transcripts/T-01` + `close` → JSON con `"fuente": "medido"`
- **Changelog**: `usage-meter` vuelve a encontrar las transcripciones en Windows y en rutas con espacios o puntos: la clave de la carpeta se codifica como lo hace Claude Code (todo carácter no alfanumérico → `-`), así que el coste de generación de specs, planes y tareas pasa de estimado a medido.

### T-02 — `GOT-010`: la función que localiza las transcripciones tenía cobertura cero

- **Descripción**: Gotcha en `docs/knowledge/gotchas/GOT-010-usage-meter-nunca-encontro-las-transcripciones.md` (frontmatter `id`/`tipo`/`area`/`estado: propuesta`/`fuente`; síntoma · causa raíz · qué hacer en su lugar · evidencia), con su fila en `docs/knowledge/README.md` dentro de la tabla y con columna Área. Lección de fondo: cuando TODOS los tests de un script inyectan la dependencia de entorno (`--transcript-dir`), el código que resuelve esa dependencia queda sin probar, y su fallo es silencioso porque el script degrada «como debe». Cumple el umbral de `knowledge-write.md`: rompió una garantía (coste medido) en silencio durante dos sesiones.
- **Estado**: en-progreso
- **Tiempo humano**: est. 0,3h · real —
- **Tiempo IA (ejec.)**: est. 0,03h · real —
- **Supervisión**: est. 0,01h · real —
- **Tipo**: docs
- **Archivos**: `docs/knowledge/gotchas/GOT-010-usage-meter-nunca-encontro-las-transcripciones.md`, `docs/knowledge/README.md`
**Criterios de aceptación**
- [ ] El fichero existe con los cuatro apartados y cita `usage-meter.py:87`, la regla `[^A-Za-z0-9]`, los 28 tests con `--transcript-dir` y los once artefactos estimados
- [ ] Fila en el índice dentro de la tabla, con Área; `lint_plugin.py` 0 errores y `tests/test_knowledge_index.py` en verde
- [ ] `knowledge-find.py "transcripciones usage-meter"` devuelve GOT-010 en el primer acierto
- **Verificación**: `python scripts/lint_plugin.py` → `0 errores` · `python -m pytest -q tests/test_knowledge_index.py` → verde · `python agent-kits/shared/knowledge-find.py "transcripciones usage-meter" --limit 1` → primera línea empieza por `GOT-010`
- **Changelog**: Documentado en `GOT-010` por qué el coste medido del plugin era una estimación en Windows sin que ningún test lo viera.
