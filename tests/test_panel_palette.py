"""T-06: la paleta del panel cumple WCAG 2.2 AA (contraste 1.4.3 y 1.4.11), leída del CSS real."""
from itertools import combinations
from pathlib import Path
import re

CSS = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/assets/panel.css'

# (primer plano, fondo, umbral, para qué). Texto normal 4,5:1; marcas, bordes y foco 3:1.
PARES = (
    ('texto', 'fondo', 4.5, 'texto sobre el fondo'),
    ('texto', 'superficie', 4.5, 'texto sobre las tarjetas'),
    ('tenue', 'fondo', 4.5, 'texto secundario sobre el fondo'),
    ('tenue', 'superficie', 4.5, 'texto secundario sobre las tarjetas'),
    ('acento', 'fondo', 4.5, 'enlaces y acentos sobre el fondo'),
    ('acento', 'superficie', 4.5, 'enlaces y acentos sobre las tarjetas'),
    ('ok', 'superficie', 4.5, 'estado correcto como texto'),
    ('aviso', 'superficie', 4.5, 'estado de aviso como texto'),
    ('error', 'superficie', 4.5, 'estado de error como texto'),
    ('fondo', 'texto', 4.5, 'enlace de salto (fondo sobre texto)'),
    ('borde', 'fondo', 3.0, 'bordes sobre el fondo'),
    ('borde', 'superficie', 3.0, 'bordes sobre las tarjetas'),
    ('foco', 'fondo', 3.0, 'anillo de foco sobre el fondo'),
    ('foco', 'superficie', 3.0, 'anillo de foco sobre las tarjetas'),
) + tuple((f'serie-{n}', fondo, 3.0, f'marca de la serie {n} sobre {fondo}')
          for n in range(1, 7) for fondo in ('fondo', 'superficie'))

NOMBRES = {n for par in PARES for n in par[:2]}


def _lineal(canal):
    canal /= 255
    return canal / 12.92 if canal <= 0.03928 else ((canal + 0.055) / 1.055) ** 2.4


def luminancia(hexa):
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lineal(r) + 0.7152 * _lineal(g) + 0.0722 * _lineal(b)


def contraste(a, b):
    mayor, menor = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (mayor + 0.05) / (menor + 0.05)


def leer_paleta(css):
    raiz = re.search(r':root\s*\{(.*?)\}', css, re.S)
    assert raiz, 'el CSS no declara :root'
    return {m.group(1): m.group(2).lower()
            for m in re.finditer(r'--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;', raiz.group(1))}


def verificar(paleta):
    """Devuelve la lista de incumplimientos; vacía si la paleta es válida."""
    fallos = [f'falta la propiedad --{n}' for n in sorted(NOMBRES) if n not in paleta]
    if fallos:
        return fallos
    for fg, bg, umbral, motivo in PARES:
        valor = contraste(paleta[fg], paleta[bg])
        if valor < umbral:
            fallos.append(f'{motivo}: --{fg} {paleta[fg]} sobre --{bg} {paleta[bg]} = {valor:.2f}:1 < {umbral}:1')
    series = [paleta[f'serie-{n}'] for n in range(1, 7)]
    for (i, a), (j, b) in combinations(enumerate(series, 1), 2):
        if a == b:
            fallos.append(f'las series {i} y {j} comparten color {a}')
    return fallos


def test_la_paleta_real_cumple_todos_los_umbrales():
    paleta = leer_paleta(CSS.read_text(encoding='utf-8'))
    assert verificar(paleta) == []


def test_el_verificador_detecta_un_texto_con_poco_contraste():
    css = CSS.read_text(encoding='utf-8')
    malo = re.sub(r'(--tenue\s*:\s*)#[0-9a-fA-F]{6}', r'\1#5a6480', css)
    fallos = verificar(leer_paleta(malo))
    assert any('--tenue' in f and '4.5' in f for f in fallos), fallos


def test_el_verificador_detecta_una_marca_de_grafico_por_debajo_de_3_a_1():
    css = CSS.read_text(encoding='utf-8')
    malo = re.sub(r'(--serie-3\s*:\s*)#[0-9a-fA-F]{6}', r'\1#2a3350', css)
    fallos = verificar(leer_paleta(malo))
    assert any('serie 3' in f for f in fallos), fallos


def test_el_verificador_detecta_el_foco_invisible_y_series_repetidas():
    css = CSS.read_text(encoding='utf-8')
    malo = re.sub(r'(--foco\s*:\s*)#[0-9a-fA-F]{6}', r'\1#101830', css)
    malo = re.sub(r'(--serie-2\s*:\s*)#[0-9a-fA-F]{6}', r'\1' + leer_paleta(css)['serie-1'], malo)
    fallos = verificar(leer_paleta(malo))
    assert any('anillo de foco' in f for f in fallos), fallos
    assert any('series 1 y 2' in f for f in fallos), fallos


def test_el_calculo_coincide_con_valores_de_referencia_wcag():
    assert round(contraste('#000000', '#ffffff'), 2) == 21.0
    assert round(contraste('#777777', '#ffffff'), 2) == 4.48  # el clásico gris que no llega a 4,5
    assert contraste('#123456', '#123456') == 1.0


def test_un_solo_tema_y_sin_dependencias_de_fuentes():
    css = re.sub(r'/\*.*?\*/', '', CSS.read_text(encoding='utf-8'), flags=re.S)
    assert css.count(':root') == 1
    assert 'prefers-color-scheme' not in css and 'data-theme' not in css
    assert '@font-face' not in css and '@import' not in css and 'url(' not in css
    assert 'http://' not in css and 'https://' not in css


def test_los_colores_del_css_solo_se_declaran_en_la_paleta():
    """Un color literal fuera de :root escaparía del test de contraste."""
    css = re.sub(r'/\*.*?\*/', '', CSS.read_text(encoding='utf-8'), flags=re.S)
    fuera = re.sub(r':root\s*\{.*?\}', '', css, flags=re.S)
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b', fuera), 'colores literales fuera de :root'
    assert not re.search(r'\b(rgb|rgba|hsl|hsla)\(', fuera)
