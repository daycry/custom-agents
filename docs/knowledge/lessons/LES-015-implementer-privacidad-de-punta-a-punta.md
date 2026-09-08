---
id: LES-015
tipo: leccion
area: Proceso / revisión adversarial
estado: propuesta
fuente: 2026-09-04-memory-retrieval/tasks.md#revisión-de-dos-lentes--intento-1-fase-4
---

## implementer

- **Un control de privacidad se prueba de punta a punta, no en la capa donde vive.** En la Fase 4 de
  `memory-retrieval`, el opt-out `<private>` protegía el log crudo del turno (test verde, criterio del ledger
  cumplido literalmente) y aun así el turno privado **volvía** a una entrada versionada por otro camino: el
  `resumen` caía a la transcripción oficial cuando el log estaba vacío. Lo cazaron las Lentes B y C de la
  revisión (gap Critical), no la suite de 17 tests nuevos en verde, porque cada test miraba una capa. Desde
  entonces el criterio se redacta sobre el **resultado observable** («el turno privado no aparece en ningún
  fichero versionado ni en su índice») y el test recorre todos los caminos que alimentan ese fichero (log,
  transcripción, `--enrich`, respuesta de la IA). **Segunda evidencia, misma iniciativa (T-21, gap B1 Critical):** la
  puerta `retro-gate.py` exigía un frontmatter que ninguna de las 7 retros reales del repo tenía — el fixture
  inventaba el formato y la puerta nunca habría abierto; el test pasó a parametrizar sobre `docs/roadmap/*/retro.md`.
  El contrato lo fijan los datos, no el fixture. — *Fuente:* [`2026-09-04-memory-retrieval/tasks.md`](../../roadmap/2026-09-04-memory-retrieval/tasks.md) (T-20 gap 1 · T-21 gap B1) y su [`retro.md`](../../roadmap/2026-09-04-memory-retrieval/retro.md).
