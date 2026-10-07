---
test-plan: project-extensions
estado: aprobado
creado: 2026-10-06
---

# QA del inventario de extensiones

- **P-01 [GWT]** Dado bundle y proyecto de fixture con los tres runtimes, al abrir
  el panel aparecen componentes propios con tipo, scope y fuente diferenciados.
- **P-02 [GWT]** Dadas piezas duplicadas, al buscar/filtrar por origen aparecen
  todas y el conflicto, sin sustituir roles del workflow ni inventar precedencia.
- **P-03 [GWT]** Dadas declaraciones MCP con secretos y servidores apagados, al
  inspeccionar solo aparecen metadata permitida y disponibilidad no verificada.
- **P-04 [GWT]** Dado móvil/teclado, al cambiar filtros y abrir detalles permanecen
  navegación, foco y contenido utilizables; sin desborde ni recursos de red.

Script: formatos Markdown/TOML/JSON/JSONC, scopes, path guards, límites,
redacción, propiedad, selección y brief. Ninguna prueba importa código de fixture.
