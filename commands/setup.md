---
description: Onboarding del plugin en un proyecto — en UNA pasada guiada crea la config compartida de presupuesto (.claude/rates.json) y decide los opt-ins de Confluence y Jira, en vez de que cada skill pregunte por su cuenta la primera vez. Idempotente; se puede relanzar para cambiar decisiones.
argument-hint: "(sin argumentos)"
---

# /setup — dejar el proyecto listo en una pasada

Evita el onboarding disperso (cada skill preguntando su opt-in la primera vez que se activa).
Una conversación corta y el proyecto queda configurado. **Idempotente**: si ya hay config, muestra
los valores actuales y ofrece cambiarlos.

## Pasos (una pregunta cada vez, en llano)
1. **Presupuesto — `.claude/rates.json`.** Si no existe, créalo desde la plantilla (`agent-kits/evaluator/templates/rates.example.json`) confirmando con el usuario: tarifa €/h, jornada (8/7), ratio de supervisión, margen; y recuérdale que el precio de tokens vigente hay que verificarlo (déjalo a 0 = "a verificar" si no lo sabe). Si existe, resume valores y ofrece ajustar.
2. **Confluence — `.claude/confluence.json`.** Pregunta: "¿Sincronizar la documentación con Confluence? [Sí/No]".
   - **No** → `enabled: false` (no volverá a preguntar).
   - **Sí** → `enabled: true` y, si el conector Atlassian está disponible, ofrece hacer **ahora** el alta guiada (skill `confluence-publish`: espacio + anclaje); si no, deja `enabled: true` y el alta se hará en la primera publicación.
3. **Jira — `.claude/jira.json`.** Pregunta: "¿Volcar los planes a Jira e imputar horas al completar tareas? [Sí/No]".
   - **No** → `enabled: false`.
   - **Sí** → `enabled: true` + pregunta la política al cubrir la jornada (`alCubrirJornada`: preguntar/parar/seguir/banco; default `preguntar`). La jornada ya viene de `rates.json`.
4. **Resumen final**: tabla corta con lo decidido y dónde vive cada config, y los siguientes pasos naturales (`/pm-cycle <idea>` para la primera iniciativa, o `@analyst` si la idea está verde).

## Reglas
- **Nada de jerga** (no menciones cloudId, manifiestos, etc.); los tecnicismos se resuelven por debajo.
- **No conectes ni publiques nada** en este comando salvo que el usuario acepte el alta guiada de Confluence.
- Respeta decisiones previas: esto **configura**, no fuerza. Cambiar de opinión = relanzar `/setup`.
