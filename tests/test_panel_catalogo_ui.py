"""T-36: Catálogo con filtros por tipo, origen y runtime (CA-28, CA-29).

Dos capas: el HTML que genera `build_panel.py` (controles nativos con nombre accesible y zona de estado) y el JS
de la página ejecutado en Node con un DOM falso. Los filtros son solo del cliente: `--json` no cambia (golden)."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from test_panel_live_ui import inventory, panel  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[1]
PAGE_JS = ROOT / 'skills/plugin-panel/assets/page-catalogo.js'

NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(not NODE, reason='Node no disponible')


def _node(cuerpo):
    programa = ('global.window = global;\nconst assert = require("node:assert/strict");\n'
                'const control = (value) => ({value, handlers:{}, addEventListener(t,f){this.handlers[t]=f;}});\n'
                'const card = (dataset, text) => ({dataset, textContent:text||"", hidden:false});\n'
                'function montar(id, cards, extra){const c={search:control(""),result:{textContent:""},'
                'detail:{textContent:""}};Object.assign(c,extra||{});c[id]={querySelectorAll(){return cards;}};'
                'global.document={getElementById(i){return c[i];}};return c;}\n'
                'require(' + json.dumps(str(PAGE_JS)) + ');\nconst P = global.PanelCatalogo;\n' + cuerpo)
    r = subprocess.run([NODE, '-e', programa], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stdout + r.stderr


DESGLOSE = ("{id:'detail',groups:[['scope','Por origen',[['project','Proyecto'],['user','Usuario'],['local','Local']]],"
            "['runtime','Por runtime',[['codex','Codex'],['opencode','OpenCode']]]]}")


def test_el_conteo_por_origen_y_runtime_cambia_con_los_filtros_combinados():
    _node('''
const cards=[card({kind:'agent',scope:'project',runtime:'codex'}),card({kind:'agent',scope:'user',runtime:'opencode'}),
 card({kind:'skill',scope:'user',runtime:'codex'})];
const c=montar('extensions',cards,{kind:control('all'),scope:control('all'),runtime:control('all')});
P.connectFilters('extensions','search','result',[['kind','kind'],['scope','scope'],['runtime','runtime']],'declaraciones',DESGLOSE);
assert.equal(c.result.textContent,'3 declaraciones visibles');
assert.equal(c.detail.textContent,'Por origen: Proyecto 1 · Usuario 2 · Local 0. Por runtime: Codex 2 · OpenCode 1.');
c.scope.value='user';c.scope.handlers.change();
assert.deepEqual(cards.map(x=>x.hidden),[true,false,false]);
assert.equal(c.detail.textContent,'Por origen: Proyecto 0 · Usuario 2 · Local 0. Por runtime: Codex 1 · OpenCode 1.');
c.runtime.value='codex';c.runtime.handlers.change();
assert.deepEqual(cards.map(x=>x.hidden),[true,true,false]);
assert.equal(c.result.textContent,'1 declaraciones visibles');
assert.match(c.detail.textContent,/Usuario 1/);
'''.replace('DESGLOSE', DESGLOSE))


def test_el_conteo_por_tipo_del_catalogo_sigue_a_la_busqueda_y_a_la_seleccion():
    _node('''
const cards=[card({kind:'agents'},'planner'),card({kind:'skills'},'tdd'),card({kind:'hooks',runtime:'codex'},'hook')];
const c=montar('catalog',cards,{kind:control('all'),'hook-runtime':control('all')});
P.connectFilters('catalog','search','result',[['kind','kind'],['hook-runtime','runtime']],'capacidades',
  {id:'detail',groups:[['kind','Por tipo',[['agents','Agentes'],['skills','Skills'],['hooks','Hooks']]]]});
assert.equal(c.detail.textContent,'Por tipo: Agentes 1 · Skills 1 · Hooks 1.');
c.search.value='tdd';c.search.handlers.input();
assert.equal(c.result.textContent,'1 capacidades visibles');
assert.equal(c.detail.textContent,'Por tipo: Agentes 0 · Skills 1 · Hooks 0.');
''')


def test_sin_zona_de_desglose_el_filtro_funciona_igual():
    _node('''
const cards=[card({kind:'agents'})];
const c=montar('catalog',cards,{kind:control('all')});
P.connectFilters('catalog','search','result',[['kind','kind']],'capacidades');
assert.equal(c.result.textContent,'1 capacidades visibles');
''')


def test_html_del_catalogo_tiene_controles_nativos_con_nombre_y_zonas_de_estado(panel, inventory):
    cuerpo = panel.cuerpos_paginas(inventory)['catalogo']
    for ident in ('kind', 'hook-runtime', 'extension-kind', 'extension-scope', 'extension-runtime'):
        assert re.search(r'<select id="%s" aria-label="[^"]+"' % ident, cuerpo), ident
    for ident in ('search', 'extension-search'):
        assert re.search(r'<input id="%s" type="search"[^>]*aria-label="[^"]+"' % ident, cuerpo), ident
    for ident in ('results', 'results-detail', 'extension-results', 'extension-detail'):
        assert re.search(r'<p id="%s"[^>]*aria-live="polite"' % ident, cuerpo), ident
    assert 'tabindex' not in cuerpo.split('id="catalog"')[1].split('id="extensions"')[0].split('<article')[0]


def test_iniciar_conecta_los_desgloses_de_las_dos_secciones():
    fuente = PAGE_JS.read_text(encoding='utf8')
    assert "'results-detail'" in fuente and "'extension-detail'" in fuente
    assert not re.search(r'innerHTML|outerHTML|insertAdjacentHTML|eval\(|fetch\(|XMLHttpRequest', fuente)
