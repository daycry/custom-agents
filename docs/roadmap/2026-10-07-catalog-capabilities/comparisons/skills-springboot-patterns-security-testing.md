# Spring Boot: patrones, seguridad, TDD y verificación — S260–S263

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **28.045 bytes/979 líneas**, sin recursos locales.
[springboot-patterns-security-testing-reading-evidence.json](springboot-patterns-security-testing-reading-evidence.json).
Nada se ejecutó ni se compiló. Propuestas para T-08.

## Decisión común

Ya fijada en [skills-java-jira-knowledge.md](skills-java-jira-knowledge.md)
(S145/S147): **no se abre especialidad Java hasta que un consumidor declare el
stack**. Entonces S145, S147, las de Quarkus (S222–S225,
[skills-quarkus-family.md](skills-quarkus-family.md)) y estas cuatro piezas se
leen juntas como una sola referencia `java.md` en `stack-practices`. Lo transversal ya tiene dueño:
`backend-practices` (autorización por recurso, errores sin detalle interno,
paginación con orden total, reintentos solo si son seguros), `tdd` (método y,
en `references/by-stack.md`, el comando de un único test JUnit con Maven y con
Gradle), `unit-tests` (cobertura oficial) y la tríada Django (S080–S082) como
precedente de cómo tratar seguridad y verificación de un framework. Las
correcciones de abajo son para ese momento.

## S260 — Patrones de Spring Boot

`10.047 bytes/315 líneas`. Controlador, repositorio, servicio transaccional,
DTO con validación, manejador global de errores, caché, asíncrono, registro,
filtros, paginación, reintentos y límite de peticiones con Bucket4j.

| Ejemplo | Adaptación |
|---|---|
| `handleGeneric` dice «Log unexpected errors» en un comentario y no registra nada | El error se pierde; registrar con identificador de correlación (backend-practices) |
| `@Transactional`, `@Cacheable` y `@Async` sin advertencia de proxy | Una llamada desde la propia clase no pasa por el proxy y la anotación no se aplica |
| `withRetry` reintenta cualquier excepción, sin aleatoriedad en la espera | Solo errores transitorios de operaciones idempotentes, con tope y jitter |
| Mapa de buckets por IP en memoria, sin expulsión | Crece con cada IP distinta; detrás de un proxy sin configurar, todos comparten un bucket (la propia pieza lo admite) |
| `Sort.by("createdAt").descending()` | Sin desempate el orden no es total y las páginas repiten o pierden filas |
| `EntityNotFoundException` en el servicio con caché | Ya señalado en S145: significado distinto en JPA |

## S261 — Seguridad con Spring Security

`8.133 bytes/273 líneas`. Filtro JWT, `@PreAuthorize`, validación, SQL
parametrizado, `PasswordEncoder`, CSRF, secretos, cabeceras, CORS, límites de
peticiones, dependencias, registros y subidas.

| Ejemplo | Adaptación |
|---|---|
| «BAD»: concatenación dentro de `@Query(value = "…'" + name + "'")` | No compila (los atributos de una anotación son constantes); el riesgo real es concatenar en `EntityManager.createNativeQuery` o `JdbcTemplate` |
| Recomienda cookies `httpOnly` para sesión y desactiva CSRF «para APIs con Bearer» | Si el token viaja en cookie, la API no es Bearer puro y CSRF debe seguir activo |
| Filtro JWT propio que no trata el fallo de `authenticate` | Preferir el resource server de Spring Security, que la propia pieza nombra |
| `.xssProtection(...)` en las cabeceras | Cabecera obsoleta, como en S080; la defensa es escape más CSP |
| Mismo mapa de buckets sin expulsión que S260 | Misma corrección |

## S262 — TDD con Spring Boot

`3.786 bytes/159 líneas`. Ciclo rojo-verde-refactor con JUnit 5, Mockito,
MockMvc, `@DataJpaTest`, Testcontainers y JaCoCo.

**Comparación.** El método es de `tdd`; no se crea otro. Correcciones: el
fragmento de JaCoCo solo tiene `prepare-agent` y `report`, sin el objetivo
`check` con regla, así que «Enforce coverage» no hace cumplir nada; el 80 % fijo
choca con `tests.coberturaMinima` declarado por proyecto; el test de integración
envía `endDate` 2030-01-01 a un DTO con `@FutureOrPresent` (S260) y empezará a
fallar en esa fecha; `@MockBean` está en desuso a favor de `@MockitoBean` desde
Spring Boot 3.4 (contrastar con la versión del consumidor); y `findByName` no
existe en el repositorio mostrado.

## S263 — Bucle de verificación

`6.079 bytes/232 líneas`. Compilación, análisis estático, tests con cobertura,
escaneo de dependencias y secretos, formato y revisión del diff, con informe
LISTO/NO LISTO.

**Comparación.** Igual que S082: un segundo bucle de verificación duplicaría a
`qa` (`qa-gate`), `unit-tests`, `adversarial-review`, `nemesis` y
`dependency-upgrade` (ADR-011). Correcciones: `@WebMvcTest` se presenta «con
contexto completo» y es un corte del contexto web; `mvn jacoco:report # verify
80%+` genera el informe pero no verifica; `spotless:apply` modifica ficheros
dentro de una verificación; el grep de secretos mira solo `*.java` y `*.yml` en
uno de sus dos comandos; y «Security: PASS» a partir de greps no es un veredicto.

**Destino S260–S263:** ninguno hasta que un consumidor declare Java. Entonces,
`java.md` con las correcciones de esta ficha y de S145; los comandos Maven y
Gradle como entradas de los dueños (como S082); y una tarea aparte para que
`coverage-gate.py` lea el informe de JaCoCo, hoy fuera de sus stacks
(pytest/jest/vitest/phpunit/go).
