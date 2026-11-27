<!-- Referencia privada de commands/dev-cycle.md (plugin-audit-2 T-16). El ritual de cierre se lee solo
     al llegar a la Fase 6. La tabla de transiciones se consulta en cada puerta de artefacto
     (go/no-go, OK del plan, cierre). -->

## Fase 6 — Sincronizar y cerrar

**Ritual de cierre de rama (obligatorio, en orden):**

1. **Verificación final sobre la rama**: suites y lint del proyecto en verde (las de verificación de fase, con el gate de cobertura si `dev.json` trae `tests.coberturaMinima` —P5 de `classic-flow.md` sin brief; sección «Cobertura» del brief con él—, una última vez sobre el estado final).
2. **Commits ordenados**: un commit lógico por tarea (`T-XX: …`), sin restos de instrumentación temporal (logs/asserts de diagnóstico fuera del diff — regla de `debug-root-cause`). Los hace el `implementer`, dueño único de los commits y de su procedimiento de selección exacta (su P4); aquí compruebas el orden, la puerta de alcance del ledger y que no queda nada de la iniciativa sin comitear. Tus propios artefactos (trazas de revisión, CHANGELOG) siguen ese mismo procedimiento. Detalle y límites: [selección de commits](../../../docs/COMMIT-SELECTION.md). Esto no autoriza push, merge, PR ni release por sí mismo.
3. **Estados del plan — los escribe el plugin (T-42)**: ANTES del resumen y del merge/PR, para que el ledger cerrado viaje en la rama (fix2). Con la verificación del paso 1 en verde (revisión sin gaps y qa verde por `qa-gate`), cierra el ledger con `python3 "$SHAREDKIT/roadmap-sync.py" docs/roadmap/<fecha>-<slug> --cerrar`: es la ÚNICA señal que pasa `tasks.md` a `completado` (el veredicto de la Fase 3 no lo cierra) y exige todas las tareas cerradas (exit 1 `open_tasks` si queda alguna); también pone al día la fila del índice. No los edites a mano. Comitea el `tasks.md` cerrado con el procedimiento del paso 2. Después, `roadmap-sync.py docs/roadmap/<fecha>-<slug> --check` → exit 0. Lo exigen `changelog-sync` y la retro. Si `ledger-lint.py` avisa del tamaño, `ledger-archive.py … --apply` antes de cerrar (ver «Ledger grande» en la Fase 3). La spec **todavía no**: pasa a `implementada` en el paso 9, solo con la puerta del paso 8 abierta.
4. **Resumen de merge/PR derivado del LEDGER** (no de memoria): título, qué se hizo tarea a tarea, criterios de aceptación cumplidos, veredicto de qa-gate y ruta de las evidencias. Es la descripción del PR o el mensaje del merge. Si el repo trae plantilla de PR (`pull_request_template.md`, en mayúsculas o minúsculas, en `.github/` o `docs/`, o la carpeta `.github/PULL_REQUEST_TEMPLATE/`), rellena SUS secciones con este resumen (N/A en las que no apliquen, sin borrarlas). Antes de crear el PR fija base y head explícitos (la base no se supone: `main` no siempre es la principal) y comprueba que la rama no tiene ya uno abierto (`gh pr list --head <rama> --state open`; sin `gh`, pregunta); si lo tiene, dilo y propón actualizar su descripción en vez de abrir otro.
5. **Integración según el flujo del repo**: merge directo o PR — si no está claro cuál usa el equipo, **pregunta**; no mergees por defecto.
6. **Limpieza**: rama integrada eliminada; worktrees retirados (`git worktree remove` + `prune`); marcadores de usage-meter sin huérfanos (`usage-meter.py status` limpio).
7. **Notas de cambios**: con el ledger ya en `completado`, invoca la skill **`changelog-sync`** (determinista, idempotente) para generar las entradas `[Unreleased]`/`[Sin publicar]` de esta iniciativa en ambos CHANGELOG, y afina la redacción sin ampliar alcance. El bullet sale del campo `- **Changelog**:` de cada tarea, así que **antes de invocarla comprueba que las tareas cerradas lo traen** (`changelog-sync.py --check` te lista las que no; sin campo el bullet degrada al título). No crea la sección de versión: eso es del release.
8. **Retro — PUERTA, no aviso (memory-retrieval T-17, spec CA-23).** Con el ledger ya en `completado`, ejecuta `/retro docs/roadmap/<fecha>-<slug>` (las causas de desviación las escribe quien las conoce: el usuario responde, tú registras; ahí también se muestran las candidatas a lección del journal) y después la puerta determinista `python3 "$SHAREDKIT/retro-gate.py" docs/roadmap/<fecha>-<slug> --sync` (mismo `$SHAREDKIT` que el resto del ciclo; con retro y fila, `--sync` aplica el cierre completo del paso 9 con `roadmap-sync.py --cerrar` —ledger incluido, aunque se olvidara el paso 3—; con tareas abiertas o sin campo `estado` en el ledger la puerta NO se abre y no escribe nada) → **exit 0 obligatorio**: `retro.md` con título y cuerpo, o frontmatter cerrado y cuerpo, más la fila de la iniciativa en `docs/roadmap/CALIBRATION.md`. Con exit 1 la iniciativa **no se declara cerrada** ni la spec pasa a `implementada`: el resumen final dice «cierre pendiente de retro» y qué falta (el script lo lista con el comando exacto). Sin `python3`, comprueba a mano los dos ficheros y dilo. Es el patrón de `qa-gate`/`ledger-lint`: un aviso que se puede ignorar se ignorará (`LES-012`).
9. **Cierre declarado**: solo con la puerta abierta, `retro-gate.py --sync` ya dejó el ledger y el plan `completado`, la spec `implementada` y la fila del índice en `cerrada` (tabla de abajo); compruébalo con `roadmap-sync.py docs/roadmap/<fecha>-<slug> --check` → exit 0 y da el resumen final. Si lo escribió tras el merge, comitea esos artefactos en la rama de integración. Con la puerta cerrada la spec se queda `aprobada` aunque el plan esté `completado` — es la señal visible (en `/roadmap-status`, en el índice) de que falta la retro.

La documentación puede proyectarse mediante el binding de documentación de `project-integrations.md`; el core no exige proveedor ni conexión. Cierra con un resumen: iniciativa, tareas completadas, estado de pruebas, coste medido (usage-meter), ruta de la doc y enlaces. La retro ya no es «siguiente paso natural»: es el paso 8 del ritual, y sin ella no hay paso 9 (la spec no pasa a `implementada`).

## Transiciones de estado (OBLIGATORIAS en cada fase)
Los artefactos nacen en `borrador`. En **cada fase/puerta** que se supera, actualiza su estado
(frontmatter + cabecera) al que toque; **no dejes nada en `borrador`** al avanzar. Vocabularios:
spec = `borrador · aprobada · implementada · obsoleta`; evaluación/plan/tareas = `borrador ·
en-progreso · en-revision · completado · cancelado`; design = `borrador · aprobado · obsoleto`.

> **Vía rápida:** aplica la fila de tareas al `tasks.md` ligero; las demás puertas de estado de artefactos corresponden al flujo completo.
>
> **`design.md` (opcional, agente `architect`):** vocabulario propio `borrador · aprobado · obsoleto`. Solo existe si se hizo el paso de diseño; la columna queda `—` si no.

| Momento | spec | evaluación | design (opcional) | plan / tasks |
|---|---|---|---|---|
| Tras evaluar (Fase 1) | borrador | `en-revision` | — | — |
| Puerta **go** | `aprobada` | `completado` | — | — |
| Puerta **no-go** | (obsoleta si se descarta) | `cancelado` | — | — |
| Diseño presentado (Fase 2-a) | aprobada | completado | `borrador` (opciones abiertas) | — |
| Opción validada por el usuario | aprobada | completado | `aprobado` | — |
| Plan creado (Fase 2-b) | aprobada | completado | aprobado (`plan:` relleno) | `borrador` |
| Puerta OK del plan → arranca impl. | aprobada | completado | aprobado | `en-progreso` (plan y fase activa) |
| Implementación y revisión (Fase 3) | aprobada | completado | aprobado | `start`/despacho → `en-progreso`; `close`/`review` → `en-revision`; `verdict` limpio → `completado`, con gaps → `en-progreso`; fase y resumen derivados (el ledger sigue `en-progreso` hasta `--cerrar`) |
| qa en rojo | aprobada | completado | aprobado | tarea/plan → `en-progreso` (reabrir) |
| Re-diseño (se descarta la opción) | aprobada | completado | `obsoleto` → nuevo `design.md` `borrador` | plan `en-revision` |
| Cierre (revisión sin gaps + qa verde → `--cerrar`; documentado + retro-gate exit 0) | `implementada` | completado | aprobado | ledger y plan `completado` |
| Cancelación en cualquier punto | (obsoleta) | `cancelado` | `obsoleto` | `cancelado` |

Las transiciones de esta tabla **las aplica la herramienta, no el orquestador a mano** (T-42): las de tarea,
`ledger-write.py` (fase y resumen incluidos); las de la iniciativa, `roadmap-sync.py`: spec y evaluación
SOLO en la puerta go/no-go (`roadmap-sync.py gate <carpeta> --decision go|no-go`, la de `/pm-cycle` y la de
la Fase 1 de `/dev-cycle`); ledger `completado` con `--cerrar` en el paso 3 de la Fase 6 o, si se olvidó, con la
retro hecha (`retro-gate.py --sync`; `--check` lo cuenta como desfase `cierre-olvidado`); con la puerta
de retro abierta, plan `completado` y spec `implementada` (`retro-gate.py --sync`); y la fila del índice
(dueño único), que refresca también `verdict`. Nunca rebaja un estado —lo adelantado lo reporta— salvo un
ledger `completado` con una tarea reabierta (qa en rojo) o una tarea nueva en `borrador`, que vuelve a
`en-progreso`: hay trabajo abierto y esa tarea es la evidencia.

**El orquestador** valida criterios y evidencias, reabre el rojo de QA con `ledger-write.py state` y decide
las puertas que son juicio (OK del plan → plan `en-progreso`, re-diseño y cancelación); `roadmap-sync.py
docs/roadmap --check` (exit 1 = desfase) le dice si algo quedó atrás.
