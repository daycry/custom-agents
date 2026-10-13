# Vídeos de demostración con Playwright y E2E de escritorio Windows — S280, S291

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Dos cuerpos completos: **45.833 bytes/1.354 líneas**, sin recursos locales.
[ui-demo-desktop-e2e-reading-evidence.json](ui-demo-desktop-e2e-reading-evidence.json).
Nada se ejecutó ni se integró; no se instalaron Playwright, pywinauto ni
dependencias. Propuestas para T-08.

## S280 — Grabar vídeos de demostración de una interfaz web

`15.256 bytes/466 líneas`. Tres fases —descubrir, ensayar, grabar— con cursor y
subtítulos inyectados, ritmo pausado y escritura visible, sobre la grabación de
vídeo de Playwright.

**Comparación.** `qa` usa Playwright para **probar**, con veredicto de
`qa-gate.py`; una demo no prueba nada y ningún rol produce material promocional.
La fase de descubrimiento sí contiene un criterio útil para `qa`: antes de
escribir selectores, inspeccionar los controles reales de cada página (tipo de
campo, opciones de un `select` con valor de marcador, botones deshabilitados
hasta tener contenido). Hoy `qa` P3 traduce cada `E2E-xx` directamente.
**Destino:** una línea en `agents/qa.md` P3 —inspeccionar los controles de la
página y localizar por rol y nombre accesible antes de generar el test—,
coherente con `stack-practices/references/react.md` («actúan por rol/nombre
accesible»). La grabación de demos queda **sin destino**.

Defectos de la fuente:

- La plantilla captura cualquier error con `console.error('DEMO ERROR')` y sigue:
  el proceso termina con 0 y guarda un vídeo de un flujo roto, contra su propia
  regla «sin capturas silenciosas». `moveAndClick` y `typeSlowly` devuelven
  `false` y la demo continúa.
- `QA_BASE_URL` admite cualquier host y la sesión se graba con usuario
  autenticado; sin el guardarraíl de hosts locales de `qa` ni aviso sobre datos
  visibles en pantalla.
- Descartar opciones cuyo texto contiene «Select» depende del idioma de la UI.
- El ritmo se fija con esperas de tiempo (`waitForTimeout`); aceptable para un
  vídeo, nunca trasladable a un test.

## S291 — E2E de aplicaciones de escritorio Windows

`30.577 bytes/888 líneas`. pywinauto sobre UI Automation para WPF, WinForms,
Win32 y Qt: identificadores estables, page objects, esperas por condición,
artefactos, traza por paso opt-in, aislamiento en tres niveles, CI y modo de
reconocimiento de imagen.

**Comparación.** `qa` cubre solo E2E web con Playwright contra hosts locales; no
hay consumidor de escritorio Windows. **Sin destino** hasta que uno lo declare;
entonces sería una referencia de `qa`, no un agente nuevo (ADR-011). Ideas que
ya coinciden con el plugin: identificador estable antes que texto o posición
(rol y nombre accesible en web); esperas por condición, nunca `sleep`; traza
opt-in con el texto tecleado **redactado por defecto** y prohibida en flujos con
credenciales, criterio alineado con `agent-kits/shared/redact.py`.

Defectos que habría que corregir antes de adoptarla:

| Ejemplo | Corrección |
|---|---|
| Job Object con `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` en `JOBOBJECT_BASIC_LIMIT_INFORMATION` (clase 2) | Ese límite exige la estructura extendida (clase 9); con la básica la llamada falla y el ejemplo lanza `WinError` |
| «El job se cierra (y mata el proceso) cuando se recolecta» | El handle es un entero de `ctypes`: no se cierra por recolección; cerrar con `CloseHandle` en el teardown |
| El docstring dice que impide crear procesos fuera del job | `KILL_ON_JOB_CLOSE` no lo impide; además el proceso ya corre antes de asignarlo y el retorno de `AssignProcessToJobObject` no se comprueba |
| Nivel 1 «aislamiento de sistema de ficheros» redirigiendo `APPDATA`/`LOCALAPPDATA`/`TEMP` | Las apps que resuelven carpetas conocidas por la API del sistema ignoran esas variables, y el registro no se aísla; es aislamiento parcial |
| El fixture del nivel 1 importa `APP_ARGS` y `APP_TITLE` de `config.py` | `config.py` no los define (usa `MAIN_WINDOW_TITLE`); el ejemplo falla al importar |
| `shlex.split(APP_ARGS)` | Reglas POSIX: en Windows se come las barras invertidas de las rutas |
| `pytest.exit` dentro del fixture | Aborta toda la sesión, no el test |
| Fila «CI display not ready → set `DISPLAY`» | Variable de X11, sin efecto en Windows |
| Cuarentena con `skip` y `skipif(CI)` | Oculta el fallo; `qa-gate.py` exige justificar cada flaky por nombre en vez de silenciarlo |

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S280 | Demo no es prueba; un criterio de descubrimiento útil | Línea en `agents/qa.md` P3 |
| S291 | Sin consumidor de escritorio; ejemplos con fallos | Futura referencia de `qa` si se declara |

Contraste oficial pendiente para S291 (documentación de Job Objects y de UI
Automation) solo si un consumidor declara una app de escritorio Windows.
