# Mensajería, REPL propio, ciclo de vida de una CLI, API documental y personajes — S174, S181, S182, S190 y S192

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **25.219 bytes/645 líneas** y recursos de S182 y S192
leídos completos: **24.103 bytes/716 líneas** (`agents/openai.yaml` de S182; en S192,
`gacha.py`, `gacha.sh` y seis referencias). El script `scripts/claw.js` que opera
S181 no viaja con ella y no se leyó.
[messages-nasiko-nutrient-persona-reading-evidence.json](messages-nasiko-nutrient-persona-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Las cinco piezas envuelven una superficie ajena al ciclo de desarrollo (mensajería
personal, un REPL del propio corpus, una CLI de un proveedor, una API comercial de
documentos y personajes para otra plataforma). **Fuera del bundle** las cinco. Se
anotan solo las ideas generales y los defectos.

## S174 — Lectura de mensajes y códigos de un solo uso

`2.896 bytes/105 líneas`. Resolver la fuente exacta (mensajes locales, mensajes
directos de redes), leer antes de redactar, buscar códigos en una ventana corta y
devolver fuente, ventana y estado (`read`, `code-found`, `blocked`, borrador
pendiente).

Misma decisión que el correo de S092 (sin superficie de mensajería en el plugin).
La regla «no afirmar que se revisó un hilo sin nombrar la fuente» coincide con la
de publicación comprobada. Riesgo propio: que un agente recupere códigos de un
solo uso de la mensajería del usuario anula la separación que da sentido al
segundo factor. **Sin destino.**

## S181 — REPL con sesiones en Markdown

`1.144 bytes/34 líneas`. Opera un REPL del corpus con sesiones persistentes,
cambio de modelo, ramas de sesión, búsqueda, compactación y exportación.

Sin el script no hay nada que evaluar más allá de cuatro consejos de uso. «Ramificar
antes de cambios arriesgados» ya lo cubre el worktree opt-in de `/dev-cycle`
(`dev.json` `worktree`); la continuidad tras compactar, el journal y el índice de
piezas. **Sin destino.**

## S182 — Ciclo de vida de una CLI de proveedor

`2.639 bytes/49 líneas` más `agents/openai.yaml` (277 bytes/4 líneas). Estado de
solo lectura, instalación con consentimiento y versión fijada (vista previa
`--dry-run`, digest del artefacto y del binario), desinstalación solo de lo que
instaló, sin buscar en `PATH`, sin `latest` como alternativa y telemetría con
consentimiento aparte.

El método coincide con el instalador propio (`install/install.mjs`: idempotente,
desinstala por manifiesto «con la lista EXACTA de lo que escribió» y solo
actualiza ficheros nativos cuyo SHA-256 coincide con su inventario; los ajenos o
modificados se conservan). Dos reglas que conviene recordar si el
instalador crece: **instalar no implica consentir telemetría**, y una instalación
parcial o ambigua no es éxito. Producto concreto: **fuera del bundle**.

## S190 — Procesado de documentos con una API comercial

`6.015 bytes/168 líneas`. Conversión, extracción, OCR, redacción de datos
personales, marcas de agua, firma y formularios mediante peticiones `curl` a un
servicio externo, o su servidor MCP.

`to-pdf` es el dueño de la conversión a PDF en el plugin y trabaja en local.
Problemas de la pieza:

| Punto | Problema |
|---|---|
| «Redactar datos personales antes de compartir» | Para redactarlos hay que enviar el documento completo, con esos datos, a un tercero; coherente con S126: proveedor bloqueado por defecto hasta que conste que puede recibirlos |
| Configuración MCP con la clave escrita en el JSON y `npx -y` sin versión | Contra `delivery-practices` (versiones fijadas, credenciales fuera de la configuración) |
| Firma CMS autofirmada presentada para «firmar contratos» | Un certificado autofirmado no acredita identidad del firmante |
| Redacción por patrón | No propone comprobar el resultado (extraer el texto del PDF redactado y buscar los patrones) |

**Fuera del bundle.**

## S192 — Forja de personajes para otra plataforma de agentes

`12.525 bytes/289 líneas` más recursos (23.826 bytes/712 líneas). Diseño guiado o
«por sorteo» de una persona (identidad, reglas, nombre, prompt de avatar) que
termina escribiendo `SOUL.md` e `IDENTITY.md`. El sorteo lo hace `gacha.py` con
`secrets`; el total que anuncia (8 millones) cuadra con sus cinco listas
(40 × 20 × 20 × 20 × 25).

En el plugin, «persona» es otra cosa: la persona de dominio que `task-brief.py`
inyecta en el brief de un subagente (`.claude/personas/<tipo>.md` del proyecto o
el catálogo de `agent-kits/shared/personas/`), con prioridades y trampas técnicas,
no un personaje. **Fuera del bundle.** Defectos:

- El paso de sorteo exige ejecutar el script y prohíbe «inventar el azar», pero la
  degradación sin Python manda elegir «al azar» entre diez opciones: lo haría el modelo.
- El prompt del avatar se escribe en una ruta fija de `/tmp` derivada del nombre:
  predecible y sin equivalente en Windows.
- «Cualquier error inesperado: registrar, saltar el paso y seguir» puede omitir un
  paso en silencio; el plugin degrada con aviso, pero no convierte un error en éxito.
- Las reglas de límite se reescriben como metáforas del personaje («no componer
  canciones» por «no inventar»); una regla de seguridad dicha en metáfora es más
  fácil de malinterpretar que la literal.

Idea general reutilizable: antes de escribir el fichero, **cada línea debe cambiar
el comportamiento del agente; si al quitarla no cambia nada, se borra**. Es el
criterio de ADR-008 aplicado línea a línea. **Destino:** una línea en los
anti-patrones de `skills/plugin-dev/SKILL.md`.
