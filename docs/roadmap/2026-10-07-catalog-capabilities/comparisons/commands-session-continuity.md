# Retoma dirigida sobre journal y ledger

La comparación propone una sola vista de retoma sobre los lectores existentes.
La selección, procedencia y composición tienen dueño en journal/progress.
No añade una etapa del ciclo, una skill ni otro almacén de memoria.

La lectura estática corresponde a la revisión fijada
`ef648e01899ba3e8dc6371642deaaf64b4477775`, realizada el 2026-10-08.
Incluye los cuerpos completos de C079/C085/C087, seis recursos compartidos
completos y dos callers parciales. C004 aporta un contraste secundario;
su cadena de verificación sigue abierta. La
[evidencia de lectura](session-continuity-reading-evidence.json) conserva
hashes, tamaños, rangos y límites. El mapa de rutas reales permanece privado.

**Cero integraciones y cero incrementos de fichas globales cerradas.**
Los recursos directos están leídos; los callers operativos y sus dependencias
fuera del alcance de retoma siguen pendientes. No se ejecutó código del corpus,
probes de runtime, inferencia, acceso remoto ni configuración del consumidor.
Tokens y latencia son desconocidos, no cero.

## Qué criterio aporta cada comando

| ID y lectura completa | Contrato y criterio útil | Destino propio propuesto |
|---|---|---|
| C079 · 8.105 bytes / 181 líneas | Seleccionar un registro explícito sin sustitución; descartar placeholders en selección implícita; presentar objetivo, fallos con razón, bloqueos y siguiente paso | Selector y vista de journal/progress; fachada de comando bajo demanda |
| C085 · 9.702 bytes / 275 líneas | Guardar trabajo confirmado con evidencia, intentos fallidos con causa, decisiones con razones y paso siguiente concreto | Campos operativos bajo el dueño journal, solo donde falte cobertura comprobada |
| C087 · 14.834 bytes / 339 líneas | Listar/seleccionar sesiones y mostrar proyecto, branch, worktree y fecha para distinguir trabajo concurrente | Selección por identidad y metadatos acotados; sin aliases personales globales |
| C004 · 1.622 bytes / 78 líneas | Comparar SHA, archivos, pruebas y cobertura entre baselines verificables | Ledger/QA; dependencia de verificación y política de limpieza pendientes |

C079:48–49 respeta la selección explícita incluso si está vacía o existe otra
entrada más reciente. Su ranking de candidatos implícitos, en 56–68, rechaza
plantillas y prioriza contenido sustantivo. La selección nativa debe distinguir
ausencia, corrupción e imposibilidad de lectura antes de decidir un fallback.

C079:92–100 y C085:88–110 conservan lo que funcionó con evidencia, lo que falló
con su causa, bloqueos y el próximo paso. Son campos útiles para retomar;
una narración histórica no acredita que el test siga pasando hoy.
C085:142–170 añade razones de decisiones y preguntas abiertas.

C087:19 y 294–295 usa metadatos de worktree y recencia. Sirven para seleccionar,
sin convertir el nombre del proyecto o la presencia de un fichero en permiso
para actuar sobre otra raíz.

## Qué cubre ya el plugin y qué falta

| Pieza propia leída | Cobertura existente | Diferencia comprobada |
|---|---|---|
| [journal.py](../../../../agent-kits/shared/journal.py):1417–1456, 1536–1598, 1691–1715, 2127–2131 | Borrador con iniciativa, resumen, decisiones, pendientes y evidencias de cambios; lectura cronológica y salida compacta | latest carece de filtro por iniciativa/session_id y selecciona una entrada por fecha distinta |
| [progress-report.py](../../../../agent-kits/shared/progress-report.py):240–260 | Progreso y tareas activas derivados del ledger canónico | Con varias iniciativas muestra una ruta placeholder; no une una selección concreta con su journal |
| [session-context.sh](../../../../hooks/session-context.sh):199–220 | Inyección del progreso y journal reciente al iniciar/retomar | Llama a latest sin selección de iniciativa o sesión |
| [knowledge-check.md](../../../../agent-kits/shared/knowledge-check.md):91–104 | Los lectores de diseño/planificación consultan la última entrada solo si coincide con su iniciativa | No prescribe recuperar una entrada anterior que sí coincida |
| [knowledge-find.py](../../../../agent-kits/shared/knowledge-find.py):1106–1124, 1201–1301, 1469–1488 | Router de memoria gobernada, permisos del adaptador, ámbito del proyecto y fallback local con motivo | Su intent de memoria no sustituye al selector de trabajo operativo |
| [work-context.md](../../../../commands/work-context.md) | Selección de capacidades por rol, stack y área | Selecciona guías, no sesiones ni trabajo pendiente |

El cierre durable y su replay/recover ya tienen dueño. El contraste conserva
ese reparto, documentado en [contracts.md](../contracts.md), sin reconstruir
otra outbox o escribir un historial paralelo. Los módulos grandes propios
se leyeron por rangos; esta ficha no afirma una auditoría completa de ellos.

La prioridad propuesta es **P1: retoma dirigida bajo demanda**. El mismo
selector/compositor compartido debe alimentar el comando y, cuando proceda,
la vista compacta de inicio. Journal aporta citas y procedencia; progress
aporta el estado actual del ledger. El compositor no calcula otra verdad
de progreso a partir de recuerdos.

T-08 debe fijar la entrada nativa de comando y su contrato. T-11 conectará
sus callers y exports después de esa decisión. La retoma vuelve a pm/dev-cycle
o al trabajo manual ya autorizado; no inicia una cadena adicional.
La captura de campos ausentes, si hace falta, se diseñará dentro de journal.
Esta lectura no implementa ni demuestra esa ampliación.

## Recursos y callers contrastados

| ID | Lectura | Contrato pertinente |
|---|---|---|
| R-6f176fdf443b | 545 líneas completas | Nombres/fechas, búsqueda, metadatos, estadísticas y lectura/escritura de registros |
| R-4cdf2ec0b48f | 481 líneas completas | Resolución/listado y persistencia de aliases |
| R-076e8356b72b | 742 líneas completas | Raíces de datos, lectura de archivos, identidad Git y utilidades de I/O |
| R-e004ae305ac0 | 245 líneas completas | Resolución de raíz personal por entorno/config/default y control de la raíz declarada |
| R-4f8126d33200 | 109 líneas completas | Contención con resolución del ancestro existente y symlinks |
| R-4a236023dc1d | 167 líneas completas | Localizador usado por C087; declara probes de recursos y fallback |
| R-1e25c3ead298 | 1–45 y 700–785, parcial | Caller de aliases y contexto histórico en inicio; sus demás imports quedan fuera de esta ficha |
| C071 | 421–442, parcial | Remisión a C085 para conservar contexto de producto; su flujo propio no se evalúa aquí |

La cadena local de imports de los seis recursos leídos usa esos mismos módulos
y bibliotecas estándar. C079/C085 se llaman entre sí; C085 cita el contrato
de nombres del lector; C087 carga lector, aliases y localizador.
No se deduce eficacia por esos enlaces. La lectura parcial de los dos callers
no cierra sus fichas ni la auditoría general de hooks.

## Qué contratos deben corregirse al consolidar

R-6f176fdf443b:170–176 acepta prefijos; 419–431 devuelve la primera coincidencia
ordenada por recencia. Una selección ambigua puede cargar otra sesión.
El selector propio debe resolver identidad exacta o presentar candidatos;
no sustituir silenciosamente la elección explícita.

C085 guarda secciones de nivel dos, mientras R-6f176fdf443b:295–319 busca
secciones de nivel tres con otros nombres. Un registro válido puede mostrar
cero tareas. La vista propia debe usar su esquema canónico, conservar campos
desconocidos como datos y distinguir vacío válido de formato incompatible.

R-4cdf2ec0b48f:42–80 convierte estado ilegible/corrupto en defaults.
Su escritura en Windows elimina el destino antes del rename (113–119).
No se traslada ese escritor ni el almacén global de aliases.
R-076e8356b72b:454–459 lee sin tope y convierte todo fallo en null.
Los límites de stdin de 351–431 no acotan esa lectura de archivo.

C087:37 fija veinte resultados en el cuerpo pese a documentar flags;
su carga muestra metadata/estadísticas, sin imprimir el cuerpo leído.
La fachada propia debe implementar sus opciones declaradas y explicar
selección, omisiones y contenido mostrado.

C079:106–112 impone una espera tras cargar; C085:54–64 pide confirmación.
El contrato propio conservará corrección/revisión del resumen, sin introducir
una confirmación nueva cuando la continuación ya esté autorizada.
C004:17–22 crea stash/commit y otro log; ese mecanismo no se propone copiar.

## Memoria operativa, doctrina y acciones actuales

[knowledge-write.md](../../../../agent-kits/shared/knowledge-write.md):20–31
mantiene el journal episódico separado de ADR/gotchas/lecciones.
La vista de retoma conserva esa frontera. Una decisión citada no se promueve
por aparecer en el briefing ni se publica mediante un backend de memoria.
Knowledge Gate conserva aprobación y ámbitos de publicación.

Los pendientes históricos son indicios. Antes de continuar, el caller contrasta
el ledger y las fuentes vigentes, sin repetir comandos antiguos por su presencia
en un resumen. R-1e25c3ead298:719–739 aporta una advertencia de contexto histórico;
es prosa dirigida al modelo, no enforcement ni prueba de dispatch nativo.

La vista de lectura no ejecutará replay/recover, mutará entradas, creará aliases
ni abrirá backends por defecto. Si falta historial, informa de la ausencia y
continúa con la tarea autorizada y su ledger disponible.

## Activación y validación pendientes

Escenarios estáticos: «retoma esta iniciativa con lo que quedó pendiente»;
paráfrasis «continúa la tarea con sus bloqueos y próximos pasos».
El negativo vecino «aprueba esta decisión como doctrina» corresponde a
knowledge-curator y su puerta existente. No son evals nativas ejecutadas.

T-11/T-14 deberán probar selección explícita sin fallback, prefijos ambiguos,
dos proyectos/worktrees, sesión repetida entre runtimes, registros vacíos,
corruptos o ilegibles, symlinks/rutas fuera de raíz, CRLF/Unicode y corpus grande.
También estado histórico frente al ledger vigente, pruebas caducadas, redacción,
topes de lectura/salida y ausencia de escrituras/red en modo de retoma.
La comparación de utilidad requerirá la misma tarea y evidencia de éxito;
leer más contexto o cargar un comando no demuestra mejor continuidad.

Esta propuesta amplía la dirección fijada en
[operational-panel-commands.md](operational-panel-commands.md) y S035 de
[skills-operations-session-context.md](skills-operations-session-context.md).
T-07 mantiene abierta la evaluación integral de memoria. T-05 conserva abierta
la cadena secundaria de C004; T-08 decide propiedad antes de implementar.
No se modifica el diseño, ledger ni código de producción desde esta ficha.
