# Caché de resultados y trabajos en segundo plano

Léela solo cuando diseñes una caché de resultados calculados (extracción,
conversión, respuestas de un servicio caro) o un worker que procesa trabajos
fuera de la petición. Los límites neutros —invalidar tras el commit, clave
caliente, cerrojo distribuido, límite de peticiones, cola al menos una vez— están
en la tabla «Caché, cerrojos y límites» de [contratos y datos](contracts-data.md)
y aquí no se repiten; esto es el método para construir sobre ellos.

## Clave de caché

La clave identifica **todo** lo que determina el resultado, y nada más:

| Componente | Por qué | Caso que descubre el defecto |
|---|---|---|
| Hash del contenido de entrada | El resultado depende de los bytes, no del nombre del fichero | Renombrar o mover el fichero da acierto; cambiar un byte da fallo |
| Versión del algoritmo y del esquema del resultado | Un cambio de código o de formato invalida lo anterior sin borrar a mano | Subir la versión del extractor no devuelve resultados del extractor viejo |
| Parámetros que cambian la salida | Idioma, calidad, opciones de conversión | Misma entrada con otra opción no recibe el resultado de la primera |
| Ámbito de privacidad (proyecto, tenant, usuario) | Un hash igual no autoriza a compartir un resultado entre identidades ni anonimiza el documento | El mismo fichero subido por dos tenants no comparte entrada si el contenido es privado |

El hash se calcula por bloques, sin cargar el fichero entero en memoria (en
Python, `hashlib.file_digest`, desde 3.11). Buscar por clave es barato, pero
calcularla exige leer la entrada completa: la caché no hace O(1) la operación.

## Mismo snapshot para hash y proceso

Si se hashea el fichero y luego se vuelve a leer para procesarlo, un cambio
entre ambas lecturas guarda el resultado de unos bytes bajo la clave de otros.
Lee una vez y procesa esa copia, o comprueba que el hash no cambió al terminar
y descarta el resultado si cambió.

El resultado reutilizable no lleva la ruta de origen: la ruta actual se adjunta
al devolverlo, para no atribuir un acierto al fichero antiguo.

## Escritura, lectura y retención

| Aspecto | Decisión | Caso que descubre el defecto |
|---|---|---|
| Escritura | Fichero temporal en el mismo directorio y renombrado atómico (`os.replace` en Python; atómico en POSIX si origen y destino están en el mismo sistema de ficheros) | Un proceso interrumpido a mitad no deja una entrada truncada que luego se lee como válida |
| Concurrencia | Dos productores de la misma clave escriben resultados equivalentes o uno espera al otro (ver «Expiración de una clave caliente») | Dos workers con el mismo fichero no corrompen la entrada |
| Lectura corrupta | JSON inválido o esquema desconocido = fallo de caché, registrado; se recalcula | Una entrada truncada no tumba la petición |
| Error de E/S o permisos | Se distingue de la entrada corrupta y se registra; no se oculta como fallo de caché | Un disco lleno o sin permisos aparece en el log, no como recálculo infinito |
| Error del proceso | Nunca se guarda; el error llega al llamante | Un fallo del extractor no queda cacheado como resultado vacío |
| Retención | Límite de tamaño o antigüedad, política de expulsión y permisos del directorio declarados | La caché no llena el disco; otro usuario del sistema no lee los resultados |
| Desactivación | Opción para saltarse la caché (depuración, reproceso forzado) | Con la caché desactivada se obtiene el mismo resultado |

## Frescura

Un acierto no oculta datos rancios: la caché devuelve la **edad** del valor
(momento en que se calculó) junto al valor, y el consumidor decide si le sirve.
La política ante una caída del origen se declara: servir el valor viejo
indicando su edad, o fallar. Una respuesta rápida con datos viejos es un fallo
de frescura, no de latencia, y se mide aparte.

## Trabajos en segundo plano

| Aspecto | Decisión | Caso que descubre el defecto |
|---|---|---|
| Durabilidad | El trabajo sale de la cola solo al confirmarse terminado; una cola en memoria del proceso no sobrevive a un reinicio | El worker cae a mitad y el trabajo se vuelve a procesar, no se pierde |
| Idempotencia | Procesar dos veces el mismo trabajo deja un único efecto | Reentrega tras caída entre procesar y confirmar |
| Reintentos | Clasificar errores (transitorio frente a determinista), timeout por intento, espera con jitter, tope de intentos y cancelación; ver «Política de reintentos» | Con tope 0 o 1, el contador se comporta como dice su nombre y no lanza un error indefinido; un 400 no se repite |
| Contrapresión | Cola acotada; al llenarse se rechaza o se ralentiza la entrada de forma visible | Un pico de trabajos no agota la memoria del worker |
| Cierre ordenado | Al parar, deja de aceptar trabajo y termina o devuelve a la cola lo que está en curso | Un despliegue no deja trabajos a medias marcados como hechos |
| Trabajos atascados | Plazo de reclamación para trabajos en curso de un worker caído | Un trabajo en `processing` no se queda así para siempre |
| Registro | Log estructurado con identificador del trabajo y correlación con la petición de origen; contenido redactado | Se sigue un trabajo desde la petición que lo creó sin copiar datos personales |

## Fuentes

Consultadas el 2026-10-14:
[Python — `hashlib.file_digest`](https://docs.python.org/3/library/hashlib.html#hashlib.file_digest),
[Python — `os.replace`](https://docs.python.org/3/library/os.html#os.replace).
