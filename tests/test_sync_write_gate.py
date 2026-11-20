#!/usr/bin/env python3
"""Puerta CA-05 del marco `knowledge-services` (restaurada en plugin-audit-2 T-08 fix1, gap 1).

La puerta NO dependia de Graphiti: protege CONSTITUTION.md (la publicacion a un backend externo es
posterior a la curacion). Ninguna pieza que se inyecta en el contexto de un agente (`agents/`,
`commands/`, y todo `.md` de `skills/` y `agent-kits/`) puede invocar `knowledge-sync.py` en modo
ESCRITURA (publicacion por defecto, `apply`, `revoke`, `--rebuild`) fuera de la propia skill
`knowledge-services`; solo lectura (`--check`, `--dry-run`, ...) si. Texto original:
`git show 21ad63f:tests/test_miservicio_security.py`; aqui sin nada de Graphiti ni de primitivas.

Ejecutar: python -m pytest -q tests/test_sync_write_gate.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _texto(ruta):
    with open(ruta, "rb") as f:
        return f.read().decode("utf-8")


def _escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


# Exencion NOMINAL, fichero a fichero: la skill duena documenta su propio sincronizador.
PIEZAS_EXENTAS_DE_SINCRONIZADOR = {
    "skills/knowledge-services/SKILL.md": None,
    "skills/knowledge-services/backends/README.md": None,
    "skills/knowledge-services/references/add-backend.md": None,
}

def _backend_de(texto):
    tokens = _tokens(texto)
    return tokens[tokens.index("--backend") + 1] if "--backend" in tokens[:-1] else None


def _exenta(etiqueta, texto):
    if etiqueta not in PIEZAS_EXENTAS_DE_SINCRONIZADOR:
        return False
    permitidos = PIEZAS_EXENTAS_DE_SINCRONIZADOR[etiqueta]
    return permitidos is None or _backend_de(texto) in permitidos
_FLAGS_SOLO_LECTURA = ("--check", "--dry-run", "--outbox-status", "--propose-config",
                        "--avisos-grupo")
# Gap #157: `--check` NO blanquea una linea que ademas publica; y una publicacion no siempre se
# escribe con `--backend <id>` a secas (`apply`/`revoke` son subcomandos del mismo camino).
_TOKENS_DE_ESCRITURA = ("apply", "revoke", "--rebuild")
_DIRECTORIOS_NO_PIEZA = {"tests", "fixtures", "__pycache__", "node_modules", ".git"}


def _piezas(root=ROOT):
    """Piezas que se INYECTAN en el contexto de un agente (etiqueta relativa -> ruta):
    `agents/*.md`, `commands/*.md` y TODO `.md` bajo `skills/` y `agent-kits/` (gap #157: un
    `references/*.md` o un fragmento de `agent-kits/shared/` instruye igual que una `SKILL.md`, y
    quedaban fuera del recorrido). Se excluyen tests y fixtures, que no instruyen a nadie."""
    piezas = {}
    for carpeta in ("agents", "commands"):
        base = os.path.join(root, carpeta)
        if not os.path.isdir(base):
            continue
        for nombre in sorted(os.listdir(base)):
            if nombre.endswith(".md"):
                piezas[carpeta + "/" + nombre] = os.path.join(base, nombre)
    for carpeta in ("skills", "agent-kits"):
        base = os.path.join(root, carpeta)
        if not os.path.isdir(base):
            continue
        for directorio, subdirs, ficheros in os.walk(base):
            subdirs[:] = sorted(d for d in subdirs if d not in _DIRECTORIOS_NO_PIEZA)
            for nombre in sorted(ficheros):
                if not nombre.endswith(".md") or nombre.startswith("test_"):
                    continue
                ruta = os.path.join(directorio, nombre)
                piezas[os.path.relpath(ruta, root).replace(os.sep, "/")] = ruta
    return piezas


def _tokens(linea):
    """Tokens de una linea de instrucciones: se sueltan comillas, backticks y parentesis, asi que
    `python3 "$KS/knowledge-sync.py" --backend miservicio` da los mismos tokens que la forma sin
    entrecomillar (gap #157: el literal `knowledge-sync.py --backend` exigia que las dos palabras
    fueran CONTIGUAS, y la regla 5 del repo obliga justo a lo contrario)."""
    return [t for t in re.split(r"""[\s`"'()<>,]+""", linea.strip()) if t]


_INTERPRETES = ("python", "python3", "py", "bash", "sh", "$")
_SPAN_DE_CODIGO_RE = re.compile(r"`([^`]+)`")


def _variable_en_codigo(linea, en_codigo):
    """Gap #181 (Minor, fix2 Fase 4): un token `$…` solo cuenta como la RUTA del sincronizador si
    va en codigo -bloque con valla, linea que arranca por el interprete, o un span de codigo que
    lleve tambien el `--backend`-. En prosa (`la ruta vive en $KS`) no es una invocacion."""
    if en_codigo or (_tokens(linea)[:1] and _tokens(linea)[0].lower() in _INTERPRETES):
        return any(t.startswith("$") for t in _tokens(linea))
    for span in _SPAN_DE_CODIGO_RE.findall(linea):
        tokens = _tokens(span)
        if "--backend" in tokens and any(t.startswith("$") for t in tokens):
            return True
    return False


def _invocacion_de_escritura(linea, en_codigo=False):
    """Motivo por el que la linea (logica) es una ESCRITURA en el grafo, o `None`. Reconoce la
    invocacion con la ruta entrecomillada o en variable (`"$KSSKILL"`, en codigo) y los flags en
    cualquier orden; el `--check` solo exime si en la MISMA unidad no hay
    `apply`/`revoke`/`--rebuild`."""
    tokens = _tokens(linea)
    if "--backend" not in tokens:
        return None
    cita_script = any(t.endswith("knowledge-sync.py") for t in tokens)
    if not (cita_script or _variable_en_codigo(linea, en_codigo)):
        return None
    escritura = [t for t in tokens if t in _TOKENS_DE_ESCRITURA]
    lectura = [t for t in tokens if t in _FLAGS_SOLO_LECTURA]
    if escritura:
        return "publica en el grafo (%s) aunque la linea traiga %s" % (
            ", ".join(escritura), lectura or "ningun flag de solo lectura")
    if not lectura:
        return "invoca `--backend` sin ningun flag de solo lectura"
    return None


def _unidades(texto):
    """Gap #175 (Important, fix2 Fase 4): la puerta era LINEA A LINEA, y la invocacion multilinea
    natural de un bloque bash (`python3 "$KS/knowledge-sync.py" \\` + `--backend miservicio apply`)
    la evadia. Devuelve `[(linea_inicial, texto, en_codigo, es_bloque)]`: cada linea LOGICA (las
    continuaciones con barra invertida final se unen) y, ademas, cada bloque con valla completo
    como una unidad (`es_bloque` = linea de la valla de cierre; `False` en las lineas), para la
    escritura partida en lineas sin continuacion."""
    unidades, acumulada, bloque = [], None, None
    for numero, linea in enumerate(texto.replace(chr(13), "").split(chr(10)), 1):
        if linea.strip().startswith(("```", "~~~")):
            if acumulada:
                unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
                acumulada = None
            if bloque is None:
                bloque = (numero, [])
            else:
                unidades.append((bloque[0], " ".join(bloque[1]), True, numero))
                bloque = None
            continue
        if bloque is not None:
            bloque[1].append(linea)
        pieza = linea.strip() if acumulada else linea
        acumulada = (acumulada[0], acumulada[1] + " " + pieza) if acumulada else (numero, pieza)
        if linea.rstrip().endswith(chr(92)):
            acumulada = (acumulada[0], acumulada[1].rstrip()[:-1])
            continue
        unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
        acumulada = None
    if acumulada:
        unidades.append((acumulada[0], acumulada[1], bloque is not None, False))
    if bloque is not None:                # valla sin cerrar: el resto del fichero es el bloque
        unidades.append((bloque[0], " ".join(bloque[1]), True, numero + 1))
    return unidades


def _ofensores_de_sincronizador(root=ROOT):
    ofensores = []
    for etiqueta, ruta in sorted(_piezas(root).items()):
        propios, lineas_ofensoras = [], set()
        for numero, texto, en_codigo, es_bloque in _unidades(_texto(ruta)):
            if es_bloque:
                continue
            motivo = _invocacion_de_escritura(texto, en_codigo)
            if motivo and not _exenta(etiqueta, texto):   # exencion NOMINAL (gap #179)
                propios.append((etiqueta, numero, motivo, texto.strip()[:120]))
                lineas_ofensoras.add(numero)
        for numero, texto, _en_codigo, es_bloque in _unidades(_texto(ruta)):
            if not es_bloque:
                continue
            motivo = _invocacion_de_escritura(texto, True)
            ya_visto = any(numero < n < es_bloque for n in lineas_ofensoras)
            if motivo and motivo.startswith("publica") and not ya_visto                     and not _exenta(etiqueta, texto):
                propios.append((etiqueta, numero, "bloque: " + motivo, texto.strip()[:120]))
        ofensores += propios
    return ofensores


def test_el_recorrido_de_piezas_no_esta_vacio():
    """Andamiaje: sin piezas, los dos tests de abajo pasarian en vacio. Gap #157: exige tambien
    las piezas que se inyectan sin ser `SKILL.md` (referencias y fragmentos compartidos)."""
    piezas = _piezas()
    for esperada in ("agents/knowledge-curator.md", "commands/dev-cycle.md",
                     "skills/knowledge-services/SKILL.md",
                     "skills/adversarial-review/references/lens-prompts.md",
                     "agent-kits/shared/knowledge-check.md"):
        assert esperada in piezas, (esperada, len(piezas))
    assert len(piezas) >= 100, len(piezas)


def test_ca05_ninguna_pieza_ajena_invoca_el_sincronizador_en_modo_escritura():
    """Fuera de la skill `knowledge-services`, una pieza puede NOMBRAR `knowledge-sync.py`, pero
    solo en un modo de SOLO LECTURA (`--check`/`--dry-run`/`--outbox-status`/`--propose-config`):
    una publicacion real (`--backend <id>` a secas, `apply`, `revoke` o `--rebuild`) es escritura
    en el grafo, este la ruta entrecomillada, en variable o con los flags en otro orden."""
    assert _ofensores_de_sincronizador() == [], _ofensores_de_sincronizador()


# ----------------------------------------------------- mutantes de la puerta CA-05 (gap #157)
# Los cinco sobre un repo MINIMO en `tmp_path`: tres formas de invocacion que el literal anterior
# no veia y dos piezas inyectadas que no estaban en el recorrido.

def _repo_de_piezas(tmp_path, piezas):
    """Repo de mentira con las piezas indicadas (`{ruta relativa: contenido}`)."""
    root = os.path.join(str(tmp_path), "repo-piezas")
    for rel, contenido in piezas.items():
        _escribir(os.path.join(root, *rel.split("/")), contenido)
    return root


_MUTANTES_INVOCACION = (
    ("ruta entrecomillada (regla 5)",
     'python3 "$KS/knowledge-sync.py" --backend miservicio --root .'),
    ("flags reordenados",
     "python3 skills/knowledge-services/scripts/knowledge-sync.py --rebuild --backend miservicio"),
    ("`--check` y despues, sin --check, publica",
     "primero `knowledge-sync.py --backend miservicio --check` y despues "
     "`knowledge-sync.py --backend miservicio apply`"),
    ("ruta en variable, estilo de la SKILL.md",
     'python3 "$KSSKILL" --backend miservicio --root .'),
)


def test_mutantes_de_invocacion_del_sincronizador_no_pasan_la_puerta(tmp_path):
    """Mutantes 1-4 del gap #157: cuatro formas REALES de publicar en el grafo desde una pieza
    ajena que el literal `knowledge-sync.py --backend` + «hay un `--check` en la linea» dejaba
    pasar (los tres primeros sobrevivian en la revision)."""
    for descripcion, linea in _MUTANTES_INVOCACION:
        root = _repo_de_piezas(tmp_path, {"commands/dev-cycle.md":
                                          "# dev-cycle\n\n" + linea + "\n"})
        ofensores = _ofensores_de_sincronizador(root)
        assert ofensores, ("el mutante sobrevive: " + descripcion, linea)


def test_una_linea_de_solo_lectura_sigue_siendo_legitima(tmp_path):
    """Control negativo del mutante anterior: la puerta no puede volverse un «cualquier mencion a
    `--backend` es escritura» (eso romperia `/doctor`, que documenta el `--check`)."""
    root = _repo_de_piezas(tmp_path, {"commands/doctor.md":
                                      "python skills/knowledge-services/scripts/knowledge-sync.py "
                                      "--backend <id> --check\n"})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)


# ------------------------------------------- mutantes de la puerta CA-05 (fix2 Fase 4)

def test_f4fix2_probe_p6_y_p4_la_invocacion_multilinea_no_evade_la_puerta(tmp_path):
    """Gap #175, probes P6 y P4: la forma NATURAL de un bloque bash (continuaciones con barra
    invertida) partia la invocacion en lineas que, sueltas, no casaban (2 passed). Las
    continuaciones se unen y el bloque de codigo cuenta ademas como una unidad."""
    formas = (
        ("p6", 'python3 "$KSSKILL/knowledge-sync.py" \\\n    --backend miservicio apply\n'),
        ("p4", 'python3 "$KS/knowledge-sync.py" \\\n  --backend miservicio \\\n  --root .\n'),
        ("rebuild", "python3 skills/knowledge-services/scripts/knowledge-sync.py \\\n"
                    "  --backend miservicio \\\n  --rebuild\n"),
    )
    for clave, comando in formas:
        for valla in ("```bash\n", "```sh\n", "```\n"):
            root = _repo_de_piezas(tmp_path / (clave + str(len(valla))),
                                   {"commands/dev-cycle.md":
                                    "# dev-cycle\n\n" + valla + comando + "```\n"})
            assert _ofensores_de_sincronizador(root), ("el probe sobrevive", clave, valla)
    # y sin valla: la continuacion se une igual en prosa indentada
    root = _repo_de_piezas(tmp_path / "suelta", {"commands/dev-cycle.md": formas[0][1]})
    assert _ofensores_de_sincronizador(root), "la continuacion fuera de bloque sobrevive"


def test_f4fix2_un_bloque_que_parte_la_publicacion_en_dos_lineas_es_una_unidad(tmp_path):
    """Gap #175 (bloque como unidad): dentro de un bloque ```bash```, la escritura en una linea
    y la invocacion en la anterior -sin barra- se leen juntas."""
    bloque = ('```bash\nKS_ARGS="--backend miservicio"\n'
              'python3 "$KS/knowledge-sync.py" $KS_ARGS apply\n```\n')
    root = _repo_de_piezas(tmp_path, {"commands/dev-cycle.md": bloque})
    assert _ofensores_de_sincronizador(root), "el bloque partido sobrevive"


def test_f4fix2_una_invocacion_multilinea_de_solo_lectura_sigue_siendo_legitima(tmp_path):
    """Control negativo del #175: el `--check` partido en continuaciones no es escritura."""
    root = _repo_de_piezas(tmp_path, {"commands/doctor.md":
                                      '```bash\npython3 "$KS/knowledge-sync.py" \\\n'
                                      '  --backend miservicio \\\n  --check\n```\n'})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)


def test_f4fix3_una_valla_sin_cerrar_cuenta_como_bloque_hasta_el_final(tmp_path):
    """Gap #190(d): la rama «valla sin cerrar» de `_unidades` no tenia test (mutante T1 vivo). Un
    bloque ```bash que no se cierra se lee como bloque hasta el final del fichero, asi que la
    escritura partida en dos lineas sin continuacion se sigue viendo."""
    texto = ('```bash\nKS_ARGS="--backend miservicio"\n'
             'python3 "$KS/knowledge-sync.py" $KS_ARGS apply\n')
    bloques = [u for u in _unidades(texto) if u[3]]
    assert bloques and bloques[0][0] == 1 and "apply" in bloques[0][1], _unidades(texto)
    root = _repo_de_piezas(tmp_path, {"commands/dev-cycle.md": texto})
    motivos = [o[2] for o in _ofensores_de_sincronizador(root)]
    assert any(m.startswith("bloque: ") for m in motivos), motivos


def test_f4fix2_probe_p3_una_variable_en_prosa_no_es_una_invocacion(tmp_path):
    """Gap #181, probe P3: una linea de PROSA que menciona `--backend` y cita `$KS` rompia la
    suite. Una variable solo cuenta como la ruta del sincronizador si es `$…/…knowledge-sync.py`
    o si va en codigo (bloque, span de codigo con el `--backend`, o linea que arranca con el
    interprete); en codigo, la forma variable SI se sigue viendo."""
    prosa = ("El flag `--backend` elige el adaptador; la ruta de la skill vive en $KS y se "
             "resuelve en runtime.\n")
    root = _repo_de_piezas(tmp_path / "prosa", {"commands/dev-cycle.md": prosa})
    assert _ofensores_de_sincronizador(root) == [], _ofensores_de_sincronizador(root)
    for clave, texto in (("bloque", '```bash\npython3 "$KSSKILL" --backend miservicio --root .\n```\n'),
                         ("span", 'Publica con `"$KSSKILL" --backend miservicio` a mano.\n'),
                         ("interprete", 'python3 "$KSSKILL" --backend miservicio --root .\n')):
        root = _repo_de_piezas(tmp_path / clave, {"commands/dev-cycle.md": texto})
        assert _ofensores_de_sincronizador(root), "la forma variable en %s sobrevive" % clave




def test_la_exencion_es_nominal_y_apunta_a_ficheros_reales(tmp_path):
    """Gap #179: la exencion es por NOMBRE de fichero, no por prefijo; otra `references/*.md` de
    la skill duena no esta exenta y la guia del adaptador (add-backend.md) si, porque documenta el
    sincronizador."""
    root = _repo_de_piezas(tmp_path, {
        "skills/knowledge-services/references/project-integration.md":
            'python3 "$KS/knowledge-sync.py" --backend miservicio apply\n'})
    assert _ofensores_de_sincronizador(root), "una referencia no exenta publica sin que la puerta lo vea"
    for pieza in PIEZAS_EXENTAS_DE_SINCRONIZADOR:
        assert not pieza.endswith("/"), pieza
        assert os.path.isfile(os.path.join(ROOT, pieza)), pieza


def test_aviso_de_grupo_del_sincronizador_es_solo_lectura_para_la_puerta(tmp_path):
    """`--avisos-grupo` (funcion OPCIONAL `estado_grupo` del adaptador) no publica: `/setup` puede nombrarlo."""
    root = _repo_de_piezas(tmp_path, {"commands/setup.md": "# setup\n\n"
        "python3 skills/knowledge-services/scripts/knowledge-sync.py --backend miservicio --avisos-grupo\n"})
    assert _ofensores_de_sincronizador(root) == []


# ------------------------------------------------ fix2 de la Fase 2 (gap 3 del intento 2)

def test_fase2fix2_forma_con_igual_y_cadenas_de_ordenes_no_evaden_la_puerta(tmp_path):
    """`--backend=x`, `--check && ... --backend x --root .` y `# luego --check` son escritura."""
    formas = (
        'python3 "$KS/knowledge-sync.py" --backend=miservicio\n',
        'python3 "$KS/knowledge-sync.py" --backend miservicio --check && '
        'python3 "$KS/knowledge-sync.py" --backend miservicio --root .\n',
        'python3 "$KS/knowledge-sync.py" --backend miservicio --check ; '
        'python3 "$KS/knowledge-sync.py" --backend miservicio apply\n',
        'python3 "$KS/knowledge-sync.py" --backend miservicio --root .  # luego --check\n',
        '```bash\npython3 "$KS/knowledge-sync.py" --check --backend miservicio\n'
        'python3 "$KS/knowledge-sync.py" --backend=miservicio --rebuild\n```\n',
    )
    for i, texto in enumerate(formas):
        root = _repo_de_piezas(tmp_path / ("f%d" % i), {"commands/dev-cycle.md": texto})
        assert _ofensores_de_sincronizador(root), ("el mutante sobrevive", texto)


def test_fase2fix2_controles_negativos_de_la_cadena(tmp_path):
    """La solo lectura con `=`, encadenada o comentada sigue siendo legitima."""
    formas = (
        'python3 "$KS/knowledge-sync.py" --backend=miservicio --check\n',
        'python3 "$KS/knowledge-sync.py" --backend miservicio --check && echo ok\n',
        'python3 "$KS/knowledge-sync.py" --backend miservicio --check  # no usar apply\n',
    )
    for i, texto in enumerate(formas):
        root = _repo_de_piezas(tmp_path / ("n%d" % i), {"commands/doctor.md": texto})
        assert _ofensores_de_sincronizador(root) == [], (texto, _ofensores_de_sincronizador(root))
