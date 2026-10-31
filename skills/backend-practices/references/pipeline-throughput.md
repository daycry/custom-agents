# Rendimiento de pipelines de datos

Léela solo cuando el cambio acelere o reestructure una ingestión, exportación,
ETL o backfill. No aplica a endpoints ni a pantallas. La reanudación y la
idempotencia del backfill están en [contratos y datos](contracts-data.md); la
comparación reproducible de variantes (corpus, condiciones, repeticiones,
métricas ausentes) es de la skill opcional `outcome-evals` (su protocolo, si está instalada). Esto
añade lo propio de mover datos: dónde se va el tiempo y cómo demostrar que la
variante rápida conserva los datos.

## Antes de optimizar: objetivo y etapas

1. Declara el **backlog** (qué volumen histórico falta) y el **destino** (qué
   retraso aceptable tiene el dato servido). Son metas distintas: vaciar el
   histórico y no quedarse atrás con lo que llega mientras corre el job.
2. Mide cada etapa por separado: extracción, red, carga, transformación y
   frescura del dato servido. Mide también cuánto crece la cola de entrada
   mientras el job corre.
3. Optimiza la etapa medida como dominante. Una lista fija de optimizaciones
   aplicada antes de medir no localiza el cuello de botella.

| Variante | Cuándo considerarla | Qué vigilar |
|---|---|---|
| Lotes más grandes | El coste por llamada domina | Memoria, tamaño de transacción y bloqueos en el destino |
| Más workers | Una etapa espera E/S | Contención en el destino, límites del proveedor, orden entre particiones |
| Agrupar ficheros pequeños | La apertura por fichero domina | Que un fichero fallido no invalide el grupo entero sin registrarlo |
| Transformar en SQL cerca del dato | La red domina | Que la lógica siga probada y versionada |
| Staging y swap | La carga bloquea a los lectores | Coherencia entre la tabla de staging y el manifiesto |
| Particionar | El volumen impide reintentar | Particiones tardías y reintento por partición |

## Contabilidad de datos

El mismo número de filas y el mismo timestamp máximo **no** prueban que el
resultado es correcto: una pérdida y un duplicado se compensan, y una
actualización errónea conserva ambos contadores. Un filtro o agregado legítimo
tampoco conserva la cardinalidad. Por dominio, define antes de comparar:

| Elemento | Qué fija |
|---|---|
| Identidad | Clave natural o de origen que identifica cada registro de punta a punta |
| Transformación | Qué entrada produce qué salida, incluidos filtros y agregados legítimos |
| Recuento por resultado | Aceptados, rechazados (con motivo) y fallidos (con error); `entrada = aceptados + rechazados + fallidos` |
| Invariantes | Sumas de control, totales por grupo, unicidad de la identidad en el destino |
| Reconciliación | Comparación por identidad entre origen y destino, no solo totales |
| Replay | Reprocesar una partición produce el mismo destino (idempotencia demostrada, no supuesta) |

## Manifiestos y checkpoints

- Un manifiesto lleva identidad del lote, versiones (código, esquema, origen) y
  qué particiones cubre.
- Se escribe **después** del commit de los datos que describe, o en la misma
  transacción. Tener un fichero con nombre de manifiesto no da atomicidad: si
  el manifiesto se publica antes que los datos, un lector ve un lote incompleto.
- El checkpoint de progreso avanza solo tras el commit del lote; un checkpoint
  adelantado salta datos al reanudar.

## Comparar variantes

- Fija un snapshot o una marca de agua alta por partición; trata llegadas
  tardías y zona horaria de forma explícita.
- Registra el instante de lectura del resultado y separa la ventana histórica
  del extremo vivo que sigue creciendo.
- Una muestra rápida no acredita el job completo con otra carga, caché o
  concurrencia: la variante se vuelve a medir en el job real.
- Al promover una variante, conserva en el informe fallos por fichero, coste,
  recursos y calidad, no solo el tiempo. No se borran datos en bruto para
  mejorar las cifras.

## Casos que descubren el defecto

| Caso | Qué debe ocurrir |
|---|---|
| Una fila perdida y otra duplicada | La reconciliación por identidad detecta ambas aunque el total cuadre |
| Actualización de un valor sin cambiar el timestamp máximo | La comparación por invariantes la detecta |
| Rechazo legítimo por filtro | Cuenta como rechazado con motivo, no como pérdida |
| Llegada tardía a una partición ya procesada | Se reprocesa o se registra; no queda fuera en silencio |
| Caída tras el commit y antes del checkpoint | Al reanudar, el lote se reprocesa sin duplicar efectos |
| Fallo parcial de un lote | Los fallidos quedan registrados y reintentables; los aceptados no se repiten |
| Dos variantes medidas en ventanas distintas | La comparación se invalida hasta medir sobre el mismo snapshot |
| Variante más rápida con más coste o más fallos | El informe lo muestra; la velocidad sola no la promueve |

Para el informe, el agregador de la skill opcional `outcome-evals`, si está instalada, agrega
ejecuciones ya hechas con sus mediciones; las métricas de dominio (aceptados,
rechazados, invariantes) las calcula el job del proyecto y se adjuntan como
evidencia. Ejecutar el backfill en un entorno real requiere autorización del
proyecto.

Sin el módulo opcional de evaluación, conserva un informe local de los mismos casos, condiciones, repeticiones y métricas observadas; no inventes resultados ni prometas un informe agregado automático.
