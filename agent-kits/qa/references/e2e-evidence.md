# E2E estables y evidencia de navegador

> Léela solo en P3 (al escribir los `E2E-xx.spec.mjs`) y al clasificar los
> resultados para el informe (P4-bis y P5). Los criterios de teclado, foco,
> estados remotos y accesibilidad siguen en la skill `frontend-quality`; aquí
> va cómo escribir specs que no fallen por azar y qué evidencia vale.

## Localizadores

La regla de P3 (rol y nombre accesible primero) se aplica con este orden:

| Prioridad | Localizador | Cuándo |
|---|---|---|
| 1 | `getByRole(rol, { name })` | Botones, enlaces, campos, encabezados: casi siempre |
| 2 | `getByLabel` | Campos de formulario con etiqueta |
| 3 | `getByPlaceholder`, `getByText`, `getByAltText`, `getByTitle` | Contenido sin rol interactivo |
| 4 | `getByTestId` | Solo si no hay rol ni texto estable; no prueba nada visible para el usuario |
| — | CSS o XPath de estructura | Se rompen al cambiar el DOM; si no queda otra, se anota como hallazgo de accesibilidad |

## Aserciones web-first

Las aserciones sobre un localizador **esperan** hasta que se cumple la
condición o vence el `expect.timeout` del runner; las comprobaciones manuales
no esperan nada.

| Así no | Así sí |
|---|---|
| `expect(await el.isVisible()).toBe(true)` | `await expect(el).toBeVisible()` |
| `expect(await lista.count()).toBeGreaterThan(0)` | `await expect(lista).toHaveCount(n)` o `await expect(lista.first()).toBeVisible()` |
| Leer `page.url()` y compararlo | `await expect(page).toHaveURL(…)` |
| `page.waitForNavigation()` | `page.waitForURL(…)` |

## Esperas prohibidas

- **`page.waitForTimeout(ms)`**: un test que espera tiempo es inestable por
  diseño; solo vale para depurar a mano y nunca queda en un spec.
- **`waitForLoadState('networkidle')`** o `waitUntil: 'networkidle'`: la
  documentación lo desaconseja para tests. Espera al estado visible con una
  aserción web-first.
- Subir `timeout`, `expect.timeout` o `retries` para que un test pase no
  arregla nada: esconde la causa.

## Aislamiento

Cada test crea sus datos (o los recibe de un fixture) y no depende del orden
ni del estado que dejó otro: almacenamiento, cookies y sesión propios. Un test
que solo pasa detrás de otro es un defecto del test, no de la app.

## Flaky a la vista

El runner del kit reintenta dos veces para que el reporter distinga:

| Resultado | Significado | Para `qa-gate.py` |
|---|---|---|
| Pasa | Pasó a la primera | Verde |
| Flaky | Falló y pasó en un reintento | No verde salvo justificación concreta en `flaky-justify.json` |
| Falla | Falló en todos los intentos | No verde |

«A veces falla» no es una justificación: el motivo nombra la causa observada
(dato compartido, animación, carrera con una petición) y la traza que lo
muestra.

Los reintentos solo clasifican un fallo que ya ocurrió; no buscan la
inestabilidad. Un spec **nuevo o reescrito** se ejecuta una vez con
`--repeat-each=3` (la misma invocación del runner con
`npx playwright test <spec> --repeat-each=3`) antes de acreditar su criterio.
Si alguna repetición falla, el spec es flaky o defecto, no verde.

## Cuarentena con dueño y fecha

Sacar un test de la ejecución (`test.fixme`, `test.skip`) lo deja como
**omitido**, y `qa-gate.py` no cuenta los omitidos como rojo. Por eso una
cuarentena solo vale si es visible:

- anotación con la incidencia: `test.fixme(true, 'motivo')` más
  `annotation: { type: 'issue', description: '<enlace o ID>' }`;
- dueño y fecha de salida, en la anotación y en el informe;
- el criterio que cubría pasa a la checklist manual (`M-xx`) mientras dure:
  un E2E en cuarentena no acredita nada;
- vencida la fecha, el test vuelve o se declara el criterio sin cobertura.

Nunca `test.skip(!!process.env.CI, …)` sin incidencia, dueño ni fecha: saca
el test de la ejecución en silencio.

## Comparación visual

Solo si el test-plan pide un bloque visual. `toHaveScreenshot` compara contra
una imagen de referencia (baseline) aprobada.

| Fijar | Por qué |
|---|---|
| Navegador y versión, sistema operativo | El nombre de la baseline incluye navegador y plataforma; otra combinación no es comparable |
| Fuentes instaladas, escala y viewport | El renderizado cambia con el host y su configuración |
| Datos, fecha, hora y zona horaria | Un contenido distinto no es una regresión visual |
| Animaciones y cursor | `toHaveScreenshot` las desactiva y oculta el cursor por defecto; no lo cambies |
| Zonas volátiles (fechas, avatares, anuncios) | `mask` o `stylePath` para taparlas; también para datos sensibles |

- Genera la baseline en el **mismo entorno** donde se compara (aquí, el runner
  de `~/.claude/tool-cache/qa/`). Una baseline de otra máquina da falsos rojos.
- Sin baseline aprobada, el resultado es **inconcluso**, no verde.
- `--update-snapshots` solo ante un cambio visual previsto y aprobado; el
  informe dice qué test, por qué y quién lo aprobó. Nunca para convertir un
  rojo en verde.
- `threshold` y `maxDiffPixels` se declaran en el informe y no se suben para
  ocultar una diferencia.

## Clasificar cada resultado

| Clase | Cuándo | En el informe |
|---|---|---|
| Pasa | Aserciones en verde a la primera | Evidencia (captura) enlazada al criterio |
| Defecto | Falla y la traza muestra un comportamiento contrario al criterio | Error, captura y traza |
| Flaky | Pasa en un reintento | Motivo o rojo |
| Inconcluso | Falta baseline, dato de prueba o entorno comparable | Qué falta para concluir |
| En cuarentena | Omitido con incidencia, dueño y fecha | Criterio movido a `M-xx` |
| No ejecutado | Playwright no instalado o el usuario lo declinó | Escenario en manual, declarado |

## Artefactos y límites

- La configuración del runner guarda captura al final de cada test y traza
  solo de los que fallan; el vídeo va apagado. Si hace falta vídeo, se activa
  con la opción `video` del config (no existe `videosPath`).
- `browser.startTracing` es el trazado de bajo nivel de Chromium, no la traza
  de Playwright: usa la opción `trace`.
- Un mock de una integración externa prueba la interfaz, no la integración:
  dilo en el informe.
- Ninguna variable de entorno sustituye al guardrail de host: los E2E corren
  solo contra hosts locales o privados, con cuentas de prueba.

## Fuentes

- Playwright — Best practices (localizadores de cara al usuario, aserciones web-first, aislamiento): https://playwright.dev/docs/best-practices · consultada 2026-10-14.
- Playwright — Locators (orden recomendado, `getByTestId`): https://playwright.dev/docs/locators · consultada 2026-10-14.
- Playwright — Page (`waitForTimeout` desaconsejado, `networkidle` desaconsejado, `waitForNavigation` obsoleto): https://playwright.dev/docs/api/class-page · consultada 2026-10-14.
- Playwright — Retries (passed / flaky / failed): https://playwright.dev/docs/test-retries · consultada 2026-10-14.
- Playwright — Command line (`--repeat-each <N>`: ejecuta cada test N veces; `--retries`): https://playwright.dev/docs/test-cli · consultada 2026-10-14.
- Playwright — Annotations (`skip`, `fixme`, anotación `issue`): https://playwright.dev/docs/test-annotations · consultada 2026-10-14.
- Playwright — Visual comparisons (baseline por navegador y plataforma, `--update-snapshots`, `threshold`, `maxDiffPixels`, `stylePath`): https://playwright.dev/docs/test-snapshots · consultada 2026-10-14.
- Playwright — LocatorAssertions (`toHaveScreenshot`: `animations`, `caret`, `mask`; `toHaveCount`): https://playwright.dev/docs/api/class-locatorassertions · consultada 2026-10-14.
- Playwright — Browser (`startTracing`, `recordVideo`): https://playwright.dev/docs/api/class-browser · consultada 2026-10-14.
