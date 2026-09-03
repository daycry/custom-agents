---
name: tdd
description: >
  Fuente ÚNICA del método RED-GREEN-REFACTOR del plugin — ley dura («el código escrito antes de su
  test se borra y se reescribe tras el rojo»), ciclo con EVIDENCIA obligatoria del rojo en el ledger
  (`RED: <test> falló con <error> · <fecha>`), qué NO es TDD (tests después, tests vacíos, asserts
  triviales, un test que ya pasaba), excepciones declaradas («TDD n/a: prosa/config») y comandos
  exactos para correr UN solo test rojo por stack. La sigue el `implementer` (y el subagente del
  brief) cuando `.claude/dev.json` tiene `tdd: true`; también a demanda. NO corre la suite completa
  ni da el verde de pruebas (eso es `qa` con `qa-gate`), ni depura fallos ajenos (`debug-root-cause`).
  Úsala cuando el usuario diga "hazlo con TDD", "escribe primero el test", "test antes del código",
  "RED-GREEN-REFACTOR", "quiero evidencia del rojo", o cuando dev.json active `tdd`.
---

# tdd — test primero, con prueba de que falló

El TDD de este plugin no es «tener tests»: es **ver el test fallar antes de escribir el código que lo
hace pasar**, y dejar esa evidencia donde alguien pueda comprobarla (el ledger `tasks.md`). Sin rojo
visto, no hubo TDD — hubo tests después.

> **Ley dura.** El código escrito antes de su test **se borra y se reescribe tras el rojo**. No se
> «rescata» añadiéndole un test que ya pasa: ese test no demuestra nada (no sabes si falla cuando el
> código está mal). Si te descubres implementando sin rojo, para, guarda la idea, borra el código y
> empieza por el test.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):
```bash
TDDSKILL="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/tdd' 2>/dev/null | head -1)"
SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
```

## Cuándo aplica (y cuándo NO)

| Situación | Qué hacer |
|---|---|
| `.claude/dev.json` → `tdd: true` (lo escribe `/setup` paso 5) | Toda tarea con código testeable sigue este ciclo; el `implementer` la invoca en su P3 y `task-brief.py` la inyecta en el brief del subagente |
| El usuario lo pide («hazlo con TDD», «escribe primero el test») | Aplica el ciclo a ese cambio aunque `dev.json` diga `false` |
| Tarea sin código testeable (prosa, docs, config, plantillas, un `.md` de agente) | **Excepción declarada:** anota en la tarea `TDD n/a: <motivo>` y sigue el flujo normal. **No fabriques un test vacío para cumplir** |
| Arreglar un fallo que ya existe | Primero `debug-root-cause` (reproducción mínima); el test de regresión de su Fase 4 ES el rojo de este ciclo |
| Correr la suite y dar el verde final | No es esto: es `qa` con `qa-gate.py`. Aquí se corre **un** test, el de la tarea |

## El ciclo — por criterio de aceptación, no por tarea entera

1. **RED — escribe el test que expresa UN criterio de aceptación y ejecútalo solo.** Debe **fallar por
   la razón correcta** (la funcionalidad no existe / devuelve otra cosa), no por un import roto o un
   typo del test. Comando por stack: lee `references/by-stack.md` **solo al llegar aquí** si no
   sabes cómo correr un único test en el proyecto. Registra la evidencia en el ledger, en la tarea:
   `RED: <fichero::test> falló con <error resumido> · <AAAA-MM-DD>`.
   **Sin esa línea el TDD de la tarea no cuenta** (lo verifica la Lente A de `adversarial-review`
   y lo exige el orquestador al validar un `DONE` de subagente).
2. **GREEN — el cambio MÍNIMO que hace pasar ese test.** Nada de «ya que estoy». Vuelve a correr
   solo ese test → pasa. Corre los tests vecinos del módulo (no la suite entera) para no romper lo
   que había.
3. **REFACTOR — con todo en verde, limpia:** nombres, duplicación, estructura. Vuelve a correr los
   mismos tests. Si un refactor exige cambiar un test, sospecha: o el test probaba implementación
   (mal test) o el refactor cambió comportamiento (no es refactor).
4. **Siguiente criterio** → vuelve a 1. Al cerrar la tarea, ejecuta su `Verificación` declarada y
   pega la salida (eso ya lo exige el ledger; el TDD añade la línea `RED:` por criterio).

En **modo subagentes** (`subagentes: true`), el subagente devuelve la evidencia del rojo en su
informe y **el orquestador** la copia al ledger al validar el `DONE` (el subagente no toca el ledger).

## Qué NO es TDD (aunque lo parezca)

- **Tests después**: implementar y luego «cubrirlo». No hay rojo; el test puede pasar por casualidad.
- **Test vacío / `assert True` / `pass`**: no puede fallar → no expresa criterio. Test-teatro.
- **Assert trivial**: `assert resultado is not None` cuando el criterio es «devuelve las filas del
  usuario». El test pasa con cualquier basura.
- **El test ya pasaba**: si lo escribes y sale verde a la primera, o el criterio ya estaba cubierto
  (dilo y no cuentes la tarea como TDD) o el test no prueba lo que crees (arréglalo hasta verlo rojo).
- **Rojo por la razón equivocada**: `ImportError`, `SyntaxError`, fixture rota. Es rojo, pero no
  evidencia: arregla el test hasta que falle por la funcionalidad ausente.
- **Un test gigante para toda la tarea**: no aísla criterios; cuando falla no dice qué. Un test por
  criterio.

Catálogo con ejemplos concretos (antes/después): `references/anti-patterns.md` — léelo **solo** si
dudas de si tu test cuenta.

## Racionalizaciones que NO valen

Formato y reglas: `"$SHAREDKIT/rationalization-table.md"`. Si te oyes decir una de estas, haz la tercera columna.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Lo testeo al final, cuando termine la tarea» | Eso es tests-después: sin rojo no sabes si el test detecta el fallo. | Un criterio → un test rojo → mínimo verde; línea `RED:` en el ledger antes de seguir. |
| «Este cambio es trivial, no necesita test» | Trivial es donde se cuelan las regresiones; si es testeable, se testea; si no, se declara. | Test rojo de 5 líneas, o anota `TDD n/a: <motivo>` explícito en la tarea. |
| «El test ya pasaba, así que el criterio está cubierto» | Un test que nunca falló no demuestra que detecte el fallo. | Rómpelo a propósito (comenta la funcionalidad) hasta verlo rojo, o admite que no es TDD. |
| «Ya escribí el código; le añado el test y listo» | Ley dura: el código anterior al rojo se borra; el test posterior es cobertura, no TDD. | Guarda la idea, borra el código, escribe el test, míralo fallar, reescribe. |
| «Pongo `assert True` para tener el hueco y luego lo relleno» | Un test que no puede fallar es test-teatro y contamina el ledger con un `RED:` falso. | Escribe el assert del criterio real aunque aún no compile la llamada. |
| «Corro la suite entera para ver el rojo» | Tarda, mezcla fallos ajenos y desanima a iterar; el rojo debe ser de TU test. | Un solo test con el comando de `references/by-stack.md`; la suite es de qa. |
| «Falló con `ImportError`, ya tengo el rojo» | Rojo por la razón equivocada: no prueba la funcionalidad ausente. | Arregla imports/fixtures hasta que falle por el assert del criterio. |
| «El refactor me obliga a cambiar el test, lo adapto» | Si el test cambia, cambió el comportamiento o el test probaba implementación. | Revierte el refactor o rediseña el test contra el comportamiento observable. |

## Salida y traza

- Por criterio: línea `RED: <fichero::test> falló con <error> · <fecha>` en la tarea del ledger.
- Por tarea: `Verificación` ejecutada con salida pegada (regla general del ledger, no de esta skill).
- Excepción: `TDD n/a: <motivo>` visible en la tarea. Nunca silencio.
- La Lente A de `adversarial-review` marca gap **Important** una tarea `completado` con `tdd: true`
  que no tenga ni `RED:` ni `TDD n/a`.

## Referencias

| Fichero | Cuándo leerlo |
|---|---|
| `references/by-stack.md` | Al llegar al paso RED si no sabes correr UN test en pytest / jest / vitest / phpunit / go test / cargo |
| `references/anti-patterns.md` | Si dudas de si tu test cuenta como rojo válido (catálogo antes/después) |

## Qué NO hace

- No corre la suite completa ni da el verde de pruebas (`qa` + `qa-gate.py`).
- No depura fallos existentes (`debug-root-cause`); no revisa el diff (`adversarial-review`).
- No decide si `tdd` está activo: eso lo lee el `implementer`/orquestador en `.claude/dev.json`.

## Degradación

Sin `references/` (instalación parcial): el ciclo y la ley dura viven en este fichero; pide al usuario
el comando de un test si no lo deduces del repo. Sin `dev.json`: solo a demanda. Nunca bloquea: si no
hay forma de correr un test (sin runner instalado), decláralo `TDD n/a: sin runner` y sigue.
