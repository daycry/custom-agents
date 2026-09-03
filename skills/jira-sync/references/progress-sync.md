# jira-sync — eventos del implementer, Done y read-back (Pasos 7 y 8)

> Referencia de la skill `jira-sync`. Léela **solo** cuando dispares un evento `arrancar` /
> `implementado` (el `implementer`) o `aprobado` (**el orquestador**) — Paso 7 —, o al traer estado
> desde Jira (Paso 8). Toda la aritmética la hace `scripts/worklog.py`; los comentarios firmados y
> el plan de operaciones los genera `scripts/jira-flow.py`; aquí está la regla que implementan y la
> política del tope diario.

> **Tres cosas que hace el script y no tienes que vigilar tú** (T-fix1): **(1) opt-in real** — lee
> `.claude/jira.json` (`--root`, o cwd hacia arriba) y con `enabled` ≠ `true` devuelve `ops: []` y
> `jira: "desactivado"`, exit 0 sin ruido; **(2) idempotencia** — anota cada plan con `ops` en
> `jira-state.json` (`flow["<issue>|<evento>|<tareas>|<intento>"]`), así que repetir el mismo evento
> da `ops: []` + `yaRealizado: true` en vez de un segundo comentario (`--force` si de verdad quieres
> repetirlo; estado corrupto o de solo lectura → aviso y sigue); **(3) worklog sin inventar issue** —
> si la tarea no está mapeada, la op de worklog sale marcada `pendiente: "issueKey"` /
> `requiereIssue: true` **sin comando**, en vez de un comando con un placeholder que se podía
> ejecutar tal cual.

## Paso 7 (parte 1) — `arrancar` e `implementado` (el `implementer`)

1. **`arrancar`** (al empezar `T-XX`, transición de estado, **sin comentario**):
   ```bash
   JF="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/jira-sync/scripts/jira-flow.py' 2>/dev/null | head -1)"
   python3 "$JF" plan --ledger tasks.md --event arrancar --actor implementer --task T-08 --json
   ```
   El plan trae la etiqueta `ca-implementer` y una transición a la categoría **`indeterminate`**
   (en curso) — descubierta por `getTransitionsForJiraIssue`, nunca por nombre ni id fijo (GOT-004);
   sáltala si el issue ya está en curso.
2. **`implementado`** (al terminar `T-XX`, comentario + worklog, **sin transición** — regla dura:
   esto YA NO marca Done; antes lo hacía, era el bug):
   ```bash
   python3 "$JF" plan --ledger tasks.md --event implementado --actor implementer --task T-08 --json
   # varias tareas de una fase en un único comentario (mismo evento, un worklog por tarea):
   python3 "$JF" plan --ledger tasks.md --event implementado --actor implementer --task T-08,T-09 --batch --json
   ```
   El comentario sale **ya redactado y firmado** (`> 🤖 **[custom-agents · implementer]** ·
   implementador · <fecha>`) a partir de lo que el ledger YA dice de cada tarea (Descripción,
   Archivos, Verificación, horas) — el modelo no redacta nada libre. El plan también trae, por
   cada tarea, la línea de `worklog.py` YA rellenada con las horas del ledger:
   ```bash
   # el propio jira-flow.py imprime algo equivalente a esto (ops[].comando en el --json):
   python3 skills/jira-sync/scripts/worklog.py plan --task T-08 --issue KEY \
       --ia-real <de la Descripción> --sup-real <de la Descripción>
   ```
   Ejecútala **con `--apply`** tras publicar el comentario en Jira, para persistir el estado (igual
   que siempre — `worklog.py` sigue siendo la única aritmética; ver "Tope de jornada diario" abajo).
   Si sale `requiereDecision`, pregunta al usuario y reejecuta con `--policy <parar|seguir|banco>`.

> **[modo fase] Dónde va cada cosa.** El issue objetivo de una tarea `T-XX` es el de **su fase**
> (`fase-N → issueKey` en el manifiesto), no uno propio — pásalo con `--issue` (o resuélvelo tú
> mismo antes de llamar a `jira-flow.py`, que si no lo recibe intenta leerlo del manifiesto). Usa
> `--batch` para agrupar todas las `T-XX` de la fase en **un** comentario del evento `implementado`,
> con un worklog por tarea. El resto del cálculo (worklog, tope, banco) es idéntico; solo cambia el
> `issueKey` destino.

## Paso 7 (parte 2) — `aprobado`: el ÚNICO punto donde se marca Done

`aprobado` lo dispara **el orquestador** (`/dev-cycle`, tabla «Ciclo Jira de la Fase 3»), **nunca
un agente**: es la única puerta que mira DOS veredictos a la vez y ni el `reviewer` ni `qa` ven los
dos. Su `--actor` es `orquestador` (cualquier otro → exit 2 diciendo qué actor espera el evento).

Y **no se emite a ciegas**: `jira-flow.py` exige las dos evidencias y, si falta alguna, devuelve
**exit 2 con la razón** y `ops: []` (antes emitía la transición a Done SIEMPRE, sin comprobar nada):

1. **Revisión limpia en el ledger** — la **última** sección `## Revisión de dos lentes — intento N`
   no deja filas de gap **pendientes** para esas tareas: o no tiene filas ("sin gaps"), o todas
   traen su corrección registrada / `descartado (rebatido)`.
2. **`--qa-verde`** — el flag con el que el orquestador declara el verde de `qa`. Pásalo **solo tras
   leer el exit 0 de `agent-kits/qa/qa-gate.py`**; nunca por el resumen de nadie ni por impresión.
   (El ledger no tiene marca canónica de "qa verde": el veredicto vive en
   `docs/roadmap/<slug>/testing/report.md`, y el exit code del gate es la evidencia.)

```bash
python3 "$JF" plan --ledger tasks.md --event aprobado --actor orquestador --task T-08 \
    --qa-verde --json
```

El plan trae **etiqueta `ca-orquestador` → transición a `done` → comentario de cierre YA FIRMADO**
(`> 🤖 **[custom-agents · orquestador]** · orquestación del ciclo (/dev-cycle) · <fecha>`), para que
en Jira quede quién cerró el issue y con qué evidencia.

**Marca Done (descubierto, no hardcodeado):** el plan trae una transición a la categoría **`done`**
— `getTransitionsForJiraIssue(issueKey)` → localiza la transición cuyo `to.statusCategory.key ==
"done"` y aplícala con `transitionJiraIssue`. **Nunca** la resuelvas por el nombre de la transición
ni del estado destino (verificado en dry-run: una transición llamada "Done" puede apuntar a un
estado localizado, p. ej. "HECHO", y los ids de transición varían por workflow) ni por un id fijo.
Si hay varias con `statusCategory.key == "done"` o ninguna clara, pregunta/omite con aviso. **[modo
fase]** el issue de la fase pasa a Done solo cuando **todas** sus tareas han recibido su propio
`aprobado`.

### Tope de jornada diario (banco de horas)

El **acumulado de horas imputadas por día** no debe pasar de `horasJornada` (por defecto 8; 7 en
periodos intensivos). Lleva ese acumulado por fecha en `.claude/jira-state.json`
(`imputadoPorDia: { "YYYY-MM-DD": 6.5 }`). Antes de imputar el worklog de una tarea:

- Calcula `restante = horasJornada − imputado_hoy`.
- **Si cabe** (`horas ≤ restante`): imputa normal y suma al acumulado del día.
- **Si NO cabe** (superaría la jornada): aplica la preferencia `alCubrirJornada` de `.claude/jira.json`:
  - **`preguntar`** (por defecto): para y ofrece las **tres** opciones; actúa según la respuesta y ofrece **recordarla** (guardarla en `alCubrirJornada` para no volver a preguntar):
    1. **Parar** — imputa solo `restante` (hasta cubrir la jornada) y **detén la implementación**; informa de cuántas horas y tareas quedan pendientes. (El `implementer` debe respetar esta parada.)
    2. **Seguir imputando** — imputa las `horas` completas aunque el día supere la jornada.
    3. **Banco (día siguiente)** — imputa `restante` hoy (hasta cubrir la jornada) y **guarda el exceso** en `bancoHoras` como una **entrada con su tarea e issue** (`{ task:"T-XX", issueKey:"…", horas, origen }`); sigue implementando. El excedente **no** se imputa hoy: queda pendiente para una jornada posterior, y sabe **a qué issue** imputarse.
  - Si `alCubrirJornada` ya tiene un valor (`parar`/`seguir`/`banco`), aplícalo sin preguntar.

> **Ejemplo (banco).** Llevas 6 h imputadas hoy y una tarea consume 3 h (tope 8 h): imputa **2 h hoy** (llegas a 8 h) y guarda **1 h** en el banco. Esa 1 h **no** se registra hoy con fecha de mañana.

- **Solo se imputan horas del día en curso.** Todo worklog se registra con la **fecha de hoy** (la real); **nunca** se post-datan horas a días futuros. Por eso el banco no se imputa por adelantado: cada entrada del banco se imputa **a su `issueKey`** cuando ese día posterior sea realmente *hoy* (en una ejecución de ese día), consumiendo el presupuesto de esa jornada. Si una entrada no cabe entera, imputa lo que quepa a su issue y **re-banca el resto de esa misma entrada**. Así, en Jira, cada día solo lleva horas registradas ese mismo día y nunca más de `horasJornada`, y cada hora va a la tarea que le corresponde.

> Igual que el volcado, esto es **opt-in**: solo ocurre si `.claude/jira.json` tiene `enabled: true`. Aunque el conector esté conectado, si no se ha activado Jira para el proyecto, no se imputa ni se transiciona nada.

## Paso 8 — traer estado desde Jira (read-back, opcional)

Sentido inverso del volcado, para no perder de vista lo que el equipo mueve en Jira. Se invoca a
demanda ("trae el estado de Jira", "sincroniza el estado desde Jira") o al **retomar** un plan.
`tasks.md` es el **ledger canónico**: Jira es espejo, así que el read-back **informa** y solo
actualiza `tasks.md` con confirmación.

1. **[modo tarea]** Para cada `T-XX → issueKey`, lee el issue con `getJiraIssue` (`status` y categoría). **[modo fase]** Para cada `fase-N → issueKey`, lee el issue de la fase y compáralo con el **agregado** de sus tareas en `tasks.md` (la fase está *Done* ⟺ todas sus `T-XX` `completado`).
2. Compara el estado del issue con el de la tarea/fase en `tasks.md` (mapa aproximado: categoría *Done* ↔ `completado`; *In Progress* ↔ `en-progreso`; *To Do* ↔ `borrador`/`en-progreso`).
3. **Clasifica y muestra** las divergencias, sin tocar nada aún:
   - Issue *Done* en Jira pero tarea no `completado` en `tasks.md` (alguien la cerró en Jira).
   - Tarea `completado` en `tasks.md` pero issue abierto en Jira (no se sincronizó el cierre; ver Paso 7).
   - Coinciden → nada que hacer.
4. **Con confirmación**, aplica los cambios acordados en `tasks.md` (y su resumen de progreso). Nunca sobreescribas el ledger en silencio; ante duda, deja la divergencia listada para que el usuario decida.
5. No imputa horas en el read-back (eso es del Paso 7, evento `implementado`).

> Es **opt-in** como el resto: solo si `.claude/jira.json` `enabled: true`. Útil al reabrir una iniciativa (`/dev-cycle` sobre una carpeta existente) para alinear `tasks.md` con lo que haya pasado en Jira entretanto.
