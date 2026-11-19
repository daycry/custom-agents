# Diagnóstico de arquitectura de un sistema de agentes

Léela solo cuando un agente, hook o memoria propios se comporten mal y la causa pueda estar en
lo que rodea al modelo (cómo se ensambla su contexto, qué memoria recibe, cómo se ejecutan e
interpretan sus herramientas) y no en el modelo; o antes de añadir una capa que reinyecte contexto
o repare respuestas.

Con un fallo reproducible, el método es la causa raíz en cuatro fases con evidencia (la skill
`debug-root-cause`, si el plugin está instalado); este mapa sirve para la fase de aislar en qué capa vive
el fallo. Diagnosticar no modifica nada: el cambio lo hace quien implementa y alguien distinto lo revisa.

## Primero: modelo o envoltura

Repite la misma petición con el contexto mínimo (sin hooks, memoria ni fragmentos añadidos) y
compara. Si el modelo acierta así y falla dentro del sistema, el defecto está en una capa, y añadir
instrucciones no lo arregla.

## Las doce capas

| Capa | Qué abarca | Fallo típico | Evidencia a recoger |
|---|---|---|---|
| 1. Ensamblado de instrucciones | Prompt del agente, fragmentos compartidos, skills precargadas, ficheros de instrucciones del proyecto, contexto de inicio de sesión | Reglas contradictorias o duplicadas; un fragmento ausente en una instalación parcial | Lista de fuentes cargadas y su tamaño |
| 2. Historial | Turnos de la sesión | Una instrucción antigua gana a la petición actual | Turno donde cambia la conducta |
| 3. Memoria | Notas, journal, conocimiento guardado | Un episodio sin curar leído como doctrina; una propuesta tratada como aceptada | Estado y procedencia de la entrada usada |
| 4. Destilación | Compactación, resúmenes | Un resumen reingresa como hecho, sin procedencia | Texto destilado frente a su fuente |
| 5. Recuperación | Búsqueda de memoria o de piezas | Resultado de otro ámbito; una ausencia leída como «no existe» | Consulta, filtros y resultados devueltos |
| 6. Selección de herramienta | Descripciones de skills, agentes y comandos | Se activa la pieza vecina | Caso de evaluación que lo reproduce |
| 7. Ejecución de herramienta | Scripts y tools | El agente afirma haber ejecutado algo sin salida que lo pruebe | Comando real, exit code y salida cruda |
| 8. Interpretación de la observación | Lo que el agente concluye de la salida | Exit 2 (uso) leído como veredicto; salida truncada leída como completa | Salida cruda frente a la frase del agente |
| 9. Formato | Parsers de registros, frontmatter y cabeceras | El parser no reconoce la sección y la trata como vacía | Línea exacta que no casa |
| 10. Transporte | stdout/stderr, JSON de hooks, codificación, subprocesos | Respuesta mutada por codificación, CRLF o diagnóstico mezclado en stdout; salida que el evento ignora | Bytes recibidos frente a bytes emitidos |
| 11. Reparación | Reintentos, fallbacks, autocorrecciones | Una llamada de reparación no visible cambia el resultado; reintentos en bucle | Registro de cada intento con su causa |
| 12. Persistencia | Registros de estado, colas, ficheros | Escritura parcial, registro dañado sobrescrito, carrera entre procesos | Estado antes y después; ver `references/persistent-workflows.md` |

## Cinco patrones de fallo de la envoltura

| Patrón | Síntoma | Pregunta que lo distingue | Corrección preferente |
|---|---|---|---|
| Respuesta mutada | Lo que llega al agente no es lo que emitió la tool | ¿Coinciden los bytes de salida y los que lee el agente? | Contrato de transporte con test (codificación, stdout limpio) |
| Ejecución fingida | El agente informa de un resultado sin ejecución | ¿Hay comando, exit y salida pegados? | Exigir la salida real como evidencia de cada entrega |
| Recuerdo contaminado | Una memoria no aprobada o de otro proyecto guía la decisión | ¿Qué estado y procedencia tiene la entrada? | Admisión de memoria: estado, ámbito y procedencia visibles |
| Artefacto comprimido como hecho | Un resumen vuelve como dato verificado | ¿Se puede llegar desde el resumen a su fuente? | Procedencia obligatoria; citas, no instrucciones |
| Reparación invisible | El resultado cambia sin que conste quién lo cambió | ¿Hay un registro por intento? | Límite de reintentos y registro de cada reparación |

## Recogida de evidencia

- Ventana del incidente, versión del plugin y del runtime, modelo.
- Fuentes de contexto cargadas, transcript si existe y salida cruda de cada tool implicada.
- Estado en disco antes y después (registros de estado, colas, ficheros de configuración del runtime).
- Sin logs ni transcript: compara código y contratos, declara qué evidencia falta y entrega un
  diagnóstico **parcial**. No reconstruyas una trayectoria, una ejecución ni la eficacia de una
  corrección que no se observaron.

## Informe

Un hallazgo por fila, priorizado:

| Campo | Contenido |
|---|---|
| Síntoma | Lo observado, con su evidencia |
| Mecanismo | Cómo produce el síntoma |
| Capa | Una de las doce |
| Causa | Frase falsable y la prueba que la confirma o «sin probar» |
| Evidencia | `fichero:línea`, comando y salida |
| Confianza | alta · media · baja, con el motivo; no es una probabilidad calibrada |
| Gravedad | Critical · Important · Minor, como en la revisión |
| Corrección propuesta | Según el orden de abajo |

El informe es evidencia del trabajo en curso: no abre otro registro paralelo ni aprueba memoria. Si el
proyecto guarda conocimiento técnico, el hallazgo se propone por su proceso de curación.

## Orden de corrección

1. Contrato en código: validación, script con test, parser que falla en vez de leer vacío.
2. Límite de reparación: reintentos acotados y registrados.
3. Admisión de memoria: estado, ámbito y procedencia antes de inyectar.
4. Menos duplicación de contexto: una sola fuente por regla.
5. Solo al final, más instrucciones en prosa. Una regla escrita no es una guardia aplicada: lo que
   deba impedirse va a un guardrail con test, no a un párrafo más.
