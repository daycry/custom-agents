---
spec: project-specialization
descripcion: >
  Especialización por proyecto como TERCER BUCLE con la misma gramática que el ciclo y la memoria
  (registro canónico + puerta de entrada + puerta de cierre): cascada de personas de proyecto en el
  brief, comando `/specialize` con evidencia obligatoria, escalera de decisión y puerta de colisión,
  registro `.claude/pieces.json` auditado por `/doctor`, tres estados por hash (gestionada/no
  gestionada/modificada), modo de adopción, y piezas de proyecto multi-runtime delegadas en
  `export-interop.py --root`. F3 (deriva semántica + «Cuándo aplica») queda diferida a una iteración
  posterior. Fuente única del alcance: `analysis.md` de esta carpeta.
estado: aprobada
creado: 2026-09-09
actualizado: 2026-09-09
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
relacionado: docs/roadmap/2026-09-04-ideas-externas/analysis.md (absorbe sus ideas 2, 3 y 4)
generacion:            # PASADA 2 de descubrimiento — ventana propia de esta reescritura
  inicio: 2026-09-09T08:38:50Z
  fin: 2026-09-09T08:45:34Z
  fuente: estimado     # `usage-meter.py close` degradó: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio a partir del tamaño de lo leído/escrito
  tokens_reales: { entrada: 70000, salida: 17000, cache_creacion: 30000, cache_lectura: 300000 }
  eur: 1.02
  horas_ia: 0.18
  duracion: 7m
  ratio_usado: 479326
---

# Especialización por proyecto — el tercer bucle

> **Evaluación:** [`evaluation.md`](evaluation.md) — **rehecha sobre esta versión de la spec**
> (pasada 2, `en-revision`): **47,0 h base · 56,4 h con margen · 2.837 € · 1.898k tokens · 9
> características** (7 heredadas + C-10 `pieces-registry.py` + C-11 multi-runtime; C-08 y C-09
> diferidas). Lleva tabla de deltas frente a la pasada 1 (45,0 h · 2.264 €): el recorte de F3
> **encarece** la iniciativa un 25 %. Veredicto: **go por tramos**, F2 con cuatro condiciones.
> **Diseño (opt-in, alcance `C-10`):** [`design.md`](design.md) — `aprobado` (2026-09-09): de las tres opciones para la forma de `.claude/pieces.json` el usuario eligió **O1** (la pieza es la raíz, sus destinos anidados, `runtime` como dato); decisión y descartadas en [`ADR-014`](../../knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md) (`propuesta`)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) (ledger canónico) — `borrador` (2026-09-09): **22 tareas en 3 fases** sobre F1+F2, con el presupuesto de la evaluación heredado por característica (47,0 h base · 56,4 h con margen · 2.837 €) y las cuatro condiciones del go convertidas en aristas del grafo de dependencias
> **Análisis de origen (única fuente del alcance de esta spec):** [`analysis.md`](analysis.md)
> **Iniciativa absorbida:** [`2026-09-04-ideas-externas/analysis.md`](../2026-09-04-ideas-externas/analysis.md) — ideas 2, 3 y 4

> **Terminología:**
> - **Pieza de plugin** — agente, skill, comando, kit o hook que vive en este repo y viaja con el
>   plugin. Es agnóstica de dominio por diseño.
> - **Pieza de proyecto** — persona, tool, skill o agente que vive en el `.claude/` del consumidor,
>   sabe de SU dominio y solo existe ahí. Es lo que esta spec permite tener.
> - **Persona** — perfil de dominio de ~10 líneas que `task-brief.py` inyecta en el brief del
>   subagente cuando la tarea lleva `- **Tipo**: <tipo>`. El hueco ya existe; hoy se rellena con uno
>   de los 6 perfiles genéricos del plugin.
> - **Registro canónico** — `.claude/pieces.json`: una fila por pieza **generada** o **adoptada**. Lo
>   escrito a mano y nunca adoptado es ciudadano de primera y aparece como «no gestionada», que es un
>   estado válido.
> - **Los tres estados de una fila del registro (por hash, no por carpeta):**
>   - **gestionada** — el hash del fichero en disco coincide con el hash anotado en su fila.
>   - **modificada** — el hash en disco es distinto del anotado (se editó a mano tras generarse, o
>     se adoptó sin línea base de generación). Nunca se pisa: se muestra el diff y se pide
>     confirmación explícita antes de tocarla.
>   - **no gestionada** — no tiene fila. Es un estado válido, no un error; puede **adoptarse**.
> - **Escalera** — orden de decisión de forma de pieza, del escalón más barato al más caro:
>   nada → persona → tool → skill → agente.
> - **Invariante de dirección** — `/specialize` **lee** `docs/knowledge/` y **nunca escribe** en él.
>   Promover a doctrina sigue siendo exclusivo de `/retro` y del contrato de promoción.
> - **`/specialize` no sabe de runtimes** — escribe siempre en formato canónico de Claude Code
>   (`.claude/…`); si el proyecto tiene Codex u OpenCode instalados, la traducción la hace
>   `export-interop.py --root`, nunca el comando.

## Contexto y objetivo

El plugin sabe **cómo** trabajar y no sabe **dónde** está trabajando (`analysis.md`, resumen en una
frase). El conocimiento del proyecto llega al momento de escribir código **en forma de puntero, no de
instrucción**: `task-brief.py` inyecta hasta `MEMORIA_LIMIT = 12` aciertos compactos de ~25 tokens
(`MEMORIA_TOPE_CHARS = 2400`, líneas `ID · estado · área · titular · ruta`), y el subagente tiene que
decidir abrir el fichero (`analysis.md` §1). En paralelo, el brief tiene un hueco **ya reservado para
doctrina aplicable** —la persona— y lo rellena con uno de 6 perfiles genéricos que no saben nada de
este proyecto (`agent-kits/shared/personas/`, 6 ficheros de 9 líneas).

El objetivo es cerrar ese hueco **sin presupuesto de tokens nuevo y sin sección nueva en el brief**:
que lo que entre en la casilla de la persona sea del proyecto y derive de su memoria. Y hacerlo con la
gramática de los dos bucles que el repo ya tiene cerrados —registro canónico, puerta de entrada,
puerta de cierre (`analysis.md` §2)— para que no sea un saco de piezas sueltas.

**Lo nuevo es un comando y dos scripts colgados de un registro** (`analysis.md` §3). Cuatro de los
siete estadios del ciclo de vida de una pieza ya tienen dueño (`task-brief.py`, el indexado nativo de
Claude Code, `/doctor` y `/retro`). **Esta pasada de descubrimiento recorta el alcance a los
estadios 1-5 (F1 + F2)**: los estadios 6-7 (deriva semántica y muerte) quedan diferidos a una
iteración posterior con punto de control nombrado (ver «Criterio de éxito»), y a cambio se cierra
mejor lo que sí entra: propiedad por hash con tres estados, modo de adopción, requisitos no
funcionales (idempotencia, concurrencia, privacidad) y una característica nueva —piezas de proyecto
multi-runtime, delegada en la maquinaria de interoperabilidad que el plugin ya usa para sí mismo.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Número de comandos | **uno** (`/specialize`, con modo sin argumentos) | La mitad mecánica de la auditoría ya tiene dueño (`/doctor`) y la semántica comparte dueño con la generación. Rectificación 1 de `analysis.md` §Procedencia |
| Criterio de fasado | **por estadio**, no por tamaño | «Ninguna fase entrega un estadio cuyo estadio siguiente no exista todavía» (`analysis.md` §5). La sección de `/doctor` es la puerta de cierre del nacimiento, no una fase aparte |
| Alcance de esta iteración | **F1 + F2** (estadios 1-5); **F3 diferida** (estadios 6-7) | F2 ya entrega su propia auditoría mecánica (`/doctor`): diferir la deriva semántica no deja ningún estadio del ciclo de vida sin dueño. Decisión de la pasada 2 de descubrimiento |
| Origen de la evidencia | **compositor**, no escáner nuevo | `project-scan.py` invoca `deps-inventory.py` + `code-health.py` + `coverage-gate.py` + `knowledge-find.py --json` (`analysis.md` §3, estadio 1) |
| Regla de evidencia | **ID de memoria O `fichero:línea` del escaneo** | Un proyecto sin `docs/knowledge/` tiene igualmente manifiestos, stack y hotspots: es evidencia legítima. Con 0 aciertos de memoria, el aviso lo dice explícitamente |
| Validación de lo generado | **las herramientas existentes** | `scripts/lint_plugin.py` (línea 1130) y `evals/check.py` (línea 253) **ya aceptan `--root`**: el criterio de «pieza válida» sigue teniendo una sola fuente (`analysis.md` §10) |
| Forma por defecto de una pieza | **persona** (~10 líneas) | Escalón más barato de la escalera; el agente es último recurso con override explícito del usuario (`ADR-011` + presupuesto del índice) |
| Puerta de colisión | **obligatoria, determinista, con contrato de salida** | `role-collision.py` es «la pieza que salva `ADR-011`»: exit 0/1 + una línea por colisión (`pieza instalada · disparador que choca · motivo`), para que sea invocable desde `/specialize` sin parsear prosa |
| Propiedad de un fichero de destino | **registro + hash, no carpeta** | `GOT-003`: la carpeta sola no basta cuando el destino puede ser el árbol desplegado del propio plugin. Regla dura: nunca se sobreescribe un fichero que no esté en el registro con hash coincidente |
| Confirmación humana | **previsualiza el LOTE completo, confirma PIEZA a pieza** | Dos puertas separables: `--dry-run`/`--plan` prueba «no escribe nada» sin ambigüedad, y N candidatos exigen N confirmaciones explícitas, no una global |
| Tope de piezas generadas | **5, acumulado en el registro** (no por invocación) | Aritmética del presupuesto medido de `skill-index.py`: `LIMITE_LINEAS = 45`, `LIMITE_CHARS = 3500` (líneas 44-45). Es una propiedad del TOTAL del proyecto, no de una llamada a `/specialize` |
| Versionado del registro | `pieces.json` **comiteado y compartido por el equipo**; `pieces-state.json` **ignorado** | Una especialización por desarrollador haría que el mismo repo se comportase distinto según quién lo abra. Calca la convención config/estado ya existente (`jira.json`/`jira-state.json`, regla 9 de `CONVENTIONS.md`); entradas ordenadas por nombre de pieza para que un conflicto de merge quede local a su línea |
| Adopción de piezas escritas a mano | **existe un modo explícito** (`/specialize --adopt`) | Sin él, el camino de F1 —personas escritas a mano, ciudadanas de primera— nunca podría entrar en el bucle del registro, y eso sí sería un estadio colgando |
| Traducción multi-runtime de piezas de proyecto | **delegada en `export-interop.py --root`; `/specialize` no sabe de runtimes** | Coherencia con cómo el plugin ya se traduce a sí mismo: variantes GENERADAS, nunca editadas a mano; `--root` ya acepta cualquier árbol con forma de plugin (verificado) |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Carpeta de personas de proyecto | `.claude/personas/<tipo>.md` | no existe | primer escalón de la cascada |
| Catálogo de personas del plugin | `agent-kits/shared/personas/` (`--personas-dir`) | 6 tipos, 9 líneas cada uno | segundo escalón (fallback, **intacto**) |
| Registro de piezas generadas — config | `.claude/pieces.json` (comiteado) | no existe | registro canónico del bucle; entradas ordenadas por nombre de pieza |
| Registro de piezas generadas — estado | `.claude/pieces-state.json` (ignorado, `.gitignore`) | no existe | parte efímera (marcadores de máquina), mismo patrón que `usage-state.json` |
| Lock del registro | `.claude/pieces.json.lock` (fichero hermano) | no existe | evita corrupción por escritura concurrente, mismo idioma que los logs de sesión |
| Tope de piezas generadas | `.claude/dev.json` (supuesto, ver §Supuestos) | **5**, acumulado en el registro | aviso + confirmación extra al superar la 5.ª fila, venga de la invocación que venga |
| Presupuesto del índice de arranque | `skill-index.py` `LIMITE_LINEAS` / `LIMITE_CHARS` | 45 / 3.500 | **no se toca**: es el que fija el tope |
| Tope de memoria en el brief | `task-brief.py` `MEMORIA_TOPE_CHARS` | 2.400 (≤ 600 tok) | **no se toca**: la persona usa su propia casilla |
| Traducción multi-runtime de piezas de proyecto | `scripts/export-interop.py --root <.claude del proyecto>` | ya existe (verificado, líneas 42-45 y 512-515) | genera `.codex/…` y `.opencode/…` para las piezas de proyecto igual que para las del plugin |

## Arquitectura y componentes

**Se reutiliza (no se construye):** `task-brief.py` (inyección de persona ya existente),
`knowledge-find.py --json`, `deps-inventory.py`, `code-health.py`, `coverage-gate.py`,
`journal.py candidatas` y `journal.py redactar()` (línea 200, redacción determinista de secretos
evidentes — se reutiliza tal cual para lo que una pieza cite), `doctor.py`, `lint_plugin.py --root`,
`evals/check.py --root`, `scripts/export-interop.py --root/--check/--list` (ya acepta cualquier árbol
con forma de plugin: `agents/`, `commands/`, `skills/`, verificado), el patrón de test de biyección de
`tests/test_knowledge_index.py`, y el indexado nativo de Claude Code para skills y agentes del
proyecto.

**Nuevo:** `project-scan.py` (compositor de evidencia), `role-collision.py` (puerta de colisión, con
contrato de exit code + formato de salida), `agent-kits/shared/pieces-registry.py` (lectura/escritura
del registro con lock, cálculo de hash, los tres estados, modo de adopción — la pieza determinista que
hace verificables la idempotencia, la concurrencia y «modificada» sin ponerlas en prosa del agente),
`commands/specialize.md` (`/specialize`, con modo sin argumentos limitado en esta iteración a **salud
del registro vía `/doctor`**, no a deriva semántica — ver «Fuera (esta iteración)»), el registro
`.claude/pieces.json` / `pieces-state.json`, la sección de especialización de `doctor.py`, y
`docs/SPECIALIZATION.md` (+ espejo en `docs/en/`) como única puerta de entrada del bucle.

**Piezas de proyecto multi-runtime (característica nueva).** `/specialize` escribe SIEMPRE en formato
canónico de Claude Code. Si el proyecto tiene Codex y/o OpenCode instalados (mapeo de destinos a
`.codex/` y `.opencode/`; la regla 5 de `CONVENTIONS.md` ya resuelve las seis raíces), la traducción la
hace `export-interop.py --root <.claude del proyecto>` — el mismo mecanismo con el que el plugin se
traduce a sí mismo hoy, sin cambio de forma. El registro anota **cada ruta escrita por runtime, con su
propio hash** (una fila `.claude/agents/hooks.md` y otra `.codex/agents/hooks.toml`, cada una con el
suyo). **Portabilidad por escalón de la escalera** (ordena qué se traduce y qué no):

| Escalón | Portabilidad | Motivo |
|---|---|---|
| Persona / tool | **neutral** | Las consume `task-brief.py`/Bash y scripts Python propios: no hay frontmatter de runtime que traducir |
| Skill | **viaja sin traducir** | Mismo `SKILL.md` para los tres runtimes, pero su `description` debe caber en ≤ 1.024 caracteres o OpenCode no la carga (mismo límite que las skills del plugin) |
| Agente | **exige traducción real** | Sus `tools` no significan lo mismo en cada runtime (permisos, sandbox); lo traduce `export-interop.py`, nunca a mano |

**Límite honesto (se escribe, no se esconde):** la puerta de confirmación humana de `/specialize` es
un **comando** de Claude Code; fuera de él se traduce a un *prompt*, y ahí depende de que el runtime lo
respete, no de una barrera técnica — la misma clase de degradación que `docs/INTEROP.md` ya documenta
para el guardrail del `implementer`. **Próximas integraciones:** añadir un runtime nuevo es una fila en
la tabla `PROVIDERS` de `install/providers.mjs` (ya existe, con `IDS` exportado, línea 167-168) más su
traductor — **nunca** un cambio en `/specialize`, que sigue sin saber de runtimes.

**Modificado:** cascada de resolución en `task-brief.py` (hoy `--personas-dir` es **un solo
directorio** con default al del plugin, líneas 481-482 y 526-528), la `description` de la skill
`plugin-dev`, `docs/FLOWS.md` (+EN), `docs/agents/ROLES.md`, `docs/CONVENTIONS.md` (reglas 3 y 9 —
fila de `pieces.json`/`pieces-state.json` con la nota config-comiteada/estado-ignorado, y nota
pieza-de-plugin vs pieza-de-proyecto), `/setup`, `docs/INTEROP.md` (+EN, fila nueva de degradación
§4) y `tests/test_export_interop.py` (casos nuevos sobre un árbol de proyecto). La plantilla de
`agent-kits/shared/knowledge-write.md` (campo «Cuándo aplica») **NO se toca en esta iteración** — va
con F3, diferida (ver «Fuera (esta iteración)»).

## Flujo (paso a paso)

1. **Evidencia** — `project-scan.py` compone stack, hotspots, stack de test y áreas de memoria. Cada
   candidato cita `fichero:línea` o el ID de una entrada de memoria; sin evidencia no se propone. Sin
   `docs/knowledge/` (o vacío), lo dice explícitamente: «las piezas propuestas se derivan solo del
   escaneo, sin memoria del proyecto».
2. **Decisión** — la escalera elige forma: nada (duplica algo instalado) → persona → tool → skill →
   agente. Cada candidato pasa por `role-collision.py` (exit 0/1 + una línea por colisión) contra las
   piezas instaladas y las ya generadas.
3. **Puerta humana** — se previsualiza el **lote completo** (`--dry-run`/`--plan` no escribe nada) y
   luego se pide **una confirmación por pieza**, en el orden previsualizado; rehusar una omite solo
   esa pieza, no cancela el lote.
4. **Nacimiento** — `pieces-registry.py` escribe la pieza en `.claude/` bajo sus rutas canónicas
   (nunca sobre un fichero fuera del registro con hash distinto — regla dura de `GOT-003`; aviso y
   confirmación extra si el destino es el árbol desplegado del propio plugin), añade su fila
   (hash incluido) al registro bajo lock, y genera su caso de eval; se valida con
   `lint_plugin.py --root` y `evals/check.py --root`. Si el proyecto tiene otros runtimes, se ofrece
   `export-interop.py --root` para traducir — nunca a mano y nunca automático sin pedirlo.
5. **Ejecución** — `task-brief.py` inyecta la persona por la cascada; skills y agentes de proyecto los
   indexa Claude Code de forma nativa.
6. **Salud** — `/doctor` audita el registro: una línea por fila, ✅/⚠️/❌ con su arreglo, distinguiendo
   `gestionada` / `modificada` (nunca se pisa; se ofrece ver el diff) / `no gestionada` (estado
   válido, ofrece adopción).
7. **Adopción** — `/specialize --adopt <ruta>` sobre una pieza «no gestionada» le añade fila al
   registro con su hash ACTUAL, anotada como `modificada` (no hay generación de referencia que
   comparar), y desde ahí participa en las mismas puertas que cualquier pieza gestionada.

> Los estadios 6-7 del ciclo de vida (deriva semántica contra la memoria, y retirada de piezas
> muertas) **no están en el flujo de esta iteración**: quedan en `analysis.md` §3 y §5 F3, diferidos
> con punto de control (ver «Criterio de éxito»).

## Alcance

- **Dentro (esta iteración):**
  - **F1 · Sustrato** — cascada `.claude/personas/<tipo>.md` → catálogo del plugin → genérico con
    aviso; tipos extensibles más allá de los 6; `docs/SPECIALIZATION.md` (+ espejo EN); sección del
    tercer bucle en `docs/FLOWS.md` (+EN) con el diagrama de `analysis.md` §2; filas en
    `docs/agents/ROLES.md`. **Una persona escrita a mano ya funciona sin generador.**
  - **F2 · Nacimiento** — `/specialize <área>`, `project-scan.py`, `role-collision.py`, registro
    `.claude/pieces.json` (+ `-state.json`) con test de biyección, evals generadas por pieza,
    desambiguación con `plugin-dev` y **la sección de `/doctor` que lo audita** (dentro de esta fase:
    no se entrega la capacidad de generar sin la de comprobar). Además, cerrado en esta pasada:
    - **Tres estados por hash** (`gestionada` / `modificada` / `no gestionada`) con `pieces-registry.py`.
    - **Modo de adopción** de piezas escritas a mano (`/specialize --adopt`).
    - **Requisitos no funcionales**: idempotencia (sin cambios → «sin cambios», exit 0), concurrencia
      (lock del registro) y privacidad (redacción de secretos evidentes con `journal.py redactar()`;
      nunca se cita `docs/security-scan/`).
    - **Piezas de proyecto multi-runtime**, delegadas en `export-interop.py --root` (nunca lógica de
      runtime dentro de `/specialize`).
    - `/specialize` **sin argumentos** en esta iteración se limita a **exponer la salud mecánica del
      registro** (lo que ya audita `/doctor`); no incluye la deriva semántica de F3.
  - Cierre estándar del repo: `lint_plugin.py` con 0 errores, suites en verde, `export-interop.py
    --check`, entradas en los DOS CHANGELOG vía `changelog-sync`, `/setup` ofreciendo `/specialize`,
    `retro.md` + fila en `CALIBRATION.md`.
- **Fuera (esta iteración — diferido, no descartado):**
  - **F3 completa: deriva semántica y retirada de piezas muertas** (estadios 6-7 de `analysis.md` §3;
    antes característica C-08 de `evaluation.md`). **Motivo:** F2 ya entrega su propia auditoría
    mecánica (`/doctor`, con biyección registro↔ficheros y aviso ⚠️/❌); diferir la deriva semántica
    **no deja ningún estadio del ciclo de vida sin dueño**. Se retoma como iniciativa propia cuando
    haya datos del criterio de éxito (ver más abajo).
  - **Campo «Cuándo aplica» en `agent-kits/shared/knowledge-write.md`** (antes característica C-09).
    Se difiere **junto con** la deriva: sin el estadio que lo lee (F3), ningún código consume ese
    campo todavía, y un campo que nadie consume es exactamente la pieza muerta que esta iniciativa
    nació para evitar. Barato no es lo mismo que útil.
- **Fuera (anti-alcance de `analysis.md` §6 — decisiones cerradas, con su motivo, no se construyen
  nunca):**
  - **Comando `/learn`.** Duplicaría la promoción de `/retro` y de `journal.py candidatas`. Su parte
    buena —confirmación humana antes de guardar— se queda como **puerta de `/specialize`**.
  - **Comando de auditoría aparte (`/piece-drift`).** Se parte por naturaleza: lo mecánico va a
    `/doctor` (ya es solo lectura, ya lee `.claude/`, ya emite ✅/⚠️/❌ + arreglo, ya tiene
    `test_doctor.py`) y lo semántico a un modo de `/specialize` (diferido con F3, ver arriba).
  - **Agentes «expertos de dominio» dentro del plugin.** El plugin se mantiene agnóstico; el dominio
    vive en el `.claude/` del consumidor.
  - **`skills/learned/` como carpeta y mecanismo aparte** (idea 2 de `ideas-externas`). Es el escalón
    «skill» de la escalera, no un mecanismo paralelo.
  - **Generar agentes por defecto.** `ADR-011` + presupuesto del índice: escalón de último recurso,
    con override explícito del usuario.
  - **Proponer servidores MCP.** Es configuración, no pieza. En Claude Code no hay primitiva de
    herramienta definida por el usuario: una «tool» aquí es un script determinista con tests que una
    pieza invoca.
  - **Tocar el contenido de las 6 personas del plugin.** Siguen siendo el fallback del último escalón
    de la cascada.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Un sub-script del compositor falta o falla (sin `git`, sin gestor de paquetes, sin stack de test) | Se omite **esa dimensión** con aviso y exit 0. Nunca se inventa dato (patrón de `code-health` y `deps-inventory`) |
| `docs/knowledge/` vacío o inexistente | El escaneo sigue funcionando **solo con evidencia de `fichero:línea`** (manifiestos, stack, hotspots) y lo dice explícitamente: «las piezas propuestas se derivan solo del escaneo, sin memoria del proyecto». Nunca bloquea |
| Candidato sin evidencia (`fichero:línea` **o** ID de memoria) | No se propone. Regla dura, no aviso |
| Candidato que duplica una pieza instalada o ya generada | Se rechaza **nombrando** la pieza que ya lo cubre (escalón «nada» de la escalera); `role-collision.py` sale con exit 1 y una línea `pieza instalada · disparador que choca · motivo` |
| Fichero de destino sin fila en el registro con hash coincidente | Se **rehúsa** escribirlo o retirarlo, y lo dice (regla dura de `GOT-003`: la propiedad es registro + hash, nunca carpeta) |
| El `.claude/` de destino **es** el árbol desplegado del plugin (marcadores `agent-kits/` o `.claude-plugin/` en su raíz) y el candidato es skill o agente (rutas canónicas indistinguibles de las del plugin) | Avisa explícitamente y exige una confirmación humana **adicional** antes de escribir en `skills/` o `agents/` |
| Pieza cuyo hash en disco no coincide con el anotado (`modificada`) | Nunca se pisa: se muestra el **diff** y se pide confirmación explícita antes de cualquier escritura |
| Registro ausente, corrupto o con fila sin fichero | `/doctor` lo reporta ⚠️ con su arreglo; el registro se reconstruye, no bloquea |
| Pieza escrita a mano (sin fila) | «No gestionada»: estado **válido**, no error; ofrece adopción |
| Escritura concurrente del registro | El lock (`.claude/pieces.json.lock`) serializa el acceso; nunca corrompe el JSON |
| Sin cambios desde la última ejecución | Idempotente: no propone nada, informa «sin cambios», exit 0 |
| Superar el tope de 5 piezas **en el registro** (no por invocación) | Aviso con el motivo (presupuesto de `skill-index.py`) y confirmación extra, sea la 6.ª fila de esta invocación o de una posterior |
| El usuario no confirma una pieza del lote | Se omite solo esa pieza; el resto del lote sigue su curso. Si no confirma ninguna, no se escribe nada. Salida limpia, exit 0 |
| Pieza generada que pediría `Bash`/`Write` o un hook de guardia | `tools` mínimos por defecto; `Bash`/`Write` solo con confirmación explícita registrada en la fila; deny **nunca** sin opt-in explícito (`ADR-007`) |
| Contenido citado por una pieza que incluye un secreto evidente | Se redacta con la misma función que `journal.py capture` (`redactar()`) antes de escribir nada |
| Contenido citado que vendría de `docs/security-scan/` | Nunca se cita: ya está excluido del espejo de Confluence y se trata igual aquí |
| Runtime adicional (Codex/OpenCode) presente | `export-interop.py --root` traduce las piezas de proyecto igual que las del plugin; `/specialize` no lo hace directamente |

## Criterios de aceptación

**F1 · Sustrato**

- [ ] [GWT] CA-01 — Dado `.claude/personas/hooks.md` en el proyecto y una tarea con `- **Tipo**: hooks`, Cuando se ejecuta `python3 agent-kits/shared/task-brief.py`, Entonces el brief lleva el contenido de `.claude/personas/hooks.md` y **no** el del catálogo del plugin. Verificación: `python3 -m pytest agent-kits/shared/test_task_brief.py -q`.
- [ ] [GWT] CA-02 — Dado que `.claude/personas/backend.md` no existe y la tarea lleva `- **Tipo**: backend`, Entonces el brief usa `agent-kits/shared/personas/backend.md` — **el comportamiento de hoy no cambia**. Verificación: la suite de `test_task_brief.py` previa sigue verde sin tocar sus asserts.
- [ ] [GWT] CA-03 — Dado un `Tipo` que no existe en ninguno de los dos escalones, Entonces el brief sale sin sección de persona, con aviso por `stderr` y **exit 0** (degradación, no bloqueo).
- [ ] CA-04 — Un tipo nuevo (p. ej. `hooks`) funciona **sin tocar código**: no hay lista blanca de los 6 tipos. Verificación: test con un tipo arbitrario + `grep -n "frontend" agent-kits/shared/task-brief.py` sin lista cerrada de tipos.
- [ ] CA-05 — `docs/SPECIALIZATION.md` existe, es la **única puerta de entrada** del bucle (registro, escalera, dos puertas, invariante de dirección, los tres estados por hash, el límite de esta iteración a F1+F2) y tiene espejo en `docs/en/SPECIALIZATION.md`; `docs/README.md` (+EN) los indexa. Verificación: ambos ficheros existen y `python3 scripts/lint_plugin.py` da 0 errores.
- [ ] CA-06 — `docs/FLOWS.md` y `docs/en/FLOWS.md` tienen la sección del tercer bucle con el diagrama de `analysis.md` §2. Verificación: `python3 -m pytest tests/test_mermaid_blocks.py -q`.
- [ ] CA-07 — `docs/agents/ROLES.md` tiene la fila de `/specialize` con DECIDE / ESCRIBE / LEE / no hace, y escrito el invariante «lee `docs/knowledge/`, nunca escribe en él». Verificación: `grep -n "specialize" docs/agents/ROLES.md`.

**F2 · Nacimiento**

- [ ] [GWT] CA-08 — Dado este repo (con memoria) o un proyecto sin `docs/knowledge/` (solo manifiestos/código), Cuando se ejecuta `project-scan.py --json`, Entonces cada candidato lleva evidencia válida en **cualquiera** de las dos formas: `fichero:línea` del escaneo o ID de una entrada de memoria — ninguna de las dos es obligatoria por sí sola, pero al menos una lo es siempre. Verificación: `python3 -m pytest tests/test_project_scan.py -q`, con un caso sobre este repo (mezcla ambas formas) y otro sobre un árbol temporal sin `docs/knowledge/` (solo `fichero:línea`).
- [ ] [GWT] CA-09 — Dado un proyecto sin `git` (o sin la herramienta de un sub-script, o con `docs/knowledge/` vacío/inexistente), Cuando se ejecuta `project-scan.py`, Entonces omite esa dimensión con aviso y **exit 0**; y si el recuento de aciertos de memoria es 0, el aviso lo dice **explícitamente** («las piezas propuestas se derivan solo del escaneo, sin memoria del proyecto»). Verificación: `pytest` con un árbol sin `docs/knowledge/` que afirma el texto del aviso y el exit code.
- [ ] CA-10 — `project-scan.py` **no** implementa escáner propio. Verificación: `grep -nE "deps-inventory|code-health|coverage-gate|knowledge-find" <ruta>/project-scan.py` devuelve las cuatro invocaciones.
- [ ] [GWT] CA-11 — Dados los candidatos `test-writer`, `code-reviewer`, `security-auditor` y `doc-writer`, Cuando se ejecuta `role-collision.py`, Entonces los **rechaza los cuatro** nombrando la pieza instalada que ya los cubre (`unit-tests`/`tdd`, `reviewer`/`adversarial-review`, `nemesis`/`cybersecurity`, `documenter`). Verificación: `python3 -m pytest tests/test_role_collision.py -q`.
- [ ] [GWT] CA-12 — Contrato de interfaz de `role-collision.py`: exit 0 si no hay colisión, exit 1 si la hay; por cada colisión imprime **una línea** con el formato `pieza instalada · disparador que choca · motivo`. Dado un candidato cuyo disparador literal entrecomillado coincide con el de una pieza instalada o ya generada, Entonces avisa con ese formato exacto (misma heurística que `lint_plugin.py` aplica al plugin). Verificación: `python3 -m pytest tests/test_role_collision.py -q` con un caso que parsea la salida por el formato y comprueba ambos exit codes.
- [ ] CA-13 — El inventario contra el que compara son las piezas **realmente instaladas** (hoy 9 agentes, 17 skills, 12 comandos) más las filas de `.claude/pieces.json`, resuelto con el `find` de la regla 5 de `CONVENTIONS.md` y **no** con una lista hardcodeada. Verificación: test que añade una pieza al árbol temporal y la ve aparecer.
- [ ] [GWT] CA-14 — Cuando se ejecuta `/specialize <área> --dry-run` (o `--plan`), Entonces se previsualiza el **lote completo** de N candidatos con su forma, evidencia y resultado de `role-collision.py`, y **no se crea ningún fichero ni fila de registro**. Verificación: test que corre `--dry-run` y afirma que el árbol de ficheros queda idéntico (diff vacío) y que `.claude/pieces.json` no cambia.
- [ ] [GWT] CA-15 — Dado un lote de N candidatos ya previsualizado, Cuando se ejecuta `/specialize` sin `--dry-run`, Entonces se piden exactamente **N confirmaciones explícitas, una por candidato**, en el orden previsualizado: confirmar una no aprueba las demás, y rehusar una **solo omite esa pieza**, no cancela el lote. Verificación: test con lote de 3 candidatos que confirma 2 y rehúsa 1, y afirma que se escriben exactamente 2 piezas con sus 2 filas de registro.
- [ ] CA-16 — Lo generado pasa la validación con las herramientas **existentes**: `python3 scripts/lint_plugin.py --root <árbol>` con 0 errores y `python3 evals/check.py --root <árbol>` en verde. **No se crea linter nuevo.**
- [ ] [GWT] CA-17 — La propiedad de un fichero de destino la decide el **registro + su hash**, no la carpeta. Dado un fichero que NO está en `.claude/pieces.json` con un hash coincidente, Cuando `/specialize` fuera a escribirlo o retirarlo, Entonces se **rehúsa** y lo dice (regla dura de `GOT-003`). Y dado un `.claude/` de destino con marcadores `agent-kits/` o `.claude-plugin/` en su raíz (es el árbol desplegado del propio plugin) y un candidato de tipo skill o agente (rutas canónicas indistinguibles de las del plugin), Cuando `/specialize` va a escribir en `skills/` o `agents/`, Entonces avisa y exige una confirmación humana **adicional** antes de hacerlo. Verificación: `python3 -m pytest agent-kits/shared/test_pieces_registry.py -q` con un caso de escritura rehusada sin registro/hash y otro de confirmación extra sobre un árbol marcado como plugin.
- [ ] [GWT] CA-18 — El tope por defecto es **5** piezas generadas, **acumulado en el registro completo del proyecto** (no por invocación de `/specialize`): la sexta fila que entraría, venga de esta invocación o de una posterior, produce aviso + confirmación extra, nunca un fallo silencioso. Motivo escrito: `skill-index.py` `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`. Verificación: test que genera 5 piezas en dos invocaciones distintas y comprueba que la 6.ª (en cualquiera de las dos) dispara el aviso.
- [ ] CA-19a — **(Estático)** Una pieza generada declara en su frontmatter `tools` **mínimos** para su forma (persona/tool sin `tools`, skill/agente sin `Bash`/`Write` salvo excepción registrada). Verificación: test sobre el frontmatter generado de cada forma.
- [ ] [GWT] CA-19b — **(Comportamiento)** Dado un candidato cuya escalera pediría `Bash` o `Write`, Cuando se genera sin que la fila de confirmación del registro lo registre explícitamente, Entonces el generador **rehúsa** emitir esos `tools` (degrada a los mínimos con aviso); un hook de guardia (deny) **nunca** se genera sin opt-in explícito (`ADR-007`). Verificación: test que pide un candidato con `Bash` sin confirmación registrada y afirma que el frontmatter resultante no lo lleva.
- [ ] [GWT] CA-20 — Cuando se ejecuta `/doctor`, Entonces hay sección de especialización con **una línea por fila** del registro (✅ `gestionada` / ⚠️ `modificada` con su arreglo —«revisa el diff y confirma»— / ❌ fila sin fichero), y las piezas escritas a mano sin fila salen como «no gestionada» (ofrece adopción), que **no** cuenta como error. Verificación: `python3 -m pytest agent-kits/shared/test_doctor.py -q`.
- [ ] CA-21 — Biyección **registro ↔ ficheros**: fila sin fichero y fichero sin fila salen ⚠️; fichero con hash distinto del anotado sale como `modificada` (nunca como ⚠️ genérico). Verificación: test determinista con su **mutante** (patrón de `tests/test_knowledge_index.py`), incluyendo el mutante de hash.
- [ ] CA-22 — La `description` de `plugin-dev` dice «de ESTE plugin» en sus disparadores; «crea un agente para el plugin» es **negativo** del caso de `/specialize` y el recíproco es negativo del de `plugin-dev`; ambas piezas tienen fila «qué NO hace» apuntándose. Verificación: `python3 evals/check.py` en verde + `grep` de las dos descriptions.
- [ ] [GWT] CA-23 — **Estado `modificada`.** Dado el hash de una pieza en disco distinto del anotado en su fila de `.claude/pieces.json` (se editó a mano tras generarse), Cuando `/specialize` o `/doctor` van a tocarla, Entonces la reportan como `modificada`, **nunca la pisan**, y muestran el diff pidiendo confirmación explícita antes de cualquier escritura. Verificación: `pytest` con fixture que genera una pieza, la edita a mano, y comprueba que el siguiente paso la detecta `modificada` y no sobreescribe sin confirmar.
- [ ] CA-24 — **Modo de adopción.** Dada una pieza «no gestionada» (sin fila) que el usuario quiere que entre en el bucle, Cuando se ejecuta `/specialize --adopt <ruta>`, Entonces se añade su fila al registro con su hash **actual**, anotada como `modificada` (no hay generación de referencia con la que compararla), y desde ahí participa en las mismas puertas que cualquier pieza gestionada. Verificación: `pytest` con una persona escrita a mano que se adopta y aparece en el registro con estado `modificada`.
- [ ] [GWT] CA-25 — **Idempotencia.** Dado un proyecto sobre el que ya se corrió `/specialize` y nada cambió (ni código, ni `docs/knowledge/`, ni piezas), Cuando se vuelve a ejecutar, Entonces no propone ningún candidato nuevo, informa «sin cambios» y sale con **exit 0**. Verificación: `pytest` que corre el flujo dos veces seguidas sobre el mismo árbol y afirma la segunda salida y el exit code.
- [ ] CA-26 — **Concurrencia.** La escritura del registro usa un fichero `.lock` hermano de `.claude/pieces.json` (mismo idioma que los logs de sesión de `journal.py`): una segunda escritura concurrente espera o falla con aviso, y el JSON nunca queda corrupto. Verificación: `pytest` con dos escrituras simultáneas que afirma un JSON válido con ambas filas, o la segunda esperando al lock.
- [ ] [GWT] CA-27 — **Privacidad.** Dado un candidato cuya evidencia citaría contenido del proyecto, Cuando se genera o previsualiza la pieza, Entonces ese contenido pasa por la misma función de redacción de secretos evidentes que usa `journal.py capture` (`redactar()`, `agent-kits/shared/journal.py:200`), y **nunca** cita nada bajo `docs/security-scan/` (ya excluido del espejo de Confluence). Verificación: `pytest` con un fixture que incluye un secreto evidente y una entrada bajo `docs/security-scan/`, y afirma que ninguno de los dos aparece citado en la evidencia.
- [ ] CA-28 — **Registro multi-runtime.** El registro anota, para cada pieza de proyecto traducida a otro runtime, la **ruta escrita y su hash por runtime** (p. ej. una fila `.claude/agents/hooks.md` y otra `.codex/agents/hooks.toml`, cada una con su propio hash), igual que el plugin ya hace consigo mismo en `interop/`. Verificación: `pytest` con una pieza multi-runtime que comprueba las N filas resultantes.
- [ ] [GWT] CA-29 — Dado un proyecto con piezas nacidas de `/specialize` en `.claude/` y Codex y/o OpenCode instalados, Cuando se ejecuta `python3 scripts/export-interop.py --root <proyecto>`, Entonces genera las variantes en `.codex/` y `.opencode/` para esas piezas **exactamente igual** que para las piezas del propio plugin (mismo mecanismo, `--root` ya existente), y `--check` detecta cuando una variante quedó desincronizada. `/specialize` **nunca** genera estas variantes directamente. Verificación: `python3 -m pytest tests/test_export_interop.py -q` con un caso nuevo sobre un árbol de proyecto con una pieza generada.
- [ ] CA-30 — `docs/INTEROP.md` (+ espejo `docs/en/INTEROP.md`) tiene una **fila nueva** en la tabla de degradación (§4) para piezas de proyecto multi-runtime, con el límite honesto escrito: la puerta de confirmación humana de `/specialize` es un comando de Claude Code y, fuera de él, se traduce a un *prompt* — depende de que el runtime lo respete, no de una barrera técnica (misma clase de degradación que el guardrail del `implementer`). Verificación: `grep -n` de la fila nueva en los dos ficheros.

**Cierre (checklist de `analysis.md` §10)**

- [ ] CA-31 — `python3 scripts/lint_plugin.py` con **0 errores**, `python3 -m pytest -q` en verde sobre la línea base de la suite, `python3 scripts/export-interop.py --check` en verde, entradas en los DOS CHANGELOG vía `changelog-sync` y `/setup` ofreciendo `/specialize` al terminar.
- [ ] CA-32 — Cada pieza nueva con doc en `docs/`, fila en `docs/README.md`, fila en `docs/agents/ROLES.md` y las reglas 3 y 9 de `CONVENTIONS.md` actualizadas: `pieces.json` (config, comiteado, entradas ordenadas por nombre) / `pieces-state.json` (estado, ignorado) con su fila en la tabla de la regla 9; nota pieza-de-plugin vs pieza-de-proyecto en la regla 3.
- [ ] CA-33 — `retro.md` en esta carpeta + fila en `docs/roadmap/CALIBRATION.md`. Verificación: `python3 agent-kits/shared/retro-gate.py` en verde.

## Criterio de éxito (diferido, con punto de control nombrado)

Esta iniciativa **no** demuestra reducción de retrabajo al cerrar: F1+F2 entregan **capacidad**
(persona de proyecto aplicable, pieza generable y auditable), no la prueba de que esa capacidad baja
los intentos del bucle de revisión. Eso es correcto y se escribe así, en vez de dejarlo como un
supuesto vago:

- [ ] CA-34 — **F2 cierra contra capacidad entregada** (CA-08 a CA-30 en verde + cierre estándar), no
  contra una métrica de impacto todavía no medible. El punto de control real es nombrado y ya tiene
  mecanismo, sin instrumentación nueva: las **retros de las dos iniciativas siguientes** a esta que
  usen al menos una persona de proyecto anotan, en su `retro.md`, una comparación explícita entre (a)
  los intentos del bucle reviewer→implementer de esa iniciativa (traza «Revisión de dos lentes —
  intento N» que `tasks.md` ya deja, regla 8 de `CONVENTIONS.md`) y (b) la media de intentos de las
  filas anteriores de `docs/roadmap/CALIBRATION.md`. Verificación: `grep -n` de esa comparación en los
  dos `retro.md` correspondientes cuando existan; hasta entonces, el criterio queda explícitamente
  abierto (no aprobado, no fallado).
- **Criterio de retirada** (heredado de `analysis.md` §9, sin cambios): si tras esas dos o tres
  iniciativas los intentos de revisión no bajan y siguen apareciendo los mismos gaps, la capa no
  aporta y se retira. Es parte del diseño, no una amenaza vacía.

## Pruebas

- **Deterministas (el gate):** `tests/test_project_scan.py` (compositor + 4 degradaciones + regla de
  evidencia con ambas formas), `tests/test_role_collision.py` (los 4 nombres canónicos + contrato de
  exit code/formato + disparador duplicado + inventario descubierto),
  `agent-kits/shared/test_pieces_registry.py` (nuevo: lock/concurrencia, los tres estados, hash,
  idempotencia, adopción, regla `GOT-003` de propiedad, redacción de secretos y exclusión de
  `docs/security-scan/`), `agent-kits/shared/test_task_brief.py` (cascada de 3 escalones, tipo
  arbitrario, degradación con exit 0), `agent-kits/shared/test_doctor.py` (sección nueva, tres estados,
  «no gestionada», biyección con mutante de hash), `tests/test_mermaid_blocks.py`,
  `tests/test_console_encoding.py` (los `.py` nuevos, `GOT-005`), `tests/test_export_interop.py`
  (casos nuevos: `--root` sobre un árbol de proyecto con piezas de `/specialize`, variantes
  `.codex/`/`.opencode/`, `--check` detectando desincronización).
- **De activación (`LES-011`):** casos en `evals/cases/command-specialize.json` con ≥ 2 positivos y
  1 negativo, más los **cruzados** con `plugin-dev` en ambos sentidos; `python3 evals/check.py`.
- **Sobre lo generado:** `lint_plugin.py --root` y `evals/check.py --root` contra un árbol temporal de
  consumidor, con y sin `.claude/` que sea el propio plugin.
- **Documentación:** `grep -n` de la fila nueva de `docs/INTEROP.md` (+EN, CA-30) y de las secciones
  nuevas de `docs/SPECIALIZATION.md` (+EN, CA-05).

## Referencias

- [`analysis.md`](analysis.md) — **única fuente del alcance**: §1 (el hueco medido), §2 (los tres
  bucles y el invariante de dirección), §3 (siete estadios), §4 (escalera y puerta de colisión), §5
  (las tres fases y su regla de orden), §6 (anti-alcance), §7 (choque con `plugin-dev`), §8 (riesgos),
  §9 (cómo se mide — base del «Criterio de éxito» de esta spec), §10 (checklist de cierre).
- [`2026-09-04-ideas-externas/analysis.md`](../2026-09-04-ideas-externas/analysis.md) — ideas 2, 3 y 4,
  absorbidas aquí (`absorbido_en` en su frontmatter).
- `agent-kits/shared/task-brief.py` — `--personas-dir` como directorio único (481-482), resolución
  (523-528), `MEMORIA_TOPE_CHARS = 2400` / `MEMORIA_LIMIT = 12` / `BRIEF_TOPE_CHARS = 10000` (103-106).
- `agent-kits/shared/skill-index.py` — `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500` (44-45).
- `scripts/lint_plugin.py:1130` y `evals/check.py:253` — `--root` ya disponible.
- `scripts/export-interop.py:42-45` (uso) y `:512-515` (`argparse`) — `--root` / `--check` / `--list`
  ya disponibles y genéricos sobre cualquier árbol con forma de plugin (verificado).
- `agent-kits/shared/journal.py:200` (`def redactar(texto)`) y `:121` (`REDACTADO`) — la función que
  reutiliza CA-27, sin reimplementar la heurística de secretos.
- `install/providers.mjs:167-168` (`PROVIDERS` / `IDS` exportados) — dónde entra un runtime nuevo, y
  por qué nunca es un cambio en `/specialize`.
- `docs/INTEROP.md` §4 (tabla de degradación, líneas ~117-130) — fila nueva de CA-30; mismo patrón de
  honestidad que ya usa para el guardrail del `implementer`.
- `agent-kits/shared/knowledge-write.md` — plantilla con `area`/`estado`/`fuente` y **sin** condición
  de activación; el campo «Cuándo aplica» queda diferido junto con F3 (ver «Fuera (esta iteración)»).
- Doctrina aplicable: `ADR-011` (un rol, un dueño), `ADR-007` (deny solo con alcance de agente),
  `ADR-008` (skills cortas), `GOT-003` (generador que escribe en el árbol que espeja — base de CA-17),
  `GOT-005` (UTF-8 en consola), `LES-013` (capacidad compartida = skill), `LES-011` (la activación se
  prueba con evals), `LES-009` (la revisión es la partida grande).

## Decisiones confirmadas (revisión del usuario · 2026-09-09 — pasada 1)

Tres pasadas de análisis conversacional (`analysis.md` §Procedencia) dejaron cerradas, y aquí se
recogen tal cual:

1. Un ecosistema, no un conjunto de piezas sueltas: todo cuelga del registro canónico. **Confirmado.**
2. También skills y tools, no solo agentes — con la escalera decidiendo la forma. **Confirmado.**
3. `/learn` y `/piece-drift` descartados como comandos propios. **Confirmado.**
4. Sin agentes de dominio dentro del plugin. **Confirmado.**
5. Piezas de proyecto fuera del alcance de `export-interop.py` en v1. **Revisado en la pasada 2** (ver
   bloque siguiente): ahora SÍ hay interop de piezas de proyecto, delegada en `export-interop.py
   --root`, sin tocar la forma en que `/specialize` trabaja.

## Decisiones confirmadas (revisión del usuario · 2026-09-09 — pasada 2, este descubrimiento)

Diez decisiones sobre el borrador de la pasada 1, aplicadas literalmente en esta reescritura:

1. **Alcance de F3**: `C-08` (deriva semántica) y `CA-23`/`CA-24` de la pasada 1 salen a «Fuera (esta
   iteración)»; F2 ya cierra su propio estadio de auditoría (`/doctor`). **Confirmado.**
2. **`GOT-003` y destinos**: propiedad por registro + hash, no por carpeta; rutas canónicas para skills
   y agentes; confirmación extra si el destino es el árbol del propio plugin. **Confirmado.**
3. **Versionado**: `pieces.json` comiteado y compartido por el equipo, `pieces-state.json` ignorado,
   entradas ordenadas por nombre. **Confirmado.**
4. **Tercer estado `modificada`**: nunca se pisa, se muestra el diff y se pide confirmación.
   **Confirmado.**
5. **Proyecto sin `docs/knowledge/`**: se genera con evidencia medida (memoria O `fichero:línea`),
   degradando con aviso explícito si no hay memoria. **Confirmado.**
6. **Criterio de éxito**: diferido con punto de control nombrado en las retros de las dos iniciativas
   siguientes. **Confirmado.**
7. **Confirmación**: lote previsualizado, confirmación pieza a pieza. **Confirmado.**
8. **Tope de 5**: acumulado en el registro, no por invocación. **Confirmado.**
9. **Adopción**: existe modo explícito para piezas «no gestionadas». **Confirmado.**
10. **Campo «Cuándo aplica»**: se difiere junto con `C-08` (F3); un campo que nadie consume todavía es
    la pieza muerta que esta iniciativa nació para evitar. **Confirmado.**

Además: cuatro NFR que faltaban (idempotencia, concurrencia, versionado —resuelto en el punto 3—,
privacidad) entran con su CA propio, y **piezas de proyecto multi-runtime** entra como característica
nueva, delegada en `export-interop.py --root` sin que `/specialize` sepa de runtimes.

## Supuestos

- **Esquema del registro.** El análisis no fija todos los campos de `pieces.json` / `pieces-state.json`
  más allá de lo que esta spec ya cierra (una fila por pieza, hash, estado, evidencia, ruta, y ahora
  también rutas por runtime cuando aplica). Se asume el resto del esquema al modo de
  `confluence-state.json` / `jira-state.json` (regla 9 de `CONVENTIONS.md`). Lo cierra el `planner`.
- **Dónde vive el tope de 5.** Se asume `.claude/dev.json`, que es donde el repo pone los opt-ins; el
  análisis solo dice «por defecto», y esta spec ya fija que el tope es acumulado, no por invocación.
- **`/setup` ofrece `/specialize`.** Está en el checklist §10 pero sin fase asignada: se presupuesta
  dentro de F2 (CA-05).
- **Retirada = borrado.** Queda fuera de esta iteración junto con el resto de F3; cuando se retome, se
  asume borrado (fichero + fila + caso de eval), sin estado «archivada», salvo que la iteración que lo
  retome decida otra cosa.
- **Horas humanas sin muestra validada.** Ninguna fila de `CALIBRATION.md` tiene horas humanas reales
  (aprendizaje 2): las horas humanas de la evaluación son estimación no calibrada. No cambia con esta
  reescritura; lo hereda el `evaluator` al rehacer `evaluation.md`.
