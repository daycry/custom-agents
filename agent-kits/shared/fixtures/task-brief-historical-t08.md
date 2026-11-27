### T-08 - Capacidad `graphiti` registrada, setup/doctor y documentacion runtime
- **Estado**: completado
- **Dependencias**: T-04, T-07
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `agent-kits/shared/test_doctor.py` (dos tests que fijan CA-14 desde el lado de `/doctor`: la cadena `graphiti` no aparece en `doctor.py` y una capacidad inventada al vuelo sale pintada sin tocarlo), `commands/setup.md`, `commands/doctor.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**` (regenerado: solo cambian los 4 ficheros derivados de `commands/doctor.md` y `commands/setup.md`), `agent-kits/shared/doctor.py` (fix1, gap #99: `_ids_backend_declarados`/`_leer_backend_entry` genericos, una fila por backend declarado; `grep -c graphiti` sigue en 0), `skills/knowledge-services/backends/graphiti.py` (fix1, gap #109: `modo(cfg)` publica), `agent-kits/shared/copias.json` (fix2, gap #122: quinta copia declarada del bloque `sanear_detalle`, en `doctor.py`), `skills/knowledge-services/backends/markdown_export.py` y `agent-kits/shared/knowledge-find.py` (fix2, gap #122: solo el centinela de la copia, «CUATRO» -> «CINCO», sin cambio de comportamiento), `agent-kits/shared/doctor.py` (fix3, gaps #133/#137; `grep -c graphiti` sigue en 0), `agent-kits/shared/test_doctor.py` (fix3, gaps #133/#137), `agent-kits/shared/capabilities.py` y `agent-kits/shared/test_capabilities.py` (fix3, gap #147), `commands/doctor.md` + `interop/**` (fix3, gap #133: la fila `(backend)` documenta el veredicto `incompleto`; regenerado con `export-interop.py`), `agent-kits/shared/doctor.py` + `agent-kits/shared/test_doctor.py` (fix4, gaps #148/#152: la fila distingue «acotada por MI recorte» de «incompleta del backend» -generica, por `total` vs la ventana que /doctor impuso- y lee el cuarto veredicto `no_verificable`), `evals/fixtures/knowledge-services/backend_test.py` (fix4, gaps #148/#152: el adaptador de fixture sabe devolver `total` y `no_verificable`), `commands/doctor.md` + `interop/**` (fix4, gap #148: las dos filas -ℹ️ acotada vs ⚠️ incompleta- y la ℹ️ de `no_verificable`; regenerado)
- **Verificacion**: `python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k graphiti` -> off/shadow/read/degradado con veredicto y remedio; `doctor.py` no contiene la cadena `graphiti`. Salida real (2026-09-21):
  ```
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k graphiti
  ............                                                             [100%]
  12 passed, 145 deselected in 0.52s

  # re-ejecutada tras `fix1` (2026-09-21), ampliada a los tests de la ronda:
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k "graphiti or f3fix1"
  21 passed, 145 deselected in 1.24s

  $ grep -c graphiti agent-kits/shared/doctor.py
  0

  $ python agent-kits/shared/capabilities.py --root .
  knowledge-gate: enabled=True health=ok — knowledge-gate: taxonomy.json valido ((plantilla por defecto))
  kwipu: enabled=False health=deshabilitado — kwipu: deshabilitado (backends.kwipu.enabled: false o sin declarar)
  graphiti: enabled=False health=deshabilitado — graphiti: deshabilitado (sin backend `type: graphiti` habilitado en taxonomy.json)

  $ python scripts/export-interop.py && python scripts/export-interop.py --check
  export-interop: 50 ficheros escritos (codex + opencode)
  export-interop --check: 50 ficheros al día
  ```
  - RED (TDD, 2026-09-21): `python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k graphiti` -> `11 failed, 1 passed` con `AssertionError: assert 'graphiti' in {'knowledge-gate', 'kwipu'}` (el registro no la declaraba). La parte de `commands/setup.md`, `commands/doctor.md` y los dos `INTEROP.md` es **TDD n/a: prosa** (el unico automatismo que la cubre es `export-interop --check`, ejecutado arriba).
  - **Decision del implementer:** `capabilities.py` NO hace red al enumerar (test `test_graphiti_no_hace_red_al_enumerar`, con `socket` monkepatcheado). El estado publicado sale de la CONFIGURACION (`mode`, preguntado al `_modo` del propio adaptador, que es la fuente unica del enum y del default) y la comprobacion EN VIVO la sigue haciendo `/doctor` por su cuenta con su presupuesto de tiempo, via `health()`/`verify()` del adaptador — exactamente el patron de `kwipu`, y evita pagar dos veces la misma red en cada `/doctor`.
  - **Precision sobre `group_id`:** un backend habilitado sin `group_id` NO puede darse: el esquema lo DERIVA del slug del proyecto (T-01-fix2). Lo que si sale como `degradado` (con el campo nombrado) es cualquier otro error de validacion del backend -p. ej. `provider.llm` ausente-, en vez del enganoso «deshabilitado» que daria leer solo `enabled`.
  Re-ejecutada tras `fix3` (2026-09-22):
  ```
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_doctor.py agent-kits/shared/test_capabilities.py
  178 passed, 1 failed in 74.27s
  ```
  (el unico rojo es `test_hook_sin_bit_ejecutable_es_aviso_con_chmod`, preexistente y SOLO en Windows: el bit de ejecucion no existe en NTFS.)
  ```
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k f3fix3
  5 passed, 174 deselected in 0.72s

  $ grep -c graphiti agent-kits/shared/doctor.py
  0

  $ python scripts/export-interop.py --check
  export-interop --check: 50 ficheros al dia
  ```
  Re-ejecutada tras `fix4` (2026-09-22):
  ```
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_doctor.py agent-kits/shared/test_capabilities.py
  1 failed, 183 passed in 57.85s

  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k f3fix4
  5 passed, 179 deselected in 1.78s

  $ grep -c graphiti agent-kits/shared/doctor.py
  0

  $ python scripts/export-interop.py && python scripts/export-interop.py --check
  export-interop: 50 ficheros escritos (codex + opencode)
  export-interop --check: 50 ficheros al día
  ```
  (el unico rojo sigue siendo `test_hook_sin_bit_ejecutable_es_aviso_con_chmod`, preexistente y SOLO en Windows.)
  **Escenario del gap #148** (`/doctor` con el adaptador REAL contra el servidor MCP falso, 250 entradas publicadas), reproducible:
  ```
  $ python -m pytest -q -p no:cacheprovider agent-kits/shared/test_doctor.py -k f3fix4_gap148
  4 passed, 141 deselected in 1.65s

  # y la fila tal y como sale, con 250 entradas sanas y con una borrada del grafo:
  [250 entradas SANAS] ℹ️ kb (backend): verificación acotada a 200 de 250 entrada(s) por /doctor (diagnóstico rápido): 50 sin confirmar; un desfase fuera de esa ventana no se ve desde aquí
           arreglo: verificación completa: `python skills/knowledge-services/scripts/knowledge-sync.py --backend <id> --check`
  [250 con mem.pattern.x000 borrada del grafo] ℹ️ kb (backend): verificación acotada a 200 de 250 entrada(s) por /doctor (diagnóstico rápido): 50 sin confirmar; un desfase fuera de esa ventana no se ve desde aquí
           arreglo: verificación completa: `python skills/knowledge-services/scripts/knowledge-sync.py --backend <id> --check`
  ```
  - **Decision del implementer (arbitraje de #148, con margen declarado):** con la ventana recortada a 200, un desfase REAL fuera de esa ventana es INDISTINGUIBLE de lo sano (`get_episodes` no tiene cursor y devuelve «los mas recientes», asi que el adaptador no puede afirmar nada de lo que no vio). En vez de inventar un ⚠️ que no se sabe justificar ni un OK que promete lo que no ha mirado, la fila es ℹ️ y lo DICE: «un desfase fuera de esa ventana no se ve desde aqui», con el comando de la verificacion COMPLETA (`knowledge-sync.py --backend <id> --check`, que no recorta). El ⚠️ queda para lo que SI es del backend: `desfase`, o `incompleto` cuando el manifiesto cabia en la ventana que /doctor le paso (test dedicado que lo fija).
**Criterios de aceptación**
- [x] Config no registra MCP ni toca configuracion global — el `setup_step` de la capacidad declara `backends.<id>` en `taxonomy.json` del PROYECTO y nada mas; `test_graphiti_setup_step_no_registra_mcp_ni_toca_config_global` prohibe que el paso mencione `claude mcp add`/`~/.claude.json`/`settings.json`, y la seccion nueva de `commands/doctor.md` y el paso de `commands/setup.md` lo dicen en llano. El adaptador habla HTTP con el `endpoint` LOCAL declarado, sin pasar por el cliente MCP del runtime (fila nueva de la tabla de degradacion en `docs/INTEROP.md` y `docs/en/INTEROP.md`).
- [x] La capacidad entra por `capabilities.py`, **sin codigo especifico de la capacidad en `doctor.py`** (CA-14 de knowledge-services; criterio reescrito en fix2 por el gap #128: el texto anterior decia «sin editar `doctor.py`» y las rondas fix1/fix2 SI lo editaron -53 y ~60 lineas, todas GENERICAS: bucle por backend declarado, presupuesto de red y saneado de etiquetas-, lo que CA-14 prohibe es el codigo por capacidad). Comprobacion mecanica: `grep -c graphiti agent-kits/shared/doctor.py` -> 0 — entrada nueva en `REGISTRO` con las seis claves del contrato y los cinco estados (`deshabilitado`/`off`/`shadow`/`read`/`degradado`), cada uno con detalle y remedio; `grep -c graphiti agent-kits/shared/doctor.py` -> 0, fijado ademas por `test_doctor_no_nombra_la_capacidad_graphiti`, y `test_doctor_pinta_una_capacidad_nueva_sin_tocar_doctor_py` demuestra que el registro basta para que salga pintada.
- **Changelog**: Projects can now turn on the optional Graphiti graph memory from `/setup` and see its state in `/doctor` (off, shadow, read or misconfigured, each with the fix); enabling it only edits the project's own knowledge configuration and never registers an MCP server or touches global settings.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.22h (medido; usage-meter, artefacto `graphiti-memory/T-08`, 5.16 EUR)
- **Tiempo IA (fix1)**: real - (medido junto con T-07-fix1 — ver nota en T-07)
- **Tiempo IA (fix2)**: real - (medido junto con T-07-fix2 — ver nota en T-07)
- **Tiempo IA (fix3)**: real - (medido junto con T-07-fix3 — ver nota en T-07)
- **Tiempo IA (fix4)**: real - (medido junto con T-07-fix4 — ver nota en T-07)
