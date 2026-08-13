---
description: Onboarding del plugin en un proyecto — en UNA pasada guiada crea la config compartida de presupuesto (.claude/rates.json), decide los opt-ins de Confluence y Jira, ofrece la constitución del proyecto (docs/CONSTITUTION.md) y las opciones de disciplina de desarrollo (.claude/dev.json: TDD, worktrees, subagentes), en vez de que cada skill pregunte por su cuenta la primera vez. Idempotente; se puede relanzar para cambiar decisiones.
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
   Escribe `.claude/dev.json` con lo elegido (p. ej. `{"tdd": false, "worktree": false, "subagentes": false}`). Si ya existe, resume y ofrece cambiar.
6. **Resumen final**: tabla corta con lo decidido y dónde vive cada config, y los siguientes pasos naturales (`/pm-cycle <idea>` para la primera iniciativa, o `@analyst` si la idea está verde).

## Reglas
- **Nada de jerga** (no menciones cloudId, manifiestos, etc.); los tecnicismos se resuelven por debajo.
- **No conectes ni publiques nada** en este comando salvo que el usuario acepte el alta guiada de Confluence.
- Respeta decisiones previas: esto **configura**, no fuerza. Cambiar de opinión = relanzar `/setup`.
