---
description: Detecta la DERIVA entre las specs implementadas y el código actual (el /speckit.analyze del plugin) — por cada spec `implementada`, subagentes de contexto fresco verifican cada criterio de aceptación contra el código de HOY y emiten veredicto vigente/derivado/no-verificable con evidencia. Escribe docs/roadmap/DRIFT.md y ofrece abrir iniciativa para lo derivado. Solo lectura del código.
argument-hint: "(opcional) <slug> — sin argumento revisa TODAS las specs implementadas"
---

# /spec-drift — ¿el código sigue cumpliendo lo que las specs dicen?

Una spec `implementada` es una promesa: el código hacía esto cuando se cerró. Con el tiempo, el
código cambia y la promesa puede romperse en silencio (**drift**). Este comando la re-verifica.
Es de **solo lectura** sobre el código: informa; la corrección va por `/pm-cycle`, nunca se
parchea desde aquí. Objetivo: **$ARGUMENTS** (vacío = todas).

## Pasos

1. **Localiza las specs a revisar.** Recorre `docs/roadmap/*/spec.md` y filtra las que tienen
   `estado: implementada` en su frontmatter (con `$ARGUMENTS`, solo la carpeta cuyo slug
   coincida). **Si no hay ninguna, dilo y termina** — no inventes análisis.

2. **Verifica cada spec con un subagente de contexto fresco** (patrón de la lente A; **lotes de
   máximo 3 en paralelo** para no disparar el coste; aplica la disciplina de lectura del kit
   shared). Prompt del subagente:

   > "Verifica la spec `docs/roadmap/<fecha>-<slug>/spec.md` contra el código ACTUAL del
   > repositorio. Por cada **criterio de aceptación** de la spec, emite exactamente uno de:
   > **vigente ✓** (el código lo cumple hoy — con evidencia `fichero:línea`), **derivado ✗**
   > (el código ya no lo cumple — con evidencia de qué cambió), o **no verificable** (el
   > criterio no es contrastable contra código: proceso, prosa, o falta acceso). Los criterios
   > `[GWT] CA-XX` se verifican también contra su bloque del `test-plan.md` si existe. Sé
   > escéptico: sin evidencia NO hay ✓ — usa `no verificable`. Devuelve una tabla
   > criterio → veredicto → evidencia. Solo lectura."

3. **Agrega la salida en `docs/roadmap/DRIFT.md`** (se sobrescribe en cada análisis; lleva la
   fecha): cabecera con fecha y alcance, una sección por spec con su tabla
   criterio → veredicto → evidencia, y un resumen final (nº de specs vigentes / con deriva /
   no concluyentes). No escribas NADA más (ni código, ni specs, ni ledgers).

4. **Resume conversacionalmente**: qué specs siguen vigentes, cuáles tienen deriva (y en qué
   criterios), y **ofrece abrir una iniciativa** con `/pm-cycle <slug>-drift` para cada spec
   derivada — la deriva se corrige por el cauce normal (spec → evaluación → puerta), no con
   un parche directo.
5. **Sincronizar con Confluence (opcional).** Aplica el paso compartido `"$SHAREDKIT/confluence-optin.md"` (skill `confluence-publish` con opt-in) sobre `docs/roadmap/DRIFT.md`. Localízalo con `SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`. Fallback si no está: invoca `confluence-publish` respetando su opt-in, sin bloquear el cierre; nunca sincronices `docs/security-scan/`.

## Reglas

- **Solo lectura del código.** Este comando escribe únicamente `docs/roadmap/DRIFT.md`.
- **Sin evidencia no hay veredicto**: `no verificable` es un resultado honesto, no un fallo.
  Nunca regales ✓ ni alarmes con ✗ sin `fichero:línea`.
- **Coste acotado**: lotes de máx. 3 subagentes; con muchas specs, sugiere filtrar por slug.
- Las specs de **prosa/proceso** (p. ej. las de este propio plugin) saldrán mayormente
  `no verificable` — es lo esperado; el valor está en las specs con criterios observables
  (idealmente `[GWT]`).
- La constitución (`docs/CONSTITUTION.md`), si existe, NO se verifica aquí (no es una spec);
  su enforcement vive en la revisión de dos lentes de `/dev-cycle`.
