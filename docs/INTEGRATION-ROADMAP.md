# Integración por fases

[English](en/INTEGRATION-ROADMAP.md) · **Español**

Orden acordado con el usuario el 2026-10-06. Cada fase se entrega con alcance,
comparación con las funciones existentes, pruebas, revisión, documentación y
push de su rama. Las fases futuras requieren su propio plan; esta página no
acredita que estén implementadas.

| Fase | Entrega | Estado |
|---|---|---|
| 1. Núcleo común | Hooks multi-runtime, selección de guías, workflow, briefs, contexto estructural opcional, evaluación de resultados y panel | Completada y publicada; evidencia en [workflow-integration](roadmap/2026-10-06-workflow-integration/tasks.md) |
| 2. Extensiones del usuario | Reconocer agentes, skills, tools y MCP propios en Claude, Codex y OpenCode; mostrar origen, conflictos y disponibilidad comprobada | Pendiente de diseño e implementación |
| 3. Capacidades del catálogo | Comparar en profundidad las skills, tools, agentes y comandos existentes en el catálogo de referencia; integrar únicamente mejoras útiles, sin duplicar responsabilidades | Pendiente; el inventario previo no sustituye al análisis funcional |
| 4. Memoria y evaluación | Medir recuperación, vigencia y utilidad; comparar mejoras con Markdown, journal y backends actuales antes de decidir cambios | Pendiente; el piloto AST actual no demuestra eficacia de recuperación |

No se crearán paquetes técnicos nuevos para rellenar huecos del catálogo de
referencia. Cualquier capacidad técnica futura debe existir allí y justificar
su incorporación frente a lo que ya tenemos. La selección será opcional y
adaptada al proyecto, sin imponer paquetes por stack a todos los usuarios.
Las guías existentes en el plugin se mantienen sujetas a sus contratos actuales.

## Qué reconoce hoy el plugin

| Componente propio | Comportamiento actual | Límite |
|---|---|---|
| Agente Markdown con frontmatter | Panel e índice leen `agents/*.md` de la raíz inspeccionada | No combinan automáticamente todas las instalaciones ni formatos de los tres runtimes; no añaden roles al workflow |
| Skill con frontmatter | Panel e índice leen `skills/*/SKILL.md` de esa raíz | El selector del workflow usa el catálogo empaquetado; descubrir una skill no la registra en él |
| Persona de dominio | El brief prioriza `.claude/personas/<tipo>.md` del proyecto | Es una persona para el brief, no un agente independiente; los tipos son libres |
| Tool | El panel resume los nombres declarados en el frontmatter de los agentes | No es un registro de herramientas propias ni prueba de ejecución o permisos |
| Servidor MCP | No hay inventario de servidores MCP en el panel | Su configuración, conexión y herramientas expuestas no se detectan actualmente |

La raíz de inspección se elige explícitamente. El reconocimiento del runtime y
el inventario del plugin son funciones diferentes; listar un fichero no prueba
que la sesión lo haya cargado. La fase 2 deberá preservar las piezas del usuario,
resolver colisiones por origen y distinguir **declarada**, **detectada** y
**disponible en la sesión**. No ejecutará herramientas ni conectará servidores
por el mero hecho de encontrarlos. Reutilizará el contrato de
[especialización](SPECIALIZATION.md), cuya cascada de personas está implementada
y cuyo registro/adopción siguen siendo trabajo pendiente.
