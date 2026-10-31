> Referencia avanzada. Empieza por el [manual explicado paso a paso](../CUSTOMIZATION.md). Este capítulo conserva contratos de implementación y configuración.

# 5. Personalizar el producto sin modificar el core

## W-16. Decidir dónde vive una ampliación

**Disparador:** el equipo necesita otro criterio, rol, sistema externo o herramienta.
**Comando de contexto:** `/work-context`; catálogo opcional con `/plugin-catalog`.
**Actores:** responsable de dominio y equipo técnico; planner registra la selección
en las tareas que la usan. **Lectores:** `project-pieces.py` y capability-route.

| Necesidad | Pieza apropiada | Ubicación/dueño | Comprobación antes de usar |
|---|---|---|---|
| Criterios de facturación, legal o negocio | Persona breve | Proyecto | Tipo de tarea y límites del brief |
| Especialista con objetivo y herramientas propias | Agente | Runtime del proyecto | ID real, contrato y herramientas permitidas |
| Método que reutilizan varios roles | Skill | Proyecto, usuario o módulo del bundle | Disparadores, referencias y casos positivos/negativos |
| Secuencia que inicia el usuario | Comando | Runtime que soporte comandos propios | Entradas, decisiones, salidas y handoffs |
| Regla permanente del proyecto | Instrucciones/constitución | Proyecto | Alcance y precedencia nativos, sin duplicar manuales |
| Operación programática | Tool o script con contrato | Proyecto/runtime | Esquema, exit codes, permisos y pruebas |
| Acceso a un servicio | Servidor MCP o conector | Runtime/administrador | Confianza, autenticación, permisos y operaciones reales |
| Uso de un proveedor en el ciclo | Adaptador + binding | Proyecto | Capacidades/eventos, destino, recibos y reconciliación |

No se añade un agente solo para envolver una skill ni una skill para enumerar
herramientas disponibles. Una configuración MCP no es un workflow. Una persona no
es una cuenta de usuario. Las extensiones complementan a los dueños del core.

## Personas de dominio y personas del equipo

Las **personas de dominio** son perfiles cortos de criterio. Para facturación:

```markdown
# Persona de facturación
Comprueba moneda, impuestos, redondeos y periodo de facturación.
Exige ejemplos de rectificación y conservación del rastro de auditoría.
No decide políticas fiscales por su cuenta ni sustituye al responsable del área.
```

Se guarda en `.claude/personas/facturacion.md`, convención propia del plugin,
y se etiqueta la tarea con `- **Tipo**: facturacion`. El brief prioriza la persona
del proyecto, luego la del catálogo; si no hay ninguna, avisa y continúa. No se
instalan agentes nativos por crear este perfil. No se copia un dossier privado de
una persona real para simular su identidad.

Las **personas del equipo** son usuarios reales con cuentas, roles y permisos en
el runtime y los servicios. El administrador las invita mediante los mecanismos
del proveedor. El equipo acuerda quién aprueba alcance, quién puede publicar y
quién es responsable de cada tarea. El plugin no crea esas identidades. Asignar
un issue a alguien puede notificarle: se previsualiza y autoriza ese efecto.

## Añadir un agente del proyecto

En Claude Code, ejemplo de especialista de lectura:

```markdown
---
name: project-billing-reviewer
description: Revisa reglas de facturación y redondeo; úsalo al revisar cambios de importes.
tools: Read, Grep, Glob
model: sonnet
---
Revisa solo el alcance recibido. Devuelve hallazgos con archivo, línea,
caso de negocio y evidencia. No edites código, no apruebes QA y no publiques.
```

Ubicación: `.claude/agents/project-billing-reviewer.md`. En Codex se declara un
agente TOML en `.codex/agents/` o un rol en su configuración; en OpenCode se usa
su formato de agentes en `.opencode/agents/` o configuración correspondiente.
No copies frontmatter de un runtime a otro como si sus campos fueran universales.
[Carpetas, formatos e inventario](../PROJECT-EXTENSIONS.md).

Ejemplo mínimo del formato independiente que reconoce el lector de Codex:

```toml
name = "project-billing-reviewer"
description = "Revisa importes y redondeo con evidencia del proyecto."
developer_instructions = "Revisa el alcance recibido; devuelve hallazgos citados. No publiques ni cambies estados."
```

Que el inventario reconozca el archivo no certifica que el runtime admita todos
los campos/opciones de la versión instalada. Comprueba el agente nativo y sus
restricciones efectivas. El modelo elegido no concede herramientas ni permisos.

## Añadir una skill de proyecto

El ejemplo Redmine del manual se acompaña de
`docs/examples/integrations/project-redmine/SKILL.md`. Se copia a la raíz de
skills del runtime: `.claude/skills/`, `.agents/skills/` para Codex o la carpeta
admitida por OpenCode. No se coloca en la caché de custom-agents.

Una skill profesional contiene nombre único, descripción con disparadores,
objetivo, entradas, pasos, límites, errores y referencias bajo demanda. Las
instrucciones dicen qué hace la capacidad; el cálculo, parsing y veredicto
determinista pertenecen a scripts probados. Si depende de una herramienta externa,
declara esa dependencia y su degradación explícita.

Para `project-redmine`, los casos mínimos incluyen configuración ausente, permisos
solo lectura, proyecto incorrecto, transición inexistente, un lote parcial y un
timeout tras crear. El ejemplo aportado es un contrato inicial para adaptar, no
una implementación de transporte que se pueda declarar probada sin esos ensayos.

## Añadir comandos y reglas

Un comando de proyecto puede coordinar la skill anterior para publicar un plan,
pero debe mantener un único dueño por operación. En Claude los comandos viven en
`.claude/commands/`; en OpenCode, en su carpeta/configuración de comandos. Codex
no recibe comandos de proyecto por el mero hecho de crear esa misma carpeta:
usa las capacidades nativas que soporte la versión instalada, por ejemplo una
skill invocable. El inventario del plugin no inventa un cargador de comandos.

Las reglas permanentes van en las instrucciones nativas del proyecto y, para
principios del producto, en `docs/CONSTITUTION.md` si se elige usarla. Evita pegar
todo el manual en el archivo de instrucciones: enlaza el detalle y carga lo
pertinente. Una instrucción local no debe relajar revisión, autorización o gates
que el proyecto haya fijado como obligatorios.

## W-17. Añadir una tool o servidor MCP

**Actor principal:** administrador o desarrollador del proyecto.
**Comandos de inventario:** `/work-context`, `/doctor`; los comandos nativos MCP
dependen del runtime. **Skill:** `delivery-practices` para revisar límites de entrega
y permisos; adaptador del proyecto para las operaciones de negocio.

| Paso | Acción | Evidencia que se necesita |
|---|---|---|
| 1 | Define la operación que falta | Ejemplo de entrada, salida y efecto; no «conectar todo» |
| 2 | Busca conector oficial o mantenido y revisa su contrato | Dueño, licencia, mantenimiento y compatibilidad |
| 3 | Elige scope y autenticación | Cuenta y proyecto correctos; secretos en almacén seguro |
| 4 | Declara servidor en el runtime | Config válida; no es todavía prueba de conexión |
| 5 | Conecta/autoriza con mecanismos del runtime | Sesión y lista de operaciones disponibles |
| 6 | Ejecuta una lectura acotada de prueba | Resultado del destino esperado y manejo de errores |
| 7 | Añade adaptador y binding si participa en el ciclo | Capacidades/eventos coinciden con lo probado |
| 8 | Previsualiza una escritura piloto y autorízala | Recibo confirmado y reconciliación probada |
| 9 | Repite pruebas al cambiar versión/permisos | No se deduce disponibilidad de un inventario antiguo |

Un script local no se convierte en tool nativa por estar en una carpeta cualquiera.
OpenCode reconoce fuentes de custom tools; Claude y Codex exponen herramientas
según sus contratos de runtime/MCP. El lector de extensiones no importa scripts,
no ejecuta exports ni instala paquetes para descubrir qué contienen.

### Ejemplos de declaraciones MCP

Estos endpoints usan `.invalid`: son ejemplos seguros que deben sustituirse por
el endpoint real aprobado. No son servidores instalables ni conexiones verificadas.

Claude Code, `.mcp.json` de proyecto:

```json
{
  "mcpServers": {
    "corporate-wiki": {
      "type": "http",
      "url": "https://wiki.example.invalid/mcp"
    }
  }
}
```

Codex, bloque de configuración MCP:

```toml
[mcp_servers.corporate_wiki]
url = "https://wiki.example.invalid/mcp"
```

OpenCode, ejemplo de formato con bloque `mcp` por servidor:

```json
{
  "mcp": {
    "corporate-wiki": {
      "type": "remote",
      "url": "https://wiki.example.invalid/mcp",
      "enabled": true
    }
  }
}
```

Usa el esquema de la versión instalada. El inventario también reconoce superficies
OpenCode V2 como `mcp.servers`; reconocer ambas no establece una precedencia nativa.
No cambies el formato solo para eliminar un aviso del inventario.

Fuentes de configuración verificadas: [MCP de Claude Code](https://code.claude.com/docs/en/mcp),
[MCP de Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) y
[MCP de OpenCode](https://opencode.ai/docs/mcp-servers/). Cada runtime conserva
su autenticación, política de confianza y permisos efectivos.

## Binding directo a una tool

Un binding puede usar `adapter: {"kind":"tool","name":"nombre-real","origin":"session"}`.
Solo es adecuado si el workflow puede comprobar el contrato de esa operación:
esquema, propósito, destino, autorizaciones y recibos. Un nombre descubierto no
demuestra que una tool sirva para todas las capacidades de un proveedor.
Para un proceso de varios pasos, un adaptador skill es normalmente más claro.

## Perfiles y entrega selectiva

Vista lógica, sin instalar ni escribir configuración:

```powershell
node --input-type=module -e "import {resolveSelection} from './install/modules.mjs'; console.log(JSON.stringify(resolveSelection({profile:'core',include:['jira']}),null,2))"
python agent-kits/shared/module-selection.py --profile core --with jira
```

Export portable de skills, desde el checkout del plugin:

```powershell
python scripts/export-skills.py --profile core --with jira --out dist/area-skills --format all
python scripts/export-skills.py --check dist/area-skills
```

Entrega por copia Claude, con limitaciones explícitas de ese modo:

```powershell
node install/install.mjs install -p claude-code --mode copy --profile core --with jira --dir <proyecto> --dry-run
```

Tras revisar el plan, se ejecuta sin `--dry-run`. El modo copia no registra por sí
solo hooks, statusline ni namespace de plugin. Los destinos con archivos ajenos o
modificados se rechazan antes de copiar; los cambios de perfil retiran únicamente
archivos propios intactos. Se conserva la selección al reinstalar sin flags.

Los plugins nativos son bundles completos. Una petición parcial incompatible se
rechaza antes de registrar o escribir; no se personaliza la caché compartida.
La selección parcial del instalador OpenCode no está soportada en esta versión;
usa el bundle completo o el paquete portable de skills según lo que necesites.
Un paquete portable no equivale al ciclo completo instalado.

## Conflictos, selección y mantenimiento

Usa nombres propios como `project-redmine` para evitar colisiones. El lector
conserva fuentes e IDs y muestra duplicados; no decide una precedencia universal
entre runtimes. Planner registra IDs de extensiones en `Extensiones` y su fuente
en `Procedencia de extensiones`. El brief revalida la selección antes de usarla.

Si existe `.claude/pieces.json`, el inventario compara sus hashes y declara
propiedad/modificación, sin adoptar ni sobrescribir archivos. No es un ejecutor
de extensiones. Los procesos de adopción/generación cancelados anteriormente no
se reactivan por instalar este diseño modular.

Versiona los contratos, ejemplos y pruebas del proyecto. Mantén estado operativo
y credenciales fuera del repositorio. Al retirar una extensión, comprueba qué
tareas la referencian y deja una alternativa o un aviso; no sustituyas silenciosamente
su nombre por otra capacidad de comportamiento diferente.
