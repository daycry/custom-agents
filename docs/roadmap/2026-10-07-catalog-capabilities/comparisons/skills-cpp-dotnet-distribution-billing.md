# Comparación de C++, pruebas .NET, distribución y soporte de facturación

Fichas S061–S065 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Cinco cuerpos completos:
48.826 bytes/1.635 líneas; cero recursos locales. El registro
[cpp-dotnet-reading-evidence.json](cpp-dotnet-reading-evidence.json) conserva
hashes, rangos de callers y contrapartes propias, reutilizaciones verificadas,
14 contrastes documentales oficiales y una lectura HTTP 404 diferenciada
de su sustituto válido. [tasks.md](../tasks.md) conserva el progreso.

Son destinos propuestos para T-08, no altas de producción. No se ejecutaron
fragmentos, comandos, agentes, builds, tests, collectors ni servicios del
corpus. No se instalaron librerías ni se publicaron mensajes, generaron
sesiones de portal o modificaron suscripciones/reembolsos. Tokens y latencia
son null. Los casos de activación son checks estáticos, no evals ejecutadas;
los callers leídos parcialmente no cuentan como otras piezas evaluadas.

## S061 — C++ moderno con recursos, invariantes y concurrencia explícitos

**Identidad.** SHA-256
`f870b47d3493b0ad0b6e3808a679ac3c429b60f03193af6c9dc0e0d9e6981436`;
22.291 bytes/724 líneas; cero recursos locales.

**Contrato y contenido útil.** Guía C++17/20/23 para implementar, revisar y
refactorizar. Conserva ownership/RAII, tipos de dominio, unidades, parámetros
por valor/const&, resultado compuesto, Rule of Zero/Five, destructores de
bases, inicialización, conversiones, estrategia de errores, observadores
no propietarios, const correcto, sincronización y profiling. Incluye
interfaces, conceptos, librería estándar, enumeraciones, headers y nombres.
Excluye C legacy y adapta hardware/embedded cuando haya restricciones reales.

**Correcciones y contexto.**

- La guía mezcla niveles de lenguaje: string_view/scoped_lock requieren
  C++17, conceptos/ranges C++20 y el caller C009 usa expected, de C++23.
  A013 sugiere clang-tidy con `-std=c++17`; no valida indiscriminadamente
  ejemplos C++20. La versión viene del proyecto/toolchain, no del nombre
  de una guía ni de un flag copiado.
- Buffer usa movimientos por defecto: el unique_ptr del origen queda vacío,
  pero su size no se pone a cero. Su copia posterior usa ese size y pointer.
  Necesita definir estado/precondiciones después de mover, mantener el
  invariante o restablecerlo; RAII evita fugas, no demuestra semántica válida
  de todos los métodos. El factorial tampoco comprueba dominio ni overflow;
  no es una función general segura por ser constexpr/noexcept.
- `transfer` adquiere dos mutex sin tratar el caso de que ambas cuentas
  sean el mismo objeto. El comentario deadlock-free no cubre mutex aliasados
  ni valida importe/invariantes. La cola bloqueante no define cierre,
  cancelación ni lifetime del consumidor; es un ejemplo de espera con
  predicado, no una cola de producción completa.
- `std::integral` y random_access_range por sí solos no establecen dominio
  matemático ni ordenabilidad de los elementos. Preservar precondiciones,
  restricciones y casos límite antes de reutilizar esos ejemplos.
- La prohibición de miembros const/referencia y el Sensor con const string
  muestran una decisión que necesita contexto: asignación/move e identidad
  estable no se resuelven con un sí/no universal. La convención de nombres,
  excepciones y elección de containers respeta el contrato del repositorio.
  Punteros indirectos no son siempre un defecto si el dominio exige identidad
  estable, polimorfismo o storage específico; rendimiento se mide.

Las Core Guidelines C.64 y CP.21 explican estado después de mover y locks
de varios mutex. Son guías de diseño con precondiciones, no un certificado
de que cada snippet las cumple.
[Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#rc-move-semantic).

**Comparación propia y decisión.** `stack-practices` cubre PHP/Python/React;
el selector tiene cuatro stacks cerrados y no detecta C++. TDD, revisión,
qa y research-first ya aportan método, evidencia y adopción de herramientas.
Conservar especialidad opcional `skills/cpp-practices/SKILL.md`, con
`references/ownership-types.md`, `references/lifetimes-concurrency.md` y
`references/interfaces-build.md`. Guía breve y detalles bajo demanda; mapas
por paquete/versión y rol en T-10, sin imponer un paquete C++ a todo usuario.

A012/A013 y C007/C008 remiten a esta guía. Su lectura de secciones no
evalúa los agentes/comandos completos ni entrega su despacho. El contenido
complementa implementer/reviewer/qa; no crea un rol revisor C++ obligatorio
ni sustituye las lentes del ciclo. Herramientas opcionales usan el
compile_commands/toolchain real, salida y exit completos, sin confundir
`head -50` con evidencia de un build terminado correctamente.

**Activación estática.** «Revisa el ownership de esta clase C++» y «la cola
comparte datos entre threads» entran. «Añade tests gtest» activa S062;
«refactoriza Python» conserva su guía. Pendientes: move/copy del origen,
auto-transfer, límites numéricos, lifetimes, espera/cierre y compilación por
versión. Una checklist o un wrapper RAII no prueba esos comportamientos.

## S062 — Pruebas C++ y diagnóstico con instrumentación real

**Identidad.** SHA-256
`a92fb5da9b7e3cd1b4dee185b3eb9d0a55352af6396bf996d2eef72d683784df`;
9.175 bytes/325 líneas; cero recursos locales.

**Valor específico.** Fixtures gtest, ASSERT para precondiciones y EXPECT
para verificaciones, gmock para interacciones, fakes para estado, CMake/CTest,
filtro de un test, full suite tras el fix, cobertura GCC/Clang, sanitizers y
flakiness. Mantiene clocks inyectados, seeds y temp dirs por test; la
sincronización usa primitivas y esperas acotadas. Fuzzing/property testing
solo cuando el proyecto ya lo soporta, no como instalación universal.

**Defectos comprobados y limitaciones.**

- El stub UserStore siempre devuelve alice; el caso verde demuestra el
  stub, no el almacenamiento real. Add declarado sin implementación produce
  fallo de enlace, que debe distinguirse de un rojo conductual. El harness
  de fuzzing comenta la llamada a ParseConfig y retorna cero; no ejercita
  código del producto.
- gtest_discover_tests consulta el ejecutable compilado. Cross-compiling,
  dependencias runtime y discovery POST_BUILD/PRE_TEST necesitan configuración
  real. La documentación CMake 3.20 ya describe ese límite.
  [GoogleTest en CMake](https://cmake.org/cmake/help/v3.20/module/GoogleTest.html).
- Un filtro sin tests no prueba verde. CTest documenta `--no-tests=error`
  desde 3.26; para la mínima 3.20 del ejemplo se necesita otra comprobación
  compatible del conteo y resultado, sin pasar flags de otra versión.
  [CTest 3.26](https://cmake.org/cmake/help/v3.26/manual/ctest.1.html#cmdoption-ctest-no-tests).
- Los flags de coverage están en example_tests. Cuando el producto vive
  en otra librería, no prueban que esa librería esté instrumentada. Un perfil
  LLVM fijo `default.profraw` no conserva múltiples procesos sin política de
  mezcla; usar identificadores/pool y combinar los perfiles reales. Los
  reportes excluyen lo no instrumentado, así que un porcentaje alto puede
  omitir precisamente el código que interesa.
  [Cobertura LLVM](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html).
- ASan y TSan tienen opciones independientes en el ejemplo; activarlas
  simultáneamente es incompatible en Clang. Versiones, plataforma y flags
  de compilación/link deben elegirse por target y configuración, sin asumir
  que flags GCC funcionan en MSVC. Presets separados y cobertura del target
  evitan un default global que alcance dependencias o no alcance el producto.
  [Sanitizers Clang](https://clang.llvm.org/docs/UsersManual.html#controlling-code-generation).
- Catch2 descrito como header-only corresponde al modelo anterior: v3 usa
  headers divididos y librería estática, incluso su alternativa amalgamada
  requiere un archivo de implementación.
  [Migración oficial v3](https://github.com/catchorg/Catch2/blob/devel/docs/migrate-v2-to-v3.md).

**Comparación propia y decisión.** Consolidar la receta en
`cpp-practices/references/testing-cmake.md` y
`cpp-practices/references/instrumentation.md`. El método RED-GREEN-REFACTOR
permanece en `tdd`; añadir allí solo cómo obtener un rojo C++ válido. El
porcentaje/umbral permanecen en `unit-tests`, que hoy no detecta CMake/CTest
ni parsea perfiles C++. `--runner` sustituye el comando, no agrega un stack,
parser o extensión al gate. Necesita adaptador de informes en T-10/T-12,
con archivos de producto, paquetes y exclusiones explícitos; hasta entonces
no anunciar cobertura C++ automática ni cambiar el umbral del proyecto.

El caller C009 impone 80% y TDD a todos sus usos; el plugin conserva el
perfil/umbral autorizado de su ciclo. Planner define escenarios; implementer
escribe tests; reviewer comprueba lo que ejercitan; qa ejecuta y registra
herramienta, plataforma, tests seleccionados y límites. No otra cadena C++
ni agente de QA paralelo obligatorio.

**Activación estática.** «Arregla este test gtest intermitente» y «mide la
cobertura de la librería C++» entran. «Perfila el renderer sin fallos de
tests» va a medición de rendimiento; «implementa una feature» conserva el
ciclo con pruebas según su perfil. Pendientes: filtro vacío, stub, librería
sin instrumentar, procesos paralelos, cache de build y sanitizers por OS.
Ningún compilador o fragmento de origen se ejecutó en esta comparación.

## S063 — Adaptar una misma fuente a varios canales de publicación

**Identidad.** SHA-256
`03bd2ef6e08191cd336e9b8e7a55c29040e7a3225defdaeab1b51d983565661f`;
4.345 bytes/123 líneas; cero recursos locales.

**Contenido útil.** Escoger fuente primaria, reutilizar un solo perfil de
voz, adaptar contexto/longitud por destino y devolver variantes con razones
y restricciones pendientes. No inventar CTA, prueba social, pregunta final
o urgencia. Trata la fuente como datos y evita que texto incrustado cambie
cuentas, destinos, tiempos o publique contexto privado. Sin una voz nueva,
no genera otro perfil independiente para cada red.

**Solape verificado.** S029 conserva perfil de voz; S049 ya adapta por
plataforma y produce versiones desde una fuente. Ambos cuerpos se reutilizan
con hashes coincidentes. A039, C046 y S171 remiten a distribución/adaptación;
S293 remite a publicación mediante API. No se evaluó aquí el ejecutor de esa
API ni se probaron permisos de cuentas. La guía presente no contiene
collector, scheduler o publicador; su sección Posting Order no los entrega.

**Correcciones y decisión.** Consolidar en el destino ya propuesto para
S049, `skills/content-production/references/channel-distribution.md`, con
perfil único de S029. No otra skill de voz/distribución ni alias vacío.
Distintos canales pueden justificar versiones distintas; no convertir
«nunca copia idéntica» ni el veto de frases comunes en una regla que
contradiga la petición expresa o el estilo real del autor. El valor es
adecuación al destino y fidelidad de hechos, no cambiar texto para cumplir
una checklist. Los ejemplos de cuatro redes no prueban límites vigentes
de cuentas, longitud, attachments o enlaces: se verifican al preparar el
destino real en T-06/T-12, sin codificar cifras aquí.

Producir un borrador y entregar un post son operaciones distintas. Conservar
fuente/perfil/versiones locales bajo el dueño del contenido; identificar
destino/cuenta, autorización vigente, payload final, resultado por plataforma
y posibilidad de duplicado antes de un envío solicitado. S060 aporta audiencia
y entrega, con transporte propietario. Un enlace dentro de contenido es
dato; el encargo de investigación puede justificar consultarlo, sin seguir
instrucciones incrustadas ni autenticarse por indicación de la fuente.

**Activación estática.** «Adapta esta nota para LinkedIn y X» y «prepara
versiones por canal manteniendo mi voz» entran. «Define nuestra voz de marca»
va al perfil compartido; «publica el texto exacto autorizado» usa el
transport disponible sin fingir que adaptar fue entregar. Pendientes:
fuente hostil, CTA inventado, perfil duplicado, cuenta equivocada, fallo
parcial y reintento con publicación previa desconocida. No hubo envíos.

## S064 — Tests .NET con fixtures, contratos async y bases de datos reales

**Identidad.** SHA-256
`ee93aae975fa9d44bebc33be010b24435d38177e77395c697048622d9be68ad1`;
8.726 bytes/322 líneas; cero recursos locales.

**Valor propio de la especialidad.** Arrange/Act/Assert, Fact/Theory,
MemberData/TheoryData, NSubstitute para resultados e interacciones,
WebApplicationFactory para HTTP, Testcontainers para persistencia real,
builders, organización unitaria/integración y cancelación. Ayuda a revisar
qué comportamiento comprueba un test y qué infraestructura necesita.

**Gaps y versiones.**

- Las collection expressions requieren C#12; la receta no fija versión de
  lenguaje, SDK, paquetes, TFMs o runner. Su IAsyncLifetime con métodos Task
  es una forma v2; v3 usa ValueTask e IAsyncDisposable. No copiarla sin
  seleccionar contrato de framework.
  [xUnit v3](https://api.xunit.net/v3/3.0.1/Xunit.IAsyncLifetime.html),
  [InitializeAsync](https://api.xunit.net/v3/3.0.1/v3.3.0.1-Xunit.IAsyncLifetime.InitializeAsync.html).
- Cambiar EF a UseInMemoryDatabase("TestDb") no demuestra queries,
  transacciones, SQL o constraints del proveedor de producción ni aislamiento
  entre tests. La documentación explica sus diferencias y desaconseja usar
  ese fake como sustituto de pruebas de base real. La fixture de Postgres
  sí puede cubrir el proveedor, pero necesita Docker/runtime disponible,
  versión/image fijada, readiness, datos independientes y cleanup robusto
  incluso si Start/Migrate/creación del contexto falla parcialmente.
  [Estrategia de pruebas EF Core](https://learn.microsoft.com/en-us/ef/core/testing/choosing-a-testing-strategy).
- Crear Order devuelve éxito y CustomerId, y el HTTP test solo mira 201 y
  Location; eso no demuestra items persistidos, precio correcto o contenido
  recuperable. Un mock que recibe Add no equivale a una transacción real.
  OrderBuilder empieza con un item por defecto y WithItem añade otro:
  mantener esa semántica explícita para no poblar casos límite sin querer.
- Task.Delay evita bloquear un thread, pero una pausa fija no sincroniza
  trabajo async. Usar señal observable, fake clock o polling con deadline,
  pruebas de cancelación y fallo, no sustituir una sleep por otra espera.
- `dotnet test --collect:"XPlat Code Coverage"` depende del runner y collector.
  La CLI actual distingue VSTest y Microsoft.Testing.Platform; opciones y
  comportamiento se verifican para global.json/csproj/paquetes reales.
  [dotnet test](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test).
- La selección de assertion library es opcional. Fluent Assertions 8+
  declara condiciones diferentes para uso comercial; comprobar versión y
  licencia con research-first antes de adoptar, sin cambiar paquetes ni
  silenciar avisos de licencia por defecto.
  [Documentación de Fluent Assertions](https://fluentassertions.com/introduction).
  La URL con slash final devolvió 404; la canónica sin slash se leyó con 200.

**Cobertura propia y decisión.** Conservar la especialidad opcional en
`skills/dotnet-practices/references/testing.md` y
`references/integration-fixtures.md`, con mapa breve en SKILL.md; reconciliar
las otras guías .NET cuando se evalúen. No imponer xUnit/FluentAssertions/
Testcontainers a un proyecto NUnit/MSTest ni crear otro agente reviewer.
TDD y depuración comparten método; unit-tests conserva cobertura/umbral.
El gate propio solo tiene parsers pytest/jest/vitest/phpunit/go: Clover no
es Cobertura por cambiar nombre y no hay adapter .NET implementado.
Agregar detección/reportes reales en T-10/T-12, con estado no disponible explícito
si faltan runner, collector o infraestructura.

**Activación estática.** «Revisa estas Theory de pedidos» y «quiero probar
el endpoint con la base real» entran. «Diseña los límites de un servicio»
va a arquitectura; «audita seguridad de ASP.NET» conserva nemesis. Pendientes:
versiones v2/v3, datos compartidos, error de setup, cancelación, contrato
serializado, queries reales, runner/collector y cobertura del código afectado.
Los snippets no se compilaron ni se ejecutaron en esta comparación.

## S065 — Resolver un incidente de facturación con estado comprobado

**Identidad.** SHA-256
`4214d79be7d1bcb62587cf6364e96ed3b70b875ec41871ac632e827ef96b370e`;
4.289 bytes/141 líneas; cero recursos locales.

**Contrato y contenido único.** Investigación de un caso de cliente:
identidad, suscripciones/facturas, clasificación de duplicado frente a
compra de equipo, renovación fallida, cancelación, portal o fallo del
producto. Distingue remediación del caso y gap para backlog. Prefiere
interfaces del proveedor cuando cumplen el caso; resume decisión,
acción comprobada, impacto y borrador de seguimiento sin PII innecesaria.

Los callers S091/S092/S102/S284 separan auditoría de código/costes,
correspondencia, análisis económico y notificaciones de remediación concreta.
Se leyeron sus secciones de relación; sus flujos completos, tools y
permisos siguen pendientes en T-03/T-06. El cuerpo de S065 no incluye
adaptador, schema de tool, implementación de portal ni verificación de efectos.

**Gaps que resolver.**

- Email/nombre de usuario orienta la búsqueda, no prueba identidad,
  entitlement o autoridad. Fijar customer/subscription/invoice/charge reales,
  cuenta/proyecto del proveedor, entorno y moneda; separar ambigüedad antes
  de tocar varias suscripciones aparentemente duplicadas.
- Su orden de «acciones reversibles» incluye cancelar y reembolsar.
  No asumir reversibilidad ni que cancelar borra deuda o equivale a devolver
  dinero. La API documenta efectos sobre items/prorations pendientes y
  cobro automático de facturas; la remediación debe comprobar el estado
  resultante y el alcance del efecto solicitado.
  [Cancelación de suscripción](https://docs.stripe.com/api/subscriptions/cancel).
- Un request de refund no es siempre dinero devuelto: el proveedor puede
  tener estado pending/failed. Resultado, referencia y reconciliación del
  estado preceden a «acción realizada» y follow-up. Si hay timeout, comprobar
  el efecto o usar idempotencia disponible antes de repetir una operación.
  [Reembolsos](https://docs.stripe.com/refunds).
- El portal puede ayudar pero tiene límites, incluidos schedules y
  configuraciones de suscripción que no puede actualizar. Verificar el
  control que necesita el cliente antes de darlo por restaurado; habilitar
  portal/configuración o generar una sesión también tiene dueño y scope.
  [Portal de clientes](https://docs.stripe.com/customer-management#limitations).
- La guía salta de clasificar a actuar/enviar sin concretar autorización,
  operación exacta, estado esperado y receipt. Reutilizar autorización
  vigente cuando cubra ese efecto; una petición de análisis no autoriza
  refunds, cancelaciones o mensajes. Redactar no significa enviar, y una
  recomendación no es una acción tomada. Datos de cliente y recibos quedan
  en el sistema/case autorizado; no se promueven a memoria o Git públicos.

**Decisión y destino.** Conservar especialidad opcional
`skills/billing-support/SKILL.md`, con `references/customer-remediation.md`
y `references/provider-state.md`. Reutilizar tools/conector del proveedor
disponible, contract-check de conexión/permiso y S060 para entrega externa;
no implementar otro SDK, motor de dinero o CRM del plugin. S056/S057 tratan
consumo LLM y no son un sustituto de esta operación. Planner registra el
gap de producto si lo hay; un rol técnico no reemplaza al operador financiero
ni convierte el incidente en aprobación automática de memoria.

**Activación estática.** «Investiga estas dos suscripciones del cliente»
y «prepara una propuesta para resolver el cobro duplicado» entran.
«Diseña una API de pagos» va a backend/api-contract; «analiza la estrategia
de precios» se compara en su especialidad; «cuánto gastó el modelo» va a
usage-report. Pendientes: cuenta ambigua, compra real de seats, refund
parcial/pendiente/fallido, timeout, cancelación al final del periodo, portal
incompatible y entrega del seguimiento. Ninguna operación se ejecutó aquí.

## Destinos y comprobación funcional pendiente

| Criterios conservados | Destino propuesto | Evidencia necesaria para entregar |
|---|---|---|
| Ownership, tipos, errores, versión, lifetimes y concurrencia C++ | cpp-practices y tres referencias | TU/toolchain real, invariantes y casos límite ejecutados |
| Fixtures/CTest/gmock, cobertura, sanitizers y flakiness | Dos referencias C++; métodos/gates compartidos | Discovery no vacío, target de producto instrumentado y reports compatibles |
| Fuente, voz única, variantes y entrega por canal | Referencia de content-production/S029/S049 | Variantes fieles y transporte/receipt real cuando se solicite enviar |
| Tests async/HTTP/persistencia/cancelación .NET | Dos referencias dotnet-practices | Framework/runner fijados, datos aislados, cleanup y BD/collector efectivos |
| Identidad, clasificación, estado e incidente de cliente | billing-support y conector del proveedor | Efecto autorizado, estado conciliado, impacto y follow-up con resultado real |

Las especialidades proceden del corpus y se seleccionan cuando el proyecto
las necesita. No son paquetes técnicos nuevos impuestos a todos los usuarios.
Los métodos/gates conservan un dueño; no se duplican TDD, QA, memoria,
aprobación de diseño o ledgers. Selector, manifiestos, versiones, recursos,
exports y docs ES/EN se actualizan juntos en T-08/T-10/T-11/T-12/T-15.
Los paths de destino son propuestas; su mera mención no los entrega.

TDD n/a: prosa/evidencia de comparación. Los checks de hashes, JSON, enlaces,
scope y tests del índice prueban trazabilidad/estructura, no compilación,
cobertura C++/.NET, publicación o eficacia de soporte financiero. La lectura
de documentación no demuestra conexión, permisos o capacidad de los tres
runtimes para ejecutar esas operaciones.
