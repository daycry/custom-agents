# Contratos y procedencia de Graphiti

Los quince fallos residuales se resolvieron con retiradas por versión, UUID del servidor,
readback y generaciones que conservan el grupo anterior. Un RED mostró que planificar
aceptaba una versión previa ausente; ahora se rechaza antes de producir operaciones.

Cuatro RED reprodujeron el bypass por nombres coincidentes. En una publicación moderna,
un nombre de Entity no establece procedencia: se exige pertenencia verificada o UUID y
nombre exactos del episodio publicado. Un hecho moderno requiere referencias explícitas.
Todos los textos extraídos conservan etiquetas de contenido derivado y sin autoridad.
Se preserva el pase que esperaba devolver una versión retirada: la lectura moderna la
descarta y se actualizó la expectativa, sin volver a servir ese resultado.

Otra observación mostró IDs y rutas largos recortados a 200 caracteres. Cuatro RED
comprobaron el recorte y traversal, controles o tamaño excesivo después del tope.
El adaptador valida ahora la identidad completa: ID hasta 512 caracteres y ruta hasta
4096. Los valores inseguros o excesivos se descartan; los seguros no se recortan.

Con el código final, Windows pasó 375 de 376 casos ampliados (una omisión) y los 288
casos del publicador, sin fallos ni errores. Linux pasó los mismos 664 casos sin
omisiones. Código y dependencias se conservaron y los tres contenedores Linux propios
fueron retirados. No se modificaron servicios externos. Las pruebas de transporte
controlado no equivalen a un cliente nativo ni demuestran utilidad comparativa.

[Evidencia](graphiti-contract66-evidence.json). Quedan repetir el recorrido semántico
real tras estas correcciones, utilidad comparativa, workflows nativos, QA global,
revisión independiente y push. La iniciativa sigue abierta.
