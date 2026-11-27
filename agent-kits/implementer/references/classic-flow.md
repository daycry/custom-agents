# Implementer — flujo clásico (sin brief)

Léelo solo si trabajas **sin brief** de `task-brief.py`: invocación directa del implementer,
despacho de `/dev-cycle` con `subagentes: false` o fallback cuando un despacho falla dos veces. Con brief, el brief y el núcleo de
`agents/implementer.md` bastan. El núcleo sigue mandando (guardrails, ledger, reglas por tarea,
commits y DoD); aquí está lo que el orquestador hace por ti cuando hay brief. `$SHAREDKIT` y
`$UTSKILL` salen de la receta del núcleo.

## Flujo (6 pasos)

**P1. Contexto.** Localiza la iniciativa; lee `improvement-plan.md` (arquitectura, archivos, criterios) y `tasks.md` (fases y tareas T-XX); en la vía rápida, solo el `tasks.md` ligero. Explora el repo (Read/Grep/Glob) para ubicar los módulos reales a tocar.

- **Constitución del proyecto (opt-in).** Si existe `docs/CONSTITUTION.md`, léela, respétala y cita el principio cuando condicione una decisión; si la tarea contradice un principio explícito, dilo antes de ejecutar. Si no existe, continúa (nunca bloquea). Esta línea es la regla entera: no abras `constitution-check.md` (es de la Lente A).
- **Memoria técnica del proyecto — lectura (siempre activa, D3).** Antes de tocar código (P1), si existe `docs/knowledge/`, ejecuta `python3 "$SHAREDKIT/knowledge-find.py" --tipo-tarea <Tipo> --contexto "<título de la T-XX>" --iniciativa <slug>` (con `subagentes: true` los aciertos ya vienen en el brief). Solo con aciertos lee `"$SHAREDKIT/knowledge-check.md"` y `--show <ID>` los ADR que restrinjan la implementación y los gotchas del área: respeta los ADR y lecciones aplicables. Sin aciertos o sin `docs/knowledge/`, sigue sin abrir nada. Sin script: lee `README.md`, no bloquea.

**P1-bis. Disciplina de desarrollo (config opt-in).** Lee `.claude/dev.json` si existe (lo crea `/setup`): `{tdd, worktree, subagentes}` — los tres con default `false`; fichero ausente o corrupto = defaults + aviso (comportamiento clásico, nunca bloquea). `subagentes` lo gestiona el orquestador `/dev-cycle` (con `subagentes: true`, las tareas las despacha él a subagentes frescos con brief de `task-brief.py`, y tú solo entras como fallback cuando un despacho falla dos veces); `tdd` y `worktree` los aplicas tú (P2 y P3). Con `tdd: false` o sin config, flujo clásico sin evidencia `RED:`.

**P2. Rama (o worktree).** Asegura la rama de trabajo (`feature/<slug>` u otra indicada). **Con `worktree: true`** en `.claude/dev.json`: crea un worktree aislado — `git worktree add ../<repo>-<slug> -b feature/<slug>` — y trabaja AHÍ toda la iniciativa (el árbol principal queda intacto). La **integración y la limpieza** (merge/PR, `git worktree remove`) NO las haces tú aquí: las dirige el **ritual de cierre** de `/dev-cycle` (Fase 6), tras qa en verde y con su verificación final — tú solo dejas la rama lista (ver P6). Si no hay git o la versión no soporta worktrees, **avisa y degrada a rama normal** (nunca bloquees). Confírmalo.

**P3. Ejecución fase a fase.** Recorre las fases en orden; dentro de cada fase, las tareas T-XX, cada una con las reglas «Por tarea» del núcleo y además:
- **Mide la tarea (usage-meter).** Al arrancarla: `python3 "$SHAREDKIT/usage-meter.py" start --artefacto "<slug>/T-XX"`; al dejarla lista para revisión, `close` con la misma clave. Fija `--runtime claude|codex|opencode` en ambos traspasos según tu runtime. Escribe las **horas-IA medidas** del JSON como tiempo IA `real` en el ledger, marcadas `(medido)` para la imputación externa. Si el meter degrada, registra la estimación a juicio como `(estimado)` y sigue (nunca bloquea). Cierra el marcador ANTES de la revisión. Con brief, lo coordina `/dev-cycle` por despacho.
- Tras `usage-meter.py start`, resuelve `task.started` por `project-integrations.md`. La proyección externa no cambia el ledger.
- **Proyección externa opcional:** resuelve `task.implemented` por `project-integrations.md` con evidencia, archivos y mediciones reales. El adaptador prepara comentarios/imputaciones según su contrato; no calcules horas fuera de su dueño. Este evento nunca cierra la tarea remota: `task.done` pertenece al orquestador tras revisión sin gaps y QA verde.
- **Respeta la parada por jornada:** si al imputar se alcanza el tope diario y la preferencia (o la elección del usuario) es **parar**, detén la implementación tras la tarea actual e informa de lo pendiente; no sigas abriendo tareas. Con **banco** o **seguir**, continúa normalmente.
- El writer actualiza la fase y la **tabla de resumen de progreso** (completadas/total, %) de `tasks.md`. **La revisión limpia registra `completado` y `- **Cerrada**: AAAA-MM-DD`**: el burndown usa esa fecha y `ledger-lint` comprueba su formato y que no sea anterior a la creación del ledger.

**P4-bis. Rama compartida.**
- **Traer la rama base:** en una rama ya compartida (empujada o con PR) integra con `merge`; `rebase` solo en una rama tuya que aún no has empujado. Una rama empujada no se reescribe: cualquier push forzado (también `--force-with-lease`) lo bloquea el guardarraíl. Sin `reset --hard` para «limpiar».
- **Conflicto:** lee las dos versiones y el commit que introdujo cada una (`git log -p --merge -- <fichero>`); no elijas `--ours`/`--theirs` en bloque. Tras resolver, repite la `Verificación` de las tareas afectadas antes de cerrar el merge; si la resolución cambia comportamiento de otra tarea, anótalo en el ledger.

**P5. Verificación de fase.** Al cerrar una fase, ejecuta las comprobaciones disponibles (tests, build). Deja constancia del resultado en `tasks.md`. **Gate de cobertura (opt-in, skill `unit-tests`).** Si `.claude/dev.json` trae `"tests": {"coberturaMinima": N}`, ejecuta `python3 "$UTSKILL/scripts/coverage-gate.py" . --changed-only --min N` (`$UTSKILL`, de la receta del kit del núcleo) sobre los ficheros de código de la fase; exit 1 (bajo el umbral) es un gap de verificación como cualquier otro — la fase no se cierra hasta subir la cobertura o justificar la excepción en `tasks.md`; exit 2 (sin herramienta/stack) degrada a aviso y no bloquea. Sin esa clave en `dev.json`, no apliques el gate (como mucho, infórmalo si la herramienta está disponible).

**P5-bis. Documentación al CERRAR CADA FASE.** Después de verificar la fase, resuelve `phase.completed` por `project-integrations.md` para las rutas modificadas. No publiques por tarea ni dupliques una revisión ya confirmada. Excluye por defecto testing, security-scan y conocimiento sin aprobar; la política del adaptador puede ser más restrictiva.

**P6. Cierre + handoff a qa.** Cuando el plan (o el alcance pedido) esté implementado, resume: qué tareas se completaron, qué quedó pendiente/bloqueado, y la rama. **Handoff a `qa`** para las pruebas E2E. Recuerda: `documenter` documentará **después**, solo si `qa` queda en verde (no lo llames tú directamente). El **ritual de cierre de rama** (verificación final, commits ordenados, resumen de PR desde el ledger, integración, limpieza de rama/worktree y marcadores) lo dirige `/dev-cycle` en su Fase 6 — deja la rama lista para ese ritual: commits por tarea y sin instrumentación temporal.

**Salida a la cadena.** Tu mensaje final sigue la **disciplina de salida** compartida (`"$SHAREDKIT/output-discipline.md"`): ≤ ~12 líneas — qué tareas cerraste, evidencia de la comprobación, estado del ledger, handoff a qa. El detalle vive en `tasks.md`. Fallback: datos, no recap de pasos.
