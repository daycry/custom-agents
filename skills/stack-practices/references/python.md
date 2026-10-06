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

## Tipos, fronteras y pruebas Python

Comprueba requires-python, lockfile y extras antes de introducir una API. Usa
Protocol para expresar una dependencia por comportamiento cuando eso permita
tests sin infraestructura; no añadas abstracciones para funciones sin variación.
Los tipos describen contratos, pero no validan por sí solos datos JSON externos.
Valida en el borde y conserva modelos de dominio independientes del transporte.

No hagas E/S, lectura de credenciales ni arranques workers al importar módulos.
Coloca el entrypoint bajo main; propaga errores clasificados, encadena su causa y
evita capturar Exception para devolver éxito. Recursos y temporales se cierran
con context managers/finally también cuando se cancela o falla una operación.

Fixtures pytest con yield restauran el estado; restringe su scope cuando haya
datos mutables. monkeypatch sobre la referencia que usa el módulo, no sobre una
definición que ya fue importada en otro namespace. tmp_path evita escribir en el
checkout real. Parametriza límites/códigos de error; assert del resultado antes
que implementación. Para async, usa el runner ya instalado y comprueba tareas
pendientes, cleanup y timeouts: un mock AsyncMock no verifica concurrencia real.

Separa test unitario de contrato con red/BD. Congela o inyecta reloj y randomness
cuando el caso lo necesite; no dependas del orden de tests ni del locale. En CLI
prueba stdin/stdout Unicode, exit codes y salida a pipe además del retorno Python.
Mantén stdlib como default del plugin; dependencias del consumidor se deciden por
su necesidad y contrato, no por una regla heredada del bundle.

Fuentes: [typing Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol),
[contextlib](https://docs.python.org/3/library/contextlib.html),
[pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html),
[monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).
