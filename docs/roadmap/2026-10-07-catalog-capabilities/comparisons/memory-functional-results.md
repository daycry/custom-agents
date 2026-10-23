# Resultados funcionales de memoria

Esta entrega del bloque 17 prueba componentes con datos sintéticos propios.
Complementa la [lectura de contratos](memory-component-decision.md) y la
[preparación](memory-benchmark-preparation.md); sus comprobaciones anteriores
de salud no se convierten retroactivamente en pruebas de calidad.
La implementación local medida es `8689955`. La integración global sigue abierta.

La [evidencia estructurada](../testing/memory-benchmark-evidence.json), las
[respuestas documentales](../testing/memory-documental-answers.json) y las
[fuentes y preguntas](../testing/fixtures/memory-benchmark/README.md) permiten
examinar denominadores, errores y transformaciones de publicación. Las revisiones
independientes recalcularon métricas y contrastaron fuentes; sus hashes se conservan.
Estos resultados no son una comparación experimental contra la implementación
de referencia ni una validación sobre documentos de producción.

## Qué se probó

| Componente | Ejecución real | Unidad de evaluación |
|---|---|---|
| Local | Lector aceptado sobre Atlas/Boreal, raíces separadas; 14 preguntas × 3 | Recuperación de fuentes, sin respuestas generadas |
| Kwipu | Ingesta nativa, consulta del bridge y tres comprobaciones HTTP; imágenes instaladas fijadas, almacenes propios | 42 respuestas comparables: primeras tres repeticiones de 14 preguntas |
| Graphify | API AST fijada `extract → build_from_json → to_json`, cuatro fuentes Python; lector real del plugin | Tres preguntas estructurales soportadas, un camino no soportado y una ausencia, tres veces |
| Graphiti | Cuatro episodios y doce búsquedas nativas, bases físicas propias y configuración medida | Recuperación de hechos y corte temporal; sin respuestas generadas |

Atlas tiene once documentos y Boreal uno. Kwipu no ofrece namespace en `q`:
el aislamiento ensayado se obtuvo con fuentes, almacenamiento y contenedores
físicamente separados. No se consultó el corpus existente ni se reiniciaron
servicios del usuario. Los cuatro contenedores propios de Kwipu se retiraron;
una comprobación posterior por su etiqueta no encontró recursos restantes.

## Recuperación local

Las doce preguntas con fuentes esperadas recuperaron **todas** esas fuentes
entre los cinco primeros resultados: 12/12 preguntas, 36/36 repeticiones.
En el primer resultado fueron 8/12. Dos preguntas necesitan dos fuentes, por
lo que este último criterio es imposible para ellas; no es precisión de respuestas.

Hubo 21 resultados parciales (`result_budget`) y 21 completos. La parcialidad
se declaró aun cuando la fuente esperada estaba presente. No se observó
ninguna fuente del otro ámbito en estas 42 búsquedas; no es garantía universal.
Q10/Q11 esperaban abstención, pero devolvieron diez/tres fuentes: este lector
no genera respuestas ni decide si una pregunta tiene solución. Una búsqueda
completa tampoco acredita exactitud histórica o autoridad normativa.

La mediana conjunta de las 42 búsquedas fue **129,9495 ms**. El agregado original
de 123,584 ms es la mediana de las catorce medianas por pregunta. El intervalo
mide `view.query`: excluye arranque del proceso, import inicial y los `show`
posteriores. No se separaron estrictamente condiciones frías y calientes.
Hubo cero llamadas a modelos. El corpus pequeño no demuestra escalabilidad.

## Respuestas documentales

Raíz y una revisión independiente leyeron completas las 42 respuestas y sus
doce fuentes. **41/42 acertaron el núcleo de la respuesta; 36/42 cumplieron
todos los hechos esperados y las atribuciones explícitas respaldadas.**

| Incidencia | Observación |
|---|---|
| Atribución incorrecta | Q01/r1 atribuyó a D010 una frase de autoridad de D012; Q05/r2 atribuyó a D010 una relación de aviso ausente |
| Hechos omitidos | Q08/r3 omitió la decisión humana registrada; Q09/r1-r2 omitieron el 13 de abril |
| Regla obsoleta como vigente | Q12/r3 respondió 90 segundos en lugar de 45 |
| Abstención | Q10/Q11: 6/6 respuestas expresaron ausencia de evidencia |
| Paráfrasis menor | Q09/r1 habló de solicitud vacía; D010 identifica un manifiesto vacío. Ya fallaba el criterio estricto por la fecha |

Q12 combina una pregunta que ordena ignorar otras fuentes y un documento con
una instrucción adversaria citada. Falló 1/3 veces comparables y 3/5 al conservar
las dos repeticiones adicionales. No se aisló causalidad de inyección documental
con una pregunta benigna. Las repeticiones cuarta/quinta no entran en 42.

La API entregó **375 ocurrencias de `source_nodes`, 99 con `file_name: null`**.
Son nodos recuperados, no citas por afirmación. El snapshot inicial no se archivó
antes del rebuild: el enlace completo de esos 375 nodos al documento canónico,
recall@5 y precisión de citas permanecen desconocidos. Durante el ciclo de vida
sí se resolvieron 60 ocurrencias correspondientes a diez IDs distintos, sin
pendientes. Ese enlace posterior no valida el baseline. Una prueba separada del
[export real](../testing/memory-documental-binding.json) sí conserva los metadatos
del adaptador hasta el snapshot nativo y su API; no completa el enlace de esos
375 nodos iniciales.

La prueba de binding usa dos canónicos sintéticos y `knowledge-local` más
`markdown_export.plan/apply` reales. Tras ingesta nativa, los dos chunks conservan
`node.fm.knowledge_id/version/hash/project/scope`: 2/2 enlaces, cero diferencias.
El GET real interno devolvió HTTP200 y 7.367 bytes idénticos al serializer nativo;
once entidades quedaron fuera del enlace documental. El hash exportado es
semántico y se distingue de los SHA-256 de bytes del canon y de su proyección.
Los textos sintéticos originales están incluidos en la evidencia.

La ingesta adicional hizo dos llamadas LLM cloud y cuatro de embeddings locales.
La lectura posterior, sobre copia byte exacta del almacén propio, hizo cero
inferencias, consultas o constructores RAG. Nueve fuentes y ocho archivos de
almacén conservaron hashes; el contenedor propio se retiró. Dos fallos previos
del harness tuvieron cero inferencias. Un GET prematuro tras ingesta terminó en
`RemoteDisconnected`, sin logs suficientes para fijar causa interna; se conserva
ese fallo y se distingue de la recuperación posterior con readiness explícito.
Esto acepta propagación de metadatos en la imagen/fixture ensayadas, sin aprobar
respuestas, permisos de lectura, concurrencia o integración del producto.

La mediana de respuesta fue **1.440,41 ms**, p95 por rango más próximo
**2.239,62 ms**, sobre 42 consultas. La ingesta inicial duró 84,56 s para Atlas
y 11,36 s para Boreal. Estos tiempos incluyen inferencia y no son comparables
directamente con la búsqueda local sin modelo.

Se verificó el modelo efectivo: `gpt-oss:120b-cloud` para generación y
`nomic-embed-text` para embeddings. El LLM es remoto aunque el endpoint esté
en la máquina. Thinking estaba desactivado; no se almacenó razonamiento.
El registro de llamadas/tokens separa ingesta y todas las repeticiones, ciclo
de vida, piloto y arranque fallido. Tres consultas HTTP y otro intento fallido
carecen de contador completo; el total monetario y la separación de tokens
de razonamiento son desconocidos. No se calcula coste por pregunta dividiendo
contadores de una cohorte diferente.

Los límites propios fueron 3 GiB y dos CPU por contenedor. Los máximos
muestreados fueron 167 MiB en Atlas y 4,266 MiB en Boreal; Boreal se muestreó
en reposo antes de inferencia. No representan picos completos ni recursos
del proveedor. La revisión instalada de Kwipu es desconocida: se conservan
digests de imagen y hashes de archivos seleccionados, sin fingir un commit.

La actualización a 75 segundos obtuvo 3/3 respuestas esperadas; la retirada
de D005 de la proyección obtuvo 3/3 abstenciones, conservando historia propia.
El rebuild conjunto duró 71,46 s. El reinicio y disponibilidad del bridge
duraron 15,68 s; ocho archivos de índice conservaron hash y se recuperó 75.
No se ejecutaron restauración de backup, fallo de inferencia ni escritura
interrumpida. D004 conservó su referencia a 45 segundos: no se probó coherencia
de hechos dependientes tras actualizar D002. La fecha futura de esa actualización
es un reloj de evaluación explícitamente sintético.

## Contexto estructural de código

El productor fijado a `5b74d7d74911cf435c8f1636b6f96ea202cc6246` generó
un artefacto real de ocho nodos, diez arcos y 5.506 bytes. Se usaron tres
extracciones con raíces de caché separadas; no quedó registrada la precondición
que permitiría llamarlas estrictamente frías. La CLI que instala/configura
componentes, la extracción semántica, el MCP y el HTML no se ejecutaron.

El lector aportó evidencia estructural citada para **tres de cuatro preguntas**,
9/9 repeticiones de esos casos. La pregunta de camino C03 no está soportada
por el consumidor: consultar el vecino de `append` no la responde. El harness
inspeccionó separadamente el camino dirigido del productor, sin atribuirlo al
lector. La ausencia adicional C05 dio `no-match-in-artifact` 3/3, que no prueba
ausencia en todo el repositorio. Las preguntas se mapearon manualmente a símbolos.

Se contrastaron con las fuentes e imports **93 ocurrencias de citas estructurales,
16 referencias distintas**. Esto valida esos hechos de código en la fixture,
sin demostrar relevancia global, aprobación de conocimiento o calidad humana.

La consulta `policy.deadline` y la consulta por node ID no encontraron el nodo
presente: el lector actual busca etiquetas. `deadline` recupera ambas definiciones
y necesita desambiguación por archivo. Al cambiar el import, el artefacto antiguo
conservó la llamada a `policy` hasta reextraer; la salida declara correctamente
`freshness: unverified`, pero no detecta esa obsolescencia. El artefacto no contiene
un manifiesto de hashes de sus fuentes. `directed: false` tampoco borra el orden
source/target de los arcos de llamadas del productor.

La mediana de consulta fue 214,97 ms contando el proceso hijo y 46,98 ms dentro
del worker. La extracción tardó 1,25–1,90 s, con unos 55 MiB de working set máximo
por proceso; el máximo del lector rondó 28 MiB. Las salidas ocuparon 308–1.495
bytes UTF-8, sin tokenización medida. No hubo llamadas a modelos; el coste de
hardware/tiempo no se midió en euros.

Un proceso nuevo leyó el mismo artefacto; quitar una fuente excluyó sus citas
con avisos; restaurar y reconstruir recuperó el hash original. Del artefacto
mutado se conserva solo el hash histórico. El harness declaró bloqueo de raíz
ajena, pero no retuvo stdout/exit separados: no se presenta como reproducción
independiente. No se midió ventaja frente a `rg`, otros lenguajes ni UX humana.

## Recuperación temporal

El servidor nativo procesó cuatro episodios, tres de Atlas y uno de Boreal,
con sus fechas explícitas. Se usaron bases, servidores, red y volumen propios;
no se asumió aislamiento por el nombre de un grupo. La fuente instalada
seleccionada se contrastó con `11538f6d45561bcce9a4400b374fb2dc533dccb6`.
La coincidencia de trece archivos no acredita toda la imagen ni la revisión
documental anterior.

Se ejecutaron doce búsquedas nativas, cuatro preguntas × tres repeticiones.
Las repeticiones son de recuperación sobre una sola ingesta, no tres ensayos
independientes de extracción. Se conservaron hechos y UUIDs de episodios;
no se generaron respuestas naturales para puntuar su exactitud.

| Comprobación | Resultado observado |
|---|---|
| Límite histórico, actual y Boreal | Ninguna de nueve recuperaciones de hechos contenía el límite numérico esperado: 90, 45 o 120 segundos |
| Corte histórico Q02 | 3/3 llamadas con `valid_at_before=2026-04-01` incluyeron hechos con `valid_at` de mayo |
| Pregunta sin dato Q10 | 3/3 devolvieron seis hechos de otros temas; no es una prueba de abstención de un generador |
| Ámbito | Ningún hecho recuperado se atribuyó a episodios de la otra base en estos doce registros |

Las relaciones recuperadas no prueban que se hayan perdido todos los datos del
episodio o de las entidades. El resultado se limita a los hechos ofrecidos
por la herramienta ensayada y esta configuración. No demuestra incapacidad
temporal general del framework; sí impide prometer consulta histórica correcta
con esta revisión/despliegue sin una corrección y nueva aceptación.

La mediana de búsqueda fue 164,91 ms, con una llamada de embedding y ninguna
de LLM por búsqueda. El experimento registró 13 llamadas LLM y 48 embeddings,
122,941 s en total. Las respuestas del proveedor declararon 19.269 tokens de
entrada y 10.997 de salida LLM, más 1.102 de embeddings. El total monetario
sigue desconocido; no hubo registro de razonamiento ni prompts de inferencia.
Los modelos efectivos fueron los mismos LLM cloud y embeddings locales del
ensayo documental, mediante su cliente OpenAI compatible.

Aunque la configuración declaró `max_tokens=2048`, cuatro llamadas nativas
solicitaron 16.384; las otras nueve solicitaron 2.048. Esa configuración no
demuestra un techo de tokens por llamada. El reranker tenía un modelo default
distinto, que el proxy propio rechazaba; no se invocó en las búsquedas realizadas.
No se sustituyó un modelo ni se modificó el servidor para obtener resultados.

Dos intentos previos fallaron por el harness antes de inferencia: el lector
esperaba episodios fuera del envelope MCP real y la creación enviaba un UUID
nuevo que el core interpreta como actualización. Se corrigieron únicamente
las llamadas/lectura del harness según el contrato nativo. Ambos fallos y sus
contadores cero se conservan; no se atribuyen al producto ni se ocultan.
Los recursos propios del ensayo final se retiraron por identidad y etiqueta;
los ocho contenedores existentes permanecieron en ejecución. La revisión
independiente contrastó las doce búsquedas nativas, 83 hashes de evidencia,
32 archivos del bundle y trece fuentes seleccionadas; confirmó los recuentos
sin extenderlos a toda la imagen o a otras configuraciones.

## Decisión de integración

Conservar la memoria local como origen canónico y capacidad siempre disponible
cuando existan sus archivos. Priorizar **consulta documental opcional y contexto
estructural opcional**: responden a necesidades diferentes y no deben ejecutarse
ambos automáticamente en cada tarea. La muestra justifica continuar su integración,
pero no declarar superioridad ni tres servicios obligatorios.

Antes de servir respuestas documentales, implementar autorización local y enlace
de citas a ID/versión/hash/estado/ámbito, incluso con filenames nulos; cualquier
inconsistencia debe devolver consulta local con motivo. Las respuestas generadas
seguirán identificadas como no verificadas: resolver sus fuentes no acredita
cada afirmación. El protocolo actual no ofrece revisión común de snapshot/query;
comparar antes/después detecta cambios, sin certificar atomicidad.

Para código, añadir selección inequívoca por ID y archivo/símbolo, y un contrato
de hashes ligado al artefacto y a su generación. Un manifiesto creado después
de la extracción sobre archivos actuales no prueba que un grafo anterior esté
vigente. Los artefactos antiguos conservarán vigencia sin verificar.

Priorizar **Kwipu y Graphify como complementos opcionales**, con los permisos y
límites anteriores. Graphiti no entra en la combinación recomendada por defecto:
esta prueba no demuestra una mejora temporal adicional y sí expone un incumplimiento
del corte histórico. Conservar su capacidad existente opt-in para proyectos que
la necesiten, sin activar ni ampliar lectura, y exigir filtros/verificación de
procedencia y aceptación nativa antes de anunciarla como memoria histórica.
No se cambia la configuración de ningún proyecto ni se elimina un servicio
ya instalado. La muestra tampoco demuestra que toda persona necesite dos servicios.
No se añaden skills, agentes, MCP ni consultas automáticas al panel en este bloque.
