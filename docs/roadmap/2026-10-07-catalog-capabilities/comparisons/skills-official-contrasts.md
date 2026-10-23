# Contraste oficial de afirmaciones de las fichas de skills — 2026-10-13

Este documento revisa las afirmaciones técnicas que las fichas `skills-*.md` de esta carpeta dejaron marcadas como no contrastadas o con contraste oficial pendiente. Cada una se ha comparado con la documentación oficial del proyecto, la especificación o el repositorio oficial, consultados el 2026-10-13 solo en lectura y sin autenticarse. Las fichas son registros y no se modifican: cuando una afirmación resulta incorrecta, la corrección queda aquí. Las citas, de 25 palabras como máximo, se dejan en su idioma original. No entran los pendientes que no contienen una afirmación técnica concreta: la guía de entorno y rendimiento de Vite «para la versión que declare el consumidor», pass@k de S097, las cifras de publicaciones externas de S110–S112, los precios de mercado de S089–S094 y la normativa de S161/S170–S172. Tampoco entran las adaptaciones de ASP.NET Core de S086 que no dependen de documentación consultada. Fuente de datos: [skills-official-contrasts.json](skills-official-contrasts.json).

Recuento: **31 confirmadas**, **3 corregidas**, **3 no concluyentes** (37 afirmaciones).

## [skills-vue-vite-tinystruct.md](skills-vue-vite-tinystruct.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 40 | Rolldown «desde v7» y minificador `oxc` por defecto (afirmación de la pieza S289). | **corregida** | [enlace](https://vite.dev/guide/migration) · [2](https://v7.vite.dev/config/build-options) | «Vite 8 uses Rolldown and Oxc based tools instead of esbuild and Rollup.» | Rolldown y Oxc por defecto llegan con Vite 8, no con Vite 7. La documentación de Vite 7 mantiene Rollup y `build.minify` por defecto `'esbuild'` («'esbuild' for client build, false for SSR build»). |
| 40 | `esbuild` «obsoleto» como minificador. | confirmada | [enlace](https://vite.dev/config/build-options) | «build.minify: 'esbuild' is deprecated and will be removed in the future.» | Vale para Vite 8 (por defecto `'oxc'`; esbuild pasa a dependencia opcional). En Vite 7 esbuild sigue siendo el minificador por defecto. |

## [skills-terminal-uncloud-x-visa.md](skills-terminal-uncloud-x-visa.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 87 | La subida de medios usa un endpoint v1.1 que hay que contrastar con la documentación vigente. | confirmada | [enlace](https://docs.x.com/changelog) · [2](https://docs.x.com/x-api/getting-started/about-x-api) · [3](https://docs.x.com/x-api/media/quickstart/media-upload-chunked) | «Today, we launched new X API v2 Media Upload endpoints.» | Entrada del 16-01-2025; la vía documentada es `POST /2/media/upload` y, en la subida por partes, `/2/media/upload/initialize`, `/{id}/append` y `/{id}/finalize`. La página «About the X API» describe v1.1 como «Limited support; use v2 for new projects», aunque todavía incluye «Some media upload endpoints» sin decir cuáles. El anuncio de retirada del foro devcommunity.x.com devolvió HTTP 403: la fecha de apagado del endpoint v1.1 queda sin confirmar. |
| 41 | `tls_insecure_skip_verify` desactiva la verificación; hay que confiar en la CA concreta. | confirmada | [enlace](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) | «turns off TLS handshake verification, making the connection insecure and vulnerable to man-in-the-middle attacks.» | La documentación añade «Do not use in production» y propone `tls_trust_pool` (p. ej. `tls_trust_pool file /path/to/cert.pem`) para confiar en una CA concreta. |
| 99 | «Directivas de confianza de Caddy» (contraste pendiente, sin afirmación concreta). | no concluyente | [enlace](https://caddyserver.com/docs/caddyfile/options) | «By default, no proxies are trusted.» | La ficha no dice qué afirma la pieza sobre la confianza en proxies, así que no hay nada que dictaminar. Queda como referencia lo que dice la documentación: `trusted_proxies` va en el bloque global `servers`, `client_ip_headers` por defecto solo lee `X-Forwarded-For` y `trusted_proxies_strict` (desde v2.8) está desactivado por defecto. La confianza TLS se registra en la fila de la línea 41. |

## [skills-ui-demo-desktop-e2e.md](skills-ui-demo-desktop-e2e.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 58 | `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` exige la estructura de límites extendida, no `JOBOBJECT_BASIC_LIMIT_INFORMATION`. | confirmada | [enlace](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information) | «This limit requires use of a JOBOBJECT_EXTENDED_LIMIT_INFORMATION structure.» | Los números de clase (2 básica, 9 extendida) y el fallo concreto de la llamada con la estructura básica no figuran en esta página; no se contrastaron. |
| 60 | `KILL_ON_JOB_CLOSE` no impide crear procesos fuera del job. | confirmada | [enlace](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information) | «Causes all processes associated with the job to terminate when the last handle to the job is closed.» | La salida del job se rige por flags distintos (`BREAKAWAY_OK`, `SILENT_BREAKAWAY_OK`). |

## [skills-springboot-patterns-security-testing.md](skills-springboot-patterns-security-testing.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 61 | `@MockBean` está en desuso a favor de `@MockitoBean` desde Spring Boot 3.4. | confirmada | [enlace](https://docs.spring.io/spring-boot/3.4/api/java/org/springframework/boot/test/mock/mockito/MockBean.html) | «since 3.4.0 for removal in 4.0.0 in favor of MockitoBean» | `@Deprecated(since="3.4.0", forRemoval=true)`; el sustituto es `org.springframework.test.context.bean.override.mockito.MockitoBean` (Spring Framework 6.2). |

## [skills-swift-swiftui.md](skills-swift-swiftui.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 30 | «Swift 5.5+» no basta para `URL.documentsDirectory`: depende de la disponibilidad en el SO. | confirmada | [enlace](https://developer.apple.com/tutorials/data/documentation/foundation/url/documentsdirectory.json) | «introducedAt: iOS 16.0, iPadOS 16.0, macOS 13.0, tvOS 16.0, watchOS 9.0, visionOS 1.0» | Metadatos de disponibilidad de la documentación de Apple (versión JSON de developer.apple.com/documentation/foundation/url/documentsdirectory). Por debajo de esas versiones hace falta `#available` con alternativa (`FileManager.urls(for:in:)`). |

## [skills-search-compliance-stocktake-compact.md](skills-search-compliance-stocktake-compact.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 123 | La memoria automática de Claude Code se guarda por proyecto en `~/.claude/projects/<proyecto>/memory/`, no en `~/.claude/memory/`. | confirmada | [enlace](https://code.claude.com/docs/en/memory) | «Each project gets its own memory directory at ~/.claude/projects/<project>/memory/.» | La ruta se puede cambiar con `autoMemoryDirectory` en `settings.json`; el índice `MEMORY.md` carga sus primeras 200 líneas o 25 KB. |
| 126 | Versión de Claude Code que retiró las herramientas de tareas (afirmación de la pieza S264, sin contrastar). | no concluyente | [enlace](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) | «Todo/task-tracking tools (TaskCreate/Get/Update/List, TodoWrite) are no longer available on Opus 4.8, Sonnet 5, Fable 5, Mythos 5, and newer models» | La ficha no recoge qué versión citaba la pieza, así que no se puede saber si acertaba. Según el registro oficial, 2.1.16 añade el sistema de tareas; 2.1.233 quita las herramientas en los modelos nuevos (se recuperan con `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`) y 2.1.268 las limita a una lista de modelos. Es una retirada por modelo, no general. |

## [skills-perl-family.md](skills-perl-family.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 45 | Con las señales diferidas de Perl, `alarm` no interrumpe a tiempo una sola coincidencia de regex larga. | confirmada | [enlace](https://perldoc.perl.org/perlipc) | «a signal that arrives during a long-running opcode (e.g. a regular expression operation on a very large string) will not be seen until» | Sección «Deferred Signals (Safe Signals)», apartado «Long-running opcodes»: el intérprete solo mira las señales antes de empezar cada opcode. |
| 56 | En la fila Total de `cover`, el primer número es la columna de sentencias, no el total. | confirmada | [enlace](https://github.com/pjcj/Devel--Cover/blob/main/lib/Devel/Cover/Criterion.pm) · [2](https://github.com/pjcj/Devel--Cover/blob/main/lib/Devel/Cover/DB.pm) | «my @Criteria = qw( statement branch condition mcdc subroutine pod time );» | Confirmado en el código fuente del repositorio oficial (commit `fc7d31c`), no en la documentación. `DB.pm` añade `total` detrás de los criterios y `print_summary` pone después una columna `scar`: el total no es ni la primera ni la última columna. Solo salen las columnas de los criterios recogidos. |

## [skills-plankton-postgres-prisma-audit.md](skills-plankton-postgres-prisma-audit.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 56 | `max_connections` solo cambia al reiniciar; `pg_reload_conf()` no basta. | confirmada | [enlace](https://www.postgresql.org/docs/current/runtime-config-connection.html) | «This parameter can only be set at server start.» | Documentación de PostgreSQL 18 (18.6). |

## [skills-python-pytorch.md](skills-python-pytorch.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 48 | En SQLAlchemy 2.x, `commit()` con `begin_nested()` confirma la transacción externa; hay que unir la sesión a una transacción externa con savepoint. | confirmada | [enlace](https://docs.sqlalchemy.org/en/20/orm/session_api.html) | «The outermost database transaction is committed unconditionally, automatically releasing any SAVEPOINTs in effect.» | La misma página documenta `join_transaction_mode="create_savepoint"` (desde 2.0.0rc1), pensado para meter una Session en una suite de pruebas sin tocar la transacción externa. |
| 49 | En modo estricto de pytest-asyncio, un fixture async necesita su propio decorador. | confirmada | [enlace](https://pytest-asyncio.readthedocs.io/en/latest/concepts.html) | «will only evaluate async fixtures decorated with @pytest_asyncio.fixture» | El modo estricto es el modo por defecto («This is why strict mode is the default mode»). |
| 27 | En Ruff actual, `select` va en `[tool.ruff.lint]`, no en `[tool.ruff]`. | confirmada | [enlace](https://docs.astral.sh/ruff/settings/) | «Options specified in the lint section take precedence over the deprecated top-level settings.» | La página no marca `select` como «Deprecated» por su nombre; la selección de reglas solo se documenta como `lint.select`. |
| 27 | Python 3.9 ya no tiene soporte. | confirmada | [enlace](https://devguide.python.org/versions/) | «3.9 \| PEP 596 \| end-of-life \| 2020-10-05 \| 2025-10-31» | Fin de vida el 31-10-2025. |

## [skills-motion-next-nuxt.md](skills-motion-next-nuxt.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 70 | Volver a `middleware.ts` en Next.js 16 «romperá» el middleware (afirmación de la pieza S188, no contrastada). | **corregida** | [enlace](https://nextjs.org/docs/app/guides/upgrading/version-16) | «The middleware filename is deprecated, and has been renamed to proxy … If you want to continue using the edge runtime, keep using middleware.» | En Next.js 16, `middleware.ts` está en desuso, no roto, y sigue siendo la opción para el runtime `edge`, que `proxy` no admite. La propia guía pide que el middleware edge no se renombre a proxy «a ciegas». Se confirma el cambio de nombre `middleware.ts` → `proxy.ts` (línea 61). Página para la versión 16.4.0. |
| 50 | Según la versión de Tailwind, el `transform` en línea de Motion anula el centrado con `-translate-x-1/2`/`-translate-y-1/2`. | confirmada | [enlace](https://tailwindcss.com/docs/translate) · [2](https://v3.tailwindcss.com/docs/translate) · [3](https://motion.dev/docs/react-motion-component) | «-translate-x-<fraction> → translate: calc(<fraction> * -100%) var(--tw-translate-y);» | En v4 la utilidad usa la propiedad CSS `translate`; en v3 usa `transform` (`translate-x-1/2` → «transform: translateX(50%);»). Motion pasa `x`/`y` a funciones de `transform` («Server will output translateX(100px)»). Que en v3 el estilo en línea pise la clase y en v4 se compongan es deducción de la cascada CSS: ninguna de las fuentes lo dice literalmente. |

## [skills-glass-polish-manim.md](skills-glass-polish-manim.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 17 | APIs de Liquid Glass: `glassEffect`, `GlassEffectContainer`, `glassEffectID` (SwiftUI) y `UIGlassEffect` (UIKit), iOS 26. | confirmada | [enlace](https://developer.apple.com/tutorials/data/documentation/swiftui/view/glasseffect(_:in:).json) · [2](https://developer.apple.com/tutorials/data/documentation/swiftui/glasseffectcontainer.json) · [3](https://developer.apple.com/tutorials/data/documentation/swiftui/view/glasseffectid(_:in:).json) · [4](https://developer.apple.com/tutorials/data/documentation/uikit/uiglasseffect.json) | «Applies the Liquid Glass effect to a view.» | `glassEffect(_:in:)`, `GlassEffectContainer` y `glassEffectID(_:in:)` aparecen desde la versión 26.0 de iOS, iPadOS, macOS, tvOS y watchOS; `UIGlassEffect`, desde iOS/iPadOS/tvOS 26.0. No se consultaron los efectos de borde de scroll ni el modo acentuado de WidgetKit. |
| 22 | «Usa siempre `GlassEffectContainer`» solo se justifica por rendimiento y transiciones. | confirmada | [enlace](https://developer.apple.com/tutorials/data/documentation/swiftui/glasseffectcontainer.json) | «SwiftUI renders the effects together, improving rendering performance and allowing the effects to interact with and morph into one another.» | Apple da como motivos el rendimiento y la fusión entre formas; en lo leído no aparece una obligación de usarlo siempre. |
| 48 | WCAG 2.2: 24×24 CSS px como mínimo (2.5.8, AA) y 44×44 (2.5.5, AAA). | confirmada | [enlace](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) · [2](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html) | «The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:» | 2.5.5 Target Size (Enhanced), nivel AAA: «at least 44 by 44 CSS pixels» (Understanding/target-size-enhanced.html). |

## [skills-foundations.md](skills-foundations.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 41 | El tamaño mínimo de 2.5.8 tiene excepciones; no basta imponer un cuadrado a todo control. | confirmada | [enlace](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | «The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:» | Excepciones: Spacing, Equivalent, Inline, User Agent Control y Essential. |

## [skills-kotlin-family.md](skills-kotlin-family.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 90 | Versiones de Gradle citadas por S152 (Kotlin, Ktor, Exposed, Kotest). | no concluyente | — | — | La ficha no anota qué versiones citaba la pieza, y el cuerpo fuente no está en el repositorio (solo su hash). Sin la afirmación concreta no hay nada que contrastar; se hará contra la versión que declare el consumidor. |

## [skills-dotnet-harness-e2e.md](skills-dotnet-harness-e2e.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 25 | Un `DbContext` no admite operaciones concurrentes (`Task.WhenAll` sobre el mismo contexto). | confirmada | [enlace](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/) | «Entity Framework Core does not support multiple parallel operations being run on the same DbContext instance.» | La misma página: «DbContext is Not thread-safe» y «always await async calls immediately, or use separate DbContext instances». |
| 31 | Errores HTTP como Problem Details (RFC 9457). | confirmada | [enlace](https://www.rfc-editor.org/rfc/rfc9457.html) | «This document obsoletes RFC 7807.» | Título: «Problem Details for HTTP APIs». |
| 79 | Playwright desaconseja `waitForLoadState('networkidle')` en tests; usar aserciones web-first. | confirmada | [enlace](https://playwright.dev/docs/api/class-page) | «DISCOURAGED wait until there are no network connections for at least 500 ms. Don't use this method for testing, rely on web assertions» | Texto de la opción `state` de `page.waitForLoadState`. |
| 82 | `browser.startTracing` es «API de Chromium antigua». | **corregida** | [enlace](https://playwright.dev/docs/api/class-browser) | «This API controls Chromium Tracing which is a low-level chromium-specific debugging tool.» | No está en desuso (Added in v1.11): es una herramienta de bajo nivel solo para Chromium, distinta del Tracing de Playwright. Matiz menor: la conclusión de la ficha (usar `trace` en la configuración) se mantiene. |
| 82 | `videosPath` es una opción inexistente; usar `trace`/`video` del config. | confirmada | [enlace](https://playwright.dev/docs/api/class-browser) · [2](https://playwright.dev/docs/test-use-options) | «Enables video recording for all pages into recordVideo.dir directory.» | `videosPath` no figura; la opción de contexto es `recordVideo`. En `use`, `video` y `trace` están apagados por defecto y dejan los artefactos en el «test output directory, typically test-results» (test-use-options; la página no nombra `outputDir`). |

## [skills-errors-evals-providers.md](skills-errors-evals-providers.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 120 | Contraste oficial pendiente de S095 sobre RFC 9457. | confirmada | [enlace](https://www.rfc-editor.org/rfc/rfc9457.html) | «This document obsoletes RFC 7807.» | La parte de S097 (pass@k/pass^k) no tiene documentación oficial de proyecto que consultar; queda fuera de este contraste. |

## [skills-installer-golang.md](skills-installer-golang.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 60 | `tt := tt` con `t.Parallel()` es innecesario desde Go 1.22. | confirmada | [enlace](https://go.dev/doc/go1.22) | «In Go 1.22, each iteration of the loop creates new variables, to avoid accidental sharing bugs.» | Solo en módulos cuyo `go.mod` declara `go 1.22` o superior. |
| 61 | Desde Go 1.24 existe `b.Loop()`, que evita que el compilador elimine el trabajo. | confirmada | [enlace](https://go.dev/doc/go1.24) | «Function call parameters and results are kept alive, preventing the compiler from fully optimizing away the loop body.» | Además, la función de benchmark se ejecuta una sola vez por `-count`. |
| 62 | `-tags=!generate` no es sintaxis válida de etiquetas. | confirmada | [enlace](https://pkg.go.dev/cmd/go) | «a comma-separated list of additional build tags to consider satisfied during the build.» | Los operadores `!`, `&&` y `\|\|` solo se describen para las líneas `//go:build`; `-tags` lista etiquetas que se dan por satisfechas. |

## [skills-parallel-containers-docs.md](skills-parallel-containers-docs.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 38 | `codex exec --cwd ... --task-file` no son flags del CLI; se usan `--cd` y el prompt posicional. | confirmada | [enlace](https://learn.chatgpt.com/docs/developer-commands?surface=cli) | «Set the workspace root before executing the task.» | Descripción de `--cd, -C`. El prompt es el argumento posicional `PROMPT` («Use - to pipe the prompt from stdin»); `--cwd` y `--task-file` no aparecen. URL de destino de la redirección 308 de developers.openai.com/codex/cli/reference. |

## [skills-flutter-ondevice-a11y.md](skills-flutter-ondevice-a11y.md)

| Línea | Afirmación | Veredicto | Fuente oficial | Cita | Nota |
|---|---|---|---|---|---|
| 60 | `<dialog>` nativo con `showModal()` resuelve la inercia del fondo y el cierre con Escape. | confirmada | [enlace](https://html.spec.whatwg.org/multipage/interactive-elements.html) | «Set subject's node document to be blocked by the modal dialog subject.» | La nota que sigue dice que el área enfocada queda inerte. Para el cierre, la especificación habla de «close request» (estado Auto de `closedby` con `showModal()`, con evento `cancel`). Que Escape sea una close request está en otra sección de la especificación que no se leyó. |
| 64 | `role="status"` es implícitamente polite. | confirmada | [enlace](https://www.w3.org/TR/wai-aria-1.2/) | «Elements with the role status have an implicit aria-live value of polite and an implicit aria-atomic value of true.» | — |
