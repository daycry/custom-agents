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


# Credenciales como argumento de un comando conocido (T-42 fix1 C-1, fix2 2-2/2-3): `curl -u|-U|--user|
# --proxy-user usuario:clave` (tambien agrupadas, `-sSu`) y `mysql*`/`mariadb* -p<clave>|--password=<clave>`.
# Se trocea como un shell (palabras con comillas; `|`, `;`, `&` y salto de linea separan comandos fuera de
# comillas; un `&` pegado por los dos lados, como en una URL, no separa) y solo se miran las opciones que van
# DESPUES del programa real: la palabra exacta `curl`/`mysql…` (con ruta, solo en posicion de comando).
# Asi `cp -pr /var/lib/mysql`, `docker run -p3306:3306 mysql:8`, `docker run -u 1000:1000 img curl …`,
# `ssh -p 22`, `mysql -p appdb` (sin clave) o `--user-agent "Foo:bar"` no se tocan. Lineal e idempotente.
_PALABRA_RE = re.compile(r"(?:[^\s\"'|;&]+|\"(?:\\.|[^\"\\\n])*\"?|'[^'\n]*'?|(?<=[^\s|;&])&(?=[^\s|;&]))+|[|;&\n]")
_PROGRAMA_RE = re.compile(r"(?i)(?:(?P<curl>curl)|mysql[a-z]*|mariadb(?:-[a-z]+)?)(?:\.exe)?")
_ENVOLTORIOS = frozenset(("sudo", "doas", "env", "exec", "nohup", "time", "command", "nice"))
_VARIABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_CURL_SIN_ARGUMENTO = frozenset("0123456#aBfgGIijJkLlMnNOpqRsSvZ")


def _sin_comillas(palabra):
    return palabra.replace('"', "").replace("'", "")


def _posicion_de_comando(limpias):
    """Indice de la primera palabra que no es `VAR=valor`, un envoltorio (`sudo`, `env`...) ni opcion de este."""
    envuelto = False
    for k, p in enumerate(limpias):
        if p in _ENVOLTORIOS:
            envuelto = True
        elif not (_VARIABLE_RE.match(p) or (envuelto and p.startswith("-"))):
            return k
    return len(limpias)


def _programa(limpias, k, posicion):
    """'curl', 'mysql' o None para la palabra k de un comando (ya sin comillas)."""
    base = re.split(r"[\\/]", limpias[k])[-1]
    m = _PROGRAMA_RE.fullmatch(base)
    if m is None or not base:
        return None
    if base != limpias[k]:  # con ruta: solo en posicion de comando
        if k != posicion:
            return None
    elif k and limpias[k - 1].startswith("--") and "=" not in limpias[k - 1]:
        return None  # valor de una opcion larga (`--name mysql`), no el programa
    return "curl" if m.group("curl") else "mysql"


def _tapar(texto, inicio, fin, cambios, curl):
    """Tapa la clave de texto[inicio:fin] (tras el primer `:` en curl); respeta comillas e idempotencia."""
    valor = texto[inicio:fin]
    if curl:
        dos_puntos = valor.find(":")
        if dos_puntos < 0:
            return
        inicio += dos_puntos + 1
    while inicio < fin and texto[inicio] in "\"'":
        inicio += 1
    final = fin
    while final > inicio and texto[final - 1] in "\"'":
        final -= 1
    if final > inicio and not texto.startswith(REDACTADO, inicio):
        cambios.append((inicio, final))


def _redactar_comando(texto, palabras, cambios):
    limpias = [_sin_comillas(texto[a:b]) for a, b in palabras]
    posicion = _posicion_de_comando(limpias)
    k = 0
    while k < len(palabras):
        programa = _programa(limpias, k, posicion)
        if programa is None:
            k += 1
            continue
        j = k + 1
        while j < len(palabras):
            if _programa(limpias, j, posicion) is not None:
                break  # otro programa del mismo comando (`docker exec … mysql`): lo mira la vuelta exterior
            a, b = palabras[j]
            w = texto[a:b]
            if programa == "mysql":
                if w.startswith("-p") and len(w) > 2:
                    _tapar(texto, a + 2, b, cambios, False)
                elif w.startswith("--password="):
                    _tapar(texto, a + 11, b, cambios, False)
            elif w in ("-u", "-U", "--user", "--proxy-user"):
                if j + 1 < len(palabras):
                    j += 1
                    _tapar(texto, palabras[j][0], palabras[j][1], cambios, True)
            elif w.startswith(("--user=", "--proxy-user=")):
                _tapar(texto, a + w.index("=") + 1, b, cambios, True)
            elif w.startswith("-") and not w.startswith("--"):
                for i in range(1, len(w)):
                    if w[i] in "uU":
                        if i + 1 < len(w):
                            _tapar(texto, a + i + 1, b, cambios, True)
                        elif j + 1 < len(palabras):
                            j += 1
                            _tapar(texto, palabras[j][0], palabras[j][1], cambios, True)
                        break
                    if w[i] not in _CURL_SIN_ARGUMENTO:
                        break
            j += 1
        k = j


def _redactar_argumentos(texto):
    cambios, palabras = [], []
    for m in _PALABRA_RE.finditer(texto):
        if m.group() in ("|", ";", "&", "\n"):
            _redactar_comando(texto, palabras, cambios)
            palabras = []
        else:
            palabras.append(m.span())
    _redactar_comando(texto, palabras, cambios)
    partes, cursor = [], 0
    for inicio, fin in cambios:
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
