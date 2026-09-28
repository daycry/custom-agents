# Recorder, puerta humana e índice (training-data-services)

> Lee esto solo al llegar a los pasos 3-5 de `SKILL.md` (grabar, aprobar Gold, consultar el índice)
> o al diagnosticar un exit code del recorder. El contrato ejecutable vive en el docstring de
> `scripts/case-recorder.py`.

## Proceso detallado (pasos 1-5)

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
   `set-status` solo reescribe `validation.json` (atómico); lo demás es inmutable. Al aprobar,
   `set-status` guarda además `content_hash` (sha256 de los siete ficheros inmutables, leídos por
   descriptor bajo el bloqueo; si alguno no se puede leer, no aprueba): ata el Gold al contenido que
   se aprobó y el ensamblador y el puente excluyen el que ya no casa. Límite: detecta cambios accidentales o del código del proyecto tras aprobar; **no protege frente a quien puede escribir el store**, que puede recalcular el hash (sha256 sin clave). `record --approved-by-human` no
   lo guarda (al escribir `validation.json` la versión aún no tiene `metadata.json`): ese Gold se
   exporta con aviso «sin hash de aprobación» hasta pasarlo por `set-status`.
5. **Consultar**: `list [--status S] [--family F] [--outcome O] [--json]` lee el índice
   `cases_index.jsonl`, que es una **caché** (una línea corrupta se ignora con aviso al leerla);
   `index rebuild` lo reconstruye desde `cases/` e `index check` lo compara (semántica abajo). El
   ensamblador lee `validation.json`, no el índice.
6. **Ensamblar** el dataset y **proponer** un caso Gold al Curator: `references/dataset.md`.

## Códigos de salida y `index check`

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

**Resumen para `/doctor` (`resumen_store`, T-10).** De solo lectura, sin bloqueos ni red: recorre
`cases/` con los mismos lectores seguros (nunca el índice) y devuelve el recuento por estado
(`pending`/`approved`/`needs_changes`/`rejected`), las versiones incompletas, los temporales
huérfanos (también los de DENTRO de una versión, como `index check`, #149), las versiones con un
`metadata.json`/`validation.json` por encima de `TOPE_FICHERO` (16 MiB: se mira el `st_size` del
descriptor antes de leer y no se cargan, #148) y los Gold vigentes con su `content_hash` (para la
frescura por contenido, #154). Cada categoría sale de un **código** que acompaña al aviso, nunca de su
texto (que incluye nombres que elige un tercero, #157). Va **acotado en tiempo** (`RESUMEN_PLAZO_S` =
2 s; medido en Windows: 10⁴ versiones tardan 10,7 s en caliente y más de 70 s en frío): pasado el tope
corta entre casos, entre versiones o a mitad del listado de la raíz o de `cases/` (#152, «al menos N»)
y lo declara (`truncado`, «N de M casos»; un caso omitido por enlace también cuenta como visto, #155);
los reintentos de los lectores ante un bloqueo tampoco pasan del plazo (#163). El total exacto lo da
`index check`.

## Qué se redacta y concurrencia

- Se redacta todo texto libre que se escribe: `request`, `context`, `constraints`, `trajectory`
  (un `arguments` en texto JSON, como estructura), las cadenas de `metrics`, `created_at`,
  `artifacts[]` (salvo `hash`), `reviewer_note`/`approved_at` y `set-status --note`; el valor textual de
  una clave sensible (`password`, `api_key`, `token`, `secret`…) se redacta entero. No se tocan
  los campos cerrados: `case_id`, `family`, `variant`, `version`, `outcome`, `supersedes_case`,
  `status`, `approved_by_human`, `hash`. Se rechazan `NaN`/`Infinity`, tipos que no son JSON, texto
  no codificable en UTF-8, más de 50 niveles de anidamiento y un `arguments` con claves duplicadas.
- El bloqueo `<root>/.cases_index.lock` (persistente, nunca se borra) solo cubre pasos cortos: la
  reserva de la versión (el `mkdir` del directorio del caso si es nuevo y el de `vNNN`), su línea del
  índice y cada `set-status`. Solo si otro lo creó a la vez (el `mkdir` del caso choca) recorre
  `cases/` una vez para decidir. Los ficheros se escriben sin él, tras la reserva, **directamente en
  `vNNN`** con `O_EXCL` (sin temporal ni `os.replace`; `metadata.json` el último); si no llega en 10 s,
  exit 3 (reintenta). Fuera del bloqueo, un caso existente se comprueba en O(1) y uno nuevo recorre
  `cases/`. 32 × 6 `record`: 0 exit 3 sin carga; ~1-2 % con la CPU saturada, igual con 100 casos que con 10⁵.
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
