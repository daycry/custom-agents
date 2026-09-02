---
id: LES-010
tipo: leccion
area: Proceso / revisión adversarial
estado: aceptada (validada: revisión de dos lentes, 2026-09-02, intento 2)
fuente: docs/roadmap/2026-09-02-adversarial-review/tasks.md (decisión del usuario) + tablas de revisión de 5 ledgers
---

## dev-cycle

- **Un mecanismo de proceso que caza críticos de forma repetida deja de ser "un paso del ciclo" y
  pasa a ser una capacidad reutilizable (skill).** La revisión adversarial de dos lentes nació
  incrustada en `commands/dev-cycle.md` Fase 3 y solo corría dentro del ciclo; en cinco ledgers
  consecutivos fue la única puerta que vio defectos que **ninguna suite en verde habría detectado**,
  así que su tasa de captura justificó extraerla a `skills/adversarial-review/` (fuente única del
  método, invocable desde `/dev-cycle`, `quick-implement` y a demanda sobre una rama sin ledger) y
  añadirle una tercera lente de seguridad **condicional** decidida por script
  (`review-lens-select.py`). Evidencia, cifras literales de los ledgers/retros:
  1. **2026-08-20 `confluence-policy`** — 3 intentos, **11 hallazgos**: **2 críticos** (el README
     staged pisado por la plantilla del marcador, con riesgo de pérdida del canónico vía pull; un
     `rmtree` sin salvaguarda que podía borrar `docs/` entero), 1 fixture no versionada por un
     patrón de `.gitignore` (suite rota en clon limpio, invisible en local) y 8 gaps más. «Ninguna
     suite en verde habría detectado los dos críticos: solo el ataque adversarial los reprodujo».
     Coste medido: ≈230k tokens en las dos lentes del intento 1 frente a 363k del implementer.
     → `GOT-002`, `GOT-003`.
  2. **2026-08-20 `knowledge-capture`** — 3 intentos, **12 gaps** en el 1.º (5 Important, 7 Minor)
     y **5 residuales** en el 3.º (1 Important, 4 Minor). El mayor fue un hueco de **diseño**, no de
     código: las entradas `propuesta` se aplicaban como doctrina sin circuito de promoción
     `propuesta`→`aceptada` — cerrado con dos promotores explícitos que hoy usan `knowledge-write.md`
     y `/retro`.
  3. **2026-08-20 `knowledge-split`** (vía rápida) — 2 intentos: 3 ficheros nacían del mismo heading
     al partir las lecciones (enmendado con sufijo `— N/3`) y un glob muerto derivado del rename
     (`lessons/evaluator-*` en `docs/CONVENTIONS.md`/EN casaba 0 ficheros).
  4. **2026-09-02 `live-visibility`** (vía rápida) — intento 1: **8 gaps corregidos**, 3 aceptados
     como deuda, 0 rebatidos: BOM UTF-8 que hacía invisible la iniciativa, `set -u` + `HOME` sin
     definir abortando los hooks, horas `(estimado)` sumadas como «IA real», rutas Windows sin casar
     en el `case` de los hooks…
  5. **2026-09-02 `deterministic-guardrails`** (vía rápida) — intento 1: **4 gaps** (2 Important,
     2 Minor), entre ellos tres **evasiones del guardrail git** (`git push origin +main`,
     `sh -c "git push --force"`, `rm -rf .`) y una precarga `skills:` de ≈15k tokens por arranque;
     intento 2: 1 regresión introducida por la propia corrección (recursión demasiado ancha en
     `check_git`). Todos reproducidos antes de corregir.

  Patrón común: los gaps aparecen en **lo que el implementador no puede ver desde dentro**
  (evasiones, entornos ajenos —BOM, Windows, clon limpio—, huecos de diseño), y el 2.º/3.º intento
  encuentra regresiones de la corrección del 1.º — por eso el bucle acotado y el traspaso de la
  tabla entre intentos forman parte del método. La lente C se añade **condicional** porque un tercer
  revisor fijo sería coste sin captura en iniciativas de prosa y scripts: `review-lens-select.py`
  aplicado a posteriori sobre los dos rangos disponibles en git da `false` para
  `deterministic-guardrails` (28 ficheros, `4e94deb..f627bda`) y `true` para `live-visibility` solo
  por la ruta `hooks/session-context.sh` (patrón `session` — la heurística es conservadora: un falso
  positivo cuesta un revisor, un falso negativo cuesta un agujero). — *Fuente:* [`2026-08-20-confluence-policy/retro.md`](../../roadmap/2026-08-20-confluence-policy/retro.md#aprendizajes),
  [`2026-08-20-knowledge-capture/tasks.md`](../../roadmap/2026-08-20-knowledge-capture/tasks.md),
  [`2026-08-20-knowledge-split/tasks.md`](../../roadmap/2026-08-20-knowledge-split/tasks.md),
  [`2026-09-02-live-visibility/tasks.md`](../../roadmap/2026-09-02-live-visibility/tasks.md),
  [`2026-09-02-deterministic-guardrails/tasks.md`](../../roadmap/2026-09-02-deterministic-guardrails/tasks.md).
  `estado: propuesta`.
