<!--
  FRAGMENTO COMPARTIDO: cuándo y cómo proponer memoria técnica del proyecto.
  Lo referencian architect, planner, implementer, qa, documenter, debug-root-cause
  y /retro. Los umbrales y el recorrido de propuesta tienen aquí su fuente única.
-->

# Proponer memoria técnica — paso compartido

Todo conocimiento nuevo recorre `candidates/pending/` → juicio de `knowledge-curator`
→ `approved/` o `candidates/{needs_changes,rejected}/`, bajo `docs/knowledge/`.
El productor propone; Curator decide categoría, evidencia y contradicciones;
`agent-kits/shared/knowledge-curation.py` persiste los bytes. La elección de diseño,
la revisión, QA, Gold o una retro aportan evidencia, nunca aprobación de memoria.

## Umbral de registro (anti-burocracia)

**Orientación: 0-2 entradas por iniciativa.** No es un límite duro. Más de ~3 es
indicio de umbral mal calibrado: se registra en la retro, no se ignora.

- **Decisión (ADR):** cierra una alternativa Y (afecta a 2+ piezas O se tomó en
  una puerta de decisión). Un nombre de variable, el orden de dos párrafos o una
  elección cuya reversión no toca una segunda pieza no merecen registro.
- **Gotcha:** costó ≥1 ciclo de depuración O rompió/casi rompió una garantía del
  producto. Un typo o un fallo aislado de CI sin repetición no lo merecen. Si la
  causa ya está documentada, enlaza la entrada existente, no la dupliques.
- **Lección:** aprendizaje de proceso transversal con fuentes verificables;
  distingue lo cualitativo técnico de los números de calibración de la retro.

## Propuesta y persistencia

Localiza `$SHAREDKIT` con las raíces del runtime (regla 5 de CONVENTIONS). Prepara
la propuesta al descubrirla, cuando su evidencia está disponible, sin reconstruirla después.
Usa Markdown UTF-8 con frontmatter simple y cuerpo: `category` como propuesta según
la taxonomía, `evidencia` justificable, `fuentes` reales y `tags` `clave:valor`.
**Nunca incluyas `estado`.** Una decisión describe alternativas descartadas;
un gotcha incluye síntoma, causa raíz, qué hacer en su lugar y test de regresión.
Una entrada derivada o de backfill cita su fuente original: no añade conclusiones
que el material no respalde.

Envía ese Markdown por stdin, sin escribirlo antes en el árbol de memoria:

```bash
python3 "$SHAREDKIT/knowledge-curation.py" propose --filename <AAAA-MM-DD-slug.md> --producer <rol> --root <proyecto>
```

El nombre es portátil ASCII, hasta 128 caracteres; el contenido, hasta 256 KiB.
El servicio redacta el texto completo, crea sólo un candidato nuevo en
`candidates/pending/` y devuelve su ruta relativa y SHA256 de los bytes finales.
Un nombre existente en cualquier estado de candidatos o en approved no se recrea.
La API equivalente es `propose(root, filename, text, producer=...)`.

La salida es JSON: `status`, `errores`, `avisos` y rutas verificadas. Código 0
confirma operación; 1 rechaza el contrato; 2 indica uso, dependencia o IO no
verificable. Conserva ruta/SHA y evidencia en el handoff al Curator y al dueño
del ledger, con el contrato de asociación siguiente. **Sin fragmento
o servicio, informa propuesta pendiente de persistir en la salida o artefacto de
trabajo permitido y continúa; nunca uses Write/Edit, movimientos o un índice
manual para saltarte el servicio.** Sin nada que cruce el umbral, no hay pendiente.

Curator aplica su decisión con SHA esperado, motivo no vacío y, para aprobar,
ID final válido/prefijado, categoría exacta, versión inicial 1 y metadata suficiente.
El gate evalúa en solo lectura; el servicio valida y persiste la representación
final con `estado: aprobado`. Un `needs_changes` conserva la propuesta y registra
el motivo; no se corrige el candidato en sitio. `rejected` es terminal. Ni el
productor ni Curator editan, renombran o borran esos archivos manualmente.
Una corrección para approve se entrega por `replacement_text`/`--replacement-stdin`,
ligada al SHA original y validada/redactada por el servicio, sin edición de approved.
Las etiquetas de productor/decisor declaran roles; no autentican identidad nativa.

## Asociación explícita para retoma

Entrega la ruta `candidate` y el `sha256` originales que devolvió propose al
orquestador dueño de `tasks.md`. Planner incorpora los handoffs explícitos de
design al generar el plan. Antes de entregar la propuesta a apply, ese dueño
registra un único bloque top-level `curation-refs-v1` en el ledger seleccionado:
apertura exacta de tres backticks seguida de `curation-refs-v1`, array JSON y
cierre exacto de tres backticks. Sin indentación, citas, comentarios ni ejemplos.

El array admite hasta ocho referencias únicas y 8 KiB. Cada objeto contiene sólo
`candidate` (ruta relativa exacta bajo candidates/pending, needs_changes o rejected)
y `sha256` (64 hex minúsculas); puede añadir `operation_id` cuando lo devuelve el
servicio. Conserva la ruta/hash de la propuesta original incluso tras publicar
approved. No infieras referencias por fecha, basename o journal, ni reemplaces
una asociación conflictiva. Un límite o conflicto queda explícitamente pendiente.

Curator devuelve el operation-id y el recibo observado al mismo dueño tras
apply/recover; sólo ese dueño actualiza la asociación. Productores y Curator
conservan sus permisos actuales: este handoff no les permite editar roadmap.
Sin ledger, conserva los datos en la salida o artefacto permitido; la retoma
no inventa una asociación. La observación no ejecuta recover/apply ni aprueba
memoria: un recibo de persistencia no certifica QA o contenido approved vigente.

## Legado, journal y conflictos

ADR/GOT/LES existentes conservan bytes, IDs, estados, enlaces y autoridad original.
`aceptada` no se reinterpreta como `aprobado`: no se crean ni promueven entradas
nuevas en `adr/`, `gotchas/` o `lessons/`, ni se migra/reaprueba/borra el legado.
Su lectura selectiva sigue `knowledge-check.md`; candidatos no entran en búsqueda
ni exportación. Sólo approved sigue el contrato de publicación externa.

El journal es memoria de sesión episódica, no curada. Lo mantiene el hook con
`journal.py` (enriquecimiento explícito de la sesión mediante `write --enrich`);
`journal.py candidatas` sólo señala patrones. Una propuesta puede citar fecha,
ruta y `session_id`, pero repetir una observación no la convierte en verdad ni
escribe memoria automáticamente. Journal no se publica como doctrina ni se
indexa entrada por entrada en `docs/knowledge/README.md`.

Curator consulta approved y el legado aceptado pertinente. Una contradicción
entre ambos corpus o una decisión de alto impacto requiere resolución humana
trazada: fecha, score o ranking no deciden. La constitución prima. Una sucesión
explícita conserva referencias sin modificar incidentalmente el legado.
La retro ocurre después del Gate principal: entrega un handoff tardío al Curator
o deja ruta/ID de propuesta y estado pendiente visibles; su cierre no aprueba memoria.
