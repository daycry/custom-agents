# jira-sync — crear issues (idempotente) y escribir de vuelta (Pasos 5 y 6)

> Referencia de la skill `jira-sync`. Léela **solo** al llegar al Paso 5 (tras el "sí" del Paso 4): detalle de `createJiraIssue` en modo tarea / modo fase, manifiesto de idempotencia y write-back a `tasks.md`.

## Paso 5 — crear (idempotente)

**[modo tarea]** Con el "sí", por cada tarea `T-XX` de `tasks.md`:
- `createJiraIssue(projectKey, issueTypeName, summary, description, parent?)`:
  - `summary` = `"T-XX · <título de la tarea>"`.
  - `description` = detalle/criterios de aceptación de la tarea (formato markdown) **+ enlace de vuelta** a la iniciativa (`docs/roadmap/<fecha>-<slug>/`) para no perder el contexto.
  - `parent` = la clave del padre (si aplica).
  - **Labels** (via `additional_fields`): `roadmap` y `<slug>` de la iniciativa, para poder filtrarla luego por JQL (`labels = "<slug>"`) — lo aprovecha el dashboard vivo desde Jira.
  - **`assignee`** (via `additional_fields`, siempre explícito): según `.claude/jira.json` (Paso 0-ter) — accountId propio si `"me"`, sin asignar si `"none"`. No dejes que el "asignado por defecto" del proyecto decida.
- **Idempotencia — manifiesto `.claude/jira-state.json`:** mapea `carpeta+T-XX → issueKey`. Antes de crear, consulta el manifiesto:
  - Ya tiene issueKey y existe (`getJiraIssue`) → **no dupliques** (salta o, si cambió el título, ofrece actualizar con `editJiraIssue`).
  - No está → crea y registra `T-XX → issueKey`.
- Muestra progreso ligero si son muchas ("Creando… 3 de 6").

**[modo fase]** Antes de agrupar, **valida el ledger** con el script compartido — un `tasks.md` mal formado (una `T-XX` fuera de fase, resumen descuadrado) crearía issues incorrectos:
```bash
LL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*agent-kits/shared/ledger-lint.py' 2>/dev/null | head -1)"
python3 "$LL" "docs/roadmap/<fecha>-<slug>/tasks.md"   # exit 0 obligatorio para volcar en modo fase
```
Si da incoherencias duras, repórtalas y no vuelques hasta que el ledger esté limpio. Con el ledger en verde y el "sí", por cada **Fase** del plan (agrupa las `T-XX` por su fase leyendo `tasks.md`):
- `createJiraIssue(...)`:
  - `summary` = `"Fase N · <título de la fase>"`.
  - `description` = objetivo de la fase + **checklist de sus tareas** en markdown (`- [ ] T-XX · <título>` una por tarea) + enlace de vuelta a la iniciativa.
  - `parent`, tipo, labels y `assignee` igual que en modo tarea (el tipo se descubre por jerarquía, Paso 2; el `assignee` sale de `.claude/jira.json`, Paso 0-ter).
- **Fase sin tareas → no se crea issue** (avísalo).
- **Idempotencia:** el manifiesto mapea `fase-N → issueKey`. Mismo criterio: si ya existe, no dupliques; si no, crea y registra `fase-N → issueKey`.
- Escribe la clave Jira en la **cabecera de cada fase** de `tasks.md` (Paso 6).

## Paso 6 — escribir de vuelta y cerrar

- En `tasks.md`, anota junto a cada `T-XX` su **clave Jira** (p. ej. una columna "Jira" o un sufijo `→ PROJ-123`). Si se usó un padre/épica, anótalo en `improvement-plan.md`.
- Actualiza `.claude/jira-state.json`.
- Cierra en llano con el recuento y **enlaces clicables**: "Creé 6 subtareas bajo PROJ-59. Aquí las tienes: <URLs>."
