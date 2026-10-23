# Comparación de comercio exterior, Flutter y dashboards operativos

Fichas S066–S068 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`: tres cuerpos completos,
47.421 bytes/929 líneas, sin recursos en sus directorios. También se leyeron
las cinco reglas Dart y sus cinco bases comunes: 30.350 bytes/1.080 líneas.
[trade-flutter-reading-evidence.json](trade-flutter-reading-evidence.json)
registra 25 fuentes y 27 contrapartes propias, rangos, reutilizaciones,
24 contrastes oficiales y tres accesos que no entregaron el documento pedido.
[tasks.md](../tasks.md) conserva el progreso.

Los destinos son propuestas para T-08/T-10, no altas de producción. No se
ejecutaron código, scripts, tests, agentes ni comandos del corpus; tampoco
compiladores, screening, trámites aduaneros, dashboards o servicios externos.
Tokens/latencia son null. Las activaciones son checks estáticos. La lectura
parcial de otra skill, agente o comando no cuenta como evaluación completa.

## S066 — Comercio exterior con hechos y normativa por jurisdicción

**Identidad.** SHA-256
`f4d418c1407a0792e05e5bfea64635e752cdcfb97827851665c6c9902e7063d4`;
29.039 bytes/256 líneas; cero recursos locales. La búsqueda de referencias
en agentes, comandos, skills y reglas canónicos no encontró callers por nombre
fuera de su propio cuerpo. Eso no demuestra uso cero ni ejecución nativa.

**Contrato y contenido útil.** Especialidad para clasificación de mercancías,
documentación, origen preferencial, valoración, screening y respuesta a
consultas/auditorías. Requiere producto real y especificaciones, países,
fecha, partes, trayecto, modalidad y documentos; produce un expediente con
hechos, fuentes, alternativas, cálculos, desconocidos y borradores.
La decisión y presentación regulatoria pertenecen al operador autorizado,
broker o responsable de compliance del proyecto, no al rol técnico planner.
La afirmación de experiencia profesional del prompt no acredita una cualificación.

Conservar la secuencia de identificación técnica, notas y partidas candidatas,
regla aplicada, alternativas descartadas, rulings pertinentes y fundamento.
Origen preferencial requiere regla por producto/acuerdo, BOM y origen de
materiales, costes respaldados y certificación aplicable. Conservar valoración
ordenada, coherencia entre factura/packing/transporte, responsabilidades
contractuales, incidencias, respuesta y registro de cambios regulatorios.

**Correcciones comprobadas.**

- La regla 2(b) no decide por sí sola el carácter esencial: remite a la regla 3.
  La regla 3(a) contiene una excepción cuando distintas partidas describen solo
  componentes; no basta elegir la descripción aparentemente más específica.
  Mantener el texto y las notas aplicables, incluyendo 5/6; los ejemplos de
  coche, perfume, tejidos, partes o dispositivos multifunción no reemplazan
  la clasificación de la mercancía realmente presentada.
  [Reglas de interpretación de la OMA](https://www.wcoomd.org/~/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-interpretation-general-rules/general_rules_interpret_hs.pdf?la=en).
- S066 cita la lista consolidada OFSI. La publicación británica informa de su
  cierre el 28 de enero de 2026 y del uso de UK Sanctions List como fuente
  de designaciones. Un nombre de lista incluido en el prompt no garantiza
  vigencia ni que se haya consultado.
  [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list).
- El ejemplo del umbral estadounidense de 800 USD omite la suspensión de
  tratamiento duty-free. CBP publicó su aplicación desde el 29 de agosto
  de 2025, con excepciones específicas. La ficha acredita esa contradicción;
  no fija el tratamiento de un envío futuro sin consultar su fecha y régimen.
  [Guía de CBP](https://content.govdelivery.com/accounts/USDHSCBP/bulletins/3f01456).
- El clearing por similitud inferior al 85% y la supuesta tasa de falsos
  positivos del 95% no tienen evidencia en el cuerpo. Un cliente habitual
  tampoco queda autorizado por su historial. OFAC describe investigación
  de identidad, programa, autorizaciones/exenciones y distinción entre
  bloqueo y rechazo; las distintas listas no tienen una prohibición común.
  Conservar esa investigación y escalación sin automatizar una autorización
  por score ni un bloqueo global indiscriminado.
  [OFAC FAQ 5](https://ofac.treasury.gov/faqs/5).
- La tabla de sanciones mezcla máximos legales con importes de una primera
  infracción/mitigación. La edición oficial 2024 de §1592 contempla límites
  diferentes según pérdida de derechos y valor doméstico. Su prior disclosure
  distingue fraude de negligencia/gross negligence y considera declaración
  antes de la investigación o sin conocimiento de ella: no respalda exigir
  ausencia de investigación en todo caso ni asignar a gross negligence el
  importe descrito por S066. La edición leída demuestra el defecto; una
  respuesta real debe confirmar normativa y procedimiento vigentes.
  [19 USC §1592, edición 2024](https://www.govinfo.gov/content/pkg/USCODE-2024-title19/html/USCODE-2024-title19-chap4-subtitleIII-partV-sec1592.htm).
- DDP no impone el método deductivo por contener derechos en el precio.
  El acuerdo de valoración distingue transaction value, identical/similar,
  deductive, computed y fallback; permite invertir 4/5 a petición del
  importador. Se precisa el método admisible y sus ajustes del régimen real,
  sin convertir una etiqueta Incoterm en algoritmo de valoración.
  [Información técnica de la OMC](https://www.wto.org/english/tratop_e/cusval_e/cusval_info_e.htm).
- FOB 2020 transfiere riesgo al estar los bienes a bordo, no al cruzar la
  borda. ICC recomienda considerar FCA cuando se entregan al transportista
  antes de estar a bordo, por ejemplo en una terminal de contenedores.
  Evitar la prohibición abstracta por tipo de mercancía: comprobar entrega,
  lugar y contrato. Costes, riesgo, título, seguro y valoración son decisiones
  relacionadas con contratos propios.
  [ICC, reglas marítimas 2020](https://library.iccwbo.org/content/tfb/BOOKS/BK_0049/BK_0049_05_RulesSea.htm).

**Hechos que necesitan verificación por caso.** Tasas por partida, porcentajes
de clasificación/false positives, cumulación AfCFTA, datos nacionales,
certificados, plazos de conservación/entrada/claims, drawback y estados FTZ/TIB
no se heredarán como tabla universal. Preservar los mecanismos y preguntas,
consultando acuerdo, autoridad, producto y fecha para cada aplicación.
No se han contrastado todos los regímenes APAC ni cada ejemplo numérico.
Los avisos con fecha/fines, targets KPI, organigrama y ventanas de escalación
son ejemplos o políticas empresariales que requieren datos del proyecto.
Una plantilla de comunicación no constituye una obligación regulatoria.

**Comparación propia y decisión.** Analyst ya descubre hechos/restricciones;
documenter ya mantiene documentación. research-first aporta investigación
de herramientas, no doctrina aduanera. knowledge-check/knowledge-write
controlan recuperación y promoción; un expediente con datos de clientes
no se publica automáticamente como memoria aceptada. capability-check y
PROJECT-EXTENSIONS distinguen selección, conexión y autorización.

Conservar especialidad opcional `skills/trade-compliance/SKILL.md`, con
`references/classification-origin.md`, `references/valuation-documents.md`
y `references/screening-response.md`. Guardar allí método y trazabilidad;
los hechos sensibles del caso permanecen en el sistema privado del proyecto.
Los informes con efecto externo comparten el contrato propuesto de S060.
No crear otro motor fiscal, screening ni cliente para cada autoridad.

**Activación estática.** «Prepara el expediente de clasificación de este
producto» y «qué información falta para justificar el origen preferencial»
entran. «Comprueba el tracking del envío» corresponde a operación logística;
«calcula los tokens de la sesión» conserva el meter propio. Si falta fecha,
destino, especificación o fuente normativa, produce preguntas/desconocidos.
No inventa una clasificación definitiva, un score de cumplimiento ni un filing.

**Validación e impacto pendientes.** Casos de mercancía incompleta/mixta,
notas excluyentes, origen no demostrado, listas cambiadas, partes con alias,
regímenes diferentes, fuente ausente, cuantías/plazos y respuesta autorizada.
Configuraciones/conectores deben acreditarse en T-06/T-12; ninguna lista o
portal de screening se conectó. Alta opcional, documentación y evals en
T-10/T-14/T-15, sin convertir una especialidad en gate obligatorio de todo proyecto.

## S067 — Dart y Flutter por versión, estado y plataforma

**Identidad.** SHA-256
`43b6e45cc3f15d8de113ed2aa9884528a9207f83f6bb1901f72a712698705706`;
16.024 bytes/564 líneas; cero recursos locales. Dependencias leídas completas:
cinco reglas Dart y cinco comunes. S104 se leyó en salud del proyecto,
estado, seguridad y análisis estático; su evaluación completa sigue pendiente.
A015/A023 y C021/C022/C023 se leyeron solo en secciones de remisión.

**Contenido útil.** Null safety, inicialización, estados cerrados, igualdad y
colecciones, generación, async, streams, lifecycle, composición de widgets,
rebuilds, Cubit/BLoC/Riverpod y DI. Conservar límites dominio/data/presentación,
repositorios, DTO/mapping, use cases cuando aporten valor, navegación/reactividad,
HTTP, refresh, errores y fakes/unit/widget/integration/golden.
La descripción promete Provider, WebView y storage; el cuerpo no ofrece
el mismo detalle. Las reglas externas sí añaden alternativas sin BLoC/Riverpod,
WebView, plataformas, seguridad, análisis y comandos de build/test.

**Correcciones por versión y comportamiento.**

- Los ejemplos iniciales de AsyncState/UserState tienen subclases const y
  una base sin constructor const. La regla Dart de estilo sí muestra la base
  correcta. El diagnóstico del analizador confirma la restricción; no se
  compiló el ejemplo para acreditar un build.
  [Constructor const y super](https://dart.dev/tools/diagnostics/const_constructor_with_non_const_super).
- La factory Freezed escrita como class sin abstract/sealed corresponde a
  otro contrato: la migración v2→v3 exige esas palabras clave. GoRouter retiró
  GoRouterRefreshStream en v5 y Riverpod 3 renombró valueOrNull a value.
  No atribuir los helpers a las bibliotecas actuales sin declarar su
  implementación, imports, generación y restricciones del pubspec/lockfile.
  [Migración Freezed](https://raw.githubusercontent.com/rrousselGit/freezed/master/packages/freezed/migration_guide.md),
  [Changelog GoRouter](https://pub.dev/packages/go_router/changelog),
  [Cambios Riverpod 3](https://riverpod.dev/docs/whats_new).
- Record.wait espera todas las futures y, ante errores, devuelve
  ParallelWaitError con valores/errores. El rótulo structured concurrency no
  demuestra cancelación, deadline ni rollback. Mantener concurrencia cuando
  las operaciones son independientes y definir fallos parciales/efectos.
  [FutureRecord2.wait](https://api.dart.dev/dart-async/FutureRecord2/wait.html).
- mounted protege el uso del contexto tras un await; no ordena resultados.
  Dos logins, logout durante login o cierre del Cubit pueden producir
  resultados tardíos. Necesita dueño/cancelación o generación de petición
  y un contrato de estado que impida restablecer una sesión cancelada.
  [BuildContext.mounted](https://api.flutter.dev/flutter/widgets/BuildContext/mounted.html).
- const y separación en widgets reducen propagación desde el padre; el
  ejemplo que afirma que sus hijos const se reconstruyen innecesariamente
  no demuestra ese coste. Tampoco const significa jamás reconstruido ante
  otras dependencias. Medir árbol, dispositivo, escenario y frames antes de
  justificar selectores, extracción o cache; liberar controllers/subscriptions.
  [Buenas prácticas Flutter](https://docs.flutter.dev/perf/best-practices).
- CartCount cuenta líneas distintas; no es necesariamente cantidad total.
  CartTotal transforma productos ausentes/loading/error en precio cero.
  El dominio debe distinguir datos incompletos, unidades/cantidades y dinero;
  un test con fake que muestra 3 no acredita el cálculo del provider real.
- `_isRetry` limita un retry por request; no impide refresh simultáneos entre
  requests. Si refresh/fetch falla sin completar el handler, falta un camino
  explícito de error. Comprobar next/resolve/reject, coordinación, cancelación,
  body replayable e idempotencia antes de reintentar mutaciones.
  [Dio](https://pub.dev/packages/dio).
- El interceptor añade token sin comprobar origen y el ejemplo construye
  una ruta con id sin validación/encoding. La baseUrl no prueba que toda
  petición sea HTTPS ni impide destinos absolutos. Validar esquema/origen,
  redirects y parámetros, y evitar tokens en logs/telemetría.
- FlutterError, PlatformDispatcher y ErrorWidget tienen funciones distintas;
  instalar handlers no acredita inicialización, disponibilidad o consentimiento
  de Crashlytics. Un fallback UI no demuestra recuperación del estado.
  [Gestión de errores Flutter](https://docs.flutter.dev/testing/errors).

**Reglas externas: destino y ajustes.**

| Regla leída | Destino propuesto | Criterios conservados y ajuste |
|---|---|---|
| Dart estilo, R-f32e9908e99d | `references/language-state.md` | Formato, nombres, null safety, sealed, futures, imports y generación por versión; lowerCamelCase para nuevas constantes según Effective Dart, respetando convenciones existentes |
| Dart patrones, R-107cc1b36ad6 | `references/language-state.md`, `references/data-boundaries.md` y `references/network-navigation.md` | Repositorio/cache, DI, mapping, dominio/data/presentación y alternativas de estado; cache con tenant/frescura/sync, save local explícito y resultados tardíos tratados |
| Dart seguridad, R-3d88a89426ff | `references/platform-security.md` | Secretos cliente/backend, TLS, storage, enlaces, SQL, Android/iOS/WebView y builds; comprobar también scheme, datos/target/versiones y necesidades reales de export/JavaScript |
| Dart testing, R-d817606eaf0d | `references/testing-build.md` y métodos compartidos | Fakes, tiempo controlado, aislamiento, widget/golden/integration/LCOV; golden update intencional, fixtures reales y umbral declarado por proyecto |
| Dart hooks, R-abb3c5c9477d | `references/testing-build.md`; dispatch compartido T-09 | Formato/análisis/tests como herramientas opt-in; regenerar/upgrade son mutaciones distintas de comprobar; no instalar este JSON como hook nativo |
| Cinco bases comunes: R-1576f07f9bd1, R-6c35567dd4b8, R-6e2d9fc34efa, R-6ea226102b9c, R-73513665cef7 | Referencias Dart y métodos compartidos TDD/revisión/QA; reconciliación completa de reglas en T-06 | Mantener claridad, límites, seguridad y evidencia; no imponer immutabilidad a cualquier API, todos los tipos de tests/80%, agentes adicionales o formato de respuesta universal |

La regla de estilo exige SCREAMING_SNAKE_CASE, frente a la preferencia
lowerCamelCase de Effective Dart. El formatter actual gestiona trailing commas
y permite configurar ancho; no fijar 80 ni commas manuales como contrato único.
[Estilo Dart](https://dart.dev/effective-dart/style),
[dart format](https://dart.dev/tools/dart-format).

La regla de seguridad describe EncryptedSharedPreferences como implementación
Android estable. flutter_secure_storage documenta cambios de ciphers/migración
desde v10; los targets necesitan su contrato efectivo. PII no equivale a
guardar cualquier base de datos en un almacén de claves; distinguir datos,
encriptación, retención y almacenamiento. Config compilada/dotenv no convierte
claves de servidor en secretos inaccesibles desde un cliente.
[flutter_secure_storage](https://pub.dev/packages/flutter_secure_storage).

El JSON de hooks usa matcher como objeto y una variable CLAUDE_FILE_PATHS
sin extractor definido. El contrato oficial usa matcher de nombres de tools
y entrada JSON; requiere adaptar el file_path y las operaciones reales.
Las bases comunes también confunden Stop con fin de sesión. T-02/T-09
conservan el despacho por runtime; no se instalaron hooks ni se ejecutaron
formatters, tests, generators o upgrades.
[Hooks de Claude Code](https://code.claude.com/docs/en/hooks).

Los tests con providers necesitan contenedor por caso, lifetime y overrides
de la versión real. La documentación actual advierte del disposal sin
listeners y muestra utilidades propias de v3; no trasladarlas a versiones
anteriores. El fake de watchAll emite una sola snapshot y no prueba cambios
posteriores. Fakes/goldens no sustituyen pruebas de plataforma, red o navegación.
[Pruebas Riverpod](https://riverpod.dev/docs/how_to/testing).

**Comparación propia y decisión.** stack-practices/selector no incluyen Dart;
TDD, debug-root-cause, revisión y unit-tests ya son métodos únicos. El gate
de cobertura no detecta Dart/Flutter ni interpreta su LCOV. frontend-quality
aporta casos de estado/foco/rendimiento, pero sus APIs HTML/React no acreditan
comportamiento Flutter. QA conserva dueño de pruebas con herramientas del target.

Conservar especialidad opcional `skills/dart-flutter-practices/SKILL.md`, con
las cinco referencias anteriores y elección por pubspec, versión y plataforma.
La relación con S104 se decidirá tras su evaluación completa, conservando
contenido útil y un método de revisión único. Cubrir operaciones útiles de A015/A023/C021–C023 mediante roles
compartidos en T-04/T-05/T-11; no crear un revisor Flutter obligatorio.
No imponer Freezed/Riverpod/BLoC/Dio/Crashlytics ni migraciones de dependencias.

**Activación estática.** «Revisa el estado y navegación de esta app Flutter»
y «login tarda y revive la sesión después de logout» entran. «Refactoriza
un formulario React» conserva su guía; «mide cobertura Flutter» usa esta
especialidad con el gate compartido cuando tenga adaptador verificado.
Pendientes: analyzer/build con fixtures completas por versión, providers,
dispose/races, refrescos simultáneos, rutas y errores, tests por target y
LCOV de producto real. Adaptadores T-09/T-12/T-14; exports/docs T-15.

## S068 — Dashboards que responden preguntas operativas

**Identidad.** SHA-256
`6823d9984c060597a312b867c317e0969e1cb0a2dec19730ce944fe789f41d38`;
2.358 bytes/109 líneas; cero recursos locales. S176 y S212 remiten a esta
capacidad para rollout/operación y avance de producto. S022 se reutiliza
con hash/rangos verificados; S238/S277 se leyeron completos como dependencias,
sin contarlos todavía como otras skills evaluadas.

**Contrato útil.** Parte de las preguntas del operador: salud, cuello de
botella, cambios y acción. Requiere plataforma/versión, instrumentación,
fuentes y entorno; produce un dashboard mínimo con queries, títulos, unidades,
variables, umbrales, rango y refresco. Separa disponibilidad, latencia,
throughput, saturación y riesgo del servicio; elimina paneles sin pregunta.
Los ejemplos Elasticsearch/Kafka/ingress son conjuntos de preguntas, no
metric names ni queries verificadas para todos los exporters.

**Diferencias operativas.**

- La checklist JSON válido no acredita el modelo del destino. Grafana
  documenta Classic, V1 Resource y V2 Resource; comprobar versión/esquema,
  datasource UID, queries, permisos y proceso de importación real.
  [Modelos de Grafana](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/view-dashboard-json-model/).
- SigNoz documenta importación JSON/Grafana y presupone una aplicación
  instrumentada. Ese soporte no demuestra que cualquier export funcione,
  tenga las mismas fuentes o produzca resultados. Un recurso generado y un
  dashboard importado/consultado son estados diferentes.
  [Dashboards SigNoz](https://signoz.io/docs/userguide/manage-dashboards/).
- p50/p95/p99 necesitan datos y agregación válidos. Prometheus advierte que
  quantiles de summaries no se agregan entre workers; los histogramas
  requieren el contrato de buckets/distribución y ventana de consulta.
  No promediar percentiles ni representar falta de muestras como salud.
  [Histogramas y summaries](https://prometheus.io/docs/practices/histograms/).
- Umbrales/colores significan algo solo con unidades, rango, ventana y criterio
  del servicio. Distinguir desconocido, vacío, stale, acceso rechazado y
  consulta fallida; probar filtros, cardinalidad, coste/refresco y drill-down.
  Cada estado accionable necesita fuente/fecha y una acción o runbook pertinente.

**Comparación propia y decisión.** plugin-panel inventaría el catálogo;
roadmap-dashboard representa ledgers y métricas de proceso. observability
separa el meter de coste del monitor vivo externo. delivery-practices
ya exige readiness/recuperación y permisos MCP; frontend-quality ya exige
filtros y estados observables. Ninguno genera actualmente dashboards de
observabilidad para servicios Grafana/SigNoz.

Conservar especialidad opcional `skills/operational-dashboards/SKILL.md`, con
`references/metrics-panels.md` y `references/platform-contracts.md`.
Comprobar schemas/queries/importación según instancia disponible. Usar
conectores del proyecto seleccionados por contrato; no instalar un collector
global ni otro backend de monitorización por activar la skill.

En T-13 aplicar las preguntas y estados útiles al panel propio: quién usa
cada sección, qué evidencia explica el estado y qué acción permite. Su
inventario local conserva su naturaleza; fuentes presentes, MCP declarado
o hooks configurados no se transforman en checks verdes de ejecución.
El roadmap conserva su ledger y el coste su meter, con frescura/procedencia.
La gestión del control panel completo del corpus sigue pendiente en T-06.

**Activación estática.** «Construye un dashboard Kafka para detectar lag y
particiones sin replicar» y «quiero distinguir errores, saturación y latencia
de este servicio» entran. «Abre el catálogo del plugin» usa plugin-panel;
«cómo va esta iniciativa» usa roadmap-dashboard. «Hazlo más vistoso» sin
pregunta ni datos requiere definir el contrato de UI antes de inventar métricas.

**Impacto y validación pendientes.** Fixtures de schema por plataforma,
fuentes ausentes, ventana/unidades/filtros, queries válidas con muestras,
agregación, error/stale y round-trip import/export con permisos. Diseño,
adaptadores e integración T-08/T-10/T-12/T-13, escenarios T-14 y docs/exports
T-15. No se conectó, importó ni renderizó ningún dashboard en este pase.

## Límites de la evidencia

Los hashes y los checks de enlaces prueban identidad/trazabilidad; no prueban
compilación, validez legal de un caso futuro, eficacia, permisos o integración.
Las diez reglas externas están leídas, pero la reconciliación global de reglas
y su aplicación automática se conserva en T-06. Sus instrucciones son material
comparado; no activan agentes, políticas, scripts o cambios del consumidor.

Los tres accesos rechazados se separan del contenido leído: ICC Academy
respondió HTTP 403, US Code devolvió una página de mantenimiento con HTTP 200
y la edición 2025 de GovInfo redirigió a /error con HTTP 200. Se leyó la regla
ICC en su biblioteca y §1592 en la edición oficial 2024. Un HTTP 200 por sí
solo no acredita que se haya obtenido el documento normativo solicitado.
