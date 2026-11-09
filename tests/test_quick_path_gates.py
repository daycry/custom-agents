"""H-15 / H-16 (auditoría 2026-11-09): la vía rápida tiene un camino de QA ejecutable y la
Lente A comprueba la evidencia TDD.

- El implementer acepta el `tasks.md` ligero sin `improvement-plan.md`.
- `qa` y el orquestador aceptan `test-plan: n/a (sin UI)` en el frontmatter de `tasks.md`.
- La Lente A pide la línea `RED:` (o `TDD n/a`) con `tdd: true`.
- quick-implement encuentra el método también en Codex, cuyo plugin no lleva `commands/`.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

import test_hooks_shell as legacy

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'test-plan: n/a (sin UI)'


def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_h15_implementer_acepta_el_ledger_ligero_sin_plan():
    entrada = next(line for line in text('agents/implementer.md').splitlines()
                   if line.startswith('- **Entrada:**'))
    assert 'vía rápida' in entrada and 'tasks.md' in entrada and 'ligero' in entrada, entrada


def test_h15_qa_acepta_el_marcador_en_el_tasks_md_ligero():
    qa = text('agents/qa.md')
    regla = next(line for line in qa.splitlines() if MARKER in line and 'frontmatter' in line)
    assert 'tasks.md' in regla.split('**', 2)[-1][:400], regla[:400]


def test_h15_dev_cycle_qa_lee_el_marcador_del_ledger_ligero():
    core = text('commands/dev-cycle.md')
    rapida = next(line for line in core.splitlines() if line.startswith('- **Vía rápida**'))
    assert MARKER in rapida, 'el tasks.md ligero declara el marcador cuando no hay UI'
    qa = next(line for line in core.splitlines() if line.startswith('3. **`qa`**'))
    assert 'tasks.md' in qa and 'vía rápida' in qa, qa[:300]


def test_h16_lente_a_comprueba_la_evidencia_tdd():
    prompts = text('skills/adversarial-review/references/lens-prompts.md')
    lente_a = next(line for line in prompts.splitlines() if line.startswith('- **Lente A'))
    assert 'tdd: true' in lente_a and 'RED:' in lente_a and 'TDD n/a' in lente_a
    assert re.search(r'RED:.{0,400}gap Important', lente_a, re.S), 'sin evidencia del rojo es gap'


def test_h16_tdd_apunta_al_criterio_real_de_la_lente_a():
    tdd = text('skills/tdd/SKILL.md')
    assert 'criterio (5b)' in tdd and 'lens-prompts.md' in tdd


@pytest.mark.skipif(legacy.BASH is None, reason='la receta de resolución necesita Bash')
def test_h15_quick_implement_resuelve_dev_cycle_en_el_plugin_de_codex(tmp_path):
    project = tmp_path / 'consumer'
    home = tmp_path / 'home'
    project.mkdir()
    home.mkdir()
    bundle = project / '.codex/plugins/fixture'
    (bundle / 'agent-kits/shared').mkdir(parents=True)
    (bundle / 'agent-kits/shared/ledger-lint.py').write_text('#\n', encoding='utf-8')
    command = bundle / 'interop/codex/command-skills/custom-agents-dev-cycle/references/command.md'
    command.parent.mkdir(parents=True)
    command.write_text('metodo-de-la-via-rapida\n', encoding='utf-8')
    skill = text('skills/quick-implement/SKILL.md')
    recipe = re.search(r'```bash\n> (R=.*?)\n> ```', skill, re.S)[1]
    recipe += '\nprintf "%s\\n" "$DEVCYCLE"\ncat "$DEVCYCLE"\n'
    env = {**os.environ, 'HOME': str(home), 'USERPROFILE': str(home)}
    env.pop('CLAUDE_PLUGIN_ROOT', None)
    result = subprocess.run([legacy.BASH, '-c', recipe], cwd=project, env=env, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=60)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines[-1] == 'metodo-de-la-via-rapida'
    assert lines[-2].replace('\\', '/').endswith('custom-agents-dev-cycle/references/command.md')


# ------------------------------------------------- revisión intento 1 (fase 2): A3, A4, A2

def test_fix1_a3_la_via_rapida_con_interfaz_va_al_flujo_completo():
    quick = text('skills/quick-implement/SKILL.md')
    fila = next(line for line in quick.splitlines() if line.startswith('| Toca interfaz'))
    assert 'flujo completo' in fila.lower() and 'test-plan.md' in fila and 'planner' in fila
    core = text('commands/dev-cycle.md')
    rapida = next(line for line in core.splitlines() if line.startswith('- **Vía rápida**'))
    assert 'con interfaz, flujo completo' in rapida


def test_fix1_a4_las_piezas_dicen_que_el_marcador_tambien_vale_en_tasks_md():
    contracts = next(line for line in text('docs/agents/CONTRACTS.md').splitlines() if line.startswith('| E1 '))
    assert 'en la vía rápida, de `tasks.md`' in contracts
    assert 'en la vía rápida, el `tasks.md` ligero' in text('docs/agents/qa.md')
    qa_p1 = next(line for line in text('agents/qa.md').splitlines() if line.startswith('**P1.'))
    impl_p1 = next(line for line in text('agents/implementer.md').splitlines() if line.startswith('**P1. Contexto.**'))
    assert 'vía rápida' in qa_p1 and 'vía rápida' in impl_p1


def test_fix1_a2_el_aviso_de_ledger_lint_sin_red_queda_como_deuda_en_t21():
    ledger = ' '.join(text('docs/roadmap/2026-11-09-plugin-audit-remediation/tasks.md').split())
    t21 = ledger[ledger.index('### T-21'):]
    assert 'aviso de ledger-lint' in t21 and 'RED:' in t21



def test_fix2_a_m2_modo_rapido_explicito_y_recomendacion_excluyen_la_interfaz():
    core = text('commands/dev-cycle.md')
    explicito = next(line for line in core.splitlines() if line.startswith('- **Vía rápida explícita:**'))
    recomendacion = next(line for line in core.splitlines() if line.startswith('**Recomendación por defecto'))
    assert 'interfaz' in explicito and 'flujo completo' in explicito
    assert 'interfaz' in recomendacion
