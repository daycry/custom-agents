# Resolutores de build: PyTorch, React, Rust y Swift — A052, A054, A057, A063

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **31.777 bytes/671 líneas**.
[agents-pytorch-react-rust-swift-build-reading-evidence.json](agents-pytorch-react-rust-swift-build-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

Los cuatro comparten forma: `tools: Read, Write, Edit, Bash, Grep, Glob`,
`model: sonnet`, comandos de diagnóstico, tabla error → causa → arreglo,
«arreglos quirúrgicos», parada tras tres intentos y salida
`[FIXED] fichero:línea` + `Status: SUCCESS/FAILED`.

**Comparación.** No hay rol nuevo: es la fase «corregir código» con dos
dueños propios. `implementer` es el único agente que toca código
(`agents/implementer.md:89-90`: cambio mínimo, compilar, lint y tests de la
zona, `Verificación` con salida pegada). `debug-root-cause` es el método cuando
el fallo resiste (`skills/debug-root-cause/SKILL.md:14-30`: reproducción
mínima, aislamiento con descartes, hipótesis probada; `:91-98`: «el síntoma no
es la causa»). La parada a los tres intentos ya existe como bucle acotado de
`/dev-cycle` (`commands/dev-cycle.md:409` y `:413`) y el gancho del tercer rojo
llama a `debug-root-cause`. La prohibición de silenciar (`#[allow]`,
`// swiftlint:disable`, `@ts-ignore`, `warnings.filterwarnings`) la comprueba
la Lente A en el diff («Puertas relajadas»,
`skills/adversarial-review/references/lens-prompts.md:20`). Diferencias reales
frente a los dueños: el resolutor decide solo, sin ledger ni criterio de
aceptación, con Write/Edit y sin puerta de alcance (`scope-check.py`); y su
«verde» es que compila, no que la tarea cumpla.

**Lo que ningún dueño dice:** `debug-root-cause` no trata el build como caso.
Las cuatro piezas coinciden en un procedimiento útil y general: el comando de
build del proyecto es la reproducción mínima, un error cada vez y build de
nuevo tras cada arreglo; el error nuevo que aparece después es un diagnóstico
nuevo y no se agrupa con el anterior (A054:83, A054:186).

**Destino común:** una línea en `skills/debug-root-cause/SKILL.md`, Fase 1
(propuesta abajo). Los cuatro agentes: **sin destino** como pieza (ADR-011).

## A052 — pytorch-build-resolver

`6.499 bytes/129 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model:
sonnet. Errores de ejecución de PyTorch y CUDA: formas de tensores,
dispositivo, gradientes, `DataLoader` y precisión mixta.

**Comparación.** ML no tiene consumidor declarado: `stack-practices/ml.md`
sigue aparcado (D-138, con S175, S176 y S220). El método es el de
`debug-root-cause`; la tabla de errores sería material de esa referencia.
Defectos a no copiar:

| Línea | Problema |
|---|---|
| :59, :95 | `torch.cuda.empty_cache()` como arreglo de memoria agotada: solo devuelve al driver bloques en caché sin uso; no libera tensores vivos |
| :62 | «Evitar relu in-place»: la misma contradicción ya anotada en S220 (in-place falla solo cuando autograd necesita el valor) |
| :66 | `retain_graph=True` como arreglo de «grafo ya liberado»: suele tapar un grafo reutilizado entre iteraciones (estado sin `detach`) y retiene memoria; contradice «causa raíz» (:106) |
| :57, :121 | El arreglo de ejemplo cambia `nn.Linear(256, 10)` por `(512, 10)`: cambia la forma de los parámetros e invalida checkpoints, pese a «no cambiar la arquitectura» (:102) |
| :77-78 | `torchsummary` es un paquete de terceros: instalarlo para diagnosticar no es una lectura |
| :96 | `model.gradient_checkpointing_enable()` es API de Hugging Face Transformers, no de `nn.Module` (`torch.utils.checkpoint`) |
| :97 | `torch.cuda.amp.autocast()` está obsoleto desde PyTorch 2.4 en favor de `torch.amp.autocast("cuda")` |

**Destino:** **sin destino**; material para D-138 si un consumidor declara
PyTorch.

## A054 — react-build-resolver

`11.187 bytes/215 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model:
sonnet. Detecta el sistema de build (Next.js, Vite, Rsbuild, CRA, webpack,
Parcel, Bun) y corrige errores de JSX/TSX, configuración del bundler,
hidratación y frontera servidor/cliente.

**Comparación.** React es stack declarado. `stack-practices/references/react.md`
ya cubre el render determinista para la hidratación (`:10`), la frontera de
secretos en frameworks híbridos (`:10-11`, `:32-33`) y que `vite build` no
comprueba tipos (`:38-42`). Falta un caso de la pieza que sí es de React y no
de un bundler: **«Invalid hook call» con hooks bien escritos** suele ser React
duplicado en `node_modules` (A054:157, :164-173), y `react`/`react-dom` se suben
juntos con `@types/react` en la misma major.

Defectos:

| Línea | Problema |
|---|---|
| :53-57 | «Respeta lo configurado» y a continuación lanza `npm`, `pnpm`, `yarn` y `bun` seguidos; el gestor sale del lockfile |
| :94 | `npm i -D @types/react @types/react-dom` sin versión, dos filas antes de exigir la misma major que `react` (:96) |
| :123 | Arreglo «envolver la función en una Server Action»: crea un endpoint público invocable desde el cliente; la Lente C lo trata como tal (`lens-c-heuristics.md:19`) y la propia fuente lo marca crítico sin autorización (A055:57, :80) |
| :148 | `typeof window !== 'undefined'` durante el render como arreglo de hidratación: produce HTML distinto en servidor y cliente, que es justo el desajuste |
| :177-179 | Tailwind con `content` y directivas `@tailwind`: es la configuración de la v3; en la v4 la entrada es `@import "tailwindcss"` |
| :23 | Remite a un `typescript-build-resolver` «futuro» que no existe en la fuente |

**Destino:** línea en `skills/stack-practices/references/react.md`
(propuesta abajo).

## A057 — rust-build-resolver

`6.857 bytes/157 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model:
sonnet. `cargo check`, préstamos y tiempos de vida, traits, `Cargo.toml`,
features y avisos de clippy.

**Comparación.** Rust aparcado (D-131). Método: `debug-root-cause`. Defectos:

| Línea | Problema |
|---|---|
| :56 | `Cell`/`RefCell` para un error de préstamo: lleva la comprobación a tiempo de ejecución (pánico); no es causa raíz |
| :58 | `.clone()` como arreglo de «cannot move out of», cuando su pareja `rust-reviewer` marca HIGH ese mismo clon (A058:48) |
| :62 frente a :131 | Prefijar con `_` silencia el aviso igual que el `#[allow(unused)]` que prohíbe |
| :38 | `cargo audit` en un arreglo de build: es cadena de suministro (`nemesis`/`dependency-upgrade`) |
| :111 | `cargo update` completo como «último recurso» sin pedir permiso: cambia todo el lockfile |

**Destino:** **sin destino**; D-131 queda como está.

## A063 — swift-build-resolver

`7.234 bytes/170 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model:
sonnet. `swift build`/`xcodebuild`, conformidad de protocolos, `Sendable`,
SPM y firma de código.

**Comparación.** Swift aparcado (D-133). Su condición de parada correcta
—provisioning o certificado ausente es acción del usuario (:157)— coincide con
la de `debug-root-cause`. Defectos:

| Línea | Problema |
|---|---|
| :87 | `swift package reset` como paso de rutina: borra el estado de paquetes y fuerza otra descarga |
| :119 | `security find-identity -v -p codesigning` lee identidades del llavero del usuario; no es necesario para diagnosticar el build |
| :146 | Prohíbe `@unchecked Sendable` «sin verificar», sin decir cómo se verifica |

**Destino:** **sin destino**; D-133 queda como está.

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `skills/debug-root-cause/SKILL.md` · Fase 1 | «En un fallo de build o compilación, la reproducción mínima es el comando de build del proyecto (gestor según lockfile). Corrige un error cada vez y vuelve a compilar; un error nuevo que aparece después es otro diagnóstico, no se arregla en el mismo cambio. Silenciar el aviso o el tipo no es un arreglo (Lente A, puertas relajadas).» |
| `skills/stack-practices/references/react.md` · «Composición, datos y pruebas React» | «Un "Invalid hook call" con hooks bien escritos suele ser React duplicado: `npm ls react` (o el equivalente del gestor) debe mostrar una copia. `react` y `react-dom` se suben juntos, con `@types/react` en la misma major; saltar de major es una tarea aparte.» |
