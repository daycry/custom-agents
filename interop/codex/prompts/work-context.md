---
description: "Selecciona las guías del plugin por rol, fase, stack y área desde manifiestos locales; reconoce agentes, skills, personas, tools y MCP propios, mostrando procedencia, conflictos y referencias sin iniciar otro ciclo ni ejecutar código del proyecto."
argument-hint: "<paquete> [rol] [stack] [área] [runtime]"
---
<!-- GENERADO por scripts/export-interop.py desde commands/work-context.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/work-context.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: se delega pidiéndolo en lenguaje natural y nombrando al agente (`reviewer`, `implementer`…), y los agentes custom se copian a `.codex/agents/`.
> Las skills se invocan mencionándolas con `$nombre`. Todo lo demás (puertas, artefactos, ledger) no cambia.

# /work-context — criterios para la tarea

Objetivo y filtros: **$ARGUMENTS**. Resuelve `agent-kits/shared/` con las raíces
del runtime, como indica `agent-kits/shared/capability-check.md`. Usa ese método
y ejecuta capability-route con el paquete, rol/fase y filtros pertinentes.
Aplica también su sección de extensiones usando project-pieces del mismo bundle,
la raíz de proyecto, el paquete como cwd y el runtime real de la sesión.

Muestra stack detectado/declarado, fuentes, advertencias y mapas seleccionados.
Si faltan filtros, usa el rol de la tarea y sus áreas explícitas; sin tarea,
usa implementer y ningún área adicional. Lee referencias solo si el usuario
pide aplicarlas. Resume las extensiones pertinentes con ID, tipo, runtime y fuente;
explica conflictos, propiedad y límites. Los MCP se muestran como declaraciones,
y las tools propias como fuentes; contrasta disponibilidad con la sesión antes
de usarlas. Registra la selección de una tarea con los campos del método común.
No modifiques configuración ni instales recursos.

La salida es contexto para pm/dev-cycle o un rol manual. No inicia otra cadena,
no calcula calidad y no genera piezas de project-specialization. Sin selector,
informa del límite y continúa con las guías disponibles.
