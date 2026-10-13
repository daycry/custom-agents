# Aceptación nativa Claude y Codex — 2026-10-13

Fuente: rama `feat/catalog-capabilities` tras la mezcla de `origin/master`
(`d553d0c`), instalada con el instalador real en proyectos sintéticos propios
bajo el temporal del usuario. Claude Code 2.1.296 con el bundle copiado en
`.claude/` (plugin instalado 1.22.0 desactivado solo en la sesión) o con
`--plugin-dir` del checkout. Codex 0.162.1 con `CODEX_HOME` aislado dentro del
proyecto: el `config.toml` global del usuario conserva su SHA antes y después.
Modelos reales configurados; salidas y llamadas de herramienta no forzadas.

| Caso | Claude | Codex |
|---|---|---|
| `/work-resume --initiative <exacta> --json` | JSON puro, semánticamente igual al compositor | JSON puro, igual al compositor (sandbox `read-only`) |
| `/work-resume --json` con dos iniciativas activas | `ambiguous` con dos candidatos, igual al compositor; ledgers intactos | `ambiguous`, igual; invoca el compositor, no lee `tasks.md` |
| Consumo de decisión aprobada vigente | `ok`, `consumida`, ack coherente | **falla**: `invalid_input` (ver causa) |
| Consumo tras editar el plan | `version_changed`, sin entrega ni ack | **falla**: `invalid_input` |
| Hooks: SessionStart, captura del turno, SessionEnd | índice inyectado; log del turno redactado, `<private>` excluido; envelope y journal | no ejecutado en esta pasada |

**Formato del consumo en Claude.** Las dos respuestas envuelven el JSON en una
valla y omiten campos (`decision`, `delivery`, `current_version`, `feedback`).
El estado y los IDs coinciden; el contrato «JSON original sin vallas» no se
cumple. Es la misma desviación registrada para OpenCode: queda pendiente.

**SessionEnd en Claude.** En 2 de 5 sesiones Claude canceló el hook
(`Hook cancelled`, GOT-011): no hubo envelope. `journal.py recover` las
materializó como `recuperado_sin_cierre` con decisiones/pendientes del log,
sin secreto y sin duplicar en una segunda pasada. El aviso «N candidata(s) sin
recuperar» contaba también logs ya capturados y se repetía en cada arranque:
corregido en `journal.py` (solo cuentan las saltadas por tope o presupuesto),
RED → GREEN en `test_recover_no_avisa_de_logs_ya_capturados_ni_en_la_segunda_pasada`.

## Causa del fallo de Codex

Python 3.13 en Windows aplica a `mkdir(mode=0o700)` una ACL explícita
(SYSTEM, Administradores, DERECHOS DE PROPIETARIO) que **reemplaza** la heredada.
El sandbox `unelevated` de Codex ejecuta con un token restringido cuyos SID
(grupo `CodexSandboxUsers` y SID de capacidad) solo aparecen en la ACL
heredada. Comprobado dentro de `codex exec -s workspace-write`: `mkdir()` y
`mkdir(0o777)` heredan esos SID; `mkdir(0o700)` los elimina. Resultado: el
sandbox no puede leer `owner.json` de un estado creado fuera, ni usar el
directorio que él mismo acaba de crear (la preparación quedó colgada sin
`owner.json`). `consume` lo reduce a `invalid_input`.

Piezas con `mkdir(mode=0o700)`: `plan-review.py` (estado de revisión),
`agent-activity-store.py`, `knowledge-curation.py` y `graphiti_publication.py` /
`graphiti_rebuild.py`. Las pruebas previas de consumo eran de OpenCode; Codex
no estaba acreditado. Corregirlo cambia la política de privacidad en Windows
de cinco piezas: decisión pendiente del usuario antes de implementar.

Límites: proyectos y decisiones sintéticos; aprobación por API del dueño, no
humana en navegador. Sin escrituras en configuración del usuario. Los
procesos propios terminaron; ninguno quedó vivo.

## Regresión tras el arreglo

`tests/test_hooks_shell.py` + `test_journal.py`: 248 passed, 10 skipped, 1 failed
(`test_replay_con_recover_max_limita_aunque_haya_cientos_de_huerfanas`, 2 de 3
recuperadas bajo el presupuesto de 2 s con la máquina cargada); aislado pasa 3 de 3.
Se conserva el fallo como sensibilidad temporal, no como verde. La copia del
checkout en `test_session_journal_ruta_del_plugin_con_espacios_y_unicode` ahora
usa solo los ficheros que git considera del proyecto: con un scratchpad local de
70.000 ficheros excluidos, la copia completa tardaba más de una hora.
