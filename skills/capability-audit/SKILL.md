---
name: capability-audit
description: >
  Auditoría semántica de skills, agentes y comandos: utilidad, solapes, vigencia,
  coste de carga, recursos y dueño de cada artefacto, con evidencia por pieza.
  Úsala cuando el usuario diga "audita capacidades", "limpia el catálogo"
  o "qué skills debemos consolidar".
---

# Auditar utilidad y coherencia

Delimita piezas y raíz autorizadas. Usa plugin-panel para inventario y el linter
para estructura; lee cuerpos, callers y recursos de las piezas evaluadas.
Lee [método y ficha](references/method.md) **solo** al auditar; registra revisadas,
no revisadas y excluidas por alcance por separado. Sigue con trabajo autorizado;
una recomendación de baja no concede permisos sobre archivos ajenos.

## Antes del veredicto

Formato: `agent-kits/shared/rationalization-table.md`.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Tiene un buen nombre» | El nombre no acredita valor ni recursos correctos. | Leo el cuerpo, los recursos y los callers reales. |
| «El inventario está completo» | Enumerar no equivale a evaluar cada capacidad. | Separo las piezas inventariadas y las evaluadas. |
| «No tiene uso registrado» | La ausencia de medición no demuestra uso cero. | Compruebo que exista una medición compatible. |
| «El linter pasó» | Estructura válida no demuestra utilidad vigente. | Verifico utilidad y vigencia además de estructura. |
| «Es parecido a otra skill» | Un solape aparente puede ocultar contenido único. | Comparo contenido y contratos de ambas piezas. |
| «Lo quitamos y listo» | Una baja puede dejar dependencias y exports rotos. | Actualizo dependencias, evals, exports y docs. |

## Salida y evidencia

Salida: decisión por pieza con defecto/valor concreto, fuente y validación;
conservar, ampliar, actualizar, consolidar o retirar. Una decisión de alcance
no es un score de eficacia. No crea otro ledger ni aprueba memoria.

| Referencia | Cuándo leerla |
|---|---|
| [Método y ficha](references/method.md) | Evaluación de utilidad y propuesta de consolidación |
