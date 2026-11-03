# Categorías y captura de conocimiento por proyecto

El usuario ha autorizado implementar categorías propias, plantillas externas al
plugin, revisión de carpetas y aportaciones humanas o de agentes. El objetivo es
capturar decisiones, procedimientos, incidencias y otras fichas útiles con un
formato comprobable y fuentes. No se importan conversaciones ni se publican datos
en servicios externos como parte de esta implementación.

## Requisitos acordados

1. Cada proyecto declara sus categorías en `taxonomy.json`; conserva el routing
   existente por backend, incluido `summary`. No se añaden categorías obligatorias.
2. Una skill ayuda a definir la categoría desde su finalidad, prepara una plantilla
   del proyecto y registra su ruta. Las actualizaciones del plugin no la sobrescriben.
3. Cada categoría puede declarar carpeta de entrada, plantilla, metadatos y
   secciones exigidos y productores permitidos: `human`, `agent` o ambos.
4. Un comando revisa la carpeta de una categoría sin modificar originales. Una
   operación explícita puede proponer documentos válidos al servicio de curación;
   no los aprueba ni los publica. Los agentes usan el mismo contrato para sus FAQ
   u otras aportaciones.
5. Origen de contenido, productor y aprobación son datos distintos. Las etiquetas
   de origen son declaraciones del flujo, no autenticación ni permisos del sistema.
6. La configuración conserva las categorías, backends y preferencias existentes.
   La aplicación usa una vista previa ligada al contenido observado y protege
   archivos existentes y rutas. Los fallos parciales se comunican y pueden retomarse.
7. Los contratos son opcionales: categorías existentes sin ellos conservan su
   comportamiento. La plantilla orienta la redacción; el contrato valida el documento.

## Arquitectura y límites

`knowledge-taxonomy-local.py` valida la configuración. Las reglas de aprobación
siguen en `knowledge-curation-rules.py`; el servicio `knowledge-curation.py` sigue
siendo el único dueño de candidatos y aprobados. El índice no abre plantillas.
Una plantilla ausente no invalida el conocimiento aprobado histórico.

Las rutas son relativas al proyecto y las plantillas pertenecen al proyecto,
no al bundle. No se ejecutan ni se interpolan como código. La nueva herramienta
no activa conexiones, modifica los servicios de knowledge-graphs ni reindexa.

La ampliación de procedencia/vigencia en las proyecciones externas necesita su
propio contrato: Graphiti rechaza contenido distinto bajo el mismo nombre de
episodio. Este trabajo no cambia identidades ni recibos remotos.

## Ejemplos que deben funcionar

- `meetings`: documentos aportados por personas; comprobar participantes,
  fecha y acuerdos; conservar original y fuentes.
- `faq`: propuestas generadas por agentes con pregunta, respuesta y referencias;
  aprobación posterior por el proceso existente.
- Categoría mixta: admitir ambos orígenes sin convertir una revisión humana en
  autoría humana del contenido generado.

## Prueba de utilidad

Una persona debe poder crear su categoría, localizar la plantilla, añadir un
documento, interpretar errores de formato, proponerlo, revisar su origen y seguir
el proceso existente hasta la aprobación. Un agente debe poder hacer el mismo
recorrido con una FAQ sin otra implementación de persistencia.
