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
_SECRETOS_RE = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\b(?:sk-ant-|sk-|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|xox[baprs]-|glpat-|AKIA|ASIA)[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(?P<pre>\bbearer\s+)(?P<sec>[A-Za-z0-9._~+/=\-]{20,})"),
    re.compile(r"(?i)(?P<pre>\b(?:api[_-]?key|secret[_-]?key|access[_-]?key|secret|token|passw(?:or)?d|pwd|clave|contrase[ñn]a)\b\s*[:=]\s*[\"']?)"
               r"(?P<sec>(?=[^\s\"']*[A-Za-z])(?=[^\s\"']*[0-9!@#$%^&*])[^\s\"']{8,})"),
)


def redactar(texto):
    """Sustituye los secretos evidentes (_SECRETOS_RE) por REDACTADO conservando el prefijo (`token=`, `Bearer `)."""
    texto = str(texto)
    for pat in _SECRETOS_RE:
        texto = pat.sub(lambda m: (m.group("pre") if "pre" in m.groupdict() else "") + REDACTADO, texto)
    return texto
# --8<-- fin redact (redactar + constantes)
