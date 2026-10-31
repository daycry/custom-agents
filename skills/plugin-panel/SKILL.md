---
name: plugin-panel
description: >
  Abre una consola local común para proyectos: sesiones y chat nativos, planes y kanban,
  comentarios, actividad, memoria e integraciones. El inventario incluye extensiones propias
  de proyecto y usuario y admite exportación HTML/JSON.
  Úsala cuando el usuario diga "dashboard", "panel de capacidades", "control panel del plugin",
  "panel del roadmap", "kanban de los planes", "dashboard del roadmap",
  "explora el catálogo del plugin" o "sesiones del proyecto".
---

# Plugin panel

## Elegir el modo

La consola operativa pertenece a esta skill; no se instala un servidor por proyecto.
Un proceso en `127.0.0.1:8769` sirve los proyectos registrados y el selector decide
el contexto. No inicies varios procesos ni elijas otro puerto automáticamente si
ya existe uno: reutiliza el enlace privado de ese proceso o informa del conflicto.

- **Trabajar desde el dashboard:** lee [Consola común](references/control-center.md)
  y ejecuta `scripts/control_center.py --workspaces <registro.json>`.
- **Piloto de un proyecto:** el mismo script admite `--project <raíz>` en lugar
  del registro. Para incorporar otros proyectos, pasa al registro común.
- **Inventario o artefacto estático:** conserva `scripts/build_panel.py --export
  <carpeta>` o `--json`; lee [Inventario y exportación](references/static-panel.md).
  Una exportación no contiene chat ni ejecuta trabajo.

Localiza los scripts en esta skill del bundle activo. No cambies configuraciones
del usuario para descubrir rutas. El servidor es explícito, nunca un efecto de
pedir un inventario. Usa Python nativo; no requiere paquetes de servidor externos.

## Proyectos y acceso

El operador mantiene un JSON explícito, fuera de los repositorios si es compartido.
Cada entrada contiene ID estable, nombre, raíz absoluta y runtimes permitidos.
No escanees carpetas personales ni registres proyectos por proximidad. El navegador
no puede enviar rutas ni modificar el registro. Los cambios del registro requieren
reiniciar el proceso, una vez terminada o revisada la ejecución propia en curso.

Entrega la URL privada sólo al usuario y conserva el handle. No la guardes en Git,
memoria, documentos o informes. En Windows, un proceso de fondo usa ventana oculta.
El enlace autoriza acceso a los proyectos de ese servidor local; no es una cuenta
por proyecto ni un servicio multiusuario. No amplíes la escucha a la red.

## Sesiones y trabajo

La conexión usa interfaces nativas de Codex, Claude Code y OpenCode compatibles.
Cada sesión valida la raíz del proyecto; no ejecuta shell libre recibido por HTTP.
Usa autenticación y políticas nativas existentes, sin opciones para saltar permisos.
Expón las capacidades y límites observados. No prometas controlar ventanas Desktop
ni importar todas las sesiones de un runtime si su adaptador no lo acredita.

Crear una sesión no envía un objetivo. Escribir un mensaje y pulsar Enviar inicia
un turno; las decisiones nativas requieren respuesta explícita y de un solo uso.
Un envío admitido, un turno iniciado y un resultado confirmado son estados distintos.
Si se pierde la confirmación, consulta antes de repetir. Interrumpir requiere
confirmación nativa; Desconectar sólo cierra la conexión/procesos propios permitidos.

La consola conserva metadatos mínimos de sesiones y comentarios locales en
`.claude/control-center/`, con dueño, bloqueo, límites y su propio `.gitignore`.
Los mensajes y las operaciones visibles quedan acotados en memoria del proceso;
el historial nativo permanece a cargo de su entorno. Nunca exportes razonamiento.

## Planes, actividad y memoria

`tasks.md` sigue siendo el registro canónico. Cartera, kanban y detalle lo leen
mediante los lectores existentes; nunca convierten arrastrar una tarjeta o añadir
una nota en QA aprobado. Continuar o revisar un plan prepara el mensaje, comprueba
la versión de sus fuentes y lo envía a una sesión elegida del mismo proyecto.
Los comentarios tienen revisión y clave de petición para evitar sobrescrituras y
duplicados. No representan por sí solos comentarios publicados en Jira o Redmine.

Actividad distingue eventos recibidos de la sesión y capturas históricas opt-in;
un estado del ledger no demuestra que un agente esté vivo. Muestra origen,
antigüedad, lectura parcial y datos no confirmados. No inventes métricas.

Memoria usa lecturas locales explícitas con `agent-kits/shared/knowledge-view.py`;
la vista no conecta Kwipu ni Graphiti. Los backends son opcionales por proyecto.
Encontrar una integración, herramienta o MCP no demuestra conexión ni autorización.
El catálogo excluye fuentes personales en esta consola compartida.

## Cierre portable y degradación

El export de esta skill incluye sus `scripts/` y `assets/`. Conserva juntos los
helpers compartidos: `agent-kits/shared/local-read.py`, `agent-kits/shared/local-state.py`,
`agent-kits/shared/redact.py`, `agent-kits/shared/project-pieces.py`,
`agent-kits/shared/ledger-view.py`, `agent-kits/shared/integration-route.py`,
`agent-kits/shared/knowledge-view.py`, `agent-kits/shared/agent-activity-store.py`,
`agent-kits/shared/agent-activity.py`, `agent-kits/shared/plan-review.py` y
`agent-kits/shared/native-roles.json`. Sus dependencias transitivas las resuelve el exportador.
El inventario informativo conserva los contratos de su referencia.

Un runtime, helper o backend ausente queda indisponible con una explicación;
las demás vistas siguen funcionando. No instales herramientas ni cambies permisos
para ocultar el problema. Conserva el registro canónico y sigue el trabajo posible.

| Recurso | Cuándo leerlo |
|---|---|
| [Consola común](references/control-center.md) | Arranque, registro, acciones, estados, límites y recuperación |
| [Inventario y exportación](references/static-panel.md) | HTML/JSON, diagnóstico importado y servidor informativo anterior |
| [Manual del dashboard](../../docs/guides/dashboard.md) | Explicar el uso a responsables y equipos |
| [Extensiones propias](../../docs/PROJECT-EXTENSIONS.md) | Piezas, personas, MCP y conflictos |
