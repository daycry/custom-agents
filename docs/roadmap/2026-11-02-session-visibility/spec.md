---
spec: session-visibility
estado: implementada
creado: 2026-11-02
---

# Sesiones externas y actividad observable

Corrección solicitada por el usuario al comprobar que su sesión Codex actual
y sus agentes no aparecían en el dashboard. Alcance de esta corrección:

1. Mostrar metadatos de sesiones Codex externas del directorio registrado mediante
   la interfaz oficial. No cargar turnos, reanudar sesiones ni enviar mensajes.
2. Identificar origen, lectura parcial, fecha y estado de ejecución no confirmado.
   No convertir una sesión conocida en una conexión activa.
3. Activar la captura informativa de este proyecto y verificar eventos reales;
   explicar cómo habilitarla en otros proyectos. No reconstruir eventos pasados.
4. Distinguir señales recientes, ausencia de señal y respuesta terminada.
5. Mantener aislamiento entre proyectos y el chat de sesiones propias.
6. Aclaración posterior del usuario: `apply_patch` aparecía en «Agentes en vivo»
   como rol no informado. Renombrar la vista «Actividad» e identificar operaciones
   como herramientas y actores desconocidos como no identificados por el runtime.
7. El usuario pide información por agente y detalle de cada ejecución, con estado,
   tiempo, tokens y dinero consumido. Mostrar medidas y procedencia cuando existen;
   ausencia explícita cuando los hooks o la interfaz nativa no las proporcionan.

Límite explícito: el descubrimiento externo de Claude/OpenCode no se añade en
este arreglo. Sus conexiones creadas en la consola y sus hooks continúan
disponibles. El inventario Codex es indexado, no archivado, del cwd exacto y
acotado a 200 entradas. Ningún resultado certifica vida de otro proceso.
