# Recuperación semántica y procedencia

La corrección vincula los UUID de hechos y la pertenencia de entidades con la fuente
vigente publicada. Grupo, UUID, versión, ID y hash del contenido deben coincidir.
Referencias desconocidas, retiradas o ambiguas no permiten sustituir la fuente por
un nombre de entidad. Una ventana o consulta de pertenencia incompleta descarta la
entidad y conserva los hechos verificados por separado.

La regresión ejecutó 275 casos en Windows y 275 en Linux, sin fallos, errores u
omisiones, con los mismos hashes de código. Cuatro RED reprodujeron atribuciones
ambiguas por respuestas parciales, límites o fuentes vigentes no observadas.
Exportación, lint y ledger pasaron; se conservaron los recibos anteriores.

La prueba real usó una instancia temporal compatible: dos versiones y un marcador,
tres envíos sin duplicados, versión 2 recuperada y dos identidades históricas verificadas.
La consulta ordinaria recuperó la fuente vigente. Dos filtros controlados separaron
hechos y entidades, manteniendo respuestas reales de MCP, y comprobaron ambos caminos.
El texto extraído declara contenido derivado, sin autoridad ni validación de afirmaciones.

Todos los trabajos terminaron y se retiraron el servidor temporal y sus grafos.
El servicio instalado sigue activo con su imagen anterior y su limitación de lecturas
entre grupos; no se ha actualizado. La imagen compatible se conserva para revisión.

[Evidencia estructurada](graphiti-provenance63-evidence.json). Esta comprobación acepta
el vínculo de fuentes en la muestra descrita. No demuestra utilidad comparativa,
handoff nativo, despliegue permanente, QA global ni cierre de la iniciativa.
