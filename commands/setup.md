---
description: Onboarding del plugin en un proyecto — en UNA pasada guiada crea la config compartida de presupuesto (.claude/rates.json), decide los opt-ins de Confluence y Jira, ofrece la constitución del proyecto (docs/CONSTITUTION.md), las opciones de disciplina de desarrollo (.claude/dev.json: TDD, worktrees, subagentes), la statusline opt-in (progreso del roadmap + coste de sesión) y la lente de seguridad de la revisión adversarial (dev.json revision.lenteSeguridad: auto/siempre/nunca), en vez de que cada skill pregunte por su cuenta la primera vez. Idempotente; se puede relanzar para cambiar decisiones.
argument-hint: "(sin argumentos)"
---

# /setup — dejar el proyecto listo en una pasada

Evita el onboarding disperso (cada skill preguntando su opt-in la primera vez que se activa).
Una conversación corta y el proyecto queda configurado. **Idempotente**: si ya hay config, muestra
los valores actuales y ofrece cambiarlos.

## Pasos (una pregunta cada vez, en llano)
1. **Presupuesto — `.claude/rates.json`.** Si no existe, créalo desde la plantilla (`agent-kits/evaluator/templates/rates.example.json`) confirmando con el usuario: tarifa €/h, jornada (8/7), ratio de supervisión, margen. Para el **precio de tokens**, ofrece ejecutar la skill **`rates-verify`** (consulta la doc oficial y lo escribe con fecha) en vez de dejarlo a 0; si el usuario no quiere ahora, déjalo a 0 = "a verificar". Si existe, resume valores y ofrece ajustar (y relanzar `rates-verify` si el precio es antiguo o está a 0).
2. **Confluence — `.claude/confluence.json`.** Pregunta: "¿Sincronizar la documentación con Confluence? [Sí/No]".
   - **No** → `enabled: false` (no volverá a preguntar).
   - **Sí** → `enabled: true` y, si el conector Atlassian está disponible, ofrece hacer **ahora** el alta guiada (skill `confluence-publish`: espacio + anclaje); si no, deja `enabled: true` y el alta se hará en la primera publicación.
3. **Jira — `.claude/jira.json`.** Pregunta: "¿Volcar los planes a Jira e imputar horas al completar tareas? [Sí/No]".
   - **No** → `enabled: false`.
   - **Sí** → `enabled: true` + pregunta la política al cubrir la jornada (`alCubrirJornada`: preguntar/parar/seguir/banco; default `preguntar`). La jornada ya viene de `rates.json`.
4. **Constitución del proyecto — `docs/CONSTITUTION.md` (opt-in).** Pregunta: "¿Quieres una constitución del proyecto — principios permanentes (código, arquitectura, convenciones, seguridad) que todos los agentes respetan y la revisión hace cumplir? [Sí/No]".
   - **No** → no se crea; los agentes trabajan sin ella (nunca bloquea). **Persiste la decisión** en `.claude/dev.json` con `"constitucion": false` — así los relanzamientos distinguen "declinado" (resume la decisión y ofrece cambiarla, sin re-preguntar de cero) de "nunca preguntado".
   - **Sí** → créala guiada desde la plantilla (`agent-kits/shared/templates/CONSTITUTION.template.md`): recorre las 4 secciones preguntando 2-3 principios por sección (breve — el fichero debe quedarse en 1-2 páginas); deja fuera lo que el usuario no tenga claro (mejor corta y real que larga e inventada). Persiste `"constitucion": true` en `.claude/dev.json`. Si el fichero ya existe, resume sus principios y ofrece revisarla.
5. **Disciplina de desarrollo — `.claude/dev.json` (opt-in, defaults off).** Pregunta las tres opciones de la cadena nativa de `/dev-cycle`, explicando el coste/beneficio en una frase cada una:
   - `tdd` — "¿Test antes del código (RED-GREEN-REFACTOR, con evidencia del rojo en el ledger)? [No]"
   - `worktree` — "¿Cada iniciativa en un worktree de git aislado? [No]"
   - `subagentes` — "¿Cada tarea implementada por un subagente de contexto fresco (más calidad por tarea, más tokens)? [No]"
   - `guardrails` — **default ACTIVADO** (solo se ofrece desactivar): "El `implementer` lleva un hook de guardia determinista (en `docs/roadmap/` solo `tasks.md`, trabajar en rama, sin `git push --force`/`branch -D`/`rm -rf` peligrosos). ¿Mantenerlo activo? [Sí]". Solo si el usuario dice no, escribe `"guardrails": false` (o por regla: `{"alcance": true, "ramaPrincipal": false, "git": true}`); si dice sí, no escribas la clave (ausente = activo).
   Escribe `.claude/dev.json` con lo elegido (p. ej. `{"tdd": false, "worktree": false, "subagentes": false}`). Si ya existe, resume y ofrece cambiar.
5-bis. **Statusline (opt-in, default No).** Pregunta: "¿Mostrar el progreso del roadmap y el coste de la sesión en la barra de estado de Claude Code? [No]".
   - **No** → persiste `"statusline": false` en `.claude/dev.json` y no toca `settings.json`.
   - **Sí** → resuelve la ruta del script **en tiempo de setup** y escríbela **ABSOLUTA** (la doc oficial de `statusLine` solo documenta `~` en `command`, no `${CLAUDE_PLUGIN_ROOT}`, y el `settings.json` de un plugin no admite la clave `statusLine`; verificado 2026-09-02):
     ```bash
     SL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*statusline/roadmap-statusline.sh' 2>/dev/null | head -1)"
     ```
     Luego **mergea** (sin pisar otras claves) en `.claude/settings.json` del proyecto el bloque oficial:
     ```json
     { "statusLine": { "type": "command", "command": "<ruta absoluta de $SL>" } }
     ```
     Si `settings.json` no existe, créalo con solo ese bloque. **Si ya hay una `statusLine` del usuario**, muéstrala y **no la sustituyas** sin confirmación explícita (por defecto se conserva la suya y se anota `"statusline": false`). Persiste `"statusline": true` en `.claude/dev.json`. Si `$SL` está vacío (instalación parcial), avisa y no escribas nada.
   - Qué muestra (una línea, ≤ ~100 caracteres): `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` (varias iniciativas activas → `📋 N iniciativas activas`). Sin `jq` usa `python3`; sin ninguno, solo el modelo. Nunca falla.
   - **Reversión**: borrar la clave `statusLine` de `.claude/settings.json` (o `/statusline remove`) y poner `"statusline": false` en `dev.json`. Relanzar `/setup` también lo ofrece.
5-ter. **Lente de seguridad de la revisión (opt-in, default `auto`).** Pregunta: "¿Añadir una tercera lente de SEGURIDAD a la revisión adversarial cuando el cambio toque auth/sesiones/secretos/config sensible? [auto (recomendado) / siempre / nunca]". Explica en una frase: `auto` = solo si `review-lens-select.py` detecta rutas o líneas sensibles en el diff (coste cero en cambios de prosa); `siempre` = un tercer revisor en cada revisión; `nunca` = solo las lentes A+B.
   - Persiste `"revision": {"lenteSeguridad": "<auto|siempre|nunca>"}` en `.claude/dev.json` **mergeando** (sin pisar `tdd`/`worktree`/`subagentes`/`guardrails`/`statusline` ni otras claves de `revision`). Si el usuario elige `auto`, escribe la clave igualmente (deja constancia de que se preguntó).
   - Menciona como **ajuste manual** (no preguntes): `"revision": {"excluir": ["hooks/**"]}` saca globs de la heurística de **ruta** de la lente (para repos cuyos ficheros inocuos casen los stems, p. ej. hooks llamados `session-*.sh`) sin sacarlos del escaneo de contenido. Detalle en la skill `adversarial-review` §1 y en `docs/CONVENTIONS.md` regla 9.
   - Idempotente: si `revision.lenteSeguridad` ya existe, resume el valor actual y ofrece cambiarlo.
6. **Resumen final**: tabla corta con lo decidido y dónde vive cada config, y los siguientes pasos naturales (`/pm-cycle <idea>` para la primera iniciativa, o `@analyst` si la idea está verde).

## Reglas
- **Nada de jerga** (no menciones cloudId, manifiestos, etc.); los tecnicismos se resuelven por debajo.
- **No conectes ni publiques nada** en este comando salvo que el usuario acepte el alta guiada de Confluence.
- Respeta decisiones previas: esto **configura**, no fuerza. Cambiar de opinión = relanzar `/setup`.
