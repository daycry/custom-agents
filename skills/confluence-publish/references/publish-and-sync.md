# confluence-publish — publicar (idempotente), modo sincronización, dashboard, staging y manifiesto

> Referencia de la skill `confluence-publish`. Léela **solo** cuando el destino ya esté resuelto y vayas a escribir en Confluence («Publicar»), cuando te invoque otro agente sin interacción («Modo sincronización»), o cuando tengas que razonar sobre el manifiesto `.claude/confluence-state.json`, el dashboard del roadmap o la carpeta staged `docs/confluence/` (D5).

## Publicar (idempotente; por debajo)

Resuelto el destino, ejecuta sin más preguntas:

0. **Regenerar el staging (si `publish.staging: true`, D5) — ANTES de calcular nada.** Igual que el
   dashboard se regenera antes de publicar (ver más abajo), el staging se regenera antes de
   comparar con el manifiesto: es la política materializada en disco, y siempre tiene que reflejar
   el `docs/` de HOY.
   ```bash
   SCOPE="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/confluence-publish/scripts/confluence-scope.py' 2>/dev/null | head -1)"
   [ -n "$SCOPE" ] && python3 "$SCOPE" --stage --root "$PWD"
   ```
   Si el script falla o no se encuentra, **degrada sin bloquear**: usa `publish.source = "docs"` y
   resuelve `include`/`exclude` en línea, como antes de D5. Con el staging activo,
   `publish.source` (`docs/confluence`) es la raíz que recorre el paso 4 más abajo — el `.md`
   staged es idéntico byte a byte al canónico (no hay transformación de contenido), así que el
   único efecto de esta regeneración es garantizar que el árbol publicado es el alcance vigente.
1. **Espacio:** `getConfluenceSpaces` → `spaceId` desde el espacio elegido.
2. **Anclaje:** raíz → sin `parentId`; bajo una página → `parentId` de la elegida (valida con `getConfluencePageAncestors`). ⚠️ En API v2 `parentId` debe ser una **página** (no folder/database).
3. **Página principal del proyecto (idempotente):** si ya la conoces (guardada), verifícala; si no, búscala por su nombre en el espacio; si no existe, créala con `createConfluencePage` (`contentFormat: "markdown"`, `parentId` según el anclaje). Guarda su id como caché.
4. **Árbol de docs (`layout: "mirror-tree"`):** recorre `publish.source` respetando `include`/`exclude`. Cada subcarpeta → una página; cada `.md` → página hija de la de su carpeta; el cuerpo de la página-carpeta sale de su `README.md`/`index.md` si existe. Título = `# H1` del documento o el nombre del fichero. **Nunca espejes el marcador `_STAGING-LEEME.md`**: con staging activo este recorrido pasa por `docs/confluence/` (el árbol staged), no por `docs/` canónico, así que la autoexclusión por código de `confluence-scope.py` (que actúa sobre el ESCANEO del canónico al generar el staging) no cubre este segundo recorrido — el `exclude` de la config sí debe listarlo explícitamente (`**/_STAGING-LEEME.md`, ver `assets/confluence.example.json`) para que no se publique como página boilerplate ni quede huérfana en cada pull.
5. **Idempotencia (clave) — vía manifiesto de estado (sin git):** consulta el manifiesto `.claude/confluence-state.json` (ver sección "Estado de sincronización"). Con staging activo, los hashes se calculan sobre los ficheros **staged** (`docs/confluence/…`, que es lo que de verdad se publica), no sobre los canónicos — como son idénticos byte a byte, el hash coincide siempre entre ambos. Para cada `.md`:
   - Está en el manifiesto y el **hash coincide** → sin cambios, no toques nada.
   - Está en el manifiesto y el **hash difiere** → `updateConfluencePage` por su `pageId`.
   - No está en el manifiesto → `createConfluencePage` y registra `pageId` + hash.
   - Como respaldo (manifiesto ausente o `pageId` no válido), busca la página por título bajo su padre (`getConfluencePageDescendants`/búsqueda) antes de crear, para no duplicar.
   Al terminar, **actualiza el manifiesto** (hash + pageId de cada página) y limpia la marca de pendiente si existía. **Nunca dupliques.**
6. Muestra progreso ligero si son muchas ("Publicando… 5 de 8").

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

Detección de cambios: **compara `docs/` contra el manifiesto de estado** (ver sección "Estado
de sincronización"), no uses git ni fechas. Regla por tipo de cambio (idempotente):

- **Crear** (fichero nuevo, no en el manifiesto) → `createConfluencePage` en su sitio del árbol y registra `pageId` + hash.
- **Modificar** (hash distinto al del manifiesto) → `updateConfluencePage` por su `pageId`.
- **Sin cambios** (hash igual) → no toques nada.
- **Eliminar** (entrada en el manifiesto cuyo fichero ya no existe) → el conector Atlassian **no** expone borrado/archivado. Marca la página como obsoleta: `updateConfluencePage` anteponiendo un aviso (p. ej. un panel “⚠️ Documento eliminado del repositorio el <fecha>; pendiente de borrar”), **quítala del manifiesto** y **lístala al usuario** para que la borre a mano. No dejes contenido eliminado como si estuviera vigente.

Alcance: solo lo que ha cambiado según el manifiesto (no reespejes todo el árbol en cada
ejecución). No importa quién ni cómo editó los ficheros.

### Dashboard del roadmap (regenerar ANTES de publicar)

Para que el PM vea el **estado real** del roadmap en Confluence sin tocar git, el dashboard se
publica como una página más — pero **generada**, no escrita a mano. Antes de calcular los cambios
a publicar, **si en el conjunto pendiente hay algo bajo `docs/roadmap/`** (o existe la carpeta y ha
cambiado respecto al manifiesto), **regenera el markdown del dashboard** con la skill
`roadmap-dashboard`, de modo que la página refleje el último estado:

```bash
DASH="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/roadmap-dashboard/scripts/build_dashboard.py' 2>/dev/null | head -1)"
[ -d docs/roadmap ] && python3 "$DASH" --root docs/roadmap --md docs/roadmap/dashboard.md
```

Luego sigue el flujo normal: `docs/roadmap/dashboard.md` entra en el espejo como cualquier `.md`
(su hash cambiará y se publicará/actualizará su página). Notas:

- **Solo el `.md` va a Confluence.** El `dashboard.html` es vista local y, al no ser `.md`, el espejo lo ignora; no lo publiques.
- Así el disparo es determinista y honesto: la página se refresca **en la misma publicación** que provocó el cambio del roadmap, y su cabecera lleva la marca `generado <fecha/hora>` para que se vea la frescura. No es tiempo real: si nadie publica, el PM ve la última versión con su fecha.
- Si `docs/roadmap/` no existe, no generes nada.

**Exclusión obligatoria:** nunca publiques `docs/security-scan/**` (datos sensibles del agente
nemesis). Respeta también los `exclude` de la config.

### Staging (regenerar DESPUÉS del dashboard, ANTES de comparar — D5)

Con `publish.staging: true`, tras regenerar `dashboard.md` (si tocaba) pero **antes** de calcular
qué se crea/actualiza, regenera `docs/confluence/`:

```bash
SCOPE="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/confluence-publish/scripts/confluence-scope.py' 2>/dev/null | head -1)"
[ -n "$SCOPE" ] && python3 "$SCOPE" --stage --root "$PWD"
```

Así `dashboard.md` (si cambió) entra en el staging de esta misma pasada. Si el script falla o no
se encuentra, degrada a `publish.source = "docs"` sin bloquear la sincronización del agente que
llamó. Detalle completo del contrato de `docs/confluence/` en la sección "qué sube y qué no" más
abajo.

## Estado de sincronización — manifiesto `.claude/confluence-state.json` (sin git)

La detección de cambios **no depende de git** ni de fechas: se hace con un **manifiesto por
contenido** que mapea cada documento local con su página en Confluence y un hash de su contenido.
La skill lo mantiene; el usuario no lo toca.

```json
{
  "docs/README.md":                 { "hash": "9f2b…", "pageId": "1317535764" },
  "docs/architecture/overview.md":  { "hash": "0a4c…", "pageId": "1317540001" }
}
```

Uso en cada ejecución:

1. Recorre `docs/` (respetando `include`/`exclude` y la exclusión de `docs/security-scan/**`), calcula el hash de cada `.md` (p. ej. sha256 del contenido).
2. Compara con el manifiesto para clasificar cada fichero en crear / modificar / sin cambios, y detecta **eliminados** (entradas del manifiesto sin fichero en disco).
3. Publica solo lo que cambió (ver "Publicar" y "Modo sincronización").
4. **Actualiza el manifiesto** con los hashes y `pageId` resultantes. Si nada cambió, no se toca Confluence.

Ventajas: determinista, detecta creado/modificado/eliminado, idempotente, e independiente de
quién editó los ficheros (agente o chat) y de si hubo commit o no.

### Marca de "pendiente" (para el hook, opcional)
Si el plugin instala el hook `PostToolUse`, éste solo deja una **marca** `.claude/.confluence-pending`
cuando se edita algo bajo `docs/` (no publica). Al ejecutarse, la skill: si existe la marca o hay
diferencias con el manifiesto, sincroniza; y al acabar **borra la marca**. Así el hook es un mero
disparador determinista y todo el trabajo real (con el conector) lo hace la skill.
