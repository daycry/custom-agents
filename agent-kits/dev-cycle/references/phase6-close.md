<!-- Referencia privada de commands/dev-cycle.md (plugin-audit-2 T-16). Léela solo al llegar a la Fase 6
     o al aplicar una puerta de estado de artefacto (go/no-go, OK del plan, cierre). -->

## Fase 6 — Sincronizar y cerrar

**Ritual de cierre de rama (obligatorio, en orden):**

1. **Verificación final sobre la rama**: suites y lint del proyecto en verde (las mismas comprobaciones de P5 del implementer, una última vez sobre el estado final).
2. **Commits ordenados**: un commit lógico por tarea (`T-XX: …`), sin restos de instrumentación temporal (logs/asserts de diagnóstico fuera del diff — regla de `debug-root-cause`). Los hace el `implementer`, dueño único de los commits y de su procedimiento de selección exacta (su P4); aquí compruebas el orden, la puerta de alcance del ledger y que no queda nada de la iniciativa sin comitear. Tus propios artefactos (trazas de revisión, CHANGELOG) siguen ese mismo procedimiento. Detalle y límites: [selección de commits](../docs/COMMIT-SELECTION.md). Esto no autoriza push, merge, PR ni release por sí mismo.
3. **Resumen de merge/PR derivado del LEDGER** (no de memoria): título, qué se hizo tarea a tarea, criterios de aceptación cumplidos, veredicto de qa-gate y ruta de las evidencias. Es la descripción del PR o el mensaje del merge. Si el repo trae plantilla de PR (`pull_request_template.md`, en mayúsculas o minúsculas, en `.github/` o `docs/`, o la carpeta `.github/PULL_REQUEST_TEMPLATE/`), rellena SUS secciones con este resumen (N/A en las que no apliquen, sin borrarlas). Antes de crear el PR fija base y head explícitos (la base no se supone: `main` no siempre es la principal) y comprueba que la rama no tiene ya uno abierto (`gh pr list --head <rama> --state open`; sin `gh`, pregunta); si lo tiene, dilo y propón actualizar su descripción en vez de abrir otro.
4. **Integración según el flujo del repo**: merge directo o PR — si no está claro cuál usa el equipo, **pregunta**; no mergees por defecto.
5. **Limpieza**: rama integrada eliminada; worktrees retirados (`git worktree remove` + `prune`); marcadores de usage-meter sin huérfanos (`usage-meter.py status` limpio).
6. **Estados del plan**: plan/tasks → `completado` (lo exigen `changelog-sync` y la retro) y fila del índice del roadmap al día con ese estado. Si `ledger-lint.py` avisa del tamaño, `ledger-archive.py … --apply` antes de cerrar (ver «Ledger grande» en la Fase 3). La spec **todavía no**: pasa a `implementada` en el paso 9, solo con la puerta del paso 8 abierta.
7. **Notas de cambios**: con el ledger ya en `completado`, invoca la skill **`changelog-sync`** (determinista, idempotente) para generar las entradas `[Unreleased]`/`[Sin publicar]` de esta iniciativa en ambos CHANGELOG, y afina la redacción sin ampliar alcance. El bullet sale del campo `- **Changelog**:` de cada tarea, así que **antes de invocarla comprueba que las tareas cerradas lo traen** (`changelog-sync.py --check` te lista las que no; sin campo el bullet degrada al título). No crea la sección de versión: eso es del release.
8. **Retro — PUERTA, no aviso (memory-retrieval T-17, spec CA-23).** Con el ledger ya en `completado`, ejecuta `/retro docs/roadmap/<fecha>-<slug>` (las causas de desviación las escribe quien las conoce: el usuario responde, tú registras; ahí también se muestran las candidatas a lección del journal) y después la puerta determinista `python3 "$SHAREDKIT/retro-gate.py" docs/roadmap/<fecha>-<slug>` (mismo `$SHAREDKIT` que el resto del ciclo) → **exit 0 obligatorio**: `retro.md` con título y cuerpo, o frontmatter cerrado y cuerpo, más la fila de la iniciativa en `docs/roadmap/CALIBRATION.md`. Con exit 1 la iniciativa **no se declara cerrada** ni la spec pasa a `implementada`: el resumen final dice «cierre pendiente de retro» y qué falta (el script lo lista con el comando exacto). Sin `python3`, comprueba a mano los dos ficheros y dilo. Es el patrón de `qa-gate`/`ledger-lint`: un aviso que se puede ignorar se ignorará (`LES-012`).
9. **Cierre declarado**: solo con la puerta abierta, spec → `implementada` (tabla de abajo) y el resumen final. Con la puerta cerrada la spec se queda `aprobada` aunque el plan esté `completado` — es la señal visible (en `/roadmap-status`, en el índice) de que falta la retro.

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
| Implementación y revisión (Fase 3) | aprobada | completado | aprobado | `start`/despacho → `en-progreso`; `close`/`review` → `en-revision`; `verdict` limpio → `completado`, con gaps → `en-progreso`; fase y resumen derivados |
| qa en rojo | aprobada | completado | aprobado | tarea/plan → `en-progreso` (reabrir) |
| Re-diseño (se descarta la opción) | aprobada | completado | `obsoleto` → nuevo `design.md` `borrador` | plan `en-revision` |
| Cierre (revisión sin gaps + qa verde + documentado + retro-gate exit 0) | `implementada` | completado | aprobado | plan `completado` |
| Cancelación en cualquier punto | (obsoleta) | `cancelado` | `obsoleto` | `cancelado` |

Aplica las transiciones de artefactos **en el mismo paso** que su puerta; el writer mantiene fase y resumen.

**El plugin aplica las transiciones de tarea de implementación y revisión.** El orquestador valida
criterios y evidencias, reabre el rojo de QA con `ledger-write.py state` y aplica las puertas
de los artefactos (go/no-go, OK del plan y cierre).
