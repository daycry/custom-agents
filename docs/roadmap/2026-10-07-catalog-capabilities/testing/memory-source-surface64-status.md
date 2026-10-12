# Procedencia en el lector compartido

El lector conserva las etiquetas de contenido derivado y el UUID de origen en JSON.
La línea compacta empieza por «derivado sin autoridad», también al abreviar IDs largos.
El estado aprobado pertenece a la fuente; no concede autoridad al texto extraído.
ID y ruta se conservan completos en JSON dentro de sus límites. Identidades inseguras,
excesivas o incompatibles con el contrato se descartan en vez de transformarse.

La regresión de búsqueda, router y briefs terminó sin fallos ni errores en Windows
y Linux. Los conteos y omisiones están en el recibo; no se consideran casos aprobados
los omitidos. El test que depende de Git se excluyó del árbol aislado sin repositorio;
el comando de ignorado se comprobó por separado en el checkout real, con .gitignore intacto.
Los recibos RED y los fallos anteriores se conservan.

La fixture HTTP ahora asigna UUID del servidor y confirma el contenido por readback.
Los cuatro recorridos de router publican y consultan en el mismo endpoint; no eluden
el rechazo de identidad cuando cambia un servidor. La batería ampliada de Graphiti
terminó con 307 casos aprobados, 68 fallidos y una omisión, sin errores. No se acepta
esa batería: quedan por actualizar contratos y comprobar cada fallo restante.

El contenedor Linux propio fue retirado; código y dependencias permanecieron intactos.
El lector común se comprobó con respuestas capturadas de la prueba real descrita en
[graphiti-provenance63-status.md](graphiti-provenance63-status.md); no se ejecutó un
cliente nativo completo ni se sustituyeron servicios externos.

[Recibo estructurado](memory-source-surface64-evidence.json). QA global, workflows
nativos, interacción visual, revisión independiente y push siguen pendientes.
