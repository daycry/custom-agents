---
spec: confluence-policy
descripcion: Política explícita de qué documentación de docs/ se publica en Confluence y qué no, y cierre de los huecos del circuito publish/pull.
estado: implementada     # borrador | aprobada | implementada | obsoleta
creado: 2026-08-20
actualizado: 2026-08-20
evaluacion: evaluation.md
plan: improvement-plan.md
generacion:               # usage-meter.py NO disponible en este entorno (sandbox cloud, sin transcripción local)
  inicio: 2026-08-20T07:28:00Z
  fin: 2026-08-20T07:33:00Z
  fuente: estimado        # degradación declarada: no hay medición de tokens
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# Política de publicación en Confluence

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md)

> **Terminología:**
> · **Mirror / espejo** — el conjunto de ficheros de `docs/` que `confluence-publish` refleja como páginas, definido por `publish.include`/`publish.exclude` de `.claude/confluence.json`.
> · **Manifiesto** — `.claude/confluence-state.json`: mapa `ruta → { hash, pageId }` que decide qué se crea/actualiza. No depende de git.
> · **Disparador** — agente o comando que, al terminar, invoca `confluence-publish` aplicando el fragmento `agent-kits/shared/confluence-optin.md`.
> · **Arrastre** — efecto de que, cuando cualquier disparador publica, la comparación contra el manifiesto sube **todo** lo que haya cambiado bajo `docs/`, no solo el artefacto del disparador.

## Contexto y objetivo

El plugin ya tiene el circuito `docs/ ↔ Confluence` completo en mecánica (skills `confluence-publish` y `confluence-pull`, opt-in compartido, manifiesto por hashes, hook `mark-docs-pending.sh`), pero **no tiene política**: nadie ha decidido explícitamente *qué* documentación es apta para un espacio de Confluence y qué debe quedarse en el repo. Hoy el alcance lo fija un `include: ["**/*.md"]` por defecto y dos exclusiones (`node_modules`, `docs/security-scan/**`).

El análisis previo sobre el repo (2026-08-20, resumido en **Referencias**) identificó cinco huecos concretos:

1. **Sobre-publicación por defecto.** Con `**/*.md`, un espejo de este repo subiría `docs/en/` (árbol EN duplicado), `docs/examples/`, `docs/agents/` (documentación interna de agentes), `atlassian-connector-notes.md` y las 11 iniciativas completas del roadmap (evaluaciones de 20-30 KB). No hay defaults documentados ni presets por audiencia.
2. **Disparadores que faltan.** Aplican el opt-in: `analyst`, `evaluator`, `planner`, `qa`, `documenter`, `/pm-backlog`. **No** lo aplican: `implementer` (actualiza `tasks.md`, el ledger canónico, en cada tarea), `/retro` (`retro.md` + `CALIBRATION.md`), `/spec-drift` (`DRIFT.md`), `/roadmap-brief` (`brief.md`) y `jira-sync` (escribe claves Jira en `tasks.md`). Los tres primeros son de **fin de ciclo**: nadie publica después, así que el arrastre nunca los recoge y en Confluence no existen; el ledger queda congelado entre publicaciones.
3. **Evidencias binarias.** El filtro `**/*.md` deja fuera `report.pdf`, `screenshots/` y `raw/` de `qa`, y `brief.pdf`. Como el `report.md` de qa **embebe capturas**, su página en Confluence sale con **imágenes rotas**. El conector Rovo MCP no expone subida de adjuntos (solo `createConfluencePage`/`updateConfluencePage`), así que "subir las capturas" no es viable con el conector actual.
4. **Asimetría publish/pull.** `confluence-pull` reutiliza `confluence.json` y el manifiesto, pero no está decidido si respeta los mismos `include`/`exclude` ni qué pasa si una página publicada fue transformada al subirla.
5. **Circuito nunca ejercitado.** No existen `.claude/confluence.json` ni `.claude/confluence-state.json` en el proyecto: el flujo publish/pull **nunca se ha ejecutado end-to-end**. La política se define antes del primer `enabled: true`, que es justo cuando el coste de equivocarse (volcar doc interna a un espacio compartido) es mayor.

**Objetivo:** dejar escrita, aplicada y documentada una política de publicación — qué sube, qué no y quién dispara — de modo que activar Confluence por primera vez en cualquier proyecto consumidor produzca un espejo **útil para su audiencia** y **sin sorpresas**.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Dónde vive la política | En `skills/confluence-publish/SKILL.md` (normativa) + `assets/confluence.example.json` (defaults ejecutables) | Fuente única: la skill ya es la dueña del alcance; duplicarla en cada agente rompería la regla de compartido vs privado |
| Forma de la política | Lista de `exclude` por defecto (opt-out) sobre `include: ["**/*.md"]` | Menos frágil que un allow-list: un doc nuevo se publica salvo que caiga en una exclusión conocida; evita que se olvide añadir cada carpeta nueva |
| Exclusiones no negociables | `docs/security-scan/**` (invariante nemesis) y `dashboard.html` (solo-local; el `.md` se regenera antes de publicar) | Ya existen y funcionan: se mantienen tal cual |
| Qué entra del roadmap | **D1 — confirmada: selección curada.** Por iniciativa suben `spec.md`, `evaluation.md` y `retro.md`; **no** suben `improvement-plan.md`, `tasks.md` ni `test-plan.md`. Los ficheros de cartera (`dashboard.md`, `BACKLOG.md`, `brief.md`, `DRIFT.md`, `CALIBRATION.md`) sí | Confluence es la vista de **decisión y resultado**, no el tablero de ejecución: plan y ledger viven en el repo (y en Jira cuando está activo). Evita volcar 11 iniciativas completas |
| Presets por audiencia | **D2 — confirmada: descartados.** Un único default sensato; la copia 1:1 sigue siendo posible editando `include`/`exclude` a mano, pero no es opción de primera clase | Menos superficie de config y de documentación; sin audiencia confirmada, un preset sería especulación cara de mantener |
| Disparadores de fin de ciclo | `/retro`, `/spec-drift` y `/roadmap-brief` aplican el fragmento `confluence-optin.md` como el resto de la cadena | Es el mismo paso compartido, ya escrito; el coste es una línea por comando y cierra el hueco del arrastre |
| Ledger (`tasks.md`) durante la implementación | **D3 — confirmada: `implementer` aplica el paso opt-in al cerrar cada fase** (no tarea a tarea, no solo al final) | Punto medio entre ruido y congelación: una publicación por fase. Ojo a la interacción con D1 (ver nota bajo la tabla) |
| Evidencias de qa | **D4 — confirmada: `**/testing/**` NO se publica** (exclusión en el mirror). Se descarta transformar el `report.md` publicado | Elimina de raíz las imágenes rotas y el riesgo de divergencia local↔remoto que afectaba a `confluence-pull`; el informe completo (md + pdf + capturas) sigue disponible en el repo |
| Determinismo de la política | **D5 — confirmada: entra.** Script `confluence-scope.py` con tests y exit codes y **dos funciones**: `--status` (informe humano: qué entra en el alcance, qué está sincronizado, qué está desactualizado/pendiente y qué queda excluido, cruzando política + `confluence-state.json`) y `--stage` (regenera `docs/confluence/`) | La regla de determinismo del repo pide cálculos y veredictos en scripts, no en prosa; y es la única forma de validar la política sin un espacio real, dado que el circuito nunca se ha ejercitado |
| Visibilidad de "qué sube" | **D5 — confirmada: carpeta `docs/confluence/` GENERADA** por `--stage` desde la política: copia exacta de lo que se publica. **Nadie la edita a mano.** Con el staging activo, `publish.source` apunta a `docs/confluence/` | El usuario quería ver a simple vista qué sube. Mantenerla **a mano** se descartó: sería una segunda fuente de verdad y derivaría del original. Generada da la misma visibilidad sin duplicar la verdad — mismo patrón que `dashboard.md` (derivado, regenerado antes de publicar) |
| Dónde escriben los agentes | **Sin cambio**: todo (ADRs, arquitectura, gotchas, roadmap) se sigue escribiendo en su sitio **canónico** de `docs/`. `docs/confluence/` es **salida, nunca entrada** | El staging no altera la taxonomía de la documentación ni añade decisiones al escribir: solo materializa la política |
| Documentación | Sección "qué sube y qué no" en la doc de la skill + espejo EN + matriz disparador→artefacto en `docs/FLOWS.md` | Regla bilingüe del repo: al cambiar un doc clave se actualiza su espejo en el mismo cambio |

> **Interacción D1 ↔ D3 (leer antes de implementar).** D1 deja `tasks.md` **fuera** del espejo por defecto y D3 hace que `implementer` **dispare** la publicación al cerrar cada fase. No es contradictorio si se separan los dos ejes: **D1 manda sobre el contenido** (qué páginas existen) y **D3 sobre el momento** (cuándo se refresca el espejo). Efecto real con la política por defecto: al cerrar fase el ledger **no** sube; lo que se refresca es el resto de lo que haya cambiado dentro del alcance (típicamente `dashboard.md`, y `spec.md`/`evaluation.md` si se tocaron). Un proyecto que quiera el ledger visible debe añadir `tasks.md` al `include` a mano (D2: no es opción de primera clase). Esto se documenta explícitamente en C-04 para que nadie espere ver el ledger en Confluence.

## Configuración / parámetros

Defaults **aprobados** para `publish` en `.claude/confluence.json` (plantilla: `skills/confluence-publish/assets/confluence.example.json`). Los valores actuales están verificados contra el fichero del repo.

| Parámetro | Clave / mecanismo | Default actual | Valor objetivo (aprobado) |
|---|---|---|---|
| Origen | `publish.source` | `docs` | **`docs/confluence`** cuando el staging está activo (D5); `docs` si se desactiva |
| Staging generado | `publish.staging` *(nuevo)* | — | **`true`** — `--stage` regenera `docs/confluence/` antes de comparar con el manifiesto |
| Layout | `publish.layout` | `mirror-tree` | **`mirror-tree`** (sin cambio) |
| Incluidos | `publish.include` | `["**/*.md"]` | **`["**/*.md"]`** (sin cambio; la política se expresa en `exclude`) |
| Excluidos | `publish.exclude` | `["**/node_modules/**", "docs/security-scan/**"]` | **`["**/node_modules/**", "docs/security-scan/**", "docs/en/**", "docs/examples/**", "docs/agents/**", "docs/**/atlassian-connector-notes.md", "docs/roadmap/**/improvement-plan.md", "docs/roadmap/**/tasks.md", "docs/roadmap/**/test-plan.md", "**/testing/**"]`** |
| Conflictos | `publish.onConflict` | `update` | **`update`** (sin cambio) |
| Preset de audiencia | — | — | **No se implementa** (D2) |

**Por qué cada exclusión:**

- `docs/en/**` — duplicaría todo el árbol en Confluence (la traducción es para lectores de GitHub, no del espacio).
- `docs/examples/**` y `docs/agents/**` — documentación interna del plugin (cómo se construyen los agentes), no del producto del consumidor.
- `docs/**/atlassian-connector-notes.md` — notas de trabajo sobre el propio conector.
- `improvement-plan.md`, `tasks.md`, `test-plan.md` (D1) — tablero de **ejecución**: su sitio es el repo y Jira. Confluence guarda la decisión (`spec.md`), su presupuesto (`evaluation.md`) y su resultado (`retro.md`).
- `**/testing/**` (D4) — evita las imágenes rotas del `report.md` (capturas embebidas que el conector no puede adjuntar) y la divergencia local↔remoto.
- `docs/security-scan/**` y `node_modules` — ya existentes; invariante de nemesis el primero.

**Qué sí sube con estos defaults:** `docs/*.md` de nivel general, `docs/roadmap/README.md`, `dashboard.md`, `BACKLOG.md`, `brief.md`, `DRIFT.md`, `CALIBRATION.md` y, por iniciativa, `spec.md` + `evaluation.md` + `retro.md`. Con el staging activo (D5) eso es **exactamente** el contenido de `docs/confluence/`: la carpeta *es* la respuesta a "qué sube", sin tener que interpretar globs.

**`docs/confluence/` — reglas de la carpeta generada (D5):**

- **Derivada, no editable.** Se regenera por completo en cada `--stage`; cualquier edición manual se pierde. Lleva un fichero de aviso generado con el "no editar" y el comando que la produce. *(Enmienda al cierre 2026-08-20: el aviso vive en `_STAGING-LEEME.md` — nombre reservado, excluido del espejo y del mapeo — y **sin fecha embebida**; un `README.md` generado colisionaba con la copia byte a byte del `docs/README.md` canónico y la fecha rompía la idempotencia entre días. La frescura la dan el manifiesto y `dashboard.md`.)*
- **Se excluye de sí misma.** `docs/confluence/**` entra en `exclude` para que un `--stage` no se anide dentro del anterior, y el hook no la trata como edición de documentación de usuario.
- **El manifiesto y el hook operan sobre el staging cuando está activo**: los hashes se calculan sobre los ficheros staged (que es lo que de verdad se publica), no sobre los canónicos.
- **`confluence-pull` mapea al fichero CANÓNICO.** Un cambio bajado de Confluence se escribe en su ruta original de `docs/`, **nunca** en la copia staged (que se regeneraría y perdería el cambio). El script debe exponer el mapeo inverso `staged → canónico` para que el pull lo use.

## Arquitectura y componentes

| Pieza | Ruta | Cambio |
|---|---|---|
| Skill de publicación | `skills/confluence-publish/SKILL.md` | **Modificar**: nueva sección normativa "qué sube y qué no" + regla de evidencias binarias |
| Config de ejemplo | `skills/confluence-publish/assets/confluence.example.json` | **Modificar**: `exclude` por defecto aprobado (sin `preset`, D2) |
| Skill de bajada | `skills/confluence-pull/SKILL.md` | **Modificar**: respeta los mismos `include`/`exclude` y, con staging activo, **escribe en el fichero canónico** usando el mapeo inverso del script (nunca en `docs/confluence/`) |
| Fragmento opt-in | `agent-kits/shared/confluence-optin.md` | **Sin cambio** (es el paso; la política vive en la skill) |
| Comandos de fin de ciclo | `commands/retro.md`, `commands/spec-drift.md`, `commands/roadmap-brief.md` | **Modificar**: añadir el paso `confluence-optin.md` al cierre |
| Implementer | `agents/implementer.md` | **Modificar**: aplicar el paso opt-in **al cerrar cada fase** (D3), con la nota de que el ledger no está en el espejo por defecto |
| QA | `agents/qa.md` | **Modificar** (menor): el informe queda **solo-local** (D4); el paso opt-in de P7 deja de apuntar a `testing/` |
| Verificador + staging | `skills/confluence-publish/scripts/confluence-scope.py` + tests en `tests/` | **Nuevo** (D5 aprobada): `--status` (informe alcance/sincronizado/desactualizado/excluido) y `--stage` (regenera `docs/confluence/`), con exit codes y `--check` de invariantes |
| Carpeta staged | `docs/confluence/` (+ su `README.md` de aviso) | **Nueva, GENERADA** — derivada de la política; no se edita a mano ni se versiona como fuente |
| Hook | `hooks/mark-docs-pending.sh` | **Modificar** (menor): ignorar `docs/confluence/**` para que regenerar el staging no marque "pendiente" en bucle |
| Documentación | `docs/FLOWS.md`, `docs/README.md` y sus espejos en `docs/en/` | **Modificar**: matriz disparador→artefacto, resumen de la política y el contrato de `docs/confluence/` (generada, no editable) |

Reutiliza sin tocar: el manifiesto por hashes (aplicado sobre el staging cuando está activo), el opt-in y la regeneración del dashboard previa a publicar.

## Flujo (paso a paso)

1. Un agente o comando termina de escribir bajo `docs/` y aplica el fragmento `confluence-optin.md`.
2. `confluence-publish` resuelve el opt-in (`enabled`, o pregunta una vez).
3. **[nuevo]** Resuelve el alcance con la política: `include` ∩ ¬`exclude`, con `docs/security-scan/**` y `**/testing/**` excluidos siempre por defecto.
4. Si hay cambios bajo `docs/roadmap/`, regenera `dashboard.md` (ya existente).
5. **[nuevo, D5]** Regenera el staging: `confluence-scope.py --stage` reescribe `docs/confluence/` con la copia exacta de lo que va a subir (+ su `README.md` de aviso). A partir de aquí la skill trabaja sobre `publish.source = docs/confluence`.
5-bis. **[nuevo]** No hay transformación de contenido: el markdown staged es idéntico al canónico (D4 elimina el único caso que pedía transformar). Publicado ≡ staged ≡ canónico.
6. Compara con el manifiesto → crear / actualizar / sin cambios / eliminado-obsoleto.
7. Actualiza el manifiesto y borra la marca `.confluence-pending`.
8. **[nuevo]** En el sentido inverso, `confluence-pull` filtra el conjunto remoto con la misma política y, con staging activo, traduce cada página a su **fichero canónico** de `docs/` (mapeo inverso del script) antes de escribir. Nunca escribe en `docs/confluence/`.

## Alcance

- **Dentro (esta iteración):**
  - Defaults `include`/`exclude` documentados y aplicados en la plantilla de config.
  - Cierre de los huecos de disparador de **fin de ciclo** (`/retro`, `/spec-drift`, `/roadmap-brief`).
  - Aplicación de la política del **ledger** en `implementer` (D3: al cerrar fase).
  - Aplicación de la política de **evidencias binarias** de `qa` (D4: `**/testing/**` fuera del espejo).
  - **Verificador + staging** (D5): `confluence-scope.py --status` / `--stage` / `--check` con tests, la carpeta generada `docs/confluence/` y su contrato de no-edición.
  - Mapeo inverso staged → canónico para `confluence-pull`, y hook/manifiesto operando sobre el staging.
  - Sección "qué sube y qué no" en la doc de la skill + espejo EN + matriz en `docs/FLOWS.md`.
  - Declaración de simetría con `confluence-pull`.
- **Fuera (siguientes specs):**
  - Subida de adjuntos/imágenes a Confluence (el conector no la expone; requeriría API directa, que choca con la regla "no reimplementes la API").
  - Permisos y restricciones por página en Confluence.
  - Migración o limpieza de espacios ya publicados con la política antigua.
  - Publicación desde `jira-sync` (sus escrituras en `tasks.md` quedan cubiertas por la decisión de ledger).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| No existe `.claude/confluence.json` | La skill pregunta una vez (opt-in). La política solo se materializa si se dice que sí; nunca bloquea al agente |
| `enabled: false` | Ningún disparador publica, incluidos los nuevos de fin de ciclo. Sin aviso repetido |
| Config antigua sin los nuevos `exclude` | La skill avisa una vez de la diferencia y ofrece actualizar; **no** reescribe la config sin confirmación (es memoria del proyecto) |
| Fichero excluido que ya tenía página en Confluence | Se trata como "eliminado del espejo": aviso al usuario + marca de obsoleto, nunca borrado silencioso (regla ya existente del conector) |
| Alguien espera ver el informe de QA en Confluence | No está: `**/testing/**` queda fuera por decisión (D4). La doc de la skill y la matriz de FLOWS lo dicen explícitamente para que la ausencia sea una decisión visible, no un fallo aparente |
| Alguien espera ver el ledger `tasks.md` en Confluence | No está (D1). El disparo por fase de `implementer` (D3) refresca el resto del alcance; para publicarlo hay que añadirlo al `include` a mano |
| Alguien edita a mano un fichero de `docs/confluence/` | El cambio se **pierde** en el siguiente `--stage`. El `README.md` generado de la carpeta lo advierte y `--status` señala la divergencia respecto al canónico antes de regenerar |
| `--stage` no se ha ejecutado desde el último cambio en `docs/` | `--status` lo marca como **desactualizado** y la skill regenera antes de comparar con el manifiesto; nunca publica un staging obsoleto |
| `confluence-pull` trae un cambio de una página staged | Se escribe en el fichero **canónico** vía el mapeo inverso; si el mapeo no resuelve (página huérfana), se avisa y no se escribe nada |
| El script `confluence-scope.py` falla o no está | Degradación con aviso: la skill vuelve a `publish.source = docs` y a resolver la política en línea; no bloquea el ciclo del agente |
| Conector Atlassian no conectado | Error en llano y siguiente paso; el ciclo del agente continúa (degradación, no bloqueo) |

## Criterios de aceptación

- [ ] CA-01 — `skills/confluence-publish/assets/confluence.example.json` incluye los `exclude` por defecto aprobados y un comentario que explica cada uno.
- [ ] CA-02 — `skills/confluence-publish/SKILL.md` tiene una sección normativa "qué sube y qué no" con la tabla de exclusiones y su motivo, incluida la exclusión de `**/testing/**` y la de plan/ledger.
- [ ] CA-03 — `commands/retro.md`, `commands/spec-drift.md` y `commands/roadmap-brief.md` aplican el paso `confluence-optin.md` en su cierre, con el mismo texto de degradación que el resto de la cadena.
- [ ] CA-04 — `agents/implementer.md` declara que aplica el paso opt-in **al cerrar cada fase** (y que el ledger no está en el espejo por defecto), y `agents/qa.md` declara que el informe de `testing/` es **solo-local**.
- [ ] CA-05 — `docs/FLOWS.md` contiene una matriz disparador→artefacto→¿se publica? que cubre los 10 disparadores conocidos y deja explícitos los "no" (plan, `tasks.md`, `testing/**`, `docs/en/`, `examples/`, `agents/`), y su espejo `docs/en/FLOWS.md` está actualizado en el mismo cambio.
- [ ] CA-06 — Ningún cambio introduce publicación de `docs/security-scan/**` (invariante verificable por inspección del `exclude` y del texto de la skill).
- [ ] [GWT] CA-07 — Dado este repositorio con la política por defecto, Cuando ejecuto `confluence-scope.py --status`, Entonces la salida clasifica cada documento en **en alcance / sincronizado / desactualizado o pendiente / excluido** (cruzando la política con `confluence-state.json`), lista `docs/en/**`, `docs/examples/**`, `docs/agents/**`, `**/testing/**` y `docs/security-scan/**` entre los excluidos, no lista ningún fichero fuera de `docs/`, y el proceso termina con código 0.
- [ ] [GWT] CA-08 — Dado un `confluence.json` cuyo `exclude` omite `docs/security-scan/**`, Cuando ejecuto `confluence-scope.py --check`, Entonces el proceso falla con código distinto de 0 y un mensaje que nombra la invariante violada.
- [ ] [GWT] CA-10 — Dado un repositorio con la política por defecto y sin `docs/confluence/`, Cuando ejecuto `confluence-scope.py --stage`, Entonces se crea `docs/confluence/` con **exactamente** los ficheros en alcance (mismo contenido byte a byte que sus canónicos) más un fichero de aviso `_STAGING-LEEME.md` con el "no editar" *(enmendado al cierre 2026-08-20: antes decía «un `README.md` … y la fecha»; el README colisionaba con el canónico en alcance y la fecha rompía la idempotencia entre días — ver §reglas de la carpeta generada)*; y Cuando lo ejecuto por segunda vez sin cambios, Entonces el resultado es idéntico (idempotente) y ningún fichero excluido aparece dentro.
- [ ] [GWT] CA-11 — Dado un staging activo y una página modificada en Confluence, Cuando `confluence-pull` resuelve su destino con el mapeo inverso del script, Entonces la ruta de escritura es el fichero **canónico** de `docs/` y nunca una ruta bajo `docs/confluence/`.
- [ ] CA-12 — `hooks/mark-docs-pending.sh` ignora `docs/confluence/**` (regenerar el staging no deja marca de pendiente), verificado con un caso de prueba del hook.
- [ ] CA-09 — `python scripts/lint_plugin.py` y las suites de `tests/` en verde tras los cambios.

## Pruebas

- **Inspección documental** (CA-01 a CA-06): revisión por criterio contra el fichero afectado; no requiere Confluence.
- **Tests unitarios** (CA-07, CA-08, CA-10, CA-11, CA-12): suite en `tests/` sobre `confluence-scope.py` con fixtures de árbol de `docs/`, un `confluence-state.json` de ejemplo y configs válidas/inválidas; cubre las tres funciones (`--status`, `--stage`, `--check`), la idempotencia del staging y el mapeo inverso. Sin red, sin conector.
- **Linter del plugin** (CA-09): `scripts/lint_plugin.py` + suites existentes.
- **Prueba end-to-end contra Confluence: fuera de alcance automatizado.** El circuito nunca se ha ejercitado y no hay espacio de pruebas; si el usuario dispone de uno, se recomienda un primer `enabled: true` contra un espacio sandbox y comparar el árbol resultante con la salida del dry-run.

## Referencias

- `skills/confluence-publish/SKILL.md` — §"Modo sincronización" (líneas 232-255), §"Estado de sincronización" (279-307), §"Config" (308-315), §"Reglas" (316-325).
- `skills/confluence-publish/assets/confluence.example.json` — bloque `publish` (`source`, `include`, `exclude`, `onConflict`).
- `skills/confluence-pull/SKILL.md` — §"Paso 1 — construir el conjunto remoto", §"Relación con confluence-publish".
- `agent-kits/shared/confluence-optin.md` — texto único del paso opt-in.
- `hooks/mark-docs-pending.sh` — marca `.confluence-pending` para cualquier edición bajo `docs/` salvo `security-scan`.
- `agents/qa.md` L26 (salida `testing/` con `report.pdf`, `screenshots/`, `raw/`), L73 (capturas embebidas en `report.md`), L77 (paso opt-in).
- `agents/implementer.md` L41-43 (ledger canónico `tasks.md`), L79 (no toca `docs/roadmap/` salvo `tasks.md`) — sin paso Confluence.
- `commands/retro.md` (escribe `retro.md` + `CALIBRATION.md`), `commands/spec-drift.md` L32/L44 (`DRIFT.md`), `commands/roadmap-brief.md` L20/L26 (`brief.md` + `brief.pdf`) — ninguno aplica el opt-in.
- `docs/README.md` L39 — descripción vigente del circuito bidireccional (a actualizar con la política).
- Análisis previo del circuito, 2026-08-20 (aportado con el encargo; verificado contra los ficheros anteriores).

## Decisiones confirmadas (revisión del usuario · 2026-08-20)

1. **D1 — Alcance por defecto = selección curada.** Documentación general + ficheros de cartera + `spec.md`/`evaluation.md`/`retro.md` por iniciativa. Fuera: `docs/en/`, `docs/examples/`, `docs/agents/`, doc interna, planes y `tasks.md`. **Confirmado.**
2. **D2 — Sin presets de audiencia.** Un único default sensato; la copia 1:1 se consigue editando `include`/`exclude` a mano, pero no es opción de primera clase. **Confirmado.**
3. **D3 — Ledger: `implementer` sincroniza al cerrar cada fase**, ni tarea a tarea ni solo al final. **Confirmado.** (Ver la nota de interacción D1 ↔ D3 bajo la tabla de decisiones: con la política por defecto el disparo por fase refresca el alcance, pero `tasks.md` en sí no sube.)
4. **D4 — `**/testing/**` no se publica.** Se descarta transformar el `report.md`; el informe con capturas queda solo-local. **Confirmado.**

5. **D5 — El verificador entra, y ampliado con staging generado.** `confluence-scope.py` tendrá `--status` (informe de alcance/sincronizado/desactualizado/excluido) y `--stage` (regenera `docs/confluence/`), y `publish.source` apuntará a la carpeta generada. **Confirmado.**
   **Motivación registrada (literal del usuario):** quería una carpeta `docs/confluence/` para **ver a simple vista qué sube**. Se descartó mantenerla **a mano** porque crearía una segunda fuente de verdad que derivaría del original; la variante **generada** da la misma visibilidad sin duplicación. Los agentes siguen escribiendo **todo** (ADRs, arquitectura, gotchas, roadmap) en sus sitios canónicos de `docs/`; el staging es solo la materialización de la política.

**No queda ninguna decisión abierta.** El alcance comprometido incluye C-01 a C-05.

## Supuestos

- El conector Rovo MCP **no** expone subida de adjuntos: solo `createConfluencePage`/`updateConfluencePage`. Lo verificaría la lista de herramientas del conector en el entorno del usuario; si en el futuro la expusiera, la decisión de evidencias se replantea.
- La audiencia del espacio de Confluence es mixta (PM + equipo): por eso la forma sigue siendo opt-out (`exclude`) y no hay presets (D2).
- Con D1, la clasificación literal de los ficheros de cartera (`CALIBRATION.md`, `DRIFT.md`) es "se publican", por no estar entre las exclusiones acordadas. Son documentos internos de proceso: si al ver el primer espejo resultan ruidosos, quitarlos cuesta una línea de `exclude` (no es deuda estructural).
- Ningún proyecto consumidor tiene aún un espejo publicado con la política antigua (en este repo es seguro: no existen `confluence.json` ni `confluence-state.json`). Si lo hubiera, haría falta una fase de limpieza que hoy está fuera de alcance.
- **`docs/confluence/` se versiona** (no se ignora en git): duplica en disco los `.md` en alcance —decenas de KB, irrelevante— y a cambio el diff de cada PR muestra exactamente qué cambia en Confluence, que es la visibilidad que motivó D5. Si un proyecto prefiere ignorarla, pierde esa ventaja pero nada más.
- El coste de esta spec y de su evaluación **no está medido**: `usage-meter.py` no está disponible en el entorno donde se generaron (sandbox sin transcripción local). Los bloques `generacion:` van marcados `estimado`/`no-medido`.
