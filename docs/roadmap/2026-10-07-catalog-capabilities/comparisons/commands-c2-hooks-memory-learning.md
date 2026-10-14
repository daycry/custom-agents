# Reglas de hooks, instintos y aprendizaje de sesión — C031–C037, C042–C043

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Nueve definiciones completas: **21.871 bytes/630 líneas**. [commands-c2-hooks-memory-learning-reading-evidence.json](commands-c2-hooks-memory-learning-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a los nueve.** Ninguno declara `allowed-tools` ni `model`. Todos escriben estado
persistente fuera del ledger y de `docs/knowledge/`: reglas en `.claude/hookify.*.local.md`,
instintos en `~/.claude/homunculus/` o skills en `~/.claude/skills/`. El estado de usuario
(`~/`) afecta a todos los proyectos de la máquina.

**Decisiones previas que se respetan.** [commands-workflow-comparison](commands-workflow-comparison.md)
fijó tres filas: «Reglas de hooks» (proponer, explicar, listar y configurar → servicio de hooks y
`/doctor`; Stop no se equipara a SessionEnd), «Memoria portable» (exportar approved, importar como
candidatos) y «Estado de memoria» (`/doctor` y panel). [operational-panel-commands](operational-panel-commands.md)
fijó para C042/C043 «criterios en `knowledge-curator`; generación de skills aplazada; ninguna
promoción automática». Las piezas subyacentes ya tienen ficha: S132 hookify
([skills-vpn-hookify-i18n-legacy](skills-vpn-hookify-i18n-legacy.md), sin destino), A011
conversation-analyzer ([agents-evaluator-simplifier-comms](agents-evaluator-simplifier-comms.md),
ya integrado en `journal.py candidatas`) y S053/S054 aprendizaje e instintos
([skills-session-learning-memory](skills-session-learning-memory.md), D-084 integrado, D-117 aparcado).

**Dueño por artefacto.** Hooks globales → `hooks/hooks.json`, que informan y no deciden
(ADR-007; `docs/observability.md:43`). Un deny solo vive en la guardia del agente
(`agent-kits/shared/guardrail-check.py`), con opt-out por regla en `dev.json` `guardrails`
(`commands/setup.md:36`). Conocimiento aprobado → `knowledge-curator`, único que decide
(`docs/agents/ROLES.md:35`); propuestas → servicio `knowledge-curation.py propose`.

## C033 — hookify-list

`484 bytes/21 líneas` · tools: hereda · model: hereda. Lista en tabla las reglas
`.claude/hookify.*.local.md` con `enabled`, `event`, `action` y `pattern`.

**Intención, artefactos y despacho.** Solo lectura, sin agente. No escribe nada.
**Disparador.** «qué reglas de hooks tengo».
**Escenarios.** (+) «qué hooks están activos en este proyecto» → `/doctor`, sección
«Automatizaciones» (`commands/doctor.md:86-90`: cada hook de `hooks.json`, statusline y
workflows, con fuente, alcance y fecha). (−) «por qué no salta el hook de journal» → también
`/doctor`, pero por su bloque de diagnóstico, no por un listado de reglas.

**Comparación.** El plugin no tiene ficheros de reglas de usuario; lo que lista `/doctor` es la
configuración real cargada, que es lo que la fila «Reglas de hooks» pide.

**Destino:** **Sin destino**: ya integrado en `/doctor` «Automatizaciones».

## C031 — hookify-configure

`390 bytes/14 líneas` · tools: hereda · model: hereda. Busca las reglas, muestra su estado,
pregunta cuáles conmutar y reescribe el campo `enabled:` (l.9-14).

**Intención, artefactos y despacho.** Escribe en `.claude/`. Sin validación del fichero ni de la regla.
**Disparador.** «desactiva la regla X».
**Escenarios.** (+) «desactiva la guardia de rama principal para este proyecto» → `/setup` o
`dev.json` `guardrails.ramaPrincipal: false` (`setup.md:36`). (−) «quita el aviso del ledger
cuando edito tasks.md» → no se conmuta: los hooks informativos no se apagan por regla salvo los
`sesion.*` documentados en CONVENTIONS.

**Comparación.** El opt-out por regla del plugin ya existe y solo afecta a la guardia de un rol,
con tests en `guardrail-check.py`. Conmutar `enabled:` en un Markdown no tiene validación.

**Destino:** **Sin destino**: ya integrado en `dev.json` `guardrails` y `/setup`.

## C032 — hookify-help

`1.187 bytes/46 líneas` · tools: hereda · model: hereda. Documentación del sistema: eventos
`bash`, `file`, `stop`, `prompt`, `all`; acciones `block|warn`; formato de regla (l.11-46).

**Intención, artefactos y despacho.** Solo muestra texto.
**Disparador.** «cómo funcionan los hooks».
**Escenarios.** (+) «qué hacen los hooks del plugin» → `docs/observability.md`. (−) «crea un
hook que bloquee `rm -rf`» → no hay hook global que bloquee (ADR-007); la guardia del
`implementer` ya lo deniega (`agents/implementer.md:62`).

**Comparación.** Defecto: «`stop`: triggers when a session ends» (l.15). `Stop` salta al
terminar cada respuesta, no al cerrar la sesión; es justo la confusión que la fila «Reglas de hooks»
prohíbe. El plugin escribe el journal en `SessionEnd`.

**Destino:** **Sin destino**.

## C034 — hookify

`1.430 bytes/50 líneas` · tools: hereda · model: hereda. Crea reglas a partir de una
descripción o, sin argumentos, analizando la conversación con `conversation-analyzer` (l.18-22).

**Intención, artefactos y despacho.** Despacha A011; escribe `.claude/hookify.{name}.local.md`
con `action: block|warn` (l.35-46) tras aprobación del usuario (l.24-31).
**Disparador.** «que no vuelva a hacer X», «crea una regla contra esto».
**Escenarios.** (+) «siempre me corriges lo mismo, apréndelo» → `journal.py candidatas` en
`/retro` paso 2-quater (`commands/retro.md:21`) y propuesta al curador. (−) «bloquea los push
forzados» → guardia del `implementer`, no una regla global.

**Comparación.** Bloquear desde un hook global por regex sobre el comando es lo que ADR-007
descarta (S132). Inferir «frustración» del tono (l.20) no es evidencia; `journal.py` clasifica
sin modelo (`agent-kits/shared/journal.py:224`).

**Destino:** **Sin destino** (ADR-007; A011 ya integrado en `journal.py candidatas`).

## C035 — instinct-export

`1.645 bytes/66 líneas` · tools: hereda · model: hereda. Exporta instintos de proyecto, globales
o ambos a YAML, con filtros de dominio y confianza.

**Intención, artefactos y despacho.** Fichero de salida o stdout (l.32). Dueño propio del
equivalente: el servicio `knowledge-curation.py export`.
**Disparador.** «comparte mis instintos con el equipo», «llévalos a otra máquina».
**Escenarios.** (+) «exporta estas tres lecciones aprobadas a otro proyecto» →
`knowledge-curation.py export --id …` (`docs/MEMORY-PORTABILITY.md:13-16`). (−) «publica la
memoria en Kwipu» → `knowledge-services` (`knowledge-sync.py`), no un paquete de exportación.

**Comparación.** El servicio propio exporta solo approved válido, por ID explícito, con SHA y
topes, y rechaza la nota que cambiaría al redactarla (`MEMORY-PORTABILITY.md:13-27`). C035
exporta por defecto **todo** (l.17, l.30), filtra por una confianza sin medida y no redacta.
Inconsistencia de frontmatter: `command: /instinct-export` (l.4) frente a `command: true` en C036/C037.

**Destino:** **Sin destino**: ya integrado en `knowledge-curation.py export`.

## C036 — instinct-import

`2.839 bytes/114 líneas` · tools: hereda · model: hereda. Importa instintos de fichero o URL
HTTP(S) con `instinct-cli.py`, detecta duplicados y fusiona por confianza (l.11-23, l.76-81).

**Intención, artefactos y despacho.** Escribe en `~/.claude/homunculus/…/inherited/` (l.40-42).
Equivalente propio: `knowledge-curation.py import`, que crea candidatos `pending`.
**Disparador.** «importa los instintos del equipo».
**Escenarios.** (+) «trae este paquete de lecciones del otro repo» → `import --check` y después
`import` (`MEMORY-PORTABILITY.md:32-36`), y el curador decide. (−) «aprueba lo importado» →
`knowledge-curator`, no el import.

**Comparación.** Defectos de la fuente: acepta URL sin integridad (l.29); con mayor confianza,
el importado **sustituye** al local (l.79); `--force` salta la confirmación (l.81, l.97). En el
plugin el import exige `--expected-sha256`, tiene preflight sin efectos y nunca aprueba: el
destino recibe propuestas pendientes (`MEMORY-PORTABILITY.md:6-8`). Coincide con la condición
«frecuencia/confianza/force no aprueban conocimiento» ya fijada.

**Destino:** **Sin destino**: ya integrado en `knowledge-curation.py import`.

## C037 — instinct-status

`2.648 bytes/59 líneas` · tools: hereda · model: hereda. Muestra los instintos por dominio con
barras de confianza; el proyecto prevalece sobre lo global (l.31-37).

**Intención, artefactos y despacho.** Solo lectura de `~/.claude/homunculus/`.
**Disparador.** «qué ha aprendido de este proyecto».
**Escenarios.** (+) «estado de la memoria técnica» → `/doctor`, bloques memoria técnica y
Journal (`commands/doctor.md:85`). (−) «busca qué sabemos de la caché» → `knowledge-find.py`
o el panel servido, no un estado.

**Comparación.** Defecto de seguridad: la l.21 ejecuta un `node -e` que hace `require` del primer
`scripts/lib/resolve-ecc-root` que encuentre recorriendo varios directorios de `~/.claude/plugins`,
incluida la caché de plugins. Carga y ejecuta código del primer candidato, sin comprobar su
procedencia. La confianza mostrada como barra (l.52-57) no es una medida.

**Destino:** **Sin destino**: ya integrado en `/doctor`.

## C043 — learn

`3.809 bytes/107 líneas` · tools: hereda · model: hereda. Extrae de la sesión un patrón
reutilizable y lo guarda como skill en `~/.claude/skills/<nombre>/SKILL.md` tras confirmación (l.40, l.81-95).

**Intención, artefactos y despacho.** Escribe una skill global que el runtime cargará en
**cualquier** proyecto. Dueño propio de la decisión de conservar aprendizaje: `knowledge-curator`.
**Disparador.** «guarda lo que hemos aprendido», «esto conviene recordarlo».
**Escenarios.** (+) «apunta esta trampa que nos costó una tarde» → `knowledge-curation.py propose`
(`/retro` paso 4-bis, `commands/retro.md:24`) y curador. (−) «aprueba esta lección como doctrina»
→ `knowledge-curator`, no una extracción.

**Comparación.** La escritura protegida (l.42-53: redacción, slug, sin sobrescritura silenciosa,
aprobación) es buena y equivale al servicio propio (`knowledge-write.md:50-56`). La diferencia de
fondo: una skill es una instrucción que se carga sola. Convertir una sesión en una skill global
salta la curación (ADR-018) y mezcla ámbitos: extrae «patrones específicos del proyecto» (l.33-36)
y los guarda siempre en el ámbito global (l.40).

**Destino:** **Sin destino**: ya integrado en `journal.py candidatas` + `propose` + `knowledge-curator`.

## C042 — learn-eval

`7.439 bytes/153 líneas` · tools: hereda · model: hereda. Como C043, con elección de ámbito
(global o proyecto), checklist de solapes y veredicto Save / Improve then Save / Absorb / Drop (l.23-118).

**Intención, artefactos y despacho.** Escribe o amplía una skill. Mismo dueño propio.
**Disparador.** «extrae y evalúa lo aprendido antes de guardarlo».
**Escenarios.** (+) «¿esto ya lo teníamos?» antes de proponer → el curador lee approved y legado
para detectar duplicados y contradicciones (`agents/knowledge-curator.md:53-56`). (−) «crea una
skill para este proyecto» → escalera de `/specialize` (`ROLES.md:40`; el comando aún no está entregado),
no un aprendizaje de sesión.

**Comparación.** Lo mejor del grupo: ámbito proyecto por defecto ante la duda (l.27), contenido
leído como no confiable (l.34-39), comprobación de solapes antes de escribir (l.86-89) y la opción
«Absorb» frente a crear otra entrada. El plugin ya tiene las tres primeras en el servicio y el
curador. La justificación del diseño, «los modelos frontera (Opus 4.6+) tienen buen criterio» (l.145),
es una afirmación sin medida. El veredicto lo emite el mismo agente que redactó el borrador.

**Destino:** **Sin destino** como comando; ver propuesta 1.

## Propuestas para integrar después

1. **P3 · `agents/knowledge-curator.md`, sección «0) ENTRADA / SALIDA»**, tras l.56, una línea:
   «Si el candidato repite una entrada aprobada, propón ampliar esa entrada en `needs_changes`
   (con la ruta de la existente) en vez de aprobar un duplicado». Fuente: «Absorb» de C042 l.99,
   l.113. El gate solo detecta colisión de `id` o de nombre de fichero con approved
   (`agent-kits/knowledge-curator/curator-gate.py:174-178`), no el solape de contenido; la
   lectura de duplicados (`knowledge-curator.md:53-56`) no dice qué hacer con uno.
2. **Ninguna línea en hooks**: listar y conmutar ya los dan `/doctor` y `dev.json` `guardrails`; la
   corrección «Stop ≠ SessionEnd» ya figura en la fila «Reglas de hooks».
