# Comandos de revisión: por lenguaje, de PR y de doble modelo — C073, C076, C080, C082, C084, C094

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis definiciones completas: **32.046 bytes/1.028 líneas**. [commands-c4-review-reading-evidence.json](commands-c4-review-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Los seis son **puertas de entrada a la fase de revisión**, que en el plugin tiene
un dueño de método y un ejecutor: la skill `adversarial-review` decide lentes,
fusión, graduación y bucle (`skills/adversarial-review/SKILL.md:77-124`) y el
agente `reviewer` ejecuta una lente en solo lectura (`agents/reviewer.md:9`,
`:45-50`). `/dev-cycle` la invoca en la Fase 3 (`commands/dev-cycle.md:408`) y
la skill acepta el modo **sin plan** sobre una rama o rango
(`SKILL.md:45`). Ningún comando propio de revisión existe ni hace falta: la
petición «revisa este diff» ya activa la skill.

Los cuatro por lenguaje (C073, C076, C082, C094) envuelven a los agentes ya
comparados en [agents-php-python-tests-mle.md](agents-php-python-tests-mle.md)
(A051) y [agents-react-rust-swift-ts-vue-review.md](agents-react-rust-swift-ts-vue-review.md)
(A055, A058, A068). Sus decisiones se respetan: ningún revisor por lenguaje entra
como pieza; las dos líneas propuestas allí **ya están integradas**
(`skills/stack-practices/references/python.md:29-30`, argumento mutable;
`react.md:31`, `key` estable). Rust y Vue siguen sin especialidad (D-131, D-135).
Aquí solo se compara lo propio del comando: qué ejecuta antes de revisar, qué
decide y qué escribe.

| Rasgo del comando (los cuatro) | Plugin |
|---|---|
| Ejecuta `pip-audit`/`safety`, `npm audit` o `cargo audit` como parte de la revisión (C073:70-71, C076:95, C082:68, C094:94) | Auditoría de dependencias con red: `nemesis` (SAST, agente 4 de `cybersecurity`) o `dependency-upgrade`; la Lente C mira solo lo que el diff introduce (`SKILL.md:35-36`) |
| Veredicto propio `Approve/Warning/Block`, con `Block` ante cualquier HIGH (C073:164-170) | La fusión gradúa Critical/Important/Minor por definición (`SKILL.md:95-102`); el cierre lo decide el orquestador |
| HIGH de estilo que bloquea el merge: comprensiones, `isinstance`, `type()` (C073:42-43), componentes de más de 200/300 líneas (C076:76, C094:72) | Estilo fuera por regla dura (`SKILL.md:22-24`, `reviewer.md:41-43`) |
| Recomienda ejecutar `black` sobre los ficheros (C073:160-161) | La revisión no reescribe; un formateo es trabajo de `implementer` dentro de una tarea |
| Lanza dos agentes «sin solape por diseño» (C076:39, C094:40) | Las lentes se reparten por preocupación y la fusión deduplica por `fichero:línea` (`SKILL.md:97-98`); el solape no se presupone |

Escenarios comunes a los cuatro (estáticos, sin routing nativo ejecutado):
**positivo** «revisa el diff de esta rama de Python/React» → `adversarial-review`
en modo sin plan, con `stack-practices` como referencia del `reviewer` (o
`/work-context` si el usuario pide primero qué guías aplican);
**negativo** «audita las dependencias con pip-audit/npm audit» → `nemesis`, no la
revisión del diff.

## C073 — python-review

`6.657 bytes/297 líneas` · tools: no declara · model: no declara. Envuelve a
`python-reviewer`: `git diff`, `mypy`, `ruff`, `black --check`, `isort`, `bandit`,
`pip-audit`, `safety`, `pytest --cov=app`, e informe por severidad con «Common Fixes».

- **Artefactos:** ninguno en disco; informe en conversación. Dueño propio del informe: la sección «Revisión de dos lentes» del ledger, escrita por `adversarial-review` (`SKILL.md:146-152`).
- **Despacho:** un agente por lenguaje; sin bucle ni traspaso entre intentos.
- **Disparador:** «revisa mi código Python antes de commitear».

**Comparación.** Cubierto por la decisión común y por A051. Propio del comando:
`pytest --cov=app` (C073:74) supone un paquete `app`, cuando `coverage-gate.py`
detecta el stack (`skills/unit-tests/SKILL.md:61-71`). La tabla de versiones
(C073:288-295) atribuye «Type hints 3.5+» sin distinguir anotaciones de variables
(3.6) ni `X | None` en tiempo de ejecución (3.10), y «Type unions» aparece con
entidades HTML escapadas (`&#96;x &#124; None&#96;`) que no se renderizan como código.
FastAPI/Flask/Django (C073:179-201): aparcados (D-129).

**Destino:** **Sin destino.** Ya integrado en `python.md` y `adversarial-review`.

## C076 — react-review

`5.820 bytes/170 líneas` · tools: no declara · model: no declara. Envuelve a
`react-reviewer` y pide `typescript-reviewer` al lado; `eslint` con
react-hooks/jsx-a11y, `tsc --noEmit`, `npm audit`.

- **Artefactos:** ninguno; informe en conversación (mismo dueño que C073).
- **Despacho:** dos agentes por lenguaje en el mismo PR.
- **Disparador:** «revisa los componentes React de este PR».

**Comparación.** Cubierto por A055 (decisión y defectos). Propio del comando:
`npx eslint . --ext .tsx,…` (C076:83, :90-92) no funciona con la configuración
plana de ESLint 9, y la falta de `eslint-plugin-react-hooks` se marca como HIGH
de configuración (C076:98): es configuración del proyecto, no un defecto del
diff. La accesibilidad tiene dueño en `frontend-quality`.

**Destino:** **Sin destino.** Ya integrado en `react.md:31` y la Lente B/C.

## C082 — rust-review

`3.898 bytes/142 líneas` · tools: no declara · model: no declara. Envuelve a
`rust-reviewer`: `cargo check`, `clippy -D warnings`, `fmt --check`, `cargo test` y
`cargo audit`, y **se detiene si alguno falla** (C082:11).

- **Artefactos:** ninguno.
- **Despacho:** un agente por lenguaje.
- **Disparador:** «revisa este cambio de Rust».

**Comparación.** Rust aparcado (D-131); seguridad en
`cybersecurity/references/language-patterns/rust.md` para la Lente C. Propio del
comando: `git diff HEAD~1` o `main...HEAD` fijos (C082:12), y la puerta «stop if
any fail» incluye `cargo test` completo: un rojo ajeno al diff impide revisar,
cuando el revisor propio revisa con la evidencia que ejecuta. Contradicción
interna: «Use `/rust-test` first» (C082:134) y a la vez el comando ya corre los tests.

**Destino:** **Sin especialidad** hasta que un consumidor declare Rust (D-131).

## C094 — vue-review

`5.813 bytes/174 líneas` · tools: no declara · model: no declara. Envuelve a
`vue-reviewer` y pide `typescript-reviewer`; `eslint` con plugin Vue, `vue-tsc`,
`npm audit`.

- **Artefactos:** ninguno.
- **Despacho:** dos agentes por lenguaje.
- **Disparador:** «revisa los `.vue` de este PR».

**Comparación.** Vue/Nuxt aparcado (D-135); `v-html` y `:href` en
`language-patterns/javascript-typescript.md` para la Lente C. Propio del comando:
`--ext` con ESLint 9 (C094:84, :90) y `vue/no-v-html: warn` como «targeted
security rule» (C094:90) mientras el mismo texto clasifica `v-html` sin sanear
como CRITICAL (C094:46): la regla automática queda por debajo del criterio.

**Destino:** **Sin especialidad** (D-135).

## C080 — review-pr

`1.343 bytes/37 líneas` · tools: no declara · model: no declara. Revisión de un PR
(`gh pr view`) con seis agentes: `code-reviewer`, `comment-analyzer`,
`pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer` y
`code-simplifier`; deduplica, ordena y solo informa con confianza ≥ 80.

- **Artefactos:** ninguno en disco.
- **Despacho:** seis agentes en abanico; `--focus` elige uno.
- **Disparador:** «revisa el PR 123».

**Comparación.** Los seis ejecutores tienen ficha en T-04: `pr-test-analyzer`
(A050) y `silent-failure-hunter` (A061) quedan cubiertos por las Lentes A y B y
`coverage-check.py`; `type-design-analyzer` (A066) por `coding-baseline.md`;
`code-simplifier` propone refactors, excluidos por la regla dura
(`SKILL.md:37`). Lo propio del comando:

| Fuente | Plugin |
|---|---|
| «Confianza ≥ 80» como filtro (C080:33) | La confianza es autodeclarada; aquí el filtro es `fichero:línea` + escenario (`reviewer.md:91-92`) |
| «Important: … style violations» (C080:36) | Estilo descartado |
| Entrada por número o URL de PR con `gh` (C080:9, :16) | El modo sin plan pide rama o rango y, si falta, pregunta la base o usa `merge-base` (`SKILL.md:45`); no resuelve un PR |

La última fila concreta la decisión ya fijada «Revisión reproducible: base/head/rango
fijados» de [commands-workflow-comparison.md](commands-workflow-comparison.md)
(línea 17), cuyo destino es el método de revisión. Publicar en el PR no se adopta:
la publicación separada de la revisión local ya está decidida allí.

Escenarios: **positivo** «revisa el PR 123» → `adversarial-review` sin plan con
base y head del PR; **negativo** «simplifícame este código» → no es revisión
(`implementer` dentro de una tarea, o `quick-implement`).

**Destino:** línea en `skills/adversarial-review/SKILL.md`, tabla «Entradas», fila
«Sin plan» (propuesta abajo).

## C084 — santa-loop

`8.515 bytes/208 líneas` · tools: no declara · model: no declara. Dos revisores
independientes (Claude Opus + Codex/Gemini/Antigravity o, en su defecto, otro
Claude) con rúbrica PASS/FAIL; si alguno falla, se corrige todo, se commitea y se
relanza con revisores nuevos hasta 3 rondas; con NICE, `git push -u origin HEAD`.

- **Artefactos:** un commit por ronda (`fix: address santa-loop review findings (round N)`) y un push. Dueños propios: los commits son de `implementer`/Fase 6 por tarea `T-XX` (`commands/dev-cycle.md:494`); la integración, del orquestador, que pregunta y no mergea por defecto (`:496`).
- **Despacho:** Agent `code-reviewer` con `model: opus` + subshell que elige backend externo.
- **Disparador:** «que lo revisen dos modelos antes de subirlo».

**Comparación.** La skill que envuelve (S244 `santa-method`) ya quedó **sin
destino** en [skills-rfc-dag-ledger-santa.md](skills-rfc-dag-ledger-santa.md). El
plugin ya tiene revisores de contexto fresco en paralelo, bucle acotado a 3 y
escalado al usuario (`SKILL.md:114-124`). Lo propio del comando choca con
contratos propios:

| Línea | Problema |
|---|---|
| :149 «Fix every flagged issue» | Sin rebate con evidencia: se corrigen también los gaps erróneos (`SKILL.md:104-112`) |
| :154 revisores «sin memoria de rondas previas» | El plugin traspasa la tabla del intento anterior para no reabrir lo juzgado (`SKILL.md:120-124`) |
| :113-123 envía la rúbrica y **el contenido completo de los ficheros** a Codex o Gemini | Salida de código del proyecto a otro proveedor sin opt-in explícito |
| :119, :123 fija `-m gpt-5.4` y `gemini-2.5-pro`; :203 pide usar el contrato de selección de cada backend | Contradicción interna; el modelo del revisor propio lo resuelve `model-tier.py` (`SKILL.md:82-83`) |
| :172-176 push automático con NICE | Un veredicto de revisión no autoriza publicar (`dev-cycle.md:496`) |
| :151-153 un commit por ronda | Mezcla tareas; aquí cada commit es `T-XX` |

La diversidad de modelo entre revisores no existe en el plugin y no hay medida
que la justifique; queda anotada sin destino.

Escenarios: **positivo** «revisión adversarial de la rama antes del PR» →
`adversarial-review`; **negativo** «súbelo cuando lo aprueben» → la revisión no
publica: Fase 6 de `/dev-cycle` pregunta el flujo de integración.

**Destino:** **Sin destino.**

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `skills/adversarial-review/SKILL.md` · «Entradas — dos modos», fila «Sin plan» | Añadir: «Si el usuario da un PR (número o URL) y `gh` responde, base y head salen de `gh pr view <n> --json baseRefName,headRefOid`; se revisa `git diff <base>...<headRefOid>` y se anota el SHA. Sin `gh` o sin acceso, pregunta la base; no se publica nada en el PR.» |
