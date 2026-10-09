# Fuentes sintéticas de los experimentos de memoria

Doce documentos propios, catorce preguntas y cuatro archivos Python. Ningún
archivo procede de un corpus del usuario. Las instrucciones adversarias de
D012 son datos de prueba: no instrucciones para quien lea esta documentación.

- [sources.json](sources.json): identidad, versión, cuerpo, fecha y SHA-256.
- [scopes.json](scopes.json): raíces Atlas/Boreal físicamente separadas.
- [questions.json](questions.json): preguntas, hechos/fuentes esperados y ausencias.
- [code-questions.json](code-questions.json): cuatro preguntas estructurales.
- [Artefacto AST real](code-control/graphify-out/graph.json): ocho nodos y diez arcos.

Los documentos mantienen sus bytes y hashes originales. Solo `sources.json`
cambia sus rutas para señalar las copias por ámbito; se omite el corpus combinado
duplicado de la preparación. La evidencia conserva hashes del manifiesto original
y del publicado. El historial sintético D003 sigue aprobado documentalmente,
pero su cuerpo lo declara sustituido: aprobación no significa vigencia actual.
El `.gitattributes` de esta carpeta desactiva la conversión de fin de línea
en sus fixtures para conservar esos bytes también con `core.autocrlf` en Windows.

Los documentos de ciclo de vida modificados no sustituyen el baseline publicado.
La actualización de D002 a 75 segundos usó una fecha futura sintética; D004 no
se actualizó, por lo que el ensayo no demuestra coherencia entre dependencias.

Para reproducir la búsqueda local, invocar el `knowledge-find.py` distribuido
con el plugin, dando `--root` a `atlas-control` o `boreal-control`,
`--view`, el texto exacto de la pregunta como argumento posicional y `--limit 10`.
El esquema y argumentos actuales se pueden consultar con `--help`.
No hace falta configurar un backend ni instalar modelos. Las mediciones históricas
excluyen arranque/import inicial y las lecturas `show` posteriores.

El contexto de código se reproduce con `code-context.py --project code-control
--graph graphify-out/graph.json --symbol accept --limit 50`. Los otros símbolos
ensayados fueron `append`, `deadline` y un símbolo ausente adicional.
La selección manual no convierte preguntas naturales en una API de caminos.
La salida declara cobertura desconocida, vigencia sin verificar y contexto no
aprobado. No se debe regenerar un artefacto ni instalar extractores implícitamente.

La ingesta documental necesita almacenes y servicios propios además de modelos
autorizados. Esta fixture no contiene credenciales, endpoints ni un ejecutor que
active inferencias. Los [resultados](../../../comparisons/memory-functional-results.md)
describen la configuración medida, los errores y lo que quedó sin ejecutar.
