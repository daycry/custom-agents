# Comparación de fundamentos de interacción y sistemas de agentes

Fichas S001–S005, revisión `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Son decisiones de comparación y destinos **propuestos**, no altas entregadas.
El progreso canónico está en [tasks.md](../tasks.md), T-03; T-08 resolverá el
diseño conjunto después de comparar el catálogo completo.

Los cinco cuerpos se leyeron completos. Cada directorio contiene únicamente su
cuerpo: no hay scripts, assets ni referencias locales adicionales. Se leyeron
los consumidores y referencias necesarios para estas decisiones, diferenciando
invocación, enlace relacionado, configuración de instalación y ejemplo.
[reading-evidence.json](reading-evidence.json) conserva IDs, hashes, tamaños y
rangos realmente leídos de 18 fuentes y 13 archivos propios. Leer una sección
de un consumidor no constituye la evaluación completa de esa otra pieza.

La búsqueda de consumidores se concentró en agentes, comandos, skills,
configuración y manifiestos canónicos. La revisión de adaptadores, generadores
y documentación operativa completa sigue en T-06. Las decisiones deberán
revalidarse si esa revisión encuentra otro contrato consumidor relevante.

## S001 — Accesibilidad por plataforma

**Identidad.** SHA-256
`2762f21d09d199009ed4f95b28c911436b367c30963dc5ddb48b8e1ad7fc1585`;
6.546 bytes, 146 líneas, cuerpo completo. Recursos locales: ninguno.

**Contrato.** Parte de un componente o flujo y su plataforma; decide semántica,
nombre accesible, estado, foco y criterios aplicables. Produce especificaciones,
ejemplos y comprobaciones de accesibilidad. Architect conserva las decisiones;
implementer, el código; reviewer, los defectos; qa, la evidencia de pruebas.
La skill no necesita un quinto propietario del mismo componente.

**Valor y defectos.** Las secciones de atributos, interacción y checklist añaden
contraste, tamaños, arrastre alternativo, entrada redundante y correspondencias
web/iOS/Android. Los ejemplos de búsqueda y toggle concretan nombre y rol.
Las recomendaciones de semántica nativa, modales y etiquetas ya están cubiertas
en parte. Hay correcciones necesarias antes de trasladar ejemplos:

- El foco visible corresponde a 2.4.7; 2.4.11 trata de no ocultar completamente
  el componente enfocado. 2.4.13 es AAA, no un requisito AA indiscriminado.
- El tamaño mínimo web de 2.5.8 tiene excepciones; no basta imponer un cuadrado
  a todo control. Reflow requiere su alcance y excepciones, no un único zoom
  universal para cualquier contenido. [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- En Compose, `stateDescription` describe estado; no sustituye cualquier hint.
  [Semántica de Compose](https://developer.android.com/develop/ui/compose/accessibility/semantics).
- El ejemplo SwiftUI de actualización en vivo y el tamaño «native» compartido
  por iOS/Android no están comprobados con SDKs. Conservar la necesidad de
  anunciar cambios y de tener targets adecuados; verificar APIs y unidades por
  plataforma antes de publicar código. No se afirma que una API no exista por
  no haberla encontrado ni se rechaza ese dominio por no usarlo aquí.

**Comparación propia.** `frontend-quality/SKILL.md` y
`references/interaction-performance.md` cubren controles nativos, etiquetas,
teclado, foco al abrir/cerrar, formularios y pruebas visuales. Su sección
«Contratos que se prueban con acciones del usuario» carece del mapa normativo
concreto y de orientación nativa por plataforma. `agents/qa.md` P4-ter declara
los bloques A11Y informativos fuera del umbral actual del gate: ampliar la guía
no puede convertir por sí solo esa evidencia en una garantía de conformidad.

**Dependencias y consumidores.** A001 invoca el método y repite parte del
checklist; S229/S231/S290 y A055/C076/C077 lo enlazan para composición, pruebas
y revisión; S176 lo incluye en flujos de producto con predicciones. El mapa
R-0243aba303d6 lo selecciona para React. R-591e7a1672e1 y R-03ffcc8e6e9e son
declaraciones de distribución, no evidencia de ejecución. Las guías vecinas de
diseño y SwiftUI son enlaces relacionados, no recursos cargados obligatoriamente.
No declara MCP ni ejecutor local. El uso de SDKs, lectores de pantalla o scanner
depende del proyecto y la plataforma; su ausencia debe quedar explícita.

**Decisión y destino propuesto.** **Ampliar** `skills/frontend-quality/` con
`references/accessibility-criteria.md` para criterios y excepciones web, y
`references/native-accessibility.md` para correspondencias verificadas por
plataforma. Mantener el método de interacción en su referencia actual y enlazarlo,
sin duplicarlo. Conservar todos los criterios útiles anteriores, incluidas
alternativas al color, etiquetas de iconos, cierre de modales, retorno de foco,
ayuda de errores y anuncios de estado. No copiar los ejemplos nativos pendientes
como código validado ni convertir el rol de diseño en implementer.

**Activación propuesta, revisión estática.** Literal: «Revisa accesibilidad de
este formulario». Paráfrasis: «No puedo usar este diálogo con teclado y lector
de pantalla». Negativo vecino: «Compara el coste de dos agentes» → outcome-evals.
Los casos distinguen interacción de medición de agentes; no se ejecutó el
selector ni una sesión nativa con estos casos nuevos.

**Coste y degradación.** Cuerpo actual 6.546 bytes/146 líneas; recursos locales
0 bytes/0 líneas. Cargar el mapa corto y solo la referencia de la plataforma
afectada. Tokens y latencia: null. Sin SDK/scanner, conservar pruebas posibles
y señalar las no ejecutadas; no anunciar conformidad completa por un checker.

**Validación e impacto.** Hash, tamaño, ausencia de recursos locales y referencias
de consumidores comprobados con lectura y helper privado. Contraste documental
con WCAG/APG/Compose el 2026-10-07; no se compilaron ejemplos SwiftUI/Compose ni
se ejecutaron lectores de pantalla, axe o E2E para esta incorporación. T-10/T-11
deben actualizar dependencias y enlaces de los destinos adoptados; T-14 probará
los escenarios y T-15 actualizará catálogo, exports y documentación ES/EN.
No se cambia todavía qa-gate ni se adopta automáticamente el ADR de A001.

## S002 — Diagnóstico de arquitectura de agentes

**Identidad.** SHA-256
`64f57e232c3533877403703bc95b3c75df9de23f657899a306f13c703009ff57`;
10.278 bytes, 257 líneas, cuerpo completo. Recursos locales: ninguno.

**Contrato.** Recibe sistema, entradas, modelos, síntomas y ventana del incidente.
Localiza el fallo en ensamblado de instrucciones, historial, memoria, destilación,
recuperación, selección/ejecución/interpretación de herramientas, formato,
transporte, reparación o persistencia. Produce hallazgos priorizados con
mecanismo, referencia de evidencia, causa y corrección propuesta. La revisión
corresponde a reviewer; la modificación, a implementer; el veredicto, a qa.
Architect utiliza los resultados que afecten a alternativas de diseño.

**Contenido único.** «The 12-Layer Stack», los cinco patrones y las preguntas de
diagnóstico separan fallos del modelo de los introducidos por wrappers: respuestas
mutadas, ejecución fingida, recuerdos contaminados, artefactos comprimidos que
reingresan como hechos y llamadas de reparación no visibles. El informe vincula
síntoma, mecanismo, capa, causa, evidencia y confianza. El orden de corrección
prioriza contratos de código, límites de reparación, admisión de memoria y menor
duplicación de contexto antes de aumentar instrucciones.

**Comparación propia.** `debug-root-cause` aporta reproducción, aislamiento e
hipótesis probada; no ofrece el mapa de capas ni una revisión preventiva del
sistema de agentes. `capability-audit` evalúa piezas del catálogo, no la ejecución
de una aplicación de agentes. `plugin-dev` contiene determinismo, DRY y degradación,
pero tiene alcance de autoría del plugin. `architect` conserva design.md y ADR
propuesto: no puede absorber una auditoría que produzca código e informe de QA
bajo el mismo propietario. La validación nativa pendiente de T-02/T-09 demuestra
también por qué una regla escrita no puede tratarse como guardia aplicada.

**Dependencias y consumidores.** S002 remite a S003 para benchmark, S004 para
diseño y S005 para depuración de ejecución. Esos cuerpos se leyeron completos.
La recomendación de escáner de seguridad no aporta una dependencia ejecutable
aquí: se deriva al método de seguridad propio si el alcance lo requiere.
R-591e7a1672e1/R-03ffcc8e6e9e declaran distribución. El frontmatter declara
Read/Write/Edit/Bash/Grep/Glob; esa metadata no demuestra permiso ni soporte
portable en los tres runtimes. No hay scripts, MCP ni API del proveedor
invocados por la pieza. Los ejemplos de `rg` son pistas de búsqueda,
no detectores suficientes ni pruebas de ejecución defectuosa.

**Decisión y destino propuesto.** **Consolidar** con S004 en una capacidad compartida
`skills/agent-system-quality/SKILL.md`, con
`references/architecture-diagnostics.md` y
`references/tool-observation-contracts.md`. Es una especialidad opcional presente
en el corpus; no un nuevo paquete obligatorio. Mantener las doce áreas, los cinco
patrones, la recolección de evidencia, preguntas y orden de corrección. Reutilizar
debug-root-cause cuando haya un fallo reproducible, outcome-evals para comparar y
los controles de seguridad existentes para ese alcance. Adaptar gravedad al
vocabulario de revisión propio conservando urgencia y motivo; una cifra de
confianza declarada no se publicará como probabilidad calibrada.

El esquema de informe necesita identidad propia y destino acordado en T-08.
Debe servir como evidencia de la tarea/informe de revisión, sin crear un segundo
ledger ni aprobar memoria. La obligación de auditar cualquier release de cualquier
aplicación del origen se cambia por activación pertinente al contrato del proyecto.
Las envolturas tipadas internas son una alternativa técnica, no una exigencia de
reescribir todas las respuestas o APIs de los runtimes.

**Activación propuesta, revisión estática.** Literal: «Audita la arquitectura de
esta aplicación de agentes». Paráfrasis: «El modelo funciona directamente, pero
nuestro wrapper contamina las respuestas; localiza la capa». Negativo vecino:
«¿Qué agente obtiene mejor tasa de éxito?» → outcome-evals. Sin ejecución del
selector ni sesión nativa para estos casos nuevos.

**Coste y degradación.** 10.278 bytes/257 líneas; recursos locales 0 bytes/0 líneas.
Separar mapa de activación de diagnóstico detallado y leer únicamente las capas
aplicables. Tokens/latencia null. Sin logs/modelos disponibles, comparar código y
contratos existentes, indicar la evidencia ausente y no fabricar la trayectoria,
ejecución de herramientas, diagnóstico concluyente o eficacia de la corrección.

**Validación e impacto.** Lectura completa, comparación de secciones y hashes
verificados. No se ejecutaron consultas de modelos ni se auditó un sistema de
consumidor; los patrones son una propuesta de método. T-08 fijará formato/dueño
del informe; T-10/T-11 deberán mantener redirects, dependencias, selección y
criterios compartidos; T-14/T-15 cubrirán evals, ejecución, docs y exports. No se
instala la distribución de origen ni se mantienen aliases vacíos.

## S003 — Comparación reproducible de agentes

**Identidad.** SHA-256
`57fa683e356b6f5612bc6d7dc101ae39c126e6edf9a48f4ec53afea3e80d7e5d`;
4.696 bytes, 147 líneas, cuerpo completo. Recursos locales: ninguno.

**Contrato.** Recibe casos representativos, revisión, petición, criterios y agentes
candidatos. Propone ejecuciones aisladas y repetidas; produce comparación por caso
de éxito, variación, tiempo y coste disponible. qa conserva la verificación; una
comparación no aprueba automáticamente una tarea ni conocimiento.

**Contenido único y límites.** «Git Worktree Isolation», workflow y prácticas
concretan copias iniciales independientes, revisión fijada, varias tareas reales
y repeticiones. Los jueces deterministas se separan de patrones y juicio de modelo.
Tres repeticiones son un comienzo para observar variación, no una conclusión
universal. Un worktree aísla archivos del repositorio; no aísla por sí solo red,
credenciales, servicios, permisos ni cachés personales.

**Comparación propia.** `outcome-evals/references/protocol.md` ya exige casos y
checks definidos antes, mismas condiciones, baseline/variante, repetición,
clasificación de ausentes y juicio auxiliar separado. `report_outcomes.py` agrega
JUnit existente con revisiones/fixtures/condiciones, métricas opcionales y checks
acotados; no lanza agentes ni crea worktrees. No se presenta ese agregador como
equivalente a un runner. El criterio textual de una palabra del ejemplo tampoco
prueba el comportamiento de backoff: el protocolo propio ya distingue ese límite.

**Dependencias y consumidores.** El único ejecutor propuesto está en un repositorio
externo; no viene incluido como recurso de la pieza. La
[documentación de su CLI](https://github.com/joaquinhuigomez/agent-eval) consultada
el 2026-10-07 muestra `--tasks`, `--agents` y `report --input`; difiere de los
flags singulares y `report --format` del cuerpo. También muestra otra estructura
de YAML. Esto prueba una discrepancia documental, no qué variantes acepta una
versión ejecutada. No se instala ni ejecuta el runner. Codex no figura entre los
adaptadores incorporados que enumera ese README; un adaptador propio no equivale
a compatibilidad ya comprobada.

S002 y S007 remiten a esta función; R-591e7a1672e1/R-03ffcc8e6e9e la distribuyen.
El frontmatter declara Read/Write/Edit/Bash/Grep/Glob; la ejecución del runner
necesita herramientas y permisos reales de la sesión, no esa declaración.
El agente cuyo nombre comparte un prefijo de evaluación no se contabiliza como
invocador sin una referencia real. Una futura integración exige revisión fijada
del runner, contrato de sus adapters, comandos válidos y autorización vigente
para sesiones con coste; la mención de instalación no concede esa autoridad.

**Decisión y destino propuesto.** **Consolidar** el método en
`skills/outcome-evals/references/protocol.md` y añadir
`references/agent-comparisons.md` para aislamiento, repeticiones y condiciones
por runtime. Conservar casos versionados, revisión, jueces, métricas ausentes y
variación. En T-08/T-12 elegir reutilización de runner o un recurso nativo solo
si añade ejecución útil con contrato real; no copiar comandos dudosos ni crear
un segundo agregador JUnit. Hasta entonces, declarar preparación/manual de
ejecución en vez de automatización entregada.

**Activación propuesta, revisión estática.** Literal: «Compara dos agentes con
estas tareas». Paráfrasis: «Mide si cambiar el workflow mejora el éxito y el coste».
Negativo vecino: «Un agente repite un comando y no termina» → debug-root-cause.
Estos casos no se ejecutaron en selector ni sesiones de modelos.

**Coste y degradación.** 4.696 bytes/147 líneas; recursos locales 0 bytes/0 líneas.
Leer el protocolo solo al preparar la comparación y las condiciones del runtime
que se vaya a medir. Tokens/latencia null. Sin runner o adapters, puede entregarse
protocolo preparado; ejecuciones no realizadas quedan not-run, coste ausente null.
No instalar herramientas ni lanzar todos los agentes al detectar sus nombres.

**Validación e impacto.** Hash y lectura comprobados, contraste documental externo
realizado; CLI, instalación, benchmark y compatibilidad de adapters **no ejecutados**.
El código del agregador propio se leyó, sin atribuir sus tests previos a esta
propuesta. T-10/T-12/T-14 tendrán que cubrir ejecución autorizada, negativos,
repeticiones y fallos; T-15 actualizará consumidores, catálogo, docs ES/EN y exports.
Mantener el almacenamiento opt-in de casos y la aprobación humana de Gold.

## S004 — Contratos de herramientas y observaciones

**Identidad.** SHA-256
`e7fb390a6663b46ea5d3c2876753a5ce32ba3bad1889686b21a42894caa1742d`;
2.100 bytes, 74 líneas, cuerpo completo. Recursos locales: ninguno.

**Contrato.** Recibe operaciones, riesgos, entradas y observaciones de una aplicación
de agentes. Decide granularidad, esquemas, salida, recuperación y presupuesto de
contexto; produce criterios de diseño y contratos que implementer convierte en
recursos y qa verifica. No es un runtime que pueda compactar o reparar la sesión
por el hecho de cargar la skill.

**Contenido único.** «Granularity Rules», «Observation Design» y «Error Recovery
Contract» enlazan tamaño de operación con riesgo/overhead y exigen resultados
interpretables, siguiente paso y condición de parada. «Core Model» une calidad de
acciones, observación, recuperación y contexto. «Benchmarking» plantea éxito,
reintentos y coste por éxito: cada métrica necesita definición, denominador y
datos compatibles; no se deduce pass@k del nombre de un contador de repeticiones.

**Comparación propia.** `plugin-dev` ya exige determinismo, DRY, recursos existentes
y degradación de piezas opcionales, pero no diseña el espacio de acciones de las
aplicaciones del consumidor. `read-discipline.md` exige búsqueda y lectura acotada;
`capability-check.md` carga referencias pertinentes y distingue disponibilidad.
Falta la comparación explícita de granularidad y del contrato de observación.
`outcome-evals` aporta el método para evaluar las variantes sin inventar eficacia.

**Dependencias y consumidores.** S002 remite a este diseño. S240 lo menciona dentro
de un ejemplo de evidencia de límites de iteración: no es una invocación
automática. R-591e7a1672e1/R-03ffcc8e6e9e son distribución. No hay scripts, MCP,
proveedores ni dependencias externas obligatorias. Las etiquetas de arquitecturas
son alternativas orientativas, no APIs ejecutables ni superioridad medida.

**Decisión y destino propuesto.** **Consolidar** con S002 en
`skills/agent-system-quality/references/tool-observation-contracts.md`.
Preservar nombres estables, entradas estrechas, forma determinista, granularidad
según riesgo, observación legible, artefactos, recuperación y límites explícitos.
Reutilizar la carga bajo demanda y el protocolo de outcome-evals. El ejemplo de
envoltura de respuesta es para tools que se diseñan; no imponerlo a APIs nativas
ajenas ni transformar silenciosamente su salida. La compactación en fronteras
de fase queda condicionada a capacidades reales, no como acción prometida.

**Activación propuesta, revisión estática.** Literal: «Diseña las herramientas de
esta aplicación de agentes». Paráfrasis: «Las respuestas de las tools son opacas
y el agente no sabe recuperarse; revisa sus contratos». Negativo vecino:
«Audita colisiones entre las skills del catálogo» → capability-audit.
Sin ejecución del selector ni sesión nativa para estos nuevos casos.

**Coste y degradación.** 2.100 bytes/74 líneas; recursos locales 0 bytes/0 líneas.
Mapa corto más referencia de diseño bajo demanda, compartida con el diagnóstico
sin cargar ambos cuerpos completos. Tokens/latencia null. Sin instrumentos o
APIs mutables, entregar contratos/propuesta, no afirmar cambios de runtime,
compactación, mejora de tasa o ejecución. No añadir tools por cada operación
sin justificar el riesgo o el coste observado.

**Validación e impacto.** Lectura, hashes y comparación de contratos realizados;
no se implementó ni ejecutó un harness por esta ficha. T-08 definirá integración
compartida; T-10/T-11/T-12 conservarán referencias, responsabilidades y contratos;
T-14 probará escenarios positivos y negativos, datos faltantes y recuperación;
T-15 mantendrá catálogo, documentación y exports sin aliases vacíos.

## S005 — Diagnóstico de bucles y deriva de ejecución

**Identidad.** SHA-256
`0cdbfe3c822ff50d21df8cd0e20c72407a6f5658089edc0e96e79a03927cb956`;
5.627 bytes, 154 líneas, cuerpo completo. Recursos locales: ninguno.

**Contrato.** Recibe una ejecución que repite fallos, acumula contexto o pierde
estado/objetivo. Captura último éxito/fallo, objetivo, secuencia pertinente,
cwd/rama/servicio y supuestos; clasifica patrón, prueba una hipótesis y aplica
recuperación acotada autorizada. Produce evidencia y resultado completo/parcial
o bloqueo. El propietario sigue siendo el rol que depura la tarea; qa conserva
el veredicto si cambia código.

**Contenido único.** «Failure Capture» relaciona intención activa, progreso real,
presión de contexto y suposiciones del entorno. La tabla distingue límite de
tools/sin salida, contexto duplicado, conexión/puerto, cuota/retry storm,
cwd/rama/carrera y una hipótesis de fix fallida. Las heurísticas conservan el
objetivo mientras reducen la operación que falla y exigen observar antes de
reintentar. No prometen resets o auto-healing que no se ejecutan.

**Comparación propia.** `debug-root-cause` ya tiene cuatro fases con evidencia,
hipótesis falsable, límite de intentos y regresión. No necesita otro ciclo de
depuración. Le falta un mapa explícito de captura para ejecución de agentes y
patrones de contexto/observación. Su cierre de memoria solo sucede tras fix
comprobado y bajo knowledge-write/Knowledge Gate; la remisión del origen a
aprendizaje no puede convertir cualquier reflexión del agente en memoria aceptada.
El gancho de tercer rojo, su intervención humana y su contador son un contrato
existente que esta consolidación no modifica de forma implícita.

**Dependencias y consumidores.** S002 lo remite para fallos de ejecución;
R-591e7a1672e1/R-03ffcc8e6e9e declaran distribución. Las referencias a verificación,
aprendizaje, deliberación y estado del workspace son rutas de continuación,
no ejecutores locales. No hay scripts, MCP ni conexiones necesarias en el cuerpo.
Para aplicaciones reales, salud de servicios, branch y filesystem deben
consultarse con herramientas disponibles dentro del alcance autorizado.

**Decisión y destino propuesto.** **Ampliar** `skills/debug-root-cause/` con
`references/agent-runtime-failures.md`, enlazado desde su mapa de activación.
Conservar captura, clasificación, prueba discriminante, recuperación reversible,
resultado/evidencia y las prohibiciones de retry ciego y reset ficticio. Encajar
esos datos en las cuatro fases actuales; reutilizar el informe/evidencia del
ledger, no añadir un segundo procedimiento ni un historial de monólogos.
Derivar verificación a qa y aprendizaje a Knowledge Gate; ambigüedad de producto
a analyst/pm-cycle. No reducir la meta a una suboperación que resulte más fácil.

**Activación propuesta, revisión estática.** Literal: «Diagnostica el bucle de este
agente». Paráfrasis: «Repite la misma tool, pierde el objetivo y no avanza».
Negativo vecino: «Diseña desde cero sus esquemas de herramientas» → la capacidad
compartida de calidad de sistemas de agentes propuesta por S002/S004.
La intención de diagnóstico tiene destino actual; el redirect de diseño solo
será invocable después de la entrega correspondiente. Casos no ejecutados.

**Coste y degradación.** 5.627 bytes/154 líneas; recursos locales 0 bytes/0 líneas.
Mantener mapa corto y leer patrones de ejecución solo cuando proceda. Tokens y
latencia null. Sin trazas o procesos observables, señalar qué no puede verificarse
y presentar diagnóstico parcial; no afirmar recuperación ni usar el paso del
tiempo como respuesta/permiso. La guía no añade un runtime de monitorización.

**Validación e impacto.** Lectura completa, consumidores pertinentes y hashes
comprobados; no se provocaron bucles de consumidor ni se ejecutó recuperación
de modelo como parte de esta ficha. T-10/T-11 deben actualizar activación,
referencia y redirects sin alterar el contador del dev-cycle accidentalmente.
T-14 debe comprobar evidencia parcial, herramientas ausentes y guardias reales;
T-15 cerrará docs, dependencias y exports. Los contratos nativos pendientes de
T-02/T-09 se mantienen como pendientes, no como limitaciones resueltas por prosa.

## Validación de la comparación

Comando privado `build_skill_read_evidence.py` con Python 3.13: exit 0;
18 lecturas de origen y 13 propias registradas, hashes de origen coincidentes
con corpus fijado y cinco directorios sin recursos adicionales. El helper valida
identidad y rangos; la evaluación semántica es la lectura y comparación descrita
en cada ficha, no el resultado del helper.

Fuentes técnicas consultadas el 2026-10-07: WCAG 2.2, APG para
[diálogo modal](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), semántica
Compose y documentación del runner externo enlazadas en S001/S003. La página
[Apple consultada](https://developer.apple.com/documentation/accessibility/accessibilitynotification/announcement)
requiere JavaScript y no acreditó la API del ejemplo: se mantiene sin verificar.
No se ejecutaron scripts del corpus ni sesiones pagadas.

Los escenarios de activación son **comparaciones estáticas de intención**, no
resultados de evals ni pruebas de comportamiento. Las integraciones, recursos
ejecutables, atribución de contenido adaptado y validación por runtime siguen
en T-08 a T-15. Esta ficha no acredita el resto del catálogo ni cierra T-03.
