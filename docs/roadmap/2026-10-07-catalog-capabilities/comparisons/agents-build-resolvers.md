# Resolutores de build e implementador de plataforma — A028, A030, A034

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres definiciones completas: **25.809 bytes/560 líneas**. [agents-build-resolvers-reading-evidence.json](agents-build-resolvers-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las tres.** Bloque «Prompt Defense Baseline» idéntico (líneas 8-15). Las tres
tienen `tools: Read, Write, Edit, Bash, Grep, Glob` y `model: sonnet`, y escriben código
del proyecto sin rama, sin ledger y sin `Verificación` declarada.

**Regla aplicada.** Tocar código es responsabilidad exclusiva de `implementer`
(`docs/agents/ROLES.md`, ADR-011). Ese agente ya hace lo que estas piezas venden como
especialidad: aplica el cambio mínimo que cumple los criterios, compila, pasa el lint y ejecuta
los tests de la zona (`agents/implementer.md:89-90`). Antes de la primera edición de cada
fichero comprueba quién lo importa (`:88`), y al cerrar cada fase vuelve a compilar
(`:104`). El tope de tres intentos de las fuentes coincide con los bucles acotados de
`/dev-cycle` (`commands/dev-cycle.md:409`, `:413`). Al tercer rojo entra `debug-root-cause`,
que prohíbe cambiar código sin una hipótesis probada (`skills/debug-root-cause/SKILL.md:11`).
Un «resolutor de build» separado duplicaría la fase de implementación.

## A028 — go-build-resolver

`4.245 bytes/103 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet. Corrige
errores de `go build`, `go vet`, staticcheck y golangci-lint con cambios mínimos. Incluye una
tabla de errores frecuentes y condiciones de parada.

**Comparación.** El método (parsear el error, leer el fichero, aplicar el cambio mínimo,
recompilar, vet y test) es el paso P3 de `implementer`. Las condiciones de parada de las
líneas 87-90 (el mismo error tras tres intentos, el arreglo crea más errores de los que
quita, el cambio sería de arquitectura) son útiles, pero ya están en el bucle acotado y en
`debug-root-cause`. Defectos de la fuente:

| Línea | Dice | Problema |
|---|---|---|
| 31-40 | «Run these in order», con `go mod tidy -v` entre los diagnósticos | `tidy` reescribe `go.mod`/`go.sum`: un diagnóstico que modifica ficheros ya es un intento de arreglo |
| 74 | `go clean -modcache && go mod download` para errores de checksum | Borra la caché de módulos de toda la máquina (afecta a otros proyectos) y oculta una suma que no cuadra, que puede ser una señal de cadena de suministro |
| 81 | «Never add `//nolint` without explicit approval» | Correcto. En el plugin, la supresión no justificada ya es gap Important de la Lente A (`lens-prompts.md:20`), pero el implementador no tiene la regla del lado de quien escribe |

**Destino:** **Sin destino** como agente: Go está aparcado (D-125). De aquí salen dos líneas
generales (ver el final de la ficha).

## A030 — harmonyos-app-resolver

`9.383 bytes/182 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet. Experto
ArkTS/ArkUI que revisa **e** implementa a la vez. Impone la gestión de estado V2 y
`Navigation` («no compromise») y lista las restricciones de sintaxis de ArkTS.

**Comparación.** Mezcla dos roles con dueños distintos: revisar (`reviewer`, de solo
lectura) e implementar (`implementer`). Su salida pone `[REVIEW]` y `[IMPLEMENT]` en el
mismo informe (líneas 171-177). Eso es exactamente el solape que ADR-011 prohíbe. Lo que
no cubre el plugin es el stack HarmonyOS/ArkTS, que no tiene consumidor. Defectos:

| Línea | Dice | Problema |
|---|---|---|
| 23-33, 151 | Solo V2 y solo `Navigation`, «MUST» en todo código | En un proyecto V1 obliga a migrar. `stack-practices` dice que las guías no fuerzan migraciones (`SKILL.md:26`) |
| 165 | «Proactive refactoring» a V2 + Navigation | Cambio fuera de alcance. `implementer` lo trata como gap Important (`implementer.md:131`, `scope-check.py`) |
| 147 | «Search official Huawei developer documentation — never guess» | No tiene WebFetch ni MCP de documentación en `tools`: la instrucción no se puede cumplir |
| 182 | Remite a «rule files in `rules/arkts/`» | No forma parte de la definición |

**Destino:** **Sin destino.** No hay consumidor del stack, y por ADR-011 no se adopta un
agente que revise y edite a la vez.

## A034 — java-build-resolver

`12.181 bytes/275 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Resolutor de errores de Maven/Gradle/javac. Detecta Spring Boot o Quarkus por el fichero de
build y trae tablas de errores por framework.

**Comparación.** Tiene el mismo patrón que A028 y es mejor en un punto: las condiciones de
parada incluyen «dependencias externas que necesitan decisión del usuario (repos privados,
licencias)» (línea 258). El catálogo Spring/Quarkus coincide con S222–S225 y S260–S263, ya
reunidas en D-126 (aparcada; los comandos Maven/Gradle quedan como entradas para sus
dueños). Defectos de la fuente:

| Línea | Dice | Problema |
|---|---|---|
| 46-56 | Diagnóstico «in order» que incluye `./mvnw test` y `./gradlew build` antes de leer el error | Lanza la suite completa para diagnosticar |
| 123 | `./mvnw clean install -U` | Instala en `~/.m2`: efecto fuera del repo |
| 152 | `rm -rf .gradle/build-cache/` | La caché de build local de Gradle vive en `~/.gradle/caches/build-cache-1`; la ruta del proyecto no es la estándar y el borrado no arregla lo que promete |
| 168, 189, 214 | `spring-boot:run`, `quarkus:dev`, `quarkusDev` como diagnóstico | Procesos que no terminan: bloquean al agente |
| 93 | Ciclo de dependencias → «`@Lazy` en una rama» | Esconde un defecto de diseño. Ante un cambio de arquitectura, la propia pieza dice parar (línea 257) |

**Destino:** **Sin destino** como agente. Java sigue aparcado (D-126). Las correcciones de
las líneas 123, 152 y 168 se anotan en D-126 para cuando un consumidor declare Java.

## Líneas generales que sí tienen destino

1. **Supresiones del lado de quien escribe** (A028:81, A034:243, y en A023:202 de la ficha
   de revisores). La Lente A ya caza la supresión no justificada, pero la tabla de
   racionalizaciones de `implementer` no tiene la excusa. Propuesta P2 en el informe.
2. **El diagnóstico no escribe** (A028:31-40 y 74, A034:123 y 152). `debug-root-cause`
   pide una reproducción mínima en la Fase 1, pero no dice que los comandos de diagnóstico
   deben dejar intacto el estado de partida. Propuesta P2 en el informe.
