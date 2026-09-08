---
id: GOT-007
tipo: gotcha
area: Tests / CI y fixtures
estado: aceptada (validada: usuario, 2026-09-08)
fuente: docs/roadmap/2026-09-04-memory-retrieval/retro.md (T-21, gaps A1/B2 de la revisión de F5-F6)
---

## La suite de codificación solo descubre scripts VERSIONADOS y exige registrarlos a mano: verde antes de `git add`, roja en CI después

- **Síntoma:** `python3 -m pytest -q tests/test_console_encoding.py` → `281 passed` en local con un script nuevo en el
  árbol; tras comitearlo, la misma suite da **4 failed** (`assert modos` y `KeyError: 'agent-kits/shared/retro-gate.py'`),
  sin nada de Windows en medio: falla igual en CI (Linux). Lo cazaron las Lentes A y B de la revisión, no la pasada
  local «verde» que figuraba en el ledger.
- **Causa:** `descubrir()` recorre `git ls-files` buscando el snippet de reconfiguración de consola (`GOT-005`), así
  que un script **sin seguimiento** no existe para la suite; y la tabla `MODOS` (cómo invocar cada script y qué exit
  codes admite) es **manual**: descubrir un script que no está en ella es el fallo.
- **Arreglo:** al crear un script con el snippet `GOT-005`, añade su entrada en `MODOS` (`tests/test_console_encoding.py`,
  patrón `"agent-kits/shared/<script>.py": [("<modo>", lambda w: [<args>], (<exits>,), <stdin>)]`) y corre la suite
  **después de `git add`**, nunca antes. Regla práctica: `git add -N <script>` (intent-to-add) basta para que `git
  ls-files` lo vea.
