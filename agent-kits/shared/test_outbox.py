#!/usr/bin/env python3
"""Tests de outbox.py (session-end-durable-capture T-01). Ejecutar:
python3 -m pytest -q agent-kits/shared/test_outbox.py

Cola atómica compartida (`agent-kits/shared/outbox.py`, ADR de la spec `session-end-durable-capture`):
`escribir` (idempotente por clave, tmp+rename), `reclamar` (outbox -> processing, exclusivo con dos
procesos), `completar` (-> done/ con manifiesto+hash), `dead_letter` (-> dead-letter/ con causa y
contador de intentos), `estado` (contadores por carpeta) y `purgar` (borrado explícito)."""
import importlib.util
import json
import os
import shutil
import stat
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "outbox.py")

spec = importlib.util.spec_from_file_location("outbox", SCRIPT)
outbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outbox)


# ------------------------------------------------------------------ escribir

def test_escribir_es_idempotente_por_clave(tmp_path):
    d = tmp_path / "cola"
    p1 = outbox.escribir(str(d), "ev1", {"a": 1})
    p2 = outbox.escribir(str(d), "ev1", {"a": 999})     # payload distinto, MISMA clave
    assert p1 == p2
    with open(p1, encoding="utf-8") as fh:
        assert json.load(fh) == {"a": 1}                # el primero manda; no se reescribe
    assert len([f for f in os.listdir(os.path.join(str(d), "outbox")) if f.endswith(".json")]) == 1


def test_escribir_no_deja_temporal_a_medias(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    nombres = os.listdir(os.path.join(str(d), "outbox"))
    assert nombres == ["ev1.json"]                      # ningún .tmp-* residual tras un write normal


def test_escribir_solo_stdlib_sin_red():
    src = open(SCRIPT, encoding="utf-8").read()
    for prohibido in ("import requests", "import urllib.request", "socket.connect", "import httpx"):
        assert prohibido not in src


# ------------------------------------------------------------------ reclamar

def test_reclamar_mueve_a_processing_y_devuelve_el_item(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    assert item is not None
    assert item["clave"] == "ev1" and item["payload"] == {"a": 1}
    assert os.path.isfile(item["path"])
    assert "processing" in item["path"].replace("\\", "/")
    assert not os.path.exists(os.path.join(str(d), "outbox", "ev1.json"))


def test_reclamar_sin_pendientes_devuelve_none(tmp_path):
    d = tmp_path / "cola"
    assert outbox.reclamar(str(d)) is None


def test_dos_reclamar_concurrentes_uno_gana_otro_none(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    with ThreadPoolExecutor(max_workers=2) as ex:
        futuros = [ex.submit(outbox.reclamar, str(d)) for _ in range(2)]
        resultados = [f.result() for f in futuros]
    ganadores = [r for r in resultados if r is not None]
    perdedores = [r for r in resultados if r is None]
    assert len(ganadores) == 1 and len(perdedores) == 1
    assert ganadores[0]["clave"] == "ev1"


# ------------------------------------------------------------------ completar / dead_letter

def test_completar_mueve_a_done_con_manifiesto_y_hash(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {"cierre": "materializado"})
    assert os.path.isfile(dst) and "done" in dst.replace("\\", "/")
    manifiesto = json.load(open(dst + ".manifest.json", encoding="utf-8"))
    assert manifiesto["cierre"] == "materializado"
    assert len(manifiesto["hash"]) == 64                # sha256 hexdigest


def test_dead_letter_mueve_con_causa_y_cuenta_intentos(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.dead_letter(item, "envelope venenoso: JSON inválido")
    assert os.path.isfile(dst) and "dead-letter" in dst.replace("\\", "/")
    causa = json.load(open(dst + ".causa.json", encoding="utf-8"))
    assert causa["causa"] == "envelope venenoso: JSON inválido"
    assert causa["intentos"] == 1


def test_dead_letter_no_bloquea_al_resto_de_la_cola(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "malo", {"x": 1})
    outbox.escribir(str(d), "bueno", {"x": 2})
    item1 = outbox.reclamar(str(d))
    outbox.dead_letter(item1, "corrupto")
    item2 = outbox.reclamar(str(d))
    assert item2 is not None
    assert outbox.completar(item2, {}) is not None


# ------------------------------------------------------------------ estado / purgar

def test_estado_cuenta_por_carpeta(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    outbox.escribir(str(d), "ev2", {"a": 2})
    item = outbox.reclamar(str(d))
    outbox.completar(item, {})
    st = outbox.estado(str(d))
    assert st["outbox"] == 1 and st["processing"] == 0 and st["done"] == 1 and st["dead-letter"] == 0
    assert st["durabilidad"] == "ok"


def test_estado_sin_cola_todo_cero(tmp_path):
    d = tmp_path / "no-existe"
    st = outbox.estado(str(d))
    assert st == {"outbox": 0, "processing": 0, "done": 0, "dead-letter": 0, "durabilidad": "ok", "permisos": "ok"}


def test_purgar_sin_confirmar_no_borra(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.purgar(str(d), confirmar=False) is False
    assert os.path.isdir(str(d))


def test_purgar_confirmado_borra_todo(tmp_path):
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.purgar(str(d), confirmar=True) is True
    assert not os.path.exists(str(d))


# ------------------------------------------------------------------ revisión intento 1 (gaps 1, 3, 9, 21, 22, 23)

def test_escribir_valida_clave_y_rechaza_escape(tmp_path):
    """Gap 23 (C4 · CWE-22): sin validar `clave`, `../../ESCAPE` crea fuera de la cola."""
    d = tmp_path / "cola"
    with pytest.raises(ValueError):
        outbox.escribir(str(d), "../../ESCAPE", {"a": 1})
    with pytest.raises(ValueError):
        outbox.escribir(str(d), "con espacios", {"a": 1})
    assert not os.path.exists(str(tmp_path / "ESCAPE.json"))


def test_reclamar_reencola_processing_huerfano_por_ttl(tmp_path):
    """Gap 1 (Critical): un item reclamado y nunca completado (corte, excepción) queda en
    `processing/` para siempre hoy; `reclamar` debe barrerlo tras `processing_ttl_s`."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    assert item is not None
    # simula que el item lleva más de la TTL en processing/ (proceso interrumpido)
    viejo = time.time() - 700
    os.utime(item["path"], (viejo, viejo))
    item2 = outbox.reclamar(str(d), processing_ttl_s=600)
    assert item2 is not None and item2["clave"] == "ev1"
    assert os.path.isfile(os.path.join(str(d), "processing", "ev1.json.intentos"))


def test_reclamar_huerfano_agota_intentos_y_va_a_dead_letter(tmp_path):
    """Gap 1/22: tras MAX_INTENTOS reencolados sin completar, el item va a dead-letter (no se
    pierde silenciosamente, y libera al resto de la cola)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    for _ in range(outbox.MAX_INTENTOS):
        item = outbox.reclamar(str(d), processing_ttl_s=0)
        assert item is not None
        viejo = time.time() - 1
        os.utime(item["path"], (viejo, viejo))
    # una reclamación más: ya alcanzó MAX_INTENTOS → dead-letter, no vuelve a outbox/processing
    assert outbox.reclamar(str(d), processing_ttl_s=0) is None
    st = outbox.estado(str(d))
    assert st["dead-letter"] == 1 and st["outbox"] == 0 and st["processing"] == 0
    causa = json.load(open(os.path.join(str(d), "dead-letter", "ev1.json.causa.json"), encoding="utf-8"))
    assert "reintentos agotados" in causa["causa"]


def test_escribir_no_deja_tmp_a_medias_tras_fallo_a_mitad(tmp_path, monkeypatch):
    """Gap 3 (CA-04): un corte a mitad de la escritura no debe dejar el destino a medias ni un
    `.tmp-*` que nadie limpie."""
    d = tmp_path / "cola"

    real_replace = os.replace

    def replace_que_falla(a, b):
        raise OSError("disco lleno simulado")

    monkeypatch.setattr(os, "replace", replace_que_falla)
    with pytest.raises(OSError):
        outbox.escribir(str(d), "ev1", {"a": 1})
    monkeypatch.setattr(os, "replace", real_replace)
    assert not os.path.exists(os.path.join(str(d), "outbox", "ev1.json"))
    restantes = [f for f in os.listdir(os.path.join(str(d), "outbox")) if ".tmp-" in f]
    assert restantes == []                              # el tmp se limpia aunque `os.replace` falle


def test_limpiar_tmp_huerfanos_borra_planted_y_respeta_ttl(tmp_path):
    """Gap 3/13/21: un `.tmp-<pid>` plantado en outbox/ (o dejado por un corte real) se ignora en
    listados y `replay`/`limpiar_tmp_huerfanos` lo borra al superar la TTL."""
    d = tmp_path / "cola"
    outbox_dir = d / "outbox"
    outbox_dir.mkdir(parents=True)
    plantado = outbox_dir / ".tmp-ev1-999.json"      # prefijo `.tmp-` AL INICIO (gap 35: no basta con "contener" .tmp-)
    plantado.write_text("{incompleto", encoding="utf-8")
    viejo = time.time() - 700
    os.utime(str(plantado), (viejo, viejo))
    assert outbox.reclamar(str(d)) is None              # el .tmp-* no es un candidato válido
    assert outbox.estado(str(d))["outbox"] == 0
    borrados = outbox.limpiar_tmp_huerfanos(str(d), ttl_s=600)
    assert borrados == 1 and not plantado.exists()


def test_purgar_antiguos_borra_done_pero_no_dead_letter(tmp_path):
    """Gap 22: `done/`/`dead-letter/` crecían para siempre; `purgar_antiguos` los acota (lo invoca
    `journal.py replay` sobre `done/`, nunca sobre `dead-letter/`). Gap 33: el filtro es
    `completado_en` del manifiesto, no el mtime del envelope (por eso aquí se reescribe el
    `completado_en` a viejo en vez de tocar solo el mtime del fichero)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "viejo", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {})
    viejo_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 40 * 86400))
    man = json.load(open(dst + ".manifest.json", encoding="utf-8"))
    man["completado_en"] = viejo_iso
    json.dump(man, open(dst + ".manifest.json", "w", encoding="utf-8"))
    borrados = outbox.purgar_antiguos(str(d), "done", dias=30)
    assert borrados == 1
    assert outbox.estado(str(d))["done"] == 0
    assert not os.path.exists(dst) and not os.path.exists(dst + ".manifest.json")


def test_purgar_antiguos_no_purga_sin_completado_en_ni_por_mtime_viejo(tmp_path):
    """Gap 33 (B6): un envelope que esperó 40 días en la outbox y se materializa HOY no debe
    borrarse en la misma pasada solo porque el fichero (heredado de `outbox/`) tenga mtime viejo;
    lo que manda es `completado_en` (hoy, recién escrito por `completar`)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "viejo-en-outbox", {"a": 1})
    p = os.path.join(str(d), "outbox", "viejo-en-outbox.json")
    viejo = time.time() - 40 * 86400
    os.utime(p, (viejo, viejo))                    # el envelope ES viejo (esperó en outbox/)
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {})               # pero se materializa AHORA
    borrados = outbox.purgar_antiguos(str(d), "done", dias=30)
    assert borrados == 0
    assert outbox.estado(str(d))["done"] == 1
    assert os.path.isfile(dst) and os.path.isfile(dst + ".manifest.json")


def test_purgar_antiguos_sin_manifiesto_o_sin_completado_en_no_purga(tmp_path):
    """Gap 33: sin `completado_en` legible, NO se purga (mejor conservar de más)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "sin-manifiesto", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.completar(item, {})
    viejo = time.time() - 40 * 86400
    os.remove(dst + ".manifest.json")               # manifiesto perdido/inexistente
    os.utime(dst, (viejo, viejo))
    assert outbox.purgar_antiguos(str(d), "done", dias=30) == 0
    assert os.path.isfile(dst)


def test_directorios_y_ficheros_de_la_cola_son_privados(tmp_path):
    """Gap 9 (B5/C1 · CWE-538/732): la cola no debe ser world-readable ni sembrarse en git status
    sin control."""
    d = tmp_path / "cola"
    p = outbox.escribir(str(d), "ev1", {"a": 1})
    assert stat.S_IMODE(os.stat(os.path.dirname(p)).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(p).st_mode) & 0o077 == 0


def test_dead_letter_no_fuga_el_handle_de_causa_json(tmp_path):
    """Gap 23 (B15): `dead_letter` abría `causa.json` sin cerrarlo (fuga de fd en Windows, donde un
    handle abierto bloquea el `os.replace` siguiente). Aquí se fuerza un segundo `dead_letter` de
    la MISMA clave (reencolando a mano) para que la lectura+reescritura de `causa.json` ocurra dos
    veces seguidas sin excepción ni fichero bloqueado."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.dead_letter(item, "primer intento")
    # reencola a mano la misma clave (simula un replay que recapturó y volvió a fallar)
    os.replace(dst, os.path.join(str(d), "outbox", "ev1.json"))
    item2 = outbox.reclamar(str(d))
    dst2 = outbox.dead_letter(item2, "segundo intento")
    with open(dst2 + ".causa.json", encoding="utf-8") as fh:
        assert json.load(fh)["intentos"] == 2


# ------------------------------------------------------------------ revisión intento 2 (gaps 25/26/31/33/40/43/46)

def test_reclamar_refresca_mtime_al_reclamar_no_al_crear(tmp_path):
    """Gap 25 (Critical): el TTL de huérfanos se medía sobre el mtime del envelope (creación), no
    sobre la reclamación. Un envelope que esperó 20 min en `outbox/` (el caso normal: `replay`
    horas después) se entregaba a DOS trabajadores: el segundo `reclamar()` volvía a verlo «viejo»
    en `processing/` nada más reclamarlo y lo re-encolaba mientras el primero seguía trabajando."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    p = os.path.join(str(d), "outbox", "ev1.json")
    viejo = time.time() - 20 * 60          # 20 minutos esperando en outbox/ (> processing_ttl_s=600)
    os.utime(p, (viejo, viejo))
    item = outbox.reclamar(str(d), processing_ttl_s=600)
    assert item is not None
    # un segundo `reclamar()` INMEDIATO no debe ver el item recién reclamado como huérfano
    assert outbox.reclamar(str(d), processing_ttl_s=600) is None
    assert outbox.estado(str(d))["processing"] == 1 and outbox.estado(str(d))["outbox"] == 0
    # ni siquiera 10s después (muy por debajo de la TTL desde la reclamación)
    reciente = time.time() - 10
    os.utime(item["path"], (reciente, reciente))
    assert outbox.reclamar(str(d), processing_ttl_s=600) is None
    assert outbox.estado(str(d))["processing"] == 1


def test_reencolar_con_backoff_no_se_reclama_hasta_pasado_el_no_antes_de(tmp_path):
    """Gap 26 (Critical): un fallo TRANSITORIO agotaba los 3 intentos en milisegundos (el bucle de
    `replay` reclamaba de inmediato el reencolado). Con backoff, el item reencolado no es
    reclamable hasta `no_antes_de`."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    resultado = outbox.reencolar_o_dead_letter(item, "fallo transitorio", intentos_max=3, backoff=True)
    assert resultado == outbox.REENCOLADO
    # el item sigue en outbox/ (no en dead-letter) pero no es reclamable todavía: backoff pendiente
    assert outbox.estado(str(d))["outbox"] == 1 and outbox.estado(str(d))["dead-letter"] == 0
    assert outbox.reclamar(str(d)) is None
    sidecar = outbox._leer_sidecar(os.path.join(str(d), "outbox", "ev1.json" + outbox.INTENTOS_SUFFIX))
    assert sidecar["intentos"] == 1 and sidecar["no_antes_de"] > time.time()


def test_reencolar_huerfano_sin_backoff_es_reclamable_de_inmediato(tmp_path):
    """Gap 26: la recuperación de huérfanos de `processing/` (worker muerto, no un fallo del
    código) NO debe llevar backoff — si lo llevara, `test_reclamar_huerfano_agota_intentos_...`
    tardaría minutos en converger y un worker muerto tardaría en recuperarse sin motivo."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    outbox.reencolar_o_dead_letter(item, "huérfano", backoff=False)
    assert outbox.reclamar(str(d)) is not None          # reclamable YA, sin esperar backoff


def test_replay_permanente_tres_pasadas_agota_intentos_y_dead_letter_recuperable(tmp_path, monkeypatch):
    """Gap 26: un fallo PERMANENTE necesita 3 PASADAS separadas (con tiempo simulado entre ellas,
    respetando el backoff) para llegar a dead-letter — no una sola pasada instantánea. Y
    `reintentar_dead_letter` lo recupera a `outbox/` con el contador a 0."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    reloj = [time.time()]
    monkeypatch.setattr(outbox.time, "time", lambda: reloj[0])
    for intento_esperado in (1, 2):
        item = outbox.reclamar(str(d))
        assert item is not None, f"debería poder reclamarse en la pasada {intento_esperado}"
        resultado = outbox.reencolar_o_dead_letter(item, "fallo permanente", intentos_max=3, backoff=True)
        assert resultado == outbox.REENCOLADO
        assert outbox.estado(str(d))["dead-letter"] == 0
        reloj[0] += outbox.BACKOFF_S * intento_esperado + 1      # avanza el reloj más allá del backoff
    item = outbox.reclamar(str(d))
    assert item is not None
    resultado = outbox.reencolar_o_dead_letter(item, "fallo permanente", intentos_max=3, backoff=True)
    assert resultado == outbox.DEAD_LETTER
    st = outbox.estado(str(d))
    assert st["dead-letter"] == 1 and st["outbox"] == 0
    causa = json.load(open(os.path.join(str(d), "dead-letter", "ev1.json.causa.json"), encoding="utf-8"))
    assert causa["intentos"] == 3                       # gap 43: el contador REAL, no 1
    recuperados = outbox.reintentar_dead_letter(str(d))
    assert recuperados == 1
    st2 = outbox.estado(str(d))
    assert st2["dead-letter"] == 0 and st2["outbox"] == 1
    sidecar = outbox._leer_sidecar(os.path.join(str(d), "outbox", "ev1.json" + outbox.INTENTOS_SUFFIX))
    assert sidecar["intentos"] == 0                      # contador a 0 tras el reintento manual


def test_reclamar_con_dead_letter_inutilizable_no_aborta_el_barrido(tmp_path):
    """Gap 31 (B4): el barrido de huérfanos de `processing/` no debe abortar `reclamar()` si
    `dead-letter/` es inutilizable (aquí, un fichero en vez de una carpeta)."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    outbox.escribir(str(d), "ev2", {"a": 2})
    item1 = outbox.reclamar(str(d))
    for _ in range(outbox.MAX_INTENTOS - 1):
        os.utime(item1["path"], (time.time() - 700, time.time() - 700))
        outbox.reclamar(str(d), processing_ttl_s=600)
        item1["path"] = os.path.join(str(d), "processing", "ev1.json")
    os.utime(item1["path"], (time.time() - 700, time.time() - 700))
    (d / "dead-letter").mkdir(parents=True, exist_ok=True)
    shutil.rmtree(str(d / "dead-letter"))
    (d / "dead-letter").write_text("no soy una carpeta", encoding="utf-8")
    # el siguiente reclamar() intentará mandar ev1 a dead-letter (agotó intentos) y fallará al
    # crear la carpeta; no debe lanzar, y ev2 (independiente) debe seguir siendo reclamable.
    errores = outbox._reclamar_huerfanos(str(d), 600)
    assert errores and errores[0]["clave"] == "ev1"
    item2 = outbox.reclamar(str(d))
    assert item2 is not None and item2["clave"] == "ev2"


def test_estado_durabilidad_degradada_cuando_fsync_falla(tmp_path, monkeypatch):
    """Gap 40: `durabilidad: degradada` no tenía un test que ejercitara la rama (mutante: fijar
    `"ok"` a fuego seguía en verde). Aquí se fuerza que `os.fsync` falle en la escritura."""
    d = tmp_path / "cola"

    def fsync_que_falla(_fd):
        raise OSError("fsync no soportado en este FS simulado")

    monkeypatch.setattr(os, "fsync", fsync_que_falla)
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.estado(str(d))["durabilidad"] == "degradada"


def test_estado_permisos_degradados_cuando_chmod_falla(tmp_path, monkeypatch):
    """Gap 46: un `chmod 0700/0600` que falla se tragaba sin ninguna señal (mutante: sin marcar
    nada, el test de arriba no lo detectaría)."""
    d = tmp_path / "cola"

    def chmod_que_falla(*a, **k):
        raise OSError("chmod no soportado en este FS simulado")

    monkeypatch.setattr(os, "chmod", chmod_que_falla)
    outbox.escribir(str(d), "ev1", {"a": 1})
    assert outbox.estado(str(d))["permisos"] == "degradados"


def test_dead_letter_propaga_el_intentos_real_no_uno_fijo(tmp_path):
    """Gap 43 (B9): `causa.json` declaraba `intentos: 1` tras 3 reintentos porque no leía el
    sidecar `.intentos`; aquí se fuerza `intentos=5` explícito (como haría `reencolar_o_dead_letter`
    tras agotar los reintentos) y se comprueba que NO se recalcula a 1."""
    d = tmp_path / "cola"
    outbox.escribir(str(d), "ev1", {"a": 1})
    item = outbox.reclamar(str(d))
    dst = outbox.dead_letter(item, "agotado", intentos=5)
    causa = json.load(open(dst + ".causa.json", encoding="utf-8"))
    assert causa["intentos"] == 5
