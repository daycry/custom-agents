# T-02: prefiltro y medición aceptados; revisión completada

Estado: **completado el 2026-10-29** tras revisión A/B/C/D sin gaps; [traza del intento 3](t02-review-attempt-3-2026-10-29.json). Cero Python en identidades no protegidas está verificado. CA-01, ajustado con aprobación del usuario el 2026-10-29, exige esa garantía y la comparación versionada transparente, sin mínimo porcentual en F1. El 80 % no se ha alcanzado y queda como objetivo de investigación posterior.

## Control intercalado válido del 2026-10-29

Diez muestras + calentamiento por variante y runtime, orden rotado, sin otras suites propias
simultáneas y sin fallos. Ambas variantes usan los mismos supervisor, mapa y fixtures.

| Runtime | Antes ms | Después ms | Reducción % | Node vacío ms |
|---|---:|---:|---:|---:|
| Claude | 933,702 | 576,892 | 38,21 | 534,270 |
| Codex | 854,110 | 540,547 | 36,71 | 530,265 |
| OpenCode | 893,032 | 554,176 | 37,94 | 513,177 |

[Recibo y fuentes](t02-paired-control-2026-10-29.json). Se mide el launcher compartido,
no la entrega nativa. Node vacío es un control observado, no un mínimo universal.
El [ajuste aprobado](f1-performance-adjustment-proposal.md) elimina el mínimo porcentual de F1.
El recibo incluye las muestras y su dispersión; se conservan todos los fallos históricos.
Esta decisión no acredita la estabilidad general de T-01. La revisión de T-02 se cierra con el intento 3; T-07 conserva la revisión y QA de la fase completa.

## Dispersión del control válido

Rango de las diez muestras medidas por variante; no es un umbral de estabilidad general de T-01.

| Runtime | Variante | Mínimo ms | Máximo ms | (máx/mín - 1) % |
|---|---|---:|---:|---:|
| claude | before | 789.984 | 1662.071 | 110.39 |
| claude | after | 503.971 | 888.418 | 76.28 |
| claude | empty_node | 456.298 | 670.969 | 47.05 |
| codex | before | 769.818 | 924.020 | 20.03 |
| codex | after | 495.997 | 575.794 | 16.09 |
| codex | empty_node | 460.787 | 587.726 | 27.55 |
| opencode | before | 785.305 | 1051.954 | 33.95 |
| opencode | after | 479.705 | 728.752 | 51.92 |
| opencode | empty_node | 446.300 | 564.590 | 26.50 |

## Histórico: comparación con la línea base de T-01

Tres pasadas de diez muestras por runtime, con un calentamiento descartado; misma fixture y launcher compartido. Se compara la mediana de las tres medianas. La carga del entorno varía; estos valores separados en el tiempo no prueban una regresión causal del código.

| Runtime | Base central ms | Prefiltro central ms | Reducción observada % | Objetivo 80 % |
|---|---:|---:|---:|---|
| claude | 897.494 | 960.182 | -6.98 | pendiente |
| codex | 865.589 | 1271.990 | -46.95 | pendiente |
| opencode | 1022.659 | 1164.369 | -13.86 | pendiente |

## Control intercalado de arranque

Diez muestras por variante más calentamiento, intercalando launcher anterior, prefiltro y Node vacío. Ambas copias del launcher usan los mismos recursos canónicos y proyectos temporales.

El prefiltro tiene mediana 1266.088 ms y Node vacío 1207.970 ms. Son costes observados en este control, no un mínimo físico universal.
El launcher anterior produjo un aviso de limpieza en una muestra. El control se conserva como FALLO y no certifica una ganancia porcentual. Su proporción descriptiva original se guarda aparte, sin usarla como puerta de rendimiento.

La prueba adicional con el launcher real del repositorio y un ejecutable Python inexistente terminó con exit 0, stdout y stderr vacíos: el caso principal del repositorio también evita Python.

## Comportamiento y límites

- Identidades exactas y roles protegidos conservan el evaluador y sus denegaciones.
- Mapas ausentes o inválidos, UTF-8/JSON dudoso y entradas sobredimensionadas conservan los diagnósticos de Python.
- La lectura incompleta tiene un plazo compartido con reloj monotónico; la entrada no puede mantener indefinidamente el launcher vivo.
- OpenCode relee el mapa y deja llegar al evaluador los errores anteriores y posteriores a setup.
- Esta prueba invoca el launcher por selector; no acredita la entrega nativa de eventos de los clientes. OpenCode ya tenía un prefiltro en su proceso persistente; su mejora aquí es la gestión del mapa y la consistencia de validación.

Evidencia: [comparación](t02-native-prefilter-comparison.json), [control intercalado](t02-native-prefilter-paired-control.json), [procedencia](t02-native-prefilter-provenance.json).
