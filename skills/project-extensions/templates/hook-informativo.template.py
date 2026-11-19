#!/usr/bin/env python3
"""{{nombre}} — hook INFORMATIVO: lee el evento por stdin, avisa por `systemMessage` y sale siempre con 0.

Un hook informativo no decide ni bloquea: si falla o falta algo, calla. Para impedir una acción
(deny) hace falta un hook de guardia con su propia suite de pruebas; no lo escribas con esta plantilla.
Contrato de entrada y salida: la documentación de hooks de tu runtime (ver references/claude-code-contracts.md).
"""
import json
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer o imprimir.
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure (capturas, pythonw): se sigue


def main():
    try:
        evento = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — entrada ilegible: silencio, nunca un traceback
        return 0
    ruta = (evento.get("tool_input") or {}).get("file_path") if isinstance(evento, dict) else None
    if ruta:
        print(json.dumps({"systemMessage": f"{{nombre}}: se modificó {ruta}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
