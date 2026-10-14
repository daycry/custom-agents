# Recuperación aumentada (RAG), SEO y extracción de specs — A053, A060, A062

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres definiciones completas: **24.203 bytes/355 líneas**.
[agents-rag-seo-specminer-reading-evidence.json](agents-rag-seo-specminer-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08/T-11.

## A053 — rag-pipeline-reviewer

`6.249 bytes/67 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisa un pipeline RAG: poda del contexto recuperado, reordenación
(reranking), evaluación con RAGAS (faithfulness, context_recall,
context_precision), citas solo a fragmentos recuperados y respuesta de
«contexto insuficiente». Salida `APPROVE / APPROVE WITH CONDITIONS / BLOCK`
con hallazgos y derivaciones.

**Comparación.** Permisos iguales a `reviewer` (solo lectura,
`agents/reviewer.md:9`), pero decide el veredicto él mismo; en el plugin lo
decide la fusión de `adversarial-review`. Ningún consumidor ha declarado un
sistema RAG; el dominio cae con ML en D-138 (aparcado). Lo general ya tiene
dueño: la política de evaluación que pide (:38-45: línea base versionada,
umbrales justificados por el proyecto, cortes por tipo de consulta, delta de
regresión permitido, sin umbral universal) es la de `outcome-evals` (corpus y
checks antes de ejecutar, `skills/outcome-evals/SKILL.md:11-14`; publicar casos y
fallos, nunca contra un umbral sin base,
`references/protocol.md:60-66`); y tratar el texto recuperado como dato y no
como instrucción ya está en
`delivery-practices/references/delivery-tools.md:81` (D-001, **ya integrado**).
El `docs/RAG-INDEX.md` de `documenter` (`agents/documenter.md:97`) es un índice
para que un agente lea la documentación, no un pipeline: no hay solape.

Defectos:

| Línea | Problema |
|---|---|
| :16 frente a :36 | Bash «solo lectura» y, a la vez, exige ejecutar el arnés RAGAS, que llama a un modelo juez: coste y red externos sin autorización explícita |
| :33 | «El primer fragmento tras reordenar debe diferir del de similitud pura» como prueba de que el reranker no es de paso: coincidir en el primero no lo demuestra; la prueba es la métrica del corpus con y sin reranker |
| :20, :30 | «top-5» como dato habitual y «volcar top-k sin filtrar» como defecto: depende del tamaño de fragmento y de la ventana; sin medir no es un hallazgo |
| :59-62 | Deriva a cuatro agentes de la fuente (`mle-reviewer`, `security-reviewer`, `performance-optimizer`, `docs-lookup`); aquí serían Lente C, Lente D y `research-first` |

**Destino:** **Especialidad de proyecto** (persona o extensión si un
consumidor declara RAG). Material para D-138 junto a S175, S176 y S220.

## A060 — seo-specialist

`2.846 bytes/71 líneas` · tools: Read, Grep, Glob, WebSearch, WebFetch · model:
sonnet. Auditoría SEO técnica: bloqueos de rastreo, `robots`, canónicas,
redirecciones, títulos, encabezados, JSON-LD, Core Web Vitals y contenido.

**Comparación.** La skill equivalente (S254) ya se decidió **Fuera del
bundle** ([skills-seo-social-graph-publisher.md](skills-seo-social-graph-publisher.md)):
lo técnico que toca al código (rendimiento medido, encabezados, texto
alternativo) es de `frontend-quality` y su mapa WCAG; el resto es dominio de
marketing. El agente no añade un rol nuevo: es una revisión de dominio con la
misma forma `[SEVERITY] ubicación/problema/arreglo` que la de `reviewer`, sin
Bash pero con red (WebSearch/WebFetch). Su «barra de calidad» (:64-67: sin
folklore SEO, sin patrones manipuladores, recomendaciones atadas a la
estructura real) es correcta.

Defectos:

| Línea | Problema |
|---|---|
| :32 | Cadenas de redirección de más de dos saltos como Critical: umbral sin fuente; el impacto depende del rastreador y del tráfico |
| :41 | «Regresiones de Core Web Vitals» sin decir con qué datos ni percentil; `frontend-quality` pide escenario medido |
| :71 | Remite a `skills/seo` como flujo canónico: la pieza que este proyecto ya dejó fuera |

**Destino:** **Fuera del bundle**, coherente con S254; persona de proyecto si
un consumidor la pide.

## A062 — spec-miner

`15.108 bytes/217 líneas` · tools: Read, Grep, Glob, Bash, Write · model:
opus. Extrae de un código existente specs de comportamiento para OpenSpec:
bloques planos `### Requirement:` (CUANDO → ENTONCES) e `### Invariant:` con
metadatos `id`, `entities`, `enforced`, `test`, en
`openspec/specs/<capability>/spec.md`, con presupuesto de lectura «muestrea y
amplía» (15 ficheros) y `Last verified` con commit.

**Comparación.** Toca tres piezas sin coincidir con ninguna:

| Pieza propia | Qué hace | Diferencia con A062 |
|---|---|---|
| `analyst` (`agents/analyst.md:43-47`, `:58-60`) | `spec.md` **hacia delante**, por conversación, aprobada por el usuario | A062 deriva la spec **del código**, sin usuario; describe lo que hay, no lo que se quiere |
| `documenter` (`agents/documenter.md:48`, `:191`) | Documentación del estado actual con evidencia; lo no verificable se marca | Describe unidades y arquitectura en prosa, no afirmaciones de comportamiento con su punto de aplicación |
| `/spec-drift` (`commands/spec-drift.md:19-30`, `:45-46`) | Contrasta los criterios de una spec `implementada` con el código de hoy: vigente/derivado/no verificable | Necesita una spec previa; A062 crea la primera |

El formato OpenSpec y su carpeta son de otra cadena: aquí la spec es la de
`docs/roadmap/<fecha>-<slug>/`. **No entra como agente** (ADR-011: la spec
tiene dueño). Lo valioso es el método para cuando una iniciativa cambia un
comportamiento **que ya existe y nadie especificó**: afirmar solo lo que el
código expresa, con dónde se aplica y qué test lo ancla; contrastar la
documentación con lo que hacen los llamantes (:192); y llevar la duda a
incógnitas en vez de inventar (:191, :196). Eso encaja en el recon de
`analyst`, que hoy no distingue comportamiento actual de comportamiento
deseado.

Defectos:

| Línea | Problema |
|---|---|
| :90, :173 | El `id` «no cambia nunca» y a la vez se deriva de `FileName.methodName`: cualquier renombrado o movimiento lo cambia y rompe el anclaje de los deltas |
| :8-10, :23 | Las restricciones de Write y Bash son prosa; nada las impone (aquí se impone con hook de guardia, ADR-007) |
| :110, :198 | `Last verified` con el commit actual: con árbol sucio el commit no representa lo leído |
| :203-204 | Afirma que `tdd-guide` leerá los `#### Scenario:` y `planner` añadirá deltas; `tdd-guide` (A065) no menciona escenarios ni OpenSpec |
| :68 | El comentario `deferred` lista ficheros `.md` en una pieza que difiere ficheros de código |

**Destino:** línea en `agents/analyst.md` (abajo). Formato OpenSpec: **Fuera
del bundle**.

## Propuestas de línea

| Fichero · sección | Texto propuesto |
|---|---|
| `agents/analyst.md` · «Reglas» (junto a criterios sin palabras vagas) | «Si la iniciativa cambia un comportamiento que ya existe y no tiene spec, el contexto registra ese comportamiento actual como afirmaciones con su punto de aplicación (`fichero:función`) y el test que lo ancla, si lo hay; lo que el código no expresa con claridad, o donde la documentación contradice a los llamantes, va a incógnitas, no a criterios. Actual y deseado no se mezclan.» |
