# Auditoría completa de custom-agents 3.2.2 (2026-11-09)

Rama auditada: `fix/plugin-root-and-doctor-scope` (master 3.2.2 más los dos arreglos de hoy).
Informe de partida de la iniciativa (ver `../spec.md`).

## Cómo se ha hecho

- **Cinco revisores de solo lectura en paralelo, uno por área:**
  - piezas del ciclo;
  - hooks y sesión;
  - scripts deterministas;
  - dashboards y consola;
  - distribución e integraciones.
- **Cada hallazgo** trae fichero:línea y evidencia. Los marcados *(inferido)* no se pudieron ejecutar.
- **Comprobación propia:**
  - consola levantada en 127.0.0.1:8769 y sondeada en vivo;
  - CI completa replicada en Linux (10.518 tests en verde);
  - relectura en el código de cada hallazgo crítico o de seguridad antes de incluirlo.
- **Las medidas** son de esta máquina (Windows, OneDrive, poca memoria): arrancar node cuesta unos 740 ms y Python unos 230 ms. Los tiempos absolutos salen pesimistas; lo trasladable a otras máquinas es el número de procesos y el trabajo repetido.

## Resumen

| Área | Crít. | Import. | Menor | Lo más relevante |
|---|---|---|---|---|
| Piezas del ciclo | 0 | 11 | 13 | La vía rápida no ejecuta qa-gate; en `lite` y en subagentes se pierden los guardarraíles; ~16 K tokens repetidos en el bucle de revisión |
| Hooks y sesión | 0 | 7 | 16 | El journal ya no se reinyecta; SessionStart tarda ~5 s; el índice oculta planner, qa, reviewer, tdd y `/setup` |
| Scripts deterministas | 1 | 9 | 11 | `worklog.py` puede borrar el banco de horas; qa-gate da verde con tests saltados |
| Dashboards y consola | 0 | 8 | 13 | Seguridad sólida; la cartera pierde las iniciativas más nuevas; los ledgers grandes no se pueden usar desde la consola |
| Distribución | 0 | 5 | 6 | En Windows el instalador puede ejecutar un `.cmd` plantado; Graphiti pasa por el proxy del sistema |
| **Total** | **1** | **40** | **59** | |

**Lo que está bien (verificado):**
- **Consola local:**
  - escucha solo en loopback y exige Host y Origin exactos;
  - pide cookie HttpOnly y Bearer, comparados en tiempo constante;
  - aplica una CSP estricta, `no-store` y `no-referrer`.
  - En vivo rechazó todo lo probado: 401 sin autenticación, 403 con Origin u Host ajenos o *cross-site*, 404 con *traversal*, 403 en POST sin Origin y 405 con PUT.
  - El JS no mete texto no confiable en `innerHTML`.
- **Parsers del ledger:** dan idéntico resultado con CRLF y BOM.
- **Firmas y borrado del instalador:** los manifiestos con HMAC y el borrado por hash son coherentes con lo documentado.
- **Interop:** respeta las tools y los permisos de los 10 agentes.
- **Versiones:** coinciden en los 5 manifiestos.

## Prioridad 1: pérdida de datos y seguridad

| # | Severidad | Dónde | Problema | Arreglo |
|---|---|---|---|---|
| 1 | **Crítico** | `skills/jira-sync/scripts/worklog.py:63-70,166` | Con un `jira-state.json` con BOM o corrupto, `load_json` devuelve `{}` sin avisar y `--apply` sobrescribe el fichero: se pierden el banco de horas y el worklog (reproducido). | Leer con `utf-8-sig`; distinguir ausente de ilegible (exit 2 sin escribir); escritura atómica. |
| 2 | Importante | `worklog.py:31-32,107,223` | Acepta fechas futuras (`2099-12-31`) y horas negativas, aunque el docstring dice que no. | Validar con exit 2. |
| 3 | Importante | `agent-kits/qa/qa-gate.py:40-47` | Un test con `expectedStatus: "skipped"` se cuenta como pasado: veredicto VERDE con 0 tests ejecutados (verificado en el código). | Clasificar `skipped` antes que `expected`. |
| 4 | Importante | `install/providers.mjs:143` | En Windows se usa `where.exe`, que busca primero en el directorio actual. Un `claude.cmd` o `codex.cmd` plantado en un repo no confiable se ejecuta al instalar o desinstalar (reproducido). | Recorrer el PATH a mano, como `hooks/run-hook.mjs:174`. |
| 5 | Importante | `skills/knowledge-services/backends/graphiti.py:411,750` | `build_opener` sin `ProxyHandler({})`: con `HTTP(S)_PROXY` o el proxy del registro, el tráfico «solo local» sale por un proxy externo. `markdown_export.py:412` sí lo anula. | Dos líneas y un test. |
| 6 | Importante | `commands/dev-cycle.md:84` · `agent-kits/shared/native-guardrail.py:20` | Con `perfil: lite` se implementa en el hilo principal y la guardia solo protege `implementer` y `architect`: se pierden los deny de rama principal, `docs/roadmap/` y git destructivo. | Despachar siempre `implementer` en secuencia, o extender la guardia al hilo en `lite`. |
| 7 | Importante | `agent-kits/dev-cycle/references/phase3-subagents.md:1,20` | En modo subagentes se despacha sin `subagent_type` implementer: mismo hueco *(inferido)*. | Despachar `custom-agents:implementer` con el brief. |
| 8 | Importante | `skills/adversarial-review/scripts/review-lens-select.py:716` | En `auto`, cualquier error (p. ej. un `--base` mal escrito) apaga las lentes de seguridad y rendimiento con exit 0. | Ante error, activarlas (fallar cerrado). |
| 9 | Importante | `install/install.mjs:1996,172` | El paso `merge` con un JSON ilegible parte de `{}` y reescribe el fichero: se pierden los demás plugins del marketplace de Codex. | Usar `leerJsonEstricto`, como en `json-set`. |
| 10 | Importante | `install/install.mjs:2464` | `uninstall` aborta todos los proveedores si un manifiesto no verifica. | Aislar por proveedor, como `install`. |
| 11 | Importante | `install/manifest-auth.mjs:33` | Rechaza cualquier ancestro symlink o junction: el instalador queda inutilizable con HOME o dotfiles enlazados, y el error es engañoso. | Resolver los ancestros existentes; exigir que no haya enlace solo en lo que crea el instalador. |
| 12 | Menor | `agent-kits/shared/guardrail-check.py:36` | Deja pasar `git reset --hard`, `clean -fdx`, borrar ramas remotas y `stash drop`, pese al «git no destructivo» de CLAUDE.md. | Añadirlos a la lista de denegación. |
| 13 | Menor | `providers.mjs:410,249` | Escribe rutas absolutas (usuario y empresa) en `.codex/config.toml` o `.claude/settings.json` del proyecto, que suelen versionarse. | Avisar, o usar `settings.local.json`. |

## Prioridad 2: funciones documentadas que no funcionan

| # | Dónde | Problema | Arreglo |
|---|---|---|---|
| 14 | `progress-report.py:472-498` · `hooks/session-context.py:206` | **El journal no se reinyecta al arrancar**: con más de 1 MiB de ledgers o más de una iniciativa activa sale solo «Journal: incomplete». Pasa en este repo (3,9 MiB). | Elegir la entrada del journal sin pasar por la selección global de ledgers. |
| 15 | `commands/dev-cycle.md:103,164` · `agents/qa.md:114` · `agents/implementer.md:62` | **La vía rápida promete qa-gate, pero nunca se ejecuta**: sin `improvement-plan.md` ni `test-plan.md`, qa avisa y termina. El implementer exige el plan. | Aceptar el ledger ligero y el marcador «sin UI» en `tasks.md`. |
| 16 | `skills/tdd/SKILL.md:52` · `lens-prompts.md:17` | «Lo verifica la Lente A», pero el prompt literal de la Lente A no menciona `RED:`. | Añadir el criterio a la Lente A y un aviso en ledger-lint. |
| 17 | `skills/plugin-panel/scripts/panel_data.py:34,335` | **La cartera corta en 64 filas en orden ascendente, así que se pierden las iniciativas más nuevas** (3 aquí) en Inicio, Iniciativas, Plan y la consola. Confirmado en vivo: `row_budget`. | Ordenar de la más nueva a la más antigua o priorizar las activas; paginar. |
| 18 | `serve_panel.py:20,453` | El presupuesto de 1 MiB del progreso se agota y 32 de 67 ledgers salen como `too_large` (diagnóstico falso). | Leer solo la cabecera y el resumen. |
| 19 | `console_service.py:68,103` | Desde la consola no se pueden «Continuar» ni «Revisar» planes con ledger > 256 KiB (5 del repo, los más activos), y el error que se muestra es genérico. | Huella en streaming; mapear el error. |
| 20 | `serve_panel.py:1361` | Un plan creado después de arrancar el panel enlaza a una página 404. | Plantilla común por id validado. |
| 21 | `agent-kits/shared/skill-index.py:215-270` | **El índice de sesión recorta por orden alfabético** y oculta planner, qa, reviewer, nemesis, tdd, unit-tests, `/setup` y `/work-resume`, mientras muestra llm-pipeline. | Ordenar por prioridad de ciclo. Mismo coste en tokens. |
| 22 | `agent-kits/shared/scope-check.py:328` | Cuenta `Archivos` dentro de bloques de código y de secciones posteriores: la puerta de alcance queda abierta de más (`**/*`). Hoy no afecta a ningún ledger. | Trocear sobre `sin_vallas`, como `parse_ledger`. |
| 23 | `agent-kits/qa/coverage-check.py:475` | Un ejemplo dentro de un bloque de código crea una tarea fantasma y da falso rojo. | Mismo parser único. |
| 24 | `commands/dev-cycle.md:162` · `ledger-write.py:217` | Tras el 3.er intento se ofrece «seguir», pero el writer no admite un intento 4. | Definir qué significa «seguir». |
| 25 | `agents/implementer.md:106` frente a `dev-cycle.md:197` | Dos dueños del commit, con métodos distintos. | Un solo dueño. |
| 26 | `skills/jira-sync/scripts/jira-flow.py:168` | `_campo` cruza saltos de línea: a Jira solo llega el primer ítem de la Verificación. | Usar el parser de ledger-lint. |
| 27 | `hooks/hooks.json:93` | En Claude no se reinyecta nada tras `/clear` (Codex sí). | Añadir `clear`. |

## Prioridad 3: rendimiento de procesos

| # | Dónde | Medido | Arreglo | Ganancia estimada |
|---|---|---|---|---|
| 28 | SessionStart (`session-context.py`, `progress-report.py`) | 4,2-6,2 s. Lee 136 veces `tasks.md` (7,9 MB) y 2 veces `usage-state.json` (3,7 MB) | Una sola instantánea del roadmap por arranque | −1 a 2 s (30-40 %) |
| 29 | `hooks/run-hook.mjs:358` | Un Python extra por hook en Windows solo para cerrar el job | Que el supervisor informe de que el job ya está vacío | −180 ms por hook |
| 30 | `hooks/subagent-progress.sh` | ~9 procesos, 2,6 s por SubagentStop, sin debounce | Portarlo a Python, como `ledger-post.py` | 2,6 s → <1 s |
| 31 | UserPromptSubmit | 1,2 s síncrono antes de cada prompt (importa `journal.py`, 2.978 líneas) | Módulo ligero, o `async` | −1 s por prompt |
| 32 | `serve_panel.py:644` | Servidor de un solo hilo; el progreso (658 ms) se recalcula en cada sondeo de 5 s y bloquea el resto | `ThreadingHTTPServer` acotado y caché por firma | Sin bloqueos |
| 33 | `console_service.py:149` | `native-sessions` sondea cada 2 s y relanza hasta 3 CLIs de runtime cada 15 s | Solo en la vista Sesiones o a demanda; backoff | CPU y memoria |
| 34 | `console_service.py:195` | `runtimes` sin caché: 600 ms por llamada en vivo, cada 2 s | Caché de 30-60 s | −600 ms por sondeo |
| 35 | `scope-check.py:397` | `isdir` por cada par fichero×patrón: 1,9 s de 3,2 s | Precalcular por patrón | −1,9 s por pasada |
| 36 | `ledger-archive.py` · `ledger-lint.py:236` | 5,6 s con 507 KB (bucles carácter a carácter) | Índices por regex | 5,6 s → <1 s |
| 37 | `skills/code-health/scripts/code-health.py:246` | 10 s en `sin_comentario` | Atajo para líneas sin comentario | 10 s → ~2 s |
| 38 | `agent-kits/shared/task-brief.py:1022` | 3 subprocesos por brief (1,3 s de 1,7 s) | Lint en proceso | −0,4 s por subagente |
| 39 | `statusline/roadmap-statusline.sh:39` | La clave de caché incluye el coste, así que casi siempre falla | Clave solo con los metadatos del roadmap | −0,5 s por refresco |
| 40 | `usage-meter.py:567` | `usage-state.json` crece sin límite (3,7 MB) | Eliminar `offsets` al cerrar | Menos carga en cada arranque |

## Prioridad 4: consumo de tokens

| # | Dónde | Coste | Arreglo | Ahorro |
|---|---|---|---|---|
| 41 | Los 10 agentes, «Contexto de capacidades» | Cada despacho lee `capability-check.md` (5,4 K car.) y ejecuta 2 scripts, aunque el ledger ya trae las capacidades | «Si el ledger o el brief traen `Capacidades`, no recalcules» | ~16 K tokens en un bucle de revisión de 12 despachos |
| 42 | Integraciones por evento | Cada evento lee `project-integrations.md` (5,2 K car.) y ejecuta un script, aunque no haya integraciones | El orquestador comprueba una vez y lo pasa a los roles | Varios K tokens por ciclo |
| 43 | `agent-kits/dev-cycle/references/phase2-planning.md:25-290` | ~15 K car. de revisión visual opcional del plan en todo flujo completo | Separarlo en una referencia bajo demanda | ~3,7 K tokens por ciclo completo |
| 44 | `commands/doctor.md:68-129` | ~11 K car. de notas internas en cada `/doctor` | Moverlas a `docs/` | ~2,7 K tokens por `/doctor` |
| 45 | Resolución del kit (11 copias por pieza) | Subagentes sin `CLAUDE_PLUGIN_ROOT` en Bash: `find` de 7,7 s por bloque | Inyectar la ruta absoluta en SessionStart y en el brief | 1 llamada y ~8 s por bloque |
| 46 | `hooks/opencode-plugin.js:226-344` | Recalcula y reinyecta hasta 10 K car. casi en cada petición *(inferido)* | Invalidar por firma, no por evento | El mayor ahorro del área en OpenCode |
| 47 | `scripts/export-interop.py:82,94` | 9 de 10 agentes de OpenCode reciben una instrucción para delegar que su permiso deniega | Solo si `Agent ∈ tools` | Menos tokens y sin contradicción |
| 48 | Bloque de sesión | Líneas opacas («Journal: incomplete»), iniciativas al 100 % listadas como en curso, ruta absoluta en el pie | Compactar | ~600 car. por arranque (−15 %) |
| 49 | `adversarial-review` · `implementer` | La explicación de los avisos de scope-check está duplicada (~2,3 K car. cada una) | Que el script imprima su propio remedio | ~1 K tokens |

Mayores cargas por defecto (caracteres del fichero más los fragmentos que ordena leer):

| Pieza | Car. | ≈ tokens |
|---|---|---|
| `/dev-cycle`, flujo completo | 58.741 | 14.685 |
| `implementer` | 48.727 | 12.181 |
| quick-implement + núcleo | 47.148 | 11.787 |
| `/dev-cycle`, vía rápida | 40.232 | 10.058 |
| `adversarial-review` + prompts | 38.106 | 9.526 |
| `qa` | 35.767 | 8.941 |

`reviewer` carga 19,8 K car. por lente: con 4 lentes y 3 intentos, hasta ~59 K tokens de prompt fijo.

## Menores y de higiene (seleccionados)

- **Documentación desalineada:**
  - la Lente D falta en `dev-cycle`, `quick-implement` y CLAUDE.md;
  - CLAUDE.md dice que los hooks globales no deniegan, pero ADR-023 añade una guardia global;
  - la doc confunde consola y panel servido (`/plugin-catalog --serve`).
- **Rutas citadas que no viajan con el plugin:** LES-010, LES-012, ADR-011, ADR-012 y ADR-017.
- **Shells muertos en `hooks/`:** `session-context.sh` (315 líneas), `progress-line.sh` y `ledger-lint-warn.sh`.
- **Degradaciones no documentadas:**
  - sin node, cada hook da «command not found»;
  - `skill-index.py` ignora `sesion.indice: false` si `dev.json` tiene BOM.
- **Consola:**
  - las preguntas o permisos nativos pendientes solo se ven dentro de Sesiones;
  - faltan 7 códigos de error en el mapa de la UI;
  - el chat no es región `aria-live`;
  - la cookie es por host, no por puerto.
- **Instalador:**
  - desde un clon copia 93 tests (2,8 MB) que el paquete npm excluye;
  - nunca poda las cachés antiguas (~5,6 MB por versión).
- **`release.py`:** su docstring habla de 3 manifiestos y son 5; una copia `.MANUAL-COPY` pendiente no bloquea.
- **Tests que faltan** (sin caso para lo documentado):
  - worklog con BOM;
  - qa-gate con `skipped`;
  - bloques de código en `tasks.md` para scope-check, coverage-check y ledger-lint;
  - paridad del parser de jira-flow;
  - topes de tiempo para ledgers de 500 KB.

## Plan propuesto

| Fase | Contenido | Hallazgos |
|---|---|---|
| F1 · Seguridad y datos | worklog, qa-gate, `where.exe`, proxy de Graphiti, guardarraíl en `lite` y subagentes, lentes que fallan en abierto, `merge` y `uninstall` del instalador | 1-12 |
| F2 · Funciones rotas | journal al arrancar, vía rápida con qa-gate y TDD, cartera y planes grandes en los dashboards, índice por prioridad, parser único del ledger | 14-27 |
| F3 · Rendimiento | SessionStart en una pasada, menos procesos por hook, consola con caché y sin relanzar CLIs, scripts de puertas | 28-40 |
| F4 · Tokens | capacidades e integraciones una vez por ciclo, referencias opcionales fuera de la carga por defecto, OpenCode por firma, bloque de sesión compacto | 41-49 |

F1 y F2 son cambios acotados y con tests reproducibles. F3 y F4 conviene medirlas antes y después con `usage-meter` y `bench`.
