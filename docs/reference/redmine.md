> Referencia avanzada. Empieza por el [manual explicado paso a paso](../CUSTOMIZATION.md). Este capítulo conserva contratos de implementación y configuración.

# 4. Redmine, wiki y proveedores de proyecto

Redmine se incorpora como adaptador del proyecto. No hace falta añadir otra marca
al core ni publicar una versión del plugin para cada organización. El mismo patrón
sirve para una wiki propia: función, contrato, herramienta, configuración y recibos.

Este ejemplo incluye una skill de referencia para implementar/adaptar, no un
conector Redmine instalado ni una conexión real certificada. El administrador debe
elegir un transporte de confianza y verificarlo en su instancia y versión.

## Qué corresponde a Redmine y qué corresponde al plugin

La API documentada de Redmine permite tratar issues y notas, consultar estados
permitidos y gestionar páginas de wiki. Las posibilidades efectivas dependen de
versión, rol y configuración de la instancia. Consulta la [API de issues](https://www.redmine.org/projects/redmine/wiki/Rest_Issues)
y la [API de wiki](https://www.redmine.org/projects/redmine/wiki/Rest_WikiPages).

El plugin aporta el ledger y los eventos. El adaptador aporta traducción de campos,
identidades, tracker, proyecto, estados y formato de la wiki. Ni `T-01` ni una fase
del plugin equivalen automáticamente a un tracker, versión o proyecto Redmine.

## W-13. Añadir el adaptador Redmine del proyecto

**Participantes:** responsable de área y equipo administrador/técnico.
**Comandos:** `/setup` y `/work-context`; no hay comando obligatorio `/redmine`.
**Skill de proyecto:** `project-redmine`. **Tools:** las que exponga el conector
seleccionado, descubiertas en la sesión. **Core:** no se modifica.

| Paso | Actor | Acción | Resultado y criterio |
|---|---|---|---|
| 1 | Responsable | Decide tarea/fase y qué información necesita el equipo | Política de colaboración y asignación |
| 2 | Administrador | Selecciona transporte/servidor y cuenta | Acceso mínimo y destino de prueba |
| 3 | Equipo | Añade skill de proyecto con su contrato | Nombre propio, instrucciones y pruebas del adaptador |
| 4 | Equipo | Define mapa de operaciones y estados | Cada capacidad declarada tiene una tool real o queda desactivada |
| 5 | Setup | Añade binding basado en `docs/examples/integrations/project.json` | `.claude/integrations.json` de este proyecto |
| 6 | Equipo | Añade preferencias no secretas | `.claude/integration-settings/redmine.json` |
| 7 | Router y lector de piezas | Validan declaraciones e inventarían skill/MCP | Disponible todavía sin verificar hasta contrastar sesión |
| 8 | Equipo + usuario | Ensaya lecturas y un cambio autorizado en destino piloto | Recibos reales; no se promociona un contrato vacío a «conectado» |

Ejemplo de preferencias del adaptador **del proyecto**, cuyo esquema no interpreta
el router del core:

```json
{
  "version": 1,
  "project_identifier": "solicitudes",
  "granularity": "task",
  "tracker": "se-descubre-en-la-instancia",
  "assignee_policy": "unassigned",
  "state_policy": {
    "started": "in-progress",
    "review_failed": "reopen",
    "accepted": "closed"
  },
  "map_file": ".claude/integration-state/redmine.json"
}
```

Los valores de estado son objetivos lógicos del adaptador de ejemplo. No son IDs
de Redmine. El implementador debe resolverlos con la configuración real y rechazar
ambigüedades. No copies estas cadenas directamente a `status_id`.

## Contrato mínimo de project-redmine

| Capacidad | Entrada desde el core | Traducción del adaptador | Evidencia exigida |
|---|---|---|---|
| `plan.export` | Ledger aprobado, tarea/fase y destino | Issue con asunto, descripción, proyecto y tracker válidos | ID devuelto/confirmado y mapa local |
| `task.read` | Referencia de issue y campos necesarios | Lectura acotada de ese proyecto | ID, campos y fecha de consulta |
| `task.progress` | Evento, tarea, actor y evidencia | Nota/comentario y estado permitido según política | Recibo de nota y estado observado |
| `worklog.write` | Medición y unidad explícitas | Imputación según contrato de la instancia | Registro real y prevención de repetición |
| `docs.publish` | Documento aprobado y revisión | Otra skill/binding de wiki, si existe | Título/ID y versión real de página |

No declares todas las capacidades por aspiración. Si el conector solo permite
leer issues, declara `task.read` y no suscribas eventos de escritura. Si una tool
combina nota y cambio de estado en una operación, documenta su resultado parcial
y cómo se reconcilia; no asumas que cualquier error revierte ambos efectos.

## W-14. Ejecutar una iniciativa con Redmine

El workflow local es W-02 a W-05: analyst/evaluator definen y evalúan; architect
puede diseñar; planner crea fases/tareas; implementer, revisión y QA trabajan.
La skill de proyecto complementa sus eventos, sin reemplazar a los agentes.

| Momento | Agente/componente emisor | Acción del adaptador | Evidencia y control |
|---|---|---|---|
| Plan aprobado | Planner, `plan.created` | Presenta issues por tarea o fase y solicita autorización | Cuenta, proyecto, tracker y asignación visibles |
| Creación | Project-redmine | Busca mapa/clave de correlación y crea lo ausente | ID por cada objeto confirmado; no lote ficticiamente atómico |
| Inicio | Implementer, `task.started` | Resuelve estado de trabajo permitido | Si no puede transicionar, deja aviso sin cambiar el ledger |
| Implementado | Implementer, `task.implemented` | Publica nota con resumen y verificación | Firma de rol, evento y tarea; no cierra el issue |
| Revisión | Adversarial-review, `review.completed`/`review.gaps` | Nota por intento y reapertura cuando procede | No duplica el comentario del reviewer ni suplanta su identidad |
| QA | QA, `task.qa-passed`/`task.qa-failed` | Nota con resultado y referencia de evidencia | No interpreta una nota como ejecución del gate |
| Aceptación | Orquestador, `task.done` | Transición final solo con ambos veredictos | Estado permitido y recibo real; si es por fase, todas sus tareas deben cumplir |
| Cierre de fase | Implementer, `phase.completed` | Handoff al binding de documentación | No publica evidencias crudas por defecto |

### Ejemplo de nota de implementación

```text
[custom-agents · implementer] · task.implemented · T-02
Cambio: endpoint de aprobación con autorización por recurso.
Verificación: comando real y resultado observado del proyecto.
Evidencia: ruta local del informe o enlace aprobado accesible al equipo.
Revisión y QA pendientes. Este evento no cierra el issue.
```

Esta plantilla ilustra el contrato. La skill del proyecto debe añadir la clave de
correlación elegida y usar el formato que admita su instancia. No adjuntes raw,
secretos o conversaciones para dar contexto a un comentario.

### Cómo evitar duplicados

La correlación relaciona iniciativa, tarea/fase, evento e intento. El mapa local
registra el objeto remoto y el recibo confirmado, nunca credenciales. Antes de
repetir una nota se consulta el registro remoto correlacionado. Un timeout
después de enviar se marca incierto y exige reconciliación; no se interpreta como
«no llegó». Si se pierde el mapa, no se recrean todos los issues automáticamente.

## W-15. Publicar en una wiki del proyecto

**Binding:** `purpose: documentation`; skill `project-wiki` u otra elegida.
**Evento:** `phase.completed`; lectura bajo petición si se implementa `docs.pull`.
**Entrada:** documentos aprobados y alcance explícito. **Tools:** lectura de página,
escritura/versionado y, solo si se necesita, adjuntos con operación separada.

El adaptador establece la conversión de Markdown al formato admitido, el árbol de
páginas, la clave estable de cada documento y la política de conflictos. Consulta
la página/revisión actual, muestra la vista previa, obtiene autorización aplicable
y publica. Registra versión y hash local tras comprobar el recibo. Si el proveedor
no ofrece escritura condicional, declara ese límite y revalida antes de actualizar;
no promete atomicidad que no existe.

Los permisos, conflicto de ediciones, borrados y adjuntos son casos separados.
Un documento retirado localmente no se borra de la wiki sin una política y una
operación autorizada. El pull, si se añade, compara ambos lados y conserva el
frontmatter local y los conflictos, igual que cualquier adaptador de documentación.

## Si se usa otra plataforma

GitHub/GitLab para issues, Linear para seguimiento, Notion para documentos o una
wiki corporativa pueden implementar los mismos puertos. No son adaptadores listos
por figurar aquí. El proyecto elige y prueba su transporte y sus capacidades reales.
Un sistema de mensajería requiere otro propósito y contrato de notificación:
no se usa `docs.publish` como atajo para enviar mensajes a personas.
