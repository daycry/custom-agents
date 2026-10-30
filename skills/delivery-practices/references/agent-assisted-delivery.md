# Entrega asistida por agentes

Léela solo cuando haya que decidir cómo repartir trabajo entre agentes y
personas, qué evidencia pedir antes de delegar, o si conviene escalar el modelo
porque una tarea sigue fallando.

No es otro ciclo. Las fases, puertas y estados de despacho son los de
`/dev-cycle`; los criterios y la `Verificación` de cada tarea los fija planner;
la revisión es de `adversarial-review` y el veredicto de pruebas, de qa. Esta
guía solo añade las decisiones que esos métodos dejan al responsable humano.

## 1. Responsabilidades

| Quién | Decide | No decide |
|---|---|---|
| Responsable humano | Aceptación de la spec, riesgo admitido, efectos externos, escalado de modelo, cierre | El veredicto de un script de puerta (lo da el script) |
| Agentes del ciclo | Lo que su rol escribe (plan, código, revisión, informe de qa) | Su propia aprobación, ni ampliar el alcance de la tarea |
| Scripts de puerta | Veredictos deterministas (ledger, alcance, qa, cobertura) | Si el criterio era el correcto |

Un agente que termina en `NEEDS_CONTEXT` o `BLOCKED` está haciendo su trabajo:
esos estados son preferibles a una salida inventada.

## 2. Aceptación antes de delegar

- Criterios de aceptación y `Verificación` (`comando → resultado esperado`)
  escritos antes de despachar la tarea. Si no se sabe qué comando la demuestra,
  la tarea está mal cortada y no se delega todavía.
- Interfaces y datos que la tarea consume o produce, declarados en el brief; el
  agente no los deduce del código cuando existe un contrato.
- Unidad = lo que una `Verificación` demuestra. No hay duración objetivo por
  tarea: el tamaño lo fija el criterio, no el reloj.
- Riesgo declarado por tarea (datos, autorización, efectos externos, rollout).
  Con riesgo alto, la tarea lleva casos de límite y regresión en su
  verificación y la revisión activa las lentes condicionales que correspondan.

## 3. Firma del fallo antes de escalar de modelo

Cuando una tarea falla, primero se clasifica el fallo con su **firma**: comando o
test, error literal, intento, contexto entregado y modelo efectivo. Solo una
clase justifica un modelo más capaz:

| Clase de fallo | Señal en la firma | Acción |
|---|---|---|
| Contexto ausente | El agente pide o inventa un dato que no estaba en el brief | Completar el brief y redespachar; no escalar |
| Operativo | Herramienta ausente, permiso denegado, timeout, red, entorno inestable | Arreglar el entorno; no escalar |
| Especificación ambigua | Dos lecturas razonables del criterio producen salidas distintas | Volver al criterio con el responsable; no escalar |
| Defecto no localizado | El mismo rojo persiste tras arreglos distintos | Causa raíz con `debug-root-cause` antes de otro intento |
| Razonamiento insuficiente | La misma firma se repite con contexto completo, entorno sano y criterio claro | Candidato a escalar |

Escalar es una decisión registrada: el motivo y la firma van al ledger de la
tarea, y el cambio se aplica en `modelos.<agente>` de `.claude/dev.json`, que
`agent-kits/shared/model-tier.py` resuelve para el orquestador. Ese ajuste es
por agente, no por tarea: devuélvelo a su valor cuando la tarea cierre. En
runtimes donde el tier no se traduce, el agente hereda el modelo de la sesión;
no se declara aplicado un tier que el runtime no aplica.

## 4. Continuidad de contexto

Una sesión nueva o una compactación conserva el contrato (ledger, brief,
criterios) y la evidencia ya obtenida (salidas pegadas, firma del fallo). No se
reinicia una sesión a ciegas en mitad de la depuración de un fallo activo: se
pierde la evidencia de descartes y el siguiente intento repite los mismos.

## 5. Coste y comparación medidos

- Coste por tarea con el medidor de uso del plugin
  (`agent-kits/shared/usage-meter.py`); sin medición compatible, el coste queda
  `null`, nunca estimado como si fuera medido.
- Un cambio de modelo, prompt o guía que pretenda generalizarse se compara con
  el protocolo de la skill opcional `outcome-evals` (su protocolo, si está instalada) (mismos casos,
  condiciones y repeticiones). Un éxito tras escalar en una tarea no demuestra
  que el modelo más caro sea mejor en general.

## 6. Indicadores de competencia para delegar

Evidencia observable en el trabajo, revisada por una persona, para decidir cuánto
delegar en un agente o en quien lo supervisa:

| Indicador | Evidencia que lo demuestra |
|---|---|
| Descompone la ambigüedad | Criterios verificables escritos antes de implementar |
| Diseña la verificación | `Verificación` que falla si el criterio no se cumple |
| Reconoce límites | `NEEDS_CONTEXT`/`BLOCKED` o preguntas concretas en lugar de supuestos |
| Controla el riesgo | Efectos externos con aprobación ligada; nada fuera del alcance de la tarea |
| Prueba límites y regresiones | Casos de error, vacío y concurrencia en los tests, no solo el camino feliz |
| Revisa integridad y rollout | Revisión de dos lentes sin `Critical` abiertos; plan de recuperación cuando hay despliegue |

Son indicios para una decisión humana, no una puntuación automática ni un
criterio de evaluación de personas. Sin evidencia, se registran los criterios y
lo pendiente; no se infiere eficacia de un agente ni de un equipo.

Sin el módulo opcional de evaluación, conserva un informe local de los mismos casos, condiciones, repeticiones y métricas observadas; no inventes resultados ni prometas un informe agregado automático.
