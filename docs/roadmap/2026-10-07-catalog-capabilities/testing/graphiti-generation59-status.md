# Reconstrucción recuperable de memoria

El adaptador construye otra generación y confirma corpus e historial antes de cambiar
la publicación. Conserva los grupos anteriores y abandonados y sus recibos inciertos.
Reanuda envíos sin reenviar, vincula los UUID nuevos a versiones/retiradas y recupera
pérdidas remotas desde snapshots propios o fuentes canónicas exactas.

La batería focal conjunta pasó 256 casos en Windows y 256 en Linux, sin fallos, errores
ni omisiones, con CTracer oficial 7.16.2. Las regresiones RED iniciales (17), de integridad
de snapshots/historial (4) y de reparación de generaciones publicadas (2) se conservan.
Exportación, export-check y linter terminaron en cero; permanecen nueve avisos del linter.

El primer Linux agotó 360 segundos usando estado temporal en el volumen compartido.
Se conserva ese fallo y la limpieza comprobada de su contenedor. Con la misma fuente,
dependencias, imagen y límite, el estado temporal en tmpfs nativo completó la batería
en unos 55 segundos. Veinte escrituras durables midieron 0,686 s en el volumen compartido
y 0,009 s en tmpfs; esto evidencia el coste de E/S, no explica fallos históricos ajenos.

[Recibo estructurado](graphiti-generation59-evidence.json). La consolidación es en la
candidata; no equivale a promoción a Git, aceptación global, commit ni push.

Pendiente: reconstrucción/verificación contra el servicio real, consultas semánticas
y recorridos nativos, adaptación de contratos previos, QA/coverage global fresca y
revisión independiente. Kwipu y Graphify siguen opcionales; Graphiti permanece opt-in.
