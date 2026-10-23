# Comparación de transporte, configuración de red y continuidad de sesión

Fichas S033–S035 de la revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Se leyeron tres cuerpos completos
y los nueve recursos locales de S035: 33.961 bytes/518 líneas de cuerpos y
49.233 bytes/1.310 líneas de recursos. [operations-reading-evidence.json](operations-reading-evidence.json)
registra hashes, rangos, consumidores y contraste documental. Las lecturas
parciales de dependencias no cuentan como evaluación completa de esas piezas.
El avance de T-03 se conserva en [tasks.md](../tasks.md).

Los destinos son **propuestas para T-08**, sin altas de producción en este bloque.
No se ejecutaron scripts del corpus, comandos de dispositivos, negociaciones,
consultas autenticadas, imports, borrados ni hooks nativos. Tokens y latencia
son null. Las comprobaciones documentales acreditan integridad de la evidencia,
no eficacia funcional. La auditoría integral de memoria sigue pendiente en T-07
y su benchmark en la fase posterior.

## S033 — Cartera de transportistas, licitación y seguimiento

**Identidad y lectura.** SHA-256
`e325d73fd0078a101e826a84178c87aeeb80700d037faf45cda8e9ba9e53b27e`;
23.645 bytes/206 líneas. No hay recursos locales en su directorio.

**Contrato y valor.** Especialidad de transporte de carga completa, carga
parcial e intermodal. Produce una evaluación de proveedores, escenarios de
adjudicación por ruta, guía de asignación y scorecard con acciones. Conserva:

- Alta y revisión recurrente de autoridad, seguros, historial y referencias,
  con entidad, jurisdicción, fecha y fuente de cada comprobación.
- Desglose de coste: linehaul, índice/tabla/base/lag del combustible, mínimos,
  servicios adicionales y coste total esperado; sensibilidad a volumen y fuel.
- Datos por ruta para RFP: origen/destino, frecuencia, equipo, ventanas,
  capacidad, servicio, condiciones y ponderaciones; comparación incumbente/nuevo.
- Recogida y entrega puntuales por separado; aceptación de tenders;
  frecuencia y severidad de reclamaciones; exactitud de facturas; tiempos de
  aceptación y recogida con definiciones y ventanas reproducibles.
- Primario y alternativas, riesgo de concentración, capacidad confirmada,
  transición por oleadas, prueba inicial y revisión antes de un compromiso largo.
- Revisiones periódicas, negociación basada en datos, forecast compartido y
  planes correctivos con responsables, plazos y evidencias de cierre.
- Escenarios de huracán, intermediación no autorizada, cambios de volumen,
  dificultades financieras, adquisición, tablas fuel y detención en instalaciones.
  Son hipótesis de trabajo con playbook local, no pruebas automáticas de culpa.
- Escalamiento por pérdida de habilitación, fallos de servicio, concentración,
  desviaciones de coste y cadena de intermediación, con política explícita.

**Correcciones necesarias.** El cuerpo atribuye 5 millones de dólares de seguro
a enseres domésticos. La [tabla oficial de FMCSA](https://www.fmcsa.dot.gov/registration/insurance-filing-requirements)
consultada distingue responsabilidad civil, seguro de carga, tipo de entidad,
mercancía y peso. Para la fila de enseres domésticos con GVWR ≥10.001 libras
indica 750.000 de responsabilidad civil y 5.000 de carga; los 5 millones
aparecen en otras categorías. No trasladar la cifra errónea ni convertir una
política empresarial más exigente en mínimo legal universal. Verificar la
regulación aplicable al caso antes de emitir una conclusión de cumplimiento.

El [aviso oficial de SMS](https://ai.fmcsa.dot.gov/sms) distingue sus indicadores
de una calificación federal de seguridad y limita ciertos datos públicos.
No tratar un percentil, ausencia de rating o información no disponible como
prohibición, autorización o calificación global. Consultar autoridad/seguros y
rating en sus fuentes correspondientes; conservar fecha y límites de acceso.

Los precios de servicios adicionales, descuentos, costes de onboarding,
duraciones de ciclo y ratios de mercado son ejemplos sin medición vigente.
Los targets necesitan contrato, tamaño de muestra, denominador, exclusiones,
zona horaria y comparabilidad del benchmark. Aceptación baja no demuestra por
sí sola precio bajo; facturas discrepantes o quejas no prueban dolo o insolvencia.
Las acciones urgentes por incumplimiento legal deben diferenciarse del ciclo
correctivo de servicio: no esperar 60 días para tratar una autoridad revocada.

Las ponderaciones de coste/servicio/capacidad/fit suman entre 90 y 115 % según
los extremos sugeridos; elegir pesos concretos que sumen 100 %. El mix de
activos/brokers/especialidades suma entre 85 y 115 % y puede mezclar ejes
solapados: definir categorías exclusivas o ejes separados. El límite propuesto
del 40 % por ruta contradice un ejemplo que incrementa asignación del 60 al
75 % y una alarma del 50 %. Una política local debe fijar precedencia, límites
y excepciones; los ejemplos de comunicación no pueden saltarse esa política.

**Comparación propia.** `research-first` ya exige fuentes y comparación;
`api-contract` acota un contrato de API. Ninguno contiene negociación de freight,
FSC, scorecards de transportistas o routing guides. `delivery-practices` trata
entrega de software; compartir la palabra entrega no acredita este dominio.
`capability-check` permite seleccionar una especialidad sin imponerla al ciclo.
La guía fuente menciona TMS y plataformas comerciales, pero no trae un adapter
ni acredita acceso real a sus datos, mensajes o cambios de asignación.

**Decisión y destinos.** **Conservar y actualizar**, como especialidad opcional
propuesta `skills/freight-operations/SKILL.md`. Destinos:
`references/portfolio-procurement.md` para costes/RFP/scorecards/asignación,
`references/carrier-vetting.md` para diligencia y fuentes jurisdiccionales,
y `references/carrier-response.md` para excepciones, corrección y escalamiento.
Su organización final se reconciliará con las demás piezas logísticas en T-08.
El informe separa propuesta de acción y acción realmente aplicada por un tool
disponible. Una fuente de datos o MCP se selecciona por proyecto; no se incluye
otra integración comercial por defecto ni se inventa experiencia profesional.
El frontmatter declara Apache-2.0; T-15 deberá resolver atribución/licencia según
los avisos aplicables antes de adaptar contenido, sin confundir nombre propio
con eliminación de obligaciones legales.

**Activación y validación.** Escenarios estáticos: positivo «evalúa ofertas de
transportistas para estas rutas con FSC»; paráfrasis «reparte volumen entre
incumbentes y nuevos según coste y servicio»; negativo «diseña un pipeline de
deployment» → `delivery-practices`. No son evals ejecutadas. T-10/T-14 deberán
probar pesos, categorías, concentración, ventanas, dato desconocido, fuentes
caducadas y requisitos dependientes de jurisdicción; no fabricar métricas reales.
Sin TMS, trabajar sobre datos aportados y marcar acciones como propuestas.

**Impacto.** El manifiesto fuente la agrupa en logística y otro target la excluye
por especialidad; esa clasificación no demuestra inutilidad ni soporte universal.
T-08 decide dueño junto al resto del dominio; T-10 añade referencias/triggers;
T-11 revisa callers; T-12 solo implementa conectores si hay contrato y alcance
autorizado; T-13 muestra disponibilidad declarada separada de ejecución;
T-14 valida; T-15 mantiene manifiestos, exports y docs ES/EN.

## S034 — Lectura y revisión de configuración IOS/IOS-XE

**Identidad y lectura.** SHA-256
`85b6a97574cc236d4a9336b1c74b42aaf4386338417e787cbed0c88677bf1179`;
5.305 bytes/164 líneas. Sin recursos locales ejecutables.

**Contrato y valor.** Método para preparar/revisar un cambio y recoger evidencia
pertinente de un router o switch. Conserva plataforma/versión, interfaces,
configuración actual, acceso de gestión, rollback y ventana antes de aplicar.
Secuencia: baseline de lectura, candidato concreto, riesgo de perder gestión,
cambio mínimo, verificación de comportamiento y persistencia intencional.

Los modos exec/global/interface/routing/line evitan mezclar comandos y contexto.
Distinguir running de startup y comprobar antes de guardar. El catálogo de
show cubre inventario/versión, CPU/memoria/logs, VTY, interfaces, BGP, VLAN,
MAC, spanning tree, rutas, protocolos, ACL, route-map y prefix-list. Elegir solo
la evidencia necesaria; salida de lectura también puede exponer secretos,
clientes y topología. Redactarla antes de enviarla a sistemas externos.

Conservar máscara wildcard frente a máscara de subred, ejemplos /32, /30,
/24 y /16, dirección in/out, permits de gestión y servicios necesarios,
hit counters y rollback con canal fuera de banda. La [guía IOS XE 17.x](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/sec-vpn/b-security-vpn/m_sec-access-list-ov-0.html)
confirma la interpretación de bits wildcard, incluyendo máscaras no contiguas,
deny implícito y observación mediante deny explícito. No generalizar todas las
opciones a cada plataforma. La misma guía advierte del orden al crear/aplicar
una ACL: una transición parcial puede perder acceso. Logging debe ajustarse
a carga y observabilidad del equipo; no añadir log indiscriminadamente.

Conservar descripción de interfaces, modo explícito de puerto, VLAN nativa
documentada, direccionamiento del peer y revisión de routing. Estado link-up
no demuestra forwarding. Verificar el cambio con rutas/vecinos/contadores y
fuente de prueba pertinente; un ping genérico no acredita la política de ACL.
No desmontar ACL, autenticación o route policies para diagnosticar.

**Límites.** Los snippets no son configuración lista para producción. El ejemplo
de trunk usa VLAN nativa 999 y allowed list 10/20/30: documentar su intención
y validar tráfico etiquetado/no etiquetado y ambos extremos según plataforma.
No declararlo defecto universal ni copiarlo sin contexto. Algunas órdenes show
son propias de ciertas plataformas; versión y feature set gobiernan su uso.
La lista no implementa parser, validador ni conexión SSH; no demuestra que un
device haya aceptado el candidato o que rollback/persistencia hayan funcionado.

**Comparación propia y callers.** `architect` diseña software con artefactos y
alcance de escritura definidos; no configura dispositivos por esa identidad.
`delivery-practices` aporta evidencia de entrega, no sintaxis IOS. En el corpus,
el arquitecto de red, BGP y automatización SSH apuntan a S034; esta apunta a
revisión de configuración, diagnóstico y salud de interfaces. Los fragmentos
leídos distinguen revisión del candidato, síntomas físicos y diagnóstico.
Sus encabezados no acreditan equivalencia completa: esas piezas se evaluarán
por cuerpo y recursos en T-03/T-04 antes de consolidar responsabilidades.

**Decisión y destinos.** **Conservar y ampliar**, mediante una especialidad
opcional propuesta `skills/network-operations/SKILL.md` y
`references/ios-review.md`. Distribuir modos, recogida, wildcard/ACL,
interfaces y verificación como secciones de esa referencia, sin repetirlas
en cada agente. Las otras referencias de red se decidirán tras leer sus cuerpos.
Seleccionar la guía por dominio/plataforma en el flujo existente; agentes
especializados aportan evidencia sin asumir la aprobación o los gates de fase.
Para ejecutar, exigir tool realmente disponible, inventario concreto y alcance
del usuario. Sin acceso al equipo, el resultado es revisión estática y lista
de verificaciones pendientes. No añadir Netmiko, SSH o cuentas como requisito
global del plugin. Windows/Claude/Codex/OpenCode comparten método, no una
presunción de shell, credenciales o comandos disponibles.

**Activación y validación.** Escenarios estáticos: positivo «revisa esta ACL IOS
antes de aplicarla»; paráfrasis «prepara baseline y comprobaciones de este
cambio en un switch»; negativo «aplica una migración SQL» → práctica de stack
y entrega correspondiente. Pendientes en T-10/T-14: fixtures de máscara/dirección,
referencias inexistentes, gestión que se pierde durante transición, plataforma
desconocida, filtros de lectura y configuración con secretos. Prueba de device
solo con entorno autorizado: parser válido y CLI aceptada no equivalen a éxito.

**Impacto.** T-08 resuelve solapes; T-10 incorpora referencia/triggers opcionales;
T-11 actualiza los callers de red tras su revisión; T-12 declara herramientas
opcionales sin ejecutarlas al inventariar; T-13 muestra soporte y límites;
T-14 comprueba escenarios reales y estáticos por separado; T-15 limpia nombres,
dependencias, módulos, exports y documentación. Sin alias vacíos al consolidar.

## S035 — Resumen reanudable y continuidad entre proyectos

**Identidad y lectura.** SHA-256
`4759d9f4959fbec9afc7bc4b06c33d5644fb059e4d74a6c94200d29112b71bf5`;
5.011 bytes/148 líneas. Sus nueve recursos se leyeron completos: 49.233
bytes/1.310 líneas. Son scripts Node y un hook diseñado para Claude Code;
no se ejecutaron ni se instalaron en perfiles personales.

**Contrato y valor.** Distingue registro de proyecto, guardado de sesión,
resumen completo, snapshot corto, cartera, retirada y migración. El resumen
guarda objetivo, punto donde quedó el trabajo, siguientes pasos ordenados,
decisiones con razones y bloqueos. JSON sería canónico y Markdown su vista.
La detección inicial de stack/repo/objetivo es un borrador; no reemplaza lo que
confirme el proyecto. Conservar estas operaciones y campos útiles al integrar,
sin tomar cada decisión conversacional como doctrina curada.

**Defectos concretos de los recursos.**

1. Un archivo personal de sesión actual se comparte entre proyectos. Guardar
   toma su sessionId sin comprobar projectPath; dos sesiones pueden atribuir
   datos al ID de otro proyecto. La alarma de sesión no guardada también
   necesita aislamiento por proyecto, runtime y sesión, no solo último ID.
2. Lectura JSON corrupta se convierte en ausencia y registro vacío. Una escritura
   posterior puede reemplazar un registro dañado; diferenciar missing, invalid,
   forbidden y unavailable. Validar esquema/tipos/tamaños y ofrecer recuperación
   con evidencia, sin reset implícito. Un nombre sin caracteres ASCII puede
   producir un nombre de directorio vacío; validar identidad separada del nombre visible.
3. JSON, Markdown y registro se escriben directamente en pasos separados, sin
   transacción, lock o recuperación conjunta. Repetir init sobre la misma ruta
   puede reiniciar sesiones. La proyección a memoria nativa puede fallar y aun
   así dejar un mensaje general de guardado exitoso: reportar cada resultado.
4. contextDir leído del registro se resuelve sin comprobar confinamiento.
   La retirada hace rm recursivo sobre esa ruta: un registro manipulado podría
   apuntar fuera del almacén. Nombres parciales eligen el primer match;
   números dependen del orden de la cartera. Usar ID estable y rechazar ambigüedad,
   resolver root/case/enlaces/worktrees según plataforma antes de toda escritura.
5. La retirada borra registro/contexto, pero no los archivos de memoria nativa
   previamente exportados ni el marcador global de sesión. No anunciar olvido
   total sin enumerar copias gestionadas y verificar la revocación de cada una.
6. Lecturas stdin/JSON/historial y campos inyectados no tienen límite de bytes.
   La cartera puede abrir todos los contextos antes de mostrar tres. Un número
   de líneas no limita tokens ni tamaño: aplicar presupuesto de lectura y salida,
   alcance del proyecto seleccionado, paginación y aviso de resultado parcial.
7. La migración interpreta Markdown con regex de títulos y bullets: CRLF y
   listas numeradas requieren fixtures. No respalda el CONTEXT.md original antes
   de sobrescribirlo, aunque promete conservar originales. No aceptar campos
   no parseados como vacíos y declarar migración completa. Hace falta plan estable,
   backup de todos los originales, verificación y recuperación de aplicación parcial.
8. Cálculo Git por fecha y HEAD~N puede diferir en merges, shallow clones o
   historia insuficiente; además omite cambios sin commit. Separar baseline SHA,
   commits, diff y working tree. Missing Git, timeout y cero cambios son estados
   distintos. Cada subprocess tiene 3 s, pero no hay un presupuesto agregado.
9. Detección de stack/objetivo es heurística; no garantiza parser de todos los
   manifiestos. URLs de remotes pueden contener credenciales. Render Markdown
   sin escape rompe tablas/frontmatter con pipes/newlines. Redactar datos y
   conservar origen/certeza antes de persistir o presentar.
10. Rutas fijas bajo el home de Claude no resuelven bundles versionados. PWD
    puede ser ajeno al cwd real; el encoding que solo sustituye barras Unix no
    acredita rutas de memoria nativa en Windows. El script resume imprime una
    sugerencia de cd: no cambia el directorio de la sesión o shell del usuario.

El hook inyecta el cuerpo completo de la skill y repite el miniestado, con
imperativos para mostrarlo como primer mensaje. No trasladar esos imperativos
desde datos históricos ni el supuesto coste de cien tokens. La salida usa
additionalContext en primer nivel; la [referencia oficial de hooks](https://code.claude.com/docs/en/hooks#sessionstart)
documenta el JSON con hookSpecificOutput/hookEventName y contexto anidado.
Esto es una discrepancia estática de contrato, no una prueba de dispatch o
de salida ignorada en una versión instalada. El contexto no debe sustituir
la petición actual ni pedir reautorización rutinaria de trabajo ya autorizado.
La skill anuncia comandos y variantes de mayúsculas, pero los scripts locales
no acreditan su registro en el cargador. T-11 deberá resolver invocaciones
propias y verificar sus formas soportadas; no conservar aliases por apariencia.

**Comparación propia.** `progress-report.py` deriva progreso de tasks.md y
`knowledge-check` consulta por contexto/ID, distinguiendo aceptada, propuesta y
obsoleta. `knowledge-write` gobierna incorporación; `knowledge-services` proyecta
approved mediante adapters, sin convertir un resumen operativo en conocimiento
aprobado. El journal ya separa capture-end y replay, con envelope/outbox,
presupuesto y cerrojo; `outbox.py` aporta temporal/replace y reporte de durabilidad.
Las secciones leídas de journal guardan primero una entrada y permiten resumen
IA opt-in, y latest presenta decisiones/pendientes como citas, no instrucciones.

`session-context.sh` ya reúne índice, progreso, últimas entradas y aciertos del
área, con salida recortada y JSON anidado. Su presupuesto de replay no acota
por sí solo toda la ejecución: las consultas de memoria tienen timeouts propios,
hay lecturas completas de stdin y búsquedas de bundle. T-09/T-14 deben revisar
tiempo agregado, I/O y dispatch nativo, además de comentarios históricos que
atribuyen límites o soporte sin prueba de la versión actual. Este bloque no
declara ya resueltos esos gaps propios. Las correspondencias leídas son parciales
de los módulos grandes, no auditoría completa de journal/backends/seguridad.

**Decisión.** **Consolidar y actualizar** la continuidad operativa sobre ledger,
journal y lectores compartidos; no incorporar el almacén personal paralelo.
Añadir una vista reanudable derivada que conserve objetivo/leftOff/nextSteps/
decisiones/blockers, referencias de iniciativa/tarea, baseline y evidencia de
sesión. Si faltan campos operativos, su captura tendrá esquema explícito y dueño
en journal, separado de progreso canónico y memoria aprobada. La actualización
debe distinguir campo omitido de objetivo explícitamente vaciado:
el guardado fuente usa un chequeo truthy que impide limpiar el objetivo.
La referencia propuesta `skills/agent-system-quality/references/persistent-workflows.md`, ya
planteada en S010/S020/S021, sigue sin existir en producción; reconciliarla en
T-08, sin presentar el destino propuesto como cobertura entregada.

| Recurso leído | Función útil y destino propio propuesto |
|---|---|
| R-fa587407c2cd · 143 líneas | Detección inicial: metadata de contexto y captura operativa; confirmar solo datos realmente necesarios, sin registro obligatorio paralelo |
| R-2fa11499e8fa · 210 líneas | Guardado: journal con esquema, identidad por proyecto/runtime/sesión, idempotencia y recuperación; campos adicionales bajo el dueño existente |
| R-5324d275a305 · 36 líneas | Reanudación: vista derivada compartida de ledger+journal, selección explícita de proyecto/iniciativa y raíz comprobada antes de actuar |
| R-d41a4d65532b · 24 líneas | Snapshot: la misma vista resumida, lectura acotada y sin replicar fuente de verdad |
| R-d24529acc80a · 40 líneas | Cartera: ampliar proyección roadmap/panel, filtrada por ámbito autorizado y paginada; no escanear por defecto todos los proyectos personales |
| R-2681f04a6297 · 44 líneas | Retirada: operación explícita por ID con plan de copias gestionadas, confinamiento y revocación comprobada; no borrar memoria curada por un nombre ambiguo |
| R-cb068a1f3ada · 202 líneas | Migración: importer opt-in solo si existen datos reales de ese formato; plan reproducible, backup íntegro, validación de pérdida y recuperación, sin alias vacío permanente |
| R-223ef62fb315 · 387 líneas | Helpers: reutilizar redacción, guards, lectura con presupuesto, outbox y contratos portables propios; normalización/escape/identidad se resuelven una vez |
| R-ff1e4ba0b647 · 224 líneas | Inicio: ampliar compositor de contexto y adapters existentes con vista compacta y timeout agregado; sin prompts completos, primer mensaje obligatorio ni registro global de sesión |

Una proyección a memoria personal del runtime, si T-07 demuestra utilidad,
será opt-in, versionada y verificada por formato/ruta/plataforma. Necesita
manifiesto de copias/hash/propiedad y revocación; no escribir automáticamente
todo el historial en el home. Conservar estado operativo privado separado de
approved. Cambios de objetivo se respaldan en petición/evidencia actual;
antigüedad indica fecha, no vigencia semántica ni tarea finalizada. Sin hook,
la misma vista debe estar disponible bajo demanda; sin historial, mostrar
ausencia y seguir con la tarea autorizada. No registrar MCP ni servicios extra.

**Activación y validación.** Escenarios estáticos: positivo «retoma esta iniciativa
en otra sesión con lo que quedó pendiente»; paráfrasis «guarda un resumen con
siguientes pasos y bloqueos»; negativo «acepta esta decisión como doctrina» →
Knowledge Gate. T-10/T-12/T-14 deberán probar dos proyectos concurrentes,
sessionId repetido entre runtimes, corrupción/schema, nombres Unicode y ambiguos,
root/enlaces fuera de alcance, init repetido, escrituras interrumpidas, proyección
parcial, retirada de copias, CRLF/listas/backup, historial grande, Git shallow/
merge/dirty/timeout y redacción. Comparar la retoma con el mismo objetivo y
evidencia, sin usar metadatos de cartera como autorización de acceso.

**Impacto y carga.** T-07 compara memoria y recuperación integral; T-08 fija
esquema/dueños y evita fuentes duplicadas; T-09 valida hooks de los tres runtimes;
T-10 incorpora método/activación; T-11 revisa comandos y roles; T-12 implementa
vista/import/proyección solo dentro del contrato decidido; T-13 presenta origen,
scope, estado de cola y copias sin credenciales; T-14 prueba aislamiento,
presupuesto y recuperación; T-15 actualiza guías ES/EN, manifiestos y exports.
Los 1.310 renglones de recursos no se copian al brief ni justifican otro framework.
No hay medición compatible de tokens, latencia o utilidad recuperada en este bloque.
