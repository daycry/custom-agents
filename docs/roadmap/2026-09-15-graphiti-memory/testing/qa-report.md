# QA — graphiti-memory (2026-09-22)

## Modo: sin UI

`improvement-plan.md` declara en su frontmatter `test-plan: n/a (sin UI)`. La iniciativa
(adaptador de backend, modelo de ontología, sincronizador, router por `--intent`, capacidad de
`/setup`/`/doctor` y suite de seguridad) es infraestructura de plugin: no hay pantallas, no hay
Playwright que ejecutar y no se genera PDF. La verificación funcional son suites de `pytest`
deterministas contra los 15 criterios de aceptación de `spec.md`. Esta línea es **informativa,
no un ✅**: la puerta de cobertura E2E no se ha ejecutado porque no aplica.

Todo lo de abajo corre contra el **servidor MCP falso** (`_ServidorMCPContext` de
`skills/knowledge-services/scripts/test_backend_graphiti.py`) y contra servidores efímeros
propios en `127.0.0.1:0`: el servidor Graphiti real estaba **apagado** y no se escribió en
ningún grafo real.

## 1. `ledger-lint.py`

```
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-graphiti-memory/tasks.md
⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título
❌ resumen descuadrado en «Fase 4 - Regresion y cierre»: tabla dice 0/2, las tareas dicen 1/2
ledger-lint: 1 incoherencias · 1 avisos (tasks.md)
```

Esa es la salida en el momento de cerrar T-09 (T-10 todavía sin `Changelog`, Fase 4 a medias).
Tras cerrar T-10 la única incoherencia que queda es el **Resumen de progreso**, que por
decisión del orquestador de esta iniciativa NO lo escribe el implementer (es suyo, igual que en
el gap #111 de la Fase 3): la fila «Fase 4» dirá 0/2 hasta que él la ponga en 2/2. La salida
final está pegada en el campo `Verificacion` de T-10 en el ledger.

## 2. `coverage-check.py` (modo sin UI)

```
$ python agent-kits/qa/coverage-check.py docs/roadmap/2026-09-15-graphiti-memory/tasks.md docs/roadmap/2026-09-15-graphiti-memory/test-plan.md docs/roadmap/2026-09-15-graphiti-memory/spec.md
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 15 criterio(s) de aceptación de la spec (ninguno [GWT]) (CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-07, CA-08, CA-09, CA-10, CA-11, CA-12, CA-13, CA-15, CA-14): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["CA-01", "CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-15", "CA-14"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Exit 0. Marcador canónico (`marcador_no_canonico: null`), ningún `[GWT]` (`gwt_sin_id: 0`),
sin referencias rotas y `rutas_ui: []` (nada con pinta de interfaz en el diff, coherente con
«sin UI»). Los 15 `CA-XX` se listan «para la revisión» (`eximidos_exigidos: false`): no eran
exigibles por esta puerta, pero sí se cruzan a mano con tests en el punto 4.

## 3. Suites de la iniciativa

Las 8 rutas de la iniciativa **más** la suite de seguridad nueva de T-09:

```
$ python -m pytest -q -p no:cacheprovider tests/test_knowledge_router.py tests/test_knowledge_find.py \
    agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py \
    skills/knowledge-services/scripts tests/test_knowledge_services.py \
    agent-kits/shared/test_knowledge_schema.py tests/test_copias_declaradas.py \
    tests/test_graphiti_security.py
FAILED tests/test_knowledge_find.py::test_show_imprime_la_entrada_completa_tal_cual
FAILED tests/test_knowledge_find.py::test_show_json_envuelve_el_contenido_con_su_ficha
FAILED tests/test_knowledge_find.py::test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres
FAILED agent-kits/shared/test_doctor.py::test_hook_sin_bit_ejecutable_es_aviso_con_chmod
4 failed, 823 passed, 1 skipped, 8 subtests passed in 460.64s (0:07:40)
```

`823 = 800` (línea base de la Fase 3) `+ 23` de `tests/test_graphiti_security.py`. Los **4
rojos son PREEXISTENTES y solo de Windows** (los tres `test_*show*` por CRLF/`cp1252`, el de
`chmod` por el bit de ejecución de NTFS), idénticos a los de la Fase 3: no son regresión.

Suite de seguridad sola:

```
$ python -m pytest -q -p no:cacheprovider tests/test_graphiti_security.py
23 passed in 25.15s
```

`tests/test_hooks_shell.py` (segunda ruta de la `Verificacion` de T-09) da **52 rojos
preexistentes en esta máquina**: sus tests ejecutan los hooks con `bash`/`python3`, que este
Windows no expone. No se tocan en esta iniciativa.

## 4. Criterios de aceptación ↔ tests

| CA | Qué exige (resumen) | Tests que lo cubren |
|---|---|---|
| CA-01 | Solo entradas `approved` válidas crean episodios con id/versión/ruta | `tests/test_graphiti_security.py::test_solo_las_entradas_aprobadas_y_enrutadas_generan_episodios` · `skills/knowledge-services/scripts/test_backend_graphiti.py::test_apply_construye_episodio_idempotente_con_procedencia` · `::test_episodio_lleva_category_entity_type_y_hash_enviado` |
| CA-02 | Re-sincronizar no duplica ni borra historial | `skills/knowledge-services/scripts/test_backend_graphiti.py::test_apply_es_idempotente_no_reenvia_add_memory_si_nada_cambio` · `::test_entrada_retirada_de_approved_genera_revoke_y_tombstone` |
| CA-03 | Consultas temporales/relacionales con procedencia y vigencia | `skills/knowledge-services/scripts/test_backend_graphiti.py::test_consultar_marca_invalidado_lo_que_tiene_tombstone` · `::test_consultar_descarta_un_nodo_sin_procedencia_conocida` · `::test_f3fix2_gap118_con_v1_y_v2_se_sirve_la_vigente_venga_en_el_orden_que_venga` |
| CA-04 | Endpoint apagado / backend sin datos degradan sin bloquear | `tests/test_graphiti_security.py::test_ca04_endpoint_apagado_degrada_sin_bloquear` · `::test_ca04_backend_sin_datos_no_bloquea_la_lectura_enrutada` |
| CA-05 | Ningún agente escribe directamente; solo Curator + sincronizador | `tests/test_graphiti_security.py::test_ca05_ninguna_pieza_invoca_primitivas_de_escritura_en_el_grafo` · `::test_ca05_ninguna_pieza_ajena_invoca_el_sincronizador_en_modo_escritura` · `::test_e18_ningun_agente_normal_cita_el_backend_graphiti` |
| CA-06 | Kwipu conserva lo documental y Graphiti no se consulta por defecto | `tests/test_knowledge_router.py::test_cli_sin_intent_no_toca_el_router_ni_cambia_el_contrato` · `::test_intent_no_declarado_cae_al_camino_local` · `::test_mode_shadow_no_lee_aunque_el_intent_este_declarado` |
| CA-07 | Categoría sin `routing.graphiti: true` nunca genera episodios (fail-closed) | `skills/knowledge-services/scripts/test_knowledge_sync.py::test_categoria_sin_routing_declarado_nunca_llega_al_adaptador` · `::test_routing_false_nunca_llega_al_adaptador` · `tests/test_graphiti_security.py::test_ningun_episodio_lleva_texto_de_lo_excluido` |
| CA-08 | Graphiti es un adaptador del contrato; el núcleo no lo menciona | `skills/knowledge-services/scripts/test_backends_init.py::test_adaptador_graphiti_vacio_falla_con_mensaje_claro` · `::test_tipo_valido_markdown_export_carga` · comprobación mecánica: `grep -c -i graphiti agent-kits/shared/doctor.py agent-kits/shared/knowledge-find.py skills/knowledge-services/scripts/knowledge-sync.py` → `0` en los tres |
| CA-09 | Proveedor de LLM/embeddings es configuración; nada cableado | `agent-kits/shared/test_knowledge_schema.py::test_graphiti_provider_llm_invalido` · `::test_graphiti_provider_none_no_exige_modelo` · `::test_graphiti_provider_model_obligatorio_si_llm_no_es_none_gap37` · `::test_graphiti_provider_api_key_no_puede_ser_un_secreto_inline` |
| CA-10 | `mode: off/shadow/read`; `shadow` no lee; `read` exige health/verify | `agent-kits/shared/test_knowledge_schema.py::test_graphiti_mode_invalido` · `tests/test_knowledge_router.py::test_mode_shadow_no_lee_aunque_el_intent_este_declarado` · `::test_intent_declarado_y_mode_read_consulta_el_backend` · `skills/knowledge-services/scripts/test_backend_graphiti.py::test_mode_off_rechaza_rebuild_y_revoke` |
| CA-11 | `--rebuild` reproducible (mismo manifiesto) y `revoke` sin borrar historial | `skills/knowledge-services/scripts/test_backend_graphiti.py::test_rebuild_reproduce_el_mismo_manifiesto_que_la_sincronizacion_incremental` · `::test_rebuild_es_el_unico_camino_que_llama_a_clear_graph_acotado_al_grupo_propio` · `::test_revoke_escribe_tombstone_sin_llamar_a_delete_episode` |
| CA-12 | Router por configuración, `intent` declarado, no declarado → local | `tests/test_knowledge_router.py::test_backends_para_intent_solo_los_habilitados_que_declaran_el_intent` · `::test_backends_para_intent_exige_true_estricto_no_verdad_difusa` · `::test_cli_intent_no_declarado_sirve_lo_local` · `::test_cli_intent_invalido_es_error_de_uso` |
| CA-13 | Ontología desde `taxonomy.json`, `entity_types` los define el servidor | `tests/test_graphiti_model.py::test_proponer_entity_types_yaml_incluye_nucleo_y_categorias` · `::test_tipo_entidad_usa_entity_map` · `::test_proponer_config_devuelve_yaml_y_entity_map_completos` · `skills/knowledge-services/scripts/test_backend_graphiti.py::test_episodio_lleva_category_entity_type_y_hash_enviado` |
| CA-14 | Salida estructurada inválida del proveedor → dead-letter, sin datos corruptos | `tests/test_graphiti_security.py::test_ca14_salida_estructurada_invalida_del_proveedor_no_llega_a_add_memory` · `::test_ca14_ollama_invalido_acaba_en_dead_letter_sin_tocar_el_manifiesto` |
| CA-15 | Cliente MCP streamable HTTP mínimo con stdlib (`/mcp` sin barra, 307, sesión) | `skills/knowledge-services/scripts/test_backend_graphiti.py::test_initialize_y_get_status_via_handshake_completo` · `::test_redireccion_307_de_mcp_con_barra_se_sigue_sin_romper` · `::test_sesion_caducada_404_reintenta_initialize_una_vez` · `tests/test_graphiti_security.py::test_la_sesion_no_cruza_esquema_host_ni_puerto` |

Los 15 CA tienen al menos dos tests que los ejercen; ninguno queda «cubierto por inspección».

### Puerta E18 de `docs/agents/CONTRACTS.md`

```
$ grep -rn -i graphiti agents/*.md | grep -v knowledge-curator.md | wc -l
0

$ python -m pytest -q -p no:cacheprovider tests/test_graphiti_model.py tests/test_knowledge_router.py tests/test_knowledge_services.py -k "router or f3fix1"
53 passed, 84 deselected in 19.75s
```

## 5. Revisión adversarial de las tres fases

Conteo mecánico por **fila** de todas las tablas de revisión del ledger (una misma fila se
repite entre intentos cuando el siguiente intento la re-verifica; lo que decide es su columna
de corrección):

| Fase | Secciones | Filas | Critical | Important | Minor | Sin cerrar |
|---|---|---:|---:|---:|---:|---:|
| Fase 1 (T-01..T-03) | 3 intentos | 30 | 0 | 10 | 20 | 0 |
| Fase 2 (T-04..T-06) | 3 intentos + verificación dirigida | 65 | 10 | 23 | 32 | 0 |
| Fase 3 (T-07, T-08) | 3 intentos + verificación dirigida | 58 | 2 | 15 | 41 | 0 |
| **TOTAL** | **10 secciones** | **153** | **12** | **48** | **93** | **0** |

Comprobación reproducible (recorre las secciones «Revisión…»/«Verificación dirigida…» del
ledger, cuenta filas por grado y lista las que no tienen marca de cierre en NINGUNA celda):

```python
import re
t = open("docs/roadmap/2026-09-15-graphiti-memory/tasks.md", encoding="utf-8").read()
tot, pend = {}, []
for s in re.split(r"\n## ", t):
    cab = s.splitlines()[0]
    if not re.match(r"(Revisi|Verificaci)", cab):
        continue
    for l in s.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", l):
            continue
        cols = [c.strip() for c in l.strip().strip("|").split("|")]
        g = re.sub(r"[*]", "", cols[1]).split(" (")[0]
        tot[g] = tot.get(g, 0) + 1
        if not any(re.match(r"\**(corregid|descartad|cerrad|sin cambio|no aplica|n/a|confirmad|ya estaba)", c, re.I) for c in cols[2:]):
            pend.append((cab[:50], cols[0], g))
print("TOTAL filas por grado:", tot)
print("filas SIN marca de cierre en ninguna celda:", len(pend))
```

Salida real (2026-09-22):

```
TOTAL filas por grado: {'Important': 48, 'Minor': 93, 'Critical': 12}
filas SIN marca de cierre en ninguna celda: 0
```

**0 gaps Critical/Important pendientes** al cierre de la Fase 4. La Fase 4 (T-09, T-10) aún no
ha pasado por su propia revisión de dos lentes: la dispara el orquestador después de esta
entrega y sus gaps irán a una sección nueva del ledger.

## 6. Puertas del repo

```
$ python scripts/lint_plugin.py
lint_plugin: 10 agentes · 0 errores · 3 avisos

$ python evals/check.py
evals/check: 40 ficheros · 144 casos (86 positivos, 58 negativos) · 40 piezas del repo · 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 50 ficheros al día
```

Las tres en exit 0. Los 3 avisos de `lint_plugin` son nombres genéricos de comando (`retro`,
`roadmap-status`, `setup`), preexistentes y ajenos a esta iniciativa.

## Veredicto

**Verde, sin UI.** 823 tests verdes en las 9 rutas de la iniciativa (4 rojos preexistentes de
Windows, ninguno de esta fase), los 15 CA cruzados con tests reales, puerta E18 en verde, las
tres puertas del repo en 0 y ninguna escritura contra el servidor Graphiti real. Lo único
abierto es de proceso, no de producto: el **Resumen de progreso** del ledger (lo actualiza el
orquestador) y la **revisión de dos lentes de la Fase 4**, todavía por lanzar.
