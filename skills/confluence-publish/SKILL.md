---
name: confluence-publish
description: >
  Publica la documentación de un proyecto en Confluence Cloud con un ASISTENTE
  GUIADO pensado para personas NO técnicas, reutilizando el conector oficial de
  Atlassian (Rovo MCP) — no reimplementa la integración. Acompaña al usuario paso
  a paso: elige el espacio y el punto de anclaje (raíz del espacio o bajo una
  página existente) mostrando nombres y árbol reales (nunca IDs), previsualiza qué
  se va a publicar, pide confirmación antes de tocar nada y espeja el árbol de
  docs/ de forma idempotente (crea o actualiza, sin duplicar). Guarda las
  preferencias en .claude/confluence.json para que la próxima vez sea de un clic.
  Úsala cuando el usuario diga "publica en Confluence", "sube la doc a Confluence",
  "sincroniza con Confluence", "crea el espacio/árbol del proyecto en Confluence".
user-invokable: true
---

# confluence-publish — publicar en Confluence con asistente guiado

Espeja la documentación local de un proyecto (`docs/…`) como un árbol de páginas en
**Confluence Cloud**, usando el **conector oficial de Atlassian (Rovo MCP)**. No hay motor
propio ni instalación: las operaciones usan las herramientas del conector.

**Esta skill la usarán personas NO técnicas.** El objetivo es que nadie tenga que conocer
IDs, claves de espacio ni editar ficheros. Tú (el agente) haces de asistente: preguntas
en lenguaje natural, ofreces opciones por su **nombre**, previsualizas y **confirmas antes
de escribir nada**. Los tecnicismos (cloudId, spaceId, parentId, pageId) se resuelven y se
guardan **por debajo**, sin exponerlos.

## Principios de interacción (obligatorios)

- **Una pregunta a la vez**, en lenguaje llano. Nunca sueltes un cuestionario largo.
- **Opciones numeradas por nombre.** Muestra "1) Marketing  2) Ingeniería  3) …", no claves ni UUIDs.
- **Nada de jerga.** Di "dónde quieres que aparezca", no "introduce el parentId". Evita cloudId/spaceKey/pageId en lo que ve el usuario.
- **Valores por defecto sensatos** y recomendados: propón la opción más común y deja cambiarla ("Por defecto lo pongo como página nueva dentro de 'Proyectos'. ¿Te vale? [Sí / elegir otro sitio]").
- **Previsualiza y confirma** antes de crear/actualizar: enseña un resumen de qué páginas se crearán y dónde, y espera un "sí" explícito.
- **Sin callejones sin salida:** si algo falla (sin conexión, sin permisos), explícalo en una frase clara y di el siguiente paso, sin volcar errores técnicos crudos.
- **Recuerda las decisiones:** guarda todo en `.claude/confluence.json` para que la próxima vez no haya que preguntar (solo confirmar).

## Requisitos

- **Conector Atlassian (Rovo MCP) conectado** en Claude (Jira & Confluence). Si no lo está,
  díselo al usuario con naturalidad ("Necesito permiso para conectarme a vuestro Confluence;
  actívalo en los conectores y volvemos") y **detente**; no intentes otra vía.
- Permiso de escritura del usuario en el espacio de destino.
- Herramientas del conector (por su función; el prefijo `mcp__…__` puede variar):
  `getAccessibleAtlassianResources`, `getConfluenceSpaces`, `getPagesInConfluenceSpace`,
  `getConfluencePage`, `getConfluencePageAncestors`, `getConfluencePageDescendants`,
  `createConfluencePage`, `updateConfluencePage` y la búsqueda (CQL) si está disponible.

## Paso 0 — opt-in (¿sincronizar con Confluence?) — SIEMPRE primero

La sincronización con Confluence es **opcional** y se decide **una vez por proyecto**. Antes de
nada, localiza la config y mira el flag `enabled` de `.claude/confluence.json`:

```bash
CFG="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*confluence.json' 2>/dev/null | head -1)"
```

- **`enabled: true`** → sincronización activada; sigue el flujo normal (conexión → espacio → árbol → subir).
- **`enabled: false`** → el usuario dijo que NO. **No hagas nada** y **no vuelvas a preguntar**.
- **No hay config** (primera vez) → **pregunta una sola vez**:
  > "¿Quieres sincronizar la documentación de este proyecto con Confluence? [Sí / No]"
  - **Sí** → crea `.claude/confluence.json` con `"enabled": true` y continúa con la conexión (Paso 1) y el asistente (espacio → árbol → subir), tal como está descrito.
  - **No** → crea `.claude/confluence.json` con `"enabled": false` (para no volver a preguntar) y termina sin sincronizar.

Este opt-in aplica igual cuando la skill se invoca a mano y cuando la llaman otros agentes
(modo sincronización): si `enabled` es `false` o el usuario dice que no, no se sincroniza nada.

## Cómo funciona por dentro (una sola idea)

Al crear una página, **si se pasa `parentId` es hija de ese nodo; si se omite, va a la raíz
del espacio.** Todo el "dónde aparece" se reduce a eso. El usuario nunca ve `parentId`: elige
un sitio por su nombre y tú traduces.

## El flujo, de un vistazo

El asistente encadena estos pasos, cada uno alimenta al siguiente:

1. **Conectar con Confluence** (interactivo) → 2. **Buscar y elegir espacio** → 3. **Ver el árbol del espacio y elegir dónde** → 4. **Nombrar la página del proyecto** → 5. **Confirmar y subir el contenido**.

Si el proyecto ya se configuró antes (`.claude/confluence.json`), se salta directo a una confirmación de una línea (**Modo rápido**, Paso 3-bis).

---

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

---

## Publicar (idempotente; por debajo)

Resuelto el destino, ejecuta sin más preguntas:

1. **Espacio:** `getConfluenceSpaces` → `spaceId` desde el espacio elegido.
2. **Anclaje:** raíz → sin `parentId`; bajo una página → `parentId` de la elegida (valida con `getConfluencePageAncestors`). ⚠️ En API v2 `parentId` debe ser una **página** (no folder/database).
3. **Página principal del proyecto (idempotente):** si ya la conoces (guardada), verifícala; si no, búscala por su nombre en el espacio; si no existe, créala con `createConfluencePage` (`contentFormat: "markdown"`, `parentId` según el anclaje). Guarda su id como caché.
4. **Árbol de docs (`layout: "mirror-tree"`):** recorre `publish.source` respetando `include`/`exclude`. Cada subcarpeta → una página; cada `.md` → página hija de la de su carpeta; el cuerpo de la página-carpeta sale de su `README.md`/`index.md` si existe. Título = `# H1` del documento o el nombre del fichero.
5. **Idempotencia (clave):** antes de crear, comprueba si ya existe una página con ese título bajo ese padre (`getConfluencePageDescendants`/búsqueda). Existe → `updateConfluencePage` (o respeta `onConflict: "skip"`); no existe → `createConfluencePage`. **Nunca dupliques.**
6. Muestra progreso ligero si son muchas ("Publicando… 5 de 8").

---

## Cierre (en lenguaje humano)

Resume sin tecnicismos y **da el enlace clicable** a la página principal:

> "Listo ✅ He publicado **Custom Agents** en el espacio **Ingeniería**, dentro de
> «Documentación de Proyectos». Creé 6 páginas y actualicé 2. Aquí lo tienes: <URL>."

Si algo se omitió o falló, dilo por página, en una frase, con el porqué y qué hacer.

---

## Modo sincronización (invocada por otros agentes, sin interacción)

Cuando **otro agente** (planner, evaluator, qa…) crea, modifica o elimina ficheros en
`docs/`, invoca esta skill para **reflejar el cambio en Confluence**. Primero aplica el opt-in
(Paso 0):

- **`enabled: true`** → sincroniza en silencio (sin asistente).
- **`enabled: false`** → no hagas nada.
- **Sin config (primera vez)** → pregunta una sola vez si se quiere sincronizar con Confluence
  (Paso 0). Si dice que sí, ejecuta el alta (conexión + espacio + árbol) y luego sincroniza; si
  dice que no, guarda `enabled: false` y no vuelvas a preguntar. No bloquees el trabajo del
  agente por esto.

Regla por tipo de cambio (idempotente, comparando por título bajo el padre correcto):

- **Crear** un `.md` → `createConfluencePage` en su sitio del árbol (según `.claude/confluence.json`).
- **Modificar** un `.md` → localiza la página equivalente y `updateConfluencePage` con el nuevo contenido.
- **Eliminar** un `.md` → el conector Atlassian **no** expone borrado/archivado de páginas. Por tanto, marca la página como obsoleta: `updateConfluencePage` anteponiendo un aviso (p. ej. un panel “⚠️ Documento eliminado del repositorio el <fecha>; pendiente de borrar”) y **lístala al usuario** para que la borre a mano. No dejes contenido eliminado como si estuviera vigente.

Alcance de la sincronización: solo lo que el agente acaba de tocar (no reespejes todo el árbol
en cada cambio). Idealmente el agente pasa la lista de rutas afectadas; si no, usa el estado de
git (`git status --porcelain docs/`) para saber qué cambió.

**Exclusión obligatoria:** nunca publiques `docs/security-scan/**` (datos sensibles del agente
nemesis, gitignored). Respeta también los `exclude` de la config.

## Config `.claude/confluence.json` (gestión interna, no la pide el usuario)

La escribe/actualiza la skill; el usuario no la edita a mano. Formato en
`assets/confluence.example.json`. Campos: `cloudId`, `spaceKey`, `anchor` (`mode`
root/child + `parentPageId`/`parentTitle`), `home` (`title` + `pageId` de caché) y `publish`
(`source`, `layout`, `include`, `exclude`, `onConflict`). Si falta `cloudId`, resuélvelo con
`getAccessibleAtlassianResources` (uno solo → úsalo; varios → pregunta por nombre) y persístelo.

## Reglas

- **Guiado y humano:** una pregunta a la vez, opciones por nombre, sin jerga, con defaults recomendados.
- **Confirma antes de escribir:** siempre previsualiza destino + nº de páginas y espera el "sí".
- **No reimplementes la API:** todo por el conector Atlassian. Si no está conectado, detente y pide conectarlo (en llano).
- **Idempotente siempre:** buscar → actualizar o crear; reejecutar no duplica.
- **La config es memoria, no un requisito del usuario:** se rellena sola la primera vez y luego solo se confirma.
- **`parentId` = ubicación** (oculto al usuario): presente → hija; ausente → raíz. Debe apuntar a una página.
- **Un proyecto → una página principal.** Todo cuelga de ella; usa el id guardado como caché para no duplicarla.
- **Errores en llano:** sin conexión / sin permiso / página fallida → una frase clara y el siguiente paso, no un volcado técnico.
