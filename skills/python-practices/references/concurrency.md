# Cancelación, concurrencia y límites

| Situación | Decisión | Escenario de prueba |
|---|---|---|
| Hijas async pertenecen a una operación | TaskGroup cuando la versión mínima sea ≥3.11 y se quiera cancelación conjunta | Una hija falla; las demás terminan canceladas y no dejan trabajo huérfano |
| CancelledError capturado para limpiar | Cleanup en finally y propagación de cancelación | El caller cancela durante E/S; recursos cerrados y tarea cancelada |
| Lista de trabajo grande | Concurrencia limitada y presión de entrada; no un task por elemento sin límite | El máximo de operaciones simultáneas respeta el límite configurado |
| Librería bloqueante dentro de async | Separar ejecución bloqueante; comprobar que cancelar el await no detiene por sí solo el trabajo en hilo | Timeout no deja una escritura tardía ignorada |
| Script procesa stdout de un hijo | Encoding explícito, timeout y significado del exit code | Unicode bajo consola Windows, timeout y salida inválida conservan diagnóstico |
| Entrada de archivos o red | Límite de bytes antes del parseo y límite del resultado | Entrada grande se rechaza sin crecer sin límite |

TaskGroup y timeouts estructurados dependen de la propagación de cancelación;
tragársela puede romper su comportamiento. La elección entre TaskGroup y
gather depende de si se necesita cancelar tareas hermanas al primer fallo.
No afirmar equivalencia entre ambos por compartir un await.

Fuente oficial, 2026-10-06:
[asyncio tasks](https://docs.python.org/3/library/asyncio-task.html).
La página consultada describe Python 3.14.8; verifica cada API frente a la
versión mínima del proyecto y usa su documentación versionada cuando difiera.
