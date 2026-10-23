# Limpieza, seguridad, fallos silenciosos, TDD y diseño de tipos — A056, A059, A061, A065, A066

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **16.867 bytes/420 líneas**.
[agents-refactor-security-silent-tdd-types-reading-evidence.json](agents-refactor-security-silent-tdd-types-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Cinco piezas transversales, sin lenguaje fijo, que repiten una fase con dueño
propio: limpiar código (`implementer` con tarea del ledger), revisar seguridad
(Lente C y `nemesis`), cazar errores silenciados (Lente B), guiar TDD (skill
`tdd`) y juzgar tipos (`coding-baseline.md`, `architect`). Ninguna entra como
agente (ADR-011). Una línea de A056 tiene destino en `planner`; A061 aporta una
precisión opcional para la Lente B.

## A056 — refactor-cleaner

`3.686 bytes/94 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model:
sonnet. Detecta código, exportaciones y dependencias sin uso con `knip`,
`depcheck` y `ts-prune`; borra por lotes con tests y un commit por lote.

**Comparación.** `code-health` mide duplicados, tamaño, hotspots y TODO, y no
refactoriza (`skills/code-health/SKILL.md:36-44`, `:99-102`); `planner` abre la
deuda solo dentro del alcance de la spec, con `fichero:línea` y `Verificación`
(`agents/planner.md:88`); `implementer` es el único que cambia código y
`scope-check.py` devuelve lo que sale del alcance como gap Important
(`agents/implementer.md:6`, `:131`). El refactor puro ya es
`TDD n/a: refactor` con la misma suite verde antes y después
(`skills/tdd/SKILL.md:41`, D-053 **ya integrado**). Lo que la pieza tiene de
propio y vale: la lista previa al borrado (A056:61-67), sobre todo las
**referencias dinámicas** (importaciones por cadena) y la **API pública**, que
ningún dueño pide comprobar al borrar. `code-health` tampoco detecta código
muerto; eso se deja a la herramienta que el proyecto ya tenga.

Defectos:

| Línea | Problema |
|---|---|
| :3 | «Úsalo PROACTIVAMENTE para borrar código»: borrado fuera de una tarea y de su alcance |
| :31-34 | `npx knip`, `npx depcheck`, `npx ts-prune` sin versión fijada: descargan y ejecutan; además `ts-prune` está en modo mantenimiento y remite a `knip`. Todo es solo JavaScript |
| :53, :72 | Commit por lote decidido por el agente; aquí el commit es por tarea `T-XX` |
| :94 | «Bundle más pequeño» como métrica de éxito, sin medirlo en ningún paso |

**Destino:** línea en `agents/planner.md`, P3, junto a «Deuda técnica medida»
(abajo).

## A059 — security-reviewer

`5.446 bytes/117 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
OWASP, secretos, validación, autorización y dependencias, con tabla de
patrones y falsos positivos.

**Comparación.** Dos dueños según el alcance: la Lente C revisa solo lo que el
diff introduce o reabre, con CWE y escenario
(`skills/adversarial-review/references/lens-prompts.md:27`), y `nemesis` hace la
auditoría completa con `cybersecurity` (OWASP Top 10:2021, CWE Top 25:2024,
`skills/cybersecurity/SKILL.md:5`, `:75`), con informe en `docs/security-scan/`.
La supresión de falsos positivos ya tiene referencia
(`cybersecurity/references/false-positive-suppression.md`). Los criterios de
diseño (autorización por recurso, cuota atómica, subidas) están en
`backend-practices/references/contracts-data.md:12-33`. Defectos:

| Línea | Problema |
|---|---|
| :3, :19 frente a :4 | Se presenta como especialista en «detección y **remediación**» y en «Respuesta de emergencia» pide ejemplo seguro, verificar la remediación y **rotar secretos** (:90-95), sin Write ni Edit; rotar es un efecto externo que no le corresponde |
| :43-53 | La lista «OWASP Top 10» es la de 2017 (XXE, deserialización insegura y registro insuficiente como categorías), no la 2021 que usa `cybersecurity` |
| :33-34 | Solo `npm audit` y `npx eslint --plugin security`: análisis de JavaScript presentado como general; `npx` descarga sin versión fijada |
| :68 | «Sin rate limiting → `express-rate-limit`»: una librería concreta como arreglo general |

**Destino:** **sin destino**; Lente C + `nemesis` cubren el rol.

## A061 — silent-failure-hunter

`1.989 bytes/59 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Bloques `catch` vacíos, registro pobre, fallbacks peligrosos, propagación
perdida y falta de timeout o rollback.

**Comparación.** Es la Lente B: «errores silenciados» está literalmente en su
prompt (`lens-prompts.md:21`). Los criterios ya tienen dueño:
`python.md:32` (encadenar la causa, no capturar `Exception` para devolver
éxito), `coding-baseline.md:52` (`cause` al relanzar, registro redactado),
`contracts-data.md:25` (timeout y clasificación del fallo de dependencia). La
pieza no define escala de severidad pese a pedirla (:57), ni alcance (¿repo o
diff?). Su «tolerancia cero» con los fallbacks (:19, :34-38) choca con una
regla del propio plugin: las piezas opcionales **degradan con aviso** y los
hooks salen siempre con 0 (`CLAUDE.md`, «Degradación, no bloqueo»). La línea
útil es la frontera: un fallback es defecto cuando oculta el fallo, no cuando
lo declara.

**Destino:** **sin destino** como pieza; precisión opcional (P3) para la
Lente B (abajo).

## A065 — tdd-guide

`3.865 bytes/100 líneas` · tools: Read, Write, Edit, Bash, Grep · model:
sonnet. Rojo-verde-refactor con cobertura del 80 %, unitarios, integración y
E2E, lista de casos límite y un anexo de evals con pass@k.

**Comparación.** `tdd` es la fuente única (ADR-011) y exige más: rojo por la
razón correcta, línea `RED:` en el ledger, `TDD n/a` declarado y un solo test
por paso (`skills/tdd/SKILL.md:39-42`, `:44-63`). La cobertura es opt-in
(`tests.coberturaMinima`, `unit-tests`); E2E es de `qa`
(`tdd/SKILL.md:42`); pass@k/pass^k ya está en
`outcome-evals/references/protocol.md:62-66` (de S097, **ya integrado**).
Defectos:

| Línea | Problema |
|---|---|
| :3, :23, :48 | 80 % universal; la regla del plugin es umbral del proyecto (resuelta en `skills-destinations.md`) |
| :24, :57 | El guía de TDD escribe también E2E, que tiene dueño (`qa`) |
| :3 | «Úsalo al corregir fallos o refactorizar»: el fallo empieza por `debug-root-cause` y el refactor es `TDD n/a` (`tdd/SKILL.md:39`, `:41`) |
| :34, :47 | Solo `npm test`; el rojo no deja evidencia en ningún sitio |
| :67 | «Large data (10k+ items)» en la lista de casos de test unitario: rendimiento sin escenario |
| :100 | «pass^3 antes de merge» para rutas críticas: umbral sin corpus, lo que `protocol.md:65-66` rechaza |

**Destino:** **sin destino**; ya integrado en `tdd` y `outcome-evals`.

## A066 — type-design-analyzer

`1.881 bytes/50 líneas` · tools: Read, Grep, Glob · model: sonnet. Puntúa
cada tipo en encapsulación, expresión de invariantes, utilidad y aplicación.

**Comparación.** La regla concreta («que no exista un estado con `datos` y
`error` a la vez») está en `coding-baseline.md:54` (unión discriminada); las
fronteras y la elección de modelo son de `architect`. La pieza pide
«puntuaciones» (:48) sin escala ni rúbrica y sin decir qué tipos revisar (todo
el repo o el diff): no produce un resultado comparable.

**Destino:** **sin destino**.

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `agents/planner.md` · P3, tras «Deuda técnica medida» | «Una tarea que borra código o dependencias sin uso declara en sus criterios cómo se descartaron referencias dinámicas (importación o registro por cadena, reflexión, plantillas) y uso como API pública; la detección es la herramienta que el proyecto ya tenga, y su `Verificación` incluye build y tests.» |
| `skills/adversarial-review/references/lens-prompts.md` · Lente B (opcional, P3) | Tras «errores silenciados»: «(un fallback es defecto si oculta el fallo: sin aviso, registro ni estado distinguible para quien llama; degradar con aviso declarado no lo es)». |
