# Verificación del manual explicado

Edición final de QA:126páginas,27workflows W-01..W-27,32gráficos Mermaid,
77marcadores y184enlaces. Fuentes ES/EN mantienen el caso continuo del portal,
peticiones, participantes, pasos, decisiones, resultados y recuperación.
Las seis referencias técnicas previas se conservan al final como consulta avanzada.

Se compilaron las64fuentes Mermaid de los capítulos ES/EN con Mermaid CLI12.0.0
y Chromium146. El PDF incorpora los32gráficos ES; no muestra código Mermaid en
lugar de dibujos. Se verificaron el índice, los27IDs de workflows, la procedencia
LF/CRLF y0desbordamientos textuales/caracteres de sustitución automatizados.

Las126páginas finales se renderizaron y revisaron en11hojas de contacto, con
inspecciones individuales de portada, diagramas y código durante la edición.
La última lectura cubrió también los ejemplos completos, catálogo de módulos,
referencia avanzada y fuentes. No se observan tablas o texto cortados.

`scripts/check-handbook.py` contrasta el PDF con22fuentes explícitas, hashes
normalizados aLF, workflows y recibos de diagramas. Tests dedicados comprueban
modificación de PDF/fuente, omisiones, recibos inválidos y rutas ajenas. CI y release
ejecutan ese gate y entregan PDF más manifiesto como assets independientes.

La lectura ES/EN de todos los capítulos y referencias fue completada por las
lentes A/B del intento1. El PDF no cambió en los intentos posteriores. El packlist
npm incluye también contratos avanzados enlazados, sin añadir journals ni roadmap.

Las pruebas de navegador y nativas, revisión final, CI y publicación se coordinan
en [el informe de consola](../../2026-10-31-control-center/testing/report.md).
No se declara la publicación antes de que ocurra; tokens/coste total no medidos.
