---
name: data-collection
description: >
  Diseña recolectores HTML, RSS o JSON con normalización, enriquecimiento opcional
  y almacenamiento recuperable. Úsala cuando el usuario diga
  "diseña un recolector de datos", "normaliza estas fuentes RSS" o
  "añade enriquecimiento opcional al colector".
---

# Recolección de datos

Guía una implementación en el proyecto consumidor; no incorpora adaptadores ni
activa servicios. Para decidir qué herramienta adoptar usa `research-first`.

1. Identifica fuentes autorizadas, formato, resultado y almacenamiento elegido.
   Lee [contratos de fuente](references/source-contracts.md) antes de recolectar.
2. Diseña normalización y enriquecimiento con
   [persistencia y enriquecimiento](references/enrichment-storage.md).
   Conserva identidad y procedencia desde el origen hasta la escritura.
3. Si hay preferencias aprendidas de feedback o ejecución periódica, lee
   [operación y feedback](references/feedback-operations.md). No lo activa por
   disponer de una clave o un almacén.
4. Usa las versiones del consumidor y documentación oficial para servicios/SDK.
   Verifica sus contratos con fixtures pertinentes antes de ejecutar contra fuentes
   reales dentro del alcance autorizado.

`llm-pipeline` puede guiar presupuesto y reintentos del enriquecimiento. El feedback
de preferencias no es conocimiento aprobado, Gold ni entrenamiento del modelo;
esas responsabilidades siguen en sus capacidades específicas.

## Sesgos al recolectar

Formato compartido: agent-kits/shared/rationalization-table.md.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «La respuesta está vacía, no había registros» | Un error de origen o de parser puede ocultarse como vacío válido. | Distinguir éxito vacío, fallo y resultado parcial con recibos. |
| «Hay una clave, así que activo la IA» | La credencial no expresa la preferencia de ejecución. | Respetar el modo desactivado y registrar enriquecimiento omitido. |
| «Emparejo la respuesta del modelo por posición» | Una salida reordenada puede atribuir datos a otro registro. | Validar cardinalidad e identificadores estables antes de mezclar. |
| «La escritura falló y la repito entera» | La operación anterior pudo persistir pese al fallo del recibo. | Reconciliar por ID y aplicar la idempotencia del almacén. |
| «Reinicio el feedback corrupto y continúo» | El reinicio silencioso destruye preferencias y oculta el fallo. | Conservar el original y ofrecer recuperación sin sobrescribirlo. |
| «Sigo todas las redirecciones del origen permitido» | Un salto puede cambiar el destino y el alcance de acceso. | Validar cada destino y respetar límites de páginas, bytes y plazo. |

## Salida y evidencia

Diseño o implementación con contratos de fuente, esquema normalizado, límites,
estados de enriquecimiento, persistencia e idempotencia. Informa registros válidos,
omitidos, parciales y fallidos sin confundir simulación con ejecución real.
