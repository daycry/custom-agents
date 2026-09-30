#!/usr/bin/env python3
"""Alta del proyecto en `<stack>/kwipu/config/projects.yaml` (setup-statusline-polish T-12, C-07).

Diseno aprobado: `docs/roadmap/2026-09-29-setup-statusline-polish/design.md`, opcion O1.

SOLO AÑADE: al final del fichero, un bloque delimitado por marcas del plugin. Nunca reescribe un
byte que ya existia y el fichero conserva su identidad (inodo, permisos, enlaces). Sin `--apply`
solo es la VISTA PREVIA (estado, bloque, `sha256`). Con `--apply --esperado <sha256>` escribe.

  kwipu-project-add.py --stack <stack> [--root R] [--backend kwipu] [--nombre N] [--json]
  kwipu-project-add.py --stack <stack> [...] --apply --esperado <sha256>

Codigos de salida: 0 vista previa / añadido / ya presente (no-op) · 1 no escribio, revirtio o el
fichero cambio durante la escritura (copia, hash distinto, identidad cambiada, verificacion
posterior; `bloque_presente` dice el estado REAL) · 2 uso (argumentos, `--apply` sin `--esperado`,
nombre o `root` invalidos, taxonomia sin backend `markdown-export`, destino que no es el del stack)
· 3 forma NO reconocida (no escribe, imprime el bloque para pegarlo a mano) · 4 conflicto de
nombre o de `root` (no escribe, pide otro nombre).

Solo stdlib. No ejecuta nada del stack: los comandos de `build_view` y de reinicio solo se
IMPRIMEN (PAT-001: el plugin no ejecuta el stack).
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import stat
import sys
import unicodedata

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))
BACKENDS_DIR = os.path.normpath(os.path.join(HERE, "..", "backends"))

# #2 (fix1): la clave del proyecto se emite sin comillas, asi que tiene que ser TEXTO para YAML
# 1.1: empieza por letra (`2024`, `0x1f`, `0b101` serian numeros) y no es una palabra reservada.
NOMBRE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
NOMBRE_MAX = 64
YAML_RESERVADAS = frozenset(("y", "n", "yes", "no", "on", "off", "true", "false", "null", "~"))
MARCA_ABRE = "# >>> custom-agents:"
MARCA_CIERRA = "# <<< custom-agents:"
_REPARSE = 0x400                      # FILE_ATTRIBUTE_REPARSE_POINT (Windows)
_O_BINARY = getattr(os, "O_BINARY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)   # #10: la escritura no sigue enlaces (no existe en Windows)
_os_write = os.write                  # indireccion: los tests inyectan escrituras rotas

E_OK, E_IO, E_USO, E_FORMA, E_CONFLICTO = 0, 1, 2, 3, 4


class FormaNoReconocida(Exception):
    """El fichero existe pero cae fuera de la gramatica minima que el script sabe ampliar."""


class Uso(Exception):
    """Argumentos, configuracion o destino invalidos (exit 2)."""


# ---------------------------------------------------------------------------------------------
# Utilidades de sistema de ficheros
# ---------------------------------------------------------------------------------------------
def _cargar(ruta, nombre):
    if not os.path.isfile(ruta):
        raise Uso(f"no se encontró `{ruta}` (debería viajar con el plugin)")
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - un modulo compartido roto degrada a uso, no a traceback
        raise Uso(f"{type(e).__name__}: {e}") from e
    return mod


def _es_enlace(st):
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & _REPARSE)


def _misma_identidad(a, b):
    """`lstat` y `fstat` describen el mismo fichero (si el sistema informa de inodo)."""
    if a.st_ino == 0 or b.st_ino == 0:
        return True
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


def _sha(datos):
    return hashlib.sha256(datos).hexdigest()


def _escapar(texto):
    """#9 (fix1): texto de `projects.yaml` o de la entrada, listo para la TERMINAL. Mismo criterio
    que `_sanear_detalle` del plugin (C0, C1, ESC, bidi, separadores de linea), pero sin recortar y
    con el escape a la vista (`\\x1b`, `\\u202e`): aqui se muestran rutas que el usuario tiene que
    leer y copiar tal cual son, y un espacio en su lugar mostraria otra ruta."""
    return "".join(c if c == " " or c.isprintable() else repr(c)[1:-1] for c in str(texto))


def _leer_fichero(ruta):
    """`(bytes, lstat)` del fichero regular, sin enlaces simbolicos ni duros compartidos. Lanza
    `FormaNoReconocida` si no cumple (ausente, enlace, no regular, `nlink > 1`)."""
    try:
        st = os.lstat(ruta)
    except OSError as e:
        raise FormaNoReconocida(f"`projects.yaml` ausente o ilegible ({type(e).__name__})") from e
    if _es_enlace(st):
        raise FormaNoReconocida("`projects.yaml` es un enlace simbólico o punto de reanálisis")
    if not stat.S_ISREG(st.st_mode):
        raise FormaNoReconocida("`projects.yaml` no es un fichero regular")
    if st.st_nlink != 1:
        raise FormaNoReconocida("`projects.yaml` tiene un enlace duro compartido")
    try:
        fd = os.open(ruta, os.O_RDONLY | _O_BINARY)
    except OSError as e:
        raise FormaNoReconocida(f"`projects.yaml` no se puede abrir ({type(e).__name__})") from e
    try:
        if not _misma_identidad(st, os.fstat(fd)):
            raise FormaNoReconocida("`projects.yaml` cambió de identidad durante la lectura")
        chunks = []
        while True:
            b = os.read(fd, 1 << 20)
            if not b:
                break
            chunks.append(b)
    finally:
        os.close(fd)
    return b"".join(chunks), st


# ---------------------------------------------------------------------------------------------
# Reconocedor de la gramatica minima
# ---------------------------------------------------------------------------------------------
_TOP_PROJECTS_RE = re.compile(r"^projects:[ ]*(#.*)?$")
_TOP_PROJECTS_CUALQUIERA_RE = re.compile(r"""^["']?projects["']?[ ]*:""")
_ALIAS_RE = re.compile(r"(?:^|[\s\-:\[\{,])[&*][A-Za-z0-9_]")
_CLAVE = r"""(?:[A-Za-z0-9_][A-Za-z0-9_.\-]*|'[^'\\]*'|"[^"\\]*")"""
# #11 (fix1): `root`, `"root"` y `'root'`, con espacios opcionales antes de `:`. Cualquier otra
# forma que PUEDA ser la clave `root` (tabulador antes de `:`, `root:` pegado al valor, clave
# compleja `?`, clave entre comillas con escapes) es forma no reconocida: si no, su `root` quedaba
# `None` y el conflicto por misma carpeta no saltaba.
_ROOT_CLAVE_RE = re.compile(r"""^ *(?:root|"root"|'root') *:(?:[ ]+(.*))?$""")
_ROOT_DUDOSA_RE = re.compile(r"""^ *(?:\?|["'][^"':]*\\|["']?root["']?[ \t]*:)""")


def _es_relleno(linea):
    s = linea.strip()
    return not s or s.startswith("#")


def _sangria(linea):
    return len(linea) - len(linea.lstrip(" "))


def _valor_root(resto):
    """Escalar de `root:` (plano, `'…'` o `"…"` sin escapes) o `FormaNoReconocida`."""
    resto = resto.strip()
    if not resto or resto[0] in "|>&*!{[%@`,#":
        raise FormaNoReconocida("`root` no es un escalar simple de una línea")
    if resto[0] in "\"'":
        q = resto[0]
        fin = resto.find(q, 1)
        if fin < 0:
            raise FormaNoReconocida("`root` con comillas sin cerrar")
        valor, cola = resto[1:fin], resto[fin + 1:]
        if ("\\" in valor or (q == "'" and cola.startswith("'"))
                or (cola.strip() and not re.match(r"^\s+#", cola))):
            raise FormaNoReconocida("`root` con escapes o texto tras las comillas")
        return valor
    return re.match(r"^(.*?)(?:\s+#.*)?$", resto).group(1).strip()


def analizar_yaml(datos):
    """Gramatica del diseno O1. Devuelve `{eol, n, paso, proyectos: [(nombre, root|None)],
    termina_en_eol}` o lanza `FormaNoReconocida` con el motivo."""
    if datos.startswith(b"\xef\xbb\xbf"):
        raise FormaNoReconocida("el fichero lleva BOM")
    if b"\x00" in datos:
        raise FormaNoReconocida("el fichero contiene bytes nulos")
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError as e:
        raise FormaNoReconocida("el fichero no es UTF-8") from e
    if "\r\n" in texto:
        resto = texto.replace("\r\n", "")
        if "\n" in resto or "\r" in resto:
            raise FormaNoReconocida("fin de línea mezclado")
        eol = "\r\n"
    elif "\r" in texto:
        raise FormaNoReconocida("fin de línea CR aislado")
    else:
        eol = "\n"
    termina = texto.endswith(eol)
    lineas = texto.split(eol)
    if termina:
        lineas.pop()

    for l in lineas:
        if re.match(r"^[ ]*\t", l):
            raise FormaNoReconocida("tabuladores en la indentación")
        if l.startswith("---") or l.startswith("...") or l.startswith("%"):
            raise FormaNoReconocida("documento YAML con marcas `---`/`...` o directivas")
        if not _es_relleno(l) and (_ALIAS_RE.search(l) or "<<:" in l):
            raise FormaNoReconocida("anclas, alias o `<<:`")

    abre = sum(1 for l in lineas if l.lstrip().startswith(MARCA_ABRE))
    cierra = sum(1 for l in lineas if l.lstrip().startswith(MARCA_CIERRA))
    if abre != cierra:
        raise FormaNoReconocida("bloque del plugin incompleto (marca de apertura sin cierre)")

    idx = [i for i, l in enumerate(lineas)
           if l and not l[0].isspace() and _TOP_PROJECTS_CUALQUIERA_RE.match(l)]
    if len(idx) != 1:
        raise FormaNoReconocida("no hay exactamente una clave `projects:` de primer nivel")
    ini = idx[0]
    if not _TOP_PROJECTS_RE.match(lineas[ini]):
        raise FormaNoReconocida("`projects:` con valor en línea")

    cuerpo = lineas[ini + 1:]
    for l in cuerpo:
        if not _es_relleno(l) and not l.startswith(" "):
            raise FormaNoReconocida("`projects:` no es la última clave de primer nivel")
    utiles = [l for l in cuerpo if not _es_relleno(l)]
    if not utiles:
        return {"eol": eol, "n": 2, "paso": 2, "proyectos": [], "termina_en_eol": termina}
    n = _sangria(utiles[0])
    hijo_re = re.compile(r"^ {%d}(%s):[ ]*(#.*)?$" % (n, _CLAVE))
    proyectos, vistos = [], set()
    actual = None                       # [nombre, root|None, sangria_de_campos|None]
    paso = None
    for l in utiles:
        s = _sangria(l)
        if s < n:
            raise FormaNoReconocida("indentación de hijos de `projects` incoherente")
        if s == n:
            m = hijo_re.match(l)
            if not m:
                raise FormaNoReconocida("hijo de `projects` fuera de la forma `nombre:`")
            nombre = m.group(1)
            if nombre[0] in "\"'":
                nombre = nombre[1:-1]
            if nombre in vistos:
                raise FormaNoReconocida(f"proyecto `{nombre}` duplicado")
            vistos.add(nombre)
            actual = [nombre, None, None]
            proyectos.append(actual)
            continue
        if actual[2] is None:
            actual[2] = s
            if paso is None:
                paso = s - n
        if s < actual[2]:
            raise FormaNoReconocida("indentación de campos incoherente")
        if s == actual[2]:
            m = _ROOT_CLAVE_RE.match(l)
            if m:
                if actual[1] is not None:
                    raise FormaNoReconocida("`root` repetido en un proyecto")
                actual[1] = _valor_root(m.group(1) or "")
            elif _ROOT_DUDOSA_RE.match(l):
                raise FormaNoReconocida("clave `root` (o una posible `root`) en una forma no reconocida")
    return {"eol": eol, "n": n, "paso": paso or 2,
            "proyectos": [(p[0], p[1]) for p in proyectos], "termina_en_eol": termina}


# ---------------------------------------------------------------------------------------------
# Bloque, raiz y conflicto
# ---------------------------------------------------------------------------------------------
def nombre_valido(nombre):
    """Texto para YAML 1.1 sin comillas (#2): `^[a-z][a-z0-9-]*$`, hasta 64 y no reservado."""
    return (isinstance(nombre, str) and len(nombre) <= NOMBRE_MAX and bool(NOMBRE_RE.match(nombre))
            and nombre.casefold() not in YAML_RESERVADAS)


def _alternativa(nombre):
    """Un nombre valido parecido (el slug, o `p-<slug>`), o `None` si no sale ninguno."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(nombre or "").lower()).strip("-")
    if not slug:
        return None
    for candidato in (slug[:NOMBRE_MAX].strip("-"), f"p-{slug}"[:NOMBRE_MAX].strip("-")):
        if nombre_valido(candidato):
            return candidato
    return None


def validar_nombre(nombre):
    if not nombre_valido(nombre):
        alt = _alternativa(nombre)
        raise Uso(f"nombre de proyecto inválido ({nombre!r}): debe cumplir {NOMBRE_RE.pattern}, "
                  f"tener hasta {NOMBRE_MAX} caracteres y no ser una palabra reservada de YAML "
                  f"({'/'.join(sorted(YAML_RESERVADAS))})"
                  + (f"; prueba `--nombre {alt}`" if alt else ""))
    return nombre


_ADMITIDOS_ROOT = frozenset("‌‍")   # ZWNJ/ZWJ: la misma salvedad que case_schema (#173)


def _caracter_prohibido_root(c):
    """#9 (fix1): control ASCII o categorias Cc/Cf/Zl/Zp (bidi como U+202E, NEL U+0085, U+2028…),
    la regla de `case_schema.validar_config` (#153/#173); ademas comillas y barra invertida."""
    return (ord(c) < 32 or c in "\"\\"
            or (c not in _ADMITIDOS_ROOT and unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp")))


def validar_root(root):
    if not root or any(_caracter_prohibido_root(c) for c in root):
        raise Uso("`root` vacía, con caracteres de control o de formato (Cc/Cf/Zl/Zp), comillas "
                  "o barras invertidas")
    return root


def calcular_root(export_real, config_dir):
    """`export_dir` real relativo a `kwipu/config/` (con `/`); absoluta si no hay relativa."""
    try:
        rel = os.path.relpath(export_real, os.path.realpath(config_dir))
    except ValueError:                  # otra unidad en Windows
        rel = export_real
    if os.sep != "/":
        rel = rel.replace(os.sep, "/")
    return validar_root(rel)


def construir_bloque(nombre, root, forma, fecha):
    n, p, eol = forma["n"], forma["paso"], forma["eol"]
    i0, i1, i2, i3 = " " * n, " " * (n + p), " " * (n + 2 * p), " " * (n + 2 * p + 2)
    lineas = [
        f"{i0}{MARCA_ABRE}{nombre} · añadido por /setup el {fecha} · no editar entre marcas >>>",
        f"{i0}{nombre}:",
        f"{i1}enabled: true",
        f'{i1}root: "{root}"',
        f"{i1}sources:",
        f'{i2}- path: "."',
        f"{i3}required: false",
        f"{i0}{MARCA_CIERRA}{nombre} <<<",
    ]
    return eol.join(lineas) + eol


def _norm_root(root, config_dir):
    ruta = root if os.path.isabs(root) else os.path.join(config_dir, root)
    return os.path.normcase(os.path.realpath(ruta)).casefold()


def clasificar(forma, nombre, root_nuevo, config_dir):
    """`(estado, detalle)`: nuevo | presente | conflicto."""
    objetivo = _norm_root(root_nuevo, config_dir)
    for existente, root in forma["proyectos"]:
        mismo_nombre = existente.casefold() == nombre.casefold()
        mismo_root = root is not None and _norm_root(root, config_dir) == objetivo
        if mismo_nombre and mismo_root:
            return "presente", f"`{existente}` ya está dado de alta con la misma `root`"
        if mismo_nombre:
            return "conflicto", (f"ya existe un proyecto `{existente}` con otra `root`"
                                 if root is not None else
                                 f"ya existe un proyecto `{existente}` sin `root` legible")
        if mismo_root:
            return "conflicto", f"esa carpeta ya está dada de alta como `{existente}`"
    return "nuevo", ""


# ---------------------------------------------------------------------------------------------
# Escritura (O1)
# ---------------------------------------------------------------------------------------------
def _crear_copia(ruta, previo):
    """Copia `projects.yaml.bak-<AAAAMMDDTHHMMSSZ>` con `O_EXCL` (sufijo `-1`, `-2`… si existe)."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"{ruta}.bak-{ts}"
    for k in range(1000):
        destino = base if k == 0 else f"{base}-{k}"
        try:
            fd = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_BINARY, 0o600)
        except FileExistsError:
            continue
        try:
            os.write(fd, previo)
            os.fsync(fd)
        finally:
            os.close(fd)
        with open(destino, "rb") as f:
            igual = f.read() == previo
        if not igual:                   # fuera del `with`: Windows no borra un fichero abierto
            os.remove(destino)
            raise OSError("la copia no coincide con el original")
        return destino
    raise OSError("sin nombre libre para la copia")


def _leer_fd(fd, desde, cuanto):
    """`cuanto` bytes desde `desde`, leidos por el DESCRIPTOR (nunca por ruta)."""
    os.lseek(fd, desde, os.SEEK_SET)
    chunks, falta = [], max(cuanto, 0)
    while falta > 0:
        b = os.read(fd, min(falta, 1 << 20))
        if not b:
            break
        chunks.append(b)
        falta -= len(b)
    return b"".join(chunks)


def _presente_en_ruta(ruta, bloque_bytes):
    """¿Está el bloque propio en lo que hay HOY en la ruta? `None` si no se puede leer."""
    try:
        with open(ruta, "rb") as f:
            return bloque_bytes in f.read()
    except OSError:
        return None


def _estado_real(presente):
    return {True: "tu bloque SÍ está en el fichero", False: "tu bloque NO está en el fichero",
            None: "no se ha podido comprobar si tu bloque está en el fichero"}[presente]


def _verificar_o_revertir(fd, ruta, previo, st_previo, bloque_bytes, n, fallo, copia):
    """#1/#7 (fix1). Tras el `write` (haya ido bien o haya lanzado `OSError` el propio `write` o
    el `fsync`) se decide solo con lo que dice el DESCRIPTOR. Exito: misma identidad (descriptor
    = lectura previa = ruta), `nlink == 1`, tamaño exacto y bytes `previo + bloque`. Si no, se
    TRUNCA POR EL DESCRIPTOR unicamente si lo que sobra es, byte a byte, lo que ESTE proceso
    escribio y nada mas cambio (identidad intacta, ruta sin reemplazar, tamaño exacto, prefijo
    igual). En cualquier otro caso NO se toca el fichero: puede haber bytes ajenos (otro
    `/setup`, un editor que guarda por rename, otro escritor que añade) y la constitucion §4
    prohibe borrarlos. Devuelve `(ok, mensaje, presente)` con el estado REAL del bloque."""
    base = len(previo)
    # Lo que este proceso pudo dejar al final: si `write` informo `n`, esos `n` bytes; si lanzo,
    # nada o el bloque entero (un `write` que lanza no informa de escrituras parciales).
    propios = [bloque_bytes[:n]] if n is not None else [b"", bloque_bytes]
    causa = (f"error de E/S tras escribir ({type(fallo).__name__})" if fallo is not None
             else "la verificación posterior falló")
    try:
        st = os.fstat(fd)
        prefijo = _leer_fd(fd, 0, base)
        cola = _leer_fd(fd, base, st.st_size - base)
        try:
            st_ruta = os.lstat(ruta)
        except OSError:
            st_ruta = None
    except OSError as e:
        presente = _presente_en_ruta(ruta, bloque_bytes)
        return False, (f"{causa} y no se pudo releer ({type(e).__name__}): no se toca nada; "
                       f"revísalo a mano (copia en {copia}) · {_estado_real(presente)}"), presente
    mismo = (_misma_identidad(st_previo, st) and st_ruta is not None and not _es_enlace(st_ruta)
             and _misma_identidad(st, st_ruta))
    if (fallo is None and n == len(bloque_bytes) and mismo and st.st_nlink == 1
            and st.st_size == base + len(bloque_bytes) and prefijo == previo and cola == bloque_bytes):
        return True, "", True
    for propio in propios:
        if not (mismo and prefijo == previo and st.st_size == base + len(propio) and cola == propio):
            continue
        if not propio:
            return False, f"{causa}: no se llegó a añadir nada · {_estado_real(False)}", False
        try:
            os.ftruncate(fd, base)               # por el DESCRIPTOR, nunca por ruta
            try:
                os.fsync(fd)
            except OSError:
                pass                             # el tamaño se comprueba abajo con `fstat`
            revertido = os.fstat(fd).st_size == base
        except OSError:
            revertido = False
        if revertido:
            return False, f"{causa}: se revirtió lo añadido (truncado) · {_estado_real(False)}", False
        presente = _presente_en_ruta(ruta, bloque_bytes)
        return False, (f"{causa} y no se pudo revertir: revísalo a mano (copia en {copia}) · "
                       f"{_estado_real(presente)}"), presente
    presente = _presente_en_ruta(ruta, bloque_bytes)
    detalle = " (prefijo alterado)" if mismo and prefijo != previo else ""
    return False, (f"el fichero cambió durante la escritura{detalle}: revísalo a mano "
                   f"(copia en {copia}) · {_estado_real(presente)}"), presente


def escribir_anadiendo(ruta, previo, st_previo, bloque_bytes, copia=None):
    """Añade `bloque_bytes` en un solo `write` y lo verifica (#1/#7/#10, fix1). Devuelve
    `(ok, mensaje, presente)`: `presente` es el estado REAL del bloque propio en el fichero
    (`True`/`False`, o `None` si no se pudo comprobar). Ver `_verificar_o_revertir`."""
    fd = os.open(ruta, os.O_RDWR | os.O_APPEND | _O_BINARY | _O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if (not _misma_identidad(st_previo, st) or st.st_size != len(previo)
                or st.st_nlink != 1 or not stat.S_ISREG(st.st_mode)):
            return False, "el fichero cambió antes de escribir; no se ha tocado", False
        n, fallo = None, None
        try:
            n = _os_write(fd, bloque_bytes)
            os.fsync(fd)
        except OSError as e:
            fallo = e
        return _verificar_o_revertir(fd, ruta, previo, st_previo, bloque_bytes, n, fallo, copia)
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------------------------
def _comandos(stack):
    return [
        f"cd {shlex.quote(stack)}",
        "python -m source_manager.build_view --config kwipu/config/projects.yaml "
        "--output kwipu/runtime/knowledge-view-v2",
        "docker compose restart kwipu kwipu-bridge kwipu-mcp",
    ]


def _fuera_de(hijo, padre):
    try:
        rel = os.path.relpath(hijo, padre)
    except ValueError:
        return True
    return rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel)


def _resolver(args):
    """Nombre, `export_dir` real, stack, `kwipu/`, `kwipu/config/`: todo validado. Lanza `Uso`."""
    ks = _cargar(os.path.join(SHARED, "knowledge-schema.py"), "kpa_knowledge_schema")
    me = _cargar(os.path.join(BACKENDS_DIR, "markdown_export.py"), "kpa_markdown_export")
    config, _o, _r, errores = ks.cargar_taxonomia(args.root)
    if errores:
        raise Uso("; ".join(f"{e['fichero']}: {e['campo']}: {e['mensaje']}" for e in errores))
    backend = (config.get("backends") or {}).get(args.backend)
    if not isinstance(backend, dict) or backend.get("type") != "markdown-export":
        raise Uso(f"`taxonomy.json` no declara un backend `markdown-export` llamado `{args.backend}`")
    cfg = dict(backend.get("config") or {})
    if not cfg.get("export_dir"):
        raise Uso(f"el backend `{args.backend}` no declara `export_dir`")
    cfg["_root"] = os.path.abspath(args.root)
    try:
        export_real = me._export_dir_resuelto(cfg)
    except Exception as e:  # noqa: BLE001 - ConfigInvalida del adaptador
        raise Uso(str(e)) from e
    if _fuera_de(export_real, os.path.realpath(args.root)):
        raise Uso("`export_dir` queda fuera de la raíz del proyecto")
    nombre = validar_nombre(args.nombre if args.nombre is not None else config.get("id_prefix"))
    if re.search(r"[\x00-\x1f\x7f]", args.stack):
        raise Uso("ruta del stack con caracteres de control")
    stack = os.path.abspath(args.stack)
    if not os.path.isdir(stack):
        raise Uso(f"el stack `{args.stack}` no es un directorio")
    kw, config_dir = os.path.join(stack, "kwipu"), os.path.join(stack, "kwipu", "config")
    if not os.path.isdir(config_dir):
        raise Uso(f"`{args.stack}` no parece un stack Kwipu: falta `kwipu/config/`")
    return nombre, export_real, stack, kw, config_dir


def ejecutar(args, out):
    try:
        nombre, export_real, stack, kw, config_dir = _resolver(args)
        root_val = calcular_root(export_real, config_dir)
    except Uso as e:
        print(f"kwipu-project-add: {_escapar(e)}", file=sys.stderr)
        return E_USO
    ruta = os.path.join(config_dir, "projects.yaml")
    fecha = datetime.date.today().isoformat()
    defecto = {"eol": "\n", "n": 2, "paso": 2}
    res = {"estado": None, "nombre": nombre, "root": root_val, "destino": ruta, "sha256": None,
           "bloque": None, "escrito": False, "bloque_presente": None, "copia": None, "mensaje": "",
           "comandos": []}

    def emitir(codigo, comandos=False):
        if comandos:
            res["comandos"] = _comandos(stack)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2), file=out)
            return codigo
        # #9 (fix1): en modo texto se escapa todo lo que viene de `projects.yaml` o de la entrada
        print(f"estado: {res['estado']}" + (f" · {_escapar(res['mensaje'])}" if res["mensaje"] else ""),
              file=out)
        print(f"destino: {_escapar(json.dumps(ruta, ensure_ascii=False))}", file=out)
        if res["sha256"]:
            print(f"sha256: {res['sha256']}", file=out)
        if res["copia"]:
            print(f"copia de seguridad: {_escapar(json.dumps(res['copia'], ensure_ascii=False))}",
                  file=out)
        if res["bloque"] and res["estado"] in ("nuevo", "no-reconocido"):
            print("bloque:", file=out)
            print(res["bloque"].rstrip("\r\n"), file=out)
        if comandos:
            print("Ejecútalos tú (este script NO los ejecuta):", file=out)
            for c in res["comandos"]:
                print(f"  {_escapar(c)}", file=out)
        return codigo

    for parte in (kw, config_dir):
        if _es_enlace(os.lstat(parte)):
            res.update(estado="no-reconocido", mensaje=f"`{os.path.basename(parte)}` es un enlace",
                       bloque=construir_bloque(nombre, root_val, defecto, fecha))
            return emitir(E_FORMA, comandos=True)
    previo = st = None
    try:
        previo, st = _leer_fichero(ruta)
        res["sha256"] = _sha(previo)
        forma = analizar_yaml(previo)
    except FormaNoReconocida as e:
        res.update(estado="no-reconocido", bloque=construir_bloque(nombre, root_val, defecto, fecha),
                   mensaje=f"{e} · pega el bloque a mano al final de `projects:` (dentro de esa clave)")
        return emitir(E_FORMA, comandos=True)

    estado, detalle = clasificar(forma, nombre, root_val, config_dir)
    res.update(estado=estado, mensaje=detalle, bloque=construir_bloque(nombre, root_val, forma, fecha))
    if estado == "presente":
        return emitir(E_OK)
    if estado == "conflicto":
        res["mensaje"] += " · elige otro nombre (`--nombre`)"
        return emitir(E_CONFLICTO)
    if not args.apply:
        return emitir(E_OK)

    if not args.esperado:                     # #13 (fix1): es un error de USO, no de E/S
        res["mensaje"] = "--apply exige --esperado <sha256 de la vista previa>"
        return emitir(E_USO)
    if args.esperado.lower() != res["sha256"]:
        res["mensaje"] = "el fichero cambió desde la vista previa: repite la vista previa"
        return emitir(E_IO)
    try:
        os.makedirs(export_real, exist_ok=True)
        res["copia"] = _crear_copia(ruta, previo)
    except OSError as e:
        res["mensaje"] = f"no se escribe nada: falló la preparación o la copia de seguridad ({e})"
        return emitir(E_IO)
    payload = (b"" if (forma["termina_en_eol"] or not previo) else forma["eol"].encode())
    payload += res["bloque"].encode("utf-8")
    try:
        ok, msg, presente = escribir_anadiendo(ruta, previo, st, payload, copia=res["copia"])
    except OSError as e:                      # antes del `write` (abrir, `fstat`): nada escrito
        ok, msg, presente = (False, f"error de E/S al abrir para escribir ({type(e).__name__}); "
                                    "no se ha tocado", False)
    if not ok:
        # #7 (fix1): se informa el estado REAL del bloque (`bloque_presente`), no «no escrito»
        res.update(escrito=bool(presente), bloque_presente=presente,
                   mensaje=msg if "(copia en " in msg else f"{msg} · copia en {res['copia']}")
        return emitir(E_IO)
    res.update(estado="añadido", escrito=True, bloque_presente=True,
               mensaje="bloque añadido al final de `projects:`")
    return emitir(E_OK, comandos=True)


def _parser():
    ap = argparse.ArgumentParser(
        description="Da de alta el proyecto en projects.yaml de Kwipu (solo añade, con confirmación).")
    ap.add_argument("--stack", required=True, help="carpeta del stack (contiene kwipu/config/)")
    ap.add_argument("--root", default=".", help="raíz del proyecto (con .claude/knowledge-services/)")
    ap.add_argument("--backend", default="kwipu", help="id del backend markdown-export")
    ap.add_argument("--nombre", default=None, help="nombre del proyecto (por defecto, el id_prefix)")
    ap.add_argument("--apply", action="store_true", help="escribe (exige --esperado)")
    ap.add_argument("--esperado", default=None, help="sha256 de la vista previa")
    ap.add_argument("--json", action="store_true")
    return ap


def main(argv=None):
    return ejecutar(_parser().parse_args(argv), sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
