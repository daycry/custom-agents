---
category: GOTCHA
evidencia: validated_case
fuentes: [docs/roadmap/2026-09-15-graphiti-memory/tasks.md]
tags: [area:knowledge-services, agente:implementer, tipo:proceso]
project: custom-agents
scope: project
source: agent
confidence: medium
---
# Un veredicto de verificación con varios consumidores: enumerarlos antes de cambiar el contrato

En la Fase 3 de `graphiti-memory` (T-07/T-08), el veredicto de `verify()` del adaptador Graphiti
ganó un tercer valor (`incompleto`, cuando el tope de lectura recorta la ventana de `get_episodes`)
sin mapear antes quién más lo consume. Cada ronda de corrección abrió un consumidor nuevo del
mismo veredicto que la anterior no había tocado: `puede_leer()` (gap #133), `/doctor` (gaps
#119/#122/#137/#148), `knowledge-sync.py --check` (gap #133 en `knowledge-sync.py`), hasta
necesitar un cuarto veredicto (`no_verificable`, gap #152) y cuatro rondas de corrección (fix1 a
fix4) sobre la misma Fase.

**Regla:** al ampliar el conjunto de valores de un veredicto/estado que ya tiene más de un
consumidor, enumerar TODOS los consumidores conocidos del contrato (grep de quien lo lee, no solo
de quien lo escribe) antes de tocarlo, y actualizarlos en la misma ronda — no dejar que cada
consumidor se entere por una revisión distinta.

Evidencia: `tasks.md`, sección «Cierre de la Fase 3 (orquestador, 2026-09-22)»: *"Lección para la
retro: la Fase 3 heredó de la Fase 2 el patrón «cada corrección abre un consumidor nuevo del mismo
veredicto» (verify → puede_leer/doctor/--check): conviene enumerar los consumidores de un contrato
ANTES de cambiarlo."*; gaps #119/#122/#133/#137/#148/#152 del ledger de la Fase 3.
