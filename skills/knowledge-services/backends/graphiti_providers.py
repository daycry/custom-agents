#!/usr/bin/env python3
"""
graphiti_providers.py — funciones de proveedor para el adaptador `graphiti.py` (ADR-018, T-04).

Decision de diseno (plan ambiguo, elegida por el implementer y documentada aqui y en el ledger,
T-04): la extraccion de entidades la hace el SERVIDOR Graphiti (su propio `config.yaml`, fuera de
este repo); estas funciones NO llaman a ningun modelo por su cuenta -evita duplicar llamadas y
manejo de credenciales que el servidor ya hace-. Lo que varia por `provider.llm` es que
parametros de `add_memory` se rellenan (p. ej. `custom_extraction_instructions` citando el modelo
configurado) para orientar esa extraccion server-side; `none` no anade ninguna instruccion y deja
que el episodio viaje tal cual (source ya decidido por el llamador).

Cada proveedor comparte la MISMA firma `(config, episodio) -> episodio_estructurado` (design.md,
enmienda 2026-09-17): anadir un proveedor nuevo es una funcion nueva aqui, sin tocar `graphiti.py`.
`config` es el sub-objeto `provider` de la config del backend (`{"llm", "model", "base_url",
"embedder", "embedder_model", "api_key_env"}`); ninguna funcion lee una credencial literal, solo
el NOMBRE de la variable de entorno (`api_key_env`) si algun proveedor futuro la necesitara.

Uso: importado por `graphiti.py` (`resolver_proveedor(nombre)`), nunca ejecutado como script.
Exit: N/A (modulo de libreria, sin CLI propia)
"""
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)


def proveedor_none(config, episodio):
    """`none`: no llama a ningun modelo ni anade instrucciones de extraccion (util para CI o
    proyectos sin modelo local); el episodio viaja tal cual lo construyo `graphiti.py`."""
    return dict(episodio)


def _con_instrucciones_de_extraccion(config, episodio, nombre_proveedor, modelo_por_defecto):
    """Comun a los proveedores que SI orientan la extraccion server-side: fija `source: "text"`
    (el cuerpo es markdown, no JSON ya estructurado) y una `custom_extraction_instructions` que
    cita el modelo configurado, sin llamar a ningun API externo desde este proceso."""
    modelo = (config or {}).get("model") or modelo_por_defecto
    salida = dict(episodio)
    salida["source"] = "text"
    salida["custom_extraction_instructions"] = (
        f"Extrae entidades y relaciones relevantes del texto usando el modelo configurado "
        f"({nombre_proveedor}:{modelo}); respeta los tipos de entidad ya definidos en el "
        "servidor."
    )
    return salida


def proveedor_ollama(config, episodio):
    return _con_instrucciones_de_extraccion(config, episodio, "ollama", "qwen2.5:7b")


def proveedor_openai(config, episodio):
    return _con_instrucciones_de_extraccion(config, episodio, "openai", "gpt-4o-mini")


def proveedor_anthropic(config, episodio):
    return _con_instrucciones_de_extraccion(config, episodio, "anthropic", "claude-haiku")


PROVEEDORES = {
    "none": proveedor_none,
    "ollama": proveedor_ollama,
    "openai": proveedor_openai,
    "anthropic": proveedor_anthropic,
}


def resolver_proveedor(nombre):
    """Devuelve la funcion de proveedor para `nombre` (`provider.llm`); levanta `ValueError` con
    un mensaje claro si `nombre` no es uno de los cuatro validos (el esquema ya lo valida antes,
    esto es un segundo fail-closed dentro del propio adaptador)."""
    fn = PROVEEDORES.get(nombre)
    if fn is None:
        raise ValueError(
            f"provider.llm desconocido: {nombre!r} (validos: {sorted(PROVEEDORES)})")
    return fn
