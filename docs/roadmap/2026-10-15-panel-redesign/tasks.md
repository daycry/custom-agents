---
generacion:               # usage-meter.py close · ventana compartida con improvement-plan.md
  inicio: 2026-10-15T09:41:41Z
  fin: 2026-10-15T10:03:37Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-0d642e69c69348c2b05ab888c500c6dc
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 84, salida: 114551, cache_creacion: 425511, cache_lectura: 6785286 }
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  eur: 8.20
  horas_ia: 1.02
  duracion: 1h 1m           # duracion_reloj: 22m
  ratio_usado: 531798.5     # CALIBRATION.md (mediana de 6)
  avisos: ["CALIBRATION: 7 filas marcadas (estimado) fuera de la mediana", "tarifa verificada el 2026-08-18", "2 transcripts leídos (1 de subagente)"]
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — Rediseño del panel local: multi-página, kanban y gráficos

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-10-15 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | [`design.md`](./design.md) — opción O1+O5 (D-A1 = O1, D-A2 = O5) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Orden de ejecución: Fase 1 → Fase 2 → Fase 4 → Fase 3** (lo pide la evaluación). Las secciones van en ese orden y los IDs `T-XX` son correlativos en el orden de ejecución. La Fase 3 conserva su número de la spec y es la última; lleva también el cierre transversal (C-05). Ninguna tarea de una fase arranca antes de que la anterior cierre con su revisión de dos lentes y la revisión visual del usuario (CA-44).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Base común | 16 | 16 | 100% | 0 / 28,8h | 3,99 / 10,5h | 0,24 / 3,6h | 0,70 / 5,58 M |
| Fase 2 — Inicio, Iniciativas y Plan | 17 | 17 | 100% | 0 / 58,4h | 4,22 / 19,1h | 0 / 6,25h | 0 / 10,16 M |
| Fase 4 — Memoria, Catálogo y Diagnóstico | 10 | 10 | 100% | 0 / 26,4h | 0 / 7,2h | 0 / 2,8h | 0 / 3,83 M |
| Fase 3 — Agentes en vivo + cierre transversal | 14 | 15 | 93% | 0 / 45,6h | 3,57 / 23,4h | 0 / 6,9h | 0 / 12,44 M |
| **TOTAL** | **57** | **58** | **98%** | **0 / 159,2h** | **11,78 / 60,2h** | **0,24 / 19,6h** | **0,70 / 32,01 M** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.

> **Revisión como línea propia (LES-009).** Las horas IA de «revisión + corrección» de cada fase (factor `f` de la evaluación) van en la tarea de cierre de la fase (T-16, T-29, T-39, T-54), no repartidas: es la partida que más se desvía y así `/retro` mide el `f` real por fase.

---

## Fase 1 — Base común

**Estado**: completado (2026-10-15) · **Estimado**: 28,8h humanas · 10,5h IA · **Real**: 3,99h IA medida (T-05..T-08 sin medir) · **Coste est.**: 1.513 € referencia · ≈ 255 € ejecución · **Tokens est.**: 5,58 M

Criterios de la spec: CA-32 a CA-41 y CA-43 (+ la parte base de CA-42 y la primera revisión de CA-44). Aplica D-A1 = O1.

### T-01 — Golden files de los contratos que no deben cambiar

- **Descripción**: Antes de refactorizar nada, fija las salidas actuales sobre fixtures propias: `build_dashboard.py --json`, `build_dashboard.py --md` (`dashboard.md`) y `build_panel.py --json` sobre un bundle de fixture. Son la red de no regresión de CA-28 y de «No regresión» de la spec.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,18h (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real 0,05h (estimado, 25 % de la IA)
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: ninguna
- **Tipo**: test
- **Archivos**: `tests/fixtures/panel-redesign/**`, `tests/test_panel_contract_golden.py`, `.gitattributes` (añadido: ver Notas)
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_panel_contract_golden.py` → `3 passed` (o más) en el código ACTUAL, antes de tocar ningún generador

**Criterios de aceptación**
- [x] Tres goldens versionados: `dashboard.json`, `dashboard.md` y `panel.json`, generados sobre `tests/fixtures/panel-redesign/roadmap/` y `tests/fixtures/panel-redesign/bundle/`, nunca sobre el repo real.
- [x] El test compara byte a byte; si un campo es volátil (fecha de generación, rutas temporales), se normaliza con una lista explícita y documentada en el test, no se excluye el fichero.
- [x] La fixture de roadmap cubre los casos que la spec exige después: estados de spec variados, iniciativa ilegible, ledger > 256 KiB, sin `generacion:`, sin `real`, `—` en horas, gaps de revisión abiertos, `execution-history.md`.
- [x] Las fixtures no contienen rutas del home, usuarios ni correos reales (CA-41).

**Subtareas**
- [x] Crear la fixture de roadmap (5-7 iniciativas mínimas) y la de bundle.
- [x] Generar los goldens con el código actual y versionarlos.
- [x] Test de comparación byte a byte con normalización declarada.

- **Changelog**: Las salidas JSON y Markdown del dashboard y el JSON del catálogo del panel quedan fijadas con goldens: el rediseño del panel no puede cambiarlas sin que falle un test.
- **Evidencia TDD**: `RED: test_dashboard_json_igual_a_su_golden, test_dashboard_md_igual_a_su_golden y test_panel_json_igual_a_su_golden fallaron con AssertionError: golden ausente: tests/fixtures/panel-redesign/golden/<nombre> · 2026-10-15` (3 failed, 2 passed). GREEN: goldens generados con `PANEL_GOLDEN_UPDATE=1` sobre el código ACTUAL (sin tocar ningún generador: `git status` limpio en `skills/` y `agent-kits/`), y 3 ejecuciones seguidas en verde.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_contract_golden.py` → `5 passed in 0.92s`. Tokens reales de la tarea ≈ 0,10 M (derivados de las horas-IA medidas × ratio 531.798; el JSON de `close` no se conservó). Independencia de la ubicación: la fixture copiada a otra carpeta absoluta produce los mismos bytes normalizados en `panel.json` y `dashboard.json` (`True True`).

**Notas**: patrón de fixture de bundle en `tests/test_plugin_panel.py:69-70` (`bundle(tmp_path)`); patrón de roadmap sintético y subprocess de `--json` en `tests/test_dashboard.py:269` (`_roadmap_procedencia`). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `9a8624fc49e8`.

### T-02 — Chart.js 4.5.1 incluido con procedencia, licencia y hash

- **Descripción**: Incluye `chart.umd.min.js` 4.5.1 sin modificar en `skills/plugin-panel/assets/vendor/chart.js/`, extraído una sola vez del tarball de npm verificando su `sha512`, con `LICENSE.md` (MIT) y `PROVENANCE.json`. Un test falla si el SHA-256 del fichero no coincide (CA-36).
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,54h (medido; la ventana incluye la suite `installer.test.mjs`, 7 min)
- **Supervisión**: est. 0,05h (≈25 % IA) · real 0,14h (estimado, 25 % de la IA)
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: ninguna
- **Tipo**: devops
- **Archivos**: `skills/plugin-panel/assets/vendor/chart.js/chart.umd.min.js`, `skills/plugin-panel/assets/vendor/chart.js/LICENSE.md`, `skills/plugin-panel/assets/vendor/chart.js/PROVENANCE.json`, `tests/test_panel_vendor.py`, `.gitignore`, `.gitattributes` (añadidos: ver Notas)
- **Cubre (tests)**: E2E-02
- **Verificación**: `python3 -m pytest -q tests/test_panel_vendor.py` → `passed`, con SHA-256 `48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a` y 208.522 bytes

**Criterios de aceptación**
- [x] Un único fichero de Chart.js en todo el árbol del plugin (el test lo busca por nombre y por contenido de cabecera).
- [x] `PROVENANCE.json` declara versión, URL del tarball, `sha512` npm, `sha256` del fichero, tamaño, licencia y fecha de extracción.
- [x] El test recalcula el SHA-256 y falla si no coincide con `PROVENANCE.json`.
- [x] Ningún script del plugin descarga nada en ejecución ni al generar: la extracción es un paso de desarrollo único y queda anotado en `Notas`.

**Subtareas**
- [x] Descargar el tarball de npm (paso de desarrollo, una vez), verificar `sha512`, extraer `dist/chart.umd.min.js`.
- [x] Escribir `LICENSE.md` y `PROVENANCE.json`.
- [x] Test de hash y de unicidad.
- [x] Comprobar que `scripts/lint_plugin.py`, `tests/test_skill_size.py`, `scripts/export-interop.py` e `install/` toleran el activo de ~210 KB (riesgo de la evaluación C-01).

- **Changelog**: El panel incluye Chart.js 4.5.1 sin modificar, con su licencia MIT y un fichero de procedencia; un test comprueba su huella y que no hay otra copia.
- **Evidencia TDD**: `RED: los 6 tests de tests/test_panel_vendor.py fallaron (falta chart.umd.min.js; FileNotFoundError de PROVENANCE.json y LICENSE.md; unicidad [] ≠ [vendor]; .gitignore ignora el fichero por **/vendor/; serve_panel.py cita http://) · 2026-10-15`. El último rojo destapó un falso positivo del propio test (el servidor cita su origen de loopback `http://127.0.0.1:<puerto>`): el patrón excluye `127.0.0.1` y `localhost`. Mutación comprobada: una copia de `chart.umd.min.js` en `skills/plugin-panel/references/` hace fallar la unicidad.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_vendor.py` → `6 passed`. Fichero: 208.522 bytes, SHA-256 `48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a` (= `design.md` I-01). Tokens reales 0,29 M facturables (`usage-meter close`: entrada 54, salida 15.347, creación de caché 272.366).

**Notas**: valores de `design.md` §2.4 I-01. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `0c292bdcf815`.

### T-03 — Spike de CSP con Chart.js en servido y en `file://` (Playwright, Chromium y Firefox)

- **Descripción**: Primer día de F1: una página mínima con un gráfico Chart.js se abre en modo servido (CSP con nonce) y en `file://` (CSP `default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:`) con la red bloqueada, en Chromium y Firefox. Decide entre `file:` y el respaldo con Chart.js incrustado y `'sha256-…'` antes de seguir.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,07h (medido; corto: ver Notas)
- **Supervisión**: est. 0,1h (≈25 % IA) · real 0,02h (estimado, 25 % de la IA)
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-02
- **Tipo**: test
- **Archivos**: `tests/e2e/panel-csp-spike.mjs`
- **Cubre (tests)**: E2E-02, E2E-04
- **Verificación**: `node tests/e2e/panel-csp-spike.mjs --engines chromium,firefox` → `securitypolicyviolation: 0` y `peticiones a otros orígenes: 0` en los 4 casos (2 motores × 2 modos), o la salida que justifica el respaldo hash, pegada en este ledger

**Criterios de aceptación**
- [x] Los 4 casos (Chromium/Firefox × servido/`file://`) se ejecutan con la red bloqueada y la salida se pega en `Notas` de esta tarea.
- [x] Decisión anotada: `file:` vale en ambos motores, o se adopta el respaldo determinista (Chart.js incrustado + `script-src 'sha256-…'`, el fichero sigue en `vendor/` con su `LICENSE`).
- [x] Sin `unsafe-eval` ni `unsafe-inline` en `script-src` en ningún caso.
- [x] Si Playwright no está instalado, el script sale con aviso y código 2 (no inventa un verde); la instalación requiere permiso del usuario.

**Subtareas**
- [x] Pedir permiso para instalar Playwright y los navegadores (mismo opt-in que `qa`, runner en `agent-kits/qa/runner/`).
- [x] Script con `page.on('console')`, `securitypolicyviolation` y `route('**', abort)` para todo origen ajeno.
- [x] Ejecutar, pegar la salida y anotar la decisión.

- **Changelog**: Comprobado en Chromium y Firefox que el panel con gráficos funciona sin red y con una política de seguridad de contenido estricta, tanto servido como abierto desde una carpeta.
- **Evidencia TDD**: `TDD n/a: pico de exploración (script de evidencia, no código de producto)`. Rojo real que cambió la decisión: la primera ejecución dio `Casos: 4 · fallidos: 1` — `[firefox · servido] securitypolicyviolation: 1 … directivas: img-src ← <origen>/…/favicon.ico → FALLA` (Firefox pide `/favicon.ico` por su cuenta y `default-src 'none'` lo bloquea).
- **Decisión (2026-10-15):** **`file:` vale en los dos motores; NO se adopta el respaldo con `'sha256-…'`** (probado igualmente: también pasa y queda como plan B documentado). Políticas que salen del pico:
  - Exportado (`<meta>`), **igual que `design.md`**: `default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:`.
  - Servido (cabecera), **cambia respecto a `design.md` y a `serve_panel.py`**: `default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'nonce-N'; img-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.
  - Toda página (los dos modos) declara `<link rel="icon" href="data:,">`.
- **Qué cambia de `design.md` (§2.4 I-01, «Modo servido»)** — afecta a T-05 (plantilla) y T-11 (servidor): (1) `style-src` del servido necesita `'self'`: con la cabecera actual (`style-src 'unsafe-inline'`) el `assets/panel.css` enlazado que prevé §5.2 se bloquea en los dos motores (`style-src-elem ← <origen>/…/spike.css`); (2) el servido necesita `img-src data:` y cada página el icono `data:,`: sin ellos Firefox registra una violación `img-src` por `/favicon.ico` (y Chromium otra `img-src` con la cabecera actual). `design.md` dice que la CSP servida «queda `script-src 'nonce-N'`»: sigue siendo cierto para `script-src`, pero no basta. El implementer no edita `design.md` (guardarraíl de `docs/roadmap/`): queda aquí para que lo recoja el orquestador.
- **Verificación ejecutada** (2026-10-15): `PLAYWRIGHT_DIR=<scratchpad>/pw node tests/e2e/panel-csp-spike.mjs --engines chromium,firefox --fallback` → exit 0:
  ```
  Playwright: cargado de --playwright-dir
  Política exportada: default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:
  Política servida:   default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'nonce-<nonce>'; img-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'
  [chromium] 155.0.4283.45 (channel msedge)
  [chromium · servido] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18387 píxeles) · fetch mismo origen: 200 → OK
  [chromium · servido · control inline] securitypolicyviolation: 1 · peticiones a otros orígenes: 0 · gráfico: sin ejecutar · inline ejecutado: no · directivas: script-src-elem ← inline → detector OK
  [chromium · servido · cabecera ACTUAL de serve_panel.py (diagnóstico)] securitypolicyviolation: 2 · peticiones a otros orígenes: 0 · gráfico: dibujado (18387 píxeles) · fetch mismo origen: 200 · directivas: img-src ← otro, style-src-elem ← <origen>/…/spike.css
  [chromium · file://] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18387 píxeles) → OK
  [chromium · file:// · control inline] securitypolicyviolation: 1 · peticiones a otros orígenes: 0 · gráfico: sin ejecutar · inline ejecutado: no · directivas: script-src-elem ← inline → detector OK
  [chromium · file:// · respaldo 'sha256-…' (informativo)] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18387 píxeles) → OK
  [firefox] 142.0.1 (bundled)
  [firefox · servido] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18183 píxeles) · fetch mismo origen: 200 → OK
  [firefox · servido · control inline] securitypolicyviolation: 1 · peticiones a otros orígenes: 0 · gráfico: sin ejecutar · inline ejecutado: no · directivas: script-src-elem ← inline → detector OK
  [firefox · servido · cabecera ACTUAL de serve_panel.py (diagnóstico)] securitypolicyviolation: 1 · peticiones a otros orígenes: 0 · gráfico: dibujado (18183 píxeles) · fetch mismo origen: 200 · directivas: style-src-elem ← <origen>/…/spike.css
  [firefox · file://] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18183 píxeles) → OK
  [firefox · file:// · control inline] securitypolicyviolation: 1 · peticiones a otros orígenes: 0 · gráfico: sin ejecutar · inline ejecutado: no · directivas: script-src-elem ← inline → detector OK
  [firefox · file:// · respaldo 'sha256-…' (informativo)] securitypolicyviolation: 0 · peticiones a otros orígenes: 0 · gráfico: dibujado (18183 píxeles) → OK
  Política del respaldo (hash de Chart.js 4.5.1 + spike.js): default-src 'none'; script-src 'sha256-SERKgtTty1vs…' 'sha256-y2JkKMty/S42…'; style-src 'self' 'unsafe-inline'; img-src data:
  Casos: 4 · fallidos: 0
  Decisión: `script-src 'self' file:` vale en chromium y firefox; no hace falta el respaldo con 'sha256-…'.
  ```
  Sin Playwright (sin `PLAYWRIGHT_DIR` y sin `agent-kits/qa/runner/node_modules`): `node tests/e2e/panel-csp-spike.mjs --engines chromium,firefox` → `Playwright no está instalado (…) Sin Playwright no hay veredicto.` · `exit=2`.

**Notas**: CSP actual del servido en `skills/plugin-panel/scripts/serve_panel.py:469-470` (nonce) y `:492` (cabecera); la del HTML estático en `skills/plugin-panel/references/panel.html:2`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `8af6b23e20d0`.

### T-04 — `redact.anonimizar` para rutas, usuario y correos

- **Descripción**: Añade `anonimizar(texto, raiz, home, usuario)` a `agent-kits/shared/redact.py`: raíz del proyecto → `.`, home → `~`, usuario del sistema → `<usuario>`, correos → `<correo>`. `redactar` y su bloque replicado no cambian. Es la primitiva de CA-41 para todo HTML/JSON del panel.
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,12h (medido)
- **Supervisión**: est. 0,05h (≈25 % IA) · real 0,03h (estimado, 25 % de la IA)
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/redact.py`, `agent-kits/shared/test_redact.py`
- **Cubre (tests)**: E2E-08
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_redact.py` → `passed` · `python3 -m pytest -q tests/test_copias_declaradas.py` → `passed` (bloque replicado intacto)

**Criterios de aceptación**
- [x] `anonimizar` es pura y determinista; acepta rutas con `\` y `/` y mayúsculas distintas en Windows.
- [x] Orden fijo documentado: `redactar` → `anonimizar` → quitar controles → recortar.
- [x] Tests con home, usuario y correo falsos; sin falsos positivos sobre rutas relativas.
- [x] `anonimizar` queda FUERA del bloque `# --8<-- redact` declarado en `agent-kits/shared/copias.json`.

**Subtareas**
- [x] RED con los casos de CA-41.
- [x] Implementar fuera del bloque replicado.
- [x] Verificar `test_copias_declaradas`.

- **Changelog**: Nueva primitiva para quitar del panel la ruta del proyecto, el directorio personal, el usuario del sistema y los correos antes de mostrarlos o exportarlos.
- **Evidencia TDD**: `RED: los 9 tests nuevos test_anonimizar_* de agent-kits/shared/test_redact.py fallaron con AttributeError: module 'redact' has no attribute 'anonimizar' · 2026-10-15` (9 failed, 33 passed). Segundo rojo, ya con la función: 3 casos de rutas Windows fallaron (`C:\Users\<usuario>\Proyectos\…` en vez de `.\docs\…`) porque el separador había quedado como `[\/]` sin la barra invertida al pegar el código por heredoc; corregido escribiendo el fichero con el editor. GREEN: `42 passed`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider agent-kits/shared/test_redact.py` → `42 passed in 3.71s` · `… tests/test_copias_declaradas.py` → `29 passed in 0.36s` (bloque `redact_redactar` intacto en `redact.py` y `journal.py`). Regresión de consumidores: `agent-kits/shared/test_journal.py` + `tests/test_console_encoding.py` → `797 passed, 10 skipped`. Cobertura (`coverage run --include=*redact.py`): `agent-kits/shared/redact.py 102 stmts, 0 miss, 100%`.

**Notas**: patrón de tests en `agent-kits/shared/test_redact.py:23-41`; bloque replicado declarado en `agent-kits/shared/copias.json:297-310` (no tocar). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `f758d6759d60`.

### T-05 — Plantilla común multi-página (`panel_pages.py`) con menú accesible

- **Descripción**: Crea `skills/plugin-panel/scripts/panel_pages.py`: plantilla común con el menú de 7 entradas en orden fijo, `aria-current="page"`, enlace «Saltar al contenido», cabecera de modo (servido / instantánea con fecha), datos de la página en `<script type="application/json" id="panel-data">` y la marca `MARKER`. Añade `assets/panel.css` y `assets/panel-core.js` (menú, foco visible, Escape).
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real n/d (sin medición en este bloque)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-01
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/assets/panel.css`, `skills/plugin-panel/assets/panel-core.js`, `tests/test_panel_pages.py`, `tests/test_console_encoding.py` (añadido: modo `--list` de `panel_pages.py`, ver Notas)
- **Cubre (tests)**: E2E-01, E2E-05
- **Verificación**: `python3 -m pytest -q tests/test_panel_pages.py` → `passed` (7 páginas con el mismo `<nav>`, `aria-current` en la actual, `href="#main"` del salto, sin JS inline)

**Criterios de aceptación**
- [x] Las 7 páginas comparten el mismo `<nav>` byte a byte salvo `aria-current` (CA-32).
- [x] Ningún `<script>` inline ejecutable; los datos van en `type="application/json"` y se escapan `<`, `>` y `&` dentro del JSON.
- [x] El foco es visible (`:focus-visible` con contraste ≥ 3:1) y ningún elemento fijo lo tapa (CA-37, WCAG 2.4.11).
- [x] Toda cadena de la plantilla está en español.

**Subtareas**
- [x] RED: test de estructura de las 7 páginas.
- [x] Plantilla y render por página con contenido de marcador.
- [x] `panel-core.js`: menú, gestión de foco, Escape genérico.

- **Cerrada**: 2026-10-15
- **Changelog**: El panel exportado tiene siete páginas con el mismo menú accesible (salto al contenido, página actual marcada, foco visible) y sin JavaScript en línea.
- **Evidencia TDD**: `RED: los 6 tests de contenido y los 11 que cargan panel_pages.py / panel-core.js de tests/test_panel_pages.py fallaron con FileNotFoundError · 2026-10-15` (6 failed, 11 errors). GREEN: `17 passed`. Dos rojos intermedios eran del propio test (el JSON lleva además `chartjs_disponible`) y de un comentario del JS que contenía la palabra de la API de inserción de HTML (la prohibición se busca por texto).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_pages.py` → `17 passed`. Comprobación en navegador (Chromium/Edge y Firefox 142, `file://`, 500 px, red bloqueada) sobre una carpeta exportada: `violaciones: 0 · externas: 0`, el menú arranca plegado, el botón lo abre, Escape lo cierra y devuelve el foco a `menu-toggle`.

**Notas**: patrón de `MARKER` y de propiedad del HTML en `skills/plugin-panel/scripts/build_panel.py:19` y `:740` (`_write_html`); render actual en `build_panel.py:655-738`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `d0c27ed3e6d5`.

### T-06 — Paleta con test de contraste WCAG 2.2

- **Descripción**: Define la paleta (texto, fondos, marcas de gráficos, bordes y foco) como propiedades CSS en `panel.css` y un test que calcula el contraste: texto ≥ 4,5:1 (grande ≥ 3:1), marcas, bordes y foco ≥ 3:1 (CA-38).
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real n/d (sin medición en este bloque)
- **Supervisión**: est. 0,05h (≈25 % IA) · real n/d
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-05
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/panel.css`, `tests/test_panel_palette.py`
- **Cubre (tests)**: A11Y-01
- **Verificación**: `python3 -m pytest -q tests/test_panel_palette.py` → `passed` (cada par color/fondo declarado cumple su umbral)

**Criterios de aceptación**
- [x] El test lee los colores DEL CSS real (no de una copia en el test) y falla si un par baja de su umbral.
- [x] Cada serie de gráfico se distingue también por patrón, forma o etiqueta, no solo por color (CA-39, WCAG 1.4.1).
- [x] Un solo tema; sin dependencias externas de fuentes.

**Subtareas**
- [x] RED con un par inválido.
- [x] Paleta y pares declarados.

- **Cerrada**: 2026-10-15
- **Changelog**: La paleta del panel (un solo tema, sin fuentes externas) cumple los contrastes WCAG 2.2 AA, y un test lo comprueba leyendo los colores del propio CSS.
- **Evidencia TDD**: `RED: test_la_paleta_real_cumple_todos_los_umbrales y los 3 test_el_verificador_detecta_* de tests/test_panel_palette.py fallaron con AssertionError: falta la propiedad --superficie / KeyError: 'serie-1' · 2026-10-15` (4 failed, 3 passed; el CSS de T-05 solo traía 4 propiedades). GREEN: `7 passed`. Mutaciones comprobadas por los propios tests: `--tenue #5a6480` (< 4,5:1), `--serie-3 #2a3350` (< 3:1), `--foco #101830` y dos series con el mismo color son detectados.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_palette.py` → `7 passed`. Contrastes reales: texto 15,3:1 sobre superficie, texto secundario 8,4:1, acento 7,9:1, bordes 3,89:1 (superficie) y 4,26:1 (fondo), foco 12,0:1, series 7,9:1 a 11,9:1.

**Notas**: el repo no tiene un test de contraste previo; patrón de test que parsea un fichero real del bundle en `tests/test_panel_vendor.py` (T-02). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `09062a7faebb`.

### T-07 — Adaptador de gráficos con tabla equivalente y «sin datos»

- **Descripción**: `assets/panel-charts.js` dibuja cada gráfico dentro de un `<figure>` con `<canvas aria-label>` y una `<table>` equivalente accesible por teclado. Si falta Chart.js o su hash no coincide, muestra solo la tabla con un aviso. `panel-core.js` expone el render de ausencias: «sin datos» / «parcial: N de M» con su origen, nunca 0 ni media.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real n/d (sin medición en este bloque)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-02, T-03, T-06
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/panel-charts.js`, `skills/plugin-panel/assets/panel-core.js`, `tests/test_panel_charts_ui.py`
- **Cubre (tests)**: E2E-06, E2E-07
- **Verificación**: `python3 -m pytest -q tests/test_panel_charts_ui.py` → `passed` (escenarios: con Chart.js, sin Chart.js, valor `null`, parcial N de M)

**Criterios de aceptación**
- [x] Todo gráfico tiene nombre accesible que dice qué muestra y su tabla equivalente (CA-39).
- [x] Un valor `null` se pinta «sin datos» y queda FUERA de las barras; nunca 0 (CA-40).
- [x] Sin Chart.js (o con `window.Chart` ausente), la página sigue entera con la tabla y el aviso (fila «Falta el fichero de Chart.js» de «Manejo de errores»).
- [x] Sin `innerHTML`; textos por `textContent`.

**Subtareas**
- [x] RED en el arnés Node con DOM falso.
- [x] Adaptador y render de ausencias.

- **Cerrada**: 2026-10-15
- **Changelog**: Los gráficos del panel se dibujan con una tabla equivalente accesible por teclado; si falta Chart.js se muestra solo la tabla, y un dato ausente aparece como «sin datos», nunca como 0.
- **Evidencia TDD**: `RED: los 13 tests de tests/test_panel_charts_ui.py fallaron con FileNotFoundError / Charts.dibujar is not a function (panel-charts.js no existía) · 2026-10-15` (13 failed). GREEN: `13 passed` (11 escenarios Node con DOM falso + formas/paleta + sin innerHTML/red).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_charts_ui.py` → `13 passed` (con Chart.js, sin Chart.js, Chart.js marcado no disponible, Chart.js que lanza, `null`, todo `null`, parcial N de M, textos por `textContent`, 6 series por forma+color+etiqueta, sin animaciones, ausencias del núcleo).

**Notas**: arnés Node con DOM falso y escenarios parametrizados en `tests/test_panel_live_ui.py:64-140` (`_live_script`, `HARNESS`). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `22dd3e544960`.

### T-08 — Modo exportado `--export <dir>` con manifiesto propio (retira `--html` del panel)

- **Descripción**: `build_panel.py --export <dir>` escribe las 7 páginas, `assets/`, `vendor/chart.js/` y `export-manifest.json` (ficheros propios + sha256 + fecha). Solo sobrescribe HTML con `MARKER` o ficheros del manifiesto con el hash que él escribió. Retira `--html`; `--json` queda igual (CA-28).
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real n/d (sin medición en este bloque)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-04, T-05, T-07
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_plugin_panel.py`, `tests/test_panel_export.py`, `commands/plugin-catalog.md`, `skills/plugin-panel/SKILL.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `interop/**` (regenerado: `commands/` tocado), `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `tests/test_panel_server.py`, `tests/test_panel_diagnostics.py`, `tests/test_panel_vendor.py` (añadidos: ver Notas)
- **Cubre (tests)**: E2E-02, E2E-08
- **Verificación**: `python3 -m pytest -q tests/test_panel_export.py tests/test_plugin_panel.py tests/test_panel_contract_golden.py` → `passed` · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [x] La carpeta exportada contiene un HTML por página, Chart.js, su `LICENSE.md`, `PROVENANCE.json` y los datos de la instantánea (CA-33).
- [x] Ningún HTML exportado contiene `http://` ni `https://` en `src`/`href` de recursos (CA-35) ni la ruta del home, el usuario o correos (CA-41, grep en el test).
- [x] Un fichero ajeno en la carpeta destino no se sobrescribe y el comando sale con 2 (comportamiento actual de `--html`).
- [x] `--json` sigue igual que el golden de T-01; `--serve` excluye `--export` como hoy excluye `--html`.
- [x] `commands/plugin-catalog.md`, `SKILL.md` y `PLUGIN-PANEL.md` (ES/EN) citan `--export`; `interop/` regenerado.

**Subtareas**
- [x] RED: migrar `tests/test_plugin_panel.py:245-249` y `:362-373` de `--html` a `--export`.
- [x] Export con manifiesto y propiedad.
- [x] Actualizar comando y doc; regenerar `interop/`.

- **Cerrada**: 2026-10-15
- **Changelog**: El comando del catálogo exporta ahora una carpeta con las siete páginas, sus activos, Chart.js con licencia y un manifiesto de lo que escribió, sin rutas, usuario ni correos propios; `--html` desaparece.
- **Evidencia TDD**: `RED: 18 tests de tests/test_panel_export.py fallaron con error: unrecognized arguments: --export · 2026-10-15` (18 failed, 1 skipped). Segundo rojo: `--export --json` imprimía el resumen en stdout antes del JSON y lo rompía (`JSONDecodeError`); el resumen pasa a stderr cuando hay `--json`. GREEN: `18 passed, 1 skipped` (el skip es el test de enlace simbólico: sin permiso para crearlos en esta máquina).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_export.py tests/test_plugin_panel.py tests/test_panel_server.py tests/test_panel_contract_golden.py` → `177 passed, 3 skipped` (golden de T-01 intacto: `--json` no cambia). `python3 scripts/export-interop.py && … --check` → `export-interop --check: 88 ficheros al día`. `lint_plugin.py` → `0 errores · 8 avisos` (los 8 de antes).

**Notas**: CLI actual en `skills/plugin-panel/scripts/build_panel.py:766-810` (exclusiones de `--serve` en `:787`); propiedad por `MARKER` en `:740`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `79ef71eb3b05`.

### T-09 — Página Catálogo con las secciones de hoy y un gráfico de piezas por tipo

- **Descripción**: Mueve a `catalogo.html` las secciones actuales `#catalog`, `#extensions`, `#workflow` y `#source-notes`, sin perder información, y añade un primer gráfico real: piezas por tipo con su tabla. Es la rebanada vertical que prueba Chart.js + tabla + CSP de punta a punta con datos que ya existen.
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,19h (medido en bloque: 0,76 h de la ventana única T-09..T-12 repartidas según el peso del estimado 0,3/0,2/0,4/0,3)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-08
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/assets/page-catalogo.js`, `tests/test_panel_pages.py`, `tests/test_plugin_panel.py`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/assets/panel.css`, `tests/panel_render.py`, `tests/test_panel_export.py`
- **Cubre (tests)**: E2E-06, E2E-22
- **Verificación**: `python3 -m pytest -q tests/test_panel_pages.py tests/test_plugin_panel.py tests/test_panel_contract_golden.py` → `passed` (mismas piezas, conteos, fuentes, conflictos, hooks y workflow que hoy)

**Criterios de aceptación**
- [x] Toda pieza, conteo, fuente, conflicto, hook y paso de workflow que mostraba el panel de una página aparece en Catálogo (test por contenido sobre el bundle de fixture).
- [x] El gráfico de piezas por tipo usa los `counts` de `build_panel.py --json` y su tabla da las mismas cifras.
- [x] `--json` igual al golden.

**Subtareas**
- [x] RED: test de equivalencia de contenido con el HTML actual.
- [x] Migrar secciones y añadir el gráfico.

- **Cerrada**: 2026-10-15
- **Changelog**: La página Catálogo del panel reúne el catálogo, las extensiones, el workflow y las notas de fuentes, y añade un gráfico de piezas por tipo con su tabla de las mismas cifras.
- **Evidencia TDD**: `RED: 7 tests de tests/test_panel_pages.py (T-09) fallaron con AttributeError: cuerpos_paginas / FileNotFoundError: page-catalogo.js · 2026-10-15` (7 failed, 17 passed). GREEN: `32 passed` en el fichero (incluye los de T-12).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_pages.py tests/test_plugin_panel.py tests/test_panel_contract_golden.py` → `144 passed, 2 skipped` (mismas piezas, conteos, fuentes, conflictos, hooks y workflow que hoy; golden de T-01 intacto). Navegador (Playwright `pw/verify-panel.mjs` en el scratchpad, servidor real y export real): Edge 155 y Firefox 142.0.1, servido y `file://`, 7 páginas cada uno → `violaciones=0 · externas=0 · errores=0`; `catalogo`: gráfico con ~307 k píxeles pintados (Edge) / ~306 k (Firefox) y tabla `Agentes=2, Skills=1, Comandos=1, Herramientas=5, Acciones de hook=15`.

**Notas**: secciones de hoy en `skills/plugin-panel/references/panel.html:26` (anclas). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `5bde05dca3d9`.

### T-10 — Página Diagnóstico con la proyección actual

- **Descripción**: Mueve a `diagnostico.html` la sección de diagnóstico actual (`--diagnostics-report`, proyección de `doctor --panel-json`), con su validación de alcance tal cual. El enriquecimiento de CA-30/31 va en F4 (T-37).
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,13h (medido en bloque: 0,76 h de la ventana única T-09..T-12 repartidas según el peso del estimado 0,3/0,2/0,4/0,3)
- **Supervisión**: est. 0,05h (≈25 % IA) · real n/d
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-08
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_diagnostics.py`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/assets/page-diagnostico.js`, `tests/panel_render.py`
- **Cubre (tests)**: E2E-23
- **Verificación**: `python3 -m pytest -q tests/test_panel_diagnostics.py` → `passed`

**Criterios de aceptación**
- [x] Mismo contenido y mismos rechazos («sin informe», otro proyecto, otro formato) que hoy.
- [x] El panel no ejecuta `doctor` ni busca informes por su cuenta.

**Subtareas**
- [x] Ajustar `tests/test_panel_diagnostics.py` a la página nueva.
- [x] Migrar la sección.

- **Cerrada**: 2026-10-15
- **Changelog**: La página Diagnóstico muestra la instantánea de doctor con los mismos rechazos de siempre (sin informe, otro proyecto, otro formato) y filtros por severidad, sin ejecutar doctor.
- **Evidencia TDD**: `RED: 16 de los 32 tests de tests/test_panel_diagnostics.py fallaron con ImportError/AttributeError: cuerpos_paginas y falta assets/page-diagnostico.js · 2026-10-15` (16 failed, 16 passed). GREEN: `32 passed`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_diagnostics.py` → `32 passed` (8 rechazos con su mensaje en `diagnostico.html`, el catálogo ya no lleva la sección, renderizar no ejecuta subprocesos ni llama a `_diagnostics`, filtros por severidad/texto probados con Node). Navegador: ver T-09 (`diagnostico` sin violaciones en Edge y Firefox, servido y `file://`).

**Notas**: validador seleccionado en CONTRACTS E30 (`agent-kits/shared/diagnostic-report.py`); proyección portable en `agent-kits/shared/doctor.py:87-88`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `40dba80a350e`.

### T-11 — Servidor multi-página: rutas de página, activos de lista blanca y nonce en todo `<script>`

- **Descripción**: `serve_panel.py` sirve `<token>/<pagina>.html` y `<token>/plan-<id16>.html`, y los activos de una lista blanca precargados al arrancar (comprueba el hash de Chart.js al arrancar). El nonce va en todas las etiquetas `<script …>` que se generan, no por reemplazo del literal `<script>`. Topes, token y validación de Host/Origin/Sec-Fetch-Site sin cambios.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,25h (medido en bloque: 0,76 h de la ventana única T-09..T-12 repartidas según el peso del estimado 0,3/0,2/0,4/0,3)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-08
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_server.py`, `tests/test_panel_review_server.py`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`
- **Cubre (tests)**: E2E-03, E2E-04
- **Verificación**: `python3 -m pytest -q tests/test_panel_server.py` → `passed` (403 sin token / Host / Origin ajenos; 404 en activo fuera de lista; CSP `default-src 'none'` con `script-src 'nonce-…'` y `connect-src 'self'`)

**Criterios de aceptación**
- [x] Escucha solo en `127.0.0.1` con la URL de token del proceso; sin token, `Host` u `Origin` distintos → 403 (CA-34).
- [x] Activos servidos solo desde la lista blanca precargada; cualquier otra ruta → 404; sin lectura de disco por petición.
- [x] Si el hash de Chart.js no coincide al arrancar, las páginas se sirven sin él (tablas + aviso), no fallan.
- [x] Sigue rechazando `?`, `%`, `\` y `#` en la ruta.

**Subtareas**
- [x] RED: rutas nuevas y nonce en `<script src>`.
- [x] Lista blanca precargada y rutas.

- **Cerrada**: 2026-10-15
- **Changelog**: El servidor local sirve las siete páginas y sus activos desde una lista cerrada, con una política de seguridad estricta y sin leer disco en cada petición; si falta Chart.js muestra solo las tablas.
- **Evidencia TDD**: `RED: contra el serve_panel.py de HEAD, los tests nuevos de tests/test_panel_server.py dieron 7 failed, 79 errors (AttributeError: render_html/cuerpos_paginas; rutas de página y activos → 404) · 2026-10-15`. El RED se obtuvo DESPUÉS de implementar (git stash de serve_panel.py y los tests nuevos contra HEAD): este bloque no lo hizo antes. GREEN: `106 passed`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_server.py` → `106 passed` (403 sin Host/Origin propios en páginas y activos; 404 sin token o con otro, en activo fuera de lista, en `plan-<id16>.html` no registrado y en `?`, `%`, `\`, `#`; CSP exacta `default-src 'none'` + `script-src 'nonce-…'` + `connect-src 'self'`; nonce en TODO `<script>`; sin lectura de disco por petición; Chart.js alterado → sin Chart.js y aviso). `tests/test_panel_review_server.py`: `server.page` → `server.pages["plan.html"]`. Con el servidor real en Edge y Firefox: ver T-09.

**Notas**: enrutado en `skills/plugin-panel/scripts/serve_panel.py:364-371` (`_route`) y `:381-393` (`do_GET`); validación en `:347-362` (`_allowed`); nonce en `:469-470`; CSP en `:492`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `866a69fc9adb`.

### T-12 — JS vivos a `assets/` y a sus páginas (progreso, memoria, actividad, revisión)

- **Descripción**: Mueve `panel-live.js`, `panel-memory.js`, `panel-activity.js` y `panel-review.js` de `references/` a `assets/` y los carga como ficheros en sus páginas (progreso vivo → Plan e Inicio; memoria → Memoria; actividad → Agentes en vivo; revisión → Plan). Los arneses de UI leen los JS de `assets/`. Retira `references/panel.html`.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,19h (medido en bloque: 0,76 h de la ventana única T-09..T-12 repartidas según el peso del estimado 0,3/0,2/0,4/0,3)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-11
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/references/**`, `skills/plugin-panel/assets/**`, `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/scripts/build_panel.py`, `tests/test_panel_live_ui.py`, `tests/test_panel_activity_ui.py`, `tests/test_panel_memory_ui.py`, `tests/test_panel_review_ui.py`, `tests/test_panel_review_server.py`, `tests/test_panel_activity_server.py`, `tests/test_panel_memory_server.py`, `skills/plugin-panel/SKILL.md`, `docs/agents/CONTRACTS.md`, `tests/panel_render.py`, `skills/plugin-panel/assets/panel.css`
- **Cubre (tests)**: E2E-10
- **Verificación**: `python3 -m pytest -q tests/test_panel_live_ui.py tests/test_panel_activity_ui.py tests/test_panel_memory_ui.py tests/test_panel_review_ui.py tests/test_panel_review_server.py tests/test_panel_activity_server.py tests/test_panel_memory_server.py` → `passed` (mismos escenarios que hoy)

**Criterios de aceptación**
- [x] La revisión visual del plan (`--review-initiative`) funciona igual: anotar y enviar una decisión (CA-43); ningún camino de escritura nuevo desde el navegador.
- [x] `api/progress`, `api/activity`, `api/memory` y `api/review/*` no cambian de forma.
- [x] Los arneses siguen prohibiendo `innerHTML`; los IDs DOM se ajustan por página.
- [x] No queda ninguna referencia a `references/panel.html` (`lint_plugin.py` sin citas rotas nuevas).

**Subtareas**
- [x] RED: arnés leyendo de `assets/`.
- [x] Mover JS y cargar por página.
- [x] Retirar `references/panel.html`.

- **Cerrada**: 2026-10-15
- **Changelog**: El panel servido carga el progreso, la memoria, la actividad y la revisión del plan como ficheros propios en la página que les corresponde; la plantilla de una sola página desaparece.
- **Evidencia TDD**: `RED: contra el árbol de HEAD, las pruebas nuevas y migradas de tests/test_panel_pages.py, test_panel_live_ui.py y test_panel_memory_ui.py dieron 85 failed (FileNotFoundError: assets/panel-live.js…, AttributeError: cuerpos_paginas) · 2026-10-15`. Como en T-11, el RED se obtuvo después de implementar (ejecutando los tests nuevos sobre un `git archive` de HEAD). GREEN: `290 passed` en las 7 suites de la Verificación.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_live_ui.py tests/test_panel_activity_ui.py tests/test_panel_memory_ui.py tests/test_panel_review_ui.py tests/test_panel_review_server.py tests/test_panel_activity_server.py tests/test_panel_memory_server.py` → `290 passed` (mismos escenarios que hoy, los arneses leen los JS de `assets/`). `python scripts/lint_plugin.py` → `0 errores · 8 avisos` (los mismos 8 de antes: ninguna cita rota nueva).

**Notas**: extracción actual del JS inline en `tests/test_panel_live_ui.py:64` (`_live_script`); refresco de 5 s en `skills/plugin-panel/references/panel-live.js:63`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `da1ad6d07b1e`.

### T-13 — `build_dashboard.vista_json(inits)` sin cambio de bytes

- **Descripción**: Extrae a una función pura `vista_json(inits)` lo que hoy hace `main()` al construir el `--json` (procedencia y contadores por iniciativa). El panel la importará en F2 para dar cifras idénticas a `--json`.
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real 0,08h (medido)
- **Supervisión**: est. 0,03h (≈25 % IA) · real n/d
- **Previsión IA**: 46k in / 7k out tok · 0,70 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`, `tests/test_dashboard.py`
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_panel_contract_golden.py tests/test_dashboard.py` → `passed` (`--json` y `--md` idénticos al golden)

**Criterios de aceptación**
- [x] `--json` y `--md` byte a byte iguales al golden de T-01.
- [x] `vista_json` no lee disco ni imprime: recibe `inits` y devuelve la lista.

**Subtareas**
- [x] Extraer la función y llamarla desde `main()`.

- **Cerrada**: 2026-10-15
- **Changelog**: El cálculo del JSON de `roadmap-dashboard` queda en una función pura reutilizable por el panel, sin cambiar un solo byte de lo que imprime `--json` ni `--md`.
- **Evidencia TDD**: `RED: tests/test_dashboard.py::test_vista_json_es_pura_y_coincide_con_el_json_de_la_cli falló con AttributeError: module 'build_dashboard' has no attribute 'vista_json' · 2026-10-15` (1 failed). GREEN: `1 passed`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_contract_golden.py tests/test_dashboard.py` → `13 passed` (`--json` y `--md` idénticos al golden de T-01; `python tests/test_dashboard.py` → `OK: 3 iniciativas, 1 aviso(s) esperado(s). Todo pasa.`). Suite ampliada con `test_copias_declaradas.py` y `test_console_encoding.py`: `655 passed`.

**Notas**: bloque a extraer en `skills/roadmap-dashboard/scripts/build_dashboard.py:1157-1170`; `scan()` en `:451`. **Implementación (2026-10-15):** `vista_json(inits)` (antes de `main()`) recibe las iniciativas de `scan()` y les añade, en sitio y devolviendo la misma lista, `estimados`, `medidos`, `generacion_total`, `generacion_otros` y `procedencia`; `main()` hace `print(json.dumps(vista_json(inits), …))`. El test nuevo compara su resultado con lo que imprime `--json` de la CLI sobre la misma fixture, comprueba que no imprime y que no abre ficheros (`builtins.open` parcheado para fallar).

### T-14 — D-A1: retirar el HTML de `roadmap-dashboard` y redirigir a sus consumidores

- **Descripción**: `build_dashboard.py` retira `--html` y `render_html()`. `/roadmap-status` conserva `dashboard.md` y exporta el panel a `docs/roadmap/panel/` aterrizando en Iniciativas; avisa una vez de la ruta nueva y nunca borra un `dashboard.html` antiguo. Se actualizan todos los consumidores de `dashboard.html`/`--html` en el mismo cambio y la relación queda en `ROLES.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,32h (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-08, T-13
- **Tipo**: backend
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`, `skills/roadmap-dashboard/SKILL.md`, `tests/test_dashboard.py`, `commands/roadmap-status.md`, `skills/confluence-pull/SKILL.md`, `skills/confluence-publish/references/publish-and-sync.md`, `skills/plugin-panel/SKILL.md`, `docs/README.md`, `docs/en/README.md`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `docs/agents/ROLES.md`, `evals/cases/command-roadmap-status.json`, `evals/cases/skill-roadmap-dashboard.json`, `evals/cases/skill-plugin-panel.json`, `evals/cases/command-plugin-catalog.json`, `install/**`, `tests/installer.test.mjs`, `interop/**` (regenerado: `commands/` tocado)
- **Cubre (tests)**: E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_dashboard.py tests/test_panel_contract_golden.py` → `passed` · `python3 scripts/lint_plugin.py` → exit 0, sin citas rotas nuevas a `dashboard.html`/`--html` · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [x] Al cerrar no quedan dos generadores HTML con el mismo rol (ADR-011): `grep -rn "render_html" skills/roadmap-dashboard` vacío.
- [x] `--json`, `--md` y `--metrics-md` iguales; los cuatro comandos consumidores siguen funcionando.
- [x] Las 13 referencias actuales a `dashboard.html`/`--html` fuera del roadmap están actualizadas (lista en `Notas`).
- [x] La `description` de `roadmap-dashboard` deja de prometer HTML y la de `plugin-panel` absorbe «dashboard del roadmap», «panel del roadmap» y «kanban de los planes»; los casos de `evals/` casan con la `description` real.
- [x] `ROLES.md`: `roadmap-dashboard` dueño de los datos de cartera; `plugin-panel` dueño de la presentación; `/roadmap-status` entrada de cartera que delega.
- [x] El instalador copia `assets/` (incluido `vendor/`) del plugin.

**Subtareas**
- [x] RED: retirar las aserciones de `render_html` de `tests/test_dashboard.py:376-397` y llevarlas a las tarjetas de Iniciativas (F2).
- [x] Retirar `--html` y `render_html()`.
- [x] Actualizar consumidores, ROLES, evals; regenerar `interop/`.

- **Cerrada**: 2026-10-15
- **Changelog**: `roadmap-dashboard` deja de generar HTML y solo calcula datos de cartera; `/roadmap-status` escribe `dashboard.md` y exporta el panel de siete páginas a `docs/roadmap/panel/`.
- **Evidencia TDD**: `RED: tests/test_dashboard.py (aserciones nuevas «roadmap-dashboard no debe conservar render_html» y «--html retirado de la CLI») falló con AssertionError: roadmap-dashboard no debe conservar render_html · 2026-10-15`; las aserciones de `render_html` se habían retirado/trasladado antes de tocar el generador. GREEN: `OK: 3 iniciativas, 1 aviso(s) esperado(s). Todo pasa.` y `13 passed`.
- **Verificación ejecutada** (2026-10-15): `pytest tests/test_dashboard.py tests/test_panel_contract_golden.py tests/test_export_interop.py` → `58 passed` (goldens `--json`/`--md`/`--metrics-md` intactos); `python scripts/lint_plugin.py` → `0 errores · 8 avisos` (los mismos 8, sin citas rotas nuevas a `dashboard.html`/`--html`); `python evals/check.py` → `52 ficheros · 192 casos … 0 errores`; `python scripts/export-interop.py` → `88 ficheros escritos` y `--check` → `88 ficheros al día`; `grep -rn render_html skills/roadmap-dashboard` (solo fuentes) → vacío; `node --test tests/installer.test.mjs` → ver Notas.
- **Verificación ejecutada (revisión intento 1, gap 12)** (2026-10-15): `node --test --test-name-pattern="panel viaja" tests/installer.test.mjs` → `✔ el panel viaja con sus assets y Chart.js vendorizado (D-A1)` · `ℹ tests 1 · suites 0 · pass 1 · fail 0 · cancelled 0 · skipped 0` (criterio «el instalador copia `assets/`, incluido `vendor/`»).

**Notas**: consumidores encontrados con grep (2026-10-15): `commands/roadmap-status.md:18,22,25`, `skills/confluence-pull/SKILL.md:105`, `skills/confluence-publish/references/publish-and-sync.md`, `skills/roadmap-dashboard/SKILL.md`, `skills/plugin-panel/SKILL.md`, `docs/README.md`, `docs/en/README.md`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `docs/PLUGIN-PANEL.md`,… Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `f2026ddf5c5c`.

### T-15 — Documentación de F1 (panel multi-página, modos, CSP, Chart.js)

- **Descripción**: Actualiza `docs/PLUGIN-PANEL.md` y su espejo EN, `docs/FLOWS.md` y `docs/en/FLOWS.md` (flujo del panel: un comando, dos modos, siete páginas) y `skills/plugin-panel/SKILL.md` (mapa ≤ 200 líneas).
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real 0,08h (medido)
- **Supervisión**: est. 0,03h (≈25 % IA) · real n/d
- **Previsión IA**: 46k in / 7k out tok · 0,70 €
- **Dependencias**: T-12, T-14
- **Tipo**: docs
- **Archivos**: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/references/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_skill_size.py` → `passed` · `python3 scripts/lint_plugin.py` → exit 0 · lectura: ES y EN describen lo mismo (modos, páginas, CSP, procedencia de Chart.js)

**Criterios de aceptación**
- [x] `SKILL.md` de `plugin-panel` ≤ 200 líneas; el detalle va a `references/<tema>.md` con «lee X solo al llegar al paso Y».
- [x] Espejos EN actualizados en el mismo cambio.
- [x] Sin rutas absolutas ni datos personales.

**Subtareas**
- [x] Redactar ES; espejar EN; comprobar tamaño.

- **Cerrada**: 2026-10-15
- **Changelog**: La guía del panel describe las siete páginas, los modos exportado y servido, la política CSP de cada uno y la procedencia de Chart.js vendorizado, en español e inglés.
- **Evidencia TDD**: `TDD n/a: prosa (documentación)`.
- **Verificación ejecutada** (2026-10-15): `pytest tests/test_skill_size.py tests/test_mermaid_blocks.py` → `30 passed` (el recorrido completo del repo no se coló); `wc -l skills/plugin-panel/SKILL.md` → `118`; `python scripts/lint_plugin.py` → `0 errores · 8 avisos`; lectura ES/EN: ambas secciones «Panel multi-página» / «Multi-page panel» traen la misma tabla de páginas, modos, CSP y procedencia de Chart.js.

**Notas**: TDD n/a: prosa. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `f6968bf1dc6c`.

### T-16 — Cierre de la Fase 1: revisión de dos lentes y revisión visual del usuario (M-01)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals en verde; revisión adversarial de dos lentes sobre el diff de la fase (Lente C si `review-lens-select.py` la activa: toca CSP y servidor); bucle acotado a 3 con Minor al backlog; y el usuario revisa la fase en el navegador (M-01) antes de abrir la Fase 2.
- **Estado**: completado
- **Cerrada**: 2026-10-15
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 6,3h · real 1,84h (medido: fix1 0,26 + fix2 0,90 + fix3 0,26 + fix4 0,42; fix1 solo cubre el cierre; las revisiones de las lentes no se midieron por tarea) (revisión + corrección, f = 1,5)
- **Supervisión**: est. 2,6h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 2,88 M in / 469k out tok · 44,08 €
- **Dependencias**: T-01..T-15
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`, `docs/roadmap/2026-10-15-panel-redesign/{spec,design,improvement-plan,test-plan}.md` (enmienda 2026-10-15 aprobada por el usuario, commit ee8e7cc), `skills/confluence-publish/SKILL.md`, `skills/confluence-publish/references/config-and-policy.md`, `skills/confluence-publish/scripts/confluence-scope.py`, `tests/test_confluence_scope.py`, `tests/test_panel_fix1.py` (bucle de corrección intento 1: gaps 1-4, 7-10), `tests/test_hook_supervisor.py`, `tests/test_knowledge_find.py`, `hooks/runtime-supervisor.py`, `tests/codex-plugin-state.test.mjs` (cambios del orquestador durante el bucle, declarados aquí para la puerta de alcance; el límite de tiempo de `codex-plugin-state.test.mjs` pasó de 7500 a 9500 ms en b09e07f, justificado por la lente A del intento 2: el techo real es el plazo de 3 s más el SIGKILL exterior de 4 s y el descendiente vive 12 s), `tests/test_panel_fix2.py`, `skills/confluence-publish/references/publish-and-sync.md` (bucle de corrección intento 2: gaps 2-2..2-8), `tests/opencode-plugin.test.mjs` y `tests/hook-runtime.test.mjs` (orquestador, bucle fix2: reporter TAP fijado ante Node ≥ 23 y plazo de SessionEnd por defecto, sin heredar `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` del entorno del desarrollador), `tests/test_panel_fix3.py` (intento 3: lista blanca de texto servido, alias 8.3, manifiesto con hash y panel real; `tests/test_panel_fix4.py` (confirmación del intento 3: contrato del saneado servido y topes tras anonimizar); `tests/test_hook_supervisor.py` con reloj controlado)
- **Cubre (tests)**: M-01
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: sección «Revisión de dos lentes — intento N: …» de la Fase 1 sin Critical ni Important abiertos, y línea «Revisión visual del usuario — Fase 1: aprobada AAAA-MM-DD» con el resultado de M-01

**Criterios de aceptación**
- [x] CA-44 de la Fase 1: suites, linter y evals en verde.
- [x] Revisión de dos lentes cerrada en ≤ 3 intentos; Minor anotados al backlog, no bloqueantes.
- [x] El usuario aprueba M-01 en el navegador (servido y exportado).

**Subtareas**
- [x] Ejecutar suites y puertas.
- [x] Despachar `adversarial-review` sobre el diff de la fase.
- [x] Pedir al usuario M-01 y anotar el resultado.

**Notas**: el contador de intentos y el worklog `[revisión]` son del orquestador. Cabecera de revisión con el formato `intento N: …` sin paréntesis tras N (la leen `jira-flow`/`task-brief`).

**Bucle de corrección — intento 1** (clave de medición `2026-10-15-panel-redesign/T-16-fix1`; la ventana se abrió con el trabajo ya hecho, así que cubre solo el cierre y no es dato de coste fiable): gaps 1, 2, 3, 4, 5, 7, 8, 9, 10 y 12 corregidos con TDD (RED y GREEN por gap en la columna «Evidencia» de la tabla); 6 (decisión del usuario) y 11 (`design.md`, orquestador) intactos. Ninguno rechazado: los diez se reprodujeron contra el código antes de corregir (`panel_pages.py` aceptaba `..` y rutas absolutas, `_redact_values` anonimizaba `scope`/`kind`/`runtime`, `description[:480]` precedía al anonimizado, `serve_panel.py` no saneaba, `confluence-scope.py` incluía `vendor/chart.js/LICENSE.md`). Tests nuevos: `tests/test_panel_fix1.py`, `agent-kits/shared/test_redact.py` (idempotencia), `tests/test_confluence_scope.py` (exportación del panel). Verificación del bucle: suites del panel + `test_dashboard` + `test_redact` + confluence + `test_console_encoding` + `test_copias_declaradas` + `test_graphiti_security` + `test_export_interop` → `1561 passed, 4 skipped`; `lint_plugin.py` → `0 errores · 8 avisos` (los mismos 8); `export-interop.py --check` → `88 ficheros al día`; `evals/check.py` → `0 errores`; `scope-check --base 14ef84b` → exit 0 (afirmación desfasada tras b09e07f: ver la nota del intento 2, gaps 2-1 y 2-9). Se tocó `commands/roadmap-status.md` (interop regenerado); no `agents/` ni `hooks/`.


**Bucle de corrección — intento 3** (clave `2026-10-15-panel-redesign/T-16-fix3`, abierta al empezar: **0,26 h IA (medido)**, 3,34 €): cinco gaps 3-1..3-5 reproducidos y corregidos con TDD (RED/GREEN en la tabla); ninguno rechazado. Tests nuevos: `tests/test_panel_fix3.py`, `tests/test_confluence_scope.py`, `tests/test_hook_supervisor.py`. Tocados: `skills/plugin-panel/scripts/{serve_panel,panel_pages}.py`, `skills/confluence-publish/scripts/confluence-scope.py`. Verificación: `lint_plugin` 0 errores · 8 avisos (los mismos); `export-interop --check` 88 al día; `evals/check` 0 errores; `ledger-lint` 0 incoherencias; `scope-check --base 14ef84b` exit 0, fuera de alcance (0); suites del panel, confluence, redact, supervisor, graphiti, copias, console_encoding → todas verdes; `node --test tests/opencode-plugin.test.mjs` → 21 pass · 0 fail.

**Bucle de corrección — intento 2** (clave de medición `2026-10-15-panel-redesign/T-16-fix2`, abierta al empezar: **0,9 h IA medidas**, 8,22 € (medido), tokens completos del transcript): los nueve gaps 2-1..2-9 se reprodujeron contra el código y se corrigieron con TDD (RED y GREEN por gap en la tabla del intento 2); ninguno rechazado. Añadida a petición del usuario la fila 2-10 (defensa de `_route` con test propio; RED por mutación temporal). Tests nuevos: `tests/test_panel_fix2.py` (2-3..2-5, 2-7, 2-10 y TOCTOU de 2-4), `agent-kits/shared/test_redact.py` (2-2), `tests/test_confluence_scope.py` (2-6), `tests/test_hook_supervisor.py` (2-8). Tocados: `agent-kits/shared/redact.py`, `skills/plugin-panel/scripts/{serve_panel,panel_pages,build_panel}.py`, `skills/confluence-publish/scripts/confluence-scope.py` (+ dos referencias), `hooks/runtime-supervisor.py` (E2: `hooks/` tocado; `export-interop.py --check` → «88 ficheros al día», sin cambios de interop). Decisiones: 2-3 sanea `api/memory` y `api/review/*` en el servidor con el saneador único (`api/activity` solo expone enums, hashes y números: sin cambio); 2-4 deja como riesgo residual la ventana mínima entre la comprobación y el `unlink` (sin descriptores relativos en Windows); 2-7 aborta (exit 2) ante punto o espacio final y salta sin borrar la entrada que solo difiere en mayúsculas (exit 0, manifiesto nuevo coherente con Chart.js listado). Verificación del bucle: suites del panel + `test_dashboard` + `test_confluence_scope` + `test_redact` + `test_hook_supervisor` + `test_copias_declaradas` + `test_graphiti_security` + `test_console_encoding` + `test_skill_size` → `1549 passed, 4 skipped` (y `test_panel_fix2` + graphiti/consola/copias/skill-size de nuevo tras 2-10 → `812 passed`); `lint_plugin.py` → `0 errores · 8 avisos` (los mismos 8, de `docs/` con `/skills`); `export-interop.py --check` → `88 ficheros al día`; `evals/check.py` → `0 errores`; `node --test tests/opencode-plugin.test.mjs` → 20 pass · 1 fail (`Windows teardown completes when PATH omits system tools`: el test espera salida TAP `# pass 1` y Node 23.8 imprime el reporter por defecto; fallo de entorno ajeno a este diff, sin JS tocado). **Salida real de `scope-check` (post-cambios de este bucle, sustituye la afirmación del intento 1)**: `python agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign --base 14ef84b` → exit 0 · «122 fichero(s) cambiado(s) · 285 patrón(es) declarados en Archivos» · «✅ en alcance (121)» (el ledger cuenta aparte) · «❌ fuera de alcance (0): —» · sin avisos ⚠️.

**Verificación ejecutada (2026-10-15, HEAD `70ba946`):** réplica de `ci.yml` en `python:3.11-slim` (`git -c core.autocrlf=false archive`): `lint_plugin` exit 0 · `evals/check` exit 0 · pytest **7955 passed, 54 skipped, 0 failed** · bench p95 7,58 ms (exit 0) · `export-interop --check` «88 ficheros al día» · `node --test` **329 pass, 0 fail**. En Windows, todas las suites del panel por tandas en verde; `scope-check --base 14ef84b` exit 0 (0 fuera de alcance). Revisión: 3 intentos más 2 confirmaciones, sin Critical ni Important abiertos; 3 Minor (M-F1-1..3) al backlog de la Fase 2; deuda del gap 6 aceptada por el usuario y verificada por mutación. M-01 aprobado por el usuario.

---

## Fase 2 — Inicio, Iniciativas y Plan

**Estado**: completado (2026-10-20) · **Estimado**: 58,4h humanas · 19,1h IA · **Real**: — · **Coste est.**: 3.054 € referencia · ≈ 447 € ejecución · **Tokens est.**: 10,16 M (antes de la enmienda: 36,0h · 10,8h IA · 1.876 € · ≈ 261 € · 5,74 M)

Criterios de la spec: CA-01 a CA-03, CA-05 a CA-14 y CA-45 a CA-54 (enmienda 2026-10-15: revisión del plan desde el panel; `design.md` §8). Incluye el campo `- **Cerrada**:` del diseño (I-02), que la evaluación dejaba fuera: diferencia declarada en `improvement-plan.md`.

> **Enmienda 2026-10-15 (T-55..T-58).** Las cuatro tareas de revisión del plan (R-1..R-4 de `design.md` §8.8) llevan los IDs correlativos T-55..T-58 para no renumerar T-01..T-54 (T-01..T-13 ya están cerradas y citadas en commits); por eso aparecen aquí, en la Fase 2, después de T-27 y antes de la documentación (T-28, que absorbe R-5) y del cierre (T-29, que absorbe R-6 con **lente C obligatoria**). Van **después de T-12, T-19 y T-23**. Orden de ejecución dentro de la fase: T-17..T-27 → T-55 → T-56 → T-57 → T-58 → T-28 → T-29.

### T-17 — `api/cartera` y proyección de cartera con las cifras de `--json`

- **Descripción**: `panel_data.cartera()` importa `build_dashboard.py` (`scan` + `vista_json`) y `progress-report.py` y proyecta lo que necesitan Inicio e Iniciativas. En servido, `api/cartera` (≤ 64 iniciativas, ≤ 64 KiB); en exportado, el mismo JSON incrustado.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,22h (medido; ventana 19:13–19:33 UTC, 4,78 €)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-16
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_data.py`, `tests/test_panel_server.py`, `tests/test_panel_fix4.py` (añadido: contrato del saneador para `api/cartera`, cierra M-F1-2 para la API nueva; ver Notas)
- **Cubre (tests)**: API-01
- **Verificación**: `python3 -m pytest -q tests/test_panel_data.py tests/test_panel_server.py` → `passed` (cifras iguales a las de `build_dashboard.py --json` y `progress-report.py` sobre la fixture, ejecutando los scripts, no un oráculo copiado)

**Criterios de aceptación**
- [x] Por iniciativa: estado de spec, «ilegible» con motivo, N/M tareas, horas y coste real/estimado y procedencia; ausente = `null` + etiqueta, nunca 0.
- [x] Los ledgers > 256 KiB salen en una lista aparte y no suman en N ni en M (CA-02).
- [x] `api/cartera` ≤ 64 KiB con 64 iniciativas; sin `?` en la ruta.
- [x] El panel no recalcula cifras de cartera: las toma de `vista_json`.

**Subtareas**
- [x] RED con la fixture de T-01 contra la salida real de los scripts.
- [x] Proyección y ruta.

- **Cerrada**: 2026-10-15
- **Changelog**: El panel servido ofrece la cartera del roadmap (estado de cada spec, tareas completadas, horas y coste real frente a estimado, procedencia y alertas) con las mismas cifras que el dashboard y el informe de progreso.
- **Evidencia TDD**: `RED: tests/test_panel_data.py falló con FileNotFoundError: skills/plugin-panel/scripts/panel_data.py (6 failed, 5 errors) · 2026-10-15`; `RED: test_http_api_cartera_proyecta_el_ledger_con_las_cifras_de_progress_report, test_http_api_cartera_cae_en_unavailable_sin_filtrar_la_causa y test_http_api_cartera_pasa_por_el_saneador_unico_del_servidor fallaron con AssertionError (404 en api/cartera; 3 failed) · 2026-10-15`. El contrato de `test_panel_fix4.py` se escribió tras el servidor y se comprobó por mutación: quitar `titulo` de `_DISPLAY_KEYS` lo pone en rojo (`1 failed, 6 passed`).

- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_data.py tests/test_panel_server.py` → `128 passed in 97.08s`; `... tests/test_panel_fix4.py` → `7 passed in 3.37s`. Las cifras se comparan ejecutando `build_dashboard.py --json` y `progress-report.py line --json` sobre la fixture de T-01 (subprocess), no contra un oráculo copiado.

**Notas**: patrón de carga de módulos del bundle `_load_shared` en `skills/plugin-panel/scripts/serve_panel.py:35-40`; snapshot acotado de progreso en `serve_panel.py:120-134` (`progress_snapshot`); lector acotado `agent-kits/shared/local-read.py` (CONTRACTS E35). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `d9a108a9c036`.

### T-18 — Página Inicio: estados de spec, avance global y real frente a estimado

- **Descripción**: `index.html` muestra el número de iniciativas por estado de spec (gráfico + tabla), el avance global «N de M tareas completadas (P %)» y el coste real frente al estimado con la línea «procedencia: X medidos · Y estimados · Z desconocidos».
- **Estado**: completado
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 1,03h (medido; ventana 19:32–19:50 UTC, 8,55 €; incluye el aviso del modo exportado y el verificador de navegador)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-17
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-inicio.js`, `skills/plugin-panel/assets/page-cartera.js` (añadido: carga y validación de la cartera compartidas con T-19), `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/scripts/build_panel.py` (añadido: esqueleto de Inicio y cartera en la exportación), `tests/test_panel_inicio_ui.py`, `tests/test_panel_pages.py`, `tests/test_panel_live_ui.py` (textos del aviso del modo exportado)
- **Cubre (tests)**: E2E-07, E2E-11
- **Verificación**: `python3 -m pytest -q tests/test_panel_inicio_ui.py` → `passed` (escenarios: estados variados, ilegible, ledger fuera de tope, sin estimación)

**Criterios de aceptación**
- [x] CA-01: cifras por estado iguales a `--json`; la ilegible aparece como «ilegible» y no cuenta en ningún estado.
- [x] CA-02: N y M iguales a la suma de `progress-report.py`; ledgers fuera de tope listados aparte.
- [x] CA-03: una iniciativa sin estimación no suma 0; la procedencia se cuenta por tipo.
- [x] Funciona en servido (vía `api/cartera`) y en exportado (JSON incrustado).

**Subtareas**
- [x] Subtarea previa (petición del usuario tras M-01): aviso del modo exportado «Copia estática del … · para verla en vivo, abre el panel servido con `/plugin-catalog --serve`».
- [x] RED en el arnés Node.
- [x] Página y gráficos.

- **Cerrada**: 2026-10-15
- **Changelog**: La página Inicio muestra cuántas iniciativas hay en cada estado de spec, el avance global de tareas y el coste real frente al estimado con su procedencia; la copia estática ahora explica cómo verla en vivo.
- **Evidencia TDD**: `RED: test_cabecera_de_modo (tests/test_panel_pages.py) y test_default_offline_has_no_operational_fetch (tests/test_panel_live_ui.py) fallaron con AssertionError: falta «Copia estática del» · 2026-10-15`; `RED: 9 failed (TypeError: datos_de_pagina() got an unexpected keyword argument 'cartera'; assets/page-inicio.js ausente del export; sin esqueleto de Inicio) en tests/test_panel_inicio_ui.py · 2026-10-15`. Los escenarios de Node escritos tras el JS pasaron a la primera: se comprobó su sensibilidad por mutación (pintar `null` como 0 y no contar iniciativas con dato → 4 failed).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_inicio_ui.py` → `24 passed in 23.05s`; `tests/test_panel_pages.py tests/test_panel_live_ui.py tests/test_panel_export.py` → `79 passed, 1 skipped`. Navegador (Edge 155 y Firefox 142, servidor real y export en `file://`, fixture de T-01): 0 violaciones de CSP, 0 peticiones externas, 0 errores; gráfico de estados dibujado (píxeles > 0) con su tabla (1·1·1·1·1·1·0), «2 de 3 tareas completadas (67 %)», epsilon listado aparte, «procedencia: 5 medidos · 1 estimados · 0 desconocidos».

**Notas**: arnés en `tests/test_panel_live_ui.py:64-140`; adaptador de gráficos de T-07. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `8f0f4b01738d`.

### T-19 — Página Iniciativas: kanban de solo lectura con alertas en texto y navegación a Plan

- **Descripción**: `iniciativas.html` muestra un kanban con una columna por estado y una tarjeta por iniciativa: slug, fecha, «N/M tareas (P %)», horas y coste real/estimado y alertas en texto. La tarjeta con plan navega a su Plan con ratón o Enter.
- **Estado**: completado
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,12h (medido; ventana 19:50–19:56 UTC, 3,85 €)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-17
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-iniciativas.js`, `skills/plugin-panel/assets/panel.css` (añadido: kanban y enlace de tarjeta), `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/scripts/build_panel.py` (añadido: esqueleto de Iniciativas), `tests/test_panel_iniciativas_ui.py`, `tests/test_panel_server.py` (añadido: los JS nuevos en la lista de activos), `tests/test_dashboard.py`
- **Cubre (tests)**: E2E-05, E2E-12
- **Verificación**: `python3 -m pytest -q tests/test_panel_iniciativas_ui.py` → `passed` (sin `draggable`, sin listeners de arrastre, alertas con texto, enlace `plan-<id16>.html`)

**Criterios de aceptación**
- [x] CA-05: solo lectura; ningún control mueve tarjetas ni escribe en fichero.
- [x] CA-06: cada alerta (ledger fuera de tope, gaps de revisión abiertos, `completado` con checkboxes sin marcar, sin estimación) lleva su texto.
- [x] CA-08: la tarjeta con plan es un enlace activable con Enter que lleva a `plan-<id16>.html`.
- [x] Las aserciones retiradas de `render_html` en T-14 tienen su equivalente aquí.

**Subtareas**
- [x] RED con las alertas de la fixture.
- [x] Kanban y navegación.

- **Cerrada**: 2026-10-15
- **Changelog**: La página Iniciativas muestra un kanban de solo lectura con una columna por estado de spec; cada tarjeta lleva fecha, tareas, horas, coste, procedencia y sus alertas en texto, y enlaza a su Plan.
- **Evidencia TDD**: `RED: 5 failed en tests/test_panel_iniciativas_ui.py (esqueleto ausente: el cuerpo de iniciativas era el marcador provisional y page-iniciativas.js no estaba cableado en panel_pages/build_panel) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_iniciativas_ui.py` → `18 passed` (12 de T-19: sin `draggable`, sin listeners de arrastre ni controles, alertas con texto, enlace `plan-<id16>.html`; el resto son de T-20). Navegador (Edge 155 y Firefox 142, servido y `file://`): 0 violaciones de CSP, 0 externas, 0 errores; 6 tarjetas en 6 columnas, 0 elementos `draggable`, Enter sobre el enlace de la tarjeta de `alfa` navega a `plan-c232e7fb147f7bbb.html` (= `sha256('2026-01-10-alfa')[:16]`).

**Notas**: alerta de checkboxes sin marcar según `agent-kits/shared/ledger-lint.py:704`; id de iniciativa `sha256(carpeta)[:16]` de `skills/plugin-panel/scripts/serve_panel.py:184`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `c55d91839b17`.

### T-20 — Iniciativas: gráficos de horas y coste por iniciativa con tabla

- **Descripción**: Dos gráficos en Iniciativas: horas real frente a estimado y coste por iniciativa, cada uno con su tabla. Las iniciativas sin datos aparecen en la tabla con «sin datos» y fuera de las barras.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real 0,05h (medido; ventana 19:56–20:02 UTC, 1,48 €)
- **Supervisión**: est. 0,1h (≈25 % IA) · real n/d
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-19
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-iniciativas.js`, `skills/plugin-panel/assets/panel-charts.js` (añadido: filas `sinDatos` solo en la tabla), `tests/test_panel_iniciativas_ui.py`, `tests/test_panel_charts_ui.py` (añadido: escenarios del adaptador)
- **Cubre (tests)**: E2E-07, E2E-13
- **Verificación**: `python3 -m pytest -q tests/test_panel_iniciativas_ui.py` → `passed` (iniciativa sin datos: fila «sin datos» en la tabla, ausente del dataset del gráfico)

**Criterios de aceptación**
- [x] CA-07: dos gráficos con su tabla equivalente.
- [x] CA-40: ningún 0 ni media en lugar de un dato ausente.

**Subtareas**
- [x] RED; gráficos.

- **Cerrada**: 2026-10-15
- **Changelog**: Iniciativas añade dos gráficos, horas y coste por iniciativa (real frente a estimado), cada uno con su tabla; las iniciativas sin datos aparecen en la tabla como «sin datos» y no en las barras.
- **Evidencia TDD**: `RED: test_adaptador_de_graficos[sin_datos_filas_en_la_tabla_y_fuera_de_las_barras] y [solo_filas_sin_datos_no_dibuja_el_grafico_pero_las_lista] fallaron con AssertionError (el adaptador no conocía spec.sinDatos; 2 failed, 13 passed) · 2026-10-15`; `RED: 6 failed en tests/test_panel_iniciativas_ui.py (figure ausente en #grafico-horas y #grafico-coste) · 2026-10-15`. Mutación: pintar los ausentes como 0 y no separar las iniciativas sin datos → 3 failed.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_iniciativas_ui.py tests/test_panel_charts_ui.py` → `18 passed` y `15 passed`. Navegador (Edge y Firefox, servido y `file://`): dos `<figure>` con canvas y tabla de 6 filas; en horas, 3 iniciativas en las barras (alfa, gamma, epsilon) y beta/delta/zeta solo en la tabla como «sin datos»; en coste, alfa/gamma/zeta en barras y beta/delta/epsilon como «sin datos»; gamma con real «sin datos» y estimado 1,25 h.

**Notas**: adaptador de T-07. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `31a73e486a1f`.

### T-21 — `ledger-view.py`: proyección pura de un `tasks.md`

- **Descripción**: Nuevo `agent-kits/shared/ledger-view.py`: tareas, fase, estado (vocabulario de `ledger-lint.ESTADOS`; desconocidos aparte con el literal), horas real/est con «(medido)»/«(estimado)», criterios con su casilla, `Verificación` (recortada a `VERIFICACION_MAX`), dependencias, enlace a historia archivada y última revisión con sus gaps abiertos. Reutiliza los parsers de `ledger-lint.py`; no crea un tercer lector de secciones de revisión (ADR-016).
- **Estado**: completado
- **Tiempo humano**: est. 4,2h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,27h (medido; ventana 20:35-20:52 UTC, 7,56 €; incluye casi todo el trabajo de T-22, cuyo cierre del meter se hizo después)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-16
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-view.py`, `agent-kits/shared/test_ledger_view.py`, `agent-kits/shared/README.md`, `agent-kits/shared/ledger-lint.py` (añadido: `parse_ledger` lee los campos que el panel proyecta, sin segundo lector), `tests/test_console_encoding.py` (añadido: modos de `ledger-view.py` y `panel_data.py`)
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_ledger_view.py` → `passed` (incluye el caso `intento N:` sin paréntesis, un `—` en horas que sale `null` y una tarea con historia en `execution-history.md` marcada «archivado»)

**Criterios de aceptación**
- [x] Importa `parse_ledger`, `secciones_revision`, `ultimo_intento_para` y `filas_pendientes_de_tarea` de `ledger-lint.py`; ningún regex de cabecera de revisión propio.
- [x] Un estado fuera del vocabulario va a `desconocidos` con su literal (CA-09).
- [x] `—` o ausencia → `null`, nunca 0 (CA-13).
- [x] Lee con `local-read.py` y el tope de 256 KiB; por encima devuelve «ledger fuera del tope» sin cifras.
- [x] No mezcla el contenido de `execution-history.md` con el del ledger: solo enlaza (CA-10).

**Subtareas**
- [x] RED con ledgers de fixture.
- [x] Proyección pura y CLI `--json`.

- **Cerrada**: 2026-10-15
- **Changelog**: El panel puede leer cualquier ledger como una vista de solo lectura: tareas por estado, horas reales y estimadas, criterios, verificación, dependencias, gaps abiertos y enlace al histórico archivado.
- **Evidencia TDD**: `RED: agent-kits/shared/test_ledger_view.py falló en la colección con FileNotFoundError: ledger-view.py (el módulo no existía) · 2026-10-15`. Sensibilidad por mutación: pintar `—` como 0 y perder el literal de los estados desconocidos → 2 failed (horas y estados).
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider agent-kits/shared/test_ledger_view.py` → `23 passed` (incluye `intento N:` sin paréntesis invisible, `—` → `null`, tarea con historia marcada «archivado» sin leer `execution-history.md`, ledger de 256 KiB + 1 → `fuera_de_tope` sin cifras); `tests/test_ledger_lint.py agent-kits/shared/test_progress_report.py agent-kits/shared/test_ledger_archive.py` → `77 passed`. `python agent-kits/shared/ledger-view.py docs/roadmap/2026-10-15-panel-redesign --json` → `status ok`, 58 tareas, 0 desconocidos.

**Notas**: parsers en `agent-kits/shared/ledger-lint.py:242` (`secciones_revision`), `:375` (`ultimo_intento_para`), `:414` (`filas_pendientes_de_tarea`), `:480` (`parse_ledger`); `ESTADOS` en `:61`; `VERIFICACION_MAX` en `:68`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `0fa81a7af2d4`.

### T-22 — Campo opcional `- **Cerrada**: AAAA-MM-DD` en el ledger

- **Descripción**: Añade el campo opcional `- **Cerrada**:` que escribe quien marca una tarea `completado` (mismo patrón que `- **Changelog**:`). `ledger-lint.py` valida solo el formato y que sea ≥ `creado`; `ledger-view.py` lo extrae; `implementer` y `/dev-cycle` lo escriben al cerrar.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,01h (medido; ventana 20:52-20:53 UTC, 0,46 €; el grueso del trabajo cayó en la ventana de T-21)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-21
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`, `agent-kits/shared/ledger-view.py`, `agent-kits/shared/test_ledger_view.py`, `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py` (sin cambios: no replica el patrón), `agent-kits/shared/copias.json` (sin cambios: `CAMPO_LEDGER_PATTERN` no es un bloque replicado), `skills/changelog-sync/scripts/changelog-sync.py` (añadido: su copia literal de `CAMPO_LEDGER_PATTERN`), `agent-kits/planner/templates/tasks.md`, `agents/implementer.md`, `commands/dev-cycle.md`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**` (regenerado: `agents/` y `commands/` tocados)
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_ledger_lint.py agent-kits/shared/test_ledger_view.py tests/test_copias_declaradas.py` → `passed` · `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-15-panel-redesign/tasks.md` → 0 incoherencias · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [x] Un ledger antiguo sin `Cerrada` sigue pasando `ledger-lint` sin avisos nuevos.
- [x] `Cerrada` con formato inválido o anterior a `creado` → incoherencia con `fichero:línea`.
- [x] Si `CAMPO_LEDGER_PATTERN` está en un bloque replicado de `copias.json`, sus copias (`task-brief.py`, `jira-flow.py`) se actualizan en el mismo cambio y `test_copias_declaradas` pasa.
- [x] `agents/implementer.md` y `commands/dev-cycle.md` dicen cuándo escribirlo; `interop/` regenerado.

**Subtareas**
- [x] RED en `tests/test_ledger_lint.py`.
- [x] Validación, extracción y prosa; regenerar `interop/`.

- **Cerrada**: 2026-10-15
- **Changelog**: Las tareas del ledger pueden llevar una fecha de cierre opcional (`Cerrada`) que el linter valida (fecha real, no anterior a la creación) y que el panel usa para el burndown; los ledgers antiguos siguen validando igual.
- **Evidencia TDD**: `RED: 4 failed en tests/test_ledger_lint.py (test_cerrada_con_formato_invalido_…, test_cerrada_vacia_…, test_cerrada_anterior_a_la_creacion_…, test_el_parser_expone_cerrada_… con KeyError: 'creado') · 2026-10-15`. La extracción de `Cerrada` en `parse_ledger` y su proyección en `ledger-view` se escribieron junto al parser de T-21; su RED es el de las pruebas de validación y de `creado`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_ledger_lint.py agent-kits/shared/test_ledger_view.py tests/test_copias_declaradas.py` → `60 passed`; `skills/changelog-sync/scripts/test_changelog_sync.py` → `84 passed` (compara `CAMPO_LEDGER_PATTERN` con la copia); `agent-kits/shared/test_task_brief.py` → `92 passed`; `ledger-lint.py` sobre los 49 `docs/roadmap/*/tasks.md` → 0 incoherencias en todos (avisos sin cambio); `python scripts/export-interop.py --check` → `88 ficheros al día` (exit 0).

**Notas**: patrón del campo opcional `Changelog` en `agent-kits/shared/ledger-lint.py:80-104` (`CAMPO_LEDGER_PATTERN` en `:102`). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `a33de1d7eed6`.

### T-23 — `api/plan-<id16>` y kanban de tareas en la página Plan

- **Descripción**: `plan-<id16>.html` muestra un kanban de solo lectura con una columna por estado del vocabulario del ledger y una franja «estado no reconocido» con el literal; tarjeta por `T-XX` con ID, título, fase, horas real/estimado y nº de gaps. En servido, `api/plan-<id16>` (≤ 64 KiB).
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,3h (medido; ventana 20:53-21:06 UTC, 6,20 €)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-21
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `tests/test_panel_server.py`, `skills/plugin-panel/scripts/build_panel.py` (añadido: índice de `plan.html`, esqueleto de la página Plan y exportado de las páginas por iniciativa), `skills/plugin-panel/assets/panel.css` (añadido: franja de estados no reconocidos), `tests/test_panel_fix4.py` (añadido: contrato de `api/plan-<id16>`, `_clip` y la marca del redactor), `tests/test_panel_export.py` (añadido: `page-plan.js` en el manifiesto)
- **Cubre (tests)**: API-02, E2E-14
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py tests/test_panel_server.py` → `passed` (5 columnas exactas + franja de desconocidos; respuesta ≤ 65.536 bytes con el ledger de fixture más grande)

**Criterios de aceptación**
- [x] CA-09: solo las 5 columnas del vocabulario; desconocidos en su franja con el literal.
- [x] La respuesta solo trae lo del kanban (ID, título, fase, estado, real/est, nº de gaps); el detalle va por T-24.
- [x] Ledger > 256 KiB → «ledger fuera del tope de lectura (256 KiB)» sin cifras.

**Subtareas**
- [x] RED; ruta, proyección y página.

- **Cerrada**: 2026-10-15
- **Changelog**: Cada iniciativa con plan tiene su página Plan con un kanban de solo lectura: una columna por estado del ledger y una tarjeta por tarea con fase, horas IA y gaps abiertos; el índice de Plan enlaza todos los planes.
- **Evidencia TDD**: `RED: test_plan_proyecta_solo_lo_del_kanban_con_su_contrato (tests/test_panel_plan_ui.py) falló con AttributeError: module 'panel_data_plan' has no attribute 'plan'; el resto de la suite (servidor, exportado y JS) con FileNotFoundError: assets/page-plan.js · 2026-10-15`; `RED: test_recorte_no_parte_la_marca_del_redactor falló con AssertionError al quitar \[secreto redactado\] de _MARKS (M-F1-3) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_plan_ui.py tests/test_panel_server.py tests/test_panel_fix4.py` → `181 passed` (5 columnas exactas + franja de desconocidos con el literal; respuesta de un ledger de 699 tareas recortada con `omitidas` y ≤ 65.536 bytes; ledger fuera del tope e ilegible sin cifras). Navegador (Edge 155 y Firefox 142, servidor real y export en `file://`, ledger real de esta iniciativa + fixture de T-01 con epsilon e iota): 0 violaciones de CSP, 0 peticiones externas, 0 errores en las 8 sesiones; Enter sobre el enlace de la tarjeta de Iniciativas navega a `plan-3603347f8e257b64.html` (antes 404), 5 columnas «Borrador (36) · En progreso (0) · En revisión (0) · Completado (22) · Cancelado (0)» con 58 tarjetas y 0 `draggable`; epsilon dice «Ledger fuera del tope de lectura (256 KiB)» e iota «Ledger no legible», ambos sin tarjetas.

**Notas**: `ledger-view.py` de T-21; patrón de ruta con parámetro sin `?` según `design.md` §2.4 I-04 y `serve_panel.py:374-380` (`_review_route`). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `3eeb456ec059`.

### T-24 — `api/plan-<id16>-<T-XX>` y detalle de tarea accesible

- **Descripción**: Al abrir una tarjeta (clic o Enter) se muestra su detalle: descripción, criterios con casilla, `Verificación` (y su salida si existe), dependencias, última «Revisión de dos lentes — intento N» con sus gaps abiertos y severidad, y el enlace «archivado» si tiene historia. Escape lo cierra devolviendo el foco a la tarjeta.
- **Estado**: completado
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,27h (medido; ventana 21:06-21:19 UTC, 4,81 €; incluye la verificación en navegador de T-23 y T-24)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-23
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `tests/test_panel_server.py`, `skills/plugin-panel/scripts/build_panel.py` (añadido: esqueleto del detalle y detalles incrustados en el exportado), `skills/plugin-panel/assets/panel.css` (añadido: detalle y región de anuncio), `tests/test_panel_fix4.py` (añadido: contrato de `api/plan-<id16>-<T-XX>`)
- **Cubre (tests)**: API-03, E2E-05, E2E-14
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py tests/test_panel_server.py` → `passed` (Escape devuelve el foco a la tarjeta; `Verificación` recortada a 2.000 caracteres; enlace «archivado»)

**Criterios de aceptación**
- [x] CA-10: todos los campos listados; el contenido de `execution-history.md` nunca aparece como si estuviera en el ledger.
- [x] CA-37: el detalle es alcanzable con Tab en orden de lectura y Escape devuelve el foco.
- [x] Todo texto pasa por `redact.redactar` + `redact.anonimizar` antes de salir.

**Subtareas**
- [x] RED; ruta del detalle y diálogo.

- **Cerrada**: 2026-10-15
- **Changelog**: Al abrir una tarjeta del plan, con clic o con Enter, se muestra el detalle de la tarea: descripción, criterios, verificación y su salida, dependencias, última revisión con sus gaps y si tiene historia archivada; Escape lo cierra y devuelve el foco.
- **Evidencia TDD**: `RED: 37 failed, 62 passed en tests/test_panel_plan_ui.py (los 37 de T-24: AttributeError: panel_data.tarea ausente, rutas api/plan-<id16>-<T-XX> en 404, esqueleto sin #plan-detalle y page-plan.js sin botón ni detalle) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_server.py` → `123 passed in 63.00s` (fix1); `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_plan_ui.py tests/test_panel_fix4.py` → `99 passed` y `12 passed` (Escape devuelve el foco a la tarjeta; `Verificación` recortada a 2.000 caracteres y su salida a 1.000; marca «archivado» sin leer `execution-history.md`; respuesta con 40 criterios y 20 gaps de 3 bytes por carácter recortada ≤ 65.536 bytes con `omitidos`). Navegador (Edge 155 y Firefox 142, servido y `file://`; ledger real de 58 tareas): 0 violaciones de CSP, 0 externas, 0 errores; Enter sobre el botón de T-18 abre el detalle (foco en la región `#plan-detalle`, anuncio «Detalle de T-18 abierto», secciones Datos · Descripción · Criterios de aceptación · Verificación · Última revisión, 7 criterios), Tab llega al botón «Cerrar detalle», Escape lo cierra y el foco vuelve al botón de T-18 (anuncio «Detalle de T-18 cerrado»), el clic abre T-22 y «Cerrar detalle» devuelve el foco a su botón.

**Notas**: redacción del servidor antes de recortar según CONTRACTS E37 (`serve_panel.py` → `agent-kits/shared/redact.py`); tope de 160 caracteres de títulos en `serve_panel.py:139`. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `93ce69bab194`.

### T-25 — Plan: avance por fase y real frente a estimado

- **Descripción**: Gráficos del Plan: avance por fase (completadas/total) con las mismas cifras que el «Resumen de progreso» del ledger, y real frente a estimado por fase y por tarea con «(medido)»/«(estimado)».
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,25h (estimado)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-23
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `skills/plugin-panel/scripts/panel_data.py` (añadido: `cerrada` en la fila), `skills/plugin-panel/scripts/build_panel.py` (añadido: contenedores de gráficos y botón), `tests/test_panel_plan_ui.py`
- **Cubre (tests)**: E2E-07, E2E-15
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (cifras por fase iguales a las de la tabla «Resumen de progreso» del ledger de fixture; `—` no se pinta como 0)

**Criterios de aceptación**
- [x] CA-11: avance por fase con su tabla, cifras iguales al resumen del ledger.
- [x] CA-13: real frente a estimado por fase y por tarea con su procedencia; `—` = «sin datos».

**Subtareas**
- [x] RED; gráficos.

- **Cerrada**: 2026-10-15
- **Changelog**: El Plan muestra el avance por fase y las horas IA reales frente a las estimadas, por fase y por tarea, cada gráfico con su tabla y con la procedencia «(medido)» o «(estimado)»; lo que falta se dice «sin datos».
- **Evidencia TDD**: `RED: 42 failed, 74 passed en tests/test_panel_plan_ui.py (los nuevos de T-25..T-27 y los de contrato de fila al exigir `cerrada`; KeyError/AssertionError: sin `cerrada` en la fila, sin graficos ni boton plan-refrescar, sin sondeo a 5 s) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_plan_ui.py` → `116 passed` (avance por fase igual a la tabla «Resumen de progreso» de la fixture alfa: Fase 1, 1 de 2; `—` se pinta «sin datos», nunca 0). Navegador (Edge 155 y Firefox 142, servido y `file://`, `verify-p4.mjs`): 0 violaciones de CSP, 0 externas, 0 errores; cada gráfico con su tabla; en el ledger real (58 tareas) los tres gráficos de barras con tabla y `canvas`.

**Notas**: `panel_data._fila_plan` añade `cerrada` (fecha ya validada por `ledger-view`, `null` si falta o es inválida) y el validador JS lo exige (clave nueva de la fila, 3.ª tarea que la usa). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `0ac34e64d4a9`.

### T-26 — Plan: burndown solo con fechas de cierre completas

- **Descripción**: Si todas las tareas `completado` llevan `Cerrada`, el Plan dibuja el burndown de pendientes por fecha; si no, muestra «burndown no disponible: N de M tareas completadas sin fecha de cierre», sin gráfico parcial ni interpolado.
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,1h (estimado)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-22, T-25
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `skills/plugin-panel/scripts/panel_data.py`, `tests/test_panel_plan_ui.py`
- **Cubre (tests)**: E2E-07, E2E-15
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (ledger con todas las fechas → serie; con una sin fecha → mensaje con N y M y sin `<canvas>`)

**Criterios de aceptación**
- [x] CA-12: burndown solo con fechas completas; mensaje exacto en el otro caso.
- [x] CA-40: ningún punto interpolado.

**Subtareas**
- [x] RED; serie y mensaje.

- **Cerrada**: 2026-10-15
- **Changelog**: El Plan dibuja el burndown de tareas pendientes solo cuando todas las completadas llevan fecha de cierre; si no, dice cuántas faltan y no dibuja un gráfico parcial.
- **Evidencia TDD**: `RED: (mismo lote que T-25: los 7 de burndown/`cerrada` en rojo antes del código) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_plan_ui.py` → `116 passed` (todas las fechas → línea con una fecha por cierre real y sin días interpolados; con una ausente → «burndown no disponible: 2 de 3 tareas completadas sin fecha de cierre», sin `canvas` ni tabla; ledger antiguo → «1 de 1…»; sin completadas → «Sin datos»). Navegador (Edge 155 y Firefox 142, servido y `file://`, `verify-p4.mjs`): 0 violaciones de CSP, 0 externas, 0 errores; cada gráfico con su tabla; ledger de alfa → mensaje exacto «1 de 1», fixture gamma con `Cerrada` → línea con tabla, plan real → mensaje.

**Notas**: Regla de `design.md` §2.4 I-02. Pendientes = tareas no canceladas menos las cerradas hasta cada fecha; los puntos son solo las fechas de cierre reales. Decisión: con CERO tareas completadas no hay mensaje de «N de M» (sería «0 de 0») sino «Sin datos: ninguna tarea completada todavía».

### T-27 — Plan: refresco vivo sin perder la tarea abierta

- **Descripción**: En servido, el kanban del Plan refresca cada 5 s por `api/plan-<id16>` y refleja el nuevo estado sin recargar ni cerrar la tarea abierta; un fallo de red conserva lo anterior con su aviso.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,3h (estimado)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-24
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `skills/plugin-panel/scripts/build_panel.py` (añadido: región de frescura y botón «Actualizar ahora»)
- **Cubre (tests)**: E2E-16
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (dos ciclos de 5.000 ms con un estado cambiado: tarjeta movida, detalle abierto y foco conservados)

**Criterios de aceptación**
- [x] CA-14: tras dos ciclos (10 s) el kanban refleja el cambio sin recargar y sin perder la tarea abierta.
- [x] El sondeo se pausa con la pestaña oculta y se cancela al refrescar a mano (comportamiento de `panel-live.js`).

**Subtareas**
- [x] RED con temporizadores falsos.
- [x] Refresco con conservación de DOM.

- **Cerrada**: 2026-10-15
- **Changelog**: En servido, el kanban del Plan se refresca solo cada 5 segundos y mueve las tarjetas sin cerrar la tarea abierta ni perder el foco; si falla la red, conserva lo último con un aviso.
- **Evidencia TDD**: `RED: (mismo lote: 6 de refresco vivo en rojo antes del código) · 2026-10-15`.
- **Verificación ejecutada** (2026-10-15): `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -q -p no:cacheprovider tests/test_panel_plan_ui.py` → `116 passed` (dos ciclos de 5.000 ms con un estado cambiado: tarjeta movida, detalle abierto, foco y región `aria-live` conservados; tarjeta sin cambios con el mismo nodo; detalle de la tarea abierta repedido en silencio si su fila cambia; fallo de red conserva y avisa; pausa con pestaña oculta; el botón cancela el sondeo). Navegador (Edge 155 y Firefox 142, servido y `file://`, `verify-p4.mjs`): 0 violaciones de CSP, 0 externas, 0 errores; cada gráfico con su tabla; copia del ledger de alfa con T-02 → completado: tras 11,5 s T-02 pasa de «En progreso» a «Completado», el detalle de T-01 sigue abierto y el foco queda en T-02.

**Notas**: Patrón de `panel-live.js` (sondeo con `setTimeout` de 5 s, `inFlight`, pausa por `visibilitychange`, abort del plazo) y conservación de DOM: las tarjetas con la misma fila reutilizan su nodo; las movidas se reinsertan y el foco se restaura por id; `ctx.boton` apunta siempre al botón vigente para que Escape devuelva el foco. El texto de `plan-estado` ya no lleva la fecha (pasa a `plan-frescura`, no viva) para no anunciar cada ciclo.

### T-55 — `plan-review.py summary`: resumen de revisiones de solo lectura (`summarize_reviews`)

- **Descripción**: Añade al dueño de la revisión (`agent-kits/shared/plan-review.py`) la operación `summarize_reviews(project, initiatives, *, state_root, deadline=None)` y su CLI `summary` (lista JSON por stdin ≤ 16 KiB). Sigue el patrón de `list_reminders`: sin inicializar, sin `.lock`, sin `fsync`, inventario doble y `approval_granted: false`. Devuelve una fila cerrada por iniciativa (`sin_revision · pendiente · cambios_pedidos · aprobada · obsoleta · no_disponible`, `version_ordinal` vN, cifras de comentarios y respuestas) y un sobre `ok|partial|unavailable` por debajo de 64 KiB (`design.md` §8.3).
- **Estado**: completado
- **Tiempo humano**: est. 5,0h · real —
- **Tiempo IA (ejec.)**: est. 1,0h · real 0,6h (estimado)
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 457k in / 75k out tok · 7,00 €
- **Dependencias**: T-12
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/plan-review.py`, `agent-kits/shared/test_plan_review_summary.py`, `agent-kits/shared/test_plan_review.py` (fix1 F2-10: caché del redactor)
- **Cubre (tests)**: API-07
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_plan_review_summary.py` → `passed` (6 estados, vN, obsoleta por `raw` y por `view`, plazo → `partial`, `state_changed`, 64 registros, árbol idéntico antes y después, con el cerrojo tomado por otro proceso) · `python3 -m pytest -q tests/test_plan_review_caller.py tests/test_panel_review_server.py tests/test_panel_review_ui.py` → `0 failed` sin tocar sus expectativas (CA-54)

**Criterios de aceptación**
- [x] [GWT] CA-49 (propiedad de solo lectura): Dado un inventario con revisiones en cada situación, Cuando se llama a `summary`, Entonces cada iniciativa recibe su estado del vocabulario cerrado y el árbol de `.claude/plan-review/` conserva los mismos nombres, tamaños y hashes; con la carpeta de estado inexistente devuelve `sin_revision` y no la crea; funciona mientras otro proceso tiene el cerrojo.
- [x] [GWT] CA-50: Dado una revisión sobre una versión del plan, Cuando el `sha256` crudo del plan difiere (o, si coincide, difiere `view_sha256`), Entonces el estado es `obsoleta` y la decisión anterior no cuenta como vigente; un plan ilegible da `no_disponible`, nunca otro estado.
- [x] `vN` es el ordinal estable de la versión entre las que tienen registros; un plazo agotado da `status: partial` con `deadline_expired`; un cambio durante la lectura da `state_changed`; `review_id` solo sale para el servidor.
- [x] [GWT] CA-54: las suites existentes de `plan-review.py` y `tests/test_panel_review_*` pasan sin modificar sus expectativas; `list_reminders` y el formato de estado no cambian.

**Subtareas**
- [x] RED: suite nueva `test_plan_review_summary.py` con los 6 estados, sin escritura, cerrojo tomado, plazo y 64 registros.
- [x] `summarize_reviews` componiendo `_inventory`/`_record`/`_projection`; CLI `summary` (exit 0 `ok|partial`, 3 `unavailable`).
- [x] Comprobar que las suites del dueño no cambian.

- **Changelog**: `plan-review.py` gana la operación de solo lectura `summary`, que devuelve el estado de revisión de varias iniciativas sin crear ni modificar nada en `.claude/plan-review/`.

- **Cerrada**: 2026-10-15

- **Evidencia TDD**: `RED: agent-kits/shared/test_plan_review_summary.py falló con AttributeError (summarize_reviews no existe; 14 failed) · 2026-10-15`

- **Verificación ejecutada** (2026-10-15): `pytest -q agent-kits/shared/test_plan_review_summary.py` → `14 passed in 55.14s`; `tests/test_plan_review_caller.py tests/test_panel_review_server.py tests/test_panel_review_ui.py tests/test_console_encoding.py tests/test_copias_declaradas.py` → `793 passed, 13 skipped`; suites del dueño (`test_plan_review*.py`) → `188 passed`.

**Notas**: decisión O7 de `design.md` §8.2 (O8, proyección en el servidor, descartada: dos lectores del mismo estado). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `0676e9b774b3`.

### T-56 — Servidor: `review_scope`, id16 → iniciativa y rutas `api/review-summary`, `api/review-current` y `api/review-open`

- **Descripción**: `serve_panel.py` recibe el ámbito nuevo en `review_scope={'state_root': …}` (sin ampliar `review_selection`), construye la correspondencia `id16 → iniciativa` con el escaneo de cartera, sustituye el `set` de ids por un registro `id64 → {iniciativa, puerta, escritura}` (tope 128) y añade `GET api/review-summary`, `GET api/review-current/<id16>` y `POST api/review-open/<id16>`; `refresh` reabre la iniciativa y la puerta del registro (`design.md` §8.4). La puerta de la apertura desde el navegador es el literal `requested-review`; un `plan-ok` ajeno se ve sin escritura (405).
- **Estado**: completado
- **Tiempo humano**: est. 7,2h · real —
- **Tiempo IA (ejec.)**: est. 1,4h · real 1,0h (estimado)
- **Supervisión**: est. 0,35h (≈25 % IA) · real —
- **Previsión IA**: 641k in / 104k out tok · 9,80 €
- **Dependencias**: T-23, T-55
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_review_panel_server.py`
- **Cubre (tests)**: API-07, E2E-24
- **Verificación**: `python3 -m pytest -q tests/test_panel_review_panel_server.py tests/test_panel_review_server.py tests/test_panel_server.py` → `passed` (id16 desconocido → 404 y estado intacto; `gate_key` en el cuerpo → 400 sin llamar al dueño; sin token u `Origin` ajeno → 403 y estado intacto; `plan-ok` ajeno → 405; respuestas ≤ 65.536 bytes; el servidor ordinario no carga el dueño)

**Criterios de aceptación**
- [x] [GWT] CA-45: Dado el panel servido con `review_scope` y una iniciativa sin revisión, Cuando el cliente envía `POST api/review-open/<id16>` con el cuerpo exacto `{"initiative_id": "<id16>"}`, Entonces el servidor abre la revisión con `open_review(..., gate_key='requested-review')` y devuelve el `review_id` registrado; un id16 que no está en la correspondencia → 404 antes de cargar el dueño y el directorio de estado no cambia.
- [x] [GWT] CA-47: Dado cualquier operación nueva de revisión, Cuando llega sin token, con `Host`, `Origin` o `Sec-Fetch-Site` ajenos, sin `Content-Type` JSON o por encima de 16 KiB, Entonces 403/400/413 y el estado no cambia; mismas cabeceras y CSP con nonce que hoy; sin cookies.
- [x] [GWT] CA-48: Dado `api/review-open`, Cuando el cuerpo trae cualquier clave distinta de `initiative_id`, `gate_key` incluida, Entonces 400 sin llamar al dueño; el registro de una revisión abierta desde el navegador tiene `gate_key = requested-review`, nunca `plan-ok`; no existe ninguna ruta que fije o cambie la puerta.
- [x] [GWT] CA-43: Dado `--review-initiative X --review-gate-key plan-ok` (como lo lanza `/dev-cycle`), Cuando se usa la revisión preseleccionada, Entonces sigue funcionando con escritura exactamente como hoy; el ámbito nuevo no cambia `review_selection` (`tests/test_panel_review_server.py:172-176` intacto).
- [x] Tope de 128 ids con respuesta explícita «demasiadas revisiones abiertas en este proceso»; los ids solo se registran desde respuestas del dueño, nunca desde el cuerpo de una petición; las carpetas sin plan, no válidas o con colisión de id16 quedan fuera de la correspondencia.

**Subtareas**
- [x] RED: suite nueva `test_panel_review_panel_server.py` (404, 400, 403, 405, tope 128, tamaño).
- [x] Correspondencia id16, registro con puerta y escritura, tres rutas, `refresh` por registro.
- [x] Comprobar `test_ordinary_server_never_loads_review_owner` y las suites existentes sin cambios.

- **Changelog**: El servidor del panel puede abrir una revisión de plan para cualquier iniciativa desde la página Plan y publica el resumen de estados de revisión, con las mismas protecciones de token, `Origin` y CSP que ya tenía.

- **Cerrada**: 2026-10-15

- **Evidencia TDD**: `RED: tests/test_panel_review_panel_server.py falló con TypeError (create_server() got an unexpected keyword argument 'review_scope'; 25 errores) · 2026-10-15`

- **Verificación ejecutada** (2026-10-15): `pytest -q tests/test_panel_review_panel_server.py` → `25 passed` (x3 repeticiones); `tests/test_panel_review_*.py tests/test_panel_server.py` → `266 passed` (sin tocar `test_panel_review_server.py:172-176`; `test_ordinary_server_never_loads_review_owner` verde); `test_panel_export/fix4/pages/console_encoding/copias_declaradas/graphiti_security` → `854 passed, 1 skipped`.

**Notas**: patrones en `serve_panel.py:190` (id16), `:252-263` (caché de 5 s), `:293-296` (`refresh`), `:319-327` (registro de ids), `:379-385` (rutas de revisión), `:353-368`/`:411-430` (protecciones). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `b6fc1b4bcd3d`.

### T-57 — CLI `--review-panel`, texto de activación y exportado sin revisión

- **Descripción**: `build_panel.py` gana el flag opt-in `--review-panel`, que exige `--serve --project … --review-state-root …` y habilita en las páginas Plan el botón «Revisar este plan», el estado y las respuestas del agente; combinable con `--review-initiative`. Sin él, la página Plan explica en una frase cómo activarlo. `panel_pages.py` sirve `panel-review.js` también con `review_scope`. `--review-state-root` sin `--review-initiative` ni `--review-panel` sigue saliendo con exit 2 y el modo exportado no lleva controles ni lee `.claude/plan-review/` (`design.md` §8.5).
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,4h (estimado)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-56
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_export.py`, `tests/test_panel_review_panel_server.py`
- **Cubre (tests)**: E2E-24
- **Verificación**: `python3 -m pytest -q tests/test_panel_export.py tests/test_panel_review_ui.py tests/test_panel_pages.py tests/test_panel_review_panel_server.py` → `passed` (el exit 2 de `--serve --project … --review-state-root …` sin iniciativa de `tests/test_panel_review_ui.py:52-57` sigue idéntico; el HTML exportado no contiene `api/review` ni controles)

**Criterios de aceptación**
- [x] [GWT] CA-52: Dado `--export`, Cuando abro cualquier página, Entonces no hay botones ni formularios de revisión, ningún `fetch` de escritura ni la ruta `api/review`; la página Plan dice «estado de revisión: solo en modo servido» y no se lee `.claude/plan-review/`.
- [x] [GWT] CA-53: Dado el panel servido sin `--review-panel` (o sin `--project`), Cuando abro el Plan, Entonces no aparece el botón y la página explica con los parámetros exactos cómo activarlo (`--review-panel --review-state-root <proyecto>/.claude/plan-review`); sin `review_scope` no se sirve `panel-review.js`.
- [x] [GWT] CA-54: `--review-initiative`, `--review-state-root` y `--review-gate-key` siguen funcionando como hoy (incl. `plan-ok` desde `/dev-cycle`); `--review-state-root` solo, sin iniciativa ni `--review-panel`, → exit 2.

**Subtareas**
- [x] RED: casos del flag, del texto de activación y del exportado en `test_panel_export.py`.
- [x] Flag, validación y paso de `review_scope`; cuerpo de la página Plan con botón o explicación.

- **Changelog**: Nuevo flag `--review-panel` para activar la revisión de planes desde el panel servido; el exportado nunca lleva controles de revisión y el comando `--review-initiative` se conserva igual.

- **Cerrada**: 2026-10-15

- **Evidencia TDD**: `RED` no capturado: los tests de T-57 se escribieron tras el flag (desviación de TDD); se comprobó que cada aserción cubre una rama (6 casos de exit 2, texto de activación, exportado sin `api/review`) · 2026-10-15`

- **Verificación ejecutada** (2026-10-15): `pytest -q tests/test_panel_export.py tests/test_panel_review_ui.py tests/test_panel_pages.py tests/test_panel_review_panel_server.py` → `0 failed` (export 30 passed/1 skipped, sin tocar `test_panel_review_ui.py:52-57`); batería final del bloque: `854 passed, 1 skipped`.

**Notas**: `build_panel.py:845-847` y `:860-862` (exclusión mutua actual); `panel_pages.py:146-147` (carga condicional del JS de revisión). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `f7c3ccf584e7`.

### T-58 — UI del Plan: abrir, comentar y decidir una revisión; estado en tarjetas y respuestas del agente

- **Descripción**: `panel-review.js` toma la iniciativa de `data-initiative-id`: `review-current` → `view` para mostrar la revisión vigente, botón «Revisar este plan» → `review-open`, cabecera de estado en la página Plan (texto «sin revisión · pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión»), comentarios por sección y decisión (aprobar / pedir correcciones) con los topes de hoy, y bajo cada comentario la respuesta del agente con su disposición y el resultado de `verify-result` («sin respuesta del agente» si no hay). El JS de Iniciativas pinta el mismo estado en texto en cada tarjeta desde `api/review-summary`, con la misma cifra. Sin `innerHTML`.
- **Estado**: completado
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 1,2h · real 1,1h (estimado)
- **Supervisión**: est. 0,3h (≈25 % IA) · real —
- **Previsión IA**: 549k in / 89k out tok · 8,40 €
- **Dependencias**: T-19, T-23, T-56, T-57
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/panel-review.js`, `skills/plugin-panel/assets/page-iniciativas.js`, `skills/plugin-panel/assets/page-plan.js`, `skills/plugin-panel/assets/panel.css`, `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_review_panel_ui.py`, `tests/test_panel_review_ui.py`
- **Cubre (tests)**: E2E-05, E2E-10, E2E-24
- **Verificación**: `python3 -m pytest -q tests/test_panel_review_panel_ui.py tests/test_panel_review_ui.py` → `passed` (el arnés Node prohíbe `innerHTML`; mismo texto de estado en tarjeta y cabecera; los escenarios de `test_panel_review_ui.py` sin cambiar sus expectativas)

**Criterios de aceptación**
- [x] [GWT] CA-45: Dado el Plan de una iniciativa sin revisión (con `--review-panel`), Cuando pulso «Revisar este plan», Entonces el cliente envía solo el id16 publicado por el servidor y la revisión aparece en la misma página; el botón es operable con teclado y el resultado se anuncia con texto.
- [x] [GWT] CA-46: Dado una revisión abierta, Cuando añado comentarios anclados por `section_id` y envío «aprobar» o «pedir correcciones», Entonces se guardan por `submit` con los mismos topes (≤ 20 comentarios, ≤ 2.000 caracteres) y el mismo error al pasarse.
- [x] [GWT] CA-49: Dado revisiones en cada situación, Cuando abro Iniciativas y el Plan, Entonces tarjeta y cabecera muestran el mismo estado en texto (no solo color) y abrir la página no escribe nada.
- [x] [GWT] CA-50: Dado una decisión sobre una versión anterior del plan, Cuando cambia el hash, Entonces tarjeta y cabecera muestran «obsoleta por cambio de versión» y la UI exige una nueva decisión.
- [x] [GWT] CA-51: Dado una revisión con `result` del agente, Cuando abro el Plan, Entonces veo bajo cada comentario la respuesta, su disposición y el resultado de `verify-result` si existe; sin respuesta, «sin respuesta del agente».
- [x] Con la revisión preseleccionada por `--review-initiative` y `plan-ok` (escritura) o con un `plan-ok` ajeno (solo lectura) la UI se comporta como indica `design.md` §8.4: sin controles de escritura en el segundo caso.

**Subtareas**
- [x] RED: arnés Node `test_panel_review_panel_ui.py` (botón, estados, cabecera, respuestas, solo lectura, sin `innerHTML`).
- [x] `panel-review.js`: entrada por id16, botón, cabecera y respuestas; cambio del literal «Sin respuesta declarada».
- [x] Estado en texto en las tarjetas de Iniciativas desde `api/review-summary`.

- **Cerrada**: 2026-10-16

- **Evidencia TDD**: `RED: tests/test_panel_review_panel_ui.py falló con 13 failed (sin controles de revisión en el Plan ni estado en tarjetas; el literal «Sin respuesta declarada» sigue) · 2026-10-16`

- **Verificación ejecutada** (2026-10-16): `pytest -q tests/test_panel_review_panel_ui.py tests/test_panel_review_ui.py` → `67 passed`; `tests/test_panel_review_panel_server.py tests/test_panel_review_server.py` + `tests/test_panel_plan_ui.py tests/test_panel_iniciativas_ui.py tests/test_panel_fix4.py` → 0 failed. Navegador (`verify-p5.mjs`, servido `--review-panel` sobre copia de fixture): Edge 155 y Firefox 142 (`channel msedge`; servidor con `--review-panel` sobre copia de fixture y `.claude/plan-review` temporal): abrir no escribe, botón por teclado, comentario, «pedir correcciones», respuesta simulada por la CLI bajo el comentario (disposición y verify-result), «obsoleta por cambio de versión» tras tocar el plan, nueva decisión «aprobada v2», mismo texto en tarjeta y cabecera; 0 violaciones de CSP, 0 externas, 0 errores; `file://` sin controles ni `api/review`.

- **Changelog**: Desde la página Plan se puede abrir una revisión, comentar por sección y decidir; el estado de revisión de cada iniciativa se ve en su tarjeta y en la cabecera del Plan, con las respuestas del agente bajo cada comentario.

**Notas**: Desviaciones: `build_panel.py`/`serve_panel.py` pasan `data-initiative-id` al Plan y un marcador `#iniciativas-revision` (solo con `--review-panel`) para que Iniciativas pida `api/review-summary` sin 404 en consola; el `fetch` vive en `panel-review.js` (`PanelReview.leerResumen`; `panel_pages.LIVE_SCRIPTS` lo carga también en Iniciativas, omitido sin ámbito), porque `test_panel_iniciativas_ui` y… Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `2dc3c72a6e01`.

### T-28 — Documentación de F2 (Inicio, Iniciativas, Plan, `ledger-view`, `Cerrada` y revisión del plan desde el panel)

- **Descripción**: Documenta las tres páginas, las API `api/cartera` y `api/plan-*`, la relación `plugin-panel` → `build_dashboard` y `plugin-panel` → `ledger-view` en CONTRACTS, y el campo `Cerrada`. **Ampliada por la enmienda (R-5 de `design.md` §8.8):** documenta el modo `--review-panel`, la operación `plan-review.py summary`, las rutas `api/review-summary`, `api/review-current/<id16>` y `api/review-open/<id16>`, la excepción de escritura de la política de solo lectura y el `plan-ok` que nunca abre el navegador; actualiza E49-E51 de CONTRACTS (E51 ya no es «selección fija») y añade la arista «panel resume revisiones» con su Puerta (T-55/T-56).
- **Estado**: completado
- **Tiempo humano**: est. 2,4h (1,8h + 0,6h de la enmienda) · real —
- **Tiempo IA (ejec.)**: est. 0,5h (0,4h + 0,1h) · real 0,2h (estimado)
- **Supervisión**: est. 0,15h (≈25 % IA) · real 0,05h (estimado, 25 % de la IA)
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-18..T-27, T-55..T-58
- **Tipo**: docs
- **Archivos**: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `agent-kits/shared/README.md`, `skills/plugin-panel/SKILL.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 scripts/lint_plugin.py` → exit 0 (ninguna fila de CONTRACTS sin Puerta) · `grep -n "review-panel" docs/PLUGIN-PANEL.md docs/en/PLUGIN-PANEL.md` → al menos una coincidencia en cada fichero · lectura: espejos EN iguales en contenido

**Criterios de aceptación**
- [x] Aristas nuevas en CONTRACTS con su Puerta ejecutable (test de T-17 y T-21) y sus «Piezas que describen».
- [x] ES y EN en el mismo cambio.
- [x] CA-44 (documentación de la enmienda): `docs/PLUGIN-PANEL.md` y su espejo EN describen `--review-panel`, `summary`, las tres rutas nuevas y la excepción de escritura; E49-E51 actualizados y la arista «panel resume revisiones» con Puerta (test de T-55 y de T-56) y «Piezas que describen»; `agent-kits/shared/README.md` lista `summary`.

**Subtareas**
- [x] Redactar y espejar.

- **Changelog**: Documentados Inicio, Iniciativas y Plan del panel, el campo Cerrada del ledger y la revisión del plan desde el panel (`--review-panel`), con su contrato en la matriz de aristas.
- **Cerrada**: 2026-10-16
- **Verificación ejecutada** (2026-10-16): `lint_plugin.py` → 0 errores (8 avisos previos: nombres genéricos y `/health`, `/skills`; ninguno de CONTRACTS) · `grep review-panel` → 5 líneas ES y 5 EN · `export-interop.py --check` → 88 ficheros al día · `scope-check --base 14ef84b` → exit 0 · `ledger-lint` → 0 incoherencias.

**Notas**: TDD n/a: prosa. Formato de arista en `docs/agents/CONTRACTS.md:96-103` (E30-E37).
 Desviaciones: aristas nuevas E56 (panel→build_dashboard, T-17), E57 (panel→ledger-view, T-21) y E58 (panel resume revisiones, T-55/T-56); E49-E51 actualizados y E51 con Puerta ejecutable. `skills/plugin-panel/SKILL.md` añadido a `Archivos` (flag `--review-panel`, +2 líneas, sin tocar `commands/`; `interop --check` verde). La UI de T-58 se describe según spec/design y `panel-review.js` vigente (cuadra al 2026-10-16).

### T-29 — Cierre de la Fase 2: revisión de dos lentes y revisión visual del usuario (M-02)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals en verde; revisión de dos lentes sobre el diff de la fase; bucle acotado a 3 con Minor al backlog; el usuario revisa Inicio, Iniciativas y Plan en el navegador (M-02). **Ampliada por la enmienda (R-6 de `design.md` §8.8):** la **lente C de seguridad es obligatoria** en esta revisión (la fase añade la vía de escritura de `api/review-open`; el orquestador la fuerza aunque `review-lens-select.py` no la marque) y M-02 incluye **abrir, comentar y decidir una revisión desde la página Plan**.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 3,0h (1,8h + 1,2h de la enmienda) · real —
- **Tiempo IA (ejec.)**: est. 9,5h (5,4h + 4,1h de la enmienda) · real — (revisión + corrección, f = 1,0, incluida la parte de `Cerrada` y la lente C sobre T-55..T-58)
- **Supervisión**: est. 3,85h (≈25 % IA + 1,5h de revisión manual: 1h + 0,5h de M-02 ampliado) · real —
- **Previsión IA**: 4,35 M in / 707k out tok · 66,48 €
- **Dependencias**: T-17..T-28, T-55..T-58
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`, `agent-kits/shared/project-pieces.py`, `tests/test_project_pieces.py` (CI-1 de M-02)
- **Cubre (tests)**: M-02
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_ledger_lint.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py agent-kits/shared/test_ledger_view.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - `python3 -m pytest -q agent-kits/shared/test_plan_review_summary.py tests/test_panel_review_panel_server.py tests/test_panel_review_panel_ui.py tests/test_plan_review_caller.py` → `0 failed` (CA-54: las suites de `plan-review.py` y `tests/test_panel_review_*` sin cambiar expectativas)
  - lectura: «Revisión de dos lentes — intento N: …» de la Fase 2 con la lente C ejecutada (obligatoria) y sin Critical ni Important abiertos, y «Revisión visual del usuario — Fase 2: aprobada AAAA-MM-DD»

**Criterios de aceptación**
- [x] CA-44 de la Fase 2.
- [x] Revisión cerrada en ≤ 3 intentos.
- [x] [GWT] CA-47 y CA-48 (enmienda): la lente C de seguridad se ejecuta sobre el diff de la fase aunque `review-lens-select.py` no la marque, y no deja Critical ni Important abiertos sobre `api/review-open`, la correspondencia id16 y el registro de ids.
- [x] El usuario aprueba M-02, incluido abrir, comentar y decidir una revisión desde la página Plan.

**Subtareas**
- [x] Suites y puertas; `adversarial-review`; M-02. **Ampliada por la enmienda 2026-10-15:** `adversarial-review` con A + B + **C obligatoria** (+ D si `review-lens-select.py` la activa); M-02 con la revisión desde el Plan.

**Notas**: **2026-10-16:** revisión cerrada en 3 intentos + verificación dirigida de fix3 (0 gaps nuevos); deuda TDD F2-1/I2-1 aceptada por el usuario (2026-10-16); CA-10 (F2-23) enmendada en la spec por decisión del usuario (2026-10-16); **M-02 aprobada por el usuario (2026-10-20).** Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `7bc9f7313123`.

- **Verificación ejecutada** (2026-10-20, HEAD `3ca861b`, `.venv` del repo, pytest 9.1.1): suites de la Verificación juntas (incluidas `test_plan_review_summary.py` y `test_plan_review_caller.py`) → `3 failed, 1604 passed, 20 skipped` en 676 s; los 3 fallos son de plazo (`test_sixty_four_records_fit_the_envelope`, `test_a_really_expired_deadline_gives_partial_with_what_was_read`, `test_the_plan_rereads_respect_the_guard`) con la máquina cargada (lint, evals, interop y scope-check en paralelo); `agent-kits/shared/test_plan_review_summary.py` en solitario → `19 passed`; `plan-review.py` y su test sin cambios en `9c47821..3ca861b` · `lint_plugin.py` → exit 0 («10 agentes · 0 errores · 8 avisos») · `evals/check.py` → 0 errores · `export-interop.py --check` → «88 ficheros al día» · `scope-check.py --base 14ef84b` → exit 0, 0 fuera de alcance · lectura: intento 3 de la Fase 2 con lente C y verificación dirigida de fix3 sin gaps; «Revisión visual del usuario — Fase 2: aprobada 2026-10-20».

---

## Fase 4 — Memoria, Catálogo y Diagnóstico

**Estado**: completado (2026-10-20) · **Estimado**: 26,4h humanas · 7,2h IA · **Real**: — · **Coste est.**: 1.370 € referencia · ≈ 190 € ejecución · **Tokens est.**: 3,83 M

Se ejecuta ANTES que la Fase 3 (orden de la evaluación). Criterios de la spec: CA-22 a CA-31. Fuentes en solo lectura; si una no trae un dato por su `--json`, se muestra «sin datos» y no se amplía su contrato (`doctor.py`, `journal.py` y `knowledge-find.py` son hotspots).

### T-30 — Memoria: entradas por tipo, estado y área (y `api/memoria`)

- **Descripción**: `memoria.html` muestra un gráfico y una tabla de entradas por tipo (ADR, gotcha, lección) y estado (`aceptada · propuesta · obsoleta`), filtrables por área. La proyección sale de `knowledge-view.snapshot`; en servido, por `api/memoria` (GET, ≤ 64 KiB) porque `api/memory` solo admite `search`/`show`/`related`.
- **Estado**: completado
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`, `tests/test_panel_memoria_fix1.py` (ronda fix1 de la revisión de F4), `tests/test_panel_memory_server.py`, `tests/memoria_fixture.py`, `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/assets/panel.css`, `tests/test_panel_fix4.py`, `tests/test_panel_export.py`, `tests/test_panel_server.py`
- **Cubre (tests)**: API-06, E2E-20
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py tests/test_panel_memory_server.py` → `passed` (conteos iguales a `knowledge-find.py --json` sobre la fixture; filtro por área)

**Criterios de aceptación**
- [x] CA-22: tipo × estado con gráfico y tabla; filtro por área con teclado.
- [x] `api/memory` (POST) no cambia; `api/memoria` respeta 64 KiB y la redacción antes de recortar.

**Subtareas**
- [x] RED; proyección, ruta y página.

- **Changelog**: Memoria muestra un gráfico y una tabla de entradas por tipo y estado, con filtro de área por teclado.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: T-29 sigue en-progreso por M-02 aplazado por el usuario; no bloquea F4 (decisión del orquestador). Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `0fdd1d9608a7`.

### T-31 — Memoria: bandeja del curador de solo lectura

- **Descripción**: La bandeja muestra el número y la lista de candidatos de `docs/knowledge/candidates/` por estado (`pending`, `needs_changes`, `rejected`) y lo aprobado en `docs/knowledge/approved/`. Sin acciones.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-30
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`
- **Cubre (tests)**: E2E-20
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py` → `passed` (ningún botón ni formulario de aprobar/rechazar/editar en el DOM)

**Criterios de aceptación**
- [x] CA-23: conteo y lista por estado; ninguna acción del curador (ADR-018).

**Subtareas**
- [x] RED; bandeja.

- **Changelog**: Memoria muestra la bandeja del curador (pendientes, cambios pedidos, rechazados y aprobadas) en solo lectura.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: dueño único de las decisiones: `agent-kits/shared/knowledge-curation.py` (CONTRACTS E53); el panel solo lee. Bandeja sin botones, formularios ni enlaces (test + navegador).

### T-32 — Memoria: línea de tiempo con sucesores y «vigente»

- **Descripción**: Línea de tiempo de entradas por fecha con su cadena de sucesión; las que rigen hoy (sin sucesor, no obsoletas) llevan «vigente».
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-30
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`
- **Cubre (tests)**: E2E-20
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py` → `passed` (cadena A→B→C: solo C «vigente»; obsoleta sin sucesor: no «vigente»)

**Criterios de aceptación**
- [x] CA-24: orden por fecha, cadena visible y «vigente» en texto.

**Subtareas**
- [x] RED; línea de tiempo.

- **Changelog**: Memoria muestra una línea de tiempo por fecha con la cadena de sucesión y marca «vigente» las entradas que rigen hoy.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: sucesión desde `knowledge-find.py` (`--related`, `agent-kits/shared/knowledge-find.py:102`). «vigente» = sin sucesor y no obsoleta, calculado con `knowledge-find` (`_relaciones_sucesion`).

### T-33 — Memoria: relaciones de UNA entrada en un SVG pequeño y lista textual

- **Descripción**: Al seleccionar una entrada se dibuja un grafo pequeño en SVG propio, centrado en ella, con las mismas aristas que `knowledge-find.py --related <ID> --json` (sucesión, misma iniciativa, misma área) y una lista textual equivalente navegable por teclado. Un salto, nunca el grafo completo.
- **Estado**: completado
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-30
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-memoria.js`, `skills/plugin-panel/assets/panel-graph.js`, `tests/test_panel_memoria_ui.py`
- **Cubre (tests)**: E2E-05, E2E-21
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py` → `passed` (aristas iguales a la salida real de `--related --json`; ningún nodo a 2 saltos; la lista textual tiene las mismas aristas)

**Criterios de aceptación**
- [x] CA-25: mismas aristas que `--related`; un salto; lista textual equivalente.
- [x] CA-37/CA-39: el SVG lleva nombre accesible; la lista es la alternativa de teclado.
- [x] Usa la operación `related` existente de `api/memory`.

**Subtareas**
- [x] RED; SVG con `createElementNS` (sin `innerHTML`).

- **Changelog**: Memoria dibuja un grafo pequeño de una entrada y sus relaciones a un salto, con una lista de texto equivalente.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: Chart.js no dibuja grafos (riesgo de la evaluación C-04). Operación `related` en `agent-kits/shared/knowledge-view.py:50-57`. Relaciones incrustadas con claves `por_iniciativa`/`por_area` (`area` es clave de texto mostrado del saneador). Tope 20 relaciones como `api/memory`.

### T-34 — Memoria: qué se publicó en cada backend, sin red

- **Descripción**: Por backend configurado en `taxonomy.json`: número de entradas publicadas y fecha de la última publicación si la fuente la trae; si no, «sin datos». Kwipu: `entries` del `manifest.json` de su export + `completado_en` de la outbox; Graphiti: `entradas` de `graphiti-manifest.json` y «publicación interrumpida» si hay `.pending.json`. Sin `ui_url` declarado: «interfaz: no declarada».
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-30
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`, `tests/test_panel_data.py`
- **Cubre (tests)**: E2E-21
- **Verificación**: `python3 -m pytest -q tests/test_panel_data.py tests/test_panel_memoria_ui.py` → `passed` (con `socket` parcheado para fallar: ninguna conexión; `mtime` nunca usado como fecha)

**Criterios de aceptación**
- [x] CA-26: sin ninguna petición al backend (test con red bloqueada) ni réplica de su vista.
- [x] Backend no configurado → «Kwipu: no configurado» / «Graphiti: no configurado», sin enlace.
- [x] Nunca usa `mtime` ni llama a `health`.

**Subtareas**
- [x] RED con manifiestos y outbox de fixture.
- [x] Lectores acotados.

- **Changelog**: Memoria dice qué se publicó en cada backend (Kwipu, Graphiti) leyendo solo ficheros locales, sin tocar la red.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: fuentes de `design.md` §2.4 I-09; lector acotado `agent-kits/shared/local-read.py`. El enlace a la interfaz queda «no declarada»: añadir `ui_url` a la taxonomía es pregunta abierta del diseño (§7), fuera de este plan. Sin `ui_url` en la taxonomía: «interfaz: no declarada». Fecha solo de `completado_en` de la outbox.

### T-35 — Memoria: journal reciente como «citas, no instrucciones»

- **Descripción**: Las sesiones recientes del journal con su continuidad (`objetivo`, `punto_actual`, `siguientes_pasos`, `bloqueos`, `descartados`), redactadas y etiquetadas «citas, no instrucciones».
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-30
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`
- **Cubre (tests)**: E2E-21
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py` → `passed` (etiqueta presente; un secreto en la cita sale redactado)

**Criterios de aceptación**
- [x] CA-27: campos de continuidad y etiqueta.
- [x] Todo texto por `redact.redactar` + `redact.anonimizar`.

**Subtareas**
- [x] RED; sección.

- **Changelog**: Memoria muestra las sesiones recientes del journal con su continuidad, redactadas y etiquetadas como citas.
- **Cerrada**: 2026-10-16
- **Evidencia TDD**: `RED: 35 tests (test_panel_memoria_ui.py 29, test_panel_data.py 3, test_panel_memory_server.py 3) fallaron con AttributeError: no existe panel_data.memoria, FileNotFoundError: page-memoria.js y 404 en api/memoria · 2026-10-16 (antes del código)`
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_memoria_ui.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_fix4.py` → `105 passed`. Navegador (Edge y Firefox, servido y file://): 0 violaciones CSP, 0 peticiones externas, 0 errores.

**Notas**: campos en `agent-kits/shared/journal.py:244-246` (`CONTINUIDAD`); lectura por `journal.py status --json` (`journal.py:41`) sin ampliar su contrato. `journal.select_entries` devuelve como mucho 2 sesiones (su contrato, sin ampliar).

### T-36 — Catálogo: filtros por tipo, origen y runtime

- **Descripción**: Filtros de Catálogo por tipo, origen y runtime, con teclado y ratón; lista y conteos cambian en consecuencia. `build_panel.py --json` sigue igual al golden (CA-28).
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,3h (estimado)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-catalogo.js`, `tests/test_panel_catalogo_ui.py`, `tests/test_panel_contract_golden.py`, `skills/plugin-panel/scripts/build_panel.py` (zonas de desglose), `skills/plugin-panel/assets/panel.css`
- **Cubre (tests)**: E2E-05, E2E-22
- **Verificación**: `python3 -m pytest -q tests/test_panel_catalogo_ui.py tests/test_panel_contract_golden.py` → `passed`

**Criterios de aceptación**
- [x] CA-29: filtros combinables; conteos coherentes; operables con teclado.
- [x] CA-28: `--json` igual al golden.

**Subtareas**
- [x] RED; filtros.

- **Cerrada**: 2026-10-16
- **Changelog**: Catálogo suma al buscador un desglose accesible por tipo, origen y runtime que se actualiza con cada filtro, con teclado y con ratón.
- **Evidencia TDD**: `RED: 4 tests de test_panel_catalogo_ui.py fallaron (AssertionError: sin desglose «Por origen»/«results-detail» ausente) · 2026-10-16 (antes del código)`.
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_catalogo_ui.py tests/test_panel_contract_golden.py tests/test_plugin_panel.py` → `117 passed, 2 skipped`. Edge y Firefox, servido y `file://`: 0 CSP, 0 externas, 0 errores.

**Notas**: página de T-09. T-29 sigue en-progreso (M-02 aplazada por el usuario a la revisión final); no bloquea. «Origen» = ámbito de extensiones (proyecto/usuario/local); el bundle no lo declara. Filtros solo del cliente: `--json` igual al golden.
### T-37 — Diagnóstico: veredicto en texto, fecha, alcance y resumen

- **Descripción**: Una fila por comprobación con su veredicto ✅/⚠️/❌ también en texto, su fecha y su alcance, y un resumen con el número de cada veredicto; sin informe, de otro proyecto u otro formato, «sin informe» o el motivo del rechazo y el comando para generarlo.
- **Estado**: completado
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real 0,3h (estimado)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-diagnostico.js`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_diagnostics.py`, `skills/plugin-panel/scripts/build_panel.py` (HTML de filas y rechazo), `skills/plugin-panel/assets/panel.css`
- **Cubre (tests)**: E2E-23
- **Verificación**: `python3 -m pytest -q tests/test_panel_diagnostics.py` → `passed` (texto «OK/aviso/error» junto al icono; resumen con los tres contadores; rechazo con el comando)

**Criterios de aceptación**
- [x] CA-30: fila por comprobación, veredicto en texto, fecha, alcance y resumen.
- [x] CA-31: no ejecuta `doctor` ni busca informes.

**Subtareas**
- [x] RED; página.

- **Cerrada**: 2026-10-16
- **Changelog**: Diagnóstico muestra cada comprobación con su veredicto en texto (OK, aviso, error) junto al icono, su fecha y alcance, y un resumen con los contadores; sin informe da el motivo y el comando para generarlo.
- **Evidencia TDD**: `RED: 10 tests nuevos de test_panel_diagnostics.py fallaron (AssertionError: sin diagnostic-verdict, diagnostic-summary ni diagnostic-command) · 2026-10-16 (antes del código)`.
- **Verificación ejecutada** (2026-10-16): `pytest tests/test_panel_diagnostics.py` → `44 passed`. Navegador (Edge y Firefox, servido y `file://`, informe real, sin informe y otro proyecto): 0 CSP, 0 externas, 0 errores.

**Notas**: `page-diagnostico.js` sin cambios (la fila ya se filtra por `data-state`); el HTML sale de `build_panel.py`. Fecha y alcance son del informe (no hay fecha por fila en el contrato de doctor). Comando: el de `commands/doctor.md`. Proyección `doctor.py --panel-json` (`agent-kits/shared/doctor.py:87-88`, `:2795`); validador de CONTRACTS E30.
### T-38 — Documentación de F4 (Memoria, Catálogo, Diagnóstico)

- **Descripción**: Documenta las tres páginas, `api/memoria` y la regla «sin datos antes que ampliar contratos de hotspots».
- **Estado**: completado
- **Cerrada**: 2026-10-16
- **Changelog**: Documentadas las páginas Memoria, Catálogo y Diagnóstico del panel, `api/memoria` y la regla «sin datos» antes de ampliar contratos.
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-30..T-37
- **Tipo**: docs
- **Archivos**: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`, `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/references/**`
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_skill_size.py` → `passed` · `python3 scripts/lint_plugin.py` → exit 0 · lectura: espejo EN

**Criterios de aceptación**
- [x] Arista `serve_panel` → `api/memoria` declarada con su Puerta.
- [x] ES y EN en el mismo cambio; `SKILL.md` ≤ 200 líneas.

**Subtareas**
- [x] Redactar y espejar.

**Evidencia TDD**: TDD n/a: prosa.

**Verificación ejecutada** (2026-10-16): test_skill_size + test_lint_plugin → 30 passed; lint_plugin exit 0 (0 errores, 8 avisos previos); export-interop --check 88 ficheros al día; SKILL.md 125 líneas; espejo EN revisado

**Notas**: aristas E59/E60 nuevas en CONTRACTS (sesenta). E42 describe `commands/plugin-catalog.md`, `skills/plugin-panel/SKILL.md`, `docs/PLUGIN-PANEL.md` (+EN).

### T-39 — Cierre de la Fase 4: revisión de dos lentes y revisión visual del usuario (M-03)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals; revisión de dos lentes; bucle acotado a 3; el usuario revisa Memoria, Catálogo y Diagnóstico en el navegador (M-03).
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 3,6h · real — (revisión + corrección, f = 1,0)
- **Supervisión**: est. 1,9h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 1,65 M in / 268k out tok · 25,19 €
- **Dependencias**: T-30..T-38
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`, `agent-kits/shared/ledger-archive.py` (archivado de Notas: tope 256 KiB), `agent-kits/shared/test_ledger_archive.py` (archivado de Notas: tope 256 KiB), `agent-kits/shared/README.md` (archivado de Notas: tope 256 KiB)
- **Evidencia TDD**: modo D de `ledger-archive.py`: `RED: 7 tests nuevos de agent-kits/shared/test_ledger_archive.py fallaron con KeyError: 'notas' / --notas-max desconocido · 2026-10-16 (antes del código)`; verde 22 passed.
- **Cubre (tests)**: M-03
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: «Revisión de dos lentes — intento N: …» de la Fase 4 sin Critical ni Important abiertos y «Revisión visual del usuario — Fase 4: aprobada AAAA-MM-DD»

**Criterios de aceptación**
- [x] CA-44 de la Fase 4.
- [x] Revisión cerrada en ≤ 3 intentos.
- [x] El usuario aprueba M-03.

**Subtareas**
- [x] Suites y puertas; `adversarial-review`; M-03.

**Notas**: la Lente A comprueba que ningún hotspot (`doctor.py`, `journal.py`, `knowledge-find.py`) cambió de contrato. **2026-10-20:** M-03 aprobada por el usuario en el navegador (Memoria, Catálogo y Diagnóstico, panel servido).

- **Verificación ejecutada** (2026-10-20, HEAD `3ca861b`): la misma tanda que T-29 (cubre todas las suites de esta Verificación) → `3 failed, 1604 passed, 20 skipped`; los 3 fallos son de plazo en `test_plan_review_summary.py`, fuera de esta Verificación, y en solitario pasan (`19 passed`) · `lint_plugin.py` → exit 0 · `evals/check.py` → 0 errores · `export-interop.py --check` → «88 ficheros al día» · `scope-check.py --base 14ef84b` → exit 0 · lectura: intento 2 de la Fase 4 sin Critical ni Important; «Revisión visual del usuario — Fase 4: aprobada 2026-10-20».

---

## Fase 3 — Agentes en vivo + cierre transversal

**Estado**: en-progreso · **Estimado**: 45,6h humanas · 23,4h IA · **Real**: 3,57h IA medida (T-45..T-53 + fix1 1,29h; T-40..T-41 sin medir; falta T-54) · **Coste est.**: 2.444 € referencia · ≈ 506 € ejecución · **Tokens est.**: 12,44 M

Última fase. Criterios de la spec: CA-04, CA-15 a CA-21 y CA-42 (eventos); además, el cierre transversal C-05. **Lente C obligatoria** en toda tarea de captura (condición 4 de la evaluación). Valores de diseño: 0 ms síncronos añadidos (O5), historial de 500 eventos / 256 KiB / 24 h, entrada ≤ 2 MiB, resumen ≤ 160.

### T-40 — Puerta de entrada de F3: condiciones de la evaluación y latencia base

- **Descripción**: Antes de tocar el hook, comprueba las cuatro condiciones de la evaluación y mide la latencia del hook actual. No escribe código del producto.
- **Estado**: completado
- **Cerrada**: 2026-10-16
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-39
- **Cubre (tests)**: —
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Verificación**: lectura: en `Notas` de esta tarea, las cuatro condiciones marcadas con su evidencia (sección de `design.md`, respuesta del usuario con fecha, URL de la doc de Codex, configuración de la Lente C) y las líneas `Hooks: PostToolUse:… (Nms)` del log de Claude Code con la latencia base

- **Changelog**: Sin cambio visible: comprueba las condiciones de entrada de Agentes en vivo y mide la latencia base del hook de actividad.

**Criterios de aceptación**
- [x] Condición 1: `design.md` tiene la sección «estados intermedios y su recuperación» de `events.json` (bloqueo ocupado, CAS fallido, escritura cortada, eventos asíncronos fuera de orden). Si no está, se pide al architect antes de seguir (el planner no la escribe).
- [x] Condición 2: el usuario confirma o cambia I-05 (0 ms síncronos) e I-03 (500 / 256 KiB / 24 h); la respuesta y su fecha quedan en `Notas`.
- [x] Condición 3: la evidencia de Codex (PreToolUse/PostToolUse sin identificador de subagente) se cita con URL y fecha de consulta.
- [x] Condición 4: la Lente C se despacha en T-54 aunque `review-lens-select.py` no la active.
- [x] Latencia base medida y anotada.

**Subtareas**
- [x] Revisar `design.md` §1-§2.4.
- [x] Preguntar al usuario I-03/I-05 (valores del diseño por defecto).
- [x] Medir y anotar.

- **Evidencia TDD**: TDD n/a: puerta de entrada, sin código del producto.
- **Verificación ejecutada**: (1) `design.md` §2.5 «Estados intermedios y su recuperación» (architect, `d448942`). (2) El usuario acepta I-05, I-03 y P-EI-1..P-EI-3 (2026-10-16, «acepto la decisión de 1 a 4»; anotado en §2.5). (3) https://learn.chatgpt.com/docs/hooks (redirección de developers.openai.com/codex/hooks, consultada 2026-10-16): `PreToolUse`/`PostToolUse` sin `agent_id`/`agent_type` (solo `SubagentStart`/`SubagentStop`), los subagentes usan el `session_id` del padre, sin duración; `async` admitido salvo MCP. (4) Lente C obligatoria en T-54 (orquestador; T-54 ya lo exige). (5) Latencia base (`run-hook.mjs` real, 12 ejecuciones, Windows): `PostToolUse` `progress-line.sh` p50 589 ms / p90 714 ms (síncrono); `SubagentStop` `agent-activity` con captura desactivada p50 1.018 ms / p90 1.085 ms (lanza Python: lo corrige T-46).

**Notas**: condiciones en `evaluation.md` «Recomendación». Medición de I-05 según `design.md` §2.4 («líneas `Hooks: PostToolUse:… (Nms)`»). Presupuesto actual del hook en `hooks/run-hook.mjs:26`.

### T-41 — Proyección pura de runs, ventanas y eventos en `agent-activity.py`

- **Descripción**: Añade a `agent-kits/shared/agent-activity.py` las constantes del historial (500 eventos, 256 KiB, 24 h, entrada 2 MiB, resumen 160) y la proyección pura de runs (`en curso` / `sin señal reciente` con duración congelada / `respuesta terminada`), ventanas de atribución (`abierta` → `cerrada` | `reemplazada` | `caducada`) y la regla de atribución a `T-XX`.
- **Estado**: completado
- **Cerrada**: 2026-10-16
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-40
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity.py`, `agent-kits/shared/test_agent_activity.py`
- **Cubre (tests)**: E2E-17, E2E-18
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_agent_activity.py` → `passed` (incluye: run con 61 s → «sin señal reciente» y duración congelada; dos ventanas abiertas → «sin atribuir»; `lote-<n>` nunca atribuye; `cerrada → abierta` sin `start` rechazado)

- **Changelog**: El historial de agentes calcula runs, ventanas de atribución y eventos con reglas puras: tras 60 s sin señal un run queda «sin señal reciente» y nunca «terminado» inferido.

**Criterios de aceptación**
- [x] CA-18: atribución solo con exactamente una ventana abierta en el run o, si no tiene, en la sesión padre; si no, «sin atribuir».
- [x] CA-19: más de 60 s → «sin señal reciente»; nunca «terminado» ni «muerto» inferidos.
- [x] CA-21: el recorte por antigüedad descarta el más antiguo y cuenta `recortado`.
- [x] `FRESH_SECONDS` (60) y `MAX_OBSERVATIONS` (64) del snapshot no cambian.

**Subtareas**
- [x] RED en `test_agent_activity.py`.
- [x] Constantes y proyecciones puras.

- **Evidencia TDD**: RED: test_agent_activity.py (26 tests nuevos) falló con AttributeError: sin MAX_EVENTS/project_runs/apply_window/attribute/trim_events · 2026-10-16 (antes del código)
- **Verificación ejecutada**: `pytest agent-kits/shared/test_agent_activity.py` → 53 passed (26 nuevos: run 61 s → sin señal reciente con duración congelada; dos ventanas → sin atribuir; lote nunca atribuye; cerrada→abierta rechazado).

**Notas**: patrón de proyección pura con `now` inyectado en `agent-kits/shared/agent-activity.py:48` (`project_activity`); constantes en `:9-10`. Estados de `design.md` §1 «Invariantes». Decisión: `recortado` cuenta solo el recorte por tope (500/256 KiB); la retención de 24 h purga sin contar. Cuarentena de 5 s en `attribute` (P-EI-2 i).

### T-42 — Resumen redactado por lista blanca y `Authorization: Basic` en el redactor

- **Descripción**: Resumen del argumento por herramienta en lista blanca (`design.md` §2.4 I-07: 1.ª línea del comando, rutas relativas, patrón + ruta, host, tipo de subagente, nombre de skill, «—» para MCP y desconocidas), en el orden fijo redactar → anonimizar → quitar controles → recortar a 160. Amplía `_SECRETOS_RE` con `Authorization: Basic …` en el canónico y en su copia declarada.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 1,17h (medido: fix1, ventana común con el código y los RED de los 8 gaps de fix1)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-41
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/redact.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_redact.py`, `tests/test_agent_activity_store.py`, `tests/test_copias_declaradas.py`
- **Cubre (tests)**: E2E-18
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_redact.py tests/test_agent_activity_store.py tests/test_copias_declaradas.py` → `passed` (corpus de secretos de `redact.py` + `Authorization: Basic`: ningún secreto en el resumen persistido ni mostrado)

- **Changelog**: Los resúmenes de herramientas del panel y el redactor ocultan también las cabeceras «Authorization: Basic …», y nunca muestran rutas absolutas, usuario ni correos.

**Criterios de aceptación**
- [x] CA-17: el resumen persistido y el mostrado pasan por `redact.py` y no contienen el secreto (corpus completo).
- [x] CA-16: nunca contenido de ficheros, salidas, prompts ni chain-of-thought; MCP y desconocidas → «—».
- [x] CA-41: rutas relativas al proyecto, sin home, usuario ni correos.
- [x] El bloque replicado de `redact.py` y su copia en `journal.py` siguen idénticos.

**Subtareas**
- [x] RED con el corpus.
- [x] Lista blanca y orden fijo; ampliar `_SECRETOS_RE` en los dos sitios.

- **Evidencia TDD**: RED: test_agent_activity_store.py (≈120 casos de resumen) falló con AttributeError: sin `summarize`; test_redact.py `test_authorization_basic_*` (6) falló con la cabecera sin redactar · 2026-10-16 (antes del código). fix1 (C-1) RED: test_redact.py::test_c1_clave_sensible_tras_prefijo… (5), ::test_c1_curl_usuario_y_clave… (6), ::test_c1_mysql_clave_pegada… (3) y ::test_c1_idem_en_el_respaldo_de_journal fallaron con el secreto intacto (`DB_PASSWORD=Hunter2xyz! psql -h db` sin cambios); test_agent_activity_store.py::test_c1_prefixed_and_argument_secrets… falló con el secreto en events.json · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest agent-kits/shared/test_redact.py tests/test_agent_activity_store.py tests/test_copias_declaradas.py` → 204 passed, 1 skipped (corpus de secretos + Authorization: Basic; bloque replicado de journal.py idéntico).
  - fix1 (C-1): `pytest agent-kits/shared/test_redact.py tests/test_copias_declaradas.py` → 118 passed (bloque replicado idéntico; casos lineales nuevos < 1,5 s) · `pytest agent-kits/shared/test_journal.py` → 192 passed, 10 skipped · `test_agent_activity_store.py` (con el resto de fix1) → verde · usuarios de `redactar` (training-data, receipts, curación, plan-review, privacidad) → verdes salvo 6 rojos de MAX_PATH de Windows ajenos (`test_case_recorder …gap87…`, `test_propose_from_case …long_gold…` ×5: `FileNotFoundError` en rutas > 260).

Decisión fix1 (C-1): sin `\b` a la izquierda en `_ASIGNACION_RE` (el final se mantiene: `my_token_count=`/`tokens=` no casan); `curl -u|--user usuario:clave` y `mysql*/mariadb* -p<clave>` solo dentro del mismo comando (segmento hasta `\n|;&`), así `sort -u`, `mkdir -p`, `ssh -p2222` o `docker -u 1000:1000` no se tocan; idempotente; `es_clave_sensible` no cambia.

**Notas**: `_SECRETOS_RE` en `agent-kits/shared/redact.py:35`; copia declarada en `agent-kits/shared/copias.json:297-310` (canónico `redact.py`, respaldo `journal.py`). Precedente de 160 caracteres en `skills/plugin-panel/scripts/serve_panel.py:139`. Lente C. `anonimizar` ya existía (T-04). El host de WebFetch se extrae por regex, sin `urllib` (la puerta de red de test_graphiti_security lo marca). Un PEM sin cierre se tapa entero antes de recortar.

### T-43 — Almacén `events.json`: anillo acotado, CAS, retención y opt-out sin escritura

- **Descripción**: `agent-activity-store.py` añade `events.json` al directorio propio (inventario de 4 a 5 nombres + `.lock`): `runs` (≤ 64), `ventanas` (≤ 64) y `events` (anillo 500 / 256 KiB / 24 h), reemplazo atómico con CAS como `snapshot.json`, `recortado`, `descartados_por_tamano` sin identidad y tope de entrada de 2 MiB solo en memoria. Sin `sesion.actividad: true` no escribe nada.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 4,2h · real —
- **Tiempo IA (ejec.)**: est. 1,0h · real 0,00h (medido: fix1, solo el cierre; código y RED dentro de la ventana común de T-42-fix1)
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 457k in / 74k out tok · 7,00 €
- **Dependencias**: T-42
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_store.py`, `tests/test_agent_activity_git.py`, `tests/test_graphiti_security.py`, `agent-kits/shared/local-state.py` (añadido: espera 0 y un intento), `agent-kits/shared/test_local_state.py` (añadido)
- **Cubre (tests)**: E2E-19
- **Verificación**: `python3 -m pytest -q tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py` → `passed` (opt-out: el directorio de estado no cambia; 501 eventos → 500 y `recortado: 1`; entrada de 2 MiB + 1 → contador; escrituras concurrentes sin pérdida de integridad)

- **Changelog**: El historial de actividad se guarda en un anillo acotado (500 eventos o 256 KiB, 24 h) que solo se escribe con `sesion.actividad: true` y se recupera solo de escrituras cortadas.

**Criterios de aceptación**
- [x] CA-20: con `sesion.actividad` ausente o `false`, ningún fichero nuevo ni modificado (test con huella del directorio).
- [x] CA-21: tope y retención; la escritura fallida no rompe nada y el llamante sale con 0.
- [x] Estados intermedios de la condición 1 cubiertos por test: bloqueo ocupado (evento perdido, sin reintento que añada latencia), CAS fallido, escritura cortada.
- [x] `snapshot.json` y su contrato (60 s, 64 filas, 64 KiB, `api/activity`, `doctor`) no cambian.
- [x] Nueva huella `sha256_lf` de `agent-activity-store.py` y `redact.py` en sus `dependencies` en `_CARGAS_LOCALES_REVISADAS`, tras revisión.
- [x] `.gitignore` del directorio propio sigue cubriendo el fichero nuevo.

**Subtareas**
- [x] RED: opt-out, tope, retención, concurrencia.
- [x] Inventario, CAS y anillo.
- [x] Huella revisada.

- **Evidencia TDD**: RED: 43 tests nuevos de test_agent_activity_store.py/test_agent_activity_git.py y 2 de test_local_state.py fallaron con AttributeError: sin `record`/`history`/`count_oversize` y sin `wait=`/`retry=` · 2026-10-16 (antes del código). fix1 RED: (A-2) test_a2_codex_mcp_publishes_events_without_replace_retries falló con `[('events.json', True)] != [('events.json', False)]` y test_a2_single_attempt_on_a_windows_sharing_violation con `assert (4 == 1)` intentos de `os.replace`; (D2) test_d2_burst_of_eight_parallel_tool_events_on_a_full_ring_loses_none falló con 7 de 8 `state_busy` · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest tests/test_agent_activity_store.py tests/test_agent_activity_git.py agent-kits/shared/test_local_state*.py` → verde dentro de 398 passed, 3 skipped; `pytest tests/test_graphiti_security.py` → 121 passed.
  - fix1 (A-2, D2): `pytest tests/test_agent_activity_store.py tests/test_agent_activity_git.py agent-kits/shared/test_local_state*.py agent-kits/shared/test_agent_activity.py` → 320 passed, 3 skipped (ráfaga de 8 ×5 seguidas: 0 perdidos; con 0,8 s/1 s perdía 1 de 8 a veces) · `pytest tests/test_graphiti_security.py` → 121 passed (huella del almacén `2a106540…c682`, revisada: sin imports ni módulos nuevos).

Decisión fix1 (D2): retención medida con el anillo lleno en Windows p50 ≈ 105 / p90 ≈ 130 ms, dominada por reabrir el `events.json` recién reemplazado (≈ 55 ms) y su reemplazo (≈ 12 ms); los validadores pasan a regex (mismas reglas; la validación baja de ≈ 50 % a ≈ 5 % del perfil). Como la retención no cabe en 100 ms × 7, los eventos de herramienta (asíncronos, I-05 intacto) esperan hasta `TOOL_LOCK_WAIT` = 1 s con plazo `TOOL_DEADLINE` = 1,3 s (bajo el presupuesto de 2 s del launcher); las señales de ciclo de vida (síncronas) siguen con 100 ms y 1 s y Codex MCP con un intento (P-EI-3, ahora también sin reintentos de `os.replace`: A-2). `design.md` §2.5 (a) dice «hasta 100 ms» y «plazo de 1 s»: pendiente de que el architect lo actualice (el implementer no escribe `design.md`).

**Notas**: inventario cerrado en `agent-kits/shared/agent-activity-store.py:119-122`; opt-in en `:92-100` (`_enabled`); tope de entrada actual en `:20` y `:264-266`; captura y CAS en `:185-233` (`capture`). Huella en `tests/test_graphiti_security.py:159-165`. Familia de riesgo de `session-end-durable-capture` (LES-016). Lente C. Añadido `history()` (lector) y `local-state.py` `wait=`/`retry=` (P-EI-3, un solo intento). Huella revisada del almacén y `redact.py` en `dependencies`. Limpieza P-EI-1 antes del inventario, solo si el resto de nombres es el esperado.

Prerrequisito (2026-10-16): inventario tolera hasta 8 .tmp-* (§2.5 c); RED test_orphan_temp_keeps_capture_and_snapshot_ok (antes del código); limpieza pendiente de P-EI-1.

### T-44 — Eventos de herramienta por runtime y ventanas por gramática exacta

- **Descripción**: `_payload` acepta los eventos de herramienta: Claude `PostToolUse` (ok) y `PostToolUseFailure` (error) con `agent_id`/`agent_type` y `duration_ms`; Codex `PostToolUse` agrupado por sesión, sin duración y resultado «sin datos»; OpenCode `tool.execute.after` con `sessionID`, `agent` y `status`. Reconoce `usage-meter.py start|close --artefacto <slug>/T-XX` solo por regex anclada sobre el argv de un evento Bash/shell.
- **Estado**: completado
- **Cerrada**: 2026-10-16
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real 0,02h (medido: fix1; código y RED en la ventana común de T-42-fix1)
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 366k in / 60k out tok · 5,60 €
- **Dependencias**: T-43
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_store.py`, `tests/test_graphiti_security.py`
- **Cubre (tests)**: E2E-17, E2E-18
- **Verificación**: `python3 -m pytest -q tests/test_agent_activity_store.py tests/test_graphiti_security.py` → `passed` (texto libre con `T-07` en commit, grep o prompt de Agent → «sin atribuir»; `-fixN` normalizado a `T-XX`; Codex sin subagente → run de sesión)

- **Changelog**: Agentes en vivo reconoce las herramientas de Claude Code, Codex y OpenCode y atribuye cada evento a su tarea solo por el comando exacto del medidor, nunca por texto libre.

**Criterios de aceptación**
- [x] CA-16: por evento, hora, herramienta, resumen, `T-XX` si se atribuyó, duración y resultado (`ok`/`error`/`null`).
- [x] CA-18: test negativo con `T-XX` en texto libre; nunca proximidad temporal.
- [x] Nunca persiste `tool_response`, contenido, salidas, prompts ni rutas absolutas.
- [x] Un runtime o evento desconocido se descarta con su código, sin excepción hacia el hook.

**Subtareas**
- [x] RED por runtime con payloads de la doc oficial (citados en T-40).
- [x] Mapeo y gramática exacta.

- **Evidencia TDD**: RED: 59 tests nuevos de test_agent_activity_store.py (gramática por runtime, ventanas, T-XX en texto libre, Codex MCP) fallaron con unsupported_event y sin ventanas · 2026-10-16 (antes del código). fix1 (C-2) RED: test_c2_patch_summary_with_a_long_whitespace_run_is_linear falló con `1.74 < 0.5` s (20.000 espacios) · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest tests/test_agent_activity_store.py tests/test_graphiti_security.py` → verde (suite de actividad 398 passed, 3 skipped; graphiti 121 passed).
  - fix1 (C-2): `_PATCH_FILE` toma el resto de la línea (`[^\n]*`) y se recorta en Python; mismo resultado con espacios/`\r` finales · `pytest tests/test_agent_activity_store.py …` → 320 passed, 3 skipped (pasada de T-43-fix1) · graphiti 121 passed.

**Notas**: `_payload` actual en `agent-kits/shared/agent-activity-store.py:155-178`; argumento `--artefacto` en `agent-kits/shared/usage-meter.py:730`. Tabla de runtimes de `design.md` §1. Lente C. Los eventos Post de un comando fallido (`PostToolUseFailure`/`status: error`) no abren ventana. Codex trae el resultado como «sin datos». Nombres de herramienta de OpenCode en minúsculas se normalizan solo para el resumen.

### T-45 — Registro de hooks: `PostToolUse` y `PostToolUseFailure` asíncronos e interop

- **Descripción**: `hooks/hooks.json` añade grupos `PostToolUse` (sin matcher) y `PostToolUseFailure` con `agent-activity`, `"async": true` y `timeout: 5`. `export-interop.py` conserva el matcher del grupo de actividad en el `PostToolUse` de Codex (hoy fuerza `^apply_patch$` en todo grupo) y omite `PostToolUseFailure`. Se regenera `interop/`.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,58h (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-44
- **Tipo**: hooks
- **Archivos**: `hooks/hooks.json`, `scripts/export-interop.py`, `tests/test_export_interop.py`, `tests/test_hooks_shell.py`, `interop/**` (regenerado: `hooks/` tocado)
- **Cubre (tests)**: E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_export_interop.py tests/test_hooks_shell.py` → `passed` · `python3 scripts/export-interop.py --check` → exit 0 · `python3 scripts/lint_plugin.py` → exit 0 (commands de `hooks.json` existentes y ejecutables)

- **Changelog**: Agentes en vivo recibe un evento por cada herramienta terminada (también las fallidas en Claude Code) sin hacer esperar a la herramienta: el hook corre en segundo plano en Claude Code y Codex.

**Criterios de aceptación**
- [x] Los grupos de actividad son `async` en Claude y Codex; el resto de grupos `PostToolUse` no cambia.
- [x] Codex: el grupo de actividad conserva su matcher; los demás siguen con `^apply_patch$`; sin `PostToolUseFailure`.
- [x] CA-42: `export-interop.py --check` pasa.

**Subtareas**
- [x] RED en `test_export_interop.py`.
- [x] Registro y traducción; regenerar `interop/`.

- **Evidencia TDD**: RED: test_export_interop.py::test_codex_activity_group_keeps_its_matcher_async_and_drops_failure, ::test_real_hooks_register_async_tool_activity_and_codex_export_matches y test_hooks_shell.py::test_hooks_json_solo_la_actividad_es_asincrona_y_toda_herramienta_la_dispara fallaron con AssertionError: PostToolUse (sin grupo de actividad; `^apply_patch$` forzado y `PostToolUseFailure` exportado) · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest tests/test_export_interop.py tests/test_hooks_shell.py` → 127 passed in 201.87s · `export-interop.py --check` → «88 ficheros al día» (exit 0) · `lint_plugin.py` → exit 0, «10 agentes · 0 errores · 8 avisos» (avisos previos de citas en docs, ninguno de `hooks.json`) · `evals/check.py` → 0 errores. Suites que leen `hooks.json` (`test_agent_activity_store`, `test_codex_command_transport`, `test_graphiti_security`, `test_hook_launcher_security`, `test_hooks_config`, `test_knowledge_services`, `test_lint_plugin`, `test_panel_diagnostics`, `test_plugin_panel`, `agent-kits/shared/test_agent_activity`, `test_doctor`) → 864 passed, 5 skipped, 2 failed: `test_doctor.py::test_config_error_long_absolute_path_keeps_file_and_field[taxonomy.json-categories|training.json-id_prefix]` con `FileNotFoundError [WinError 3]` por ruta > MAX_PATH del tmp de Windows (previo y ajeno a esta tarea; la réplica Linux de T-53 lo confirma).

Decisión: un grupo es «de actividad» solo si TODOS sus hooks son el launcher de `agent-activity`; un grupo mixto sigue la regla general (`^apply_patch$`). Ningún otro hook es `async` (los que informan necesitan que el runtime espere su `systemMessage`); `SubagentStart`/`SubagentStop` siguen síncronos.

**Notas**: grupos actuales en `hooks/hooks.json:34-50`; matcher forzado en `scripts/export-interop.py:407-408`. Lente C.

### T-46 — Atajo del launcher: sin opt-in no se lanza Python

- **Descripción**: En `hooks/run-hook.mjs`, para `agent-activity`, Node lee `.claude/dev.json` (≤ 64 KiB, `node:fs`) y sale con 0 antes de lanzar Python si `sesion.actividad !== true`. Nueva huella del launcher tras revisión.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,11h (medido; los tests se redactaron dentro de la ventana de T-45)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-45
- **Tipo**: hooks
- **Archivos**: `hooks/run-hook.mjs`, `tests/hook-budget.test.mjs`, `tests/hook-runtime.test.mjs`, `tests/test_graphiti_security.py`, `interop/**` (regenerado: `hooks/` tocado)
- **Cubre (tests)**: E2E-19
- **Verificación**: `node --test tests/hook-budget.test.mjs tests/hook-runtime.test.mjs` → `pass` · `python3 -m pytest -q tests/test_graphiti_security.py` → `passed` (nuevo `_LAUNCHER_NODE_HASH`; solo `child_process`, `fs`, `path`, `url`)

- **Changelog**: Sin `sesion.actividad: true`, el hook de actividad ya no arranca Python: sale en unos 80 ms en lugar de cerca de un segundo.

**Criterios de aceptación**
- [x] Con la captura desactivada, el hook no lanza ningún proceso Python (test que espía `spawn`).
- [x] `dev.json` ausente, ilegible, > 64 KiB o con JSON inválido → sale con 0 sin Python.
- [x] I-05: latencia síncrona añadida 0 ms en Claude y Codex (`async`), medida y anotada; excepción documentada: MCP en Codex.
- [x] Exit 0 siempre (ADR-007); sin red.

**Subtareas**
- [x] RED en `hook-budget.test.mjs`.
- [x] Bloque aislado del atajo; huella revisada.

- **Evidencia TDD**: RED: hook-budget.test.mjs «activity opt-in: …» (4 casos) falló con «activity-optin block not found» / TypeError: activityEnabled is not a function / «main must call activityEnabled»; hook-runtime.test.mjs «agent-activity without the opt-in never launches Python…» falló con «absent: Error: spawnSync … EOF» (el launcher lanzaba el hijo y le pasaba la entrada) · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `node --test tests/hook-budget.test.mjs tests/hook-runtime.test.mjs` → tests 30 · pass 30 · fail 0 · `pytest tests/test_graphiti_security.py tests/test_hook_launcher_security.py tests/test_hook_supervisor.py` → 143 passed (huella nueva `f86f0a1e…2599`; imports del launcher: `child_process`, `fs`, `path`, `url`) · `node --test tests/hook-post-preflight.test.mjs tests/hook-guard-delivery.test.mjs tests/session-end-budget.test.mjs` → 127 pass, 0 fail · `export-interop.py --check` → 88 al día · `lint_plugin.py` → 0 errores · `evals/check.py` → 0 errores.
- **Medición I-05** (`run-hook.mjs agent-activity` real, 12 ejecuciones, Windows, mismo método que T-40): captura desactivada p50 78 ms / p90 97 ms (antes 1.018 / 1.085 ms: ya no arranca Python); captura activa p50 393 ms / p90 420 ms. Los dos corren con `async: true` (T-45): la latencia síncrona añadida a la herramienta es 0 ms en Claude Code y Codex; la excepción son las herramientas MCP de Codex, que el runtime ejecuta siempre en síncrono (con un único intento sin espera, P-EI-3, T-44).

Revisión de la huella: el diff del launcher solo añade el bloque `activity-optin` (lee `dev.json` con `openSync`/`fstatSync`/`readSync`/`closeSync` de `node:fs`, ≤ 64 KiB + 1 byte, `TextDecoder` estricto, `JSON.parse`, `sesion.actividad === true`) y su llamada antes de buscar Python; sin red, sin procesos nuevos, sin escritura. Con la captura desactivada se drena stdin (una entrada grande nunca choca con una tubería cerrada) y se sale con 0, como mucho a 1 s.

**Notas**: presupuesto por hook en `hooks/run-hook.mjs:24-31` (`childBudgetMs`); hooks conocidos en `:36-38`. Huella en `tests/test_graphiti_security.py:122` y módulos admitidos en `:787`. Lente C.

### T-47 — OpenCode: binding de actividad en `tool.execute.after` sin esperar al hijo

- **Descripción**: `hooks/opencode-plugin.js` registra el binding de actividad en `tool.execute.after` (herramienta, `status`, `agent`, args solo para el resumen) y lanza el hijo sin `await`, registrándolo en `children` para el cierre.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,15h (medido; parte de los tests se redactó en la ventana de T-45; fix1 0,00: código y RED en la ventana común de T-42-fix1)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-44
- **Tipo**: hooks
- **Archivos**: `hooks/opencode-plugin.js`, `tests/opencode-plugin.test.mjs`, `interop/**` (regenerado: `hooks/` tocado), `skills/plugin-panel/scripts/build_panel.py` (añadido: el inventario del panel valida el catálogo del adaptador binding a binding y rechazaba el nuevo), `tests/test_plugin_panel.py` (añadido)
- **Cubre (tests)**: E2E-09
- **Verificación**: `node --test tests/opencode-plugin.test.mjs` → `pass` (la promesa del evento resuelve antes de que termine el hijo; el hijo queda en `children`) · `python3 scripts/export-interop.py --check` → exit 0

- **Changelog**: En OpenCode, Agentes en vivo recibe también un evento por herramienta terminada, sin hacer esperar a la herramienta y sin enviar al proceso de captura más que lo que necesita el resumen.

**Criterios de aceptación**
- [x] CA-42: OpenCode emite eventos de herramienta; si V2 no trae `sessionID`/`agent` en un runtime real, se declara en la página y en `docs/INTEROP.md`.
- [x] Las vinculaciones de actividad e inicio/fin siguen separadas (GOT-022).

**Subtareas**
- [x] RED en `opencode-plugin.test.mjs`.
- [x] Binding sin `await`.

- **Evidencia TDD**: RED: opencode-plugin.test.mjs «catalog declares tool activity…» falló con TypeError: Cannot read properties of undefined (reading 'domain'); «tool activity resolves before its child ends…», «…child is tracked and cleanup terminates it» y «…ignores foreign sessions and keeps the post notifications» fallaron con «Adapter effect was not observed» (reconfirmado contra el adaptador de HEAD: 4 fail); test_plugin_panel.py «…exposes_adapter_budget» con el binding nuevo falló con `assert 0 == 8` (catálogo rechazado) · 2026-10-20 (antes del código). fix1 (B2) RED: «tool activity is dispatched before the awaited post handlers…» falló con «activity started 1514 ms after the first post handler» · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `node --test tests/opencode-plugin.test.mjs tests/hook-runtime.test.mjs` → tests 44 · pass 44 · fail 0 · `export-interop.py --check` → 88 al día (regenera `interop/opencode/plugins/custom-agents/index.js`) · `pytest tests/test_plugin_panel.py tests/test_panel_contract_golden.py` → 115 passed, 2 skipped · `pytest tests/test_export_interop.py tests/test_graphiti_security.py tests/test_panel_diagnostics.py tests/test_agent_activity_store.py` → verde (446 passed en la pasada conjunta, cuyo único rojo era el golden, corregido) · `lint_plugin.py` → 0 errores.
  - fix1 (B2): el registro pone el binding sin `await` (`tool-activity`) delante de `post` sea cual sea el orden del catálogo · `node --test tests/opencode-plugin.test.mjs tests/hook-runtime.test.mjs` → 45 pass, 0 fail · `export-interop.py --check` → 88 al día · `pytest tests/test_panel_contract_golden.py tests/test_plugin_panel.py tests/test_export_interop.py` → 163 passed, 2 skipped (golden sin cambios).

Decisiones: (1) binding propio `tool-activity` en el catálogo (dominio `tool`, `execute.after`, `PostToolUse`, 2.500 ms); comparte el evento nativo con `post`, así que el adaptador registra UNA función por evento nativo que llama a `tool-activity` (sin esperar) y luego a `post` (como hoy). (2) La búsqueda de la sesión y el hijo corren en segundo plano; la tarea en vuelo se guarda en `inflight` y el hijo en `children`, y el cierre espera a los dos. (3) Al hijo solo le llegan `sessionID`, `tool`, `status`, `agent` y las claves que lee la lista blanca del resumen del almacén (`_raw_summary`); de un parche, solo sus líneas `*** Add|Update|Delete File:`. (4) El inventario del panel acepta el catálogo con o sin `tool-activity` (un adaptador anterior no declara eventos de herramienta; ningún otro binding es opcional): así el golden de `--json` no cambia aquí y su actualización queda en T-51. No validado en un OpenCode V2 real (sin runtime en esta máquina): si V2 no trae `sessionID`/`agent`, lo declaran la página (T-49) y `docs/INTEROP.md` (T-52).

**Notas**: binding de actividad actual en `hooks/opencode-plugin.js:19` y despacho en `:263-270` (hoy con `await run(...)`); `agent` ya usado por la guardia (`design.md` §1, l. 163). Gotcha `custom-agents.GOT-022`. Lente C.

### T-48 — API `api/actividad-runs` y `api/actividad-run-<key16>`

- **Descripción**: Dos rutas nuevas: la lista de runs y la línea de tiempo de un run (≤ 150 últimos eventos, con `recortado`), ambas ≤ 64 KiB y redactadas. `api/activity` no cambia.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real 0,17h (medido: 0,17 + fix1 0,00; código y RED de fix1 en la ventana común de T-42-fix1)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-43
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/panel_data.py`, `tests/test_panel_activity_server.py`
- **Cubre (tests)**: API-04, API-05
- **Verificación**: `python3 -m pytest -q tests/test_panel_activity_server.py` → `passed` (≤ 65.536 bytes con 500 eventos; `key16` inexistente → 404; sin token → 403)

- **Changelog**: El panel servido ofrece dos lecturas nuevas de actividad: la lista de runs con sus eventos recientes y la línea de tiempo de un run (sus últimos 150 eventos), siempre dentro de 64 KiB y con el texto saneado.

**Criterios de aceptación**
- [x] Tope de 64 KiB y 150 eventos por run con `recortado`.
- [x] Sin `?` en la ruta; `key16` validado por regex exacta.
- [x] Captura desactivada → respuesta con el estado y cómo activarla, no una lista vacía.

**Subtareas**
- [x] RED; rutas.

- **Evidencia TDD**: RED: 13 tests nuevos de test_panel_activity_server.py fallaron con AttributeError: 'PanelServer' object has no attribute 'actividad_runs' / 'actividad_run' y la ruta HTTP con `assert (404 == 200)` · 2026-10-20 (antes del código). fix1 (D1) RED: test_d1_history_validation_loads_agent_activity_once_per_request[runs|run] falló con `assert 500 <= 1` cargas de `agent-activity.py` · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest tests/test_panel_activity_server.py tests/test_panel_server.py` → 184 passed, 2 skipped (500 eventos de 160 caracteres que escapan a muchos bytes → cuerpo ≤ 65.536 en las dos rutas; `key16` inexistente o ambiguo → 404; mayúsculas, 15/17 caracteres, `?` o `/` final → 404; sin capacidad → 404 y Host ajeno → 403, sin leer el historial; POST → 405) · `pytest tests/test_console_encoding.py tests/test_panel_data.py tests/test_panel_memory_server.py tests/test_panel_review_server.py tests/test_panel_review_panel_server.py` → 798 passed · pasada de todas las `tests/test_panel_*.py` + `test_plugin_panel` + `test_graphiti_security` → 1207 passed (el único rojo, `test_no_scope_has_no_new_routes`, coincidió con una edición en vuelo y pasa en las dos repeticiones) · `lint_plugin.py` → 0 errores.
  - fix1 (D1): `activity_history` carga `ROLES` una vez por petición y se lo pasa al validador · `pytest tests/test_panel_activity_server.py tests/test_panel_server.py tests/test_panel_inicio_ui.py tests/test_panel_live_ui.py tests/test_panel_activity_ui.py tests/test_panel_privacy.py tests/test_panel_pages.py tests/test_panel_export.py` → 360 passed, 3 skipped.

Decisiones: (1) Proyección en `panel_data.actividad_runs`/`actividad_run` (pura, con `project_runs`/`project_events` de `agent-activity.py`); el servidor valida la lectura de `agent-activity-store.history` con un conjunto cerrado de claves y motivos (fuera de forma → `invalid_history`, nada parcial), sanea `tool`/`resumen`/`tarea`/`ultima_herramienta` con el saneador único del panel y recorta a 64/160/200. (2) Respuesta de runs: `runs` (más reciente primero, `key16` = 16 primeros hex del `run_key`; nunca las claves completas), `recientes` (10 últimos eventos, para Inicio en T-50), `eventos` (total), `recortado` y `descartados_por_tamano`. (3) Tope de 64 KiB: la lista suelta primero `recientes` y luego runs; la línea de tiempo suelta los eventos más antiguos y los suma a `recortado`. (4) `key16` que casa con dos runs → 404 (nunca se adivina). (5) «Sin token → 403» de la Verificación: el contrato vigente del servidor (`test_no_capability_never_calls_snapshot`) responde 404 sin capacidad y 403 con Host/Origin ajenos; se mantiene y se prueba así. (6) Captura desactivada o `invalid_config` → `status: unavailable` con `reason` y `activar` (cómo activarla).

**Notas**: snapshot de actividad actual en `skills/plugin-panel/scripts/serve_panel.py:206-226` (`_unavailable_activity`, `activity_snapshot`, 222 líneas: no ampliarla, crear función nueva). Lente C.

### T-49 — Página Agentes en vivo: runs, línea de tiempo y declaraciones por runtime

- **Descripción**: `agentes.html` muestra una fila por run (runtime, rol, inicio, duración, última herramienta) y, al abrirlo, su línea de tiempo. Estados «sin señal reciente», «tarea: sin atribuir», «historial recortado a los últimos N eventos», «captura informativa: puede tener huecos», «actividad desactivada» con cómo activarla, y por runtime «este runtime no emite eventos de herramienta» o «Codex no identifica el subagente: se agrupan por sesión».
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real 0,12h (medido: 0,05 + fix1 0,07; el JS y su arnés se redactaron dentro de la ventana de T-48, ≈ 0,1h más)
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 366k in / 60k out tok · 5,60 €
- **Dependencias**: T-48
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-agentes.js`, `skills/plugin-panel/assets/panel-activity.js` (sin cambios: el snapshot vivo sigue igual), `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_activity_ui.py`
- **Cubre (tests)**: E2E-17, E2E-18, E2E-19, E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_panel_activity_ui.py` → `passed` (escenarios: run activo, run > 60 s, evento sin atribuir, historial recortado, captura desactivada, Codex por sesión)

- **Changelog**: Nueva vista Agentes en vivo en el panel servido: una fila por run (runtime, rol, inicio, duración, última herramienta y estado) y, al abrirlo, su línea de tiempo con la tarea atribuida o «sin atribuir»; dice qué no aporta cada runtime y que la captura puede tener huecos.

**Criterios de aceptación**
- [x] CA-15, CA-16, CA-18, CA-19, CA-20 y CA-21 visibles con sus textos.
- [x] CA-42: cada runtime declara lo que no aporta; nada se omite en silencio.
- [x] Refresco de 5 s como hoy; sin `innerHTML`.

**Subtareas**
- [x] RED en el arnés.
- [x] Página.

- **Evidencia TDD**: RED: 20 tests nuevos de test_panel_activity_ui.py (`test_agentes_dom_contract[*]` ×18, `…never_writes_html…`, `test_served_agentes_page_loads_its_script…`) fallaron con FileNotFoundError: …/assets/page-agentes.js y con `'src="assets/page-agentes.js"' in …` falso · 2026-10-20. Transparencia: el primer borrador de `page-agentes.js` se escribió antes que el test; se retiró del árbol, se escribió el arnés, se obtuvo el rojo con el asset ausente y después se restauró y se cableó (constitución §1: el rojo es real, pero el orden de redacción no fue el ideal). fix1 (A-1, deuda aceptada por el usuario 2026-10-20, opción b, con verificación por mutación): 8 escenarios nuevos, cada uno RED contra SU mutante sobre una copia limpia (`AssertionError [ERR_ASSERTION]`, 1 failed) y verde sin él · 2026-10-20.
- **Verificación ejecutada**: `pytest tests/test_panel_activity_ui.py` → 44 passed (run activo con runtime, rol, inicio, duración y última herramienta; run de 120 s «sin señal reciente» con duración congelada de 8 min; línea de tiempo con hora, herramienta, resumen, «tarea: sin atribuir», `panel/T-07`, duración y resultado; «Historial recortado a los últimos 150 eventos» en el run y «…500 eventos» en la lista; «Actividad desactivada» con cómo activarla, sin usar el texto del servidor; Codex «agrupa por sesión» y «sin eventos de herramienta»; declaraciones por runtime y «Captura informativa: puede tener huecos» siempre visibles; filas o eventos fuera de forma no llegan al DOM; refresco de 5 s, un pedido en vuelo, plazo de 4 s, pausa con la pestaña oculta; el arnés lanza error ante `innerHTML`) · todas las `tests/test_panel_*.py` (salvo los servidores de memoria/revisión, ya verdes en T-48) + `test_plugin_panel` → 940 passed, 6 skipped · `lint_plugin.py` → 0 errores.
  - fix1 (A-1): `pytest tests/test_panel_activity_ui.py tests/test_panel_privacy.py` → 55 passed · mutación (`mutar_agentes.py` sobre `git archive` + test nuevo): **32 de 32 mutantes aplicables cazados** (antes 24/32; vivos cazados ahora: duración de run nula como 0, resultado nulo como ok, sin tope de 64 runs, sin tope de 150 eventos, dos pedidos en vuelo, caché permitida, respuesta no ok aceptada, respuesta tardía de otra generación); ninguno equivalente.

Decisiones: `page-agentes.js` solo en servido (`LIVE_ASSET_FILES` y `LIVE_SCRIPTS['agentes']`; si falta, el servidor lo omite como al resto de vivos) y construye su propio DOM debajo de la sección del snapshot vivo, sin tocar `build_panel.py`; la tabla lleva `caption` y `th scope=col`; el texto de «cómo activarla» es una constante local (no se pinta texto libre del servidor).

**Notas**: JS de actividad actual en `skills/plugin-panel/assets/panel-activity.js` (movido en T-12; refresco en su l. 67 original de `references/`). Lente C. A-1 (fix1): deuda TDD aceptada por el usuario (2026-10-20, opción b), cerrada con 32/32 mutantes cazados.

### T-50 — Inicio: actividad reciente

- **Descripción**: En servido, Inicio muestra los últimos eventos de actividad (agente, rol, herramienta, tarea si la hay, hace cuánto) con enlace a Agentes en vivo; con la captura desactivada, «actividad desactivada» y cómo activarla.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,03h (medido: 0,03 + fix1 0,00; código y RED de fix1 en la ventana común de T-42-fix1)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-49
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-inicio.js`, `tests/test_panel_inicio_ui.py`
- **Cubre (tests)**: E2E-19
- **Verificación**: `python3 -m pytest -q tests/test_panel_inicio_ui.py` → `passed`

- **Changelog**: Inicio muestra en el panel servido los últimos eventos de actividad (agente o sesión, runtime, herramienta, tarea y hace cuánto) con enlace a Agentes en vivo; si la captura está desactivada dice cómo activarla, y la copia exportada avisa de que la actividad solo existe en servido.

**Criterios de aceptación**
- [x] CA-04 en sus dos ramas (activa / desactivada).
- [x] En modo exportado, la sección dice que la actividad solo existe en servido.

**Subtareas**
- [x] RED; sección.

- **Evidencia TDD**: RED: 4 tests nuevos de test_panel_inicio_ui.py (`test_ca04_*` ×3, `test_exportado_dice_que_la_actividad_solo_existe_en_servido…`) fallaron con «sin pedido a api/actividad-runs», `0 == 1` pedidos y TypeError: Cannot read properties of undefined (reading 'textContent') (sin sección) · 2026-10-20 (antes del código). fix1 (B1) RED: test_b1_actividad_reanuda_el_sondeo_al_volver_la_pestana falló con «al volver se reanuda: 1 !== 2» y test_b1_respuesta_llegada_con_la_pestana_oculta… con `1 !== 2` pedidos · 2026-10-20 (antes del código)
- **Verificación ejecutada**: `pytest tests/test_panel_inicio_ui.py` → 30 passed · `pytest tests/test_panel_inicio_ui.py tests/test_panel_export.py tests/test_panel_server.py tests/test_panel_pages.py tests/test_panel_live_ui.py tests/test_panel_iniciativas_ui.py tests/test_panel_charts_ui.py` → 297 passed, 3 skipped.
  - fix1 (B1): escucha de `visibilitychange` (oculta → pausa; visible → `leer()`), como `page-agentes.js`; el arnés admite varios oyentes por evento (Cartera y Actividad) · `pytest tests/test_panel_inicio_ui.py` → 32 passed (dentro de la pasada de 360 de T-48-fix1).

Decisiones: la sección «Actividad reciente» la construye `page-inicio.js` (sin tocar `build_panel.py`) y lee `recientes` de `api/actividad-runs` (T-48) cada 5 s, solo en servido; en exportado no pide nada y lo dice. El test que fija las rutas de red del JS de Inicio pasa de «solo `api/cartera`» a una lista exacta por fichero (`page-cartera.js` → `api/cartera`; `page-inicio.js` → `api/actividad-runs`).

**Notas**: página de T-18; datos de `api/actividad-runs` (T-48).

### T-51 — Golden de `build_panel.py --json` actualizado solo con los hooks nuevos y grep de datos personales en eventos

- **Descripción**: El inventario de `--json` cambia porque hay hooks nuevos: el golden de T-01 se actualiza con un diff limitado a esos registros y revisado. Se añade el grep de CA-41 sobre `events.json` y sobre las respuestas de las API de actividad.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real 0,09h (medido)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-45, T-48
- **Tipo**: test
- **Archivos**: `tests/fixtures/panel-redesign/**`, `tests/test_panel_contract_golden.py`, `tests/test_panel_privacy.py`
- **Cubre (tests)**: E2E-08
- **Verificación**: `python3 -m pytest -q tests/test_panel_contract_golden.py tests/test_panel_privacy.py` → `passed` · lectura: el diff del golden solo añade los grupos de hook de actividad (pegado en `Notas`)

- **Changelog**: El inventario del panel (`--json`) declara los nuevos registros de actividad por herramienta en los tres runtimes, y una prueba de privacidad comprueba que ni el historial ni las respuestas de actividad ni la copia exportada llevan la ruta del home, el usuario o correos.

**Criterios de aceptación**
- [x] CA-28: el único cambio del golden son los registros de hook nuevos; `dashboard.json` y `dashboard.md` intactos.
- [x] CA-41: ningún HTML, JSON ni evento con la ruta del home, el usuario o correos, en servido y exportado.

**Subtareas**
- [x] Regenerar el golden y revisar el diff.
- [x] Test de privacidad sobre toda la salida.

- **Evidencia TDD**: RED: con los registros nuevos en el bundle de la fixture (`hooks/hooks.json`: grupo `PostToolUse` de actividad y `PostToolUseFailure`; `interop/codex/hooks.json`: `PostToolUse` de actividad; `opencode-plugin.js`: binding `tool-activity`), `test_panel_contract_golden.py::test_panel_json_igual_a_su_golden` falló con «panel.json cambió respecto a su golden (CA-28)» · 2026-10-20; después `PANEL_GOLDEN_UPDATE=1`. `test_panel_privacy.py` es de caracterización (la protección ya existía desde T-42/T-48): su primer rojo vino de un corpus fuera del contrato de `redact.anonimizar` (usuario pegado con guion en un nombre de fichero, ver Notas); con el corpus del contrato pasa, y una mutación que quita `anonimizar` del resumen del almacén lo vuelve rojo (`1 failed, 2 passed`).
- **Verificación ejecutada**: `pytest tests/test_panel_contract_golden.py tests/test_panel_privacy.py` → 9 passed · `git diff --stat tests/fixtures/panel-redesign/golden/dashboard.json …/dashboard.md` → vacío (intactos) · todas las `tests/test_panel_*.py` (salvo los servidores de memoria/revisión) + `test_plugin_panel` → 947 passed, 6 skipped · `lint_plugin.py` → 0 errores.

Diff revisado del golden (`golden/panel.json`, +90 / −2): 4 registros nuevos con `handler: agent-activity` — `claude-code` `PostToolUse` (`hooks/PostToolUse/1/0`, `timeout: 5` s, `matcher: ""`), `claude-code` `PostToolUseFailure` (`hooks/PostToolUseFailure/0/0`), `codex` `PostToolUse` (`interop/codex/hooks.json`, `hooks/PostToolUse/0/0`) y `opencode` `PostToolUse` (`tool.execute.after`, `hook-catalog/bindings/tool-activity/handlers/0`, 2.500 ms, `adapter-supervision`); y los contadores `hook_group_count` 12 → 14 y `counts.hooks` 15 → 19. Nada más cambia.

Aviso para la revisión: (1) `redact.anonimizar` (T-04) sustituye el usuario solo como palabra entera, y trata `-` como parte de la palabra: un nombre de cuenta pegado con guion o letras (`notas-jdoe.txt`) se conserva en el resumen. Es el contrato vigente (evita falsos positivos como «ana» en «ana-lisis») y no se toca aquí; la prueba lo deja escrito. (2) El título y la descripción del manejador `agent-activity` en el inventario («Señales recientes de actividad» / «Observaciones de sesión opt-in…») siguen describiendo solo las señales de sesión; ahora también captura herramientas. Cambiarlos movería más el golden: queda para la revisión.

**Notas**: riesgo «CA-28 choca con la fase 3» de `design.md` §6. A-4/C-3 (fix1): deuda aceptada por el usuario (2026-10-20, opción b); CA-41 enmendada en la spec (usuario unido por guion o tras punto); comentario en el corpus de `test_panel_privacy.py`.

### T-52 — Documentación de F3: observabilidad, interop, flujos y contratos

- **Descripción**: `docs/observability.md` (+EN): captura de herramientas, opt-in, topes, borrado manual del directorio; `docs/INTEROP.md`: degradación por runtime con la cita de Codex; `docs/FLOWS.md` (+EN): flujo del hook asíncrono; `docs/PLUGIN-PANEL.md` (+EN): página Agentes; `docs/agents/CONTRACTS.md`: arista hook → `events.json` y panel → API de actividad.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real 0,13h (medido)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-41..T-51
- **Tipo**: docs
- **Archivos**: `docs/observability.md`, `docs/en/observability.md`, `docs/INTEROP.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`, `docs/en/INTEROP.md` (añadido: espejo EN de `docs/INTEROP.md`; regla bilingüe)
- **Cubre (tests)**: —
- **Verificación**: `python3 scripts/lint_plugin.py` → exit 0 (aristas nuevas con Puerta; sin citas rotas) · lectura: espejos EN y la cita de Codex con URL

- **Changelog**: La documentación explica Agentes en vivo: cómo activar la captura de herramientas, qué registra y qué no, sus topes, cómo borrar el historial a mano y qué aporta cada runtime.

**Criterios de aceptación**
- [x] Cada runtime documenta lo que emite y lo que no.
- [x] La guía dice cómo borrar el historial (el panel no borra).
- [x] ES y EN en el mismo cambio.

**Subtareas**
- [x] Redactar y espejar.

- **Evidencia TDD**: TDD n/a: prosa (documentación de F3); la puerta es el linter (citas y Puerta de las aristas nuevas) y las suites que leen la doc.
- **Verificación ejecutada**: `lint_plugin.py` → exit 0, «10 agentes · 0 errores · 8 avisos» (los mismos 8 avisos previos de citas `/skills` y `/health`; ninguno nuevo; E61 y E62 con Puerta y scripts existentes) · `evals/check.py` → 0 errores · suites que leen la doc (`test_cifras_medidas`, `test_codex_command_transport`, `test_coverage_check`, `test_knowledge_services`, `test_lint_plugin`, `test_panel_pages`, `test_review_jira_owner`, `test_training_data_services`, `test_usage_meter`) → 606 passed, 1 skipped · `test_graphiti_security` → 121 passed. Lectura: `docs/observability.md` + EN (sección «Agentes en vivo: captura de herramientas (opt-in)»: activar, qué registra, atribución, coste medido, topes, huecos, desactivar y **borrar a mano `.claude/agent-activity/`**; chuleta), `docs/INTEROP.md` + EN (fila «Eventos de herramienta» en la tabla de degradación por runtime y hueco con la cita https://learn.chatgpt.com/docs/hooks consultada el 2026-10-16; OpenCode V2 «no validado en un runtime real»), `docs/FLOWS.md` + EN (§6b «Captura de herramientas para Agentes en vivo», diagrama del hook asíncrono), `docs/PLUGIN-PANEL.md` + EN (sección «Agentes en vivo», APIs y actividad reciente de Inicio; fila de la tabla de páginas), `docs/agents/CONTRACTS.md` (E61 hook → `events.json`, E62 panel → API de actividad; recuento «sesenta y dos», E1–E62).

Nota: `docs/agents/CONTRACTS.md` es solo ES (como el resto de `docs/agents/`).

**Notas**: TDD n/a: prosa. No hay arista de actividad en CONTRACTS hoy: regla base de P3-bis (`docs/observability.md`, FLOWS).

### T-53 — Cierre transversal (C-05): multi-runtime, evals, interop, tamaño de skills y réplica Linux

- **Descripción**: Comprueba que las 7 páginas se generan desde Claude Code, Codex y OpenCode; que `SKILL.md` de `plugin-panel` y `roadmap-dashboard` caben en 200 líneas; que `evals/` casa con las `description` reales; que `interop/` está al día; y replica `ci.yml` en un contenedor Linux antes del push. Deja el campo `- **Changelog**:` en las tareas con cambio visible; los CHANGELOG los escribe `changelog-sync` en la Fase 6 de `/dev-cycle`.
- **Estado**: completado
- **Cerrada**: 2026-10-20
- **Tiempo humano**: est. 9,6h · real —
- **Tiempo IA (ejec.)**: est. 1,2h · real 1,00h (medido: 0,97, con la espera de la réplica Linux, + fix1 0,03)
- **Supervisión**: est. 0,3h (≈25 % IA) · real —
- **Previsión IA**: 549k in / 89k out tok · 8,40 €
- **Dependencias**: T-52
- **Tipo**: devops
- **Archivos**: `skills/plugin-panel/SKILL.md`, `skills/roadmap-dashboard/SKILL.md`, `evals/cases/skill-plugin-panel.json`, `evals/cases/skill-roadmap-dashboard.json`, `evals/cases/command-plugin-catalog.json`, `evals/cases/command-roadmap-status.json`, `docs/README.md`, `interop/**` (regenerado), `docs/roadmap/2026-10-15-panel-redesign/tasks.md`, `CHANGELOG.md`, `CHANGELOG.es.md` (añadidos en fix1, A-3: `changelog-sync` descarta el slug ya presente)
- **Cubre (tests)**: E2E-09
- **Verificación**:
  - `python3 scripts/export-interop.py --check` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 -m pytest -q tests/test_skill_size.py tests/test_export_interop.py` → `passed`
  - réplica de `ci.yml` en `python:3.11-slim` con `git -c core.autocrlf=false archive` → mismos verdes que en Windows (salida pegada en `Notas`)
  - lectura: generación de las 7 páginas en los tres runtimes anotada con su runtime

- **Changelog**: Las siete páginas del panel se generan igual desde Claude Code, Codex y OpenCode, y la guía de la skill del panel explica Agentes en vivo y cómo borrar su historial.

**Criterios de aceptación**
- [x] CA-42: las 7 páginas se generan en los tres runtimes; lo que falta se declara.
- [x] Sin rojos que solo salgan en Linux (CRLF de `.sh`, rutas).
- [x] Las tareas con cambio visible llevan `- **Changelog**:`.

**Subtareas**
- [x] Generación por runtime.
- [x] Réplica Linux.
- [x] Campos `Changelog`.

- **Evidencia TDD**: TDD n/a: verificación transversal y prosa (`skills/plugin-panel/SKILL.md`).
- **Verificación ejecutada** (2026-10-20, árbol de `T-52` + este cambio, `git stash create` → `d8265cd`):
  - Windows: `export-interop.py --check` → «88 ficheros al día» · `evals/check.py` → «52 ficheros · 192 casos … 0 errores» · `pytest tests/test_skill_size.py tests/test_export_interop.py` → 78 passed · `lint_plugin.py` → 0 errores, 8 avisos (los previos) · `skills/plugin-panel/SKILL.md` 133 líneas y `skills/roadmap-dashboard/SKILL.md` 63 (≤ 200) · `scope-check.py docs/roadmap/2026-10-15-panel-redesign --base 9c47821` → exit 0, 38 cambiados, 38 en alcance, 0 fuera, 0 avisos, 0 criterios alterados.
  - Réplica de `ci.yml.MANUAL-COPY` en `python:3.11-slim` (Python 3.11.17, Node v22.23.3; `git -c core.autocrlf=false archive`): `lint_plugin` 0 errores · `evals/check` 0 errores · suites en modo script 0 fallos · pytest **8701 passed, 54 skipped, 0 failed** (incluye los dos `test_doctor …long_absolute_path…` que en Windows chocan con MAX_PATH) · bench p95 8,37 ms / p99 9,92 ms (exit 0) · `export-interop --check` 88 al día · `node --test` **354 tests, 338 pass, 0 fail** · sintaxis y JSON OK · `release.py --check` OK · exit 0. Mismos verdes que en Windows.
  - Generación por runtime (`build_panel.py --root . --project . --runtime <r> --export`, más el servidor con el inventario de cada runtime): **claude-code**, **codex** y **opencode** → exit 0 y las 7 páginas (`index`, `iniciativas`, `plan`, `agentes`, `memoria`, `catalogo`, `diagnostico`); el `agentes.html` exportado dice «Sin servicio» y no carga `page-agentes.js`; el servido sí. Hooks de actividad declarados: claude-code `PostToolUse`, `PostToolUseFailure`, `SubagentStart`, `SubagentStop`; codex `PostToolUse`, `SubagentStart`, `SubagentStop` (sin `PostToolUseFailure`: lo declara la página); opencode `PostToolUse` (`tool.execute.after`) y `ActivityObserved`. No se ejecutaron Codex ni OpenCode reales en esta máquina: la generación usa el inventario de cada runtime.
  - Campos `Changelog`: T-41..T-52 los llevan; sin él solo quedan las tareas de puerta sin cambio visible (T-16, T-29, T-39, T-40, T-53, T-54).
  - fix1 (A-3): bullets EN/ES de T-45..T-52 a mano en «phase 3 (live agents)» / «fase 3 (agentes en vivo)» desde su `Changelog`, y sección «phase 3 review» / «revisión de la fase 3» con las correcciones de fix1; `Changelog` añadido a T-40 y T-53 · `lint_plugin.py` → 0 errores, 8 avisos (los previos) · `evals/check.py` → 0 errores · `export-interop.py --check` → 88 al día · `scope-check.py … --base 14ef84b` → exit 0, 193 en alcance, 0 fuera · `ledger-lint.py` → 0 incoherencias.

`skills/plugin-panel/SKILL.md`: párrafo de Agentes en vivo (historial, APIs, atribución, declaración por runtime y borrado a mano); la `description` no cambia (los evals siguen casando).

**Notas**: TDD n/a: verificación y prosa. Nota de memoria «verificar en Linux antes de push» (normalizar CRLF de los `.sh`). Release fuera de este plan: `python3 scripts/release.py X.Y.Z` tras el PR.

### T-54 — Cierre de la Fase 3: revisión de dos lentes con Lente C obligatoria y revisión visual del usuario (M-04)

- **Descripción**: Puerta final: suites de CA-44, linter y evals; revisión adversarial de dos lentes **más la Lente C de seguridad obligatoria** sobre todo el diff de la fase (hooks, almacén, redactor, launcher, servidor); bucle acotado a 3 con Minor al backlog; el usuario revisa Agentes en vivo y el panel completo en el navegador (M-04).
- **Estado**: en-progreso
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 15,0h · real — (revisión + corrección: f = 2,0 de C-03 + f = 0,5 de C-05)
- **Supervisión**: est. 4,75h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 6,86 M in / 1,12 M out tok · 104,95 €
- **Dependencias**: T-40..T-53
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Cubre (tests)**: M-04
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py tests/test_export_interop.py agent-kits/shared/test_agent_activity.py agent-kits/shared/test_redact.py` → `0 failed` · `node --test tests/hook-budget.test.mjs tests/hook-runtime.test.mjs tests/opencode-plugin.test.mjs` → `pass`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: «Revisión de dos lentes — intento N: …» con la Lente C incluida, sin Critical ni Important abiertos, y «Revisión visual del usuario — Fase 3: aprobada AAAA-MM-DD»

**Criterios de aceptación**
- [ ] CA-44 de la Fase 3.
- [ ] Lente C despachada aunque `review-lens-select.py` no la active (condición 4 de la evaluación), con su salida en el ledger.
- [ ] Revisión cerrada en ≤ 3 intentos; las huellas de `test_graphiti_security.py` cambiadas tienen su revisión explícita.
- [ ] El usuario aprueba M-04.

**Subtareas**
- [ ] Suites y puertas.
- [ ] `adversarial-review` con A + B + C (+ D si `review-lens-select.py` la activa por la latencia del hook).
- [ ] M-04.

**Notas**: `skills/adversarial-review/scripts/review-lens-select.py:573` (modo `siempre`); el orquestador fuerza C sin tocar `.claude/dev.json` del usuario. Si el bucle llega al 3.er rojo de qa, `debug-root-cause` antes de preguntar.

## Revisión de dos lentes — intento 1: Fase 1 (T-01..T-15) — 5 Important, 7 Minor, 0 Critical (lentes: A+B+C)

Diff `14ef84b..HEAD` (112 ficheros; Chart.js vendorizado excluido del análisis de contenido). Lentes A, B y C en paralelo con el agente `reviewer` (opus, contexto fresco). Lente D no se lanzó: su único motivo fue `chart.umd.min.js` (tercero sin modificar) y la ruta de un test (`test_panel_export.py`), sin código de producción con carga. Gaps reproducidos por las lentes salvo donde se indica; fusionados y deduplicados por el orquestador (C-1 = A-3).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Borrado fuera del destino guiado por un `export-manifest.json` previo: `ruta` con `..` o absoluta → `destino / rel` y `unlink()` sin comprobar contención (CWE-22/CWE-73; constitución §4) | T-08 | corregido: `_leer_manifiesto` valida cada entrada (dict con `ruta` str y `sha256` hex de 64; ruta POSIX relativa sin barra invertida, `:`, NUL, raíz ni componentes `.`/`..`/vacíos; resultado resuelto dentro de `destino`; padres no enlaces). Entrada inválida: se ABORTA (exit 2, mensaje sin ruta absoluta) antes de escribir o borrar nada; elegido sobre «avisar y seguir» porque un manifiesto con una entrada hostil no es de fiar entero y limpiar el resto a ciegas repetiría el riesgo. | `skills/plugin-panel/scripts/panel_pages.py:183-193,243-246`; lentes A y C: `victim/settings.json` borrado con exit 0 (relativa y absoluta) · **Evidencia de la corrección:** `RED: tests/test_panel_fix1.py::test_una_ruta_del_manifiesto_fuera_del_destino_no_borra_nada[…] (11 casos), test_la_ruta_absoluta_real_de_la_victima_tampoco_se_borra y test_una_entrada_mal_formada… (3 casos) fallaron con «DID NOT RAISE ValueError» y la víctima borrada · 2026-10-15`; GREEN: `tests/test_panel_fix1.py` en verde (el caso de padre enlace se ejerce; skip solo si la máquina no crea symlinks); incluye una entrada válida anidada que sí se limpia (cubre las líneas de limpieza) |
| 2 | Important | Anonimizar los campos de vocabulario cerrado del inventario (`scope`, `kind`, `runtime`…): usuario `user`/`project`/`agent` → `KeyError` sin capturar en `--export`; usuario `codex` → `data-runtime="<usuario>"` y el filtro oculta los hooks | T-08, T-04 | corregido: el saneado distingue las claves de vocabulario cerrado (`CLAVES_CERRADAS` en `build_panel.py`: `scope`, `kind`, `runtime`, ids, estados, conteos, `source`, `workflow`…; una clave cerrada cubre su subárbol), que solo se redactan, del texto libre, que se anonimiza; `project-pieces` recibe un redactor que respeta el vocabulario exacto. | `build_panel.py:799-817` → `redact.py:191`; `build_panel.py:628`; lente B reproducido · **Evidencia de la corrección:** `RED: test_un_usuario_con_nombre_de_vocabulario_no_rompe_la_exportacion_ni_los_filtros[user|project|agent|codex] falló con data-runtime="&lt;usuario&gt;" · 2026-10-15`; GREEN: 4 passed (fixture de T-01 vía `materializar()`, exit 0, valores de `data-scope`/`data-runtime`/`data-kind` dentro del vocabulario, hooks `codex` presentes) |
| 3 | Important | Se recorta antes de anonimizar (contra el orden documentado en `redact.py`): un correo o ruta del home cortado a 480 caracteres se filtra a medias (`ana.lopez@a`) | T-08, T-04 | corregido: se anonimiza ANTES de recortar: `build_inventory(scrub=…)` aplica redactar→anonimizar en origen (`_catalog`, título y matcher de hook, textos de extensiones vía el redactor de `project-pieces`) y recorta después; `anonimizar` pasa a ser idempotente (`_marca_usuario`) porque el texto vuelve a pasar por el saneado final. | `build_panel.py:139` (`description[:480]`) + `:799-817`; lente B reproducido · **Evidencia de la corrección:** `RED: test_un_correo_que_cruza_el_corte_de_480…, test_una_ruta_del_home_que_cruza… y test_los_textos_de_extensiones_… fallaron con «ana.lop» / ruta del home partida en el HTML · 2026-10-15`; GREEN: 3 passed; `agent-kits/shared/test_redact.py::test_anonimizar_es_idempotente_…[usuario|correo|jdoeuser]` (RED `<<usuario>>` → GREEN) |
| 4 | Important | CA-41 no se cumple en modo servido: el servidor de T-11 renderiza el inventario sin anonimizar (la spec asigna CA-41 a la Fase 1 en ambos modos) | T-11 | corregido: un único punto de saneado (`_scrubber` en `build_panel.py`) para exportado y servido: `main` lo construye con `--export` o `--serve` y lo pasa a `build_inventory(scrub=…)` y a `server.run(scrub=…)`; `progress_snapshot(scrub=…)` lo aplica a los títulos de `api/progress`. `api/memory`, `api/activity` y `api/review` devuelven datos de sus propios dueños y no muestran texto del inventario: sin cambios. | `serve_panel.py:505-509`; `build_panel.py:820-826`; lente A reproducido (`jdoeuser`, correo y ruta del home en `catalogo.html` servido) · **Evidencia de la corrección:** `RED: test_el_catalogo_servido_no_lleva_home_correo_ni_usuario falló con el usuario de prueba en el catalogo.html servido; test_progress_snapshot_anonimiza… falló con TypeError (sin parámetro scrub) · 2026-10-15`; GREEN: 2 passed (`create_server` con la página `catalogo.html` real) |
| 5 | Important | `scope-check` exit 1: `CHANGELOG.md`/`.es.md` sin declarar y sin el slug (al cerrar, `changelog-sync` duplicaría los bullets); spec/design/plan/test-plan y el criterio de T-29 cambiados por la enmienda del 2026-10-15 sin constancia en `Archivos` | T-16 (alcance), T-01..T-15 | corregido: (a) `CHANGELOG.md`/`.es.md` declarados en `Archivos` de T-15 y las secciones de la iniciativa llevan el slug `panel-redesign` en su cabecera (`changelog-sync` lo busca entre comillas invertidas); (b) `Archivos` de T-16 declara `{spec,design,improvement-plan,test-plan}.md` («enmienda 2026-10-15 aprobada por el usuario, commit ee8e7cc») y los ficheros de este bucle; (c) T-29 recupera el literal original «Suites y puertas; `adversarial-review`; M-02.» con la ampliación detrás. Consecuencia: al cerrar, `changelog-sync` ya no añade la sección (ve el slug), así que las Fases 2-4 deben añadir sus bullets a mano bajo esa cabecera o retirar la marca antes de sincronizar. | `scope-check.py --base 14ef84b --json`; `changelog-sync.py:824`; `grep -c panel-redesign CHANGELOG*.md` → 0 · **Evidencia de la corrección:** `python agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign --base 14ef84b` → exit 0, «fuera de alcance (0)», criterios alterados 0; `changelog-sync.py --only panel-redesign --check` sobre una copia temporal marcada `estado: completado`: sin marca → «falta en CHANGELOG.md, CHANGELOG.es.md» (duplicaría); con marca → «sin entradas pendientes ✅» |
| 6 | Important | Constitución §1: RED de T-11 y T-12 obtenido después de implementar (declarado en sus Notas). No se puede rehacer | T-11, T-12 | deuda aceptada por el usuario (2026-10-15: «ok, pero los tests han de funcionar correctamente»); condición verificada con mutaciones, ver abajo | `tasks.md` Notas de T-11 y T-12 |
| 7 | Minor | `/roadmap-status` crea `docs/roadmap/` en un proyecto que no lo tiene (incumple «no crees carpetas vacías») | T-14 | corregido: el bloque de `/roadmap-status` solo ejecuta `[ -d docs/roadmap ] && dashboard --md … && panel --export …` (sin roadmap o con el dashboard fallido no se exporta ni se crea nada); `exportar_sitio` aborta (exit 2, sin ruta) si el padre del destino no existe: solo crea el propio destino. | `commands/roadmap-status.md:19-20`; `panel_pages.py:197` (lectura de código) · **Evidencia de la corrección:** `RED: test_roadmap_status_no_exporta_sin_roadmap_ni_si_el_dashboard_falla (sin la comprobación de que existe la carpeta) y test_no_se_crean_los_padres_del_destino (exit 0 con padres creados) fallaron · 2026-10-15`; GREEN: ambos passed |
| 8 | Minor | Exportación a medias: un fichero normal en lugar de un directorio padre (`assets`) no se detecta en la pasada previa; queda `agentes.html` escrito y exit 2 con la ruta absoluta en el mensaje | T-08 | corregido: pasada previa: cada ancestro entre destino y fichero que existe y no es directorio aborta antes de escribir (`output was not created by plugin-panel: <ruta relativa>`, sin ruta absoluta). | `panel_pages.py:226-242`; lente B reproducido · **Evidencia de la corrección:** `RED: test_un_fichero_donde_va_un_directorio_se_detecta_antes_de_escribir falló con agentes.html escrito y la ruta absoluta en stderr · 2026-10-15`; GREEN: passed |
| 9 | Minor | El `LICENSE.md` de Chart.js exportado bajo `docs/` entra en el alcance de Confluence; `publish-and-sync.md` afirma lo contrario | T-14, T-08 | corregido: `confluence-scope.py` excluye por código toda carpeta con `export-manifest.json` del generador `custom-agents plugin-panel` (`panel_export_dirs`, con su motivo en `--status`), no solo `docs/roadmap/panel/`; documentado en `SKILL.md`, `config-and-policy.md` y corregida la afirmación de `publish-and-sync.md`. | `panel_pages.py:49`; `skills/confluence-publish/references/publish-and-sync.md:74`; `confluence-scope.py --status` → «En alcance (1)» · **Evidencia de la corrección:** `RED: tests/test_confluence_scope.py::test_panel_export_folder_is_out_of_scope_wherever_it_lives falló con docs/roadmap/panel/vendor/chart.js/LICENSE.md en alcance · 2026-10-15`; GREEN: `test_confluence_scope.py` + `test_confluence_cli_additional.py` en verde (un manifiesto de otro generador o ilegible no excluye nada) |
| 10 | Minor | La `description` de `/roadmap-status` dice «no modifica nada» y ahora escribe `dashboard.md` y `docs/roadmap/panel/` | T-14 | corregido: nueva `description` de `/roadmap-status`: «Lee docs/roadmap/ y ESCRIBE docs/roadmap/dashboard.md y la carpeta docs/roadmap/panel/ …; no crea docs/roadmap/ si falta»; el cuerpo deja de decir «solo lectura». | `commands/roadmap-status.md:2` · **Evidencia de la corrección:** `RED: test_la_description_de_roadmap_status_declara_lo_que_escribe falló con «no modifica nada» · 2026-10-15`; GREEN: passed; `export-interop.py` regenerado y `--check` → «88 ficheros al día»; `evals/check.py` → «52 ficheros · 192 casos … 0 errores» |
| 11 | Minor | `design.md` no recoge la CSP servida decidida en T-03 (`style-src 'self'`, `img-src data:`, icono `data:,`) | T-03 | corregido por el orquestador: `design.md` §2.4 I-01 añade la cabecera servida completa y el porqué de cada ajuste | `design.md:205` frente a `panel_pages.py:38-39` |
| 12 | Minor | Criterio «el instalador copia `assets/`» sin salida pegada | T-14 | corregido: salida pegada en T-14 (`Verificación ejecutada`, línea «revisión intento 1, gap 12»). | `tasks.md` Verificación de T-14; lente A ejecutó `node --test --test-name-pattern="panel viaja" tests/installer.test.mjs` → `pass 1` · **Evidencia de la corrección:** `node --test --test-name-pattern="panel viaja" tests/installer.test.mjs` → `✔ el panel viaja con sus assets y Chart.js vendorizado (D-A1)` · `ℹ tests 1 · pass 1 · fail 0` |

Anotados sin corrección (no bloquean): T-05..T-08 sin medición IA real (no recuperable; `/retro` las tratará como `n/d`); hasta la Fase 2 la página Iniciativas no tiene contenido, así que no debe publicarse una release entre fases; el `<noscript>` de Catálogo remite a cifras de arriba que cuentan registros de hook (20) mientras el gráfico cuenta acciones (28); el alias 8.3 de un componente con punto no se reduce a `.` (sin dato personal).

**Revisión visual del usuario — Fase 1: aprobada 2026-10-15** (M-01: «me parece bien», servido y exportado). Petición derivada para el primer bloque de la Fase 2: el aviso del modo exportado («Instantánea del … · no se actualiza sola», `skills/plugin-panel/scripts/panel_pages.py:78`) pasa a decir cómo verlo en vivo («Copia estática del … · para verla en vivo, abre el panel servido con `/plugin-catalog --serve`»); el usuario: «me parece mejor».

**Condición del usuario sobre la deuda del gap 6 («los tests han de funcionar correctamente»), verificada por mutación (2026-10-15).** Sobre una copia limpia de HEAD (`git archive`), se inyectó cada fallo en el código de T-11/T-12 y se corrieron sus suites con `-x`. Se detectan 10 de 10 mutantes aplicables: sin nonce en `<script>` (`test_http_sirve_cada_pagina_con_su_csp_y_el_nonce_en_cada_script`), `script-src 'self'` (`test_http_bind_capability_headers_and_canonical_update`), token sin comprobar (`test_http_paginas_y_activos_sin_token_o_con_otro_token_dan_404_sin_contenido`), `plan-<id16>` fuera del inventario (`test_http_activo_o_pagina_fuera_de_la_lista_blanca_es_404`), Chart.js alterado aceptado (`test_http_chart_con_huella_distinta_se_sirve_sin_chart_y_con_aviso`), activos leídos de disco por petición (`test_http_no_lee_disco_por_peticion`), actividad cargada en Memoria y progreso fuera de Inicio (`test_cada_pagina_servida_carga_solo_sus_js_vivos`), JS vivos en exportado (`test_scripts_son_ficheros_en_orden_y_chart_solo_si_esta_disponible`) y revisión servida sin seleccionar (`…lista_blanca_es_404[assets/panel-review.js]`). Hay 1 mutante equivalente, que no es un hueco de los tests: quitar el rechazo de `? % \ #` en `serve_panel.py` `_route` deja `tests/test_panel_server.py` en 106 passed, porque la búsqueda exacta en la lista blanca ya devuelve 404 a esas rutas. La comprobación es una defensa extra sin efecto observable.

## Revisión de dos lentes — intento 3: Fase 1 (T-01..T-15) — 2 Important, 3 Minor, 0 Critical (lentes: A+B+C)

Diff `b09e07f..HEAD` (commit 95c72d3, fix2), revisado por un solo revisor con las tres lentes por falta de memoria en la máquina. Las filas 2-1..2-10 quedan cerradas con test. Las dos puertas relajadas no ocultan ningún fallo: `--test-reporter=tap` solo hace válidas las aserciones TAP con Node ≥ 23, y quitar `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` aísla el test del entorno del desarrollador (la variable la cubre `hook-budget.test.mjs`).

**Decisión del orquestador al 3.er intento con gaps (skill `adversarial-review` §5): seguir.** Los gaps son concretos, reproducidos y acotados a ficheros de la fase. El usuario exige cero rojos y que los tests funcionen. Se corrige en un bucle fix3 y se verifica con una revisión de confirmación sobre ese diff, sin abrir más rondas. Si esa confirmación encontrara algo más, se devolverá la decisión al usuario.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 3-1 | Important | `_scrubbed` anonimiza también los valores de vocabulario cerrado de `api/review`/`api/memory` (`runtime`, `state`, `disposition`, `caller_id`…): con una cuenta `codex`, `runtime: '<usuario>'` hace fallar los validadores de `panel-review.js` y la revisión no se puede aprobar ni pedir cambios | T-11 | corregido: `_scrubbed` pasa de lista cerrada de claves (denylist) a LISTA BLANCA de texto libre que solo se muestra: `titular`, `texto`, `evidencia`, `estado_detalle`, `ruta` (memoria), `response_text` y `note` (respuestas y verificaciones del agente) y `title`/`text` solo dentro de `sections` (texto del plan). Todo lo demás (vocabularios cerrados, ids, hashes, `runtime`, `state`, `disposition`, `caller_id`) queda intacto; el porqué está documentado en el código. | `serve_panel.py:126-137`; `panel-review.js:22,51,184`; sonda real · **Evidencia de la corrección:** `RED: tests/test_panel_fix3.py::test_cuenta_codex_y_vocabulario_cerrado_intactos_y_texto_mostrado_anonimizado falló (runtime anonimizado, validador de panel-review.js) · 2026-10-15`; GREEN: `pytest tests/test_panel_fix3.py tests/test_panel_fix2.py` → `22 passed`; el test pasa la respuesta real del servidor por el validador de `panel-review.js` (arnés Node) con `producer.runtime='codex'` y `consumer_registration`; el texto del plan y la respuesta del agente salen anonimizados; `api/memory` sigue anonimizada (test de fix2 verde) |
| 3-2 | Important | El saneado de `api/review` vuelve al servidor: `render` rellena los textarea con `draft_comments` ya anonimizados y el siguiente Guardar/Aprobar/Pedir cambios entrega `<correo>`/`<usuario>` al agente; el texto más largo puede pasar el tope de 2.000 caracteres y bloquear la revisión | T-11 | corregido: con la lista blanca, `draft_comments` y `decision.comments[].text` (entrada del propio usuario, que vuelve en Guardar/Decidir) ya no se tocan; `text` solo se anonimiza dentro de `sections`. | `serve_panel.py:330`; `panel-review.js:153,168,196,218`; `plan-review.py:556,298` · **Evidencia de la corrección:** `RED: test_comentario_del_usuario_vuelve_intacto_y_se_entrega_intacto falló: texto devuelto «…a <correo>; revisar ~/notas y a <usuario>» ≠ el guardado · 2026-10-15`; `RED: test_scrubbed_no_toca_text_fuera_de_sections falló: '<x>' != 'mio' · 2026-10-15`; GREEN: ambos en `tests/test_panel_fix3.py` → `passed` (guardar con correo y ruta del home → la vista conserva el texto exacto y `submit` entrega exactamente ese texto) |
| 3-3 | Minor | Resto de 2-7: `_clave_fs` no conoce los alias 8.3 de Windows; `vendor/chart.js/CHARTU~1.JS` con el sha real borra el Chart.js recién escrito (rc 0, el manifiesto lo lista) | T-08 | corregido: la validación del manifiesto rechaza (exit 2, sin tocar nada) cualquier componente con el patrón de nombre corto 8.3 `~[0-9]`; y `_borrar_si_es_nuestro` compara la ruta resuelta del candidato (en Windows `resolve()` expande el alias) con el conjunto de rutas resueltas de lo escrito en la exportación y no borra si coincide. | `panel_pages.py:199-201,312`; sonda `GetShortPathNameW` · **Evidencia de la corrección:** `RED: test_una_entrada_con_patron_de_nombre_corto_8_3_aborta_y_deja_chart[CHARTU~1.JS|a~1/x.txt|CHART~12.js] falló (exit ≠ 2) · 2026-10-15`; `RED: test_la_limpieza_no_borra_lo_recien_escrito_aunque_la_ruta_sea_un_alias_8_3 falló con TypeError (sin el conjunto resuelto), con `GetShortPathNameW` real · 2026-10-15`; GREEN: `pytest tests/test_panel_fix3.py tests/test_panel_fix2.py tests/test_panel_export.py` → `44 passed, 1 skipped` (los 8.3 de `test_panel_fix3.py` corren, no se saltan) |
| 3-4 | Minor | Resto de 2-6: un manifiesto plantado un nivel por debajo de `docs/` vuelve a excluir en bloque su subárbol, y las entradas listadas no se contrastan con su `sha256` | T-14 | corregido: `panel_export_files` solo excluye una entrada listada si el fichero existe, es regular y su sha256 coincide con el declarado, y solo honra manifiestos cuya carpeta tiene `index.html` empezando por el MARKER de plugin-panel (`PANEL_INDEX_MARKER`; un test lo compara con `panel_pages.MARKER`). | `confluence-scope.py:273,285`; sonda `resolve_scope` · **Evidencia de la corrección:** `RED: test_panel_manifest_entry_needs_matching_hash falló (LICENSE.md con hash distinto no estaba en alcance) y test_panel_manifest_without_a_real_panel_beside_it_excludes_nothing falló (manifiesto sin panel excluía) · 2026-10-15`; GREEN: `pytest tests/test_confluence_scope.py` → `31 passed` (incluye el caso legítimo con `exportar_sitio` real: LICENSE.md excluido) |
| 3-5 | Minor | `test_group_cleanup_without_ps_reads_proc` falla de forma intermitente con la máquina cargada: el plazo real de 0,25 s de `close_group` corre durante la contabilidad de un `/proc` falso en disco | 296c1fa (orquestador) | corregido solo en tests (plazo de producción intacto): `_Reloj` + fixture `reloj` sustituyen `supervisor.time` con un reloj congelado en los tests de `close_group` con `/proc` falso y `ps` falso; nuevo test del caso opuesto (reloj lento → «could not be confirmed»). La fragilidad real: el plazo se comprueba tras el primer barrido, antes de confirmar el siguiente. | `runtime-supervisor.py:213`; 1 fallo en una tanda y verde en solitario (13 passed) · **Evidencia de la corrección:** `RED: test_group_cleanup_without_ps_reads_proc y test_group_cleanup_keeps_owner_running_and_kills_children fallaron con OSError «group termination could not be confirmed» bajo un monotonic que avanza 0,3 s por llamada · 2026-10-15`; GREEN: `pytest tests/test_hook_supervisor.py` → `14 passed` |

**Confirmación del intento 3 (diff `95c72d3..HEAD`, cb405d3, lentes A+B+C, 2026-10-15).** Cerradas con test 3-2, 3-3 (el alias 8.3 real corrió con `GetShortPathNameW`), 3-4 y 3-5; scope-check exit 0. **3-1 queda parcial** y aparecen hallazgos nuevos causados por fix3. Como estaba fijado, la decisión pasa al usuario.

Decisión: corregir (orquestador, 2026-10-15, siguiendo la recomendación al usuario). Bucle fix4 (clave `2026-10-15-panel-redesign/T-16-fix4`: **0,42 h IA (medido)**, 2,91 €).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| C-1 | Important | Regresión de fix3: la lista blanca `_DISPLAY_KEYS` deja fuera `area`, `category`, `estado` y `tipo` de `api/memory` (texto libre del frontmatter que `panel-memory.js:66-70` muestra y que con fix2 se anonimizaba); `initiative` de `api/review` también, aunque es un slug acotado por regex (CWE-359) | T-11 | corregido: la lista blanca `_DISPLAY_KEYS` cubre ahora TODO texto libre que el panel muestra y no vuelve al servidor: `tipo`, `estado`, `estado_detalle`, `titular`, `area`, `category`, `evidencia`, `ruta`, `texto`, `relation` (memoria; inventario contra `panel-memory.js:51-70,100-120` y `knowledge-view.py` `compact`) y `title`/`text` de `sections`, `response_text`, `note` (revisión). `initiative` NO se toca (decisión con evidencia: el anonimizador no casa un usuario unido por guiones a otras palabras, así que sería un no-op, y es la identidad pública de la iniciativa; el JS solo exige `string`). Queda intacto lo que vuelve al servidor o valida por vocabulario (`id`, `origen`, `source_sha256`, `runtime`, `caller_id`, hashes, `draft_comments`, `decision.comments[].text`). Test de contrato por respuesta completa de `api/memory` y `api/review` con usuario/home/correo plantado en cada campo y las dos listas explícitas: un campo sin clasificar falla. | `serve_panel.py:132-133`; sonda: `area: jdoeuser /home/jdoeuser/x jdoe@example.org` llega intacto con fix3 y sale `<usuario> ~/x <correo>` con 95c72d3  **Evidencia de la corrección:** `RED: tests/test_panel_fix4.py::test_contrato_memoria_cada_campo_mostrado_anonimizado_y_el_resto_intacto y ::test_contrato_revision_… fallaron (area/category/estado/tipo/ruta/relation sin anonimizar; `note` sin tope) · 2026-10-15`; GREEN: `pytest tests/test_panel_fix4.py` → `5 passed` |
| C-2 | Minor | El cotejo de sha256 deja de excluir el `LICENSE.md` del panel si el consumidor versiona `docs/roadmap/panel/` y Git for Windows lo saca con CRLF (el exportador escribe LF) | T-14 | corregido: `_sha_coincide` acepta el sha256 de los bytes tal cual O el de los bytes con CRLF normalizado a LF, solo para ficheros de texto (`.md .txt .html .json`); Chart.js (`.js`) se compara tal cual. | `confluence-scope.py:270-271,303`  **Evidencia de la corrección:** `RED: tests/test_confluence_scope.py::test_panel_manifest_entry_tolerates_git_line_ending_conversion y ::test_panel_manifest_binary_or_js_is_compared_as_is fallaron (LICENSE.md con CRLF en alcance) · 2026-10-15`; GREEN: `pytest tests/test_confluence_scope.py` → `33 passed` (LICENSE.md reescrito con CRLF sigue excluido; contenido distinto no) |
| C-3 | Minor | Anonimizar alarga el texto (`<usuario>` es más largo que un usuario corto): un `titular` de 160 caracteres o un `response_text` cerca de 1.000 pasa del tope de los validadores del JS y el panel rechaza toda la respuesta (viene de fix2) | T-11 | corregido: `_scrubbed` recorta DESPUÉS de anonimizar, en el servidor, a los topes de los validadores (`_CAPS`: 160 en campos cortos, 1.000 en `evidencia`/`ruta`, 12.000 en `texto`, `response_text` 1.000 car./2.048 bytes, `note` 500/1.024) con `_clip`, que no parte una marca (`<usuario>`, `<correo>`) ni un carácter. El módulo no usaba indicador de recorte (solo `[:limit]`); no se añade. | `panel-memory.js:21`, `panel-review.js:24`  **Evidencia de la corrección:** `RED: tests/test_panel_fix4.py::test_titular_de_160_… y ::test_response_text_de_mil_… fallaron (response_text de 2.500 caracteres tras anonimizar; sin `_clip`) · 2026-10-15`; GREEN: `pytest tests/test_panel_fix4.py` → `5 passed` (respuestas reales del servidor pasan los validadores de `panel-memory.js` y `panel-review.js` en el arnés Node) |

**Confirmación de fix4 (diff `cb405d3..HEAD`, 70ba946, lentes A+B+C, 2026-10-15): 0 Critical, 0 Important, 3 Minor.** C-1 y C-2 quedan cerradas con test. C-3 queda parcial y pasa a M-F1-1. Lente C sin hallazgos: no hay fuga de PII en `api/memory` ni en `api/review`, y la tolerancia CRLF no permite excluir contenido distinto. Los Minor no bloquean el cierre (skill `adversarial-review` §3) y pasan al backlog de la Fase 2, que vuelve a tocar `serve_panel.py` y la revisión (T-56, T-58):

| # | Grado | Gap | Destino | Evidencia |
|---|---|---|---|---|
| M-F1-1 | Minor | Tope agregado de `feedbackValid` (16.384 bytes de `response_text`, 4.096 de `note`, 65.536 del historial): `_clip` recorta campo a campo, y anonimizar puede pasar la suma, con lo que el panel rechaza la revisión entera | T-56 (servidor), backlog | `serve_panel.py:162-177`; `panel-review.js:39`; sonda: 16.260 → 16.420 bytes |
| M-F1-2 | Minor | El test de contrato de C-1 usa fixtures escritas a mano: un campo nuevo del productor (`knowledge-view.compact`, `plan-review`) no lo hace fallar si no se añade también a la fixture | T-56/T-58, backlog | `tests/test_panel_fix4.py:33-49,92-102` |
| M-F1-3 | Minor | `_clip` puede partir la marca `[secreto redactado]` del redactor (solo estético: el secreto no se filtra) | T-56, backlog | `serve_panel.py:146,153-158`; `redact.py:34` |

Bucle de revisión de la Fase 1 cerrado: 3 intentos y 2 confirmaciones, sin gaps Critical ni Important pendientes. La deuda del gap 6 la aceptó el usuario y se verificó por mutación.

## Revisión de dos lentes — intento 3: Fase 2 (T-17..T-28, T-55..T-58) — 2 Important, 5 Minor, 0 Critical (lentes: A+C, B+D)

Confirmación sobre `ae57334..7ee05f1` (fix2, 2026-10-16). Lente A: I2-2..I2-8 hechas con test; los 15 tests nuevos fallan sobre `ae57334` (RED real). I2-2 probado con el dueño real; I2-3: 3,4 s → 0,06 s en el caso adversario. C sin hallazgos en invalidación, `avisos`, registro, plazos y `panel-review.js`.

**Decisión del orquestador al 3.er intento con gaps (skill `adversarial-review` §5): seguir**, como en la Fase 1: gaps concretos, reproducidos y acotados a dos funciones; ronda fix3 corta con TDD y verificación dirigida B+C. F2-1, I2-1 y F2-23 siguen a decisión del usuario.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| I3-1 | Important | El hash de contenido de la firma (fix2) abre con `open()` sin `local-read`: sigue symlinks fuera del proyecto y se bloquea con un FIFO; un `GET api/cartera` cuelga el servidor de un hilo | T-17 | corregido (fix3): la firma lee con `local-read` (regular, sin redirecciones, tope, sin FIFO); si falla, sin caché · RED test_la_firma_no_sigue_un_symlink…/…no_se_bloquea_con_un_fifo… (antes del código; Linux python:3.11: 167 passed) | `panel_data.py:256-257,279,409`; sonda FIFO/symlink en `python:3.11-slim`; CWE-59, CWE-400 |
| I3-2 | Important | Regresión de F2-4: `CARTERA_MAX_AGE` 10 s y `_cartera_built` tomado al empezar el cálculo; el cliente vuelve a pedir 10 s después de la respuesta, así que la caché no acierta nunca | T-17 | corregido (fix3): `_cartera_built` se toma al terminar el cálculo y `CARTERA_MAX_AGE` vuelve a 60 s · RED test_la_cartera_acierta_con_el_sondeo_de_10_s… (4 cálculos de 4; antes del código) | `serve_panel.py:29,462`; `page-cartera.js:16,124`; reloj simulado: 4 de 4 sondeos recalculan |
| I3-3 | Minor | La firma hashea hasta 128 × 2 × 256 KB por petición sin el tope agregado `MAX_SCAN_BYTES` | T-17 | corregido (fix3): la firma cuenta bytes hasheados y rebasa `MAX_SCAN_BYTES` -> firma única (sin caché) · RED test_la_firma_de_la_cartera_tiene_un_tope_agregado… (antes del código) | `panel_data.py:257,279` frente a `:35,320`; CWE-770 |
| I3-4 | Minor | El aviso `rangos_sin_expandir` no llega a `api/plan-*`: la tarea dice «Sin revisión registrada» sin aviso | T-21 | corregido (fix3): `avisos` viaja en `api/plan-*` y la página lo muestra con `textContent` (cabecera y detalle) · RED test_el_servidor_lleva_los_avisos…, …proyeccion_y_el_exportado…, …pagina_plan_muestra_el_aviso… (antes del código) | `ledger-view.py:225-226`; `panel_data.py:430-445,497-520` |
| I3-5 | Minor | `proyectar` cuesta tareas × filas × ids aunque no haya rangos (1.000 × 330 filas: 115 s); previo a fix2 | T-21 | corregido (fix3): `ledger-view` construye un índice id -> secciones/filas una vez (8,3 s -> <2 s con 1.000 × 3.300 filas) · RED test_mil_tareas_y_330_filas_por_seccion… (antes del código) | `ledger-view.py:216` |
| I3-6 | Minor | `review()` no invalida la caché si el dueño escribió y la respuesta acaba en `TimeoutError` o 413 | T-56 | corregido (fix3): `review()` invalida la caché en `finally` si el dueño pudo escribir (timeout, 413, excepción) · RED test_una_operacion_que_pudo_escribir_olvida_la_cache… (3 casos, antes del código) | `serve_panel.py:583-586` |
| I3-7 | Minor | `firma_fallos` solo vive en memoria: ningún endpoint ni `/doctor` lo muestra | T-17 | deuda (backlog F3) | `serve_panel.py:499` |

**Verificación dirigida de fix3 (diff `2a4c6ef..1beb9fa`, lentes B+C, 2026-10-16): 0 gaps nuevos.** I3-1..I3-6 ✓ con test que falla sobre `2a4c6ef` (Linux `python:3.11-slim`: symlink, FIFO y tope 22 passed; `test_panel_server.py` 132 passed). I3-5: proyección idéntica en los 49 ledgers reales (`2a4c6ef` frente a HEAD, sin `observed_at`). I3-7 queda en el backlog de la Fase 3. Bucle de revisión de la Fase 2 cerrado sin Critical ni Important de corrección pendientes; F2-1/I2-1 (deuda TDD): **deuda aceptada por el usuario (2026-10-16)**; las fases 4 y 3 exigen RED antes del código en el brief. F2-23 (CA-10): **spec enmendada por decisión del usuario (2026-10-16)**: «archivado» como texto, sin enlace.

## Revisión visual del usuario — Fase 2 (M-02), ronda 1: 3 hallazgos + 1 rojo de CI

Panel servido con `--review-panel` sobre una copia del roadmap (2026-10-16). Hallazgos del usuario en el navegador y rojo de la CI Linux sobre `c3ac718`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| M2-1 | Important | Iniciativas se queda en «Leyendo la cartera…»: `api/cartera` en frío tarda 2-47 s en esta máquina (49 iniciativas) y el cliente aborta a los 4 s sin aviso; el kanban no aparece | T-17 | corregido (fix M-02): cartera calculada al arrancar y en hilo de fondo con Lock; cliente «Calculando… (reintento en 3 s)» · RED test_la_primera_peticion_responde_calculando (antes del código) | `curl` 47,3 s en frío y 0,06 s en caché; `page-cartera.js:17` `PLAZO_MS = 4000` |
| M2-2 | Important | La tarjeta de progreso en vivo de Inicio no enlaza a su Plan y muestra «Referencia de lectura SHA-256…» | T-18 | corregido (fix M-02): enlace «Ver plan» a plan-<id16>.html; SHA-256 en `details` cerrado «Detalle técnico» · RED plan_link, test_el_progreso_marca (antes del código) | `panel-live.js:52` |
| M2-3 | Minor | Agentes en vivo dice «No se pudo actualizar» cuando `api/activity` responde `disabled` (opt-in apagado) | T-12 | corregido (fix M-02): con `disabled` dice «desactivada (opt-in)» y la clave `sesion.actividad` de dev.json · RED disabled_says_opt_in_and_how_to_enable (antes del código) | `api/activity` → `status: unavailable, reason: disabled` |
| CI-1 | Important | Rojo en CI Linux: `tests/test_project_pieces.py::test_multiline_metadata_within_read_budget_finishes_before_panel_timeout` (`TimeoutExpired` a 15 s); solo tarda 10,7-14,2 s en Linux | — (project-extensions) | corregido (causa raíz): `_metadata` hacía `re.match` por línea con sangría; sin regex ahí y `_agent_servers` sale sin `mcpServers` (3,7 → 1,7 s) · RED test_metadata_parsing_does_no_regex_work (antes del código) | CI `c3ac718`: 1 failed, 8319 passed |

**Revisión visual del usuario — Fase 2: aprobada 2026-10-20** (M-02, ronda 2, panel servido con `--review-panel` sobre el roadmap real en `3ca861b`): Inicio, Iniciativas y Plan aprobados; desde el Plan de `2026-09-09-brief-budget` abrió la revisión, guardó un comentario de sección y la aprobó (`api/review-summary` → «aprobada v1», 1 comentario); también aprobó sin comentarios la de `2026-08-12-sdd-hardening`. El estado vive solo en `.claude/plan-review/` (ignorado por git; puerta `requested-review`, no `plan-ok`).

## Revisión de dos lentes — intento 2: Fase 4 (T-30..T-38) — 0 Important, 3 Minor, 0 Critical (lentes: A+B+C+D)

Confirmación de fix1 sobre `01a1adc..469db9a` (2026-10-16), un revisor `reviewer` (opus) con las cuatro lentes por memoria. F4-1, F4-3..F4-10 ✓ con test; los 38 tests de `tests/test_panel_memoria_fix1.py` fallan sobre `01a1adc` (RED real). Ningún test existente relajado. C: 30 hosts probados en Python y JS, ningún host público sale como enlace; `_scrub_memoria` cubre todo el texto libre en servido y exportado. D: recálculo solo con la caché vencida, `memoria` 0,46 s y `_scrub_memoria` 0,03 s en el repo real. **Bucle cerrado sin Critical ni Important;** los Minor pasan al backlog de la Fase 3. T-39 sigue `en-progreso` hasta M-03 (el usuario lo revisará al final, 2026-10-16).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| F4-11 | Minor | Un recálculo fallido de `api/memoria` no se ve en la página: la versión buena sale `ok`/`complete` y `recalculo_fallido` se pierde con 16 avisos; añadirlo puede pasar de 64 KiB | T-30 | deuda (backlog F3) | `serve_panel.py:701-706`; `page-memoria.js:165-169` |
| F4-12 | Minor | Python y JS discrepan en `[0:0:0:0:0:0:0:1]` y `[fe80::1%25eth0]`: la tarjeta dice «host no local» para un loopback (etiqueta, no seguridad) | T-34 | deuda (backlog F3) | `panel_data.py:600-606`; `page-memoria.js:63-68` |
| F4-13 | Minor | «Actualizar» con la caché vencida devuelve la versión vieja sin reintentar | T-30 | deuda (backlog F3) | `serve_panel.py:676-684`; `page-memoria.js:530-532` |

**Revisión visual del usuario — Fase 4: aprobada 2026-10-20** (M-03, panel servido en `3ca861b`): Memoria, Catálogo y Diagnóstico aprobados sin hallazgos.

## Revisión de dos lentes — intento 1: Fase 3 (T-40..T-53) — 7 Important, 7 Minor, 0 Critical (lentes: A+C, B+D)

Diff `8fc3eb3..3ca861b` (2026-10-20), dos revisores `reviewer` (opus) en paralelo. C **forzada** por la condición 4 de la evaluación (además `review-lens-select` la activó: `private-key` en `agent-activity-store.py:493`, `authorization-header` en `journal.py:279` y `redact.py:47`); D activada por `await-en-bucle` en `hooks/opencode-plugin.js:301,303` (falso positivo: `tool-activity` es síncrona y `post` ya se esperaba). Puerta previa: `scope-check --base 14ef84b` → exit 0, 0 fuera de alcance. `export-interop.py --check` → «88 ficheros al día». Gaps reproducidos por los revisores y, los Important, comprobados por el orquestador (`redact` con `DB_PASSWORD=` sin redactar; `retry=` sin uso en el store; `_load_shared` sin caché; sección «phase 3» del CHANGELOG con T-41..T-44 solo). A-2 y D3 eran el mismo gap: fusionados.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| C-1 | Important | El resumen de Bash/PowerShell se guarda y se sirve **sin redactar** con secretos en variable con prefijo (`DB_PASSWORD=`, `API_TOKEN=`, `AWS_SECRET_ACCESS_KEY=`, `PGPASSWORD=`), `curl -u user:pass` y `mysql -p…`: `_ASIGNACION_RE` exige `\b` y `_` es carácter de palabra. Fallo anterior a la fase, pero la F3 lo lleva a `events.json`, `api/actividad-run-*` y Agentes en vivo (CA-17) | T-42 | corregido (fix1): clave tras `_`/prefijo sin `\b` izquierdo; `curl -u u:p` y `mysql -p<s>` por comando; `journal.py` idéntico · RED test_c1_* (16) · GREEN 118 passed | `redact.py:39`; `agent-activity-store.py:530-531,570`; sonda: `DB_PASSWORD=Hunter2xyz! psql -h db` sale igual en events.json y `api/actividad-run-<key16>`; CWE-532/312 |
| A-2 | Important | P-EI-3 (decisión del usuario 2026-10-16) a medias: `nowait` quita la espera del cerrojo, pero `_publish_events` no pasa `retry=False` y `os.replace` reintenta hasta 4 veces (≈140 ms síncronos en Codex MCP en Windows); docstring y ledger dicen lo contrario; sin test | T-43 | corregido (fix1): `nowait` → `retry=False` en `events.json` · RED test_a2_* (2) · GREEN 320 passed | `agent-activity-store.py:296` frente a `:631`; `local-state.py:53-55,75`; `design.md:398` (= D3 de la Lente D) |
| D2 | Important | El cerrojo se tiene ≈85-135 ms por escritura (revalida los 500 eventos carácter a carácter) y la espera es 100 ms: con herramientas en paralelo se pierde la mayoría de los eventos (8 hooks a la vez → 3 escritos, 5 perdidos, con anillo vacío o lleno); si cae un `usage-meter.py start`, lo siguiente queda «sin atribuir» | T-43 | corregido (fix1): validadores por regex + espera de herramienta 1 s ≥ 7 × retención p90 (≈ 130 ms), plazo 1,3 s · RED test_d2_burst… (7/8 perdidos) · GREEN 0/8 ×5 | `agent-activity-store.py:243-256,635-640`; `local-state.py:99`; bench: p50 128-136 ms con anillo lleno; cProfile `_validate_events` 124 de 264 ms |
| D1 | Important | `_valid_history_event` recarga `agent-activity.py` (`exec_module` sin caché) por CADA evento: 500 por petición, ≈180-190 ms; servidor de un hilo con Inicio + Agentes sondeando cada 5 s → ≈0,2 s de bloqueo por petición al resto de rutas | T-48 | corregido (fix1): `ROLES` una vez por petición · RED test_d1_* (500 cargas) · GREEN 360 passed | `serve_panel.py:37-45,563`; bench: `500 _load_shared ms 185.0` |
| B1 | Important | «Actividad reciente» de Inicio deja de refrescarse para siempre tras ocultar la pestaña una vez: `leer()` solo se reprograma si `!document.hidden` y no hay escucha de `visibilitychange` (sí la hay en `page-agentes.js:232`, `panel-live.js:84`) | T-50 | corregido (fix1): `visibilitychange` pausa y reanuda · RED test_b1_* (2) · GREEN 32 passed | `page-inicio.js:212-229`; arnés de `test_panel_inicio_ui.py`: tras volver, 1 pedido y 0 temporizadores pendientes |
| A-3 | Important | Los bullets de T-45..T-52 no están en ningún CHANGELOG y no llegarán solos: la sección ya lleva el slug y `changelog-sync` descarta todo slug presente | T-53 | corregido (fix1): 8 bullets EN/ES + sección «phase 3 review»; `Changelog` en T-40/T-53 · TDD n/a (prosa) · lint/evals 0 errores | `changelog-sync.py:12,824`; `CHANGELOG.md` «phase 3»: 3 bullets (T-41..T-44); el ledger lo advirtió en la F1 |
| A-1 | Important | T-49: `page-agentes.js` se escribió antes que su test y se **restauró** tras el rojo, no se reescribió; constitución §1 y ley dura de `tdd` («el código anterior al rojo se borra»). El rojo es un único `FileNotFoundError` para 18 casos | T-49 | deuda aceptada por el usuario (2026-10-20, opción b); verificada por mutación en fix1: 32/32 cazados (8 escenarios nuevos, RED cada uno contra su mutante) | `tasks.md` T-49 (nota transparente); `docs/CONSTITUTION.md` §1; `skills/tdd/SKILL.md` |
| C-2 | Minor | Regex con retroceso superlineal en el resumen de `apply_patch` (`(.+?)\s*$` con racha de espacios): 40 KB → 14,8 s de CPU en segundo plano; el launcher corta a 2 s y se pierde el evento | T-44 | corregido (fix1): `[^\n]*` + recorte en Python · RED test_c2_… (1,74 s) · GREEN 320 passed | `agent-activity-store.py:492`; 5k/10k/20k/40k → 0,095/0,42/1,54/14,8 s; CWE-1333 |
| B2 | Minor | OpenCode: `tool-activity` no se despacha «primero» (comentario) sino tras los `post` esperados en serie (≈1,8 s en Windows, hasta 60 s): `observed_at` llega tarde y el run puede salir «sin señal reciente» | T-47 | corregido (fix1): `tool-activity` delante de `post` en el registro · RED (1514 ms) · GREEN 45 pass | `hooks/opencode-plugin.js:291-304`; orden del catálogo l.17/l.19 |
| C-3 | Minor | El hueco de `anonimizar` (usuario unido por guion: `notas-jdoe.txt`, `ssh jdoe-laptop`) llega ahora a texto libre de eventos, `api/actividad-run-*` y Agentes en vivo; queda en la máquina (el exportado no lleva eventos) | T-42 | deuda aceptada por el usuario (2026-10-20, opción b); CA-41 enmendada en la spec (excepción: usuario unido por guion o tras punto) | `redact.py:205`; `agent-activity-store.py:575`; CWE-359 |
| A-4 | Minor | CA-41 no tiene excepciones y el test de privacidad usa un corpus que esquiva el caso conocido; lo decidió el implementer sin aceptación | T-51 | deuda aceptada por el usuario (2026-10-20, opción b); CA-41 enmendada en la spec (excepción: usuario unido por guion o tras punto) | `tests/test_panel_privacy.py:4-5,20`; `spec.md:230` |
| A-5 | Minor | E3: el Catálogo describe `agent-activity` como «Observaciones de sesión opt-in» y ahora captura cada herramienta | T-51/T-52 | backlog (cambiarlo mueve más el golden; CA-28) | `build_panel.py:212`; golden: 4 registros nuevos con ese texto |
| B3 | Minor | Un evento de herramienta con `cwd` en un subdirectorio del proyecto (tras `cd src`, o un worktree) se descarta como `project_mismatch` | T-44 | backlog (verificar qué `cwd` manda Claude Code tras un `cd` antes de cambiar la regla, que también rige `SubagentStart`/`Stop`) | `agent-activity-store.py:440`; sonda: `cwd=root/src` → `project_mismatch` |
| D4 | Minor | OpenCode con la captura apagada (el defecto) lanza igualmente un `node` + `session.get` por herramienta (≈80 ms de CPU cada uno, en segundo plano) | T-47 | backlog | `hooks/opencode-plugin.js:239-254` |

Sin hallazgos en el resto: páginas solo con `textContent`; rutas nuevas tras `_allowed()` y capacidad `hmac.compare_digest`; `key16` por regex exacta y prefijo ambiguo → 404; JSON estricto; symlinks y `nlink>1` rechazados; opt-in comprobado en Node y en Python; binding `tool-activity` opcional justificado (solo él puede faltar, `test_opencode_optional_binding_never_replaces_a_required_one`); golden de T-51 cambia solo en las altas y los dos contadores; ningún test relajado. **T-48 «sin token → 403»: Verificación mal redactada, no gap** (el 404 sin capacidad ya existía en `8fc3eb3`; copia el literal de CA-34, que diverge del servidor desde la F1 → `/spec-drift`). Fragilidad de `test_plan_review_summary.py` bajo carga: ningún cambio de la fase la explica (plazos absolutos de 0,3-0,4 s en el propio test). Fuera de lente, anotado: el hueco de `_ASIGNACION_RE` afecta también al journal versionado (lo cubre la corrección de C-1); `_clean_temps` borra `.tmp-*` regulares de > 60 s sin probar autoría (P-EI-1 aceptada por el usuario).

## Historial archivado

- 2026-10-15 · «Revisión de dos lentes — intento 2: Fase 1 (T-01..T-15) — 3 Important, 6 Minor, 0 Critical (lentes: A+B+C)» → [execution-history.md](execution-history.md) · SHA-256 `d61eb2c7b857fa4ea4b5c1ac3ada276c3524b033db9b039612e546385fc492d6`
- 2026-10-16 · «Revisión de dos lentes — intento 1: Fase 2 (T-17..T-28, T-55..T-58) — 8 Important, 16 Minor, 0 Critical (lentes: A+B+C+D)» → [execution-history.md](execution-history.md) · SHA-256 `34e2fc47f3fe983af8d6c5f6df1a9baaab660162b8fc79af2dddf88070346d5b`
- 2026-10-16 · «Revisión de dos lentes — intento 2: Fase 2 (T-17..T-28, T-55..T-58) — 3 Important, 5 Minor, 0 Critical (lentes: A+C, B+D)» → [execution-history.md](execution-history.md) · SHA-256 `4ef8ebe0266262f09f3125a8406352bf57f7258cc3f4de049f8e0d0313af4598`
- 2026-10-20 · «Revisión de dos lentes — intento 1: Fase 4 (T-30..T-38) — 3 Important, 7 Minor, 0 Critical (lentes: A+C, B+D)» → [execution-history.md](execution-history.md) · SHA-256 `38739915e10bde53690f3d12cfbae28ab15b846af05ca32584863e2b3e20db1a`
