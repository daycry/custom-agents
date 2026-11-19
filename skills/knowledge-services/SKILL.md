---
name: knowledge-services
description: >
  Marco para publicar conocimiento aprobado a un backend externo que el proyecto enchufa: carga
  adaptadores por `type` (contrato de 6 funciones), aplica routing cerrado y usa una outbox
  recuperable. El plugin no incluye adaptadores. Lectura externa solo opt-in; no promueve candidatos.
  Úsala cuando el usuario diga "sincroniza el conocimiento con mi backend", "publica
  docs/knowledge/approved en un servicio externo", "por qué mi backend no ve esta entrada", "añade un
  backend de knowledge-services" o "cómo conecto un MCP de memoria al proyecto".
---

# knowledge-services — de `approved/` a un backend externo, sin acoplar el plugin a ninguno

## Alcance y activación

Publica `docs/knowledge/approved/` a backends externos por config de proyecto (`taxonomy.json`).
`knowledge-sync.py --backend <id> [--dry-run|--check|--rebuild]` carga el adaptador por `type`,
aplica `routing` antes de construir entradas (fail-closed) y usa `outbox.py` para
staging/dead-letter; un fallo de `apply()` puede dejar una publicación parcial recuperable, sin
rollback global. **El plugin no incluye ningún adaptador** (`backends/` solo trae el cargador y el
contrato): un proyecto escribe el suyo, lo declara en `taxonomy.json` y lo carga por
`backends/<type>.py` o por un directorio extra (`--backends-dir`). Un `type` sin adaptador sale con
exit 2 y un mensaje claro, sin traceback; los backends que el plugin incluyó hasta 3.x
(retirados en 4.0.0) lo dicen como «retirado». La lectura externa opcional usa
`knowledge-find.py --intent`, con backend habilitado, `read` e intent autorizados.

`docs/knowledge/approved/` es el origen Markdown canónico, curado por `knowledge-curator`.
Su versionado en Git depende de la política del proyecto; la memoria propia de este repositorio
está excluida de Git. La recuperación local consulta tanto este corpus como ADR/GOT/LES legados.
Esta skill lo **proyecta** hacia fuera mediante un adaptador del proyecto, sin cambiar el núcleo
(`knowledge-sync.py`). Instalar la skill no habilita ni configura ningún servicio externo.

## Módulo y puerto opcionales

Esta skill pertenece a `memory-integrations`, fuera del perfil core. Curación y
recuperación local conservan sus dueños en el shared kit y no la requieren.
Para usar un proveedor desde el workflow común, lee
[Integración de proyecto](references/project-integration.md): bindings del propósito
`knowledge`, backend exacto, autorización, routing y recibos existentes. Instalar el
módulo, declarar el binding y verificar una operación son estados diferentes.

## Cuándo NO usarla

- Para curar o aprobar conocimiento: productores proponen por `agent-kits/shared/knowledge-curation.py`;
  `knowledge-curator` juzga, `curator-gate.py` valida sin persistir y el servicio aplica con SHA
  original/motivo/metadatos. Esta skill sólo lee `approved/`, nunca escribe ahí ni aprueba por sync.
- Para consultar conocimiento: usa `agent-kits/shared/knowledge-find.py`. Su router por `--intent`
  consulta un backend enchufado solo con autorización explícita y conserva el respaldo local con su
  motivo; sin backend declarado devuelve únicamente lo local.
- Para reindexar un servicio externo (reconstruir índices, reiniciar contenedores): esta skill
  **nombra** el remedio (`verify`), nunca lo ejecuta — es responsabilidad del servicio (CA-16).
- Sin `taxonomy.json` con `backends.<id>.enabled: true`, no hay nada que sincronizar: `/doctor`
  reporta la capacidad como desactivada, y eso es correcto, no un error.

## Piezas

| Fichero | Qué es |
|---|---|
| `scripts/knowledge-sync.py` | Único punto de entrada; nunca menciona un backend concreto. |
| `backends/__init__.py` | Carga y valida el adaptador por `type` (`backends/README.md`: contrato completo de las 6 funciones). |
| `scripts/fixtures/adaptador_prueba.py` | Adaptador de PRUEBA de las suites del marco (`type: "adaptador-prueba"`): publica en una carpeta con diario; se carga por `directorios`, nunca desde `backends/`. |
| `agent-kits/shared/knowledge-find.py` | Recuperación local y router por `--intent`: lectura externa autorizada o fallback local con motivo; lee `backends/README.md` al configurar esa lectura. |
| `agent-kits/shared/knowledge-schema.py` | Taxonomía del proyecto (`taxonomy.json`), fail-closed; `--setup-id-prefix` propone/valida/guarda el `id_prefix` (CA-14). Aviso de destino ajeno, si el adaptador lo implementa: `knowledge-sync.py --avisos-grupo [--consultar-servidor]`. |
| `agent-kits/shared/knowledge-curation.py` + `agent-kits/shared/knowledge-curation-rules.py` | Dueños de persistencia y validación reutilizable en la fase anterior a sync; propose/apply/recover no se invocan para publicar ni sustituyen juicio del Curator. Referencias del bundle compartido, no un segundo gate. |
| `agent-kits/shared/knowledge-index.py` | Índice de `approved/`. |
| `agent-kits/shared/knowledge-local.py` + `knowledge-taxonomy-local.py` | Lectores compartidos sin red: corpus aprobado y reglas locales de taxonomía. |
| `agent-kits/shared/knowledge-view.py` | Snapshot acotado y consulta local compartidos por CLI/panel; validación aprobada pura sobre textos ya leídos, sin caché o backends. |
| `agent-kits/shared/knowledge-read-context.py` + `agent-kits/shared/local-read.py` | Autorización canónica y lectura estable acotada para el opt-in documental; dependencias del bundle portable. |
| `agent-kits/shared/outbox.py` | Staging/dead-letter reutilizado (CA-15), nunca reimplementado aquí. |
| `agent-kits/shared/capabilities.py` | Registro de capacidades opcionales (`/setup`, `/doctor`, T-09). |

## Uso

Plugin instalable (regla 5 de `docs/CONVENTIONS.md`): localiza el script en runtime con el
patrón de seis raíces, nunca una ruta relativa fija.

```bash
R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; [ -f "$R/$M" ] || R="$(for r in "$PWD"/.{claude,codex,opencode} ~/.{claude,codex}/plugins/cache/daycry ~/.{claude,codex,config/opencode}; do find "$r" -maxdepth 5 -path "*/$M" ! -path "$r/jobs/*" ! -path "$r/worktrees/*" 2>/dev/null | sort -V | tail -1 | grep . && break; done)"; R="${R%/$M}"; KSSKILL="${R:+$R/skills/knowledge-services/scripts/knowledge-sync.py}"
python3 "$KSSKILL" --backend <id> --root . --check
python3 "$KSSKILL" --backend <id> --root . --dry-run
python3 "$KSSKILL" --backend <id> --root .
python3 "$KSSKILL" --backend <id> --root . --rebuild
python3 "$KSSKILL" --backend <id> --root . --outbox-status
```

- `--check`: `health()` + `verify()`, no toca la publicación ni la outbox. `exit 0` solo si
  `estado == "sano"` y `verify().ok`. `verify()` tiene TRES veredictos (`estado`: `ok` ·
  `incompleto` · `desfase`): `incompleto` (la ventana de lectura no alcanzó el grafo) NO es `ok`,
  se imprime con su `no_verificado` y su `aviso`, y sale ≠ 0.
- `--dry-run`: calcula `plan()` y lo imprime; nunca llama a `apply()` ni drena la outbox.
- (ninguno): primero DRENA la outbox propia — reintenta cualquier envelope PENDIENTE de este
  mismo backend cuyo backoff ya venció (`_drenar_outbox_propia`, aplica sus `ops` de forma
  idempotente; si vuelve a fallar, incrementa `intentos` de verdad y escala a `dead-letter` al
  llegar a `MAX_INTENTOS`) — y LUEGO hace `plan()` + `apply()` reales del sync fresco, con
  staging/dead-letter de `outbox.py`. Un envelope de OTRO backend que bloquee el reclamo se cede
  con `outbox.ceder_paso()` sin tocar su presupuesto de reintentos. Un fallo de `apply()` en el
  sync fresco reencola con backoff (nunca dead-letter directo por un solo fallo); la proyección
  puede quedar parcialmente actualizada; el diario del adaptador conserva el objetivo pendiente.
- `--rebuild`: `rebuild(entries, cfg)` sobre TODAS las entradas ya enrutadas para ese backend
  (equivale a `plan(entries, cfg, force=True)` + `apply`, fuerza `upsert` en todo).
- `--outbox-status`: imprime `outbox.estado()` de la cola de este backend y sale — no publica ni
  drena nada. Es el diagnóstico de referencia cuando una corrida sospecha que hay envelopes
  atascados.

Añadir un backend nuevo: un fichero `<type>.py` con las 6 funciones — ver `backends/README.md`
para el contrato exacto y `scripts/fixtures/adaptador_prueba.py` para un ejemplo completo.

## Guardrails

- **Fail-closed por routing**: una categoría sin `routing` declarado, o `routing.<id>: false`,
  jamás llega al adaptador — ni siquiera para "solo probar".
- **Recuperación por diario**: un adaptador que publica fichero a fichero lleva un diario
  (objetivo pendiente → publica → manifiesto final, como el adaptador de prueba) y nunca borra ni
  mueve ficheros ajenos a los que su propio manifiesto controla. Un fallo va primero
  a reencolado con backoff (`outbox.py`) y solo escala a `dead-letter` al agotar los reintentos —
  no se repite el apply fresco dentro de la misma corrida, sí en la siguiente. El drenaje
  precede al plan fresco para reconciliar el destino con el canon actual. El lote no es atómico;
  archivos ya publicados o revocados no se revierten.
- **`verify` nombra, no ejecuta** (CA-16): el reindexado real es del servicio, nunca de este plugin.
- **Lectura opt-in separada de publicar**: backend habilitado e intent declarado como `true`.
  Canon, routing y filtros preceden a la red/inferencia; incoherencias vuelven a local.
- **Respuesta generada sin autoridad**: `source_nodes` identifica fuentes recuperadas, no citas
  por afirmación. El lector no aprueba ni ejecuta instrucciones de esa respuesta.
- **Local sin Docker**: panel y hooks mantienen lectura local; no consultan ni arrancan servicios.
- **Validación no es aprobación/persistencia**: gate e índice verifican contrato/forma; Curator
  decide y `apply_decision` persiste ligado al SHA. Design/revisión/QA/Gold/repetición no aprueban
  memoria nueva. Legado conserva bytes/estados/autoridad sin migración ni reaprobación automática;
  conflicto/alto impacto exige resolución humana trazada, no fecha/score.
- **Límites de la capa de curación**: cerrojo cooperativo, etiquetas de actor no autenticadas,
  publicación/retirada/recibo separados; sin atomicidad multiarchivo ni sandbox universal.
  POSIX sincroniza directorios; el helper Windows no lo hace. La implementación y su revisión/QA
  no acreditan aceptación nativa o supervivencia a corte eléctrico. Esta skill no añade esos permisos.
- **Sin dependencias externas**: todo el código de esta skill es stdlib puro.

## Qué NO hace

- No decide taxonomía ni categorías (eso es `taxonomy.json`, por proyecto).
- No aprueba ni rechaza conocimiento (eso es `knowledge-curator`).
- No registra ni descubre servicios por su cuenta (nada de "auto-discovery" de red): el proyecto declara su backend en `taxonomy.json`.
- No incluye adaptadores concretos.
