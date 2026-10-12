# Trasladar conocimiento entre proyectos

[English](en/MEMORY-PORTABILITY.md) · **Español**

La memoria local sigue siendo la fuente de verdad. Puedes trasladar notas
aprobadas a otro proyecto con `knowledge-curation.py export` e `import`. El destino
recibe propuestas pendientes: importar no aprueba, publica ni sincroniza con
servicios externos. Humanos y agentes usan el mismo servicio de persistencia.

## Exportar una selección

Resuelve `$SHAREDKIT` con las raíces de instalación del runtime, como hace el ciclo.
Ejecuta `python3 "$SHAREDKIT/knowledge-curation.py" export --root <origen>
--source-id <etiqueta-origen> --id <id-exacto> --out <archivo-relativo>`.
Repite `--id` por nota; no hay selección implícita de todo el corpus. Las opciones
`--scope-category` y `--scope-area` filtran metadatos locales mediante AND.

Conserva el JSON de respuesta, la ruta y el SHA del paquete completo. La salida
debe ser nueva y quedar fuera de `.git`, configuración, memoria y ledger. Exportar
no modifica las notas originales. Etiquetas de proyecto y productor son
declaraciones, no autenticación ni permisos de backend.

El paquete v1 cerrado conserva bytes Markdown, BOM/CRLF y SHA originales mediante
base64. Exporta sólo approved válido; una nota que cambiaría al pasar por el
redactor se rechaza. Topes: 32 notas, paquete de 1 MiB, 256 KiB por nota/propuesta,
4096 entradas de inventario y 8 MiB acumulados de lectura. No recorta notas ni
divide lotes silenciosamente.

## Comprobar e importar

1. Copia explícitamente el paquete al proyecto de destino. No cambies sus bytes.
2. Ejecuta `python3 "$SHAREDKIT/knowledge-curation.py" import --root <destino>
   --destination-id <etiqueta-destino> --package <archivo-relativo>
   --expected-sha256 <sha-del-paquete> --check`.
   El preflight comprueba todo el lote sin crear candidatos, intents, recibos o
   lock; puede tomar un lock cooperativo existente para leer un estado estable.
3. Si decides persistir el lote válido, ejecuta la misma operación sin `--check`.
   El servicio revalida paquete, policy, proyecto y reservas bajo el lock antes de
   publicar. Conserva el JSON también si el exit no es cero.
4. Revisa cada `candidate_path` y `candidate_sha256`. Curator usa el Gate y
   `apply` existentes para decidir explícitamente, ligado al SHA pendiente. Sólo
   esa decisión asigna un ID de destino y versión inicial 1 al aprobar.

El import conserva cuerpo y metadatos representables, pero elimina ID, versión y
estado aprobados; establece `proposed_by: import` y procedencia inmediata `import_*`.
No promete borrar cualquier campo histórico de aprobación. Legado, journal,
configuración y routing externos permanecen fuera de esta operación.

## Reintentos y efectos parciales

Repetir la misma solicitud reconoce sólo intents/recibos propios y archivos
verificados por identidad y SHA. No adopta un archivo ajeno de bytes iguales ni
salta reservas cambiando la policy o etiqueta. Un recibo completo es historia de
una propuesta: si Curator movió la nota, el retry informa `missing_or_moved` y no
la recrea ni deduce aprobación.

El estado import vive bajo `docs/knowledge/candidates/.curation/import-v1/`, con
records distintos de `apply` y campo `import_operation_id`. No hay un segundo
almacén de memoria ni otra puerta de aprobación.

Un lote no es una transacción multiarchivo. Si falla la persistencia, las primeras
entradas pueden estar pendientes y las siguientes sin iniciar. La respuesta
distingue `not_started`, `persistence_pending` y `orphan_unrecoverable`. Un staging
sin intent propio probado no se adopta por hash ni se purga automáticamente.

`written` informa efectos de propuesta observados, no éxito ni durabilidad frente
a pérdida de energía: `false` antes de intentar crear, `null` si una creación OS
falló sin resultado probado, `true` tras observar creación o propiedad persistida.
La infraestructura del lock queda fuera de ese indicador. Para export, consulta
también `output_current`; una respuesta fallida puede tener bytes publicados.

| Exit | Resultado |
|---|---|
| 0 | Export completo, preflight completo o recibos import verificados |
| 1 | Validación o conflicto |
| 2 | Uso, dependencia, I/O o estado no verificable |

La lectura local permanece disponible sin servicios externos. Trasladar notas no
activa Kwipu, Graphiti, Graphify ni modelos; esas capacidades siguen sus contratos
y opt-ins propios.
