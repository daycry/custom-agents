# Revisores por lenguaje: React, Rust, Swift, TypeScript y Vue — A055, A058, A064, A067, A068

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **48.779 bytes/716 líneas**.
[agents-react-rust-swift-ts-vue-review-reading-evidence.json](agents-react-rust-swift-ts-vue-review-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Los cinco son `tools: Read, Grep, Glob, Bash` y `model: sonnet`: misma
superficie que `reviewer` (`agents/reviewer.md:9`), que es `opus`/`high`.
Reparten la revisión **por lenguaje** y dentro de él por tema (tabla
«Scope vs typescript-reviewer», A055:19-34 y A068:19-36), deciden ellos mismos
`Approve/Warning/Block` y piden invocarse juntos en el mismo PR.

**Comparación.** El plugin reparte la misma fase **por preocupación**, no por
lenguaje: `adversarial-review` decide qué lentes aplican y funde los
resultados (Critical/Important/Minor, `skills/adversarial-review/SKILL.md:99-101`);
`reviewer` ejecuta una lente sin corregir y sin comentar estilo
(`agents/reviewer.md:39-50`). Lente B = corrección (hooks, reactividad,
préstamos, promesas), Lente C = seguridad del diff con
`cybersecurity/references/language-patterns/<lenguaje>.md`, Lente D =
rendimiento con escenario de carga. El conocimiento por stack viene de
`stack-practices` (`references/react.md`, `coding-baseline.md` para
TypeScript) y la accesibilidad de `frontend-quality`. Diferencias que se
señalan:

| Fuente | Propio |
|---|---|
| El agente da el veredicto `Block` si hay un HIGH | La fusión de la skill gradúa; `reviewer` solo propone grado |
| Ejecuta lint, typecheck, tests y `gh pr view` antes de revisar y **se detiene** si algo está rojo (A055:42, A058:20, A064:20, A067:24-29) | Revisa el diff con la evidencia que ejecuta; un rojo ajeno al diff no impide revisar |
| Mezcla estilo y composición en HIGH/MEDIUM: funciones > 50 líneas, anidamiento > 4, componente > 200/300 líneas, orden de `derive`, `var` frente a `let` | Estilo fuera (`adversarial-review/SKILL.md:37`); tamaño y anidamiento son indicadores de `code-health`, no defectos (`coding-baseline.md:19-21`) |
| «Recomienda instalar» plugins de lint durante la revisión (A055:136, A068:159) | Revisar no instala nada |
| `MUST BE USED` en la `description` de los cinco | La activación la decide el orquestador por lentes |

Regla de stacks (ya fijada): React y TypeScript tienen consumidor; Rust, Swift
y Vue quedan aparcados (D-131, D-133, D-135). **Ningún revisor por lenguaje
entra como agente.** Dos líneas de React y TypeScript faltan en las
referencias propias; se proponen abajo.

## A055 — react-reviewer

`11.411 bytes/167 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Reglas de hooks, estado derivado, frontera RSC, Server Actions,
`dangerouslySetInnerHTML`, accesibilidad, rendimiento y formularios.

**Comparación.** Casi todo tiene dueño: estado derivado, efectos con cleanup,
reset por `key` y frontera servidor/cliente en `react.md:3-11` y `:32-36`;
`dangerouslySetInnerHTML` y `"use server"` como endpoint público disparan la
Lente C (`lens-c-heuristics.md:17-19`); `href` con `javascript:` está en
`language-patterns/javascript-typescript.md:50`; accesibilidad en
`frontend-quality/references/accessibility-criteria.md:13-31`; memoización solo
con medida en `react.md:66`. **No cubierto:** la `key` de listas dinámicas
(A055:94); `react.md:9` solo trata `key` para resetear estado.

Defectos:

| Línea | Problema |
|---|---|
| :125, :130-131 | `eslint --ext`: la opción no existe con la configuración plana de ESLint 9 |
| :87 | `target="_blank"` sin `rel="noopener"` como HIGH de accesibilidad: es seguridad, y los navegadores actuales ya aplican `noopener` por defecto con `_blank` |
| :43 | Falta de `exhaustive-deps` en la configuración del lint como HIGH: es configuración del proyecto, no un defecto del diff |
| :55 | «Detén la revisión» ante un `dangerouslySetInnerHTML` sin documentar: el revisor reporta, no bloquea el resto |

**Destino:** línea en `react.md` (abajo).

## A058 — rust-reviewer

`5.656 bytes/103 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Seguridad, errores, propiedad y tiempos de vida, concurrencia, calidad y
rendimiento en Rust.

**Comparación.** Rust aparcado (D-131); la parte de seguridad ya está en
`language-patterns/rust.md` para la Lente C. Defectos:

| Línea | Problema |
|---|---|
| :21 | `git diff HEAD~1` o `main...HEAD` fijos: justo lo que A067:21 prohíbe («no fijar `main`») |
| :44 | `Box<dyn Error>` en librerías como CRITICAL: decisión de API, no un fallo |
| :41 | `let _ = result;` como «error silenciado» CRITICAL: es el descarte explícito; el problema es descartarlo sin motivo |
| :64-65, :82 | Tamaño, anidamiento y orden de `derive` como HIGH/MEDIUM: estilo |

**Destino:** **sin destino**; D-131 queda como está.

## A064 — swift-reviewer

`7.325 bytes/116 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Opcionales forzados, errores, concurrencia, memoria (ARC), diseño por
protocolos y rendimiento en Swift.

**Comparación.** Swift aparcado (D-133); `language-patterns/swift-kotlin.md`
cubre la seguridad. Defectos:

| Línea | Problema |
|---|---|
| :21 | Mismo `HEAD~1`/`main` fijo que A058 |
| :33 | «Keychain o variables de entorno» para secretos: una app iOS publicada no tiene variables de entorno, y un secreto dentro del binario no se protege |
| :30, :74 | Desempaquetado forzado como CRITICAL y herencia frente a protocolos como HIGH: graduación por preferencia |

**Destino:** **sin destino**; D-133 queda como está.

## A067 — typescript-reviewer

`9.068 bytes/124 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Seguridad, tipos, asincronía, errores, patrones de Node y rendimiento en
TypeScript/JavaScript; el bloque React queda como reserva.

**Comparación.** `coding-baseline.md:39-54` es el dueño de TypeScript: datos
externos como `unknown` validados en el borde, `catch` con `unknown`, `cause`
al relanzar, `Promise.all` frente a `allSettled` y uniones discriminadas. La
contaminación de prototipo y `eval` están en
`language-patterns/javascript-typescript.md:20-42`. **No cubierto:** la
promesa sin esperar (en un handler, un constructor o `forEach(async …)`,
A067:54-57).

Defectos:

| Línea | Problema |
|---|---|
| :63 | Error boundaries «alrededor de subárboles async y de carga de datos»: no capturan errores asíncronos ni de handlers (`react.md:93-97`) |
| :69 | «`any` implícito por falta de tipo de retorno»: TypeScript infiere el retorno; `noImplicitAny` no salta por eso |
| :55 | Las `await` secuenciales como HIGH con «considera `Promise.all`»: cambia orden, límites y semántica de fallo (`coding-baseline.md:53`) |
| :29, :105 | `eslint --ext` (ESLint 9) y «si el lint falla, detente» |
| :61 | «Envolver siempre `JSON.parse`»: depende de si la entrada ya está validada |

**Destino:** fila en `coding-baseline.md` (abajo).

## A068 — vue-reviewer

`15.319 bytes/206 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Reactividad, composables, plantillas, componentes, Router, Pinia, SSR de Nuxt,
rendimiento y formularios en Vue.

**Comparación.** Vue/Nuxt aparcado (D-135; su línea de render determinista ya
está en `react.md:10`). `v-html` y `:href` están en
`language-patterns/javascript-typescript.md:74-75`. Defectos:

| Línea | Problema |
|---|---|
| :84 | `key={index}` con sintaxis JSX en una regla de Vue (`:key="index"`) |
| :113 | `process.client`: obsoleto en Nuxt 3 en favor de `import.meta.client` |
| :147 | `eslint --ext` (ESLint 9) |
| :91, :140 | La misma regla de «más de 300 líneas» dos veces, en HIGH y en MEDIUM |

**Destino:** **sin destino**; D-135 queda como está.

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `skills/stack-practices/references/react.md` · «Composición, datos y pruebas React» | «Las listas que se reordenan, insertan o borran llevan `key` estable del dato; el índice solo vale si la lista es fija. Con índice, el estado local y el foco pasan a la fila equivocada.» |
| `skills/stack-practices/references/coding-baseline.md` · tabla TypeScript | Fila «Promesa sin esperar»: «Toda promesa se espera, se devuelve o maneja su rechazo; `forEach` no espera callbacks `async` (usa `for…of` o la fila "Varias promesas")» · escenario: «Un rechazo dentro de `forEach(async …)` no llega al `catch` y el handler ya respondió éxito.» |
