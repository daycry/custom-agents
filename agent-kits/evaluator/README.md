# agent-kits/evaluator — toolkit privado del agente `evaluator`

Plantilla para generar evaluaciones/presupuestos a partir de un documento de toma de requerimientos. Uso interno del agente `evaluator`.

- `templates/evaluation.md` — plantilla de la evaluación (cuadro de mando, requerimientos recibidos, evaluación por característica, comparativa, presupuesto total, recomendación, handoff a planner).
- `assets/doctrina/` — las **9 lecciones de estimación/calibración** (`LES-001…009`) como **doctrina del plugin**: lo que el `evaluator` consulta el primer día en cualquier proyecto (`knowledge-find.py --doctrina --area estimacion`). Ver la sección de abajo.

Las evaluaciones generadas se guardan en `docs/roadmap/<fecha>-<slug>/` del proyecto, **no** aquí.

**Documentación completa:** [`docs/agents/evaluator.md`](../../docs/agents/evaluator.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)

## Doctrina del plugin — `assets/doctrina/` (iniciativa `memory-retrieval`, T-15)

**Criterio, aplicado entrada por entrada:** una entrada de `docs/knowledge/` de este repo es **doctrina del
plugin** si es **cierta para cualquier proyecto que use estos agentes**, no solo para este repo. Lo demás es
memoria de ESTE proyecto y se queda en `docs/knowledge/`. La doctrina viaja como asset del plugin — `agent-kits/`
llega en las dos formas de instalación (plugin y copia como `.claude/`), `docs/` no — y es el fondo con el que el
`evaluator` estima **el primer día**: `python3 "$SHAREDKIT/knowledge-find.py" --doctrina --area estimacion --limit 0`.
La memoria del proyecto consumidor **nace vacía** y nadie copia nada a su `docs/knowledge/`: `--doctrina` lee los
assets, y sin la bandera un proyecto sin memoria devuelve 0 aciertos (spec CA-21).

| Entrada | ¿Doctrina? | Por qué |
|---|---|---|
| `LES-001`, `LES-002`, `LES-003`, `LES-004`, `LES-005`, `LES-006`, `LES-007`, `LES-008`, `LES-009` (área «Estimación / calibración») | ✅ | medidas sobre este plugin, pero ciertas para quien estime con estos agentes: el coste está en la revisión, medir cambia el diagnóstico, calibrar cambia cifras publicadas, la prosa se mide en minutos, TDD encarece ejecución y abarata revisión, la spec previa reduce coste, separa lo que mides de lo que vendes, presupuesta el coste de proceso aparte, la revisión es la partida grande |
| `LES-010` (revisión adversarial como skill) | ❌ | decisión de diseño de ESTE plugin, ya materializada en `skills/adversarial-review/` |
| `LES-011`, `LES-012`, `LES-013` (evals, release, elección de pieza) | ❌ | proceso de desarrollo de ESTE plugin; un consumidor no desarrolla el plugin |
| `LES-014` (comentarios de Jira firmados por script) | ❌ | integración concreta de `jira-sync`, ya cableada en la skill |
| `ADR-*`, `GOT-*` | ❌ | decisiones y trampas de este repo; lo universal que contienen ya vive en las skills y fragmentos que viajan (p. ej. `GOT-005` → snippet de codificación en cada script) |

**Una sola fuente.** Los 9 ficheros de `assets/doctrina/` son copias **byte a byte** de `docs/knowledge/lessons/LES-001…009`
y `tests/test_doctrina_viaja.py` lo exige (mismo patrón que las copias `.MANUAL-COPY`). Para cambiar una lección:
edita la de `docs/knowledge/lessons/` y copia el fichero. La carpeta no lleva README: contiene exactamente las 9.
No viaja en el paquete portable «solo skills» (`scripts/export-skills.py`): sin `evaluator` no hay quien la aplique.
