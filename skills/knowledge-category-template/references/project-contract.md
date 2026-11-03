# Contrato de categorías del proyecto

Todos los campos nuevos son opcionales. Las categorías anteriores conservan sus
reglas comunes de aprobación; no se les añade una plantilla automáticamente.

| Campo | Significado |
|---|---|
| `key` | Clave exacta de la categoría, elegida por el proyecto. |
| `folder` | Carpeta bajo `docs/knowledge/approved/`; no es la bandeja de entrada. |
| `min_evidence` | Nivel exigido de la escalera de evidencia del proyecto. |
| `template` | Archivo Markdown relativo al proyecto, fuera del plugin instalado. |
| `inbox` | Carpeta relativa con originales; no admite Git, candidatos ni approved. |
| `allowed_producers` | Lista no vacía de `human`, `agent` o ambos. Sin campo, conserva el flujo anterior. |
| `required_metadata` | Claves de frontmatter con valor no vacío, escalar o lista de cadenas. |
| `required_sections` | Títulos ATX sin `#`, con contenido; se comparan sin distinguir mayúsculas. |
| `routing` | Destinos declarados: `true`, `false` o `summary`; sin permiso no hay publicación. |

No hay lenguaje de plantillas ni código evaluado. Los metadatos continúan usando
el YAML simple que admite el plugin: cadenas y listas, no objetos anidados.
El contrato exige presencia y formato básico; no acredita que una afirmación sea
cierta. Las fechas de revisión pueden exigirse como metadatos, pero este comando
no calcula caducidad ni inventa una fecha.

## Ejemplo: actas humanas

```json
{
  "key": "meetings",
  "folder": "meetings",
  "min_evidence": "single_case",
  "template": ".claude/knowledge-templates/meetings.md",
  "inbox": "docs/meetings",
  "allowed_producers": ["human"],
  "required_metadata": ["fecha", "participantes"],
  "required_sections": ["Objetivo", "Acuerdos", "Referencias"],
  "routing": {}
}
```

La plantilla puede contener frontmatter con esas claves vacías y encabezados
`## Objetivo`, `## Acuerdos` y `## Referencias`. Son huecos para redactar, no una
entrada ya válida. Para aprobar se mantienen evidencia, fuentes y tags `clave:valor`.

## FAQ de agentes y categorías mixtas

Una FAQ puede declarar `allowed_producers: ["agent"]`, `required_sections` con
`Pregunta`, `Respuesta` y `Referencias`, y un inbox propio. `documenter` u otro
productor existente aporta respuestas contrastables y declara `origin=agent`.
No hace falta crear otro agente ni activar un LLM adicional.

Una categoría mixta usa `["human", "agent"]`. El flujo registra `content_origin`
y `proposed_by` por separado. El servicio impide cambiar un origen ya declarado
al aprobar. No son identificadores autenticados: un actor con acceso al sistema
puede declarar valores; los permisos físicos requieren controles del entorno.

## Configuración y recuperación

El JSON de solicitud tiene exactamente dos claves: `category` (bloque nuevo o
parche de una categoría existente) y `template_text` (Markdown). Las demás
categorías y conexiones se conservan. No se sobrescribe una plantilla diferente.
Para actualizar su diseño, crea otro archivo y cambia la referencia en la categoría.

La aplicación crea primero la plantilla y después publica atómicamente la
taxonomía, bajo el lock cooperativo del servicio de curación. Si falla el segundo
paso, devuelve `partial`; conserva la plantilla y retoma con una vista nueva.
No es una transacción global frente a editores que ignoren ese lock.

La plantilla no define por sí sola las reglas: las listas `required_metadata` y
`required_sections` son el contrato. Borrar la plantilla no cambia aprobados
históricos. Cambiar el contrato afecta a futuras aprobaciones; antes de endurecerlo,
revisa los candidatos y los procedimientos que lo usan.

## Límites de revisión

La revisión acepta Markdown visible, omite README y nombres ocultos, recorre hasta
cuatro niveles y acota entradas y bytes. Una lectura incompleta no autoriza una
propuesta. `expected_sha256` vincula proyecto, política, origen y fuentes observadas.
Los originales no se modifican y la segunda propuesta de la misma fuente pendiente
reutiliza el candidato idéntico. Una colisión diferente se comunica sin sobrescribir.
