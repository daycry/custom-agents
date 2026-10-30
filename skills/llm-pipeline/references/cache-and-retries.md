# Caché y reintentos

Identifica un único dueño de reintentos. Revisa también los automáticos del SDK y
transporte; documenta intentos totales y reintentos por separado: cero reintentos
permite la llamada inicial. Ajusta la política al tipo de operación y a la posibilidad
de duplicación. No asumas idempotencia por reutilizar el mismo texto.

Todo intento respeta el plazo global y su presupuesto reservado. Acota espera y
número de intentos; usa backoff y jitter cuando corresponda al contrato. Interpreta
`Retry-After` solo donde el proveedor lo soporte, sin exceder el plazo restante.
Cancelación durante espera o transporte debe terminar el trabajo propio y conservar
el estado incierto si la operación remota pudo ejecutarse.

Una caché de aplicación necesita clave y aislamiento por contexto/autorización,
versión de prompt, modelo y parámetros que afecten al resultado. No mezcla datos
entre clientes ni conserva contenido sensible por defecto. Define invalidación
y permisos de lectura acordes con el origen del dato.

La caché de prompts del proveedor tiene un contrato distinto. Conserva los roles
y bloques del prompt al estructurarlo; comprueba requisitos, TTL y métricas en la
documentación oficial vigente. No fijes umbrales o modelos del recuerdo ni atribuyas
aciertos sin señales de uso. Mide por separado caché de aplicación y de proveedor.
