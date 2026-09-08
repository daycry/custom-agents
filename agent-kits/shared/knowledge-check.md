<!--
  FRAGMENTO COMPARTIDO: memoria técnica del proyecto (bucle de lectura, fuente única).
  Lo referencian los agentes que LEEN antes de trabajar (evaluator, planner, implementer,
  qa, documenter, reviewer, architect). Calcado del patrón de `constitution-check.md` y del
  protocolo de bookends de `agents/nemesis.md` (§1, "apertura lee / cierre actualiza" sobre
  `docs/security-scan/STATE.md`+`MEMORY.md`) — aquí no hay cierre porque la escritura la
  hacen otros fragmentos (`knowledge-write.md`), no el lector.
  Si cambias la regla aquí, cambia para todos — no la dupliques en prompts: cada agente lleva
  UNA línea con su orden y remite aquí (memory-retrieval T-07).
-->

# Memoria técnica del proyecto — paso compartido (bucle de lectura)

**Antes de trabajar**, comprueba si el proyecto consumidor tiene memoria técnica acumulada:

```bash
[ -d docs/knowledge/ ] && echo "memoria técnica presente"
```

- **Si existe `docs/knowledge/`:** **pregunta, no leas el índice entero.** `README.md` (índice de
  entrada, 31 filas ≈ 3.685 tokens) se sigue vigilando como fuente, pero el camino de lectura es
  `knowledge-find.py` (mismo kit): una consulta devuelve **una línea por acierto**
  (`ID · estado · área · titular · ruta`, ≤ 120 caracteres) y **solo entonces** abres, por ID, la
  entrada concreta que necesites — lectura SELECTIVA (progressive disclosure): nunca "todo `gotchas/`"
  ni "todo `lessons/`", nunca el corpus entero. Localiza el script como cualquier pieza del kit
  (regla 5 de `CONVENTIONS`):

  ```bash
  SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
  python3 "$SHAREDKIT/knowledge-find.py" --area estimacion --tipo lesson          # capa 1: aciertos compactos de un área (normalizada, sin acentos)
  python3 "$SHAREDKIT/knowledge-find.py" --tipo-tarea devops --contexto "<título de la tarea>" --iniciativa <slug>   # capa 1 ENRUTADA por área (la del brief)
  python3 "$SHAREDKIT/knowledge-find.py" --related ADR-010                        # capa 2: grafo curado (sucesión · misma iniciativa · misma área)
  python3 "$SHAREDKIT/knowledge-find.py" --show GOT-005                           # capa 3: la entrada completa — SOLO la que vayas a aplicar
  ```

  - **Distingue por `estado` antes de aplicar nada** (spec `knowledge-capture` §Bucle de lectura
    punto 5 y §Manejo de errores "Entrada dudosa o no verificada"): una entrada `estado: aceptada`
    ya pasó la revisión de dos lentes (o el usuario en la puerta) — aplícala como doctrina normal.
    Una entrada `estado: propuesta` **NO** está validada todavía: preséntala como propuesta
    pendiente ("hay una propuesta sin validar que dice X, tómala como indicio, no como regla
    cerrada"), no la apliques como si fuera doctrina vinculante, y dilo explícitamente si
    condiciona una decisión tuya. Una entrada `estado: obsoleta` no se aplica; sigue el enlace a
    la que la sustituye. `--related <ID>` la muestra como `sustituida por →`, y el `estado` va
    **delante** en cada acierto precisamente para que lo veas antes que el titular.
  - Aplica lo que digan (respetando la distinción de estado de arriba) salvo que el histórico más
    reciente (un ADR `obsoleta` con sucesor, o una lección contradicha por evidencia posterior) las
    anule explícitamente — gana lo más reciente, y la constitución del proyecto
    (`constitution-check.md`), si existe, prima sobre la memoria.
- **Si NO existe `docs/knowledge/`:** continúa sin ella — es **siempre activa pero degrada en
  silencio** (D3 de la iniciativa `knowledge-capture`): la carpeta nace en el primer registro
  (`knowledge-write.md`), nunca bloquea a un lector que llega antes de que exista. Si el script no
  está (instalación parcial), lee `README.md` y abre solo las filas cuya columna «Área» toque tu tarea.

**Reparto de qué lee cada agente** — la orden exacta, no una intención (evita que todos abran todo —
protege la inversión de `2026-08-10-token-diet`). `$SHAREDKIT` es el kit localizado arriba; sustituye
`<…>` por los datos de tu iniciativa/tarea; con 0 aciertos, sigue sin abrir nada:

| Agente | Ejecuta (capa 1) | Y abre con `--show <ID>` solo… |
|---|---|---|
| `evaluator` | `python3 "$SHAREDKIT/knowledge-find.py" --area estimacion --tipo lesson` (memoria del proyecto) **y** `python3 "$SHAREDKIT/knowledge-find.py" --doctrina --area estimacion --limit 0` (doctrina del plugin: las 9 lecciones `LES-001…009`, disponibles también sin `docs/knowledge/`; T-16) | las lecciones de estimación/calibración que condicionen ESTA estimación (`--doctrina --show <ID>` para las del plugin) |
| `planner` | `python3 "$SHAREDKIT/knowledge-find.py" --contexto "<título de la spec>" --iniciativa <slug>` y, además, `python3 "$SHAREDKIT/knowledge-find.py" --tipo adr --limit 0` | los ADR que acoten el diseño del plan y las lecciones de proceso del área |
| `architect` | `python3 "$SHAREDKIT/knowledge-find.py" --tipo adr --contexto "<título de la spec>"` | los ADR `aceptada` que acotan las opciones (uno vigente no se re-abre sin decirlo) |
| `implementer` | `python3 "$SHAREDKIT/knowledge-find.py" --tipo-tarea <Tipo de la T-XX> --contexto "<título de la T-XX>" --iniciativa <slug>` (con `subagentes: true` **ya viene en el brief**: sección «Memoria técnica del proyecto» de `task-brief.py`) | los ADR que restringen la implementación y los gotchas del área (trampas ya comprobadas) |
| `reviewer` | `python3 "$SHAREDKIT/knowledge-find.py" --tipo adr --tipo-tarea <Tipo> --contexto "<título de la T-XX>" --iniciativa <slug>` | el ADR `aceptada` que el diff parezca contradecir: si lo contradice, es un gap con su ID como evidencia |
| `qa` | `python3 "$SHAREDKIT/knowledge-find.py" --tipo gotcha --contexto "<título de la iniciativa>"` (con 0 aciertos, `--tipo gotcha --limit 0`: son pocos y baratos) | el gotcha que evite reabrir un flaky ya diagnosticado |
| `documenter` | `python3 "$SHAREDKIT/knowledge-find.py" --limit 0` (una línea por entrada del corpus: es quien indexa/deriva la documentación de producto) | lo que vaya a documentar |

**Journal de sesión (`docs/knowledge/journal/`, memoria EPISÓDICA — iniciativa `memory-health`).**
Es la bitácora cronológica que deja el hook `SessionEnd` (`agent-kits/shared/journal.py`): qué pasó en
la última sesión, qué ficheros se tocaron, qué tareas cambiaron de estado, qué quedó pendiente. No es
doctrina (no está curada ni validada) y NO sustituye a `adr/`/`gotchas/`/`lessons/`. `evaluator`,
`planner` y `architect` abren **solo la última entrada** (`journal.py latest --n 1`, o el fichero más
reciente de la carpeta) y **solo si su `iniciativa:` coincide con la iniciativa en la que trabajan** —
para retomar el hilo (pendientes, decisiones apuntadas), nunca para leer el histórico entero. Al
arrancar/retomar la sesión ya viene inyectada por `session-context.sh` — igual que los aciertos de
memoria del **área de la iniciativa activa** (bloque «Memoria técnica del área activa»); si los ves en
el contexto, no los repitas.

No leas por leer: si la consulta no devuelve ninguna entrada de tu área para esta tarea, sigue sin
abrir nada más — la progressive disclosure es la protección contra el coste de "leer memoria" en
cada invocación.
