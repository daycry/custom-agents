# Paralelismo por paneles, contenedores y consulta de documentación — S083–S085

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **26.185 bytes/803 líneas**, cero recursos en sus
directorios. [parallel-containers-docs-reading-evidence.json](parallel-containers-docs-reading-evidence.json)
registra fuentes y contrapartes propias. Los scripts y el arnés que citan S083 y
S084 (`orchestrate-worktrees.js`, `docker/plugin-setup/compose.yaml`) no se
leyeron: sus afirmaciones quedan como declaradas, no comprobadas. Nombres
originales en el mapa privado; [tasks.md](../tasks.md) es el ledger canónico.
Las decisiones son propuestas para T-08.

No se ejecutaron tmux, dmux, Docker, Compose ni consultas Context7. Nada de este
bloque está integrado. S084 era una de las cuatro fichas que el bloque de despliegue
dejó «para comparación completa antes del diseño final»; queda cerrada aquí.

## S083 — Orquestación de agentes en paneles tmux

**Identidad.** SHA-256 `6e4028d61a55…` (completo en la evidencia), 6.336 bytes/192
líneas. Cinco patrones de paralelismo por paneles (investigar+implementar,
ficheros independientes, test+fix, varios runtimes, revisión por perspectivas),
worktrees por panel y un helper que crea ramas, ficheros de handoff y sesión tmux.

**Valor y cobertura existente.** El plugin ya tiene paralelismo con contrato:
`subagentes` de `/dev-cycle` (una tarea = un subagente fresco con brief de
`task-brief.py` y estados DONE/BLOCKED), `worktree` opt-in y las lentes de
`adversarial-review` en paralelo, todas con ledger canónico y puertas. dmux no
añade un rol: es un lanzador externo de sesiones sin estado compartido.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| Patrón 1: implementar mientras otra sesión investiga | Contradice «solo tareas independientes» de la propia pieza; en el plugin la investigación (research-first) precede al diseño |
| Patrón 3: un panel ejecuta tests en watch y otro corrige | Dos sesiones sobre el mismo árbol sin cerrojo; el fixer ve resultados de una versión que él mismo está cambiando |
| Patrón 5: revisión por perspectivas en paneles | Ya existe con contexto fresco y fusión en `adversarial-review`; los paneles no fusionan ni gradúan |
| `git merge feat/auth` y `feat/billing` al terminar | Sin puerta: el plugin exige revisión de dos lentes y `qa-gate` antes de integrar |
| Investigación escrita en `/tmp/...` | Fuera del proyecto y del ledger: se pierde la procedencia |
| `seedPaths` copia ficheros sin commitear a cada worktree | Puede propagar secretos o borradores; requiere lista explícita y revisión |
| «Mantener menos de 5-6 paneles» por coste | Heurística sin medición; el coste real lo da `usage-meter` |
| Lanzador `codex exec --cwd ... --task-file` en el ejemplo | Flags no contrastados con el CLI instalado (0.162.1 usa `--cd` y prompt posicional) |

**Decisión propuesta.** No adoptar dmux ni el helper. Conservar como criterio en
la documentación de `subagentes`: aislar por worktree cuando las tareas
compartan ficheros, y solo paralelizar tareas sin dependencia en el ledger.

## S084 — Docker y Compose

**Identidad.** SHA-256 `2a880cf2f640…`, 14.937 bytes/520 líneas. Compose de
desarrollo, Dockerfile multietapa, overrides, redes, volúmenes, endurecimiento,
secretos, arnés aislado para probar instaladores, `.dockerignore` y depuración.

**Valor y cobertura existente.** `delivery-practices/references/delivery-tools.md`
ya fija artefacto inmutable, build frente a runtime, usuario sin privilegios,
readiness/liveness, migraciones y rollback. El delta útil es el **arnés de
instaladores aislado**: el plugin ya prueba su instalador en contenedores Linux
(`python:3.11-slim` y los hashes de evidencia de Codex) sin un contrato escrito.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| Secretos con `secrets:` «(Swarm mode)» | Compose también admite secretos de fichero sin Swarm; preferirlos a `env_file`, que deja valores en `docker inspect` |
| `.env` con `env_file` como opción «GOOD» | Visible en el entorno del proceso y en inspect; solo para desarrollo local |
| Postgres y Redis publicados en `0.0.0.0` en el Compose base | Publicar en `127.0.0.1` o no publicar, como la propia pieza recomienda más abajo |
| Credenciales `postgres:postgres` en la URL | Aceptable solo en desarrollo local aislado; nunca en el fichero base compartido con otros entornos |
| `npm prune --production` | Opción sustituida por `--omit=dev` en npm actual |
| `adduser -S appuser -u 1001` sin `-G appgroup` | El usuario no queda en el grupo que luego usa `--chown` |
| «Containers are ephemeral — all data lost on restart» | Los datos sobreviven a un reinicio; se pierden al eliminar el contenedor |
| «Compose en producción sin orquestador» como antipatrón universal | Depende del contexto; no imponer Kubernetes |
| `docker compose down -v` y `docker system prune` en la lista de depuración | Destructivos sobre recursos ajenos; limitar al proyecto con `-p` y marcarlo |
| Arnés: imagen por digest, UID numérico, repo de solo lectura, copia a `tmpfs`, `network_mode: none`, `cap_drop: ALL`, sin credenciales del host, dry-run por defecto | **Conservar**: coincide con cómo se validan instalador y hooks en esta rama; falta escribirlo como contrato |
| «Un contenedor Linux no valida macOS ni Windows» | **Conservar** literal: es la regla que ya aplica la memoria del proyecto (réplica Linux ≠ Windows) |

**Destino propuesto.** Ampliar `delivery-practices` con una sección «arnés
de pruebas aislado» y una fila de secretos de Compose. Sin skill nueva.

## S085 — Documentación vigente mediante Context7

**Identidad.** SHA-256 `81ad2b5b4acb…`, 4.912 bytes/91 líneas. Resolver el ID
de biblioteca, elegir candidato, consultar como máximo 3 veces y citar versión.

**Valor y cobertura existente.** `research-first` ya exige fuentes originales
con versión fijada, declarar canales inaccesibles sin inferir ausencia y no usar
popularidad ni scores como sustituto de adecuación. Context7 es un canal más,
opcional: está instalado como plugin en este entorno, pero no en todos los runtimes.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| Elegir candidato por «benchmark score» y «reputación» | Contradice research-first: elegir por coincidencia con el paquete y la versión del lockfile del proyecto |
| «Usar en vez de los datos de entrenamiento» siempre | Se activa con cualquier mención a un framework; coste y latencia por pregunta trivial |
| Versión «si el usuario la menciona» | La versión sale del manifiesto o lockfile del proyecto, no solo del mensaje |
| Redactar secretos antes de consultar | **Conservar**: la consulta sale a un servicio externo |
| Tope de 3 llamadas y declarar incertidumbre | **Conservar** |

**Destino propuesto.** Una fila en la tabla de canales de `research-first`:
Context7 como canal opcional, con versión desde el lockfile, redacción previa
y doble comprobación contra la documentación oficial cuando la respuesta cambie
una decisión. Sin skill nueva.

Validación pendiente: lectura de los scripts citados por S083/S084, ejecución
del arnés en un contenedor propio y una consulta Context7 de prueba.
