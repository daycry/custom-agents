# .NET idiomático, arneses por tarea y E2E con Playwright — S086–S088

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **22.875 bytes/773 líneas**, cero recursos en sus
directorios. [dotnet-harness-e2e-reading-evidence.json](dotnet-harness-e2e-reading-evidence.json)
registra fuentes y contrapartes propias. Nombres originales en el mapa privado;
[tasks.md](../tasks.md) es el ledger canónico. Las decisiones son propuestas para T-08.

No se compiló C#, no se ejecutó Playwright ni se generó ningún arnés. Nada de
este bloque está integrado.

## S086 — Patrones idiomáticos de C# y .NET

**Identidad.** SHA-256 `61bc21a6c6d6…` (completo en la evidencia), 9.316 bytes/322
líneas. Inmutabilidad, nulabilidad explícita, inyección de dependencias,
async/await con cancelación, Options, Result, repositorio con EF Core, middleware,
Minimal API, guard clauses y antipatrones.

**Valor y cobertura existente.** El bloque C++/.NET (S064) ya propuso
`skills/dotnet-practices/references/testing.md`. S086 aporta la referencia de
diseño que faltaba para esa especialidad opcional; no hay guía .NET propia.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `Task.WhenAll` sobre servicios que comparten un `DbContext` con ámbito | Un `DbContext` no admite operaciones concurrentes; paralelizar solo dependencias que lo permitan |
| `PlaceOrderAsync(request)` sin token y con `CancellationToken.None` | Contradice «async con cancelación» de la misma pieza; propagar el token del llamador |
| Minimal API llama `PlaceOrderAsync(request, cancellationToken)` | La firma definida arriba no acepta token: el ejemplo no compila |
| `Result<T>` como `record` con constructores privados | Los records generan igualdad y `with` que pueden saltarse las invariantes; usar clase sellada o unión discriminada de la versión |
| `?? throw new ArgumentNullException` en constructores con DI | Redundante con contenedor y tipos no anulables; `ArgumentNullException.ThrowIfNull` cuando haga falta |
| Repositorio genérico sobre EF Core | `DbContext` ya es unidad de trabajo; el repositorio solo cuando abstraiga una frontera real |
| `TypedResults.BadRequest(result.Error)` con texto libre | Problem Details (RFC 9457), coherente con backend-practices |
| Log de método, ruta y estado en middleware | La ruta puede llevar datos; redactar y no registrar query strings |
| `ConcurrentDictionary` como sustituto de estado estático mutable | Sigue siendo estado global compartido entre peticiones; decidir el ciclo de vida |
| «`string.Format` en bucles → StringBuilder» | Medir antes; los manejadores de interpolación ya optimizan muchos casos |

**Destino propuesto.** `skills/dotnet-practices/references/design-async.md`
junto a la de testing de S064, con versión de SDK/C# del `global.json` y
`.csproj`. Sin rol revisor .NET obligatorio.

## S087 — Arneses por tarea en modos de workflow dinámicos

**Identidad.** SHA-256 `bdf7902e4e21…`, 5.389 bytes/124 líneas. Cuándo crear
un arnés local, contrato (objetivo, entradas, salidas, eval, handoff), árbol
de decisión, criterios para extraer una skill compartida, checkpoints de panel,
gates de eval por tipo de trabajo y antipatrones.

**Valor y cobertura existente.** Casi todo existe con dueño: `/dev-cycle`
(objetivo, criterios, Verificación por tarea, ledger como handoff), vía rápida y
quick-implement para lo puntual, `plugin-dev` para extraer piezas, `outcome-evals`
para evals reproducibles, `plugin-panel` para estado observable y `retro` para
patrones repetidos. El delta es un criterio explícito de **cuándo un arnés
ad hoc merece convertirse en pieza** del plugin.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| Arnés local «bajo un área temporal o del proyecto» | El plugin exige ledger canónico; un arnés sin `tasks.md` pierde la trazabilidad |
| «Extraer cuando se cumplan 2 de 5 criterios» | **Conservar** como regla de `plugin-dev` junto a ADR-011 (un rol, un dueño): evita duplicar piezas |
| Checkpoints Plan/Queue/Run/Gate/Handoff en un panel | Ya proyectados por `plugin-panel --serve` desde el ledger; no otro almacén |
| «Señal de tokens/coste si existe» | `usage-meter`; sin medición compatible, nulo, nunca estimado como medido |
| Referencias a un panel y estado propios del catálogo de origen | No aplicables; sustituir por los dueños propios |
| «Do not claim reusable until another teammate can rerun the eval» | **Conservar**: coincide con la exigencia de `Verificación` reproducible |

**Destino propuesto.** Añadir a `plugin-dev` el criterio de extracción (2 de 5
señales + sin solape de rol). Sin skill nueva.

## S088 — Patrones E2E con Playwright

**Identidad.** SHA-256 `b0e00e7e17cb…`, 8.170 bytes/327 líneas. Organización,
Page Object Model, configuración, cuarentena de flakies, artefactos, CI,
plantilla de informe y ejemplos de wallet y operaciones financieras.

**Valor y cobertura existente.** `qa` ejecuta Playwright solo contra hosts
locales con guardarraíl, genera specs desde `E2E-xx`, informe md+pdf y veredicto
por `qa-gate.py`; `frontend-quality` cubre teclado, foco y estados remotos.
El delta es una guía de estabilidad de tests para quien escribe los specs.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `waitForLoadState('networkidle')` como patrón y como arreglo de flakiness | La documentación de Playwright lo desaconseja para tests; esperar aserciones web-first sobre el estado visible |
| Localizadores por `data-testid` en todos los ejemplos | Preferir `getByRole`/`getByLabel`, que además prueban accesibilidad (frontend-quality); `data-testid` como último recurso |
| `expect(count).toBeGreaterThan(0)` sobre `count()` | Sin reintento automático; usar `toHaveCount`/aserciones de locator |
| `browser.startTracing` y `videosPath` | API de Chromium antigua y opción inexistente en `use`; `trace`/`video` del config y `outputDir` |
| `retries: 2` en CI | Oculta flakies; registrarlas como tales en el informe, no contarlas como verde (qa-gate) |
| `test.skip(process.env.CI, …)` como cuarentena | Saca el test de CI sin plazo ni dueño; cuarentena con issue y fecha de salida |
| `BASE_URL` de staging en CI | Contradice el guardarraíl del plugin: E2E solo contra hosts locales/privados |
| Prueba de «trade» que se salta solo con `NODE_ENV=production` | Una variable de entorno no protege frente a efectos con dinero real; el guardarraíl debe ser de host y cuenta de prueba |
| Mock de `window.ethereum` | Útil para la UI; no prueba la integración con el wallet ni la firma |

**Destino propuesto.** `agent-kits/qa/references/stable-specs.md` (o una
sección de `frontend-quality`): locators accesibles, aserciones web-first,
sin `networkidle`/`waitForTimeout`, flakies visibles y cuarentena con dueño.

Contraste oficial pendiente: no se consultó en este bloque la documentación de
Playwright, ASP.NET Core ni EF Core; las adaptaciones que dependen de versión
se contrastarán antes de integrar.
