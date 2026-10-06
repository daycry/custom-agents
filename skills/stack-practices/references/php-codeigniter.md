# Decisiones de persistencia en CI4

| Situación | Decisión | Prueba que detecta el fallo |
|---|---|---|
| Payload no confiable llega a Model | Mantener allowedFields como allowlist; validar autorización por separado | Un campo administrativo enviado por el cliente no cambia; otro usuario no puede editar el recurso |
| Query Builder usado directamente | No asumir validación, callbacks ni protección de Model | Entrada inválida por el camino Builder produce rechazo explícito según contrato |
| Varias escrituras forman una operación | Una frontera transaccional y verificación del estado final | Fallar la segunda escritura conserva la base anterior, sin commit parcial |
| Catch usado como único indicador de rollback | Comprobar el comportamiento de la versión instalada | Un error SQL con la configuración real no se presenta como éxito |
| Transacciones anidadas | El nivel exterior determina la frontera real; evitar commits internos independientes | Un fallo interior no deja una escritura exterior confirmada |

CI4 desde 4.3.0 no lanza por defecto excepciones de transacción aunque DBDebug
esté habilitado. Comprobar transStatus después de transComplete o configurar
transException según el contrato y entorno. No cambiar producción DBDebug
para ocultar errores. resetTransStatus pertenece a versiones desde 4.6.0;
no usarlo sin verificar el lockfile.

Fuentes oficiales, 2026-10-06:
[transacciones](https://codeigniter4.github.io/userguide/database/transactions.html),
[Model](https://codeigniter4.github.io/userguide/models/model.html).
Las páginas consultadas muestran CI4 4.7.4; manda la versión del consumidor.

## Fronteras y pruebas de PHP/CodeIgniter

Verifica PHP, extensiones, framework y PHPUnit en composer.json y composer.lock.
Mantén controladores como adaptadores HTTP: validan forma y delegan reglas de
dominio a servicios; la autorización se comprueba también cuando el servicio se
invoca fuera del controlador. Evita esconder dependencias mutables en un service
locator si impide aislar el caso; sigue el patrón de inyección ya usado.

Declara rutas y métodos explícitos cuando el proyecto requiera control de filtros.
Comprueba CSRF en métodos de escritura y filtros con rutas equivalentes; no asumas
que Legacy Auto Routing respeta la misma superficie que las rutas declaradas.
No migres automáticamente el router. Un Model con allowedFields no es validación
de dominio ni autorización: prueba esos caminos también cuando se use Builder.

Una prueba de servicio aísla reloj, mail y red; una de persistencia usa el motor
real y un estado restaurable; una feature prueba ruta, filtro, sesión y respuesta.
Incluye error SQL, entrada inválida, doble envío y fallo tras la primera escritura.
Evita tests que solo cuentan llamadas internas y pasan aunque el resultado sea
incorrecto. No ejecutes migraciones de fixtures contra la base del consumidor.

Fuentes: [routing](https://codeigniter.com/user_guide/incoming/routing.html),
[security](https://codeigniter.com/user_guide/libraries/security.html),
[testing](https://codeigniter.com/user_guide/testing/overview.html),
[PHPUnit](https://docs.phpunit.de/). Usa el manual de la versión bloqueada.
