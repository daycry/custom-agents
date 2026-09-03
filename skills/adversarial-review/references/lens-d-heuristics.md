# Heurística de la Lente D (review-lens-select.py) — detalle

Léelo desde el paso 1 de `SKILL.md` **solo** si un motivo devuelto por `review-lens-select.py` te
sorprende o quieres ajustar `revision.excluir`. El contrato exacto son las constantes `RUTA_RE_D`/
`CONTENIDO_D_INDEPENDIENTE`/`LOOP_D_RE`/`PATRONES_TRAS_BUCLE_D` del script y sus tests
(`pytest -q skills/adversarial-review/scripts`); este texto las explica. Superiority T-04: misma
arquitectura, mismo script y mismo contrato de salida que la Lente C — decisión independiente.

Devuelve `lente_d: true|false` + motivos (fichero + patrón, y línea cuando aplica).

## Por RUTA (stems anclados al inicio de un token)

`repository`, `repo`, `dao`, `query`, `sql`, `migration(s)`, `cache`, `queue`, `worker`, `batch`,
`export`, `import`, `report`, `loop`, `scheduler` — `repository/user_repo.py`, `src/dao/UserDao.php`,
`workers/email_worker.py`, `jobs/scheduler.py` sí; ninguno lleva límite final (no son prefijo de
palabras inocuas habituales en este repo, a diferencia de `token(s)`/`acl`/`helm` en la Lente C). La
prosa (`.md`/`.txt`/`.rst`) y `docs/**` no se evalúan por ruta, igual que en C; `tests/**` sí.
`"revision": {"excluir": [...]}` en `dev.json` es el MISMO campo que usa la Lente C (mismos globs,
traductor de `confluence-scope.py`) y saca ficheros solo de la heurística de ruta de D — el
contenido añadido en un fichero excluido sigue escaneándose.

## Por CONTENIDO de las líneas añadidas del diff

Dos familias, ambas sobre las líneas `+` del diff (las borradas no cuentan; untracked cuentan
enteros); prosa/`docs/**`, tests y fixtures no se escanean por contenido (igual que en C); los
binarios se saltan.

**(a) Independientes de contexto** — basta con que aparezcan en cualquier línea añadida:

| Patrón | Qué detecta |
|---|---|
| `sleep-bloqueante` | una llamada `sleep(...)` — bloquea el hilo/proceso en vez de un delay asíncrono |
| `read-file-sync` | `readFileSync(...)` — lectura de disco síncrona en código que puede ser hot-path |
| `json-doble-vuelta` | `JSON.parse(JSON.stringify(...))` — clonar un objeto con doble serialización |

**(b) Dependientes de un bucle previo** — solo cuentan si aparecen dentro de una VENTANA de 6 líneas
añadidas **siguientes, del mismo fichero**, tras la apertura de un bucle de una sola línea
(`for x in y:` de Python, o la forma con paréntesis de otros lenguajes — heurística de proximidad
sobre texto, no un parser del lenguaje: puede tener falsos positivos, que `revision.excluir` o el
rebate con evidencia (§4 de `SKILL.md`) resuelven):

| Patrón | Qué detecta dentro del bucle |
|---|---|
| `n-plus-one` | una llamada de consulta — `.query(`, `.all()`, `->get()`, `->first()`, o `SELECT` — típica N+1 |
| `await-en-bucle` | `await` — serializa E/S que podría lanzarse en paralelo (`Promise.all`/`asyncio.gather`) |
| `regex-en-bucle` | `re.compile(...)` — compila la misma expresión regular en cada vuelta en vez de una vez fuera |
| `concat-en-bucle` | `+= "..."` — concatenación de cadenas O(n²) en vez de acumular en lista y unir al final |
| `bucle-anidado-con-llamada` | un SEGUNDO bucle dentro del primero que a su vez contiene una de las llamadas de arriba (típico recorrido de matriz con una consulta por celda) — se añade ADEMÁS de `n-plus-one`, no en su lugar |

El motivo se ancla en la línea de **apertura del bucle exterior**, no en la línea exacta del patrón
(igual que el resto del script: `fichero:línea` apunta al punto donde el revisor debe mirar el
contexto completo, no a un carácter suelto).

## Config y degradación

`.claude/dev.json` → `"revision": {"lenteRendimiento": "auto" | "siempre" | "nunca"}` — mismo
vocabulario y mismo default `auto` que `lenteSeguridad`; valor desconocido o `dev.json`
ilegible/ausente → `auto` + aviso por stderr (nunca bloquea). `/setup` paso 5-ter pregunta el modo
de ambas lentes en la misma pregunta. La lista exacta de patrones es el contrato: `RUTA_RE_D`/
`CONTENIDO_D_INDEPENDIENTE`/`PATRONES_TRAS_BUCLE_D`/`VENTANA_D` en el propio script, con sus tests.

## Qué NO detecta (a propósito)

Esto es una heurística de proximidad textual sobre el diff, no profiling real ni un parser del
lenguaje: no mide complejidad algorítmica real, no ejecuta el código, no sabe si un bucle recorre 3
elementos o 3 millones, y no ve bucles multilínea (`while`, bloques `{ }` de varias líneas en C-like)
salvo que abran en una sola línea seguida del cuerpo. Por eso la Lente D solo decide SI vale la pena
lanzar al revisor humano-artificial con criterio de rendimiento (`references/lens-prompts.md`); el
veredicto de "es o no un problema real, y de qué orden de magnitud" lo da esa lente, con el
escenario de carga concreto — nunca este script.
