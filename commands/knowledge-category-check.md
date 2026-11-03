---
description: >
  Revisa documentos de una categoría del proyecto contra sus campos, secciones y origen
  permitido. No modifica originales; con petición explícita prepara candidatos para curación.
  Úsalo cuando el usuario diga "revisa la categoría meetings", "comprueba el formato de las FAQ"
  o "check de categoría".
argument-hint: <categoría> [--origin human|agent] [--propose]
---

# /knowledge-category-check — revisar una carpeta de conocimiento

Categoría y opciones: **$ARGUMENTS**. Resuelve el proyecto consumidor y el bundle
instalado con las seis raíces de `docs/CONVENTIONS.md`, regla 5. Localiza
`skills/knowledge-category-template/scripts/category-template.py` dentro de ese
bundle; no escribas un scanner ni otro servicio de propuestas.

## Revisar

Ejecuta `check --root <proyecto> --category <clave>` y muestra el informe por
archivo. El origen predeterminado `human` describe documentos aportados por una
persona; usa `--origin agent` para contenido generado por agentes. No deduzcas
la autoría del nombre del archivo o del actor que pulsa el comando.

El resultado conserva las rutas originales y distingue documento válido,
campos/secciones pendientes, conflicto de origen e inventario incompleto.
Un resultado válido solo comprueba el contrato de formato y metadatos, no los hechos.
La revisión predeterminada no escribe y no abre la plantilla para imponer
instrucciones: las reglas proceden de la categoría en `taxonomy.json`.

## Proponer cuando se haya pedido

Si el encargo incluye proponer las entradas válidas, conserva el
`expected_sha256` del informe y ejecuta el mismo `check` con `--propose` y
`--expected-sha256 <hash>`. Un inventario incompleto o modificado no se fuerza.
La herramienta llama a `agent-kits/shared/knowledge-curation.py`; conserva
original, ruta de fuente, hash de sus bytes, origen declarado y productor.

Entrega candidatos y SHA a `knowledge-curator` mediante el proceso existente
(`agent-kits/shared/knowledge-write.md`). No marques `estado: aprobado`, no
muevas archivos a approved ni sincronices servicios como efecto de este comando.
Para crear o ajustar la categoría, usa la skill `knowledge-category-template`.

## Racionalizaciones que no valen

Aplica `agent-kits/shared/rationalization-table.md` al comprobar el resultado.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Yo corregiré el acta original al revisarla» | Revisar no autoriza editarla. | Mostrar correcciones por separado. |
| «Yo copiaré lo válido a approved» | El formato no sustituye la curación. | Proponer mediante el servicio existente. |
| «Yo ignoraré los archivos que no pude leer» | El inventario quedaría incompleto. | Informar del límite y no proponer. |
| «Yo cambiaré el origen para que pase» | Alteraría la procedencia declarada. | Resolver el conflicto con la persona. |
| «Yo reutilizaré una vista antigua» | El documento o la política pueden cambiar. | Obtener un informe nuevo y revisar su hash. |
| «Yo anunciaré que ya está en el grafo» | Proponer no publica ni indexa. | Mostrar el estado real del candidato. |

## Resultado

Resume categoría, origen, archivos revisados, errores concretos y candidatos
creados o ya pendientes. Conserva los SHA para la revisión posterior. Si hay
fallos parciales, nombra cada archivo afectado; no presentes éxito global.
