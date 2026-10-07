# Comparación de contratos, costes y revisión de decisiones

Fichas S055–S060 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Se leyeron los seis cuerpos
completos, 42.223 bytes/1.123 líneas, y sus tres recursos completos,
12.909 bytes/374 líneas. [contract-cost-reading-evidence.json](contract-cost-reading-evidence.json)
registra 22 fuentes y 20 archivos propios, hashes, rangos de callers y
contrapartes, siete contrastes
documentales y la consulta de versión/ayuda de Codex. El progreso está en
[tasks.md](../tasks.md). Las dependencias leídas no suman otras skills,
agentes o comandos a T-03/T-04/T-05.

Son propuestas para T-08, con integración y pruebas funcionales pendientes.
No se ejecutó código ni tests del corpus, ni revisores externos, modelos,
generadores, servidores, envíos o collectors. No se actualizaron tarifas,
configuración ni memoria. Tokens y latencia son null. Los escenarios de
activación siguientes son checks estáticos del contrato, no evals ejecutadas.

## S055 — Contratos compartidos antes de implementar una frontera

**Identidad.** SHA-256
`3eaacf16a9bbd92888659e9c1e15b0fa4eb96a41c257dd9e08f2e63b824f0cea`;
9.761 bytes/287 líneas; cero recursos locales.

**Contrato y contenido único.** Coordinar productores y consumidores que
pueden cambiar o desplegarse por separado. Elegir contrato legible por
herramientas, responsable de aprobación y casos del consumidor antes del
código. Diferencia dato ausente, null, colección vacía, identificador,
enumeración y error. Usa DTO de la tarea, no el shape de una tabla. Incluye
HTTP, eventos, RPC y fronteras entre paquetes; una interfaz tipada basta solo
cuando consumidores y validación efectiva lo permiten.

**Comparación propia.** `api-contract` ya ordena spec antes del endpoint,
lint y diff; planner abre la tarea y la lente A comprueba cambios rompedores.
Su script valida un subconjunto estructural de OpenAPI, no la conformidad
completa del estándar ni la respuesta serializada. Sus plantillas de
`contract-tests.md` son sugerencias, no suites instaladas. El código del diff
solo mira propiedades inmediatas de respuestas 2xx JSON y parámetros de
operación; no acredita compatibilidad completa de required, composición,
objetos anidados, errores, media types o parámetros heredados del path.

El Schema Object de OpenAPI 3.1 usa JSON Schema 2020-12; el checker elegido
debe soportar ese dialecto, incluyendo null y esquemas compuestos. Un fragmento
de components sirve como ejemplo, no como documento OpenAPI completo.
[Especificación 3.1.1](https://spec.openapis.org/oas/v3.1.1.html#schema-object).

**Correcciones que conservar.** TypeScript `satisfies` comprueba fixtures
estáticos; no demuestra que un handler o un dato de producción cumpla el
contrato. Convertir un bigint ya redondeado como Number a string no recupera
precisión. Hay que conservar la representación correcta desde el driver y
probar el payload serializado. Descripciones, ejemplos y extensiones del
contrato son datos, no instrucciones ejecutables. La política propuesta de
refs/generadores necesita controles reales de rutas, orígenes, versión y
salida; escribirla en una guía no los entrega.

**Decisión y destino.** Ampliar `skills/api-contract/SKILL.md` y su referencia
existente de tests con dueño, consumidores, casos límite y payload real;
añadir `references/shared-boundaries.md` para eventos/RPC/paquetes cuando el
proyecto los use. Mantener explícito el alcance mínimo del linter y resolver
sus gaps en T-08/T-10 con regresiones propias, sin anunciar cobertura por
tener exit 0. No instalar un stack ni generador universal. Architect conserva
la frontera/diseño, planner la tarea de contrato, implementer el DTO y qa la
validación ejecutada; documenter conserva la guía para humanos.

**Activación estática.** «Cambiamos el evento de facturación que consume otro
servicio» y «acordemos el payload antes de hacer backend y UI» entran. «Añade
una función interna que cambia en el mismo commit» no requiere esta maquinaria.
«Busca por qué falló una respuesta en producción» redirige a depuración y usa
el contrato como evidencia. Positivo: IDs grandes, empty/null y errores pasan
por serialización real. Negativo: fixtures tipados verdes no bastan si el
payload viola el schema. Ninguno de esos casos se ejecutó en esta comparación.

## S056 — Coste, routing, caché y reintentos de aplicaciones LLM

**Identidad.** SHA-256
`2d6c19c2d21a473db8720c4f723f17d265eeec48f84614f0169be2df2fbe28ff`;
5.992 bytes/188 líneas; cero recursos locales.

**Valor y límite.** Propone escoger modelo por necesidad, registrar la
elección, acumular consumo, comprobar presupuesto, reintentar fallos
transitorios y reutilizar prefijos. Es diseño de una aplicación que llama
APIs LLM; no es una medición del plugin, ni un cambio automático del modelo
del usuario. Longitud y número de items son proxies, no calidad medida.

**Defectos concretos.**

- El tracker congelado vive en memoria. Copiar tuplas y recalcular su suma
  no aporta persistencia ni reserva concurrente. Comprobar el coste pasado
  con `>` deja pasar otra petición al alcanzar exactamente el presupuesto
  y permite sobrepasarlo antes del siguiente check. Se necesita reserva,
  coste desconocido explícito, reconciliación y límite del request.
- `max_retries` cuenta intentos en el bucle de ejemplo; cero termina sin
  llamada ni resultado. Falta importar `time`; el snippet no es un pipeline
  completo. El backoff no contempla jitter, Retry-After ni deadline común.
  El SDK ya reintenta dos veces por defecto: otra capa puede multiplicar
  solicitudes. Hay que asignar un dueño a los retries y registrar resultados
  inciertos sin asumir que una llamada fallida no consumió recursos.
  [SDK Python](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python#retries).
- El supuesto system prompt aparece como texto de usuario. Conservar su
  rol semántico es distinto de cachearlo. `cache_control` no evita enviar el
  contenido ni demuestra un hit; umbral, TTL y campos de usage dependen del
  modelo/plataforma. Por ejemplo, el umbral actual de Haiku 4.5 es 4.096
  tokens, así que «más de 1.024» no es una regla universal.
  [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#cache-limitations).
- Su afirmación de ahorro de 3–4 veces no se deduce de la propia tabla:
  las tarifas que declara para Haiku 4.5 y Sonnet 5 tienen relación 2:1.
  Tampoco predice coste por tarea, que depende de llamadas y tokens reales.
  Modelos, precios y multiplicadores requieren fecha/fuente; no copiar la
  tabla a una configuración permanente.

**Cobertura propia y decisión.** `rates-verify` verifica precios para
evaluator/planner; `usage-meter.py` mide ventanas de transcripciones Claude
y convierte tokens usando configuración y calibración. Ninguno implementa
el routing/reserva/retries de una aplicación. Conservar especialidad opcional
`skills/llm-pipeline/SKILL.md`, con `references/cost-control.md` y
`references/cache-and-retries.md`: APIs y dependencias del proyecto, proveedor
explícito, baseline de calidad/latencia/coste y fallback limitado por política.
La propuesta no impone Anthropic, nombres de modelos ni SDK al plugin.
S022/S050 aportan los mecanismos generales de jobs, caché y snapshot; la
referencia LLM conserva sus diferencias de facturación y prompt cache.

**Activación estática.** «Nuestro batch llama a una API LLM y excede el
presupuesto» y «quiero medir si un modelo pequeño mantiene calidad» entran.
«Cuánto ha consumido esta sesión» va a S057; «el brief supera su tamaño» al
contrato de contexto. Positivos futuros: reserva concurrente, reconciliación,
hit real y calidad mínima. Negativos: modelo más barato que falla el criterio,
retry duplicado y coste desconocido tratado como cero. Validación pendiente.

## S057 — Informes de consumo con procedencia y ámbito

**Identidad.** SHA-256
`f868207abd550308bc18902ecdfd2c51ad1ea85ba692dbe95cd9c3561da2a8bb`;
5.102 bytes/107 líneas; cero recursos locales.

**Contrato y recursos de soporte.** Consulta un JSONL local de snapshots
acumulados. Reducir por sesión evita sumar el mismo consumo varias veces.
El comando C006 comparte log y lógica; R-aa073f6b406b produce filas desde
Stop y R-7d9940f71285 mantiene una caché por sesión con cursor en bytes,
lectura por chunks, 16 MiB por catch-up y descarte reanudable de líneas
mayores de 1 MiB. Se leyeron completos esos tres soportes; no se ejecutaron.
El bridge se leyó en sus secciones de consumo, no como auditoría completa.

**Contenido útil y gaps.**

- Dedupe por message.id y snapshots acumulados son útiles. El productor
  lee entero el transcript en cada Stop; el cursor acota lectura del log
  de costes, no ese trabajo ni los reports, que también leen todo el log.
  La retención limita snapshots, no el histórico. El consumidor de caché
  puede ir atrasado tras llegar al límite, sin campo claro de catch-up.
- El productor suma todos los mensajes pero aplica la tarifa del último
  modelo a todo el total. No incluye subagentes como nuestro meter por
  proyecto. Modelo desconocido cae a Sonnet y ausencia de transcript produce
  ceros; el bridge también retorna ceros ante ausencia/error. Eso no prueba
  coste cero ni cobertura completa.
- La tabla por familias usa multiplicadores universales y puede clasificar
  mal versiones. La documentación actual tiene tarifas de caché distintas
  para modelos como Opus 5.5 y Fable 5.1, además de TTL distintos. Conservar
  precio, modelo, plataforma, fecha y procedencia por registro, o declarar
  estimación incompleta.
  [Precios oficiales](https://platform.claude.com/docs/en/about-claude/pricing).
- La cabecera llama al número de statusline coste facturado y lo describe
  como per-process. La documentación lo define como estimación de sesión,
  calculada en cliente, que puede diferir de la factura. El archivo temporal
  del productor solo comprueba edad y número; no prueba autenticidad ni
  registra si el resultado vino de ese archivo o del cálculo del transcript.
  [Datos de statusline](https://code.claude.com/docs/en/statusline#available-data).
- La caché valida offsets y tres ventanas de fingerprint, publica con
  escritura atómica y permite reconstrucción. Eso no es un hash íntegro del
  prefijo ni una transacción entre writers. Su selección por dominancia de
  tokens/coste puede preferir un importe viejo frente a una corrección a
  la baja. Hace falta generación/cursor y contrato de correcciones, no
  asumir que el mayor número siempre es el más nuevo.
- Los ejemplos de informe atribuyen el total de la sesión a la fecha y
  modelo del último snapshot. Una sesión de dos días queda entera en uno;
  no es gasto diario. Falta separación por proyecto y zona horaria. El
  fallback session/path/timestamp tampoco define identidad inequívoca.
  C006 exporta las últimas cien filas crudas con `join(',')`, sin escaping
  CSV ni marcar que son snapshots no sumables. «Últimos siete días» toma
  siete fechas con actividad, no una ventana de siete días calendario.

**Comparación propia.** Nuestro meter deduplica respuestas globalmente,
incluye subagentes y mide ventanas por artefacto con offsets y timestamp.
Sin transcripciones compatibles conserva tokens/coste/horas null. No es
todavía un informe general de sesiones para los tres runtimes. En las
secciones leídas, `_eur` usa una tarifa común y valora caché sin tarifa a
cero con aviso: también requiere modelo por registro y coste parcial
explícito. No convertir esa carencia propia en afirmación de medición completa.

**Decisión y destino.** Ampliar `agent-kits/shared/usage-meter.py` con el
contrato de procedencia/cobertura y collectors opt-in de T-12; añadir una
skill opcional `skills/usage-report/SKILL.md` que consuma esa salida y los
datos canónicos de artefactos. Compartir el lector/report con panel y
roadmap; cachés reconstruibles no serán otro ledger de presupuesto. Mantener
separados tokens medidos, coste estimado, coste incompleto y factura externa
si llega a existir una fuente compatible. El formato persistente y la
compatibilidad de lectura los decide T-08, sin migrar logs ajenos aquí.

**Activación estática.** «Desglosa el consumo por proyecto/modelo» y «exporta
el uso medido de esta semana» entran. «Reduce llamadas de mi app» va a S056;
«presupuesta una iniciativa» conserva evaluator/planner. Casos pendientes:
doble snapshot, modelos mixtos, medianoche, corrección a la baja, subagentes,
rotación, UTF-8 parcial, concurrencia y log ausente. Un report vacío no es
una factura de cero ni una calibración.

## S058 — Revisar una decisión conservando el desacuerdo

**Identidad.** SHA-256
`2104d002d301a061a16d21ea2e00292f80b66b20c9883a33525a7de404153502`;
6.358 bytes/204 líneas; cero recursos locales.

**Contrato y valor.** Para una decisión ambigua con alternativas reales,
propone posición inicial y tres perspectivas: escéptica, práctica y crítica
de premisas. Cada una recibe contexto compacto y devuelve posición,
razones, riesgo y sorpresa. Una ronda por defecto, síntesis que conserva
el desacuerdo más fuerte y condición que cambiaría la recomendación.
No cuenta votos como prueba de corrección ni pide convergencia forzada.

**Solapes y límites comprobados.** La guía prescribe contexto fresco y
dispatch paralelo, pero no tiene orquestador o recurso que lo implemente.
El caller S077 distingue revisión constructiva por roles de esta decisión;
S005 la deriva cuando el problema es ambigüedad, no fallo técnico. No se
auditaron completos S077 ni sus ejecutores. La orden «sin hedging» debe
corregirse: tomar posición puede convivir con incertidumbre y límites.
Tres prompts no garantizan independencia, diversidad de modelo ni calidad.

Architect ya compara opciones en design.md; adversarial-review comprueba
conformidad/defectos del diff y qa valida resultados. No convertir las voces
en tres roles permanentes, sustituir aprobación de diseño o añadir otra
revisión obligatoria a cada tarea. Las referencias de persistencia y al
tracker externo no conceden permiso para publicar ni aprobar memoria.

**Decisión y destino.** Conservar especialidad opcional
`skills/decision-review/SKILL.md` y `references/decision-deliberation.md`.
Architect puede aplicarla a una alternativa concreta, reutilizando design.md;
en uso manual devuelve recomendación y desacuerdo. Contexto, presupuesto,
handles, fallo parcial y capacidad real del runtime deben quedar explícitos.
Con delegación autorizada/capacidad disponible usa perspectivas frescas; si
no, declara el alcance de la deliberación. Respeta elecciones y decisiones
ya delegadas por el usuario. ADR solo por el umbral y writer existentes;
ninguna síntesis se convierte automáticamente en doctrina o envío externo.

**Activación estática.** «Contrasta si vale la pena migrar ahora» y «dame
las objeciones más fuertes a esta alternativa» entran. «Revisa este diff»
va a adversarial-review; «implementa el diseño aprobado» conserva implementer.
Pendiente: perspectivas separadas, dissent visible, timeout de una voz y
recomendación con evidencia incompleta. El resumen no acredita que hubo
subagentes frescos si el runtime no los ejecutó.

## S059 — Crítica externa opcional después del borrador

**Identidad.** SHA-256
`3c67816efdab97c89f8433b8a88d720ca736871467f7d6d1ff344fee59f18ce5`;
5.987 bytes/167 líneas. R-cfb72d544f0a se leyó completo: 9.479 bytes/305
líneas. Su test R-a7067c585eb3 se leyó completo como soporte, sin ejecución.

**Contenido único.** Añade un solo nodo a S058: crítica de un borrador y
su desacuerdo más fuerte con packet mínimo. Explicita destinatario de la
transferencia, redacción, consentimiento aplicable y relación entre
proveedores. Desde host OpenAI hacia OpenAI es crítica externa del mismo
proveedor, no diversidad de proveedores. Un resultado ausente deja la
deliberación original identificada; no inventa crítica ni cambia modelo.

**Adaptador y contraste.** El recurso limita packet a 64 KiB, timeout de
invocación a 10–120 segundos, probes a cinco segundos cada uno y buffers del
proceso. Usa directorio temporal, entorno allowlisted, salida final y cleanup.
Desactiva features, MCP, instrucciones de skills y configuraciones mediante
flags; exige exactamente CLI 0.146.0 y toggles estables. Codex instalado
responde 0.160.1 a `--version`: la condición de versión del recurso lo
rechazaría antes de la crítica. No se ejecutó el recurso para demostrarlo.

La ayuda instalada confirma flags de exec usados, incluidos ephemeral,
ignore-user-config, ignore-rules, strict-config y output-last-message.
La documentación aclara que ignorar config conserva autenticación en
CODEX_HOME y que sandbox selecciona una política, no prueba por sí solo
ausencia de herramientas o lectura confinada.
[Referencia CLI](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
La snapshot Markdown contiene tablas renderizadas fuera del texto; la ayuda
local y la lectura de la página complementan ese límite.

**Gaps antes de integrar.**

- El timeout de review no incluye espera por EOF de stdin ni ambos probes.
  `maxBuffer` acota stdout/stderr del proceso, no `readFileSync` de la salida
  final. Hace falta deadline agregado y lectura final acotada.
- El entorno conserva HOME/USERPROFILE/CODEX_HOME para autenticación.
  Directorio vacío, read-only y lista de flags no acreditan aislamiento
  completo de instrucciones, herramientas o datos del usuario.
- Los tests ordinarios mockean probes/spawn. El test real de sentinel
  está condicionado a opt-in y, aun ejecutado, comprobaría una vía/versión,
  no todo el árbol de capacidades ni todos los sistemas operativos.
- Dos bloques llamados untrusted no impiden que el packet contenga
  instrucciones hostiles; la crítica devuelta es dato y requiere revisión.
  Reintentar tras timeout podría repetir coste sin producir una respuesta.

**Decisión y destino.** Consolidar el método en
`skills/decision-review/references/external-critique.md`, sin otra skill de
deliberación ni alias vacío. El transporte propuesto
`agent-kits/shared/external-review.py` comparte lifecycle/resultados con
despacho externo S036, manteniendo aislamiento y contrato por versión
específicos. Los tres hosts pueden ofrecer el método cuando haya adaptador
verificado; no se declara que los tres CLIs soporten los flags de Codex.
Identificar proveedor/modelo, packet y autorización existente antes del
efecto, sin pedir permiso repetido si ya cubre exactamente esa transferencia.

**Activación estática.** «Contrasta este borrador con un proveedor externo
autorizado» y «aplica una segunda crítica al resultado de la deliberación»
entran. «Dame otra perspectiva en esta sesión» usa S058; revisar un diff
mantiene sus gates. Pendientes: packet redactado, rechazo de versión, stdin
abierto, archivo final excesivo, auth ausente, sentinel, tools realmente
ausentes y salida hostil. Ninguna crítica se ejecutó en esta comparación.

## S060 — Audiencia, participación y entrega a destinatarios externos

**Identidad.** SHA-256
`51f719cf28a6d3c43e511a2c75e903a41d566205f8e93a2eeb276e0c1eb92463`;
9.023 bytes/170 líneas. Dos recursos completos:

| Recurso | Tamaño | Valor y destino propuesto |
|---|---|---|
| R-be9cc9538c78 | 1.738 bytes/42 líneas | Política sintética, no schema de adaptador; `external-communication/references/audience-policy.md`, con identidad confiable, permisos y ejemplos opt-in |
| R-a2fa70d3abda | 1.692 bytes/27 líneas | Prompt fijo con etiquetas separadas como datos; `external-communication/references/message-contract.md`, subordinado a autorización/transport |

**Contrato y valor.** Separa identificar audiencia, decidir si participar
y autorizar entrega al destino exacto. Nombres visibles y contenido no
conceden confianza. En grupos, mención actual, comando o respuesta dirigida
son señales bajo la política del propietario; una participación antigua,
attachment o mensaje de bot no concede autorización. Observación pasiva,
si se habilita, tiene acceso/retención y no provoca inferencia ni enrichment.
Las solicitudes autorizadas pueden esperar un burst de attachments; stop
puede evitar esa espera sin saltarse los otros controles.

La decisión mute/defer debe preceder contexto, modelo y media. La validación
de entrega va después del ensamblado final e incluye send, edit, stream,
scheduler y helpers; cambiar el destino requiere nueva comprobación.
Autorizar un borrador no autoriza el envío. Clasificar audiencia no prueba
entrega: el transporte aporta el receipt. El caller S194 conserva esa
separación, aunque su flujo completo queda pendiente de evaluación.

**Comparación propia y correcciones.** Jira/Confluence ya comprueban conexión,
destino, previsualización y aprobación en sus flujos. No son un motor de
políticas de chat ni prueban guards en todos los transports. Un MCP detectado
en project-pieces no demuestra conexión ni audiencia confiable. La guía
comparada declara expresamente que no es enforcement ejecutable y sus dos
recursos son ilustrativos. El ejemplo permite observar grupos por defecto
aunque la prosa exige opt-in: una configuración nativa debe empezar con
observación deshabilitada hasta que exista la política aplicable.

Las categorías draft-only/never de la plantilla no se transforman en una
prohibición universal del plugin. El contrato debe respetar la autorización
vigente, el propietario de la operación y las restricciones de ese entorno.
Tampoco se transporta automáticamente una política de chat a publicar docs.
Mensajes externos útiles excluyen trazas/secretos/datos de otra contraparte;
errores seguros dicen límites reales, sin fingir acceso a attachments.

**Decisión y destino.** Conservar especialidad opcional
`skills/external-communication/SKILL.md`, con las dos referencias indicadas,
seleccionada cuando el proyecto tiene transports a terceros. Reutilizar
conectores y políticas del runtime propietario; no crear un segundo motor
de permisos del plugin. Cada adaptador necesario se integra en T-09/T-12
solo con contrato y controles reales. Shared proporciona clasificación y
redacción aplicables, no credenciales, autoridad sintética ni envíos nuevos.
Panel muestra declaración/disponibilidad/verificación por separado.

**Activación estática.** «Este bot responde en un canal de proveedores» y
«revisa cuándo pueden entregarse sus mensajes» entran. «Sube estas páginas
al destino de Confluence ya autorizado» conserva confluence-publish;
«redacta un email local» no implica conectar/enviar. Pendientes: grupos,
DM individual/grupal, bots, mención adversarial, burst, cambios de destino,
stream y helpers. Tests deben demostrar contadores de trabajo en cero al
mutear y rutas positivas autorizadas, con identidades sintéticas y sin
canales, términos o recibos privados en fixtures públicas.

## Integración compartida y puertas pendientes

| Criterio útil | Dueño y artefacto | Puerta real pendiente |
|---|---|---|
| Frontera productor/consumidor, payload y cambio compatible | api-contract, design/tarea/spec existentes | Schema correcto, serialización y consumidor real; no solo lint |
| Routing/calidad/reserva/cache/retries LLM | llm-pipeline opcional, configuración de la aplicación | Calidad mínima, presupuesto concurrente y uso real por proveedor |
| Consumo sin doble conteo, modelos y procedencia | usage-meter, collectors y usage-report | Deltas por fecha/modelo/proyecto, incompleto/null y pruebas de reader |
| Alternativas y desacuerdo | decision-review, design/ADR según dueño | Perspectivas ejecutadas y fallos parciales explícitos |
| Crítica externa aislada | referencia y transporte compartidos | Contratos por versión/OS, deadline, herramientas y datos aislados |
| Audiencia/participación/entrega | external-communication, transport propietario | Guards en cada ruta, receipts y positivos/negativos reales |

No se introducen ledgers competidores, aprobación automática de memoria,
paquetes universales, modelos por defecto nuevos o efectos externos. Altas,
consolidaciones, recursos, mappings, exports y docs ES/EN se resolverán
juntos en T-08/T-10/T-11/T-15. Los nombres de destino son propuestas propias,
no archivos de producción entregados por esta comparación. T-14 debe
verificar escenarios y eficacia con sus límites, además de estructura.

TDD n/a: prosa/evidencia de comparación. Hashes, enlaces, scope y pruebas de
índice validan trazabilidad; no prueban ninguna de las puertas funcionales
anteriores. Ningún precio leído se escribió en la configuración del usuario.
