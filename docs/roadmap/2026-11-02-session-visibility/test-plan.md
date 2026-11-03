# Plan de pruebas — sesiones y actividad

Interfaz local del plugin. Las pruebas usan un proyecto de fixture por workspace,
sin inferencia. Las evidencias reales del proyecto sólo conservan conteos y
comprobaciones booleanas; no guardan credenciales, nombres de conversación ni IDs.

## E2E-01 — Sesiones externas y contador observado

- **Tareas**: T-01, T-02.
- **Dado**: cero conexiones propias y una conversación Codex externa del workspace.
- **Cuando**: se abre Sesiones.
- **Entonces**: hay una tarjeta de sólo lectura y el contador muestra 1; controles
  de enviar/interrumpir no se activan para esa conversación. El título se escapa.
- **Ausencia**: una consulta fallida indica indisponibilidad, nunca cero demostrado.

## E2E-02 — Estado y detalle de ejecución

- **Tareas**: T-03.
- **Dado**: un agente identificado con final comunicado y operaciones capturadas.
- **Cuando**: se abre Actividad y Ver ejecución.
- **Entonces**: estado Terminado, fecha y tiempo observado; tokens/coste explícitamente
  no disponibles si el hook no los entrega; operaciones con resumen, herramienta,
  resultado comunicado y duración sólo cuando existe. Las herramientas no se
  presentan como agentes.

## E2E-03 — Aislamiento de proyectos

- **Tareas**: T-01, T-02.
- **Cuando**: se cambia de workspace y llega una respuesta atrasada del anterior.
- **Entonces**: no aparecen sesiones, operaciones ni detalles del proyecto anterior.
  Los IDs de otro workspace son rechazados por el servidor.

## E2E-04 — Recuperación y teclado

- **Tareas**: T-03.
- **Cuando**: falla un refresco de detalle y después se recupera el mismo contenido.
- **Entonces**: desaparece el error y reaparece la ficha. Sus controles tienen
  nombres accesibles y funcionan con teclado. Cerrar devuelve foco al agente.

## E2E-05 — Comprobación real sin ejecutar modelos

- **Tareas**: T-01, T-02.
- **Cuando**: se abre el proyecto registrado y se consulta su inventario real.
- **Entonces**: incluye la sesión actual y muestra señales reales recibidas después
  del opt-in. Una sesión encontrada no se etiqueta como conexión controlable.
- **Evidencia**: API y navegador automatizado local, sólo conteos/booleanos en el
  informe público; capturas reales, si se precisan, quedan fuera de Git.

## M-01 — Edge del usuario

La inspección directa está pendiente si el puente de navegador no puede verificar
su URL. Se declara ese límite; el navegador automatizado no se presenta como una
inspección de la pestaña personal de Edge.
