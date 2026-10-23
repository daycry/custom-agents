# Comandos de build, revisión y TDD por stack (Go, Gradle, Kotlin) — C026–C029, C039–C041

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Siete definiciones completas: **31.001 bytes/1.295 líneas**. [commands-c2-stack-build-review-test-reading-evidence.json](commands-c2-stack-build-review-test-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a los siete.** Ninguno declara `allowed-tools` ni `model`: heredan todas las
herramientas y el modelo de la sesión, también los dos de revisión, que en el plugin serían
de solo lectura (`agents/reviewer.md`, `tools: Read, Grep, Glob, Bash`). Ninguno fija rama,
ledger, base del diff ni `Verificación` por tarea. Son envoltorios de agentes y skills ya
comparados: los resolutores de build en [agents-build-resolvers](agents-build-resolvers.md)
(A028) y [agents-java-kotlin](agents-java-kotlin.md) (A036, A037), el revisor Go en
[agents-stack-domain-reviewers](agents-stack-domain-reviewers.md) (A029) y las skills Kotlin
y Go en [skills-kotlin-family](skills-kotlin-family.md) e
[skills-installer-golang](skills-installer-golang.md). Aquí solo se compara lo propio del
comando: despacho, artefactos, orden, puertas y umbrales.

**Regla aplicada.** Go y Kotlin/Gradle están aparcados hasta que un consumidor declare el
stack (D-125, D-122, D-111 en [skills-destinations](skills-destinations.md)). La decisión de
[commands-workflow-comparison](commands-workflow-comparison.md) («Reparación incremental» →
`implementer`, método de depuración y ciclo; «Revisión reproducible» → método de revisión y
`reviewer`) se respeta: ningún comando por lenguaje añade una fase.

**Dueño por artefacto.** Código corregido → `implementer`, único que toca código
(`docs/agents/ROLES.md:31`). Informe de revisión → la skill `adversarial-review`, que traza
`## Revisión de dos lentes — intento N` en `tasks.md` (`ROLES.md:39`), ejecutada por `reviewer`.
Evidencia del rojo → línea `RED:` del ledger que escribe `implementer` (`skills/tdd/SKILL.md:46-50`).
Gate de cobertura → `coverage-gate.py` de la skill `unit-tests`, opt-in.

## C026 — go-build

`3.792 bytes/183 líneas` · tools: hereda · model: hereda. Despacha a `go-build-resolver`
(l.7) para corregir errores de `go build`, `go vet` y linters uno a uno, recompilando tras cada cambio.

**Intención, artefactos y despacho.** Reparar el build sin refactorizar (l.158-164) con
parada a los tres intentos (l.166-172). Escribe código sin ledger; dueño propio: `implementer`.
**Disparador.** «`go build ./...` falla», «arregla el build tras el pull».
**Escenarios.** (+) «el build está roto tras traer `main`, arréglalo» → `implementer` en la tarea
en curso de `/dev-cycle` (o `quick-implement`) con `debug-root-cause` al tercer rojo. (−)
«sube `golang.org/x/net` a la última» → `dependency-upgrade`, no un reparador de build.

**Comparación.** El método es `agents/implementer.md:89-90` (cambio mínimo, compilar, lint y
tests de la zona) y el bucle acotado de `commands/dev-cycle.md:413`. Defectos propios del comando:

| Línea | Dice | Problema |
|---|---|---|
| 40-41 | `go mod verify` y `go mod tidy -v` como «Diagnostic Commands Run» | `tidy` reescribe `go.mod`/`go.sum`: un diagnóstico que modifica ficheros (mismo defecto que A028) |
| 94 | Arreglo de ejemplo `count, _ := strconv.Atoi(countStr)` | Descarta el error para que compile; su gemelo C027 l.35 lo gradúa CRITICAL («Ignored errors») |
| 156 | `cannot find package` → `go get` | Añade una dependencia como arreglo de build; `implementer.md:90` lo prohíbe y lo deriva a `dependency-upgrade` |

**Destino:** **Sin destino** (Go aparcado, D-125). Ya cubierto por `implementer.md:90` y `debug-root-cause`.

## C027 — go-review

`3.436 bytes/148 líneas` · tools: hereda · model: hereda. Despacha a `go-reviewer` (l.7):
diff de `.go`, vet/staticcheck/golangci-lint, `-race`, `govulncheck` e informe por severidad.

**Intención, artefactos y despacho.** Revisar antes de commit o PR. Salida en el chat con
veredicto PASS/WARNING/FAIL (l.130-136); dueño propio del veredicto: la fusión de
`adversarial-review` (`ROLES.md:39`).
**Disparador.** «revisa mis cambios Go», «antes de commitear».
**Escenarios.** (+) «revísame este diff» en un repo Go → `adversarial-review` (lentes A/B y,
si `review-lens-select.py` lo pide, C/D) ejecutada por `reviewer`. (−) «¿qué CVE tienen mis
dependencias Go?» → `nemesis`, no la revisión del diff (`skills/adversarial-review/SKILL.md:35`).

**Comparación.** Diferencias de procedimiento: no fija base ni rango («modified via `git diff`»,
l.11), mientras que `reviewer` revisa `git diff <base>...HEAD` (`agents/reviewer.md:59`) y el modo
sin plan pide la base (`adversarial-review/SKILL.md:45`); bloquea el merge con un HIGH (l.136),
cuando el plugin obliga a corregir Critical e Important definidos por consecuencia
(`SKILL.md:99-101`); y gradúa estilo (godoc ausente, l.47), que `reviewer` no comenta (`reviewer.md:41`).
`govulncheck` (l.66) descarga la base de vulnerabilidades: búsqueda de CVE es de `nemesis`.

**Destino:** **Sin destino** (D-125; A029 ya sin destino).

## C028 — go-test

`5.635 bytes/268 líneas` · tools: hereda · model: hereda. TDD con tests de tabla:
interfaz, rojo, mínimo verde, refactor y cobertura ≥ 80 % con `go test -cover`.

**Intención, artefactos y despacho.** Sin agente: el método vive en el cuerpo y remite a
`tdd-workflow` y `golang-testing` (l.265-268). Escribe tests y código; dueño: `implementer`
siguiendo la skill `tdd` con `dev.json` `tdd: true` (`commands/dev-cycle.md:376`).
**Disparador.** «hazlo con TDD en Go», «test primero».
**Escenarios.** (+) «escribe primero el test de esta función» → skill `tdd`; comando del stack en
`skills/tdd/references/by-stack.md:16` (`go test ./paquete -run '^TestCriterio$' -v`). (−)
«¿qué cobertura tenemos?» → `unit-tests` (`coverage-gate.py`, que ya detecta Go,
`skills/unit-tests/SKILL.md:5`), no un ciclo TDD.

**Comparación.** El ciclo coincide con `skills/tdd/SKILL.md:44-50`. Lo que el comando hace distinto:

| Línea | Dice | Problema |
|---|---|---|
| 16, 234-241 | Cobertura ≥ 80 % obligatoria; 100 % lógica crítica, 90 % API pública | Umbrales fijos sin medida del proyecto. En el plugin el gate es opt-in (`tests.coberturaMinima`) y solo sobre el diff |
| 53, 108-115 | Stub `panic("not implemented")` y «Tests fail as expected (panic)» | En Go un `panic` en un subtest aborta el binario de test: el resto de la tabla no corre y el rojo no llega al assert. `by-stack.md:27-34` no trata este caso |
| 197 | `tt := tt // Capture` | Innecesario desde Go 1.22 (variable de bucle por iteración), la misma corrección de versión anotada en D-125 |

**Destino:** **Sin destino** como comando. Una fila general en `by-stack.md` (propuesta 1).

## C029 — gradle-build

`2.550 bytes/70 líneas` · tools: hereda · model: hereda. Arregla errores de Gradle en
Android y KMP: detecta el tipo de proyecto, agrupa errores, cambio mínimo y rebuild.

**Intención, artefactos y despacho.** Sin agente: procedimiento en el cuerpo. Escribe código y
`build.gradle.kts`; dueño: `implementer`.
**Disparador.** «Gradle no compila», «error de KSP/expect-actual».
**Escenarios.** (+) «el módulo `composeApp` no compila» → `implementer` en su tarea. (−)
«alinea Kotlin y Compose a la última» → `dependency-upgrade` (spec de upgrade), no un arreglo de build.

**Comparación.** Es la pieza mejor acotada del grupo: para y pregunta si el arreglo añade
dependencias, cambia módulos, falla la sincronización o el error está en código generado
(l.46-51), igual que `implementer.md:90`. Defecto: su tabla propone «alinear versiones de Kotlin
y Compose en `libs.versions.toml`» (l.67), un cambio de versión que su propia guarda debería
detener y que `implementer.md:90` deriva a `dependency-upgrade`.

**Destino:** **Sin destino** (Kotlin/Gradle aparcado, D-122). La guarda de l.46-51 ya existe.

## C039 — kotlin-build

`4.351 bytes/174 líneas` · tools: hereda · model: hereda. Despacha a `kotlin-build-resolver`
(l.7): `./gradlew build`, detekt y ktlint, arreglo por error y resumen.

**Intención, artefactos y despacho.** Igual que C026 para Kotlin. Dueño del código: `implementer`.
**Disparador.** «`./gradlew build` falla», «detekt reporta violaciones».
**Escenarios.** (+) «no compila tras el merge» → `implementer` + `debug-root-cause` al tercer rojo.
(−) «limpia los avisos de ktlint de todo el repo» → tarea propia planificada, no parte de un arreglo de build.

**Comparación.** Defectos propios del comando:

| Línea | Dice | Problema |
|---|---|---|
| 40 | `./gradlew build --refresh-dependencies` como refresco opcional | Red y cachés sin confirmación; `implementer.md:90` |
| 87-88 | Arreglo de tipo: `?: return@get call.respond(HttpStatusCode.BadRequest, …)` | Cambia el contrato HTTP del endpoint para que compile: deja de ser «surgical» (l.155) |
| 153 | Tercera pasada: «ktlint warnings — Fix formatting» | Mezcla formato en un arreglo de build; `scope-check.py` lo vería como cambio fuera de alcance |

Mejora sobre A036: «`when` must be exhaustive → añadir las ramas de la sealed class» (l.143), sin el `else`.

**Destino:** **Sin destino** (D-122; A036 ya sin destino).

## C040 — kotlin-review

`3.628 bytes/140 líneas` · tools: hereda · model: hereda. Despacha a `kotlin-reviewer` (l.7):
build, detekt, ktlint y tests, más seguridad, null safety y corrutinas.

**Intención, artefactos y despacho.** Como C027. Veredicto: fusión de `adversarial-review`.
**Disparador.** «revisa mis cambios Kotlin».
**Escenarios.** (+) «revisión de la rama» → `adversarial-review`. (−) «qué funciones son demasiado
largas» → `code-health` (tamaño y anidamiento deterministas), no una revisión del diff.

**Comparación.** Contradicción interna: `GlobalScope` figura como CRITICAL en la lista (l.33) y
el ejemplo lo marca HIGH (l.99). Gradúa como HIGH, y por tanto bloqueante (l.128), funciones de
más de 50 líneas y anidamiento > 4 (l.42-43): tamaño de código, que en el plugin mide `code-health`
y que `reviewer` no convierte en gap sin escenario (`reviewer.md:41`). Las comas finales (l.47)
son estilo. Ejecuta `./gradlew build` y `test` (l.56-65): admisible como evidencia, pero sin
`allowed-tools` nada impide que edite.

**Destino:** **Sin destino** (D-122; A037 ya sin destino).

## C041 — kotlin-test

`7.609 bytes/312 líneas` · tools: hereda · model: hereda. TDD con Kotest, MockK y Kover,
cobertura ≥ 80 %.

**Intención, artefactos y despacho.** Como C028. Dueño: `implementer` con la skill `tdd`.
**Disparador.** «TDD en Kotlin», «test con Kotest primero».
**Escenarios.** (+) «escribe primero el test» → `tdd`; comando del stack en `by-stack.md:19`
(`./gradlew test --tests '…'`). (−) «gate de cobertura con Kover» → `unit-tests`, que hoy sale
con exit 2 para Gradle (`skills/unit-tests/SKILL.md:101`; parser aparcado, D-111).

**Comparación.** Mismos umbrales fijos que C028 (l.16, 277-284). El rojo de ejemplo es
`NotImplementedError` de un stub `TODO()` (l.62, 149-154): equivale al `NameError` de la función
nueva que `by-stack.md:30` da por válido, pero conviene decirlo. `open build/reports/…` (l.268)
solo existe en macOS.

**Destino:** **Sin destino** (D-122, D-111). Comparte la propuesta 1.

## Propuestas para integrar después

1. **P3 · `skills/tdd/references/by-stack.md`, tabla «Ves… / Es…» (l.27-34)**, fila nueva:
   «`NotImplementedError` / `panic("not implemented")` / `TODO()` del **stub de la función nueva** |
   Rojo válido, como el `NameError` | Regístralo; en Go un `panic` aborta el resto de subtests de la
   tabla: comprueba en GREEN que corren todos los casos». Fuente: C028 l.108-115, C041 l.149-154.
2. **Ninguna línea nueva en `implementer` ni en `adversarial-review`**: «no `go get`/`--refresh-dependencies`
   como arreglo» y «no descartar errores para compilar» ya los cubren `implementer.md:90` y la Lente B.
   Las correcciones de versión (Go 1.22, comas de Kotlin) acompañan a D-125/D-122 cuando un
   consumidor declare el stack.
