# Comandos de build, pruebas, cobertura, formato y limpieza — C074, C075, C077, C078, C081, C083, C091

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Siete definiciones completas: **31.922 bytes/1.156 líneas**. [commands-c4-build-test-reading-evidence.json](commands-c4-build-test-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Los siete cambian código o tests fuera de una tarea del ledger. En el plugin el
código lo toca **solo** `implementer` (`docs/agents/ROLES.md`, fila implementer),
dentro de una `T-XX` con `Archivos` y `Verificación`; el método viene de skills
compartidas: `debug-root-cause` para un build roto
(`skills/debug-root-cause/SKILL.md:21-25`), `tdd` para el orden test→código
(`skills/tdd/SKILL.md:44-50`), `unit-tests` para medir cobertura sin inventar
(`skills/unit-tests/SKILL.md:61-71`) y `code-health` para medir sin refactorizar
(`skills/code-health/SKILL.md:99-102`). La puerta de entrada es `/dev-cycle`
(o `quick-implement` para un cambio pequeño); ninguno de estos comandos tiene
hueco como comando propio.

Los ejecutores ya tienen ficha en T-04:
[agents-pytorch-react-rust-swift-build.md](agents-pytorch-react-rust-swift-build.md)
(A054, A057), [agents-refactor-security-silent-tdd-types.md](agents-refactor-security-silent-tdd-types.md)
(A056, A065). Sus líneas **ya están integradas**: build como reproducción mínima
(`debug-root-cause/SKILL.md:21-25`), React duplicado (`react.md:41-42`), borrado
de código sin uso con referencias dinámicas descartadas (`agents/planner.md:88`) y
refactor puro como `TDD n/a: refactor` (`tdd/SKILL.md:41`, D-053). Los umbrales de
cobertura por capa ya se resolvieron: el umbral es del proyecto
(`tests.coberturaMinima`, [skills-destinations.md](skills-destinations.md) línea 391).

## C074 — quality-gate

`1.909 bytes/52 líneas` · tools: no declara · model: no declara. Entrada manual
al formateador que la fuente ejecuta como hook `PostToolUse`: Biome/Prettier,
`gofmt` o `ruff format` sobre un fichero; `ECC_QUALITY_GATE_FIX=true` aplica el formato.

- **Artefactos:** el fichero reformateado (con FIX). Dueño propio: `implementer`, dentro de su tarea.
- **Despacho:** un script de hook alimentado con JSON por stdin.
- **Disparador:** «pasa el formateador a este fichero».

**Comparación.** [operational-panel-commands.md](operational-panel-commands.md)
(línea 65) dejó C074 como decisión provisional hasta leer el handler. El handler
sigue sin leer, pero el contrato que el propio comando declara ya basta para
decidir: un hook `PostToolUse` que **reescribe** ficheros con FIX choca con
ADR-007 (los hooks globales informan; los propios son `mark-docs-pending`,
`ledger-lint-warn` y `progress-line`, `hooks/hooks.json`). El formateo es
herramienta del proyecto, que `implementer` ejecuta en P5 junto a tests y build
(`agents/implementer.md:105`). Defectos de la fuente: `$ARGUMENTS [path]` (C074:50)
frente a «the script takes no CLI arguments» (C074:15, :50-52); `.md` entra en
Prettier/Biome (C074:20) y reformatea prosa.

Escenarios: **positivo** «cierra la fase con lint y formato en verde» →
`implementer` P5 con los comandos del proyecto; **negativo** «formatea cada
fichero que edites, automáticamente» → no hay hook que escriba; se declara en
la tarea o en la configuración del propio proyecto.

**Destino:** **Sin destino.** Cierra la decisión provisional.

## C075 — react-build

`5.454 bytes/187 líneas` · tools: no declara · model: no declara. Envuelve a
`react-build-resolver`: detecta Vite/webpack/Next/CRA/Parcel/esbuild/Bun, corre el
build, agrupa por capa y arregla un error cada vez; para a los 3 intentos.

- **Artefactos:** código y dependencias instaladas (`npm i -D @types/react-portal`, C075:98-100). Dueño propio: código → `implementer`; subir o añadir dependencias → spec de `dependency-upgrade` y tarea del plan.
- **Despacho:** un agente por framework.
- **Disparador:** «falla `npm run build` tras subir React».

**Comparación.** Cubierto por A054 y la Fase 1 de `debug-root-cause`. Lo propio
del comando:

| Línea | Problema |
|---|---|
| :36-39 | Lanza `npm`, `pnpm`, `yarn` y `bun build` uno tras otro con `2>/dev/null`: ejecuta gestores que el proyecto no usa y oculta sus errores. El plugin usa el gestor que indica el lockfile (`debug-root-cause/SKILL.md:22`) |
| :98-100 | Instala un paquete durante el arreglo sin confirmación; [commands-workflow-comparison.md](commands-workflow-comparison.md) (línea 16) ya fijó «no instalar … por inferencia» |
| :171 | «Same error persists after 3 attempts» por error; el tope propio es por bucle de la iniciativa (`commands/dev-cycle.md:413`) |

Escenarios: **positivo** «el build de React falla en esta tarea» →
`debug-root-cause` Fase 1 dentro de la tarea de `implementer`, con `react.md`;
**negativo** «sube React a la 19» → `dependency-upgrade` (spec de upgrade), no un arreglo de build.

**Destino:** **Sin destino.** Ya integrado en `debug-root-cause` y `react.md:41-49`.

## C081 — rust-build

`4.578 bytes/187 líneas` · tools: no declara · model: no declara. Envuelve a
`rust-build-resolver`: `cargo check`, `clippy -D warnings`, `fmt --check`,
`cargo tree --duplicates` y `cargo audit`; arregla un error cada vez.

- **Artefactos:** código Rust. Dueño propio: `implementer`.
- **Despacho:** un agente por lenguaje.
- **Disparador:** «`cargo build` no compila».

**Comparación.** Rust aparcado (D-131); el procedimiento general ya está en
`debug-root-cause`. Lo propio: la estrategia trata los avisos de Clippy como
segunda prioridad del arreglo (C081:33, :165), lo que amplía un arreglo de
compilación a lint; y `cargo audit` (C081:42) es auditoría de dependencias con red
(`nemesis`).

Escenarios: **positivo** «el build falla tras un merge» → `debug-root-cause`
genérico; **negativo** «¿hay crates vulnerables?» → `nemesis`.

**Destino:** **Sin especialidad** hasta que un consumidor declare Rust (D-131).

## C077 — react-test

`7.335 bytes/265 líneas` · tools: no declara · model: no declara. TDD para React con
Testing Library y Vitest o Jest: firma, tests de comportamiento, rojo, código
mínimo, refactor y cobertura por capa.

- **Artefactos:** tests y componente. Dueño propio: `implementer` con `tdd: true` (evidencia `RED:` en el ledger, `tdd/SKILL.md:50`).
- **Despacho:** ninguno; el comando es el método.
- **Disparador:** «hazme este componente con TDD».

**Comparación.** `tdd` es la fuente única del ciclo y `references/by-stack.md:11-12`
ya da el comando de un test con Jest y Vitest; la accesibilidad tiene dueño en
`frontend-quality`. Diferencias:

| Línea | Problema |
|---|---|
| :78-122, :125-131 | Escribe cuatro tests y los ejecuta juntos; el plugin pide **un** criterio y **un** test en rojo cada vez (`tdd/SKILL.md:46`) |
| :116-121 | «Is keyboard reachable»: `input.focus()` programático pasa con cualquier `input`; no prueba el orden de tabulación (`user.tab()`). Es un test que no puede fallar (`tdd/SKILL.md`, tabla de racionalización) |
| :216-224 | Umbrales fijos por capa; aquí el umbral es del proyecto |

Escenarios: **positivo** «con TDD, añade el buscador con debounce» → `tdd` vía
`implementer`; **negativo** «¿cuánta cobertura tiene este componente?» → `unit-tests`.

**Destino:** **Sin destino.** Ya integrado en `tdd` y `by-stack.md`.

## C083 — rust-test

`7.003 bytes/308 líneas` · tools: no declara · model: no declara. TDD para Rust con
`#[test]`, rstest, proptest y mockall; cobertura del 80 % con `cargo llvm-cov`.

- **Artefactos:** tests y código Rust. Dueño propio: `implementer`.
- **Despacho:** ninguno.
- **Disparador:** «escribe esta función Rust con TDD».

**Comparación.** `by-stack.md:17` ya da `cargo test <criterio> -- --exact`. La
cobertura no se puede medir con `coverage-gate.py`: Cargo sale con exit 2 y
`buildSinSoporte` (`unit-tests/SKILL.md:99-102`; parser aparcado en D-111). Lo
propio: cuatro tests a la vez (C083:66-121) y objetivos fijos (100 % lógica crítica,
C083:277), igual que C077.

**Destino:** **Sin especialidad** (D-131).

## C091 — test-coverage

`2.742 bytes/73 líneas` · tools: no declara · model: no declara. Mide la cobertura
con la herramienta del stack, lista los ficheros por debajo del 80 % y **genera
tests** hasta superar el umbral; informe antes/después.

- **Artefactos:** tests nuevos e informe. Dueño propio: la medida → `unit-tests`; los tests → `implementer` en una tarea con criterios.
- **Despacho:** ninguno.
- **Disparador:** «sube la cobertura al 80 %».

**Comparación.** `unit-tests` mide con la herramienta oficial y **no elige qué
tests escribir** (`unit-tests/SKILL.md:94-95`). Diferencias:

| Línea | Problema |
|---|---|
| :49-51 | «Si sigue por debajo del 80 %, repite»: generar tests para llegar a un número produce los anti-patrones que el plugin no cuenta como cobertura (asserts triviales, mocks de todo, `unit-tests/SKILL.md:50-59`) |
| :43 | «Mock external dependencies (database…)» como regla; las pruebas de datos del consumidor PHP van contra motor real (`php-codeigniter.md`, ver [agents-php-python-tests-mle.md](agents-php-python-tests-mle.md)) |
| :15 | `pytest --cov=src` supone la carpeta `src` |
| :28 | Útil: el código muerto infla el denominador. Ya lo cubre el borrado con tarea (`planner.md:88`) |

Escenarios: **positivo** «¿qué % cubre el diff de esta rama?» →
`coverage-gate.py --changed-only`; **negativo** «genérame tests hasta el 80 %» →
no se fabrican tests por número: `planner` abre la tarea con criterios y
`implementer` la ejecuta.

**Destino:** **Sin destino.** Ya integrado en `unit-tests`.

## C078 — refactor-clean

`2.901 bytes/84 líneas` · tools: no declara · model: no declara. Detecta código
muerto (`knip`, `depcheck`, `ts-prune`, `vulture`, `deadcode`, `cargo udeps`), lo
clasifica en SAFE/CAUTION/DANGER y borra uno a uno con la suite antes y después.

- **Artefactos:** borrados de código y dependencias. Dueño propio: `planner` abre la tarea (`planner.md:88`), `implementer` borra.
- **Despacho:** ninguno; herramientas externas por `npx`.
- **Disparador:** «limpia el código muerto».

**Comparación.** Cubierto por A056, cuya línea ya está en `planner.md:88`.
`code-health` mide duplicados pero no detecta código muerto. Lo propio del comando:

| Línea | Problema |
|---|---|
| :44 | «Revert with `git checkout -- <file>`»: descarta **todos** los cambios sin comitear del fichero, también los del usuario o de otra tarea. El guardarraíl lo permite (`agent-kits/shared/guardrail-check.py:569-573` trata `checkout … -- fichero` como restauración) y `implementer.md:102` solo veta `reset --hard` |
| :55-61 frente a :84 | «Consolidate duplicates… merge into one» y, después, «Don't refactor while cleaning»: contradicción |
| :15-17 | `npx` sin versión fijada (ya señalado en A056) |

Escenarios: **positivo** «borra las exportaciones sin uso del módulo de pagos» →
tarea de `planner` con referencias dinámicas descartadas → `implementer`;
**negativo** «¿dónde hay código duplicado?» → `code-health`, solo informe.

**Destino:** **Sin destino** como comando; una línea en `implementer` (abajo).

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `agents/implementer.md` · P4 «Commits lógicos», viñeta de `reset --hard` (línea 102) | Añadir: «Para deshacer un intento fallido, revierte solo tus cambios (`git diff` del intento → `git apply -R`, o `git restore -p`); nunca `git checkout -- <fichero>` ni `git restore <fichero>` sobre un fichero que ya tenía cambios sin comitear antes del intento.» |
