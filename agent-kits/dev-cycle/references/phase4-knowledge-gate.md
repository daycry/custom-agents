## Fase 4-bis — Knowledge Gate (siempre tras QA verde y `documenter`, agente `knowledge-curator`)
Tras cerrar la Fase 4, comprueba los candidatos de la iniciativa bajo
`docs/knowledge/candidates/{pending,needs_changes}/`: pueden proceder de architect,
planner, implementer, qa, documenter, debug-root-cause, el usuario o el puente de casos,
siempre propuestos mediante `knowledge-curation.py`. `rejected/` es terminal y no dispara
esta fase. Si hay alguno pendiente, invoca **knowledge-curator** para juzgar categoría
exacta, evidencia, fuentes, tags, lista negra y contradicciones con approved y legado
aceptado pertinente; las de alto impacto o contradictorias requieren resolución humana.

- **Handoff y retoma.** Como dueño del ledger, registra las rutas candidate/SHA
  explícitas devueltas por propose en el único bloque de `knowledge-write.md`
  antes de entregar propuestas a apply. Conserva los handoffs de design al pasar
  por planner. Tras apply/recover, incorpora sólo el operation-id real devuelto
  por Curator; sin recibo mantiene pendiente. No infieras identidades ni cambies
  asociaciones conflictivas. Las propuestas tardías de retro usan el mismo
  handoff; productores, Curator y servicio no ganan permisos sobre roadmap.
- **Persistencia única.** `curator-gate.py` conserva evaluación readonly y códigos;
  Curator aplica por `knowledge-curation.py` con SHA esperado, motivo e ID final obligatorio
  al aprobar. El servicio persiste los bytes; el rol no escribe, mueve o borra memoria
  manualmente ni promueve ADR/GOT/LES legacy. Sin servicio o recibo completo, deja ruta/ID
  u operation-id y estado pendiente visibles, sin fallback Write/Edit.
- **Omisión honesta.** Sin candidatos, di una línea ("sin candidatos de conocimiento que curar")
  y continúa a Fase 5. No es un gap ni bloquea el cierre. Una propuesta que no pudo persistirse
  se informa como tal; no se presenta como ausencia de propuestas.
- **Kwipu/Graphiti nunca condicionan el cierre.** El servicio deja approved correcto y
  Curator muestra el recibo o una operación pendiente explícita. La exportación por
  `knowledge-sync.py` sigue asíncrona y reconstruible; su fallo se anota y no detiene el ciclo.
- **Handoff tardío de retro.** La retro de Fase 6 ocurre después de este Gate: sus propuestas
  entregan un handoff explícito al Curator o quedan con ruta/ID y pending visibles.
  QA, revisión y cierre de retro no aprueban memoria; accepted legacy no equivale a approved.
- Curator y el servicio no tocan roadmap ni código del proyecto; el orquestador
  conserva únicamente el handoff explícito en su ledger. El servicio sólo persiste memoria.
