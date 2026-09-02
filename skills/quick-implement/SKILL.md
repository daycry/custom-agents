---
name: quick-implement
description: Atajo en lenguaje natural para la VÍA RÁPIDA de /dev-cycle — implementa UN cambio pequeño y bien definido conservando el ledger canónico y las puertas de calidad (revisión de dos lentes + qa-gate), sin papeleo de PM (sin spec, evaluación ni plan). No duplica el método: delega en la vía rápida de `commands/dev-cycle.md`, su fuente única. NO la uses si el trabajo tiene incógnitas o varias fases, toca muchos ficheros, el usuario quiere presupuesto o traza PM (eso es /pm-cycle o el flujo completo de /dev-cycle), el usuario ya escribió /dev-cycle (respeta el comando), o el cambio es trivial de una línea (hazlo directamente, sin ciclo); ante la duda, PREGUNTA antes de arrancar. Úsala cuando el usuario pida implementar algo concreto SIN escribir el comando y diga "implementa X rápido", "hazme este cambio pequeño", "añade X directo", "arréglalo sin papeleo", "solo impleméntalo".
---

# quick-implement — la vía rápida, sin tener que escribir el comando

Existe por una razón concreta y verificada: los **commands** (`/dev-cycle`) solo se disparan si el
usuario escribe la barra, mientras que las **skills** se activan por su descripción. Esta skill es
esa puerta de entrada — y nada más.

> **Fuente única, cero duplicación (regla del repo).** Esta skill **NO** reimplementa la vía
> rápida: la resuelve y la sigue. Si el método cambia en `commands/dev-cycle.md`, cambia aquí
> automáticamente.
>
> ```bash
> # $PWD/commands cubre el caso de trabajar SOBRE el propio repo del plugin (si no, ganaría la copia instalada)
> DEVCYCLE="$(find "$PWD/.claude" "$PWD/commands" "$HOME/.claude" -type f -path '*commands/dev-cycle.md' 2>/dev/null | head -1)"
> ```
>
> Qué seguir de ese fichero, en este orden: **Fase 0** (modo y carpeta de la iniciativa) → **Fase
> 0-bis, rama «vía rápida»** → **Fase 3 COMPLETA** (implementación + revisión de dos lentes + `qa`
> con `qa-gate`: ojo, `qa` está DENTRO de la Fase 3) → **Fase 6** (cierre). La **Fase 4
> (`documenter`) solo si el usuario la pide**; en vía rápida no es automática.
>
> Si no lo encuentras (instalación parcial), **dilo y para**: ofrece implementar el cambio a mano,
> avisando de que no habrá ledger ni puertas. Nunca improvises un método paralelo.

## Paso 1 — Filtro de idoneidad (OBLIGATORIO, antes de tocar nada)

La vía rápida es para cambios que se describen en **una o dos frases** y tocan **pocos ficheros**.
Comprueba el objetivo contra esta tabla y **di en voz alta** cuál aplica:

| Señal en la petición | Qué hacer |
|---|---|
| Alcance pequeño y claro, sin incógnitas | **Adelante** con la vía rápida |
| Incógnitas, varias fases, alcance difuso | **No arranques**: propón `/pm-cycle` (definir + presupuestar) o el flujo completo de `/dev-cycle` |
| El usuario quiere saber coste/esfuerzo antes | Flujo completo: la puerta económica ES el valor |
| Trivial de una línea (un typo, un literal) | Ofrece hacerlo **sin ciclo**; el ledger y las puertas no compensan |
| El usuario escribió `/dev-cycle` | No te actives: manda el comando |

Si dudas entre vía rápida y flujo completo, **pregunta una vez** con tu recomendación y respeta la
respuesta. Regla dura: **nunca arranques un ciclo con rama, ledger y puertas a partir de un
comentario de pasada.** El usuario pidió *rápido*; sorprenderle con ceremonia es peor que preguntar.

## Paso 2 — Ejecuta la vía rápida canónica (leyéndola, no de memoria)

**Ejecuta los hitos que define `$DEVCYCLE`, con su contenido tal como está escrito allí** — aquí
solo van los nombres, para no mantener una copia que se desincronice:

1. **Ledger ligero** (`docs/roadmap/<fecha>-<slug>/tasks.md`) — el único papeleo; sostiene
   progreso, imputación de horas y volcado a Jira.
2. **Medición** con `usage-meter.py`, respetando su **regla de no-solape**: una ventana para el
   ledger, que se **cierra en cuanto queda escrito** (antes de implementar), y después **una
   ventana por cada `T-XX`** (`<slug>/T-XX`). Nunca una ventana global que englobe a las de las
   tareas: contaría los mismos tokens dos veces.
3. **Implementación** por `implementer`, con la disciplina de `.claude/dev.json` si está activa.
4. **Las puertas NO se saltan**: la revisión adversarial es la skill **`adversarial-review`** (fuente
   única del método: puerta `scope-check.py` antes de gastar revisores, lentes A/B + lente C de
   seguridad condicional, bucle acotado a 3) y después `qa` con `qa-gate` (todo dentro de la Fase 3). Es lo que separa la vía rápida de "escribir código a lo loco": ahorra
   ceremonia, no seguridad. Solo se omiten a petición **explícita** del usuario.
5. **Cierre**: estados finales del ledger y ritual de cierre de rama si hay rama.

Ante cualquier duda sobre el *cómo* de un hito, la respuesta está en `$DEVCYCLE`, no aquí.

## Paso 3 — Cierra diciendo qué traza queda

Dos líneas al terminar: qué se implementó, qué puertas pasó (revisión, qa) y qué se omitió por ser
vía rápida (spec, evaluación, plan, presupuesto y —salvo que el usuario la pidiera— la
documentación de `documenter`). Así el usuario sabe qué tiene documentado y qué no, y puede pedir
el flujo completo si más adelante lo necesita.
