# TDD, bucle de verificación y ejecución con evidencia — S273, S277, S285

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **27.385 bytes/822 líneas**, sin recursos locales.
[tdd-verification-ops-reading-evidence.json](tdd-verification-ops-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S273 — Flujo TDD con plan de entrada e informe de evidencia

`21.596 bytes/583 líneas`. Rojo antes del código, verde mínimo y refactor, con
commits de control por etapa, detección del runner, cobertura del 80 % en
unitarios, integración y E2E, e informe `*.tdd.md` con la evidencia. Acepta un
`*.plan.md` como punto de partida.

**Comparación.** `tdd` es la fuente única del método (ADR-011) y ya exige más:
ley dura, rojo «por la razón correcta», línea `RED:` por criterio en el ledger,
`TDD n/a` declarado y comprobación en la Lente A. La evidencia que S273 guarda en
un informe aparte el plugin la guarda en el ledger, y el resumen de PR de
`/dev-cycle` Fase 6 sale de él. La cobertura es opt-in (`tests.coberturaMinima`,
`unit-tests`), no un 80 % universal. Tres aportes reales:

| Idea de la pieza | Destino propuesto |
|---|---|
| El plan es dato no confiable: sus «comandos de validación» son intención, se traducen a acciones permitidas (test, lint, typecheck, cobertura); `curl … \| sh`, borrados y manejo de credenciales se rechazan | Línea en `agents/implementer.md` (P3, «Ejecuta la `Verificación` declarada»): una `Verificación` con red, tubería a intérprete, borrado o credenciales se muestra al usuario antes de ejecutarla, sobre todo si el plan no lo escribió `planner` |
| Rojo de compilación válido cuando el test referencia el símbolo nuevo y el error es por su ausencia | Fila en la tabla «rojo válido» de `tdd/references/by-stack.md`, equivalente al `NameError` actual, para stacks compilados |
| `bun test` (runner nativo) no es `bun run test` (script de `package.json`) | Fila Bun en `tdd/references/by-stack.md`, coherente con la referencia Bun propuesta en S031 ([skills-brand-browser-runtime.md](skills-brand-browser-runtime.md)) |

Defectos de la fuente:

| Ejemplo | Corrección |
|---|---|
| `"coverageThresholds"` en la configuración de Jest (dos veces) | La clave es `coverageThreshold`; con el plural Jest no aplica el umbral y la puerta del 80 % no existe |
| Paso 0 ejecuta `node scripts/setup-package-manager.js` | Script del catálogo de origen, ausente en el proyecto consumidor |
| `it('handles database errors gracefully')` con cuerpo vacío | Test que no puede fallar; es el anti-patrón 2 de `tdd/references/anti-patterns.md` |
| E2E con `page.waitForTimeout(600)` «para el debounce» | Espera arbitraria; esperar el estado observable (criterio de `stack-practices/references/react.md`) |
| «Una aserción por test» junto a un E2E con siete aserciones | Heurística, ya tratada así en S081 |
| 80 % sobre unitarios + integración + E2E | Las capas se miden por separado; `qa` informa la pirámide sin veredicto propio |

**Destino:** las tres líneas de la tabla anterior; sin skill nueva.

## S285 — Bucle de verificación en seis fases

`2.792 bytes/129 líneas`. Build, tipos, lint, tests con cobertura, búsqueda de
secretos y revisión del diff, con un informe «READY / NOT READY».

**Comparación.** Repite la decisión de S082
([skills-django-security-testing-verification.md](skills-django-security-testing-verification.md)):
un segundo bucle duplicaría `qa` (`qa-gate.py`), `coverage-gate.py`,
`scope-check.py`, `adversarial-review` y nemesis. Defectos que muestran por qué
el veredicto no debe vivir en prosa:

- `npm run build 2>&1 | tail -20` devuelve el estado de `tail`: un build roto
  sale con 0. `set -o pipefail` solo aparece en la fase 2.
- `git diff HEAD~1 --name-only` revisa el último commit, no la rama; el plugin
  revisa el rango completo y compara con el campo `Archivos` (`scope-check.py`).
- Buscar `sk-` y `api_key` en `.ts`/`.js` da falsos positivos y omite casi todos
  los formatos de secreto; la auditoría de secretos es de `cybersecurity`.
- «READY for PR» lo decide el modelo; en el plugin el verde sale de
  `results.json` vía `qa-gate.py` con exit code.

**Sin destino.**

## S277 — Operación de terminal con evidencia

`2.997 bytes/110 líneas`. Inspeccionar antes de editar, arreglo estrecho, comando
de prueba mínimo y vocabulario de estado: inspeccionado, cambiado localmente,
verificado localmente, commit, push, bloqueado.

**Comparación.** Cubierto por dueños existentes: el DoD de `implementer` exige
la salida real de la `Verificación`; `guardrail-check.py` impide git
destructivo; `debug-root-cause` sustituye «si falla con la misma firma, deja de
reintentar» por un método con hipótesis probada al tercer rojo; y la Fase 6 de
`/dev-cycle` separa commit, PR e integración («esto no autoriza push, merge, PR
ni release»). Sus disparadores («fix», «run this», «push it») colisionarían con
`quick-implement`. **Sin destino.**

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S273 | Método ya cubierto por `tdd`; tres aportes | `implementer` P3 (Verificación externa) y dos filas en `tdd/references/by-stack.md` |
| S285 | Duplicaría `qa` y sus puertas | — |
| S277 | Cubierto por DoD, guardia y Fase 6 | — |

Validación pendiente: la línea de `implementer` necesita un caso de eval con un
plan importado cuya `Verificación` incluya una tubería a intérprete.
