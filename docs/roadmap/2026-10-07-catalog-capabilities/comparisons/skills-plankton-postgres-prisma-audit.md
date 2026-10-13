# Calidad al escribir, PostgreSQL, Prisma y preparación para producción — S207, S208, S211, S214

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **39.818 bytes/1.084 líneas**, sin recursos locales.
[plankton-postgres-prisma-audit-reading-evidence.json](plankton-postgres-prisma-audit-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S207 — Calidad en cada edición (Plankton)

`12.896 bytes/328 líneas`. Un hook `PostToolUse` formatea y pasa linters en cada
edición, lanza subprocesos `claude -p` (Haiku, Sonnet u Opus según la violación,
hasta 600 s) para corregir lo que queda y sale con 2 si siguen violaciones.
Hooks `PreToolUse` bloquean editar configuraciones de linter y usar `pip` o
`npm`. Termina con una sección propia sobre un **techo de complejidad de
trinquete**.

**Comparación.** El diseño choca con ADR-007: los hooks globales informan y un
deny solo vive en el alcance de un agente. Aquí bloquean por política del
proyecto de origen, e invocan modelos desde un hook con un coste que el usuario
no ve. **No se adopta el mecanismo.** Quedan dos ideas con dueño claro:

| Idea | Encaje |
|---|---|
| Un agente que relaja la configuración (desactiva reglas, añade supresiones, baja umbrales, salta tests) en vez de corregir el código | Criterio para la Lente A en `skills/adversarial-review/references/lens-prompts.md`: una relajación de linter, tests o umbral que el plan no justifica es gap Important. Se revisa en el diff, no se bloquea por hook |
| Trinquete: el techo se fija en el peor valor medido (más un margen), nunca se excluyen ficheros y se baja a mano en un commit propio cuando se simplifica un punto caliente | `code-health` ya compara con `--baseline`; una línea que explique ese uso. Imponer el techo es tarea de la CI del proyecto, no del plugin, que sigue saliendo con 0 |

| La pieza | Problema |
|---|---|
| Tabla «Complementarios, sin solape» | La sección siguiente resuelve un conflicto entre el formateador de un hook y el de otro en JS/TS |
| La lista de configuración protegida incluye `pyproject.toml` y `tsconfig.json` | Cualquier cambio de dependencias exigiría revisión; el criterio debe mirar reglas y umbrales relajados, no nombres de fichero |
| «Corrige el 40-50 % de los problemas en silencio» | Cifra sin fuente |
| Bloquea `npm install` y deja pasar `npm publish` | Política de un proyecto impuesta a todos |

La sección del trinquete es la mejor parte: cita su fuente con fecha, separa lo
verificado de la práctica propia del autor y avisa de que la plantilla JSON no
es válida hasta medir.

**Destino:** el criterio de relajación en la Lente A y una línea de uso del
`--baseline` como trinquete en `skills/code-health/SKILL.md`.

## S208 — Patrones de PostgreSQL

`3.914 bytes/148 líneas`. Chuleta de índices, tipos, índices compuestos,
cubrientes y parciales, RLS, upsert, paginación por cursor, cola con
`SKIP LOCKED`, consultas de diagnóstico y una plantilla de configuración.

**Comparación.** `backend-practices` es el dueño; `references/contracts-data.md`
ya exige orden total con desempate en la paginación, allowlist de ordenación,
revisar N+1 y migrar en fases. S070
([skills-data-pipelines-research.md](skills-data-pipelines-research.md)) fijó
como destino una referencia `database-migrations.md` en esa misma skill, que aún
no existe. Las correcciones de abajo son para ella:

| Ejemplo | Adaptación |
|---|---|
| Plantilla `ALTER SYSTEM SET max_connections = 100` seguida de `pg_reload_conf()` | `max_connections` solo cambia al reiniciar el servidor; recargar no basta |
| `statement_timeout = '30s'` global | También corta migraciones, backfills y tareas largas; fijarlo por rol o sesión |
| Cola: `UPDATE … SET status = 'processing' … FOR UPDATE SKIP LOCKED` | Un worker que cae deja el trabajo en `processing` para siempre; hace falta plazo de reclamación y procesado idempotente |
| Cursor `id > $last_id ORDER BY id`, «O(1) frente a O(n)» | Vale solo ordenando por `id`, y no es O(1): es una búsqueda en índice |
| Consulta de FK sin índice con `a.attnum = ANY(i.indkey)` | Da por bueno un índice con la columna en cualquier posición; uno donde no es la primera no sirve para buscar por la FK |
| `bigint` antes que UUID, `text` antes que `varchar(255)`, `numeric(10,2)` para dinero | Preferencias, no reglas: el tope de `numeric(10,2)` y sus dos decimales dependen de la moneda |
| RLS con `(SELECT auth.uid())` | `auth.uid()` es de Supabase, no de PostgreSQL |

**Destino:** las dos primeras filas y la de la cola, en la futura
`skills/backend-practices/references/database-migrations.md`. Sin skill nueva.

## S211 — Patrones de Prisma

`15.281 bytes/401 líneas`. Estrategia de ID, `include` frente a `select`, forma
de transacción, cliente único, N+1, paginación por cursor, borrado lógico,
códigos de error y trampas: `updateMany` devuelve un recuento, `migrate dev`
puede resetear la base y `@updatedAt` no se aplica en escrituras masivas.

**Comparación.** Es un ORM de backend TypeScript, y ningún consumidor ha
declarado ese stack (`stack-practices` cubre React en frontend). No se abre
especialidad. Lo transversal ya está en `contracts-data.md`: campos expuestos
explícitos (aquí, mapear a DTO), servicio externo fuera de la transacción, N+1 y
migración en fases. Los comandos de migración de Prisma ya se contrastaron en
S070. Correcciones para cuando haya consumidor:

| Ejemplo | Adaptación |
|---|---|
| Arreglo de `updateMany`: `findMany` de IDs → `updateMany` → `findMany` | Tres sentencias sin transacción: entre la lectura y la escritura pueden cambiar las filas; envolverlas o repetir el predicado en la escritura |
| Backfill en un solo `updateMany` sobre toda la tabla | Sin lotes ni reanudación; `contracts-data.md` pide un backfill que tolere corte y reintento |
| La cabecera dice que `relationJoins` «puede» cargar con JOIN; la tabla dice «usa JOIN por defecto» | Contradicción interna; comprobar la versión y la configuración del proyecto |

**Destino:** ninguno hasta que un consumidor declare backend TypeScript con
Prisma.

## S214 — Auditoría de preparación para producción

`7.727 bytes/207 líneas`. Auditoría con evidencia local: superficie de release,
cambios recientes, límites de autenticación, datos, pagos, trabajos en segundo
plano y despliegue; nota de 0 a 100 con topes y recomendación de publicar o
bloquear.

**Comparación.** Lo cubren varias piezas con dueño: `delivery-practices`
(readiness, configuración, rollback), `backend-practices` (idempotencia,
autorización), `nemesis` (seguridad) y `qa` (recorridos E2E). No hace falta una
pieza nueva (ADR-011). La pieza dice que la nota «no implica certeza», pero sus
bandas y topes deciden «no publicar»: es una puntuación del modelo usada como
veredicto. Aporta tres cosas que el plugin no tiene escritas:

| Idea | Encaje |
|---|---|
| Salida con **evidencia comprobada** y **evidencia ausente** («qué cambiaría la confianza») | Línea en `skills/delivery-practices/references/delivery-tools.md` |
| Variables de entorno requeridas validadas al arrancar, con fallo inmediato; CI verde no es preparación para producción | Misma referencia, en el contrato de entrega |
| Webhook entrante: verificar la firma antes de interpretar el cuerpo; idempotente por evento; tolerar duplicados, repeticiones y desorden | Fila nueva en la tabla de `skills/backend-practices/references/contracts-data.md` |

Defecto: el ejemplo propone un health check que comprueba la base **y el
proveedor de pagos**. Si ese check se usa como liveness, la caída del proveedor
reinicia la aplicación; `delivery-tools.md` ya separa readiness de liveness por
ese motivo.

**Destino:** las dos líneas en `delivery-tools.md` y la fila de webhooks en
`contracts-data.md`. Sin nota numérica.
