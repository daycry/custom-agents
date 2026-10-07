# Integración por fases

[English](en/INTEGRATION-ROADMAP.md) · **Español**

Orden acordado con el usuario el 2026-10-06. Cada fase se entrega con alcance,
comparación con las funciones existentes, pruebas, revisión, documentación y
push de su rama. Las fases futuras requieren su propio plan; esta página no
acredita que estén implementadas.

| Fase | Entrega | Estado |
|---|---|---|
| 1. Núcleo común | Hooks multi-runtime, selección de guías, workflow, briefs, contexto estructural opcional, evaluación de resultados y panel | Completada y publicada; evidencia en [workflow-integration](roadmap/2026-10-06-workflow-integration/tasks.md) |
| 2. Extensiones del usuario | Reconocer agentes, skills, personas, tools y MCP propios en Claude, Codex y OpenCode; mostrar origen, conflictos y disponibilidad sin verificar | Completada y publicada en feat/project-extensions; diez tareas, revisión y QA cerradas. [Plan y evidencia](roadmap/2026-10-06-project-extensions/tasks.md) |
| 3. Capacidades del catálogo | Comparar en profundidad las skills, tools, agentes y comandos existentes en el catálogo de referencia; integrar mejoras útiles y verificar el alcance real de guardias por runtime | En progreso (1/16); inventario completo reconciliado: 455 piezas principales y 4.212 archivos, incluidos los paneles. Comparación semántica e integración pendientes. [Plan y evidencia](roadmap/2026-10-07-catalog-capabilities/tasks.md) |
| 4. Memoria y evaluación | Medir recuperación, vigencia y utilidad; comparar mejoras con Markdown, journal y backends actuales antes de decidir cambios | Pendiente; el piloto AST actual no demuestra eficacia de recuperación |

No se crearán paquetes técnicos nuevos para rellenar huecos del catálogo de
referencia. Cualquier capacidad técnica futura debe existir allí y justificar
su incorporación frente a lo que ya tenemos. La selección será opcional y
adaptada al proyecto, sin imponer paquetes por stack a todos los usuarios.
Las guías existentes en el plugin se mantienen sujetas a sus contratos actuales.

## Qué reconoce la rama de extensiones

| Componente propio | Comportamiento actual | Límite |
|---|---|---|
| Agente | Lector y panel reconocen Markdown, TOML y roles de configuración de proyecto/usuario por runtime | Una declaración no prueba carga; complementa los roles del ciclo |
| Skill con frontmatter | Inventario de fuentes nativas y compatibles, con selección explícita por ID | El contenido se consulta bajo demanda; no se añade automáticamente al catálogo empaquetado |
| Persona de dominio | El brief prioriza `.claude/personas/<tipo>.md` del proyecto | Es una persona para el brief, no un agente independiente; los tipos son libres |
| Tool | Muestra nombres declarados y fuentes JS/TS de OpenCode | No ejecuta exports ni acredita permisos o disponibilidad |
| Servidor MCP | Inventaría declaraciones de proyecto, usuario y agentes; señala definiciones Claude inválidas y desactivación declarada | No conecta servidores ni exporta endpoints, comandos, variables o credenciales |

`feat/project-extensions` contiene esta integración publicada y verificada. El
lector compartido alimenta `/work-context`, la selección del ledger, las
referencias del brief y el panel con filtros independientes. Preserva duplicados
y muestra fuentes; antes de invocar hay que contrastar las capacidades de la
sesión. Reutiliza el contrato O1 de [especialización](SPECIALIZATION.md) para
validar propiedad en modo lectura; generación/adopción siguen en su plan propio.

Los resultados, el informe QA, la retro y la comprobación remota están en el
ledger de fase 2. El cierre acredita reconocimiento y selección de extensiones;
no acredita adopción, generación ni las fases 3 y 4. El catálogo publicado
de fase 1 mantiene su entrega registrada en su propio ledger.

**Comprobación de alcance pendiente en fase 3:** la documentación Claude actual
indica que los agentes de plugin ignoran `hooks`, `mcpServers` y `permissionMode`
de su frontmatter. La guardia declarada del implementer debe probarse por modo
de instalación y ajustarse antes de afirmar su cobertura en plugins. Véanse los
[contratos verificados](../skills/plugin-dev/references/claude-code-contracts.md).
