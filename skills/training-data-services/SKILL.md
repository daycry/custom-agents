---
name: training-data-services
description: >
  Captura DETERMINISTA de casos (petición, contexto, trayectoria chat/SFT sin chain-of-thought,
  métricas opacas del proyecto, validación) en un case store versionado FUERA de Git y de
  `docs/knowledge/`, y ensamblado de dataset solo con casos Gold aprobados por un humano. Opt-in
  por proyecto con `.claude/knowledge-services/training.json`; sin él, cero impacto. El plugin
  valida FORMA, nunca dominio: no calcula métricas, no marca Gold solo, no entrena ni sirve
  modelos. `scripts/case_schema.py` valida `training.json` y el esquema del caso (vocabularios
  cerrados de `validation.status` y `outcome`, mapeo declarado desde `useful|dead_end|corrected`).
  Úsala cuando el usuario diga "guarda este intento como caso", "captura casos para entrenar un
  modelo local", "valida el esquema del caso", "prepara un dataset con los casos aprobados",
  "activa training-data-services", o al activar la capacidad `training` desde `/setup`.
---

# training-data-services — casos versionados y dataset Gold, sin saber nada del dominio

Algunos proyectos repiten tareas con una forma objetiva de medir el éxito y quieren conservar cada
intento para entrenar después un modelo local más barato. Esta skill da el **mecanismo genérico**:
esquema del caso, recorder determinista, puerta humana para Gold y ensamblador de dataset. Todo lo
de dominio (métricas, simulación, herramientas) es del proyecto consumidor.

> Regla central: **Gold es siempre una acción humana explícita** y **solo Gold se exporta**. El
> conocimiento aprobado nunca alimenta hacia atrás al case store (anti-leakage).

## Cuándo NO usarla

- Para curar o aprobar conocimiento (`docs/knowledge/candidates/`): `knowledge-curator` (esta skill,
  como mucho, **propone** un caso Gold, `bridge_to_curator`); para publicarlo (Kwipu): `knowledge-services`.
- Para calcular una métrica, simular o evaluar semánticamente un resultado: código del proyecto.
- Para lanzar un fine-tuning, servir un modelo o correr un benchmark: siempre fuera del plugin.
- Sin `training.json` (o con `enabled: false`) no hay nada que hacer: la capacidad está apagada y
  eso es correcto, no un error.

## Piezas

| Fichero | Qué es |
|---|---|
| `scripts/case_schema.py` | Validador stdlib de `training.json` y del caso (exit 0 válido · 1 errores · 2 uso/JSON ilegible). Fuente única de los vocabularios cerrados y del mapeo de `outcome`. |
| `scripts/case-recorder.py` | Recorder (API importable + CLI `record` · `set-status` · `index` · `list`; todos aceptan `--config <training.json>` y `--project-root <dir>`). Graba cada intento como versión inmutable `cases/<family>.<variant>/v<NNN>/`. La redacción la delega en `agent-kits/shared/redact.py` (fuente única); sin él se niega a grabar. Un caso `corrected` exige que la versión que corrige exista y sea `failure` o `corrected`. |
| `assets/` | Plantillas del case store: `training.example.json`, ejemplo completo `case-store-example/` (caso con par fallo → corrección) y `README.md` con la estructura y cada fichero de versión (`metadata.json`, `validation.json`, `cases_index.jsonl`…). Ubicación: `docs/knowledge/adr/ADR-019-case-store-fuera-de-docs-knowledge.md`. |
| Capacidad `training` | Entrada de `agent-kits/shared/capabilities.py`: `deshabilitado` sin fichero, `error` con fichero y campo si la config es inválida, `declarado`/`ok` según exista `root`. Sin red. |

## Config opt-in — `.claude/knowledge-services/training.json`

| Clave | Obligatoria | Qué es |
|---|---|---|
| `version` | sí | `1` |
| `enabled` | no (`false`) | Activa la capacidad `training` |
| `root` | si `enabled` | Raíz del case store; la elige el proyecto (relativa a su raíz o absoluta, sin `~`); nunca dentro de `<proyecto>/docs/knowledge/` (resuelto con `realpath`, sin distinguir mayúsculas) |
| `id_prefix` | si `enabled` | Slug que prefija el `case_id`: `<id_prefix>-<family>.<variant>` |
| `ids` | no | `family_pattern` / `variant_pattern` (regex, sin puntos por defecto) · `version_width` (dígitos de `v<NNN>`, 3 por defecto) |
| `bridge_to_curator` | no (`false`) | Un caso Gold puede proponerse como candidato a `knowledge-curator` (nunca se aprueba solo) |

Cualquier otra clave se rechaza (salvo `$comment`), para que una errata no pase en silencio.

## Esquema del caso (resumen; el contrato completo vive en el docstring de `case_schema.py`)

- Obligatorios: `case_id`, `version` (entero ≥ 1), `family`, `variant`, `request` (literal),
  `trajectory` (turnos `system|user|assistant|tool` con `content`/`tool_calls`), `validation`,
  `outcome`. Para `record`, `version`, `case_id` y `validation` son opcionales: se asignan la
  siguiente versión libre, `<id_prefix>-<family>.<variant>` y `pending`.
- `validation.status` ∈ `pending · approved · needs_changes · rejected` (`approved` ⇔
  `approved_by_human: true`); `outcome` ∈ `success · failure · corrected`; `corrected` exige (y solo él admite)
  `supersedes_case: "<case_id>@v<NNN>"` en forma canónica (dígitos ASCII, relleno a `version_width`,
  ≥ 1) del mismo `case_id` y una versión anterior.
- `family`/`variant` son directorios: sin separadores, `..`, `.` (separa family y variant), `:`,
  controles, espacio final ni nombres reservados de Windows (`con`, `nul`, `com1`…), sea cual sea el patrón.
- La trayectoria **nunca** guarda chain-of-thought: se rechaza toda clave que empiece por `reasoning`,
  `thinking`, `thought`, `chain_of_thought` o `scratchpad` (sin distinguir mayúsculas, a cualquier
  profundidad del turno, también en `arguments`).
- Excepciones y límite: `reasoning_effort`, `thinking_budget` y `reasoning_level` son parámetros de
  proveedor y se admiten **solo** dentro de `tool_calls[].arguments`. Un turno con más de 50 niveles
  de anidamiento se rechaza.
- Un tipo inesperado es un error `{campo, mensaje}`, nunca un crash. `metrics` es un objeto JSON
  opaco del proyecto (el plugin no lo interpreta); `artifacts`, solo referencias `{path, hash, kind}`.
- `context`: texto u objeto libre; admite `refs: [{"ref": "<fichero:línea|nodo>", "kind": "..."}]`
  opcional para citar procedencia (nadie está obligado a usarla).

### Mapeo declarado de `outcome` desde fuentes externas

El vocabulario cerrado no se amplía: una fuente externa se **traduce** con `mapear_outcome(valor,
fuente)` (`OUTCOME_MAPEO`); lo que no esté en la tabla devuelve `None` (no se inventa).

| Fuente | Valor externo | `outcome` |
|---|---|---|
| `graphify` (`save-result`) | `useful` | `success` |
| `graphify` | `dead_end` | `failure` |
| `graphify` | `corrected` | `corrected` (el caso debe declarar `supersedes_case`) |

## Proceso

1. **Activar**: `training.json` con `enabled: true`, `root` e `id_prefix` (`/setup`, capacidad `training`).
2. **Validar** antes de escribir nada: `python3 scripts/case_schema.py config <training.json>` y
   `python3 scripts/case_schema.py case <caso.json> --config <training.json>`. `root` se resuelve
   contra la raíz deducida de `<proyecto>/.claude/knowledge-services/training.json` (o el cwd);
   `--project-root <dir>` la fija a mano. Si la ruta no se puede resolver, se rechaza.
3. **Grabar** cada intento: `python3 scripts/case-recorder.py record <caso.json>
   [--config <training.json>] [--project-root <dir>]`. Valida el caso original (forma y
   chain-of-thought), redacta y vuelve a validar lo redactado; solo entonces escribe. Sin `version`
   toma la siguiente libre (lo normal al repetir un intento); con `version` explícita (p. ej. para
   reproducir un store) se rechaza si ya existe, con cualquier ancho. Una versión nunca se
   sobrescribe; no hay borrado. Si la siguiente automática superaría `v999999999`, rechazo
   explícito: el caso agotó los números (graba con otro `variant`).
4. **Aprobar Gold**, siempre a mano, por una de las dos vías (misma puerta: el flag debe ser
   exactamente `True`): `set-status <case_id> <versión> approved --approved-by-human [--note …]`
   sobre una versión grabada, o `record <caso.json> --approved-by-human` con un caso que ya llega
   `approved`. Sin el flag, rechazo explícito. `needs_changes`, `rejected` y `pending` no lo piden.
   `set-status` solo reescribe `validation.json` (atómico); lo demás es inmutable.
5. **Consultar**: `list [--status S] [--family F] [--outcome O] [--json]` lee el índice
   `cases_index.jsonl`, que es una **caché** (una línea corrupta se ignora con aviso al leerla);
   `index rebuild` lo reconstruye desde `cases/` e `index check` lo compara (semántica abajo). El
   ensamblador leerá `validation.json`, no el índice.
6. **Ensamblar** el dataset (T-07…T-09, pendiente): solo Gold, dedup, benchmark por familia.

### Códigos de salida y `index check`

Exit 0 ok · exit 1 rechazo (caso o config inválidos, sin el flag de Gold, enlace, versión que ya
existe; en `record`, también el store cambió durante la escritura o una manipulación detectada) ·
exit 2 uso, JSON ilegible, error de E/S (también al escribir la versión: disco lleno, permisos) o
**permanente** (permisos, solo lectura, sistema sin bloqueos `ENOLCK`: reintentar no sirve, arregla
la causa) · **exit 3 transitorio**: **no se ha escrito nada** y reintentar es seguro. Si `record`
falla tras reservar (exit 1 o 2), la reserva queda y `index check` la reporta. Exit 3 por subcomando:

- `record`: el bloqueo no llegó en la reserva, o hubo más de 64 números ocupados 3 veces seguidas.
  Nunca después de grabar: si la línea del índice no se escribió, sale con 0 y un aviso («`index
  rebuild`»; si el aviso dice PERMANENTE, arregla antes los permisos). No la repitas.
- `set-status`: el bloqueo no llegó. `index rebuild`: algún bloqueo no llegó o la identidad del
  índice (sustituido o truncado) cambió 3 veces seguidas. `index check`: la identidad cambió 3
  veces seguidas. `list`: nunca.

`index check` no escribe ni toma el bloqueo. Sale con **exit 1** si hay alguna de estas diferencias:

| Motivo | Exit | Qué hacer |
|---|---|---|
| Versión en `cases/` y no en el índice, al revés, o un campo distinto | 1 | `index rebuild` |
| Una línea corrupta del índice (se ignora con aviso al leerla) | 1 | `index rebuild` |
| Versión incompleta (sin `metadata.json` o `validation.json`) o con `mtime` futuro | 1 | Repárala o graba otra versión (se conserva) |
| Versión duplicada (mismo número con dos anchos) | 1 | Deja un solo directorio por número |
| Entrada con nombre de versión que no es un directorio de versión (fichero, enlace roto, número fuera de rango) | 1 | Retírala o renómbrala (no cuenta como duplicado) |
| Enlace (symlink/junction) o fichero que es un enlace duro | 1 | Sustitúyelo por el fichero real; nunca se sigue |
| Fichero que no es un fichero regular, no legible tras los reintentos (bloqueada o sin permisos) o JSON ilegible | 1 | Revisa permisos y contenido |
| `metadata.json` que no casa con su ruta o con el esquema, o `validation.json` incoherente (`approved` sin humano) | 1 | Corrígelo a mano; no se indexa |
| Un temporal huérfano `.tmp-*` (raíz, `cases/`, un caso o una versión) de hace ≥ 60 s o con `mtime` futuro, o un `.tmp-*` que es un enlace | 1 | Si no hay nada en marcha, bórralo a mano (el enlace, no su destino) |
| Un fragmento final del índice sin salto de línea que persiste (escritor muerto a mitad de línea) | 1 | `index rebuild` |
| Grabación interrumpida al publicar `metadata.json` (dos nombres: él y un `.tmp-*` hermano; no es un enlace duro) | 1 | Retira ese `.tmp-*` (solo ese nombre): la versión queda completa |
| Dos casos que solo difieren en mayúsculas, o un directorio con versiones de dos `case_id` (no se indexa la del intruso) | 1 | Renombra, fusiona o mueve a mano |

Es **informativo** (exit 0, línea `info:`) lo que está **en curso**: una versión sin
`metadata.json` (o con él a medio publicar) cuyo directorio tiene `mtime` de hace menos de 60 s, una
completa que está en `cases/` y no en el índice con `metadata.json` de hace menos de 60 s, o un
temporal reciente; y un caso que agotó los números de versión. Bajo
escritura muy intensa, `check` puede reportar un **falso positivo** transitorio que un segundo
`check` ya no ve.

### Qué se redacta y concurrencia

- Se redacta todo texto libre que se escribe: `request`, `context`, `constraints`, `trajectory`
  (un `arguments` en texto JSON, como estructura), las cadenas de `metrics`, `created_at`,
  `artifacts[]` (salvo `hash`), `reviewer_note`/`approved_at` y `set-status --note`. No se tocan
  los campos cerrados: `case_id`, `family`, `variant`, `version`, `outcome`, `supersedes_case`,
  `status`, `approved_by_human`, `hash`. Se rechazan `NaN`/`Infinity`, tipos que no son JSON, texto
  no codificable en UTF-8, más de 50 niveles de anidamiento y un `arguments` con claves duplicadas.
- El bloqueo `<root>/.cases_index.lock` (persistente, nunca se borra) solo cubre pasos cortos: la
  reserva de la versión (el `mkdir` del directorio del caso si es nuevo y el de `vNNN`), su línea del
  índice y cada `set-status`. Solo si otro lo creó a la vez (el `mkdir` del caso choca) recorre
  `cases/` una vez para decidir; el resto no depende del tamaño del store. Los ficheros se escriben
  sin él, tras la reserva, **directamente en `vNNN`** con `O_EXCL` (sin temporal ni `os.replace`;
  `metadata.json` el último); si no llega en 10 s, exit 3. Fuera del bloqueo, un caso que ya existe
  se comprueba en O(1); solo uno nuevo recorre `cases/` (10⁵ casos, 32 × 6 `record`: 0 exit 3).
- Límite declarado: en un sistema que distingue mayúsculas, dos casos creados a la vez que solo
  difieren en mayúsculas quedan en dos directorios (los dos siguen admitiendo `record`); `index
  check` reporta la pareja.
- **Límites declarados de la escritura** (sin `openat`/`O_NOFOLLOW` portables): quien tenga escritura
  en el store y sustituya un directorio por un enlace en los microsegundos entre una comprobación y
  una creación solo puede hacer que un fichero **nuevo** del recorder (o un directorio vacío nuevo:
  el del caso, `vNNN` o `final/`; en Windows, el índice o el bloqueo vacíos si planta un symlink de
  fichero) aparezca fuera: nunca se sobrescribe ni se borra nada. Se detecta (exit 1) y el aviso
  nombra la ruta solo si es el fichero creado (si no, «no localizado»). En `set-status`, con **dos**
  sustituciones de `vNNN` en ese intervalo, puede reemplazarse un `validation.json` en el destino del
  enlace (dentro o fuera del store) y crearse allí el temporal: quien puede hacerlo ya podía
  escribirlo. Lo único que el recorder borra es su propio `.tmp-<token>`, si sigue siendo el suyo.
- `index rebuild` (serializado con `<root>/.cases_rebuild.lock`) recorre `cases/` y relee del disco,
  sin bloquear a los escritores, lo que cambió mientras tanto; con el bloqueo solo copia el
  residual (las últimas líneas llegadas) **tal cual**. Límite declarado: un `set-status` muerto entre
  su escritura y su línea cuya clave caiga en ese residual queda como sin rebuild; `check` lo reporta.
- Nunca se escribe a través de un enlace que salga de `root` o entre en `docs/knowledge/`, ni en
  un índice, bloqueo o temporal con enlaces duros; el índice y el bloqueo se abren sin seguir
  enlaces (`O_NOFOLLOW` en POSIX; en todos, el nombre debe ser el fichero abierto). Los lectores
  omiten todo enlace sin seguirlo.

## Degradación

- Sin `training.json` o con `enabled: false`: la capacidad no existe para el ciclo (CA-01). Inválido:
  `/doctor` lo informa con fichero y campo; nada se bloquea. Sin `python3`: el resto del plugin sigue.

## Scripts y rutas

Rutas relativas dentro de la skill; desde fuera, `find` sobre las seis raíces de la regla 5 de `docs/CONVENTIONS.md`
(`-path '*skills/training-data-services'`). Los tests viven junto a los scripts, solo en el repo; sin dependencias.
