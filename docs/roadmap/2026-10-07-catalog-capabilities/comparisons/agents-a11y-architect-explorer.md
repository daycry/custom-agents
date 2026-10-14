# Diseño, accesibilidad y exploración — A001, A003, A006, A007

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **19.725 bytes/527 líneas**. [agents-a11y-architect-explorer-reading-evidence.json](agents-a11y-architect-explorer-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las cuatro.** Bloque «Prompt Defense Baseline» idéntico (líneas 8-15, mismo
texto en los 17 agentes A001–A017). Pide no emitir código «salvo que la tarea lo
requiera y esté validado», y A001 entrega código como primera salida. El plugin ya
trata el contenido externo como dato en `delivery-practices`
(`references/delivery-tools.md:81`, D-001). **Sin destino.**

## A001 — a11y-architect

`7.339 bytes/149 líneas` · tools: Read, Write, Edit, Grep, Glob · model: sonnet.
Arquitecto de accesibilidad WCAG 2.2 para web, iOS y Android. Genera el código del
componente, describe el árbol de accesibilidad y mapea criterios. Incluye una plantilla ADR-ACC.

**Comparación.** Los criterios web ya tienen dueño en `frontend-quality`:
`references/accessibility-criteria.md:13-32` (mapa WCAG 2.2 con nivel y excepciones),
`references/interaction-performance.md` (modal y área de pulsación, D-026/D-027) y la
persona `agent-kits/shared/personas/frontend.md:3` (foco, etiquetas, contraste, teclado)
para la Lente B y los subagentes con `Tipo: frontend`. Escribir el componente es del
`implementer`, único que toca código (`docs/agents/ROLES.md:31`). A001 tiene Write/Edit
sin rama, sin ledger y sin `Verificación`. Una decisión de diseño la abre `architect`, que
deja el ADR como propuesta (`agents/architect.md:138-144`). La plantilla ADR-ACC (líneas 114-118)
marca **Accepted** como estado de partida, y eso choca con ADR-018: solo el curador aprueba. Defectos de la fuente:

| Línea | Dice | Corrección |
|---|---|---|
| 82 | Indicador de foco de alto contraste = SC 2.4.11 | 2.4.11 es «Foco no oculto (mínimo)», AA; la apariencia del foco es 2.4.13, AAA (`accessibility-criteria.md:22` ya los separa) |
| 38 | «24x24 spacing or 44x44 target size» | Mezcla 2.5.8 (AA: 24×24 o espaciado equivalente) con 2.5.5 (AAA: 44×44); la fila de D-027 ya distingue ambos |
| 149 | Depende de la skill `accessibility` | No forma parte de la definición; las correspondencias nativas siguen aparcadas (D-113) |

**Destino:** **Sin destino.** Lo web ya está integrado en `frontend-quality`
(D-026, D-027, D-030) y en la persona `frontend`. Lo nativo sigue aparcado (D-113).

## A003 — architect

`7.276 bytes/220 líneas` · tools: Read, Grep, Glob · model: opus. Arquitecto
generalista: estado actual, requisitos, propuesta, trade-offs, principios, patrones,
ADR, checklist de diseño de sistema y anti-patrones.

**Comparación.** El `architect` propio cubre la misma fase con contrato más estricto.
Parte de una spec aprobada y redacta 2-3 opciones con la misma tabla de
complejidad, riesgo, coste y reversibilidad (`agent-kits/architect/templates/design.md:44-80`).
Recomienda una, pero la elige el usuario en dos pasadas (`agents/architect.md:109-127`).
Exige impacto por ruta real (`:105-107`, `design.md:102-109`) y deja el ADR como propuesta (P5).
En la fuente, «Decision: Final choice» la toma el agente. Sus tools son de solo lectura,
pero se le pide «create ADRs», que no puede escribir. Su ADR de ejemplo nace «Accepted»
(ADR-018). La sección «Project-Specific Architecture» (195-218) fija un stack (Next.js,
Supabase, Redis) y escalones de 10K a 10M usuarios sin medida que los respalde. Además,
eleva «spread operators» a decisión de arquitectura. Los anti-patrones (183-193) no cambian el comportamiento (D-069).

Lo que el plugin **no** tiene: el checklist de requisitos no funcionales (líneas
163-167: latencia, throughput, disponibilidad, recuperación). `analyst` pide criterios
«medibles si se puede» y restricciones (`agents/analyst.md:72-73`), pero no nombra
esos requisitos. El `design.md` solo los recoge si la spec los trae.

**Destino:** línea en `agents/analyst.md`, dimensión 5: «incluye los requisitos no
funcionales que condicionen el diseño (volumen, latencia, disponibilidad,
recuperación) con la cifra que dé el usuario o un documento. Sin cifra, el requisito
va a incógnitas; nunca se inventa un umbral». El resto, **sin destino**.

## A006 — code-architect

`2.525 bytes/80 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Diseña una
funcionalidad a partir de los patrones del repo. Entrega ficheros a crear y modificar,
interfaces, flujo de datos y orden de construcción.

**Comparación.** Queda entre `architect` y `planner`. Del `architect` toma el impacto
por ruta real (`design.md:102-109`; «sin rutas reales no hay diseño»,
`agents/architect.md:107`). Del `planner`, la descomposición y el orden (`agents/planner.md:88`).
Da una sola propuesta, sin alternativas ni validación del usuario. El propio exige
2-3 opciones o declarar el diseño trivial (`agents/architect.md:157-159`). El orden
«types → core → integration → UI → tests → docs» (líneas 50-55) va capa por capa, al
contrario que las rebanadas verticales de `planner.md:88` (D-095), y deja los tests al
final, contra `tdd`. «Simplest architecture / no speculative abstractions» ya está en
`skills/stack-practices/references/coding-baseline.md:14`.

**Destino:** **Sin destino.**

## A007 — code-explorer

`2.585 bytes/78 líneas` · tools: Read, Grep, Glob · model: sonnet. Antes de construir,
traza puntos de entrada, flujo de ejecución, capas, patrones y dependencias de una funcionalidad.

**Comparación.** El reconocimiento es un paso de cada rol que lo necesita, no un rol
propio: `agents/analyst.md:103`, `agents/planner.md:86` y `agents/architect.md:105-107`.
Todos comparten `agent-kits/shared/read-discipline.md:11-17`: grep antes de Read, muestra
representativa y, si se delega, «que devuelva hallazgos (rutas + líneas + resumen)».
Sus permisos son mínimos y correctos. La plantilla de salida (entradas, flujo, ficheros
clave, dependencias) está más estructurada, pero no aporta ninguna regla que cambie
el comportamiento. El contexto citado de AST ya lo da `agent-kits/shared/code-context.py`.
Un agente aparte duplicaría un paso que ya tiene cuatro dueños (ADR-011).

**Destino:** **Sin destino.**
