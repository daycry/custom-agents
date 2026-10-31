# Integración de memoria por proyecto

La curación y la recuperación Markdown local pertenecen al core. Esta skill y sus
adaptadores se distribuyen en el módulo opcional `memory-integrations`. Un perfil
core no entrega la skill; los plugins nativos completos pueden contenerla sin
activarla. Graphify es un extractor externo opcional, separado de esta publicación.

Usa el puerto común `agent-kits/shared/project-integrations.md`, propósito `knowledge`.
Para peticiones manuales filtra `knowledge.publish` o `knowledge.read`; las capacidades
`knowledge.check` y `knowledge.rebuild` son operaciones independientes. El ejemplo
`docs/examples/integrations/memory.json` declara bindings sin eventos automáticos:
una aprobación del Curator por sí sola no publica nada. No introduzcas red en hooks.

En el adaptador bundle, el `id` del binding identifica exactamente el backend de
`taxonomy.json`. Antes de operar comprueba la igualdad y que su tipo y configuración
estén validados. Un binding no concede permisos ni habilita categorías: siguen
siendo obligatorios `backends.<id>.enabled`, el routing explícito de cada categoría
y las puertas adicionales de lectura. No cambies esos valores para conseguir un verde.
Varios bindings no autorizan enviar una misma pregunta a todos los proveedores.

La CLI de bajo nivel conserva su uso explícito `--backend <id>` para administración;
no es un despachador automático del core. La consulta local sin `--intent` no utiliza
servicios. La lectura con intent conserva el router de memoria existente; su opt-in
en la taxonomía y autorización de consulta son independientes de declarar un binding.

Presenta vista previa, destino, entradas aprobadas y categorías antes de publicar.
Usa `--dry-run`, luego la operación autorizada; registra los recibos reales del
adaptador. En Kwipu, exportar, indexar y consultar son pasos diferentes. En Graphiti,
encolar no es confirmar persistencia. Los resultados inciertos se reconcilian con
los diarios existentes; no crees otra cola ni publiques candidatos o conversaciones.
Los recibos y respuestas generadas no aprueban conocimiento nuevo.

Una integración de proyecto puede usar otro proveedor mediante su propia skill y
contrato. No modifica el core ni reutiliza tipos de backend ajenos. Instalar una
biblioteca, iniciar contenedores, añadir cuentas o cambiar permisos requiere una
acción concreta autorizada y no forma parte de descubrir una declaración.
