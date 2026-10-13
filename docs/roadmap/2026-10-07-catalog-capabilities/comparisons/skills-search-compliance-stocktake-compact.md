# Buscar antes de construir, cumplimiento, inventario de skills y compactación — S250, S255–S257, S264

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **31.623 bytes/734 líneas**. Recursos: los tres scripts
de S257, completos (13.729 bytes/385 líneas); de S255 (78.845 bytes/2.127 líneas)
se leyeron completos los prompts, fixtures, `pyproject.toml` y los nueve módulos
de `scripts/` (45.292 bytes/1.279 líneas) y **no** los tres ficheros de `tests/`
(33.553 bytes/848 líneas; solo se contaron sus 43 funciones `test_`), por eso
S255 consta con recursos `listed-not-read`.
[search-compliance-stocktake-compact-reading-evidence.json](search-compliance-stocktake-compact-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S250 — Buscar antes de construir

`8.210 bytes/183 líneas`. Preflight de canales, búsqueda en paralelo (registros
de paquetes, MCP, skills, GitHub), puntuación de candidatos y decisión
adoptar/extender/componer/construir.

**Comparación.** `research-first` es el dueño y ya cubre el preflight («si un
canal no está accesible, decláralo sin inferir ausencia»), la búsqueda en el
repo primero y la decisión adoptar/adaptar/construir. Lo único que añade es la
opción **componer** (2–3 piezas pequeñas). Choca en varios puntos:

| La pieza | El plugin |
|---|---|
| «Score candidates» (9/10, 8/10) como base de la decisión | research-first: «no uses popularidad ni un score agregado como sustituto de adecuación» |
| Paso 5 «Install package / Configure MCP» dentro del flujo | Instalar requiere que forme parte del trabajo autorizado |
| «Exact match, MIT/Apache → adopt» | La licencia se contrasta con el proyecto, no con una lista fija |
| Ejemplo 2: cliente HTTP con reintentos, «zero custom code» | Qué se reintenta (solo lo idempotente, con tope) es la decisión real (backend-practices, fallo de dependencia) |
| Dice lanzar «the researcher agent» pero el bloque usa `general-purpose` | Nombre de rol inexistente |
| El planner invoca la búsqueda antes de su fase 1 | En el plugin la usan analyst y architect; planner no |

**Destino:** una línea en `research-first` paso 4: «adoptar, adaptar, **componer**
o construir». Nada más.

## S256 — Buscar una skill antes de crearla

`4.486 bytes/141 líneas`. Capturar intención y sinónimos, buscar en skills
locales y del marketplace, después en GitHub y la web, revisar el candidato
externo, ordenar y ofrecer usar/bifurcar/crear.

**Comparación.** Dentro de este repo, crear una pieza es territorio de
`plugin-dev`, cuyo paso «No reinventar» solo mira scripts. Falta el paso
equivalente para piezas: antes de una skill o agente nuevo, buscar en el
inventario (`plugin-panel`, `skill-index.py`) un dueño existente y, si lo hay,
proponer la línea en él (ADR-011). La revisión de candidatos externos (leer el
`SKILL.md`, buscar comandos de shell, escrituras, red, credenciales e
instalaciones; no editar originales del marketplace) es buena y pertenece a
`research-first`: una skill de terceros es código. Defectos: ordena GitHub con
`--sort stars` (popularidad otra vez) y una de las tres consultas web fijas
apunta al repositorio de origen del corpus.

**Destino:** paso 0 de `plugin-dev` («busca dueño antes de crear») y una fila en
`research-first/references/comparison.md` para skills y plugins externos.

## S257 — Inventario y auditoría de skills

`7.819 bytes/195 líneas` más tres scripts (inventario, diferencias por fecha,
guardado de resultados). Modo rápido por cambios y modo completo con subagentes
por lotes de ~20 y veredicto Keep/Improve/Update/Retire/Merge.

**Comparación.** `capability-audit` es el dueño y su método ya fija lo
importante: conservar/ampliar/actualizar/consolidar/retirar, motivo concreto,
cobertura existente comprobada y delta con destino. Coincide en exigir motivos
autosuficientes (para retirar: defecto y quién cubre; para fusionar: destino y
contenido). Choca en lo técnico:

| La pieza | El plugin |
|---|---|
| El modo rápido reevalúa solo si `mtime > evaluated_at` | method.md: «El mtime por sí solo no demuestra equivalencia»; reutilizar exige cuerpo, recursos, callers y contrato iguales (hash) |
| Uso a 7/30 días contando eventos `Read` sobre la ruta del `SKILL.md` | Una skill cargada por la herramienta Skill no es un `Read`: el contador da 0 a skills en uso. «Ausencia de logs no significa cero uso» |
| `save-results.sh` fusiona pero nunca elimina entradas | Las piezas retiradas quedan en la caché como vigentes |
| La caché se escribe dentro del directorio de la propia skill | En una instalación como plugin ese directorio lo reemplaza la actualización |
| Inventario con `node` + `jq` + `awk` en bash | Dependencias que el plugin evita en scripts deterministas (Python con tests) |

**Sin destino.** Como mucho, una línea de ejemplo de «motivo suficiente» en
`capability-audit/references/method.md`.

## S255 — Medir si las skills se cumplen

`2.500 bytes/59 líneas`. Genera con un modelo una especificación de pasos a
partir de una skill, tres escenarios con presión creciente (de apoyo, neutro y
en contra), los ejecuta con `claude -p`, clasifica las llamadas a herramientas
con otro modelo, comprueba el orden de forma determinista e informa de la tasa
de cumplimiento.

**Comparación.** El plugin mide la **activación** (`evals/run.py`, casos con
positivos y negativos) y los **resultados** (`outcome-evals`), no la secuencia
de herramientas. La idea valiosa son los **escenarios en contra**: «hazlo rápido,
los tests son opcionales» contra `tdd`, `quick-implement` o `adversarial-review`.
Pero el plugin ya deja un artefacto mejor que una clasificación: la línea
`RED:` del ledger y el veredicto de los scripts de puerta. Defectos:

| La pieza | Corrección |
|---|---|
| El modelo clasifica qué llamada es «escribir test» o «test rojo»; la tasa sale de esa etiqueta | Una puntuación del modelo no es un veredicto; comprobar el artefacto (`RED:`, `qa-gate`) |
| Especificación y escenarios se regeneran con un modelo en cada ejecución | outcome-evals: el corpus y el criterio se fijan antes de ejecutar |
| `ALLOWED_SETUP_EXECUTABLES` con `npm` y `pip` para «evitar ejecución arbitraria» | `npm install`/`pip install` ejecutan scripts del paquete; `cp`/`mv` aceptan rutas absolutas fuera del sandbox |
| Sandbox fijo en `/tmp/skill-comply-sandbox` y `claude -p` sin `--bare` con `Bash` permitido | No portable a Windows; la sesión carga hooks y plugins del anfitrión y Bash no queda confinado |
| `runner.py` redacta la ruta del home en las observaciones, pero `report.py` escribe `skill_path` tal cual | El informe filtra el usuario que el runner intentaba ocultar |
| Recomienda «promover a hook» los pasos con cumplimiento < 60 % | Un hook global informa; un bloqueo solo en el frontmatter de un agente (ADR-007) |
| El fixture «cumple» muestra `1 passed` para un test que nunca importa `fib` | El clasificador se fía del texto de salida, no de que el rojo y el verde sean posibles |

**Destino:** un tipo de caso «en contra» en `evals/` para las piezas de
disciplina (prompt que desalienta el método; `expect` comprobado por artefacto,
no por clasificación) y una línea en `outcome-evals/references/protocol.md`:
la presión del prompt es una condición más a fijar y comparar. No se adopta el
runner.

## S264 — Compactación por fases

`8.608 bytes/156 líneas`. Hook `PreToolUse` en Edit/Write que lee la transcripción
y sugiere `/compact` por tamaño de contexto o número de llamadas, guía de cuándo
compactar y qué sobrevive.

**Comparación.** Sugerir es compatible con «los hooks informan», pero un hook
en cada edición que relee la transcripción es coste fijo para una señal que el
plugin ya da: la statusline opt-in muestra el contexto usado, `session-context.sh`
reinyecta índice de piezas y estado del roadmap tras `compact`, y la regla
«escribe el plan en un fichero antes de compactar» es el ledger canónico. La
«tabla de disparadores para cargar skills bajo demanda» es lo que ya hace
`skill-index.py`. Defectos: sitúa la memoria en `~/.claude/memory/`, cuando la
memoria automática de Claude Code se guarda por proyecto
(`~/.claude/projects/<proyecto>/memory/`, observado en esta instalación); cifras
sin medición («reduce el contexto base un 50 %+», «95 %+» de una herramienta
externa); y una afirmación de versión sobre la retirada de las herramientas de
tareas que no se contrastó.

**Sin destino.**
