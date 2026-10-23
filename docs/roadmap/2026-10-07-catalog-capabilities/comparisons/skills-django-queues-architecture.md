# Django: tareas distribuidas, ORM y APIs — S078–S079

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Dos cuerpos completos: **34.250 bytes/1.193 líneas**, cero recursos en sus
directorios. [django-core-reading-evidence.json](django-core-reading-evidence.json)
registra 11 fuentes, 14 contrapartes propias y 14 contrastes oficiales. Lecturas
de consumidores parciales no cuentan como evaluación de sus agentes/skills.
Los nombres originales quedan en el mapa privado; [tasks.md](../tasks.md) es
el ledger canónico. Las decisiones siguientes son propuestas para T-08.

No se ejecutaron código, snippets, tests del corpus, instalaciones, migraciones,
workers, brokers ni pagos. Ninguna propuesta de este bloque está integrada en
producción. Los escenarios son checks preparados; no atribuir ejecución real
a un ejemplo, un hash o un test documental.

## S078 — Trabajo distribuido con Django y Celery

**Identidad.** SHA-256
`1f9189ece910eb90a5d2cd520a9a6238ccb89a3e48629ac1ad9b55ec3eb21f88`,
13.134 bytes/458 líneas, cero recursos locales. Cubre configuración por namespace,
registro de tareas, ejecución diferida, retries, Beat, canvas, resultados,
observación y tests. R-591e7a1672e1/R-03ffcc8e6e9e declaran la pieza; S079/S081
y testing Python son dependencias textuales. El mapa R-6a2e152ec772 tiene triggers
para Django general, pero no una entrada específica de esta pieza; no demuestra
activación nativa ni que todas las tareas sean seleccionadas correctamente.

**Valor y cobertura existente.** `backend-practices/references/contracts-data.md`
ya exige idempotencia ligada a identidad/contenido, resultado durable, límites de
E/S y separación de transacción local y efecto remoto. `stack-practices`/Python
aporta cancelación, recursos, imports y fixtures; delivery conserva recuperación
y herramientas. Falta su aplicación concreta a broker/worker/scheduler/result
backend de Celery. El delta es esa costura distribuida, sin un método TDD nuevo,
un motor de workflows del plugin o infraestructura obligatoria del consumidor.

**Defectos y criterios que se conservan corregidos.**

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `acks_late=True` promete reencolar al caer el worker | Distinguir caída del worker completo de terminación del proceso hijo, acknowledgements y política de redelivery; probarlos por versión, pool y broker. No activar reject-on-worker-lost sin valorar bucles de fallos |
| Usuario ausente se descarta y correo se presenta como idempotente | Un registro no confirmado puede aparecer después; despachar tras commit. Usuario inexistente puede ser una política válida, pero no evita enviar dos veces a uno existente: deduplicación del efecto con clave y estado |
| `delay(user.pk)` desde una operación que crea datos | `on_commit` o API versionada equivalente cuando la tarea dependa del commit. Registrar fallo de publicación después del commit y recuperación; el callback no hace atómico DB + broker |
| Guard de pago usa `select_for_update()` sin bloque transaccional visible | Declarar unidad atomic y motor real; bloqueo local no resuelve aceptación remota seguida de caída ni demuestra transición de estado. Clave idempotente del proveedor/reconciliación y reglas del dominio |
| `mark_shipped` no actualiza si ya salió de PROCESSING | Conservar update condicional, pero distinguir misma transición repetida de otro tracking incompatible o estado inválido; `updated=0` no prueba por sí solo éxito previo |
| `default_retry_delay=60` se comenta como primer delay con backoff activo | Separar delay manual del cálculo de autoretry/backoff; comprobar factor/jitter, tope y excepciones de la librería realmente usada |
| Rate limit convierte `retry_after` directamente a int | Validar forma, rango y plazo total; distinguir dato ausente/malformado y formato del cliente. No reintentar errores de negocio ni cobros inciertos como simples fallos transitorios |
| Tras max retries, crea FailedCharge y retorna normalmente | Tabla de fallos no es DLQ del broker. Retorno puede aparecer como tarea exitosa y continuar canvas; representar fallo de dominio, deduplicar registro y definir reparación/replay autorizado |
| Sentry recibe args/kwargs y debug imprime request completa | Redactar datos personales/secretos, tamaño y rutas sensibles antes de observación. JSON no cifra el mensaje ni autoriza a todos los lectores del broker |
| ETA de un día con Redis y configuración por defecto | Contrastar ventana de visibility, retención, consumo y recuperación; para futuro lejano evaluar scheduler durable. Aumentar timeout cambia el tiempo de recuperar mensajes perdidos |
| Un Beat y periodo fijo | Mantener un scheduler por schedule; la tarea puede solaparse aunque haya un solo Beat. Resolver timezone/DST, reinicio y exclusión por unidad de trabajo |
| Chord suma resultados de tareas paralelas | Comprobar backend compatible, resultados conservados, callback/errback y tareas restantes tras fallo; distinguir signature de AsyncResult, sin bloquear un worker esperando a sus hijas |
| Tests eager y assert de una llamada demuestran retry | Separar lógica aislada, política de retry y transporte real. El número de llamadas y excepción dependen de configuración y camino invocado; no tratar ese assert como prueba de redelivery |
| Instalación añade results/beat y Redis siempre | Elegir extras/backend/scheduler del proyecto; incluir migraciones, versiones y configuración necesarias solo cuando se usen. No arrancar infraestructura o instalar paquetes al leer la guía |

**Contraste oficial.** Celery **5.6.3** documenta acknowledgements incluso ante
determinadas terminaciones del hijo con `acks_late`; el backoff automático usa
su factor y jitter. Estos contratos no certifican idempotencia de los ejemplos.
[Tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

Desde Celery **5.4**, `delay_on_commit` requiere la base DjangoTask correspondiente
y no devuelve ID de tarea. Para versiones anteriores se conserva `on_commit`;
su fallo posterior no revierte la transacción ya confirmada. Un outbox durable
es una opción del dominio, no una consecuencia automática del callback.
[Django/Celery](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html),
[transacciones Django 5.2](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

Redis tiene visibility timeout y tradeoffs para ETA/retries largos. Beat exige
un scheduler por schedule y no impide solapamiento de ejecuciones. Chords requieren
resultados y backend compatible; fallo de una hija no cancela todas las demás.
[Redis](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html),
[Beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html),
[Canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html).

El modo eager es emulación y no acredita un worker real. Las fixtures de testing
tienen dependencias y capas distintas. Celery no declara soporte Windows desde
4.x: que custom-agents funcione en Windows no acredita soporte nativo de su worker.
Ensayar en el entorno admitido del consumidor; tests estáticos Windows siguen
separados de broker/pool real en Linux u otro entorno soportado.
[Testing](https://docs.celeryq.dev/en/stable/userguide/testing.html),
[FAQ](https://docs.celeryq.dev/en/stable/faq.html).

**Decisión y destino.** Conservar como referencia opcional
`skills/django-practices/references/distributed-tasks.md`, junto a S079 y las
fichas S080–S082 pendientes. Guía del consumidor, sin dependency runtime del
plugin. Mantener criterios compartidos en backend/delivery y métodos de tests
en tdd/unit-tests/qa; no duplicar el pipeline ni declarar otro agente de fase.
S234 necesita su evaluación completa antes de cerrar solapes Redis.

**Activación preparada.** «Añade tareas Celery a nuestra app Django»;
«El trabajo periódico se duplica al reiniciar workers»; negativo «Optimiza
cancelación asyncio sin cola» → Python; «El hook de SessionEnd no llega» → hooks,
sin sustituirlo por Celery. El diagnóstico puede necesitar esta referencia y
debug-root-cause; un trigger no autoriza ejecutar pagos, replay o purge.

**Validaciones pendientes T-14.** Commit/rollback y broker caído después del
commit; duplicado simultáneo, caída después de pago aceptado; proceso hijo
terminado vs worker completo; retries agotados visibles; payload inválido y
redacción; ETA mayor que ventana Redis; Beat doble y job lento; timezone/DST;
chord con hija fallida, backend incompatible y result ignorado; cleanup de PDF
interrumpido; shutdown y publicación parcial. Separar unitarios, DB real y worker
real. No se ejecutó ningún escenario de ese tipo aquí.

**Carga/impacto.** 458 líneas bajo demanda; tokens/latencia null. T-08/T-10 decide
fragmentación/activación, T-11 handoffs, T-12 disponibilidad de herramientas,
T-14 ejecuciones y T-15 docs/exports. Si faltan broker, worker o runner, indicar
limitación concreta; no dar verde ni instalar dependencias silenciosamente.

## S079 — Arquitectura Django, consultas y contrato de APIs

**Identidad.** SHA-256
`14abe2b635054dff872c07d4993057e614b48ac718c0431f1299931be7d69516`,
21.116 bytes/735 líneas, cero recursos locales. Entradas R-591e7a1672e1,
R-03ffcc8e6e9e y R-6a2e152ec772; consumidores A017 230–251/A018 135–163,
S008 111–128, S175 26–40, S217 117–129 y S234 390–403, leídos parcialmente.
Sus recomendaciones no se adoptan por referencia: el ejemplo de `migrate --fake`
de A017 no prueba que historial/esquema coincidan ni autoriza reparar producción.
Comparación completa de ambos agentes queda en T-04.

**Valor.** Organización de apps/settings, QuerySets/managers, serializers/viewsets,
servicios, caches, signals/middleware, N+1, índices y bulk operations. La salida
útil adapta estos mecanismos al esquema y contrato existente; no cambia todo
proyecto a un árbol de carpetas o base de datos prefijados.

**Comparación propia.** Backend ya cubre autorización por recurso/tenant,
paginación, idempotencia, queries y migraciones. Python cubre import/E/S/fixtures;
la referencia de ciberseguridad Python incluye errores Django de raw SQL, escaping,
configuración y serialización. Es cobertura editorial existente, no verificación
de todas sus alternativas, versiones o hallazgos. El contenido nuevo son los
puntos de extensión y efectos concretos del framework; seguridad/pruebas completas
S080–S082 deben contrastarse antes de cerrar la especialidad.

**Correcciones y contenido útil.**

| Área del cuerpo | Decisión de integración |
|---|---|
| Settings separados con env/WhiteNoise/CORS/debug toolbar | Mantener forma existente y declarar dependencias/imports/versiones. Target de producción explícito, secrets sin defaults inseguros, logs portables con redacción; HSTS/proxy no son presets universales |
| Usuario basado en AbstractUser con email como identificador | Configurar AUTH_USER_MODEL y manager/admin/formularios coherentes antes de la primera migración; sustituir un usuario existente requiere diseño de datos, no copiar la clase |
| Registro guarda usuario, después hash y otro save | Construir password/validaciones antes de persistir o usar servicio/manager adecuado; evitar estado intermedio y doble efecto de signals, con unidad transaccional y constraints |
| Product usa slug único y agrega índice sobre slug | Revisar índices ya creados por unicidad/foreign key y planes reales. Slug derivado puede colisionar; definir manejo concurrente y no confiar en save para todo camino de escritura |
| `CheckConstraint(check=...)` | Seleccionar API de la versión mínima. En Django 5.2 `condition` es vigente y `check` está deprecado desde 5.1; no forzar migración de versiones del consumidor |
| Serializer lee discount/rating y ViewSet usa created_by/is_featured ausentes en Product mostrado | Declarar precondiciones del modelo/queryset e imports, completar una fixture coherente; no presentar esos fragmentos como app ejecutable ni exigir esos campos a todos |
| IsAuthenticated + IsOwnerOrReadOnly con queryset global | Definir política efectiva en listas, detalle y creación; filtrar ámbito permitido y validar relaciones/tenant. Nombre de permiso no acredita que listas o featured estén filtrados |
| `my_products` asume que paginate_queryset siempre devuelve página | Cubrir paginación desactivada y defaults; fallback de lista acotada según contrato. Featured/custom APIView requieren decisión explícita de límites y orden |
| Carrito lee ID/quantity y crea item sin validación completa | Validar tipos/rangos, autorización/tenant, stock, unicidad y repetición concurrente. Clasificar entrada inválida sin convertirla en 500; no una escritura duplicada por reintento |
| Service atomic copia carrito pero pago está fuera de esa unidad | Verificar propiedad y estabilidad de carrito/precios/stock; separar transacción local y pasarela. Reconciliar cobro aceptado pero estado/email fallido, no prometer exactly-once por atomic |
| Cache guarda listas de modelos y fragmento sidebar global | Los objetos de modelo pueden ser cacheables, pero retención/invalidation, scope por usuario/tenant/idioma y permisos siguen pendientes. No usar pickle de entrada no confiable ni compartir contenido privado por una key global |
| Dos receivers crean Profile y después guardan instance.profile | Relación puede faltar en datos históricos; definir unicidad/recuperación y política de errores. Bulk paths no envían todas las señales; no esconder invariantes del dominio en un callback |
| Middleware escribe last_active cada request y mide time.time | Declarar campos/imports/orden respecto a auth; reducir escrituras según necesidad, evitar señales recursivas y escoger reloj monotónico para duración. No registrar rutas/datos sensibles sin redacción |
| bulk_create de Product ignora slug generado por save | Bulk no llama save ni todas las señales; generar campos obligatorios y respetar constraints explícitamente, por batches y motor. Bulk update tampoco ejecuta save/auto_now por sí solo |
| select_related/prefetch/index se presentan como optimización | Conservar elección por cardinalidad, campos consumidos y medición de consultas/plan; prefetch no evita N+1 si el serializer añade otras relaciones. No índices duplicados o ilimitados por lista de buenas prácticas |

**Contratos oficiales.** Django 5.2 distingue API de constraints, operaciones
bulk que omiten save/signals y bloqueo por motor. TestCase puede ocultar un
select_for_update fuera de atomic y SQLite no acredita bloqueo real: usar una
prueba transaccional adecuada en el motor del consumidor.
[Constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/),
[QuerySets](https://docs.djangoproject.com/en/5.2/ref/models/querysets/).

AUTH_USER_MODEL se fija antes de las primeras migraciones; cambiarlo a mitad
del proyecto requiere tratamiento de esquema/datos. No asumir que definir una
clase y USERNAME_FIELD configura todos los consumidores de autenticación.
[Usuario personalizado](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/).

DRF no aplica automáticamente permisos por objeto a cada resultado de lista
ni a la creación. Su paginación exige configuración y llamadas apropiadas;
ambos defaults de paginación pueden estar en None. El cache admite objetos
serializables, pero variar por identidad sigue siendo una decisión necesaria.
[Permissions](https://www.django-rest-framework.org/api-guide/permissions/),
[Pagination](https://www.django-rest-framework.org/api-guide/pagination/),
[Cache](https://docs.djangoproject.com/en/5.2/topics/cache/).

**Decisión y destinos.** Conservar especialidad opcional `django-practices`:
`references/architecture-orm.md` para settings/models/queries/signals/middleware;
`references/api-cache.md` para DRF, servicios y caches; S078 en distributed-tasks.
Remitir criterios genéricos a backend/Python y métodos únicos de pruebas/revisión
al ciclo existente. S080–S082 definirán seguridad/tests/verificación sin abrir
otros motores ni agentes duplicados. Todo criterio útil del cuerpo tiene esos
destinos; el refactor material de callers, catálogo y exports queda T-10/T-15.

**Activación preparada.** Literal «Revisa el ORM y serializers de esta app Django»;
paráfrasis «Evita que nuestras listas DRF mezclen tenants y hagan N+1»;
negativo «Define HTTP para una API sin Django» → backend/api-contract;
«Arregla permisos de un agente Codex» → contrato de runtime, no permisos DRF.
Una app Django sin DRF/Celery activa solo referencias pertinentes, según manifiesto
y versiones; Python declarado no demuestra que Django esté instalado.

**Casos pendientes.** Queryset de otro tenant, lista/detalle/create y relación
ajena; paginación None/vacía/orden repetido; imports/campos faltantes; usuario
custom y primera migración; slug concurrente/bulk; cache entre identidades y
tras actualización; profile ausente, signals omitidas y middleware reiterado;
atomic con rollback, carrito cambiado y pago aceptado con confirmación fallida;
N+1 del serializer, índices redundantes y lotes grandes. Ejecuciones por versión
real de Django/DRF y motor en T-14; tests documentales no bastan.

**Carga/impacto.** 735 líneas originales, referencias divididas bajo demanda,
tokens/latencia null. Architect conserva diseño; planner riesgos y tareas;
implementer código del consumidor; reviewer/qa/nemesis los veredictos existentes.
Ausencia parcial de Django, DRF, broker o herramientas se informa con su alcance,
sin crear paquetes en todos los proyectos ni inventar porcentajes/capacidades.
T-08/T-10/T-11/T-12/T-14/T-15 mantienen integración y validación pendientes.
