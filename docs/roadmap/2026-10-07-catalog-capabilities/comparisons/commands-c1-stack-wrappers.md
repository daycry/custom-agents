# Envoltorios por stack: C++, FastAPI y Flutter — C007–C009, C019, C021–C023

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Siete definiciones completas: **26.252 bytes/1.019 líneas**. [commands-c1-stack-wrappers-reading-evidence.json](commands-c1-stack-wrappers-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Regla aplicada y decisiones previas

Los siete comandos son envoltorios de un stack sin consumidor declarado: C++
(D-124), FastAPI dentro de Python (D-129) y Dart/Flutter (D-134). La regla única
de [skills-destinations.md](skills-destinations.md) (línea 11) los deja aparcados.
Los agentes que despachan ya tienen ficha: `cpp-build-resolver` (A012) y
`dart-build-resolver` (A015) en [agents-build-resolvers-core.md](agents-build-resolvers-core.md);
`cpp-reviewer` (A013) en [agents-review-cpp-csharp-db.md](agents-review-cpp-csharp-db.md);
`fastapi-reviewer` (A022) y `flutter-reviewer` (A023) en
[agents-stack-domain-reviewers.md](agents-stack-domain-reviewers.md). Lecturas parciales
previas: C007–C009 en `skills-cpp-dotnet-distribution-billing.md` (35, 73, 142) y
C021–C023 en `skills-trade-flutter-observability.md` (137, 246, que pide cubrirlos
con roles compartidos y sin revisor Flutter obligatorio). Esta ficha no reabre esas
decisiones: añade el despacho, los dueños y los defectos propios de cada comando.

**Dueños por artefacto, comunes a los siete.** Arreglar un build o un test es
código del proyecto → `implementer` (`docs/agents/ROLES.md:31`). Revisar es
`adversarial-review` con `reviewer` de solo lectura (`agents/reviewer.md:9`),
con criterio de stack solo para PHP/CodeIgniter, Python y React
(`skills/stack-practices/SKILL.md:4-5`). El método de test primero es `tdd`; el
rojo de compilación por el símbolo nuevo ya es rojo válido
(`skills/tdd/references/by-stack.md:31`, D-054 integrado). La cobertura es
opt-in con `coverage-gate.py`, que da exit 2 con builds sin soporte
(`skills/unit-tests/SKILL.md:98-101`); el umbral es del proyecto. Las pruebas E2E
y su veredicto son de `qa`. Ninguno de los siete declara `tools` ni `model`.

## C007 — cpp-build

`4.030 bytes/173 líneas`. Despacha `cpp-build-resolver`: CMake, compilación,
enlazado y avisos, un error cada vez.

- **Disparador:** «no compila el proyecto C++». **Escenario +:** en un proyecto
  con ledger → `implementer` P3 con la línea de build roto. **Escenario −:**
  «sube Boost para que enlace» → `dependency-upgrade`.
- **Defectos propios:** `cmake --build build 2>&1 | head -100` (33) devuelve el
  estado de `head`, así que un build roto sale con 0; `clang-tidy src/*.cpp --
  -std=c++17` (36) ignora `compile_commands.json` y el estándar del proyecto;
  «Add appropriate cast» (145) repite el defecto de A012; y «Warnings third»
  (152) amplía el alcance de un arreglo de build a limpiar avisos.

## C008 — cpp-review

`3.456 bytes/132 líneas`. Despacha `cpp-reviewer`: diff C++, `clang-tidy`,
`cppcheck`, memoria, concurrencia y C++ moderno.

- **Disparador:** «revisa este cambio C++». **Escenario +:** `adversarial-review`
  con Lentes B/C/D sin referencia de stack. **Escenario −:** «audita la memoria
  de todo el repo» → no es revisión de diff; `nemesis` si es seguridad.
- **Defectos propios:** `cmake --build build -- -Wall -Wextra -Wpedantic` (61) pasa
  los flags a la herramienta de build nativa, no al compilador: `make` interpreta
  `-W <fichero>` como «finge que este fichero cambió» (`-Wall` marca un fichero
  llamado `all`) y en `ninja` tampoco son flags de compilador, así que no activa
  ningún aviso; los avisos van en `CMAKE_CXX_FLAGS` al configurar. La aprobación (116-120) bloquea con cualquier HIGH,
  como A013.

## C009 — cpp-test

`5.880 bytes/251 líneas`. TDD con GoogleTest, CTest y cobertura con lcov; no
despacha agente.

- **Disparador:** «hazlo con TDD en C++». **Escenario +:** skill `tdd` (ley dura
  y `RED:` en el ledger) con el comando de UN test del stack. **Escenario −:**
  «sube la cobertura al 80 %» sin `tests.coberturaMinima` → no hay gate; el
  umbral lo decide el proyecto (`unit-tests`).
- **Defectos propios:** ya anotados `std::expected` (C++23) frente a
  `-std=c++17` y el 80 % universal. Además, el paso 1 crea las interfaces antes
  del test (11, 46-58), así que el rojo del ejemplo es un error de **enlazado**
  (104-105), no de compilación por el símbolo nuevo: vale como rojo solo si el
  símbolo ausente es el que se va a escribir. Y reconfigura el directorio
  `build` con `--coverage` (146, 206), mezclando el build instrumentado con el normal.

## C019 — fastapi-review

`1.007 bytes/39 líneas`. Despacha `fastapi-reviewer`.

- **Disparador:** «revisa este endpoint FastAPI». **Escenario +:** Python sí es
  stack con consumidor → `adversarial-review` con `stack-practices/references/python.md`,
  `backend-practices`, `api-contract` si el diff toca la spec y Lente C para CORS
  o autenticación. **Escenario −:** «genera la documentación de la API» →
  `documenter`; no es revisión.
- **Comparación:** el comando no añade nada a A022 salvo remitir a `/python-review`
  y a la skill `security-scan` (34-39), piezas de la fuente sin equivalente aquí.

## C021 — flutter-build

`4.085 bytes/164 líneas`. Despacha `dart-build-resolver`.

- **Disparador:** «`flutter analyze` da errores». **Escenario +:** `implementer`
  P3. **Escenario −:** «resuelve el conflicto de versiones de pub» → `dependency-upgrade`.
- **Defectos propios:** repite `response.id ?? ''` (80) de A015, que oculta un id
  nulo; trata `flutter build apk` y `flutter build web` (39-40) como diagnóstico
  rutinario, cuando son builds completos de plataforma que exigen su toolchain;
  y propone ajustar restricciones en `pubspec.yaml` (135) a la vez que dice
  parar ante conflictos de paquetes (153).

## C022 — flutter-review

`3.955 bytes/116 líneas`. Despacha `flutter-reviewer`.

- **Disparador:** «revisa este PR de Flutter». **Escenario +:** `adversarial-review`
  sin referencia de stack. **Escenario −:** «revisa la accesibilidad de la web» →
  `frontend-quality`, que es web y no acredita Flutter.
- **Defectos propios:** gradúa «architecture violations» como CRITICAL (39) y la
  propagación de `const` como HIGH (43), y cualquier HIGH bloquea (103-104): el
  estilo bloquea el merge. Exige `flutter analyze` limpio antes de revisar (23),
  lo que mezcla la puerta del implementador con la del revisor.

## C023 — flutter-test

`3.839 bytes/144 líneas`. Ejecuta la suite y arregla fallos uno a uno; cita
`flutter-reviewer` y `dart-build-resolver` como relacionados, sin despacharlos.

- **Disparador:** «fallan los tests de Flutter». **Escenario +:** dentro de una
  iniciativa, `implementer` corrige y `qa` da el veredicto. **Escenario −:**
  «regenera los goldens» sin un criterio que pida el cambio visual → ninguna
  pieza propia lo hace por su cuenta.
- **Defectos propios:** el segundo arreglo del ejemplo cambia el texto esperado
  del test para que coincida con el widget (93-94), sin comprobar cuál de los dos
  dice la spec; `--update-goldens` se recomienda cuando el golden falta o difiere
  «si el cambio era intencionado» (44-45, 127-128) sin decir quién lo decide; y
  sustituir `pumpAndSettle` por `pump(Duration)` (131) puede esconder una
  animación que no termina. El 80 % del ejemplo (106) no sale de ninguna configuración.

## Lo que el plugin no tiene

Dos defectos de estos comandos son independientes del stack y aparecen también
en stacks con consumidor:

1. **Tuberías que ocultan el exit.** `build | head` (C007:33) sale con 0 aunque
   el build falle; S285 tenía el mismo defecto con `tail`
   (`skills-tdd-verification-ops.md:52-53`, sin destino entonces). Ninguna pieza
   propia lo advierte.
2. **Regenerar el valor esperado.** `--update-goldens` (C023) es lo mismo que
   `jest -u` o `vitest -u` en React: reescribe la aserción. La Lente B ya caza
   «assert debilitado» (`references/lens-prompts.md:21`), pero no nombra este caso.

## Destino

**Sin especialidad** para los siete (D-124, D-129, D-134). Dos líneas propias:

1. `agents/implementer.md`, P3, tras la línea de `Verificación` (`:91`): «El
   estado de una tubería es el del último proceso: `build 2>&1 | head` sale con 0
   aunque el build falle. Ejecuta con `set -o pipefail`, o guarda la salida en un
   fichero y lee el exit del propio comando antes de pegarla en el ledger».
2. `skills/adversarial-review/references/lens-prompts.md`, Lente B, junto a
   «assert debilitado»: «…incluido un snapshot o golden regenerado (`-u`,
   `--update-goldens`) sin un criterio que pida ese cambio de salida».

Para cuando se abra D-124: anotar en su fila los defectos de C007:33/36,
C008:61 y C009:146. Para D-134: C021:39-40/135 y C022:39/43.

## Resumen

| ID | Agente despachado (ficha) | Destino |
|---|---|---|
| C007 | A012 | Sin especialidad (D-124); aporta la línea de tuberías |
| C008 | A013 | Sin especialidad (D-124) |
| C009 | — | Sin especialidad (D-124); rojo ya cubierto por D-054 |
| C019 | A022 | Sin destino (D-129) |
| C021 | A015 | Sin especialidad (D-134) |
| C022 | A023 | Sin especialidad (D-134) |
| C023 | — | Sin especialidad (D-134); aporta la línea de goldens |
