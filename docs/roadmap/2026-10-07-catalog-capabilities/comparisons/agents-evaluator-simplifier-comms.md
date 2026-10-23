# Evaluación de entregas, simplificación, comentarios, conversaciones y comunicación — A002, A005, A009–A011

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **22.451 bytes/546 líneas**. [agents-evaluator-simplifier-comms-reading-evidence.json](agents-evaluator-simplifier-comms-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las cinco.** Mismo bloque «Prompt Defense Baseline» (líneas 8-15), **sin
destino**: el contenido externo como dato ya está en
`skills/delivery-practices/references/delivery-tools.md:81` (D-001).

## A002 — agent-evaluator

`9.117 bytes/215 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet. Puntúa la
salida de un agente de 1 a 5 en cinco ejes, con evidencia, y emite un veredicto
«Deliver / Fix / Redo». Limita Bash a la lectura.

**Comparación.** Su rúbrica ya está integrada como juicio auxiliar en
`skills/outcome-evals/references/delivery-quality.md` (D-049, desde S007, que leyó este
agente como consumidor). Cada eje vale `cumple`, `parcial`, `falla` o `desconocido` (`:16-28`).
No se promedia (`:32-33`). Una afirmación de prueba exige el artefacto (`:36-37`). La
fuente difiere en tres puntos, y en los tres la versión propia es la corregida:

- **Media.** La fila OVERALL (líneas 94 y 149) promedia los ejes y deja que uno compense un fallo.
- **Veredicto.** «VERDICT: Deliver as-is» funciona como aprobación. En el plugin, aprobar
  es de `qa` y `adversarial-review`, y la rúbrica no aprueba nada (`delivery-quality.md:5-6`).
- **Dependencias fijas.** Usa la ruta `skills/agent-self-evaluation/SKILL.md` (25) y un
  formato atado a `scripts/evaluate.py`, cuyo puntuador ya invalidó S007.

Defecto concreto en el endurecimiento de Bash (34): pide `git log --no-pager` y
`git diff --no-pager`. `--no-pager` es una opción global de git y va antes del
subcomando (`git --no-pager log`). Escrito así, git falla con «unrecognized argument:
--no-pager», comprobado con git local en este repo. `-c core.pager=cat` también es
global. En el ejemplo «Strong», además, `X.X/5` (123) queda sin rellenar junto a un 4.6.
Los permisos de solo lectura son adecuados.

**Destino:** **Sin destino**: ya integrado en `outcome-evals` (D-049).

## A005 — chief-of-staff

`6.600 bytes/160 líneas` · tools: Read, Grep, Glob, Bash, Edit, Write · model: sonnet.
Triaje personal de correo, Slack, LINE, Messenger y calendario en cuatro niveles.
Redacta borradores con el tono de `SOUL.md` y hace un seguimiento obligatorio tras cada envío.

**Comparación.** Ningún rol del ciclo cubre este dominio, que es personal. La
comunicación externa está aparcada (D-151) y la regla de contenido no confiable, ya
integrada (D-001). Choca con el plugin en cuatro puntos:

| Línea | La pieza | El plugin |
|---|---|---|
| 110, 143 | Tras cada envío, `git commit & push` de `relationships.md`, `todo.md` y notas de relación | Datos personales de terceros fuera de git |
| 112, 141 | Un `PostToolUse` «bloquea» hasta cumplir el checklist | `PostToolUse` corre cuando la herramienta ya se ejecutó y no puede impedir el envío; los hooks globales propios solo informan (ADR-007) |
| 33-36 | El nivel `skip` archiva todo lo que llegue de `noreply`, `alert`, `@github.com`, `@jira` | Archivaría avisos de seguridad y de facturación sin que nadie los lea |
| 141, 144 | «LLMs forget instructions ~20% of the time»; las reglas inyectadas «cannot choose to ignore» | Afirmaciones sin fuente |

Depende además de herramientas que la definición no incluye: `gog` y `calendar-suggest.js`.

**Destino:** **Fuera del bundle.**

## A009 — code-simplifier

`2.265 bytes/56 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet.
Simplifica código reciente sin cambiar su comportamiento: anidamiento, ternarios,
código muerto, duplicación y `console.log`.

**Comparación.** El refactor tiene dueño. Lo hace el `implementer`, dentro de una
tarea del ledger (`docs/agents/ROLES.md:31`). `tdd` define el refactor puro como
`TDD n/a: refactor`: la misma suite en verde antes y después, con tests de
caracterización si falta cobertura (`skills/tdd/SKILL.md:41`). `code-health` mide
duplicados, anidamiento y funciones largas. `coding-baseline.md:13-21` fija los criterios
y advierte de que longitud y anidamiento no justifican un refactor fuera de alcance.
La fuente pide «verify no behavioral change» (56), pero no dice con qué test. Además,
escribe sobre «recently modified code» sin plan ni `scope-check`: un fichero fuera de
`Archivos` es gap Important (`agents/implementer.md:131`).

**Destino:** **Sin destino.**

## A010 — comment-analyzer

`2.034 bytes/54 líneas` · tools: Read, Grep, Glob · model: haiku. Revisa los
comentarios por exactitud, completitud, valor y elementos engañosos. Agrupa la salida
en Inaccurate, Stale, Incomplete y Low-value.

**Comparación.** El criterio está en `coding-baseline.md:16-17`: los comentarios
explican el porqué, y una señal de fallo es el comentario que ya no coincide con el
código. La documentación pública también está ahí. La antigüedad de TODO/FIXME la mide
`code-health` con `git blame`. Un comentario que contradice el código del diff es
defecto de la Lente B solo si induce un error con escenario concreto; lo demás es
estilo y la regla dura lo descarta. Sus permisos y su modelo son mínimos y adecuados,
pero la salida no exige `fichero:línea`.

**Destino:** **Sin destino.**

## A011 — conversation-analyzer

`2.435 bytes/61 líneas` · tools: Read, Grep · model: haiku. Busca en las
conversaciones correcciones, frustración, reversiones y errores repetidos, y propone
reglas de hookify (`action: block|warn`).

**Comparación.** La detección ya existe y no usa modelo. `journal.py candidatas`
clasifica `correccion_usuario`, `resolucion_error`, `workaround` y otras categorías
(`agent-kits/shared/journal.py:224`). Los patrones repetidos en dos o más sesiones van
como propuesta a `knowledge-curator` (D-084, integrado). La pieza choca en dos puntos:
crea reglas `block` por expresión regular desde hooks globales (ADR-007; S132 ya quedó
sin destino) e infiere frustración por el tono. Además, depende de `/hookify`, que es ajeno al plugin.

**Destino:** **Sin destino**: ya integrado en `journal.py candidatas`.
