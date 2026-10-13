# Python: patrones y pruebas; PyTorch — S218–S220

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **47.666 bytes/1.965 líneas**, sin recursos locales.
[python-pytorch-reading-evidence.json](python-pytorch-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S218 — Patrones de Python

`16.914 bytes/751 líneas`. Tutorial general: legibilidad, EAFP, anotaciones de
tipo, excepciones encadenadas, context managers, comprensiones y generadores,
dataclasses, decoradores, concurrencia con hilos, procesos y asyncio, estructura
de paquete y `pyproject.toml`.

**Comparación.** Python es un stack declarado y su dueño es
`skills/stack-practices/references/python.md`, más denso y preciso: cancelación
y concurrencia acotada, validación en el borde, nada de E/S al importar,
limpieza en `finally`, y no capturar `Exception` para devolver éxito. Varios
ejemplos de la pieza incumplen esas reglas:

| Ejemplo | Adaptación |
|---|---|
| `fetch_all_urls` captura `Exception` y guarda `"Error: …"` como valor del resultado | Mezcla errores con datos; `python.md` ya lo prohíbe |
| `fetch_all` con `asyncio.gather` crea una sesión HTTP por URL y lanza todas a la vez | Sin límite de concurrencia (regla de `python.md`) y sin reutilizar la sesión del cliente |
| Context manager `timer` sin `try/finally` | Si el bloque falla, no mide ni limpia |
| «Usa una función generadora» y el ejemplo devuelve una lista | El texto y el código no coinciden |
| `pyproject` con `requires-python = ">=3.9"` y `select` en `[tool.ruff]` | 3.9 ya no tiene soporte; en Ruff actual la selección va en `[tool.ruff.lint]`. Fijar versiones por el proyecto |

**Destino:** ninguno; `python.md` ya cubre lo útil.

## S219 — Pruebas en Python

`18.955 bytes/817 líneas`. pytest: aserciones, fixtures y sus ámbitos,
parametrización, marcadores, `unittest.mock`, pruebas async, ficheros temporales,
organización, configuración y comandos.

**Comparación.** El método es de `tdd` (con la fila pytest en
`references/by-stack.md`), la medida de `unit-tests` y los criterios de pruebas
Python de `python.md` (fixtures con `yield`, ámbito acotado, `monkeypatch` sobre
la referencia que usa el módulo, `tmp_path`). La pieza no aporta nada que falte y
tiene ejemplos que fallan:

| Ejemplo | Adaptación |
|---|---|
| `@patch("mypackage.api_call")` y luego llama a `api_call()` del módulo de test | Se parchea un nombre y se llama a otro: el test no prueba el mock. Es el caso de «parchear donde se usa» de `python.md` |
| Ejemplo de `autospec`: solo usa `db_mock.return_value` y afirma `db_mock.assert_called_once()` | El mock nunca se llamó: la aserción falla siempre |
| Fixture `temp_file` que escribe `temp.txt` en el directorio actual | Escribe en el checkout; usar `tmp_path` |
| `db_session` con `begin_nested()` y el test llama a `commit()` | Con SQLAlchemy 2.x, `commit()` confirma la transacción externa y el `rollback()` del fixture no deshace nada; hay que unir la sesión a una transacción externa con savepoint |
| Fixture async con `@pytest.fixture` | En modo estricto de pytest-asyncio necesita su propio decorador |
| Test «de integración» contra `https://api.example.com` | Red real en la suite |
| «Rutas críticas: 100 % de cobertura» | El plugin no impone porcentajes; el umbral es opt-in (`tests.coberturaMinima`) |

**Destino:** ninguno. La fila de SQLAlchemy queda como candidata para
`python.md` si un consumidor declara esa librería.

## S220 — Patrones de PyTorch

`11.797 bytes/397 líneas`. Código agnóstico de dispositivo, semillas, formas de
tensores, módulos, bucles de entrenamiento y validación, `DataLoader`,
checkpoints, precisión mixta, checkpointing de gradientes y `torch.compile`.

**Comparación.** Ningún consumidor ha declarado un stack de aprendizaje
automático; como con el cómputo GPU de S142, **no se abre especialidad**.
Correcciones para entonces:

| Ejemplo | Adaptación |
|---|---|
| El módulo de ejemplo «bueno» usa `nn.ReLU(inplace=True)`; los anti-patrones dicen que lo in-place rompe autograd | Contradicción interna; la operación in-place es segura en muchos casos y falla cuando autograd necesita el valor sobrescrito |
| `torch.save(model.state_dict(), …)` es «malo» en checkpoints y «bueno» en anti-patrones | Depende del objetivo (reanudar frente a exportar pesos); decirlo |
| `set_seed` como «reproducibilidad completa» | No siembra los workers del `DataLoader` ni activa algoritmos deterministas |
| «Precisión mixta para 2x de velocidad»; `@torch.no_grad()` «más eficiente» que el bloque | Cifra y comparación sin fuente |

**Destino:** ninguno hasta que un consumidor declare PyTorch.
