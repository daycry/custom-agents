# Comparación de prácticas Angular

## S014 — Componentes, reactividad, formularios y herramientas Angular

**Estado.** Ficha semántica completa; destino **propuesto**, sin integración de
producción. Resuelve la lectura que quedó pendiente en el checkpoint de
[arquitectura y operaciones](skills-architecture-operations.md). El progreso
canónico está en [tasks.md](../tasks.md), T-03; T-08 fijará el diseño conjunto.

**Identidad y lectura.** Revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`, SHA-256 del cuerpo
`28ee37a8cf63add48fffc7c8676c6368aee35f3042525e79769b5a3d4e01aed1`;
11.021 bytes/155 líneas. Se leyeron el cuerpo completo, los 35 recursos locales
completos —120.171 bytes/3.845 líneas— y las secciones pertinentes de tres
consumidores externos al directorio. [angular-reading-evidence.json](angular-reading-evidence.json)
registra IDs, hashes, rangos y reutilización de lecturas propias con hash
coincidente. Verificar hashes acredita identidad, no eficacia semántica.

**Contrato.** Ante una tarea Angular, comprueba versión, workspace, dependencias,
builder, runner y estrategia existente; selecciona la referencia de la operación
y produce código, una decisión arquitectónica o escenarios de prueba pertinentes.
Architect decide límites y alternativas; planner convierte riesgos en tareas;
implementer conserva componentes y pruebas; reviewer y qa contrastan el mismo
contrato. La guía aporta especialidad a esos roles, sin iniciar otro ciclo.

**Comparación propia.** `stack-practices` tiene referencias PHP, Python y React;
su referencia React cubre estado derivado, cleanup, respuestas obsoletas y pruebas
por interacción, pero no APIs Angular. `frontend-quality` ya exige controles
nativos, foco/teclado, estados remotos, errores asociados, historial, movimiento
reducido y mediciones. `tdd`, `unit-tests`, `api-contract` y contratos de datos
conservan sus métodos; el linter OpenAPI no prueba guards ni navegación Angular.
`delivery-practices` ya separa una declaración MCP de sus capacidades efectivas.
`capability-catalog.json` no contiene selección de stack Angular. Es cobertura
parcial de criterios transversales, no sustitución de esta especialidad.

### Contenido conservado y destinos propuestos

Decisión: **actualizar** como `skills/angular-practices/SKILL.md`, con un mapa corto
y las nueve referencias siguientes bajo su directorio `references/`. Son
especialidad y herramientas presentes en el corpus, activadas por necesidad;
no un paquete de dependencias que se instale en todos los proyectos. Cada fila
identifica un recurso completo y su contenido útil. Los ejemplos se reescriben
con versiones y fixtures coherentes antes de incorporarlos.

| Recurso leído | Criterio que se conserva | Referencia propia propuesta |
|---|---|---|
| R-47c8bcd1b934 | Anatomía y metadata; standalone según versión; plantillas y control flow, tracking y exhaustividad | `components.md` |
| R-e1edbd390693 | Inputs requeridos, transforms puros, model y compatibilidad con inputs existentes | `components.md` |
| R-590ed8e4becb | Outputs, nombres/eventos, suscripciones y cleanup; no asumir bubbling DOM | `components.md` |
| R-4a89a03ccc55 | Host bindings, colisiones con consumidor y atributos estáticos; slider requiere contrato accesible completo | `components.md` |
| R-11045afb9b08 | signal/computed, dependencias dinámicas, memoización, readonly y untracked; readonly no implica inmutabilidad profunda | `reactivity.md` |
| R-a7c5ec410a4c | linkedSignal para estado editable dependiente, conservar selección válida y tratar lista vacía | `reactivity.md` |
| R-e98b54ec26d3 | resource/httpResource, params/loader, aborto, estados, errores, hasValue y reload; lecturas frente a mutaciones | `reactivity.md` |
| R-674af3d9490f | effect para sistemas externos, cleanup y tracking síncrono; afterRenderEffect por fases y plataforma | `reactivity.md` |
| R-cc95f35e9ff9 | FormControl/Group/Array, builder, setValue/patchValue, validación, estado y contratos de reset | `forms.md` |
| R-a0e354278b00 | FormsModule/ngModel/NgForm, registro del control, estados y feedback en formularios sencillos | `forms.md` |
| R-a915a4440240 | Modelo/FieldTree/FieldState/schema, validación cruzada y async, reglas condicionales, arrays, controles y submit | `signal-forms.md` |
| R-719cdeaa86ab | Tokens, servicios, inject y composición por DI, sin filtrar instancias entre scopes | `dependency-injection.md` |
| R-ba4eb9c8566c | Servicios, providedIn y providers locales; ciclo de vida acorde al dueño | `dependency-injection.md` |
| R-a580bf113c49 | InjectionToken y providers useClass/useExisting/useValue/useFactory/multi; funciones provide* | `dependency-injection.md` |
| R-0297a37e91d8 | Contextos válidos de inject, assert y runInInjectionContext; límites síncronos | `dependency-injection.md` |
| R-6a448fa67883 | Environment/ElementInjector, jerarquía, optional/self/skipSelf/host y providers/viewProviders | `dependency-injection.md` |
| R-5961fe0d8a05 | Orden first-match, parámetros, wildcard final, redirects, pathMatch y títulos | `routing-rendering.md` |
| R-2311c0f14c28 | Carga eager/lazy, loadComponent/loadChildren y selección contextual; exports y sintaxis comprobados | `routing-rendering.md` |
| R-d8d85827b748 | Outlets principales, anidados y nombrados, eventos y datos del outlet | `routing-rendering.md` |
| R-38dc57294569 | RouterLink/navigate, rutas absolutas/relativas, query/matrix, historial y replaceUrl | `routing-rendering.md` |
| R-b5904490f704 | Guards funcionales, CanMatch y fallback, UrlTree/RedirectCommand y resultados async; autorización del servidor separada | `routing-rendering.md` |
| R-6929a9b4abef | ResolveFn, datos previos a activación, errores/redirección, feedback e inicialización de signals | `routing-rendering.md` |
| R-552e863eaa0d | Eventos, debugging y seguimiento de navegación por resultados terminales; cleanup de listeners | `routing-rendering.md` |
| R-828c6f44d983 | CSR/SSR/SSG híbrido, rutas de servidor, hydration, event replay y defer según plataforma | `routing-rendering.md` |
| R-48ffb3f964f0 | View transitions, soporte/fallback, estilos globales, nombres únicos y selección de transición | `styling-motion.md` |
| R-e8c8f4955c9f | Accordion, Listbox, Combobox/select/multiselect, Menu/Menubar, Tabs, Toolbar, Tree y Grid headless | `accessible-components.md` |
| R-1b6aca69a8fe | animate.enter/leave, completion, CSS de estados, altura, stagger/paralelo, Web Animations y DSL existente | `styling-motion.md` |
| R-00f9e1953a14 | Styles/styleUrl, encapsulación y límites de Shadow DOM, :host/:host-context, compatibilidad ng-deep y estilos externos | `styling-motion.md` |
| R-14265f040690 | Integración Tailwind/PostCSS y CSS por versión, dependencias y configuración del workspace | `styling-motion.md` |
| R-c4942d40eb1e | TestBed/ComponentFixture, actuar/esperar/assert y rendering async/zoneless | `testing.md` |
| R-68ec47921ec4 | HarnessLoader, TestbedHarnessEnvironment, predicates y API de interacción; usar harness disponible | `testing.md` |
| R-aeab52b5a816 | provideRouter, RouterTestingHarness y navegación real; instancia/DOM/guards/resolvers comprobados | `testing.md` |
| R-cc051ee21fea | Journeys E2E con runner existente, helpers/fixtures, locators accesibles y esperas por estados | `testing.md` |
| R-0ca3282fa344 | CLI compatible para generar, añadir/migrar dependencias, serve/proxy, build, test, E2E y deploy autorizado | `tooling.md` |
| R-aa965b152db3 | MCP CLI opcional, capacidades, efectos, restricciones local/read-only y configuración específica del host | `tooling.md` |

El mapa conserva elección de estrategia existente, contexto de versión, imports,
bindings, excepciones y casos límite. Accesibilidad comparte `frontend-quality`;
los tests comparten TDD/unit-tests/qa; tools y MCP comparten selección y permisos.
Una sugerencia de servidor, framework CSS o biblioteca ARIA no los instala.

### Correcciones necesarias y contraste técnico

**Versiones y workspace.** El cuerpo pide la última estable para proyectos nuevos
pero acepta cualquier `ng version` local/global sin contrastar esa condición.
Debe resolver versión solicitada, versión efectiva y compatibilidad de Node/CLI
en el workspace. Se reutilizan scripts/lockfile; un npx flotante no acredita una
versión reproducible. La regla de generar rutas con CLI también necesita corregirse:
el recurso CLI reconoce que las definiciones Routes se escriben explícitamente.
`ng build` valida compilación, no interacción, autorización o accesibilidad.
La preferencia universal por ng add contradice la instalación ARIA con npm del
otro recurso: usar schematics solo cuando el paquete/version los proporcione y
respetar el gestor y las instrucciones verificadas del workspace. Un proxy de
desarrollo con secure:false no se traslada a producción. ng e2e puede solicitar
instalación si falta un builder; comprobar el target antes de ejecutarlo. Build,
test y deploy conservan efectos distintos y la autorización pertinente.

**Reactividad y DI.** R-e98b54ec26d3 etiqueta resource como experimental;
la [API actual](https://angular.dev/api/core/resource) lo declara estable desde
v22 y reservado a lecturas, con cancelación de cargas. Hay que conservar su
estado por versión, no aplicar el marcador antiguo a todas. En R-674af3d9490f:69,
setupChart recibe width sin leerlo; la [API de afterRenderEffect](https://angular.dev/api/core/afterRenderEffect)
pasa el resultado de la fase anterior como Signal. Corregir el ejemplo si la
función espera un número y definir limpieza del widget. Efectos async necesitan
tratamiento de errores, teardown y respuestas obsoletas; no basta leer antes de
await. [runInInjectionContext](https://angular.dev/api/core/runInInjectionContext)
no mantiene inject válido tras await. linkedSignal debe manejar opciones vacías.

**Formularios por versión y dominio.** La presencia de una API no basta para
imponerla a un formulario nuevo. Signal Forms figura como
[experimental en v21](https://v21.angular.dev/api/forms/signals/form), mientras
[FormField](https://angular.dev/api/forms/signals/FormField) es estable desde v22.
La [guía de elección](https://angular.dev/guide/forms/signals/overview) conserva
Reactive Forms como opción válida para aplicaciones existentes. Separar árbol,
estado llamado y directiva; schemaPath no es FieldState. Tipos, transformaciones
y controles deben coincidir con la versión mínima y el contrato del dominio.

La prohibición universal de null del cuerpo es excesiva:
[diseño del modelo](https://angular.dev/guide/forms/signals/model-design) distingue
undefined —ausencia de campo— de null, que puede representar vacío compatible.
No convertir una edad ausente en cero para satisfacer un ejemplo. La prohibición
de value en todo control contradice los radios del propio recurso; la
[guía de Signal Forms](https://angular.dev/essentials/signal-forms) usa value para
radios/opciones y declara que select multiple no está soportado actualmente.
R-a915a4440240 lo prohíbe en un apartado pero lo recomienda en dos posteriores.
Conservar multiselección mediante una alternativa compatible probada, no copiar
ese binding. Un control ngModel necesita name cuando se registra en NgForm;
no extender esa regla sin excepción a controles standalone o fuera del formulario.

R-a915a4440240:370 usa el estado sin llamar al árbol, contrario a su propia regla.
Sus schemas iniciales referencian propiedades no declaradas; fragmentos
condicionales usan nombres/paths y funciones inconsistentes. El validador de
fecha :592 acepta un parseo inválido al devolver undefined: se requiere un error
distinto y política explícita de fecha/zona. Los ejemplos deben conservar valores
al fallar, identidad de filas y errores asociados; no basta color o console.log
del modelo personal. Ocultar un campo no decide por sí solo qué envía el servidor.

La [API submit](https://angular.dev/api/forms/signals/submit) exige un callback
que devuelve Promise, devuelve Promise<boolean> y rechaza envíos concurrentes
del mismo campo o ancestros. No es obligatorio escribir la palabra async si ya
se devuelve Promise; tampoco atribuir un doble envío a esta API sin reproducirlo.
El estado pending/submitting debe comunicarse en UI. Validación async usa el
contrato de [validateAsync](https://angular.dev/api/forms/signals/validateAsync),
con errores, cancelación/debounce y resultado por campo probados en fixture.

**Routing y render.** R-2311c0f14c28:27 tiene un backtick sobrante tras then:
corregir sintaxis y resolver el export real. Resolver convertido con toSignal
sin valor inicial/requireSync necesita tratar el valor inicialmente indefinido
según su contrato; no inferir fallo ejecutado. NavigationEnd/Cancel/Error son
resultados alternativos, no pasos de una única navegación; añadir NavigationSkipped
en el contrato de loading y liberar listeners. En R-48ffb3f964f0:46, to.url se
compara con string aunque [ViewTransitionInfo](https://angular.dev/api/router/ViewTransitionInfo)
entrega ActivatedRouteSnapshot y su [url es UrlSegment[]](https://angular.dev/api/router/ActivatedRouteSnapshot).
Comparar una URL reconstruida o criterio de ruta compatible. CSR/SSR/SSG exige
prueba de servidor, hydration y fallback; no atribuir SEO o seguridad solo al modo.

**Accesibilidad y estilos.** Conservar los ocho patrones ARIA, su elección por
intención, CSS de estados, keyboard/focus y carga diferida cuando corresponda.
El ejemplo Menu usa ngMenuTrigger pero no importa MenuTrigger en su lista;
la [guía oficial](https://angular.dev/guide/aria/menu) muestra esa dependencia.
El ejemplo Tree usa ngTreeGroup; la [API actual](https://angular.dev/api/aria/tree/TreeItemGroup)
usa ngTreeItemGroup en ng-template con ownedBy. Es diferencia a resolver por
versión, no prueba de que todos los ejemplos antiguos fallen. Ni las directivas
ni un slider incompleto acreditan labels, contraste o accesibilidad end-to-end.
Mantener la preferencia de controles nativos de frontend-quality cuando resuelven
el producto; usar patrones custom cuando sean necesarios o se soliciten.

El recurso Tailwind impone v4 a cualquier proyecto, prohíbe configuración JS y
recomienda @use para SCSS. La [guía oficial de actualización](https://tailwindcss.com/docs/upgrade-guide)
admite config JS explícita con @config y señala incompatibilidad de diseño con
preprocesadores Sass. La [integración Angular](https://tailwindcss.com/docs/installation/framework-guides/angular)
describe el flujo CSS/PostCSS; mantener v3 existente o migrar con tarea y pruebas.
La [API de encapsulación](https://angular.dev/api/core/ViewEncapsulation) marca
ExperimentalIsolatedShadowDom como experimental: no presentarlo como equivalente
estable. [animate.enter/leave](https://angular.dev/guide/animations) conserva CSS,
completion y compatibilidad del DSL sin mezclarlos en un mismo componente;
respetar movimiento reducido y plataforma, sin imponer migración general.

**Tests y CLI/MCP.** R-aeab52b5a816 atribuye router y getHarness a
RouterTestingHarness; su [API actual](https://angular.dev/api/router/testing/RouterTestingHarness)
expone navigateByUrl/routeDebugElement/routeNativeElement y fixture, no esos
miembros. Obtener Router con TestBed.inject y la instancia con navigateByUrl.
No garantizar navegación inicial a / sin initialUrl/contrato probado. Los
harnesses de componentes CDK son otra API y no están disponibles en toda UI.
Conservar tests por comportamiento, runner configurado y router real para
integración; no prohibir cualquier mock en un unit test de otro contrato.

La [documentación actual del MCP CLI](https://angular.dev/ai/mcp) presenta
devserver.* y run_target entre las tools por defecto; el recurso conserva build,
test/e2e/modernize y flags experimentales de otro contrato. No congelar esa lista:
comprobar versión y tools expuestas. run_target puede incluso desplegar un target;
inventario/conexión no autorizan ese efecto. Reutilizar el CLI del proyecto,
registrar restricciones y lifecycle del servidor y mantener configuración
Claude/Codex/OpenCode nativa. No conectar ni ejecutar npx/servidores del corpus.

### Dependencias, activación, coste e impacto

**Consumidores.** R-591e7a1672e1:146–172 incluye la especialidad en distribución;
R-03ffcc8e6e9e:39–51 la enumera en otro perfil; S229:254–275 la enlaza para
comparación entre frameworks. Se comprobaron sus secciones y búsqueda de callers
en agents/commands/skills/manifests/config. Los perfiles/generadores completos
se revisarán operativamente en T-06. Los enlaces salientes a TDD, seguridad y
patrones frontend expresan métodos relacionados, no 35 recursos adicionales.

**Dependencias reales.** Versiones de Angular/Node/TypeScript/RxJS y paquetes
core/forms/router/CLI, workspace y builder del consumidor; ARIA, CDK/Material,
Tailwind/PostCSS y runner solo cuando se usen. API/MCP y SSR dependen además del
host/plataforma. No se instalaron ni compilaron SDKs, fixtures, apps o servidores.
La consulta oficial documenta contratos; no demuestra dispatch nativo ni eficacia.

**Activación estática.** Literal: «Crea un formulario Angular con validación
asíncrona». Paráfrasis: «La selección debe mantenerse al cambiar las opciones
en esta app Angular». Negativo: «Revisa el foco del modal React» → frontend-quality
y referencia React existente. Otro negativo: «Lista mis MCP» → inventario de
extensiones, no arranque Angular. Son escenarios propuestos; selector y agentes
no ejecutados. Una mera palabra Angular en una dependencia transitiva no activa
todas las referencias ni autoriza una migración.

**Degradación/coste.** Carga inicial del mapa y después la referencia pertinente,
no las 4.000 líneas completas. Tokens/latencia null sin medición compatible.
Sin CLI/runner/servidor compatible se conserva diseño y se declara validación
pendiente; no se afirma build/test verde ni se instala una alternativa de oficio.
La guía es común a los tres runtimes, pero sus capacidades operativas se comprueban
por sesión. Ausencia de logs no demuestra uso cero.

**Impacto y validación pendiente.** T-08 debe fijar matriz de versiones y enlaces
de frontend-quality/stack-practices, selector por manifiesto y activación por
intención. La implementación actualizará catálogo, docs ES/EN, exports y evals
con dueño único por método; no duplica roles, gates ni registro de extensiones.
Fixtures mínimas deben comprobar compilación y comportamiento de formularios
(null/arrays/async/submit), reactividad/DI, guards/resolvers/redirecciones,
render híbrido, ARIA/teclado y harnesses; tools requieren esquema y despacho
reales. Eso sigue pendiente en T-09/T-10/T-12/T-14. Esta ficha y sus hashes no
se presentan como integración funcional ni cierre de T-03.
