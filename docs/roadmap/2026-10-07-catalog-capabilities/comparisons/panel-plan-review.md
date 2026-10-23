# Revisión visual y aprobación de planes

Petición del usuario del 2026-10-09: comprobar los comandos de aprobación
mediante UI. [Evidencia](panel-plan-review-reading-evidence.json): 20 fuentes
de la revisión `ef648e01899ba3e8dc6371642deaaf64b4477775`, con hashes y rangos.
Lectura de implementación, consumidores y prueba de integración; no se ejecuta
origen ni se convierte esa prueba leída en QA propia.

## Función comprobada

R-977a20b4bd1a ofrece una entrada visual que abre el plan, espera feedback,
permite modificarlo y continúa tras aprobar. R-dbe89d282313 conecta esa señal
a la confirmación de planificación. R-d6c09c287a66 define el workflow común;
R-5cfa1fa3014f implementa la CLI que consume JSON del servidor.

R-90614daade3c muestra anotaciones, chat y botones de aprobar o pedir cambios.
R-eb6ff08db625 procesa feedback HTTP, SSE hacia el navegador y long-poll hacia
el agente. Cambiar el archivo recarga la vista; sin consumidor escuchando el
comentario queda en cola. R-6102e84932bd comprueba ese circuito en un test de
integración. Es una función implementada, separada del panel operativo.

La persistencia usa sesiones JSON identificadas por la ruta del artefacto;
R-5b405c303a19 guarda veredictos y pendientes. El servidor no inicia trabajo
ni concede permisos de herramientas. Las instrucciones del consumidor aplican
la confirmación al workflow. No se ha observado conexión con el plan mode nativo.

La CLI es reutilizable por los tres runtimes. El mecanismo de recuperación
mediante Stop está registrado para Claude; no se ha encontrado equivalente
en los registros Codex/OpenCode revisados. Esto no acredita paridad nativa.

Otros procedimientos revisados piden confirmación conversacional o generan
instrucciones; no se cuentan como otra UI implementada. La gestión PM2 es
gestión de procesos, no de proyectos. El recurso de aprobación de mensajes
aporta contratos de versión y reclamación, pero no entrega el panel anunciado.

## Mejoras necesarias para integrarlo

| Límite observado | Decisión propia |
|---|---|
| Aprobación identifica la ruta, sin hash del contenido | Ligar decisión a iniciativa, artefacto y SHA-256 revisado |
| El plan puede cambiar después de aprobar | Rechazar la decisión obsoleta y pedir revisión de la versión nueva cuando corresponda |
| La entrega retira feedback antes de confirmar consumo | Persistir pendiente/entregada/consumida, con ID y confirmación idempotente |
| Contexto/estado de navegador no equivale a permiso nativo | Aplicar solo la puerta del workflow autorizado; preservar permisos y QA |
| Servidor independiente y recuperación específica de Claude | Integrar transporte en el servidor propio y consumidor común, con pruebas por runtime |

La experiencia elegida incluye vista del plan, comentarios por sección,
aprobar/pedir cambios, respuesta de estado y recarga. El archivo y el ledger
siguen siendo canónicos. Las decisiones son recibos de revisión; no otra
base de planes. Texto acotado y redactado, sin transcripciones o razonamiento.

Esta vista será opcional. Solo sustituirá una confirmación que el workflow
ya requiere o una revisión visual solicitada; no impondrá aprobaciones nuevas
ni volverá a preguntar por acciones previamente autorizadas. Cancelar o cerrar
la página no autoriza continuar. Ausencia de consumidor, cambios de versión,
concurrencia, duplicados y recuperación necesitan tests propios.

El rendering debe tratar contenido como datos, sin scripts, recursos externos,
rutas libres ni comandos ejecutables del documento. Acceso loopback, Host/Origin,
sesión de revisión y controles de escritura se diseñarán antes de integrar.
Este contraste añade un destino operativo a T-08/T-11/T-13; no entrega todavía
la UI propia ni cierra la evaluación completa de comandos o skills.
