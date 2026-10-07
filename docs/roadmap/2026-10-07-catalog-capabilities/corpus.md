# Corpus de comparación

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
El inventario de [corpus.json](corpus.json) incluye todos los archivos tracked:
4.212 archivos, 57.707.707 bytes y 872.074 líneas de texto. Los binarios cuentan
en bytes; sus líneas son nulas. No se encontraron enlaces simbólicos.

Se comprobaron los 455 hashes de piezas principales frente al mapa privado y
al registro de fase 1: 293 skills, 68 agentes y 94 comandos. El resto incluye
recursos de esas piezas, scripts, adaptadores, reglas, documentación, tests,
integraciones, ejemplos, prototipos y soporte de instalación. Ninguna categoría
se excluye por no coincidir con el stack de este repositorio.

## Identidad y reproducibilidad

Las piezas principales conservan sus IDs S/A/C. Los archivos auxiliares usan
IDs opacos estables derivados de su ruta relativa. El mapa entre ID y archivo
original permanece en la investigación privada; el manifiesto público usa
nombres funcionales propios y hashes de contenido.

Cada archivo regular se leyó como bytes y se comprobó dentro del clon fijado,
sin ejecutar su contenido. El hash es SHA-256 sobre los bytes del checkout.
El digest agregado es SHA-256 de la lista ordenada de registros de identidad,
hash y tipo según el helper privado `build_catalog_corpus.py`. El resultado
completo se conserva en `catalog-corpus-full.json`, fuera de la distribución.
El checkout estaba limpio y su HEAD coincidía con la revisión fijada.

Digest de inventario:
`1170274c9a1a7b996d548692ae26bb3294ebecefa3ddd96a39cca00f3d08667d`.

Los 455 bundles estructurales vinculan cada pieza a archivos dentro de su
directorio. Esa pertenencia no acredita dependencias ni callers: la lectura
semántica debe añadir recursos externos al directorio y consumidores reales.
Las categorías y sus tamaños están completos en el manifiesto.

## Panel y recursos operativos

Se identificaron tres entradas declaradas en el manifiesto del origen:

| Función | ID de fuente | Bytes | Líneas |
|---|---|---|---|
| Panel de escritorio | R-8ab9d88e012a | 41.621 | 956 |
| Panel de navegador | R-7b761940e6db | 68.144 | 954 |
| Informe de preparación operativa | R-ec2c637e28f7 | 55.632 | 1.191 |

El manifiesto enlaza también 30 archivos cuya ruta identifica paneles o planos
de control: implementación, soporte, tests, guías, informes y prototipos.
Esta búsqueda no garantiza que todos sus imports tengan ese nombre. T-06 debe
seguir los imports y callers para cerrar la comparación funcional completa.
No se ha lanzado ninguna de estas aplicaciones ni sus scripts.

## Estado de la comparación

Inventariadas: 455 piezas principales y 4.212 archivos totales. Al cerrar T-01
había **cero** evaluadas semánticamente; `semantic_reviews_at_inventory` conserva
ese snapshot y no es un contador vivo. El avance de comparación e integración
se registra en [tasks.md](tasks.md). Las adaptaciones acotadas de la fase anterior
no se convierten en evaluación exhaustiva por coincidir sus hashes.

Las fichas siguen el [contrato de auditoría](audit-contract.md). El progreso
canónico permanece en [tasks.md](tasks.md), con T-03/T-04/T-05 por tipo de pieza
y T-06/T-07 para recursos operativos y memoria.
