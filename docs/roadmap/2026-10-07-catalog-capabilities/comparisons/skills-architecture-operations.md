# Comparación de arquitectura, contratos y operaciones

Fichas S013 y S015–S020, revisión
`ef648e01899ba3e8dc6371642deaaf64b4477775`. Los siete cuerpos y sus consumidores
pertinentes se leyeron; ninguno tiene recursos locales adicionales. Son destinos
**propuestos**, sin integración de producción. T-08 resolverá el diseño conjunto.
El progreso se mantiene en [tasks.md](../tasks.md), T-03.

[architecture-reading-evidence.json](architecture-reading-evidence.json)
registra hashes, tamaños, rangos y fuentes técnicas. Incluye también el cuerpo
de S014, cuya evaluación quedó pendiente en ese checkpoint: tenía 35 recursos
locales aún no leídos. Esa lectura se completó después en la
[ficha Angular](skills-angular.md), con evidencia propia; el JSON anterior
conserva su alcance histórico. Los cuerpos o secciones de otras piezas usados como dependencia/caller
no incrementan el contador de skills evaluadas. Los adaptadores/generadores
operativos completos siguen en T-06. No se ejecutó código del corpus.

## S013 — Arquitectura por capas Android y Kotlin Multiplatform

**Identidad y lectura.** SHA-256
`20cbb9d7778462c549ccd32c830c0004fc7b92cfa009db99900d773373115f12`;
8.887 bytes/340 líneas, cuerpo completo; recursos locales 0 bytes/0 líneas.

**Contrato y valor.** Parte del proyecto y sus dependencias para decidir módulos,
inversión de dependencias, UseCases, repositorios y flujo dominio/datos/presentación.
Architect conserva límites y alternativas; implementer desarrolla módulos y
tests; qa comprueba compilación y comportamiento. Las secciones de mappers,
fuentes locales/remotas, Room/SQLDelight/Ktor y Koin/Hilt concretan ese diseño.
Conserva independencia del dominio, no filtrar DTOs/entities a UI, concurrencia
estructurada, repositorios enfocados, ausencia de ciclos y plugins de convención.

**Defectos y comparación.** El repositorio suspendido usa runCatching sin
distinguir cancelación: la [API de Kotlin](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html)
captura Throwable. S149 exige propagar CancellationException, por lo que los
ejemplos deben armonizarse y probar cancelación antes de copiarse. El UseCase
devuelve Result pero el ejemplo UI espera Try: son alternativas que necesitan
tipos coherentes. Separar tags con una barra pierde información si el dato
contiene el delimitador; convertir status mediante valueOf requiere tratar
valores desconocidos. Los ejemplos DI y Gradle son fragmentos sin fixture
compilada; versiones y wiring completo siguen sin validación ejecutada.

`agents/architect.md` P2–P5 ya exige módulos reales, alternativas y ADR;
`backend-practices/references/contracts-data.md` conserva límites de datos,
transacciones y fallos. `frontend-quality` cubre interacción, no arquitectura
KMP. Ninguno detalla módulos Kotlin, mappers, persistencia multiplataforma o DI.
La especialidad aporta valor aunque este repo no tenga una aplicación Android.

**Dependencias y consumidores.** S045 y S149 enlazan layering desde UI/async;
S217 lo selecciona por stack. R-0243aba303d6 lo incluye en el mapa Android;
R-591e7a1672e1/R-03ffcc8e6e9e son distribución. Gradle/Kotlin, SDKs, motores
locales y DI dependen del consumidor. Las skills vecinas no son recursos locales
precargados ni un paquete técnico obligatorio.

**Decisión/destino.** **Actualizar** como referencia opcional propuesta
`skills/kotlin-practices/references/layered-architecture.md`; la skill compartida
y su relación con S045/S149 se resolverán tras comparar esas piezas en T-08.
Conservar todos los criterios y alternativas de arriba, corrigiendo cancelación,
tipos y serialización. Reutilizar architect, gates y contratos de datos;
no imponer una clase UseCase vacía por cada llamada sin valorar la operación.

**Activación estática.** Literal: «Estructura módulos de esta app Android».
Paráfrasis: «Dónde colocamos repositorios y casos de uso en este KMP».
Negativo: «Comprueba el foco de un modal» → frontend-quality. No se ejecutó
selector, compilador, Gradle, Room/SQLDelight/Ktor ni DI.

**Coste, degradación e impacto.** Cargar mapa y referencia del motor/DI relevante;
tokens/latencia null. Sin SDK/build compatible, diseño y pruebas pendientes,
sin declarar compilación. Hash/lectura y API runCatching contrastados el
2026-10-07. T-10/T-11 deberán resolver callers y contenidos, T-14 fixtures de
tipos/cancelación/mappers y T-15 documentación, dependencias y exports ES/EN.

## S015 — Conectores que respetan la arquitectura del repositorio

**Identidad y lectura.** SHA-256
`00a0d01e234f213d343f0040bbebd56e042978768ce5bb7117776a75bd9547e8`;
2.664 bytes/121 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** Recibe API objetivo y patrón existente, decide superficie
mínima y produce configuración, transporte, mapeo, entrypoint, registro, pruebas
y docs coherentes. Architect conserva límites; implementer integra y qa verifica.
Inspeccionar conectores existentes antes de generar HTTP evita una segunda
arquitectura. Incluye autenticación, paginación, retries, límites y webhooks/polling.
El mínimo de dos ejemplos no puede bloquear un repo con uno o ninguno: distinguir
evidencia disponible de diseño nuevo justificado. Tampoco copiar un patrón obsoleto.

**Comparación propia.** `delivery-practices` «MCP como contrato de acceso»
separa herramientas/configuración/permisos y connection/health;
`backend-practices` cubre errores, datos, retries y atomicidad. El contrato de
`knowledge-services/backends/README.md` ya muestra una integración propia con
seis funciones, carga por tipo, routing previo y fallos explícitos. Estos métodos
no tienen una pauta general para completar wiring y comprobar equivalencia con
los conectores del consumidor. El contrato de seis funciones es específico de
knowledge-services, no una interfaz universal que deba imponerse a cualquier API.

**Dependencias y consumidores.** S212 deriva capacidades de producto a
integraciones; R-591e7a1672e1/R-03ffcc8e6e9e distribuyen la pieza.
R-6a2e152ec772 declara triggers manuales para construir una integración, no
ejecución nativa acreditada. Las referencias a métodos backend/MCP/GitHub son
continuaciones, sin SDK o ejecutor local. Contratos del proveedor requieren
consulta oficial y fixture del proyecto al implementar.

**Decisión/destino.** **Ampliar** delivery-practices con la referencia propuesta
`references/repository-connectors.md`. Conservar house style, comparación de
layout/schema/auth/errores/tests, alcance mínimo, capas y registro/discovery.
Enlazar MCP/backend y usar el patrón vigente del consumidor. La implementación
no implica conectar cuentas o ejecutar operaciones externas por inventario.

**Activación estática.** Literal: «Añade este proveedor como los existentes».
Paráfrasis: «Necesitamos otra integración sin crear un cliente paralelo».
Negativo: «Lista los MCP declarados» → work-context/project-pieces, sin construir
conector. No se ejecutaron estos triggers ni clientes externos.

**Coste, degradación e impacto.** 2.664 bytes/121 líneas; cargar la referencia
cuando se añada un conector. Tokens/latencia null. Sin patrón o API comprobada,
explicitar opciones/contrato pendiente, no copiar shapes como código completo.
Lectura y hashes comprobados; sin SDK instalado ni cuenta conectada.
T-08/T-10 definirán método, T-11 callers y T-12/T-14 configuración/fixtures reales;
T-15 actualizará dependencias, exports y docs ES/EN.

## S016 — Diseño de contratos REST

**Identidad y lectura.** SHA-256
`250e464413a13c0eb93cc73447b423df1f9aa8e4f80e5e68c41f895b2c33e352`;
13.224 bytes/524 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** A partir de recursos y consumidores decide métodos,
estados, errores, paginación, filtros, autorización, cuotas y versionado. Produce
contrato y ejemplos; architect decide compatibilidad, implementer construye,
documenter explica y qa prueba implementación. Aporta alternativas envelope/flat,
offset/cursor, campos dispersos, orden múltiple, versionado URL/header y ejemplos
Next.js, DRF y Go, con checklist de documentación y ausencia de detalles internos.

**Defectos y comparación.** Cuotas fijas, menos de 10.000 filas, dos versiones
y seis meses de retirada son políticas ilustrativas, no requisitos universales
ni rendimiento medido. Sunset anuncia una expectativa de retirada, no obliga
a responder 410 tras la fecha según [RFC 8594](https://datatracker.ietf.org/doc/html/rfc8594).
Un cursor base64 no aporta secreto ni autorización; estabilidad depende del orden,
filtros y política de datos mutables, no solo de elegir cursor. El ejemplo Next.js
no trata JSON malformado antes de safeParse aunque el contrato distingue ese error.
Las plantillas no prueban tenant/ownership, límites de body o wiring del servidor.

`backend-practices/references/contracts-data.md` ya exige orden total/desempate,
cursor ligado a filtros, allowlists, autorización de recurso/tenant, errores
redactados e idempotencia. `api-contract` «Flujo contract-first» y «Qué NO hace»
valida estructura y cambios acotados, no todo diseño REST. Delta útil: alternativas
y criterios de API visibles para consumidores. Añadir un campo no es garantía
universal de compatibilidad con clientes estrictos; ni el linter propio ni la tabla
de origen prueban todos los consumidores. Mantener explícito ese alcance.

**Dependencias y consumidores.** S022/S042 derivan contrato HTTP a esta guía;
S055 lo complementa con cambio contract-first; S176 lo usa para serving/modelos.
R-0243aba303d6 lo selecciona para FastAPI, R-6a2e152ec772 declara triggers y
R-591e7a1672e1/R-03ffcc8e6e9e distribuyen. Frameworks/validadores/limiter y
almacén dependen del proyecto; sin ejecutor local ni servicio MCP propio.

**Decisión/destino.** **Ampliar** backend-practices con la referencia propuesta
`references/http-contract-design.md`, reutilizando contracts-data y api-contract.
Conservar métodos/estados, alternativas de naming/envelope/paginación/filtros,
campos y auth, cuotas/reintentos, versión/migración y checklist. Adaptar convenciones
al contrato existente, sin envolver respuestas o renombrar URLs por gusto.
Los ejemplos por stack seguirán opcionales y necesitan fixture/versiones reales.

**Activación estática.** Literal: «Diseña endpoints y paginación de esta API».
Paráfrasis: «Qué contrato exponemos para errores y retirada de versiones».
Negativo: «Valida el YAML OpenAPI» → api-contract, sin confundir estructura con
comportamiento. No se ejecutaron selector, endpoint ni ejemplos de frameworks.

**Coste, degradación e impacto.** 13.224 bytes/524 líneas; mapa común y ejemplo
pertinente bajo demanda. Tokens/latencia null. Sin servidor/consumidores, publicar
diseño y compatibilidad pendiente. Lectura/hashes y contraste RFC; sin pruebas
de cargas, cuotas ni SDKs. T-08/T-10 definirán referencias; T-11 actualizará callers,
T-14 verificará malformed JSON, permisos, cursores y compatibilidad; T-15 docs/exports.

## S017 — Registro y recuperación de decisiones de arquitectura

**Identidad y lectura.** SHA-256
`263b20e81801aa5fa7e75eaec6c38345c0ac028ca0edbd67b1b9071c5fcbe11f`;
7.182 bytes/180 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** Captura una alternativa significativa o recupera el porqué
de una decisión; produce ADR, índice y enlace de sustitución. Conserva contexto,
decisión, alternativas/motivos, consecuencias positivas/negativas/riesgos, fecha
y participantes. Distingue propuesto/aceptado/retirado/sustituido y marca backfill
con fecha original. Evita trivialidades y cambios sin razón documentada.

**Comparación propia.** `knowledge-write.md` «Umbral», «Autoría, estado y revisión»
y «Contradicciones» ya define ADR, índice, trazabilidad, revisión/promoción y
enlace de obsolescencia. `templates/adr.md` contiene contexto/decisión/alternativas/
consecuencias; architect P5 lo escribe en `docs/knowledge/adr/` y enlaza diseño.
El método de origen propone otro árbol, numeración de cuatro dígitos y confirmaciones
para cada escritura. Duplicarlo fragmentaría recuperación y estados. La aceptación
de una decisión no debe confundirse con completar la revisión de su propuesta;
la autorización ya existente se conserva sin preguntar de nuevo por cada carpeta.
Delta útil: participantes explícitos y pauta de lectura por pregunta/motivo,
sin añadir un segundo índice ni promover automáticamente doctrina.

**Dependencias y consumidores.** S058/S059 remiten decisiones duraderas tras
deliberación; S176 lo usa para datos/modelos/rollout. R-591e7a1672e1/R-03ffcc8e6e9e
son distribución. Las menciones a planner/reviewer describen integración deseada,
no un hook ejecutado. Sin scripts/MCP locales. Estados originales necesitan mapa
al vocabulario propio y procedencia, no traducción ciega de frontmatter.

**Decisión/destino.** **Consolidar** en knowledge-write/knowledge-check y la
plantilla ADR existente. Conservar todos los campos/lifecycle útiles, backfill,
sustitución e índice; añadir participantes cuando aporten información real.
Architect mantiene diseño/ADR y knowledge-curator las responsabilidades de gobierno
que le corresponden. La lectura responde al porqué con estado, fuente y fecha,
sin crear una entrada porque una búsqueda no encontró nada.

**Activación estática.** Literal: «Registra por qué elegimos este almacén».
Paráfrasis: «Por qué se descartó esa alternativa de arquitectura».
Negativo: «Guarda el resultado de cada comando» → journal/observabilidad pertinente,
sin ADR por cada episodio. No se ejecutó recuperación nueva ni escritura de memoria.

**Coste, degradación e impacto.** 7.182 bytes/180 líneas; reutilizar fragmentos
shared y leer ADRs pertinentes. Tokens/latencia null. Sin índice/entrada, indicar
ausencia; crear propuesta solo dentro del trabajo autorizado y con fuente.
Lectura/hash/plantilla comprobados, sin promoción de memoria. T-07/T-08 decidirán
el delta; T-10/T-11 actualizarán referencias y T-14/T-15 validarán gobierno/docs/exports.

## S018 — Artículos y guías con voz sustentada en fuentes

**Identidad y lectura.** SHA-256
`4aa61709450a2148ef4036896d870da748e93ad68528bb7679b74f3597ffb021`;
2.926 bytes/80 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** A partir de audiencia, propósito, notas/fuentes y estilo
solicitado produce artículo, ensayo, tutorial o newsletter revisado. Aporta hilo
argumental, función de cada sección, evidencia antes de adjetivos, eliminación
de relleno/credibilidad inventada y formato adecuado al medio. El autor conserva
el borrador; documenter mantiene documentación técnica cuando ese es el artefacto.
Redactar no autoriza publicar ni enviar a terceros.

**Comparación propia.** `agent-kits/shared/docs-style.md` ya exige voz activa,
ejemplos reales, párrafos con un concepto y ausencia de adjetivos vacíos. Es una
pauta de documentación técnica con criterios citables, no un método de ensayo,
newsletter o adaptación a una voz aportada. S029 y su recurso R-37a37583ac4d
definen el perfil reutilizable; se leyeron como contrato necesario para S018,
no como evaluación completa de toda la especialidad de estilo. Sus defaults de
autor/marca específicos no deben imponerse al consumidor. Usar fuentes y tono
solicitados, sin asumir que una voz cortante sirve a toda audiencia.

**Dependencias y consumidores.** S256 lo presenta como alternativa local para
redacción, con límite frente a release notes. R-591e7a1672e1 lo distribuye y
R-03ffcc8e6e9e lo excluye de un perfil de ingeniería; esa exclusión no elimina
su utilidad opcional. S029 es dueño del perfil en origen; el destino conjunto se
resolverá al completar su ficha. Sin ejecutor/MCP local obligatorio ni publicación.

**Decisión/destino.** **Actualizar** como capacidad opcional propuesta
`skills/long-form-writing/`, con referencia de estructura por medio y enlace al
dueño único del perfil que decida T-08. Conservar reglas, proceso, ensayo/tutorial/
newsletter y gate de fuentes/voz/novedad/formato. Reutilizar docs-style para
documentación técnica, sin análisis de voz repetido o persistencia personal automática.

**Activación estática.** Literal: «Escribe un artículo con estas notas y ejemplos
de tono». Paráfrasis: «Convierte esta investigación en una newsletter coherente».
Negativo: «Sincroniza el changelog desde tareas cerradas» → changelog-sync.
No se ejecutó una evaluación de estilo ni se publicó contenido.

**Coste, degradación e impacto.** 2.926 bytes/80 líneas; perfil confirmado y
referencia del medio bajo demanda. Tokens/latencia null. Sin ejemplos suficientes,
explicitar límites y usar tono acordado; no inventar hechos o aprobación de estilo.
Lectura/hash y contrato de perfil comprobados; sin benchmark editorial.
T-08/T-10 resolverán esa dependencia, T-11 callers, T-14 escenarios y T-15 docs/exports.

## S019 — Auditoría del estado de automatizaciones

**Identidad y lectura.** SHA-256
`71aa878fd06ef02f0c8ca50eaaee0ec45995981d769d8701806b9b83ca8a2f2c`;
4.167 bytes/143 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** Inventaría jobs, CI, hooks, conectores, MCP y wrappers;
contrasta evidencia y propone conservar/consolidar/retirar/arreglar primero.
Produce tabla de estado, fuente, prueba y siguiente acción, antes de reescribir.
El auditor conserva el diagnóstico; los dueños de cada sistema ejecutan cambios
autorizados y qa comprueba recuperación. Prioriza fallo real frente a redundancia
de escaso valor, con firma exacta y desconocidos explícitos.

**Comparación propia.** `commands/doctor.md` diagnostica instalación, configs,
hooks y capacidades opt-in del plugin, con comprobación acotada health/verify y
sin ejecutar remedios. `capability-check.md`/PROJECT-EXTENSIONS separan declaración
y disponibilidad; capability-audit compara semántica de piezas, no jobs en vivo.
Delta: ampliar el alcance operativo a workflows del consumidor y su evidencia
reciente, con dueño y prioridades. Configurado, autenticado y verificado son
dimensiones distintas; deshabilitado por elección no significa roto. Ni registro
del hook ni health demuestra despacho efectivo: T-02/T-09 conservan esa prueba.

**Dependencias y consumidores.** R-591e7a1672e1 distribuye; R-03ffcc8e6e9e
excluye un perfil específico. Las cabeceras de las dependencias de superficie,
conocimiento, GitHub, investigación y verificación se leyeron para sus contratos,
sin dar por evaluados sus cuerpos completos. S091 está ligado a una aplicación
consumidora concreta, no un detector de coste universal. Logs/CLI/API necesitan
acceso real y redacción; no leer secretos o repos adyacentes por conveniencia.

**Decisión/destino.** **Ampliar** mediante la capacidad propuesta
`skills/automation-audit/`, que reutiliza doctor/project-pieces y los métodos
operativos que resulten de T-06. Conservar grupos de superficie, estados con
fuente/fecha/alcance, firma de fallo, evidencia y recomendaciones con prioridad.
No crear otro health checker paralelo ni afirmar «live» por configuración.
El panel podrá consumir evidencia explícita, sin vender un snapshot como servicio.

**Activación estática.** Literal: «Qué jobs y hooks están funcionando o rotos».
Paráfrasis: «Tenemos varias automatizaciones; localiza fallos y solapes».
Negativo: «Valora si dos skills duplican un método» → capability-audit.
No se consultaron cuentas, CI remoto, comunicaciones ni jobs del consumidor.

**Coste, degradación e impacto.** 4.167 bytes/143 líneas; metadatos primero,
prueba acotada solo para afirmaciones relevantes. Tokens/latencia null.
Sin acceso/logs recientes, estado desconocido con próxima comprobación; no
autenticar ni arreglar por inventario. Lectura/hash y contratos propios comprobados.
T-06/T-08 decidirán integración; T-12/T-13 recursos/panel, T-14 evidencia real
y T-15 docs/exports. La revisión de configuraciones no autoriza modificaciones.

## S020 — Operación autónoma con capacidades del runtime

**Identidad y lectura.** SHA-256
`74afde3fa6e8423bdbf43f53b24c7b4a8b441648a1ad8f23953dc6eba3378409`;
12.864 bytes/271 líneas, cuerpo completo; recursos locales 0/0.

**Contrato y valor.** Diseña memoria, programación, ejecución CLI/CI, control
de ordenador y cola persistente como capacidades separadas. Produce setup y
flujo acotado a una petición de autonomía, no un runtime empaquetado always-on.
Architect define límites; operaciones conserva runner/schedules; cada rol su
artefacto y validación. Preserva autorización de acciones/destinos, dry-run,
credenciales privadas, revisión de paquetes e integración opcional de computer use.

**Comparación y defectos.** S010 ya aporta persistencia/scheduler/estado;
dev-cycle conserva tasks.md y knowledge-write separa journal/propuestas/doctrina.
Una cola Markdown no demuestra claim atómico, exclusión, reintento, cancelación
o recuperación tras caída. No usarla como cola multi-worker sin ese contrato.
El ejemplo de aprobar PR si CI está verde no sustituye revisión ni autorización
de publicación. Enviar comentarios, leer correo privado o controlar otras apps
requiere capacidad efectiva y alcance autorizado, no solo configurar un servidor.

La [documentación actual de tareas programadas](https://code.claude.com/docs/en/scheduled-tasks)
distingue /loop ligado a sesión de alternativas Cloud/Desktop. /loop tiene
expiración y restauración condicionada al reanudar; esa restauración no ejecuta
tareas durante una sesión cerrada. Seleccionar mecanismo por versión y objetivo,
sin prometer que un prompt provisiona un daemon o que solo existe cron externo.
La [memoria automática de Claude](https://code.claude.com/docs/en/memory) carga
un índice acotado y lee detalles bajo demanda; no todos los archivos al inicio
ni la misma memoria en cualquier subagente/máquina. Ese contrato no es universal
en Codex/OpenCode y no reemplaza la recuperación dirigida del plugin.

**Dependencias y memoria.** S002 lo enlaza para setup; distribución en
R-591e7a1672e1, exclusión específica en R-03ffcc8e6e9e. La
[metadata oficial del servidor de referencia](https://registry.npmjs.org/@modelcontextprotocol%2fserver-memory/2026.8.31)
confirma versión y bin; HTTP 200/hash registrados, sin instalarlo. Su
[README oficial](https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/memory/README.md)
documenta entidades/relaciones/observaciones, consultas, lectura de grafo completo,
JSONL y configuración Windows. Esto acredita documentación, no tools disponibles
en esta sesión, aislamiento de proyectos, procedencia ni calidad del conocimiento.
La proyección propia knowledge-services exige routing previo y estado/evidencia
para lectura; su contrato también declara límites de reconstrucción histórica,
que T-07 debe comparar, sin asumir memoria propia perfecta ni adoptar un grafo
sin gobierno. Retrieval/eficacia siguen pendientes de experimentos de fase 4.

**Decisión/destino.** **Consolidar** con S010 en la referencia propuesta
`skills/agent-system-quality/references/persistent-workflows.md`, con referencias
de scheduling/memoria/control de ordenador por capacidad real bajo demanda.
Conservar los cinco componentes, persistencia de cola, límites, ejemplos de
review/research/preparación y verificación de ejecuciones. Reutilizar ledger y
memoria gobernada; no montar una cola competidora para tareas del roadmap.
Los candidatos MCP solo se adoptarán tras comparación T-07 y diseño T-08;
no copiar la inicialización de identidades/contactos como efecto automático.

**Activación estática.** Literal: «Diseña un flujo que vigile esto cada día».
Paráfrasis: «Cómo combinamos cola, memoria y ejecución programada con permisos».
Negativo: «Continúa esta tarea del ledger» → dev-cycle, sin crear schedules.
No se ejecutó /loop, prompts, CI, computer use ni creación de entidades.

**Coste, degradación e impacto.** 12.864 bytes/271 líneas; referencias de las
capacidades elegidas, tokens/latencia null. Sin scheduler, memoria o control
de ordenador verificados, declarar disponibles/pedidos/pendientes por separado
y mantener operación manual. Lectura/hash, metadata y docs oficiales contrastados
el 2026-10-07, sin instalar servicios ni modificar configuración. T-07/T-08 fijarán
diseño; T-09/T-12 verificarán runtime y ejecución, T-14 fallos/recuperación y
T-15 distribución/docs. Configuración válida no demuestra reemplazo de otro framework.

## Estado de este bloque

Siete fichas completas, ninguna integración funcional nueva. S014 permanece
fuera del contador de evaluadas: cuerpo leído y recursos inventariados, sin
lectura completa de sus 35 referencias ni veredicto. No se retira por tamaño
o stack. Los destinos serán revalidados con consumidores operativos y el resto
del catálogo antes de modificar producción.
