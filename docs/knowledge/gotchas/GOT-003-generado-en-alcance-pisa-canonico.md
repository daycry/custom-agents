---
id: GOT-003
tipo: gotcha
area: Confluence / staging
estado: aceptada (validada: usuario, 2026-08-20)
fuente: docs/roadmap/2026-08-20-confluence-policy/tasks.md (gaps C1/C2) vía retro.md
---

## Un fichero generado dentro de una carpeta en alcance del espejo puede pisar (o borrar) el contenido canónico

- **Síntoma:** dos hallazgos CRÍTICOS de la revisión adversarial de `confluence-policy` sobre el
  staging generado `docs/confluence/`: (C1) el marcador de aviso del staging se escribía como
  `README.md` y **pisaba** la copia staged de `docs/README.md` — y como `--map` resolvía esa ruta
  al canónico con exit 0, un `confluence-pull` posterior habría sobrescrito el `docs/README.md`
  real con boilerplate; (C2) `--stage` hacía `shutil.rmtree(out_dir)` sin salvaguarda — un `--out`
  mal configurado (p. ej. `docs/`) se borraba entero.
- **Causa raíz:** un generador que escribe dentro del árbol que él mismo espeja necesita nombres
  **reservados** para sus ficheros propios (que no puedan colisionar con ningún canónico en
  alcance) y una comprobación de que el destino que va a borrar es **suyo** — nada de eso viene
  gratis con "copiar y limpiar".
- **Qué hacer en su lugar:** marcador con nombre reservado y excluido del alcance en cualquier
  carpeta (`_STAGING-LEEME.md`), copia byte a byte garantizada con `assert` defensivo, y
  `assert_safe_stage_target()` que rehúsa borrar salvo destino inexistente, vacío o staging
  reconocible (contiene el marcador).
- **Evidencia / fuente:** [`docs/roadmap/2026-08-20-confluence-policy/tasks.md`](../../roadmap/2026-08-20-confluence-policy/tasks.md)
  (T-08, gaps C1/C2; commits `b9c342a`, `2e73522`; tests `test_stage_copies_readme_byte_for_byte`,
  `test_stage_refuses_unsafe_out_target`). Contexto en [`retro.md`](../../roadmap/2026-08-20-confluence-policy/retro.md).

`estado: aceptada (validada: usuario, 2026-08-20)`
