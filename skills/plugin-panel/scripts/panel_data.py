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
import json
import os
from pathlib import Path
import re
import stat
import sys

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
_FECHA = re.compile(r'\d{4}-\d{2}-\d{2}')
_CONTROLES = re.compile('[' + chr(0) + '-' + chr(0x1f) + chr(0x7f) + '-' + chr(0x9f) + chr(0x202a) + '-' + chr(0x202e) + chr(0x2066) + '-' + chr(0x2069) + ']')
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


def _estado_fichero(ruta, contenido=False):
    """`(mtime, tamaño)` de un fichero, más un hash de su contenido con `contenido` (acotado a `MAX_FILE_BYTES`): el
    mtime de FAT/exFAT/red es grueso y marcar `[ ]` -> `[x]` no cambia el tamaño. `None` si no se puede leer."""
    try:
        info = os.stat(ruta)
    except OSError:
        return None
    if not contenido:
        return (info.st_mtime_ns, info.st_size)
    try:
        with open(ruta, 'rb') as fichero:
            huella = hashlib.sha256(fichero.read(MAX_FILE_BYTES + 1)).hexdigest()[:16]
    except OSError:
        huella = None
    return (info.st_mtime_ns, info.st_size, huella)


CON_CONTENIDO = ('tasks.md', 'retro.md')   # los dos ficheros que cambian a mano dentro de la misma ventana de mtime


def cartera_firma(project):
    """Firma barata de todo lo que lee `cartera`: `docs/roadmap` y, por iniciativa, sus artefactos, `retro.md` y
    `testing/` (nombre, mtime, tamaño; `tasks.md` y `retro.md` también con un hash de su contenido). Dos firmas
    iguales = la cartera no ha cambiado y no hay que recalcularla (ni leer ni parsear ningún ledger). Si no se puede
    leer, la firma es única cada vez: nunca sirve una copia vieja."""
    raiz = os.path.join(str(project), 'docs', 'roadmap')
    try:
        firma = [_estado_fichero(raiz)]
        with os.scandir(raiz) as it:
            nombres = sorted(e.name for e in it)
        for nombre in nombres[:MAX_SCAN]:
            ruta = os.path.join(raiz, nombre)
            firma.append((nombre, _estado_fichero(ruta), tuple(
                _estado_fichero(os.path.join(ruta, a), a in CON_CONTENIDO) for a in ARTEFACTOS + ('retro.md', 'testing'))))
        return tuple(firma)
    except OSError:
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


def firma_ledger(project, ident):
    """`(mtime, tamaño, hash)` del `tasks.md` de la iniciativa `ident`: cambia cuando cambia lo que `plan`/`tarea`
    proyectan (el hash cubre el mtime grueso). `None` si el id no se resuelve; `()` si no se puede leer (cuenta en
    `FIRMA_FALLOS`). Solo sirve para invalidar cachés; cualquier otra excepción sube al llamador."""
    carpeta = _carpeta(project, ident, _load_shared('local-read.py'))
    if carpeta is None:
        return None
    firma = _estado_fichero(os.path.join(str(project), 'docs', 'roadmap', carpeta, 'tasks.md'), True)
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
    return None if t is None else _detalle(ident, tarea_id, t)


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
    return respuesta, {t['id']: _detalle(ident, t['id'], t) for t in resuelto[1]['tareas']}


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
