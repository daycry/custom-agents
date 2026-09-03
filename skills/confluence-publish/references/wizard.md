# confluence-publish — el asistente guiado, paso a paso (Pasos 1 a 5, confirmación, modo rápido y cierre)

> Referencia de la skill `confluence-publish`. Léela **solo** cuando el opt-in (Paso 0 del `SKILL.md`) esté en `true` y vayas a acompañar al usuario por el asistente (conectar → espacio → árbol → nombre → confirmar) o a cerrar en llano. Contiene los guiones literales de cada paso, incluidos el navegador de árbol (3-A) y el modo conversacional (3-B).

## Paso 1 — conectar con Confluence (interactivo)

Es lo primero, y se hace acompañando al usuario, no fallando en silencio:

1. Comprueba la conexión con `getAccessibleAtlassianResources`.
2. **Si NO está conectado:** explícalo en llano y guía la acción, sin jerga:
   > "Para publicar necesito conectarme a vuestro Confluence. Ábrelo en los conectores de Claude (Atlassian) y dime cuando esté; lo compruebo al instante."
   Ofrece reintentar ("¿Ya está? Vuelvo a comprobar"). Reintenta `getAccessibleAtlassianResources` cuando el usuario confirme. No sigas hasta que conecte.
3. **Si hay varios sites Atlassian**, muéstralos por su nombre y deja elegir (guarda el `cloudId` por debajo). Si solo hay uno, úsalo sin preguntar.
4. Cuando conecte, confírmalo con naturalidad: "Conectado ✅ a **<nombre del site>**." y sigue.
5. Ahora localiza la config del proyecto:
   ```bash
   CFG="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*confluence.json' 2>/dev/null | head -1)"
   ```
   - **Si existe** → **Modo rápido** (Paso 3-bis).
   - **Si no** → sigue al Paso 2.

---

## Paso 2 — buscar y elegir espacio

El usuario puede tener muchos espacios: **permite buscar por nombre**, no solo listar.

1. Ofrece de entrada los más probables y la opción de buscar:
   > "¿En qué espacio lo publico? Puedes escribir parte del nombre para buscar.
   > 1) Ingeniería   2) Operaciones   3) Marketing   4) 🔎 Buscar otro…"
2. Si escribe texto para buscar, filtra con `getConfluenceSpaces` (por nombre/clave) y muestra las coincidencias **por su nombre**, numeradas. Si no hay coincidencias, dilo y deja reintentar.
3. Al elegir, guarda internamente el espacio (spaceKey/spaceId) y **pasa a mostrar su árbol** (Paso 3). El propio hecho de elegir espacio dispara la vista del árbol.

---

## Paso 3 — ver el árbol del espacio y elegir dónde

**Detecta el entorno primero:**

- **Con artefactos (Cowork / app de escritorio):** usa el navegador visual (Paso 3-A).
- **Sin artefactos (Claude Code CLI o extensión de VSCode):** el host de artefactos no existe; usa el **modo conversacional** del árbol (Paso 3-B). No intentes `create_artifact`.

Para saberlo, comprueba si la herramienta de crear artefactos está disponible; si no lo está, ve directo al Paso 3-B.

### Paso 3-A — navegador de árbol (artefacto del plugin)

Nada más elegir espacio, **abre el navegador de árbol del plugin** para que el usuario
explore y elija. **No improvises un HTML**: usa siempre la plantilla incluida y publícala como
artefacto (así todos usan el mismo).

1. Localiza la plantilla sin depender del scope:
   ```bash
   TPL="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/confluence-publish/assets/tree-browser.template.html' 2>/dev/null | head -1)"
   ```
2. Resuelve los datos: `cloudId` (de `getAccessibleAtlassianResources`), `homepageId` del espacio elegido (viene en `getConfluenceSpaces`), la clave y el nombre del espacio, y el `DEFAULT_NAME` (nombre de la carpeta del proyecto).
3. **Copia la plantilla y sustituye los marcadores** `{{SERVER}}` (el nombre completo `mcp__<uuid>__getConfluencePageDescendants` del conector conectado), `{{CLOUD_ID}}`, `{{HOME_ID}}`, `{{SPACE_KEY}}`, `{{SPACE_NAME}}`, `{{SPACE_INITIALS}}`, `{{DEFAULT_NAME}}`.
4. Publica el resultado con `create_artifact` (con `mcp_tools=[el getConfluencePageDescendants del conector]`). El artefacto **navega el árbol en vivo**: al expandir un nodo llama a `getConfluencePageDescendants`, sin volcar nada al chat.
5. **Al pulsar "Elegir aquí"** el propio artefacto pregunta al usuario:
   - **Usar esa página como destino** → el contenido colgará directamente de ella (no se crea página nueva).
   - **Crear una página hija nueva** → pide el **nombre** y colgará el contenido de esa página nueva.
   - En la **raíz del espacio** siempre se crea una página nueva (pide nombre).
   La elección queda en `window.__dest = {mode, parentPageId, parentPath, name}` (`mode`: `existing` | `child` | `root-child`). Cuando el usuario te diga "publica aquí", lee esa decisión y continúa.

### Paso 3-B — navegación conversacional (CLI/VSCode, sin artefactos)

Mismo resultado, en texto. Navega el árbol bajo demanda con el conector:

1. Carga el primer nivel con `getConfluencePageDescendants` sobre el `homepageId` del espacio (o `getPagesInConfluenceSpace`). Muestra las páginas **numeradas por título**, indicando cuáles tienen subpáginas.
2. Ofrece siempre estas acciones: **abrir** una página (número → recarga sus hijas con `getConfluencePageDescendants`), **subir** un nivel, o **elegir** el destino actual.
3. Al elegir una página, pregunta en texto lo mismo que el artefacto:
   > "¿Cómo publico en «X»? 1) Usar esta página como destino  2) Crear una página hija (dime el nombre)"
   Y para la raíz del espacio, siempre se crea página nueva (pide nombre).
4. Registra la decisión equivalente (`mode`: `existing` | `child` | `root-child`, más `parentPageId` y `name`) y continúa igual que en 3-A.

---

## Paso 4 — confirmar el nombre (si procede)

El nombre ya se ha capturado en el artefacto salvo que el usuario eligiese "usar esta página"
(modo `existing`), en cuyo caso no se crea página nueva. Si hace falta, confírmalo en una línea.

---

## Paso 5 — confirmar y subir

**Previsualiza y confirma** (ver bloque de confirmación) y, con el "sí":

- `mode: "existing"` → **no crees home**; usa `parentPageId` como contenedor y cuelga de él el árbol de `docs/`.
- `mode: "child"` → crea la página `name` bajo `parentPageId` y cuelga de ella.
- `mode: "root-child"` → crea la página `name` en la raíz del espacio (sin `parentId`) y cuelga de ella.

Luego **sube el contenido** espejando `docs/` (Paso "publicar"). Al terminar, **guarda
`.claude/confluence.json`** con todo lo elegido (conexión, espacio, ubicación, modo, nombre)
usando `assets/confluence.example.json` como base: "Lo he recordado; la próxima vez será directo."

---

## Confirmación (SIEMPRE, antes de escribir)

Antes de crear/actualizar, enseña un resumen claro y humano y **espera un sí**:

> "Voy a hacer esto:
> • Espacio: **Ingeniería**
> • Ubicación: dentro de **Documentación de Proyectos**
> • Página principal: **Custom Agents**
> • Debajo colgaré 8 páginas (una por documento).
> ¿Lo publico? [Sí / Cambiar algo]"

Si dice "cambiar algo", vuelve a la pregunta correspondiente. No escribas hasta el "sí".

---

## Paso 3-bis — modo rápido (config ya existe)

Cuando ya hay `.claude/confluence.json`, no interrogues: **confirma en una línea** y publica.

> "Publico la doc en **Ingeniería › Documentación de Proyectos › Custom Agents** (como la última vez). ¿Actualizo? [Sí / Cambiar destino]"

Si dice "cambiar destino", reusa los pasos 2–3 del asistente (espacio / ubicación) y actualiza la config.

## Cierre (en lenguaje humano)

Resume sin tecnicismos y **da el enlace clicable** a la página principal:

> "Listo ✅ He publicado **Custom Agents** en el espacio **Ingeniería**, dentro de
> «Documentación de Proyectos». Creé 6 páginas y actualicé 2. Aquí lo tienes: <URL>."

Si algo se omitió o falló, dilo por página, en una frase, con el porqué y qué hacer.
