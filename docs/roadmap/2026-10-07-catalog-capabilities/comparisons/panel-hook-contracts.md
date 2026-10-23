# Panel: contratos declarados de hooks por runtime

Bloque 6 sobre la revisión fijada `ef648e01899ba3e8dc6371642deaaf64b4477775`.
La [evidencia de lectura](panel-hook-reading-evidence.json) conserva hashes,
rangos y límites. Las tres entradas de dashboard se releyeron parcialmente;
siete recursos pertinentes se releyeron completos. Se conservan las lecturas
históricas completas, sin convertir esta revisión dirigida en cierre de todas
las dependencias, almacenes u observaciones. No se ejecutó código del corpus.

## Comparación y decisión

Las vistas comparadas separan resumen, procedencia, avisos, observaciones y
operaciones; tienen defensas de navegación y accesibilidad. Parte de sus
indicadores depende de servicios y estado persistido fuera del catálogo.
La propuesta propia conserva navegación verificable, fuentes y estados
desconocidos sin introducir servidor, base de tareas, score o conexión externa.

La inspección del panel propio encontró cinco gaps: todos los runtimes leían
el registro Claude; el launcher actualizado no identificaba la guardia ni los
comandos Codex; el pie describía una ubicación de guardias antigua; móvil
ocultaba Fuentes; timeout y agrupación no distinguían contratos por runtime.
La prueba propia de lectura obtuvo ocho handlers y SessionEnd de 5 s en los
tres entornos, aunque el registro Codex declara 3 s. Esto es diagnóstico del
panel previo, no observación de ejecución de esos hooks.

La integración reutiliza `plugin-panel`, los registros nativos, el mapa de
roles y el adapter existente. Claude y Codex tienen fuentes independientes.
OpenCode incorpora datos JSON estrictos entre marcadores del adapter propio:
los datos gobiernan registros, handlers, filtros de escritura, eventos y
presupuestos; el panel los lee como datos sin importar JavaScript inspeccionado.
Las transformaciones de payload permanecen en callbacks propios probados.
Se rechaza una tabla independiente que solo documente constantes duplicadas.

Cada handler conserva ID, runtime, canal nativo, fuente y localizador,
activación, función pública, comportamiento y procedencia del presupuesto.
La guardia muestra los IDs del mapa central y sus límites. La agrupación es
runtime más evento: handlers y grupos tienen contadores explícitos. Ausencia,
fuente inválida y presupuesto no declarado son estados distintos; ninguna
fuente fallida se sustituye por Claude. Carga y ejecución siguen sin verificar.

El stream de idle/ejecución OpenCode no se presenta como hook de teardown
nativo ni hereda el límite de 3 s de Codex. El presupuesto supervisado del
adapter y el timeout del registro tampoco prueban finalización o captura durable.
El panel no ejecuta doctor automáticamente: algunas comprobaciones consultan
runtimes y backends opcionales. Una futura proyección deberá ser opt-in y
conservar fuente, scope, vigencia, límites y remedio del informe canónico.

## Validación y alcance

RED/GREEN de inventario por runtime, presupuestos inválidos, fuentes ausentes,
metadata, guardias y contrato consumido por el adapter. QA de navegador para
filtros, enlaces, historial, teclado, seis etapas y Fuentes móvil; delta nativa
OpenCode para el adapter modificado, exports y revisión independiente.
El ledger registra resultados y límites; no se afirma eficacia por declaración.
Bloque aceptado en revisión y [QA final](../panel-command-qa-evidence.json);
[delta nativo](../panel-native-delta-evidence.json) con sus límites. T-06/T-13 globales
abiertas; sin nuevas skills, backend activado ni cambio del parser de guardias.
