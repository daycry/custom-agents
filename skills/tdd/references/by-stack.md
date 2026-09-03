# Correr UN solo test rojo, por stack

Léelo al llegar al paso **RED** de `SKILL.md` si no sabes cómo ejecutar un único test en el proyecto.
Regla: el rojo se ve en **un** test (el de tu criterio), no en la suite. Detecta el stack por los ficheros
del repo (columna «señal»), no preguntes si es evidente.

| Stack | Señal en el repo | Un solo test | Salida esperada en RED |
|---|---|---|---|
| **pytest** (Python) | `pytest.ini` · `pyproject.toml [tool.pytest]` · `tests/test_*.py` | `python3 -m pytest -q "tests/test_x.py::test_criterio" -x` | `1 failed` con el `AssertionError` (o `NameError` de la función aún inexistente); NO `ImportError` del test |
| **unittest** (Python sin pytest) | `python -m unittest` en docs/CI | `python3 -m unittest tests.test_x.TestX.test_criterio -v` | `FAILED (failures=1)` |
| **jest** (JS/TS) | `jest.config.*` · `"jest"` en `package.json` | `npx jest tests/x.test.ts -t "criterio" --runTestsByPath` | `1 failed` · `Expected … Received …` |
| **vitest** | `vitest.config.*` · `"vitest"` en devDependencies | `npx vitest run tests/x.test.ts -t "criterio"` | `1 failed` · `AssertionError` |
| **mocha** | `.mocharc.*` | `npx mocha test/x.spec.js --grep "criterio"` | `1 failing` |
| **phpunit** (PHP) | `phpunit.xml(.dist)` | `vendor/bin/phpunit --filter 'testCriterio' tests/XTest.php` | `FAILURES! Tests: 1, Failures: 1` |
| **pest** (PHP) | `tests/Pest.php` | `vendor/bin/pest --filter 'criterio'` | `FAILED … 1 failed` |
| **go test** | `go.mod` · `*_test.go` | `go test ./paquete -run '^TestCriterio$' -v` | `--- FAIL: TestCriterio` · `FAIL` |
| **cargo** (Rust) | `Cargo.toml` | `cargo test criterio -- --exact --nocapture` | `test criterio ... FAILED` · `1 failed` |
| **dotnet** (C#) | `*.csproj` · `*.sln` | `dotnet test --filter "FullyQualifiedName~Criterio"` | `Failed! - Failed: 1` |
| **JUnit/Gradle** (Java/Kotlin) | `build.gradle(.kts)` | `./gradlew test --tests 'paquete.XTest.criterio'` | `FAILED` · `1 test completed, 1 failed` |
| **JUnit/Maven** | `pom.xml` | `mvn -q -Dtest=XTest#criterio test` | `Tests run: 1, Failures: 1` |
| **rspec** (Ruby) | `.rspec` · `spec/` | `bundle exec rspec spec/x_spec.rb:LINEA` | `1 example, 1 failure` |
| **Playwright E2E** | `playwright.config.*` | `npx playwright test tests/x.spec.ts -g "criterio"` | `1 failed` — pero ojo: E2E es territorio de `qa`; el rojo TDD suele ser unitario |
| **bash** (scripts del plugin) | `hooks/*.sh` · `tests/test_hooks_shell.py` | `python3 -m pytest -q tests/test_hooks_shell.py -k criterio` (pytest lanza el `.sh`) | `1 failed` |

## Qué mirar en la salida (rojo válido vs rojo inválido)

| Ves… | Es… | Qué hacer |
|---|---|---|
| `AssertionError: expected X, got Y` / `Expected … Received …` | **Rojo válido**: falla por el criterio | Registra `RED: …` y pasa a GREEN |
| `NameError` / `AttributeError` / `undefined is not a function` sobre la función NUEVA | **Rojo válido**: la funcionalidad no existe todavía | Registra `RED: …` (resume el error) |
| `ImportError` / `ModuleNotFoundError` / `Cannot find module` del **test** | Rojo por la razón equivocada | Arregla el import del test; vuelve a correr |
| `SyntaxError` en el test · fixture no encontrada · `0 tests collected` | El test no se ejecutó | Arregla el test hasta que corra y falle por el assert |
| `passed` a la primera | No hay rojo | O el criterio ya estaba cubierto (dilo; no cuenta como TDD) o el test no prueba lo que crees: rómpelo a propósito hasta verlo fallar |

## Formato de la línea en el ledger

```
RED: tests/test_model_tier.py::test_override_parcial_solo_effort falló con AssertionError: ('opus','inherit') != ('opus','xhigh') · 2026-09-03
```

Un `RED:` por criterio, dentro de la tarea (`### T-XX`), antes o junto al campo `Verificación`. Fecha en
`AAAA-MM-DD`. Si el subagente lo devuelve en su informe, el orquestador lo copia tal cual.
