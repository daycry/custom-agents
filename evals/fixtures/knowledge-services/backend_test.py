"""
backend_test.py — adaptador `type: "test"` de fixture (knowledge-services T-07, CA-12). Demuestra
que añadir un backend nuevo es UN fichero nuevo (aquí, fuera del árbol real del plugin) sin tocar
`knowledge-sync.py` ni `backends/__init__.py`. Implementa el contrato completo de forma trivial,
sin red ni disco fuera de lo que el propio `cfg` le indique.

`cfg` admite, para que los tests lo controlen sin variables de entorno:
  "estado_salud"   -> el `estado` que devuelve `health()` (default "sano")
  "forzar_error_apply" -> si es verdadero, `apply()` levanta `RuntimeError` (para probar que un
                          error de `apply` no borra la publicación anterior ni tumba el CLI)
  "forzar_error_health" -> si es verdadero, `health()` levanta `RuntimeError` (gap 90: probar que
                          `knowledge-sync.py --check` no revienta con un traceback)
  "forzar_error_plan"   -> si es verdadero, `plan()` levanta `RuntimeError` (gap 90, idem para el
                          camino de publicación real y `--dry-run`)
  "desfase"        -> lista que `verify()` devuelve tal cual en `desfase` (default vacía)
"""


def health(cfg):
    if (cfg or {}).get("forzar_error_health"):
        raise RuntimeError("fallo forzado por el test (forzar_error_health)")
    return {"estado": (cfg or {}).get("estado_salud", "sano"), "detalle": "fixture de tests"}


def plan(entries, cfg):
    if (cfg or {}).get("forzar_error_plan"):
        raise RuntimeError("fallo forzado por el test (forzar_error_plan)")
    return [{"accion": "upsert", "id": e.get("id"), "modo": e.get("modo")} for e in entries]


def apply(ops, cfg):
    if (cfg or {}).get("forzar_error_apply"):
        raise RuntimeError("fallo forzado por el test (forzar_error_apply)")
    return {"aplicados": len(ops)}


def verify(cfg):
    desfase = list((cfg or {}).get("desfase") or [])
    return {"ok": not desfase, "desfase": desfase}


def rebuild(entries, cfg):
    return {"reconstruidos": len(entries)}


def revoke(knowledge_id, cfg):
    return {"revocado": knowledge_id}
