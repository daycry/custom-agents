"""Proyecciones de solo lectura del panel multi-página: la cartera de iniciativas y el plan de una iniciativa.

`roadmap-dashboard` es el dueño de los datos de cartera (`scan` + `vista_json`, el contrato de `--json`) y
`progress-report.py` el de «N de M tareas»; este módulo solo los proyecta para Inicio e Iniciativas y NO
recalcula ninguna cifra que ellos ya den. Un dato ausente es `None` (JSON `null`), nunca 0.

`plan` y `tarea` proyectan el ledger de UNA iniciativa con `agent-kits/shared/ledger-view.py` (dueño único de
«qué dice el ledger»): `plan` solo trae lo del kanban (id, título, fase, estado, horas IA y nº de gaps abiertos) y
`tarea` el detalle de una tarea; el contenido de `execution-history.md` nunca se lee ni se mezcla.

El texto libre del repo (títulos, slug, literal de un estado, coste estimado, fase, criterios, verificación, gaps)
sale SIN anonimizar: lo sanea el servidor (`serve_panel._scrubbed`, lista blanca `_DISPLAY_KEYS`) o el exportador,
con el mismo saneador que el resto de APIs.
"""
import datetime
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import sys
import urllib.parse

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAX_SCAN = 128                      # carpetas de docs/roadmap que se listan
MAX_INITIATIVES = 64                # filas de la respuesta
MAX_FILE_BYTES = 256 * 1024         # tope de lectura de un ledger (local-read.py)
MAX_ARTIFACT_BYTES = 1024 * 1024    # un artefacto mayor no se abre
MAX_SCAN_BYTES = 16 * 1024 * 1024   # tope total de lo que lee el escaneo de una petición
MAX_LEDGER_BYTES = 8 * 1024 * 1024  # tope total de lectura de ledgers para N/M
MAX_RESPONSE_BYTES = 65536
ESTADOS_SPEC = ('borrador', 'aprobada', 'implementada', 'obsoleta')
CATEGORIAS = ESTADOS_SPEC + ('ilegible', 'sin_spec', 'no_reconocido')
ARTEFACTOS = ('spec.md', 'evaluation.md', 'design.md', 'improvement-plan.md', 'tasks.md')
_FECHA = re.compile(r'\d{4}-\d{2}-\d{2}', re.ASCII)   # `\d` de str casa dígitos Unicode; el validador de JS, no
_CONTROLES = re.compile('[' + chr(0) + '-' + chr(0x1f) + chr(0x7f) + '-' + chr(0x9f) + chr(0x202a) + '-' + chr(0x202e) + chr(0x2066) + '-' + chr(0x2069) + chr(0x2028) + '-' + chr(0x2029) + ']')
_EUR = re.compile(r'(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,](\d{1,2}))?\s*(?:€|EUR\b)')


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError('bundled helper unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_shared(filename):
    return _load('panel_data_' + filename.replace('-', '_').replace('.py', ''), REPO / 'agent-kits/shared' / filename)


def _load_ledger_view():
    return _load_shared('ledger-view.py')


def _load_dashboard():
    return _load('panel_data_build_dashboard', REPO / 'skills/roadmap-dashboard/scripts/build_dashboard.py')


# Topes de los textos libres, en code points: los mismos que valida el JS de las páginas (`page-cartera.js`)
# y que el servidor aplica DESPUÉS de anonimizar (`serve_panel._CAPS`); aquí solo evitan que una respuesta
# con textos enormes agote el presupuesto de 64 KiB antes de llegar al saneador.
TOPES = {'titulo': 160, 'slug': 80, 'est_texto': 120, 'literal': 48, 'fase_nombre': 160,
         'descripcion': 1500, 'criterio': 400, 'verificacion': 2000, 'ejecutada': 1000, 'salida': 1000,
         'cabecera': 160, 'gap': 400, 'correccion': 400}
MAX_TAREAS = 400                    # tarjetas de la respuesta de `plan`; el servidor recorta más si pesa > 64 KiB
MAX_CRITERIOS = 40                  # criterios y gaps de la respuesta de `tarea`; el servidor recorta más si pesa > 64 KiB
MAX_GAPS = 20
TAREA_RE = re.compile(r'T-\d{1,4}')
ID16_RE = re.compile(r'[a-f0-9]{16}')
# Vocabulario de estados del ledger (`ledger-lint.ESTADOS`, en el orden de las columnas). Solo se repite aquí para
# poder contestar «no disponible» cuando `ledger-view.py` no carga; un test lo compara con el de `ledger-view`.
ESTADOS_LEDGER = ('borrador', 'en-progreso', 'en-revision', 'completado', 'cancelado')


def _limpio(valor, tope=None):
    if valor is None:
        return None
    texto = _CONTROLES.sub('', str(valor))
    return texto[:TOPES[tope]] if tope else texto


def _eur(texto):
    """Primer importe en euros de un texto de coste del `evaluation.md` («1.300 EUR», «~605 €», «1,25 EUR»).
    Sin importe reconocible → `None`: el texto no se interpreta más allá de eso."""
    m = _EUR.search(texto or '')
    if not m:
        return None
    entero = re.sub(r'[.,]', '', m.group(1)) if re.search(r'[.,]\d{3}$', m.group(1)) else m.group(1)
    return float(entero + ('.' + m.group(2) if m.group(2) else ''))


def _suma(valores):
    presentes = [v for v in valores if v is not None]
    return round(sum(presentes), 6) if presentes else None


def _horas(progreso):
    """{real, est, humanas:{real,est}}: producción = IA + supervisión (lo que se imputa); `—` → None."""
    progreso = progreso or {}
    ia, su, hu = (progreso.get(k) or (None, None) for k in ('ia', 'supervision', 'humanas'))
    return {'real': _suma([ia[0], su[0]]), 'est': _suma([ia[1], su[1]]),
            'humanas': {'real': hu[0], 'est': hu[1]}}


def _coste(rec):
    cos = (rec.get('procedencia') or {}).get('coste') or {}
    texto = _limpio(rec.get('coste'), 'est_texto')
    return {'real_eur': _suma([v.get('eur') for v in cos.values()]),
            'real_parcial': bool((cos.get('estimado_incompleto') or {}).get('artefactos')),
            'est_eur': _eur(texto), 'est_texto': texto}


def _categoria(rec):
    if not rec.get('has_spec'):
        return 'sin_spec', None, None
    estado = rec.get('spec_estado')
    if estado is None:
        return 'ilegible', None, 'sin_estado'
    if estado in ESTADOS_SPEC:
        return estado, None, None
    return 'no_reconocido', _limpio(estado, 'literal'), None


def _fecha(carpeta, rec):
    for candidata in (rec.get('creado'), carpeta[:10]):
        if isinstance(candidata, str) and _FECHA.fullmatch(candidata.strip()):
            return candidata.strip()
    return None


def _tamano_artefactos(ruta):
    """Suma de bytes de los artefactos de una carpeta; `None` si alguno es un enlace, no es regular o pasa del tope."""
    total = 0
    for nombre in ARTEFACTOS:
        try:
            info = os.lstat(os.path.join(ruta, nombre))
        except FileNotFoundError:
            continue
        except OSError:
            return None
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARTIFACT_BYTES:
            return None
        total += info.st_size
    return total


def _id16(carpeta):
    return hashlib.sha256(carpeta.encode('utf8')).hexdigest()[:16]


def _fila_base(carpeta, rec):
    categoria, literal, motivo = _categoria(rec) if rec else ('ilegible', None, 'sin_lectura')
    fila = {'id': _id16(carpeta), 'slug': _limpio(carpeta, 'slug'), 'titulo': _limpio((rec or {}).get('titulo') or carpeta, 'titulo'),
            'fecha': _fecha(carpeta, rec or {}), 'categoria': categoria, 'tiene_plan': bool((rec or {}).get('has_plan')),
            'ledger': 'sin_ledger', 'tareas': None}
    if literal is not None:
        fila['literal'] = literal
    if motivo is not None:
        fila['motivo'] = motivo
    return fila


def _leer_ledger(fila, project, carpeta, reader, progress, lint, presupuesto):
    """Rellena `ledger`, `tareas` y las alertas que salen del ledger. `presupuesto[0]` = bytes que quedan."""
    alertas = []
    rel = f'docs/roadmap/{carpeta}/tasks.md'
    limite = min(MAX_FILE_BYTES, presupuesto[0])
    if limite <= 0:
        fila['ledger'] = 'sin_lectura'
        return alertas, 'scan_budget'
    lectura = reader.read_text(project, rel, max_bytes=limite)
    presupuesto[0] -= lectura['bytes']
    estado = lectura['status']
    if estado == 'not_found':
        return alertas, None
    if estado == 'too_large':
        if limite < MAX_FILE_BYTES:                              # falta presupuesto, no es el tope del ledger
            fila['ledger'] = 'sin_lectura'
            return alertas, 'scan_budget'
        fila['ledger'] = 'fuera_de_tope'                         # se lista aparte y no suma en N ni en M
        alertas.append({'codigo': 'fuera_de_tope', 'n': 1})
        return alertas, None
    if estado != 'ok':
        fila['ledger'] = 'ilegible' if estado in ('invalid_encoding', 'not_regular') else 'sin_lectura'
        return alertas, estado
    try:
        analizado = progress.parse_ledger(lectura['text'])      # un solo parseo: N/M, completado_sin_marcar y gaps
        if not analizado['tareas']:
            raise ValueError('sin tareas `### T-XX` reconocibles')  # el mismo rechazo que `progress.resumir`
        secciones = lint.secciones_revision(lectura['text'])
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        fila['ledger'] = 'ilegible'
        return alertas, 'malformed'
    fila['ledger'] = 'ok'
    total = len(analizado['tareas'])
    completadas = sum(1 for t in analizado['tareas'] if t['estado'] == 'completado')
    fila['tareas'] = {'total': total, 'completadas': completadas, 'pct': round(100 * completadas / total)}
    abiertos = sum(1 for s in secciones for f in s['filas'] if lint.gap_pendiente(f))
    if abiertos:
        alertas.append({'codigo': 'gaps_abiertos', 'n': abiertos})
    sucias = sum(1 for t in analizado['tareas'] if t.get('estado') == 'completado' and t.get('unchecked', 0) > 0)
    if sucias:
        alertas.append({'codigo': 'completado_sin_marcar', 'n': sucias})
    return alertas, None


def _totales(filas, issues):
    por_estado = dict.fromkeys(CATEGORIAS, 0)
    for fila in filas:
        por_estado[fila['categoria']] += 1
    con_tareas = [f['tareas'] for f in filas if f['tareas']]
    n, m = sum(t['completadas'] for t in con_tareas), sum(t['total'] for t in con_tareas)
    reales = [f['coste']['real_eur'] for f in filas if f['coste']['real_eur'] is not None]
    estimados = [f['coste']['est_eur'] for f in filas if f['coste']['est_eur'] is not None]
    return {'iniciativas': len(filas), 'por_estado': por_estado,
            'tareas': {'completadas': n, 'total': m, 'pct': round(100 * n / m) if m else 0, 'ledgers': len(con_tareas)}
            if con_tareas else None,
            'fuera_de_tope': [{'id': f['id'], 'slug': f['slug']} for f in filas if f['ledger'] == 'fuera_de_tope'],
            'coste': {'real_eur': _suma(reales), 'real_n': len(reales), 'est_eur': _suma(estimados), 'est_n': len(estimados)},
            'procedencia': {k: sum(f['procedencia'][k] for f in filas) for k in ('medidos', 'estimados', 'desconocidos')}}


def _vacia(status, issue=None):
    resultado = {'version': 1, 'source': 'roadmap_cartera',
                 'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
                 'status': status, 'complete': status == 'ok', 'issues': [], 'iniciativas': [],
                 'totales': {'iniciativas': 0, 'por_estado': dict.fromkeys(CATEGORIAS, 0), 'tareas': None,
                             'fuera_de_tope': [], 'coste': {'real_eur': None, 'real_n': 0, 'est_eur': None, 'est_n': 0},
                             'procedencia': {'medidos': 0, 'estimados': 0, 'desconocidos': 0}}}
    if issue:
        resultado['issues'].append({'status': issue})
    return resultado


FIRMA_FALLOS = {'oserror': 0}   # rastro de diagnóstico (solo un contador: ningún texto del usuario ni rutas)


class _SinFirma(OSError):
    """La lectura protegida del contenido falló o rebasó el tope: no hay firma fiable (el llamador no cachea)."""


class _LecturaFirma:
    """Lectura del contenido para las firmas: `local-read.py` (fichero regular, sin redirecciones en ningún ancestro,
    `nlink`, sin bloquear en FIFOs, `MAX_FILE_BYTES`), la MISMA protección que el cálculo normal, más un tope
    agregado de bytes hasheados por petición (`MAX_SCAN_BYTES`)."""
    def __init__(self, project, reader):
        self.project, self.reader, self.gastado = str(project), reader, 0

    def huella(self, ruta):
        relativa = os.path.relpath(str(ruta), self.project).replace(os.sep, '/')
        lectura = self.reader.read_bytes(self.project, relativa, max_bytes=MAX_FILE_BYTES, include_digest=True)
        self.gastado += lectura['bytes']
        if self.gastado > MAX_SCAN_BYTES:
            raise _SinFirma('scan_budget')
        if lectura['status'] == 'too_large':
            return 'fuera_de_tope'                      # el cálculo lo reporta como `fuera_de_tope`; basta (mtime, tamaño)
        if lectura['status'] != 'ok':
            raise _SinFirma(lectura['status'])          # not_regular, redirected_path, changed_path, unreadable...
        return lectura['sha256'][:16]


def _estado_fichero(ruta, lectura=None):
    """`(mtime, tamaño)` de un fichero, más un hash de su contenido con `lectura` (una `_LecturaFirma`): el mtime de
    FAT/exFAT/red es grueso y marcar `[ ]` -> `[x]` no cambia el tamaño. `None` si no existe; `_SinFirma` si el
    contenido no se puede leer con la protección de `local-read.py`."""
    try:
        info = os.stat(ruta)
    except OSError:
        return None
    if lectura is None:
        return (info.st_mtime_ns, info.st_size)
    return (info.st_mtime_ns, info.st_size, lectura.huella(ruta))


CON_CONTENIDO = ('tasks.md', 'retro.md')   # los dos ficheros que cambian a mano dentro de la misma ventana de mtime


def cartera_firma(project):
    """Firma barata de todo lo que lee `cartera`: `docs/roadmap` y, por iniciativa, sus artefactos, `retro.md` y
    `testing/` (nombre, mtime, tamaño; `tasks.md` y `retro.md` también con un hash de su contenido). Dos firmas
    iguales = la cartera no ha cambiado y no hay que recalcularla (ni leer ni parsear ningún ledger). Si no se puede
    leer, la firma es única cada vez: nunca sirve una copia vieja."""
    raiz = os.path.join(str(project), 'docs', 'roadmap')
    try:
        lectura = _LecturaFirma(project, _load_shared('local-read.py'))
        firma = [_estado_fichero(raiz)]
        with os.scandir(raiz) as it:
            nombres = sorted(e.name for e in it)
        for nombre in nombres[:MAX_SCAN]:
            ruta = os.path.join(raiz, nombre)
            firma.append((nombre, _estado_fichero(ruta), tuple(
                _estado_fichero(os.path.join(ruta, a), lectura if a in CON_CONTENIDO else None) for a in ARTEFACTOS + ('retro.md', 'testing'))))
        return tuple(firma)
    except Exception:  # noqa: BLE001 - OSError, `_SinFirma` o un ayudante ausente: sin firma fiable no se cachea
        return object()


def cartera(project):
    """Cartera del roadmap de `project`: una fila por iniciativa y los totales de Inicio. Solo lectura."""
    try:
        reader = _load_shared('local-read.py')
        progress = _load_shared('progress-report.py')
        lint = _load_shared('ledger-lint.py')
        dashboard = _load_dashboard()
    except Exception:  # noqa: BLE001 - un ayudante ausente o roto no revela su ruta ni su error
        return _vacia('unavailable', 'reader_unavailable')
    resultado = _vacia('ok')
    issues = resultado['issues']

    def issue(status):
        resultado['complete'] = False
        if len(issues) < 16 and {'status': status} not in issues:
            issues.append({'status': status})

    listado = reader.list_names(project, 'docs/roadmap', max_entries=MAX_SCAN)
    if listado['status'] not in ('ok', 'incomplete'):
        resultado = _vacia('not_found' if listado['status'] == 'not_found' else 'unavailable', listado['status'])
        resultado['complete'] = False
        return resultado
    if not listado['complete']:
        issue('incomplete_scan')
    raiz = os.path.join(str(project), 'docs', 'roadmap')
    registros, filas, extra = [], [], {}
    escaneado = 0
    for carpeta in listado['names']:
        directorio = reader.list_names(project, 'docs/roadmap/' + carpeta, max_entries=1)
        if directorio['status'] in ('not_found', 'not_regular'):
            continue                                            # los índices del roadmap son ficheros
        if directorio['status'] not in ('ok', 'incomplete'):
            issue(directorio['status']); continue
        ruta = os.path.join(raiz, carpeta)
        tamano = _tamano_artefactos(ruta)
        if tamano is not None and escaneado + tamano > MAX_SCAN_BYTES:
            issue('scan_budget'); tamano = None
        rec = None
        if tamano is not None:
            escaneado += tamano
            try:
                rec = dashboard._scan_una(ruta)
            except (OSError, ValueError, UnicodeError, RecursionError, KeyError, TypeError, AttributeError):
                rec = None; issue('unreadable')
            if rec is None and not any(os.path.exists(os.path.join(ruta, n)) for n in ('spec.md', 'evaluation.md', 'tasks.md')):
                continue                                        # no es una carpeta de iniciativa
        if len(filas) == MAX_INITIATIVES:
            issue('row_budget'); break
        fila = _fila_base(carpeta, rec)
        if tamano is None and rec is None:
            fila['motivo'] = 'fuera_de_tope'
        filas.append(fila); registros.append(rec)
        extra[fila['id']] = carpeta
    vistos = [r for r in registros if r is not None]
    if vistos:
        dashboard.vista_json(vistos)                            # cifras de cartera: las de `--json`, en sitio
    presupuesto = [MAX_LEDGER_BYTES]
    for fila, rec in zip(filas, registros):
        carpeta = extra[fila['id']]
        alertas, problema = _leer_ledger(fila, project, carpeta, reader, progress, lint, presupuesto)
        if problema:
            issue(problema if problema in ('malformed', 'scan_budget') else 'ledger_' + problema)
        if rec is None:
            fila['horas'] = _horas(None)
            fila['coste'] = {'real_eur': None, 'real_parcial': False, 'est_eur': None, 'est_texto': None}
            fila['procedencia'] = {'medidos': 0, 'estimados': 0, 'desconocidos': 0}
            if fila['ledger'] == 'sin_ledger' and fila.get('motivo') == 'fuera_de_tope':
                fila['ledger'] = 'fuera_de_tope'
                alertas.append({'codigo': 'fuera_de_tope', 'n': 1})
        else:
            fila['horas'] = _horas(rec.get('progreso'))
            fila['coste'] = _coste(rec)
            fila['procedencia'] = {'medidos': rec['medidos'], 'estimados': rec['estimados'],
                                   'desconocidos': rec['generacion_otros']}
        if fila['horas']['est'] is None and fila['horas']['humanas']['est'] is None and fila['coste']['est_eur'] is None:
            alertas.append({'codigo': 'sin_estimacion', 'n': 1})
        fila['alertas'] = alertas
    resultado['iniciativas'] = filas
    resultado['totales'] = _totales(filas, issues)
    while filas and len(json.dumps(resultado, ensure_ascii=False).encode('utf8')) > MAX_RESPONSE_BYTES:
        filas.pop(); issue('output_budget'); resultado['totales'] = _totales(filas, issues)
    if not resultado['complete']:
        resultado['status'] = 'partial'
    return resultado


# --- Plan de una iniciativa (T-23/T-24) -----------------------------------------------------------------------

def _carpeta(project, ident, reader):
    """Carpeta de `docs/roadmap` cuyo `sha256(carpeta)[:16]` es `ident`, o `None` (id mal formado, sin roadmap o
    carpeta que no es un directorio). Solo se resuelve el id contra los nombres que lista `local-read.py`."""
    if not isinstance(ident, str) or not ID16_RE.fullmatch(ident):
        return None
    listado = reader.list_names(project, 'docs/roadmap', max_entries=MAX_SCAN)
    if listado['status'] not in ('ok', 'incomplete'):
        return None
    for nombre in listado['names']:
        if _id16(nombre) == ident:
            directorio = reader.list_names(project, 'docs/roadmap/' + nombre, max_entries=1)
            return nombre if directorio['status'] in ('ok', 'incomplete') else None
    return None


def _ahora():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def _vista(project, ident):
    """(carpeta, proyección de `ledger-view`) de la iniciativa `ident`; `None` si el id no se resuelve; `ImportError`
    y compañía si falta un ayudante (el llamador lo traduce a «no disponible»)."""
    reader = _load_shared('local-read.py')
    carpeta = _carpeta(project, ident, reader)
    if carpeta is None:
        return None
    return carpeta, _load_ledger_view().leer(Path(str(project)) / 'docs' / 'roadmap' / carpeta)


def _con_avisos(respuesta, vista):
    """Los `avisos` de la proyección (vocabulario cerrado, p. ej. `rangos_sin_expandir`) viajan en la respuesta solo
    cuando los hay: sin ellos, «Sin revisión registrada» pasaría por un dato completo (I3-4)."""
    if vista.get('avisos'):
        respuesta['avisos'] = list(vista['avisos'])
    return respuesta


def firma_ledger(project, ident):
    """`(mtime, tamaño, hash)` del `tasks.md` de la iniciativa `ident`: cambia cuando cambia lo que `plan`/`tarea`
    proyectan (el hash cubre el mtime grueso). `None` si el id no se resuelve; `()` si no se puede leer (cuenta en
    `FIRMA_FALLOS`). Solo sirve para invalidar cachés; cualquier otra excepción sube al llamador."""
    carpeta = _carpeta(project, ident, _load_shared('local-read.py'))
    if carpeta is None:
        return None
    try:
        firma = _estado_fichero(os.path.join(str(project), 'docs', 'roadmap', carpeta, 'tasks.md'),
                                _LecturaFirma(project, _load_shared('local-read.py')))
    except _SinFirma:
        FIRMA_FALLOS['oserror'] += 1
        return None                                     # redirigido, no regular o ilegible: el cálculo normal lo reporta
    if firma is None:
        FIRMA_FALLOS['oserror'] += 1
        return ()
    return firma


def _fila_plan(t):
    return {'id': t['id'], 'titulo': _limpio(t['titulo'], 'titulo'), 'fase_nombre': _limpio(t['fase'], 'fase_nombre'),
            'estado_tarea': t['estado'], 'literal': _limpio(t['literal'], 'literal'),
            'horas': {'real': t['horas']['ia']['real'], 'est': t['horas']['ia']['est'],
                      'fuente': t['horas']['ia']['fuente']},
            'gaps': len(t['gaps']), 'cerrada': t['cerrada']}


def plan(project, ident):
    """Kanban de la iniciativa `ident` (id16): solo lo que pinta una tarjeta. `None` si el id no se resuelve.

    Un ledger que no se puede mostrar (`fuera_de_tope`, `ilegible`, `sin_ledger`, `sin_tareas`, `sin_lectura`) lleva
    su estado y NINGUNA cifra (`tareas: null`, nunca una lista vacía que parezca «sin tareas»). Las tareas con un
    estado fuera del vocabulario llevan `estado_tarea: null` y el literal; la página las pone en su franja."""
    try:
        resuelto = _vista(project, ident)
    except Exception:  # noqa: BLE001 - un ayudante ausente o roto no revela su ruta ni su error
        return _plan_vacio(ident, None, 'unavailable', 'reader_unavailable')
    if resuelto is None:
        return None
    return _plan_de(ident, *resuelto)


def _plan_de(ident, carpeta, vista):
    estado = vista['status']
    respuesta = _plan_vacio(ident, carpeta, 'ok' if estado == 'ok' else estado, None if estado == 'ok' else estado)
    if estado != 'ok':
        return respuesta
    _con_avisos(respuesta, vista)
    filas = [_fila_plan(t) for t in vista['tareas']]
    if len(filas) > MAX_TAREAS:
        respuesta['omitidas'] = len(filas) - MAX_TAREAS
        respuesta['complete'] = False
        respuesta['status'] = 'partial'
        respuesta['issues'].append({'status': 'task_budget'})
        filas = filas[:MAX_TAREAS]
    respuesta['tareas'] = filas
    return respuesta


def _env_tarea(ident, tarea_id, status, issue=None):
    return {'version': 1, 'source': 'ledger_tarea', 'status': status, 'complete': status == 'ok',
            'observed_at': _ahora(), 'id': ident, 'tarea_id': tarea_id,
            'issues': [{'status': issue}] if issue else [], 'omitidos': {'criterios': 0, 'gaps': 0}, 'tarea': None}


def tarea(project, ident, tarea_id):
    """Detalle de la tarea `tarea_id` de la iniciativa `ident` (id16). `None` si el id o la tarea no se resuelven.

    Trae descripción, criterios con su casilla, `Verificación` (≤ 2.000 caracteres) y su salida, dependencias, la
    última revisión con sus gaps abiertos y la marca `archivado` (solo el enlace: `execution-history.md` no se lee).
    Criterios y gaps se topan (`MAX_CRITERIOS`, `MAX_GAPS`) y lo omitido se cuenta en `omitidos`: nunca se inventa."""
    if not isinstance(tarea_id, str) or not TAREA_RE.fullmatch(tarea_id):
        return None
    try:
        resuelto = _vista(project, ident)
    except Exception:  # noqa: BLE001 - un ayudante ausente o roto no revela su ruta ni su error
        return _env_tarea(ident, tarea_id, 'unavailable', 'reader_unavailable')
    if resuelto is None:
        return None
    _, vista = resuelto
    if vista['status'] != 'ok':
        return _env_tarea(ident, tarea_id, vista['status'], vista['status'])
    t = next((x for x in vista['tareas'] if x['id'] == tarea_id), None)
    return None if t is None else _con_avisos(_detalle(ident, tarea_id, t), vista)


def plan_y_detalles(project, ident):
    """`(plan, {T-XX: detalle})` de la iniciativa `ident` con UNA lectura y UNA proyección del ledger (el exportado
    pedía `tarea()` por tarea y reproyectaba el ledger entero cada vez). Cada valor es lo que devuelven `plan()` y
    `tarea()`. `None` si el id no se resuelve; con un ledger no mostrable, sin detalles."""
    try:
        resuelto = _vista(project, ident)
    except Exception:  # noqa: BLE001 - un ayudante ausente o roto no revela su ruta ni su error
        return _plan_vacio(ident, None, 'unavailable', 'reader_unavailable'), {}
    if resuelto is None:
        return None
    respuesta = _plan_de(ident, *resuelto)
    if resuelto[1]['status'] != 'ok':
        return respuesta, {}
    return respuesta, {t['id']: _con_avisos(_detalle(ident, t['id'], t), resuelto[1]) for t in resuelto[1]['tareas']}


def _detalle(ident, tarea_id, t):
    """Respuesta `api/plan-<id16>-<T-XX>` de la tarea `t` de una proyección ya leída."""
    v, r = t['verificacion'], t['revision']
    respuesta = _env_tarea(ident, tarea_id, 'ok')
    respuesta['omitidos'] = {'criterios': max(0, len(t['criterios']) - MAX_CRITERIOS),
                             'gaps': max(0, len(t['gaps']) - MAX_GAPS)}
    if any(respuesta['omitidos'].values()):
        respuesta['status'], respuesta['complete'] = 'partial', False
        respuesta['issues'].append({'status': 'task_budget'})
    respuesta['tarea'] = {
        'id': t['id'], 'titulo': _limpio(t['titulo'], 'titulo'), 'fase_nombre': _limpio(t['fase'], 'fase_nombre'),
        'estado_tarea': t['estado'], 'literal': _limpio(t['literal'], 'literal'),
        'descripcion': _limpio(t['descripcion'], 'descripcion'),
        'criterios': [{'criterio': _limpio(c['texto'], 'criterio'), 'marcado': c['marcado']}
                      for c in t['criterios'][:MAX_CRITERIOS]],
        'verificacion': _limpio(v['texto'], 'verificacion') if v else None,
        'verificacion_recortada': bool(v and v['recortada']),
        'ejecutada': _limpio(v['ejecutada'], 'ejecutada') if v else None,
        'salida': _limpio(v['salida'], 'salida') if v else None,
        'dependencias': t['dependencias'][:40], 'archivado': t['archivado'], 'cerrada': t['cerrada'],
        'horas': t['horas'],
        'revision': {'intento': r['intento'], 'cabecera': _limpio(r['cabecera'], 'cabecera'),
                     'abiertos': r['abiertos']} if r else None,
        'gaps': [{'intento': g['intento'], 'num': g['num'], 'grado': g['grado'], 'gap': _limpio(g['gap'], 'gap'),
                  'correccion': _limpio(g['correccion'], 'correccion')} for g in t['gaps'][:MAX_GAPS]]}
    return respuesta


def _plan_vacio(ident, carpeta, status, issue):
    return {'version': 1, 'source': 'ledger_plan', 'status': status, 'complete': status == 'ok',
            'observed_at': _ahora(), 'id': ident, 'slug': _limpio(carpeta, 'slug'),
            'issues': [{'status': issue}] if issue else [], 'vocabulario': list(ESTADOS_LEDGER),
            'omitidas': 0, 'tareas': None}


# --- Memoria (T-30..T-35) -------------------------------------------------------------------------------------------

MEM_MAX_ITEMS = 20                  # candidatos y entradas aprobadas que lista la bandeja por estado
MEM_MAX_RELACIONES = 20             # igual que `knowledge-view.MAX_RESULTS`: un salto, nunca el grafo entero
MEM_MAX_SESIONES = 2                # lo que devuelve `journal.select_entries` (su contrato; no se amplía)
MEM_MAX_BACKENDS = 8
MEM_OUTBOX_LEIDOS = 64              # manifiestos de `done/` que se leen para la última publicación
KS = '.claude/knowledge-services'
CANDIDATOS = ('pending', 'needs_changes', 'rejected')
_BACKEND_RE = re.compile(r'[a-z][a-z0-9_-]{0,31}', re.ASCII)
_ISO_Z = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', re.ASCII)
_URL_UI = re.compile(r'https?://[^\s?#@\\\x00-\x1f]{1,190}')
_MARCA_REDACTOR = '[secreto redactado]'
# Redes que el guardrail de nemesis (`lib-guardrail.sh`) admite como locales/privadas. Aqui se comparan como REDES y no
# por prefijo de texto: `127.0.0.1.example.com` no es loopback.
_REDES_LOCALES = tuple(ipaddress.ip_network(n) for n in (
    '127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '169.254.0.0/16', '::1/128', 'fc00::/7', 'fe80::/10'))
_SUFIJOS_LOCALES = ('.test', '.local', '.localhost', '.internal')


def _host_local(url):
    """`True` si el host de `url` es loopback o privado (mismo criterio que `lib-guardrail.sh`); nunca resuelve nombres."""
    try:
        host = urllib.parse.urlsplit(url).hostname
    except ValueError:
        return False
    if not host:
        return False
    host = host.lower().rstrip('.')
    if host in ('localhost', 'host.docker.internal') or host.endswith(_SUFIJOS_LOCALES):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip.version == red.version and ip in red for red in _REDES_LOCALES)


def _fecha_ok(valor):
    """`AAAA-MM-DD` real (ASCII y existente en el calendario); si no, `None`."""
    if not isinstance(valor, str) or not _FECHA.fullmatch(valor):
        return None
    try:
        datetime.date.fromisoformat(valor)
    except ValueError:
        return None
    return valor


def _iso_z_ok(valor):
    """Instante `AAAA-MM-DDTHH:MM:SSZ` real: el validador de la pagina (`Date.parse`) rechaza uno imposible."""
    if not isinstance(valor, str) or not _ISO_Z.fullmatch(valor):
        return False
    try:
        datetime.datetime.fromisoformat(valor[:-1])
    except ValueError:
        return False
    return True


def _corta(texto, tope):
    """Corta a `tope` code points sin partir la marca del redactor."""
    if len(texto) <= tope:
        return texto
    inicio = texto.find(_MARCA_REDACTOR)
    while inicio != -1:
        if inicio < tope < inicio + len(_MARCA_REDACTOR):
            return texto[:inicio]
        inicio = texto.find(_MARCA_REDACTOR, inicio + 1)
    return texto[:tope]


def _redactado(redact, valor, tope):
    """redactar -> quitar controles -> recortar (el orden de `redact.py`: el secreto se reconoce entero antes de cortar)."""
    if valor is None:
        return None
    return _corta(_CONTROLES.sub(' ', redact.redactar(str(valor))), tope)


def _lista_redactada(redact, valores, tope, maximo=3):
    return [_redactado(redact, v, tope) for v in (valores if isinstance(valores, list) else [])[:maximo] if isinstance(v, str)]


def _issue_memoria(datos):
    def issue(codigo):
        datos['complete'] = False
        if len(datos['issues']) < 16 and {'status': codigo} not in datos['issues']:
            datos['issues'].append({'status': codigo})
        if datos['status'] in ('ok', 'not_found'):
            datos['status'] = 'partial'
    return issue


def _memoria_vacia(status, issue=None):
    estados = {e: {'situacion': 'no_disponible', 'n': None, 'items': []} for e in CANDIDATOS}
    datos = {'version': 1, 'source': 'memoria_panel', 'observed_at': _ahora(), 'status': status,
             'complete': status == 'ok', 'issues': [], 'total': 0, 'recortado': 0, 'conteos': {}, 'entradas': [],
             'bandeja': {'estados': estados, 'aprobadas': {'n': None, 'items': []}}, 'backends': [],
             'journal': {'status': 'unavailable', 'sesiones': []}}
    if issue:
        datos['issues'].append({'status': issue})
    return datos


def _recortar_bandeja(datos, limite, tope=None):
    """Quita elementos del FINAL de la lista mas larga de la bandeja hasta que ocupe `limite` bytes (o, con `tope`, hasta
    que la respuesta entera quepa). Los conteos `n` no cambian: son los de la carpeta, no los listados."""
    bandeja = datos.get('bandeja')
    if not isinstance(bandeja, dict):
        return

    def listas():
        yield from (e['items'] for e in bandeja['estados'].values() if e.get('items'))
        if bandeja['aprobadas'].get('items'):
            yield bandeja['aprobadas']['items']

    def pesa(valor):
        return len(json.dumps(valor, ensure_ascii=False).encode('utf8'))
    while (pesa(datos) > tope) if tope is not None else (pesa(bandeja) > limite):
        mayor = max(listas(), key=len, default=None)
        if not mayor:
            break
        mayor.pop()


def ajustar_memoria(datos, tope=MAX_RESPONSE_BYTES):
    """Recorta `entradas` por el final hasta que la respuesta quepa en `tope` bytes (los conteos siguen siendo los del
    corpus entero) y lo declara (`recortado`, `status: partial`). Lo usan `memoria` y el servidor, que vuelve a medir
    DESPUÉS de anonimizar (anonimizar alarga el texto)."""
    def tamano():
        return len(json.dumps(datos, ensure_ascii=False).encode('utf8'))
    exceso = tamano() - tope
    if exceso <= 0:
        return datos
    # La bandeja nunca agota el presupuesto entera: se recorta primero a la mitad (sus `n` siguen siendo los reales y la
    # pagina dice «se listan X de n»); despues las entradas por el final; y solo si aun asi no cabe, mas bandeja.
    _recortar_bandeja(datos, tope // 2)
    exceso = tamano() - tope
    filas = datos['entradas']
    while filas and exceso > 0:
        exceso -= len(json.dumps(filas.pop(), ensure_ascii=False).encode('utf8')) + 1
        datos['recortado'] += 1
    while filas and tamano() > tope:
        filas.pop()
        datos['recortado'] += 1
    if tamano() > tope:
        _recortar_bandeja(datos, 0, tope=tope)
    datos['complete'], datos['status'] = False, 'partial'
    if {'status': 'output_budget'} not in datos['issues'] and len(datos['issues']) < 16:
        datos['issues'].append({'status': 'output_budget'})
    return datos


def _fila_entrada(e, redact, sucesion):
    sustituida = [i for r, _x, i in sucesion if r == 'sustituida por']
    fecha = _fecha_ok((e.get('fecha') or '').strip())
    return {'id': e['id'], 'tipo': _redactado(redact, e['tipo'], 160) or '', 'estado': _redactado(redact, e['estado'], 160) or '',
            'area': _redactado(redact, e['area'], 160) or '', 'titular': _redactado(redact, e['titular'], 160) or '',
            'fecha': fecha,
            'iniciativa': _redactado(redact, e.get('iniciativa') or '', 80),
            'origen': 'approved' if str(e['ruta']).startswith('docs/knowledge/approved/') else 'proyecto',
            'vigente': e['estado'] != 'obsoleta' and not sustituida,
            'sustituida_por': _etiquetas(redact, sustituida),
            'sustituye_a': _etiquetas(redact, [i for r, _x, i in sucesion if r == 'sustituye a'])}


def _etiqueta(redact, valor):
    """Id de un sucesor (que puede NO estar en el corpus): redactado, sin controles y de <= 256 puntos de codigo, como
    pide la pagina; nunca vacio."""
    return _redactado(redact, valor, 256).strip() or '(sin id)'


def _etiquetas(redact, valores, maximo=16):
    """Hasta `maximo` etiquetas distintas (la pagina rechaza mas de 16)."""
    salida = []
    for valor in valores:
        etiqueta = _etiqueta(redact, valor)
        if etiqueta not in salida and len(salida) < maximo:
            salida.append(etiqueta)
    return salida


def _relaciones_de(find, unicos, e, redact):
    rel = find.relaciones(unicos, e)
    # Claves propias (`por_iniciativa`, `por_area`): `area` es una clave de texto mostrado del saneador y no puede contener ids.
    salida = {'sucesion': [], 'por_iniciativa': [], 'por_area': [], 'enlaces': []}
    origen = {'sucesion': 'sucesion', 'por_iniciativa': 'iniciativa', 'por_area': 'area', 'enlaces': 'enlaces'}
    filas = {grupo: rel.get(origen[grupo], []) for grupo in salida}
    total = sum(len(f) for f in filas.values())
    # Reparto por turnos: el cupo de 20 se comparte y ningun grupo con relaciones se queda sin ninguna en silencio.
    cupo = dict.fromkeys(salida, 0)
    quedan = MEM_MAX_RELACIONES
    while quedan and any(cupo[g] < len(filas[g]) for g in salida):
        for grupo in salida:
            if quedan and cupo[grupo] < len(filas[grupo]):
                cupo[grupo] += 1
                quedan -= 1
    for grupo in salida:
        for fila in filas[grupo][:cupo[grupo]]:
            if grupo == 'sucesion':
                relacion, destino, ident = fila
                salida[grupo].append({'relacion': relacion, 'id': _etiqueta(redact, ident), 'ausente': destino is None})
            else:
                salida[grupo].append(fila['id'])
    salida['recortado'] = total > MEM_MAX_RELACIONES
    salida['total'] = total
    return salida


def _entradas_memoria(project, datos, redact, relaciones):
    """Proyecta el corpus de `knowledge-view.snapshot` + `knowledge-find.parsear_corpus`: la misma lectura acotada que
    `api/memory`; aquí solo se resumen metadatos (el cuerpo de una entrada no viaja)."""
    issue = _issue_memoria(datos)
    view, find = _load_shared('knowledge-view.py'), _load_shared('knowledge-find.py')
    snap = view.snapshot(project)
    for codigo in snap['corpus_read']['issues']:
        issue(codigo)
    try:
        corpus = find.parsear_corpus(snap['files'])
    except Exception:  # noqa: BLE001 - un corpus que no parsea se dice, sin su causa
        issue('corpus_ilegible')
        corpus = []
    validas = []
    for e in corpus:
        ident = e.get('id')
        if (not isinstance(ident, str) or not 0 < len(ident) <= 256 or redact.redactar(ident) != ident
                or _CONTROLES.search(ident)):
            issue('identidad_invalida')
            continue
        validas.append(e)
    cuentas = {}
    for e in validas:
        cuentas[e['id'].casefold()] = cuentas.get(e['id'].casefold(), 0) + 1
    if any(n > 1 for n in cuentas.values()):
        issue('identidad_duplicada')
    unicos = [e for e in validas if cuentas[e['id'].casefold()] == 1]
    sucesion = getattr(find, '_relaciones_sucesion', None)
    filas, conteos, rel, vistos = [], {}, {}, set()
    for e in sorted(validas, key=find.clave_orden):
        if e['id'] in vistos:      # el mismo id dos veces: una sola fila (la pagina rechaza ids repetidos); el aviso ya esta dado
            continue
        vistos.add(e['id'])
        unico = cuentas[e['id'].casefold()] == 1
        suc = (sucesion(unicos, e) if sucesion else find.relaciones(unicos, e)['sucesion']) if unico else []
        fila = _fila_entrada(e, redact, suc)
        filas.append(fila)
        conteos.setdefault(fila['tipo'], {}).setdefault(fila['estado'], 0)
        conteos[fila['tipo']][fila['estado']] += 1
        if relaciones and unico:
            rel[e['id']] = _relaciones_de(find, unicos, e, redact)
    datos['entradas'], datos['conteos'], datos['total'] = filas, conteos, len(filas)
    if relaciones:
        datos['relaciones'] = rel
    if not filas and datos['complete']:
        datos['status'] = 'not_found'
    return filas


def _titular_candidato(texto):
    for linea in texto.splitlines():
        if linea.startswith('# '):
            return linea[2:].strip()
    return ''


def _bandeja(project, reader, find, redact, aprobadas):
    """Candidatos del curador por estado (carpetas de `docs/knowledge/candidates/`) y lo aprobado. Solo lectura: el panel
    no ofrece ninguna decisión; es de `knowledge-curator` (ADR-018)."""
    estados = {}
    for estado in CANDIDATOS:
        ruta = 'docs/knowledge/candidates/' + estado
        listado = reader.list_names(project, ruta, max_entries=128)
        if listado['status'] == 'not_found':
            estados[estado] = {'situacion': 'ausente', 'n': 0, 'items': []}
            continue
        if listado['status'] not in ('ok', 'incomplete'):
            estados[estado] = {'situacion': 'no_disponible', 'n': None, 'items': []}
            continue
        nombres = [n for n in listado['names'] if n.lower().endswith('.md') and n.lower() != 'readme.md']
        items = []
        for nombre in nombres[:MEM_MAX_ITEMS]:
            lectura = reader.read_text(project, ruta + '/' + nombre, max_bytes=16 * 1024)
            fm, cuerpo = find.frontmatter(lectura['text']) if lectura['status'] == 'ok' else ({}, '')
            items.append({'candidato': _redactado(redact, nombre, 160),
                          'titular': _redactado(redact, _titular_candidato(cuerpo) or None, 160),
                          'category': _redactado(redact, fm.get('category') or None, 40)})
        estados[estado] = {'situacion': 'ok' if listado['complete'] else 'incompleto', 'n': len(nombres), 'items': items}
    lista = [{'id': f['id'], 'titular': f['titular'], 'area': f['area']} for f in aprobadas]
    return {'estados': estados, 'aprobadas': {'n': len(lista), 'items': lista[:MEM_MAX_ITEMS]}}


def _json_acotado(reader, project, ruta, tope=256 * 1024):
    lectura = reader.read_text(project, ruta, max_bytes=tope)
    if lectura['status'] != 'ok':
        return None
    try:
        return json.loads(lectura['text'])
    except (ValueError, RecursionError):
        return None


def _existe(reader, project, ruta):
    return reader.read_bytes(project, ruta, max_bytes=1)['status'] in ('ok', 'too_large')


def _ruta_del_proyecto(project, valor):
    """Ruta relativa y segura dentro del proyecto (acepta una absoluta que caiga dentro); si no, `None`."""
    if not isinstance(valor, str) or not valor or '\x00' in valor:
        return None
    try:
        if os.path.isabs(valor):
            valor = Path(valor).resolve().relative_to(Path(str(project)).resolve()).as_posix()
        partes = valor.replace('\\', '/').split('/')
    except (OSError, ValueError):
        return None
    if any(p in ('', '.', '..') or ':' in p for p in partes):
        return None
    return '/'.join(partes)


def _ultima_publicacion(reader, project, backend):
    """`(fecha, parcial)`: el `completado_en` MAS RECIENTE de `done/*.manifest.json` de la outbox del backend (la fecha
    real de materializacion que escribe `outbox.completar`; nunca el `mtime`) y si el listado o la lectura se quedaron cortos."""
    ruta = f'{KS}/_sync-outbox/{backend}/done'
    listado = reader.list_names(project, ruta, max_entries=256)
    if listado['status'] not in ('ok', 'incomplete'):
        return None, False
    todos = sorted((n for n in listado['names'] if n.endswith('.manifest.json')), reverse=True)
    mejor = None
    for nombre in todos[:MEM_OUTBOX_LEIDOS]:
        dato = _json_acotado(reader, project, ruta + '/' + nombre, 16 * 1024)
        fecha = dato.get('completado_en') if isinstance(dato, dict) else None
        if _iso_z_ok(fecha) and (mejor is None or fecha > mejor):
            mejor = fecha
    # `list_names` devuelve un prefijo del directorio si hay mas de 256 ficheros, y solo se leen `MEM_OUTBOX_LEIDOS`:
    # en ambos casos puede haber una publicacion mas reciente que no se vio («al menos»).
    return mejor, (not listado['complete']) or len(todos) > MEM_OUTBOX_LEIDOS


def _fila_backend(project, reader, ident, cfg):
    tipo = cfg.get('type') if isinstance(cfg.get('type'), str) else ''
    conf = cfg.get('config') if isinstance(cfg.get('config'), dict) else {}
    fila = {'backend': ident, 'tipo': tipo[:40], 'situacion': 'deshabilitado' if cfg.get('enabled') is False else 'configurado',
            'entradas': None, 'ultima': None, 'ultima_parcial': False, 'interrumpida': False, 'ui_url': None,
            'ui_url_no_local': False}
    if tipo == 'markdown-export':
        carpeta = _ruta_del_proyecto(project, conf.get('export_dir') or KS + '/kwipu-export')
        if carpeta:
            manifiesto = _json_acotado(reader, project, carpeta + '/manifest.json')
            if isinstance(manifiesto, dict) and isinstance(manifiesto.get('entries'), dict):
                fila['entradas'] = len(manifiesto['entries'])
            fila['interrumpida'] = _existe(reader, project, carpeta + '/manifest.pending.json')
    elif tipo == 'graphiti':
        manifiesto = _json_acotado(reader, project, KS + '/graphiti-manifest.json')
        if isinstance(manifiesto, dict) and isinstance(manifiesto.get('entradas'), dict):
            fila['entradas'] = len(manifiesto['entradas'])
        fila['interrumpida'] = _existe(reader, project, KS + '/graphiti-manifest.pending.json')
    fila['ultima'], fila['ultima_parcial'] = _ultima_publicacion(reader, project, ident)
    url = conf.get('ui_url')
    if isinstance(url, str) and _URL_UI.fullmatch(url):
        # Un repo clonado no puede apuntar el enlace «abrir» a un host externo: solo loopback/privado (guardrail de nemesis).
        if _host_local(url):
            fila['ui_url'] = url
        else:
            fila['ui_url_no_local'] = True
    return fila


def _backends(project, reader, issue):
    """Qué se publicó en cada backend de `taxonomy.json`, leyendo SOLO ficheros locales: ninguna conexión, ninguna
    llamada a `health`, ninguna fecha de `mtime`. Lo que la fuente no trae es `None` («sin datos» en la página)."""
    configurados = {}
    leida = reader.read_text(project, KS + '/taxonomy.json', max_bytes=64 * 1024)
    if leida['status'] == 'ok':
        try:
            declarados = json.loads(leida['text']).get('backends')
            configurados = declarados if isinstance(declarados, dict) else {}
        except (ValueError, AttributeError, RecursionError):
            issue('taxonomia_invalida')
    elif leida['status'] != 'not_found':
        issue('taxonomia_' + leida['status'])
    filas = [_fila_backend(project, reader, ident, cfg) for ident, cfg in list(configurados.items())[:MEM_MAX_BACKENDS]
             if isinstance(ident, str) and _BACKEND_RE.fullmatch(ident) and isinstance(cfg, dict)]
    for ident, tipo in (('kwipu', 'markdown-export'), ('graphiti', 'graphiti')):
        if not any(f['backend'] == ident for f in filas):
            filas.append({'backend': ident, 'tipo': tipo, 'situacion': 'no_configurado', 'entradas': None, 'ultima': None,
                          'ultima_parcial': False, 'interrumpida': False, 'ui_url': None, 'ui_url_no_local': False})
    orden = {'kwipu': 0, 'graphiti': 1}
    return sorted(filas, key=lambda f: (orden.get(f['backend'], 2), f['backend']))


def _journal(project, redact):
    """Sesiones recientes del journal con su continuidad, por la selección pública y acotada de `journal.py`
    (`select_entries`: ya redacta y recorta). Son CITAS del historial, no instrucciones."""
    try:
        resultado = _load_shared('journal.py').select_entries(str(project))
    except Exception:  # noqa: BLE001 - sin el lector, «no disponible», sin su causa
        return {'status': 'unavailable', 'sesiones': []}
    estado = resultado.get('status') if isinstance(resultado, dict) else None
    if estado not in ('ok', 'empty', 'not_found', 'incomplete'):
        return {'status': 'unavailable', 'sesiones': []}
    sesiones = []
    # Con una lectura incompleta (frontmatter roto, mas de 128 ficheros) `journal.py` no promueve nada a `entries`, pero
    # ofrece las `candidates` legibles: se muestran, con la lista marcada como incompleta (no acredita ausencia ni «las ultimas»).
    lista = resultado.get('candidates') if estado == 'incomplete' else resultado.get('entries')
    for e in (lista or [])[:MEM_MAX_SESIONES]:
        if not isinstance(e, dict):
            continue
        c = e.get('continuidad') if isinstance(e.get('continuidad'), dict) else {}
        sesiones.append({'fecha': _fecha_ok(str(e.get('fecha') or '')),
                         'iniciativa': _redactado(redact, e.get('iniciativa') or '', 80),
                         'resumen': _redactado(redact, e.get('resumen') or '', 240),
                         'objetivo': _redactado(redact, c.get('objetivo'), 240),
                         'punto_actual': _redactado(redact, c.get('punto_actual'), 240),
                         'siguientes_pasos': _lista_redactada(redact, c.get('siguientes_pasos'), 240),
                         'bloqueos': _lista_redactada(redact, c.get('bloqueos'), 240),
                         'descartados': _lista_redactada(redact, c.get('descartados'), 240),
                         'decisiones': _lista_redactada(redact, e.get('decisiones'), 240),
                         'pendientes': _lista_redactada(redact, e.get('pendientes'), 240)})
    return {'status': estado, 'sesiones': sesiones}


def memoria(project, relaciones=False):
    """Proyección de Memoria para `api/memoria` y la copia exportada: entradas por tipo y estado con su sucesión y su
    «vigente», bandeja del curador, backends y journal. Solo lectura y sin red. `relaciones=True` (copia exportada, que
    no puede preguntar a `api/memory`) añade las de cada entrada: ids de un salto, como `knowledge-find --related`.
    Un dato que una fuente no trae es `None`; nunca se inventa ni se pinta como 0."""
    try:
        redact = _load_shared('redact.py')
        reader = _load_shared('local-read.py')
        find = _load_shared('knowledge-find.py')
    except Exception:  # noqa: BLE001 - un ayudante ausente o roto no revela su ruta ni su error
        return _memoria_vacia('unavailable', 'reader_unavailable')
    datos = _memoria_vacia('ok')
    datos['bandeja'] = None
    datos['journal'] = {'status': 'unavailable', 'sesiones': []}
    try:
        filas = _entradas_memoria(project, datos, redact, relaciones)
        datos['bandeja'] = _bandeja(project, reader, find, redact, [f for f in filas if f['origen'] == 'approved'])
        datos['backends'] = _backends(project, reader, _issue_memoria(datos))
        datos['journal'] = _journal(project, redact)
    except Exception:  # noqa: BLE001 - una lectura que falla no deja la página a medias: vacía y dicho
        return _memoria_vacia('unavailable', 'read_failed')
    return datos if relaciones else ajustar_memoria(datos)
