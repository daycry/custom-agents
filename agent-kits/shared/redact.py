#!/usr/bin/env python3
"""
redact.py — redacción DETERMINISTA de secretos evidentes (agent-kits/shared).

Extraído de `journal.py:redactar` (session-end-durable-capture T-02, CA-11): fuente ÚNICA de
`redactar` y sus constantes (`REDACTADO`, `_SECRETOS_RE`). Antes de que la prosa del usuario toque
el LOG CRUDO (`journal.py capture`) o la entrada del journal (que SE VERSIONA), se sustituyen los
secretos evidentes: claves de API con prefijo conocido, JWT, bloques PEM, `Bearer`, y
`clave|token|password… = valor` con valor de ≥ 8 caracteres que mezcla letras y dígitos/símbolos.
Alta precisión antes que cobertura: «tokens por hora (479326)» o «password reset flow» no se tocan.

`anonimizar(texto, raiz, home, usuario)` (panel-redesign T-04, CA-41) quita además los datos
personales de lo que el panel publica: raíz del proyecto → `.`, home → `~`, correos → `<correo>` y
usuario del sistema → `<usuario>`. Vive FUERA del bloque replicado (no tiene copia en journal.py).
Orden fijo del saneado de todo texto persistido o exportado por el panel y el almacén de actividad:
redactar → anonimizar → quitar controles → recortar. Redactar va primero porque sus patrones
reconocen el secreto entero (`token=…`); recortar va al final para no partir un secreto ni una ruta
antes de sustituirlos.

`journal.py` importa `redactar`/`REDACTADO`/`_SECRETOS_RE` de aquí (misma carpeta,
`agent-kits/shared/`); si viaja sin este fichero (paquete portable, ver `docs/CONVENTIONS.md` regla
«compartido vs privado»), usa una copia local declarada en `agent-kits/shared/copias.json` (bloque
`redact_redactar`, ADR-016), comparada byte a byte por `tests/test_copias_declaradas.py`.
"""
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# --8<-- redact (redactar + constantes) — REPLICADO LITERAL en agent-kits/shared/redact.py (canónico) y en agent-kits/shared/journal.py (respaldo local, ADR-016)
REDACTADO = "[secreto redactado]"
_CLAVES_SENSIBLES = r"api[_-]?key|secret[_-]?key|access[_-]?key|secret|token|passw(?:or)?d|pwd|clave|contrase[ñn]a"
_CLAVE_SENSIBLE_RE = re.compile(r"(?i)(?:" + _CLAVES_SENSIBLES + r")")
_PEM_BEGIN_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_PEM_END_RE = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")
# Sin `\b` a la izquierda: la clave casa tambien tras `_`, `-` o un prefijo (`DB_PASSWORD=`, `API_TOKEN=`,
# `AWS_SECRET_ACCESS_KEY=`, `PGPASSWORD=`; panel-redesign T-42 fix1, C-1). El `\b` final se mantiene:
# `my_token_count=` o `tokens=` no son claves sensibles.
_ASIGNACION_RE = re.compile(r"(?i)(?:" + _CLAVES_SENSIBLES + r")\b\s*[:=]\s*[\"']?")
_ASIGNACION_FIN_RE = re.compile(r"[\s\"']")
_ASIGNACION_LETRA_RE = re.compile(r"[A-Za-z]", re.I)
_ASIGNACION_VARIADA_RE = re.compile(r"[0-9!@#$%^&*]")
_SECRETOS_RE = (
    re.compile(r"\b(?:sk-ant-|sk-|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|xox[baprs]-|glpat-|AKIA|ASIA)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(?P<pre>\bbearer\s+)(?P<sec>[A-Za-z0-9._~+/=\-]{20,})"),
    # `Authorization: Basic <base64>` (cabecera HTTP, tambien como par JSON o con `Proxy-`): panel-redesign T-42
    re.compile(r"(?i)(?P<pre>\bauthorization[\"']?\s*[:=]\s*[\"']?basic\s+)(?P<sec>[A-Za-z0-9+/=_\-]{6,})"),
    # par clave-valor JSON (o repr de Python) con la clave sensible ENTRECOMILLADA: el valor entero, sea
    # cual sea su forma (#139 de training-data-services: `"password": "…"` no casaba con `password=`)
    re.compile(r"(?i)(?P<pre>(?P<q>[\"'])(?:" + _CLAVES_SENSIBLES + r")(?P=q)\s*:\s*(?P<q2>[\"']))"
               r"(?P<sec>(?:\\.|(?!(?P=q2))[^\\])+)(?=(?P=q2))"),
)


def _redactar_pem(texto):
    """First valid BEGIN through the next valid END, independently of family.

    An unterminated block remains intact. Search its missing END only once,
    rather than retrying the entire remaining body at every nested BEGIN.
    """
    partes, cursor = [], 0
    while True:
        inicio = _PEM_BEGIN_RE.search(texto, cursor)
        if inicio is None:
            break
        fin = _PEM_END_RE.search(texto, inicio.end())
        if fin is None:
            break
        partes.extend((texto[cursor:inicio.start()], REDACTADO))
        cursor = fin.end()
    partes.append(texto[cursor:])
    return "".join(partes)


def _redactar_asignaciones(texto):
    """Preserve the original >=8, letter and diverse-character classification.

    Cache each whitespace/quote-delimited value's end and last qualifying
    characters. Repeated sensitive prefixes inside a failed candidate reuse
    that scan instead of rescanning the remaining suffix quadratically.
    """
    partes, cursor, posicion = [], 0, 0
    token_fin = -1
    ultima_letra = ultimo_variado = -1
    while True:
        prefijo = _ASIGNACION_RE.search(texto, posicion)
        if prefijo is None:
            break
        inicio = prefijo.end()
        if inicio >= token_fin:
            fin = _ASIGNACION_FIN_RE.search(texto, inicio)
            token_fin = fin.start() if fin else len(texto)
            ultima_letra = ultimo_variado = -1
            for match in _ASIGNACION_LETRA_RE.finditer(texto, inicio, token_fin):
                ultima_letra = match.start()
            for match in _ASIGNACION_VARIADA_RE.finditer(texto, inicio, token_fin):
                ultimo_variado = match.start()
        if token_fin - inicio >= 8 and ultima_letra >= inicio and ultimo_variado >= inicio:
            partes.extend((texto[cursor:prefijo.start()], prefijo.group(), REDACTADO))
            cursor = posicion = token_fin
        else:
            posicion = inicio
    partes.append(texto[cursor:])
    return "".join(partes)


# Credenciales como argumento de un comando conocido (T-42 fix1 C-1, fix2 2-2/2-3, fix3 3-1): `curl -u|-U|
# --user|--proxy-user usuario:clave` (tambien agrupadas, `-sSu`) y `mysql*`/`mariadb* -p<clave>|--password=`.
# Se trocea como un shell: `|`, `;`, `&` y salto de linea separan comandos fuera de comillas (un `&` pegado por
# los dos lados, como en una URL, no separa). Una credencial se tapa si el programa (`curl`, `mysql…`, por
# nombre, con o sin ruta y en CUALQUIER posicion: tras `sudo -u x`, `--`, `timeout 10`, `xargs`, `$(`) aparece
# ANTES en el mismo comando (las formas con `=`, en cualquier punto del comando); asi `cp -pr /var/lib/mysql`, `docker run -p3306:3306 mysql:8` o `docker run -u
# 1000:1000 img curl …` no se tocan (el programa va despues). Una comilla solo agrupa si cierra en la misma
# linea: la que no cierra (`can't`) es un caracter mas y no esconde nada. Lo que va entre comillas se trocea
# ademas como comando anidado (`sh -c "…"`, `ssh host '…'`; dentro de `"…"`, `\"` vuelve a ser comilla).
# Ante la duda, tapar de mas. Lineal (cada nivel de comillas recorre su texto una vez) e idempotente.
_TROZO_RE = re.compile(r"[^\s\"'\\|;&]+")
_DOBLE_CIERRE_RE = re.compile(r"(?:\\.|[^\"\\\n])*\"")
_ESCAPE_DOBLE_RE = re.compile(r"\\([\"\\$`])")
_PROGRAMA_RE = re.compile(r"(?i)(?<![\w.\-])(?:(?P<curl>curl)|mysql[a-z]*|mariadb(?:-[a-z]+)?)(?:\.exe)?(?![\w.\-:])")
_VALOR_DE_OPCION = frozenset(("--name", "--hostname"))  # `docker run --name mysql -p3306:3306`: un nombre
_CURL_SIN_ARGUMENTO = frozenset("0123456#aBfgGIijJkLlMnNOpqRsSvZ")
_PROFUNDIDAD_MAX = 4


def _desescapar(escape):
    r"""`\"` -> `\x01"` y `\\` -> `\x01\x01` (mismo largo): dentro de `"…"`, lo escapado vuelve a ser texto."""
    return "\x01" + ("\x01" if escape.group(1) == "\\" else escape.group(1))


def _sin_comillas(palabra):
    return palabra.replace('"', "").replace("'", "")


def _programa(palabra, anterior):
    """'curl', 'mysql' o None para una palabra (sin comillas) de un comando; `anterior`, la palabra previa."""
    m = _PROGRAMA_RE.search(palabra)
    if m is None or ":" in palabra[2:m.start()]:
        return None  # `/data/x:/var/lib/mysql` (volumen) o `https://h/curl` (URL) no son el programa
    if anterior in _VALOR_DE_OPCION:
        return None
    return "curl" if m.group("curl") else "mysql"


def _tapar(texto, inicio, fin, base, cambios, curl):
    """Tapa la clave de texto[inicio:fin] (tras el primer `:` en curl); respeta comillas e idempotencia."""
    valor = texto[inicio:fin]
    if curl:
        dos_puntos = valor.find(":")
        if dos_puntos < 0:
            return
        inicio += dos_puntos + 1
    while inicio < fin and texto[inicio] in "\"'\x01":
        inicio += 1
    final = fin
    while final > inicio and texto[final - 1] in "\"'\x01":
        final -= 1
    if final > inicio and not texto.startswith(REDACTADO, inicio):
        cambios.append((base + inicio, base + final))


def _redactar_comando(texto, palabras, base, cambios, heredado):
    """Redacta un comando y devuelve, por palabra, los programas vistos ANTES de ella (y todos los del comando).

    Las formas cortas o separadas (`-u x:y`, `-pX`) se anclan a un programa anterior; las de `=` (`--user=`,
    `--proxy-user=`, `--password=`), a un programa en cualquier punto del comando, como fix1. `heredado` son
    los programas del comando que envuelve a unas comillas (`curl '-u' 'a:X'`, `mysql "-pX"`)."""
    limpias = [_sin_comillas(texto[a:b]) for a, b in palabras]
    programas = [_programa(p, limpias[k - 1] if k else None) for k, p in enumerate(limpias)]
    vistos, todos = heredado
    todos = todos.union(programas)
    antes, j = [], 0
    while j < len(palabras):
        a, b = palabras[j]
        w = texto[a:b]
        programa = programas[j]
        antes.append(vistos)
        j += 1
        if programa is not None:
            vistos = vistos | {programa}
            continue
        q = len(w) - len(w.lstrip("\"'\x01"))  # `"-pX"`: la opcion entre comillas tambien cuenta
        a, w = a + q, w[q:]
        if w.startswith("--password=") and "mysql" in todos:
            _tapar(texto, a + 11, b, base, cambios, False)
        elif w.startswith(("--user=", "--proxy-user=")) and "curl" in todos:
            _tapar(texto, a + w.index("=") + 1, b, base, cambios, True)
        if "mysql" in vistos and w.startswith("-p") and len(w.rstrip("\"'\x01")) > 2:
            _tapar(texto, a + 2, b, base, cambios, False)
        if "curl" not in vistos:
            continue
        if limpias[j - 1] in ("-u", "-U", "--user", "--proxy-user"):
            if j < len(palabras):  # el valor se mira tambien como palabra: `-u -pX` tras curl y mysql
                _tapar(texto, palabras[j][0], palabras[j][1], base, cambios, True)
        elif w.startswith("-") and not w.startswith("--"):
            for i in range(1, len(w)):
                if w[i] in "uU":
                    if i + 1 < len(w.rstrip("\"'\x01")):
                        _tapar(texto, a + i + 1, b, base, cambios, True)
                    elif j < len(palabras):
                        _tapar(texto, palabras[j][0], palabras[j][1], base, cambios, True)
                    break
                if w[i] not in _CURL_SIN_ARGUMENTO:
                    break
    antes.append(vistos)
    return antes, todos


def _trocear(texto, base, profundidad, cambios, heredado=(frozenset(), frozenset())):
    """Trocea `texto` en comandos y redacta cada uno; el contenido de cada comilla cerrada, tambien, como
    comando anidado que hereda los programas que su comando tenia antes de esa palabra."""
    palabras, pendientes, anidados, inicio, i, n = [], [], [], None, 0, len(texto)
    fin_linea, sin_cierre = -1, {"'": -1, '"': -1}

    def cerrar_comando():
        antes, todos = _redactar_comando(texto, palabras, base, cambios, heredado)
        anidados.extend((a, b, c, (antes[k], todos)) for a, b, c, k in pendientes)
        palabras.clear()
        pendientes.clear()

    while i < n:
        m = _TROZO_RE.match(texto, i)
        if m is not None:
            inicio = i if inicio is None else inicio
            i = m.end()
            continue
        c = texto[i]
        if c == "\\":
            salto = 2 if texto.startswith("\n", i + 1) else 3 if texto.startswith("\r\n", i + 1) else 0
            if salto:  # continuacion de linea: separa palabras, no comandos
                if inicio is not None:
                    palabras.append((inicio, i))
                    inicio = None
                i += salto
                continue
            inicio = i if inicio is None else inicio
            i += 2
            continue
        if c in "\"'":
            inicio = i if inicio is None else inicio
            if i >= fin_linea:
                fin_linea = texto.find("\n", i)
                fin_linea = n if fin_linea < 0 else fin_linea
            cierre = -1
            if i >= sin_cierre[c]:
                if c == "'":
                    cierre = texto.find("'", i + 1, fin_linea)
                else:
                    d = _DOBLE_CIERRE_RE.match(texto, i + 1, fin_linea)
                    cierre = d.end() - 1 if d else -1
                if cierre < 0:
                    sin_cierre[c] = fin_linea  # ninguna comilla de este tipo cierra ya en esta linea
            if cierre < 0:
                i += 1  # una comilla que no cierra es un caracter mas
            else:
                if cierre > i + 1 and profundidad < _PROFUNDIDAD_MAX:
                    pendientes.append((i + 1, cierre, c, len(palabras)))
                i = cierre + 1
            continue
        if c == "&" and inicio is not None and i + 1 < n and not (texto[i + 1].isspace() or texto[i + 1] in "|;&"):
            i += 1  # `&` pegado por los dos lados (`?a=1&b=2`): parte de la palabra
            continue
        if inicio is not None:
            palabras.append((inicio, i))
            inicio = None
        if c in "|;&\n":
            cerrar_comando()
        i += 1
    if inicio is not None:
        palabras.append((inicio, n))
    cerrar_comando()
    for a, b, c, contexto in anidados:
        interior = texto[a:b]
        if c == '"':  # mismo largo: `\"` -> `\x01"`, para que la comilla escapada vuelva a agrupar
            interior = _ESCAPE_DOBLE_RE.sub(_desescapar, interior)
        _trocear(interior, base + a, profundidad + 1, cambios, contexto)


def _redactar_argumentos(texto):
    cambios = []
    _trocear(texto, 0, 0, cambios)
    partes, cursor = [], 0
    for inicio, fin in sorted(cambios):
        if inicio < cursor:  # solapa con lo ya tapado (comando y comando anidado): una sola marca
            cursor = max(cursor, fin)
            continue
        partes.extend((texto[cursor:inicio], REDACTADO))
        cursor = fin
    partes.append(texto[cursor:])
    return "".join(partes)


def es_clave_sensible(clave):
    """True si `clave` es EXACTAMENTE una clave sensible (`password`, `api_key`, `token`…, sin
    distinguir mayusculas): `redactar_estructura` del recorder redacta entonces su valor textual."""
    return isinstance(clave, str) and _CLAVE_SENSIBLE_RE.fullmatch(clave) is not None


def redactar(texto):
    """Sustituye los secretos evidentes (_SECRETOS_RE) por REDACTADO conservando el prefijo (`token=`, `Bearer `)."""
    texto = _redactar_pem(str(texto))
    for pat in _SECRETOS_RE[:-1]:
        texto = pat.sub(lambda m: (m.group("pre") if "pre" in m.groupdict() else "") + REDACTADO, texto)
    texto = _redactar_argumentos(texto)
    texto = _redactar_asignaciones(texto)
    texto = _SECRETOS_RE[-1].sub(lambda m: m.group("pre") + REDACTADO, texto)
    return texto
# --8<-- fin redact (redactar + constantes)


# ---- anonimizar (panel-redesign T-04, CA-41) — FUERA del bloque replicado: solo vive aquí --------
ANON_RAIZ = "."
ANON_HOME = "~"
ANON_USUARIO = "<usuario>"
ANON_CORREO = "<correo>"
_MARCAS_PROPIAS = frozenset(m for m in (ANON_RAIZ, ANON_HOME, ANON_USUARIO, ANON_CORREO)
                            if m.startswith("<") and m.endswith(">"))
_ANON_USUARIO_MIN = 3   # «a», «yo»: un usuario tan corto casaría con palabras corrientes
# Local-part y dominio con TLD alfabético: «chart.js@4.5.1» o «@playwright/test» no son correos.
_CORREO_RE = re.compile(r"(?<![\w.%+\-])[\w.%+\-]+@[\w\-]+(?:\.[\w\-]+)*\.[A-Za-z]{2,}(?![\w\-])")
_DRIVE_RE = re.compile(r"^([A-Za-z]):(?:[\\/]|$)")
_SEP = r"[\\/]+"                         # separador de ruta: barra invertida o barra, repetidas
_ANTES_RUTA = r"(?<![\w.\-])"            # no empieza en mitad de un nombre («docs/home/x»)
_TRAS_RUTA = r"(?![\w\-]|\.[\w\-])"      # termina en límite de componente; un punto final sí vale


def _componentes(ruta):
    return [c for c in re.split(_SEP, ruta.strip()) if c]


def _corto_83(componente):
    """Forma corta 8.3 de Windows (`ABCDEFGHIJ` → `ABCDEF~N`) de un componente largo sin punto."""
    if "." in componente or (len(componente) <= 8 and " " not in componente):
        return None
    base = re.sub(r"[^A-Za-z0-9_$%'`\-@{}!#()&^]", "", componente)[:6]
    return re.escape(base) + r"~\d{1,4}" if base else None


def _patron_ruta(ruta):
    """Regex de una ruta absoluta con cualquier separador, en sus formas equivalentes. Windows (con
    unidad): sin distinguir mayúsculas, también `/c/…` (Git Bash) y los alias 8.3. POSIX: literal."""
    ruta = str(ruta).strip()
    unidad = _DRIVE_RE.match(ruta)
    partes = _componentes(ruta[2:] if unidad else ruta)
    if not partes:
        return None   # la raíz «/» o una unidad sola borrarían toda ruta absoluta
    if unidad:
        cuerpo = _SEP.join("(?:" + re.escape(p) + ("|" + _corto_83(p) if _corto_83(p) else "") + ")" for p in partes)
        letra = re.escape(unidad.group(1))
        return re.compile(_ANTES_RUTA + "(?:" + letra + ":|/" + letra + ")" + _SEP + cuerpo + _TRAS_RUTA, re.I)
    return re.compile(_ANTES_RUTA + _SEP + _SEP.join(re.escape(p) for p in partes) + _TRAS_RUTA)


def _alias(valor):
    if valor is None or isinstance(valor, (str, bytes)) or hasattr(valor, "__fspath__"):
        valor = [valor]
    return [str(v) for v in valor if v is not None and str(v).strip()]


def _marca_usuario(m):
    """Sustituye el usuario salvo que sea EXACTAMENTE el interior de una marca que produce este
    módulo (`<usuario>`, `<correo>`: constantes `ANON_*` entre `<>`, en minúsculas): así `anonimizar`
    es idempotente aunque la cuenta se llame como una marca, y un texto que se anonimiza en origen y
    otra vez al exportar no acaba en `<<usuario>>`. Cualquier otro `<…>` (`<jdoeuser>`) se anonimiza."""
    texto = m.string
    marca = texto[m.start() - 1:m.end() + 1]
    return m.group(0) if marca in _MARCAS_PROPIAS else ANON_USUARIO


def anonimizar(texto, raiz, home, usuario):
    """Quita los datos personales de un texto que va a un HTML/JSON del panel (CA-41).

    Función PURA: no lee el entorno, el disco ni la plataforma; lo que se anonimiza son
    exactamente los argumentos. `raiz` y `home` aceptan una ruta (str/Path) o una lista de alias
    equivalentes; `usuario` es el nombre de la cuenta del sistema. Sustituye, en este orden:
      1. la raíz del proyecto → `.` (antes que el home: suele estar dentro de él);
      2. el home → `~`;
      3. los correos → `<correo>` (antes que el usuario: `ana@x.org` no deja `<usuario>@x.org`);
      4. el usuario como palabra entera → `<usuario>`, sin distinguir mayúsculas.
    Las rutas casan con barra invertida o `/`, solo en límite de componente y nunca dentro de una ruta
    relativa; las de Windows (con unidad) sin distinguir mayúsculas y también como `/c/…` y con
    sus nombres cortos 8.3. Un usuario de menos de 3 caracteres, la raíz `/` o una unidad sola
    se ignoran. Va DESPUÉS de `redactar` (ver el orden del módulo)."""
    texto = str(texto)
    for valor, marca in ((raiz, ANON_RAIZ), (home, ANON_HOME)):
        for patron in filter(None, (_patron_ruta(r) for r in sorted(_alias(valor), key=len, reverse=True))):
            texto = patron.sub(marca, texto)
    texto = _CORREO_RE.sub(ANON_CORREO, texto)
    usuario = str(usuario or "").strip()
    if len(usuario) >= _ANON_USUARIO_MIN:
        texto = re.sub(_ANTES_RUTA + re.escape(usuario) + r"(?![\w\-])", _marca_usuario, texto, flags=re.I)
    return texto
