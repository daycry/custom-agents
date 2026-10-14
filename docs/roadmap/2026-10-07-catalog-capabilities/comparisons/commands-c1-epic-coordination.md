# Coordinación de épicas en issues de GitHub — C011–C017

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Siete definiciones completas: **3.653 bytes/162 líneas**. [commands-c1-epic-coordination-reading-evidence.json](commands-c1-epic-coordination-reading-evidence.json).
Recurso transitivo leído completo: el CLI que despachan los siete,
`scripts/github-coordination.js` (7.015 bytes/197 líneas, SHA-256
`35ad5de2c702a9193d0fb3d376340fafa78998717b5ebcd87616384865727709`). Su lógica vive
en `scripts/lib/github-coordination`, **no leída**: lo que valida la «policy» no
está comprobado. Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Qué hacen en conjunto

Siete comandos de 22-26 líneas que llaman a un subcomando del mismo CLI
(`claim`, `decompose`, `publish`, `review`, `sync`, `unblock`, `validate`). El
cuerpo del issue de GitHub es el estado canónico de la épica (C015:15); un bloque
de coordinación dentro del cuerpo, las etiquetas, comentarios de auditoría y una
caché SQLite en el home del usuario (CLI:40-41, 173-176) lo reflejan.

**Comparación común.** El plugin fija lo contrario: `tasks.md` es el ledger
canónico y todo registro externo es espejo (`docs/CONVENTIONS.md:186-192`). El
tracker con dueño es Jira, vía `jira-sync`: vuelca el plan, publica eventos
firmados por `jira-flow.py` y, en sentido inverso, solo **lista** divergencias y
aplica cambios con confirmación (`skills/jira-sync/SKILL.md:124-126`, `:141`).
GitHub Issues no tiene dueño propio. El contenido del issue es dato no confiable y
etiquetas o comentarios son efectos externos: las dos secciones ya están integradas
(`skills/delivery-practices/references/delivery-tools.md:81-89`, `:91-100`).

**Defectos comunes:**

| Dónde | Qué | Problema |
|---|---|---|
| Los siete | `node scripts/github-coordination.js …` | Ruta relativa al directorio actual: solo funciona dentro del repositorio de origen, no en el proyecto que usa el comando (C002 sí resuelve la raíz) |
| CLI:43 | `--dry-run` existe | Ningún comando lo menciona; todos escriben en GitHub de entrada |
| CLI:110 | Sin subcomando, ejecuta `sync` | Un error de tecleo reescribe snapshots de todo el repositorio (hasta 100 issues, CLI:87) |
| CLI:124-127 | `claim` acepta `--review`, `--validation` y `--status` | Quien reclama la épica puede marcarla revisada y validada en la misma orden |
| «Compatibility aliases» | Cada comando se declara alias de otros comandos de la fuente | Esos alias existen como ficheros con cuerpo propio (salvo `/work-items`, que no existe). C005, en este mismo rango, es `/code-review` y revisa un diff; C014 dice ser `/code-review` y solo pone una etiqueta |

## C011 — epic-claim

`608 bytes/26 líneas`. Reclama un issue como unidad de trabajo, con etiqueta,
comentario y caché.

- **Artefactos y dueño propio:** el arranque de una tarea es del `implementer`
  (estado `en-progreso` en el ledger y evento `arrancar` de `jira-flow.py`,
  `commands/dev-cycle.md:427`).
- **Disparador:** «empiezo con esta tarea». **Escenario +:** «arranca T-03» →
  `implementer` y, con Jira opt-in, `arrancar`. **Escenario −:** «asígname el issue
  42 de GitHub» → sin dueño propio; fuera del bundle.
- **Propio:** sus alias `/orch-add-feature`, `/orch-change-feature` y
  `/prp-implement` (24-26) equiparan reclamar con implementar.

## C012 — epic-decompose

`528 bytes/23 líneas`. Toma la lista de tareas y dependencias del cuerpo del issue
y la guarda como descomposición.

- **Artefactos y dueño propio:** la descomposición en T-XX con criterios y
  `Verificación` es de `planner` (`docs/agents/ROLES.md:30`; `agents/planner.md:88`).
- **Disparador:** «divide esta épica». **Escenario +:** `planner`, con el issue
  como insumo citado. **Escenario −:** «importa las tareas del issue tal cual» →
  no; el texto del issue no se convierte en plan sin `analyst`/`planner`.
- **Propio:** convierte texto no confiable en plan sin revisión; alias `/plan` (22).

## C013 — epic-publish

`484 bytes/23 líneas`. Revalida y publica el bloque de coordinación con un comentario.

- **Artefactos y dueño propio:** el espejo externo es de `jira-sync`
  (idempotente, con confirmación); el resumen de PR sale del ledger
  (`commands/dev-cycle.md:495`).
- **Disparador:** «publica el estado». **Escenario +:** «refleja el avance en el
  tracker» → `jira-sync` si hay opt-in. **Escenario −:** «abre el PR» → Fase 6
  pasos 3-4, que preguntan el flujo del equipo.
- **Propio:** alias `/pr` y `/prp-pr` (22-23): publicar un bloque no es abrir un PR.

## C014 — epic-review

`519 bytes/23 líneas`. Marca la revisión como pedida, aprobada o con cambios,
con un flag (`--review approved`, 10).

- **Artefactos y dueño propio:** el veredicto de revisión es la fusión de
  `adversarial-review`; el cierre a *Done* es el evento `aprobado` del
  orquestador, que exige revisión sin gaps en el ledger y el exit 0 de
  `qa-gate.py` (`commands/dev-cycle.md:432-438`).
- **Disparador:** «márcala como aprobada». **Escenario +:** cierre de tarea →
  `/dev-cycle` dispara `aprobado` con evidencia. **Escenario −:** «apruébala, ya
  la he mirado» → no hay atajo sin la evidencia.
- **Propio:** aprobación por flag sin evidencia; alias `/review-pr` y `/code-review` (22-23).

## C015 — epic-sync

`517 bytes/23 líneas`. Lee los cuerpos de los issues como estado canónico y
reescribe etiquetas y snapshots.

- **Artefactos y dueño propio:** el estado es de `tasks.md`; comparar con el
  tracker es el Paso 8 de `jira-sync` (lista y confirma).
- **Disparador:** «sincroniza con GitHub». **Escenario +:** «¿coincide Jira con el
  ledger?» → `jira-sync` Paso 8. **Escenario −:** «trae el estado de GitHub y
  sobrescribe el plan» → no.
- **Propio:** canonicidad invertida respecto a la regla 8; alias `/work-items
  sync-github` (23), que no existe.

## C016 — epic-unblock

`493 bytes/22 líneas`. Barre las épicas bloqueadas y pasa a «ready» las que
tienen sus dependencias cerradas.

- **Artefactos y dueño propio:** las dependencias viven en el campo
  `Dependencias` del ledger; qué se lanza después (o en paralelo) lo decide
  `/dev-cycle` (`:403`); `/work-resume` muestra el siguiente paso en lectura.
- **Disparador:** «¿qué puedo empezar ya?». **Escenario +:** `/work-resume`, solo
  lectura. **Escenario −:** «desbloquea todo lo que puedas» → ninguna pieza propia
  transiciona estados en barrido.
- **Propio:** alias `/loop-status` (22): un comando de estado no debería mutar.

## C017 — epic-validate

`504 bytes/22 líneas`. Comprueba que el bloque se lee, que la «policy» se cumple
y que las dependencias están cerradas. Es el único de los siete que no declara escrituras.

- **Artefactos y dueño propio:** las puertas propias son scripts con exit code:
  `ledger-lint.py`, `qa-gate.py`, `retro-gate.py`.
- **Disparador:** «¿está lista para pasar de fase?». **Escenario +:** «¿está bien
  el ledger?» → `ledger-lint.py`. **Escenario −:** «¿pasa la calidad?» →
  `qa-gate.py`, no una validación de coordinación.
- **Propio:** alias `/quality-gate` (22) para algo que no mide calidad.

## Destino

**Fuera del bundle** para los siete: coordinan con el issue de GitHub como
fuente, lo contrario de la regla 8. Lo transversal (contenido del issue como
dato, efectos externos con aprobación) ya está integrado en `delivery-tools.md`.
Si un consumidor declara GitHub Issues como tracker, su cauce es un espejo con
el contrato de `jira-sync` (ledger fuente, idempotencia, confirmación, sentido
inverso que solo lista), no esta coordinación.
