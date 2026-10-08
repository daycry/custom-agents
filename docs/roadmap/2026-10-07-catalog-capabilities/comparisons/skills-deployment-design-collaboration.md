# Despliegue, sistema visual y perspectivas de equipo — S075–S077

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Los tres cuerpos completos suman **22.246 bytes y 714 líneas**, sin recursos
locales en sus directorios. La descripción de un pipeline, generador o sesión
no equivale a entregar un ejecutor.
[deploy-design-team-reading-evidence.json](deploy-design-team-reading-evidence.json)
conserva 20 fuentes, 19 contrapartes propias, reutilizaciones por hash y 13
contrastes oficiales. Un error del lector web y su lectura HTTP posterior válida
están diferenciados. Los nombres originales quedan en el mapa privado.
El ledger canónico sigue siendo [tasks.md](../tasks.md), T-03.

Los destinos son **propuestas para T-08**, sin integración de producción. No se
ejecutaron scripts, tests del corpus, builds de imágenes, CLI de proveedores,
despliegues, previews, modelos ni sesiones de subagentes. Los criterios siguientes
son checks estáticos preparados, no evidencia de ejecución nativa.

## S075 — Rollout, artefactos y recuperación de una entrega

**Identidad.** SHA-256
`b864abd1954570c4a469b7e1deb897e57858d25db2fd98d035ff7bca4a15b9b6`,
11.113 bytes/428 líneas, cuerpo completo, cero recursos locales. Callers
canónicos: S154/S176/S214/S217/S264, leídos solo en sus secciones pertinentes;
mapping de stack, triggers, manifiestos y tests de referencias. Se separaron
copias de otros bundles/traducciones. Esas relaciones no prueban que el pipeline
se ejecute ni cuentan como evaluación completa de esas otras skills.

**Contrato y valor.** Para preparar una aplicación, compara rolling, blue-green
y canary; relaciona compatibilidad entre versiones, imágenes de varias etapas,
checks, configuración, recuperación y operación. La salida útil es el plan de
rollout con artefacto/entorno, checks y condición de parada, además de los archivos
de CI/container del consumidor cuando se soliciten. No convierte preparar un
despliegue en autorización para publicarlo o cambiar tráfico.

**Cobertura propia.** `delivery-practices/references/delivery-tools.md` ya fija
artefacto inmutable, credenciales, versiones/digests, señales, readiness/liveness,
compatibilidad de migraciones y recuperación. S071 ya propone el detalle de
migraciones en backend; no crear otro método. El delta son las decisiones de
estrategia y evidencias del recorrido CI → artefacto → rollout → observación.
`outcome-evals` aporta comparación reproducible; qa conserva veredicto y nemesis
seguridad. Tener probes o un nombre de entorno no acredita la operación completa.

**Defectos y correcciones.**

| Observación concreta | Contrato de integración |
|---|---|
| Rolling se anuncia como zero downtime; blue-green como rollback instantáneo | Son objetivos condicionados por readiness, capacidad, drenaje, sesiones y estado compartido. Revertir tráfico no deshace datos, mensajes ni efectos externos |
| Tags de imagen con versión amplia se describen como reproducibles | Registrar digest y provenance del artefacto realmente probado; aplicar política de actualización y soporte, sin sustituir todos los stacks por una versión fija del plugin |
| Go desactiva CGO y copia un binario; Python copia site-packages/bin | Verificar requisitos nativos, arquitectura/libc, runtime libraries, permisos y arranque frío del proyecto. Una receta no demuestra que cualquier aplicación arranque |
| Healthcheck depende de herramientas/rutas que el runtime final debe contener | Probar el comando y endpoint en la imagen final. Puertos expuestos y healthcheck declarados no configuran por sí solos el routing del orquestador |
| Job deploy solo ejecuta `echo`; staging/smoke aparecen en prosa, no en el YAML | Marcar plantilla incompleta, no despliegue exitoso. Vincular ID/digest, entorno, proceso y readback real; probar las transiciones que se anuncien |
| Login al registry usa token sin permisos explícitos en el ejemplo | Resolver política efectiva y permisos mínimos del job; no depender de defaults desconocidos. Serializar/cancelar rollouts según su estado para evitar publicar una revisión anterior al final |
| Checks de dependencias secuenciales, sin deadlines, y latencia fija de 2 ms | Medir latencia real y acotar cada dependencia/total; errores y partial deben ser visibles. Proteger el endpoint detallado y mantener liveness separado de dependencia remota |
| Misma ruta siempre 200 para readiness/liveness/startup | Determinar capacidad de servir y arranque según el servicio; un endpoint constante no demuestra esquema compatible, calentamiento o disponibilidad de dependencias necesarias |
| Puerto es cualquier número coercible y el secret solo exige longitud | Validar entero/rango, config de dominio y proveedor; longitud no mide entropía. No exponer valores sensibles en diagnóstico de validación |
| Rollback agrupa imagen, proveedor y estado de migración | Separar revertir aplicación/tráfico, reparar datos y marcar historial. Conservar expand/contract y forward fix cuando el rollback no sea seguro |
| Checklist exige scaling/on-call para todo despliegue | Hacer pertinentes estos controles al tamaño y riesgo, con n/a razonado. No inventar cobertura total de errores por marcar una lista |

**Vigencia contrastada.** Los tags son mutables; Docker distingue stages y
digest, con actualización posterior explícita. La política Go mantiene una
versión mayor hasta que existan dos más nuevas; la lectura actual registra Go
1.27. El ejemplo 1.22 no puede seguir tratándose como baseline mantenida.
Alpine 3.19 tiene fin de soporte ordinario registrado el **1 de noviembre de
2025**, con extensiones «on request»; eso no convierte cada imagen antigua en
inválida ni demuestra que disponga de una extensión contratada.
[Docker](https://docs.docker.com/build/building/best-practices/),
[Go](https://go.dev/doc/devel/release),
[Alpine](https://alpinelinux.org/releases/).

npm 11 documenta lockfile coherente, flags de resolución compatibles e
include/omit para separar dependencias de build y runtime. No imponer npm a un
proyecto con otro gestor. Kubernetes distingue readiness, liveness y startup;
la pérdida temporal de una dependencia puede retirar tráfico sin matar el pod.
[npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/),
[probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).

La guía oficial de Container registry declara permisos del token; el alcance de
attestations/OIDC depende del workflow elegido. GitHub recomienda SHA completo
para acciones inmutables. No copiar versions/tags como garantía de seguridad ni
conceder permisos adicionales que el proyecto no necesita.
[Publicación de imágenes](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images),
[uso seguro](https://docs.github.com/en/actions/reference/security/secure-use).

Railway `up` documenta subida del código local, no `--commit`; detached solo
confirma encolado. El comando también puede abrir onboarding o crear recursos si
no están enlazados: resolver identidad/target antes de ejecutarlo. Vercel distingue
solicitud, estado pendiente y límites de rollback por plan; timeout del cliente
no cancela necesariamente la operación. Son contratos leídos, no llamadas hechas.
[Railway up](https://docs.railway.com/cli/up),
[Vercel rollback](https://vercel.com/docs/cli/rollback).

Prisma ORM **v7** documenta `migrate resolve --rolled-back` como estado de una
migración fallida; no ejecuta SQL inverso ni revierte una migración exitosa.
La guía debe respetar la versión del consumidor, sin mezclarla con comandos de
otra generación ni prometer recuperación de datos por cambiar metadata.
[CLI v7](https://docs.prisma.io/docs/orm/v7/reference/prisma-cli-reference).

**Decisión y destino.** Ampliar `delivery-practices` con
`references/rollout-recovery.md` y `references/ci-artifacts.md`. Mantener containers,
configuración y probes en la referencia existente, y migraciones en backend.
S032 aporta observación postdeploy; S084/S154 requieren todavía su comparación
completa antes del diseño definitivo de Docker/Kubernetes. No otro agente de
deployment ni pipeline obligatorio para todos los proyectos.

**Activación preparada.** Literal «Prepara CI y rollout canary para esta app»;
paráfrasis «Decide cómo sustituir la versión sin perder tráfico y cómo recuperarla».
Negativo «Este endpoint devuelve 500» → depuración/backend; «Sube la rama» → Git,
sin afirmar despliegue por push. El implementer produce archivos; qa comprueba
la imagen y escenario; el orquestador aplica la autorización vigente para efectos.

**Casos pendientes.** Imagen sin endpoint/binario/library; lockfile incompatible;
token sin permisos; digest probado distinto del publicado; dos releases fuera de
orden; startup lento y dependencia caída; métricas parciales o latencia sin medir;
secret/config inválidos; interrupción entre build y deploy; proveedor encolado
que termina failed; rollback con esquema irreversible y con mensajes ya enviados.
Windows/Linux y proveedores se prueban según stack/versiones realmente disponibles.

**Carga e impacto.** Referencias bajo demanda, tokens/latencia null. Recursos,
credenciales y targets son del consumidor. T-08/T-10 contenidos; T-11 handoffs;
T-12 runners/adaptadores; T-14 comprobaciones y T-15 docs/exports. No se modifica
ninguna infraestructura durante esta comparación.

## S076 — Sistema visual derivado de una interfaz existente

**Identidad.** SHA-256
`1969e4cb6cd13cdafff5f84353047d6e55cebc24e1a595ec48e6e2c666f3d8b1`,
2.815 bytes/83 líneas, cero recursos locales. Callers S001/S106/S213, triggers
y manifests relacionan consistencia visual con accesibilidad/producto. El cuerpo
propone modos y outputs; no entrega parser de flags, extractor de CSS ni plantilla
de preview que se hayan podido ejecutar aquí.

**Valor y cobertura.** Conserva tres tareas: extraer decisiones visuales reales,
proponer tokens con rationale y revisar coherencia entre componentes/estados.
`frontend-quality/references/interaction-performance.md` ya aporta foco, teclado,
estados remotos, layout/zoom, movimiento y medición. No ofrece el inventario de
color/tipografía/espaciado/shadows ni el recorrido token → CSS → preview. Ese delta
complementa frontend-quality; no sustituye pruebas de interacción o conformidad.

**Correcciones.** Diferenciar extracción observada, propuesta de normalización y
estilo aprobado. Un hex repetido puede tener dos usos semánticos; dos valores
distintos pueden ser deliberados por estado/tema. Conservar procedencia por regla,
componente y theme, variables resueltas y overrides, sin convertir una frecuencia
en decisión. La investigación de tres competidores no es requisito universal ni
necesita un MCP específico: alcance/budget y fuentes disponibles mandan.

JSON con nombre de tokens no acredita un formato interoperable. DTCG **2025.10**
define tipos/valores/referencias y ciclos como error; es un Community Group Report,
no una Recommendation/Standard de W3C. Adoptar formato y transform por versión
solo si el proyecto los necesita; mantener schema/origen para otras formas.
[Formato](https://www.designtokens.org/tr/2025.10/format/).

CSS custom properties dependen de cascade/inheritance; no equivalen a variables
globales ni sirven dentro de media queries. Los fallbacks tienen reglas de validez;
deben probarse estilos computados y themes, no solo comparar texto generado.
WCAG 2.2 AA 2.5.8 tiene tamaño de target y excepciones concretas; un score visual
de 0–10 no comprueba ese criterio ni certifica toda la norma.
[Custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties),
[Target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

Las diez dimensiones son una rúbrica editorial: anclar ejemplos, razones y n/a;
no exigir dark mode si no está en alcance ni representar «polish» como medición.
Gradientes, vidrio, tipografías o colores no son defectos por sí mismos: valorar
legibilidad, jerarquía, intención y preferencia del producto. Mantener la entrevista
y voz de S028/S029 cuando aplique; no reemplazar identidad con un preset universal.

**Decisión y destino.** Ampliar `frontend-quality` con
`references/visual-system.md` y triggers explícitos de generación/auditoría.
Conservar tokens, CSS, rationale y preview como outputs del consumidor, en sus
rutas existentes o un área acordada de `docs/design/`, sin crear archivos vacíos
en todos los proyectos. Distinguir el sistema visual de `design.md` de arquitectura.
Implementer mantiene tokens/styles/preview; documenter el rationale; architect
expone alternativas en su artefacto. S107 requiere todavía comparación completa
para cerrar solapes de dirección visual en T-08.

El preview debe usar la misma fuente/versiones de tokens, controles accesibles y
estados reales; no solo un mock de tarjetas. Escapar/validar nombres, valores y
contenido, acotar assets y URLs, y evitar ejecución o lectura externa no solicitada.
Probar clases, aliases, temas, error de datos, viewport y teclado antes de atribuir
utilidad al HTML. La falta de browser permite propuesta estática con límite visible.

**Activación preparada.** «Extrae los tokens de nuestra UI» y «Haz coherentes los
estados visuales del panel» entran; «El menú no cambia de seleccionado» va primero
a la traza de interacción/estado de frontend-quality. «Diseña la arquitectura de
datos» conserva architect/backend. Tokens bajo demanda, coste null; T-13 puede
usar la guía en el panel, pero esta ficha no verifica ni cambia el panel actual.

**Casos pendientes T-14.** Aliases cíclicos/ausentes, scopes y temas, valor CSS
inválido con fallback, mismo color con semánticas distintas, JSON inyectado en
HTML/CSS, breakpoint transformado, foco/contraste, zoom, reduced motion y preview
desfasado del CSS usado. Un score alto y ausencia de scanner errors no dan verde.
T-10/T-11/T-15 actualizarán contenido, consumidores, activación y exports.

## S077 — Perspectivas constructivas antes de planificar

**Identidad.** SHA-256
`727b093c8f8284923e54619b9193e5dee9e9ae0ea87b5fb65e1e01e0206fe621`,
8.318 bytes/203 líneas, cero recursos locales. Manifiestos/package declaran la
pieza. Test **R-dae4b1919d2c** leído completo, fuera del directorio, no ejecutado:
comprueba frases, prompt template, archivos referenciados y registro. No despacha
cuatro agentes ni demuestra ausencia de efectos. S058 se reutilizó por hash y
lectura completa anterior; el resto de relaciones no se cuenta como alta integrada.

**Valor específico.** Sobre una propuesta común, obtiene preocupaciones de
producto, arquitectura, implementación y pruebas. Cada perspectiva devuelve
reacción, preocupaciones, primera acción y pregunta; síntesis conserva conflictos.
Es diagnóstico constructivo de alcance/testabilidad antes del plan, distinto de
revisión de un diff, veredicto QA o decisión adversarial con alternativas.

**Comparación propia.** Analyst 55–105 ya concreta objetivo/alcance/criterios e
incógnitas; architect 96–164 contrasta opciones con riesgos y handoff; planner
estructura tareas/test-plan y qa ejecuta evidencia. La [propuesta S058](skills-contracts-costs-decisions.md)
conserva desacuerdo para una decisión ambigua. Ninguno necesita convertirse en
cuatro personajes permanentes ni ceder su artefacto a una conversación informal.

**Correcciones necesarias.**

| Contrato del cuerpo | Adaptación profesional |
|---|---|
| Cuatro prompts simultáneos obligatorios | Respetar capacidad real, autorización de delegación y presupuesto; cola/lotes con handles, cancelación y fallos visibles. Un solo modelo representando voces no se anuncia como agentes independientes |
| Contexto de un archivo raíz, hasta 150 palabras y cinco campos | Reutilizar spec/design/ledger vigentes y selección propia. Acotar resumen con provenance, distinguir omitido/desconocido y preservar criterios críticos; no escribir otro registro paralelo por faltar un archivo |
| Eliminar secretos o imperativos por instrucción al modelo | Redactar con límites verificables y tratar datos como datos. Una etiqueta no prueba resistencia a inyección; conservar restricciones legítimas sin obedecer instrucciones externas ni difundir valores privados |
| Tres perspectivas con la misma preocupación la convierten en blocker | Coincidencia puede venir del mismo resumen/modelo. Graduar por impacto/evidencia y criterio de aceptación; registrar desacuerdo y qué observación resolvería la tensión |
| Analysis-only en prompt | Aplicar tools/permisos efectivos por runtime; los agentes propios tienen writers, así que no invocarlos en modo habitual y asumir read-only. Separar consulta de producción de sus artefactos |
| Persistencia opcional con nombre por día y sufijo | Conservar autorización, scope, ID y concurrencia de escritura; no sobrescribir otra sesión por elegir el mismo sufijo. No guardar en memoria aceptada o tracker por defecto |

**Decisión y destino.** Consolidar con la especialidad opcional propuesta
`decision-review`, en `references/collaborative-perspectives.md`, como modo de
feedback por roles. S058 conserva deliberación adversarial; S275, composer de
equipos, necesita su ficha completa para decidir el transporte compartido en
T-08/T-11/T-12. No otro motor del ciclo ni otra revisión obligatoria por tarea.
Esta propuesta no afirma que decision-review ya exista en el plugin distribuido.

La sesión devuelve síntesis, fuentes, incertidumbres y cobertura real de voces;
las necesidades pasan al writer correspondiente. Respeta decisiones y elecciones
ya autorizadas. No marca spec/plan aprobados, qa verde, tareas completas o memoria
aceptada por consenso. [Contratos por runtime](../contracts.md) delimitan formatos
nativos: estas perspectivas no requieren inventar un cargador de «personas» ni
confundir `/personality` con un especialista de dominio.

**Activación preparada.** Literal «Dame perspectivas de producto, arquitectura,
dev y QA sobre esta propuesta»; paráfrasis «Detecta las tensiones antes de elaborar
el plan». Negativo «Revisa este diff» → adversarial-review; «Ejecuta las pruebas»
→ qa; «Contrasta una decisión go/no-go» → modo S058. «Implementa» conserva el
workflow/implementer, sin añadir automáticamente cuatro consultas.

**Casos pendientes.** Slot insuficiente, timeout/cancelación y una perspectiva
ausente; respuestas duplicadas o fuera del formato; constraint omitida por resumen;
secreto/datos con instrucciones; tres opiniones erróneas coincidentes; consulta
con permisos de escritura inadvertidos; dos sesiones guardadas a la vez; persistencia
no pedida; retorno parcial o síntesis sin dissent; formato y modelos nativos por
runtime. Tests de prosa no prueban esos comportamientos.

**Carga e impacto.** Cuatro respuestas de hasta 250 palabras más síntesis son
un presupuesto textual del método, no una medición de tokens/coste. Contexto
repetido y ejecución paralela se medirán por lote cuando exista meter compatible.
T-08/T-10 modos; T-11 roles/handoffs; T-12 transporte; T-14 pruebas y T-15 docs,
exports y retirada de referencias sustituidas. Cero integración de producción
y ninguna sesión de equipo ejecutada en este bloque.
