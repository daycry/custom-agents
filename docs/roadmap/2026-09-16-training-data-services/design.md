---
design: training-data-services
estado: aprobado
opcion_elegida: O1
spec: spec.md
evaluation: evaluation.md
plan: improvement-plan.md
---

# Diseno - captura de casos y ensamblado de dataset

## Opciones consideradas

| Opcion | Descripcion | Decision |
|---|---|---|
| O1 | Skill propia con esquema/recorder/ensamblador genericos; metricas y validacion siempre del proyecto. | **Elegida.** |
| O2 | Capacidad integrada en la skill `knowledge-services`. | Descartada: mezcla un ciclo de alto volumen sin curar con uno de bajo volumen curado. |
| O3 | El plugin ejecuta o llama a herramientas de dominio (Blender, simulacion). | Descartada: acopla el plugin a un dominio concreto; rompe "base para todos los proyectos". |
| O4 | Deduplicacion por embeddings/modelo semantico. | Descartada: anade dependencia y servicio para un problema que shingles deterministas ya resuelven (mismo criterio que ADR-013). |

## Esquema de un caso

```text
<root>/                          # declarado por el proyecto en training.json; el plugin no impone nombre
├── cases_index.jsonl            # append-only: {case_id, version, family, variant, status, outcome, updated_at}
├── cases/<family>.<variant>/
│   └── v<NNN>/
│       ├── metadata.json        # case_id, family, variant, version, created_at, outcome, supersedes_case
│       ├── request.json         # peticion LITERAL del usuario/proceso, sin normalizar
│       ├── context.json         # contexto normalizado (esquema libre, lo define el proyecto)
│       ├── constraints.json     # restricciones (esquema libre, lo define el proyecto)
│       ├── trajectory.jsonl     # una linea JSON por turno (ver formato abajo)
│       ├── metrics.json         # metricas YA CALCULADAS por el proyecto (opaco para el plugin)
│       ├── validation.json      # {status, approved_by_human, approved_at, reviewer_note}
│       └── final/                # SOLO referencias: {path, hash, kind} — nunca contenido binario inline
└── exports/<export_id>/
    ├── manifest.json            # que case_id@version entraron, hash de cada uno, asignacion train/benchmark
    ├── train.jsonl
    └── benchmark.jsonl
```

`metadata.json.outcome` ∈ `success` | `failure` | `corrected`. Un caso `corrected` declara `supersedes_case: "<case_id>@v<NNN>"`, conservando el par fallo→correccion como dato de primera clase (el de mas valor segun la practica de dominio citada), sin fusionar ni borrar el intento fallido.

## Formato de trayectoria (compatible con SFT, sin atarse a un framework)

Cada linea de `trajectory.jsonl` es un turno, con la misma forma que usan la mayoria de formatos de fine-tuning por chat:

```json
{"role": "system", "content": "...", "ts": "2026-09-16T10:00:00Z"}
{"role": "user", "content": "...", "ts": "..."}
{"role": "assistant", "content": "...", "tool_calls": [{"name": "...", "arguments": {...}}], "ts": "..."}
{"role": "tool", "name": "...", "content": "...", "ts": "..."}
```

Reglas: **nunca** se guarda chain-of-thought privado (mismo principio que `journal.py` T-12: solo el turno observable, no el razonamiento interno). El ensamblador de dataset concatena `trajectory.jsonl` de un caso en un array `messages`, listo para exportarse en formato JSONL compatible con las herramientas de fine-tuning habituales (mensajes `system`/`user`/`assistant`/`tool`), sin comprometerse a un entrenador concreto.

## Redaccion de secretos compartida (una sola fuente de verdad)

> **Enmienda 2026-09-17**: la extraccion a `agent-kits/shared/redact.py` la entrega `session-end-durable-capture` (T-02); esta iniciativa la consume. El texto siguiente describe el resultado, no una tarea de esta iniciativa.

`journal.py` ya tiene una funcion `redactar()` probada (claves con prefijo conocido, JWT, PEM, `Bearer`, `clave|token|password = valor`). Se extrae a `agent-kits/shared/redact.py` como modulo compartido; `journal.py` pasa a importarla y el recorder de casos la aplica a `request.json`/`context.json`/`trajectory.jsonl` ANTES de escribir a disco. Ninguna logica de redaccion se duplica.

## Deduplicacion determinista (sin embeddings, mismo criterio que ADR-013)

Se reutiliza la tecnica de shingles/Jaccard que ya usa `skills/code-health/scripts/code-health.py` para detectar codigo duplicado, aplicada al contenido variable de cada caso (peticion + contexto + trayectoria, EXCLUYENDO boilerplate fijo que se repetiria en todos los casos y daria falsos positivos). Dos casos con similitud ≥ un umbral configurable se marcan como near-duplicates en el manifiesto del export; el ensamblador conserva solo uno por grupo salvo que el proyecto pida lo contrario explicitamente.

## Particion anti-leakage (benchmark reservado)

La particion se hace por **familia completa**, nunca por version suelta: si una familia tiene versiones v001..v009, o TODA la familia va a train, o TODA va a benchmark. Esto evita el riesgo que la propia practica de dominio senala (leakage de versiones casi identicas entre train y test). El export exige al menos una familia reservada como benchmark antes de generar `train.jsonl`; sin eso, el ensamblador se niega a exportar y explica por que.

## Aprobacion humana explicita (Gold)

Transicionar `validation.status` a `approved` exige el flag `--approved-by-human` en el recorder; sin el, la operacion se rechaza (mismo patron que el flag `--qa-verde` de `jira-flow.py`, que exige evidencia leida por un humano antes de cerrar un issue). `needs_changes`/`rejected` no exigen el flag: no son promociones, son estados intermedios que el propio codigo del proyecto puede fijar.

## Puente a `knowledge-curator` (opt-in, nunca automatico)

Un caso Gold puede proponerse como candidato de conocimiento con un comando explicito que arma el candidato (categoria del `taxonomy.json` del proyecto, `source_cases: [case_id@version]`, evidencia `validated_case`) y lo entrega al Knowledge Gate de `knowledge-services`. La aprobacion del candidato sigue las mismas reglas que cualquier otro: nunca automatica por venir de un caso Gold.

## Que NO hace el plugin

- No calcula ninguna metrica de dominio ni interpreta `metrics.json` semanticamente: solo valida que sea un objeto JSON.
- No ejecuta fine-tuning, no sirve modelos, no corre benchmarks.
- No acepta contenido binario inline (mallas, imagenes, audio): solo referencias con ruta y hash.
- No marca Gold automaticamente bajo ninguna circunstancia.
