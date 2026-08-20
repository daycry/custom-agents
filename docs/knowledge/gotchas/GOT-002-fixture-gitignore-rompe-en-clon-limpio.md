---
id: GOT-002
tipo: gotcha
area: Tests / fixtures
estado: aceptada (validada: usuario, 2026-08-20)
fuente: docs/roadmap/2026-08-20-confluence-policy/tasks.md (gap I1) vía retro.md
---

## Un fixture bajo un patrón de `.gitignore` queda sin versionar y la suite pasa en local pero rompe en clon limpio/CI

- **Síntoma:** la suite `tests/test_confluence_scope.py` pasaba completa en el working tree del
  desarrollo, pero fallaba entera en un clon limpio del repo (reproducido por la revisión
  adversarial de `confluence-policy`, gap I1).
- **Causa raíz:** el fixture `tests/fixtures/confluence-scope/docs/security-scan/finding.md` caía
  bajo el patrón `**/security-scan/` de `.gitignore` (pensado para hallazgos reales, no para
  fixtures) y nunca llegó a versionarse — presente en local, ausente en cualquier clon. Ningún
  test lo detecta: el fichero *existe* donde corre la suite.
- **Qué hacer en su lugar:** al añadir fixtures cuyo path imite carpetas sensibles/ignoradas,
  verificar con `git ls-files <ruta-del-fixture>` que quedaron trackeados (y añadir la excepción
  `!tests/fixtures/**` si hace falta). Idealmente, verificar la suite también en un clon limpio.
- **Evidencia / fuente:** [`docs/roadmap/2026-08-20-confluence-policy/tasks.md`](../../roadmap/2026-08-20-confluence-policy/tasks.md)
  (T-09, gap I1; commit `5f740cc`; verificación de clon limpio en el cierre de Fase 4) — costó un
  intento de revisión. Contexto en [`retro.md`](../../roadmap/2026-08-20-confluence-policy/retro.md).

`estado: aceptada (validada: usuario, 2026-08-20)`
