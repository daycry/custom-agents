---
name: discovery
description: >
  Paso de DESCUBRIMIENTO previo a evaluar: convierte una idea vaga en una
  especificación sólida antes de que el `evaluator` la presupueste, para no
  estimar sobre ambigüedades. Asistente guiado que hace preguntas dirigidas
  (objetivo, usuarios, alcance, fuera de alcance, criterios de éxito,
  restricciones, datos/integraciones, supuestos) y redacta/afina la spec.md de
  la iniciativa. Úsala cuando el usuario diga "afinar la idea", "discovery",
  "prepara la spec", "define bien esto antes de presupuestar", o al arrancar
  /pm-cycle con un objetivo poco definido.
user-invokable: true
---

# discovery — de idea vaga a spec sólida (antes de evaluar)

El presupuesto solo es tan bueno como la spec: estimar sobre requisitos ambiguos da cifras
infladas y baja confianza. Esta skill **afina la idea con el usuario** y deja una `spec.md`
clara en `docs/roadmap/<fecha>-<slug>/`, lista para que el `evaluator` la presupueste.

**Pensada como asistente guiado.** Una pregunta a la vez, en lenguaje llano, con ejemplos y
defaults propuestos; no un cuestionario largo de golpe. El usuario puede decir "no sé" y se
registra como **incógnita/supuesto**, no se inventa.

## Cuándo se usa
- Al arrancar `/pm-cycle` con un objetivo **poco definido** (se ofrece; opt-in).
- A demanda ("hagamos discovery de …"), antes de `evaluator`.
- **No** se usa si ya hay una `spec.md` madura: en ese caso, directo a evaluar.

## Flujo
1. **Encaja la carpeta**: deriva `<slug>` y fija `docs/roadmap/<fecha>-<slug>/` (la misma que usará evaluación/plan). Si ya hay `spec.md`, léela y afínala en vez de empezar de cero.
2. **Entrevista dirigida** — cubre, una a una, solo las que falten:
   - **Problema / objetivo**: ¿qué problema resuelve y por qué ahora?
   - **Usuarios / actores**: ¿para quién? ¿quién lo usa o se ve afectado?
   - **Alcance (in)**: qué entra, en 3-6 puntos concretos.
   - **Fuera de alcance (out)**: qué NO se hace (clave para acotar el presupuesto).
   - **Criterios de éxito**: cómo se sabrá que está hecho (medibles si se puede).
   - **Restricciones**: plazos, stack, normativa, dependencias, presupuesto tope.
   - **Datos / integraciones**: sistemas, APIs, permisos, datos sensibles.
   - **Supuestos e incógnitas**: lo que no se sabe aún (se marca, no se inventa).
   Propón un borrador de respuesta cuando puedas y deja confirmar/ajustar; no alargues.
3. **Redacta la spec** con la plantilla del `evaluator` (para que encaje con la cadena):
   ```bash
   EVALKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/evaluator' 2>/dev/null | head -1)"
   # plantilla en "$EVALKIT/templates/spec.md"
   ```
   Rellena contexto/objetivo, alcance in/out, criterios de aceptación, restricciones, datos y un
   bloque de **supuestos e incógnitas**. Estado inicial `borrador`. Registra la iniciativa en `docs/roadmap/README.md`.
4. **Cierra con handoff a evaluación**: resume la spec en 3-4 líneas, señala las incógnitas que más afectan al coste, y ofrece continuar con `evaluator` (o con `/pm-cycle`, que ya lo encadena). No presupuestes tú.

## Reglas
- **No inventes requisitos.** Lo que el usuario no sepa se registra como incógnita/supuesto explícito; baja la confianza de la futura estimación en vez de rellenar huecos.
- **Acota con el "fuera de alcance".** Es la sección que más ahorra en presupuesto y malentendidos; insiste en ella.
- **No planifiques ni estimes** (eso es `evaluator`/`planner`). Aquí solo se define el QUÉ.
- **Formato de la cadena**: usa la plantilla `spec.md` del `evaluator` y el mismo `<slug>`, para que evaluación y plan cuelguen de la misma carpeta.
- **Breve y humano**: prioriza cerrar las ambigüedades que mueven el coste; no conviertas el discovery en un interrogatorio.
