"""Corpus de fix15 (T-06, plugin-audit-2, intento 15): git codificado dos veces o tras un envoltorio que el guardarrail no trataba.

Origen: las 9 sondas de la lente C (`lc15/ex2.py`), los 13 aciertos de su barrido `fz` (`fz15_hits.json`), y las formas de las lentes A, B y C sobre
`flock`, `nohup --`, `nice` (ventana `toks[:6]`), `chrt`, `taskset`, `doas`, `winpty`, `/usr/bin/time` y las abreviaturas de `env -S`. Escrito con
escapes ASCII para que el fichero no dependa de la codificacion.
"""
BS = chr(92)

_X = "$'" + BS + "x24" + BS + "x27" + BS + "x5cx67it" + BS + "x27 reset --hard'"          # nivel 1 -> $'\x67it' reset --hard
_O = "$'$" + BS + "'" + BS + "134x67it" + BS + "' reset --hard'"                          # igual con octal
_U = "$'" + BS + "u0024" + BS + "u0027" + BS + "u005cx67it" + BS + "u0027 reset --hard'"
_SW = "$'" + BS + "x24" + BS + "x27" + BS + "x5cx67it" + BS + "x27 switch main'"

# Git codificado DOS veces dentro de una lectura incompleta (un `case` fuera de la lista blanca) o directamente.
DOBLE15 = [
    "bash -c " + _X, "eval " + _X, "bash -c " + _O,
    'echo "$(time -p case x in *) bash -c ' + _X + ';; esac)"',
    'echo "$(time -p case x in *) eval ' + _X + ';; esac)"',
    'echo "$(time -p case x in *) sh -c ' + _O + ';; esac)"',
    'echo "$(coproc case x in x) bash -c ' + _U + ';; esac)"',
    'echo "$(! case x in *) eval ' + _X + ';; esac)"; true',
    'echo $(time -p case x in *) bash -c ' + _X + ';; esac)',
    'echo "$(time -p case x in *) bash -c ' + _SW + ';; esac)"',
    'cat <(time -p case x in *) eval ' + _U + ';; esac)',
    'echo "$(case esac in *) bash -c ' + _X + ';; esac)"',
]
_EV = "eval $'" + BS + "x24" + BS + "x27" + BS + "x5cx67it" + BS + "x27' reset --hard"
HITS15 = [
    "echo $(! case x in [x]) " + _EV + ";;&\nesac); true",
    "echo <(time -p case x in a|x) " + _EV + ";;\nesac); true",
    "echo $(coproc case x in a|x) " + _EV + ";& esac); true",
    "echo $(cat <<E\nE\ncase esac in x|esac) " + _EV + ";;& esac); true",
    "echo $(! case x in [x]) " + _EV + ";&\nesac); true",
    "echo $(cat <<E\nE\ntime -p case x in x) " + _EV + "\n;; esac)",
    "echo <(! case x in *) " + _EV + "\n;;\nesac); true",
    "echo <(time -p case x in x|esac) " + _EV + ";& esac)",
    'echo $(cat <<E\nE\n! case x in "x") ' + _EV + ";;& esac)",
    "echo $(! case x in *) " + _EV + ";;\nesac)",
    "echo $(coproc case x in x) " + _EV + ";; esac); true",
    "echo $(cat <<E\nE\ncoproc case x in x) " + _EV + ";;&\nesac); true",
    "echo <(case esac in *) " + _EV + "\n;; esac); true",
]


def codificado(n):
    """`git` codificado `n` veces con `\\x5c`: hacen falta `n` rondas de decodificacion para llegar a `\\x67it`."""
    return BS + "x5c" + "x5c" * (n - 1) + "x67it"


# (forma, binario que debe existir para que bash ejecute el git falso). Todas las formas ejecutan git con bash real.
ENVOLTORIOS15 = [
    ("flock F -c 'git reset --hard'", "flock"),
    ("flock -n F -c 'git reset --hard'", "flock"),
    ('flock F -c "GIT reset --hard"', "flock"),
    ("flock F --command 'git reset --hard'", "flock"),
    ("flock --command='git reset --hard' F", "flock"),
    ("flock -x F -c \"g''it switch main\"", "flock"),
    ("nohup -- git reset --hard", "nohup"),
    ("nohup -- GIT reset --hard", "nohup"),
    ("nohup -- bash -c 'git reset --hard'", "nohup"),
    ("nohup -- git switch main", "nohup"),
    ("nice -+5 -n 1 -n 1 -n 1 bash -c \"g''it reset --hard\"", "nice"),
    ("nice -+5 -n 1 -n 1 -n 1 -n 1 -n 1 bash -c \"g''it reset --hard\"", "nice"),
    ("nice -+5 nice nice nice nice nice bash -c \"g''it reset --hard\"", "nice"),
    ("nice -+5 nice nice nice nice nice nice nice nice nice nice nice sh -c 'GIT reset --hard'", "nice"),
    ("chrt 10 git reset --hard", "chrt"),
    ("chrt -f 10 git reset --hard", "chrt"),
    ("chrt -r 1 GIT reset --hard", "chrt"),
    ("chrt -o 0 git reset --hard", "chrt"),
    ("taskset 1 git reset --hard", "taskset"),
    ("taskset -c 0 git reset --hard", "taskset"),
    ("taskset 0x3 Git reset --hard", "taskset"),
    ("taskset --cpu-list 0,1 git reset --hard", "taskset"),
    ("doas git reset --hard", "doas"),
    ("doas -u root git reset --hard", "doas"),
    ("doas -- git reset --hard", "doas"),
    ("doas -n GIT reset --hard", "doas"),
    ("winpty git reset --hard", "winpty"),
    ("winpty -Xallow-non-tty git reset --hard", "winpty"),
    ("winpty -Xplain GIT reset --hard", "winpty"),
    ("/usr/bin/time git reset --hard", "/usr/bin/time"),
    ("/usr/bin/time -p git reset --hard", "/usr/bin/time"),
    ("/usr/bin/time -f %e git reset --hard", "/usr/bin/time"),
    ("/usr/bin/time -o /dev/null -a git reset --hard", "/usr/bin/time"),
    ("command time -f %e git reset --hard", "/usr/bin/time"),
    ("env --split 'git reset --hard'", "env"),
    ("env --s 'git reset --hard'", "env"),
    ("env --split='git reset --hard'", "env"),
    ("env --spli 'GIT reset --hard'", "env"),
    ("env --split-string 'git reset --hard'", "env"),
    ("su -c 'git reset --hard' root", "su"),
]
# Formas de cada envoltorio que se permiten (no deben ser un falso deny).
LEGITIMAS15 = [
    "flock F -c 'echo hola'", "flock -n F make", "flock F -c 'make test'", "nohup -- make", "nohup make &",
    "nice -n 5 make", "nice -+5 make", "nice -+5 echo ok", "chrt 10 make", "chrt -f 10 make", "taskset -c 0 make",
    "taskset 1 make", "doas make", "doas -u root make", "winpty python x.py", "/usr/bin/time -p make",
    "/usr/bin/time -f %e make", "time -p make", "env --split 'make test'", "env --s 'A=1 make'", "timeout 5 make",
    "git status", "nohup -- git status", "flock F -c 'git status'", "chrt 10 git status", "taskset -c 0 git log -1",
    "doas git status", "winpty git log --oneline -3", "/usr/bin/time -p git diff --stat", "env --split 'git status'",
]

# Lo que bash ejecuta como git y el guardarrail NO ve: LIMITE declarado (expansiones en la palabra de mando, xargs con el
# subcomando por stdin). Cada forma es (orden, clase).
LIMITE15 = [
    ("{git,} reset --hard", "llaves en la palabra de mando"),
    ("{g..g}it reset --hard", "secuencia de llaves en la palabra de mando"),
    ("x=; g${x}it reset --hard", "expansion de parametros en la palabra de mando"),
    ("g$()it reset --hard", "sustitucion de orden vacia en la palabra de mando"),
    ("x=; env -S 'g${x}it reset --hard'", "`${VAR}` dentro de `env -S`"),
    ("echo reset --hard | xargs git", "xargs con el subcomando por stdin"),
]
# Formas con globs o con NUL crudo, que dependen del runtime: solo se comprueba que el guardarrail las permite.
LIMITE15_SOLO_ALLOW = [
    ("./g[i]t reset --hard", "glob en la palabra de mando"),
    ("g" + chr(0) + "it reset --hard", "NUL crudo (bash lo ignora o no segun la version)"),
]

# Formas de ENVOLTORIOS15 que bash NO ejecuta como git en este arnes aun existiendo el binario (motivo declarado).
SIN_PARIDAD15 = {
    "su -c 'git reset --hard' root": "`su` reinicia el PATH y puede pedir contrasena: el git falso no se ve",
    "chrt 10 git reset --hard": "`chrt` sin politica usa SCHED_RR y necesita CAP_SYS_NICE (falla sin privilegios)",
    "chrt -r 1 GIT reset --hard": "`-r` es SCHED_RR y necesita CAP_SYS_NICE (falla sin privilegios)",
    "chrt -f 10 git reset --hard": "`-f` es SCHED_FIFO y necesita CAP_SYS_NICE (falla sin privilegios)",
}
SIN_PARIDAD15.update({o: "`coproc` lanza el `case` en segundo plano: el efecto no es observable de forma determinista"
                      for o in DOBLE15 + HITS15 if "coproc" in o})
SIN_PARIDAD15.update({o: "`<( )` no se ejecuta si el comando que lo recibe (`echo`) no lee el descriptor"
                      for o in DOBLE15 + HITS15 if o.startswith("echo <(")})
SIN_PARIDAD15.update({o: "`winpty` exige una terminal (stdin no es un tty en el arnes) y no lanza el programa"
                      for o, b in ENVOLTORIOS15 if b == "winpty"})
