#!/usr/bin/env python3
"""
redact.py — redacción DETERMINISTA de secretos evidentes (agent-kits/shared).

Extraído de `journal.py:redactar` (session-end-durable-capture T-02, CA-11): fuente ÚNICA de
`redactar` y sus constantes (`REDACTADO`, `_SECRETOS_RE`). Antes de que la prosa del usuario toque
el LOG CRUDO (`journal.py capture`) o la entrada del journal (que SE VERSIONA), se sustituyen los
secretos evidentes: claves de API con prefijo conocido, JWT, bloques PEM, `Bearer`, y
`clave|token|password… = valor` con valor de ≥ 8 caracteres que mezcla letras y dígitos/símbolos.
Alta precisión antes que cobertura: «tokens por hora (479326)» o «password reset flow» no se tocan.

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
_ASIGNACION_RE = re.compile(r"(?i)\b(?:" + _CLAVES_SENSIBLES + r")\b\s*[:=]\s*[\"']?")
_ASIGNACION_FIN_RE = re.compile(r"[\s\"']")
_ASIGNACION_LETRA_RE = re.compile(r"[A-Za-z]", re.I)
_ASIGNACION_VARIADA_RE = re.compile(r"[0-9!@#$%^&*]")
_SECRETOS_RE = (
    re.compile(r"\b(?:sk-ant-|sk-|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|xox[baprs]-|glpat-|AKIA|ASIA)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(?P<pre>\bbearer\s+)(?P<sec>[A-Za-z0-9._~+/=\-]{20,})"),
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


def es_clave_sensible(clave):
    """True si `clave` es EXACTAMENTE una clave sensible (`password`, `api_key`, `token`…, sin
    distinguir mayusculas): `redactar_estructura` del recorder redacta entonces su valor textual."""
    return isinstance(clave, str) and _CLAVE_SENSIBLE_RE.fullmatch(clave) is not None


def redactar(texto):
    """Sustituye los secretos evidentes (_SECRETOS_RE) por REDACTADO conservando el prefijo (`token=`, `Bearer `)."""
    texto = _redactar_pem(str(texto))
    for pat in _SECRETOS_RE[:-1]:
        texto = pat.sub(lambda m: (m.group("pre") if "pre" in m.groupdict() else "") + REDACTADO, texto)
    texto = _redactar_asignaciones(texto)
    texto = _SECRETOS_RE[-1].sub(lambda m: m.group("pre") + REDACTADO, texto)
    return texto
# --8<-- fin redact (redactar + constantes)
