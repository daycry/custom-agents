# 6. Operación, adopción y resolución de incidencias

## Puesta en marcha de un área

El responsable elige un proyecto piloto, un objetivo pequeño y las funciones
externas necesarias. Se asignan un dueño del proceso, un administrador de conectores
y un responsable técnico. Se acuerda qué operaciones puede realizar cada cuenta,
qué documentos son publicables y quién aprueba cambios con efectos externos.

Primero se ejecuta un ciclo local completo. Después se añade una integración de
seguimiento y, si hace falta, la de documentación. Se prueba con una tarea/página
de destino controlado, incluyendo una operación rechazada y una reconciliación.
Solo entonces se amplía a más iniciativas. Un inventario de MCP conectado no
sustituye esta aceptación de negocio y técnica.

## W-18. Validar y operar una integración

**Comandos:** `/doctor`, `/work-context` y el router de solo lectura.
**Actores:** usuario del proyecto, administrador y dueño del adaptador.
**Tools:** diagnóstico local y lecturas del proveedor cuando se solicitan.

| Paso | Actor | Acción | Interpretación correcta |
|---|---|---|---|
| 1 | Usuario | Fija raíz de proyecto y runtime | Un diagnóstico de otra raíz no acredita esta instalación |
| 2 | Router | Valida bindings y filtra por evento/operación | `declared` solo significa declaración válida |
| 3 | Doctor | Revisa instalación, configuración y avisos | No certifica despachos anteriores ni permisos remotos |
| 4 | Runtime/administrador | Comprueba conexión, cuenta y tools | Se separa autenticación de permiso sobre el destino |
| 5 | Adaptador | Hace una lectura acotada | Comprueba el objeto/proyecto real y la paginación |
| 6 | Usuario | Revisa una operación concreta | Autorización aplicable al efecto previsto |
| 7 | Adaptador | Ejecuta y clasifica el resultado | Confirmado, omitido, fallido o incierto |
| 8 | Dueño | Conserva recibo mínimo o reconcilia | No reintenta a ciegas una escritura incierta |

Ejemplo de validación sin llamadas remotas:

```powershell
python agent-kits/shared/integration-route.py --project <proyecto> --check
python agent-kits/shared/integration-route.py --project <proyecto> --event task.started
python agent-kits/shared/project-pieces.py --project <proyecto> --runtime codex --project-only --json
```

Los scripts se localizan en el bundle instalado; estos ejemplos desde el checkout
no fijan una ruta de usuario. `--check` usa exit 2 para configuración inválida,
parcial o no disponible. En el workflow ordinario esos problemas se comunican y
se omite la proyección inválida, conservando las puertas del trabajo local.

## Estados del router

| Estado | Significado | Acción |
|---|---|---|
| `absent` | No hay declaración ni opt-in reconocido | Trabajar localmente o configurar una función |
| `disabled` | No hay bindings activos | Respetar la elección; no volver a activar por detectar un MCP |
| `declared` | Hay bindings válidos que coinciden | Comprobar disponibilidad, contrato, destino y permisos |
| `no_match` | Hay bindings activos, pero no para ese filtro | No usar otra integración por aproximación |
| `partial` | Coinciden bindings válidos y hay declaraciones rechazadas | Mostrar diagnóstico; usar solo las independientes válidas |
| `invalid` | No se puede usar la declaración solicitada | Revisar esquema/duplicados; no resetear ni buscar otra cuenta |
| `unavailable` | No se pudo obtener una lectura segura o dependencia | Restaurar el bundle o corregir acceso; seguir localmente |

Disponibilidad y permisos permanecen `unverified`, y ejecución `not_run`, en la
salida del router. Son límites deliberados de ese lector, no una prueba de fallo
del proveedor. La ejecución real debe quedar evidenciada por su adaptador.

## Incidencias habituales

| Síntoma | Comprobar | Resolución |
|---|---|---|
| Configuración válida, tool ausente | Runtime, conexión, versión y catálogo real | Activar/corregir el conector; no inventar un nombre de tool |
| Usuario conectado, escritura rechazada | Cuenta, destino, rol y política administrativa | Administrador revisa permisos; no se escala automáticamente |
| Estado remoto no disponible | Transiciones permitidas del objeto concreto | Dejar pendiente y acordar mapeo; no forzar un ID de ejemplo |
| Timeout tras crear/comentar | ID/correlación y datos del proveedor | Reconciliar antes de repetir; mantener resultado incierto |
| Cambiaron documento local y remoto | Hash base y revisión de ambas partes | Vista previa de conflicto y elección del usuario |
| Se duplican comentarios | Dueño del evento y clave de intento | Un único publicador; recibos por operación, no booleano global |
| Plan por fase cierra demasiado pronto | Tareas del lote y gates de todas | Reabrir/reconciliar según autorización y corregir adaptador |
| Inventario parcial de extensiones | Formato, límites, enlaces y conflictos | Corregir la declaración; no interpretar omisión como permiso |
| `plugin contents changed; hook approval required` | Versión instalada y cambios del bundle | Revisar/aprobar con la interfaz nativa; no modificar hashes de confianza para saltarla |
| Hook sin nombre o sin ejecución acreditada | Etiqueta en versión instalada y resultado del proceso | Actualizar por el flujo admitido; separar problema de UI y fallo de ejecución |

Un mensaje de UI sobre una conversación desconocida no es recibo de fallo de un
proceso. Del mismo modo, tener un hash aprobado no demuestra que un hook se haya
ejecutado. El diagnóstico se basa en el resultado y los registros pertinentes,
acotados y sin volcar conversaciones ni configuración privada completa.

## Migrar al contrato modular

El usuario ha permitido cambios de versión mayor. Este manual no promete que
cualquier configuración histórica funcione sin revisión. El contrato explícito
es `.claude/integrations.json`, versión 1, con bindings por función.

Antes de cambiar, guarda una copia privada de preferencias y mapas. Identifica
destinos reales y operaciones ya publicadas. Prepara los bindings con el esquema
nuevo; una lista explícita vacía desactiva la selección externa. Si el archivo
nuevo existe, prevalece sobre opt-ins anteriores incluso si está vacío o inválido;
no se ignora para usar una configuración antigua sin avisar.

Solo en ausencia del archivo nuevo se reconocen los opt-ins locales Jira y
Confluence con `enabled` booleano. Esa lectura se conserva como transición
explícita, sin migración automática. Los archivos de otro proyecto o HOME no se
usan como sustitutos. Los scripts Jira requieren la raíz del proyecto; ya no
heredan el opt-in de un directorio padre.

Los paquetes portable modificados no se regeneran encima: exporta a otro destino,
compara cambios e integra lo que proceda. Las instalaciones por copia con perfil
no adoptan archivos históricos por su nombre. Usa un destino limpio o reconcilia
los archivos y su propiedad antes de cambiar perfil. No borres mapas remotos para
eludir un conflicto de migración.

## Mantener el manual y el PDF

Los capítulos Markdown son la fuente de la edición de entrega. Al cambiar un
workflow se actualizan pasos, dueños, comandos, skills, tools, configuraciones,
eventos y errores en ambos idiomas. Los ejemplos deben seguir pasando la validación
del router y las pruebas del adaptador correspondiente. El PDF se regenera desde
esa misma fuente y se revisa visualmente antes de distribuirlo.

Un responsable puede pedir: «Prepara la spec de esta iniciativa», «Muéstrame el
plan antes de crear tareas», «Publica solo los documentos de esta fase» o «Dime
qué quedó pendiente de sincronizar». El producto debe responder con resultados,
evidencias y decisiones pendientes, sin obligarle a aprender IDs internos ni a
leer logs crudos para entender qué pasó.

## Recuperar una instalación por copia interrumpida

Una actualización de perfil no es una transacción de todo el árbol. Si se cancela
o falla, pueden haberse aplicado algunos archivos. El manifiesto incompleto conserva
los hashes propios anteriores y los planificados, para reconocer archivos intactos
sin adoptar una modificación del consumidor. Tras reconciliar el conflicto, repetir
la instalación conserva la selección y retoma el cambio; la desinstalación también
puede retirar los archivos propios que se mantuvieron en su versión anterior.

Cada archivo se revalida antes de reemplazarlo. En perfiles protegidos, un bloqueo
persistente de Windows termina con error: no se recurre a truncar el archivo en uso.
Esta protección detecta cambios observados; no es un bloqueo universal frente a
escritores externos ni una garantía de atomicidad multiarchivo. Conserva la evidencia
del error y revisa el manifiesto antes de decidir repetir o desinstalar.
