# Resolutores de build — A004, A012, A015, A017

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **26.047 bytes/684 líneas**. [agents-build-resolvers-core-reading-evidence.json](agents-build-resolvers-core-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Comparación común

Los cuatro tienen Read, Write, Edit, Bash, Grep y Glob y usan sonnet. Cada uno edita
código con cambios mínimos hasta que el build pasa y se detiene tras tres intentos.
También comparten el bloque «Prompt Defense Baseline» (líneas 8-15, sin destino). En
el plugin, esa responsabilidad ya tiene dueño:

| Qué hacen | Dueño propio |
|---|---|
| Editar código para ponerlo en verde | `implementer`, único que toca código (`docs/agents/ROLES.md:31`), con cambio mínimo y comprobación de compilación, lint y tests (`agents/implementer.md:89-90`) |
| «Nunca suprimir avisos sin aprobación» | Lente A, criterio «Puertas relajadas» (`skills/adversarial-review/references/lens-prompts.md:20`, D-059) |
| Parar tras tres intentos | Bucle acotado a 3 (`commands/dev-cycle.md:409`) y `debug-root-cause`: «prohibido cambiar código sin una hipótesis probada» (`SKILL.md:11-12`) |
| Subir o fijar dependencias | `dependency-upgrade` prepara la iniciativa; no actualiza nada (`SKILL.md:88`) |

Un agente resolutor sería un segundo dueño del código, sin ledger, sin `scope-check`
y sin `Verificación` (ADR-011).

Lo que el plugin **no** dice en ningún sitio es que borrar el lockfile, reinstalar o
subir paquetes, limpiar cachés globales, marcar migraciones con `--fake` o matar
procesos por puerto no son arreglos. Las cuatro fuentes los proponen como recetas
rápidas. `guardrail-check.py:36-42` solo bloquea los casos catastróficos (`rm -rf` de
`/`, `~`, `.git` o `.`; `prune`, `kubectl delete`, `DROP`), y está bien que no vaya más
allá: el resto depende del contexto y debe ir en prosa.

**Destino común:** dos líneas.

1. En `agents/implementer.md`, P3, tras «Implementa el cambio mínimo…» (`:89`): «Un
   build o una instalación rota no se arregla borrando el lockfile, subiendo paquetes,
   limpiando cachés globales, marcando migraciones con `--fake` ni matando procesos por
   puerto: eso cambia versiones o estado fuera del alcance de la tarea. Si la causa es
   una dependencia, anótala y propón una iniciativa con `dependency-upgrade`; si el rojo
   persiste tras tres intentos, aplica `debug-root-cause`».
2. En `skills/debug-root-cause/SKILL.md`, «Reglas»: «Limpiar cachés o reinstalar
   dependencias es un experimento de la Fase 2, no un fix: si el fallo desaparece, la
   causa era el estado previo y hay que nombrarla».

## A004 — build-error-resolver

`4.749 bytes/123 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Errores de TypeScript y de build en Node/Next.js: `tsc --noEmit`, `npm run build`,
`eslint`, una tabla de errores frecuentes y una «Quick Recovery».

**Comparación.** Está cubierto por la tabla común. Defectos:

- **«Quick Recovery» (94-103).** `rm -rf node_modules package-lock.json && npm install` borra
  el lockfile y vuelve a resolver todo el árbol, con versiones nuevas fuera de alcance.
  Va contra su propio «Minimal Diffs» (27).
- **ESLint sobre todo el repo.** `npx eslint . --fix` contradice «Refactor unrelated code» (77).
- **Dependencias.** «Add missing dependencies» (72) aparece sin ninguna decisión sobre quién las aprueba.
- **Umbral.** «< 5% of affected file» (110) no tiene base.
- **Errores mal clasificados.** `Hook called conditionally` (63) es una regla de lint de
  React, no un error de compilación.

**Destino:** **Sin destino** como agente. Aporta a la línea común.

## A012 — cpp-build-resolver

`4.108 bytes/99 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
CMake, enlazado y plantillas, con `clang-tidy`, `cppcheck` y `ctest`. Prohíbe `#pragma`
sin aprobación y fija condiciones de parada.

**Comparación.** Es la más contenida de las cuatro. Su tabla propone «Add cast» para
`cannot convert X to Y` (59), en contra de su propio «fix root cause over suppressing
symptoms» (78). El material de C++ espera en D-124.

**Destino:** **Sin especialidad** hasta que un consumidor declare C++ (D-124).

## A015 — dart-build-resolver

`7.671 bytes/210 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
`dart analyze`/`flutter analyze`, pub, `build_runner`, Gradle y CocoaPods.

**Comparación.** Está cubierto por la tabla común. Se contradice en varios puntos:

| Línea | Dice | Choca con |
|---|---|---|
| 73, 88-91, 202-205 | Arreglar conflictos con `flutter pub upgrade`, `dependency_overrides` o «Upgraded dio to ^5.3.0» | Su condición de parada «package upgrades that change behavior» (191) |
| 66 | Añadir `!` como fix | «Prefer null-safe patterns over bang operators» (184) |
| 199 | `response.id ?? ''` | Oculta un id nulo con una cadena vacía: silencia el error en vez de tratarlo |
| 94, 171 | `flutter pub cache repair`, `pod deintegrate` | Tocan la caché global del usuario o la integración del proyecto, no el error |

**Destino:** **Sin especialidad** (D-134).

## A017 — django-build-resolver

`9.519 bytes/252 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
pip/Poetry, migraciones, settings, imports, conexión a la base, `collectstatic` y `runserver`.

**Comparación.** Está cubierto por la tabla común. Las migraciones genéricas ya están
en `skills/backend-practices/references/database-migrations.md` («Estado a medias»,
`:48`). Tiene las instrucciones más peligrosas del rango:

| Línea | Instrucción | Riesgo |
|---|---|---|
| 213 | `lsof -ti:8000 \| xargs kill -9` | Mata cualquier proceso que ocupe el puerto, sea del usuario o no |
| 103, 226 | `InconsistentMigrationHistory` → «squash or fake»; «Never delete migration files — fake them instead» | `--fake` marca como aplicada una migración que no corrió y desincroniza el esquema; la propia fuente lo matiza en 229, pero la tabla lo recomienda |
| 117 | `migrate <app> zero` («dev only!») | Borra las tablas de la app; choca con su parada por cambios destructivos (235) |
| 230 | Preferir `pip install --upgrade` a editar `requirements.txt` | Cambia versiones sin fijarlas, contra la reproducibilidad (persona `devops.md:3`) |
| 86, 89, 206 | `--force-reinstall`, `poetry cache clear --all pypi`, `collectstatic --clear` | Efectos globales o borrados que no corrigen la causa |

**Destino:** **Sin especialidad** (D-128). Aporta a la línea común.
