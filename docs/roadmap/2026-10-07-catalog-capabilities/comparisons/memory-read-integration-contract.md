# Contrato de la siguiente integración de memoria

Diseño del bloque18, todavía sin implementar ni aceptar mediante QA. Se deriva
de los [resultados funcionales](memory-functional-results.md) y amplía las piezas
existentes. La memoria local, captura de sesión y curación conservan sus contratos;
los requisitos de continuidad nativa pendientes siguen en el ledger global.

## Consulta documental opcional

Extender `markdown-export` con las dos funciones de lectura opcionales ya
definidas por el contrato de adaptadores: `puede_leer` y `consultar`.
Las seis funciones obligatorias de publicación/verificación siguen intactas.
No crear otro escritor de estado, motor RAG, skill, agente o MCP.

`config.read.enabled` será `false` por defecto. La lectura requiere backend
habilitado, intent explícito autorizado y `read.enabled: true`. Sin intent,
las consultas ordinarias, hooks y panel permanecen locales. Configuraciones
antiguas siguen publicando igual. No importar un adaptador para descubrir
si una consulta local podría usarlo.

Antes de red, obtener un corpus aprobado completo, aplicar el routing actual
del backend y comparar proyección/manifest/canon. Una categoría ausente o
desautorizada no llega a inferencia. Un pending, revocación, cambio de cuerpo,
versión o política sin sincronizar cierra lectura con motivo y fallback local.
Reutilizar selección pura del dueño de sync; no importar su ejecutor desde hooks.
Los filtros del caller que no puedan restringir todo el corpus del servidor
deben degradar antes de inferir, porque `/query` no ofrece filtros de documentos.

El núcleo construye contexto interno con raíz física, backend, intent, allowlist,
huella local y deadline; no se admite desde configuración del consumidor.
El router deja de exigir un grupo universal a todos los adaptadores y delega
el requisito al adaptador. Graphiti conserva su rechazo sin grupo efectivo.
Un `group_id` no convierte el HTTP documental en una consulta aislada.

| Enlace requerido | Comprobación |
|---|---|
| Canon | ID, versión exacta, SHA-256 de bytes, estado aprobado, evidencia, categoría y ruta física local |
| Proyección | Filename propio, hash semántico del export, versión, prefijo de proyecto, scope y modo summary/completo |
| Snapshot | Todos los chunks esperados, sin documentos extra, ID/version/hash/ámbito coherentes y node IDs únicos |
| Consulta | Cada source node resuelto a un único enlace de esa generación; filename nulo permitido por node ID, filename contradictorio rechazado |

Los hashes canónico y semántico del export tienen definiciones distintas.
No deducir ID por basename ni rellenar campos desde el texto generado.
Varios chunks de un documento son válidos si convergen al mismo enlace;
una entidad no se convierte en fuente documental. La verificación histórica
por nombre no se presenta como permiso fuerte de lectura.

La propagación de `knowledge_id/version/hash` del export real hasta snapshot
es aceptación obligatoria con un almacén sintético propio. El benchmark
documental inicial usaba `fm.id` y no la acredita. La
[prueba separada de metadata](../testing/memory-documental-binding.json) ya
verificó dos exports reales hasta chunks persistidos y GET nativo HTTP200,
con cero diferencias y once entidades excluidas. Esto acepta esa propagación
en la imagen probada, sin sustituir el gate completo ni QA de lectura del producto.
Si el servidor no devuelve los campos requeridos, la lectura degrada con
`binding_incompleto`.

Usar un único deadline monotónico para autorización, DNS/TCP/TLS, health,
snapshot previo, POST, snapshot posterior y normalización. Extender el transporte
acotado existente, con POST sin redirecciones y límites estrictos de pregunta,
respuesta, nodos, bytes y JSON. No guardar preguntas/respuestas en corpus,
journal, manifest o caché; no reindexar, reiniciar ni repetir POST automáticamente.

Exigir mismo snapshot/enlaces y huella local antes/después. Cualquier cambio
o cita sin resolver suprime la respuesta completa y devuelve recuperación local.
El protocolo no exporta una revisión compartida snapshot/query: esta comprobación
detecta cambios observables, pero no prueba atomicidad ni evita cambios ABA.

La salida separa entradas canónicas, source nodes y respuesta generada.
La respuesta se etiqueta **no verificada, sin autoridad y sin citas por afirmación**,
aunque todas sus fuentes estén enlazadas. El score es de recuperación. El router
conserva el envelope adicional genérico y compatibilidad con adaptadores antiguos.
`--limit` limita entradas presentadas; no promete limitar inferencia del servidor.
Una respuesta sin fuentes resolubles degrada; no se interpreta una frase del
modelo como prueba fiable de ausencia.

Archivos: `skills/knowledge-services/backends/markdown_export.py`, transporte
y tests de esa skill, `agent-kits/shared/knowledge-find.py`, selección pura
de sync, `knowledge-schema.py`, `schemas/taxonomy.schema.json` del kit y
tests correspondientes. Actualizar documentación y exports existentes del mismo
bloque cuando el contrato esté implementado. No habilitar lectura en el panel
por detectar un servicio.

## Identidad y vigencia del contexto de código

Ampliar `code-context.py` conservando `--symbol` y su API posicional. Añadir
selección exacta por `--node-id` o por el par `--source-file`/`--label`.
Exigir exactamente un modo, comparación sensible a mayúsculas e identidad
completa antes de redacción/recorte. No inferir namespace desde puntuación.
IDs duplicados invalidan todas sus ocurrencias y arcos; un par con varios
IDs devuelve ambigüedad sin contexto, incluso con límite de un resultado.

Conservar vecindad de un salto y relaciones AST citadas. No presentar búsqueda
por etiqueta como selección exacta ni `no-match-in-artifact` como ausencia
del repositorio. Esta entrega no introduce caminos transitivos ni análisis
semántico implícito.

Aceptar un sidecar opcional `<graph>.sources.json`, ligado al SHA-256 de los
bytes originales del artefacto, con esquema/version, alcance de inputs declarados,
paths relativos canónicos, longitudes y SHA-256 de cada input. El productor
debe observar esos bytes antes y después de extraer y publicar el sidecar solo
tras export exitoso. No crear un recibo de archivos actuales para legitimar
un artefacto antiguo. Commit, mtime o el indicador `directed` no prueban vigencia.

| Condición | Resultado requerido |
|---|---|
| Artefacto antiguo sin sidecar automático | Contexto legacy permitido, vigencia sin verificar y aviso |
| Sidecar explícito ausente/inaccesible | Verificación no disponible, contexto vacío |
| Esquema, claves duplicadas, binding o cobertura de inputs inválidos | Verificación inválida, contexto vacío |
| Input declarado ausente o bytes distintos | Artefacto obsoleto, contexto vacío |
| Presupuesto, permisos o lectura inestable | Verificación parcial/no disponible, contexto vacío; conservar cualquier obsolescencia ya probada |
| Todos los inputs declarados coinciden | Acuerdo de bytes del conjunto declarado; cobertura global desconocida y contexto no aprobado |

Recalcular todos los hashes por consulta, incluidos inputs sin nodo seleccionado;
solo se admite caché dentro de esa llamada. El recibo no autentica a su productor,
no descubre archivos nuevos ni verifica semántica de arcos. Mantener límites
de artefacto/nodos/arcos y añadir topes de recibo, archivos y bytes acumulados.
Validar rutas, archivos regulares y enlaces antes de leer; no seguir rutas
remotas, ejecutar Git, importar extractor, instalar dependencias o escribir recibos.
Las comprobaciones ordinarias no constituyen contención atómica frente a cambios
hostiles concurrentes de ancestros; no prometer esa garantía desde un precheck.

Archivos: `agent-kits/shared/code-context.py`, `tests/test_code_context.py`,
contrato de contexto en docs y exports existentes. Mantener la lógica en el
lector standalone con sus helpers actuales; la creación del recibo es una
operación explícita del productor externo, separada de consulta.

## Aceptación y orden

1. Probar metadata del export documental real y cerrar el contrato del snapshot.
2. Escribir y observar RED de autorización, enlaces, carreras, límites y
   envelope antes de cambiar lectura documental; conservar publicación y fallback.
3. Escribir RED de selectores, colisiones y recibos antes de cambiar lector AST;
   añadir aceptación sobre un artefacto nuevo con productor/recibo explícitos.
4. Revisión independiente A/B y C/D cuando correspondan; QA Windows/Linux,
   bundle parcial, exports y documentación coherente antes de publicar.
5. Corregir/aceptar filtros históricos y procedencia Graphiti antes de anunciar
   esa utilidad; no activarlo como requisito general para completar los dos anteriores.

Todos los escenarios de pruebas usan proyectos y servicios propios. Los RED
propuestos todavía no se han ejecutado: este diseño no es evidencia de implementación.
Los casos de restore, escritura interrumpida, corpus grande, UX y aprendizaje
continúan pendientes y no se cierran por aceptar una interfaz de lectura.
