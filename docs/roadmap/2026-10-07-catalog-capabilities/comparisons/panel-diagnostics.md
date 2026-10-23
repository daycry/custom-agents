# Diagnóstico operativo explícito

Continuación dirigida de la comparación de paneles para el bloque 14, sobre
el corpus fijado en `ef648e01899ba3e8dc6371642deaaf64b4477775`. Cinco recursos
revalidados por SHA-256 y rangos concretos en
[panel-diagnostics-reading-evidence.json](panel-diagnostics-reading-evidence.json).
Solo lectura, sin ejecutar origen ni consultar configuración del consumidor.
La lectura anterior completa de algunos cuerpos y esta lectura parcial se
conservan como cohortes distintas; no se reclasifica evaluación global.

R-ec2c637e28f7 separa requisitos actuales/completos, preparación del diagnóstico
y publicación (esta última falsa). R-949360f20153 permite avisos por Git ausente
o comprobaciones GitHub omitidas sin impedir su agregado ready; no se copia ese
agregado como prueba de carga, funcionamiento o ausencia de problemas.
R-c01714e02ad5 distingue vista declarada, recomendación e indisponibilidad.
R-7b761940e6db aporta navegación y filtros; R-97af5d1ebf36 delimita la consulta
externa que aquí no se ejecuta. Los renderers/opciones restantes, documentos
auxiliares y consumidores de almacenamiento/runtime siguen fuera del cierre.

Doctor propio, en la base `2610a27`, ya calcula estados y hasta tres prioridades.
Su JSON general también incluye rutas y detalles libres: no sirve como formato
portable del catálogo. La integración conserva los resultados por fila y una
referencia al arreglo en doctor, con fecha y alcance explícitos, en un contrato
versionado y acotado. Los títulos públicos conocidos tienen allowlist; los
dinámicos no se publican. No se incorpora backend, score, otra skill ni escritor.

El panel recibe un fichero seleccionado, nunca ejecuta el diagnóstico ni lee
servicios para completarlo. Fuente, scope y fecha describen una instantánea
histórica, no autenticidad, readiness actual ni ejecución de hooks. Formato,
límites, ausencia, antigüedad y scope incompatible preceden a la UI; privacidad,
teclado y escenarios de navegador son puertas de QA de esta entrega.
