---
name: unit-tests
description: >
  Pirámide de pruebas y GATE de cobertura determinista, agnóstico de stack — `coverage-gate.py`
  detecta pytest/jest/vitest/phpunit/go, ejecuta su cobertura OFICIAL solo si la herramienta está
  en PATH y mide el % global o, con `--changed-only`, SOLO los ficheros de código del diff. Nunca
  inventa un porcentaje: sin herramienta/stack/parseo, avisa y sale con 2. Skill COMPARTIDA, no un
  agente nuevo (decisión: evitar roles duplicados — LES-013): la usan `implementer` (gate opt-in
  por fase) y `qa` (pirámide en el informe). NO es el método de escribir el test (eso es `tdd`) ni
  las pruebas E2E (`qa`). Úsala cuando el usuario diga "sube la cobertura de tests", "qué % de
  cobertura tenemos", "pon un gate de cobertura", "pirámide de pruebas", "cuántos tests unitarios
  faltan", o cuando `dev.json` traiga `tests.coberturaMinima`.
---

# unit-tests — la base de la pirámide, medida sin inventar nada

Un ciclo con `tdd` bien seguido y un `qa` en verde no dicen cuánto del código NUEVO queda sin
probar. Esta skill mide eso: **cobertura del diff**, con la herramienta oficial de cada stack, y
un gate que el `implementer` puede aplicar por fase si el proyecto lo pide.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):
```bash
UTSKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/unit-tests' 2>/dev/null | head -1)"
python3 "$UTSKILL/scripts/coverage-gate.py" <ruta> [--min 80] [--changed-only [--base <ref>]] [--json]
```

## La pirámide — qué va en cada capa y por qué la base es unitaria

| Capa | Qué prueba | Quién la ejecuta aquí | Proporción orientativa |
|---|---|---|---|
| **Unitaria** | Una función/módulo aislado: ramas, límites, errores | El propio código del proyecto + este gate mide su %; el CÓMO escribirla es `tdd` | La mayoría (rápida, barata, aísla la causa) |
| **Integración** | Dos o más módulos reales juntos (BD, API interna, colas) | El proyecto (sin script propio aquí) | Menos: solo las costuras que de verdad fallan al integrar |
| **E2E** | El flujo completo desde la UI/API pública | `qa` con Playwright + `qa-gate.py` | Poca: cara, lenta, frágil — solo los escenarios `E2E-xx` del plan |

La base es unitaria porque un fallo ahí señala la línea exacta; un E2E rojo solo dice "algo se
rompió". Si la mayoría de tus tests son E2E, cada regresión cuesta más de diagnosticar que de
arreglar. Detalle y ejemplos: `references/pyramid.md`.

## Qué probar PRIMERO (cuando el tiempo es limitado)

1. **Ramas de error**: el `except`, el `if not encontrado`, el timeout — es donde vive el bug que
   nadie reprodujo en desarrollo.
2. **Límites**: lista vacía, un solo elemento, el máximo permitido, el offset justo en el borde.
3. **Contratos entre módulos**: lo que un módulo asume que el otro le da (tipo, formato, invariante)
   — ahí es donde un refactor de otro rompe silenciosamente tu código.

El "camino feliz" es el que menos falla en producción; si solo hay tiempo para un test, que sea de
los tres de arriba, no del camino feliz.

## Anti-patrones (no cuentan como cobertura real)

- **Test que replica la implementación**: reescribe la misma lógica en el test en vez de afirmar el
  resultado — cualquier refactor correcto lo rompe.
- **Mocks de todo**: si mockeas la función que estás probando, no pruebas nada; mockea solo lo
  externo (red, disco, reloj).
- **Asserts triviales**: `assert resultado is not None` cuando el criterio es "devuelve las filas
  del usuario" — pasa con cualquier basura.
- **Tests que dependen del orden**: si `test_b` solo pasa porque `test_a` corrió antes y dejó
  estado, no son tests unitarios — son un integration test disfrazado, y frágil.

## El gate — `coverage-gate.py`

Detecta el stack por los ficheros del proyecto (pytest si hay `pyproject.toml`/`pytest.ini`/
`setup.cfg` o `tests/`+`*.py`; jest/vitest por `package.json`; phpunit por `phpunit.xml*`/
`composer.json`; go por `go.mod`), ejecuta su cobertura OFICIAL **solo si la herramienta está en
PATH** y parsea el % global y por fichero. Con `--changed-only [--base <ref>]` mide la MEDIA de
solo los ficheros de código del diff (sin tests ni prosa) — la métrica que de verdad importa para
un cambio concreto, no la del proyecto entero. Exit **0** si el % evaluado ≥ `--min` (80 por
defecto), **1** si no llega, **2** sin herramienta/stack/parseo — con aviso explícito, **nunca un
% inventado**. `--json` para consumo por script; `--runner <cmd>` sustituye el comando oficial
(los tests de este repo lo usan para mockear la ejecución).

## Integración con el resto de la cadena

- **`implementer` (P5, opt-in):** si `.claude/dev.json` trae `"tests": {"coberturaMinima": N}`,
  ejecuta `coverage-gate.py --changed-only --min N` al cerrar cada fase; sin esa clave, solo
  informa si la herramienta está disponible (nunca bloquea el cierre por su cuenta).
- **`qa`:** incluye en su informe la pirámide — el % unitario de este gate (si el proyecto lo
  configuró) junto al % de escenarios E2E de `qa-gate.py` — para que el lector vea las dos capas
  juntas, no solo la E2E.
- **Lente A de `adversarial-review`:** cuando comprueba "los criterios con test tienen su test",
  cita el % de `coverage-gate.py --changed-only` de las tareas afectadas como dato de apoyo (no
  sustituye la revisión línea a línea del test).
- **`/setup` (paso 5-quinquies):** pregunta la cobertura mínima, opt-in, default sin gate.

## Delimitación (qué NO hace esta skill)

- **No es `tdd`**: `tdd` es el MÉTODO de escribir el test (rojo antes que verde); esta skill mide
  el resultado agregado, no dicta el orden de escritura.
- **No es `qa`**: `qa` ejecuta los escenarios E2E con Playwright y da el veredicto final del plan
  (`qa-gate.py`); aquí solo se mide la capa unitaria.
- **No es un agente nuevo**: decisión explícita para no duplicar roles (`implementer` ya escribe
  código y `qa` ya prueba) — ver `LES-013` en `docs/knowledge/lessons/`.
- No ejecuta la suite completa por su cuenta más allá de lo que la herramienta de cobertura ya
  corre; no elige qué tests escribir; no sube ni baja el umbral por su cuenta.

## Degradación

Sin la herramienta del stack en PATH (o paquete de cobertura no instalado, p. ej. `pytest-cov`):
exit 2 con aviso explícito, nunca un % inventado — el ciclo sigue, solo sin gate automático. Sin
git (o `--changed-only` fuera de un repo): aviso y, si no hay nada que medir, exit 0. Sin
`dev.json` o sin la clave `tests.coberturaMinima`: el `implementer` no aplica el gate, solo informa
si puede.

## Referencias

| Fichero | Cuándo leerlo |
|---|---|
| `references/pyramid.md` | Detalle de la pirámide con ejemplos por capa y por qué cada anti-patrón falla en la práctica |
