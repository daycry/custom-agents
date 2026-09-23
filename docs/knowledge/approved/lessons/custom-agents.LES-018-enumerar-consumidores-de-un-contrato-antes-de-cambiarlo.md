---
id: custom-agents.LES-018
category: LESSON
version: 1
estado: aprobado
evidencia: validated_case
project: custom-agents
scope: project
source: agent
confidence: medium
fuentes:
  - docs/roadmap/2026-09-15-graphiti-memory/tasks.md (Cierre de la Fase 3, orquestador 2026-09-22 — «Lección para la retro»)
  - docs/roadmap/2026-09-15-graphiti-memory/tasks.md (gaps #119, #122, #133, #137, #148, #152 — consumidores de `verify()`: `puede_leer()`, `/doctor`, `knowledge-sync.py --check`)
  - docs/roadmap/2026-09-15-graphiti-memory/tasks.md (escenario reproducible del gap #133: los tres veredictos y sus tres consumidores)
tags:
  - area:knowledge-services
  - agente:implementer
  - tipo:proceso
curador: knowledge-curator
fecha_aprobacion: 2026-09-23
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

---

*Curado el 2026-09-23 por `knowledge-curator` (`/dev-cycle` Fase 4-bis, `graphiti-memory`): la cita del cierre de la Fase 3 y los seis gaps verificados en el ledger (existen, y el escenario del gap #133 «los tres veredictos y sus tres consumidores» es reproducible). **Categoría corregida de `GOTCHA` a `LESSON`** (P2): es una regla de proceso sobre cómo cambiar un contrato, no una trampa de herramienta o entorno — misma familia que `LES-016` del corpus legado (cada estado intermedio tiene dueño), a la que complementa: allí el dueño de cada estado, aquí el mapa de quién lee cada valor. El nivel `validated_case` se sostiene: el patrón se repitió en dos Fases (2 y 3) y se cerró con tests dedicados y mutantes por consumidor (cierre de la Fase 3).*
