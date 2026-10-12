# Propuesta, juicio y persistencia de memoria

Contrato del bloque23, 2026-10-10. Implementación candidata disponible;
aceptación global pendiente. La comprobación técnica nativa de curación/portabilidad
se conserva en [su evidencia](../testing/native-memory-curation38-evidence.json);
no acredita juicio semántico real ni todos los clientes/backends.
Parte del estado publicado `3be4821`; no cambia las dieciséis tareas macro.
Complementa la [recuperación local](memory-local-recovery-contract.md) y la
[comparación de aprendizaje](skills-session-learning-memory.md).

## Un recorrido para conocimiento nuevo

Desde este cambio, architect, planner, implementer, qa, documenter,
debug-root-cause, retro y el puente de casos proponen exclusivamente candidatos
nuevos. Usan el servicio compartido `agent-kits/shared/knowledge-curation.py`.
No escriben ni promueven nuevas entradas ADR/GOT/LES en el árbol legado.
La revisión de código, design elegido, QA, repetición y Gold aportan evidencia;
ninguno aprueba por sí solo conocimiento. No se añade una skill ni un agente.

El servicio persiste bytes; knowledge-curator decide categoría, suficiencia,
contradicciones y decisión. El gate actual conserva su evaluación de solo
lectura y sus códigos. El servicio reutiliza sus validadores de contenido,
el parser local, la taxonomía y el redactor; no copia reglas de aprobación.
Una declaración de productor/decisor no autentica identidad nativa. El
confinamiento efectivo de herramientas en tres clientes requiere aceptación
independiente; no se acredita por el CLI ni por una etiqueta de rol.

## API y CLI compartidos

Todas las operaciones devuelven `(resultado, código)`; 0 confirma operación,
1 rechaza el contrato y 2 indica uso, dependencia o IO no verificable. El
resultado tiene `status`, `errores`, `avisos` y rutas relativas verificadas.
No imprime contenido crudo ni excepciones con datos del consumidor.

- `propose(root, filename, text, producer=..., reserved_aliases=())`: Markdown UTF-8 hasta 256 KiB,
  nombre portátil ASCII de hasta 128 caracteres, frontmatter simple y cuerpo.
  Redacta todo el texto antes de persistir. No admite `estado`, crea sólo
  `candidates/pending/<filename>` y devuelve ruta y SHA256 de los bytes finales.
  Un nombre ya existente en cualquier estado o approved no se vuelve a crear.
  Hasta ocho aliases históricos ASCII portátiles de hasta 255 caracteres se
  comparan por basename sin distinguir mayúsculas bajo el mismo cerrojo. Sólo
  reservan nombres; no son rutas ni destinos, ni amplían el límite de 128 del
  archivo nuevo. El puente Gold conserva la referencia completa y su hash,
  acorta sólo el slug cuando hace falta y entrega el SHA real del servicio.
- `apply_decision(root, candidate, decision, expected_sha256=..., metadata=None,
  replacement_text=None, reason=..., decider="knowledge-curator")`: candidato relativo exacto en
  pending/needs_changes/rejected, SHA obligatorio y motivo no vacío.
  `approve` exige id final válido/prefijado, categoría exacta, versión inicial 1,
  evidencia/fuentes/tags suficientes y `estado: aprobado` en la representación
  final. Errores del índice bloquean; colisión de ID/nombre nunca sobrescribe.
  `reject` y `needs_changes` conservan contenido y motivo sin exigir evidencia
  suficiente; rejected es terminal. Necesidades de cambios no modifican en
  sitio un candidato: se conserva la propuesta y se registra el motivo.
  Para aprobar una corrección puede aportar `replacement_text`: Markdown final
  redactado y validado; la intención conserva el original y ambos hashes.
  Sólo `approve` admite esa corrección; nunca es una edición de approved.
- `recover(root, operation_id, decider="knowledge-curator")`: recuperación
  explícita de una operación preparada por el mismo servicio. No introduce un
  juicio nuevo, no vuelve a aprobar contenido cambiado y no elimina fuente
  modificada. Registra el estado pendiente cuando no puede completar.

CLI: `propose --filename <nombre.md> --producer <rol> [--reserved-alias <nombre.md>]`
lee Markdown de stdin; el alias es repetible hasta ocho veces;
`apply <ruta-relativa> --decision <decisión> --expected-sha256 <sha> --reason
<motivo> [--metadata-json <objeto>] [--replacement-stdin]`; `recover <operation-id>`. Todas admiten
`--root <proyecto>` y salida JSON. Sin bundle compartido, se informa pendiente;
el productor no recurre a Write/Edit para saltarse el servicio.

## Asociación y observación de retoma

Propose entrega candidate/SHA al dueño existente del ledger; planner incorpora
handoffs explícitos de design cuando lo crea. Ese dueño registra antes de apply
un único bloque top-level `curation-refs-v1`, según `knowledge-write.md`:
array JSON de hasta ocho referencias únicas/8 KiB, claves candidate/sha256 y
operation_id opcional. Curator devuelve el operation-id del servicio para que
el dueño lo añada después. Sin ledger, conserva el handoff en su artefacto
permitido; no hay asociación inferida ni nuevos permisos de escritura roadmap.

`inspect_reference(root, candidate, expected_sha256, *, operation_id=None)` sólo
observa esa identidad mediante lectores/validadores del servicio. No ejecuta
apply/recover, cerrojo escritor ni limpieza de staging. El bucket de candidato
admite hasta 16 nombres y todas las referencias comparten 1 MiB adicional al
dossier. Un ID explícito no tiene fallback; asociaciones múltiples, IO o lectura
incompleta no prueban ausencia. Los cuerpos approved no se leen.

`completed_receipt_observed` liga un recibo validado a los hashes de su intención;
no certifica contenido approved vigente ni QA, y target_content_verified permanece
false. El dossier conserva estados/reasons, identidades completas o no resolubles,
prefijos completos, contador de omisiones y truncamiento verdadero dentro de
12.000 bytes JSON/32 líneas/6.000 caracteres. No crea otro almacén o workflow.

## Publicación y recuperación

Escritores cooperantes comparten un cerrojo de proceso no bloqueante bajo
candidates. IO rechaza traversal, ADS, nombres reservados, enlaces redirigidos,
archivos no regulares, enlaces duros ajenos y escaneos incompletos. Lecturas y
enumeración son acotadas. No lee Git, backends, transcripciones ni ejecuta modelos.

Cada transición registra una intención inmutable ligada al hash original,
decisión, motivo redactado, política/taxonomía y bytes finales. Publica el
destino completo sin sobrescritura, lo verifica y sólo entonces retira la
fuente exacta comprobada. Un recibo final confirma ambas fronteras. Cortar
entre ellas deja intención/fuente o destino recuperables; no se promete una
transacción atómica de varios archivos. El aprobado puede ser visible tras
su publicación y antes de finalizar la limpieza y el recibo.

Las intenciones se organizan por SHA256 de la ruta exacta del candidato:
`operations/<sha-ruta>/<operation-id>.json`. Una decisión enumera y valida
sólo las intenciones de ese candidato; no recarga payloads de candidatos
históricos ajenos ni borra sus registros. El recibo continúa separado por
operation-id. Recuperar por ID enumera nombres con el límite de entradas,
exige una única coincidencia y verifica ruta, hash, contenido e identidad
del registro elegido antes de usarlo. Un ID duplicado o una intención fuera
del directorio ligado a su fuente bloquea sin adoptar ni limpiar registros.
La búsqueda por nombres y el historial del mismo candidato siguen acotados;
no se promete tiempo constante ni aceptación de un corpus de tamaño ilimitado.
Este formato se fija antes de publicar el servicio: no migra memoria existente.

Intenciones y recibos incluyen el staging exacto y su identidad de archivo,
construidos antes de escribir sus bytes. El hash de la intención liga también
esa información. Si el corte sucede después de enlazar el registro y antes de
retirar su staging, recover valida el registro y su contenido esperado, exige
exactamente esos dos enlaces de la misma identidad y hash y retira únicamente
ese staging. No acepta un enlace adicional, un staging ajeno o un registro
alterado. Un registro terminado debe tener un solo enlace y ningún staging.

La recuperación reconoce únicamente el destino de bytes exactos de su intención;
contenido, fuente o configuración cambiados antes de publicar bloquean.
Un destino ajeno no se adopta. No se borra otro archivo para corregir un fallo.
El cerrojo no excluye editores externos: las verificaciones detectan cambios,
pero no acreditan un sandbox universal ni inmunidad a renombres hostiles durante
IO. Esos límites se deben conservar en documentación y evidencia por plataforma.

## Compatibilidad y conflictos

ADR/GOT/LES existentes conservan bytes, IDs, estados, enlaces y autoridad original;
aceptada no se reinterpreta como aprobado. No hay migración, reaprobación ni
borrado automáticos. Journal/candidatas sigue siendo episódico y de solo lectura;
una propuesta explícita puede citarlo, sin elevar repetición a verdad.
Doctrina empaquetada, retrieval, índices reconstruibles y exportación approved
mantienen sus contratos. Candidatos no entran en búsqueda ni en publicación externa.

Curator consulta approved y legado aceptado pertinente. Ante contradicción o
alto impacto requiere resolución humana trazada; fecha, score o ranking no
resuelven conflictos. Constitución prima. Una sucesión explícita registra sus
referencias sin modificar el legado incidentalmente.
Retro ocurre después del Gate principal: entrega un handoff al curador o deja
ruta/ID y estado pendiente visibles. Cerrar QA/revisión/retro no aprueba memoria.

## Evidencia necesaria para aceptar

RED previo al código; propuesta redactada y nunca aprobada; nombres/duplicados;
SHA cambiado; ID obligatorio, versión y taxonomía; índice erróneo y colisiones;
terminal rejected; gate anterior no mutante; no sobrescritura ni mutación del
legado; interrupción antes/después de publicación y recuperación idempotente;
fuente alterada conservada; concurrencia cooperativa; enlaces/IO por OS;
compatibilidad Gold/nombres/hash ausente y journal; todos los callers alineados;
proyecciones regeneradas; revisión fresca y QA congelada Windows/Linux.
Las pruebas de servicio no sustituyen aceptación nativa, eficacia a escala,
aprendizaje automático o superioridad experimental.
