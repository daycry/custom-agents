# Laravel: fronteras y persistencia

Comprueba PHP, `laravel/framework` y PHPUnit/Pest en Composer y su lockfile.
El código de arranque y registro de middleware depende de la major: sigue la
estructura existente, sin trasladar automáticamente archivos de otro esqueleto.

| Situación | Criterio | Escenario que lo comprueba |
|---|---|---|
| Entrada y autorización | Validar forma con el mecanismo del proyecto; políticas/gates comprueban acceso al recurso | Un usuario válido no puede modificar el recurso de otro |
| Eloquent recibe un payload | Seleccionar campos permitidos; no usar el payload completo como autoridad | Un atributo administrativo añadido al envío no se persiste |
| Varias escrituras | Frontera transaccional coherente; una excepción no se convierte en éxito | Fallar la segunda escritura revierte la primera |
| Relaciones en un listado | Medir consultas y cargar lo necesario; no serializar relaciones sin límite | Aumentar registros no provoca una consulta extra por fila |
| Job depende de una escritura | Comprobar dispatch tras commit con la configuración real | Rollback no deja un job que asume datos confirmados |
| Un job se repite | Idempotencia de negocio y recibos de efectos externos | Dos entregas conservan una sola operación efectiva |

`DB::transaction` revierte y relanza ante excepción. Su opción de reintento por
deadlock puede volver a ejecutar el cuerpo: evita efectos externos irreversibles
dentro de él. Dispatch tras commit ordena respecto a la transacción; no equivale
por sí solo a un outbox durable ni garantiza entrega exactamente una vez.

Acota timeout, intentos y plazo global de jobs/HTTP según el transporte; verifica
que la redelivery no se adelanta al tiempo permitido al worker. Los workers de
larga vida no deben conservar datos de otra tarea en estado mutable compartido.
No cambies sus supervisores ni ejecutes colas del consumidor para aplicar la guía.

Usa feature tests para rutas, políticas, validación y respuesta; pruebas con el
motor real para locks, transacciones y concurrencia. Los fakes de cola/mail prueban
dispatch, no la ejecución o entrega externa. No usa SQLite como prueba de una
garantía específica de otro motor.

Fuentes oficiales consultadas el 2026-10-30: [base de datos Laravel 12.x](https://laravel.com/docs/12.x/database)
y [colas Laravel 12.x](https://laravel.com/docs/12.x/queues). Son referencias de
contrato, no la versión prescrita al consumidor; abre el manual de su major.
