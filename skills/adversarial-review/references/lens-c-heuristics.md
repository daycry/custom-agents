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
