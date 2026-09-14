# Heurística de la Lente C (review-lens-select.py) — detalle

Léelo desde el paso 1 de `SKILL.md` **solo** si un motivo devuelto por `review-lens-select.py` te
sorprende o quieres ajustar `revision.excluir`. El contrato exacto son las constantes `CONTENIDO`/`RUTA_RE`
del script y sus tests (`pytest -q skills/adversarial-review/scripts`); este texto las explica.

Devuelve `lente_c: true|false` + motivos (fichero + patrón). Heurística por **RUTA** (stems anclados
al inicio de un token de la ruta y, los que son prefijo de palabras inocuas, con límite final:
`auth(?!or)`, login, session(s), token(s)¹, oauth, jwt, password, secret(s), crypt, permission(s),
acl¹, rbac¹, cors¹, csrf, upload, payment, billing, docker, nginx, k8s, helm¹; más `.env*`,
`Dockerfile*` y `.github/workflows/` — `authz.py`/`session-context.sh`/`tokens.py`/`token_store.py`
sí; `oracle.py`/`tokenizer.py`/`helmet.py`/`author.md` no (¹ = con límite `(?![a-z])`); la prosa
`.md/.txt/.rst` y `docs/**` no se evalúan por ruta, `tests/**` sí; `"revision": {"excluir": ["hooks/**"]}`
en `dev.json` saca globs de la heurística de ruta —para un repo cuyos hooks se llamen `session-*.sh`—
**sin** sacarlos del escaneo de contenido) y por **CONTENIDO de las
líneas añadidas** del diff (las borradas no cuentan): `eval(`/`exec(`, `subprocess` **solo con
`shell=True` en la misma línea**, `os.system(`/`os.popen(`, `innerHTML`/`dangerouslySetInnerHTML`,
`pickle.loads(`, `yaml.load(`, SQL concatenado o en f-string, `API_KEY`, `PRIVATE KEY`/`BEGIN RSA`,
`Authorization:`, `Set-Cookie`. La prosa, `docs/**`, los tests y las fixtures no se escanean por
contenido (contienen payloads a propósito); los binarios se saltan. Configurable en
`.claude/dev.json` → `"revision": {"lenteSeguridad": "auto" | "siempre" | "nunca", "excluir": ["glob", …]}`
(default `auto`, sin exclusiones; `/setup` paso 5-ter pregunta el modo; `excluir` es ajuste manual).
El script nunca bloquea: ante error avisa por stderr y devuelve `false`. La lista exacta de patrones
es el contrato: `CONTENIDO`/`RUTA_RE` en el propio script, con sus tests.


## Tercera heurística: FLUJO de texto del consumidor hacia un prompt (T-18, hueco E4)

Las dos heurísticas de arriba miran **patrones de código peligroso** y **stems de ruta**. Ninguna ve
**flujo de datos**, y ese hueco tiene un caso real medido: en `project-specialization` F1 el diff
abrió un canal desde `.claude/personas/<tipo>.md` (texto que escribe el CONSUMIDOR del plugin) hacia
el brief que lee un modelo, y `review-lens-select.py` devolvió `lente_c: false` **las tres veces**.
Lo cazó la Lente B en las tres. Una lente que depende de que otra haga su trabajo no es una puerta.

**Qué detecta** — una **conjunción de dos condiciones**, nunca una sola:

1. El diff **añade** una línea que nombra una **fuente de texto del consumidor** —`.claude/**` (con
   barra o como componente entrecomillado de un `os.path.join`), `dev.json`, `personas/`,
   `CONTINUE-HERE*`, `docs/knowledge/**`— **y** esa línea, o alguna de las **8 líneas añadidas
   siguientes del mismo fichero**, **lee** (`open(`, `read_text(`, `.read(`, `json.load`,
   `readFileSync(`, `glob.`, `os.listdir(`, `loads(`). Nombrar una ruta en un mensaje de error o en
   un comentario no abre ningún canal, y por eso la lectura es obligatoria.
2. El fichero **compone texto para un modelo**: lo dice su **nombre** (`brief`, `prompt`,
   `persona`) o su **cabecera** —docstring de módulo, o frontmatter e introducción si es un `.md`
   de pieza—, y ahí no basta mencionar la palabra: tiene que decir que **compone o entrega** ese
   texto a un modelo, o lanzar `claude -p`. Los ficheros de **datos** (`.json`, `.yml`, `.toml`…)
   quedan fuera: no componen nada, los compone quien los lee.

**Qué corpus se mira.** El código que ya se escaneaba **más los `.md` de pieza** (`agents/`,
`commands/`, `skills/`, `hooks/`, `agent-kits/`). En este plugin los prompts **son prosa**, así que
el canal «texto del consumidor → modelo» se abre escribiendo una frase, no un `open(` — y con el
corpus anterior, que excluía toda la prosa, era invisible: la misma clase de canal que el caso F1
que justifica esta heurística. En un `.md` la lectura se reconoce además por el **verbo** (`lee`,
`carga`, `antepón`, `inyecta`…), no solo por la llamada. Fuera del corpus quedan el **registro**
(`docs/roadmap/**`, el journal), que no es una pieza sino la bitácora de un proyecto, y la
documentación **de esta misma skill**: `lens-c-heuristics.md` explica el canal que la heurística
busca, así que se dispararía consigo misma cada vez que alguien la editara. Es la misma
auto-inmunidad que ya protege al código del selector, aplicada a su prosa.

**Lo que costaba no acotar la condición 2** (gap B-1 de la revisión de R4b): con la primera
redacción —cualquier mención de `brief`/`prompt`/`persona`/`system`, más `'-p'` de argparse—
quedaban clasificados como «compone un prompt» **67 de los 139** ficheros escaneables del repo
(48 %), incluidos los 18 `evals/cases/*.json` y `plugin.json`. Una condición que se cumple en la
mitad del árbol no acota nada: convierte la conjunción en la heurística de fuente a secas. Con la
redacción de arriba son **6 de 139** (4 %), y los seis componen un prompt de verdad
(`task-brief.py`, `journal.py`, `evals/run.py`, `headless.yml`, `session-journal.sh`,
`user-prompt-capture.sh`).

**Qué NO detecta, y por qué.** Sin la condición 2 esto avisaría de **cualquier** script que lea
`dev.json`, que son casi todos los del plugin: sería un aviso perpetuo, que es la forma más rápida de
que una puerta deje de leerse. Por eso la condición 2 mira **solo el nombre y la cabecera**, nunca el
cuerpo: un script que se limite a *mencionar* «prompt» o «persona» en una constante —este mismo
`review-lens-select.py`, sin ir más lejos— no cuenta como compositor. Tampoco detecta el flujo que
pasa por variables intermedias a lo largo de un fichero, ni el que cruza de un fichero a otro: esto es
una heurística de **proximidad** sobre líneas añadidas, no un análisis de taint. Un flujo repartido en
tres funciones se le escapa, y lo asume.

**Forma de la salida.** Un motivo nuevo con **`tipo: "flujo"`** —valor nuevo del campo `tipo` que ya
existía, no una clave ni un flag nuevos— con `fichero`, `linea` y `patron`. La forma del `--json` y la
lista de flags no cambian.

**Cómo se apaga.** Con la **misma** válvula que las otras dos, no con una nueva: `revision.excluir`
saca el fichero de la heurística de flujo igual que de la de ruta, y `revision.lenteSeguridad: nunca`
apaga la Lente C entera. Los motivos de flujo se concatenan a los de patrón **antes** de decidir,
precisamente para que la válvula no se duplique.

**Tasa de disparo medida** (ficheros declarados en los `Archivos` de los **últimos 5 ledgers**,
antes/después del cambio, re-medida con el corpus ampliado a los `.md` de pieza): **ningún ledger
pasa de `false` a `true`**. Dos de ellos (`plugin-refactor`, `project-specialization`) ganan **4**
motivos de flujo cada uno, pero ya estaban en `true` por la heurística de ruta;
`usage-meter-transcripts` sigue en `false` e `installer-registro-real` sigue en `true` sin motivos
de flujo. El criterio de T-18 era «sube como máximo un ledger».

**El contrato exacto** son las constantes `FUENTE_CONSUMIDOR_RE`, `LECTURA_RE`, `LECTURA_PROSA_RE`,
`NOMBRE_PROMPT_RE`, `CABECERA_PROMPT_RE`, `EXT_DE_DATOS`, `PIEZA_MD_RE`, `AUTOINMUNE_RE` y
`VENTANA_FLUJO` del script, con sus cuatro tests (el fixture del caso F1 y los tres negativos:
lectura de `.claude/**` en un fichero que no compone prompt · fichero de prompt sin texto del
consumidor · `revision.excluir` apagándolo).
