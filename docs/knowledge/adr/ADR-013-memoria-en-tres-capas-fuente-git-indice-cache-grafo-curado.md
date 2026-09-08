---
id: ADR-013
titulo: Memoria técnica en tres capas — la fuente de verdad es el Markdown en git, el índice es una caché reconstruible y el grafo es curado, no cronológico
estado: propuesta
fecha: 2026-09-08
iniciativa: memory-retrieval
---

# ADR-013: Memoria técnica en tres capas — fuente en git, índice como caché, grafo curado

## Contexto

El análisis de `memory-retrieval` midió que el plugin **escribía** memoria bien (31 entradas curadas ≈ 27.100
tokens) y la **recuperaba** mal: 17 entradas (55 %) sin ninguna pieza ejecutable que las citara, 0 tokens de
memoria inyectados al arrancar sesión, 0 entradas de journal y un índice de entrada que costaba 3.685 tokens
por consulta. Las alternativas del mercado (`claude-mem` y similares) resuelven la recuperación con un almacén
propio —SQLite o vectores— alimentado por observación sin filtro, un servidor que hay que instalar y una
cronología como único grafo.

## Decisión

La memoria técnica se organiza en **tres capas**, y el orden importa:

1. **Fuente de verdad: los ficheros Markdown de `docs/knowledge/` en git** — una entrada por fichero, con
   `estado` (`propuesta` / `aceptada` / `obsoleta` con sucesor), fecha y fuente; `docs/knowledge/README.md`
   es el único índice de entrada y la biyección `ficheros ↔ filas` la vigila `lint_plugin.py`
   (`lint_knowledge_index`, ERROR). Una memoria que es un diff con autor y fecha se **revisa en un PR**; un
   SQLite no.
2. **Índice como CACHÉ reconstruible**: `knowledge-find.py` mantiene un SQLite FTS5 en
   `.claude/knowledge-index.sqlite` (ignorado por git) con el hash del corpus; se regenera solo y **degrada
   a recorrido plano** si `sqlite3` no trae FTS5 o el fichero está corrupto. Sin dependencias: `sqlite3` es
   stdlib; sin embeddings ni servicio.
3. **Grafo CURADO en vez de cronología**: `--related <ID>` navega sucesor/sustituida, misma iniciativa y
   misma área —relaciones que alguien escribió—, no «lo que pasó justo antes». La cronología vive aparte,
   en el journal episódico (`ADR-010`), y lo que se repite en él **asciende** por la puerta de `/retro`
   (`journal.py candidatas`, siempre `propuesta`).

Sobre ese esqueleto, la recuperación es **presupuestada y probada**: cada punto de inyección tiene un tope
medido (brief del subagente ≤ 600 tokens de memoria, arranque de sesión ≤ 300, brief completo ≤ 10.000
caracteres) y un test que se pone rojo si el camino no se recorre (`tests/test_memory_path.py`, evals).
La **doctrina del plugin** (lecciones ciertas para cualquier proyecto que use estos agentes) viaja como
asset copiado byte a byte (`agent-kits/evaluator/assets/doctrina/`, `--doctrina`) y la memoria del proyecto
consumidor **nace vacía**.

## Alternativas descartadas

- **Embeddings / búsqueda semántica** — añadiría una dependencia (modelo o servicio) y un almacén opaco para
  un corpus de decenas de entradas cortas; FTS5 con `unicode61` y las raíces ligeras del tokenizador
  recuperan lo mismo con cero dependencias y resultados reproducibles.
- **Capturar todo** (cada `PostToolUse`, cada turno, sin filtro) — coste y ruido sin curación; el usuario lo
  descartó explícitamente. Se captura **solo el turno del usuario**, con opt-out `<private>`, redacción de
  secretos evidentes y log no versionado; lo que merece doctrina se **promueve**, no se acumula.
- **Retirar el journal** (el análisis lo planteó: «0 entradas») — se descartó porque el hueco era de
  *contenido* (`decisiones: []` siempre), no de *mecanismo*; se corrigió la conclusión de `ADR-010` (el hook
  no devuelve, escribe) en vez de borrar la pieza.
- **Un almacén propio como fuente de verdad** (el SQLite ES la memoria, como en `claude-mem`) — no se puede
  revisar en un PR, no distingue doctrina de indicio y no sobrevive a un `git clone`.

## Consecuencias

Se gana recuperación determinista con presupuesto explícito por camino, memoria auditable en git y
doctrina que viaja con el plugin, sin dependencias. Se paga con disciplina: cada entrada nueva necesita su
fila con «Área» en el índice (el linter lo exige), el índice FTS5 se reconstruye al primer uso tras cada
cambio del corpus, y la curación sigue siendo humana (revisión de dos lentes o usuario): el sistema
**propone**, nunca acepta solo. Si el corpus creciera hasta que el recorrido plano dejara de bastar como
degradación, el índice pasaría de caché a requisito — se abriría entonces una iniciativa, no antes.

## Estado

`propuesta` — a validar por la revisión de dos lentes de `memory-retrieval` (Fases 5-6) o el usuario en la
puerta. Pasa a `aceptada` cuando se valide; a `obsoleta` si una decisión posterior la reemplaza (enlazar aquí).
