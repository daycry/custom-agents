---
id: ADR-006
titulo: "Un fichero por entrada para gotchas y lecciones (como `adr/`)"
estado: aceptada
fecha: 2026-08-20
iniciativa: knowledge-split
---

# ADR-006: Un fichero por entrada para gotchas y lecciones (como `adr/`)

## Contexto

`docs/knowledge/gotchas.md` y `docs/knowledge/LESSONS.md` nacieron como ficheros únicos (spec
`knowledge-capture`), a diferencia de `adr/` (ya un fichero por decisión desde el principio). Tras
el primer día real de uso —16 tareas de `knowledge-capture` más 3 intentos de revisión de dos
lentes, y una segunda iniciativa (`confluence-policy`) aportando 2 gotchas más el mismo día— tres
problemas se hicieron visibles: (1) **crecimiento previsible** — ambos ficheros ya mezclaban
entradas de iniciativas y agentes distintos en un único documento que solo crece; (2) **lectura no
selectiva** — `knowledge-check.md` pedía abrir el fichero de área entero aunque solo una entrada
tocara la tarea, pagando tokens de progressive disclosure que el propio `2026-08-10-token-diet`
quería evitar; (3) **colisión de escritura en paralelo** — dos agentes (o dos lotes) añadiendo una
entrada a la vez al mismo fichero compartido es el mismo riesgo que `knowledge-write.md` ya
documentaba y mitigaba para el `id:` de ADR, pero aquí además con colisión de FICHERO, que en
`adr/` no existe. Adicionalmente, el plan de publicación a Confluence (`confluence-policy`, D1)
funciona mejor con una página por entrada que con una página que agrega N entradas no relacionadas.

## Decisión

`docs/knowledge/gotchas.md` y `docs/knowledge/LESSONS.md` se dividen a **un fichero por entrada**,
igualando el patrón que `adr/` ya tenía: `docs/knowledge/gotchas/<slug>.md` y
`docs/knowledge/lessons/<agente>-<slug>.md` (agrupación por agente en el propio nombre del
fichero, ya que no hay subcarpetas por agente). Cada entrada lleva frontmatter `tipo`/`area`/
`estado`/`fuente` además de su cuerpo (antes solo vivía como sección dentro del fichero agregado).
`docs/knowledge/README.md` pasa a ser el **índice de entrada**: una fila por entrada enlazando al
fichero individual, no a una sección del agregado. `agent-kits/shared/knowledge-check.md` pasa a
lectura **SELECTIVA**: el índice señala la entrada exacta y solo esa se abre — nunca "todo
`gotchas/`" ni "todo `lessons/`". `adr/` no cambia: ya cumplía este patrón. La migración conserva
el texto y la traza de validación (`estado: aceptada (validada: ..., 2026-08-20[, intento N])`)
sin retocar ni una palabra; los ficheros antiguos quedan como stub de redirección de ≤5 líneas
(la escritura remota no puede borrarlos del disco de quien ya los tenía) — en proyectos
consumidores nuevos, `gotchas/` y `lessons/` nacen directas, sin stub.

## Alternativas descartadas

- **Mantener un fichero único con un umbral de tamaño que dispare el split más adelante** —
  descartado: los tres problemas (crecimiento, lectura no selectiva, colisión de escritura) ya
  eran observables con solo 3 gotchas y 9 lecciones; esperar a un umbral arbitrario habría dejado
  el problema sin resolver justo cuando más agentes escriben en paralelo.
- **Subcarpetas por agente dentro de `lessons/`** (`lessons/evaluator/<slug>.md`) en vez de
  prefijo en el nombre — descartado: añade un nivel de anidamiento sin beneficio claro sobre un
  índice plano, y complica los enlaces relativos existentes sin necesidad.
- **Activar ya el índice generado + `knowledge-lint.py`** (D4 de `knowledge-capture`) aprovechando
  el split — descartado: D4 sigue diferido a propósito (>15 entradas o la primera colisión de ID
  de ADR); este split resuelve la colisión de FICHERO pero no toca la colisión de `id:`, que sigue
  siendo el disparador correcto para D4.

## Consecuencias

Todo escritor (`planner`/`implementer` para ADR, `debug-root-cause`/`qa` para gotchas, `/retro`
para lecciones) crea un fichero nuevo en vez de editar uno compartido — la colisión de FICHERO en
paralelo desaparece para los tres tipos; solo el `id:` de ADR conserva el riesgo de colisión
(mitigado igual que antes: renumerar y declararlo en la retro). Todo lector aplica
`knowledge-check.md` de forma selectiva: índice → entrada concreta, protegiendo la inversión de
`2026-08-10-token-diet`. Los 12 ficheros migrados (3 gotchas + 9 lecciones, estas últimas
repartiendo el bloque compartido "Tres lecciones..." en 3 ficheros autocontenidos que repiten su
intro/traza) se pueden comprobar contra el histórico de git para verificar que el texto no cambió.
Los stubs `gotchas.md`/`LESSONS.md` solo existen en **este** repo (que no publica a Confluence —
no tiene `confluence.json`), así que no hay página-stub que se publique por error aquí; un proyecto
consumidor nace con `gotchas/`/`lessons/` directas y sin stub. Si algún proyecto heredara un stub,
puede excluirlo añadiéndolo a su `exclude` de `confluence.json` — no se cambia el `exclude` de
ejemplo de este repo por no tener el caso.

## Estado

`aceptada (validada: usuario, 2026-08-20)` — decidida por el usuario el mismo día, vía fast-track
(sin spec/evaluación/plan). Fuente:
[`docs/roadmap/2026-08-20-knowledge-split/tasks.md`](../../roadmap/2026-08-20-knowledge-split/tasks.md)
(contexto de la decisión, bloque introductorio).

**Ampliado 2026-08-20** (`knowledge-ids`, T-05 del mismo ledger): nomenclatura `GOT-NNN-<slug>.md`
/ `LES-NNN-<agente>-<slug>.md` con ID en frontmatter, igualando el patrón `ADR-NNN` — decidida por
el usuario. La colisión de `id:` pasa a aplicar a las tres familias con la misma mitigación
(renumerar y declararlo en la retro), sin cambiar el disparador de D4 (>15 entradas o la primera
colisión de IDs, en cualquiera de las tres).
