# Quarkus: patrones, seguridad, TDD y verificación — S222–S225

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **70.186 bytes/2.484 líneas**, sin recursos locales.
[quarkus-family-reading-evidence.json](quarkus-family-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

Se confirma lo fijado en [skills-java-jira-knowledge.md](skills-java-jira-knowledge.md):
**no se abre especialidad Java/Quarkus** en `stack-practices` hasta que un
consumidor declare el stack. Cuando ocurra, estas cuatro piezas se leen junto con
S145, S147 y S260–S263 como una única referencia `java.md`, con las correcciones
de abajo. Lo transversal ya tiene dueño:

| Tema | Dueño propio |
|---|---|
| Autorización por recurso, idempotencia, outbox, paginación estable | `backend-practices/references/contracts-data.md` |
| Comando de un solo test Maven/Gradle | `tdd/references/by-stack.md` (ya tiene las filas JUnit) |
| Umbral de cobertura con la herramienta oficial | `unit-tests` (`tests.coberturaMinima`) |
| Readiness y contenedores | `delivery-practices` |
| OWASP, dependencias vulnerables, DAST local | `nemesis` con `cybersecurity` |

Dos huecos que conviene registrar para ese momento, no antes: `coverage-gate.py`
no detecta JaCoCo y `deps-inventory.py` no lee `pom.xml` ni `build.gradle`.

## S222 — Patrones Quarkus con Camel y Panache

`21.520 bytes/723 líneas`. Servicios CDI con Lombok, servicio de eventos,
rutas Camel hacia RabbitMQ, recursos REST, repositorios Panache, mapeo de
excepciones, `CompletableFuture`, caché, configuración YAML por perfil y salud.

| Ejemplo | Adaptación |
|---|---|
| `process()` publica a la cola y registra eventos dentro de `@Transactional` | El mensaje sale aunque la transacción revierta, y la propia pieza pide «evitar operaciones asíncronas dentro de transacciones»: outbox o publicar tras el commit (ya en `contracts-data.md`) |
| `createErrorEvent` seguido de `throw WebApplicationException` en el mismo método transaccional | La excepción revierte la transacción y con ella el evento de error que se quería guardar |
| `GenericExceptionMapper<Exception>` | También casa con `WebApplicationException`; según la implementación, los 400/404 lanzados por el servicio salen como 500. Mapear solo lo no controlado |
| `list(page, size)` sin tope de `size`, sin orden y devolviendo entidades | Tope, orden total estable y DTO (fila de paginación de `contracts-data.md`) |
| `.log("Publishing message to RabbitMQ: ${body}")` | Vuelca el payload completo al log; redactar |
| `uploadOriginalFile` consume en otro hilo un `InputStream` recibido | El llamante puede cerrar el flujo de la petición antes de que corra la tarea |
| `@CacheResult` sobre un método que devuelve `Optional` | Cachea también el vacío: un documento creado después sigue «sin existir» hasta invalidar |
| Perfil `%test` con H2 y PostgreSQL en el resto | Mismo defecto que SQLite en S081: no reproduce el motor; usar el motor real |

## S223 — Seguridad en Quarkus

`12.401 bytes/468 líneas`. JWT/OIDC, `@RolesAllowed`, comprobación de propiedad
con `SecurityIdentity`, validación, consultas parametrizadas, BCrypt, CORS,
cabeceras, límites de peticiones, auditoría y secretos.

Aporta una regla útil y general: **no usar `X-Forwarded-For` directamente** para
identificar al cliente; usar la dirección real tras un proxy de confianza o la
identidad autenticada. Va a la sección de límites propuesta para S234 en
[skills-rails-redis-rust.md](skills-rails-redis-rust.md).

| Ejemplo | Adaptación |
|---|---|
| `CustomAuthFilter.validateToken` devuelve `true` | Plantilla que acepta cualquier token si se copia; además duplica la verificación JWT/OIDC ya configurada |
| Ejemplo «malo» con `@Query(... nativeQuery = true)` | Es una anotación de Spring Data, no de Panache |
| `RateLimitFilter` | Sin `@Provider` no se registra; mapa de limitadores por IP sin cota de memoria y por réplica: un contador por proceso no es un límite global (ya anotado en [skills-iteration-backend-benchmarks.md](skills-iteration-backend-benchmarks.md)) |
| `X-XSS-Protection: 1; mode=block` | Cabecera obsoleta; mismo criterio que en S080 |
| `authenticate()` no calcula hash cuando el correo no existe | La diferencia de tiempo revela qué correos están registrados |

## S224 — TDD en Quarkus

`25.526 bytes/812 líneas`. Pruebas unitarias con Mockito y `@Nested`, rutas
Camel con `AdviceWith`, servicio de eventos, `CompletableFuture`, recursos con
REST Assured, integración y JaCoCo.

**Comparación.** `tdd` es la fuente única del ciclo; nada nuevo de método. Los
ejemplos tienen fallos que una referencia futura no debe heredar:

| Ejemplo | Adaptación |
|---|---|
| Test «fallo de persistencia → `createErrorEvent`» | El servicio de S222 solo crea ese evento al fallar la validación; y en ejecución real el evento se revierte con la transacción. Con mocks pasa un comportamiento que no existe |
| Test de propagación de `LogContext` | Captura el contexto en el mismo hilo y antes de ejecutar la tarea: no prueba propagación |
| Test de fallo de S3 espera `"S3 unavailable"` en el mensaje | El servicio envuelve el error en `StorageException("Upload failed", e)`; el mensaje de la `CompletionException` no contiene el texto esperado |
| `@Transactional` en un test que crea por HTTP con REST Assured | La petición corre en otro hilo y otra transacción: el rollback del test no limpia lo creado |
| «Verificar siempre las interacciones» | Acopla el test al diseño; el plugin prioriza aserciones sobre el resultado (`tdd/references/anti-patterns.md`) |
| Cobertura 80 % de líneas y 70 % de ramas | Ya existe `tests.coberturaMinima` con herramienta oficial; no imponer cifras |

## S225 — Bucle de verificación Quarkus

`10.739 bytes/481 líneas`. Diez fases: build, análisis estático, tests y
cobertura, seguridad, nativo, carga con k6, salud, imagen, configuración y
documentación, con script y workflow.

**Comparación.** Misma decisión que S082 en
[skills-django-security-testing-verification.md](skills-django-security-testing-verification.md):
un segundo bucle de verificación duplicaría a `qa` (ADR-011). Solo valdrían los
comandos de solo lectura como entradas de sus dueños.

| Ejemplo | Adaptación |
|---|---|
| `mvn clean verify -DskipTests` y después `mvn clean test` | El segundo `clean` borra lo construido: compila dos veces |
| OWASP ZAP con `docker run` contra la API | Aunque apunte a `localhost`, el DAST es de `nemesis` y pasa por su guardarraíl; un contenedor lanzado aparte no |
| `-Dsonar.login=${SONAR_TOKEN}` en la línea de órdenes | El token queda visible en la lista de procesos |
| «Arranque < 100 ms», «sin TODO en el PR» | Umbrales sin medición; registrar lo medido |
| Informe con casillas marcadas | Una casilla sin la salida de la ejecución no es verificación (criterio de S082) |

**Destino (las cuatro):** anotación para la futura `java.md`; **sin especialidad
ahora**.
