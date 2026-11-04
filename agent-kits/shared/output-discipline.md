# Disciplina de salida al orquestador

En un handoff, el detalle vive en los artefactos (`spec.md`, `evaluation.md`,
`improvement-plan.md`, `tasks.md`, `report.md`, docs). No lo repitas en el mensaje.
Devuelve **≤ ~12 líneas** con:

- **Rutas** creadas o modificadas.
- **Cifras** clave: coste, horas, tareas, tests y veredicto disponibles.
- **Estado**, siguiente paso/handoff y cualquier decisión pendiente del usuario.

Evita recapitular pasos o reexplicar el artefacto. La conversación directa con el
usuario queda fuera de este límite: responde con naturalidad y claridad.

## Herramientas y esperas

Conserva logs completos y exit codes; muestra primero resumen y fallos pertinentes,
expandiendo lo necesario para diagnosticar. Usa las esperas nativas para procesos
y CI; no recargues plan/instrucciones por sondeo. Informa al usuario durante la
espera. Un resultado pendiente o resumido no convierte un fallo en verde.
