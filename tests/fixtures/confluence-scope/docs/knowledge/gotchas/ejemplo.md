---
tipo: gotcha
area: Fixture de test
estado: aceptada (validada: usuario, 2026-08-20)
fuente: tests/test_confluence_scope.py
---

# Fichero de fixture

Prueba que el subárbol `docs/knowledge/gotchas/` (un fichero por entrada, `knowledge-split`)
entra en el alcance de Confluence igual que el resto de `docs/knowledge/**` (T-16 de
`knowledge-capture`, D1 de `confluence-policy`: no está en el `exclude`).
