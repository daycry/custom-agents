# Contrato de las fichas de comparación

Aplicar el método canónico de
[capability-audit](../../../skills/capability-audit/references/method.md).
Este documento fija la trazabilidad de esta iniciativa, sin duplicar el método
ni crear un segundo ledger.

## Evidencia por pieza

Cada uno de los 455 IDs principales necesita una ficha con estos campos:

| Campo | Contenido exigido |
|---|---|
| Identidad | ID, revisión, hash del cuerpo y tamaño medido; ruta original solo en el mapa privado |
| Lectura | Cuerpo completo leído; IDs/hashes de recursos y callers leídos, incluidos los externos al directorio |
| Contrato | Intención, entradas, decisiones, salidas y responsable del artefacto |
| Contenido único | Criterios concretos que aportan valor; secciones y ejemplos que lo demuestran |
| Comparación propia | Piezas y secciones actuales realmente leídas; solapes y diferencias explícitos |
| Dependencias | Imports, scripts, tools, MCP, configuración, permisos y contratos técnicos por versión |
| Decisión | Conservar, ampliar, actualizar, consolidar o retirar; motivo funcional comprobable |
| Destino | Archivo/sección propios propuestos, dueño y criterios conservados; propuesta o entrega diferenciadas |
| Activación | Petición literal, paráfrasis, negativo vecino y redirect; ejecución y check estático separados |
| Coste | Bytes/líneas del cuerpo y recursos, modo de carga; tokens y latencia nulos sin medición compatible |
| Validación | Comando, versión, resultado y evidencia; «no ejecutado» para lo que no se probó |
| Impacto | Callers, dependencias, evals, documentación, manifiestos y exports que cambiarían |

Un recurso compartido puede tener una ficha funcional propia y ser citado por
varias piezas; reutilizar esa lectura requiere los mismos hashes, consumidores
y contratos relevantes. Un enlace presente o una extracción automática no
demuestra que se haya leído el recurso ni que su API funcione.

## Contabilidad y decisiones

Registrar por separado inventariadas, leídas, evaluadas e integradas. Cerrar
una ficha exige cuerpo, recursos y callers necesarios para su veredicto; un
fallo de lectura deja pendiente la pieza. Una validación no ejecutada puede
acompañar una propuesta, pero no acreditar su integración funcional.

Las exclusiones requieren un motivo concreto de utilidad, responsabilidad o
contrato. No basta un nombre parecido, falta de logs, un stack diferente o
que la función no se use en este repositorio. No se inventan paquetes que
no estén presentes en el corpus; las especialidades útiles son opcionales.

Antes de integrar, T-08 fija destinos concretos y elimina duplicación de método.
Una consolidación conserva todo criterio útil y retira los callers sustituidos;
no entrega aliases vacíos. Las fichas de memoria comparan mecanismos aquí y
definen experimentos de fase 4; no declaran un benchmark todavía no ejecutado.

Los originales y sus nombres permanecen en investigación privada. Las fichas
públicas usan los IDs y nombres funcionales propios; cualquier contenido
adaptado conserva la atribución legal exigible en el lugar correspondiente.
