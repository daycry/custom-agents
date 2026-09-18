---
name: knowledge-services
description: >
  Publica `docs/knowledge/approved/` a backends externos (Kwipu, futuros como Graphiti) por
  config de proyecto (`taxonomy.json`), sin acoplar el plugin a ninguno — `knowledge-sync.py
  --backend <id> [--dry-run|--check|--rebuild]` carga un adaptador por `type` (6 funciones:
  `health/plan/apply/verify/rebuild/revoke`), aplica `routing` ANTES de construir entradas
  (fail-closed) y usa `outbox.py` para staging/dead-letter — un fallo de `apply()` nunca borra la
  publicación anterior. Adaptador Kwipu (`markdown-export`): un Markdown por entrada con el
  frontmatter del Knowledge Gate (`project`/`scope`/`category`/`source`/`confidence`/
  `knowledge_id`/`version`/`hash`) + `manifest.json`; `verify` NOMBRA el reindexado sin
  ejecutarlo. Úsala cuando el usuario diga "sincroniza el conocimiento con Kwipu", "publica
  docs/knowledge en el grafo", "exporta approved a Kwipu", "por qué Kwipu no ve esta entrada",
  "añade un backend de knowledge-services", o al activar la capacidad `kwipu` desde `/setup`.
---

# knowledge-services — de `approved/` a un backend externo, sin acoplar el plugin a ninguno

`docs/knowledge/approved/` es el origen canónico (Git, revisado, curado por `knowledge-curator`).
Esta skill lo **proyecta** hacia fuera: hoy Kwipu (grafo local), mañana cualquier otro backend que
declare su propio `type` — el núcleo (`knowledge-sync.py`) no cambia al añadir uno.

## Cuándo NO usarla

- Para curar o aprobar conocimiento: eso es `knowledge-curator` (`curator-gate.py`) sobre
  `docs/knowledge/candidates/`. Esta skill solo lee `approved/`, nunca escribe ahí.
- Para consultar el grafo ya publicado (queries, respuestas): eso es del stack de Kwipu/Graphiti,
  fuera del plugin.
- Para reindexar Kwipu de verdad (`build_view`, reiniciar contenedores): esta skill **nombra** el
  remedio (`verify`), nunca lo ejecuta — es responsabilidad del stack externo (CA-16).
- Sin `taxonomy.json` con `backends.<id>.enabled: true`, no hay nada que sincronizar: `/doctor`
  reporta la capacidad como desactivada, y eso es correcto, no un error.

## Piezas

| Fichero | Qué es |
|---|---|
| `scripts/knowledge-sync.py` | Único punto de entrada; nunca menciona un backend concreto. |
| `backends/__init__.py` | Carga y valida el adaptador por `type` (`backends/README.md`: contrato completo de las 6 funciones). |
| `backends/markdown_export.py` | Adaptador Kwipu (`type: "markdown-export"`): CA-17/CA-16, ver `references/kwipu-adapter.md`. |
| `agent-kits/shared/knowledge-schema.py` | Taxonomía del proyecto (`taxonomy.json`), fail-closed. |
| `agent-kits/shared/knowledge-index.py` | Índice de `approved/`. |
| `agent-kits/shared/outbox.py` | Staging/dead-letter reutilizado (CA-15), nunca reimplementado aquí. |
| `agent-kits/shared/capabilities.py` | Registro de capacidades opcionales (`/setup`, `/doctor`, T-09). |

## Uso

Plugin instalable (regla 5 de `docs/CONVENTIONS.md`): localiza el script en runtime con el
patrón de seis raíces, nunca una ruta relativa fija.

```bash
KSSKILL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/knowledge-services/scripts/knowledge-sync.py' 2>/dev/null | head -1)"
python3 "$KSSKILL" --backend kwipu --root . --check
python3 "$KSSKILL" --backend kwipu --root . --dry-run
python3 "$KSSKILL" --backend kwipu --root .
python3 "$KSSKILL" --backend kwipu --root . --rebuild
```

- `--check`: `health()` + `verify()`, no toca la publicación. `exit 0` solo si `estado == "sano"`
  y `verify().ok`.
- `--dry-run`: calcula `plan()` y lo imprime; nunca llama a `apply()`.
- (ninguno): `plan()` + `apply()` reales, con staging idempotente de `outbox.py`; un fallo de
  `apply()` va a `dead-letter`, la publicación anterior queda intacta.
- `--rebuild`: `rebuild(entries, cfg)` sobre TODAS las entradas ya enrutadas para ese backend.

Añadir un backend nuevo: un fichero `backends/<type>.py` con las 6 funciones — ver
`backends/README.md` para el contrato exacto y `references/kwipu-adapter.md` para el ejemplo real
(Kwipu) con sus derivaciones documentadas (frontmatter CA-17, mapeo de salud, algoritmo de
`verify`).

## Guardrails

- **Fail-closed por routing**: una categoría sin `routing` declarado, o `routing.<id>: false`,
  jamás llega al adaptador — ni siquiera para "solo probar".
- **Nunca se borra la publicación anterior en error**: `apply()` publica ATÓMICO; un fallo va a
  `outbox.py` `dead-letter`, no se reintenta dentro de la misma corrida.
- **`verify` nombra, no ejecuta** (CA-16): el reindexado real es del stack, nunca de este plugin.
- **Sin dependencias externas**: todo el código de esta skill es stdlib puro.

## Qué NO hace

- No decide taxonomía ni categorías (eso es `taxonomy.json`, por proyecto).
- No aprueba ni rechaza conocimiento (eso es `knowledge-curator`).
- No registra el backend en Kwipu/Graphiti por su cuenta (nada de "auto-discovery" de red).
