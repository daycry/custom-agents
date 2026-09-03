---
name: jira-sync
description: >
  Vuelca un plan (tasks.md de docs/roadmap/<fecha>-<slug>/) a Jira creando issues,
  vía el conector oficial de Atlassian (Rovo MCP). Se ofrece al CREAR el plan
  (opt-in). Asistente guiado para elegir destino: en Cowork/escritorio abre un
  ARTEFACTO interactivo (buscar proyecto / buscar issue padre por clave, texto o
  JQL); en CLI o VS Code hace lo mismo de forma CONVERSACIONAL (por texto, eligiendo
  por número). Determina el tipo de issue según la jerarquía del padre (no lo
  hardcodea), comprueba campos obligatorios, PREVISUALIZA y pide confirmación antes
  de crear nada, es idempotente (no duplica) y escribe las claves Jira de vuelta en
  tasks.md. Úsala cuando el usuario diga "vuelca el plan a Jira", "crea las tareas
  en Jira", "sincroniza el plan con Jira", "pásame esto a Jira".
user-invokable: true
---

# jira-sync — volcar el plan a Jira (con artefacto o conversacional)

Convierte las tareas de un plan (`docs/roadmap/<fecha>-<slug>/tasks.md`) en **issues de Jira**,
usando el **conector oficial de Atlassian (Rovo MCP)** — sin integración propia. Se ofrece **al
crear el plan** y es **opt-in**: si el usuario no quiere, no se hace nada.

**Pensada para no técnicos.** Una pregunta a la vez, lenguaje llano, **previsualiza y confirma
antes de crear**. Nada se escribe en Jira sin un "sí" explícito.

## Requisitos

- **Conector Atlassian (Rovo MCP) conectado** con permiso de escritura (`write:jira-work`). Si no
  lo está, dilo en llano ("Necesito conectarme a vuestro Jira; actívalo en los conectores y
  volvemos") y **detente**.
- Herramientas del conector (por su función; el prefijo `mcp__…__` puede variar):
  `getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `searchJiraIssuesUsingJql`,
  `getJiraProjectIssueTypesMetadata`, `getJiraIssueTypeMetaWithFields`, `createJiraIssue`,
  `getJiraIssue`, `editJiraIssue` (checklist de la descripción en modo fase), y para la
  sincronización de progreso `addWorklogToJiraIssue`, `addCommentToJiraIssue` (comentarios de
  progreso y de revisión), `getTransitionsForJiraIssue`, `transitionJiraIssue`.
- Un plan existente: `docs/roadmap/<fecha>-<slug>/tasks.md` (tareas `T-XX`).

## Paso 0 — opt-in y conexión

1. Localiza la config y respeta el flag `enabled`:
   ```bash
   JCFG="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*jira.json' 2>/dev/null | head -1)"
   ```
   - `enabled: false` → no hagas nada. Sin config (primera vez) → pregunta **una vez**: "¿Quieres volcar los planes a Jira?"; guarda la decisión en `.claude/jira.json`.
2. Comprueba conexión con `getAccessibleAtlassianResources`; si no está, guía a conectarla y detente. Resuelve el `cloudId` (uno solo → úsalo; varios → pregunta por nombre) y persístelo.

> **Lectura bajo demanda (token-diet).** Este fichero es el mapa: cada paso trae su regla en 1-3 líneas
> y remite a `references/<tema>.md` para la casuística completa. **Abre una referencia solo cuando
> llegues al paso que la cita** (tabla al final); no las cargues todas al arrancar.

## Paso 0-bis — granularidad del volcado (por TAREA o por FASE)

Campo `granularidad` en `.claude/jira.json`: **`tarea`** (por defecto, un issue por `T-XX`) o **`fase`**
(un issue por fase con sus `T-XX` como checklist). Si falta, pregunta una vez y persiste. Nunca
mezcles modos en silencio si el manifiesto ya tiene claves del otro. → `references/destination-and-types.md`.

## Paso 0-ter — asignación de los issues creados (`assignee`)

Si `assignee` no está en `.claude/jira.json`, pregunta una vez (`"me"` | `"none"`, defecto `"me"`) y
persiste; al crear (Paso 5) fija SIEMPRE `assignee` explícito en `additional_fields` — nunca confíes en
el "asignado por defecto" del proyecto (GOT-004). → `references/destination-and-types.md`.

## Paso 1 — elegir destino (proyecto + padre opcional)

Resultado buscado, sea cual sea el modo: **`{ projectKey, parentKey|null }`**. Detecta el entorno:
**Paso 1-A** artefacto (Cowork/escritorio, plantilla `assets/jira-picker.template.html`) o **Paso 1-B**
conversacional (CLI/VS Code, resultados numerados). → `references/destination-and-types.md`.

## Paso 2 — decidir el TIPO de issue (según la jerarquía del padre, descubierto)

No hardcodees nombres de tipo: `getJiraProjectIssueTypesMetadata(projectKey)` y decide por
`hierarchyLevel` + `subtask` (sin padre → nivel 0; padre nivel ≥ 1 → nivel 0 con `parent`; padre nivel 0
→ subtarea). → `references/destination-and-types.md`.

## Paso 3 — comprobar campos obligatorios (evitar fallos al crear)

`getJiraIssueTypeMetaWithFields(projectKey, issueTypeId, requiredFieldsOnly:true)`; un obligatorio
extra sin default se pregunta una vez y va en `additional_fields`. Comportamientos verificados del
conector: `docs/atlassian-connector-notes.md`. → `references/destination-and-types.md`.

## Paso 4 — previsualizar y CONFIRMAR (obligatorio) — la previsualización ES un dry-run

Construida con verificaciones reales de solo lectura; muestra cuántos issues, de qué tipo y dónde
cuelgan, y **espera "sí"**. "Simúlalo" → detente aquí con el informe. → `references/destination-and-types.md`.

## Paso 5 — crear (idempotente)

**[modo tarea]** un `createJiraIssue` por `T-XX` (`summary` = `"T-XX · <título>"`, labels `roadmap` +
`<slug>`, `assignee` explícito). **[modo fase]** primero `ledger-lint.py` exit 0, luego un issue por fase
con checklist. Manifiesto `.claude/jira-state.json` (`T-XX → issueKey` / `fase-N → issueKey`): si ya
existe, **no dupliques**. → `references/create-and-writeback.md`.

## Paso 6 — escribir de vuelta y cerrar

Anota la clave Jira junto a cada `T-XX` (o en la cabecera de la fase) en `tasks.md`, actualiza el
manifiesto y cierra en llano con recuento y enlaces. → `references/create-and-writeback.md`.

## Paso 7 — ciclo de eventos firmado (comentarios + horas + Done)

Cada evento (`arrancar` · `implementado` · `revision` · `gaps` · `aprobado` · `qa-verde` · `qa-rojo`) lo
dispara su actor fijo (`implementer` · `reviewer` · `qa` · **`orquestador`** para `aprobado`) ejecutando
`scripts/jira-flow.py plan --event <evento> --actor <actor> --task T-XX --ledger tasks.md --json`: el script **lee el ledger** y devuelve el plan de operaciones
(transición · etiqueta `ca-<agente>` · comentario YA FIRMADO — `> 🤖 **[custom-agents · <agente>]** ·
<rol> · <fecha>` — · comando de `worklog.py`); el agente solo **ejecuta** ese plan vía el conector, nunca
redacta el comentario a mano. **El cálculo NO se hace a mano:** la aritmética de horas sigue siendo de
`scripts/worklog.py plan … --apply` (real→est, tope de jornada DIARIO, banco por issue; `drain` al
retomar el día); `jira-flow.py` solo la invoca con las horas que ya constan en el ledger. **Regla dura
(corrige un bug de diseño anterior): Done NUNCA se marca al completar una tarea** — se descubre por
`to.statusCategory.key == "done"` y ocurre **solo** en el evento `aprobado`, que dispara **el
orquestador** (`--actor orquestador`; otro actor → exit 2) y **no a ciegas**: exige revisión limpia en
el ledger **y** `--qa-verde` (el exit 0 de `qa-gate.py`), o exit 2 con la razón y `ops: []`. Quién dispara cada evento y
cuándo, en una única tabla (token-diet, no se duplica aquí): `commands/dev-cycle.md` Fase 3. **Opt-in comprobado por el script** (lee `.claude/jira.json`: `enabled` ≠ `true` → `ops: []`,
`jira: "desactivado"`, exit 0) e **idempotente por clave** en `jira-state.json` (`flow`), así que
reejecutar `/dev-cycle` no publica dos veces. → `references/progress-sync.md` (eventos del `implementer` + `aprobado` + tope de
jornada + read-back) y `references/review-publish.md` (eventos de `reviewer`/`qa`, comentarios por
intento).

## Paso 8 — traer estado desde Jira (read-back, opcional)

Sentido inverso: compara el `status` de cada issue con `tasks.md` (ledger canónico), lista divergencias
y aplica cambios **solo con confirmación**; no imputa horas. → `references/progress-sync.md`.

## Config `.claude/jira.json` (gestión interna, editable)

Campos: `enabled`, `granularidad`, `assignee`, `cloudId`, `horasJornada` (de `rates.json`),
`alCubrirJornada`, `ratioSupervision`, `defaults`. Estado en `.claude/jira-state.json` (mapeo, imputado
por día, banco, `worklogImpl`/`worklogRevision`, `reviewComentado`). → `references/config.md`.

## Reglas

- **Opt-in y confirmación:** nunca creas en Jira sin que el proyecto lo haya activado y sin un "sí" a la previsualización.
- **Doble modo:** artefacto en Cowork/escritorio; conversacional en CLI/VS Code. Mismo resultado (`{projectKey, parentKey}`); no dependas de que exista el host de artefactos.
- **No hardcodees tipos ni búsquedas:** descubre los tipos por jerarquía; construye la JQL acotada al proyecto; `searchResultMode:"issues"` siempre.
- **Payloads mínimos (ahorro de tokens):** en toda llamada al conector (`searchJiraIssuesUsingJql`, `getJiraIssue`…) pide **solo los campos que vas a usar** con `fields:[…]` (p. ej. `["summary","status","issuetype","parent"]` al buscar padre; `["summary","status","timetracking","aggregatetimespent"]` al leer progreso) y acota `maxResults` (p. ej. 25-50) en vez de traer la respuesta completa por defecto, que es enorme. Nunca pidas "todos los campos" salvo que de verdad los necesites; si falta uno, añádelo a la lista explícita.
- **Idempotente:** el manifiesto evita duplicados al reejecutar. `tasks.md` sigue siendo el ledger canónico del progreso; Jira es un espejo para el equipo.
- **Errores en llano:** sin conexión / sin permiso / campo obligatorio inesperado / issue padre inválido → una frase clara y el siguiente paso, no un volcado técnico.
- **Solo el plan indicado:** trabaja sobre la carpeta `docs/roadmap/<fecha>-<slug>/` en curso; no toques otras iniciativas.

## Qué NO hace

- No reimplementa la API de Jira ni usa tokens propios: todo pasa por el conector Atlassian (Rovo MCP).
- No crea, imputa ni transiciona nada sin opt-in (`enabled: true`) y sin el "sí" a la previsualización.
- No convierte `tasks.md` en espejo de Jira: el ledger manda; el read-back informa y pide confirmación.
- No calcula worklogs en prosa ni redacta comentarios libres: la aritmética vive en
  `scripts/worklog.py` y los comentarios (ya firmados) en `scripts/jira-flow.py` + las 6 plantillas de
  `assets/` (una `comment-*.md` por evento con comentario) (ambos con tests).

## Referencias (lectura bajo demanda)

| Fichero | Léelo SOLO cuando… | Contiene |
|---|---|---|
| `references/destination-and-types.md` | llegues al **Paso 0-bis** y hasta cerrar el **Paso 4** | granularidad, `assignee`, Paso 1-A (artefacto) / 1-B (conversacional), tipo por jerarquía, campos obligatorios, previsualización/dry-run |
| `references/create-and-writeback.md` | tengas el "sí" y vayas a crear (**Pasos 5-6**) | `createJiraIssue` en modo tarea / fase, manifiesto de idempotencia, write-back a `tasks.md` |
| `references/progress-sync.md` | dispares un evento del `implementer` (`arrancar`/`implementado`), `aprobado`, o pidan traer estado (**Pasos 7-8**) | `jira-flow.py` + `worklog.py`, regla de horas, Done descubierto solo en `aprobado`, tope de jornada diario y banco, read-back |
| `references/review-publish.md` | dispares un evento de `reviewer` (`revision`/`gaps`) o `qa` (`qa-verde`/`qa-rojo`) (**Paso 7**) | plantillas firmadas por intento, worklog `[revisión]` por intento, clave `rev-fase-N`, idempotencia |
| `references/config.md` | tengas que leer/escribir un campo de `jira.json` o `jira-state.json` | todos los campos con defaults y de dónde salen |
| `docs/atlassian-connector-notes.md` (plugin) | el conector devuelva un error o un dato inesperado | hechos verificados del conector (JQL acotada, `searchResultMode`, jerarquía…) |
