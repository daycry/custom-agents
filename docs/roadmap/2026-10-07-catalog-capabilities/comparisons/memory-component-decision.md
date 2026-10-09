# Cómo elegir los componentes de memoria para agentes y personas

El usuario confirma tres candidatos: Kwipu, Graphiti y Graphify. La elección puede
conservar tres, dos, uno o ninguno. La memoria fundamental seguirá disponible
para agentes y personas aunque ningún servicio externo aporte valor suficiente.

Esta lectura fija fuentes primarias al 2026-10-09. No instaló componentes ni
ejecutó consultas, benchmarks, restauraciones o interfaces. Una comprobación
independiente de disponibilidad consultó health e inventario de modelos del
despliegue existente, sin recuperar memoria ni enviar inferencias. La
[evidencia de lectura](memory-component-reading-evidence.json) distingue fuentes,
revisiones, hashes y rangos. Las capacidades anunciadas son hipótesis de utilidad;
su publicación no demuestra que funcionen mejor en nuestro proyecto.

La [dirección aceptada](../operational-priorities.md) mantiene Markdown local
como origen canónico. El [contrato de comandos y panel](memory-command-contract.md)
define la consulta explícita y acotada. Esta comparación añade selección
de componentes; no cierra T-07, T-11 o T-13 ni añade nuevas skills.

Actualización del bloque16: la consulta común está implementada y validada
por revisión A/B/C/D, QA Windows/Linux y siete casos reales del panel en Chrome.
El cuarto pase acotado cerró el defecto de comillas; un addendum A/B corrigió
únicamente el guard de red del test Linux. CLI y panel comparten snapshot,
búsqueda, ID, relaciones, procedencia y diagnósticos de parcialidad.
La [evidencia de implementación](../testing/memory-query-evidence.json) separa
cohortes, fallos preservados y límites. Esta entrega parcial no demuestra mejor
calidad de recuperación ni completa la selección de componentes.

## Comparación con la memoria de referencia y la propia

La referencia comparada está fijada a `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Los recursos `R01` a `R08` de la evidencia conservan hashes y líneas de código
y documentación leídos. La lectura compara sus contratos; no ejecutó sus hooks,
MCP ni pruebas y no infiere eficacia de sus ejemplos.

| Capacidad | Referencia comparada | Plugin propio | Aporte candidato por demostrar |
|---|---|---|---|
| Continuidad | Resumen de sesión, coincidencia de repositorio y envoltura histórica al reanudar; posible resumen con modelo | Journal separado y reanudación con estados y evidencia | Los tres deben complementar la continuidad sin repetir acciones antiguas. |
| Aprendizaje | Observaciones por proyecto, patrones con confianza y evolución a componentes | Propuestas del journal y decisión del curador antes de aprobar | Recuperar mejor no sustituye aprobar patrones o instrucciones. |
| Memoria explícita | Markdown por proyecto/equipo/usuario, ID, estado, procedencia y destinos; confianza admitida `unreviewed` | Conocimiento aprobado versionado, candidatos y memoria episódica distintos | Kwipu y Graphiti deben resolver citas al ID/versión/estado propios. |
| Recuperación | Scoring léxico local; CLI y MCP usan el mismo vault; límites de archivos/bytes y diagnósticos de truncamiento | Búsqueda local y router por intent con respaldo; snapshot común acotado validado por QA de implementación | Kwipu puede añadir recuperación semántica; Graphiti relaciones e historial; Graphify estructura de código. |
| Uso humano | CLI y Markdown legible; el ejemplo de conformidad no acredita UX | Documentos, estado y consulta explícita del panel; búsqueda/ID/relaciones compartidas validadas en Chrome | Kwipu ofrece exploración documental; Graphify navegación de código; Graphiti necesita presentación propia. |

`R01` limita el escaneo a 5.000 entradas y 16 MiB; `R02` limita documento y cuerpo.
La búsqueda exige estado activo, pero no aprobación: `R02` solo admite confianza
`unreviewed`. `R03` y `R04` delegan búsqueda en el mismo motor; el servidor fija
identidad del consumidor y permite memoria de usuario solo por opt-in. Estas
ideas justifican un contrato común y límites explícitos, sin copiar su confianza
como autoridad de nuestro Knowledge Gate.

`R05` describe un verificador de procedencia de ejemplo y pruebas sintéticas
de conformidad. El verificador no está habilitado en el CLI/MCP central: no lo
contamos como garantía de verdad, archivo durable o autenticación. `R06` y `R07`
separan resumen pasado de instrucciones actuales. `R08` describe aprendizaje con
observador; su afirmación de fiabilidad no es una medición de esta revisión.

La mejora útil frente a ambas bases debe ser concreta: encontrar información
que la búsqueda léxica omite, resolver vigencia/relaciones con fuentes, o navegar
dependencias correctamente. Ningún componente sustituye el origen local,
la aprobación, los estados de ausencia ni la comprensión humana de los documentos.

## Despliegue documentado y disponibilidad observada

La documentación del despliegue existente separa documentación revisable,
conocimiento generado aprobado e índices internos. Su política exige que los
repositorios sigan siendo operables sin Kwipu (`D-412ea76009f6`). El Source
Manager documenta copia controlada, fuentes habilitadas, contención de rutas,
vista montada en lectura y eliminación de residuos de fuentes deshabilitadas.
Son políticas documentadas; no inspeccionamos su configuración ni el corpus.

Kwipu y Graphiti tienen almacenamiento y ciclo de vida separados y comparten
Ollama. El despliegue documenta `gpt-oss:120b-cloud` como LLM y embeddings locales;
esto difiere del default primario de Kwipu. La copia/restore documentada exige
consistencia, manifiesto y validación; no ejecutamos restauración. Las pruebas
documentadas distinguen health de consulta citada y episodio procesado.
La evidencia identifica estas fuentes por IDs y hashes, sin publicar rutas privadas.

La comprobación del 2026-10-09 a las 13:39:21 UTC observó ocho contenedores en
ejecución, Graphiti/Ollama/FalkorDB/Open WebUI saludables, health HTTP 200 de
Kwipu y Graphiti e inventario de modelos de Ollama. El inventario incluía
modelos cloud y locales; no demuestra qué modelo ejecuta una recuperación.
No se verificaron ingestión, calidad, latencia, fuentes, navegación o restauración,
ni que las imágenes instaladas correspondan a las revisiones primarias fijadas.

Antes de un experimento se verificará compatibilidad y procedencia de la imagen,
fuentes sintéticas autorizadas, scope aislado, modelo efectivo y destino de datos.
La futura prueba no reconstruirá el índice general ni borrará grupos existentes.

## Qué aporta cada candidato y qué tenemos realmente

| Candidato | Uso humano documentado | Uso por agentes documentado | Integración propia observada |
|---|---|---|---|
| Kwipu | Terminal y navegador con grafo 3D, preguntas y apertura de fuentes | MCP y HTTP con respuesta y citas | `markdown-export` publica Markdown aprobado y verifica health/snapshot. No ofrece consulta enrutada. |
| Graphiti | Necesita herramientas de presentación alrededor del framework | Grafo temporal, episodios, hechos y búsqueda mediante MCP/API | Adaptador opt-in con publicación, verificación y lectura `read`; respaldo local por el router. |
| Graphify | Grafo HTML, informes y exportaciones para explorar un repositorio | Consultas estructurales, caminos y MCP sobre grafo persistido | `code-context.py` lee contexto AST citado de un artefacto existente. No ejecuta el extractor ni activa su MCP. |

La fila de Kwipu sigue el
[README fijado](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/README.md).
Graphiti distingue explícitamente su framework de las herramientas gestionadas
de Zep: no atribuimos al componente abierto el dashboard del producto comercial.
[Comparación oficial](https://github.com/getzep/graphiti/blob/1026ae7ae25e7e4cfcc1c7ebe00347b8a90f52a0/README.md).
Graphify documenta sus productos y consultas en su
[README fijado](https://github.com/Graphify-Labs/graphify/blob/5b74d7d74911cf435c8f1636b6f96ea202cc6246/README.md).
No evaluamos usabilidad abriendo sus interfaces en esta lectura.

Kwipu coincide con el contrato de bridge que espera nuestro adaptador:
`GET /health` y `GET /graph/snapshot`. Esto identifica el candidato oficial
confirmado por el usuario; no identifica la revisión instalada en un consumidor
ni acredita compatibilidad por ejecutar una petición.
[API oficial](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/bridge/app.py),
[adaptador propio](../../../../skills/knowledge-services/backends/markdown_export.py).

## Qué hay que comprobar para ofrecer memoria gobernada

Kwipu devuelve respuesta y citas con `node_id`, `file_name` y score opcional.
Eso no equivale a ID, versión, estado y evidencia del conocimiento aprobado.
Una futura lectura propia resolverá las citas al corpus canónico antes de servirlas
como conocimiento gobernado. Un score no demuestra autoridad ni respuesta correcta.
[Formato HTTP](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/bridge/query.py),
[formato MCP](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/kwipu_mcp_server.py).

El bridge Kwipu inicializa con `build_if_missing=False`. Su MCP inicializa el
motor con el default, que puede construir almacenamiento ausente. El flag del
bridge deshabilita ese build; no acredita cero efectos: el constructor crea
el directorio de conocimiento y la carga entra en lock/recuperación. Una futura
consulta verificará también los efectos del arranque. No hemos probado este
recorrido ni integrado recuperación Kwipu en el plugin.
[Inicialización del bridge](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/bridge/query.py),
[motor](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/geode_graph.py).

Graphiti ofrece filtros de vigencia de hechos y procedencia por UUID de episodio.
Son oportunidades para consultas históricas y relaciones que el índice local no
resuelva. Nuestro adaptador conserva procedencia y versiones, pero no envía esos
filtros temporales ni usa `get_episode_entities` en `consultar`. El intent llamado
`temporal` no entrega automáticamente todas las capacidades del servidor actual.
[Tools y filtros oficiales](https://github.com/getzep/graphiti/blob/1026ae7ae25e7e4cfcc1c7ebe00347b8a90f52a0/mcp_server/src/graphiti_mcp_server.py),
[adaptador propio](../../../../skills/knowledge-services/backends/graphiti.py).

Graphify clasifica relaciones extraídas, inferidas y ambiguas. El lector propio
acepta únicamente contexto AST citado y declara cobertura desconocida, vigencia
sin verificar y contexto no aprobado. Sus relaciones sirven para localizar
evidencia del código, sin convertirse en decisiones de proyecto aprobadas.
[Arquitectura oficial](https://github.com/Graphify-Labs/graphify/blob/5b74d7d74911cf435c8f1636b6f96ea202cc6246/ARCHITECTURE.md),
[lector propio](../../../../agent-kits/shared/code-context.py).

La integración Graphify futura verificará versión del esquema, commit de construcción
y dirección de arcos. El formato usa `directed: false` con dirección en el orden
de los enlaces; archivos anteriores pueden conservar marcadores `_src`/`_tgt`.
El lector propio no valida toda esa compatibilidad por aceptar nodos y citas.
[Carga de dirección](https://github.com/Graphify-Labs/graphify/blob/5b74d7d74911cf435c8f1636b6f96ea202cc6246/graphify/paths.py),
[exportación](https://github.com/Graphify-Labs/graphify/blob/5b74d7d74911cf435c8f1636b6f96ea202cc6246/graphify/export.py).

## Qué persiste y cuánto trabajo exige operarlo

| Componente | Persistencia y reconstrucción observadas | Costes que exige medir |
|---|---|---|
| Base local propia | Markdown canónico y caché SQLite reconstruible; journal separado. Consulta ordinaria con snapshot acotado y caché solo completa; `--view`/panel sin caché. | Calidad de recuperación, latencia, contexto entregado y UX humana todavía sin medir. |
| Kwipu | Índice derivado con generaciones, lock y revisión. Cambios o borrados provocan reconstrucción por lote en el código actual. | Extracción y respuestas con modelo, embeddings, CPU/GPU/RAM, almacenamiento, duración de rebuild y mantenimiento de watcher/bridge/UI. |
| Graphiti | Base de grafos, episodios y relaciones derivadas; publicación propia con manifiesto. `rebuild` propio vacía el grupo antes de republicar. | Base de datos, extracción/deducción, embeddings, cola, copias/restauración, llamadas y costes del proveedor real. |
| Graphify | Grafo JSON y productos exportables; escritura atómica y actualización desde fuentes. El artefacto puede quedar atrasado. | Extracción AST y almacenamiento; extracción semántica de documentos si se usa; compatibilidad, reconstrucción y vigencia. |

El código de Kwipu contiene publicación en staging y recuperación de backup;
la lectura de ese mecanismo no prueba durabilidad ante los fallos de nuestra máquina.
[Publicación](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/geode_graph.py),
[locks y escritura JSON](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/kwipu_storage.py).
Graphiti requiere operar una base y proveedores efectivos; sus requisitos no fijan
nuestro gasto. No trasladamos cifras promocionales de rendimiento a este proyecto.
[Requisitos oficiales](https://github.com/getzep/graphiti/blob/1026ae7ae25e7e4cfcc1c7ebe00347b8a90f52a0/README.md).

Kwipu puede operar localmente, pero su modelo por defecto es `gpt-oss:20b-cloud`.
Un endpoint Ollama local no prueba que la inferencia permanezca local. La selección
del modelo y del endpoint forma parte del experimento antes de indexar documentos.
[Configuración real](https://github.com/benmaster82/Kwipu/blob/01dd7d40fd5b071fc158aec4fcd69b85be4c0a22/kwipu_config.py).

Graphify permite extracción AST sin modelo. La extracción semántica de otros
contenidos tiene otro recorrido y puede usar un proveedor externo. Su README
contradice el default de logging entre la tabla de variables y Privacy.
En la revisión fijada, `_log_path()` solo habilita el registro por opt-in;
comprobamos el código y conservamos la contradicción documental como límite.
[Código de logging](https://github.com/Graphify-Labs/graphify/blob/5b74d7d74911cf435c8f1636b6f96ea202cc6246/graphify/querylog.py).
No instalaremos su skill o hooks para descubrir un artefacto existente.

## Qué mejora primero nuestro plugin

El [contrato local](memory-command-contract.md) identifica lectura íntegra del
corpus, caché implícita y estados degradados que el panel no debe pintar saludables.
El bloque 16 añade snapshot común acotado y consulta explícita CLI/panel.
También cierra los `resp.read()` sin tope de `markdown_export.health` y `verify`:
health/error 64 KiB, snapshot 2 MiB, JSON de 64 niveles y plazo monotónico
compartido entre DNS, conexión, redirecciones y respuesta. La IP privada queda
fijada por salto; Host/SNI y validación HTTPS se conservan. El resolver de sistema
preexistente puede seguir tras vencer la espera; no se afirma cancelación del kernel.
La salud del bridge no demuestra inferencia local ni calidad de recuperación.

El [router propio](../../../../agent-kits/shared/knowledge-find.py) conserva
autorización, procedencia, filtros y motivos del respaldo local. La
[sincronización](../../../../skills/knowledge-services/scripts/knowledge-sync.py)
conserva autoridad de publicación y routing. La integración mantendrá esos dueños,
con una salida común para comandos y dashboard; no invocará backends desde polling.

## Qué experimentos permiten elegir tres, dos, uno o ninguno

**Decisión de arquitectura propuesta, todavía sin benchmark:** mantener la base
local como control; probar Kwipu primero para conocimiento documental de humanos
y agentes; evaluar Graphify en tareas estructurales de código; exigir a Graphiti
valor adicional en relaciones e historial. La cantidad final queda abierta.

| Escenario compartido | Qué compara | Evidencia necesaria |
|---|---|---|
| Encontrar una decisión y abrir su fuente | Base local y recuperación documental candidata | Respuesta correcta, ID/version/estado, fuente vigente y navegación humana efectiva. |
| Reconstruir un cambio entre fechas | Base local, Kwipu y Graphiti | Distinguir vigente e histórico sin aplicar el obsoleto; todas las afirmaciones citadas. |
| Unir relaciones entre documentos | Candidatos documentales y temporales | Relaciones comprobables y omisiones; no contar inferencias sin fuente como aciertos. |
| Localizar dependencia e impacto en código | rg/lectura vigente y Graphify | Dirección, símbolos y citas correctas; tiempo de agente y persona. |
| Pregunta sin respuesta o de otro proyecto | Todos los caminos aplicables | Abstención o ausencia explícita; ningún dato ajeno o hecho inventado. |
| Revocar, actualizar y reconstruir | Cada proyección que se pruebe | No recuperar como vigente lo revocado; recuperación tras fallo y conservación de fuentes. |

Usaremos las mismas fuentes y preguntas para los caminos comparables. Las métricas
incluirán aciertos citados, errores obsoletos/ajenos, omisiones, latencia, contexto,
recursos y costes observados. Separaremos utilidad humana de agente y contratos
de eficacia. Los benchmarks publicados por un proveedor no sustituyen esta evaluación.

Un componente permanecerá si añade utilidad comprobada y un dueño claro, con costes
aceptables para el proyecto. Una combinación deberá mejorar frente a sus piezas
por separado, sin duplicar instrucciones ni multiplicar consultas automáticamente.
Graphify puede permanecer como contexto opcional aunque no sea backend de memoria.

Si un componente no aporta valor, retiraremos su adaptador y referencias activas
mediante plan de migración y verificación. Conservaremos memoria canónica y datos
del usuario; la retirada no borrará su servicio o almacenamiento externo. Si no
permanece ninguno, comandos y dashboard seguirán ofreciendo la memoria local.

La [preparación del benchmark](memory-benchmark-preparation.md) contrasta versiones
y aislamiento del despliegue. La revisión Graphiti instalada difiere de la documental;
se necesitan instancias/almacenes propios antes de probar ingesta y recuperación.

Esta entrega prepara evaluación y cierra consultas locales. No activa servicios,
mide costes, acredita UX ni decide mantener un backend por pruebas de esquema.
