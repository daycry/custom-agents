---
name: debug-root-cause
description: Depuración SISTEMÁTICA hasta la causa raíz en 4 fases con evidencia obligatoria (reproducción mínima → aislamiento → hipótesis probada → fix + test de regresión). Prohibido "arreglar a ciegas". La invoca /dev-cycle automáticamente al 3.er rojo del bucle qa→implementer (antes de rendirse y preguntar), y se puede usar a demanda. Úsala cuando el usuario diga "depura esto a fondo", "encuentra la causa raíz", "por qué falla esto", "lleva tres intentos y sigue rojo".
---

# debug-root-cause — causa raíz con evidencia, no parches a ciegas

Método para cuando un fallo se resiste: en vez de otro intento de arreglo "a ver si cuela",
**cuatro fases con evidencia obligatoria en cada una**. La regla dura que gobierna todo:

> **PROHIBIDO cambiar código sin una hipótesis probada.** Si no puedes explicar POR QUÉ falla
> con evidencia en la mano, aún no te toca arreglar — te toca seguir en la fase donde estés.

## Las 4 fases (secuenciales; cada una termina con su evidencia)

**Fase 1 — Reproducción mínima.**
Reduce el fallo al caso más pequeño que lo dispara: un test concreto, un input concreto, un
comando concreto. Quita todo lo que no haga falta para que falle. Si no consigues reproducirlo
de forma determinista, documenta las condiciones en que aparece/desaparece — eso YA es
información (sugiere carrera, estado compartido o dependencia del entorno).
*Evidencia:* el comando/test mínimo y su salida de fallo, pegados.

**Fase 2 — Aislamiento de la causa.**
Acorrala dónde vive el fallo, con datos: bisección (¿desde qué commit falla? `git bisect` si
hay historia), instrumentación (logs/asserts temporales en los puntos sospechosos), o corte
del sistema en mitades (¿falla antes o después de X?). Registra qué DESCARTASTE y con qué
evidencia — descartar es avanzar.
*Evidencia:* la zona acotada (fichero/función/condición) y la lista de descartes con su dato.

**Fase 3 — Hipótesis formulada y PROBADA.**
Enuncia la causa en una frase falsable: "falla porque X hace Y cuando Z". Diseña la prueba
más barata que la confirme o la tumbe (un assert, un input diseñado, un log en el punto
exacto) y ejecútala. Si la hipótesis cae, vuelve a la Fase 2 con lo aprendido — NO pases a
arreglar "por si acaso".
*Evidencia:* la hipótesis literal + el resultado de la prueba que la confirma.

**Fase 4 — Fix + test de regresión.**
Arregla LA CAUSA (no el síntoma) con el cambio mínimo que la hipótesis justifica, y deja un
**test de regresión** que falla sin el fix y pasa con él (idealmente, la reproducción mínima
de la Fase 1 convertida en test). Re-ejecuta la suite completa: el fix no puede romper otra
cosa.
*Evidencia:* diff del fix + test de regresión en verde + suite en verde.

**Cierre de Fase 4 — memoria técnica (siempre activa, D3).** Localiza el kit compartido:
`SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`.
Con la Fase 4 completa (fix aplicado, no propuesto), comprueba el umbral de
`"$SHAREDKIT/knowledge-write.md"`: si esta causa raíz
costó **≥1 ciclo de depuración** (llegaste a esta skill) o **rompió/casi rompió una garantía del
producto**, escribe un gotcha en un fichero nuevo `docs/knowledge/gotchas/GOT-NNN-<slug>.md` con los 4 campos — **síntoma** (de la
Fase 1), **causa raíz** (de la Fase 3, la hipótesis probada), **qué hacer en su lugar**, y
**evidencia** (enlace/referencia al test de regresión de esta misma fase) — y actualiza el índice
`docs/knowledge/README.md` en el mismo cambio. Si no cruza el umbral (fix trivial, o causa ya
documentada en un gotcha existente — enlázalo, no dupliques), **no escribas nada**: decláralo así
en la evidencia de cierre. Si `docs/knowledge/` no existe, créala en este primer registro; si el
fragmento no está disponible, no bloquea: sigue sin escribir gotcha.

## Integración con /dev-cycle (gancho del 3.er rojo)

Cuando el bucle qa→implementer llega al **3.er rojo**, `/dev-cycle` ejecuta **UNA pasada** de
esta skill ANTES de parar y preguntar al usuario. **En el gancho, la pasada se detiene al
final de la Fase 3**: hipótesis probada + **fix PROPUESTO** (diff descrito, sin aplicar) —
la Fase 4 (aplicar el fix + test de regresión) solo se ejecuta DESPUÉS de que el usuario
decida "seguir con el fix". A demanda (fuera del gancho), la skill recorre las 4 fases
completas. Resultado del gancho:

- **Diagnóstico concluyente** (Fases 1-3 completas): la pregunta al usuario llega con la causa
  probada y el fix propuesto — decide con información, no a ciegas.
- **Diagnóstico parcial**: se presenta lo descartado (Fase 2) y las hipótesis vivas, y SE
  PREGUNTA igual que hoy — pero con evidencia sobre la mesa. Dentro de la pasada, el ciclo
  Fase 3→Fase 2 se recorre como máximo **2 veces**; a la segunda hipótesis caída, se reporta
  parcial (la pasada es acotada, no una investigación abierta).

En el gancho, el cierre de Fase 4 (memoria técnica) **solo aplica cuando la Fase 4 se completa de
verdad** (el usuario decidió "seguir con el fix" y el fix quedó aplicado con su test). Con
diagnóstico parcial, o con Fase 4 detenida en "fix propuesto sin aplicar", no se escribe gotcha —
no hay causa raíz probada en la mano, solo hipótesis vivas o un fix sin confirmar.

Si el usuario elige "seguir con el fix", aplicarlo (Fase 4) abre un ciclo de qa nuevo con el
contador a cero — **una sola vez**: si ese ciclo vuelve a agotar sus 3 rojos, NO se repite el
diagnóstico automático; se pregunta directamente con todo lo acumulado. Una sola pasada: esta
skill no alarga el bucle indefinidamente. El tiempo consumido se imputa como implementación
de la tarea afectada (no es revisión).

Aplica en la **cadena nativa** de `/dev-cycle`. Si el usuario pidió explícitamente delegar en un
motor SDD externo, manda el método de depuración de ese motor (no dupliques métodos en la
misma sesión).

## Reglas

- **Evidencia o no ocurrió**: cada fase cierra con su dato pegado, no con "ya lo miré".
- **Los descartes se registran** — la siguiente persona (o pasada) no debe repetir el camino.
- **El síntoma no es la causa**: si el fix no se deduce de la hipótesis probada, es un parche.
- **Instrumentación temporal se retira** al cerrar (logs/asserts de diagnóstico fuera del diff final).
- Si el fallo resulta ser de la SPEC (comportamiento esperado mal definido), no lo "arregles"
  en código: repórtalo — eso es una decisión de producto (spec → `/pm-cycle`).
