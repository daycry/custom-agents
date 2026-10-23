# Revisión de código general, C++, C# y base de datos — A008, A013, A014, A016

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **28.855 bytes/614 líneas**. [agents-review-cpp-csharp-db-reading-evidence.json](agents-review-cpp-csharp-db-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las cuatro.** Tienen las mismas tools que el `reviewer` propio (Read, Grep,
Glob, Bash) y el mismo bloque «Prompt Defense Baseline» (líneas 8-15, sin destino).
El dueño es la pareja método/ejecutor de ADR-011 (`docs/agents/ROLES.md:58-60`). La skill
`adversarial-review` decide las lentes: A y B siempre; C y D cuando las activa
`review-lens-select.py`. También funde los resultados y los gradúa como
Critical/Important/Minor (`SKILL.md:95-102`). `reviewer` ejecuta una lente en contexto
fresco y sin modificar código (`agents/reviewer.md:45-50`). Regla única de stacks: C++
y .NET no tienen especialidad hasta que un consumidor declare el stack.

## A008 — code-reviewer

`13.877 bytes/323 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor
único del diff (`git diff --staged` y `git diff`). Recorre un checklist de seguridad,
calidad, React/Next, backend, rendimiento y buenas prácticas. Solo reporta con más
del 80 % de confianza, pasa una puerta previa de cuatro preguntas, filtra una lista de
falsos positivos y emite un veredicto Approve/Warning/Block.

**Comparación.** Hay tres coincidencias con lo propio. Una revisión limpia es válida
(líneas 66-74; `reviewer.md:89`, `SKILL.md:139`). Un hallazgo exige línea y escenario
(puerta 1-2, líneas 44-48; `reviewer.md:89-90`). Un HIGH/CRITICAL exige prueba
(55-64; racionalizaciones de `SKILL.md:137-138`). Las diferencias son de
responsabilidad. Hace una sola pasada con todas las lentes mezcladas y sin contexto
fresco por criterio. No tiene Lente A: no comprueba la conformidad con spec, plan ni
constitución. Incluye estilo (LOW: formato, nombres, números mágicos, JSDoc), que la
regla dura propia descarta (`SKILL.md:22-24`). Su «MUST BE USED for all code changes»
se solapa con la puerta de `/dev-cycle` Fase 3. Defectos:

- **Contradicción interna.** Pone «Large functions (>50 lines)» y «Large files (>800 lines)»
  como HIGH (147-148), pero su propia lista marca «Function too long» como falso
  positivo (89-90). `coding-baseline.md:19-21` ya trata la longitud como indicador, no como defecto.
- **Dependencias vulnerables.** «Insecure dependencies — known vulnerable packages» (125)
  en una revisión de diff es auditoría de dependencias. En el plugin es de `nemesis` (`SKILL.md:35-36`).
- **Coste de modelos.** El addendum v1.8 (321-323) lo pide sin criterio verificable;
  el modelo por agente ya lo fija `model-tier.py`.

Lo que el plugin **no** tiene: «antes de señalar validación o manejo de error
ausente, sigue al menos un llamante» (49-50, 81-85). La Lente B
(`references/lens-prompts.md:21`) pide un escenario concreto, pero no esa
comprobación. La Lente C ya filtra con `cybersecurity/references/false-positive-suppression.md`.
La Lente D exige escenario de carga y orden de magnitud (`lens-prompts.md:29`), lo
que ya descarta el N+1 de cardinalidad fija (líneas 97-98 de la fuente).

**Destino:** línea en `skills/adversarial-review/references/lens-prompts.md`, Lente
B: «Antes de reportar una validación o un manejo de error ausente, sigue al menos un
llamante o el marco que lo gestiona; si un nivel superior ya lo cubre, no es gap». El
resto ya está cubierto.

## A013 — cpp-reviewer

`3.972 bytes/81 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor C++:
seguridad de memoria, seguridad, concurrencia, calidad y rendimiento, con
`clang-tidy` y `cppcheck`.

**Comparación.** Su método es el de `reviewer` y las lentes B, C y D. El material de
C++ espera en D-124 (`cpp-practices`, aparcado). Correcciones para cuando se abra:

| Línea | Dice | Corrección |
|---|---|---|
| 75-79 | Bloquea con HIGH | A008 (292-295) trata HIGH como Warning: dos escalas en el mismo catálogo; la propia gradúa por definición |
| 46 | «Detached threads: `std::thread` without `join()` or `detach()`» | El defecto es el hilo que no se une ni se desprende (`std::terminate` al destruirse); el título dice lo contrario |
| 70 | `clang-tidy --checks='*,-llvmlibc-*'` | Activa todas las familias, también guías de estilo ajenas; el ruido resultante lo descarta la regla dura |
| 33 | «Null dereference: pointer access without null check» | Invita al falso positivo que A008 (95-96) manda saltar: hay que trazar el tipo |

**Destino:** **Sin especialidad** hasta que un consumidor declare C++ (D-124).

## A014 — csharp-reviewer

`5.692 bytes/110 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor
C#/.NET: seguridad, errores, async, tipos, calidad y rendimiento, con comprobaciones
de ASP.NET Core, EF Core, Minimal APIs y Blazor. Usa `dotnet build`, `dotnet format`
y `dotnet test`.

**Comparación.** Igual que A013. El material de .NET está en D-123 (aparcado).
Ejecutar `dotnet test` con cobertura como evidencia es coherente con `reviewer.md:48-50`. Correcciones:

| Línea | Dice | Corrección |
|---|---|---|
| 31 | «`JsonSerializer` with `TypeNameHandling.All`» | `TypeNameHandling` es de Newtonsoft.Json (`JsonSerializerSettings`); `System.Text.Json.JsonSerializer` no tiene esa opción |
| 36 | `catch { }` vacío como CRITICAL | Infla la severidad: el propio reserva Critical para pérdida de datos, seguridad explotable o criterio que rompe el objetivo (`SKILL.md:99-101`) |
| 66, 70 | Naming y `sealed` como MEDIUM | Estilo: se descarta salvo que la constitución lo fije |

**Destino:** **Sin especialidad** (D-123).

## A016 — database-reviewer

`5.314 bytes/100 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Especialista PostgreSQL/Supabase: rendimiento de consultas, esquema, RLS, pooling y
concurrencia. Consulta `pg_stat_statements` con `psql $DATABASE_URL`.

**Comparación.** El método ya tiene dueño en `backend-practices`.
`references/database-migrations.md` cubre bloqueos, `CONCURRENTLY`, el estado a
medias, el backfill y `SKIP LOCKED` (:70, :81). `references/contracts-data.md` cubre
paginación, N+1 e interbloqueo. Ambas se integraron desde S071/S208 (D-021). La
persona `agent-kits/shared/personas/db.md:3-7` se aplica a la Lente B y a los
subagentes con `Tipo: db`. La Lente D cubre el N+1 del diff. Sus permisos son
incoherentes: las tools son de solo lectura, pero las responsabilidades «Implement
RLS», «Configure pooling» y «Set up monitoring» (23-28) son de escritura. Defectos:

- **Conexión a una base viva.** Conecta con `psql $DATABASE_URL` (33-36), es decir, a la
  base del entorno, que puede ser producción. El `reviewer` propio usa Bash solo para tests y scripts locales.
- **`EXPLAIN ANALYZE`.** Lo pide (43) sin avisar de que
  [ejecuta la sentencia](https://www.postgresql.org/docs/current/sql-explain.html): en
  INSERT/UPDATE/DELETE aplica el cambio. Ni la persona `db` ni `database-migrations.md` lo advierten.
- **`auth.uid()`.** `(SELECT auth.uid())` (53, 86) es de Supabase, no de PostgreSQL. Ya se corrigió en S208.
- **Cifras sin base.** «Index foreign keys — always, no exceptions» (60) y «SKIP LOCKED 10x
  throughput» (63) no citan medida. El cursor `id > $last` tiene la misma limitación que señaló S208.

**Destino:** dos líneas. (1) En `agent-kits/shared/personas/db.md`, «Calidad
exigible»: «el plan se revisa con `EXPLAIN`; `EXPLAIN ANALYZE` ejecuta la sentencia,
así que con DML va dentro de una transacción con `ROLLBACK` y nunca contra una base
compartida o de producción». (2) En `agents/reviewer.md`, «Reglas duras»: «Bash no
abre conexiones con credenciales del entorno (`$DATABASE_URL`, tokens): la evidencia
sale de tests y scripts locales». El resto ya está integrado (D-021).
