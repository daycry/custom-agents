---
design: knowledge-services
estado: aprobado
opcion_elegida: O1
spec: spec.md
evaluation: evaluation.md
plan: improvement-plan.md
---

# Diseno - Knowledge Gate y Kwipu

| Opcion | Decision |
|---|---|
| O1 | Markdown canonico + Curator + export Kwipu derivado. **Elegida.** |
| O2 | Kwipu como almacen primario. Descartada: no hay curacion ni revision Git. |
| O3 | Graphiti primero. Descartada: aumenta operacion y no resuelve primero la documentacion. |

## Modelo

```text
docs/knowledge/{candidates/{pending,needs_changes,rejected},approved/{decisions,patterns,constraints,heuristics,failures,corrections,skills,tools,cases}}
  -> schema/index validator -> kwipu exporter -> .claude/knowledge-services/kwipu-export
```

`approved/` es versionado y canonico. El export contiene Markdown autocontenido, enlaces, frontmatter y `manifest.json`; se publica desde staging de forma atomica y se puede borrar. Kwipu indexa solo ese directorio.

`documenter` retorna propuestas con categoria, fuentes y evidencia. `knowledge-curator` es el unico escritor de candidatos y aprobados; contradicciones, cambios de taxonomia y reglas de alto impacto requieren confirmacion humana. Los hooks no hacen red.