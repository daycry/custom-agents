# Retirada de los backends Kwipu y Graphiti (plugin-audit-2, T-08..T-10)

Registro de la retirada decidida por el usuario el 2026-11-10. El marco `knowledge-services` se
conserva sin adaptadores incluidos (revisión del 2026-11-18, T-10).

## Cómo recuperar lo retirado

- **Commit recuperable:** `21ad63ffd07812c1c649e1ef184b71f7f1f1c51d` (rama `feat/plugin-audit-2`,
  `git rev-parse HEAD` justo antes de borrar). Release anterior que también lo contiene: `v3.3.0`
  (`fb3bb37`) y `v3.2.3`.
- **Cliente MCP de Graphiti:** `skills/knowledge-services/backends/graphiti.py`, clase `ClienteMCP`
  (línea 575 en el commit anotado), con su guardarraíl de red (`_SinRedireccionAutomatica`,
  `HostNoPermitido`) y el servidor MCP falso de las suites (`skills/knowledge-services/scripts/_mcp_fake.py`
  y `scripts/fixtures/graphiti/`). **No envía `Authorization: Bearer`**: habla con un endpoint local
  sin credenciales; quien lo reutilice contra un MCP autenticado debe añadir esa cabecera.
- Adaptador Kwipu: `skills/knowledge-services/backends/markdown_export.py` + `references/kwipu-adapter.md`
  + `scripts/kwipu-project-add.py`, en el mismo commit.
  Recuperar un fichero: `git show 21ad63f:<ruta> > <ruta>`.

## Suite «ningún hook hace red»

`tests/test_graphiti_security.py` no se borra entero: pasa a `tests/test_hook_network_egress.py`
(`git mv`), conserva el escáner que cargan `test_hook_launcher_security.py` y `hook-budget.test.mjs`
y su huella revisada (SHA-256 de `agent-activity-store.py`, actualizada en fix20), y pierde los tests
específicos de Graphiti (lista y recuento más abajo, al ejecutar).

## Acciones del usuario

- `.claude/knowledge-services/taxonomy.json` (local, no versionado) sigue declarando `kwipu` y
  `graphiti`. El plugin lo trata como retirado: `knowledge-sync.py --backend kwipu` sale con
  exit 2 y el mensaje «retirado en la versión 4.0.0». Quita ahí los backends y sus claves
  `routing.kwipu|graphiti`, o déjalo: no rompe nada, solo no publica.
- Los PDF generados (`output/pdf/custom-agents-manual-operativo.pdf` y
  `guia-resultados-calidad-custom-agents.pdf`) se regeneran con T-38; hoy aún citan los backends.
- Cualquier export ya publicado (`kwipu-export/`, grafo de Graphiti) no se toca: la retirada es
  del plugin, no de tus datos.
