---
spec: dev-cycle-dataset
estado: aprobada
creado: 2026-09-16
actualizado: 2026-09-16
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
---

# Adaptador de dataset sobre el propio ciclo de desarrollo (dogfooding)

> [Evaluacion](evaluation.md) · [Diseno](design.md) · [Plan](improvement-plan.md)

## Objetivo

Aplicar el mecanismo generico de `training-data-services` al propio `/dev-cycle`, como PRIMER adaptador de dominio real: cada tarea `T-XX` cerrada se traduce en un caso (peticion, contexto, trayectoria, metricas, validacion) usando SOLO senales ya deterministas que el ciclo produce hoy (ledger, revision adversarial, `qa-gate.py`, `usage-meter.py`). Ningun juicio del LLM decide el `outcome` ni la `validation`: los deciden los mismos scripts que ya gobiernan el ciclo.

Es la validacion de que el mecanismo de `training-data-services` generaliza a un dominio real antes de que otro proyecto (p. ej. uno con simulacion fisica) confie en el. Es tambien la fuente inicial de un dataset propio de "tarea -> implementacion -> veredicto -> correccion" acumulable a traves de TODOS los proyectos que usen este plugin.

## Dependencias

Depende de `training-data-services` (usa su esquema de caso, `case-recorder.py`, deduplicacion y ensamblador tal cual). No depende de `graphiti-memory`. No requiere ningun cambio en `knowledge-services` mas alla del puente opcional que `training-data-services` ya define.

## Alcance

- Opt-in en `.claude/dev.json` (`"datasetCapture": {"enabled": false, "mode": "metadata"}`), en la misma familia de opciones que `tdd`/`worktree`/`subagentes`.
- Adaptador (script, sin agente nuevo) que en la **Fase 6 (ritual de cierre)** de `/dev-cycle` traduce cada `T-XX` cerrada de la iniciativa a un caso: `request` desde `- **Descripcion**:`, `context` desde spec/plan/design/persona, `constraints` desde los criterios de aceptacion y `- **Archivos**:`.
- **Modo `metadata` (default):** la trayectoria NO incluye el diff de codigo fuente completo; incluye solo metadatos deterministas — ficheros tocados (rutas relativas), comandos ejecutados (`- **Verificacion**:`), y el resumen ya redactado del campo `- **Changelog**:`. Nunca contenido propietario del diff.
- **Modo `full-diff` (opt-in EXPLICITO y por separado, con aviso de riesgo):** incluye ademas el diff real de la tarea. Requiere que el usuario lo active a sabiendas (doble opt-in: activar la captura Y activar `full-diff`).
- `outcome`/`validation` **derivados 100% de scripts existentes**: `ledger-lint.py` (coherencia), `qa-gate.py` (exit code), el ultimo veredicto de `adversarial-review` (gaps Critical/Important pendientes o no) y la presencia de marcadores `usage-meter` `T-XX-fix<N>` (indica `failure` -> `corrected`).
- **Familia = iniciativa** (`docs/roadmap/<fecha>-<slug>/`), variante = `T-XX`: reserva la iniciativa ENTERA como benchmark si aplica, nunca tareas sueltas de la misma iniciativa — evita fugar correcciones casi identicas entre train y benchmark dentro del mismo ciclo.
- Aprobacion humana (Gold) en el **mismo punto donde ya decide un humano** hoy: la puerta de integracion/merge del ritual de cierre (Fase 6, paso 4). Usa el mismo flag `--approved-by-human` de `case-recorder.py`.
- Reutiliza `redact.py` (de `training-data-services`) sobre cualquier texto capturado.

## Fuera de alcance

- `full-diff` como default: siempre opt-in explicito.
- Cualquier entrenamiento, benchmark o servicio de modelo: sigue siendo responsabilidad de quien consuma el dataset.
- Aplicarlo a iniciativas de otros proyectos que no sean este repo (cada proyecto que quiera dogfooding sobre SU propio ciclo escribe su propio adaptador siguiendo este mismo patron).
- Cambiar el comportamiento de `/dev-cycle` cuando `datasetCapture` no esta activo: cero impacto.

## Criterios de aceptacion

- [ ] CA-01 - Con `datasetCapture` desactivado (default), `/dev-cycle` funciona identico a hoy.
- [ ] CA-02 - En modo `metadata` (default), ningun caso contiene el diff de codigo fuente completo.
- [ ] CA-03 - `full-diff` exige un opt-in EXPLICITO distinto del opt-in de activacion; activar solo `datasetCapture` nunca incluye el diff.
- [ ] CA-04 - `outcome` y `validation` se derivan de `ledger-lint.py`/`qa-gate.py`/veredicto de revision/marcadores `usage-meter`, nunca de un juicio del LLM.
- [ ] CA-05 - La familia de un caso es la iniciativa completa; la particion de benchmark de `training-data-services` nunca deja una tarea de una iniciativa en train si otra tarea de la MISMA iniciativa esta en benchmark.
- [ ] CA-06 - Gold solo se marca en el paso de integracion/merge del ritual de cierre, con confirmacion humana explicita.
- [ ] CA-07 - Todo texto capturado pasa por `redact.py` antes de escribirse.

## Decisiones confirmadas (usuario, 2026-09-16)

1. Es la primera iniciativa que consume `training-data-services` como adaptador de dominio real (el propio plugin).
2. El modo `metadata` (sin diff de codigo) es el default; `full-diff` es opt-in explicito y separado.
3. `outcome`/`validation` se derivan mecanicamente de piezas ya existentes del ciclo; no hay juicio nuevo del LLM.
4. Familia = iniciativa completa (no tarea suelta), para proteger la particion anti-leakage.
