---
spec: training-data-services
estado: aprobada
creado: 2026-09-16
actualizado: 2026-09-16
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
---

# Captura de casos y ensamblado de dataset para entrenamiento local

## Contexto y objetivo

Algunos proyectos que usan este plugin (por ejemplo, un pipeline de generacion procedural con Blender/Ollama) ejecutan tareas repetibles con una forma objetiva o semi-objetiva de medir el exito (simulacion, metricas, tests). Con volumen suficiente, esos proyectos quieren conservar cada intento — peticion, contexto, trayectoria, metricas, validacion — para poder ensamblar despues un dataset y entrenar un modelo local mas barato que sustituya al modelo grande en tareas rutinarias.

Esta iniciativa da al plugin un mecanismo GENERICO para capturar esos "casos" de forma determinista y versionada, y ensamblar un dataset a partir de los casos aprobados por un humano. El plugin **no** sabe nada del dominio (no conoce Blender, geometria ni ninguna metrica concreta) y **no** ejecuta entrenamiento, ni sirve modelos, ni corre benchmarks: eso es siempre responsabilidad del proyecto consumidor.

Es la tercera pieza del area de conocimiento, junto a `knowledge-services` (memoria curada) y `graphiti-memory` (proyeccion temporal), pero resuelve una pregunta distinta: `knowledge-services` responde "que sabemos con certeza" (poco volumen, curado); esta iniciativa responde "que intentamos y que paso" (mucho volumen, sin curar en el momento de captura, se conserva todo incluidos los fallos).

## Relacion con las otras dos iniciativas (una sola direccion)

```text
caso ejecutado (peticion + contexto + trayectoria + metricas + validacion)
  -> case store (esta iniciativa)
       -> humano marca Gold
            -> PUEDE proponerse como candidato de conocimiento (knowledge-curator, knowledge-services)
                 -> approved -> Kwipu / Graphiti
```

Un caso Gold puede proponerse como candidato; el conocimiento aprobado **nunca** alimenta hacia atras al case store (evita contaminar el dataset con su propio resultado curado — "leakage").

## Alcance

- Configuracion opt-in `.claude/knowledge-services/training.json`: activado/desactivado, ruta del case store (declarada por el proyecto, no un nombre fijo del plugin), esquema de IDs (`family`/`variant`/version), y si los casos Gold pueden proponerse como candidato de conocimiento.
- Esquema de "caso": peticion literal, contexto, restricciones, trayectoria (plan, tool calls, parametros, resultados — nunca chain-of-thought privado), metricas (JSON ya calculado por el proyecto), validacion (`pending`/`approved` [Gold]/`needs_changes`/`rejected`) y referencias a artefactos finales.
- Recorder determinista: ID estable, nunca sobrescribe una version existente, nunca borra un caso rechazado en silencio.
- Marcar un caso como Gold es **siempre una accion humana explicita** (el recorder exige una confirmacion humana; ningun script ni agente puede marcarlo Gold por si solo).
- Ensamblador de dataset: exporta SOLO casos Gold, con deduplicacion, particion de benchmark reservada explicitamente y aviso de near-duplicates entre versiones — nunca ejecuta ni orquesta el entrenamiento en si.
- Puente opcional hacia `knowledge-curator` (`knowledge-services`): un caso Gold puede proponerse como candidato; la aprobacion sigue las mismas reglas del Knowledge Gate (nunca automatica).
- `/doctor` informa si esta activado, cuantos casos hay por estado y si el dataset esta desactualizado — nunca bloquea.

## Fuera de alcance

- Cualquier metrica o herramienta de dominio (medir pendiente, simular una bola, `bpy`, etc.): siempre codigo del proyecto consumidor, nunca del plugin.
- Marcar Gold automaticamente (por un LLM o por una regla): prohibido por diseno.
- Ejecutar fine-tuning/SFT/LoRA, servir Ollama o correr el benchmark: siempre fuera del plugin.
- Un agente "case-curator": no se crea; marcar Gold es una accion humana simple, no un rol que decide con criterio propio.
- Captura automatica de conversaciones/trayectorias sin llamada explicita del codigo del proyecto (no hay hook que capture esto solo).
- Aplicar esto al propio ciclo de `custom-agents` (dogfooding sobre `tasks.md`/revision/qa): posible extension futura, no entra en esta entrega.

## Criterios de aceptacion

- [ ] CA-01 - Sin `training.json` o con `enabled: false`, el ciclo actual (dev-cycle, knowledge-services, graphiti-memory) funciona identico: cero impacto si no se activa.
- [ ] CA-02 - El recorder nunca sobrescribe un `case_id` + version existente; un caso rechazado se conserva, nunca se borra en silencio.
- [ ] CA-03 - El ensamblador de dataset excluye por diseno cualquier caso que no este marcado Gold por un humano.
- [ ] CA-04 - Ninguna metrica, herramienta o logica de validacion de dominio vive en el plugin; el recorder solo consume JSON ya calculado por el proyecto.
- [ ] CA-05 - Un caso Gold puede proponerse como candidato de conocimiento, pero nunca se aprueba automaticamente por venir de un caso Gold.
- [ ] CA-06 - El ensamblador reserva una particion de benchmark y senala near-duplicates entre versiones antes de exportar.
- [ ] CA-07 - `/doctor` informa el estado de esta capacidad sin bloquear nunca el ciclo.
- [ ] CA-08 - Esta entrega no ejecuta ni orquesta fine-tuning, ni sirve modelos, ni corre benchmarks.
- [ ] CA-09 - El recorder redacta secretos evidentes en la trayectoria ANTES de escribir a disco, reutilizando la misma logica de `journal.py` (una sola fuente de verdad).
- [ ] CA-10 - La deduplicacion detecta near-duplicates entre versiones sin embeddings ni servicio externo, con la misma tecnica de shingles que ya usa `code-health.py`.
- [ ] CA-11 - La particion de benchmark nunca dejar una version de una familia en train si otra version de la MISMA familia esta en el benchmark.
- [ ] CA-12 - Un caso con `outcome: failure` seguido de una version `outcome: corrected` conserva la relacion (`supersedes_case`) en el dataset ensamblado.

## Decisiones confirmadas (recomendacion tecnica aplicada, 2026-09-16)

1. **Nombre**: `training-data-services`.
2. **Dependencias**: depende de `knowledge-services` (puente Gold -> candidato); NO depende de `graphiti-memory`.
3. **Ubicacion**: skill propia `skills/training-data-services/`, separada de `knowledge-services`. El ciclo de vida de un caso (alto volumen, sin curar) es distinto del de un candidato de conocimiento (bajo volumen, curado); mezclarlos repetiria el problema de acoplar dos cosas de naturaleza distinta.
4. **Gold siempre humano**: el recorder EXIGE un flag explicito (`--approved-by-human`) para la transicion a `approved` (Gold); sin el, rechaza la operacion. `needs_changes`/`rejected` los puede fijar el codigo del propio proyecto sin ese flag, porque no son promociones.
5. **Cero acoplamiento de dominio**: ningun adaptador de Blender/geometria entra en `custom-agents`; el plugin solo aporta el mecanismo generico (esquema, recorder, ensamblador, puente al Curator).

## Decisiones tecnicas adicionales (ver `design.md` para el detalle)

- **Formato de trayectoria compatible con chat/SFT** (`role`/`content`/`tool_calls` por turno), para que el ensamblado de dataset sea una conversion directa, sin atarse a un framework de entrenamiento concreto.
- **Redaccion de secretos reutilizada**: se extrae la logica ya existente y probada de `journal.py` (`redactar()`) a un modulo compartido (`agent-kits/shared/redact.py`) que usan tanto el journal como el recorder de casos — una sola fuente de verdad para algo sensible a seguridad.
- **Deduplicacion determinista sin embeddings**: mismo principio que ADR-013 (sin dependencias, sin servicio externo) y la misma tecnica que ya usa `code-health.py` para duplicados de codigo (shingles/Jaccard), aplicada al contenido variable de cada caso.
- **Anti-leakage por familia**: la particion de benchmark reserva familias/variantes ENTERAS fuera del entrenamiento, nunca versiones sueltas de una familia que ya esta en train.
- **Pares fallo -> correccion como dato de primera clase**: el esquema declara `outcome` (`success`/`failure`/`corrected`) y `supersedes_case`, para conservar la relacion entre un intento fallido y su correccion posterior — es el dato de mas valor segun la propia experiencia de dominio citada.

## Supuestos

- El proyecto que active esto ya tiene su propia forma de calcular metricas y decidir "needs_changes"/"rejected"; el plugin no la sustituye ni la valida semanticamente, solo la forma (JSON valido, campos requeridos).
- El volumen de casos puede ser alto (cientos por sesion); el recorder debe ser barato y determinista, sin analisis semantico caro por caso.
- La decision de activar esta capacidad es por proyecto; el plugin sigue funcionando igual para quien no la active.
