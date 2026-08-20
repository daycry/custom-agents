<!--
  FRAGMENTO COMPARTIDO: memoria técnica del proyecto (bucle de lectura, fuente única).
  Lo referencian los agentes que LEEN antes de trabajar (evaluator, planner, implementer,
  qa, documenter). Calcado del patrón de `constitution-check.md` y del protocolo de
  bookends de `agents/nemesis.md` (§1, "apertura lee / cierre actualiza" sobre
  `docs/security-scan/STATE.md`+`MEMORY.md`) — aquí no hay cierre porque la escritura la
  hacen otros fragmentos (`knowledge-write.md`), no el lector.
  Si cambias la regla aquí, cambia para todos — no la dupliques en prompts.
-->

# Memoria técnica del proyecto — paso compartido (bucle de lectura)

**Antes de trabajar**, comprueba si el proyecto consumidor tiene memoria técnica acumulada:

```bash
[ -d docs/knowledge/ ] && echo "memoria técnica presente"
```

- **Si existe `docs/knowledge/`:** lee primero su `README.md` (índice de entrada, progressive
  disclosure) — **no** abras `adr/`, `gotchas/` ni `lessons/` enteros de entrada; cada entrada vive
  en su propio fichero con ID (`adr/ADR-NNN-<slug>.md`, `gotchas/GOT-NNN-<slug>.md`,
  `lessons/LES-NNN-<agente>-<slug>.md`). Del índice, abre **solo el fichero de la entrada concreta** cuya
  columna "Área" toque la tarea que tienes delante (p. ej. si estimas, abres los ficheros de área
  "Estimación / calibración"; si tocas Confluence, los de área "Confluence") — lectura SELECTIVA:
  nunca "todo `gotchas/`" ni "todo `lessons/`", solo las entradas señaladas por el índice.
  - **Distingue por `estado` antes de aplicar nada** (spec `knowledge-capture` §Bucle de lectura
    punto 5 y §Manejo de errores "Entrada dudosa o no verificada"): una entrada `estado: aceptada`
    ya pasó la revisión de dos lentes (o el usuario en la puerta) — aplícala como doctrina normal.
    Una entrada `estado: propuesta` **NO** está validada todavía: preséntala como propuesta
    pendiente ("hay una propuesta sin validar que dice X, tómala como indicio, no como regla
    cerrada"), no la apliques como si fuera doctrina vinculante, y dilo explícitamente si
    condiciona una decisión tuya. Una entrada `estado: obsoleta` no se aplica; sigue el enlace a
    la que la sustituye.
  - Aplica lo que digan (respetando la distinción de estado de arriba) salvo que el histórico más
    reciente (un ADR `obsoleta` con sucesor, o una lección contradicha por evidencia posterior) las
    anule explícitamente — gana lo más reciente, y la constitución del proyecto
    (`constitution-check.md`), si existe, prima sobre la memoria.
- **Si NO existe `docs/knowledge/`:** continúa sin ella — es **siempre activa pero degrada en
  silencio** (D3 de la iniciativa `knowledge-capture`): la carpeta nace en el primer registro
  (`knowledge-write.md`), nunca bloquea a un lector que llega antes de que exista.

**Reparto de qué lee cada agente** (evita que todos abran todo — protege la inversión de
`2026-08-10-token-diet`):

| Agente | Qué abre además del índice |
|---|---|
| `evaluator` | `lessons/LES-*-evaluator-*.md` que apliquen (lecciones de estimación/calibración) |
| `planner` | `adr/ADR-*.md` + `lessons/LES-*.md` que apliquen (decisiones y lecciones de proceso que afectan al diseño del plan) |
| `implementer` | `adr/ADR-*.md` + `gotchas/GOT-*.md` que apliquen (decisiones que restringen la implementación y trampas ya comprobadas) |
| `qa` | `gotchas/GOT-*.md` que apliquen (trampas ya comprobadas, útil para no repetir un flaky ya diagnosticado) |
| `documenter` | todo lo que liste el índice (`adr/`, `gotchas/`, `lessons/`) — es quien indexa/deriva la documentación de producto |

No leas por leer: si el índice no tiene ninguna entrada de tu área para esta tarea, sigue sin
abrir nada más — la progressive disclosure es la protección contra el coste de "leer memoria" en
cada invocación.
