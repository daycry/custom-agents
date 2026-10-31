# Consola de trabajo v3 — diseño y contrato de entrega

Petición aprobada del usuario: UI moderna, interactiva y útil; un puerto para los
proyectos registrados; sesiones y chat, planes/kanbans, inicio de trabajo, actividad,
memoria e integraciones. La autorización incluye implementación, commits, push, PR
y release v3.0.0. Las limitaciones nativas se explican; no se simula paridad Desktop.

## Decisión

Componer el panel existente y las interfaces de sesión nativas. La consola es una
superficie propia; no copia bases privadas ni automatiza ventanas de aplicaciones.
El proceso local mantiene un registro explícito de workspaces. Cada operación se
resuelve en servidor por workspace + sesión/plan; ningún endpoint acepta una ruta
arbitraria. Un único servidor loopback sirve UI y API. No se expone por red como si
fuera un producto multiusuario autenticado.

Alternativas: una terminal incrustada reproduce escape sequences y dificulta
accesibilidad/controles; leer bases de Desktop es frágil y no concede control de
sesiones; reimplementar un agente duplica políticas y configuración. Se eligen
adaptadores nativos y una matriz de capacidades real por entorno/versión.

## Dirección visual

Centro de trabajo denso y legible: superficies grafito, acento violeta para acciones
y turquesa para actividad observada; estados siempre con texto. Navegación lateral
estable y selector de proyecto. Sesiones con lista, conversación y herramientas;
cartera en lista/tablero; detalle con fases, kanban y panel de tarea/comentarios;
actividad con agentes y línea temporal; memoria separa canon y servicios opcionales.
Tema claro/oscuro, teclado, foco visible y movimiento reducido. No hay métricas,
avatares de personas o pulsos vivos ficticios. Vista vacía invita a una acción útil.

## Interfaces contrastadas el 2026-10-31

- Codex: app-server permite conversaciones, eventos e intervenciones; se usa stdio
  y se contrasta el esquema generado por la versión instalada. La selección del
  proyecto se valida en cada thread. No se presupone controlar una ventana Desktop.
  [Fuente oficial](https://learn.chatgpt.com/docs/app-server).
- Claude Code: intercambio stream-json y reanudación; el protocolo de control del
  SDK permite transportar peticiones de permiso e interrupciones sin omitir controles.
  Sesiones conocidas por la consola; descubrimiento adicional solo con interfaz
  compatible y alcance verificable. [CLI](https://code.claude.com/docs/en/cli-reference),
  [transporte](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/transport/subprocess_cli.py),
  [control](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/query.py).
- OpenCode: servidor local con sesiones, mensajes, eventos y decisiones. Se verifica
  el OpenAPI del ejecutable instalado; no se presupone que V1 y V2 compartan rutas.
  [Documentación oficial](https://opencode.ai/docs/server/).

Versiones locales observadas: Codex CLI 0.166.0, Claude Code 2.1.311 y OpenCode
2.0.12. Son evidencia de este equipo, no versiones mínimas universales. Una conexión
incompatible queda indisponible con explicación. Cada adaptador expone capacidades
comprobadas y límites. Servicios nativos pueden abrir canales internos propios; el
usuario abre una sola URL de dashboard.

## Datos y responsabilidades

- Los planes se leen mediante panel_data/ledger-view. tasks.md sigue siendo canónico.
  Una interacción de tablero solicita trabajo en la sesión; no inventa aprobación,
  QA ni tarea completada por arrastrar una tarjeta.
- Comentarios propios: nota de colaboración con ID, autor declarado, fecha y tarea;
  texto redactado antes de persistir, escritura con dueño y control de versión.
  No es comentario remoto ni veredicto del Curator. Comentarios externos solo si la
  integración configurada los ofrece y confirma su operación.
- Sesión: proveedor nativo e ID, workspace y estado observado. Un turno en ejecución
  no admite un segundo envío accidental; el cliente conserva borrador al fallar.
- Chat y eventos de herramientas se muestran de forma acotada y redactada en memoria
  del proceso. No se exportan conversaciones crudas ni razonamiento interno. La
  persistencia nativa pertenece al runtime; la consola guarda solo vínculos propios.
- Actividad con procedencia, timestamp y estado desconocido si no hay observación.
  No inferir skills/MCP usados de que estén instalados. Omitir thinking/reasoning.
- Inicio/retoma de plan entrega un prompt revisable a la sesión elegida. Las puertas
  del ciclo y los permisos nativos siguen vigentes. No lanzar workers desde un GET.

## Aislamiento y recuperación

Autenticación local por capacidad de arranque, cookie HttpOnly SameSite y CSRF con
Origin/Host. Sin CORS ni shell libre por HTTP. IDs ligados al workspace en servidor;
rechazo de IDs ajenos, rutas inseguras, enlaces y respuestas excesivas. Presupuestos
para cuerpos, líneas, eventos, procesos y tiempo de conexión. Registros sin tokens.
El navegador descarta respuestas de un workspace/sesión anterior y cancela sus
lecturas al cambiar. Desconectar no equivale a detener al runtime. Interrupción
solicitada y terminación confirmada se distinguen. Se cierran solo procesos propios.
Una respuesta perdida no se reenvía automáticamente. Sesiones heredadas desconocidas
requieren descubrimiento y validación; nunca se acepta un ID arbitrario del navegador.

## Verificación

TDD por criterio para registro, aislamiento HTTP, sesiones, cada protocolo y control
de duplicados; fixtures de fallos y presupuestos. Pruebas reales acotadas por runtime
sin modificar servicios existentes. Navegador: flujo de sesión, cambio de proyecto,
kanban/detalle/comentarios, error/reintento, teclado, 375px y escritorio. Capturas de
UI real y estados vacíos. CI del commit final y documentación/PDF coherentes antes
de release. Ollama permanece pendiente por elección previa del usuario.


## Ajuste del acceso local tras la prueba de frontera

Una cookie de un host puede llegar a otros puertos del mismo host (RFC6265). La
credencial de arranque no se coloca en la cookie: viaja en Authorization desde el
cliente, ligado a su origen/puerto. Se conserva solo en sessionStorage de la pestaña
para recargar, nunca en archivos del proyecto, logs o URL después del bootstrap.
La cookie HttpOnly/SameSite contiene otro nonce independiente y no autentica sola.
No existe endpoint que devuelva la credencial a partir de esa cookie. Host/Origin
y la cabecera siguen siendo obligatorios. Credenciales de proveedores no llegan al
navegador. Este acceso es local y no sustituye identidad multiusuario por red.
Fuente: https://www.rfc-editor.org/rfc/rfc6265#section-8.5
