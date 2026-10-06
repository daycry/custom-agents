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
