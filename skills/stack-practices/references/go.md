# Go: contratos, concurrencia y pruebas

Lee esta referencia solo para una tarea Go. Architect, planner, implementer,
reviewer y qa comparten estos criterios; TDD, revisión y cobertura conservan
sus métodos. Usa `--stack go` en el selector cuando el proyecto declare Go.
La declaración selecciona orientación, no acredita una compilación ni una toolchain disponible.

## Qué versión y módulo gobiernan la tarea

Lee go.mod, go.sum, go.work si existe y la configuración de CI del módulo afectado.
Contrasta la directiva `go`, la sugerencia `toolchain`, reemplazos locales, vendoring
y plataforma objetivo. Un workspace no convierte todos sus módulos en un solo paquete.
Ejecuta las comprobaciones desde el módulo correspondiente o respeta el workspace
que usa su CI. No cambies versiones para hacer que un ejemplo compile.

Comprueba la toolchain disponible antes de recomendar APIs nuevas. `GOTOOLCHAIN=auto`
puede descargar otra versión; si no se han autorizado descargas, usa la toolchain
local y comunica una incompatibilidad. Tampoco instales linters ni regeneres
dependencias o código como efecto implícito de aplicar esta guía.

| Versión del lenguaje o toolchain | Criterio |
|---|---|
| Semántica anterior a Go 1.22 | Una clausura asíncrona puede capturar la misma variable de bucle; pasa el valor o crea una copia por iteración |
| Semántica Go 1.22 o posterior | Las variables declaradas por el bucle tienen identidad por iteración; no añadas `tt := tt` por rutina. Variables externas reutilizadas con `=` siguen compartidas |
| Toolchain y mínimo compatibles con Go 1.24 o posterior | Puedes usar `for b.Loop() { ... }` en benchmarks; conserva `b.N` cuando el proyecto soporte una versión anterior |

## Qué comprobar al implementar y revisar

| Situación | Decisión | Evidencia útil |
|---|---|---|
| Interfaces | Declara contratos pequeños donde se consumen; usa tipos concretos cuando no haga falta una abstracción | El caller puede probar su contrato sin un framework de mocks nuevo |
| Receptores y valor cero | Decide mutabilidad y propiedad por tipo; no copies tipos que contienen mutex en uso | Construcción y llamadas respetan invariantes, incluso con valores vacíos |
| Errores | Devuelve fallos con contexto; usa `%w` cuando el caller deba conservar su identidad y `errors.Is`/`errors.As` para distinguirlos | El caller observa el fallo original sin comparar textos; cancelación no se informa como éxito |
| Interfaces y nil | Un puntero nil dentro de una interfaz no equivale a una interfaz nil | El retorno `error` vale nil en éxito; no uses un puntero de error tipado nil para representar éxito |
| Recursos | Cierra archivos, cuerpos HTTP y filas al terminar su uso; evita acumular `defer` dentro de un bucle largo | El fallo intermedio también libera recursos; cada iteración conserva un presupuesto acotado |
| Slices, maps y buffers | Explica aliasing y duración; no devuelvas memoria que vuelve a un pool y puede reutilizarse | Una operación posterior no altera un resultado ya entregado |
| Goroutines | Cada goroutine tiene dueño, señal de salida y espera de terminación; limita el trabajo en vuelo | Cancelar el padre permite terminar y esperar sus workers, incluso con cola llena |
| Contextos | Propaga `context.Context` hasta E/S y esperas; libera contextos derivados con su cancelación | El test observa cancelación real y finalización, no solo que se llamó a cancel |
| Canales | Define quién envía y quién cierra; coordina productores antes de cerrar y permite cancelar envíos/recepciones bloqueados | No hay doble cierre, envío tras cierre ni espera infinita por una salida de error |
| Estado compartido | Protege invariantes con sincronización apropiada; no uses sleeps como exclusión | Los escenarios concurrentes pasan con race detector cuando la plataforma lo soporta |
| HTTP, si aplica | Reutiliza clientes/transports, propaga contexto y configura timeouts según el servicio | Servidor lento, cuerpo incompleto y cancelación respetan el presupuesto acordado |

Un contexto cancelado no espera goroutines por sí mismo. Una cola con capacidad
finita tampoco limita los productores si se crea una goroutine por cada envío.
Elige el límite y el mecanismo de espera del proyecto; no introduzcas una librería
de concurrencia sin necesidad. Un timeout remoto puede dejar un resultado incierto:
comprueba idempotencia o reconciliación antes de repetir una escritura.

## Qué pruebas ejecutar

Usa la suite existente. En tests por tablas y subtests, crea datos independientes;
`t.Parallel()` no autoriza compartir estado mutable ni depender del orden de ejecución.
Los tests de cancelación usan señales observables y plazos acotados, no sleeps
arbitrarios como prueba de que un worker terminó. Un detector de carreras limpio
solo cubre los caminos ejecutados, no demuestra ausencia de carreras en toda la aplicación.

| Necesidad | Comando de referencia | Límite |
|---|---|---|
| Un rojo concreto | `go test ./paquete -run '^TestCriterio$' -count=1 -v` | Sustituye paquete y nombre por los del proyecto; confirma que el test se ejecutó |
| Suite del módulo | `go test ./... -count=1` | No afirma haber recorrido otros módulos del workspace |
| Comprobaciones estáticas existentes | `go vet ./...` y `gofmt -l .` | Formatea solo archivos del cambio; no instala analizadores adicionales |
| Carreras | `go test -race ./...` | Requiere una plataforma/toolchain compatible y los requisitos de cgo; si falta soporte, informa del check no ejecutado |
| Cobertura | `go test ./... -coverprofile=coverage.out` | `unit-tests` y su gate oficial aplican el umbral del proyecto; no impongas 100% universal |
| Benchmark acotado | `go test ./paquete -run '^$' -bench '^BenchmarkCriterio$' -benchmem` | Verifica que se ejecutó; no deduzcas una mejora de una sola muestra |

Prueba límites, errores y finalización de workers. Usa `httptest` para un servicio
HTTP local y dobles por contrato para aislar red o persistencia. Fuzzing, cuando
aporte valor, mantiene semillas reproducibles y un presupuesto explícito; no llama
a servicios reales sin autorización. Medir rendimiento precede a introducir pools
o sincronización adicional. En bucles con `b.N`, evita que una optimización del
compilador elimine el trabajo medido. `b.Loop()` tiene su propia protección;
no traslades mecánicamente patrones antiguos a esa API.

## Fuentes y vigencia

Documentación oficial consultada el 2026-10-31. Contrasta siempre con la versión
del consumidor; estas referencias no fijan una versión mínima global del plugin:

- [Módulos y directivas go/toolchain](https://go.dev/doc/modules/gomod-ref).
- [Selección y descarga de toolchains](https://go.dev/doc/toolchain).
- [Semántica de bucles Go 1.22](https://go.dev/doc/go1.22#language).
- [Benchmarks Go 1.24](https://go.dev/doc/go1.24#new-benchmark-function).
- [Contextos](https://pkg.go.dev/context) y [cliente HTTP](https://pkg.go.dev/net/http#Client).
- [Interfaces y errores nil](https://go.dev/doc/faq#nil_error).
- [Testing y fuzzing](https://pkg.go.dev/testing) y [race detector](https://go.dev/doc/articles/race_detector).
