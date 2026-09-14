#!/usr/bin/env python3
"""
coverage-check.py — puerta de COBERTURA criterios↔tests del agente qa.

Cruza el ledger `tasks.md` (campo «Cubre (tests)» de cada tarea) con el
`test-plan.md` (bloques E2E-xx / M-xx / API-xx / A11Y-xx) y detecta:

ERRORES (exit 1):
  - Referencias rotas: una tarea declara «Cubre (tests): E2E-03» pero ese
    bloque no existe en el test-plan.
  - Criterios [GWT] sin cubrir (con <spec.md>): un criterio Given/When/Then
    `- [ ] [GWT] CA-XX — …` de la spec promete comportamiento testeable; si su
    ID CA-XX no aparece en el test-plan, es cobertura que FALTA (no opcional).
AVISOS (informativos; qa los triagea — las tareas sin UI no necesitan cobertura):
  - Tareas sin cobertura declarada (campo vacío o «—»).
  - Bloques del test-plan que ninguna tarea referencia (posible test huérfano).
  - Criterios [GWT] sin ID CA-XX (sin ID no hay trazabilidad; añádelo).

Salida: informe por stdout (para el report.md de qa) + resumen JSON final.
Uso:
  python3 coverage-check.py <tasks.md> <test-plan.md> [spec.md]
Si el test-plan no existe: exit 0 con aviso (iniciativa sin UI; la puerta no
aplica) — SALVO que la spec traiga criterios [GWT]: esos prometen test, así
que sin test-plan cuentan como sin cubrir (exit 1).

Marcador `test-plan: n/a (sin UI)` (C-08, hueco E1): si el `improvement-plan.md`
de la MISMA carpeta lo declara en su frontmatter, la ausencia de test-plan es
una DECISIÓN, no un olvido: la salida lo dice y NO pide regenerarlo con
`planner` (era la contradicción E1: `planner` genera el test-plan «si hay UI» y
`qa` sin él pedía regenerarlo, en bucle). Sin el marcador y sin test-plan, el
aviso es UNO y trae el comando que lo fija.

Con el marcador, los criterios [GWT] de la spec NO fuerzan exit 1: sin UI no hay
E2E que los cubra y su evidencia es el campo `Verificación` de la tarea que los
cierra en `tasks.md`. No se silencian: se listan en una línea informativa (y en
`test_plan_na` del JSON) para que la revisión pueda cazar un marcador puesto
para esquivar la puerta. Sin marcador, un [GWT] sin test-plan sigue siendo
exit 1, como siempre.

La línea del marcador es **ℹ️, nunca ✅** (gap R4a-2): un ✅ se lee como «cobertura
comprobada» en el informe de qa y aquí no se ha comprobado cobertura ninguna, se
ha aceptado una declaración. Y lo que queda sin comprobar se LISTA siempre: los
criterios [GWT] si los hay, si no los criterios `CA-XX` de la spec, si no las
tareas del ledger, y si no hay nada que listar lo dice con esas palabras. Solo los
[GWT] estaban EXIGIDOS por la puerta: el resto se lista «para la revisión», que no
es lo mismo que eximir (gap R4a-22; `eximidos_exigidos` en el JSON lo distingue).

Rutas con pinta de interfaz (gap R4a-19): se miran el **diff** (`git diff --name-only`
contra la misma base que `scope-check.py`, más `git status`) Y los campos `Archivos`
del ledger, y la salida dice de dónde salió cada ruta. El diff es imprescindible: lo
EXCLUIDO por `scope-check` —por defecto o por `alcance.excluir` de `dev.json`— está
en el diff y NO en `Archivos`, así que mirando solo el ledger el caso que
`agents/qa.md` manda cazar (marcador «sin UI» sobre un diff con `.tsx`/`components/`)
era invisible: con `excluir: ["src/components/**"]` las dos puertas salían 0 y
`rutas_ui` vacía. Sin git (o sin base determinable) se degrada a `Archivos`
DICIÉNDOLO, nunca en silencio — y también lo dice cuando la base resuelta es `HEAD`
o el diff no aporta ficheros: ahí la fuente «diff» no ha aportado nada, y afirmar
lo contrario con `rutas_ui_degradado: null` era la misma degradación silenciosa por
otra puerta (gap R4a-30).
"""
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

TEST_ID = re.compile(r"\b((?:E2E|M|API|A11Y)-\d+)\b", re.I)
# criterio G/W/T de la spec: "- [ ] [GWT] CA-01 — Dado…" — tolerante: viñeta -/*,
# checkbox marcado o no, [GWT] en cualquier caja, ID opcionalmente en **negrita**
GWT_RE = re.compile(
    r"^\s*[-*]\s*\[[ xX]\]\s*\[GWT\]\s*(?:\*\*)?(CA-\d+)?(?:\*\*)?", re.M | re.I)


def _sin_fences(text):
    """Quita bloques de código cercados (```/~~~): un ejemplo de criterio [GWT]
    dentro de documentación no debe contar como criterio real."""
    out, en_fence = [], False
    for ln in text.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            en_fence = not en_fence
            continue
        if not en_fence:
            out.append(ln)
    return "\n".join(out)


# Marcador C-08 (E1). Literal ÚNICO en las cinco piezas (`agents/planner.md`,
# `commands/dev-cycle.md`, `agents/qa.md`, la plantilla del planner y este script): cambiarlo en
# una sola rompe la cadena sin que nada lo vea.
MARCADOR_SIN_UI = "test-plan: n/a (sin UI)"
# Clave de PRIMER NIVEL (sin sangría: en YAML, ` test-plan:` anidado es `plan.test-plan`, otra
# cosa), valor opcionalmente entrecomillado (`"n/a (sin UI)"` es YAML válido y equivalente) y
# ANCLADO al final salvo comentario YAML: sin ancla, `test-plan: n/a (sin UI) — pero hay UI`
# eximía igual (gap R4a-7).
# Forma CANÓNICA: EXACTAMENTE el literal `test-plan: n/a (sin UI)` — clave en minúsculas, UN solo
# espacio tras los dos puntos y el valor sin comillas. Es la única forma que encuentra un
# `grep -F "test-plan: n/a (sin UI)"`, que es el criterio con el que se declaró canónica, y la que
# escriben las 5 piezas. `re.I` y el `[ \t]*` dejaban pasar `Test-Plan:`, `N/A (SIN UI)` y
# `test-plan:n/a (sin UI)` (gap R4a-23); el `[ \t]+` con comillas opcionales dejaba pasar el
# tabulador, el doble espacio y las dos formas entrecomilladas, que tampoco las encuentra el `grep`
# y aquí salían como canónicas SIN aviso (gap R4a-31). Todas ellas siguen eximiendo por la regex
# LAXA —no romper un plan que ya pasaba— pero con AVISO.
MARCADOR_RE = re.compile(
    r"""^test-plan: n/a \(sin UI\)[ \t]*(?:\#[^\n]*)?$""", re.M)
MARCADOR_RE_LAXO = re.compile(
    r"""^test-plan[ \t]*:[ \t]*(?P<q>["'])?n/a[ \t]*\(sin UI\)(?(q)(?P=q))[ \t]*(?:\#[^\n]*)?$""",
    re.M | re.I)

# Rutas con pinta de interfaz: si el diff o el alcance declarado las tocan, un marcador «sin UI»
# es sospechoso y sale un ⚠️ (gaps R4a-2 y R4a-19). Lista ampliada en R4a-26: `.astro`, `.twig`,
# `.svg`, `assets/`, `web/` y `components` como NOMBRE de fichero (`src/components.ts`).
# Acotada en R4a-31/R4a-36, porque cada falso positivo es un gap que el revisor tiene que desmontar:
#   - los tokens de CARPETA exigen barra detrás (`public/`, `assets/`): un fichero sin extensión
#     llamado `public` o `assets` no es una vista;
#   - `web` solo cuenta en la RAÍZ (`^web/`): `tests/fixtures/web/a.json` y
#     `infra/terraform/web/main.tf` son datos de prueba e infraestructura, no interfaz;
#   - `components.<ext>` no cuenta si la extensión es de CONFIGURACIÓN (`components.json` de
#     shadcn/ui es un fichero de config, no un componente); `src/components.ts` sigue contando.
UI_PISTAS = re.compile(
    r"(\.(tsx|jsx|vue|svelte|astro|twig|html|htm|css|scss|sass|less|svg)\b"
    r"|(^|/)(components?|pages?|views?|ui|frontend|front-end|webapp|templates?|public|static|"
    r"screens?|layouts?|styles?|assets|e2e)/"
    r"|^web/"
    r"|(^|/)components?\.(?!json|ya?ml|toml|lock|cfg|ini|conf)\w+$"
    r"|playwright|cypress|selenium|storybook)", re.I)


# La MISMA regex, pero solo con las ramas que NO dependen del nombre de una carpeta: extensión de
# vista, `components.<ext>` como nombre de fichero y herramienta de E2E. Sirve para saber si la
# pista viene SOLO del directorio, que es el caso que hay que acotar (gap B4-4).
UI_PISTAS_NO_DIR = re.compile(
    r"(\.(tsx|jsx|vue|svelte|astro|twig|html|htm|css|scss|sass|less|svg)\b"
    r"|(^|/)components?\.(?!json|ya?ml|toml|lock|cfg|ini|conf)\w+$"
    r"|playwright|cypress|selenium|storybook)", re.I)

# Extensiónes que pueden ser interfaz cuando la ÚNICA pista es la carpeta (gap B4-4): vistas,
# plantillas de servidor y código de cliente. Un `db/views/v.sql`, un `templates/mail.json`, un
# `static/datos.csv`, un `assets/fuente.ttf`, un `screens/README.json` o un `e2e/datos.csv` caen
# todos en carpetas de la lista y NINGUNO es una vista: son datos, configuración o binarios, y el
# caso más realista —el backend puro— es justo quien declara «sin UI» y tenía que desmontar el
# falso positivo a mano. Lista PERMISIVA a propósito: fuera de ella, el aviso no salta.
EXT_INTERFAZ = frozenset("""
tsx jsx vue svelte astro twig html htm xhtml css scss sass less styl
js mjs cjs ts mts cts coffee
php erb haml slim hbs handlebars mustache pug jade ejs liquid njk jinja jinja2 j2 blade tpl mjml
razor cshtml vbhtml aspx jsp marko riot elm dart swift kt xaml storyboard xib
""".split())

_EXT_RE = re.compile(r"\.([A-Za-z0-9_]+)$")


def _parece_ui(tok, root=None):
    """¿Este token tiene pinta de interfaz?

    Los documentos (`.md`, `.txt`) NO cuentan por el nombre de su carpeta: un
    `agent-kits/planner/templates/improvement-plan.md` es una plantilla de texto, no una vista
    (falso positivo real de este mismo repo). Para un documento haría falta una pista de
    extensión, que por definición no tiene.

    Cuando la pista viene SOLO de la carpeta, dos correcciones más:

    - **Carpeta sin barra al final de la ruta** (gap B4-3): `src/components` o `frontend` son la
      forma que `scope-check.casa()` soporta a propósito para declarar una carpeta, y exigir la
      barra las dejaba fuera (falso NEGATIVO: con la fuente «diff» degradada, la puerta callaba).
      Se resuelve como lo resuelve `casa()`: preguntando al sistema de ficheros. Si `root` dice que
      el token ES un directorio, cuenta como carpeta; si no —un fichero sin extensión llamado
      `public` o `assets`, el falso positivo que cerró R4a-36—, sigue sin contar.
    - **Extensión también de interfaz** (gap B4-4): con la carpeta como única pista, la extensión
      tiene que estar en `EXT_INTERFAZ`. Sin extensión ninguna (la carpeta declarada), cuenta.
    """
    if not tok or " " in tok:
        return False
    if re.search(r"\.(md|markdown|txt|rst)$", tok, re.I):
        return False
    if UI_PISTAS_NO_DIR.search(tok):
        return True                       # extensión de vista, `components.<ext>` o herramienta E2E
    cand = tok
    if not tok.endswith("/") and root and os.path.isdir(os.path.join(root, tok)):
        cand = tok + "/"                  # carpeta declarada sin barra (gap B4-3, como `casa()`)
    if not UI_PISTAS.search(cand):
        return False
    m = _EXT_RE.search(os.path.basename(cand.rstrip("/")))
    return m is None or m.group(1).lower() in EXT_INTERFAZ


def _scope_check_mod():
    """El módulo `agent-kits/shared/scope-check.py` (helpers de git), o None si no se puede cargar.

    Se importa en vez de re-implementar `git diff`: la base del diff tiene que ser LA MISMA que la
    de la puerta de alcance (merge-base con main/master, o HEAD en la rama principal), y duplicar
    esa escalera aquí sería una copia más que mantener."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared", "scope-check.py")
    if not os.path.isfile(ruta):
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_scope_check_helpers", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 — es una mejora del aviso, nunca puede tumbar la puerta
        return None


# El consejo «pasa `--base <ref>`» viene de `scope-check.py`, que SÍ acepta ese flag; reenviarlo tal
# cual mandaba al usuario a escribir un flag que `coverage-check.py` no tiene (gap R4a-35).
_CONSEJO_BASE_AJENO = re.compile(r"\s*[—-]?\s*pasa\s+`--base[^\n]*", re.I)


def rutas_del_diff(tasks_path):
    """(rutas cambiadas según git, motivo de degradación|None) con la base de `scope-check.py`.

    Nunca lanza: si no hay git, no hay base determinable o no se pueden cargar los helpers,
    devuelve ([], motivo) y quien llama lo DICE en la salida.

    El motivo no es solo para los fallos duros (gap R4a-30): cuando la base resuelta es `HEAD` —rama
    principal, donde `scope-check` mira solo lo que no está comiteado— o cuando el diff contra la
    base no aporta NINGÚN fichero, la fuente «diff» no ha aportado nada y hay que decirlo. Devolver
    `None` ahí afirmaba que no hubo degradación, y «no he mirado el diff» no es lo mismo que «he
    mirado y no hay interfaz»: `qa` daba por inspeccionado un diff que nadie miró."""
    mod = _scope_check_mod()
    if mod is None:
        return [], "no se han podido cargar los helpers de git de scope-check.py"
    partida = os.path.dirname(os.path.abspath(tasks_path)) or "."
    try:
        root = mod.repo_root(partida)
        if not root:
            # TRES causas distintas con remedios distintos (gaps R4a-34 y B4-2): sin git, sin
            # repositorio, y el repositorio que SÍ está pero cuyo `git rev-parse` falla (config
            # rota, `safe.directory`, repo corrupto), donde el diagnóstico es el stderr de git que
            # aquí se tragaba. `motivo_sin_repo` y `git_disponible` pueden no existir en un kit
            # viejo, así que se preguntan con tolerancia y se cae al mensaje de dos causas
            motivo = getattr(mod, "motivo_sin_repo", None)
            if callable(motivo):
                return [], motivo(partida)
            hay_git = getattr(mod, "git_disponible", lambda: True)()
            return [], ("esto no es un repositorio git" if hay_git else
                        "no hay `git` en el PATH (no es que falte el repositorio: falta git)")
        base, desc = mod.resolver_base(root, None)
        cambiados = list(mod.ficheros_cambiados(root, base))
        if base == "HEAD":
            return cambiados, (
                f"la base del diff es «{desc}», así que el diff no aporta ficheros: solo se han "
                "mirado los cambios sin comitear")
        del_diff = [ln.strip() for ln in
                    mod.git(root, "diff", "--name-only", base, "HEAD").splitlines() if ln.strip()]
        if not del_diff:
            return cambiados, (f"el diff contra la base «{desc}» no aporta ningún fichero: solo se "
                               "han mirado los cambios sin comitear")
        return cambiados, None
    except Exception as e:  # noqa: BLE001 — sin base clara (ni main ni master), git roto, …
        motivo = _CONSEJO_BASE_AJENO.sub("", str(e)).strip().rstrip(".—- ")
        return [], (f"sin base de diff determinable ({motivo}); `coverage-check.py` no acepta "
                    "`--base`: declara en el campo `Archivos` de su tarea los ficheros que quieras "
                    "que se miren")


def _raiz_del_repo(tasks_path):
    """Raíz del repositorio, o None. Solo para resolver si un token declarado es una CARPETA
    (gap B4-3, `_parece_ui`): sin raíz, la pregunta al sistema de ficheros no se hace y el token
    sin barra sigue sin contar. Nunca lanza."""
    mod = _scope_check_mod()
    if mod is None or tasks_path is None:
        return None
    try:
        return mod.repo_root(os.path.dirname(os.path.abspath(tasks_path)) or ".")
    except Exception:  # noqa: BLE001 — es una mejora de la pista, nunca puede tumbar la puerta
        return None


def rutas_con_pinta_de_ui(tasks_text, tasks_path=None):
    """(rutas con pinta de interfaz, {ruta: origen}, motivo de degradación|None).

    Mira DOS fuentes y dice de cuál salió cada ruta (`diff`, `ledger` o `diff+ledger`):
      - el **diff** (`git diff --name-only` contra la base de `scope-check.py` ∪ `git status`),
      - los tokens de los campos `- **Archivos**:` del ledger (el alcance declarado).
    El diff no es redundante con el ledger: lo EXCLUIDO por `scope-check` (por defecto o por
    `alcance.excluir`) está en el diff y no en `Archivos`, y es justo ahí donde se escondía el caso
    que hay que cazar (gap R4a-19). Sin git —o con una base que no aporta diff, como `HEAD` en la
    rama principal— se degrada al ledger con el motivo, nunca en silencio (gap R4a-30).
    """
    del_ledger = []
    raiz = _raiz_del_repo(tasks_path)
    for ln in tasks_text.splitlines():
        if not re.match(r"^\s*-\s*\*\*Archivos\*\*\s*:", ln):
            continue
        for tok in re.findall(r"`([^`\n]+)`", ln.split(":", 1)[1]):
            tok = tok.strip().replace("\\", "/")
            if _parece_ui(tok, raiz) and tok not in del_ledger:
                del_ledger.append(tok)
    if tasks_path is None:
        del_diff, degradado = [], "no se ha mirado el diff (sin ruta del ledger)"
    else:
        del_diff, degradado = rutas_del_diff(tasks_path)
    del_diff = [f.replace("\\", "/") for f in del_diff]
    del_diff = [f for f in del_diff if _parece_ui(f, raiz)]
    origen = {}
    for f in del_diff:
        origen[f] = "diff"
    for f in del_ledger:
        origen[f] = "diff+ledger" if f in origen else "ledger"
    return sorted(origen), origen, degradado


def que_se_exime(tasks_text, spec_path, gwt_ids):
    """(qué se está eximiendo, lista de ids) para la línea de trazabilidad del marcador.

    Escalera: criterios [GWT] de la spec → criterios `CA-XX` de la spec → tareas del ledger →
    nada que listar. Nunca devuelve una lista vacía sin decir por qué (gap R4a-2).

    OJO con la palabra: solo el primer peldaño estaba EXIGIDO por la puerta (lo único que fuerza
    exit 1 es un `[GWT]` sin cubrir). Los `CA-XX` no-[GWT] y las `T-XX` no estaban sujetos a nada,
    así que ahí no se exime: se LISTAN para la revisión (gap R4a-22). Quien llama distingue los
    dos casos mirando `gwt_ids`."""
    if gwt_ids:
        return "criterio(s) [GWT] de la spec", list(gwt_ids)
    if spec_path and os.path.isfile(spec_path):
        texto = _sin_fences(open(spec_path, encoding="utf-8-sig", errors="replace").read())
        cas = []
        for m in re.finditer(r"^\s*[-*]\s*\[[ xX]\]\s*(?:\*\*)?(CA-\d+)", texto, re.M):
            if m.group(1).upper() not in cas:
                cas.append(m.group(1).upper())
        if cas:
            return "criterio(s) de aceptación de la spec (ninguno [GWT])", cas
    tareas = []
    for m in re.finditer(r"^###\s+(T-\d+)\b", tasks_text, re.M):
        if m.group(1) not in tareas:
            tareas.append(m.group(1))
    if tareas:
        return "tarea(s) del ledger (la spec no aporta criterios rastreables)", tareas
    return "", []


def sin_ui_declarado(tasks_path):
    """¿El `improvement-plan.md` de la carpeta de la iniciativa declara `test-plan: n/a (sin UI)`
    en su frontmatter? Devuelve (bool, ruta_del_plan|None, línea no canónica|None). Nunca lanza."""
    plan = os.path.join(os.path.dirname(os.path.abspath(tasks_path)), "improvement-plan.md")
    if not os.path.isfile(plan):
        return False, None, None
    try:
        # utf-8-sig: un BOM al principio del plan anulaba el marcador en silencio (gap R4a-8)
        with open(plan, encoding="utf-8-sig", errors="replace") as fh:
            texto = fh.read()
    except OSError:
        return False, None, None
    # solo el frontmatter: el marcador citado en la prosa del plan no decide nada.
    # El cierre `---` puede ser el FIN DEL FICHERO sin salto final: sin `(?:\r?\n|\Z)` la cabecera
    # salía vacía y el marcador desaparecía en silencio (exit 0 declarado → exit 1; gap R4a-24).
    m = re.match(r"^---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", texto, re.S)
    cabecera = m.group(1) if m else ""
    if MARCADOR_RE.search(cabecera):
        return True, plan, None
    laxo = MARCADOR_RE_LAXO.search(cabecera)
    if laxo:
        # se acepta (no romper un plan que ya pasaba) pero se avisa: escrito así, el `grep` con el
        # que el resto de la cadena busca el literal NO lo encuentra (gap R4a-23)
        return True, plan, laxo.group(0).strip()
    return False, plan, None


def gwt_criteria(spec_path):
    """(ids CA-XX de criterios [GWT], nº de [GWT] sin ID) de la spec; ([], 0) si no hay."""
    if not spec_path or not os.path.isfile(spec_path):
        return [], 0
    text = _sin_fences(open(spec_path, encoding="utf-8-sig", errors="replace").read())
    ids, sin_id = [], 0
    for m in GWT_RE.finditer(text):
        if m.group(1):
            ids.append(m.group(1).upper())
        else:
            sin_id += 1
    return ids, sin_id


def main():
    if len(sys.argv) not in (3, 4):
        print("uso: coverage-check.py <tasks.md> <test-plan.md> [spec.md]")
        sys.exit(1)
    tasks_path, plan_path = sys.argv[1], sys.argv[2]
    spec_path = sys.argv[3] if len(sys.argv) == 4 else None
    gwt_ids, gwt_sin_id = gwt_criteria(spec_path)

    if not os.path.isfile(tasks_path):
        print(f"❌ no existe {tasks_path}")
        sys.exit(1)
    # se calcula SIEMPRE: `test_plan_na` es una clave del contrato del --json en las cuatro ramas
    # de salida, no solo en las dos sin test-plan (gap R4a-9)
    sin_ui, plan_md, marcador_no_canonico = sin_ui_declarado(tasks_path)
    if marcador_no_canonico:
        print(f"⚠️  el marcador del plan («{marcador_no_canonico}») NO está en la forma canónica "
              f"«{MARCADOR_SIN_UI}»: se acepta, pero escrito así el `grep` del literal con el que "
              "el resto de la cadena lo busca no lo encuentra — corrígelo en improvement-plan.md")
    if not os.path.isfile(plan_path):
        if gwt_ids and not sin_ui:
            # los [GWT] prometen test: sin test-plan, son cobertura que falta
            for cid in gwt_ids:
                print(f"❌ {cid}: criterio [GWT] de la spec sin test-plan que lo cubra")
            print(json.dumps({"applies": True, "broken_refs": 0,
                              "tasks_sin_cobertura": [], "tests_sin_referencia": [],
                              "gwt_cubiertos": [], "gwt_sin_cubrir": gwt_ids,
                              "gwt_sin_id": gwt_sin_id, "test_plan_na": False,
                              "marcador_no_canonico": marcador_no_canonico}, ensure_ascii=False))
            sys.exit(1)
        if gwt_sin_id:
            # prometen test pero sin ID no se pueden rastrear: avisar, no silenciar
            print(f"⚠️  {gwt_sin_id} criterio(s) [GWT] sin ID CA-XX en la spec y sin "
                  "test-plan: prometen test pero no son rastreables (añade IDs y test-plan)")
        if sin_ui:
            # DECISIÓN declarada, no olvido: ni se pide regenerar nada (hueco E1). ℹ️ y NO ✅: no
            # se ha comprobado cobertura, se ha aceptado una declaración (gap R4a-2)
            print(f"ℹ️  {MARCADOR_SIN_UI} declarado en {os.path.basename(plan_md)}: iniciativa sin "
                  "UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)")
            tasks_text = open(tasks_path, encoding="utf-8-sig", errors="replace").read()
            que, ids = que_se_exime(tasks_text, spec_path, gwt_ids)
            eximidos = ids
            # «eximir» solo vale para lo que la puerta EXIGÍA: los [GWT]. Lo demás se lista para la
            # revisión, que es otra cosa y más floja (gap R4a-22)
            exigidos = bool(gwt_ids)
            if ids and exigidos:
                # no se silencian: se dice QUÉ se exime y DÓNDE se verifica, para que la revisión
                # pueda cazar un marcador puesto para esquivar la puerta
                print(f"ℹ️  se eximen {len(ids)} {que} ({', '.join(ids)}): su evidencia es el campo "
                      "`Verificación` de la tarea que los cierra en tasks.md (ejecutado y pegado "
                      "por implementer), no un E2E")
            elif ids:
                print(f"ℹ️  se listan para la revisión {len(ids)} {que} ({', '.join(ids)}): la "
                      "puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que "
                      "aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea "
                      "que los cierra en tasks.md")
            else:
                print("ℹ️  no hay nada que listar: ni la spec trae criterios con ID ni el ledger "
                      "tiene tareas `### T-XX` (si esperabas ver algo aquí, revisa la spec)")
            ui, ui_origen, ui_degradado = rutas_con_pinta_de_ui(tasks_text, tasks_path)
            if ui_degradado:
                print(f"⚠️  no se ha podido mirar el DIFF entero ({ui_degradado}): la búsqueda de "
                      "rutas de interfaz se apoya en el alcance declarado en los campos `Archivos` "
                      "(más lo que haya sin comitear), que NO incluye lo que scope-check excluye — "
                      "un `.tsx` excluido no se vería aquí")
            if ui:
                detalle = ", ".join(f"{f} [{ui_origen[f]}]" for f in ui[:5])
                print(f"⚠️  hay {len(ui)} ruta(s) con pinta de interfaz "
                      f"({detalle}{'…' if len(ui) > 5 else ''}) y el plan declara "
                      f"«{MARCADOR_SIN_UI}»: o el marcador sobra, o esas rutas no son UI — dilo en "
                      "el ledger antes de que la revisión lo pregunte "
                      "([diff] = fichero cambiado, [ledger] = campo `Archivos`)")
        else:
            eximidos, ui, ui_origen, ui_degradado, exigidos = [], [], {}, None, False
            print("⚠️  sin test-plan.md: la puerta de cobertura no aplica (iniciativa sin UI). "
                  "Si es por diseño, declara `" + MARCADOR_SIN_UI + "` en el frontmatter de "
                  "improvement-plan.md y este aviso desaparece; si la iniciativa SÍ tiene UI, "
                  "genera el test-plan con `planner`")
        print(json.dumps({"applies": False, "gwt_sin_id": gwt_sin_id, "test_plan_na": sin_ui,
                          "marcador_no_canonico": marcador_no_canonico,
                          "eximidos": eximidos, "eximidos_exigidos": exigidos,
                          "rutas_ui": ui, "rutas_ui_origen": ui_origen,
                          "rutas_ui_degradado": ui_degradado}, ensure_ascii=False))
        sys.exit(0)

    plan = open(plan_path, encoding="utf-8", errors="replace").read()
    defined = set()
    for m in re.finditer(r"^#{2,4}\s*.*?\b((?:E2E|M|API|A11Y)-\d+)\b", plan, re.M | re.I):
        defined.add(m.group(1).upper())
    # también acepta "**E2E-01**", primera celda de tabla "| E2E-01 |" y listas "- E2E-01"
    for m in re.finditer(r"\*\*((?:E2E|M|API|A11Y)-\d+)\*\*", plan, re.I):
        defined.add(m.group(1).upper())
    for m in re.finditer(r"^\|\s*((?:E2E|M|API|A11Y)-\d+)\s*\|", plan, re.M | re.I):
        defined.add(m.group(1).upper())
    for m in re.finditer(r"^\s*[-*]\s*((?:E2E|M|API|A11Y)-\d+)\b", plan, re.M | re.I):
        defined.add(m.group(1).upper())

    tasks = open(tasks_path, encoding="utf-8", errors="replace").read()
    task_re = re.compile(r"^###\s+(T-\d+)[^\n]*", re.M)
    cubre_re = re.compile(r"^\s*-\s*\*\*Cubre \(tests\)\*\*\s*:\s*(.*)$", re.M)

    # trocear por tarea
    positions = [(m.start(), m.group(1)) for m in task_re.finditer(tasks)]
    errors, sin_cobertura, referenced = [], [], set()
    if not positions:
        print("❌ no se han detectado tareas `### T-XX` en tasks.md — la puerta no puede validar cobertura")
        print(json.dumps({"applies": True, "broken_refs": 0, "no_tasks": True,
                          "test_plan_na": sin_ui,
                          "marcador_no_canonico": marcador_no_canonico}, ensure_ascii=False))
        sys.exit(1)
    for i, (pos, tid) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(tasks)
        chunk = tasks[pos:end]
        m = cubre_re.search(chunk)
        if not m:
            sin_cobertura.append(tid)
            continue
        val = m.group(1).strip()
        ids = [i.upper() for i in TEST_ID.findall(val)]
        if not ids:
            sin_cobertura.append(tid)
            continue
        for t in ids:
            referenced.add(t)
            if t not in defined:
                errors.append(f"{tid}: referencia rota — «{t}» no existe en el test-plan")

    unreferenced = sorted(defined - referenced)

    # criterios [GWT] de la spec: su CA-XX debe aparecer en el test-plan (cualquier forma:
    # encabezado, **CA-01**, celda de tabla, lista o mención plana — prometen test 1:1)
    gwt_sin_cubrir = [cid for cid in gwt_ids
                      if not re.search(rf"\b{cid}\b", plan, re.I)]
    gwt_cubiertos = [cid for cid in gwt_ids if cid not in gwt_sin_cubrir]

    for tid in sin_cobertura:
        print(f"⚠️  {tid}: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)")
    for t in unreferenced:
        print(f"⚠️  {t}: ningún «Cubre (tests)» lo referencia (¿test huérfano?)")
    if gwt_sin_id:
        print(f"⚠️  {gwt_sin_id} criterio(s) [GWT] sin ID CA-XX en la spec (sin ID no hay trazabilidad)")
    for cid in gwt_sin_cubrir:
        print(f"❌ {cid}: criterio [GWT] de la spec sin aparición en el test-plan (cobertura que falta)")
    for e in errors:
        print(f"❌ {e}")

    print(json.dumps({
        "applies": True,
        "defined": sorted(defined),
        "referenced": sorted(referenced),
        "broken_refs": len(errors),
        "tasks_sin_cobertura": sin_cobertura,
        "tests_sin_referencia": unreferenced,
        "gwt_cubiertos": gwt_cubiertos,
        "gwt_sin_cubrir": gwt_sin_cubrir,
        "gwt_sin_id": gwt_sin_id,
        "test_plan_na": sin_ui,
        # la clave sale en las CUATRO ramas del --json, no en dos: quien la lee no puede depender de
        # qué rama tomó la puerta (mismo defecto que R4a-9, una línea más abajo — gap R4a-32)
        "marcador_no_canonico": marcador_no_canonico,
    }, ensure_ascii=False))
    sys.exit(1 if (errors or gwt_sin_cubrir) else 0)


if __name__ == "__main__":
    main()
