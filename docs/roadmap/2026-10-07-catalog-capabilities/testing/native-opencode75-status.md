# OpenCode nativo sobre el candidato actual

OpenCode 2.0.12 carga el plugin actual mediante el instalador de proyecto.
Dos prompts retenidos comprueban UTF-8 y exclusión de contenido privado;
dos loops del agente con proveedor local controlado comprueban contexto,
escritura de un archivo propio, post-tool, captura de final de ejecución
y materialización del journal al iniciar la siguiente sesión.

La actividad opt-in conserva registros de `execution_finished` recibidos
del stream nativo. La colección sigue siendo incompleta: no prueba agentes
vivos, destrucción, todos los agentes o interacción de un humano.

El servidor termina naturalmente con exit 0; el job propio queda sin
procesos activos, sin fuga, y la fuente conserva todos sus hashes. No se
heredan credenciales del proveedor, se alteran preferencias personales ni
se usa navegador o inferencia de un modelo externo. La primera preparación
fallida por ruta de ejecutable incorrecta permanece en su recibo privado.

Este recorrido no prueba guardias de roles protegidos, aprobación humana
por UI, todo el workflow ni los otros runtimes. [Evidencia](native-opencode75-evidence.json).
