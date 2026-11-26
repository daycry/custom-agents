"""plugin-audit-2 T-17: una receta del kit por pieza.

La receta que localiza el bundle (regla 5 de docs/CONVENTIONS.md) se repetía por paso: 19 veces en
9 agentes y 14 en 9 comandos. Cada agente o comando la escribe UNA vez y esa receta define todas las
variables de kit que la pieza usa (`SHAREDKIT`, `EVALKIT`, `DEVKIT`…); si consulta un `SHAREDKIT`
heredado, solo lo acepta absoluto. La ejecución real sin `CLAUDE_PLUGIN_ROOT` (raíces `.codex` y
`.opencode` falsas) vive en tests/test_plugin_root_resolution.py.
"""
import functools
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARCA = 'M=agent-kits/shared/ledger-lint.py'
ASIGNA = re.compile(r'\b([A-Z][A-Z_]*)="\$\{R:\+\$R/[^"]+\}"')
ABSOLUTO = 'case "$SHAREDKIT" in /*|?:*)'


def piezas():
    return sorted(p for d in ('agents', 'commands') for p in (ROOT / d).glob('*.md'))


@functools.lru_cache(maxsize=None)
def variables_de_kit():
    """Nombres que alguna receta del repo asigna con `${R:+$R/…}` (SHAREDKIT, EVALKIT, DASH…)."""
    nombres = set()
    for d in ('agents', 'commands', 'skills'):
        for p in (ROOT / d).rglob('*.md'):
            nombres |= set(ASIGNA.findall(p.read_text(encoding='utf-8')))
    return frozenset(nombres)


def receta(texto):
    return next((l for l in texto.splitlines() if MARCA in l), None)


@pytest.mark.parametrize('pieza', piezas(), ids=lambda p: f'{p.parent.name}/{p.name}')
def test_como_mucho_una_receta_por_pieza(pieza):
    n = pieza.read_text(encoding='utf-8').count(MARCA)
    assert n <= 1, f'{pieza.parent.name}/{pieza.name}: {n} recetas; resuelve el kit una vez y reutiliza las variables'


@pytest.mark.parametrize('pieza', piezas(), ids=lambda p: f'{p.parent.name}/{p.name}')
def test_la_receta_define_todas_las_variables_de_kit_que_usa_la_pieza(pieza):
    texto = pieza.read_text(encoding='utf-8')
    usadas = {v for v in variables_de_kit() if re.search(r'\$\{?' + v + r'\b', texto)}
    if not usadas:
        return
    linea = receta(texto)
    assert linea, f'{pieza.parent.name}/{pieza.name} usa {sorted(usadas)} sin receta que las defina'
    definidas = set(ASIGNA.findall(linea))
    assert usadas <= definidas, f'{pieza.parent.name}/{pieza.name}: la receta no define {sorted(usadas - definidas)}'


@pytest.mark.parametrize('pieza', piezas(), ids=lambda p: f'{p.parent.name}/{p.name}')
def test_un_sharedkit_heredado_solo_se_acepta_absoluto(pieza):
    linea = receta(pieza.read_text(encoding='utf-8')) or ''
    consulta = linea.split(MARCA, 1)[-1].split('R="${R%/$M}"', 1)[0]
    if '$SHAREDKIT' in consulta:
        assert ABSOLUTO in consulta, f'{pieza.parent.name}/{pieza.name}: SHAREDKIT relativo aceptado'


def test_el_recuento_baja_a_una_receta_por_fichero():
    total = sum(p.read_text(encoding='utf-8').count(MARCA) for p in piezas())
    con_receta = sum(MARCA in p.read_text(encoding='utf-8') for p in piezas())
    assert total == con_receta


SOBREVIVE = re.compile(r'variables\s+no\s+sobreviven\s+entre\s+(llamadas|bloques)', re.I)


def bloque_de_la_receta(texto):
    """(inicio, fin) del bloque cercado que contiene la receta; la línea sola si no va cercada."""
    i = texto.index(MARCA)
    ini = texto.rfind('```', 0, i)
    fin = texto.find('```', i)
    if ini < 0 or fin < 0:
        return texto.rfind('\n', 0, i) + 1, texto.find('\n', i)
    return ini, fin + 3


@pytest.mark.parametrize('pieza', piezas(), ids=lambda p: f'{p.parent.name}/{p.name}')
def test_fix1_gap6_la_receta_avisa_de_reutilizar_la_ruta_si_hay_usos_en_otras_llamadas(pieza):
    """plugin-audit-2 revisión intento 1, gap 6: si la pieza usa sus variables de kit fuera del bloque
    de la receta, junto a la receta dice que la ruta absoluta se reutiliza en cada llamada porque las
    variables no sobreviven entre llamadas de Bash (analyst y qa no lo decían)."""
    texto = pieza.read_text(encoding='utf-8')
    linea = receta(texto)
    if not linea:
        return
    ini, fin = bloque_de_la_receta(texto)
    fuera = texto[:ini] + texto[fin:]
    usadas = {v for v in ASIGNA.findall(linea) if re.search(r'\$\{?' + v + r'\b', fuera)}
    if not usadas:
        return
    junto = texto[max(0, ini - 400):ini] + texto[fin:fin + 400]
    assert SOBREVIVE.search(junto), (f'{pieza.parent.name}/{pieza.name} usa {sorted(usadas)} fuera de la receta y no '
                                     'avisa de que las variables no sobreviven entre llamadas de Bash')
