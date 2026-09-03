# jira-sync — comentarios firmados de revisión y qa, por intento (Paso 7)

> Referencia de la skill `jira-sync`. Léela **solo** cuando dispares un evento de `reviewer`
> (`revision` · `gaps`) o de `qa` (`qa-verde` · `qa-rojo`). Se disparan **por intento** — no una sola
> vez al cerrar. Tres de los cuatro son comentario-only; la excepción es **`gaps`, que además
> REABRE el issue** (transición a la categoría `indeterminate`, destino lógico `reabrir`): si la
> tarea vuelve a `en-progreso` en el ledger, el tablero tiene que contarlo igual (T-fix1).

## `revision` / `gaps` — el `reviewer`, tras CADA intento del bucle de dos lentes

El agente **revisor** (revisión adversarial de dos lentes de `/dev-cycle`, bucle acotado a 3
intentos con `implementer`) escribe, tras CADA intento, la sección `## Revisión de dos lentes —
intento N` en `tasks.md` (tabla `# · Grado · Gap · Tarea · Corrección · Evidencia`, o "sin gaps").
Este paso publica ESE intento en Jira — no espera al cierre del bucle:

```bash
JF="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/jira-sync/scripts/jira-flow.py' 2>/dev/null | head -1)"
# el propio script decide si el intento N tuvo gaps para esa tarea y exige el --event que casa
# (exit 2 si pides `gaps` sin gaps reales, o `revision` habiendo gaps — así no puedes publicar el
# evento equivocado). `--intento N` es OBLIGATORIO en estos dos eventos: elige la sección del ledger
# que se publica y el pie «intento N+1 de 3» del comentario, así que sin él → exit 2 (antes caía a 1
# en silencio y publicaba los gaps del intento 1 con el pie del 2, T-fix1):
python3 "$JF" plan --ledger tasks.md --event revision --actor reviewer --task T-08 --intento 1 --json
python3 "$JF" plan --ledger tasks.md --event gaps     --actor reviewer --task T-08 --intento 1 --json
```

1. **Localiza la plantilla fija**: `jira-flow.py` ya trae el comentario renderizado (firmado, `> 🤖
   **[custom-agents · reviewer]** · revisor · <fecha>`, etiqueta `ca-reviewer`) contra
   `assets/comment-revision-aprobada.md` (sin gaps) o `assets/comment-revision-gaps.md` (con la
   tabla de gaps de ESE intento, filtrada a las tareas pedidas) — nunca prosa libre.
2. **Publica el comentario** con `addCommentToJiraIssue`, con la **granularidad del volcado**:
   **[modo tarea]** el issue de cada `T-XX`; **[modo fase]** usa `--batch T-08,T-09,…` para un único
   comentario en el issue de la fase con todas las tareas revisadas en ese intento.
3. **Aviso al `implementer` (si hay gaps): NO es por Jira.** El evento `gaps` de `jira-flow.py`
   **no** notifica al implementador — eso lo hace, por el lado del ledger, la inyección de gaps
   pendientes de `agent-kits/shared/task-brief.py` (el subagente de corrección la ve al arrancar).
   El comentario en Jira es solo el espejo para el equipo/PM.
4. **Imputa el worklog de revisión POR INTENTO**, si tienes las horas de ESE intento (si no las
   pasas, `jira-flow.py` avisa y **solo** publica el comentario — nunca bloquea). El propio script
   evita duplicar: **una pasada de revisión son UNAS horas, cubra una tarea o varias.**
   ```bash
   # [modo tarea] una tarea → una entrada de worklog normal, bajo su propia T-XX:
   python3 "$JF" plan --ledger tasks.md --event gaps --actor reviewer --task T-08 --intento 1 \
       --ia-real 0.4 --sup-real 0.1 --json
   # [modo fase / --batch] varias tareas en la MISMA pasada → jira-flow.py genera UNA sola entrada
   # con una clave sintética rev-<T-XX>-<T-YY>-… (issue destino = el de la fase) — NUNCA una por
   # tarea, o se contaría la misma hora dos veces:
   python3 "$JF" plan --ledger tasks.md --event gaps --actor reviewer --task T-08,T-09 --batch \
       --intento 1 --ia-real 0.4 --json
   ```
   Ejecuta el comando de `worklog.py` que trae el plan (`ops[].comando`), con `--apply` tras publicar
   el comentario en Jira. Cada pasada del bucle es su propia entrada de worklog (con su duración y su
   fecha en Jira); el script acumula el total en `worklogRevision` (aparte de `worklogImpl`) y
   registra `reviewAttempts: [{intento, fecha, horas}]` para `/retro`. La clave sintética evita pisar
   el registro de una `T-XX` real. Las **correcciones** que hace el `implementer` durante el bucle son
   tiempo de **implementación** (`--kind implementacion`, la de por defecto en el evento
   `implementado`), no `[revisión]`.
5. **Idempotencia: la lleva el script.** `jira-flow.py` anota cada plan con `ops` en
   `.claude/jira-state.json` bajo `flow["<issue>|<evento>|<tareas>|<intento>"]`, así que reejecutar
   `/dev-cycle` sobre un intento ya publicado devuelve `ops: []` + `yaRealizado: true` (exit 0) en
   vez de un segundo comentario y un segundo worklog; `--force` lo repite a propósito. El campo
   `reviewComentado` sigue siendo el resumen legible por tarea/fase (último intento publicado), pero
   ya no eres tú quien tiene que consultarlo para no duplicar.

## `qa-verde` / `qa-rojo` — `qa`, tras CADA intento de verificación

`qa` produce un veredicto (verde/rojo) con evidencias (`docs/roadmap/<slug>/testing/` u otra ruta).
Publícalo como comentario, también por intento:

```bash
python3 "$JF" plan --ledger tasks.md --event qa-verde --actor qa --task T-08 --intento 1 \
    --resumen "3/3 casos verdes; sin regresiones" --evidencia "docs/roadmap/<slug>/testing/" --json
python3 "$JF" plan --ledger tasks.md --event qa-rojo  --actor qa --task T-08 --intento 1 \
    --resumen "2 casos rojos: …" --evidencia "docs/roadmap/<slug>/testing/" --json
```

Sin transición ni worklog (el tiempo de `qa` no se imputa aparte; el informe local ya lo
documenta) — solo el comentario firmado (`ca-qa`). Un `qa-rojo` devuelve al `implementer` para
corrección (por el ledger, igual que los gaps de revisión); un `qa-verde` es, junto con `revision`
sin gaps, lo que habilita **al orquestador** a disparar `aprobado` (Paso 7, parte 2 de
`progress-sync.md`). `jira-flow.py` nunca encadena `aprobado` por su cuenta, y **`qa` tampoco lo
dispara**: su `--actor` es `orquestador` (otro actor → exit 2) y exige revisión limpia en el ledger
más `--qa-verde`, que el orquestador pasa solo tras leer el exit 0 de `qa-gate.py`. Misma
idempotencia que arriba (no repetir un intento ya comentado).
