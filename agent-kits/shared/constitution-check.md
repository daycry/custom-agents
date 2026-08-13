<!--
  FRAGMENTO COMPARTIDO: constitución del proyecto (fuente única).
  Lo referencian los agentes que ESCRIBEN (analyst, evaluator, planner, implementer,
  qa, documenter) y la revisión adversarial de /dev-cycle (lente A).
  Si cambias la regla aquí, cambia para todos — no la dupliques en prompts.
-->

# Constitución del proyecto — paso compartido

**Antes de trabajar**, comprueba si el proyecto consumidor tiene constitución:

```bash
[ -f docs/CONSTITUTION.md ] && echo "constitución presente"
```

- **Si existe `docs/CONSTITUTION.md`:** léela (es corta por diseño, 1-2 páginas) y **respétala** en todo lo que produzcas. Cuando un principio condicione una decisión tuya, **cítalo** ("por Constitución §2, no accedo a la BD desde el controlador"). Si la tarea que te piden **contradice** un principio explícito, dilo antes de ejecutar: el usuario decide si la tarea cambia o si la constitución se revisa (vía iniciativa, nunca de tapadillo).
- **Si NO existe:** continúa sin ella — es **opt-in** y su ausencia nunca bloquea. No la crees por tu cuenta; la ofrece `/setup` (plantilla en `agent-kits/shared/templates/CONSTITUTION.template.md`).

**Para la revisión adversarial (lente A):** la constitución, si existe, es una entrada más de la revisión. Un diff que **viole un principio EXPLÍCITO** del fichero es **gap de corrección**, citando la línea del principio violado. Lo que no esté escrito ahí es estilo, no gap — no inventes principios.
