# Revisión del manual PDF

Artefacto: `output/pdf/custom-agents-manual-operativo.pdf`.
Edición de documentación 2026-10-30, preparada en rama; no anuncia una nueva release.
Fuente: manual completo en español y seis capítulos, tres ejemplos de bindings/skill
y catálogo de módulos. Los hashes íntegros figuran en `pdf-manifest.json`.

- 39 páginas A4; 18 workflows W-01 a W-18 presentes en el texto extraído.
- 138 enlaces y 62 entradas de navegación; destinos internos válidos.
- Sin texto fuera de los límites de página y sin glifos de sustitución U+FFFD.
- Autoría con ReportLab y fuentes Arial/Consolas; dependencia privada de generación,
  sin añadir dependencias Python al runtime del plugin.
- Todas las páginas renderizadas y revisadas visualmente en cuatro hojas de contacto,
  más páginas completas de portada, tablas y ejemplos. Revisión repetida tras el
  ajuste final de paginación de 40 a 39 páginas.
- Portada con jerarquía clara, índice navegable, cabeceras/pies, filas alternas,
  cabeceras de tabla repetidas y bloques de código envueltos.
- Incluye participantes, comandos, agentes, skills, tools/MCP, configuración,
  pasos, entradas, salidas, puertas y recuperación. Atlassian desarrolla tareas/fases,
  comentarios, transición y permisos; Redmine es un adaptador de referencia sin
  transporte instalado ni conexión real declarada.

SHA256: `9fd179986feeff8c8c2fcd395fc13a8d9f81fef6ec27624843b1f7452f95cf42`.

Markdown sigue siendo la fuente mantenible. Las credenciales, logs privados,
configuración personal e histórico del roadmap no se incorporan al manual.

Los hashes de las fuentes corresponden a UTF-8/LF, igual que los blobs publicados
en Git. Se comprob? cada una de las once fuentes, y se revis? de nuevo el PDF
tras corregir el hash del cat?logo cuya copia de trabajo ten?a CRLF.
