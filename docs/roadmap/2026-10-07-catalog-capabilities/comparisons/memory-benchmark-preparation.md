# Preparación de la comparación de memoria

La [decisión de componentes](memory-component-decision.md) sigue abierta. Esta
preparación contrasta documentación y metadata del despliegue; no mide calidad,
coste, durabilidad ni experiencia humana. La evidencia pública resumida está en
[compatibilidad observada](memory-deployment-compatibility.json).

## Compatibilidad del despliegue

Kwipu declara `gpt-oss:120b-cloud` y `nomic-embed-text` en su respuesta de salud.
Es configuración declarada, sin llamada de inferencia. Su esquema HTTP de consulta
acepta `q`, sin selector de namespace. El experimento necesita instancia, fuentes
y almacenamiento propios; una pregunta que mencione otro proyecto no aísla datos.

La imagen Graphiti declara revisión `11538f6d45561bcce9a4400b374fb2dc533dccb6`,
distinta de la revisión documental `1026ae7ae25e7e4cfcc1c7ebe00347b8a90f52a0`.
La etiqueta no acredita que todo el contenido de la imagen coincida con ese commit.
La versión `1.29.1` pertenece al framework MCP, no a una versión acreditada de
Graphiti. Su proveedor/modelo efectivo queda desconocido.

El esquema instalado ofrece grupos en algunas herramientas, pero `delete_episode`
y `get_episode_entities` carecen de selector de grupo. En la fuente fijada,
las rutas de episodios, procedencia y limpieza usan el driver predeterminado
sin resolución física explícita por grupo en esos recorridos. Es una limitación
identificada mediante análisis estático, sin prueba sobre los datos del despliegue.
[Servidor de esa revisión](https://github.com/getzep/graphiti/blob/11538f6d45561bcce9a4400b374fb2dc533dccb6/mcp_server/src/graphiti_mcp_server.py),
[driver FalkorDB](https://github.com/getzep/graphiti/blob/11538f6d45561bcce9a4400b374fb2dc533dccb6/graphiti_core/driver/falkordb_driver.py).

El benchmark Graphiti necesita servidor y base propios. Se verificará el grupo
predeterminado y, por separado, la compatibilidad entre grupos. No se limpiará
el servicio compartido ni se asumirá aislamiento porque exista un parámetro.

Graphify requiere productor AST revisado y fijado, fuentes propias y artefacto
resultante. Un JSON inventado solo demuestra comportamiento del lector. La
extracción real y la vigencia de sus citas siguen sin medir.

## Experimento preparado

Se han preparado 12 documentos sintéticos, 14 preguntas documentales, cuatro
fuentes/preguntas de código, seis escenarios de ciclo de vida y una fixture
separada de IDs duplicados. Atlas y Boreal tienen corpus físicamente separados;
el control de ámbito se hace por raíz/almacén, antes de recuperar conocimiento.

La comparación separará búsqueda local, respuestas documentales, relaciones
temporales y contexto de código. No equiparará un resultado lexical con una
respuesta generada. Cada resultado requiere fuente esperada y estado/version
correctos; errores obsoletos, datos ajenos, omisiones y abstenciones se registran.

Latencia, contexto, llamadas, recursos, actualización/revocación, reconstrucción
y restauración se medirán con modelos y endpoints explícitos. La conectividad
de nuevas instancias a esos endpoints sigue sin verificar. No se copiarán
volúmenes, corpus o configuración del despliegue existente.

La preparación ha realizado cero consultas de memoria, ingestas, inferencias
y cambios Docker. No decide conservar tres, dos, uno o ningún componente.
La consulta local acotada sirve de control; la decisión final exige resultados
y evaluación humana además de contratos técnicos.

## Ejecución posterior separada

Esta preparación conserva sus límites históricos. El bloque17 ejecutó después
los [experimentos funcionales](memory-functional-results.md), con resultados,
errores preservados, modelos efectivos, contadores y fuentes sintéticas públicas.
No se atribuyen sus consultas/ingestas a las comprobaciones metadata anteriores.
La decisión de prioridad y la implementación restante se describen en ese informe.
