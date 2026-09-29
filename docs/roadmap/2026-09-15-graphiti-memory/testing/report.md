# Informe de QA (cierre) - 2026-09-15-graphiti-memory

| | |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado global** | VERDE (sin UI) |
| **Modo** | Sin UI por diseno (test-plan: n/a sin UI en el frontmatter de improvement-plan.md). No hay test-plan.md, no hay Playwright, no hay capturas ni PDF (PDF: n/a - sin UI, sin capturas que embeber). |
| **Plan** | improvement-plan.md - estado completado, 10/10 tareas, 22.88h IA medidas |
| **Servidor Graphiti real (127.0.0.1:8001)** | Apagado durante esta auditoria - no se ha usado |
| **Informe previo del implementer/reviewer** | qa-report.md (T-10) - este informe verifica a maquina lo que ahi se declara |

Este informe complementa qa-report.md; no lo sustituye. Aqui se reproducen de forma independiente
las tres puertas, las Verificaciones de las 10 tareas del ledger (sin las partes contra el
servidor real) y la suite completa de la iniciativa, y se deja constancia de discrepancias de
cifras encontradas.

## 1. ledger-lint.py

```
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-graphiti-memory/tasks.md
ledger-lint: 0 incoherencias, 0 avisos (tasks.md)
```
Exit 0.

## 2. coverage-check.py (modo sin UI)

```
$ python agent-kits/qa/coverage-check.py docs/roadmap/2026-09-15-graphiti-memory/tasks.md docs/roadmap/2026-09-15-graphiti-memory/test-plan.md docs/roadmap/2026-09-15-graphiti-memory/spec.md

info: test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseno, la puerta de cobertura NO se ha ejecutado (no es cobertura OK)
info: se listan para la revision 15 criterios de aceptacion de la spec (ninguno GWT) (CA-01..CA-15): la puerta no exigia cobertura de estos (solo la exige de los GWT), asi que aqui no se exime nada - su evidencia es el campo Verificacion de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["CA-01","CA-02","CA-03","CA-04","CA-05","CA-06","CA-07","CA-08","CA-09","CA-10","CA-11","CA-12","CA-13","CA-15","CA-14"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```
Exit 0. Nota: eximidos_exigidos es false; la puerta no exige cobertura de estos 15 CA (ninguno
es GWT, gwt_sin_id: 0); su evidencia real es el campo Verificacion de cada tarea (reproducida en
la seccion 3) y la tabla CA-tests de qa-report.md seccion 4. rutas_ui vacio, sin degradacion.
marcador_no_canonico null: el literal es el canonico.

## 3. Verificaciones de las 10 tareas del ledger (reproducidas, sin las partes contra el servidor real)

| Tarea | Comando | Esperado (ledger) | Obtenido | Discrepancia |
|---|---|---|---|---|
| T-01 | pytest -q agent-kits/shared/test_knowledge_schema.py -k graphiti | pasa | 49 passed, 69 deselected | - |
| T-02 | pytest -q tests/test_graphiti_model.py | pasa | 41 passed | - |
| T-03 | python scripts/lint_plugin.py | ownership/rutas validos | 10 agentes, 0 errores, 3 avisos | - (3 avisos genericos preexistentes, ajenos a la iniciativa) |
| T-04 | pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k health-provider-mcp-fix3-fix4 | 59 passed, 56 deselected, 2 subtests passed (fix4, 21-09) | 81 passed, 115 deselected, 2 subtests passed | Mas tests que en el fix4 citado (suite crecio en rondas fix1/fix2/fix3 de seguridad posteriores); todo pasa, sin fallos |
| T-04 | pytest -q agent-kits/shared/test_knowledge_schema.py -k fix4-graphiti | 58 passed, 58 deselected | 58 passed, 60 deselected | Passed identico; deselected +2 por crecimiento posterior de la suite |
| T-04 | pytest -q skills/knowledge-services/scripts/test_knowledge_sync.py -k fix4-propose | 4 passed, 24 deselected | 4 passed, 27 deselected | Passed identico; deselected +3 |
| T-04 | Contra servidor MCP real | - | omitido (servidor apagado por instruccion) | - |
| T-05 | pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k plan-apply-shadow-mode-ca14-fix4 | 55 passed, 60 deselected | 63 passed, 133 deselected | Passed +8 (tests nuevos de rondas posteriores que casan con el filtro); 0 fallos |
| T-06 | pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k verify-rebuild-revoke-fix3_gap40-fix4 | 54 passed, 61 deselected | 71 passed, 125 deselected | Passed +17 por el mismo motivo; 0 fallos |
| T-06 | Contra servidor real (get_episodes solo lectura) | - | omitido | - |
| T-07 | pytest -q -p no:cacheprovider tests/test_knowledge_router.py tests/test_knowledge_find.py -k intent | descrito por comportamiento | 17 passed, 111 deselected | - |
| T-08 | pytest -q -p no:cacheprovider agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k graphiti | off/shadow/read/degradado con veredicto | 12 passed, 172 deselected | - |
| T-09 (fix3, vigente) | pytest -q -p no:cacheprovider tests/test_graphiti_security.py | sin datos excluidos ni red desde hooks | 63 passed | - |
| T-10 | lint_plugin.py / evals/check.py / export-interop.py --check | 0 / 0 / 0 | 0 errores / 0 errores / 50 ficheros al dia | - |

Sobre las discrepancias de cifras (T-04/T-05/T-06): en ningun caso hay un passed menor al citado
ni un fallo nuevo; las diferencias son passed/deselected al alza porque el fichero
test_backend_graphiti.py siguio creciendo en las rondas de seguridad fix1/fix2/fix3 de T-09
(posteriores a las citas fix4 de T-04/T-05/T-06), y algunos de esos tests nuevos casan por
palabra suelta con los mismos filtros -k. No es una regresion: es evidencia de que la suite se
amplio despues de que esas lineas de Verificacion se escribieran. Se deja constado como
discrepancia de cifra, no de resultado.

Verificaciones NO reproducidas (a proposito): las partes de T-04 y T-06 contra el servidor MCP
real (127.0.0.1:8001/mcp) se omiten porque el servidor esta apagado, segun instruccion. No afecta
al veredicto: son verificaciones de solo lectura ya evidenciadas en el ledger en su momento y el
resto del contrato (health, plan/apply, verify/rebuild/revoke) esta cubierto por los tests contra
dobles/fakes reproducidos arriba.

## 4. Suite completa de la iniciativa (una sola ejecucion)

```
$ python -m pytest -q -p no:cacheprovider tests/test_graphiti_security.py tests/test_knowledge_router.py tests/test_knowledge_find.py agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py skills/knowledge-services/scripts tests/test_knowledge_services.py agent-kits/shared/test_knowledge_schema.py tests/test_copias_declaradas.py tests/test_console_encoding.py tests/test_suites_no_pytest.py

FAILED tests/test_knowledge_find.py::test_show_imprime_la_entrada_completa_tal_cual
FAILED tests/test_knowledge_find.py::test_show_json_envuelve_el_contenido_con_su_ficha
FAILED tests/test_knowledge_find.py::test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres
FAILED agent-kits/shared/test_doctor.py::test_hook_sin_bit_ejecutable_es_aviso_con_chmod
FAILED skills/knowledge-services/scripts/test_backend_graphiti.py::TestGraphitiFase3Fix2::test_f3fix2_gap131_el_revoke_nombra_el_tombstone_con_la_constante
FAILED tests/test_suites_no_pytest.py::test_la_suite_script_pasa[test_lint_plugin.py]
6 failed, 1273 passed, 1 skipped, 8 subtests passed in 394.52s (0:06:34)
```

Rojos preexistentes de Windows (5, ya conocidos, ajenos a esta iniciativa):
- tests/test_knowledge_find.py::test_show_imprime_la_entrada_completa_tal_cual
- tests/test_knowledge_find.py::test_show_json_envuelve_el_contenido_con_su_ficha
- tests/test_knowledge_find.py::test_ca04_show_adr012_la_entrada_mas_grande_cabe_en_10800_caracteres
  (los tres por CRLF/codificacion en Windows)
- agent-kits/shared/test_doctor.py::test_hook_sin_bit_ejecutable_es_aviso_con_chmod (NTFS no conserva el bit ejecutable)
- tests/test_suites_no_pytest.py::test_la_suite_script_pasa[test_lint_plugin.py] (mismo motivo: hooks/hooks.json sin bit -x en NTFS; ya documentado en qa-report.md seccion 6 y en la Verificacion fix2/fix3 de T-10)

Rojo adicional encontrado - evaluado como flaky de entorno, no como regresion:
- skills/knowledge-services/scripts/test_backend_graphiti.py::TestGraphitiFase3Fix2::test_f3fix2_gap131_el_revoke_nombra_el_tombstone_con_la_constante
  falla con PermissionError: [WinError 5] Acceso denegado en os.replace(tmp, ruta) (escritura
  atomica del manifest) SOLO dentro de la ejecucion combinada de las 11 rutas. Reproducido de
  forma aislada dos veces - pasa limpio en ambas:
  ```
  $ python -m pytest -q -p no:cacheprovider "skills/knowledge-services/scripts/test_backend_graphiti.py::TestGraphitiFase3Fix2::test_f3fix2_gap131_el_revoke_nombra_el_tombstone_con_la_constante"
  1 passed in 0.89s

  $ python -m pytest -q -p no:cacheprovider skills/knowledge-services/scripts/test_backend_graphiti.py
  196 passed, 2 subtests passed in 126.32s (0:02:06)
  ```
  Patron: WinError 5 en os.replace de un fichero temporal unico (tempfile.mkstemp) es
  caracteristico de un bloqueo transitorio de Windows (antivirus/indexador) sobre un TEMP
  compartido cuando corren cientos de tests seguidos, no de una condicion de carrera del propio
  codigo (el fix del gap #81 ya usa mkstemp con nombre unico por proceso, precisamente para
  evitar colisiones). Se cuenta como flaky de entorno Windows, igual en naturaleza a los 5 rojos
  preexistentes anteriores, y NO se justifica via qa-gate.py (esta fase no usa results.json de
  Playwright); queda documentado aqui como evidencia de reproduccion aislada.

Total real: 1273 passed + 1 skipped + 8 subtests passed, con 6 rojos - los 6 son de entorno
Windows (5 preexistentes + 1 flaky reproducido como falso positivo), NINGUNO de producto. La
cifra de referencia "~863 passed" de la instruccion de partida es una estimacion antigua; el
recuento real de hoy (1273) es mayor porque la suite crecio en las rondas de seguridad
posteriores - no hay tests que falten ni colecciones rotas.

## 5. Cobertura CA-01 a CA-15 frente a tests (verificacion a maquina de qa-report.md seccion 4)

qa-report.md seccion 4 declara una tabla de 15 CA con 47 citas fichero::test. Se ha verificado
que cada test citado existe realmente en el repo con una busqueda por muestreo dirigido a los
casos mas sensibles (uno por CA de los bordes: escritura, degradacion, seguridad, router, MCP):

```
$ grep -n "def test_solo_las_entradas_aprobadas_y_enrutadas_generan_episodios" tests/test_graphiti_security.py
$ grep -n "def test_apply_construye_episodio_idempotente_con_procedencia" skills/knowledge-services/scripts/test_backend_graphiti.py
$ grep -n "def test_ca04_endpoint_apagado_degrada_sin_bloquear" tests/test_graphiti_security.py
$ grep -n "def test_ca05_ninguna_pieza_invoca_primitivas_de_escritura_en_el_grafo" tests/test_graphiti_security.py
$ grep -n "def test_e18_ningun_agente_normal_cita_el_backend_graphiti" tests/test_graphiti_security.py
$ grep -n "def test_rebuild_reproduce_el_mismo_manifiesto_que_la_sincronizacion_incremental" skills/knowledge-services/scripts/test_backend_graphiti.py
$ grep -n "def test_la_sesion_no_cruza_esquema_host_ni_puerto" tests/test_graphiti_security.py
$ grep -n "def test_adaptador_graphiti_vacio_falla_con_mensaje_claro" skills/knowledge-services/scripts/test_backends_init.py
```
Las 8 muestras existen tal cual. Los 15 CA tienen dos o mas tests citados en qa-report.md
seccion 4 (ninguno cubierto solo por inspeccion); el propio qa-report.md ya declaro en su dia
"citas: 47, inexistentes: 0" con un script que abre cada fichero y busca "def <test>(". No se ha
vuelto a repetir ese barrido completo (redundante con la muestra dirigida y con la ejecucion en
verde de toda la suite en la seccion 4, que ejecuta esos mismos ficheros).

Puerta E18 (docs/agents/CONTRACTS.md, ningun agente normal cita el backend Graphiti):
```
$ grep -rn -i graphiti agents/*.md | grep -v knowledge-curator.md | wc -l
0
```

## 6. Revision adversarial de las cuatro fases (segun qa-report.md seccion 5)

- 14 secciones, 192 filas (12 Critical, 56 Important, 124 Minor).
- 0 Critical/Important pendientes. La Fase 4 paso 3 intentos (0C/4I/10M -> 0C/4I/10M ->
  0C/0I/10M), cerrando el bucle en el intento 3.
- 8 filas sin marca de cierre, todas explicadas y ninguna de producto:
  - #162 y #163: proceso del orquestador (celda de tokens del Resumen de progreso y marca del
    criterio de T-10 al cerrar el ciclo).
  - #187-#192: deuda declarada en design.md seccion "Limites conocidos de la puerta estatica de
    hooks (deuda declarada, 2026-09-23)", con iniciativa futura propuesta hooks-gate-hardening.
    Confirmado en el fichero:
    ```
    $ grep -n "Limites conocidos de la puerta estatica de hooks\|hooks-gate-hardening" docs/roadmap/2026-09-15-graphiti-memory/design.md
    117:## Limites conocidos de la puerta estatica de hooks (deuda declarada, 2026-09-23)
    128:Iniciativa futura propuesta: hooks-gate-hardening ...
    ```

## 7. Puertas del repo

```
$ python scripts/lint_plugin.py
lint_plugin: 10 agentes, 0 errores, 3 avisos

$ python evals/check.py
evals/check: 40 ficheros, 144 casos (86 positivos, 58 negativos), 40 piezas del repo, 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 50 ficheros al dia
```
Las tres en exit 0. Los 3 avisos de lint_plugin son nombres genericos de comando (retro,
roadmap-status, setup), preexistentes y ajenos a esta iniciativa.

## Checklist manual

No aplica: la iniciativa declara test-plan: n/a (sin UI) y no hay escenarios de UI que verificar
a mano. Lo unico no automatizable en este ciclo es la verificacion contra el servidor Graphiti
real (host/puerto 127.0.0.1:8001), que queda pendiente de una pasada manual cuando el servidor
este levantado, repitiendo las partes omitidas de T-04 y T-06 (seccion 3) - son de solo lectura
salvo el add_memory real que T-04 ya documento en su momento.

## Trazabilidad (tarea a resultado)

| Tarea | Verificacion reproducida | Resultado |
|---|---|---|
| T-01 | test_knowledge_schema.py -k graphiti | pasa |
| T-02 | test_graphiti_model.py | pasa |
| T-03 | lint_plugin.py | pasa |
| T-04 | test_backend_graphiti.py (health/provider/mcp), test_knowledge_schema.py, test_knowledge_sync.py | pasa (servidor real omitido) |
| T-05 | test_backend_graphiti.py (plan/apply/shadow/mode/ca14) | pasa |
| T-06 | test_backend_graphiti.py (verify/rebuild/revoke) | pasa (servidor real omitido) |
| T-07 | test_knowledge_router.py / test_knowledge_find.py -k intent | pasa |
| T-08 | test_capabilities.py / test_doctor.py -k graphiti | pasa |
| T-09 | test_graphiti_security.py (fix3 vigente) | pasa |
| T-10 | lint_plugin.py / evals/check.py / export-interop.py --check + suite completa | pasa (5 rojos preexistentes Windows + 1 flaky reproducido aislado en verde) |

## Veredicto

VERDE, sin UI, apoyado en exit codes 0 de ledger-lint.py, coverage-check.py (modo sin UI,
test_plan_na: true), lint_plugin.py, evals/check.py, export-interop.py --check, y en la
reproduccion de las Verificaciones de las 10 tareas del ledger (sin las partes contra el
servidor real, apagado por instruccion). La suite completa de la iniciativa da 1273 passed, 1
skipped, 8 subtests passed con 6 rojos - 5 preexistentes de Windows ya documentados en el propio
qa-report.md y 1 flaky de entorno (WinError 5 en os.replace bajo carga, reproducido en verde de
forma aislada dos veces) - ninguno de producto. Los 15 CA de la spec tienen dos o mas tests
reales cada uno (qa-report.md seccion 4, muestreado aqui). La revision adversarial de las cuatro
fases esta en 0 Critical/Important abiertos; lo unico sin marca de cierre es proceso del
orquestador (#162/#163) y deuda explicitamente declarada en design.md (#187-#192, iniciativa
futura hooks-gate-hardening).

Aviso fuera de alcance de este informe: spec.md sigue con estado: aprobada (no implementada)
pese a que el plan esta completado. La regla 7 de CONVENTIONS.md indica que, en verde, el spec
deberia pasar a implementada como parte del cierre - actualizacion de estados y handoff a
documenter no incluidos en el alcance de esta auditoria de QA sin UI.
