---
plan: catalog-capabilities
estado: en-progreso
creado: 2026-10-07
spec: spec.md
evaluacion: evaluation.md
test-plan: test-plan.md
---

# Plan de comparación e integración funcional

Base publicada: 6187b12. Rama feat/catalog-capabilities, sin integración en main.
Ledger canónico tasks.md; las fichas y matrices documentan decisiones, no crean
otro registro de progreso. Cada fase conserva un ciclo de revisión acotado y
los veredictos anteriores. Los tests no sustituyen la lectura de las piezas.

| Fase | Tareas | Entrega |
|---|---|---|
| 1. Comparación | T-01…T-07 | Corpus reconciliado, contratos actuales y fichas semánticas completas con diferencias útiles y destinos propios |
| 2. Integración | T-08…T-13 | Diseño consolidado, guardias/despacho nativos, capacidades opcionales, workflow y panel coherentes |
| 3. Verificación y cierre | T-14…T-16 | QA funcional/nativo, limpieza/documentación y publicación comprobada |

T-01 enumera también soporte y control panel; T-03…T-07 leen cuerpos, recursos
y callers, no solo resúmenes extraídos. La auditoría de skills incluye todos los
dominios del corpus; su incorporación concreta se decide por utilidad y solape.
La memoria se compara aquí y se mide en fase 4 antes de modificar su gobierno.

## Prioridad operativa del 2026-10-08

Por petición del usuario, T-03/T-10 quedan aplazadas en 79/293 skills
evaluadas. Se priorizan hooks, comandos, dashboard y memoria según
[operational-priorities.md](operational-priorities.md). T-02/T-06/T-07
alimentan primero el diseño y entrega de los bloques pertinentes; T-05 se
aplica a los comandos de cada bloque. T-08/T-11/T-13 y sus verificaciones
dependen del contenido que utilizan, sin esperar a todas las skills,
agentes o integraciones opcionales. Se conserva la aceptación global de
las 16 tareas, incluida la comparación pendiente para cuando se retome.

T-08 traduce diferencias verificadas a un diseño sin duplicar roles ni gates.
T-09 aborda guardias y contratos nativos antes de ampliar automatizaciones.
Las tareas de integración pueden agrupar piezas relacionadas, conservando
trazabilidad por ID y contratos de contenido. Una retirada exige destino de
todos los criterios útiles y actualización de sus consumidores en la misma tarea.

T-14 separa pruebas de activación, comportamiento y carga real del runtime.
T-16 verifica el primer push de entrega y después publica el cierre documental,
para registrar evidencia observada y evitar afirmaciones de publicación futura.
Las pruebas y decisiones pendientes no se convierten en deuda automáticamente.


## Cómo verificar conservación y recuperación local

El BLOQUE20 aplica el [contrato de recuperación local](comparisons/memory-local-recovery-contract.md) a las macros existentes T-07/T-08/T-09/T-11/T-13/T-14/T-15. T-16 conserva el cierre global pendiente. La selección exige doce casos N01–N09 y una regresión RED/GREEN del parser para enlaces inline entrecomillados.

Primero congelar contrato, fuentes, fixture y receta. Corregir el parser con evidencia del autor; después revisar el diff y ejecutar QA integrada Windows/Linux. Conservar fallos previos, identidad de hijos, barreras, manifiestos y hashes antes/después. La cobertura oficial del diff y qa-gate mantienen sus puertas existentes.

Antes de la QA integrada, la aceptación permanecía `UNKNOWN` hasta revisar la evidencia real; el recibo ROOT actual acepta únicamente el Bloque20. No cambia los estados macro ni añade comandos de backup, hooks, backends o dependencias. Los resultados de consulta publicados siguen siendo evidencia de su experimento original; no acreditan restauración ni cortes de sesión.

QA del Bloque20 aceptada por ROOT únicamente para la selección congelada sintética Windows/Linux, según la [evidencia de revisión y QA](testing/memory-local-recovery-review-evidence.json). La verificación correctiva Linux conserva el gate 1 original y aplica un nuevo gate 0 a los mismos artefactos, sin repetir tests. Los doce casos de recuperación y seis guardias pasan sin skips en ambos OS; fuente 985, coverage 212/235 y diff 7/7 permanecen comprobados. No cambia ninguna macro, QA19 ni cierre global; publicación, tres hosts nativos, escala y eficacia comparativa siguen pendientes.
