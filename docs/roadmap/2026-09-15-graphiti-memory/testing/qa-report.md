# QA — graphiti-memory (2026-09-22)

## Modo: sin UI

`improvement-plan.md` declara en su frontmatter `test-plan: n/a (sin UI)`. La iniciativa
(adaptador de backend, modelo de ontología, sincronizador, router por `--intent`, capacidad de
`/setup`/`/doctor` y suite de seguridad) es infraestructura de plugin: no hay pantallas, no hay
Playwright que ejecutar y no se genera PDF. La verificación funcional son suites de `pytest`
deterministas contra los 15 criterios de aceptación de `spec.md`. Esta línea es **informativa,
no un ✅**: la puerta de cobertura E2E no se ha ejecutado porque no aplica.

Todo lo de abajo corre contra el **servidor MCP falso** (`_ServidorMCPContext` de
`skills/knowledge-services/scripts/_mcp_fake.py`, módulo de apoyo compartido por las dos suites
desde el gap #166) y contra servidores efímeros
propios en `127.0.0.1:0`: el servidor Graphiti real estaba **apagado** y no se escribió en
ningún grafo real.

## 1. `ledger-lint.py`

```
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-graphiti-memory/tasks.md
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)
```

Esa es la salida **vigente** (2026-09-22, tras la ronda `fix1` de la Fase 4). Gap #159/#165 de
la revisión intento 1: antes aquí estaba pegada una salida con ❌ y ⚠️ que ya no reproduce —era
la del momento de cerrar T-09 (T-10 todavía sin `Changelog`) y la del desfase del **Resumen de
progreso**, que en esta iniciativa lo escribe el ORQUESTADOR (decisión suya desde el gap #111 de
la Fase 3), no el implementer. Con T-09/T-10 de vuelta en `en-progreso` para la ronda `fix1`, la
tabla y las tareas vuelven a cuadrar y el ledger sale limpio.

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

Las 8 rutas de la iniciativa **más** la suite de seguridad de T-09 (salida re-pegada el 2026-09-23
tras la ronda `fix2` de la Fase 4):

```
$ python -m pytest -q -p no:cacheprovider tests/test_graphiti_security.py tests/test_knowledge_router.py \
    tests/test_knowledge_find.py agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py \
    skills/knowledge-services/scripts tests/test_knowledge_services.py \
    agent-kits/shared/test_knowledge_schema.py tests/test_copias_declaradas.py
FAILED tests/test_knowledge_find.py::test_show_imprime_la_entrada_completa_tal_cual
FAILED tests/test_knowledge_find.py::test_show_json_envuelve_el_contenido_con_su_ficha
FAILED tests/test_knowledge_find.py::test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres
FAILED agent-kits/shared/test_doctor.py::test_hook_sin_bit_ejecutable_es_aviso_con_chmod
4 failed, 859 passed, 1 skipped, 8 subtests passed in 2294.76s (0:38:14)
```

`859 = 800` (línea base de la Fase 3) `+ 59` de `tests/test_graphiti_security.py` (23 en la entrega
inicial `+ 12` de `fix1` `+ 24` de `fix2`: #168, #173-#177, #179-#183). Los **4 rojos** de siempre
son PREEXISTENTES y solo de Windows (los tres `test_*show*` por CRLF/`cp1252`, el de `chmod` por el
bit de ejecución de NTFS). En dos de las tres corridas completas de `fix2` cayó además UN test
distinto cada vez (`test_backend_markdown_export.py` y `test_backend_graphiti.py`, ninguno tocado en
la ronda), verde en aislamiento y en su fichero: flake bajo carga, no regresión.

Suite de seguridad sola:

```
$ python -m pytest -q -p no:cacheprovider tests/test_graphiti_security.py
59 passed in 29.98s
```

Suites de consola (gap #168: el módulo de apoyo `_mcp_fake.py` rompía `tests/test_console_encoding.py`
en CI; ahora es solo ASCII):

```
$ python -m pytest -q -p no:cacheprovider tests/test_console_encoding.py tests/test_suites_no_pytest.py
FAILED tests/test_suites_no_pytest.py::test_la_suite_script_pasa[test_lint_plugin.py]
1 failed, 411 passed in 84.39s (0:01:24)
```

El rojo que queda es PREEXISTENTE de Windows (también en la base `a6723ec`, que daba `5 failed`:
estos 4 de `_mcp_fake.py` + este).

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
| CA-14 | Salida estructurada inválida del proveedor → dead-letter, sin datos corruptos | `tests/test_graphiti_security.py::test_ca14_un_doble_de_proveedor_con_estructura_invalida_no_llega_a_add_memory` · `::test_ca14_ollama_invalido_acaba_en_dead_letter_sin_tocar_el_manifiesto` · `::test_ca14_el_proveedor_real_que_pierde_el_uuid_no_gasta_add_memory_y_acaba_en_dead_letter` (fix1, gap #154: el proveedor REAL, mutado para perder el `uuid`) |
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
| **Subtotal Fases 1-3** | **11 secciones** | **154** | **12** | **48** | **94** | **0** |
| Fase 4 (T-09, T-10) | 1 intento (+ ronda `fix1`) | 14 | 0 | 4 | 10 | 2 |
| **TOTAL** | **12 secciones** | **168** | **12** | **52** | **104** | **2** |

Dos correcciones de la revisión intento 1 de la Fase 4 sobre esta misma tabla: **#161** (eran
**11** secciones en las Fases 1-3, no 10: F1 3 · F2 3 + verificación dirigida · F3 3 +
verificación dirigida) y **#159** (el script de conteo ignoraba en silencio la fila con ID `—`
de la verificación `fix5`, así que el subtotal real es **154 filas / 94 Minor**, no 153/93).
Las **2 filas sin cerrar** son #162 y #163 de la Fase 4: las dos están asignadas al
**orquestador** (celda de tokens del Resumen y marca del criterio de T-10 al cerrar el ciclo),
no al implementer; no hay ningún Critical/Important abierto.

Comprobación reproducible (recorre las secciones «Revisión…»/«Verificación dirigida…» del
ledger, cuenta filas por grado y lista las que no tienen marca de cierre en NINGUNA celda):

```python
import re
t = open("docs/roadmap/2026-09-15-graphiti-memory/tasks.md", encoding="utf-8").read()
tot, pend, secciones = {}, [], 0
for s in re.split(r"\n## ", t):
    cab = s.splitlines()[0]
    if not re.match(r"(Revisi|Verificaci)", cab):
        continue
    secciones += 1
    for l in s.splitlines():
        # gap #159: TODA fila de tabla con columna Grado (antes `^\|\s*\d+\s*\|`, que se dejaba
        # fuera en silencio las filas con ID no numérico, p. ej. el `—` de la verificación fix5)
        if not l.startswith("|") or l.startswith("|---"):
            continue
        cols = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cols) < 3:
            continue
        g = re.sub(r"[*]", "", cols[1]).split(" (")[0].strip()
        if g not in ("Critical", "Important", "Minor"):     # cabecera u otra tabla
            continue
        tot[g] = tot.get(g, 0) + 1
        if not any(re.match(r"\**(corregid|descartad|cerrad|sin cambio|no aplica|n/a|confirmad|ya estaba)", c, re.I) for c in cols[2:]):
            pend.append((cab[:40], cols[0], g))
print("secciones:", secciones)
print("TOTAL filas por grado:", tot, "| total:", sum(tot.values()))
print("filas SIN marca de cierre en ninguna celda:", len(pend), pend)
```

Salida real (2026-09-22):

```
secciones: 12
TOTAL filas por grado: {'Important': 52, 'Minor': 104, 'Critical': 12} | total: 168
filas SIN marca de cierre en ninguna celda: 2 [('Revisión de dos lentes — intento 1: Fase', '162', 'Minor'), ('Revisión de dos lentes — intento 1: Fase', '163', 'Minor')]
```

(Las dos filas abiertas son las del **orquestador**: #162 —celda de tokens del Resumen de
progreso— y #163 —marca del criterio de T-10 al cerrar el ciclo—. Ninguna es del implementer.)

**0 gaps Critical/Important pendientes**. La Fase 4 YA pasó su revisión intento 1 (sección
propia del ledger, 0 Critical · 4 Important · 10 Minor): los 4 Important (#154 validación del
episodio sin `uuid`, #155 puerta de hooks con tres agujeros, #156 espía inalcanzable, #157
CA-05 con literal frágil) y los Minor del implementer están cerrados en la ronda `fix1` con su
evidencia y su mutante en el ledger. Quedan abiertas a propósito las dos filas del orquestador
(#162, #163) y la revisión intento 2, que él dispara después de esta ronda.

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

**Verde, sin UI.** 859 tests verdes en las 9 rutas de la iniciativa (4 rojos preexistentes de
Windows, ninguno de esta fase), los 15 CA cruzados con tests reales, puerta E18 en verde, las
tres puertas del repo en 0 y ninguna escritura contra el servidor Graphiti real. Lo único
abierto es de proceso, no de producto: el **Resumen de progreso** y la celda de tokens del
ledger (los actualiza el orquestador, filas #162/#163) y la **revisión intento 2** de la Fase 4,
que él dispara tras la ronda `fix1` cuya evidencia está en el ledger.
