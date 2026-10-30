# T-18: conservar el índice completo

Decisión **no-go para el recorte productivo**, confirmada el 2026-10-30.
T-18 se cancela por su condición aprobada en T-08. Claude Code, Codex y OpenCode
mantienen el índice completo; no se cambia configuración global ni instalación.

La evidencia [nativa autenticada de F1](t06-native-visibility-authenticated-2026-10-29.json)
acredita que Claude Code ve 27 skills y sus descripciones. La sesión permitió
solo la herramienta Skill y no la usó. Visibilidad de descripciones y activación
correcta ante tareas son mediciones distintas: ese recibo no contiene una
comparación de resultados con índice completo frente a nombres o ausencia de índice.

No hay evidencia nueva que satisfaga la condición «sin degradar la activación».
Las evals literales y las pruebas deterministas del índice comprueban sus
contratos, pero no sustituyen esa comparación. No se presenta como demostrado
el ahorro aproximado de 650 tokens del esqueleto ni se marca implementado un
recorte inexistente. Una reconsideración futura requiere corpus y resultados
comparables en sesiones nativas, con índice como única variable.

Se ejecuta sin cambios la suite `agent-kits/shared/test_skill_index.py`; su resultado
se registra en las notas de T-18 y en el recibo de decisión. TDD n/a: cancelación
condicional sin código productivo nuevo. Las instrucciones y el índice actual
siguen sujetos a la revisión y QA de fase T-19.
