# Revisores y resolutor JVM (Java, Kotlin) — A035–A037

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres definiciones completas: **26.215 bytes/485 líneas**. [agents-java-kotlin-reading-evidence.json](agents-java-kotlin-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Regla común: Java y Kotlin son stacks **sin consumidor** (`skills-destinations.md`,
«Regla de stacks y dominios sin consumidor»; D-122 Kotlin, D-126 Java, D-111
parsers de cobertura, todos aparcados). Lo transversal de los tres ya tiene
dueño. Se comparan responsabilidad, permisos y salida, no nombres.

## A035 — java-reviewer

`13.333 bytes/190 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisor de cambios Java que detecta Spring Boot o Quarkus por el fichero de build
y aplica prioridades CRITICAL→MEDIUM (seguridad, errores, capas, JPA/Panache,
MongoDB, concurrencia, pruebas, máquinas de estado) con veredicto Approve/Warning/Block.

**Comparación.** El ejecutor es `reviewer` (`agents/reviewer.md:39-50`, mismos
permisos de solo lectura) por las lentes de `adversarial-review`. La seguridad
Java la cubre la Lente C con `cybersecurity/references/language-patterns/java.md`
(deserialización, SpEL, JNDI, Actuator expuesto, asignación masiva vía
`@ModelAttribute`). Idempotencia antes de mutar, reintentos con jitter, colas
sin pérdida y paginación acotada están en `backend-practices`
(`contracts-data.md:20,22,26`, `cache-jobs.md:60-61`). El N+1 es la Lente D. Lo
que el plugin **no** cubre son las reglas propias de Spring, Quarkus, Panache y
JPA, y eso queda aparcado como `java.md` (D-126, con S145/S147/S222–S225/S260–S263).
Diferencia de método: la fuente mezcla estilo (nombres de tests, `instanceof`
con cast, `StringBuilder`) con defectos y bloquea por cualquier HIGH. `reviewer`
excluye el estilo (`agents/reviewer.md:41-43,94`). Defectos:

| Punto | Problema |
|---|---|
| «If any CRITICAL security issue is found, stop and escalate to `security-reviewer`» (l.66) | Parar la revisión pierde el resto de hallazgos; el propio enruta con «Fuera de mi lente» sin parar (`reviewer.md:87,93`) |
| `@Transactional` «not … repository» (l.84) frente a «any `@Query` that mutates requires `@Modifying` + `@Transactional`» (l.95) | Contradicción: la consulta modificadora vive en el repositorio y la propia pieza le exige la anotación allí |
| `.get()` sobre `Optional` como CRITICAL (l.70) e idempotencia comprobada tarde como MEDIUM (l.145) | Escala invertida: lo segundo duplica cobros; lo primero es un `NoSuchElementException` |
| Paso 2: `./mvnw verify` / `./gradlew check` antes de revisar (l.35-37); `dependency-check:check` (l.170) | El wrapper descarga la distribución y ejecuta todo el build del repositorio; el chequeo de CVE descarga la base NVD. `reviewer` ejecuta el test que cita el criterio (`reviewer.md:71-73`), no el build completo |
| «MUST BE USED for all Java code changes» (l.3) | Disparador proactivo total que compite con la revisión de dos lentes |

**Destino:** **Sin destino** (Java sin consumidor, D-126). Si un consumidor lo
declara, la tabla anterior acompaña a `java.md`.

## A036 — kotlin-build-resolver

`5.203 bytes/127 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Arregla errores de compilación Kotlin y Gradle con cambios mínimos: tabla
error→causa→arreglo, comandos de diagnóstico y parada tras 3 intentos.

**Comparación.** Escribir código es de `implementer`, el único agente que lo
toca (`agents/implementer.md:6`, ADR-011). Un error que persiste lo trata
`debug-root-cause` (4 fases con evidencia, `SKILL.md:14-50`), que `/dev-cycle`
invoca al tercer rojo (`commands/dev-cycle.md:413`). El tope de 3 intentos y
«arreglar la causa, no suprimir el síntoma» coinciden con la cadena. Con Write y
Edit, el agente sería un **segundo implementador** sin ledger, sin `Verificación`
y sin `guardrail-check.py`: duplica una fase. Lo que el plugin no tiene, la tabla
de errores del compilador Kotlin y los comandos de Gradle, es del stack aparcado
(D-122; Kover en D-111). Defectos:

| Punto | Problema |
|---|---|
| «`'when' expression must be exhaustive` → Add missing branches or `else`» (l.58) | Un `else` sobre una `sealed class` anula la exhaustividad que pide su gemelo `kotlin-reviewer` (A037 l.109): la próxima subclase ya no da error |
| Bloque «Kotlin Compiler Flags» con `allWarningsAsErrors = true` (l.89-97) | Activarlo en un build roto multiplica los errores; contradice «Surgical fixes only» (l.101) |
| `./gradlew clean && rm -rf .gradle/build-cache/` (l.75), `--refresh-dependencies` (l.72) | Borrado y red sin confirmación; `implementer` pide el OK del usuario para borrados y red (`implementer.md:90`) |

**Destino:** **Sin destino**: el método ya está en `implementer` y
`debug-root-cause`, y Kotlin queda aparcado (D-122).

## A037 — kotlin-reviewer

`7.679 bytes/168 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisor Kotlin para Android, KMP y Compose: fronteras de módulos, corrutinas y
Flow, recomposición, fallos de Android y seguridad de la plataforma, con
resumen por severidad y veredicto.

**Comparación.** El ejecutor es `reviewer`, con los mismos permisos. La
seguridad Android tiene filas en `cybersecurity/references/language-patterns/swift-kotlin.md`
(componente exportado l.60, `addJavascriptInterface` l.54). La regla «no tragarse
`CancellationException`» equivale a la de `CancelledError` en
`stack-practices/references/python.md:5-15`: está escrita para Python y, para
Kotlin, espera al consumidor (D-122; S149–S153 en `skills-kotlin-family.md`).
Defectos:

| Punto | Problema |
|---|---|
| «stop the review and hand off to `security-reviewer`» (l.48 y l.126) | El mismo corte que en A035 |
| Ejemplo `remember(item.id) { { … } }` (l.95-100) | Con el salto fuerte (*strong skipping*) de las versiones recientes del compilador de Compose, las lambdas se memorizan solas: es un consejo que depende de la versión y la pieza no lo dice. Verificar contra la versión del consumidor |
| «Only report issues with >80% confidence» (l.56) | Umbral sin medida; `reviewer` exige `fichero:línea` y un escenario concreto (`reviewer.md:89-90`) |
| La lógica de negocio en el ViewModel se gradúa CRITICAL (l.62-64) | Una preferencia de arquitectura bloquea igual que una credencial en logs |

**Destino:** **Sin destino** (D-122 aparcado). Las correcciones acompañan a la
especialidad cuando un consumidor declare Kotlin.
