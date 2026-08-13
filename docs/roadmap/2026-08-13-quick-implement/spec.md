---
spec: quick-implement
descripcion: Skill auto-invocable por lenguaje natural que abre la VÍA RÁPIDA de /dev-cycle sin escribir el comando ("implementa X rápido", "hazme este cambio pequeño"). No duplica el método: delega en la vía rápida de commands/dev-cycle.md, su fuente única. Nace de una limitación real de Claude Code: los commands solo se disparan con la barra, las skills se activan por descripción
estado: implementada      # borrador | aprobada | implementada | obsoleta
creado: 2026-08-13
actualizado: 2026-08-13
evaluacion: n/a — vía rápida (ledger ligero: tasks.md)
plan: n/a — vía rápida (ledger ligero: tasks.md)
generacion:
  inicio: 2026-08-13T11:20:31Z
  fin: 2026-08-13T11:21:29Z
  fuente: medido
  tokens_reales: { entrada: 8, salida: 3031, cache_creacion: 6559, cache_lectura: 1715071 }
  eur: null
  horas_ia: 0.03
  duracion: 2m
  ratio_usado: 300000
---

# Vía rápida sin barra: skill `quick-implement`

> **Origen:** conversación del 2026-08-13. Pregunta del usuario: «¿y si no le digo `/dev-cycle`, simplemente "implementa xxx en modo rápido", también funciona?». **No**: los *commands* de `commands/` solo se invocan escribiendo la barra; el modelo no los lanza por lenguaje natural. Las *skills*, en cambio, **sí** se auto-invocan por su `description` (verificado contra la documentación oficial de Claude Code). De ahí esta spec. Anotada primero en backlog y **implementada el mismo día** como vía rápida a petición del usuario: ledger en [`tasks.md`](tasks.md).

## Problema

Sin la barra, una petición del tipo «implementa el endpoint /health, rápido» acaba en una implementación directa en el contexto principal: el código se escribe, pero **sin nada del aparato del plugin** — sin carpeta de iniciativa, sin `tasks.md` como ledger canónico, sin revisión adversarial de dos lentes, sin `qa-gate` y sin medición de coste. Se pierde justo lo que aporta valor.

## Idea

Una skill compartida `quick-implement` cuya `description` capture las frases naturales de "cambio pequeño ya" y cuyo cuerpo sea **una puerta de entrada delgada**, no un método nuevo:

1. **Resolver la fuente única**: `find` sobre `$PWD/.claude` y `$HOME/.claude` hasta `commands/dev-cycle.md`, leer su «Fase 0-bis → vía rápida» y seguirla (ledger ligero → implementación → revisión de dos lentes → qa → cierre). Si no lo encuentra: avisar y parar, nunca improvisar un método paralelo.
2. **Filtro de idoneidad** antes de arrancar: alcance de una o dos frases y pocos ficheros → adelante; incógnitas, varias fases o necesidad de presupuesto → proponer `/pm-cycle` o el flujo completo; trivial de verdad (un typo) → ofrecer hacerlo sin ciclo, porque el ledger no compensa.
3. **Cierre informativo**: decir explícitamente qué puertas pasó (revisión, qa) y qué se omitió por vía rápida (spec, evaluación, plan, presupuesto).

## Alcance

- `skills/quick-implement/SKILL.md` (solo prosa; sin scripts nuevos).
- Filas de doc: `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`; badge de skills 10 → 11 en ambos README (lo exige `tests/test_readme_badges.py`).
- **Implementado tal cual**: la mitigación del riesgo (disparadores en negativo + filtro de idoneidad obligatorio como Paso 1) forma parte de la skill entregada.
- Fuera: reimplementar la vía rápida (violaría DRY y la fuente única), y cualquier cambio en `commands/dev-cycle.md`.

## Riesgo principal (lo que hay que resolver bien)

**Que la skill secuestre peticiones que no le tocan.** Una `description` demasiado amplia haría que cualquier «cámbiame esto» arrancara rama, ledger y puertas — exactamente la sorpresa que la barra explícita evita hoy. Mitigación: disparadores redactados en negativo además de en positivo (el bloque «NO la uses si…»), y el filtro de idoneidad del punto 2 como primer paso obligatorio. Merece una prueba real en un proyecto consumidor antes de darla por buena.

## Contraargumento a favor de NO hacerla

La barra es un **acto deliberado**: garantiza que nadie arranca un ciclo con puertas por un comentario de pasada. Esta skill cambia ese contrato por comodidad. Si en la práctica escribir `/dev-cycle` no molesta, la skill añade superficie y riesgo sin ganancia real.

## Estimación gruesa

~1 h base (solo prosa + doc + badges). Valor: elimina la fricción de recordar el comando. Coste asumido: el riesgo de auto-invocación indebida, mitigado con disparadores negativos y el filtro de idoneidad — pendiente de **validación en un proyecto consumidor real** (si en la práctica secuestra peticiones, la corrección es afinar la `description`, no rehacer el método).
