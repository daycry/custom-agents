#!/usr/bin/env python3
"""mutantes.py — campaña de mutantes VERSIONADA de `changelog-sync.py` + `ledger-lint.py`.

Por qué existe: «14 de 25 mutantes sobrevivían; 0 de 40 sobreviven ahora» era la única afirmación
de la iniciativa `changelog-brief` que nadie podía reproducir — y estaba mal por los dos extremos
(`RESUMEN_MAX 200→400` ya moría en `5a51d7c`, así que sobre-contaba supervivientes; y cuatro
mutantes genuinos seguían vivos, así que sub-contaba). Un recuento que no se puede volver a
ejecutar no es una medición: es una creencia. Aquí la lista es código, con su motivo por mutante,
y el recuento sale de ejecutarla.

Cada mutante es una SUSTITUCIÓN LITERAL en el fichero objetivo. Un mutante que la suite no mata es
un hueco de test, no un fallo del script: el arreglo es escribir el test que lo mate.

Uso:
  python3 mutantes.py                 # campaña completa · exit 0 si todos mueren, 1 si sobrevive alguno
  python3 mutantes.py --list          # la lista, sin ejecutar nada
  python3 mutantes.py --only <substr> # solo los mutantes cuyo nombre contenga <substr>
  python3 mutantes.py -q              # una línea por mutante, sin la salida de pytest

NO se ejecuta en `pytest -q` (la campaña completa cuesta ~1 min: un pytest por mutante, y la suite
de la skill tarda ~2 s). Lo que SÍ entra en la suite es
`test_el_arnes_de_mutantes_esta_al_dia`, que comprueba que cada `busca` sigue apareciendo
EXACTAMENTE UNA VEZ en su fichero: un mutante que dejó de aplicarse en silencio contaría como
«muerto» sin haber probado nada, y eso es la forma en que un arnés se podre.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — GOT-005

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SYNC = "skills/changelog-sync/scripts/changelog-sync.py"
LINT = "agent-kits/shared/ledger-lint.py"
TESTS = "skills/changelog-sync/scripts/test_changelog_sync.py"
CIFRAS = "tests/test_cifras_medidas.py"      # la puerta de las cifras de la doc (T-07)
# Ficheros de doc que `CIFRAS` compara contra la medición: sin ellos en el árbol, los mutantes de
# medición sobrevivirían por falta de corpus, no por falta de test.
DOCS_CIFRAS = ["skills/changelog-sync/references/medicion-escalera.md",
               "skills/changelog-sync/SKILL.md",
               "docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md",
               "docs/knowledge/README.md", "docs/CONVENTIONS.md", "docs/en/CONVENTIONS.md"]

# Ficheros que la suite necesita ver en la raíz del árbol temporal para no SALTARSE sus tests
# dependientes del repo (`REPO` se resuelve como `<tmp>`): el kit compartido, la plantilla de tarea
# del planner, `release.py` (el test del `SLUG_PENDIENTE` lee su regex) y los ledgers reales.
CONTEXTO = [LINT, "agent-kits/planner/templates/tasks.md", "scripts/release.py",
            CIFRAS, *DOCS_CIFRAS]

# --- La lista. `objetivo` → fichero; `busca`/`pone` → sustitución literal; `motivo` → qué fallo
# real reintroduce el mutante (si no se puede nombrar el fallo, el mutante no vale la pena);
# `pruebas` → qué suites lo tienen que matar (por defecto la de la skill).
#
# Mutantes PROBADOS y descartados por EQUIVALENTES (no se listan para que el recuento signifique
# algo; se anotan aquí para no volver a escribirlos):
#   · `if n_frases > RESUMEN_FRASES_MAX:` → `if corto != re.sub(r"\s+", " ", campo).strip():`
#     (la formulación vieja del aviso). Es equivalente desde que `frases()` recorta sobre
#     `separa_frases()`: los dos lados normalizan el espaciado igual, así que «el texto cambió» ⟺
#     «había más de n frases». Su modo de fallo (aviso disparado por el espaciado, o mintiendo
#     sobre el recuento) solo era alcanzable por el `return s` que se ha eliminado.
#   · `RESUMEN_MAX 200 → 400` en el intento 1: ya moría en `5a51d7c`, y contarlo como superviviente
#     es lo que hizo que «14 de 25» sobre-contase.
MUTANTES = [
    # ---- parseo de los campos del ledger ----
    dict(nombre="campo-changelog-se-come-el-salto", objetivo=SYNC,
         busca=r'r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]*(?P<txt>.*)$"',
         pone=r'r"^\s*-\s*\*\*Changelog\*\*\s*:\s*(?P<txt>.*)$"',
         motivo="con re.M, `\\s*` se come el `\\n`: un campo VACÍO publica la línea siguiente"),
    dict(nombre="campo-descripcion-se-come-el-salto", objetivo=SYNC,
         busca=r'r"^[^\S\n]*-[^\S\n]*\*\*Descripci[oó]n\*\*[^\S\n]*:[^\S\n]*(.*)$"',
         pone=r'r"^\s*-\s*\*\*Descripci[oó]n\*\*\s*:\s*(.*)$"',
         motivo="mismo fallo en `Descripción` (era anterior a la iniciativa)"),
    dict(nombre="campo-archivos-se-come-el-salto", objetivo=SYNC,
         busca=r'r"^[^\S\n]*-[^\S\n]*\*\*Archivos\*\*[^\S\n]*:[^\S\n]*(.*)$"',
         pone=r'r"^\s*-\s*\*\*Archivos\*\*\s*:\s*(.*)$"',
         motivo="un `- **Archivos**:` vacío INVENTA ficheros con lo que haya debajo"),
    dict(nombre="campo-changelog-exige-guion-exacto", objetivo=SYNC,
         busca=r'r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]*(?P<txt>.*)$"',
         pone=r'r"^- \*\*Changelog\*\*:[^\S\n]*(?P<txt>.*)$"',
         motivo="`-  **Changelog**:` (dos espacios) pasa el linter y lo descarta el generador"),
    dict(nombre="bloque-no-cierra-en-h2", objetivo=SYNC,
         busca='RE_FIN_BLOQUE = re.compile(r"^##\\s", re.M)',
         pone='RE_FIN_BLOQUE = re.compile(r"^##ZZZ", re.M)',
         motivo="la cola del ledger cuenta como parte de la ÚLTIMA tarea"),
    dict(nombre="bloque-no-ignora-las-vallas", objetivo=SYNC,
         busca="bloques = re.split(r\"\\n(?=### (?:T-\\d+|Fase)\\b)\", sin_vallas(text))",
         pone="bloques = re.split(r\"\\n(?=### (?:T-\\d+|Fase)\\b)\", text)",
         motivo="un `## Ejemplo` citado en una valla corta la tarea y pierde el campo de debajo"),
    dict(nombre="continuacion-sin-guarda-de-vinetas", objetivo=SYNC,
         busca=r'CONTINUACION_PATTERN = r"^[ \t]{1,3}(?![-*+>|]\s|\d+[.)]\s|<!--|\|)\S"',
         pone=r'CONTINUACION_PATTERN = r"^[ \t]+\S"',
         motivo="absorbe criterios, filas de tabla y campos indentados como si fueran prosa"),
    dict(nombre="continuacion-sin-guarda-de-campos", objetivo=SYNC,
         busca="    return bool(RE_CONTINUACION.match(ln)) and not RE_CAMPO_LEDGER.match(ln)",
         pone="    return bool(RE_CONTINUACION.match(ln))",
         motivo="un `  **Estado**: completado` se traga dentro del resumen"),
    dict(nombre="verificacion-se-come-el-campo", objetivo=LINT,
         busca="        if not ms or _CAMPO_LEDGER_RE.match(lines[j]):",
         pone="        if not ms:",
         motivo="el campo indentado bajo `Verificación` lo publica el generador y el linter no lo ve"),
    dict(nombre="fase-h3-no-cierra-la-tarea", objetivo=LINT,
         busca='        if re.match(r"^###\\s+Fase\\b", ln):',
         pone='        if re.match(r"^###\\s+FaseZZZ\\b", ln):',
         motivo="un campo bajo `### Fase 2` se atribuye distinto en cada parser"),
    dict(nombre="lint-no-ignora-las-vallas", objetivo=LINT,
         busca="    lines = sin_vallas(text).splitlines()",
         pone="    lines = text.splitlines()",
         motivo="un `- **Changelog**:` citado en una valla se lee como el campo"),
    # ---- frases y abreviaturas ----
    dict(nombre="abreviaturas-vacias", objetivo=SYNC,
         busca='ABREVIATURAS = ("p. ej.", "ej.", "vs.",',
         pone='ABREVIATURAS = (\n    ) if True else ("p. ej.", "ej.", "vs.",',
         motivo="`Sr. Pérez` vuelve a parecer fin de frase"),
    dict(nombre="abreviaturas-sin-vs", objetivo=SYNC, busca='"vs.", "sr."', pone='"sr."',
         motivo="`vs. Claude` parte la frase"),
    dict(nombre="abreviaturas-sin-p-ej", objetivo=SYNC, busca='"p. ej.", "ej.",', pone='"ej.",',
         motivo="`p. ej. Windows` parte la frase"),
    dict(nombre="abreviaturas-con-etc", objetivo=SYNC, busca='("p. ej.", "ej.", "vs.",',
         pone='("etc.", "p. ej.", "ej.", "vs.",',
         motivo="`etc.` tapa un fin de frase real y `frases()` devuelve el texto entero"),
    dict(nombre="abreviaturas-con-uu", objetivo=SYNC, busca='"ee.", "a. m."', pone='"ee.", "uu.", "a. m."',
         motivo="«… en EE. UU. Ahora en Canadá.» deja de partirse donde debe"),
    dict(nombre="abreviatura-sin-frontera-de-palabra", objetivo=SYNC,
         busca="            if k == 0 or not antes[k - 1].isalpha():   # frontera: «las cosas.» no es «…s.»\n                return True",
         pone="            return True",
         motivo="«la red.» acaba en «ed.», así que ninguna frase normal cierra"),
    dict(nombre="frases-sin-tope", objetivo=SYNC,
         busca='    return " ".join(f.strip() for f in fs[:max(0, n)]).strip()',
         pone='    return " ".join(f.strip() for f in fs).strip()',
         motivo="`frases()` deja de recortar: publica todas las frases del campo"),
    dict(nombre="aviso-de-recorte-siempre", objetivo=SYNC,
         busca="        if n_frases > RESUMEN_FRASES_MAX:", pone="        if n_frases >= 0:",
         motivo="el aviso miente: dice que recortó cuando no recortó"),
    dict(nombre="fin-de-frase-sin-asterisco", objetivo=SYNC,
         busca=r'FIN_FRASE = re.compile(r"\.(?=\s+[A-ZÁÉÍÓÚÑ¿«`*])")',
         pone=r'FIN_FRASE = re.compile(r"\.(?=\s+[A-ZÁÉÍÓÚÑ¿«`])")',
         motivo="`. **(1) …` deja de contar como fin de frase"),
    # ---- corte de nivel superior ----
    dict(nombre="cortes-sin-punto-y-coma", objetivo=SYNC, busca='CORTES = ":;—–"', pone='CORTES = ":—–"',
         motivo="el corte por `;` desaparece"),
    dict(nombre="cortes-sin-rayas", objetivo=SYNC, busca='CORTES = ":;—–"', pone='CORTES = ":;"',
         motivo="el corte por `—`/`–` desaparece"),
    dict(nombre="cortes-solo-dos-puntos", objetivo=SYNC, busca='CORTES = ":;—–"', pone='CORTES = ":"',
         motivo="solo queda el delimitador que el intento 1 ya fijaba"),
    dict(nombre="abre-sin-parentesis", objetivo=SYNC, busca='ABRE, CIERRA = "([{«", ")]}»"',
         pone='ABRE, CIERRA = "[{«", "]}»"',
         motivo="se corta DENTRO de un paréntesis"),
    dict(nombre="abre-sin-corchete", objetivo=SYNC, busca='ABRE, CIERRA = "([{«", ")]}»"',
         pone='ABRE, CIERRA = "({«", ")}»"', motivo="se corta dentro de `[corchetes]`"),
    dict(nombre="abre-sin-llave", objetivo=SYNC, busca='ABRE, CIERRA = "([{«", ")]}»"',
         pone='ABRE, CIERRA = "([«", ")]»"', motivo="se corta dentro de `{llaves}`"),
    dict(nombre="abre-sin-comillas-latinas", objetivo=SYNC, busca='ABRE, CIERRA = "([{«", ")]}»"',
         pone='ABRE, CIERRA = "([{", ")]}"', motivo="se corta dentro de «comillas»"),
    dict(nombre="corte-por-parentesis-desactivado", objetivo=SYNC,
         busca='            if depth == 0 and ch == "(" and not (i and s[i - 1] == "]"):',
         pone='            if False:', motivo="el `(` de nivel superior deja de cortar"),
    dict(nombre="corte-parte-un-enlace-markdown", objetivo=SYNC,
         busca='            if depth == 0 and ch == "(" and not (i and s[i - 1] == "]"):',
         pone='            if depth == 0 and ch == "(":',
         motivo="`[texto](destino)` se parte y deja la referencia colgando"),
    dict(nombre="cerco-de-uno-en-uno", objetivo=SYNC, busca="            elif cerco == run:",
         pone="            else:",
         motivo="un tramo ``a`b:c`` queda «abierto y cerrado» y el corte entra dentro del código"),
    # ---- topes ----
    dict(nombre="resumen-max-120", objetivo=SYNC, busca="\nRESUMEN_MAX = 200\n", pone="\nRESUMEN_MAX = 120\n",
         motivo="el tope del resumen se mueve por debajo"),
    dict(nombre="resumen-max-400", objetivo=SYNC, busca="\nRESUMEN_MAX = 200\n", pone="\nRESUMEN_MAX = 400\n",
         motivo="el tope del resumen se mueve por encima"),
    dict(nombre="resumen-frases-max-3", objetivo=SYNC, busca="\nRESUMEN_FRASES_MAX = 2 ",
         pone="\nRESUMEN_FRASES_MAX = 3 ", motivo="el tope de frases se mueve"),
    dict(nombre="archivos-max-5", objetivo=SYNC, busca="ARCHIVOS_MAX = 3            #",
         pone="ARCHIVOS_MAX = 5            #", motivo="vuelve la lista de 5 ficheros"),
    dict(nombre="archivos-max-tocados-4x", objetivo=SYNC,
         busca="ARCHIVOS_MAX_TOCADOS = 2 * ARCHIVOS_MAX", pone="ARCHIVOS_MAX_TOCADOS = 4 * ARCHIVOS_MAX",
         motivo="el paréntesis reaparece con 12 ficheros tocados"),
    dict(nombre="corte-min-palabras-1", objetivo=SYNC, busca="CORTE_MIN_PALABRAS = 5",
         pone="CORTE_MIN_PALABRAS = 1", motivo="la puerta de «idea completa» deja pasar rutas sueltas"),
    dict(nombre="corte-min-palabras-9", objetivo=SYNC, busca="CORTE_MIN_PALABRAS = 5",
         pone="CORTE_MIN_PALABRAS = 9", motivo="la puerta descarta frases cortas legítimas"),
    # ---- normalización y marcado ----
    dict(nombre="negrita-se-borra-en-vez-de-cerrarse", objetivo=SYNC,
         busca='        t += "**"                            # negrita abierta por el corte: se CIERRA, no se borra',
         pone='        t = t.replace("**", "")',
         motivo="`los **27 scripts` pierde el énfasis que escribió el autor"),
    dict(nombre="negrita-contada-con-el-codigo-dentro", objetivo=SYNC,
         busca="    if sin_codigo(t).count(\"**\") % 2 == 1:", pone="    if t.count(\"**\") % 2 == 1:",
         motivo="un `**` literal dentro de un glob añade un `**` huérfano que abre negrita"),
    dict(nombre="sin-codigo-de-uno-en-uno", objetivo=SYNC,
         busca="""        cierre = next((j for j in range(k + 1, len(runs))
                       if runs[j][1] - runs[j][0] == largo), None)""",
         pone="        cierre = k + 1 if k + 1 < len(runs) else None",
         motivo="los runs de acentos graves se emparejan mal y `` ``a`b`` `` se rompe"),
    dict(nombre="prosa-sin-dieresis", objetivo=SYNC,
         busca=r'if re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñüÜçÇïÏàèòÀÈÒ]{2,}", w)])',
         pone=r'if re.search(r"[A-Za-z]{2,}", w)])',
         motivo="una palabra cuyas únicas rachas lleven acento deja de contar como prosa"),
    dict(nombre="sin-mayuscula-inicial", objetivo=SYNC,
         busca='    t = re.sub(r"^([a-záéíóúñüç])", lambda m: m.group(1).upper(), t, count=1)',
         pone="    pass", motivo="el resumen automático empieza en minúscula"),
    # ---- placeholder ----
    dict(nombre="placeholder-basta-mencionarlo", objetivo=SYNC,
         busca="    resto = RE_PLACEHOLDER.sub(\" \", sin_codigo(s))\n    return not resto.strip(PLACEHOLDER_RELLENO)",
         pone="    return bool(RE_PLACEHOLDER.search(s))",
         motivo="un `{{…}}` CITADO descarta el texto que escribió una persona"),
    dict(nombre="placeholder-ignorado", objetivo=SYNC,
         busca="    if es_placeholder(campo):", pone="    if False:",
         motivo="el `{{…}}` de la plantilla llega literal al CHANGELOG"),
    dict(nombre="placeholder-solo-en-el-campo", objetivo=SYNC,
         busca="    if es_placeholder(d):", pone="    if False:",
         motivo="un `{{…}}` en la `Descripción` se publica literal"),
    dict(nombre="placeholder-no-cuenta-en-la-deuda", objetivo=SYNC,
         busca='    return bool((t or "").strip()) and not es_placeholder(t)',
         pone='    return bool((t or "").strip())',
         motivo="la deuda reporta 0 justo en el caso que la plantilla crea"),
    dict(nombre="placeholder-lint-basta-mencionarlo", objetivo=LINT,
         busca="    resto = _PLACEHOLDER_RE.sub(\" \", sin_codigo(s))\n    return not resto.strip(PLACEHOLDER_RELLENO)",
         pone="    return bool(_PLACEHOLDER_RE.search(s))",
         motivo="el linter y el generador vuelven a discrepar sobre qué es un placeholder"),
    # ---- render del bullet ----
    dict(nombre="bullet-trunca-con-elipsis", objetivo=SYNC,
         busca='            linea += f" {texto}"',
         pone='            linea += f" {texto[:60]}…"',
         motivo="vuelve el truncado con `…` que la iniciativa prohíbe"),
    dict(nombre="bullet-sin-puntero-al-ledger", objetivo=SYNC,
         busca='            linea += f" ([ledger]({ledger}))"', pone="            pass",
         motivo="el camino `titulo` deja de apuntar al ledger"),
    dict(nombre="aviso-con-forma-de-slug-pendiente", objetivo=SYNC,
         busca='    return (f"{slug}: {len(sin)}/{len(ts)} tarea(s) sin `- **Changelog**:` "',
         pone='    return (f"{slug} (2026-01-01): {len(sin)}/{len(ts)} tarea(s) sin `- **Changelog**:` "',
         motivo="el aviso adopta la forma `<slug> (fecha)` y `release.py` lo lee como pendiente"),
    dict(nombre="degradacion-no-cuenta-titulo", objetivo=SYNC,
         busca='    deg = d["caminos"].get("titulo", 0)', pone="    deg = 0",
         motivo="la línea del total dice que nada degrada"),
    # ---- criterio único entre los dos scripts ----
    dict(nombre="patron-del-campo-divergente", objetivo=LINT,
         busca=r'    r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]*(?P<txt>.*)$"',
         pone=r'    r"^[^\S\n]*-[^\S\n]*\*\*Changelog\*\*[^\S\n]*:[^\S\n]?(?P<txt>.*)$"',
         motivo="las dos copias del patrón dejan de ser la misma cadena"),
    dict(nombre="criterio-de-valla-divergente", objetivo=LINT,
         busca=r'VALLA_PATTERN = r"^[^\S\n]*(?:`{3,}|~{3,})"',
         pone=r'VALLA_PATTERN = r"^[^\S\n]*(?:`{3,})"',
         motivo="los dos parsers dejan de reconocer la misma valla"),
    # ---- medición (T-07) ----
    dict(nombre="corpus-base-sin-fijar", objetivo=SYNC, pruebas=[TESTS, CIFRAS],
         busca='CORPUS_BASE_HASTA = "2026-09-04"', pone='CORPUS_BASE_HASTA = "2099-01-01"',
         motivo="el corpus base deja de ser el de la medición y las cifras de la doc se mueven"),
    dict(nombre="mediana-con-n-par-mal", objetivo=SYNC, pruebas=[TESTS, CIFRAS],
         busca="    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) // 2",
         pone="    return s[n // 2]",
         motivo="la mediana de una lista par deja de ser la de la doc"),
    dict(nombre="medicion-cuenta-los-legacy", objetivo=SYNC, pruebas=[TESTS, CIFRAS],
         busca='    base = [r for r in regs if r[0] < CORPUS_BASE_HASTA]',
         pone='    base = list(regs)',
         motivo="el corpus base se convierte en el de hoy y la doc deja de reproducir"),
]


def _tree(dest):
    """Árbol temporal con la skill + el contexto que su suite necesita para NO saltarse tests."""
    os.makedirs(os.path.join(dest, os.path.dirname(SYNC)), exist_ok=True)
    for rel in (SYNC, TESTS, *CONTEXTO):
        src = os.path.join(REPO, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
    base = os.path.join(REPO, "docs", "roadmap")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            p = os.path.join(base, d, "tasks.md")
            if os.path.isfile(p):
                os.makedirs(os.path.join(dest, "docs", "roadmap", d), exist_ok=True)
                shutil.copy(p, os.path.join(dest, "docs", "roadmap", d, "tasks.md"))
    for fn in ("CHANGELOG.md", "CHANGELOG.es.md"):
        src = os.path.join(REPO, fn)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(dest, fn))
    return dest


def comprueba_lista():
    """[str] con los problemas de la lista: un `busca` que no aparece EXACTAMENTE una vez ya no
    prueba nada y contaría como mutante muerto. Es lo que la suite comprueba en cada ejecución."""
    problemas, vistos = [], set()
    for m in MUTANTES:
        if m["nombre"] in vistos:
            problemas.append(f"{m['nombre']}: nombre duplicado")
        vistos.add(m["nombre"])
        if not m.get("motivo"):
            problemas.append(f"{m['nombre']}: sin motivo (¿qué fallo real reintroduce?)")
        p = os.path.join(REPO, m["objetivo"])
        if not os.path.isfile(p):
            problemas.append(f"{m['nombre']}: no existe {m['objetivo']}")
            continue
        n = open(p, encoding="utf-8").read().count(m["busca"])
        if n != 1:
            problemas.append(f"{m['nombre']}: `busca` aparece {n} vez/veces en {m['objetivo']} "
                             f"(debe ser 1) — el mutante ya no se aplica")
        if m["busca"] == m["pone"]:
            problemas.append(f"{m['nombre']}: `busca` == `pone` (mutante vacío)")
    return problemas


def campaña(solo=None, silencioso=False):
    problemas = comprueba_lista()
    for p in problemas:
        print(f"❌ arnés: {p}")
    if problemas:
        return 2
    lista = [m for m in MUTANTES if not solo or solo in m["nombre"]]
    if not lista:
        print(f"mutantes: ningún mutante casa «{solo}»")
        return 2
    originales = {rel: open(os.path.join(REPO, rel), encoding="utf-8").read()
                  for rel in {m["objetivo"] for m in lista}}
    muertos, vivos = 0, []
    with tempfile.TemporaryDirectory() as tmp:
        raiz = _tree(tmp)
        for m in lista:
            dst = os.path.join(raiz, m["objetivo"])
            for rel, txt in originales.items():
                open(os.path.join(raiz, rel), "w", encoding="utf-8").write(txt)
            open(dst, "w", encoding="utf-8").write(
                originales[m["objetivo"]].replace(m["busca"], m["pone"], 1))
            objetivos = [os.path.join(raiz, t) for t in m.get("pruebas", [TESTS])
                         if os.path.isfile(os.path.join(raiz, t))]
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", *objetivos],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=raiz)
            vivo = r.returncode == 0
            muertos += not vivo
            if vivo:
                vivos.append(m)
            ultima = next((l for l in reversed((r.stdout or "").strip().split("\n")) if l.strip()),
                          "(sin salida)")
            print(f"{'🟥 SOBREVIVE' if vivo else '✅ muerto  '}  {m['nombre']:42} "
                  + ("" if silencioso else f"| {ultima}"))
    print(f"\nmutantes: {muertos}/{len(lista)} muertos")
    for m in vivos:
        print(f"⚠️  sobrevive {m['nombre']} ({m['objetivo']}): {m['motivo']} "
              f"— falta el test que lo mate")
    return 0 if not vivos else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="campaña de mutantes de changelog-sync")
    ap.add_argument("--list", action="store_true", dest="listar")
    ap.add_argument("--only")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args(argv)
    if a.listar:
        for m in MUTANTES:
            print(f"{m['nombre']:42} {m['objetivo']:52} {m['motivo']}")
        print(f"\nmutantes: {len(MUTANTES)} en la lista")
        return 0
    return campaña(a.only, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
