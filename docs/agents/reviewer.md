# Agente: reviewer (una lente, solo lectura)

## Propósito
Dar cuerpo a las **lentes** de la skill `adversarial-review` con un agente de contexto fresco que **no
puede escribir**: `tools: Read, Grep, Glob, Bash` (Bash solo para ejecutar tests/scripts como evidencia;
Write/Edit no están en la lista, así que no hay regla que recordar — no tiene la herramienta). Antes las
lentes iban a subagentes genéricos con las herramientas del padre; ahora el revisor es una pieza con
tier propio (`opus` · `effort: high`, override en `dev.json` `modelos.reviewer`) y contrato de salida fijo.

## Entrada / salida
- **Entrada (la da la skill):** la lente (`A` conformidad con spec/plan/constitución — y `docs-style.md`
  en iniciativas de prosa —, `B` corrección/robustez con persona de dominio, `C` seguridad introducida por
  el diff), el diff/rango, los artefactos (`improvement-plan.md`, `tasks.md`, `design.md` si existe) y, si
  N > 1, la tabla del intento anterior. El prompt literal viene de
  `skills/adversarial-review/references/lens-prompts.md`.
- **Salida (estructura fija que la skill fusiona):** tabla por criterio ✓/✗/no verificable con evidencia
  (`fichero:línea` o comando → salida), gaps graduados `Critical/Important/Minor` con escenario concreto
  (y CWE en C), lo ejecutado, y «fuera de mi lente» para enrutar lo que vio de otra lente. «Sin
  defectos» es una salida válida.

## Cómo lo usa la cadena
- `adversarial-review` §2 despacha **una llamada al Agent tool por lente** con `subagent_type: reviewer`
  y el `model` de `model-tier.py reviewer` (si viene de `dev.json`); las 2-3 llamadas van en paralelo.
- **Fallback:** si el agente no está disponible (instalación parcial), la skill lanza un subagente
  genérico con el mismo prompt y lo anota — degradación, no bloqueo.
- Una petición del usuario tipo «revisa este diff» va a la **skill** (que decide lentes, puerta
  `scope-check`, fusión y traza), no al agente directamente; el agente solo es la lente.

## Qué NO hace
- No corrige, no propone refactors, no comenta estilo, no decide qué pasa al 3.º intento (skill/orquestador).
- No duplica la tabla de racionalización del revisor: la aplica desde `skills/adversarial-review/SKILL.md`.
- No audita seguridad completa (`nemesis`) ni da el verde de pruebas (`qa`).

## Dependencias
- Skill `adversarial-review` (método, graduación, tabla del revisor, prompts literales).
- Fragmentos `agent-kits/shared`: `personas/`, `docs-style.md`, `constitution-check.md`, `output-discipline.md`.
