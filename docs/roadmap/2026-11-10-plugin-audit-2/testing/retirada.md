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

## Medidas (T-08)

| Medida | Antes (`21ad63f`) | Después |
|---|---|---|
| `skills/knowledge-services/` (ficheros versionados · líneas) | 49 · 20.617 | 10 · 2.404 (marco + adaptador de prueba) |
| Ficheros bajo `agent-kits skills tests install hooks scripts evals` que citan Kwipu/Graphiti | 90 · 46.971 líneas | 20 (ver «menciones declaradas») · las 63 supervivientes de la lista original suman 23.327 |
| `tests/test_graphiti_security.py` → `tests/test_hook_network_egress.py` | 2.953 líneas · 126 tests | 1.913 líneas · 90 tests |
| `tests/test_graphiti_model.py` | 418 líneas | borrado |

## Tests quitados de la suite «ningún hook hace red» (36; 11 restaurados en fix1, ver abajo)

Clasificación por nombre; son los de episodios `add_memory`, proveedores Ollama, puertas CA-05/E18 sobre
la escritura en el grafo y guardarraíl de red del cliente MCP (IMDS, redirecciones, sesión). **Corrección
del intento 1 (fix1, gap 1):** la puerta CA-05 del *sincronizador* no dependía de Graphiti —protege
`docs/CONSTITUTION.md` (publicar a un backend es posterior a la curación)— y se restauró (marcados
«restaurado» abajo) en `tests/test_sync_write_gate.py` (11 tests, `git show 21ad63f:tests/test_graphiti_security.py`
sin nada de Graphiti ni de las primitivas `add_memory`…, que sí eran del grafo; exención nominal de
`SKILL.md`, `backends/README.md` y `references/add-backend.md`):
- `test_aviso_de_grupo_del_sincronizador_es_solo_lectura_para_la_puerta_ca05` — restaurado
- `test_ca04_backend_sin_datos_no_bloquea_la_lectura_enrutada`
- `test_ca04_endpoint_apagado_degrada_sin_bloquear`
- `test_ca05_ninguna_pieza_ajena_invoca_el_sincronizador_en_modo_escritura` — restaurado
- `test_ca05_ninguna_pieza_invoca_primitivas_de_escritura_en_el_grafo`
- `test_ca14_el_proveedor_real_que_inyecta_uuid_no_gasta_add_memory_y_acaba_en_dead_letter`
- `test_ca14_ollama_invalido_acaba_en_dead_letter_sin_tocar_el_manifiesto`
- `test_ca14_un_doble_de_proveedor_con_estructura_invalida_no_llega_a_add_memory`
- `test_cada_salto_de_redireccion_se_revalida_contra_el_guardarrail`
- `test_direcciones_sin_sentido_como_destino_se_rechazan`
- `test_e18_ningun_agente_normal_cita_el_backend_graphiti`
- `test_el_origen_de_un_salto_es_la_terna_esquema_host_puerto`
- `test_el_recorrido_de_piezas_no_esta_vacio` — restaurado
- `test_el_servidor_mcp_falso_se_carga_una_sola_vez`
- `test_f4fix2_el_modulo_de_apoyo_mcp_es_solo_ascii`
- `test_f4fix2_la_validacion_exige_source_y_source_description_aunque_no_haya_base`
- `test_f4fix2_las_references_de_la_skill_duena_no_estan_exentas_por_prefijo` — restaurado
- `test_f4fix2_probe_p3_una_variable_en_prosa_no_es_una_invocacion` — restaurado
- `test_f4fix2_probe_p6_y_p4_la_invocacion_multilinea_no_evade_la_puerta` — restaurado
- `test_f4fix2_un_bloque_que_parte_la_publicacion_en_dos_lineas_es_una_unidad` — restaurado
- `test_f4fix2_un_proveedor_que_altera_la_identidad_o_pierde_campos_no_llega_a_add_memory`
- `test_f4fix2_una_invocacion_multilinea_de_solo_lectura_sigue_siendo_legitima` — restaurado
- `test_f4fix2_vacio_es_tambien_la_cadena_vacia_o_en_blanco`
- `test_f4fix3_una_valla_sin_cerrar_cuenta_como_bloque_hasta_el_final` — restaurado
- `test_host_publico_sin_allow_remote_se_rechaza_antes_de_conectar`
- `test_imds_se_rechaza_siempre_incluso_con_allow_remote`
- `test_la_sesion_no_cruza_esquema_host_ni_puerto`
- `test_la_sesion_tampoco_cruza_de_hostname_con_el_mismo_puerto`
- `test_mutante_primitivas_en_una_pieza_inyectada_que_no_es_skill_md`
- `test_mutantes_de_invocacion_del_sincronizador_no_pasan_la_puerta` — restaurado
- `test_ningun_episodio_lleva_texto_de_lo_excluido`
- `test_openers_de_graphiti_ignoran_proxy_del_entorno`
- `test_redirecciones_301_302_303_no_se_siguen`
- `test_solo_las_entradas_aprobadas_y_enrutadas_generan_episodios`
- `test_una_cadena_de_redirecciones_no_es_infinita`
- `test_una_linea_de_solo_lectura_sigue_siendo_legitima` — restaurado

Se conservan los 90 restantes: escáner «ningún hook hace red» (recorrido transitivo, mutantes, AST,
lanzador de Node con su SHA-256 revisado, almacén de actividad), y el espía de `cargar_adaptador`
con el argv real de `hooks/session-context.sh`, ahora sobre un backend genérico de prueba.
`pytest --collect-only` del fichero: 90 (= 126 − 36).

## Decisiones tomadas al ejecutar (T-08)

- **Mensaje «retirado»:** vive en `backends/__init__.py` (`RETIRADOS`, `VERSION_RETIRADA`), no en
  `knowledge-sync.py`: el invariante «el núcleo no nombra ningún backend» y su test se conservan. Solo
  afina el «no encontrado» (si el proyecto aporta su propio adaptador con ese `type`, se carga). No
  menciona ningún sustituto.
- **Router de lectura:** ya no deriva `group_id` (era de Graphiti): entrega la config declarada tal cual
  (`copias.json` pierde los bloques `hosts_locales`, `direccion_prohibida_siempre`, `group_id_por_defecto`
  y `modo_backend`; `sanear_detalle` baja de 5 a 2 copias: `knowledge-find.py` y `doctor.py`).
- **Panel de memoria:** deja de leer manifiestos de adaptador; lista los backends declarados con la
  fecha de su outbox y no inventa filas «no configurado» para Kwipu/Graphiti.
- **`knowledge-schema.py`:** sin reglas por `type` (la validación de `backends.<id>` es la genérica de
  `knowledge-taxonomy-local.py`); `--setup-id-prefix` ya no devuelve `instalacion_previa` ni avisa de
  conocimiento exportado (eran manifiestos de los adaptadores retirados).
- **Plantilla y respaldo de `taxonomy.json`:** `backends: {}` y categorías sin `routing` (fail-closed:
  no exportan a ningún sitio).

## Lectura documental de Kwipu (resuelta en fix1, gap 2)

Se retiró lo que quedaba: la rama `markdown-export` de `consultar_intent` y `_documental_prepare` de
`knowledge-find.py`, `knowledge-read-context.py` (+ su test), `documental_read_options`/`DOCUMENTAL_READ_LIMITS`
de `knowledge-taxonomy-local.py`, el reenvío de `knowledge-schema.py`, `documentalConfig` del esquema, las filas
E44 y E43 (lectura) de `docs/agents/CONTRACTS.md` y la fila del README de `agent-kits/shared`. `markdown-export` da
ahora el mismo «retirado desde la versión 4.0.0 … add-backend.md» que `graphiti` en `--intent`
(`tests/test_knowledge_router_read.py`, parametrizado). La salida `respuesta_generada` queda como campo
**genérico** de un adaptador propio, sin el vínculo canónico del contexto documental (`no_verificada`, sin
autoridad); `tests/test_knowledge_router_read.py` pasa de 16 tests documentales a los genéricos y la guarda.

## `/doctor` y panel con backends declarados (fix1, gap 3)

`knowledge-gate` publica en `health.backends` los ids con `enabled: true` (contrato genérico, sin nombres): una
fila por backend con la comprobación en vivo si el adaptador carga, o ⚠️ «no disponible» con la guía si es
retirado o desconocido. El panel marca `retirado` a un backend activo cuyo `type` figura en `RETIRADOS` (lectura
con `ast`, sin ejecutar nada). El adaptador de prueba contiene sus rutas (gap 4) y la guía lo exige.

## Menciones declaradas (lo que sigue citando los nombres tras T-08)

- Guardas de ausencia y compatibilidad: `skills/knowledge-services/backends/__init__.py` (`RETIRADOS`),
  `skills/knowledge-services/scripts/test_knowledge_sync.py` (backend retirado sale con «retirado»),
  `agent-kits/shared/test_capabilities.py`, `agent-kits/shared/test_knowledge_schema.py` (taxonomía heredada
  valida con reglas genéricas), `agent-kits/shared/test_doctor.py` y `tests/test_knowledge_router.py`
  (el núcleo no nombra ningún backend), `tests/test_hook_network_egress.py` (cabecera histórica), `tests/test_knowledge_router_read.py` y `tests/test_panel_data.py` (un `type` retirado sale «retirado»), `tests/test_doctor_notes_in_docs.py` y `tests/fixtures/dev-cycle-modular-replacements.json` (motivos fechados).
- Documentación y evals que retira T-09: `agent-kits/dev-cycle/references/phase4-knowledge-gate.md`,
  `agent-kits/shared/{README,doctor-reference}.md`, `evals/cases/{command-setup,skill-knowledge-category-template,skill-knowledge-services}.json`,
  `skills/knowledge-category-template/SKILL.md`, `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}`,
  `tests/fixtures/opencode-v2-agent-contract.json` (descripción del agente `knowledge-curator`).
- Fuera de alcance, congelada: `skills/training-data-services/**` (la retira o no T-32).
