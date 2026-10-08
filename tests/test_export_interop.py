#!/usr/bin/env python3
"""Suite de la INTEROP con Codex y OpenCode (`scripts/export-interop.py`).

Cubre las tres cosas que pueden romper la importación del plugin en otra herramienta:

1. **Sincronía** — el árbol generado refleja las piezas del repo (`--check` en verde). Es la
   misma puerta que corre CI y `release.py`: si alguien toca un agente y no regenera, falla aquí.
2. **Formato** — lo generado es válido y COMPLETO para cada runtime: TOML parseable con las tres
   claves obligatorias de Codex, frontmatter con `description` en OpenCode, manifiesto con los
   punteros que Codex lee, hooks solo con eventos que Codex dispara de verdad.
3. **Invariantes que no se pueden perder al traducir** — el `reviewer` declara límites reales
   de permisos por runtime, y ninguna `description` de skill pasa del tope de OpenCode
   (1.024 caracteres): pasarse no es un aviso, es una skill que NO carga.

Ejecutar: python3 -m pytest -q tests/test_export_interop.py   (o `python3 tests/test_export_interop.py`)
"""
import importlib.util
import json
import os
import re
import sys
import tomllib

import pytest

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Tope de `description` de una skill en OpenCode (doc oficial: «1-1024 characters»).
OPENCODE_DESC_MAX = 1024
# Eventos verificados en la documentación oficial de Codex, 2026-10-06.
CODEX_EVENTOS_OK = {"SessionStart", "UserPromptSubmit", "SubagentStop", "SessionEnd",
                    "PreToolUse", "PostToolUse", "Stop", "PreCompact", "PostCompact",
                    "SubagentStart", "PermissionRequest"}


def _mod():
    p = os.path.join(ROOT, "scripts", "export-interop.py")
    spec = importlib.util.spec_from_file_location("export_interop", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MOD = _mod()


def test_native_roles_map_and_exports_use_exact_owned_ids():
    plan = MOD.generar(ROOT)
    assert 'agent-kits/shared/native-roles.json' in plan
    mapping = json.loads(plan['agent-kits/shared/native-roles.json'])
    roles = [n for n, _, _ in MOD.piezas(ROOT, 'agents')]
    assert mapping == {'schema_version': 1, 'runtimes': {
        runtime: {n: ('custom-agents:' if runtime == 'claude' else 'custom-agents-') + n
                  for n in roles} for runtime in ('claude', 'codex', 'opencode')}}
    for role in roles:
        native = mapping['runtimes']['codex'][role]
        assert tomllib.loads(plan[f'interop/codex/agents/{native}.toml'])['name'] == native
        assert f'interop/opencode/agents/{native}.md' in plan
        assert f'interop/codex/agents/{role}.toml' not in plan


def test_delegation_adapts_owned_ids_without_rewriting_source_body():
    body = 'Delegate reviewer. Read agents/reviewer.md and user-reviewer instructions.\n'
    codex = MOD.codex_agente('architect', 'description: Own\ntools: Read', body)
    assert 'spawn_agent' in codex and 'agent_type' in codex
    assert 'reviewer → `custom-agents-reviewer`' in codex
    assert body in codex
    opencode = MOD.opencode_agente('architect', 'description: Own\ntools: Read', body)
    assert '`subagent`' in opencode and 'agent: "custom-agents-reviewer"' in opencode
    assert body in opencode


def test_obsolete_generated_exports_are_removed_without_touching_unowned_files(tmp_path, capsys):
    own = tmp_path / 'interop/codex/agents/architect.toml'
    own.parent.mkdir(parents=True)
    own.write_text(MOD.cabecera('toml', 'agents/architect.md') + 'old export\n', encoding='utf8')
    user = tmp_path / 'interop/codex/agents/consumer.toml'
    user.write_text('name = "consumer"\n', encoding='utf8')
    plan = {'interop/codex/agents/custom-agents-architect.toml': 'new export\n'}
    assert MOD.comprobar(str(tmp_path), plan) == 1
    assert 'OBSOLETO' in capsys.readouterr().out
    assert MOD.escribir(str(tmp_path), plan, quiet=True) == 0
    assert not own.exists() and user.read_text(encoding='utf8') == 'name = "consumer"\n'
    assert MOD.comprobar(str(tmp_path), plan) == 0


@pytest.mark.parametrize('quote', ['', '"'])
def test_codex_exports_known_launcher_runtime_and_pretool_registration(tmp_path, quote):
    (tmp_path / 'hooks').mkdir()
    command = 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" ' + quote + 'session-context.sh' + quote
    guard = 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" ' + quote + 'native-guardrail' + quote + ' --runtime=claude'
    src = {'hooks': {'SessionStart': [{'hooks': [{'command': command, 'timeout': 5}]}],
                     'PreToolUse': [{'matcher': 'Write|Bash', 'hooks': [{'command': guard, 'timeout': 5}]}]}}
    (tmp_path / 'hooks/hooks.json').write_text(json.dumps(src), encoding='utf8')
    hooks = json.loads(MOD.codex_hooks_json(str(tmp_path)))['hooks']
    assert hooks['SessionStart'][0]['hooks'][0]['command'] == command + ' --runtime=codex'
    assert hooks['PreToolUse'][0]['matcher'] == '^(Bash|apply_patch|PowerShell)$'
    assert hooks['PreToolUse'][0]['hooks'][0]['command'] == guard.replace('--runtime=claude', '--runtime=codex')


def test_opencode_v2_permission_actions_match_native_shell_and_subagent():
    permissions = MOD.permisos_opencode(['Read'])
    assert permissions['shell'] == 'deny' and permissions['subagent'] == 'deny'
    assert 'bash' not in permissions and 'task' not in permissions
    permissions = MOD.permisos_opencode(['Read', 'Bash', 'Agent'])
    assert permissions['shell'] == 'allow' and permissions['subagent'] == 'allow'


def test_guard_description_uses_the_same_native_map_as_exported_name():
    mapping = {'schema_version': 1, 'runtimes': {'codex': {'architect': 'custom-agents-own-architect'}}}
    exported = tomllib.loads(MOD.codex_agente('architect', 'description: Owned\ntools: Read, Edit', 'Own body', mapping))
    assert exported['name'] == 'custom-agents-own-architect'
    assert 'ID exacto `custom-agents-own-architect`' in exported['developer_instructions']
    assert '{native_id}' not in exported['developer_instructions']


def test_opencode_exporta_paquete_nativo_y_config_sin_instructions():
    plan = MOD.generar(ROOT)
    package = json.loads(plan['interop/opencode/plugins/custom-agents/package.json'])
    assert package['type'] == 'module' and package['main'] == 'index.js'
    assert 'interop/opencode/plugins/custom-agents/index.js' in plan
    assert 'interop/opencode/plugins/custom-agents-hooks.js' not in plan
    config = json.loads(plan['interop/opencode/opencode.json'])
    assert config['plugins'] == ['./.opencode/plugins/custom-agents']
    assert 'instructions' not in config


def test_exportacion_detecta_artefactos_ausentes_y_modificados(tmp_path, capsys):
    plan = {'interop/codex/hooks.json': '{"hooks": {}}\n', 'interop/opencode/opencode.json': '{}\n'}
    assert MOD.escribir(str(tmp_path), plan, quiet=True) == 0
    assert MOD.comprobar(str(tmp_path), plan) == 0
    (tmp_path / 'interop/codex/hooks.json').write_text('changed', encoding='utf8')
    (tmp_path / 'interop/opencode/opencode.json').unlink()
    assert MOD.comprobar(str(tmp_path), plan) == 1
    output = capsys.readouterr().out
    assert 'DESINCRONIZADO interop/codex/hooks.json' in output
    assert 'FALTA         interop/opencode/opencode.json' in output


def test_indice_opencode_degrada_si_falta_el_kit(tmp_path):
    for folder in ('agents', 'commands', 'skills/demo'):
        (tmp_path / folder).mkdir(parents=True)
    (tmp_path / 'agents/demo.md').write_text('---\ndescription: Demo agent.\n---\nBody', encoding='utf8')
    (tmp_path / 'skills/demo/SKILL.md').write_text('---\nname: demo\ndescription: Demo skill.\n---\nBody', encoding='utf8')
    index = MOD.opencode_indice(str(tmp_path))
    assert '**Agentes**' in index and '**Skills**' in index
    assert 'Demo agent' in index and 'Demo skill' in index


def leer(rel):
    with open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------------------------- 1. sincronía

def test_arbol_generado_al_dia():
    """`--check` en verde: lo del disco == lo que produciría el generador ahora mismo."""
    plan = MOD.generar(ROOT)
    desincronizados = []
    for rel, contenido in plan.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            desincronizados.append("FALTA " + rel)
        elif leer(rel) != contenido:
            desincronizados.append("DISTINTO " + rel)
    assert not desincronizados, ("interop desincronizada; corre `python3 scripts/export-interop.py`:\n  "
                                 + "\n  ".join(desincronizados))


def test_generacion_determinista():
    """Dos generaciones seguidas dan exactamente el mismo árbol (ni fechas ni orden aleatorio)."""
    assert MOD.generar(ROOT) == MOD.generar(ROOT)


def test_cubre_todas_las_piezas():
    """Cada agente y cada comando del repo tiene su traducción en LOS DOS runtimes."""
    plan = MOD.generar(ROOT)
    agentes = [f[:-3] for f in sorted(os.listdir(os.path.join(ROOT, "agents"))) if f.endswith(".md")]
    comandos = [f[:-3] for f in sorted(os.listdir(os.path.join(ROOT, "commands"))) if f.endswith(".md")]
    faltan = [r for n in agentes for r in (f"interop/codex/agents/custom-agents-{n}.toml",
                                           f"interop/opencode/agents/custom-agents-{n}.md") if r not in plan]
    faltan += [r for n in comandos for r in (f"interop/codex/prompts/{n}.md",
                                             f"interop/opencode/commands/{n}.md") if r not in plan]
    assert not faltan, "piezas sin traducir: %s" % faltan


# --------------------------------------------------------------------- 2. formato

def test_codex_agentes_toml_valido():
    """TOML parseable con las tres claves que Codex exige, y `developer_instructions` con cuerpo."""
    base = os.path.join(ROOT, "interop", "codex", "agents")
    for fn in sorted(os.listdir(base)):
        with open(os.path.join(base, fn), "rb") as f:
            d = tomllib.load(f)
        for k in ("name", "description", "developer_instructions"):
            assert d.get(k), "%s: falta o está vacía la clave obligatoria `%s`" % (fn, k)
        assert d["name"] == fn[:-5], "%s: `name` debe coincidir con el fichero" % fn
        assert len(d["developer_instructions"]) > 500, "%s: cuerpo sospechosamente corto" % fn
        if "model_reasoning_effort" in d:
            assert d["model_reasoning_effort"] in ("low", "medium", "high", "xhigh", "max"), fn


def test_codex_manifiesto_apunta_a_lo_que_existe():
    m = json.loads(leer(".codex-plugin/plugin.json"))
    assert m["name"] == "custom-agents"
    for clave in ("skills", "hooks"):
        destino = m[clave].lstrip("./")
        assert os.path.exists(os.path.join(ROOT, destino.replace("/", os.sep))), \
            "plugin.json `%s` apunta a %s, que no existe" % (clave, m[clave])
    # La versión no puede divergir del manifiesto de Claude Code (los bumpea `release.py` juntos).
    assert m["version"] == json.loads(leer(".claude-plugin/plugin.json"))["version"]
    assert m["interface"]["displayName"]


def test_codex_marketplace_valido():
    mk = json.loads(leer(".agents/plugins/marketplace.json"))
    assert mk["plugins"], "marketplace sin plugins"
    p = mk["plugins"][0]
    assert p["policy"]["installation"] in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE")
    # Codex ≥ 0.155 (esquema serde) solo admite estos dos valores: un `NONE` invalida el manifiesto
    # ENTERO y rompe `codex plugin marketplace list` para TODOS los marketplaces del usuario
    # (gap M-01, verificado con codex-cli 0.155.1 en Windows).
    assert p["policy"]["authentication"] in ("ON_INSTALL", "ON_USE"), \
        "authentication no válido para Codex: %r" % p["policy"]["authentication"]
    assert p["category"] and p["source"]["source"] == "local"
    assert p["version"] == json.loads(leer(".claude-plugin/plugin.json"))["version"]


def test_codex_hooks_solo_eventos_que_dispara():
    h = json.loads(leer("interop/codex/hooks.json"))["hooks"]
    assert h, "hooks.json de Codex vacío"
    desconocidos = set(h) - CODEX_EVENTOS_OK
    assert not desconocidos, "eventos que Codex no conoce: %s" % desconocidos
    assert h["PostToolUse"][0]["matcher"] == "^apply_patch$"
    assert len(h["PostToolUse"][0]["hooks"]) == 3
    for grupo in h.get("SessionStart", []):
        assert "compact" in grupo.get("matcher", "")


def test_codex_session_end_va_en_shell_form_no_exec_form():
    """Gap 16 de la revisión intento 1 (C5 · CWE-78): Codex no tiene el contrato de `args` (exec
    form) verificado como Claude Code; `SessionEnd` (declarado en exec form en `hooks/hooks.json`)
    se traduce a shell form (`bash "<ruta>"`) para la interop, sin `args` sueltos. Gap 36 de la
    revisión intento 2: la cadena se construye por interpolación directa entre comillas DOBLES
    (nunca `shlex.quote`), segura porque el argumento ya pasó el patrón `_ARG_SEGURO_RE`. Gap 49 de
    la revisión intento 3 (A-49): el formato es IDÉNTICO —comillas DOBLES— al de los otros cuatro
    hooks del mismo fichero (antes `shlex.quote` producía comillas simples aquí, un formato
    distinto sin ninguna fuente que confirme cuál expande Codex de verdad)."""
    src = json.loads(leer("hooks/hooks.json"))["hooks"]["SessionEnd"][0]["hooks"][0]
    assert src.get("args"), "hooks/hooks.json ya no declara SessionEnd en exec form: revisa este test"
    h = json.loads(leer("interop/codex/hooks.json"))["hooks"]["SessionEnd"][0]["hooks"][0]
    assert "args" not in h
    assert h["command"] == ('node "%s" "%s"' % tuple(src["args"])) + ' --runtime=codex'
    assert h.get("timeout") == 3
    # mismo formato (comillas dobles) que los otros hooks de shell form del propio fichero
    otro = json.loads(leer("interop/codex/hooks.json"))["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert otro.startswith('node "') and h["command"].startswith('node "')


def test_codex_hooks_respetan_limite_session_end_y_runner_windows():
    hooks = json.loads(MOD.codex_hooks_json(ROOT))["hooks"]
    assert hooks["SessionEnd"][0]["hooks"][0]["command"].endswith(' --runtime=codex')
    assert hooks["SessionEnd"][0]["hooks"][0]["timeout"] == 3
    assert hooks["UserPromptSubmit"][0]["hooks"][0]["timeout"] == 5
    for groups in hooks.values():
        for group in groups:
            for hook in group["hooks"]:
                assert hook["command"].startswith('node "')
                assert 'run-hook.mjs' in hook["command"]


def test_hook_a_shell_form_pasa_intacto_lo_que_no_es_exec_form():
    """Un hook sin `args` (la mayoría: ya en shell form) no lo toca `_hook_a_shell_form`."""
    h = {"type": "command", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"', "timeout": 5}
    assert MOD._hook_a_shell_form(h, "UserPromptSubmit") == h


def test_hook_a_shell_form_falla_con_args_invalidos_en_vez_de_exportar_tal_cual():
    """Gap 36 (B12): un hook con `command: bash` y `args` de forma inválida (≠ 1 arg, o un arg con
    metacaracteres de shell) se exportaba TAL CUAL, sin traducir y sin ningún aviso — la peor
    combinación posible. Ahora `ValueError` nombrando el evento, y NUNCA se llega a construir/
    emitir una cadena `command`."""
    base = {"type": "command", "command": "bash"}
    casos = [
        {**base, "args": []},                                    # 0 argumentos
        {**base, "args": ["a.sh", "b.sh"]},                       # 2 argumentos
        {**base, "args": ["$(rm -rf /)"]},                        # `$(` — command substitution
        {**base, "args": ['"; rm -rf / #']},                      # `"` — rompe las comillas
        {**base, "args": ["`whoami`"]},                           # backtick
        {**base, "args": ["python3 -c 'evil()'"]},                # espacios (ni siquiera un arg único válido)
    ]
    for h in casos:
        with pytest.raises(ValueError, match="SessionEnd"):
            MOD._hook_a_shell_form(h, "SessionEnd")


def test_hook_a_shell_form_arg_seguro_con_placeholder_no_lanza():
    """El patrón seguro SÍ admite `${CLAUDE_PLUGIN_ROOT}` (placeholder que Codex sustituye antes de
    pasar el `command` a una shell): no debe fallar el caso normal."""
    h = {"type": "command", "command": "bash", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/session-journal.sh"]}
    nh = MOD._hook_a_shell_form(h, "SessionEnd")
    assert "args" not in nh and nh["command"].startswith("bash ")


def test_hook_a_shell_form_command_bash_produce_comillas_dobles_no_shlex_quote():
    """Gap 49 (A-49): el `command` traducido usa comillas DOBLES por interpolación directa, NUNCA
    `shlex.quote` (que sobre un valor con `$`/`{`/`}` produce comillas simples — un formato distinto
    al de los otros hooks de `interop/codex/hooks.json`, sin fuente que confirme que Codex las
    expande igual)."""
    h = {"type": "command", "command": "bash", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"]}
    nh = MOD._hook_a_shell_form(h, "SessionEnd")
    assert nh["command"] == 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"'
    assert "'" not in nh["command"]


def test_hook_a_shell_form_intercepta_sh_no_solo_bash():
    """Gap 53 (B-52): el intérprete traducible no es solo `bash` — `sh` también es shell form
    seguro con el mismo patrón."""
    h = {"type": "command", "command": "sh", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"]}
    nh = MOD._hook_a_shell_form(h, "SessionEnd")
    assert "args" not in nh and nh["command"] == 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"'


def test_hook_a_shell_form_falla_con_command_no_literal_bash_o_sh_con_args():
    """Gap 53 (B-52 · CWE-78 latente): antes solo se interceptaba `command == "bash"` EXACTO —
    `/bin/bash`, `python3` (u otro intérprete cualquiera) con `args` se exportaban a Codex TAL CUAL,
    exit 0, sin ningún aviso, pese a que el docstring prometía traducir TODO exec form. Ahora
    cualquier `command` con `args` que no sea `bash`/`sh` literal hace fallar el export."""
    casos = [
        {"type": "command", "command": "/bin/bash", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/x.sh"]},
        {"type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/x.py"]},
        {"type": "command", "command": "bash", "args": ["a.sh", "b.sh"]},   # dos argumentos
    ]
    for h in casos:
        with pytest.raises(ValueError, match="SessionEnd"):
            MOD._hook_a_shell_form(h, "SessionEnd")


def test_opencode_agentes_frontmatter():
    """Frontmatter con `description`, `mode` y `permission`; el cuerpo conserva el prompt."""
    base = os.path.join(ROOT, "interop", "opencode", "agents")
    for fn in sorted(os.listdir(base)):
        t = leer("interop/opencode/agents/" + fn)
        bloque, cuerpo = MOD.partir_frontmatter(t)
        assert bloque, "%s: sin frontmatter" % fn
        assert MOD.campo(bloque, "description"), "%s: sin description" % fn
        assert re.search(r"^mode: (subagent|primary|all)$", bloque, re.M), "%s: `mode` inválido" % fn
        assert re.search(r"^permission:$", bloque, re.M), "%s: sin bloque `permission`" % fn
        assert len(cuerpo) > 500, "%s: cuerpo sospechosamente corto" % fn


def test_opencode_config_valida():
    cfg = json.loads(leer("interop/opencode/opencode.json"))
    assert cfg["$schema"] == "https://opencode.ai/config.json"
    assert cfg["plugins"] == ["./.opencode/plugins/custom-agents"]
    assert "instructions" not in cfg


def test_opencode_adaptador_de_hooks_es_copia_fiel():
    """El .js de interop es copia EXACTA de su fuente en hooks/ (una sola fuente de verdad)."""
    assert leer("interop/opencode/plugins/custom-agents/index.js") == leer("hooks/opencode-plugin.js")


def test_generados_llevan_marca():
    """Todo fichero generado se identifica como tal (nadie lo edita a mano por error)."""
    sin_marca = [rel for rel, txt in MOD.generar(ROOT).items()
                 if MOD.MARCA not in txt and not rel.endswith((".json", ".js"))]
    assert not sin_marca, "generados sin cabecera «GENERADO»: %s" % sin_marca


# --------------------------------------------------------------------- 3. invariantes

def test_reviewer_no_declara_sandbox_independiente_inexistente():
    """Codex 0.161.0 conserva permisos del padre: el TOML no impone read-only."""
    with open(os.path.join(ROOT, "interop", "codex", "agents", "custom-agents-reviewer.toml"), "rb") as f:
        codex = tomllib.load(f)
    assert "sandbox_mode" not in codex, "Codex ignora este campo por rol; no debe exportarse como protección"
    bloque, _ = MOD.partir_frontmatter(leer("interop/opencode/agents/custom-agents-reviewer.md"))
    assert re.search(r"^\s+edit: deny$", bloque, re.M), "reviewer con `edit` permitido en OpenCode"


def test_agentes_con_escritura_la_conservan():
    """La traducción no puede DEJAR SIN herramientas a quien las declara (p. ej. implementer)."""
    bloque, _ = MOD.partir_frontmatter(leer("interop/opencode/agents/custom-agents-implementer.md"))
    assert re.search(r"^\s+edit: allow$", bloque, re.M)
    assert re.search(r"^\s+shell: allow$", bloque, re.M)


def test_descripciones_de_skill_caben_en_opencode():
    """OpenCode valida `description` en 1-1024 caracteres: pasarse = skill que no carga."""
    largas = []
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        p = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            bloque, _ = MOD.partir_frontmatter(f.read())
        n = len(MOD.campo(bloque, "description"))
        assert n, "skill `%s`: sin description (OpenCode y Codex la exigen)" % d
        if n > OPENCODE_DESC_MAX:
            largas.append("%s (%d)" % (d, n))
    assert not largas, ("descriptions por encima de %d caracteres — OpenCode NO cargaría la skill: %s"
                        % (OPENCODE_DESC_MAX, ", ".join(largas)))


def test_skills_nombre_coincide_con_carpeta():
    """Requisito de los dos runtimes: `name` == carpeta, kebab-case."""
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        p = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            bloque, _ = MOD.partir_frontmatter(f.read())
        assert MOD.campo(bloque, "name") == d, "skill `%s`: `name` no coincide con la carpeta" % d
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d), "skill `%s`: no es kebab-case" % d


def test_campo_plieta_escalares_de_bloque():
    """`campo()` entiende `>` y `|` de YAML: 12 de las 17 skills escriben así su description."""
    bloque = "name: x\ndescription: >\n  linea uno\n  linea dos\nmodel: opus\n"
    assert MOD.campo(bloque, "description") == "linea uno linea dos"
    assert MOD.campo(bloque, "model") == "opus"
    assert MOD.campo("description: plano\n", "description") == "plano"
    assert MOD.campo("a: 1\n", "ausente") == ""


def test_toml_multi_escapa_cuerpo_con_triple_comilla():
    """Un cuerpo con `'''` no puede romper el TOML generado."""
    out = MOD.toml_multi("texto con ''' dentro")
    assert out.startswith('"""'), "debería caer al literal escapado"
    assert tomllib.loads("k = " + out)["k"].strip() == "texto con ''' dentro"


def _tests():
    return [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in _tests():
        try:
            fn()
            print("ok   %s" % nombre)
        except AssertionError as e:
            fallos += 1
            print("FAIL %s\n     %s" % (nombre, e))
    print("\ntest_export_interop: %d casos · %d fallo(s)" % (len(_tests()), fallos))
    sys.exit(1 if fallos else 0)
