# Qué debe conservar la recuperación de memoria local

Contrato del BLOQUE20, aceptado por ROOT únicamente para la selección sintética congelada Windows/Linux. Los doce casos de recuperación y seis guardias obligatorios pasan sin skips en ambos OS. La [evidencia de revisión y QA](../testing/memory-local-recovery-review-evidence.json) registra Windows: 514 passed/0 failed/14 skipped y Linux: 528 passed/0 failed/0 skipped. La verificación correctiva aplica un nuevo qa-gate oficial sobre los mismos artefactos Linux retenidos y conserva el gate 1 y verdict NO-PASS originales. Esta aceptación no modifica los estados macro ni la aceptación de QA19 y no acredita publicación, tres hosts nativos o eficacia a escala.

La memoria local conserva el corpus canónico, las sesiones pendientes y sus estados. El índice SQLite es una caché reconstruible. Restaurar una copia no aprueba propuestas ni convierte memoria heredada en conocimiento aprobado.

Este contrato complementa [la decisión de componentes](memory-component-decision.md), [los resultados funcionales](memory-functional-results.md) y [el contrato de lectura](memory-read-integration-contract.md). Sus resultados anteriores no acreditan estos cortes ni esta restauración.

## Qué cuenta como captura confirmada

El drill confirma una captura mediante salida satisfactoria de la CLI y un envelope final válido, ligado a sesión y SHA256. Guarda ese recibo antes del corte. El ACK del drill no añade una API ni acredita el comportamiento de tres hosts nativos.

Una captura detenida antes de publicar el envelope final permanece sin confirmar. El log conservado permite recuperación explícita con `recuperado_sin_cierre`. Publicar el journal y completar el envelope son fronteras distintas; repetir replay debe conservar una sola entrada por sesión.

## Qué doce casos son obligatorios

N02 tiene dos variantes y N04 tiene tres. Los otros siete grupos tienen un caso cada uno: doce casos obligatorios, sin omisiones ni skips acreditados como aceptación.

| Caso | Oráculo obligatorio |
|---|---|
| N01 | Restaurar conserva bytes, versiones, origen, enlaces y resultados canónicos. Conserva también outbox, processing, done, dead-letter y backoff. El estado heredado mantiene su autoridad original. |
| N02 / absent | Con caché ausente, comparar búsqueda indexada reconstruida con lectura sin índice sobre corpus completo. La vista de lectura conserva el árbol y no crea caché. |
| N02 / corrupt | Repetir el mismo oráculo con caché corrupta. Comprobar reconstrucción SQLite real y conservación del corpus; una lectura parcial no prueba ausencia de FTS5. |
| N03 | Detener antes de publicar la captura. Antes y después del corte: ningún envelope final ni ACK; log idéntico y temporal observado con nombre, sesión, bytes y SHA256 conservados. Recuperar produce una entrada sin cierre confirmado, conserva la cita pendiente y no emite ACK. |
| N04 / claim_after_claiming | Desde captura confirmada, detener tras claim. Tras reinicio y vencimiento sintético documentado del claim, replay materializa una sola entrada y completa envelope/manifiesto. Un segundo replay no duplica ni cambia el journal anterior. |
| N04 / journal_after_publish | Aplicar el mismo oráculo deteniendo después de publicar el journal. Conservar el recibo previo y la observación exacta de esta frontera. |
| N04 / done_before_envelope_move | Aplicar el mismo oráculo antes de mover el envelope a done. Verificar sesión del envelope final y hash de su manifiesto. |
| N05 | Instrumentar un fallo de manifiesto alcanzado realmente. Observar aviso, reintento/backoff y progreso de otra sesión. Restaurar y reintentar completa ambos manifiestos; replay posterior no duplica ni altera el journal anterior. |
| N06 | Rechazar copia interrumpida, contenido manipulado y destino existente antes de modificar destino o staging. La copia íntegra quiescente restaura en destino nuevo. Conservar el canónico `preserve.tmp-2026.md`: una subcadena temporal no autoriza excluirlo. |
| N07 | Excluir candidatos de consulta; conservar estados heredados sin promocionarlos. Seleccionar el aprobado válido por ID, versión y origen. Una colisión devuelve ambigüedad sin selección automática. |
| N08 | Vista y status funcionan offline y conservan bytes y metadatos del árbol. Auditar cero intentos de procesos/red en esas lecturas. Un bundle sin soporte `outbox.py` comunica degradación y no crea autoridad ni materializa memoria. |
| N09 | Separar los proyectos sintéticos físicamente. Excluir turnos privados y redactar el secreto de fixture antes de persistir o mostrar. Tras restaurar, conservar la cita pública y la separación de scope. |

## Qué formato aprobado debe admitir el parser

Una lista YAML simple inline con valores entrecomillados, como `enlaces: ["ADR-PEER"]`, debe representar los mismos IDs que la lista sin comillas y la lista en bloques. El caso conserva literalmente la entrada entrecomillada; cambiarla a bloques ocultaría la regresión.

El cambio del parser requiere RED observado contra la fuente anterior y GREEN contra la corrección. Verificar extracción de enlaces, selección del aprobado y relación por ID. Mantener validación de evidencias, estado, versión y colisiones. Esta regresión específica complementa los doce casos; su verde unitario no acepta el bloque completo.

## Qué límites hacen interpretable la evidencia

El drill usa fixtures sintéticas, fuentes congeladas y directorios propios nuevos. Copia sólo rutas canónicas y estado local declarados. Rechaza escapes, enlaces y archivos no regulares. La copia quiescente inventaría tamaño, SHA256, mtime y modo; verifica estabilidad y escribe el manifiesto completo al final.

La receta limita la copia a 128 archivos, 256 KiB por archivo y 2 MiB totales. Excluye temporales por formato productor y directorio, nunca por subcadena intermedia. Una copia online o un corte eléctrico real requieren otra evidencia.

Cada hijo pertenece a un Popen exacto. PID, parent PID, nonce, script y frontera ligan la barrera y el recibo. El cleanup conserva esa identidad incluso ante fallos de control y cierra todos los handles. No usa kills generales. En Windows, el ejecutable instalado elegido debe conservar la identidad observada del hijo; registrar su ruta resuelta y hash.

El soporte aislado usa `-I -X utf8 -B`. Los probes esperados de bytecode se registran aparte y fuerzan ausencia; las lecturas desconocidas siguen prohibidas. Una prohibición intentada permanece fallo aunque el producto capture la excepción. Comprobarlo también en hijos detenidos en barrera.

La receta admite nuevos lanzamientos durante un plazo monotónico de 420 segundos.
Un hijo ya admitido conserva sus tiempos propios: 25 segundos para alcanzar una
barrera, hasta 30 para finalizar y cinco para recogerlo tras un corte. Los 420
segundos no son un límite total de ejecución. Los límites de procesos y salida
siguen vigentes; la salida se comprueba al terminar y no acredita un límite de RAM
ni un SLA. El drill no ejecuta modelos, backends, hosts nativos ni instala dependencias.

## Qué evidencia permite cerrar este bloque

Conservar selección e IDs exactos, fuente antes/después, Gold, recipe, harness, JUnit completo, CLI stdout/stderr/exit, auditorías, ACK, barreras y manifiestos. Registrar cada intervención sintética. Preservar también ejecuciones fallidas y clasificar producto, fixture e infraestructura sin convertirlas en PASS retrospectivo.

ROOT ejecuta la selección congelada en Windows y Linux, revisa todos los oráculos y el aislamiento, y aplica las puertas de revisión, cobertura oficial del diff y qa-gate pertinentes. Resultados de autor, pruebas de eficacia anteriores y lectura de código no sustituyen esa aceptación.

Las comprobaciones de privacidad cubren los secretos y scopes declarados en Gold. No prueban redacción universal, escala, aprendizaje entre sesiones ni compatibilidad nativa de tres hosts. Esos pendientes conservan su estado en el ledger.

## Dónde continúa el trabajo

T-07 mantiene decisión y límites de memoria; T-08 integra este contrato. T-09 liga captura, publicación y recuperación a sus guardias. T-11 conserva handoffs existentes; T-13 presenta estados sin activar restauración. T-14 reúne pruebas y revisión; T-15 integra documentación; T-16 conserva el cierre global pendiente.

El bloque no crea comandos de backup, hooks, backends, dependencias, skills ni agentes. La operación humana sigue en las guías existentes de consulta y retoma. Los dieciséis estados macro permanecen iguales; sólo T-01 está completado.
