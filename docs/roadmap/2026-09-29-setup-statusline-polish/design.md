---
design: "setup-statusline-polish"
titulo: "Alta del proyecto en projects.yaml de Kwipu (solo añade) y enmienda a ADR-018 / PAT-001"
estado: borrador              # borrador | aprobado | obsoleto
creado: "2026-09-30"
actualizado: "2026-09-30"
spec: spec.md                 # enlace hacia atrás (misma carpeta)
evaluacion: "evaluation.md"
plan: improvement-plan.md     # el plan ya existe; T-09 es la tarea de diseño que bloquea T-12/T-13
adr: "docs/knowledge/adr/ADR-020-alta-kwipu-append-only-en-projects-yaml.md"   # SOLO LOCAL: docs/knowledge/ no se versiona (PR #14)
opcion_elegida: "pendiente"   # pendiente | O1 | O2 | O3 — se fija SOLO tras la validación del usuario
generacion:
  inicio: 2026-09-29T22:02:28Z
  fuente: estimado            # el meter degradó: carpeta de transcripciones no disponible
  tokens_reales: null
  eur: null
  horas_ia: 0.17              # estimado = duración de reloj; no derivado de tokens
  duracion: 10m
  ratio_usado: 479326         # CALIBRATION.md (mediana de 5)
---

# Diseño — Alta del proyecto en `projects.yaml` de Kwipu (solo añade)

> **Spec:** [`spec.md`](spec.md) (aprobada) · **Evaluación:** [`evaluation.md`](evaluation.md) (go condicionado, condiciones 1-3) · **Plan:** [`improvement-plan.md`](improvement-plan.md) (T-09 → T-12, T-13) · **ADR:** `ADR-020` `propuesta`, solo local en `docs/knowledge/adr/` (no se versiona; la decisión versionada es la sección «Decisión» de este documento)

| | |
|---|---|
| **Estado** | borrador |
| **Opción elegida** | pendiente — recomendada O1 |
| **Validada por el usuario** | pendiente |

## 1. Contexto y restricciones

La spec pide que `/setup` dé de alta el proyecto en `<stack>/kwipu/config/projects.yaml` sin modificar ni borrar nada (alcance 7, flujo 1-7, CA-09..CA-13). La evaluación condiciona C-07 a una decisión escrita, porque choca con tres textos vigentes:

- **ADR-018 §2** (`aceptada`): «No hay `project_id`, tenant ni `projects.yaml`». Descarta el *control plane* multi-proyecto.
- **PAT-001** (`approved/`): el adaptador «nunca ejecuta el stack». Tocar `projects.yaml` le da al plugin «permisos y superficie de fallo que no le corresponden».
- **Constitución §4**: «Una pieza nunca borra ni sobrescribe lo que no ha creado; no sigue rutas decididas por un tercero (enlaces, traversal)». La escritura atómica que citaba la spec (temporal + `os.replace`) reemplaza un fichero que el plugin no creó.

Qué hay hoy en el repo y en el stack:

- `skills/knowledge-services/backends/markdown_export.py` exporta a `export_dir` (`.claude/knowledge-services/kwipu-export` en `agent-kits/shared/templates/taxonomy.json`) y solo nombra el remedio (`REMEDIO`, línea 152).
- `skills/knowledge-services/scripts/knowledge-sync.py` usa esta convención de salida: `0` ok · `1` errores · `2` uso.
- `<stack>/kwipu/source_manager/build_view.py` (externo, se ejecuta en el host) carga el YAML con `yaml.safe_load`. Exige que `projects` sea un mapa, que cada id cumpla `Path(id).name == id` y que un proyecto `enabled` tenga un `root` que exista como directorio. Si no, **aborta toda la vista**. Resuelve un `root` relativo contra `kwipu/config/`. Si falla, no toca la vista anterior: descarta el staging.
- La muestra anonimizada (orquestador, 2026-09-29) usa estilo de bloque, `projects:` como **última** clave de primer nivel, indentación de 2 espacios y `root` relativa entre comillas dobles.

**Restricciones que fijan el espacio de soluciones**

- Solo stdlib y multi-runtime (constitución §2). La stdlib no trae parser YAML, así que el script reconoce una gramática mínima y rechaza todo lo demás.
- El plugin no ejecuta `build_view` ni reinicia contenedores (PAT-001, fuera de alcance de la spec): imprime los comandos.
- Nada de datos personales en lo versionado: ejemplos con `<stack>/…`. La ruta del stack **no se persiste** en `taxonomy.json`, que puede estar versionado. `/setup` la pide cada vez.
- La decisión del usuario es firme: el setup **añade**, con vista previa, confirmación, copia de seguridad e idempotencia.

## 2. Opciones (2-3)

Las tres comparten el contrato del script (gramática, `root`, conflicto, códigos de salida; ver §4). Se diferencian en **cómo** se escribe, o si se escribe.

### O1 — Append in situ con bloque marcado (`O_APPEND` + identidad antes/después)

El script nunca reescribe el fichero. Tras la vista previa y la confirmación:

1. `lstat` del destino: fichero regular, sin enlace simbólico ni *reparse point*, y `st_nlink == 1`. Si hay un enlace duro compartido, no se escribe (lección de #197 en `training-data-services`).
2. Lee los bytes previos por un descriptor, comprueba que `fstat` coincide con el `lstat` (`st_dev`, `st_ino`) y que el `sha256` coincide con el `--esperado` de la vista previa.
3. Crea una copia con `O_CREAT|O_EXCL`, le hace `fsync` y la relee para comparar el hash.
4. Abre con `O_WRONLY|O_APPEND` y comprueba de nuevo la identidad y que `st_size` sigue igual. Añade el bloque en **un solo** `os.write`, comprueba los bytes escritos y hace `fsync`.
5. Relee el fichero. Debe ser `previo + bloque`, con la misma identidad y el par nombre→`root` presente. Si no lo es y el prefijo sigue intacto, `os.truncate(len(previo))`: solo quita los bytes que acaba de añadir. Si el prefijo cambió, no toca nada y señala la copia.

El bloque va entre marcas de comentario del plugin (`# >>> custom-agents:<nombre> …` / `# <<< custom-agents:<nombre> <<<`). El usuario ve qué es suyo y qué no, y puede borrarlo a mano.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: comprobaciones de identidad, escritura única y reversión por `truncate`. Todo es stdlib (`os.open`, `os.fstat`, `os.truncate`) y funciona en Windows y POSIX |
| Riesgo | Bajo-medio. Un corte a mitad de `write` puede dejar un bloque truncado. Lo mitiga que `build_view` aborta sin tocar la vista, la marca de apertura sin cierre da exit 3 en la siguiente pasada y la copia existe. En Windows, `O_APPEND` no es atómico entre escritores concurrentes; la relectura lo detecta |
| Coste relativo | M |
| Reversibilidad | Alta. El bloque está delimitado y la copia es exacta. La identidad del fichero (inodo, permisos, ACL, enlaces, dueño) nunca cambia, así que no hay nada irreversible |

### O2 — Reemplazo atómico (temporal + `fsync` + `os.replace`) con prefijo idéntico

Es el flujo que citaba la spec. Se escribe `previo + bloque` en un temporal hermano y se hace `os.replace` sobre `projects.yaml`, con copia y relectura. El contenido previo queda byte a byte igual, pero el **fichero** es otro.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: patrón conocido del repo (`outbox.py`, `markdown_export.py`), pero hay que copiar modo y ACL a mano y manejar el `PermissionError` de Windows si otro proceso tiene el fichero abierto |
| Riesgo | Medio. **Viola §4 tal como está redactada**, porque sustituye un fichero que el plugin no creó; exige enmendar la constitución, que es del usuario. Rompe enlaces duros, pierde dueño/ACL si no se copian, falla si el fichero es un *bind mount* de un solo fichero y provoca conflictos en carpetas sincronizadas (OneDrive) |
| Coste relativo | M |
| Reversibilidad | Media. El contenido vuelve con la copia, pero la identidad perdida (enlaces, dueño, ACL) no se recupera |

### O3 — No escribir: generar el bloque y que el usuario lo pegue

El script hace todo menos escribir. Reconoce la forma, detecta el conflicto y la idempotencia, e imprime el bloque exacto con la línea donde va. El usuario lo pega. Es la reducción que dejaba la evaluación si no se aceptaba la ADR (≈ −8 h humanas, −3 h IA). Coincide con la rama «forma no reconocida» de O1/O2.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: solo lectura y formato |
| Riesgo | Bajo para el stack, que nunca se toca. Riesgo de uso: el usuario pega mal (indentación) y `build_view` aborta. No hay copia porque no hay escritura |
| Coste relativo | S |
| Reversibilidad | Total: no hay efecto que deshacer. No requiere enmienda de ADR-018 ni de PAT-001 |

## 3. Criterios de decisión

1. **Constitución §4 sin enmienda** (manda sobre cualquier opción). El usuario pidió respetarla, no reescribirla.
2. **Cumplir la decisión del usuario**: el setup *añade* sin un paso manual.
3. **Reversibilidad y daño acotado** sobre un recurso compartido del usuario (el stack sirve a varios proyectos, y un `projects.yaml` roto tumba la vista de todos).
4. **Coste**, solo como desempate; la evaluación ya presupuestó C-07 completo.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto:** **O1** (append in situ con bloque marcado). Es la única que cumple a la vez §4 al pie de la letra (criterio 1) y la decisión del usuario (criterio 2): no reescribe ni un byte previo, no cambia la identidad del fichero, y lo único que crea son los bytes del bloque, marcados, y la copia (`O_EXCL`). También es la de mayor reversibilidad (criterio 3). Cuesta lo mismo que O2 (criterio 4).

**pendiente — a validar por el usuario.**

Descartadas (propuesta, se confirma en la pasada 2):

- **O2**: viola §4 como está redactada (criterio 1) y su identidad perdida no se recupera (criterio 3).
- **O3**: incumple la decisión «el setup añade» (criterio 2). Queda como la rama de degradación (exit 3) de O1.

### Decisión (enmienda a ADR-018 / PAT-001)

*Propuesta con O1. Se reescribe en la pasada 2 si el usuario elige otra.*

1. **ADR-018 §2 se enmienda, no se deroga.** `projects.yaml` sigue sin ser plano de control ni fuente de verdad. El plugin no introduce `project_id` ni tenant, y no lo lee para decidir su comportamiento, salvo para comprobar idempotencia y conflicto en el alta. La fuente del nombre y de la carpeta sigue siendo `taxonomy.json` (`id_prefix`, `backends.<id>.config.export_dir`). La entrada en `projects.yaml` es una **proyección derivada** que se escribe una vez.
2. **PAT-001 se acota con una excepción nombrada.** El adaptador (`markdown_export.py`), `knowledge-sync.py`, los hooks y `/doctor` siguen sin escribir en el stack y sin ejecutarlo. Una sola pieza, `skills/knowledge-services/scripts/kwipu-project-add.py`, invocada desde `/setup` 5-sexies, puede **añadir** una entrada, y solo con una confirmación explícita atada al hash del fichero. `build_view` y los reinicios se siguen imprimiendo, nunca se ejecutan. PAT-001 vive en `approved/` y solo `knowledge-curator` puede versionarlo, así que la v2 va como candidata (§7).
3. **§4 se cumple por construcción.** Nunca se reescribe un byte existente, se conserva la identidad del fichero, se niega ante enlaces simbólicos o duros compartidos, la copia es nueva (`O_EXCL`) y la reversión solo trunca lo que el script acaba de añadir.

### Contrato del script (común a las tres opciones)

**Gramática reconocida** (por líneas; cualquier otra cosa → exit 3):

- UTF-8 sin BOM. Fin de línea uniforme: todo LF o todo CRLF; el bloque usa el mismo. Si hay mezcla, exit 3. Sin tabuladores en la indentación.
- Sin `---`, `...` ni directivas `%`, y sin anclas ni alias (`&`, `*`, `<<:`) en ninguna línea que no sea comentario.
- Exactamente una línea de primer nivel `projects:` (con comentario opcional), sin valor en línea: `projects: {}` o `projects: null` → exit 3.
- `projects:` es la **última** clave de primer nivel: tras ella, toda línea que no esté en blanco ni sea comentario va indentada. Esto garantiza que lo añadido al final cae dentro de `projects`.
- Hijos de `projects` con una indentación `N > 0` constante: `^ {N}<clave>:\s*(#.*)?$`, clave simple o entre comillas simples o dobles sin escapes. Un valor en línea (`p: {…}`) o una clave duplicada → exit 3. Sin hijos, `N = 2` y el paso de campos es 2.
- `root` de cada hijo: un campo directo `^ {M}root:\s+<escalar>\s*(#.*)?$`, con escalar plano, `'…'` o `"…"` sin escapes. Un `root` multilínea (`|`, `>`) o repetido → exit 3. Si falta `root`, se registra como «ilegible»: cuenta como conflicto si el nombre coincide.
- Una marca `# >>> custom-agents:` sin su cierre `# <<<` → exit 3 («bloque del plugin incompleto», con la ruta de la copia).

**Bloque emitido** (con `N` y el paso detectados; la muestra da 2 y 2):

```yaml
  # >>> custom-agents:<nombre> · añadido por /setup el AAAA-MM-DD · no editar entre marcas >>>
  <nombre>:
    enabled: true
    root: "<root>"
    sources:
      - path: "."
        required: false
  # <<< custom-agents:<nombre> <<<
```

Si el fichero no acaba en fin de línea, el bloque empieza por uno; sigue siendo un añadido. `required: false` hace que un `export_dir` vacío no aborte la vista.

**`root`: relativa a `kwipu/config/`, con absoluta como respaldo.** Es relativa, como la convención del fichero y de la muestra, porque sobrevive a mover o sincronizar stack y proyecto juntos. Pasa a absoluta solo si `os.path.relpath` no es posible (otra unidad o ancla en Windows). Siempre se escribe con `/` y entre comillas dobles. Se valida que no haya caracteres de control, `"` ni `\`; si los hay, exit 2. Se calcula desde el `realpath` de `export_dir` resuelto contra la raíz del proyecto, con las reglas de `_export_dir_resuelto` de `markdown_export.py`. Si `export_dir` no existe, `--apply` lo crea: es del plugin y está dentro del proyecto. Así `build_view` no aborta por un `root` inexistente.

**Nombre:** `id_prefix` de `taxonomy.json` (T-10) o `--nombre`. Se valida con `^[a-z0-9][a-z0-9-]*$` y hasta 64 caracteres; si no cumple, exit 2.

**Conflicto** (se compara sin distinguir mayúsculas, porque `build_view` usa el nombre como carpeta y Windows no las distingue):

| Caso | Resultado |
|---|---|
| Mismo nombre y misma `root` tras normalizar (`normcase(realpath(config_dir / root))`) | No-op, «ya presente», exit 0 |
| Mismo nombre y otra `root`, o `root` ilegible | Conflicto, exit 4: no escribe y pide otro nombre |
| Otro nombre con la misma `root` | Conflicto, exit 4: «esa carpeta ya está dada de alta como `<otro>`». Renombrar no se hace aquí, porque eso es modificar |

**Interfaz y confirmación.** Sin `--apply`, el script es la vista previa y nunca escribe. Imprime el estado (`nuevo · presente · conflicto · no-reconocido`), el bloque, la ruta destino escapada y el `sha256` actual, y con `--json` también el campo `estado`. `/setup` pide la confirmación al usuario. Solo entonces relanza con `--apply --esperado <sha256>`. Si el fichero cambió entre la vista previa y el `--apply`, exit 1 y se vuelve a previsualizar; eso cubre dos `/setup` simultáneos. Si el usuario no confirma, no se invoca `--apply`: exit 0, como pide la spec.

**Códigos de salida:**

| Código | Significado |
|---|---|
| `0` | Vista previa emitida, bloque añadido o ya presente (no-op) |
| `1` | No escribió o revirtió por E/S: fallo de la copia, hash distinto al `--esperado`, identidad cambiada, verificación posterior fallida |
| `2` | Uso: argumentos, nombre o `root` inválidos, `taxonomy.json` sin backend `markdown-export` o sin `export_dir`, destino fuera de `<stack>/kwipu/config/projects.yaml` |
| `3` | **Forma no reconocida**: ausente, ilegible, fuera de la gramática, enlace simbólico o duro compartido, bloque del plugin incompleto. No escribe e imprime el bloque para pegar a mano |
| `4` | Conflicto de nombre o de `root`. No escribe y pide otro nombre |

**Comandos que imprime** (nunca los ejecuta; el script no importa `subprocess`). Si se declaran, se imprimen tal cual los de `backends.<id>.config.reindex` (lista de cadenas). Si no, los de la guía de operación del stack, con `<stack>` sustituido:

```text
cd <stack>
python -m source_manager.build_view --config kwipu/config/projects.yaml --output kwipu/runtime/knowledge-view-v2
docker compose restart kwipu kwipu-bridge kwipu-mcp
```

### Anexo C-08 — qué es una «instalación nueva» (para T-10; no abre opciones)

Es **previa**, y conserva el `group_id` que se deriva hoy de la carpeta, recibiendo aviso, si ocurre cualquiera de estas cosas:

- existe `.claude/knowledge-services/graphiti-manifest.json` o `graphiti-manifest.pending.json`;
- algún backend `type: "graphiti"` tiene `enabled: true`;
- ya declara un `group_id` explícito, que nunca se toca.

En cualquier otro caso es **nueva**: `/setup` materializa `group_id = id_prefix` explícito en `taxonomy.json`. Materializarlo en la config, en vez de cambiar la derivación en tiempo de carga (`_con_group_id_por_defecto` en `agent-kits/shared/knowledge-schema.py`), evita la migración silenciosa que señaló la evaluación. La implementación y el test son de T-10.

## 5. Impacto en módulos y ficheros

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `skills/knowledge-services/scripts/kwipu-project-add.py` | Gramática, conflicto, vista previa y `--apply` según la opción elegida (O1: append con identidad); códigos 0-4 | Nuevo (T-12) |
| `skills/knowledge-services/scripts/test_kwipu_project_add.py` | CA-09..CA-13, gramática (cada rechazo → 3), enlaces, `nlink>1`, hash cambiado, reversión por `truncate`, bytes previos idénticos | Nuevo (T-12) |
| `skills/knowledge-services/backends/markdown_export.py` | Solo se reutiliza `_export_dir_resuelto`, cargado por ruta como en `knowledge-sync.py:131`; sin cambio de comportamiento | Leído |
| `commands/setup.md` (5-sexies) | Pide la ruta del stack (no la persiste), vista previa → confirmación → `--apply --esperado`, rama exit 3 (pegar a mano) y exit 4 (otro nombre); imprime los comandos | Modificado (T-13) |
| `skills/knowledge-services/SKILL.md`, `skills/knowledge-services/references/kwipu-adapter.md` | Contrato del alta y excepción acotada a PAT-001 | Modificado (T-12) |
| `docs/agents/CONTRACTS.md` | Arista `/setup` → `kwipu-project-add.py` con Puerta | Modificado (T-13) |
| `agent-kits/shared/templates/taxonomy.json` | Opcional: `backends.kwipu.config.reindex` documentado (ausente = comandos por defecto) | Modificado (T-12, si se acepta) |
| `interop/**` | Regenerado por `scripts/export-interop.py` tras tocar `commands/setup.md` | Generado (T-13) |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Corte a mitad del `write`: bloque truncado y YAML inválido | Baja | Alto: `build_view` aborta la vista de todos los proyectos | `build_view` no toca la vista anterior si falla; la marca sin cierre da exit 3 con la ruta de la copia; un solo `write` de un bloque < 1 KB |
| Un `projects.yaml` válido pero fuera de la gramática (flujo, anclas, `projects` no al final) | Media | Bajo: no escribe, cae a pegar a mano | Exit 3 con el bloque impreso y la línea donde va. La gramática crece solo con muestras reales |
| El proyecto se mueve o se borra y su `root` deja de existir | Media | Alto: `build_view` aborta toda la vista | El mensaje final lo avisa y dice qué bloque quitar. El plugin nunca borra la entrada (fuera de alcance) |
| Escritor concurrente (editor o segundo `/setup`) | Baja | Medio | `--esperado <sha256>`, identidad y tamaño antes del `write`, relectura después; si el prefijo cambió, no se toca nada |
| La copia contiene rutas de otros proyectos del usuario | Media | Medio si acaba versionada | Vive junto al original en `<stack>/kwipu/config/` (fuera del repo del proyecto), nunca en `.claude/` |
| El `export_dir` se indexa entero, incluido `manifest.json` si el stack permite `.json` | Baja | Bajo | Hoy `allowed_extensions` no incluye `.json`; se documenta en `kwipu-adapter.md` |
| Enmienda no curada: PAT-001 sigue diciendo lo contrario en `approved/` | Alta hasta curar | Bajo | Candidata v2 para `knowledge-curator` (§7); la ADR-020 y este diseño lo citan |

## 7. Preguntas abiertas

- **Para el usuario (puerta):** ¿O1, O2, O3 o una variante?
- **PAT-001 v2:** solo la puede aprobar `knowledge-curator`. ¿Se abre la candidata en `docs/knowledge/candidates/pending/` en la pasada 2 o al cerrar T-12?
- **ADR-018:** añadir en su cabecera la nota «enmendada por ADR-020 (§2)». No está en el alcance de escritura de `architect`; queda para quien la acepte.
- **`reindex` configurable** en `taxonomy.json`: ¿entra en T-12 o se imprimen siempre los comandos por defecto?
- **La copia en `kwipu/config/`** añade un fichero sin seguimiento si el stack es un repo git. ¿Se acepta, o se prefiere un subdirectorio `backups/` junto al fichero?

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-30 | Diseño creado (`borrador`); tres opciones y la recomendación O1 presentadas al usuario vía el orquestador |
