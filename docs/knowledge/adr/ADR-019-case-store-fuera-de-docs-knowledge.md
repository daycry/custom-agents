---
id: ADR-019
titulo: "El case store de `training-data-services` vive fuera de Git y de `docs/knowledge/`, en el `root` que declara el proyecto"
estado: propuesta          # propuesta | aceptada | obsoleta
fecha: 2026-09-23
iniciativa: training-data-services
---

# ADR-019: El case store vive fuera de `docs/knowledge/` (y fuera de Git), en el `root` del proyecto

## Contexto

`training-data-services` captura **casos** (petición, contexto, trayectoria, métricas, validación)
para ensamblar después un dataset de entrenamiento local. `docs/knowledge/` ya es la memoria
técnica del plugin: pocas entradas, curadas (`knowledge-curator`, `ADR-018`), versionadas en Git y
proyectadas a Kwipu/Graphiti. Un caso es lo contrario: **mucho volumen** (cientos por sesión, spec
§Supuestos), **sin curar** al capturarse, con fallos incluidos a propósito, y con artefactos finales
que pueden ser pesados. Hacía falta decidir dónde vive, porque la respuesta condiciona a cuatro
piezas: el esquema de `training.json` (`case_schema.py`), el recorder (T-04), la capacidad
`training` de `capabilities.py` y el puente hacia `knowledge-curator`.

## Decisión

1. El case store vive en la ruta `root` que declara `.claude/knowledge-services/training.json`; el
   plugin **no impone nombre ni ubicación**, y la recomendación es una carpeta **fuera del
   repositorio Git** (o ignorada por él).
2. `root` **nunca** puede apuntar dentro de `docs/knowledge/`: `case_schema.py` lo rechaza como
   error de configuración (y `/doctor` lo informa por la capacidad `training`, sin bloquear).
3. El único camino de un caso hacia `docs/knowledge/` es el **puente opt-in**
   (`bridge_to_curator`): un caso Gold se propone como candidato en
   `docs/knowledge/candidates/pending/` y lo decide `knowledge-curator` con sus reglas de siempre.
   Nunca al revés: el conocimiento aprobado no alimenta el case store (anti-leakage, spec).
4. `exports/` (dataset ensamblado) vive también bajo `root`, nunca en Git.

## Alternativas descartadas

- **`docs/knowledge/cases/`** (una carpeta más de la memoria): mezcla un flujo de alto volumen sin
  curar con uno curado de bajo volumen; los lectores selectivos (`knowledge-check.md`,
  `knowledge-find.py`) y la publicación a Kwipu tendrían que aprender a excluirlo, e inflaría el
  índice único de `docs/knowledge/README.md`. Es la misma razón por la que `design.md` descartó O2
  (meter la capacidad en `knowledge-services`).
- **Una ruta fija del plugin** (p. ej. `.claude/training/`): `.claude/` es config y estado pequeño
  (regla 9 de `docs/CONVENTIONS.md`), no datos de volumen; y cada proyecto tiene su propio sitio
  para datos grandes (disco aparte, volumen compartido).
- **Versionar los casos en Git**: artefactos pesados y alto volumen engordan el repo sin revisión
  humana que aporte nada; la trazabilidad la dan el versionado `v<NNN>` inmutable y el
  `manifest.json` de cada export (hash por caso).

## Consecuencias

- `case_schema.py` valida `root` (obligatorio con `enabled: true`, nunca bajo `docs/knowledge/`).
- La capacidad `training` informa si `root` existe (`ok`) o aún no (`declarado`); informar nunca lo crea.
- Perder `training.json` solo apaga la capacidad: el case store en `root` no se toca.
- El proyecto es responsable del respaldo del case store (fuera del alcance del plugin).
- La memoria de `docs/knowledge/` no cambia: sigue siendo la única fuente de verdad curada (ADR-018).

## Relación con ADR-018 (fuente de verdad)

[ADR-018](ADR-018-arquitectura-de-memoria-markdown-canonico-backends-declarados.md) punto 1 dice que
la fuente de verdad es el Markdown en git y que «cualquier dataset» es una proyección reconstruible
desde ella. Esta ADR no lo contradice, lo acota: **ADR-018 habla del conocimiento curado; el case
store es evidencia bruta no curada, deliberadamente fuera de git y de `docs/knowledge/`**. No es una
segunda fuente del conocimiento del proyecto ni un índice suyo: es materia prima (peticiones,
trayectorias, fallos) que nunca se reconstruye desde `docs/knowledge/` —el anti-leakage lo prohíbe— y
de la que solo se obtienen dos cosas derivadas: el dataset de `exports/` (proyección del case store,
reconstruible desde él con su `manifest.json`) y, por el puente opt-in, candidatos `pending` que
entran en la fuente curada de ADR-018 por la puerta de siempre (`knowledge-curator`). El «dataset» de
ADR-018 punto 1 es el que se proyecta desde la memoria curada; el de esta ADR se proyecta desde la
evidencia bruta, y por eso vive con ella y no en git.
