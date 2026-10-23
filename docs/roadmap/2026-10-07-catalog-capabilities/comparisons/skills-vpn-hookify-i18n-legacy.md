# VPN doméstica, reglas de hooks, traducción y estilo heredado — S131–S134

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **29.807 bytes/732 líneas**, sin recursos locales.
[vpn-hookify-i18n-legacy-reading-evidence.json](vpn-hookify-i18n-legacy-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S131 — VPN WireGuard doméstica

`10.628 bytes/306 líneas`. Servidor, clientes, túnel dividido o completo, claves,
DDNS y diagnóstico. Mismo dominio que S127–S130: **fuera del bundle**. Las claves
se crean con `umask 077` y la pieza insiste en no versionarlas; sin embargo, la
plantilla pide **pegar la clave privada** en `wg0.conf` mediante un heredoc y el
generador de configuración en Python devuelve la clave privada en una cadena que
fácilmente acaba en logs.

## S132 — Reglas de hookify

`3.712 bytes/128 líneas`. Ficheros Markdown con frontmatter que casan comandos,
ediciones, prompts o el cierre por expresión regular y muestran un aviso o bloquean.

**Comparación.** El plugin separa por diseño los hooks globales (**informan, nunca
deciden**, ADR-007) de las guardias por rol (deniegan solo en el frontmatter del
agente, con `guardrail-check.py` y tests). Una regla de usuario que bloquea por
expresión regular sobre el texto del comando es frágil (variables, comillas,
alias) y sería un segundo mecanismo de decisión. Aviso por patrón sí encaja con
los hooks que informan, pero la pieza depende de un plugin ajeno (`/hookify`).
**Sin destino**; si se quisiera, sería una extensión de proyecto.

## S133 — Sincronización de traducciones JSON

`7.051 bytes/141 líneas`. Traducir claves leyendo dónde se usan en la interfaz,
respetar glosario, marcadores y plurales, preparar un parche revisable y no usar
las rutas de escritura de una herramienta concreta cuya revisión de código mostró
pérdidas de datos.

**Comparación.** Sin equivalente propio. La pieza está bien construida: el texto
fuente y el glosario son datos, no instrucciones; no escribe JSON por shell;
conserva claves y tipos ajenos; y distingue validación estructural de calidad de
traducción. Encaja en `frontend-quality` (copias de interfaz) como referencia
opcional «traducciones», con versión de la herramienta comprobada antes de usarla.

## S134 — Heredar el estilo de un proyecto antiguo

`8.416 bytes/157 líneas`. Escanear el código por cuatro dimensiones (anatomía de
fichero, estado y control, infraestructura, errores), resolver conflictos con el
usuario de uno en uno y escribir un fichero de reglas con ficheros ejemplares y
prohibiciones.

**Comparación.** El plugin tiene `docs/CONSTITUTION.md` (opt-in en `/setup`), la
lente A que revisa conformidad y `project-specialization`. Aporta dos cosas útiles:
el **umbral de señal** (una minoría pequeña se resuelve sola; un empate o una
bifurcación en una dimensión central se pregunta) y las **preguntas de una en
una** con evidencia de ambos lados. Correcciones: la «declaración de cumplimiento
en la cadena de razonamiento» de cada tarea no es verificable; el hook duro
`PreToolUse` sobre `Write|Edit` contradice que los hooks globales solo informan;
y ofrecer reescribir `CLAUDE.md` del proyecto necesita confirmación explícita.
**Destino:** umbral de señal y preguntas de una en una para la sección de
constitución de `/setup`.
