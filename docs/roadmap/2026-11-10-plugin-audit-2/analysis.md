# Auditoría del plugin — 2026-11-10 (segunda pasada)

Auditoría de solo lectura sobre `fix/plugin-audit-remediation` @ `129dbeb`. Cinco auditores en paralelo (roadmap, agentes y comandos, skills, código, ejecución e integración) y verificación del orquestador sobre los hallazgos de más impacto. No repite la auditoría del 2026-11-09 (`../2026-11-09-plugin-audit-remediation/testing/auditoria-2026-11-09.md`), ya remediada.

Convenciones: **[V]** verificado por el orquestador sobre el código; **[M]** medido por un auditor; **[E]** estimado. Tokens ≈ caracteres / 4, sin tokenizer. No hay consumo facturado medido.

## Veredicto

El plugin funciona y sus puertas son sólidas. Lo que le separa de «perfecto» no son bugs sino tres excesos:

1. **Alcance.** 10 de las 34 skills no pertenecen al ciclo spec → qa y concentran el 65 % del código de `skills/`.
2. **Texto que se paga muchas veces.** La misma regla vive en el agente, en el fragmento al que remite y a veces en el brief; la receta del kit está 33 veces; el ledger crece sin tope de tokens.
3. **Capas que ya no ejecuta nadie.** Shells de hooks que solo corren en tests, copias literales «de respaldo» entre módulos que se importan entre sí, un segundo servidor de panel, ramas legacy del instalador.

## Presupuesto de tokens medido [M]

| Concepto | Caracteres | ≈ tokens |
|---|---|---|
| Descriptions de 34 skills + 16 comandos + 10 agentes (cada sesión) | 20.848 | 5.200 |
| Bloque de `SessionStart` (este repo) | 4.583 | 1.150 |
| Ciclo completo con `subagentes` + `tdd`, solo carga fija | 951.612 | 238.000 |
| Ciclo completo clásico | 571.034 | 143.000 |
| Vía rápida | 236.175 | 59.000 |
| `tasks.md` de `plugin-audit-remediation`, una lectura | 175.744 | 44.000 |

Los cinco mayores contribuyentes del ciclo con subagentes: cuerpo de `implementer` × 12 (314 K), skill `tdd` × 12 (121 K), `knowledge-check*.md` × 11 (114 K), brief × 12 (108 K), `adversarial-review/SKILL.md` × 3-9 (54-163 K). El plugin no declara servidores MCP: su coste de contexto por MCP es 0.

## Plan priorizado

### Nivel 1 — Defectos (antes de mergear el PR #32 o justo después)

| # | Hallazgo | Evidencia | Acción | Esf. |
|---|---|---|---|---|
| 1.1 | **[V]** `SessionStart` avisa en falso `CALIBRATION.md: tasks.md ilegible (redirected_path)` y lo mismo con `README.md` | `agent-kits/shared/progress-report.py:479-481,495-497` | Saltar lo que no sea directorio | S |
| 1.2 | **[V]** `implementer` no tiene `Skill` en `tools:` y el cuerpo le ordena invocar `tdd`, `dependency-upgrade`, `debug-root-cause` | `agents/implementer.md:7,9,91,94` | Añadir `Skill` o dar la ruta del `SKILL.md` como alternativa; revisar `qa` (`to-pdf`). Falta comprobarlo en una sesión real | S |
| 1.3 | **[V]** Comando y skill `confluence-pull` comparten nombre; la skill es `user-invocable` | `commands/confluence-pull.md`, `skills/confluence-pull/SKILL.md:8` | Borrar el comando y añadir la comprobación al linter | S |
| 1.4 | `pm-cycle` dice que `architect` escribe el ADR; el agente lo tiene prohibido | `commands/pm-cycle.md:96` | Copiar la redacción de `phase2-planning.md` | S |
| 1.5 | Comandos «solo lectura» que escriben; `/tmp/` en Windows | `commands/roadmap-metrics.md:2`, `roadmap-brief.md:2,16-17` | Corregir descriptions y usar un temporal portable | S |
| 1.6 | No queda claro quién implementa en perfil normal | `commands/dev-cycle.md:155` frente a `:83-84,151` | Escribir «despacha `implementer`» | S |
| 1.7 | `nemesis` declara `Agent` pero despachado desde `/dev-cycle` no puede anidar | `agents/nemesis.md:13,141` | Alternativa explícita en serie | S |
| 1.8 | Guardarraíl: `git checkout -- .`, `git restore .`, `checkout -f` no denegados (deuda de F1) | `tasks.md:675` de la iniciativa anterior | Pocas reglas más un test | S |
| 1.9 | `code-health.py` no termina sobre el repo completo (timeout 300 s) | ejecución del auditor | Investigar exclusiones y coste cuadrático | S-M |
| 1.10 | Disparador «dashboard» pelado en `plugin-panel` | description de la skill | Dejar solo disparadores con sujeto | S |

### Nivel 2 — Tokens: más ahorro por menos esfuerzo

| # | Hallazgo | Ahorro | Acción | Esf. |
|---|---|---|---|---|
| 2.1 | El ledger no tiene freno de tokens: avisa a 183 KB, cuando ya son 45 K tokens por lectura | [E] ≈ 30 K tokens por lectura en ledgers grandes | Umbral a 40-60 KB, archivar al cerrar fase (`ledger-archive.py` ya existe), pasar a la Lente A solo la fase revisada | M |
| 2.2 | El subagente con brief carga el cuerpo entero de `implementer` (26 K), con secciones que tiene prohibido usar | [E] 24-30 K tokens por ciclo | Núcleo corto; flujo clásico a `agent-kits/implementer/references/` | M |
| 2.3 | Doble pago: el agente resume la regla y además manda leer el fragmento (`knowledge-check*`, `constitution-check`, `rationalization-table`) | [E] hasta 28 K tokens por ciclo | Fragmento solo si hay aciertos; quitar el puntero a la tabla de racionalización (es guía de autoría) | S-M |
| 2.4 | Con `tdd`, cada subagente carga la skill entera (10 K) aunque el brief ya trae la sección TDD | [E] 25 K tokens por ciclo | Ley dura y formato `RED:` en el brief; skill bajo demanda | S |
| 2.5 | El revisor abre `adversarial-review/SKILL.md` (18 K) para una tabla de 4 K | [E] hasta 21 K tokens por ciclo | Tabla a `references/` o al prompt de la lente | S |
| 2.6 | **[V]** Receta del kit: 19 veces en 9 agentes y 14 en 9 comandos | [M] −7,5 KB | Una por pieza, que derive todas las variables | S |
| 2.7 | Índice de `SessionStart` duplica en Claude Code el listado nativo, truncado y con 18 de 34 skills | [M] 844 tokens por arranque y compactación | Solo cabecera en runtime `claude`; mantener en Codex y OpenCode. Contrastar con evals de activación | S |
| 2.8 | Reglas de este repo dentro de agentes genéricos (`export-interop`, `CONTRACTS.md`) | [M] ≈ 4,2 KB | A la constitución del repo o a `plugin-dev` | M |
| 2.9 | Párrafos «Alcance y activación»: la description antigua pegada al cuerpo, en 5 agentes/comandos y 16 skills | [M] −15 KB | Borrar (comprobar `--diet-check` y `test_source_snapshot`) | S |
| 2.10 | `setup.md` carga 24 K; el 36 % es Kwipu/Graphiti/training | [M] ≈ 9 KB por `/setup` | Paso 5-sexies a referencia bajo demanda | S-M |
| 2.11 | `dev-cycle.md` carga el cierre y la tabla de transiciones desde el primer turno | [E] ≈ 10 KB | `phase6-close.md` bajo demanda | S |
| 2.12 | `capability-check.md`: 5,6 K para una salida de 200-300 caracteres | [E] ≈ 3,5 KB por ciclo | Núcleo de ≈ 1,8 K; extensiones solo si el proyecto tiene piezas propias | S |
| 2.13 | `qa.md:114` (2 K) solo aplica a QA sin UI; `implementer.md` repite reglas 2-5 veces | [E] 6-7 KB | Referencia condicional; deduplicar | S-M |
| 2.14 | Cabecera «ORQUESTA agentes» en los 16 comandos exportados, aunque 12 no despachan | [M] ≈ 600 caracteres por invocación en Codex/OpenCode | Emitirla solo si el cuerpo nombra un rol | S |

### Nivel 3 — Alcance (decisión de producto)

| # | Propuesta | Efecto |
|---|---|---|
| 3.1 | Partir el marketplace con `modules.json` (ya existe): `custom-agents` núcleo + satélites | Habilita 3.2-3.4 sin borrar nada |
| 3.2 | Sacar del núcleo `training-data-services` (6.400 líneas + 11.810 de test; nadie la invoca) y `knowledge-services` (8.021 + 9.706; Kwipu y Graphiti) | −861 caracteres por sesión, −2,1 MB de paquete |
| 3.3 | Sacar `voice-profile`, `content-production`, `relationship-planning`, `competitive-analysis` (nadie las invoca) y `plugin-dev` (solo sirve en este repo) | −1.289 caracteres por sesión |
| 3.4 | Fusionar `llm-pipeline` y `data-collection` como referencias de `backend-practices`; `confluence-pull` como modo de `confluence-publish` | 34 → 24 skills |
| 3.5 | Un solo modo de implementación «brief por tarea» (hoy: clásico, `lite`, `subagentes` con lote paralelo y worktrees por tarea) | −4 KB de prosa y una dimensión de configuración; se pierde el lote paralelo |
| 3.6 | Retro fuera de la vía rápida (hoy exige `retro.md`, fila y entrevista para un cambio de dos líneas) | Menos fricción |
| 3.7 | `/roadmap-metrics` dentro de `/roadmap-status --metrics` | 16 → 15 comandos |
| 3.8 | Cancelar o ejecutar `dev-cycle-dataset` (aprobada, Go, 0 % de código, 26 h estimadas) | Sin consumidor real, cancelar |

### Nivel 4 — Código: simplificar sin cambiar conducta

| # | Hallazgo | Evidencia | Acción | Ahorro / esf. |
|---|---|---|---|---|
| 4.1 | CI 875 s: pytest en serie (749 s) y 27 ficheros que corren dos veces | `ci.yml.MANUAL-COPY:44-50` [V] | `pytest -n auto`, quitar el bucle, publicar `--durations` | [E] 14 → 5-6 min; S |
| 4.2 | **[V]** Los `.sh` de hooks son alias: producción ejecuta el `.py`. `test_hooks_shell.py` (74 tests) prueba los shells, no lo que corre | `hooks/run-hook.mjs:326-343` | Reapuntar los tests al lanzador, arreglar lo que aflore, borrar 7 `.sh` y los dos no registrados (`ledger-lint-warn.sh`, `progress-line.sh`) | −860 l; M |
| 4.3 | **[V]** Copias literales entre módulos que se importan entre sí | `journal.py:262-553` (copia de `redact.py`, 291 l), `task-brief.py:662-922` (copia de `ledger-lint.py`, 260 l) | Borrar las copias intra-`shared`; conservar las que cruzan a `skills/` | −650 l; S-M |
| 4.4 | 17 lectores de `dev.json`, 47 cargadores de módulo por ruta, 11 parsers de frontmatter, 6 escrituras atómicas, 7 cerrojos | ver informe de código | Un módulo común (`kit.py`) migrando primero hooks y `shared` | [E] −900 l; M-L |
| 4.5 | `journal.py` (2.873 l, 6 responsabilidades, reexporta 44 privados para tests) y `doctor.py` (3.192 l, 9 diagnósticos) | `journal.py:582-631` | Partir; los tests importan el módulo real | M-L |
| 4.6 | El índice FTS5 de `knowledge-find.py` no ahorra lectura ni parseo | `knowledge-find.py:967-998` | Borrarlo tras comprobar que el orden de resultados no cambia | [E] −280 l; M |
| 4.7 | Dos servidores HTTP de panel; `serve_panel.py` (1.575 l) solo aporta la revisión de plan | `console_service.py:19` | Reducirlo a servidor de revisión de plan | [E] −600-800 l; M |
| 4.8 | Hooks: `UserPromptSubmit` síncrono sin emitir nada [V]; 3 `node` por edición; `SessionStart` compila 6.700 líneas antes de mirar si hay proyecto | `hooks/hooks.json` | `async`, un solo handler post-edición, carga perezosa | 1,2-2,1 s por prompt [M]; S-M |
| 4.9 | Statusline: escáner JSON en Bash con paridad de redondeo (≈ 110 de 226 l) | `statusline/roadmap-statusline.sh:33-152` | Cachear solo el segmento del roadmap, o reescribir en node | −100 l; S |
| 4.10 | Instalador: ramas legacy inalcanzables y 5 comprobaciones de «dentro de la raíz» | `install/install.mjs:466-497,1624-1646` | Retirar y unificar | −195 l; S |
| 4.11 | Entre 840 [V] y 1.275 [M] tests se llaman como la historia de la remediación (`test_f4fix2_5_*`); 125 ficheros de test fijan prosa | `tests/test_f4fix*` | Renombrar por conducta; invariantes de prosa al linter | M |
| 4.12 | Capa bash del lanzador solo para guardrails por frontmatter | `runtime-entry.sh`, `runtime-bin/` | Enrutar a Python contenido (comprobar el modo bundle copiado) | −75 l; S |

Revisado y justificado, **no tocar**: `runtime-supervisor.py` con Job Objects, el prefiltro del guardarraíl en node, `redact.py` y `local-read.py` como fuentes únicas, `outbox.py` para `knowledge-sync`, las cuatro `*-practices`, `tdd` frente a `unit-tests`, `roadmap-dashboard` frente a `plugin-panel` (un solo generador HTML).

### Nivel 5 — Higiene del roadmap

- Cerrar `plugin-audit-remediation`: `/retro`, estados, PR #32, merge y release (permiso del usuario).
- Cerrar `kwipu-metadata`, `session-visibility`, `knowledge-verification` (PR ya mergeados, falta retro y `estado:`).
- Otras 7 iniciativas `completado` sin retro desde el 2026-10-31: una retro agrupada o una exención escrita.
- Estados rancios: planes de `project-specialization`, `catalog-capabilities`, `control-center`; specs de `brief-budget`, `audit-remediation`; `opencode-reader-fixes`.
- Ramas con trabajo a medias: `model-routing-lab` (activa), `graphiti-uuid-fix`, `sdd-proporcional`, `project-dashboard`. 36 worktrees registrados.
- 6 candidatos de memoria sin curar en `docs/knowledge/candidates/pending/`.
- Checklist manual M-01 del instalador (19 casillas): ejecutarla o anotarla como no verificable.

## Decisiones del usuario

1. ¿Se parte el plugin en núcleo + satélites (nivel 3.1-3.4)?
2. ¿Un solo modo de implementación (3.5) y retro fuera de la vía rápida (3.6)?
3. `dev-cycle-dataset`: ¿cancelar?
4. Excepción «evidenciado (medida)» en la constitución (pendiente de la iniciativa anterior).
5. Destino de las ramas a medias.

## Lo que no se verificó

- **Consumo real.** Todo son tamaños de fichero; los ahorros estimados suponen que los agentes leen los fragmentos que se les manda aplicar. No se observaron transcripciones.
- **Comportamiento en ejecución** de 1.2, 1.3 y 1.7: se apoyan en el contrato de `tools:` y en el listado de la sesión, que es el plugin instalado (3.2.3), no la rama.
- **Suites.** No se ejecutó ninguna completa (memoria). Los tiempos son de la CI en Linux.
- **Codex y OpenCode.** Solo se midieron los ficheros generados.
- **Los 59 menores de la auditoría anterior** que no están escritos en el repo.
- **Si algún test fija** los literales que se proponen mover (2.8, 2.9).
