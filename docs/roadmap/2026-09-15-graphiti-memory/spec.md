---
spec: graphiti-memory
estado: aprobada
creado: 2026-09-15
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
---

# Memoria relacional temporal con Graphiti

## Objetivo

Anadir Graphiti como proyeccion relacional y temporal opcional del conocimiento ya aprobado por `knowledge-services`. Markdown/Git permanece canonico; Graphiti solo recibe eventos derivados, conserva `knowledge_id` y permite relacionar evidencia, versiones, sucesiones y contradicciones.

## Dependencia de entrada

No comienza implementacion hasta que `knowledge-services` entregue esquema validado, `docs/knowledge/approved/`, Curator y exportacion Kwipu. Si esa puerta no esta completa, este plan permanece `borrador`.

## Alcance

- Configuracion opt-in de endpoint, grupo logico y telemetria desactivable.
- Adaptador determinista `approved/` -> episodios Graphiti, con idempotencia y procedencia, **filtrado por `routing.graphiti` de `.claude/knowledge-services/taxonomy.json`** (mismo fichero que define categorias y enrutado Kwipu en `knowledge-services`): solo sincroniza las categorias que el proyecto declare `true`.
- Modelo inicial: `Knowledge`, `Evidence`, `Case`, `Constraint`, `Failure`, `Correction` y relaciones `SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`, `MITIGATES`, `APPLIES_TO`.
- Router de lectura que selecciona Graphiti solo para consultas relacionales o temporales y conserva fallback Markdown/Kwipu.
- Salud, desfase, reindexacion explicita y pruebas con backend local.

## Fuera de alcance

- Capturar prompts, conversaciones, TODOs o logs; llamadas de red en hooks; Graphiti como fuente de verdad; escritura directa por agentes; multi-proyecto; sincronizacion cloud; entrenamiento Ollama.

## Criterios de aceptacion

- [ ] CA-01 - Solo entradas `approved` validas crean episodios Graphiti con `knowledge_id`, version y ruta fuente.
- [ ] CA-02 - Repetir sincronizacion no duplica nodos/relaciones ni elimina historial.
- [ ] CA-03 - Las consultas temporales y de relaciones incluyen procedencia y estado vigente/sustituido.
- [ ] CA-04 - Endpoint apagado, modelo local invalido o backend sin datos degradan sin bloquear el ciclo.
- [ ] CA-05 - Los agentes no pueden escribir directamente; solo Curator y sincronizador aprobado.
- [ ] CA-06 - Kwipu conserva preguntas documentales y Graphiti no se consulta por defecto.
- [ ] CA-07 - Una categoria sin `routing.graphiti: true` en `taxonomy.json` nunca genera episodios (fail-closed), y el sincronizador no asume un routing universal para todo `approved/`.

## Decisiones confirmadas (usuario, 2026-09-15)

1. Graphiti viene despues de la gobernanza Markdown/Kwipu, no en paralelo.
2. Su funcion es memoria relacional/temporal, no captura indiscriminada de agentes.
3. Un proyecto consumidor es un unico limite de aislamiento; el grupo Graphiti evita mezclar instalaciones que compartan Docker.