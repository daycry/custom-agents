#!/usr/bin/env python3
"""{{nombre}} — hook INFORMATIVO: lee el evento por stdin, avisa por `systemMessage` y sale siempre con 0.

Un hook informativo no decide ni bloquea: si falla o falta algo, calla. Para impedir una acción
(deny) hace falta un hook de guardia con su propia suite de pruebas; no lo escribas con esta plantilla.
Contrato de entrada y salida: la documentación de hooks de tu runtime (ver references/claude-code-contracts.md).
"""
import json
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer o imprimir.
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure (capturas, pythonw): se sigue


# Controles, secuencias ANSI, separadores Unicode y marcas bidi: falsean una línea que lee el usuario.
_CONTROLES = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]")


def _limpio(texto, tope=200):
    return _CONTROLES.sub(" ", str(texto))[:tope]


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — entrada ilegible: silencio, nunca un traceback
        return 0
    entrada = evento.get("tool_input") if isinstance(evento, dict) else None
    ruta = entrada.get("file_path") if isinstance(entrada, dict) else None   # `tool_input` puede no ser un objeto
    if isinstance(ruta, str) and ruta:
        print(json.dumps({"systemMessage": f"{{nombre}}: se modificó {_limpio(ruta)}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
