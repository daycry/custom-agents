# Revisores por stack y por dominio — A018, A022–A024, A029, A032

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis definiciones completas: **40.431 bytes/786 líneas**. [agents-stack-domain-reviewers-reading-evidence.json](agents-stack-domain-reviewers-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las seis.** Bloque «Prompt Defense Baseline» idéntico (líneas 8-15), el mismo
de A001–A017. El plugin trata el contenido externo como dato en la pieza que lo recibe
(D-001, D-071, D-074). **Sin destino.**

**Regla aplicada.** Revisar un diff tiene dueño: la skill `adversarial-review`, que
despacha cada lente al agente `reviewer` (`skills/adversarial-review/SKILL.md:77-93`). Ese
agente es de solo lectura y revisa contra un criterio fijado por la lente
(`agents/reviewer.md:53-56`). El criterio por stack sale de `stack-practices`, que solo cubre
PHP/CodeIgniter, Python y React. Los stacks y frameworks sin consumidor quedan aparcados
(regla única de `skills-destinations.md:11`). Ninguno de estos seis agentes abre un rol nuevo:
la diferencia está en el checklist, no en la responsabilidad.

Diferencias de procedimiento comunes a A018, A023, A024 y A029. Las cuatro bloquean con
cualquier hallazgo HIGH, y su HIGH mezcla defectos con estilo. El plugin gradúa por
definición: Critical/Important obligan a corregir y Minor no bloquea
(`skills/adversarial-review/SKILL.md:99-102`). Además prohíbe el estilo
(`agents/reviewer.md:92-95`, «Reglas duras»). En el plugin, un gap sin `fichero:línea` y sin
escenario concreto no cuenta como gap (`agents/reviewer.md:90-91`). Las cuatro fuentes se
conforman con «Issue/Fix».

## A018 — django-reviewer

`7.985 bytes/169 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor Django/DRF:
seguridad, ORM, migraciones, DRF, rendimiento, Celery y huecos de test, con `manage.py check`,
ruff, mypy y bandit.

**Comparación.** Lo transversal ya tiene dueño. El N+1 lo cubren la Lente D
(`lens-prompts.md:29`) y `contracts-data.md:24`. Los campos explícitos en la serialización
(frente a `fields='__all__'`) están en `contracts-data.md:24`, la paginación con límite en
`:22` y las migraciones en dos fases en `backend-practices/references/database-migrations.md:4`.
La Lente C cubre `csrf_exempt`, `SECRET_KEY` y `eval`. Los permisos son los mismos que los de
`reviewer`. Lo que el plugin no tiene es la especialidad Django, aparcada como D-128.
Defectos de la fuente:

| Línea | Dice | Corrección |
|---|---|---|
| 54 | `bulk_create` sin `update_conflicts` = «pérdida silenciosa de datos» | Sin `ignore_conflicts` lanza `IntegrityError`. Lo silencioso es `ignore_conflicts=True` |
| 115 | `blank=True` sin `null=True` en campos no texto: «la base guarda cadena vacía» | No la guarda: el formulario acepta el vacío y el `save()` falla o exige un valor por defecto |
| 124 | Sin `@pytest.mark.django_db` los tests «no tocan la base en silencio» | pytest-django falla de forma explícita al acceder a la base («Database access not allowed») |
| 26 | Supone CI en verde y, si duda, ejecuta `gh pr checks` | Depende de la red y de GitHub. El plugin revisa con la evidencia que ejecuta él |
| 19 | Exige que `python-reviewer` haya pasado antes o después | Encadena revisores sin orquestador. En el plugin la fusión es de la skill (§3) |

**Destino:** **Sin destino nuevo.** Lo transversal ya está integrado en `backend-practices`
y en las Lentes C y D. Django sigue aparcado (D-128). Las tres correcciones de la tabla se
anotan en la fila D-128 para cuando un consumidor declare Django.

## A022 — fastapi-reviewer

`3.514 bytes/79 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor FastAPI:
construcción de la app, modelos Pydantic, async, inyección de dependencias, CORS,
overrides de test y OpenAPI.

**Comparación.** La pieza más sobria del grupo: alcance y fuera de alcance explícitos
(líneas 19-33), ejecuta comprobaciones locales «cuando sea seguro» y cierra con
`Tests checked` y `Residual risk` (líneas 76-79). El `reviewer` del plugin pide lo mismo
con «Lo ejecutado» (`agents/reviewer.md:87`) y con «no verificable» por criterio (`:70-74`). El
cliente bloqueante dentro de async está en `stack-practices/references/python.md:8`. El
override de test que apunta a la dependencia equivocada equivale a `python.md:39`
(monkeypatch sobre la referencia que usa el módulo). Los modelos de respuesta y los errores
de OpenAPI son de `api-contract`. Los timeouts y la paginación están en
`contracts-data.md:22-25`. Su CORS `*` con credenciales es un hallazgo correcto: Starlette
refleja el origen si hay cookies. Le corresponde a la Lente C.

**Destino:** **Sin destino.** Queda cubierto por `python.md`, `backend-practices`,
`api-contract` y la Lente C. FastAPI sigue aparcado (D-129).

## A023 — flutter-reviewer

`15.239 bytes/252 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor Flutter/Dart:
arquitectura por capas, gestión de estado, composición de widgets, rendimiento, ciclo de vida,
accesibilidad, i18n y seguridad móvil. Declara «no refactorizas» (línea 25).

**Comparación.** El grupo de checklist coincide con S104, ya aparcada como D-134. El control
de ruido de las líneas 60-64 (consolidar hallazgos similares, confianza > 80 %, no marcar
código sin cambios salvo seguridad CRITICAL) equivale a lo que el plugin ya exige: solo el
diff (`lens-prompts.md:29`, «SOLO el diff») y un escenario concreto. Diferencias:

| Línea | Dice | Problema |
|---|---|---|
| 107-114, 250 | «Hardcoded spacing» y la falta de `const` son HIGH, y cualquier HIGH bloquea | Contradice su propia regla de saltarse las preferencias de estilo (línea 63) |
| 45, 214 | Ante seguridad CRITICAL «para y pasa a `security-reviewer`» | Ese agente no existe en el plugin. La seguridad del diff es de la Lente C, la auditoría de `nemesis` |
| 157 | Exige Crashlytics/Sentry | Elige proveedor. `stack-practices` no elige librerías (`SKILL.md:26`) |

**Destino:** **Sin destino nuevo.** Dart/Flutter sigue aparcado (D-134). Los criterios de
accesibilidad web equivalentes ya están en `frontend-quality`.

## A024 — fsharp-reviewer

`5.618 bytes/109 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor F#: seguridad
.NET, errores, idioms funcionales, seguridad de tipos, rendimiento y Giraffe/Saturn/EF/Fable.

**Comparación.** El mismo esquema de A029, con `dotnet build` y `fantomas --check`. Hay
dos HIGH que bloquean y son de estilo: «bucles imperativos donde `List.map` es más claro»
(línea 44) y «funciones de más de 40 líneas» (línea 55). Los dos los descarta la regla dura
de `reviewer`. Lo que sí es corrección (excepciones tragadas con `with _ -> ()`, `.Result`
bloqueante, `_` comodín que oculta nuevos casos de la unión) lo cubre la Lente B sin
especialidad.

**Destino:** **Sin destino nuevo.** .NET/F# sigue aparcado (D-123).

## A029 — go-reviewer

`3.771 bytes/85 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Revisor Go: seguridad,
manejo de errores, concurrencia, calidad, rendimiento y buenas prácticas, con vet, staticcheck,
`-race` y govulncheck.

**Comparación.** No tiene formato de salida (sin `fichero:línea`). Pone como CRITICAL el
`return err` sin envolver (línea 38): envolver es una decisión de API, porque `%w` expone el
error interno como contrato. También marca como «misuse» no usar `defer mu.Unlock()` (línea
46), y en bucles calientes no siempre lo es. `govulncheck` (línea 76) descarga la base de
vulnerabilidades: buscar CVE es de `nemesis`, no de la revisión del diff.

**Destino:** **Sin destino nuevo.** Go sigue aparcado (D-125).

## A032 — healthcare-reviewer

`4.304 bytes/92 líneas` · tools: Read, Grep, Glob · model: opus. Revisor clínico: precisión del
apoyo a la decisión clínica (CDSS), exposición de datos de salud (PHI), integridad clínica,
mapeos ICD-10/SNOMED y HL7/FHIR.

**Comparación.** Es el único del grupo sin Bash, más estricto que `reviewer`, pero así no
puede ejecutar la evidencia que el plugin exige. Su dominio coincide con S120–S126, ya
declaradas **Fuera del bundle** (`skills-growthlog-healthcare-imports.md:25-49`,
`skills-hexagonal-hipaa-homelab.md:31-39`). Las reglas «ante la duda, NEEDS REVIEW» y
«una fuga de PHI siempre es CRITICAL» (líneas 89-91) encajan con la graduación por definición.
El checklist da por hecho Supabase (`service_role`, RLS, líneas 44-45) como si fuera general.
Si un consumidor lo necesita, su cauce es una persona de dominio del proyecto:
`.claude/personas/<tipo>.md`, que la Lente B antepone cuando la tarea lleva `Tipo`
(`lens-prompts.md:22-26`).

**Destino:** **Especialidad de proyecto** (persona `.claude/personas/clinico.md` del
consumidor, con fuentes clínicas propias). Fuera del bundle.

## Incidencia en una pieza propia

`agents/reviewer.md` no conoce la Lente D. La skill despacha hasta cuatro lentes al agente
`reviewer` («C solo si `lente_c`; D solo si `lente_d`», `SKILL.md:90-92`), pero el agente
solo lista A, B y C en la `description` (línea 3), en «Entrada» (líneas 53-56) y en la
cabecera de salida (`Lente <A|B|C>`, línea 81). Un revisor de Lente D recibe un prompt cuya
lente no reconoce su propia definición. Propuesta P1 en «Incidencias» del informe.
