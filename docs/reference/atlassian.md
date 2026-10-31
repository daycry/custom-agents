> Referencia avanzada. Empieza por el [manual explicado paso a paso](../CUSTOMIZATION.md). Este capítulo conserva contratos de implementación y configuración.

# 3. Atlassian: Jira y Confluence

Este capítulo desarrolla una configuración de proyecto con los módulos opcionales
`jira` y `confluence`. Los workflows del core siguen siendo los del capítulo 2.
La integración añade proyecciones externas; no cambia quién aprueba el alcance,
quién revisa el código o quién verifica las pruebas.

## Contrato y preparación

El servidor oficial Rovo MCP para Cloud tiene disponibilidad dinámica de tools:
la sesión puede exponer operaciones directamente o mediante descubrimiento. El
catálogo consultado el 30-10-2026 incluye el endpoint v2 y la separación de lectura,
escritura y operaciones destructivas. Verifica las herramientas y su esquema real;
los ejemplos históricos del plugin no son una lista obligatoria de nombres actuales.
[Documentación oficial de Rovo MCP](https://developer.atlassian.com/cloud/rovo-mcp/)
y [catálogo de herramientas](https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/).

Cloud y Data Center requieren contratos distintos. Un servidor compatible de otro
proveedor se puede elegir por proyecto, pero se debe revisar su autenticación,
operaciones y formato de contenidos. El plugin no configura uno automáticamente.

## W-08. Configurar Atlassian para un equipo

**Participantes:** responsable de área, administrador Atlassian y usuario del runtime.
**Comando:** `/setup`. **Skills:** `jira-sync`, `confluence-publish` y
`confluence-pull` solo para las funciones elegidas. **Tools:** conector real de la
sesión, al principio con lecturas de identidad/destinos.

| Paso | Quién y qué hace | Comprobación | Salida |
|---|---|---|---|
| 1 | Administrador autoriza el conector y sus permisos | Tenant correcto y acceso mínimo necesario | Cuenta conectada en el runtime, fuera del JSON del proyecto |
| 2 | Equipo decide módulos y funciones | Jira para seguimiento; Confluence para documentos; ambos o uno | Selección explícita, sin dependencia del core |
| 3 | Setup prepara bindings | Copia adaptada de `docs/examples/integrations/atlassian.json` | `.claude/integrations.json` |
| 4 | Adaptador consulta destinos visibles | Site/proyecto/espacio reales; no IDs inventados | Preferencias de destino |
| 5 | Usuario elige granularidad y asignación | Tarea/fase; asignar a sí mismo o dejar sin asignar | `.claude/jira.json` |
| 6 | Usuario elige árbol de documentos | Espacio y página raíz o anclaje existente | `.claude/confluence.json` |
| 7 | Router valida declaración | `--check` sin errores; no prueba conexión | Binding válido |
| 8 | Equipo prepara una operación piloto | Vista previa de una tarea/página en destino de prueba | Escritura solo después de autorización concreta |

El ejemplo de bindings declara seguimiento y publicación al cierre de fase. El
binding de pull tiene `events: []`: se invoca a petición, sin descargar cambios
automáticamente cada vez que se modifica un documento.

Configuración de Jira de ejemplo, sin credenciales:

```json
{
  "enabled": true,
  "cloudId": "site-elegido-en-la-sesion",
  "granularidad": "tarea",
  "assignee": "none",
  "alCubrirJornada": "preguntar",
  "defaults": {"projectKey": "AREA", "parentKey": null}
}
```

El site debe resolverse mediante el conector. Esta cadena es un ejemplo de
configuración, no un identificador listo para publicar. Jornada, tarifas y ratio
de supervisión proceden de la configuración económica; no se duplican como cifras
arbitrarias en cada tarea. Los scripts Jira del bundle usan los archivos canónicos
de esa raíz: `.claude/jira.json` y `.claude/jira-state.json`.

## Elegir tarjeta por tarea o tarjeta por fase

| Política | Qué se crea | Cuándo conviene | Qué se mantiene en el ledger |
|---|---|---|---|
| `granularidad: tarea` | Un issue por `T-XX` | Responsables o prioridades distintas por unidad de trabajo | Criterios, verificación y mediciones de cada tarea |
| `granularidad: fase` | Un issue por fase y checklist de sus tareas | Tablero ejecutivo con menos tarjetas | Todas las tareas y su estado, sin simplificar QA |

Para «Aprobación de solicitudes», modo tarea puede crear `T-01 Permisos`, `T-02 API`,
`T-03 Interfaz` y `T-04 Regresión`. En modo fase puede crear «Fase 1 · Base»,
«Fase 2 · Experiencia» y «Fase 3 · Verificación», manteniendo las cuatro tareas en
el ledger y su checklist correspondiente.

Un issue por fase no pasa a Done porque una sola tarea haya terminado. Se evalúa
el conjunto de tareas de esa fase con sus evidencias y gates. Cambiar la
granularidad después de publicar requiere un plan explícito de reconciliación;
no borres el mapa para que «parezca la primera vez», pues duplicaría objetos.

## W-09. Crear el plan en Jira sin duplicarlo

**Disparador:** planner terminó un plan local aprobado; `plan.created` selecciona
el binding `task-tracking` con `plan.export`, o el usuario invoca `jira-sync`.
**Agente:** planner prepara el handoff; la skill/adaptador Jira realiza la proyección.
**Tools:** lectura de destinos, metadatos y campos; creación tras la confirmación.

| Paso | Actor | Acción exacta | Resultado verificable |
|---|---|---|---|
| 1 | Router | Selecciona binding por evento/operación | No ejecuta ni concede permiso |
| 2 | Jira-sync | Lee plan y config de esta raíz | Tareas/fases válidas; `ledger-lint` cuando corresponde |
| 3 | Jira-sync + usuario | Elige proyecto y padre opcional | Destino legible por nombre y clave |
| 4 | Adaptador | Descubre jerarquía y tipos permitidos | No asume que cualquier proyecto tenga una épica o subtarea concreta |
| 5 | Adaptador | Consulta campos obligatorios y permisos | Valores faltantes resueltos antes de crear |
| 6 | Usuario | Revisa número de issues, títulos, asignación y padre | Aprobación del lote concreto |
| 7 | Adaptador | Consulta mapa previo y crea solo lo ausente | ID/clave real por respuesta confirmada |
| 8 | Adaptador | Guarda mapa y anota referencias en ledger | `.claude/jira-state.json` y claves junto a tarea/fase |
| 9 | Orquestador | Resume creados, existentes, fallidos e inciertos | Enlaces reales y siguiente acción; el plan local conserva su autoridad |

Una confirmación parcial del lote se conserva como parcial. Si tres issues se
crearon y el cuarto agotó el tiempo, no se vuelven a crear los tres primeros.
Se consulta el cuarto por clave correlacionable antes de intentar otra creación.
Si el conector no permite demostrar su resultado, se solicita reconciliación.

## W-10. De inicio de tarea a Done, con comentarios y revisión

El core emite eventos neutrales. Jira-sync traduce estos eventos al plan de
operaciones de `jira-flow.py`, que no llama por sí mismo a Jira. La ejecución
remota se realiza con las tools de la sesión; `confirmar` se usa después del
recibo real, no después de generar un JSON.

| Evento y dueño | Evento interno Jira | Efecto previsto | Condición |
|---|---|---|---|
| `task.started`, implementer | `arrancar` | Objetivo lógico En curso | Tarea/issue mapeado; transición disponible |
| `task.implemented`, implementer | `implementado` | Comentario de implementación y plan de worklog | Evidencia del ledger; nunca Done |
| `review.completed`, skill de revisión | `revision` | Comentario firmado de ese intento | Veredicto y tareas del intento local |
| `review.gaps`, skill de revisión | `gaps` | Comentario de hallazgos y reapertura prevista | Evidencia de gaps y transición permitida |
| `task.qa-passed`, QA | `qa-verde` | Comentario de verificación | Resultado real de qa-gate; sin cierre propio |
| `task.qa-failed`, QA | `qa-rojo` | Comentario de fallo y retorno al ciclo | No permite Done |
| `task.done`, orquestador | `aprobado` | Comentario de aceptación y objetivo lógico Done | Revisión sin gaps, QA verde y evidencia local |
| `review.worklog`, orquestador | Plan de worklog de revisión | Imputación separada por intento | Tiempo correspondiente, política y autorización |

Los objetivos lógicos no son nombres ni IDs fijos de transición. El adaptador
consulta el workflow/las transiciones accesibles del issue y resuelve el objetivo.
Si no existe una transición permitida, explica la incompatibilidad y deja la
proyección pendiente. No cambia la configuración del workflow de Jira para forzarla.

### Qué contienen los comentarios

La firma indica rol y fecha, por ejemplo `[custom-agents · implementer]`. El
comentario de implementación enlaza la tarea, cambios, archivos, verificación y
medición disponible. El de revisión indica intento, tareas, lentes, hallazgos y
evidencia; los rebates quedan trazados. QA aporta resultado y conteo del gate y
ruta del informe. El orquestador enlaza los dos veredictos que permiten el cierre.

Ejemplo ilustrativo de contenido, no recibo de una publicación:

```text
[custom-agents · qa] · verificación · fecha de la ejecución
Tarea: T-02 · API de aprobación
Resultado: gate verde, con el conteo observado por el runner
Evidencia: docs/roadmap/<iniciativa>/testing/report.md
El cierre queda a cargo del orquestador tras la revisión independiente.
```

La firma del agente es una atribución de workflow; no suplanta a una persona de
Atlassian ni demuestra una identidad criptográfica. La cuenta real que escribió
el comentario y los permisos son los del conector.

### Horas, intentos y repetición

`worklog.py` es el dueño del cálculo de imputación, la jornada diaria y el banco
de horas. Usa datos reales cuando existen y distingue estimaciones según su
contrato. El tiempo de revisión se separa del de implementación. No uses duración
de terminal ni tiempo de espera como si fueran esfuerzo IA medido.

La clave de evento incluye issue, evento, tareas e intento. Un evento confirmado
no se publica de nuevo al retomar el ciclo. «Pendiente» no significa «no ocurrió»:
antes de repetir se revisan comentarios/transiciones/worklogs en el proveedor.
No uses `--force` para resolver un resultado que todavía es incierto.

## W-11. Publicar documentación al cerrar una fase

**Disparador:** `phase.completed`; alternativamente, una petición explícita de
publicación. **Dueños:** implementer emite el evento; `confluence-publish` adapta;
documenter mantiene los documentos. **Tools:** lectura de árbol/páginas y escritura
de páginas con contrato comprobado. **Estado:** `.claude/confluence-state.json`.

| Paso | Responsable | Acción | Salida/decisión |
|---|---|---|---|
| 1 | Implementer | Verifica fase y enumera documentos cambiados | Se publica al cierre de fase, no una vez por cada tarea |
| 2 | Router | Selecciona binding de documentación | Rutas candidatas, sin permiso implícito |
| 3 | Confluence-publish | Lee política y resuelve alcance/staging | Lista real de documentos permitidos |
| 4 | Adaptador + usuario | Elige espacio, anclaje y página del proyecto | Árbol de destino legible |
| 5 | Adaptador | Compara hashes, mapa y revisión remota | Crear, actualizar, sin cambios o conflicto por documento |
| 6 | Usuario | Revisa la vista previa | Autoriza el lote concreto |
| 7 | Adaptador | Publica por página y registra recibos | IDs/revisiones reales; estado parcial si el lote falla |
| 8 | Orquestador | Resume enlaces y pendientes | No declara todo publicado por haber iniciado el lote |

La plantilla de política está en el módulo Confluence. Por defecto excluye el
ledger y plan de ejecución, testing, material sensible y candidatos de conocimiento.
Un resumen ejecutivo sí puede publicarse. La protección de security-scan y
conocimiento no aprobado no se puentea añadiendo un include. Revisa el alcance
de un proyecto real en vez de copiar una política de otro sin entenderla.

La edición Markdown y el PDF entregable son productos distintos. La publicación
de páginas no adjunta automáticamente todos los PDF ni convierte capturas locales
en adjuntos accesibles. Si se necesita ese efecto, se exige una operación y tool
que lo soporten, una vista previa y un recibo separado.

## W-12. Traer cambios de Confluence a docs

**Entrada:** `/confluence-pull` o petición equivalente, módulo disponible y mapa
previo. **Skill:** `confluence-pull`. **Tools:** lectura remota y escritura local
controlada. **No publica páginas durante el pull.**

El adaptador lee preferencias y mapa de esta raíz, consulta páginas gestionadas,
compara la versión remota, el hash publicado y el contenido local, y presenta
qué se actualizaría. Si cambiaron ambos lados, conserva el conflicto y solicita
decisión; no aplasta el trabajo local. La confirmación autoriza las escrituras
locales previstas, preservando frontmatter y límites de alcance.

El staging de Confluence es salida derivada, nunca fuente canónica para el pull.
Se usa el mapeo inverso del script de alcance para escribir el archivo canónico.
Sin mapa o sin página gestionada no se adivina un destino. Después del pull se
regeneran índices/estado correspondientes; traer texto no ejecuta instrucciones
remotas ni aprueba cambios de alcance del plan.
