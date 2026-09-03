---
name: dependency-upgrade
description: >
  Prepara la ACTUALIZACIÓN de dependencias de un proyecto sin tocarlas: inventario DETERMINISTA con
  `deps-inventory.py` (manifiestos package.json · composer.json · requirements*.txt · pyproject.toml
  · go.mod · Gemfile · *.csproj y sus lockfiles; versión declarada y bloqueada; «latest» SOLO del
  `outdated` oficial de npm/composer/pip/go si la herramienta está en PATH — nunca inventado),
  clasifica cada salto en patch/minor/major («major = breaking probable → leer el changelog
  upstream»), lee el changelog/UPGRADING de los major y redacta la `spec.md` de una iniciativa
  «upgrade-<paquete|lote>» con la plantilla del evaluator, para que `evaluator` la presupueste y
  `planner` la planifique. NO actualiza nada por su cuenta y NO busca vulnerabilidades/CVE (eso es
  `nemesis` con la skill `cybersecurity`). Úsala cuando el usuario diga "actualiza las dependencias",
  "qué dependencias están desactualizadas", "prepara el upgrade de <paquete>", "inventario de
  dependencias", "qué breaking changes tiene subir a la versión X", "plan para subir de major".
---

# dependency-upgrade — inventariar, clasificar y especificar el upgrade (no ejecutarlo)

Subir dependencias «a ojo» es la forma más cara de romper un proyecto. Esta skill separa tres cosas
que suelen mezclarse: **qué hay** (inventario determinista), **qué se rompe** (changelog upstream de
cada major) y **qué se decide** (una `spec.md` que `evaluator` presupuesta y `planner` planifica).
El upgrade en sí lo hace `implementer` dentro de la iniciativa, con suites y smoke.

> **Regla.** Ninguna versión sale de la cabeza del modelo. `latest` viene del `outdated` oficial de
> la herramienta; si no está o no hay red, el informe dice `—` y lo avisa. **Esta skill no ejecuta
> `npm update`, `composer update`, `pip install -U` ni `go get -u`.**

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):

```bash
DUSKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/dependency-upgrade' 2>/dev/null | head -1)"
EVALKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/evaluator' 2>/dev/null | head -1)"
python3 "$DUSKILL/scripts/deps-inventory.py" <ruta> [--json] [--no-outdated] [--timeout 60]
```

## Cuándo NO usarla

| Parece esto, pero es… | Pieza correcta |
|---|---|
| «Busca vulnerabilidades / CVE / supply chain en las dependencias» | `nemesis` (skill `cybersecurity`, dimensión dependencias) — aquí se miran **versiones y breaking changes**, no exposición |
| «Sube ya la versión de X y arregla lo que rompa» (ejecutar) | `/dev-cycle` o `quick-implement` sobre la spec que produce esta skill |
| «Este paquete falla al arrancar» | `debug-root-cause` |
| «Mide la salud del código» (duplicados, hotspots) | `code-health` |

## Proceso (3 pasos)

1. **Inventario.** `python3 "$DUSKILL/scripts/deps-inventory.py" . ` (añade `--json` para guardarlo en
   la iniciativa). Lee la cabecera: nº de `major` / `minor` / `patch` / sin `latest`. Si hay avisos
   «`npm` no está en PATH» o «superó N s», el `latest` de ese ecosistema **no existe**: dilo y, si el
   usuario lo quiere, pídele que ejecute la herramienta él (o instale/conecte red) — no lo rellenes.
   Exit 0 siempre; 2 solo por ruta inexistente.
2. **Breaking changes por `major`.** Para cada dependencia marcada `major ⚠️ breaking probable`
   (y las `minor` de frameworks que el usuario señale), localiza su changelog/`UPGRADING`/notas de
   release upstream: con **WebFetch** si está disponible (GitHub releases, `CHANGELOG.md` del repo,
   guía oficial de migración); si no, anótalo como **pendiente de leer** con la URL probable — nunca
   resumas un changelog que no has leído. Registra por paquete: versión actual → destino, breaking
   changes que afectan a ESTE proyecto (grep de los símbolos/APIs citados en el código), y esfuerzo
   relativo (bajo/medio/alto). Lee `references/upgrade-notes.md` **solo al llegar aquí** si dudas
   de qué buscar en un changelog.
3. **Spec de la iniciativa.** Crea `docs/roadmap/<AAAA-MM-DD>-upgrade-<paquete|lote>/spec.md` con la
   plantilla `"$EVALKIT/templates/spec.md"` (`estado: borrador`; misma cadena spec → evaluación →
   plan de la regla 7 de CONVENTIONS) y regístrala en `docs/roadmap/README.md`:
   - **Alcance:** la tabla del inventario (declarada · bloqueada · latest · salto) de lo que entra;
     **fuera de alcance** explícito (lo que se deja para otro lote, y por qué).
   - **Riesgos:** los breaking changes del paso 2 con su fichero afectado; dependencias transitivas
     que arrastra un major (p. ej. subir un framework fuerza a subir sus plugins).
   - **Criterios de aceptación:** `[GWT]` mínimos — suites del proyecto en verde con las versiones
     nuevas; smoke de arranque/build; lockfile regenerado y comiteado; cero versiones «flotantes»
     nuevas; `deps-inventory.py` tras el cambio → esos paquetes en `igual`.
   - Cierra con el **handoff**: «presupuesta con `evaluator`; si es go, planifica con `planner`».
   Un lote razonable: **todos los patch/minor en una iniciativa** y **un major por iniciativa**
   (o por familia: framework + plugins).

## Guardrails

- **Solo lectura del proyecto.** Escribes únicamente `spec.md` (y su fila en el índice del roadmap).
  Nada de `package.json`, lockfiles ni `vendor/`.
- **Herramientas con timeout** (`--timeout`, 60 s): `npm outdated` puede colgarse sin red; el script
  lo convierte en aviso, no en bloqueo.
- **Monorepos:** el script recorre el árbol y agrupa por manifiesto (cada `outdated` corre en la
  carpeta de SU manifiesto); si es enorme, pásale la subcarpeta.
- **`pip list --outdated` mira el entorno activo**, no `requirements.txt`: si el venv no está
  activado o no coincide, el `latest` puede referirse a otro entorno — dilo en la spec.
- **Degradación:** sin `python3` no hay skill; sin herramientas, inventario sin `latest`; sin
  WebFetch, breaking changes «pendientes de leer». El ciclo sigue en los tres casos.

## Qué NO hace

No actualiza dependencias, no regenera lockfiles, no ejecuta tests, no busca CVE ni secretos
(`nemesis`/`cybersecurity`), no estima horas (`evaluator`) ni descompone en tareas (`planner`), y
no promete un `latest` que ninguna herramienta ha devuelto.

## Scripts y referencias

| Fichero | Qué es |
|---|---|
| `scripts/deps-inventory.py` | Inventario MD/JSON: 7 manifiestos + lockfiles, declarada/bloqueada/latest, salto semver, avisos; exit 0 · 2 uso |
| Tests (junto al script; no viajan en el paquete portable) | 11 casos con fixtures de los 7 manifiestos y `outdated` mockeado (ejecutor inyectable): `python3 -m pytest -q skills/dependency-upgrade/scripts` |
| `references/upgrade-notes.md` | Qué buscar en un changelog/UPGRADING y cómo anotar un breaking change (léelo solo en el paso 2) |
