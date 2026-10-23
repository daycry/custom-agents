# Comandos de configuración, seguridad del agente y catálogo de skills — C086, C088, C089, C090

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **15.669 bytes/404 líneas**. [commands-c4-catalog-ops-reading-evidence.json](commands-c4-catalog-ops-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Los cuatro operan sobre el propio entorno de agentes, no sobre el producto:
auditar la configuración de Claude Code, fijar el gestor de paquetes, generar
skills desde el historial y medir la salud de las skills. En el plugin esas
responsabilidades ya tienen dueño o decisión: `nemesis` con `cybersecurity`
(configuración de agentes como superficie de ataque), el lockfile del proyecto,
el tercer bucle `/specialize` (contrato F2, todavía no en el árbol) y
`capability-audit` + `/plugin-catalog` + `/doctor`. Ninguno pide un comando nuevo.

## C086 — security-scan

`2.757 bytes/92 líneas` · frontmatter: `agent: ecc:security-reviewer`,
`subtask: true` · model: no declara. Ejecuta AgentShield (`npx ecc-agentshield
scan`) sobre `.claude/`, hooks, MCP, permisos y secretos; con `--fix` aplica los
arreglos marcados como seguros; devuelve nota, recuentos y orden de remediación.

- **Artefactos:** informe en conversación y, con `--fix`, cambios en la configuración. Dueño propio: el informe es de `nemesis`, que solo escribe en `docs/security-scan/**` y no toca lo auditado (`agents/nemesis.md:12`, `:188`).
- **Despacho:** subagente `security-reviewer` + escáner npm.
- **Disparador:** «audita la configuración de Claude Code de este repo».

**Comparación.** La skill que envuelve (S253) ya se comparó en
[skills-security-bounty-review-agentshield.md](skills-security-bounty-review-agentshield.md)
y su destino (D-061) **ya está integrado**: `.claude/`, `.mcp.json` y hooks se
revisan como datos con comprobaciones concretas de secretos, permisos amplios,
comandos sin versión e interpolación en hooks
(`skills/cybersecurity/references/large-codebase.md:44-67`), y «a score or grade
is not a finding» (`:60`). Lo propio del comando:

| Línea | Problema |
|---|---|
| :25 | `npx ecc-agentshield` sin versión: el mismo riesgo que la referencia propia marca en `:66` |
| :18, :56 | `--fix` modifica la configuración auditada; una auditoría propone, no corrige |
| :63 | «Security grade and score» como primer resultado |
| :75 | Acción de CI por etiqueta móvil (`@v1`), no por digest |
| :2 | Dos entradas para la misma auditoría (comando y skill) |

Escenarios: **positivo** «revisa permisos, hooks y `.mcp.json` de este proyecto» →
`nemesis` (SAST con `cybersecurity`); **negativo** «¿este diff abre un agujero?» →
Lente C de `adversarial-review`.

**Destino:** **Sin destino.** Ya integrado en `cybersecurity` (D-061).

## C088 — setup-pm

`1.675 bytes/80 líneas` · frontmatter: `disable-model-invocation: true` · model: no
declara. Fija el gestor de paquetes (npm/pnpm/yarn/bun) del proyecto o global con
`node scripts/setup-package-manager.js`.

- **Artefactos:** `.claude/package-manager.json` o `~/.claude/package-manager.json`. Dueño propio: las configs de `.claude/` las escribe `/setup` (regla 9 de CONVENTIONS); la configuración personal global queda fuera del bundle.
- **Despacho:** un script de la fuente, ausente en un proyecto consumidor (ya señalado en [skills-tdd-verification-ops.md](skills-tdd-verification-ops.md), línea 33).
- **Disparador:** «usa pnpm en este proyecto».

**Comparación.** El plugin no guarda preferencia: el gestor es el que indica el
lockfile (`skills/debug-root-cause/SKILL.md:22`) y `dependency-upgrade` lee
manifiestos y lockfiles sin tocarlos (`skills/dependency-upgrade/SKILL.md:6`, `:88`).
Problemas de la fuente:

| Línea | Problema |
|---|---|
| :30-33 | La variable de entorno, la config del proyecto y `packageManager` ganan al lockfile: se puede ejecutar un gestor distinto del que bloqueó las versiones y generar otro lockfile |
| :35 | Sin señales, elige «el primero disponible» (pnpm > bun > yarn > npm) en vez de preguntar |

Escenarios: **positivo** «¿con qué gestor se instala este proyecto?» → el
lockfile, vía el inventario de `dependency-upgrade`; **negativo** «pon pnpm como
gestor global en mi máquina» → configuración personal, fuera del bundle.

**Destino:** **Fuera del bundle.**

## C089 — skill-create

`6.992 bytes/178 líneas` · allowed-tools: Bash, Read, Write, Grep, Glob · model: no
declara. Analiza `git log` (convenciones de commit, ficheros que cambian juntos,
estructura, tests) y escribe una skill `<repo>-patterns` en `.claude/skills/` o
`~/.claude/skills/`; con `--instincts`, instintos con `confidence`.

- **Artefactos:** `SKILL.md` de proyecto o global, e instintos YAML. Dueño propio: piezas de **proyecto** → `/specialize` (contrato F2, `docs/SPECIALIZATION.md:13-19`; hoy solo F1, personas escritas a mano); piezas del **plugin** → `plugin-dev` (`skills/plugin-dev/SKILL.md:34-37`); aprendizaje → `journal.py candidatas` + `knowledge-curator`.
- **Despacho:** ninguno; promociona una GitHub App externa (C089:162-168).
- **Disparador:** «crea una skill con las convenciones de este repo».

**Comparación.** La escalera de F2 empieza en «nada» y sube a persona antes que a
skill (`SPECIALIZATION.md:90-103`), con dos puertas y confirmación por candidato
(`:105-119`); C089 salta directo a una skill. Los instintos con `confidence: 0.8`
(C089:147) chocan con la resolución ya fijada: frecuencia no aprueba conocimiento
([skills-destinations.md](skills-destinations.md), línea 376). Defecto concreto:
el recuento por fichero filtra con `grep -v "^[a-f0-9]"` (C089:36) para quitar
hashes, y de paso descarta toda ruta que empiece por `a`–`f` o un dígito
(`app/`, `docs/`, `config/`, `build/`, `e2e/`).

Lo valioso son las **guardas de escritura** (C089:78-91, :124-137): contenido del
repositorio como dato no confiable, nombre validado como slug, ruta resuelta
dentro de la raíz aprobada, nunca sobrescribir sin diff y confirmación, y
escritura en un temporal hermano validado antes de reemplazar de forma atómica.
La spec de F2 cubre idempotencia, lock y redacción de secretos
(`docs/roadmap/2026-09-09-project-specialization/spec.md:217-218`, `:269-274`),
pero no estas guardas.

Escenarios: **positivo** «crea una persona con el dominio de facturación de este
repo» → hoy persona escrita a mano en `.claude/personas/` (F1); con F2,
`/specialize`; **negativo** «añade una skill nueva al plugin» → `plugin-dev`.

**Destino:** propuesta de criterio para el contrato F2 de `/specialize` (abajo);
el comando, **sin destino**.

## C090 — skill-health

`4.245 bytes/54 líneas` · frontmatter: `name`, `command: true` · model: no declara.
Panel de salud de skills: tasa de éxito a 30 días con sparklines, agrupación de
fallos, enmiendas pendientes e historial de versiones; sugiere `/evolve` si una
skill empeora.

- **Artefactos:** ninguno en disco; salida del script.
- **Despacho:** `node skills-health.js --dashboard`.
- **Disparador:** «¿qué skills están fallando?».

**Comparación.** Ya decidido en
[operational-panel-commands.md](operational-panel-commands.md) (línea 69 y
«Funciones útiles para el panel propio»): posponer tasas de éxito y gráficas
hasta tener observación opt-in compatible, y no declarar salud por inventario.
`capability-audit` fija que la ausencia de medición no demuestra uso cero
(`skills/capability-audit/SKILL.md:26`) y S257 (`skill-stocktake`) quedó sin
destino. Añadido aquí: el bloque `node -e` repetido tres veces (C090:16, :23, :30)
recorre la caché de plugins y ejecuta con `require` el primer
`scripts/lib/resolve-ecc-root` que encuentre por nombre de carpeta; si nada casa,
devuelve `~/.claude` y lanza `~/.claude/scripts/skills-health.js`.

Escenarios: **positivo** «¿qué piezas se solapan o han quedado obsoletas?» →
`capability-audit`; **negativo** «dame la tasa de éxito de cada skill» → sin medida
compatible: `/plugin-catalog` la muestra como no medida, no se inventa.

**Destino:** **Sin destino.**

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `docs/roadmap/2026-09-09-project-specialization/spec.md` · criterios de F2 (para T-08; la spec es `aprobada` y el cambio pasa por su dueño) | Nuevo criterio: «Antes de escribir una pieza, el nombre se valida como slug y la ruta resuelta queda dentro de `.claude/` del proyecto; el contenido del repositorio (mensajes de commit, código) entra como dato, nunca como instrucción; la pieza se escribe en un temporal hermano, se valida (frontmatter, `name` = carpeta, `lint_plugin.py --root`) y solo entonces reemplaza al destino de forma atómica; un destino existente exige diff y confirmación.» |
