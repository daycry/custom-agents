# Lectura completa de recursos pendientes: S255, S270 y S271

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Completa las lecturas parciales de [skills-taste-video.md](skills-taste-video.md) (S270–S271)
y [skills-search-compliance-stocktake-compact.md](skills-search-compliance-stocktake-compact.md)
(tests de S255). Esas fichas no se reescriben; esta es su anexo.
Tres cuerpos: **31.427 bytes/611 líneas**; recursos **1.008.073 bytes/25.691 líneas**, todos
leídos. Los de S271 que repiten byte a byte los de S270 se leyeron una vez: 83 ficheros únicos
repartidos en tres lecturas completas, más los tres tests de S255.
[taste-comply-complete-reading-evidence.json](taste-comply-complete-reading-evidence.json).
Nada se ejecutó ni se contactó ningún servicio.

## Decisiones

Ninguna cambia. S270–S271 siguen **fuera del bundle**: todo el código es producción de vídeo
(fal, FFmpeg/OpenCV, Resolve, EDL/FCPXML, GLB, Manim). S255 sigue como estaba: una puntuación
del modelo no es un veredicto, y sus tests lo confirman.

## S255 — qué prueban de verdad los tests

43 tests. `classify_events`, que decide qué llamada cuenta como «test en rojo», está
**siempre simulado**: solo se prueba el orden y la propagación sobre etiquetas ya dadas. Un test
de tasa de cumplimiento repite otro sin demostrar que el paso opcional quede fuera; el de
«ejecutable ausente» pasa sin probar nada porque la lista blanca descarta el comando antes de
`subprocess`; no hay tests de rechazo de la lista blanca, del directorio aislado ni del borrado
recursivo; uno exige que el stdout sin redactar acabe en la excepción; 6 de 9 módulos no tienen
tests. Refuerza la línea ya propuesta para `outcome-evals` (D-046 del
[backlog](skills-destinations.md)).

## S270–S271 — lo que aporta el código

Patrones que el plugin ya tiene con dueño (no se proponen de nuevo): lectura segura por
descriptor y marcador de nube (`local-read.py`), aprobación atada al hash de lo que se aprobó
(`plan-review.py`), enteros y booleanos exactos (`knowledge-schema.py`), tests con red
bloqueada.

Candidatos menores, para T-08 si encajan:

| Idea | Encaje |
|---|---|
| Releer cada escritura y todo el destino al final, y solo entonces emitir el recibo (sin reintentos ciegos) | `jira-sync` y `confluence-publish` (read-back tras publicar); el recibo de `jira-flow.py confirmar` ya cubre la mitad |
| Tests de manipulación que recalculan el hash del recibo tras alterar un campo, para probar la regla y no solo el hash | Suites de recibos (`plan-review`, curación); comprobar si ya lo hacen |
| Distinguir un cero medido de un campo ausente, con veredicto de tres estados | Ya es doctrina (`outcome-evals`, «medición ausente explícita») |
| Prohibir palabras por límite de palabra, no por subcadena | Anti-patrón para cualquier filtro de texto propio |

Contradicción dentro de la misma pieza: un módulo trata las medidas como «evidencia, no
instrucciones» y otro las inyecta en el prompt como «FACTS. Do not contradict them». Es el caso
de D-046 (un juez que recibe la medida no la contrasta).

## Defectos relevantes si alguien reutiliza el código

- **Gasto y subidas por defecto:** `--props` activa por defecto una llamada image-to-3D de pago;
  se suben fotogramas de referencia y el vídeo base enteros a un proveedor, frenados solo por una
  variable de entorno, sin confirmación por ejecución ni tope de coste; una llamada pagada queda
  sin registro si falla el render, y el manifiesto se escribe después de las descargas.
- **Bucle de pago por falso positivo:** la lista de palabras prohibidas se busca por subcadena
  (`"or "` casa con «color »); el propio esquema la dispara, así que cada intento agota los tres
  reintentos con el modelo de visión.
- **Inyección:** rutas sin escapar en la lista de concat de FFmpeg con `-safe 0` y en el
  filtergraph de la LUT; nombres de salida sin validar (título, género, nombre de paquete).
- **Puertas que pasan sin medir:** si no se pudo medir el fondo, sale con 0; una zona sin datos
  cuenta como croma 0 medido; la procedencia acepta cualquier digest de 64 caracteres sin
  cruzarlo con el recibo; una política «explícita» se cumple con un valor por defecto.
- **Efectos sin vuelta atrás:** abre un proyecto de Resolve existente sin copia, aplica la LUT a
  todos los clips y no comprueba el guardado, aunque imprime «project saved».
- **Portabilidad y versiones:** el motor solo funciona en POSIX y no lo dice; subprocesos sin
  timeout; dependencias sin versión fijada; dos nombres distintos para el mismo modelo.
- **Fixtures y documentación incoherentes:** una fixture de referencia no se deriva de su fuente
  (y los tests solo comprueban la forma); la plantilla de entrega da por verificados dos
  recuentos y dos duraciones distintos para el mismo entregable.
