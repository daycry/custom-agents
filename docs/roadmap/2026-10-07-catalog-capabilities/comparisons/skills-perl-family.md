# Perl: patrones, seguridad y pruebas — S202–S204

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **36.729 bytes/1.485 líneas**, sin recursos locales.
[perl-family-reading-evidence.json](perl-family-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

`stack-practices` cubre PHP/CodeIgniter, Python y React. Como con Java (S145,
S147), .NET (S086) y Go (S116–S117), **no se abre especialidad Perl hasta que un
consumidor declare el stack**. Cuando ocurra, las tres piezas se leen juntas como
una sola referencia `perl.md`, y además:

- `skills/tdd/references/by-stack.md` gana una fila `prove -lv t/x.t` con la
  salida roja esperada (`not ok`, `Failed 1/N subtests`).
- `coverage-gate.py` de `unit-tests` necesita un analizador de Devel::Cover que
  salga con 2 si no encuentra la fila de totales (ver S204).

Lo transversal ya está en `backend-practices`
(`references/contracts-data.md`): allowlist de campos de ordenación, valores
parametrizados y errores sin detalles internos. El método TDD que repite S204 es
de `tdd`, y la auditoría de seguridad, de `nemesis` con `cybersecurity`.

## S202 — Patrones de Perl moderno

`11.591 bytes/505 líneas`. `use v5.36`, firmas, desreferencia postfija, `isa`,
Moo, `class` de 5.38, expresiones regulares con nombre, `open` de tres
argumentos, Path::Tiny, cpanfile con carton, perltidy y perlcritic.

| Ejemplo | Adaptación |
|---|---|
| «Acceso profundo seguro»: `$config->{cache}{host}` devuelve `undef` «sin error» | La lectura autovivifica `$config->{cache}`: crea la clave intermedia. Comprobar con `exists` nivel a nivel o desactivar la autovivificación |
| Fila de la tabla «`builtin::true / false` → `use builtin 'true', 'false';`» | No hay patrón heredado que sustituir: las dos columnas son la misma API, experimental en 5.36 |
| `eval "require $module"` marcado como inyección y sustituido por Module::Runtime | Correcto; conservar |

## S203 — Seguridad en Perl

`13.856 bytes/504 líneas`. Modo taint, validación por allowlist, `system` en
forma de lista, DBI con placeholders, codificación de salida, CSRF, cabeceras y
políticas de seguridad de perlcritic.

| Ejemplo | Adaptación |
|---|---|
| `safe_match` corta un regex catastrófico con `alarm` | Con las señales diferidas que Perl usa por defecto, la señal se atiende entre operaciones del intérprete; una sola coincidencia de regex larga no se interrumpe a tiempo. Reescribir el patrón (la propia pieza muestra cuantificadores posesivos) o ejecutarlo en un proceso aparte con límite |
| `$app->secrets(['long-random-secret-rotated-regularly'])` | Secreto literal en el código; leerlo del entorno o de configuración fuera del repo |
| `safe_path` resuelve con `realpath` y compara el prefijo antes de abrir | Entre la comprobación y la apertura un enlace puede cambiar; la propia pieza trata TOCTOU en otra sección sin unirla a esta función |

## S204 — Pruebas en Perl

`11.282 bytes/476 líneas`. Test::More y Test2::V0, subtests, `dies`/`lives`,
`prove`, `.proverc`, Test::MockModule, Devel::Cover y SQLite en memoria.

| Ejemplo | Adaptación |
|---|---|
| Gate de CI: `cover -report text … \| perl -ne 'if (/Total.*?(\d+\.\d+)/) { exit 1 if $1 < 80 }'` | Toma el primer número de la fila de totales, que es la columna de sentencias, no el total. Si no hay fila de totales, sale con 0 y el gate pasa. El principio de `coverage-gate.py` («sin parseo, exit 2; nunca un % inventado») corrige ambos |
| `.proverc` con `-j4` por defecto | En paralelo, las fixtures compartidas (BD, ficheros fijos) se pisan; activarlo solo con aislamiento por test |
| «80 %+ de cobertura» como regla | Aquí el umbral es opt-in por proyecto (`dev.json` `tests.coberturaMinima`) |

**Destino:** ninguno hasta que un consumidor declare Perl. Entonces, la
referencia y las dos piezas de prueba descritas arriba.
