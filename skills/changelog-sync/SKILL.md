---
name: changelog-sync
description: >
  Genera las entradas `[Unreleased]` (EN) y `[Sin publicar]` (ES) del CHANGELOG a partir de los
  ledgers CERRADOS del roadmap (`docs/roadmap/*/tasks.md` con `estado: completado`), de forma
  DETERMINISTA e idempotente: un bullet por tarea `T-XX` con su título, la primera frase de su
  descripción y sus ficheros clave, con la categoría `Added|Changed|Fixed` deducida (o declarada
  en el frontmatter). No crea la sección de versión (eso es el script de release del proyecto) ni inventa
  alcance. Úsala cuando el usuario diga "escribe el changelog", "sincroniza el CHANGELOG",
  "genera las notas de la release", "actualiza [Unreleased]", o al cerrar una iniciativa.
---

# changelog-sync — el CHANGELOG sale del ledger, no de la memoria

Al cerrar una iniciativa hay que dejar constancia en el CHANGELOG. Escribirlo «de memoria» al
final del día es justo cuando se olvidan tareas y se inventa alcance (pasó en la v1.15.0: las
notas se redactaron a mano cuatro veces — [`LES-012`](../../docs/knowledge/lessons/)). Aquí la
fuente es el **ledger canónico**, que ya tiene el título, la descripción y los ficheros de cada
tarea; el script solo los traslada.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):

```bash
CLS="$(find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/changelog-sync/scripts/changelog-sync.py' 2>/dev/null | head -1)"
```

## Cuándo usarla

- **Al cerrar una iniciativa** (`/dev-cycle` Fase 6, `quick-implement`): su ledger acaba de pasar
  a `completado`, así que ya hay entrada que generar.
- **Antes de un release**: el script de release del plugin (`release.py`) ejecuta `--check` en sus precondiciones y
  **avisa** si falta alguna entrada (no bloquea: se puede publicar deuda de notas a sabiendas).
- **A demanda**, cuando el CHANGELOG se ha quedado atrás respecto al roadmap.

## Cómo se ejecuta

```bash
python3 "$CLS" --check              # exit 1 si hay ledgers cerrados sin entrada (no escribe)
python3 "$CLS" --dry-run            # imprime lo que escribiría, sin tocar nada
python3 "$CLS"                      # escribe en CHANGELOG.md y CHANGELOG.es.md
python3 "$CLS" --only <slug>        # una sola iniciativa
python3 "$CLS" --check --json       # para consumo por script
```

Exit: `0` ok o nada pendiente · `1` solo con `--check` y entradas pendientes · `2` uso
(falta un CHANGELOG, `--only` con un slug que no está cerrado).

## Qué produce

Una subsección por iniciativa, insertada bajo la cabecera de la sección abierta y ordenada por
fecha (la más reciente arriba):

```markdown
### Added — `mi-iniciativa` initiative (2026-09-03)

- **T-01 — Título de la tarea** Primera frase de su descripción. (`a.py`, `b.md`)
```

- **Categoría**: `fix|corrige|corrección|saldar|bug|regresión` → `Fixed`;
  `cambia|retira|renombra|migra|sustituye|reemplaza` → `Changed`; resto `Added`. Para fijarla a
  mano, añade `changelog: Added|Changed|Fixed` al frontmatter del ledger — el override manda.
- **Idempotencia**: si el slug ya aparece entre acentos graves en el CHANGELOG, no se vuelve a
  escribir. Puedes reescribir el texto generado sin miedo: no se regenera.

## Cómo afinar el texto generado

El bullet automático es un **punto de partida honesto**, no la nota final:

1. Reescribe la redacción para que hable del **valor** («los hooks informan del progreso»), no de
   la tarea («T-02 hooks»). Puedes fundir varios bullets en uno.
2. Quita los ficheros que no aporten y añade el enlace al ADR/lección si la iniciativa lo tiene.
3. **Nunca amplíes el alcance**: si el bullet no lo dice, no pasó. Lo que falte, está en el
   ledger; lo que no esté en el ledger, no va al CHANGELOG.

## Qué NO hace

- **No crea la sección de versión** ni mueve `[Unreleased]` → `[X.Y.Z]`: eso es el script de
  release del plugin, `release.py` (que además comprueba árbol limpio, versión creciente y tag libre).
- **No traduce con modelo**: el ledger está en español, así que el bullet ES y EN salen del mismo
  texto. Traducir la versión EN es trabajo humano (o de un turno del agente) posterior.
- **No inventa alcance ni cifras**, no lee la conversación y no toca ledgers.
