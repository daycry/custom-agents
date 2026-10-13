# Familia Kotlin: corrutinas, Exposed, Ktor, idioma y pruebas — S149–S153

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **89.275 bytes/3.232 líneas**, sin recursos locales.
[kotlin-family-reading-evidence.json](kotlin-family-reading-evidence.json).
Nada se ejecutó ni se compiló. Propuestas para T-08.

## Decisión común

`stack-practices` cubre PHP/CodeIgniter, Python y React. Igual que con Java
(S145–S148) y Go (S116–S117), **no se abre especialidad Kotlin mientras ningún
consumidor declare el stack**. Hay una tensión con fichas anteriores: S013
(arquitectura por capas Android/KMP) y S045 (Compose) ya propusieron una
especialidad opcional `kotlin-practices` con referencias `layered-architecture.md`
y `compose-ui.md`, como S064/S086 hicieron con `dotnet-practices`. T-08 debe
resolverlo en un solo sentido para todos los stacks sin consumidor; si se abre,
estas cinco piezas se leen junto a S013 y S045 como
`async.md`, `persistence.md`, `server-ktor.md`, `idioms.md` y `testing.md`, con
las correcciones de abajo. Lo transversal ya tiene dueño: N+1, paginación con
orden total, errores con identificador estable y autorización por recurso en
`backend-practices/references/contracts-data.md`; RED-GREEN-REFACTOR en `tdd`
(su `by-stack.md` ya trae la fila JUnit/Gradle); cobertura en `unit-tests`.

Una limitación propia que conviene anotar: `coverage-gate.py` detecta pytest,
jest/vitest, phpunit y go. Un proyecto Gradle con Kover sale con exit 2 (sin
stack), de modo que el umbral de `tests.coberturaMinima` no se aplicaría a
Kotlin hasta añadir el parser de su informe.

## S149 — Corrutinas y Flow (Android/KMP)

`7.869 bytes/285 líneas`. Concurrencia estructurada, `supervisorScope`,
`StateFlow` con `WhileSubscribed`, operadores, `SharedFlow` para eventos,
dispatchers, cancelación cooperativa y pruebas con Turbine.

| Ejemplo | Corrección |
|---|---|
| `.catch { emit(emptyList()) }` tras `flatMapLatest` en el buscador | `catch` termina el flujo aguas arriba: tras el primer error el buscador deja de reaccionar a nuevas consultas. Capturar dentro de `flatMapLatest` |
| `MutableSharedFlow<Effect>()` sin buffer para eventos de una vez | Con `replay = 0` y sin colector activo el evento se pierde (rotación, segundo plano); decidir buffer o canal según el contrato |
| Prueba de ViewModel con `advanceUntilIdle()` | `viewModelScope` usa `Dispatchers.Main`; sin `Dispatchers.setMain(...)` con un dispatcher de prueba el test no controla ese hilo |
| `flow { dao.observeAll().map{…}.collect { emit(it) } }` | Envoltura innecesaria: basta `.map` sobre el flujo del DAO |

La regla «no capturar `CancellationException`» es correcta y contradice a S013
y S152, que usan `runCatching` en funciones suspendidas.

## S150 — Exposed, HikariCP y Flyway

`22.119 bytes/720 líneas`. Tablas DSL y DAO, CRUD, joins, agregados, subconsultas,
paginación, lotes, upsert, columnas JSONB, repositorio y pruebas con H2.

| Ejemplo | Corrección |
|---|---|
| `transferFunds` bajo el comentario «transacciones anidadas con savepoints» | No hay anidamiento; `balance` no existe en la entidad; no valida importe positivo ni saldo; con `READ_COMMITTED` dos transferencias concurrentes pierden actualizaciones: bloqueo de fila o actualización atómica |
| Pruebas en H2 `MODE=PostgreSQL` sobre una columna `jsonb` con `PGobject` | H2 no reproduce ese tipo; `contracts-data.md` ya dice que una base distinta no demuestra el comportamiento del motor real |
| `baselineOnMigrate(true)` por defecto | Marca como migrada una base no vacía desconocida; solo como decisión explícita |
| Paginación por `createdAt DESC` sin desempate | Orden total estable (fila «Paginación» de `contracts-data.md`) |
| `resultedValues!!` en `create` | Contradice la regla «evitar `!!`» de S152 |
| `UsersTable` definida dos veces | Ejemplo no compilable tal cual |

## S151 — Servidor Ktor

`19.536 bytes/690 líneas`. Estructura, routing DSL, serialización, JWT,
StatusPages, CORS, Koin, validación, WebSockets y `testApplication`.

| Ejemplo | Corrección |
|---|---|
| `exception<IllegalArgumentException>` → 400 con `cause.message` | Cualquier `require` interno o fallo de librería se presenta como error del cliente y filtra el mensaje; errores de validación con identificador estable, el resto 500 redactado |
| `ContentTransformationException` → 400 con `cause.message` | Expone detalles del parser |
| `GET /users` público; `PUT`/`DELETE` solo autenticados | Lista datos personales sin control y cualquier usuario autenticado modifica a otro: falta autorización por recurso |
| `UserRoutesTest` espera 201 en `POST /users` sin token y `AuthenticatedRoutesTest` espera 401 en la misma ruta | Las dos versiones de `userRoutes()` se contradicen |
| `response.body<ApiResponse<…>>()` con el `client` por defecto | Sin `ContentNegotiation` en el cliente de prueba no deserializa |
| `configureDI()` definida dos veces | Ejemplo no compilable tal cual |
| `prettyPrint = true` | Opción de desarrollo, no de producción |

## S152 — Patrones idiomáticos de Kotlin

`18.951 bytes/712 líneas`. Nulabilidad, inmutabilidad, clases selladas y de
valor, funciones de ámbito, extensiones, corrutinas, delegación, DSL, secuencias,
Gradle y errores con `Result`.

| Ejemplo | Corrección |
|---|---|
| `user?.email ?: "unknown@example.com"` como «bueno» | Inventa un dato y oculta que el usuario no existe |
| `connection.run { prepareStatement(sql); executeQuery() }` | Descarta la sentencia y llama `executeQuery` sobre la conexión |
| Anti-patrón «fuga de tipos de plataforma» | El bloque «malo» muestra código correcto |
| `createUser` con `runCatching` en función suspendida | Captura la cancelación (contradice S149) |
| `observeUsers` con `.catch { emit(emptyList()) }` tras un sondeo infinito | Un error detiene el sondeo para siempre y se confunde con «no hay usuarios» |
| `require('@' in value) { "Invalid email: $value" }` | El dato personal acaba en excepciones y logs |
| `Result.Loading` dentro del resultado de dominio | Mezcla estado de UI con el resultado de la operación |

Las versiones de Gradle (Kotlin, Ktor, Exposed, Kotest) no se contrastaron.

## S153 — Pruebas con Kotest, MockK y Kover

`20.800 bytes/825 líneas`. Ciclo TDD, estilos de spec, matchers, MockK,
`runTest`, pruebas de Flow, propiedades, datos tabulados, extensiones, Kover y CI.

**Comparación.** Coincide con `tdd` en el ciclo y difiere en la evidencia del rojo:

| Ejemplo | Corrección |
|---|---|
| Rojo con `NotImplementedError` de un `TODO()` | Es el «rojo por la razón equivocada» de `tdd`: debe fallar el assert del criterio |
| El verde añade una regex que ningún test exige | Más allá del mínimo; o se añade el caso o se quita |
| `queries.emit(...)` tras `launch { collect }` en `runTest` | Con el dispatcher estándar el colector aún no se ha suscrito y las emisiones se pierden: `runCurrent()` o dispatcher no confinado |
| `advanceTimeBy(1000)` y `completed shouldBe true` | Las tareas programadas exactamente en ese instante necesitan `runCurrent()` |
| `every { repository.findById(...) }` sobre una función que otros ejemplos tratan como `suspend` | `coEvery`/`coVerify` |
| Objetivos 100/90/80 % por tipo de código | Umbral del proyecto (`tests.coberturaMinima`), no universal |
| `codecov/codecov-action@v5` por etiqueta | SHA completo, como se anotó para acciones de GitHub en S075 |

**Destino S149–S153:** sin especialidad mientras no haya consumidor; las tablas
de arriba quedan como correcciones para entonces. Anotar en `unit-tests` que
Gradle/Kover no está entre los stacks de `coverage-gate.py`.
