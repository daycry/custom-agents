# Comparación de identidad, voz, navegador y runtime

Fichas S028–S032 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Se leyeron los cinco cuerpos y
los nueve recursos locales completos. [brand-ui-reading-evidence.json](brand-ui-reading-evidence.json)
conserva hashes, tamaños, rangos, reutilizaciones y contrastes oficiales.
Los fragmentos de otros callers/dependencias no cuentan como skills evaluadas.
El progreso de T-03 se mantiene en [tasks.md](../tasks.md).

Los destinos siguientes son **propuestas** para T-08, pendientes de integración
y pruebas funcionales. Este bloque es lectura y análisis estático: no se
ejecutaron recursos del corpus, entrevistas, perfiles personales, pruebas de
navegador, instalaciones, migraciones, despliegues ni monitors. Tokens y latencia
son null; los tests documentales no acreditan eficacia o invocación nativa.

## S028 — Descubrimiento de identidad de marca entre sesiones

**Identidad y lectura.** SHA-256
`e6b9999ef722a42e0a01cd663072608609f69acc6bfd558fa3d4a14fcc3650b9`;
7.550 bytes/140 líneas; cuerpo y ocho recursos completos, 13.988 bytes/484 líneas.

**Contrato y valor.** Entrevista de identidad con siete módulos de entrada y
una síntesis final. Conserva propósito/valores en acción, posicionamiento y
alternativas, audiencia/ICP/trigger/resultado, personalidad/arquetipo,
voz por contexto, narrativa y límites entre fundador y organización. Al
final produce brandbook con prisma de identidad, asociaciones, señales de
equity, tensiones resueltas, dudas abiertas y próximos pasos.

Leer el estado y módulo activo antes de preguntar; informar progreso y permitir
cambiar de módulo. Una pregunta, paráfrasis y profundización por respuesta;
laddering, porqués, ejemplo concreto y técnica proyectiva ante respuestas
genéricas. La saturación orienta cuándo resumir, no acredita por sí misma
que todos los campos tengan evidencia. Conservar citas/ejemplos atribuidos
separados de interpretación, candidatos, preguntas y contradicciones.
Para varios participantes, entrevistas independientes y reconciliación
explícita antes de dar una formulación por acordada.

**Defectos y estado.** El texto promete guardar respuestas según avanzan, pero
el protocolo solo escribe al cerrar un módulo. Una sesión interrumpida antes
de ese punto puede perder material. El checkpoint necesita estado parcial por
respuesta confirmada y relación verificable con los archivos existentes.
Un único archivo por fundador requiere secciones por módulo o destinos
diferenciados: sobrescribirlo en cada módulo perdería respuestas anteriores.
Conservar finalización con módulo activo y nextModule null coherentes;
versionar esquema, identificar entrevista/participantes, representar saltos
y reanudación, distinguir terminado de omitido y evitar escrituras concurrentes.

Los filtros de nombre/ruta están en instrucciones, no en un escritor ejecutable.
Un path absoluto bajo el proyecto necesita resolver confinamiento real y
enlaces, además de rechazar segmentos peligrosos. Los recursos contienen
encabezados pegados a números de lista o citas; corregir Markdown antes de
convertirlos en plantillas finales. Sus marcos son guías conceptuales, no
cuestionarios psicométricos validados ni mediciones de eficacia de este plugin.

**Comparación propia.** `analyst` ya exige pregunta individual, ejemplos,
reformulación e incógnitas; su único entregable autorizado por contrato actual
es spec.md e índice. No incluye entrevista de marca ni brandbook/checkpoint.
`documenter` escribe documentación de producto bajo docs, con fuentes; no
produce por defecto identidad aspiracional o material de entrevista.
`knowledge-write` mantiene publicación curada: Raw y opiniones no se convierten
automáticamente en memoria aceptada. La integración deberá resolver dueño y
permiso de cada artefacto, no ampliar silenciosamente el rol analyst.

**Decisión y destinos.** **Conservar y actualizar** como especialidad opcional
propuesta `skills/brand-strategy/SKILL.md`, con
`skills/brand-strategy/references/discovery-method.md` y ocho plantillas:

| Recurso leído | Criterios que conserva | Destino propuesto bajo `skills/brand-strategy/templates/` |
|---|---|---|
| R-ee59d14f0aeb | Propósito, valores, límites y puente al posicionamiento | `purpose.md` |
| R-1a6ee86e2b82 | Categoría, cliente, alternativas, diferenciación e hipótesis de espacio | `positioning.md` |
| R-23071bd463ac | ICP, trigger, dolor/resultado, ajuste, señales y segmentos por probar | `audience.md` |
| R-cf6e7aad5766 | Arquetipos, dimensiones con evidencia, comportamiento y límites | `personality.md` |
| R-7c653c8ba4ff | Espectros de voz, matriz por contenido, ejemplos y tres checks | `voice-tone.md` |
| R-ec2515d0b81f | Origen, conflicto, transformación, trueline y cliente como protagonista | `narrative.md` |
| R-b249c73fe69e | Equity del fundador/organización, límites, transición y riesgos | `founder-boundaries.md` |
| R-03af6cd5a3ec | Síntesis de siete módulos, prisma/sistema de identidad, tensiones y acciones | `brandbook.md` |

El estado de entrevista es un artefacto de dominio, no otro ledger de tareas.
Guardar solo en el destino de proyecto acordado; Raw puede necesitar un
directorio privado. Publicación/sincronización y validación de brandbook tienen
alcance propio. Los tipos de persona del plugin orientan agentes y no son
estas dimensiones de personalidad de marca.

**Dependencias y activación.** S043/S044 usan el brief de identidad para
análisis competitivo; S024 ya propone su rúbrica. S029 aporta el perfil de
voz por muestras. Manifiestos distribuyen la especialidad, sin probar entrevista
o disponibilidad universal. Literal: «Define la identidad de nuestra marca».
Paráfrasis: «Entrevista a los fundadores y prepara un brief para diseño».
Negativo: «Especifica el contrato de esta API» → analyst/api-contract habitual.
Son escenarios estáticos; no se entrevistó, escribió estado ni generó brandbook.

**Coste, degradación e impacto.** Leer solo método y módulo activo; no las
ocho plantillas siempre. Sin respuestas o fuentes, mantener incógnitas y
formulaciones propuestas, sin inventar consenso. T-08/T-10/T-11 definirán dueño,
dependencias, contratos de escritura y activación. T-12/T-14 verificarán
checkpoint, interrupción, múltiples participantes, rutas y terminal coherente.
T-15 documentará privacidad, plantillas y exports ES/EN.

## S029 — Perfil de voz sustentado en muestras

**Identidad y lectura.** SHA-256
`57c7f8440b7bd4c91c0d325640b5c6fb7a3dc7fc05595946c7bc705761a987a7`;
3.648 bytes/98 líneas y R-37a37583ac4d completo, 1.063 bytes/55 líneas.

**Contrato y valor.** Produce un perfil reutilizable desde muestras reales,
con autor/objetivo/confianza/fuentes, ritmo, compresión, capitalización,
paréntesis, preguntas, estilo de claims, recursos preferidos/prohibidos, CTA
y notas por canal. Recoger muestras representativas cuando existan; distinguir
voz pública y de trabajo si difieren. Reutilizar el perfil confirmado en la
sesión, con persistencia duradera solo cuando se pida y en el destino indicado.
No crear archivos versionados con fingerprints personales sin petición.

**Defectos y comparación.** La preferencia rígida por publicaciones sociales
no garantiza que sean representativas para documentación, soporte o propuestas.
Seleccionar fuentes por canal/objetivo/fecha y separar conflictos, sin inventar
una voz unificada. Los defaults de un autor y sitio particulares se retiran
de la adaptación; no fijan estilo del consumidor. Las prohibiciones de estilo
son criterios de las fuentes o del usuario, no vetos universales.
El schema pide que cada prohibición sea observable o solicitada y que no se
promedien fuentes contradictorias: conservar esa regla también en el cuerpo.

`docs-style` aporta redacción técnica y ejemplos citables, no un perfil de voz
personal. S018 propone long-form-writing y un dueño único del perfil; S028
elicita intención de marca, distinta de muestras de escritura observadas.
No convertir este perfil en persona de agente ni memoria canónica obligatoria.
Un campo Confidence textual no demuestra calibración: explicar cobertura y
límites de muestras, permitir corrección y conservar proveniencia.

**Decisión y destinos.** **Conservar y actualizar** como mapa opcional propuesto
`skills/voice-profile/SKILL.md` y
`skills/voice-profile/references/profile-schema.md`. Conservar todos los campos,
proceso de fuentes, separación por canal, confirmación y persistencia opt-in.
S018 y los futuros métodos de contenido apuntarán a este dueño único; el módulo
de voz de S028 lo usa cuando haya muestras y registra hipótesis cuando no haya.

**Dependencias y consumidores.** Los fragmentos leídos de contenido,
crossposting, email, contactos, inversores, leads, SEO, campañas, ranking
social y API social consumen el perfil antes de redactar; agente y comando
de marketing también. Esa lectura no autoriza publicar, enviar ni autenticarse.
La integración de las otras piezas se decidirá en sus fichas/T-08. El acceso
social es opcional; muestras aportadas y documentos pertinentes son fallback.

**Activación estática.** Literal: «Extrae mi estilo de estos textos».
Paráfrasis: «Mantén una voz consistente en varios canales».
Negativo: «Reanuda la entrevista de posicionamiento» → S028; «corrige una
ruta de docs» → documenter/docs-style. No se capturó voz personal ni accedió
a una cuenta para extraer posts o enviar mensajes.

**Coste, degradación e impacto.** Cargar perfil breve confirmado y solo
muestras necesarias; tokens/latencia null. Sin fuentes suficientes, explicitar
incógnitas y usar tono acordado sin atribuir una imitación acreditada.
T-10/T-11 deberán retirar defaults específicos y análisis duplicados de callers.
T-14 verificará fuente insuficiente/conflictiva, canal y persistencia; T-15
actualizará docs/dependencias/exports ES/EN.

## S030 — QA de interfaz con navegador y baseline visual

**Identidad y lectura.** SHA-256
`6eb78a2460adcde116e6b44fcdff7ae37aeec6208241a24417cb2db4b3b254cd`;
4.104 bytes/105 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Cuatro fases: smoke de consola/red/performance/capturas;
interacciones de navegación/formularios/auth/journeys; comparación visual
por viewport y tema; accesibilidad automatizada más teclado/foco/landmarks.
Conservar credenciales de prueba, alcance de mutaciones, redacción de capturas,
baseline ausente como inconcluso y evidencia por hallazgo. QA conserva informe
y gate; una etiqueta editorial de shipping no sustituye aceptación.

**Defectos y fuentes.** Medir INP necesita interacción, y un smoke de laboratorio
no demuestra Web Vitals de campo: conservar el contrato de S023 ya comparado.
Consola «ruido» debe tener causa/allowlist trazable, no ocultar todo lo externo.
No todos los 4xx o status distintos de 200 son defectos: contrastar respuesta
esperada y caso negativo. Los tres anchos y delta de 5px son ejemplos, no gates
universales. El [método Playwright](https://playwright.dev/docs/test-snapshots)
exige entornos coherentes entre baseline y nueva captura. Fijar browser/OS/
fuentes/datos/tiempo/animaciones y baseline aprobado; no actualizarlo para
ocultar una regresión. Documentar diferencias previstas y redacción aplicada.

La [guía WAI](https://www.w3.org/WAI/test-evaluate/tools/selecting/)
distingue checks automáticos de juicio humano. El porcentaje genérico de
cobertura del texto no declara denominador, reglas, versión o corpus;
no usarlo como porcentaje de conformidad. Registrar reglas ejecutadas,
incompletas y checks manuales. Nombre prefijado de tools o MCP «preferido»
no demuestra disponibilidad, instalación ni autorización en los tres runtimes.
El ejemplo SHIP WITH FIXES incluye un formulario fallido: no convertirlo en
verde si incumple un criterio obligatorio.

**Comparación propia.** `frontend-quality` ya exige teclado/foco/estados/
performance reproducible. `agents/qa.md` conserva E2E, informe, escenarios
manuales y qa-gate; `qa-gate.py` convierte fallos/evidencia ausente en no verde.
`lib-guardrail.sh` pretende limitar hosts a locales/privados: la guía externa
de preview no amplía ese contrato. Su filtro usa patrones de texto, no valida
IP/DNS: `10.*` puede aceptar un nombre como `10.example.com`, y el host IPv6
con corchetes no coincide con el literal `::1`. Son límites del código leído,
sin resolver DNS ni ejecutar requests; T-09/T-14 deben contrastar parsing,
redirects y autorización real antes de afirmar aislamiento. Faltan contrato explícito de
baseline visual, procedencia del entorno y clasificación de smoke vs cobertura
del test-plan. Un MCP browser disponible no equivale al reporter que espera
el gate actual; cualquier adaptación debe preservar resultados verificables.

**Decisión y destinos.** **Ampliar** frontend-quality con referencia propuesta
`skills/frontend-quality/references/browser-evidence.md`, y QA/test-plan/
plantillas existentes. Conservar las cuatro fases, distinguir no ejecutado,
inconcluso, defecto y resultado válido, vincular evidencia a aceptación.
Mantener dueño único del informe/gate y guard actual; contrato de entornos,
reporter y herramientas se resuelve explícitamente en T-08/T-09/T-12.

**Dependencias y activación estática.** S023 comparte baselines; S032 la
observación posterior. MLE y product-lens enlazan QA de journeys/rollout.
Literal: «Comprueba formularios y capturas de esta interfaz».
Paráfrasis: «Valida teclado, navegación y cambios visuales antes de entregar».
Negativo: «Vigila salud tras el despliegue» → S032/delivery; «renderiza una
animación 3D» → S026. No se invocó navegador, axe, Playwright ni QA funcional.

**Coste, degradación e impacto.** Leer checklist del flujo pertinente, registrar
herramientas/versiones y límites; tokens/latencia null. Sin browser, baseline
o checker compatible, declarar pendiente/inconcluso y conservar manuales.
T-10/T-11 armonizarán QA y callers; T-12/T-14 probarán resultados parciales,
baseline ausente, comparaciones, mutaciones y criterios fallidos. T-13/T-15
mostrarán límites y actualizarán docs/manifiestos/exports ES/EN.

## S031 — Bun como alternativa de runtime y toolchain

**Identidad y lectura.** SHA-256
`8015a977827ddd8536e89c4693a575b8deb5b04073b8a483c320c5419abc35da`;
2.608 bytes/85 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Conserva elección Bun/Node, ejecución JS/TS y scripts,
package manager/lockfile, bundler, runner bun:test, env, Bun.file/Bun.serve,
migración y despliegue. Architect decide compatibilidad; implementer desarrolla
y qa verifica los comandos reales. No elegir Bun por defecto en todos los
proyectos nuevos ni migrar dependencias solo por activar la guía.

**Vigencia contrastada.** La [tabla oficial de compatibilidad](https://bun.sh/docs/runtime/nodejs-compat)
declara diferencias por API, no compatibilidad perfecta. La
[guía TypeScript](https://bun.sh/docs/typescript) separa ejecutar y comprobar
tipos. La [guía de lockfile](https://bun.sh/docs/pm/lockfile) conserva transición
de formato binario a texto desde 1.2; comprobar versión y lockfile del proyecto
antes de migrar o borrar uno. La [publicación 1.4](https://bun.com/blog/bun-v1.4)
describe el cambio Zig→Rust: la implementación citada en el corpus no es un
invariante para todas las versiones. Estas fuentes no acreditan versión
instalada ni funcionamiento de este plugin bajo Bun.

[Vercel](https://vercel.com/docs/functions/runtimes/bun) documenta bunVersion,
versiones admitidas, diferencias por framework/preset y runtime en beta.
Instalar/build con Bun no demuestra que la función se ejecute con Bun;
verificar artefacto y configuración. Conservar frozen-lockfile y versionado.
El rendimiento depende de workload: medir con S023/S025, sin trasladar cifras
ajenas como mejora del consumidor. Los ejemplos FOO=bar necesitan adaptación
al shell; el test aritmético solo ilustra API, no es evidencia de migración.

**Comparación propia.** `stack-practices` selecciona PHP/Python/React por
manifiestos, no Bun; `delivery-practices` separa build/runtime y exige artefacto
real. TDD y unit-tests conservan sus métodos/gates, pero la existencia de
bun:test no acredita que sus adapters actuales admitan reporter/cobertura Bun.
Detectar paquete/runtime, contrato de coverage y typecheck antes de declararlos
soportados. No añadir una referencia JS genérica inexistente por similitud.

**Decisión y destinos.** **Conservar y actualizar** como referencia opcional
propuesta `skills/stack-practices/references/bun.md`, con selección por runtime
declarado/comprobado y mapa actualizado tras T-08. Mantener todos los usos,
alternativas, límites por versión y rollback de migración; combinar con
delivery y pruebas existentes, sin paquete técnico obligatorio ni upgrade
automático. Los comandos son ejemplos a adaptar a herramientas instaladas.

**Dependencias y activación estática.** La sección Bun del TDD de origen
enlaza esta guía y distingue runner nativo de scripts npm. Manifiestos la
distribuyen como práctica de stack. Literal: «Evalúa migrar este servicio a
Bun». Paráfrasis: «Revisa lockfile y bun:test de este proyecto».
Negativo: «Añade una regla PHP» → referencia PHP existente. No se ejecutó Bun,
typecheck, runner, instalación, build ni deploy Vercel.

**Coste, degradación e impacto.** Cargar solo la referencia pertinente;
tokens/latencia null. Sin Bun compatible, mantener Node o declarar pruebas
pendientes según el objetivo; no instalar en silencio. T-10/T-12 definirán
selección y adapters; T-14 comprobará compatibilidad/lockfile/tipos/reporters
y fixtures de migración. T-15 documentará matriz/exports ES/EN.

## S032 — Observación de salud tras desplegar

**Identidad y lectura.** SHA-256
`d2cb536f8ccb201266e094542cb20af8a4d6474feb5b16116cfb4497c2b8149f`;
3.128 bytes/108 líneas; cuerpo completo, recursos locales 0/0.

**Contrato y valor.** Conserva pase único, vigilancia con intervalo/duración
y comparación de entornos. Observa HTTP, errores nuevos de consola/red,
regresiones de performance, contenido crítico, salud de API, assets/content-type
y conexión/eventos/heartbeat SSE. El informe guarda baseline/delta y niveles
de señal; no equivale a una prueba de todos los journeys ni calidad del producto.

**Defectos concretos.** No hay monitor, scheduler, parser de flags, writer de
logs ni notificador local. Sus comandos slash dependen del host; instrucciones
Markdown no acreditan continuidad durante horas o reanudación entre sesiones.
Un PostToolUse de git push no confirma deploy concluido ni identifica URL/
artefacto publicado. El disparo necesita resultado real del despliegue y
asociación de versión/entorno; un hook global no debe abrir red en cada push.
Un handler acotado no puede ejecutar toda la ventana de vigilancia dentro
del timeout de un hook: separar evento, autorización, arranque y estado real
del proceso según el contrato del runtime.
Enviar a webhooks o notificaciones requiere capacidad y alcance explícitos,
no es efecto de esta comparación ni dependencia obligatoria.

Status !=200 no siempre es fallo: declarar respuestas esperadas, redirects,
auth y endpoints. Conservar ventanas, límites, timeouts/cancelación y baseline
de versión comparable. SSE requiere content-type y recepción observada de
evento/heartbeat esperado; conexión abierta sin datos no prueba salud.
Comparar staging/producción necesita condiciones y datos equivalentes o
límites declarados. Una medición ausente no es cero ni HEALTHY. Umbrales
temporales/consola/performance se acuerdan por servicio y entorno, sin ocultar
fallos como ruido o presumir INP por navegación sin interacción.

**Comparación propia.** `delivery-practices` ya conserva readiness/liveness,
artefacto, shutdown y rollback. `frontend-quality`/outcome-evals guardan
condiciones y baseline; QA prueba journeys locales/privados. No hay en estos
métodos un monitor persistente acreditado, SSE ni protocolo de comparación
postdeploy. Observación externa de un entorno propio necesita un contrato
operativo explícito; no ampliar el guard de QA por copiar esta skill.

**Decisión y destinos.** **Ampliar** delivery-practices con referencia propuesta
`skills/delivery-practices/references/post-deploy-observation.md` y un monitor
opt-in futuro en T-12, si T-08 confirma su contrato. Conservar las ocho señales,
tres modos, severidad, reporte y notificación opcional. Definir URL/entorno/
artefacto, esquema versionado, intervalo/deadline/presupuesto, estado terminal,
historial acotado/redactado y dato parcial. Compartir baselines S023 y evidencia
del ledger, sin otro daemon ni scheduler por defecto. Un handle vivo observado
prueba espera; un archivo de estado o un resumen previo no prueba proceso vivo.

**Dependencias y activación estática.** S030 acompaña verificación previa,
S023 medición y MLE/product-lens salud de rollout. Literal: «Comprueba salud
tras este despliegue». Paráfrasis: «Vigila endpoints, assets y SSE durante
esta ventana». Negativo: «Valida todos los flujos del formulario» → qa/S030.
No se contactaron endpoints, streams, schedulers o webhooks ni inició monitor.

**Coste, degradación e impacto.** Cargar señales pertinentes y condiciones,
no historial completo; tokens/latencia null. Sin herramienta o acceso, informar
no ejecutado; al agotar ventana, finalizar con cobertura real y motivo.
T-09/T-12/T-14 verificarán trigger/versionado, límites, cancelación, SSE,
errores y métricas ausentes. T-10/T-11 armonizarán callers; T-13/T-15 panel,
disponibilidad, docs/dependencias/exports ES/EN.

## Cobertura y trabajo siguiente

Los nueve recursos locales tienen destino propuesto explícito; las cinco
fichas distinguen valor, solapes, defectos, activación estática y validación
pendiente. No se incorporó código ni se ejecutó una entrevista, QA o monitor.
La lectura de fragmentos comerciales/técnicos no cierra otras fichas ni T-06.
S033 y siguientes permanecen pendientes de evaluación, sin excluir dominios
por no ser el stack de este repo. T-08 resolverá conjunto, dueños y contratos
después de completar la comparación del catálogo, operación y memoria.
