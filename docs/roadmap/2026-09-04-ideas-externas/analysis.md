---
analisis: ideas-externas
descripcion: >
  Comparativa de `custom-agents` con dos toolkits públicos de Claude Code — `thedotmack/claude-mem`
  (memoria persistente) y `WorldFlowAI/everything-claude-code` (agentes, comandos, skills, rules y
  hooks) — para extraer ideas aprovechables. Precede a la spec: aquí no hay plan ni presupuesto.
estado: borrador
creado: 2026-09-04
fuente: petición del usuario (2026-09-04), con los dos enlaces
relacionado: docs/roadmap/2026-09-04-memory-retrieval/analysis.md
---

# Dos toolkits externos, y las ocho ideas que valen

## Lo primero, porque cambia cómo leer el resto

**`WorldFlowAI/everything-claude-code` es un espejo congelado de `affaan-m/everything-claude-code`.**
Su `README.md`, su `plugin.json` y su `marketplace.json` apuntan todos a `affaan-m` como
`homepage`/`repository`/`author`, y las instrucciones de instalación dicen
`/plugin marketplace add affaan-m/everything-claude-code`. La única capa propia es
`WORLDFLOWAI.md`, una guía de adopción interna. Señales de actividad: **27 commits**, un solo autor
aparente, ficheros de ejemplo fechados en **enero de 2026** y `rules/performance.md` hablando de
modelos de esa época. Las ~1,5 k estrellas que muestra la página son casi seguro heredadas del fork.

**Si vas a copiar algo, mira el upstream, no este fork.** Lo que sigue vale igual, porque las ideas
son las mismas; pero las cifras de inventario son las del espejo.

## Su README promete cuatro cosas que su código no sostiene

Esto es lo más útil que saco de la revisión, porque es exactamente el error que hay que no cometer:

| Lo que promete | Lo que hace |
|---|---|
| «Memory Persistence — hooks que guardan y cargan contexto entre sesiones **automáticamente**» | `scripts/hooks/session-start.js` hace `log()` de cuántas sesiones hay y de la ruta de la última. `log()` **escribe en stderr**, y en `SessionStart` solo **stdout** entra en contexto. **Inyecta 0 tokens.** Ni la ruta. |
| «Continuous Learning — auto-extrae patrones de las sesiones a skills reutilizables» | `evaluate-session.js` cuenta mensajes del transcript y, si pasan de 10, hace `log()` de «evalúa para patrones extraíbles». **No escribe ni un fichero. No llama a ningún modelo. Siempre `exit 0`.** |
| «Contexts — inyección dinámica de system prompt» | `contexts/{dev,research,review}.md` existen (400-600 bytes cada uno). **Nada en el repo los carga.** |
| «Instalar el plugin te da acceso instantáneo a todos los comandos, agentes, skills y **hooks**» | `plugin.json` declara **solo** `commands` y `skills`. `rules/` —la pieza que el README vende como diferencial— **no llega nunca por esa vía**. |

Y el `session-end.js` escribe una plantilla con `[Session context goes here]` y `### Completed - [ ]`
que **nada rellena nunca**: los tres ejemplos de sesión del repo están escritos a mano para el README.

**Dato que lo remata: 3 de sus 11 skills están funcionalmente muertas** (`eval-harness`,
`verification-loop`, `project-guidelines-example`: sin frontmatter, así que no se indexan ni se
activan) **y una cuarta está rota** (`clickhouse-io`, con un bloque `---` vacío antes del real). Dos
de ellas son precisamente las que el README destaca. **Un linter de piezas de veinte líneas lo habría
cazado** — es la mejor prueba empírica de que el nuestro vale lo que cuesta.

## Ninguno de los dos resuelve nuestro problema de memoria

Lo comprobé contra los tres huecos medidos en [`memory-retrieval/analysis.md`](../2026-09-04-memory-retrieval/analysis.md):

| Nuestro hueco medido | `claude-mem` | `everything-claude-code` |
|---|---|---|
| 0 tokens de memoria inyectados al arrancar | inyecta de verdad, con búsqueda | **0 también — y por un bug** (stderr en vez de stdout) que nadie ha detectado |
| 17 de 31 entradas que nadie cita (recuperación) | **resuelto**: `search` → `timeline` → `get_observations`, con coste en tokens declarado | **no existe** recuperación: `utils.js` tiene `findFiles`/`grepFile` sin usar para memoria |
| el brief del subagente no lleva memoria | no aplica (no tiene subagentes con brief) | formato de handoff en prosa, sin persistencia ni inyección |
| journal con 0 entradas | captura sin filtro y comprime con IA | **peor**: plantillas que nunca se rellenan |

**Conclusión: `claude-mem` es el único de los dos con algo que aprender sobre memoria, y ya está
recogido en el análisis anterior.** De `everything-claude-code` lo que se aprende es otra cosa.

## Las ocho ideas que sí valen

Ordenadas por relación valor/coste sobre nuestros huecos reales.

### 1. Hook `PreCompact` — el instante exacto en que se pierde el contexto

No lo usamos. Ellos sí (`scripts/hooks/pre-compact.js`): escribe un log de compactación y anexa una
marca al fichero de sesión activo. **Es el gancho natural para volcar memoria automáticamente**: en
vez de esperar a que alguien escriba una entrada, escribes tú cuando el contexto está a punto de
morir. Ataca de raíz el «journal con 0 entradas» sin pedir disciplina a nadie. Coste: un script.

### 2. `skills/learned/` — la memoria destilada como skill activable

Su `commands/learn.md` guarda las lecciones en `~/.claude/skills/learned/`. La idea es más profunda
de lo que parece: **una lección en `docs/knowledge/` hay que ir a buscarla; una lección con
`name` + `description` en `skills/` la recupera el indexador de Claude Code sin que nadie la cite.**

Eso ataca nuestro problema de recuperación **por el mecanismo, no por el contenido** — y es
complementario al `knowledge-find.py` de la iniciativa `memory-retrieval`: la búsqueda sirve al
agente que ya está trabajando; la skill generada sirve al agente que **no sabe que debería buscar**.
Ellos tienen la idea y no la implementan; nosotros tenemos el contenido y no lo recuperamos.

### 3. El campo `When to Use` en la plantilla de lección

Su plantilla de skill aprendida es `Problem` / `Solution` / `Example` / **`When to Use`**. Ese cuarto
campo es el que falta en la mayoría de memorias curadas, la nuestra incluida: **sin condición de
activación explícita, una lección no se recupera nunca**. Nuestras entradas tienen `area`, que es una
etiqueta; `When to Use` es una condición. Es una línea en la plantilla de `knowledge-write.md` y
mejora directamente el enrutado de las 31 entradas.

### 4. `/learn` con confirmación humana — el hermano barato de `/retro`

Su `/learn` revisa la sesión, redacta con plantilla fija y **pide confirmación antes de guardar**. No
espera a cerrar una iniciativa. Nuestro `/retro` es ceremonioso —iniciativa cerrada, desviaciones,
calibración— y **lleva 15 días parado con 13 iniciativas cerradas después**: es plausible que esté
parado justo por eso. Un `/learn` de mitad de sesión, con gate de confirmación para que no entre
basura, es la mitad del problema resuelta por la mitad del coste.

### 5. El nudge acumulativo por contador

`suggest-compact.js` cuenta llamadas a herramientas en un fichero temporal y a las 50 sugiere
`/compact`, luego cada 25. Patrón genérico de veinte líneas, aplicable a nuestros dos huecos de
disciplina: «llevas N turnos y M ficheros tocados sin entrada de journal», «llevas 15 días sin
`/retro`». Barato, y ataca lo que ningún linter puede: que alguien se acuerde.

### 6. `pass@k` y `pass^k` como métrica de fiabilidad de activación

De `skills/eval-harness/SKILL.md`: `pass@3 > 90 %` para capacidades, `pass^3 = 100 %` para
regresión. Nuestras evals de activación son **binarias**: activa o no activa. Con `pass@k`
distinguimos «activa a la primera» de «activa en tres intentos», y `pass^k` da un umbral duro para lo
crítico. **Coste de implementación: cero** — es una convención de reporte sobre lo que ya medimos.

### 7. Taxonomía explícita de graders, con escalón humano

También de `eval-harness`: **code-based** (determinista) / **model-based** (prompt con nota 1-5) /
**human** (`[HUMAN REVIEW REQUIRED]` con `Risk Level: LOW/MEDIUM/HIGH`), y la regla *«revisión humana
para seguridad — nunca automatizar del todo»*. Le pone nombre a una frontera que nosotros aplicamos
sin nombrarla, y el escalón humano con nivel de riesgo encaja con nuestras puertas de control.

### 8. Detección de gestor de paquetes en seis niveles

`scripts/lib/package-manager.js` con tests: `CLAUDE_PACKAGE_MANAGER` → `.claude/package-manager.json`
→ campo `packageManager` → lockfile → config global → fallback. **Es lo mejor construido de su repo**,
y da portabilidad real a nuestros scripts multi-stack (`coverage-gate.py`, `deps-inventory.py`) sin
preguntar al usuario.

### Dos más que dejo anotadas sin recomendar

- **Hooks que BLOQUEAN con `exit 1`** (dev server fuera de tmux, crear `.md` fuera de una allowlist).
  Nuestra doctrina es «la degradación nunca bloquea», y es correcta **para la degradación**. Pero para
  una **violación de política** —crear documentación fuera de la estructura de `docs/roadmap/`— un
  bloqueo duro es la herramienta adecuada. Merece distinguir los dos casos antes de decidir.
- **`/checkpoint` + `/verify` contra git** (`.claude/checkpoints.log` con `fecha | nombre | sha`, y
  comparación de ficheros, tests y cobertura *ahora vs. entonces*). Marcadores más finos que nuestro
  ledger por tarea; el diff de cobertura contra un checkpoint es una señal que hoy no tenemos.

## Dónde estamos por delante, para no perderlo al copiar

| | Nosotros | Ellos |
|---|---|---|
| Linter de piezas propias | sí | **no** — y le cuesta 3 skills muertas y 1 rota de 11 |
| Tests | 1.178 | 3 ficheros de utilidades JS; **0 cobertura** de agentes, skills, comandos y rules |
| CI | sí | **no existe `.github/`** |
| Evals de activación | ejecutables | doctrina en prosa, **cero evals del propio plugin** |
| Versionado y CHANGELOG | sí | **nada**: sin CHANGELOG, sin `version`, sin releases |
| Licencia | fichero real | badge MIT **sin fichero `LICENSE`** en el árbol |
| Determinismo en scripts | tests + exit codes | 9 de sus 14 hooks son `node -e` **inline dentro del JSON**, intesteables |
| SKILL.md ≤ 200 líneas + `references/` | sí | **al revés**: `e2e-runner.md` ~900 líneas, `frontend-patterns` ~650, todo inline |
| Model tiering | `dev.json` + `model-tier.py` | `model: opus` en los 4 agentes verificados, **contradiciendo su propia `rules/performance.md`** |
| Presupuesto real (h/€/tokens) | sí | nada |
| Cadena con puertas y revisión adversarial | sí | 4 cadenas fijas, sin puertas, sin ledger, sin rebate |
| Frontmatter en comandos | sí | **ninguno** en los 5 verificados |
| Bilingüe ES/EN | sí | solo EN |

**Donde ellos ganan de verdad:** portabilidad (Node en vez de Bash, Windows real, detección de gestor
de paquetes con tests) y **profundidad de dominio** en TypeScript/React/Next.js/Playwright/ClickHouse
— sus `backend-patterns` y `frontend-patterns` son bibliotecas de patrones concretos con código.
Nosotros somos fuertes en proceso y agnósticos de stack; ellos son fuertes en un stack y débiles en
proceso. **No es la misma clase de herramienta**, y la comparación honesta lo dice: si alguien quiere
patrones de React, su repo le sirve más que el nuestro.

## Sobre la pieza «rules», que era la que más curiosidad daba

Son 8 ficheros markdown de 30-60 líneas, **sin ningún frontmatter**. El mecanismo de carga es:
copiarlos a `~/.claude/rules/` y que `~/.claude/CLAUDE.md` los **mencione en una tabla**. No hay
`@import`, no hay hook que los inyecte, no hay carga condicional. **No es un mecanismo: es un
`CLAUDE.md` troceado en ocho ficheros con una tabla de contenidos en prosa.** Un `rule` que nadie
lee es exactamente el problema que tenemos nosotros con `docs/knowledge/` — solo que ellos lo tienen
por diseño y nosotros por accidente.

Lo aprovechable de la idea es la **modularización temática** (ocho ficheros de 40 líneas en vez de un
`CLAUDE.md` de 400) y que dos de ellos documenten cosas que nosotros tenemos en código pero no
escritas para leer: **política de tiering** (`rules/performance.md`) y **cuándo delegar en un
subagente** (`rules/agents.md`). El vehículo no vale; el contenido sí.

## Procedencia

Todo lo afirmado sobre los dos repos externos sale de leer su código y sus manifests, no solo el
README, y donde el dato no era legible se dice: la API de metadatos de GitHub devolvió 403, así que
las señales de salud (estrellas, actividad, contribuidores) son **estimación**, y cuatro ficheros no
se pudieron reproducir literalmente. El inventario, los frontmatters, el contenido de los hooks y las
cuatro promesas incumplidas están **verificados en el árbol**. Lo nuestro está medido sobre el repo en
`3569f5d` (v1.17.0) y su rama de trabajo.
