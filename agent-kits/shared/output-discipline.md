<!--
  FRAGMENTO COMPARTIDO: disciplina de salida en los handoffs de la cadena.
  Lo referencian evaluator, planner, implementer, qa, documenter (agentes que un
  orquestador — /dev-cycle, /pm-cycle — invoca en cadena).
  Objetivo: el mensaje final de cada agente NO se apila como un informe en el
  contexto del orquestador. El detalle para el humano vive en los ARTEFACTOS.
-->

# Disciplina de salida (mensaje final al orquestador)

Tu **mensaje final** cuando te invoca un orquestador (o el chat principal) es **datos para el siguiente paso, no un informe para el humano**. El detalle ya está escrito en tus artefactos (`spec.md`, `evaluation.md`, `improvement-plan.md`, `tasks.md`, `report.md`, docs…); no lo repitas en el mensaje.

Formato: **≤ ~12 líneas**, con:
- **Rutas** de los ficheros que has creado/modificado.
- **Cifras** clave (coste, horas, nº de tareas, conteo de tests, veredicto…).
- **Estado** y **siguiente paso / handoff**.

Evita: recap de los pasos que has dado, re-explicar el contenido del artefacto, prosa de relleno, felicitaciones. Si algo necesita decisión del usuario, dilo en una línea señalada, no en tres párrafos.

Esto no aplica a la **conversación directa con el usuario** (p. ej. analyst tomando requisitos, o cuando el usuario te invoca suelto y espera una respuesta legible): ahí responde con naturalidad. Aplica cuando eres un eslabón de la cadena y tu salida alimenta a otro agente.
