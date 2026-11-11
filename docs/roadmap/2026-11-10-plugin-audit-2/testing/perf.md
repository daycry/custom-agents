# Rendimiento medido — plugin-audit-2

Medidas de las tareas de rendimiento. El implementer no puede escribir en `testing/` (guardarraíl del rol), así que las registró en el ledger ([tasks.md](../tasks.md)). Este fichero las recoge. La fuente de cada cifra es la evidencia de la tarea citada.

## T-23 — CI en paralelo

Entorno: Linux `python:3.11-slim`, un contenedor con `-m 1g` y 4 CPU, árbol de `git archive` en LF. Las dos formas ejecutan los mismos 11.190 tests.

| Paso | CI anterior | CI nueva |
|---|---|---|
| Ficheros `tests/test_*.py` ejecutados como script | 163 s (160 de 163 repetían lo que ya recoge pytest) | 9 s (solo los 3 sin `def test`) |
| pytest | 1.340 s en serie | 615 s con `-n auto -m "not serie"` (734 s con el anfitrión cargado) |
| Paso serie (tests de tiempo de pared o de lock) | — | 55 s |
| **Total** | **1.503 s** | **679 s (45 %)** |

El tope del paso en paralelo lo marca `test_task_brief::test_ca08…`, que tarda entre 131 y 166 s.

Después del ciclo de corrección 1 desapareció el bucle de scripts. Las suites mixtas se ejecutan con envoltorios `test_suite_legada_*` y las suites que son solo script, con `test_la_suite_script_pasa`. Medido en el anfitrión con carga:

- pytest en paralelo: 11.299 passed en 969 s;
- paso serie: 14 passed;
- envoltorios: 57 s de cola en total, dentro del paso en paralelo (45 s el de `test_lint_plugin`).

## T-07 — code-health sobre este repo

| Momento | Ficheros | Tiempo | Resultado |
|---|---|---|---|
| Antes | 7.644 (7.204 bajo `.pytest_cache`) | `leer()` 446,6 s; `lineas_codigo()` 64,3 s; `duplicados()` > 89 s sin terminar (perfil cortado a 600 s) | No termina |
| Exclusiones de carpetas ocultas, `worktrees/` y `site-packages/` | 439 | 37 s | `parcial: false` |
| Tope de 50 ocurrencias por ventana | 439 | 32 s | `parcial: true` (4 ventanas recortadas) |
| Ciclo de corrección 1 (`--max-pairs 0 --max-seconds 200`) | 439 | 76 s | 10.033 pares, por debajo del tope por defecto de 100.000 |

Memoria del emparejado con el fixture de 60 ficheros idénticos de 500 líneas: 75 MiB antes del tope total de pares; menos de 40 MiB después (`tracemalloc`).

Linux con 1 GiB: antes del tope por ventana, el test de rendimiento moría por falta de memoria (rc 137) con 120 ficheros idénticos.
