"""panel-redesign T-42 fix3 (gap 3-1, CWE-532): no-regression corpus of the argument redactor.

fix2 anchored `curl -u` / `mysql -p` credentials to the program in command position and lost
secrets that fix1 (`96ae4f7`) covered: inside quotes (`sh -c "…"`, `ssh host '…'`), after a prose
apostrophe (`can't`), after `--` or a long option, and with an absolute path out of command
position. Guarantee: everything fix1 covered stays covered; fix2's additions on top; ante la duda,
tapar de más. Run: python -m pytest -q tests/test_redact_fix3.py
"""
import importlib.util
import itertools
import math
import os
import re
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "agent-kits" / "shared"
_spec = importlib.util.spec_from_file_location("redact_fix3", SHARED / "redact.py")
redact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redact)


def _respaldo_de_journal():
    """The replicated block of journal.py (backup without redact.py), executed on its own."""
    source = (SHARED / "journal.py").read_text(encoding="utf8")
    start = source.index("# --8<-- redact (redactar + constantes)")
    end = source.index("# --8<-- fin redact (redactar + constantes)", start)
    namespace = {"re": re}
    exec(compile(source[start:end], "journal_backup_fix3", "exec"), namespace)
    return namespace["redactar"]


# ---- generative corpus: credential forms x wrappers ------------------------------------------------
# (form with {p} for the program word, program, secret fragments that must disappear)
FORMAS = [
    ("{p} -u admin:S3cretPw1 https://x.test", "curl", ("S3cretPw1",)),
    ("{p} -su admin:S3cretPw2 https://x.test", "curl", ("S3cretPw2",)),
    ("{p} -sSu admin:S3cretPw3 https://x.test", "curl", ("S3cretPw3",)),
    ("{p} -U proxy:Pr0xyPw44 https://x.test", "curl", ("Pr0xyPw44",)),
    ("{p} --user admin:S3cretPw5 https://x.test", "curl", ("S3cretPw5",)),
    ("{p} --proxy-user proxy:Pr0xyPw66 https://x.test", "curl", ("Pr0xyPw66",)),
    ("{p} --user=admin:S3cretPw7 https://x.test", "curl", ("S3cretPw7",)),
    ("{p} -uroot -pS3cretPw8 appdb", "mysql", ("S3cretPw8",)),
    ('{p} -p"S3cret Pw9x" appdb', "mysql", ("S3cret", "Pw9x")),
    ("{p} --password=S3cretPw10 appdb", "mysql", ("S3cretPw10",)),
    ("{p} -h db -pS3cretPw11 appdb", "mysqldump", ("S3cretPw11",)),
    ("{p} -pS3cretPw12 -e 'select 1'", "mariadb", ("S3cretPw12",)),
]


def _dq(texto):
    """Body of a shell double-quoted string."""
    return texto.replace("\\", "\\\\").replace('"', '\\"')


# (name, builder, accepts forms with a double quote, accepts forms with a single quote)
ENVOLTORIOS = [
    ("plain", lambda c: c, True, True),
    ("sh -c double", lambda c: 'sh -c "%s"' % _dq(c), True, True),
    ("bash -c single", lambda c: "bash -c '%s'" % c, True, False),
    ("ssh single", lambda c: "ssh host '%s'" % c, True, False),
    ("ssh double", lambda c: 'ssh host "%s"' % _dq(c), True, True),
    ("docker exec sh -c", lambda c: 'docker exec db sh -c "%s"' % _dq(c), True, True),
    ("prose double", lambda c: 'He said "use %s"' % c, False, True),
    ("prose single", lambda c: "He said 'use %s' twice" % c, True, False),
    ("apostrophe", lambda c: "I can't connect: %s" % c, True, True),
    ("apostrophe after ;", lambda c: "the server doesn't answer; I ran %s" % c, True, True),
    ("apostrophe pair", lambda c: "it doesn't work with %s, isn't it" % c, True, False),
    ("sudo -u", lambda c: "sudo -u postgres %s" % c, True, True),
    ("sudo --preserve-env", lambda c: "sudo --preserve-env %s" % c, True, True),
    ("kubectl --", lambda c: "kubectl exec -it mysql-0 -- %s" % c, True, True),
    ("compose --", lambda c: "docker compose exec db -- %s" % c, True, True),
    ("timeout", lambda c: "timeout 10 %s" % c, True, True),
    ("env -i", lambda c: "env -i %s" % c, True, True),
    ("xargs", lambda c: "xargs %s" % c, True, True),
    ("VAR= nohup &", lambda c: "LANG=C nohup %s &" % c, True, True),
    ("$( )", lambda c: "echo $(%s)" % c, True, True),
    ("backticks", lambda c: "echo `%s`" % c, True, True),
    ("after pipe", lambda c: "cat urls | %s" % c, True, True),
    ("after &&", lambda c: "cd /tmp && %s" % c, True, True),
]
PROGRAMAS = ("name", "path")


def _casos():
    for (forma, programa, secretos), (nombre, envolver, admite_dq, admite_sq), ruta in itertools.product(
            FORMAS, ENVOLTORIOS, PROGRAMAS):
        if ('"' in forma and not admite_dq) or ("'" in forma and not admite_sq):
            continue
        palabra = programa if ruta == "name" else "/usr/bin/" + programa
        texto = envolver(forma.format(p=palabra))
        yield pytest.param(texto, secretos, id="%s|%s|%s" % (programa, nombre, ruta))


CASOS = list(_casos())


def test_corpus_is_large_enough():
    assert len(CASOS) >= 450, len(CASOS)


@pytest.mark.parametrize("texto,secretos", CASOS)
def test_generative_corpus_leaves_no_secret_in_clear(texto, secretos):
    salida = redact.redactar(texto)
    for secreto in secretos:
        assert secreto not in salida, (texto, salida)
    assert redact.REDACTADO in salida
    assert redact.redactar(salida) == salida  # idempotent


def test_generative_corpus_same_in_the_journal_backup():
    respaldo = _respaldo_de_journal()
    for caso in CASOS:
        texto = caso.values[0]
        assert respaldo(texto) == redact.redactar(texto), texto


# ---- the reviewer's probe (gap 3-1, intento 3): 23 cases copied, not imported -------------------
SONDA = [
    ('bash -c "mysql -uroot -pS3cretPw1 appdb"', 'S3cretPw1'),
    ("sh -c 'curl -u admin:S3cretPw1 https://x.test'", 'S3cretPw1'),
    ('docker exec db sh -c "mysql -uroot -pS3cretPw1 db"', 'S3cretPw1'),
    ("ssh host 'mysql -pS3cretPw1 db'", 'S3cretPw1'),
    ('kubectl exec -it mysql-0 -- mysql -uroot -pS3cretPw1', 'S3cretPw1'),
    ('docker compose exec db -- mysql -pS3cretPw1', 'S3cretPw1'),
    ('sudo -u postgres /usr/bin/mysql -pS3cretPw1', 'S3cretPw1'),
    ('timeout 10 /usr/bin/curl -u admin:S3cretPw1 https://x', 'S3cretPw1'),
    ('sudo --preserve-env mysql -pS3cretPw1', 'S3cretPw1'),
    ("it doesn't work with mysql -uroot -pS3cretPw1 appdb", 'S3cretPw1'),
    ("the server doesn't answer; I ran curl -u admin:S3cretPw1 https://x", 'S3cretPw1'),
    ('He said "use curl -u admin:S3cretPw1"', 'S3cretPw1'),
    ('password="Abc12345xyz" curl x', 'Abc12345xyz'),
    ('Authorization: Bearer abcdefghijklmnopqrstuvwxyz123', 'abcdefghijklmnopqrstuvwxyz123'),
    ('export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG', 'wJalrXUtnFEMI'),
    ('mysql -pS3c\\"ret appdb', 'S3c'),
    ("mysql -p$'S3c\'retPw1' db", 'S3c'),
    ('curl -u admin:S3cretPw1 \\n  https://x', 'S3cretPw1'),
    ('mysql <<EOF\n-- x\nEOF\nmysql -pS3cretPw1', 'S3cretPw1'),
    ('curl -u "admin:S3cret', 'S3cret'),
    ('-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----', 'abc'),
    ('xargs curl -u admin:S3cretPw1', 'S3cretPw1'),
    ('env -i /usr/bin/curl -u admin:S3cretPw1 x', 'S3cretPw1'),
]


def test_probe_has_23_cases():
    assert len(SONDA) == 23


@pytest.mark.parametrize("texto,secreto", SONDA)
def test_probe_of_the_review_leaves_no_secret_in_clear(texto, secreto):
    salida = redact.redactar(texto)
    assert secreto not in salida, salida
    assert redact.redactar(salida) == salida


# ---- explicit cases of the four causes --------------------------------------------------------------
@pytest.mark.parametrize("texto,secreto", [
    ('sh -c "curl -u admin:S3cretX1"', "S3cretX1"),
    ("ssh host 'mysql -pS3cretX2 db'", "S3cretX2"),
    ('docker exec db sh -c "mysql -uroot -pS3cretX3 db"', "S3cretX3"),
    ('He said "use curl -u admin:S3cretX4"', "S3cretX4"),
    ("I can't connect: mysql -u root -pS3cretX5 db", "S3cretX5"),
    ("the server doesn't answer; I ran curl -u admin:S3cretX6 https://x", "S3cretX6"),
    ("kubectl exec -it mysql-0 -- mysql -uroot -pS3cretX7", "S3cretX7"),
    ("docker compose exec db -- mysql -pS3cretX8", "S3cretX8"),
    ("sudo --preserve-env mysql -pS3cretX9", "S3cretX9"),
    ("sudo --preserve-env curl -u a:S3cretX10", "S3cretX10"),
    ("sudo -u postgres /usr/bin/mysql -pS3cretX11", "S3cretX11"),
    ("timeout 10 /usr/bin/curl -u admin:S3cretX12 https://x", "S3cretX12"),
    ("env -i /usr/bin/curl -u admin:S3cretX13 x", "S3cretX13"),
    ("xargs curl -u admin:S3cretX14", "S3cretX14"),
    ('sh -c "ssh h \\"mysql -p\'S3cret X15\' db\\""', "X15"),
    ("ssh h 'sh -c \"curl -u a:S3cretX16\"'", "S3cretX16"),
    ('docker exec db sh -c "mysql -p\\"S3cret X17\\" db"', "X17"),
])
def test_the_four_causes_of_the_leak_are_covered(texto, secreto):
    salida = redact.redactar(texto)
    assert secreto not in salida, salida
    assert redact.redactar(salida) == salida


@pytest.mark.parametrize("texto,secreto", [
    ('mysql "-pS3cretY1" db', "S3cretY1"),
    ("curl '-u' 'admin:S3cretY2' https://x", "S3cretY2"),
    ("curl ' -u admin:S3cretY3 ' https://x", "S3cretY3"),
    ("curl \\\n  -u admin:S3cretY4 https://x", "S3cretY4"),
    ("--password=S3cretY5 mysql", "S3cretY5"),        # `=` forms: program anywhere in the command, as fix1
    ("--user=admin:S3cretY6 -s curl", "S3cretY6"),
    ("curl -u -pS3cretY7 mysql -u -pS3cretY8", "S3cretY8"),
])
def test_quoted_options_continuations_and_equal_forms(texto, secreto):
    salida = redact.redactar(texto)
    assert secreto not in salida, salida
    assert redact.redactar(salida) == salida


# ---- what must stay intact ----------------------------------------------------------------------------
@pytest.mark.parametrize("limpio", [
    "cp -pr /var/lib/mysql /backup", "mkdir -pv /etc/mysql/conf.d", "docker run -p3306:3306 mysql:8",
    "docker run -u 1000:1000 img curl https://x.test", "ssh -p 22 host", "git log -p", "mkdir -p out",
    "pytest -p no:cacheprovider tests", "mysql -p appdb", "curl --user-agent \"Foo:bar\" https://x.test",
    "curl -A 'Foo:bar' https://x.test", "max_tokens=12345678a", "ls /opt/curl -u", "tar -cpf a.tar /srv/mysql",
    "curl -u admin https://x.test", "rsync -pu a:b c", "curl -o out:file https://x.test",
    "docker run --name mysql -p3306:3306 mysql:8", "service mysql restart", "cat /etc/mysql -p",
    # fix3 extras: volumes, image tags and URLs that name the program are not the program
    "docker run -v /data/mysql:/var/lib/mysql -p3306:3306 mysql:8",
    "docker run --hostname mysql -p3306:3306 img", "sh -c 'mkdir -p /etc/mysql'",
    "it's fine; we don't use mysql here", "He said \"ssh -p 22 host\"",
])
def test_paths_images_and_foreign_options_stay_intact(limpio):
    assert redact.redactar(limpio) == limpio


@pytest.mark.parametrize("texto,secreto", [
    ('password="Abc12345xyz" curl x', "Abc12345xyz"),
    ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123", "abcdefghijklmnopqrstuvwxyz123"),
    ("-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----", "abc"),
    ("export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG", "wJalrXUtnFEMI"),
    ("mysql <<EOF\n-- x\nEOF\nmysql -pS3cretPw1", "S3cretPw1"),
    ('curl -u "admin:S3cret', "S3cret"),
    ('mysql -pS3c\\"ret appdb', "S3c"),
    ("mysql -p$'S3c\\'retPw1' db", "S3c"),
])
def test_non_regression_list_of_intento_3(texto, secreto):
    salida = redact.redactar(texto)
    assert secreto not in salida, salida


# ---- linear cost and idempotence on pathological inputs (up to ~1 MB) ------------------------------
_B = "\\"
# Un generador por caso patológico: `generador(n)` devuelve la entrada de tamaño ~n (T-23 fix4: el tamaño se
# adapta por caso hasta superar el suelo de CPU, así que cada caso se genera a la medida).
_GENERADORES = [
    lambda n: "a&" * n, lambda n: "a" * n * 2, lambda n: '"' * n, lambda n: ('"' + _B) * n,
    lambda n: "x'" * n, lambda n: "curl -" + "v" * n * 2, lambda n: "curl -u " + "a" * n * 2,
    lambda n: "curl " * n, lambda n: ("sudo " * n) + "/a/mysql -pX", lambda n: ("A=1 " * n) + "mysql -pX",
    lambda n: "--x mysql " * n, lambda n: "/" * n * 2 + "mysql", lambda n: ("a&" * n) + " " + ("&a" * n),
    lambda n: "curl " + "-u a:b " * n, lambda n: '"' + ("a" + _B) * n, lambda n: ('"a" ' * n) + "x",
    lambda n: ("curl -" + "v" * 50 + " ") * (n // 25), lambda n: "sh -c \"" + "'a' " * n + "\"",
    lambda n: "ssh h '" + '"x" ' * n + "'", lambda n: "it's " * n + "mysql -pX",
    lambda n: ("curl \"-u a:" + _B + '"' + "x ") * (n // 5), lambda n: "'" + '"' * n,
    lambda n: "\"$(curl -u a:X)\" " * (3 * n // 10),
]


def _patologicos(n=100000):
    return [g(n) for g in _GENERADORES]


CRECIMIENTO = 16             # la entrada grande es ×16 la pequeña
# ALCANCE DE LA PUERTA (decisión del usuario, T-23 fix6): rechaza el coste CUADRÁTICO o peor (razón ≈ 16 con ×16), no
# distingue un n^1,5 (razón 4) de la carga ajena y NO lo cubre. Lineal ≈ 1. El umbral 6 deja ~3× de margen a cada lado.
RAZON_RELATIVA_MAX = 6.0     # razón (t_grande / t_pequeño) / CRECIMIENTO máxima de un caso «no cuadrático»
SUELO_CPU = 0.05 if os.name == "nt" else 0.02  # s de CPU del caso pequeño (el reloj de Windows tiene 15,6 ms de resolución: 0,05 s = ~3 ticks, bastan con el umbral 6 y la mediana; con 0,1 s la puerta tardaba 7 min;
#                                               en Linux 0,02 s: la puerta costaba ~9 s por caso con 0,05 s, T-23 fix5)
TOPE_CARACTERES = 1_000_000  # tope de tamaño del caso pequeño (el grande es ×16: ≤ 16 MB)
SUELO_DEMO = 0.03 if os.name == "nt" else 0.01   # suelo de las demostraciones de la propia puerta (funciones sintéticas)
MUESTRAS = 3                 # muestras (pares pequeño/grande) por ronda: se toma la MEDIANA de las razones
RONDAS = 2                   # la segunda ronda solo se toma si la primera dio rojo; la mediana es de TODAS las muestras
PAUSA_RONDAS = 1.0           # s entre rondas: una ráfaga de carga ajena no cubre las dos
TOPE_CPU_GRANDE = 10.0       # s: un caso grande que tarde (o prometa tardar) más se da por colgado (cuadrático o peor)
TOPE_CPU_CRECIMIENTO = 30.0  # s de CPU totales gastados en hallar el tamaño que supera el suelo


def _es_lineal(razon_relativa):
    """La puerta protege la ausencia de retroceso CATASTRÓFICO (cuadrático o peor), no el tiempo de pared ni un
    n^1,5. La razón es `(t_grande / t_pequeño) / CRECIMIENTO` de la MEDIANA de las muestras: lineal ≈ 1, n^1,5 ≈ 4
    (fuera de alcance) y cuadrático ≈ 16. Pasa si es ≤ 6."""
    return razon_relativa <= RAZON_RELATIVA_MAX


def _cpu(funcion, *args):
    inicio = time.process_time()
    salida = funcion(*args)
    return time.process_time() - inicio, salida


class SinSuelo(Exception):
    """El caso pequeño no superó el suelo de CPU dentro de los topes: no se puede medir una razón."""


# Una muestra por debajo de `esperado / VALIDA_DIV` no es una medida. En Windows el reloj de CPU es de 15,6 ms y
# bajo carga devuelve 0 para una llamada de 0,1 s (÷8); en Linux es de ns y solo un cero absurdo se descarta (÷64):
# con ÷8 una réplica cargada descartó TODAS las rondas de dos casos (T-23 fix5b).
VALIDA_DIV = 8 if os.name == "nt" else 64


def _validas(muestras, esperado):
    return [m for m in muestras if m >= esperado / VALIDA_DIV]


def _mediana(valores):
    ordenados = sorted(valores)
    medio = len(ordenados) // 2
    return ordenados[medio] if len(ordenados) % 2 else (ordenados[medio - 1] + ordenados[medio]) / 2


def _medir(funcion, generador, n0=1500, suelo=None, pausa=None, rondas=None):
    """Mide `funcion` con una entrada pequeña (tamaño adaptado hasta superar `SUELO_CPU`) y otra ×16.
    Devuelve `(razon_relativa, t_chico, t_grande, salida_grande)`; `razon_relativa` es `None` si se llegó al
    tope de tamaño sin superar el suelo (la función es inocua a ese tamaño: no hay razón que medir) y se
    lanza `SinSuelo` si el tope de CPU del crecimiento se agota antes. Un grande por encima de
    `TOPE_CPU_GRANDE` s devuelve una razón infinita (colgado).

    La razón es la MEDIANA de las razones de varias muestras (no el mínimo: una muestra pequeña anómala volvía rojo
    un lineal y una grande afortunada daba verde a un cuadrático, T-23 intento 6, gap 7). Antes de ejecutar la entrada
    grande se sonda una ×4: si su exponente promete pasar de `TOPE_CPU_GRANDE` s (cúbico o peor), se rechaza SIN
    ejecutarla (gap 15). Con dos muestras de acuerdo en una ronda no se toma la tercera: la mediana ya está decidida."""
    suelo = SUELO_CPU if suelo is None else suelo
    pausa = PAUSA_RONDAS if pausa is None else pausa
    rondas = RONDAS if rondas is None else rondas
    n, gastado = n0, 0.0
    while True:
        chico = generador(n)
        funcion(chico)                                        # calentamiento: cachés de regex y de intérprete
        t, _ = _cpu(funcion, chico)
        if t >= suelo:
            # el suelo se CONFIRMA con una segunda medida: un pico de carga no lo cruza (Windows con 6 bucles: el caso
            # pequeño «de 0,1 s» costaba 0,016 s en las muestras y la razón salía 3,9 para un caso lineal)
            t = min(t, _cpu(funcion, chico)[0])
        gastado += t
        if t >= suelo:
            break
        if len(chico) * 2 > TOPE_CARACTERES:
            return None, t, None, None
        if gastado >= TOPE_CPU_CRECIMIENTO:
            raise SinSuelo(f"el caso pequeño no supera {suelo} s de CPU tras gastar {gastado:.1f} s")
        n *= 2
    # sonda ×4: el exponente medido extrapola el coste del ×16 sin ejecutarlo
    tm, _ = _cpu(funcion, generador(n * 4))
    if tm > 0 and t > 0 and tm > t:
        exponente = math.log(tm / t) / math.log(4)
        if tm * 4 ** exponente > TOPE_CPU_GRANDE:
            return float("inf"), t, tm * 4 ** exponente, None
    grande = generador(n * CRECIMIENTO)
    razones, tcs, tgs, salida = [], [], [], None
    for ronda in range(rondas):
        if ronda:
            time.sleep(pausa)
        tomadas = 0
        while tomadas < MUESTRAS:
            tc = _cpu(funcion, chico)[0]
            tg, salida = _cpu(funcion, grande)
            if tg > TOPE_CPU_GRANDE:
                return float("inf"), tc, tg, salida
            tomadas += 1
            if tc >= suelo / VALIDA_DIV and tg >= CRECIMIENTO * suelo / VALIDA_DIV:
                razones.append((tg / tc) / CRECIMIENTO)
                tcs.append(tc)
                tgs.append(tg)
            if tomadas == 2 and len(razones) >= 2 and _es_lineal(razones[-1]) == _es_lineal(razones[-2]):
                break                  # dos de acuerdo: la mediana de tres ya cae de ese lado
        if razones and _es_lineal(_mediana(razones)):
            break                      # lo superlineal de verdad sale rojo en TODAS las rondas: solo se repite el rojo
    if not razones:
        raise SinSuelo("ninguna ronda dio muestras de CPU válidas (el reloj devolvió tiempos muy por debajo de lo "
                       f"esperado): suelo={suelo} chico={t}")
    return _mediana(razones), _mediana(tcs), _mediana(tgs), salida


def test_el_criterio_de_linealidad_distingue_lineal_de_cuadratico():
    """Alcance (fix6, decisión del usuario): la puerta rechaza el coste CUADRÁTICO o peor. Un n^1,5 (razón 4 con
    ×16) queda FUERA de su alcance: la medida de CPU de una máquina compartida no separa 4 de 1 con garantías."""
    assert _es_lineal(1.0) and _es_lineal(1.8) and _es_lineal(3.0)   # lineal ≈ 1, con ruido
    assert _es_lineal(4.0)                        # n^1,5: fuera de alcance (documentado)
    assert not _es_lineal(8.0)                    # claramente superlineal
    assert not _es_lineal(16.0)                   # cuadrático
    assert not _es_lineal(float("inf"))           # colgado


def _lineal_de_verdad(entrada):
    acc = 0
    for _ in range(10):
        for c in entrada:
            acc += ord(c) ^ 3
    return acc


def _regex_cuadratica(entrada):
    return re.compile(r"x*y").search(entrada)               # retroceso: O(n²) sobre "xxxx…"


@pytest.mark.serie
def test_la_puerta_deja_pasar_una_funcion_lineal_real():
    relativa, tc, tg, _ = _medir(_lineal_de_verdad, lambda n: "x" * (n * 4), suelo=SUELO_DEMO)
    assert relativa is not None and _es_lineal(relativa), (relativa, tc, tg)


def _con_reloj_simulado(monkeypatch, segundos_por_longitud):
    """Sustituye el reloj de CPU de la puerta por un modelo determinista: el coste de `funcion(entrada)` es
    `segundos_por_longitud(len(entrada))`. Ejercita la LÓGICA de la puerta (crecimiento hasta el suelo, sonda ×4, mediana
    de las razones, umbral 6) sin depender de la carga de la máquina."""
    def falso(funcion, *args):
        return segundos_por_longitud(len(args[0])), args[0]
    monkeypatch.setattr(sys.modules[__name__], "_cpu", falso)


def test_la_puerta_separa_lineal_de_cuadratico_y_deja_fuera_el_n_a_la_1_5(monkeypatch):
    """La separación que importa: lineal ≈ 1 y cuadrático = 16 frente al umbral 6. El n^1,5 (razón 4) queda fuera de
    alcance por decisión del usuario (fix6): con el reloj real una razón 4 no se distingue de la carga ajena."""
    veredictos = {}
    for nombre, modelo in (("lineal", lambda n: 2e-6 * n), ("n^1,5", lambda n: 2e-8 * n ** 1.5),
                           ("cuadratico", lambda n: 1e-9 * n * n)):
        _con_reloj_simulado(monkeypatch, modelo)
        relativa, tc, tg, _ = _medir(lambda s: None, lambda n: "x" * n, suelo=0.02, pausa=0)
        veredictos[nombre] = (None if relativa is None else round(relativa, 2), _es_lineal(relativa))
    assert veredictos["lineal"][1] and abs(veredictos["lineal"][0] - 1.0) < 0.05, veredictos
    assert veredictos["n^1,5"][1] and abs(veredictos["n^1,5"][0] - 4.0) < 0.2, veredictos   # fuera de alcance
    assert not veredictos["cuadratico"][1] and abs(veredictos["cuadratico"][0] - 16.0) < 0.5, veredictos


@pytest.mark.serie
def test_la_puerta_rechaza_la_regex_cuadratica_que_antes_quedaba_bajo_el_suelo():
    """`re.compile(r"x*y").search("x"*N)` con N pequeño tardaba < 50 ms y la puerta anterior no comparaba
    razones (`tc=0.0000 tg=0.4062` pasaba): ahora el tamaño crece hasta superar el suelo y la razón sale ≈ 16.

    Fix7 (gap 15): la demostración con reloj real pasa por la MEDIANA de las muestras. Antes la resolvía siempre la sonda
    ×4 con un `inf` sacado de UNA sola muestra (5/5 en Windows) y la mediana nunca se ejercitaba: aquí el tope de un
    caso grande se sube (`tope`) para que el cuadrático dé muestras MEDIBLES, y se exige una razón FINITA."""
    relativa, tc, tg, _ = _medir(_regex_cuadratica, lambda n: "x" * n, n0=500, suelo=SUELO_DEMO, pausa=0,
                                 rondas=1, tope=TOPE_CPU_DEMO)
    assert relativa is not None and math.isfinite(relativa), (relativa, tc, tg)   # la mediana, no un `inf` de la sonda
    assert not _es_lineal(relativa), (relativa, tc, tg)
    # (sin `tc >= suelo/8`: `_medir` solo devuelve muestras de al menos ese valor, la aserción no podía fallar)
    assert tg > tc                                          # el grande cuesta de verdad más que el pequeño


def test_un_inf_de_la_sonda_x4_necesita_confirmacion_antes_del_rojo(monkeypatch):
    """Fix7 (gap 15): una sola medida ×4 inflada por la carga (aquí 10×, la primera) no vuelve rojo un caso lineal: la
    sonda promete `inf` y se confirma con una segunda muestra; si esa no lo confirma, el caso sigue por la mediana."""
    llamadas = {"x4": 0}
    modelo = lambda n: 2e-6 * n

    def falso(funcion, *args):
        n = len(args[0])
        t = modelo(n)
        if n == 48000:                                              # el caso ×4 del tamaño adaptado (12000 × 4)
            llamadas["x4"] += 1
            if llamadas["x4"] == 1:
                t *= 10
        return t, args[0]
    monkeypatch.setattr(sys.modules[__name__], "_cpu", falso)
    relativa, tc, tg, _ = _medir(lambda s: None, lambda n: "x" * n, n0=1500, suelo=0.02, pausa=0)
    assert llamadas["x4"] >= 2, llamadas                       # se confirmó con una segunda muestra ×4
    assert relativa is not None and _es_lineal(relativa), (relativa, tc, tg)


def test_el_cuadratico_sigue_siendo_rojo_con_la_confirmacion_de_la_sonda(monkeypatch):
    _con_reloj_simulado(monkeypatch, lambda n: 1e-9 * n * n * 40)          # cuadrático caro: la sonda promete > tope
    relativa, _tc, _tg, _ = _medir(lambda s: None, lambda n: "x" * n, n0=1500, suelo=0.02, pausa=0)
    assert not _es_lineal(relativa), relativa


def test_sin_suelo_alcanzado_no_se_aprueba_por_razon():
    """Una función inocua que no supera el suelo con el tope de tamaño devuelve `None` (no una razón
    inventada) y una que gasta el tope de CPU antes de llegar lanza `SinSuelo`."""
    llamadas = []
    relativa, t, grande, salida = _medir(lambda s: llamadas.append(len(s)), lambda n: "x" * n)
    assert relativa is None and grande is None and salida is None     # no se midió ningún caso grande
    assert max(llamadas) * 2 > TOPE_CARACTERES                        # y se llegó de verdad al tope de tamaño


@pytest.mark.serie
def test_una_muestra_de_cpu_a_cero_no_da_una_razon_disparatada(monkeypatch):
    """El reloj de CPU de Windows carga por ticks y bajo carga puede devolver 0 para una llamada de 0,1 s
    (visto: razón 5,6e7 en una pasada). Las muestras por debajo de 1/8 de lo esperado se descartan: una función
    lineal con las muestras pequeñas de la primera ronda a 0 sigue dando una razón ≈ 1."""
    real, llamadas = _cpu, [0]

    def falso(funcion, *args):
        t, salida = real(funcion, *args)
        if funcion is _lineal_de_verdad:
            llamadas[0] += 1
            if llamadas[0] == 3:                      # la primera muestra pequeña de la ronda 1 (1 y 2 = el suelo y su confirmación)
                return 0.0, salida
        return t, salida
    monkeypatch.setattr(sys.modules[__name__], "_cpu", falso)
    # suelo bajo: el caso supera el suelo a la primera (sin doblar) y el índice de llamadas es estable
    relativa, _tc, _tg, _ = _medir(_lineal_de_verdad, lambda n: "x" * (n * 10), suelo=0.01, pausa=0)
    # el objetivo es que el cero NO dispare la razón (antes 5,6e7); la linealidad fina la mide la puerta (con un suelo de 0,01 s, menor que un tick de Windows, el ruido bajo carga da razones de decenas)
    assert llamadas[0] >= 3 and relativa < 1000, (llamadas, relativa)   # el bug daba 5,6e7; <20 fallaba con 23 bajo carga


def test_las_muestras_invalidas_se_descartan():
    pequena = 0.1 / VALIDA_DIV / 2                      # por debajo del umbral de validez de la plataforma
    assert _validas([0.0, 0.2, pequena], 0.1) == [0.2]
    assert _validas([0.0, 0.0], 0.1) == []


def test_sin_suelo_por_tope_de_cpu_falla_con_motivo(monkeypatch):
    monkeypatch.setattr(sys.modules[__name__], "TOPE_CPU_CRECIMIENTO", 0.0)
    with pytest.raises(SinSuelo, match="no supera"):
        _medir(lambda s: len(s), lambda n: "x" * n)


# serie: mide tiempo de CPU; T-23 fix4 (autocalibrada con una referencia lineal y tamaño adaptativo)
@pytest.mark.serie
@pytest.mark.parametrize("k", range(23))
def test_linear_cost_on_pathological_inputs(k):
    generador = _GENERADORES[k]
    relativa, tc, tg, salida = _medir(redact.redactar, generador)
    if relativa is None:
        # inocuo incluso al tamaño tope: por construcción el caso pequeño (el tope, ~1 M de caracteres) no superó el
        # suelo, así que no hay razón que medir. La propiedad que SÍ puede fallar aquí es la idempotencia.
        tope = generador(TOPE_CARACTERES // 2)
        una = redact.redactar(tope)
        assert redact.redactar(una) == una, k
        return
    assert _es_lineal(relativa), (k, generador(40)[:40], round(relativa, 2), round(tc, 3), round(tg, 3))
    una = redact.redactar(generador(4000))                    # idempotencia sobre una salida pequeña: la del
    assert redact.redactar(una) == una, k                     # grande costaba otra pasada de redact sobre ×16


def test_quoted_prose_without_options_avoids_nested_command_scans(monkeypatch):
    """Apostrophes must not trigger command analysis for option-free quoted prose.

    Keep the trailing credential oracle: skipping the prose must still redact the real
    command, including the quote-blind pass that handles unmatched prose apostrophes.
    """
    original = redact._redactar_comando
    redundant = []

    def observe(texto, *args, **kwargs):
        if "-" not in texto:
            redundant.append(len(texto))
        return original(texto, *args, **kwargs)

    monkeypatch.setattr(redact, "_redactar_comando", observe)
    prose = "it's " * 200
    output = redact.redactar(prose + "mysql -pRegressionPw1")
    assert output == prose + "mysql -p" + redact.REDACTADO
    assert redact.redactar(output) == output
    assert not redundant, f"unnecessary command scans over option-free prose: {len(redundant)}"


def test_idempotent_on_the_whole_corpus():
    for texto in [c.values[0] for c in CASOS] + [t for t, _ in SONDA]:
        una = redact.redactar(texto)
        assert redact.redactar(una) == una, texto


# ---- fix4 (C4-1, B4-1, B4-2): prose apostrophe paired with the credential quote; option value naming
# the program ------------------------------------------------------------------------------------------
FIX4 = [
    # C4-1: an apostrophe of the prose closes on the same line as the quote that opens the credential
    ("I can't connect: mysql -u root -p'S3cretPw1' db", "S3cretPw1"),
    ("it doesn't work: curl -u 'admin:S3cretPw1' https://x", "S3cretPw1"),
    ("the server doesn't answer; I ran curl --user='admin:S3cretPw1' x", "S3cretPw1"),
    ("the users' table: curl -u 'admin:S3cretPw1' x", "S3cretPw1"),
    ("I can't connect: /usr/bin/mysql -u root -p'S3cretPw1' db", "S3cretPw1"),
    ("it doesn't work: /usr/bin/curl -u 'admin:S3cretPw1' https://x", "S3cretPw1"),
    ('he said "it fails: curl -u "admin:S3cretPw1" x', "S3cretPw1"),
    # B4-1: the value of an option that contains mysql/mariadb is not the program
    ("mysql -uroot -pRoot!mysql db", "Root!"),
    ("mysql -uroot -pS3cr3t@mysql db", "S3cr3t@"),
    ('mysql -uroot -p"S3cr3t@mysql" db', "S3cr3t@"),
    ("mariadb -pTopSecret=mariadb db", "TopSecret"),
    ("mysql -pApp#2024/mysql db", "App#2024"),
    ("mysql -uroot --password=mysql db", "--password=mysql"),
    ("/usr/bin/mysql -uroot -pRoot!mysql db", "Root!"),
    ("/usr/bin/mariadb -pTopSecret=mariadb db", "TopSecret"),
    ("/usr/bin/mysql -uroot --password=mysql db", "--password=mysql"),
]


@pytest.mark.parametrize("texto,secreto", FIX4)
def test_fix4_apostrophe_and_option_value_naming_the_program(texto, secreto):
    salida = redact.redactar(texto)
    assert secreto not in salida, salida


def test_fix4_slash_only_password_is_covered():
    salida = redact.redactar("mysql -uroot -p/mysql db")
    assert "-p/mysql" not in salida, salida


# B4-2: on fix3, `-p/mysql` was the program and the quoted word only named curl after a first pass
NO_IDEMPOTENTES_FIX3 = ['--user=a:b!curl -p/mysql " password=Abcd1234!mysql curl "']


@pytest.mark.parametrize("texto", [t for t, _ in FIX4] + ["mysql -uroot -p/mysql db"] + NO_IDEMPOTENTES_FIX3)
def test_fix4_idempotent(texto):
    una = redact.redactar(texto)
    assert redact.redactar(una) == una, una


@pytest.mark.parametrize("texto,secreto", FIX4)
def test_fix4_same_in_the_journal_backup(texto, secreto):
    assert secreto not in _respaldo_de_journal()(texto)


# ---- fix6 (gaps 7 y 15): mediana en lugar de mínimo, umbral 6 y tope de CPU antes de medir lo grande --------------
def test_la_mediana_resiste_una_muestra_pequena_atipica(monkeypatch):
    """Gap 7 (intento 6): con `min` de las muestras, UNA muestra pequeña anómala (reloj que se queda corto, 0,15× de lo
    esperado y aun así válida) volvía rojo un lineal. Con la mediana de las muestras de una ronda lo absorbe."""
    cuentas = {}

    def falso(funcion, *args):
        n = len(args[0])
        t = 2e-6 * n
        if n == 12000:                                  # el tamaño pequeño de esta función con suelo 0,02
            cuentas[n] = cuentas.get(n, 0) + 1
            if cuentas[n] % 3 == 0:
                t *= 0.15
        return t, args[0]
    monkeypatch.setattr(sys.modules[__name__], "_cpu", falso)
    relativa, _tc, _tg, _ = _medir(lambda s: None, lambda n: "x" * n, suelo=0.02, pausa=0)
    assert relativa is not None and _es_lineal(relativa), relativa


def test_un_coste_peor_que_cuadratico_se_rechaza_sin_ejecutar_el_caso_grande(monkeypatch):
    """Gap 15: el tope de CPU se aplica ANTES de medir la entrada grande, con una sonda ×4: un cúbico (o peor) que
    tardaría minutos no se ejecuta; devuelve razón infinita (colgado)."""
    largos = []

    def falso(funcion, *args):
        largos.append(len(args[0]))
        return 1e-13 * len(args[0]) ** 3, args[0]
    monkeypatch.setattr(sys.modules[__name__], "_cpu", falso)
    relativa, _tc, _tg, _ = _medir(lambda s: None, lambda n: "x" * n, suelo=0.02, pausa=0)
    assert relativa == float("inf") and not _es_lineal(relativa)
    assert 16 * 6000 not in largos, sorted(set(largos))     # el caso pequeño es 6000: nunca se ejecutó el ×16 (96000)


def test_el_umbral_es_6_y_la_demostracion_real_no_reintenta():
    """Decisión del usuario (fix6): umbral ~6 frente a la razón 16 del cuadrático; sin reintentos de la demostración
    (`INTENTOS_DEMO`): con la mediana y ese margen el reloj real basta."""
    assert 5 <= RAZON_RELATIVA_MAX <= 8
    assert "INTENTOS_DEMO" not in globals()
