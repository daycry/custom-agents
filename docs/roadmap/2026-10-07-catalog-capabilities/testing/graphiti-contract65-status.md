# Contratos de publicación y recuperación

Los constructores de respuestas simuladas asignan UUID remotos, sin extraerlos de
peticiones nuevas del cliente. Los recorridos de publicación y consulta mantienen
el mismo endpoint. Las pruebas de reconstrucción conservan el grupo anterior y
comprueban el contenido y la procedencia, sin exigir los mismos UUID entre grupos.
Las respuestas de otros grupos se rechazan; se retiró un aviso inalcanzable.

Un RED reprodujo la pérdida de la causa original al reintentar un envío incierto.
El recibo conserva ahora clase y detalle saneado y redactado, hasta 500 caracteres.
El diagnóstico no habilita un segundo envío ni cambia la confirmación por readback.
Los campos de error son opcionales y se validan antes de usar un recibo existente.
La regresión del publicador pasó 280 casos en Windows y 280 en Linux, sin omisiones.
Se probaron redacción, controles y rechazo de recibos malformados. Las tres pruebas
de seguridad antes fallidas también pasaron con el código final.

La batería ampliada de 376 casos pasó 356 y dejó 19 fallidos y una omisión.
Tras las últimas correcciones se repitieron exactamente esos 19: cuatro pasaron
y quedan 15 fallos. No se presenta este foco como una nueva suite ampliada verde.
Quedan escenarios de retirada, recuperación y metadatos incompletos por resolver.

Se conservan los recibos fallidos originales, los jobs terminaron sin fuga y el
contenedor Linux propio fue retirado. Los servicios externos no se sustituyeron.
[Evidencia](graphiti-contract65-evidence.json). Aceptación global, recorridos nativos,
utilidad comparativa, revisión independiente y push siguen pendientes.
