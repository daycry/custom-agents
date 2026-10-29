"""panel-redesign T-42 fix3 (gap 3-1, CWE-532): no-regression corpus of the argument redactor.

fix2 anchored `curl -u` / `mysql -p` credentials to the program in command position and lost
secrets that fix1 (`96ae4f7`) covered: inside quotes (`sh -c "…"`, `ssh host '…'`), after a prose
apostrophe (`can't`), after `--` or a long option, and with an absolute path out of command
position. Guarantee: everything fix1 covered stays covered; fix2's additions on top; ante la duda,
tapar de más. Run: python -m pytest -q tests/test_redact_fix3.py
"""
import importlib.util
import itertools
import os
import re
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
def _patologicos():
    b, n = "\\", 100000
    return [
        "a&" * n, "a" * n * 2, '"' * n, ('"' + b) * n, "x'" * n, "curl -" + "v" * n * 2,
        "curl -u " + "a" * n * 2, "curl " * n, ("sudo " * n) + "/a/mysql -pX", ("A=1 " * n) + "mysql -pX",
        "--x mysql " * n, "/" * n * 2 + "mysql", ("a&" * n) + " " + ("&a" * n), "curl " + "-u a:b " * n,
        '"' + ("a" + b) * n, ('"a" ' * n) + "x", ("curl -" + "v" * 50 + " ") * 4000,
        "sh -c \"" + "'a' " * n + "\"", "ssh h '" + '"x" ' * n + "'", "it's " * n + "mysql -pX",
        ("curl \"-u a:" + b + '"' + "x " ) * 20000, "'" + '"' * n, "\"$(curl -u a:X)\" " * 30000,
    ]


def test_linear_cost_on_pathological_inputs():
    for texto in _patologicos():
        started = time.perf_counter()
        salida = redact.redactar(texto)
        assert time.perf_counter() - started < 1.5, (len(texto), texto[:40])
        assert redact.redactar(salida) == salida, texto[:40]


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
