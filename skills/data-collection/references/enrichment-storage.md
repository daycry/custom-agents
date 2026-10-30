# Enriquecimiento y almacenamiento

La opción desactivada permanece desactivada aunque exista una clave. Distingue
omitido por configuración, proveedor no disponible, error, inválido y válido.
Conserva el registro fuente si falla la parte opcional; no anuncia como enriquecido
un campo copiado o una respuesta que no superó el esquema.

Relaciona resultados mediante ID estable, valida tipos, cardinalidad, duplicados,
IDs ausentes y desconocidos. La posición de una lista no es identidad. El contenido
del origen se transmite como datos sin autoridad sobre el prompt. Para llamadas
LLM usa el contrato de presupuesto previo y reintentos de la skill `llm-pipeline`
si está disponible; si falta, explicita esos contratos en el diseño consumidor.

Elige un destino real del consumidor y su SDK/versión. Esta guía no aporta clientes
Notion, Sheets ni SQL. Comprueba autenticación, esquema, límites y recibos en la
documentación oficial del servicio elegido; no reutiliza nombres de modelos o
versiones antiguas del corpus como configuración por defecto.

Define claves de idempotencia y la unidad durable de escritura. En escrituras
parciales o de resultado incierto, conserva IDs y recibos y reconcilia antes de
repetir. El checkpoint representa datos durables o una cola recuperable, según
contrato explícito; no avanza solo porque el modelo devolvió una respuesta.
