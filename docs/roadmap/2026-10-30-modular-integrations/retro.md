# Retrospectiva — núcleo modular e integraciones de proyecto

## Resultado y alcance

El core conserva el ciclo local y sus dueños. Las 33 skills se distribuyen en 17 core
y 16 opcionales; los proyectos pueden elegir proveedores y extensiones sin incorporarlos
al catálogo global. Las 37 propuestas conservan decisión, motivo, dueño y fuentes como
candidatas; no se implementan para aumentar el número. Las seis skills previas se
mantienen en módulos opcionales. No se publican versiones ni se reabren fases canceladas.

El manual ES/EN desarrolla 18 workflows y personalización de roles, personas, agentes,
skills, tools y MCP. La edición española PDF tiene 39 páginas, con ejemplos completos,
índice navegable y revisión visual. Un ejemplo no equivale a una conexión validada.

## Qué cambió gracias a la revisión

Tres intentos independientes A/B/C/D detectaron cinco Important iniciales y un
Important nuevo de recuperación. Preflight por sí solo no protegía la edición
concurrente; revalidar sin conservar los hashes propios previos tampoco permitía
recuperar un upgrade interrumpido. Las dos obligaciones se comprueban por separado.
Checkpoints por archivo multiplicaban las escrituras; agruparlos reduce ese coste
sin perder estados recuperables. Se conserva el aprendizaje de LES-016: todo estado
intermedio debe tener dueño y una recuperación verificable.

La lente A final vio un Important de evidencia A04 y un Minor A05 antes del último
delta documental. Se conserva ese resultado, junto con la regresión dedicada y
la corrección literal comprobadas por ROOT; no se inventa otra revisión independiente.

## Medición y mejoras del proceso

Tokens, coste y esfuerzo IA son null: el meter no dispone de una transcripción compatible
con cobertura completa para esta ejecución. No se calcula una desviación sin presupuesto
comparable ni se transforma reloj, esperas o duración de tests en horas IA. La fila de
CALIBRATION no añade una muestra numérica ni altera el ratio vigente.

El harness privado necesita archivar desde los blobs Git para conservar pares de
archivos byte idénticos; no debe normalizar solo una mitad según su extensión.
Los contenedores que prueban supervisión necesitan init para recoger descendientes.
Un timeout del padre no demuestra la salida de todo su árbol; el barrido adicional
Windows lo mostró y se terminó el descendiente propio verificado. Debe registrarse
la identidad de procesos al arrancar futuros harnesses y comprobar su terminación.

Los resúmenes públicos también son contrato: los cuatro README recibieron la regresión
A03 para que un PDF opcional no reaparezca como requisito. La procedencia del PDF usa
UTF-8/LF y hashes de los once blobs publicados; no el CRLF accidental de un checkout.

## Adopción posterior

Antes de conectar un proveedor, el área elige destino, granularidad, permisos y política
de confirmación; prueba lectura, lote parcial, transición denegada y resultado incierto.
La publicación de la próxima versión mayor se decide por separado. No se atribuye a
esta entrega un resultado de integraciones reales ni una prueba Ollama pendiente.
