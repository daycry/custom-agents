---
id: LES-011
tipo: leccion
area: Proceso / desarrollo del plugin (activación de piezas)
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fuente: docs/roadmap/2026-09-03-activation-reliability/tasks.md (decisión del usuario, comparación con superpowers)
---

## plugin-dev

- **La `description` de una skill, comando o agente es una promesa de activación, y una promesa
  se prueba, no se asume.** Este plugin ganaba en método (cadena de agentes, ledger canónico,
  puertas deterministas) pero perdía frente a superpowers en lo más básico: que la pieza correcta
  se dispare cuando el usuario describe la necesidad sin nombrarla. El linter avisaba de
  «description sin frase-gatillo» y ahí acababa la verificación: nadie había comprobado nunca,
  con un prompt real, que `quick-implement` se activa con «hazme este cambio sin papeleo» y NO con
  «necesito un módulo con incógnitas y presupuesto». Se cerró en tres capas, todas mecánicas:
  1. **Evals de activación (`evals/`).** Un JSON por pieza (31 targets, 96 casos) con ≥ 2 positivos
     —uno `literal` que contiene una frase de la description REAL, otro `parafrasis`— y ≥ 1 negativo
     **vecino** (comparte vocabulario y pide otra cosa; `redirect` a la pieza correcta). `check.py`
     corre en CI y ata cada caso a la description: cambiarla rompe el literal hasta que se
     actualizan ambas. `run.py` lanza los casos de verdad en local (`claude -p … --plugin-dir`) y
     detecta la activación en la transcripción; cuesta tokens, por eso no está en la CI.
  2. **Índice de piezas al arrancar (`skill-index.py` + hook `SessionStart`).** Las descriptions
     solo se ven cuando Claude las busca; el índice compacto (una línea por pieza, ≤ 3.500
     caracteres, caché por hash, también tras compactar) las pone delante en cada arranque con las
     reglas de enrutado. Coste fijo y medido, informativo, desactivable.
  3. **Tablas de racionalización** antes del DoD/veredicto de `implementer`, `adversarial-review` y
     `qa`: nombrar la excusa («los tests ya pasaban antes») en el momento en que aparece es más
     eficaz que repetir la regla.

  Regla derivada para `plugin-dev`: una pieza nueva **no está terminada** sin su fichero en
  `evals/cases/` (≥ 1 positivo y 1 negativo; el linter avisa si falta) y, si tiene DoD o
  veredicto, sin su tabla de racionalización. No hay formato oficial de evals de activación en
  Claude Code (verificado 2026-09-03: `claude plugin` no tiene `eval`; el `skill-creator` mide
  calidad de salida), así que el formato es propio y convertible 1:1 (`prompt`→`query`,
  `activates`→`should_trigger`). — *Fuente:*
  [`2026-09-03-activation-reliability/tasks.md`](../../roadmap/2026-09-03-activation-reliability/tasks.md),
  [`evals/README.md`](../../../evals/README.md). `estado: propuesta`.
