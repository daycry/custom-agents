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
| Fase 1 — Base común | 13 | 16 | 81% | 0 / 28,8h | 1,75 / 10,5h | 0,24 / 3,6h | 0,49 / 5,58 M |
| Fase 2 — Inicio, Iniciativas y Plan | 0 | 13 | 0% | 0 / 36,0h | 0 / 10,8h | 0 / 3,7h | 0 / 5,74 M |
| Fase 4 — Memoria, Catálogo y Diagnóstico | 0 | 10 | 0% | 0 / 26,4h | 0 / 7,2h | 0 / 2,8h | 0 / 3,83 M |
| Fase 3 — Agentes en vivo + cierre transversal | 0 | 15 | 0% | 0 / 45,6h | 0 / 23,4h | 0 / 6,9h | 0 / 12,44 M |
| **TOTAL** | **13** | **54** | **24%** | **0 / 136,8h** | **1,75 / 51,9h** | **0,24 / 17,0h** | **0,49 / 27,60 M** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.

> **Revisión como línea propia (LES-009).** Las horas IA de «revisión + corrección» de cada fase (factor `f` de la evaluación) van en la tarea de cierre de la fase (T-16, T-29, T-39, T-54), no repartidas: es la partida que más se desvía y así `/retro` mide el `f` real por fase.

---

## Fase 1 — Base común

**Estado**: en-progreso · **Estimado**: 28,8h humanas · 10,5h IA · **Real**: — · **Coste est.**: 1.513 € referencia · ≈ 255 € ejecución · **Tokens est.**: 5,58 M

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

**Notas**: patrón de fixture de bundle en `tests/test_plugin_panel.py:69-70` (`bundle(tmp_path)`); patrón de roadmap sintético y subprocess de `--json` en `tests/test_dashboard.py:269` (`_roadmap_procedencia`). El `--json` se emite en `skills/roadmap-dashboard/scripts/build_dashboard.py:1157-1170`. Este golden se actualiza UNA vez en F3 (T-51), con diff limitado a los registros de hook nuevos. **Implementación (2026-10-15):** fixture de roadmap con 6 iniciativas + 1 carpeta y 1 fichero que no son iniciativa: `alfa` (cadena completa, spec `aprobada`, `generacion:` medido, gaps de revisión abiertos), `beta` (spec `borrador`, sin `generacion:`), `gamma` (`implementada`, horas `—` sin real, `testing/`, `execution-history.md`, etiquetas nuevas de evaluación), `delta` (ilegible: spec sin frontmatter con bytes no UTF-8 —que solo existen en la copia materializada, ver abajo— y evaluación sin etiquetas), `epsilon` (vía rápida, ledger de 273.499 bytes > 256 KiB, `generacion:` sin medida) y `zeta` (`obsoleta`, evaluación `cancelado` por frontmatter, coste parcial). El ledger grande se generó una vez con un script de desarrollo determinista (no versionado; el fichero sí). Bundle de fixture: 2 agentes, 1 skill, 1 comando, `hooks/hooks.json`, `interop/codex/hooks.json` (con un timeout inválido), el catálogo de hooks de OpenCode (copiado del `hooks/opencode-plugin.js` real, solo el bloque de datos) y `native-roles.json`; extensiones `project/` y `home/` (agente, persona, skills con un conflicto de nombre, TOML de Codex, fuente de tool, `.mcp.json` con URL y cabecera privadas que no salen). **Normalización declarada en el test** (`NORMALIZACION` + `_ids_de_usuario`): fin de línea CRLF→LF, fecha de `dashboard.md`, separador `\` del campo `path`, e ids de piezas de USUARIO derivados del hash de la ruta absoluta de la raíz (`project-pieces.py:505`). **Desviación:** `.gitattributes` gana `tests/fixtures/panel-redesign/** text eol=lf`; sin ella, `core.autocrlf=true` en Windows extrae CRLF y los goldens dejan de cuadrar (mismo caso que `tests/fixtures/knowledge-corpus/**`). Para regenerar en T-51: `PANEL_GOLDEN_UPDATE=1` y revisar el diff de `golden/`. **Materialización (corrección tras la suite repo-wide):** la primera versión versionaba la spec de `delta` con bytes no UTF-8 y rompía `tests/test_review_jira_owner.py::test_paso_9_no_aparece_en_ningun_md_vivo_del_repo` (lee todo `.md` vivo en UTF-8 estricto; en CI habría fallado). Ahora el árbol versionado es UTF-8 válido (lo vigila `test_el_arbol_versionado_solo_lleva_utf8_valido`) y los generadores corren sobre una copia en `tmp` que hace `materializar()` (copia `roadmap/`, `bundle/`, `project/`, `home/` y escribe los bytes no UTF-8 de `delta`); los goldens no cambiaron. Las fases siguientes que usen la fixture deben importar `materializar` de `tests/test_panel_contract_golden.py`. Verificación tras el cambio: `… tests/test_panel_contract_golden.py` → `6 passed in 3.03s`.

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

**Notas**: valores de `design.md` §2.4 I-01. Patrón de comprobación de huella por SHA-256 en `tests/test_graphiti_security.py:122` (`_LAUNCHER_NODE_HASH`). Si `install/` no copia `assets/`, se anota y se corrige en T-14. **Extracción (paso de desarrollo único, 2026-10-15):** `curl -sS -f` de `https://registry.npmjs.org/chart.js/4.5.1` (metadatos) y del tarball `https://registry.npmjs.org/chart.js/-/chart.js-4.5.1.tgz` (1.576.314 bytes) a una carpeta vacía del scratchpad; un script con `python -I` fuera de esa carpeta comprobó `sha512-GIjfiT9dbmHRiYi6Nl2yFCq7kkwdkp1W/lp2J99rX0yo9tgJGn3lKQATztIjb5tVtevcBtIdICNWqlq5+E8/Pw==` = `dist.integrity` del registro = valor de `design.md` (y `shasum` sha1 `19dd1a9a386a3f6397691672231cb5fc9c052c35` = registro), y solo entonces leyó con `tarfile` dos miembros sin ejecutar nada: `package/dist/chart.umd.min.js` (SHA-256 `48444a82…f54a`, igual al publicado por jsDelivr que cita el diseño) y `package/LICENSE.md` (MIT, «Copyright (c) 2014-2024 Chart.js Contributors», SHA-256 `41a84aa2…4cce`). Ningún script del plugin descarga: lo vigila `test_ningun_script_del_panel_descarga_nada`. **Desviaciones (ficheros fuera del `Archivos` original):** (1) `.gitignore` tenía `**/vendor/`, que ignoraba el fichero: sin la excepción `!skills/plugin-panel/assets/vendor/`, el plugin instalado por marketplace (clon de git) no lo traería; (2) `.gitattributes` gana `skills/plugin-panel/assets/vendor/** -text`: con `core.autocrlf=true` git podría convertir fines de línea y romper el SHA-256 (el test lo vigila con `git check-attr`). **Tolerancia del activo (riesgo C-01):** `lint_plugin.py` → `0 errores · 8 avisos` (los 8 preexistentes: 3 nombres genéricos, `/health`, `/skills` ×4); `export-interop.py --check` → `88 ficheros al día`; `test_skill_size.py` → `30 passed`; `test_export_skills.py` + `test_export_interop.py` → `65 passed`; `export-skills.py` lleva el `vendor/` al paquete portable con el mismo SHA-256 y `--check` → `241 ficheros · 0 problema(s)`; `install/` copia `skills/` entero con `cpSync` (sin filtro de tamaño; `installer.test.mjs` → `145 pass, 0 fail`) y `npm pack --dry-run` incluye los 3 ficheros de `vendor/chart.js/`: **no hace falta corregir nada en T-14**. Nota para T-11: el fichero termina en `//# sourceMappingURL=chart.umd.min.js.map` (sin modificar); el `.map` no se incluye, así que un navegador con las herramientas de desarrollo abiertas lo pedirá y recibirá 404 (no es CSP ni red externa).

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

**Notas**: CSP actual del servido en `skills/plugin-panel/scripts/serve_panel.py:469-470` (nonce) y `:492` (cabecera); la del HTML estático en `skills/plugin-panel/references/panel.html:2`. Runner Playwright de referencia: `agent-kits/qa/runner/playwright.config.mjs`. El nombre `.mjs` sin `.test` evita que la CI lo recoja (no hay navegadores en CI). La evidencia va a este ledger: el guardrail del implementer prohíbe escribir en `docs/roadmap/**/testing/`. **Ejecución (2026-10-15):** permiso de instalación: el orquestador autorizó en el brief el Playwright del scratchpad (`@playwright/test` 1.56.1) y `npx playwright install firefox` (descarga oficial, Firefox 142.0.1, build v1495). El Chromium de Playwright 1.56 (rev. 1194) no está en la caché del usuario: el motor Chromium se probó con `channel: 'msedge'` (Edge del sistema, motor Chromium); el script cae a ese canal solo si falta el ejecutable empaquetado (`--chromium-channel` lo fija). Cómo mide: la red se bloquea con `context.route(/^https?:\/\//)`, que aborta y cuenta todo origen ajeno al servidor de loopback (en `file://`, todo http/https), y `context.on('request')` cuenta cualquier otra petición que no sea `file:/data:/about:/blob:`; las violaciones salen de un detector `securitypolicyviolation` inyectado con `addInitScript` y de los mensajes de consola de CSP. Cada motor y modo lleva un CONTROL (script inline prohibido) que debe dar ≥ 1 violación y no ejecutarse; sin él, «0 violaciones» podría ser un detector roto. También prueba `fetch('ping')` al mismo origen (`connect-src 'self'` → 200) y que el gráfico pinta píxeles en el `<canvas>`. Los datos van en `<script type="application/json">`, que no dispara CSP en ningún motor. El servidor del pico imita el de `serve_panel.py` (token en la ruta, rechazo de `?`, `%`, `\` y `#`, nonce por respuesta); el script no escribe en el repo (carpeta temporal que borra al salir) ni imprime rutas locales ni el token. **Medición:** `usage-meter close` solo contó 10 respuestas en la ventana (37.822 tokens facturables), menos que el trabajo hecho (redacción del script y tres ejecuciones); el real de IA parece corto y se deja tal cual, marcado como medido.

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

**Notas**: patrón de tests en `agent-kits/shared/test_redact.py:23-41`; bloque replicado declarado en `agent-kits/shared/copias.json:297-310` (no tocar). Lo consumen `panel_data.py` (F1-F4) y el almacén de actividad (F3). **Implementación (2026-10-15):** `anonimizar(texto, raiz, home, usuario)` y sus constantes (`ANON_RAIZ`, `ANON_HOME`, `ANON_USUARIO`, `ANON_CORREO`) van DESPUÉS del marcador `# --8<-- fin redact`; `redactar` no cambia. Orden interno: raíz → home → correos → usuario (los correos antes que el usuario para no dejar `<usuario>@dominio`). El orden del saneado completo (`redactar → anonimizar → quitar controles → recortar`) queda en el docstring del módulo con su porqué. Decisiones de la implementación, sin cambio de alcance: (1) pura de verdad: no lee entorno ni disco ni `os.name`; el «Windows» se reconoce por la FORMA de la ruta (con unidad `C:`), que casa sin distinguir mayúsculas, con `\` o `/`, como `/c/…` de Git Bash, dentro de `file:///C:/…` y con los nombres cortos 8.3 de los componentes largos sin punto (`ABCDEFGHIJ` → `ABCDEF~N`, el caso de las rutas `%TEMP%` cortas); las rutas POSIX casan literalmente; (2) límites: la ruta solo casa en límite de componente (`/home/ana` no toca `/home/anabel`) y nunca dentro de una relativa (`docs/home/ana/…`); un punto final de frase sí cuenta como límite; (3) `raiz`/`home` aceptan también `Path` o una lista de alias equivalentes (la raíz real y la resuelta por un enlace); (4) se ignoran un usuario de menos de 3 caracteres (casaría con palabras como «a» o «yo») y una raíz que sea solo `/` o una unidad. Consumidores previstos: `panel_data.py` (F1-F4) y el almacén de actividad (F3); ningún llamante actual cambia (solo se añade API).

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

**Notas**: patrón de `MARKER` y de propiedad del HTML en `skills/plugin-panel/scripts/build_panel.py:19` y `:740` (`_write_html`); render actual en `build_panel.py:655-738`. Prohibido `innerHTML` (lo vigilan los arneses de `tests/test_panel_live_ui.py:70`). **Implementación (2026-10-15):** `panel_pages.py` expone `PAGES` (slug, archivo, título), `render_page(slug, modo, generado, datos, cuerpo, chart_ok)` y `json_seguro` (escapa `<`, `>`, `&`, U+2028/2029). La entrada «Plan» del menú apunta a `plan.html` (índice de planes, tercera de las siete); los `plan-<id16>.html` por iniciativa llegan en la fase 2: **desviación menor respecto a `design.md` §5.2**, que no lista `plan.html` pero exige siete entradas fijas. `render_page` inyecta `chartjs_disponible` en `panel-data` y solo pone el `<script src="vendor/…">` si `chart_ok`. CSP: modo exportado en `<meta>` con la política de T-03; modo servido sin `<meta>` (la pone el servidor, T-11, con la política de T-03; `CSP_SERVIDO` queda definida y sin usar aquí) y todas las páginas llevan `<link rel="icon" href="data:,">`. `panel-core.js`: menú plegable ≤ 760 px (`matchMedia`); sin JS el menú queda siempre visible; Escape solo actúa con el menú abierto. **Aviso de entorno:** `package.json` es `"type": "module"`, así que `require()` de un `assets/*.js` lo trata como ESM y `module.exports` no existe: los arneses Node leen `global.PanelCore` / `global.PanelCharts`, no el valor devuelto. **Desviación:** el linter marcó `panel_pages.py` (fuente con tildes) por no reconfigurar stdio; se le añadió el snippet y un modo `--list` (imprime el menú en JSON) con su entrada en `MODOS` de `tests/test_console_encoding.py`.

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

**Notas**: el repo no tiene un test de contraste previo; patrón de test que parsea un fichero real del bundle en `tests/test_panel_vendor.py` (T-02). Validación visual de la paleta: revisión del usuario M-01. **Implementación (2026-10-15):** paleta oscura única en `:root` de `panel.css` (`--fondo --superficie --texto --tenue --acento --ok --aviso --error --borde --foco --serie-1..6`); el test declara 26 pares (texto 4,5:1; bordes, foco y marcas 3:1; incluye el del enlace de salto) y además falla si hay un color literal fuera de `:root` (escaparía del cálculo). CA-39 (series no solo por color) queda repartido: la paleta da 6 colores distintos entre sí (test) y las formas (`FORMAS`, 6) y las etiquetas de la tabla equivalente las verifica T-07 (`test_las_formas_cubren_todas_las_series_de_la_paleta`). La validación visual sigue siendo la revisión del usuario M-01.

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

**Notas**: arnés Node con DOM falso y escenarios parametrizados en `tests/test_panel_live_ui.py:64-140` (`_live_script`, `HARNESS`). Política de ausencia `null` + etiqueta de `design.md` §5 (`panel_data.py`) y `build_dashboard.py:1169` («ausente = null, nunca 0»). **Implementación (2026-10-15):** `PanelCharts.dibujar(contenedor, spec, {chartDisponible})` crea `<figure class="grafico">` con `<figcaption>`, `<div class="lienzo"><canvas role="img" aria-label="título. descripción. Los mismos datos están en la tabla siguiente.">` y `<div role="region" tabindex="0" aria-label="Tabla equivalente: …">` con la `<table>` (`caption`, `th scope`). Un `null` va al dataset como `null` con `spanGaps:false` (Chart.js no dibuja la barra) y a la tabla como «sin datos» (`td.sin-datos`); si NINGÚN valor existe no se dibuja canvas y se muestra «Sin datos (origen: …)». `spec.parcial` pinta «Parcial: N de M (origen: …)». Si Chart.js falta, está marcado no disponible (`chartjs_disponible:false` del `panel-data`, que pone el exportador cuando su huella no coincide) o su constructor lanza, queda solo la tabla con el aviso «Chart.js no está disponible…». `panel-core.js` expone `celda`, `textoAusencia` y `renderAusencia`. Color por serie desde `--serie-N` (CSSOM, no inline) y forma por `FORMAS` (6); animación desactivada. Sin inserción de HTML, `eval` ni red (lo vigila el test). En navegador solo se comprobó el menú (T-05), no un gráfico real: el primer gráfico con Chart.js real es T-09.

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

**Notas**: CLI actual en `skills/plugin-panel/scripts/build_panel.py:766-810` (exclusiones de `--serve` en `:787`); propiedad por `MARKER` en `:740`. Piezas que describen (CONTRACTS E33): `commands/plugin-catalog.md`, `skills/plugin-panel/SKILL.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`. CSP del `<meta>` según la decisión de T-03. **Implementación (2026-10-15):** `panel_pages.exportar_sitio(destino, datos, generado, unsafe_link)` escribe 7 HTML + `assets/{panel.css,panel-core.js,panel-charts.js}` + `vendor/chart.js/{chart.umd.min.js,LICENSE.md,PROVENANCE.json}` + `export-manifest.json` (`generador`, `version`, `generado`, `ficheros[{ruta,sha256,bytes}]`). Propiedad: HTML con `MARKER` o fichero del manifiesto previo con el hash que se escribió; **todos los choques se comprueban ANTES de escribir** (nada a medias), un manifiesto ajeno o corrupto también aborta, y un fichero que el manifiesto previo listaba y ya no se genera se retira solo si su hash sigue igual. `build_panel._unsafe_link` (bloque replicado de rutas de nube) se inyecta como parámetro para no copiarlo a `panel_pages.py` (lo vigila `test_copias_declaradas`). Chart.js se verifica contra el `sha256` de `PROVENANCE.json` al exportar; si no coincide o falta, se omite todo `vendor/`, las páginas no cargan el script, `chartjs_disponible` va a `false` y sale un aviso por stderr (degrada, no falla). Datos personales: `redactar → anonimizar` sobre TODOS los textos del inventario (raíz, `--project`/`--root` y alias resueltos → `.`; home y `--home` → `~`; usuario de `getpass` → `<usuario>`; correos → `<correo>`) antes de incrustarlos; el test busca usuario, correo, home y raíz en cada fichero exportado (menos `vendor/`). El contenido de las páginas es provisional («Esta página todavía no muestra contenido.»); `catalogo.html` ya incrusta el inventario anonimizado (`panel-data.inventario`) y todas llevan `contadores`; el contenido real llega en T-09/T-10 y la fase 2. `render_html`, `TEMPLATE` y `references/panel.html` NO se tocan: el modo servido los sigue usando hasta T-11/T-12. Salida: sin `--json`, una línea de resumen sin rutas por stdout; con `--json`, el resumen va a stderr para no romper el JSON. **Desviaciones (ficheros fuera del `Archivos` original, todos por retirar `--html`):** `docs/PROJECT-EXTENSIONS.md` y su espejo EN citaban `--html panel.html`; `tests/test_panel_server.py:232` usaba `--html` como opción excluyente de `--serve` (ahora `--export`); `tests/test_panel_diagnostics.py:18` fija el `argument-hint` del comando (ahora `[carpeta de exportación] …`); `commands/plugin-catalog.md` cambió su `argument-hint` y su ejemplo, por lo que se **regeneró `interop/`** (5 ficheros: el comando de Codex —`SKILL.md` y `references/command.md`—, el de OpenCode y el índice de OpenCode). **Fallo preexistente corregido:** `tests/test_panel_vendor.py:118` (T-02) capturaba un subproceso en modo texto sin `encoding=`; `tests/test_console_encoding.py::test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8` lo detecta en la suite repo-wide y no estaba entre los tests corridos al cerrar T-02; se añadió `encoding='utf-8', errors='replace'`. Carpeta exportada de verdad comprobada en Chromium (Edge) y Firefox 142 con `file://` y red bloqueada: `violaciones: 0 · externas: 0`.

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

**Notas**: secciones de hoy en `skills/plugin-panel/references/panel.html:26` (anclas). Filtros de CA-29 en F4 (T-36). **Notas de implementación (2026-10-15):** los constructores de sección de `render_html` (`_cards`, `_extensions_html`, `_workflow_html`, `_flow_html`) siguen en `build_panel.py` (ahí está el inventario) y su HTML sale idéntico (comprobado con una comparación ad hoc contra el `render_html` de `HEAD`: `#catalog` solo difiere en un salto de línea de la plantilla, `#extensions`, `#workflow`, notas, cifras y flujo son byte a byte iguales). `build_panel.cuerpos_paginas(data, live, review_enabled, review_id, actividad)` devuelve el cuerpo de las 7 páginas; el exportador lo recibe ya anonimizado (`exportar_sitio(..., cuerpos=)`). `catalogo.html` lleva: flujo de etapas, cifras (`#inventario`), gráfico de piezas por tipo, `#catalog`, `#extensions`, `#workflow`, `#source-notes` y el pie. El gráfico usa `counts` de `--json` con la etiqueta «Acciones de hook» (los `counts.hooks` son acciones, no registros; las cifras de `#inventario` siguen diciendo «Registros de hook» como hoy); un conteo ausente va como `null` («sin datos»). `assets/page-catalogo.js` (filtros, ancla/hook, etapas y gráfico) expone `global.PanelCatalogo`; `connectFilters` es el de la plantilla anterior, ahora probado desde el asset. Desaparece la barra lateral y el héroe de marketing de la página única (el menú común las sustituye); las anclas `#catalog`, `#extensions`, `#workflow`, `#source-notes` se conservan. El CSS de componentes (tarjetas, controles, cifras, hooks…) se añade a `panel.css` solo con variables de `:root` (el test de paleta sigue verde). **Desviaciones (ficheros fuera del `Archivos` original):** `tests/panel_render.py` (ayuda de tests: renderiza una página como el exportador o el servidor), `tests/test_panel_export.py` (la lista de ficheros exportados suma `page-catalogo.js` y `page-diagnostico.js`), `panel.css`, `build_panel.py`. Los tests que antes llamaban `panel.render_html(data)` en `tests/test_plugin_panel.py` pasan a `pagina(panel, data, "catalogo")` (el de `connectFilters` se prueba cargando `page-catalogo.js`; se retiran las comprobaciones de los enlaces de la barra lateral, que ya no existe).

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

**Notas**: validador seleccionado en CONTRACTS E30 (`agent-kits/shared/diagnostic-report.py`); proyección portable en `agent-kits/shared/doctor.py:87-88`. **Notas de implementación (2026-10-15):** `_diagnostics_html` (validación de alcance y mensajes) no cambia; solo su `<h2>` pasa de «Diagnóstico» (el `<h1>` ya lo dice) a «Instantánea de doctor». El panel no ejecuta `doctor` ni busca informes: el cuerpo se genera con `data["diagnostics"]`, que sigue produciendo `build_inventory` solo si el usuario pasó `--diagnostics-report`. `assets/page-diagnostico.js` (nuevo, no estaba en `Archivos`) lleva los filtros que antes eran un script en línea y la navegación a las filas desde «Acciones prioritarias» (abre el `<details>`, resetea los filtros y enfoca la fila). `tests/test_panel_diagnostics.py` pasa de `panel.render_html(data)` a `pagina(panel, data, "diagnostico")` y se retira la aserción del enlace `href="#diagnostics"` de la barra lateral.

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

**Notas**: enrutado en `skills/plugin-panel/scripts/serve_panel.py:364-371` (`_route`) y `:381-393` (`do_GET`); validación en `:347-362` (`_allowed`); nonce en `:469-470`; CSP en `:492`. Patrón de tests 403 en `tests/test_panel_server.py:183-194`. **Notas de implementación (2026-10-15):** `create_server` pide a `panel_pages.cargar_assets("servido", review=…)` los ficheros (los JS vivos suman a los comunes; progreso y memoria obligatorios con el error opaco de antes, revisión solo si hay selección, actividad degrada con el aviso de la página) y los guarda en `server.assets` (ruta relativa → bytes, tipo); las 7 páginas se renderizan UNA vez con `render_page(modo="servido", nonce=…)` y quedan en `server.pages`; el nonce va en todas las etiquetas `<script …>` que genera la plantilla (también la de datos JSON), ya no por reemplazo del literal `<script>`. La raíz `<token>/` sirve `index.html`. `server.plan_pages` está vacío (las páginas `plan-<id16>.html` llegan en la Fase 2; la ruta existe y devuelve 404 si no está registrada, y 200 si la Fase 2 registra la página). Chart.js se comprueba contra `PROVENANCE.json` UNA vez al arrancar: si no coincide o falta, las páginas se sirven sin él (`chartjs_disponible:false`) y `run()` imprime el aviso por stderr; no falla. CSP servida = `panel_pages.CSP_SERVIDO` (decidida en T-03; añade `style-src 'self'` e `img-src data:` a la anterior). Si el render falla tras abrir el puerto, `create_server` cierra el socket antes de relanzar (nada a medias). Topes, token y validación Host/Origin/Sec-Fetch-Site sin cambios. Los comentarios nuevos de `serve_panel.py` son ASCII a propósito: ese fichero no declara modo de arranque en `test_console_encoding.py` y un símbolo no ASCII + el snippet de reconfiguración lo obligaría a declararlo (no tiene CLI propia).

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

**Notas**: extracción actual del JS inline en `tests/test_panel_live_ui.py:64` (`_live_script`); refresco de 5 s en `skills/plugin-panel/references/panel-live.js:63`. CONTRACTS E48/E51 (revisión): describen `docs/PLUGIN-PANEL.md`, `docs/FLOWS.md` (+EN); se actualizan en T-15. **Notas de implementación (2026-10-15):** `git mv` de `references/panel-{live,memory,activity,review}.js` a `assets/` (contenido intacto: mismos IDs DOM, mismos `api/progress`, `api/activity`, `api/memory`, `api/review/*`; no hay camino de escritura nuevo) y `git rm` de `references/panel.html`; desaparecen `TEMPLATE` y `render_html` de `build_panel.py` (la carpeta `references/` queda vacía y se elimina). Mapa de scripts por página en `panel_pages.LIVE_SCRIPTS` (solo modo servido): `inicio` → `panel-live.js`; `plan` → `panel-live.js` + `panel-review.js` (solo con `--review-initiative`); `agentes` → `panel-activity.js`; `memoria` → `panel-memory.js`. La página exportada nunca los carga ni llama a `api/*`. Cada sección viva se coloca en su página con los mismos IDs (`#operations` en Inicio y Plan, que nunca coinciden en la misma página; `#plan-review`, `#activity`, `#memory-query`), por eso «los IDs DOM se ajustan por página» no hizo falta más que en el reparto, no en los scripts. Los tests UI de memoria/actividad/revisión/progreso leen los JS de `assets/` y siguen prohibiendo `innerHTML`; los que degradaban si faltaba un asset ahora lo prueban sobre `cargar_assets` con `ASSETS_DIR` apuntando a una copia. `SKILL.md` cambia sus dos filas de referencias (la plantilla de una página sale; la vista de actividad apunta a `assets/`), y `docs/agents/CONTRACTS.md` E34 cita `cuerpos_paginas(live=True)` en lugar de `render_html(live=True)`. La documentación larga (`docs/PLUGIN-PANEL.md` y espejo EN: «/panel.html es un artefacto…») queda para T-15.

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
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-08, T-13
- **Tipo**: backend
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`, `skills/roadmap-dashboard/SKILL.md`, `tests/test_dashboard.py`, `commands/roadmap-status.md`, `skills/confluence-pull/SKILL.md`, `skills/confluence-publish/references/publish-and-sync.md`, `skills/plugin-panel/SKILL.md`, `docs/README.md`, `docs/en/README.md`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `docs/agents/ROLES.md`, `evals/cases/command-roadmap-status.json`, `evals/cases/skill-roadmap-dashboard.json`, `evals/cases/skill-plugin-panel.json`, `evals/cases/command-plugin-catalog.json`, `install/**`, `interop/**` (regenerado: `commands/` tocado)
- **Cubre (tests)**: E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_dashboard.py tests/test_panel_contract_golden.py` → `passed` · `python3 scripts/lint_plugin.py` → exit 0, sin citas rotas nuevas a `dashboard.html`/`--html` · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [ ] Al cerrar no quedan dos generadores HTML con el mismo rol (ADR-011): `grep -rn "render_html" skills/roadmap-dashboard` vacío.
- [ ] `--json`, `--md` y `--metrics-md` iguales; los cuatro comandos consumidores siguen funcionando.
- [ ] Las 13 referencias actuales a `dashboard.html`/`--html` fuera del roadmap están actualizadas (lista en `Notas`).
- [ ] La `description` de `roadmap-dashboard` deja de prometer HTML y la de `plugin-panel` absorbe «dashboard del roadmap», «panel del roadmap» y «kanban de los planes»; los casos de `evals/` casan con la `description` real.
- [ ] `ROLES.md`: `roadmap-dashboard` dueño de los datos de cartera; `plugin-panel` dueño de la presentación; `/roadmap-status` entrada de cartera que delega.
- [ ] El instalador copia `assets/` (incluido `vendor/`) del plugin.

**Subtareas**
- [ ] RED: retirar las aserciones de `render_html` de `tests/test_dashboard.py:376-397` y llevarlas a las tarjetas de Iniciativas (F2).
- [ ] Retirar `--html` y `render_html()`.
- [ ] Actualizar consumidores, ROLES, evals; regenerar `interop/`.

**Notas**: consumidores encontrados con grep (2026-10-15): `commands/roadmap-status.md:18,22,25`, `skills/confluence-pull/SKILL.md:105`, `skills/confluence-publish/references/publish-and-sync.md`, `skills/roadmap-dashboard/SKILL.md`, `skills/plugin-panel/SKILL.md`, `docs/README.md`, `docs/en/README.md`, `docs/PROJECT-EXTENSIONS.md`, `docs/en/PROJECT-EXTENSIONS.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md` y los dos casos de `evals/`. `design.md` §5 lista solo parte: los de `docs/PROJECT-EXTENSIONS.md` y `publish-and-sync.md` son adicionales. `render_html()` actual en `build_dashboard.py:573`; argumento en `:1117`.

### T-15 — Documentación de F1 (panel multi-página, modos, CSP, Chart.js)

- **Descripción**: Actualiza `docs/PLUGIN-PANEL.md` y su espejo EN, `docs/FLOWS.md` y `docs/en/FLOWS.md` (flujo del panel: un comando, dos modos, siete páginas) y `skills/plugin-panel/SKILL.md` (mapa ≤ 200 líneas).
- **Estado**: borrador
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 46k in / 7k out tok · 0,70 €
- **Dependencias**: T-12, T-14
- **Tipo**: docs
- **Archivos**: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/references/**`
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_skill_size.py` → `passed` · `python3 scripts/lint_plugin.py` → exit 0 · lectura: ES y EN describen lo mismo (modos, páginas, CSP, procedencia de Chart.js)

**Criterios de aceptación**
- [ ] `SKILL.md` de `plugin-panel` ≤ 200 líneas; el detalle va a `references/<tema>.md` con «lee X solo al llegar al paso Y».
- [ ] Espejos EN actualizados en el mismo cambio.
- [ ] Sin rutas absolutas ni datos personales.

**Subtareas**
- [ ] Redactar ES; espejar EN; comprobar tamaño.

**Notas**: TDD n/a: prosa. Piezas que describen según CONTRACTS E33/E34/E37/E48: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `skills/plugin-panel/SKILL.md`.

### T-16 — Cierre de la Fase 1: revisión de dos lentes y revisión visual del usuario (M-01)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals en verde; revisión adversarial de dos lentes sobre el diff de la fase (Lente C si `review-lens-select.py` la activa: toca CSP y servidor); bucle acotado a 3 con Minor al backlog; y el usuario revisa la fase en el navegador (M-01) antes de abrir la Fase 2.
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 6,3h · real — (revisión + corrección, f = 1,5)
- **Supervisión**: est. 2,6h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 2,88 M in / 469k out tok · 44,08 €
- **Dependencias**: T-01..T-15
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Cubre (tests)**: M-01
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: sección «Revisión de dos lentes — intento N: …» de la Fase 1 sin Critical ni Important abiertos, y línea «Revisión visual del usuario — Fase 1: aprobada AAAA-MM-DD» con el resultado de M-01

**Criterios de aceptación**
- [ ] CA-44 de la Fase 1: suites, linter y evals en verde.
- [ ] Revisión de dos lentes cerrada en ≤ 3 intentos; Minor anotados al backlog, no bloqueantes.
- [ ] El usuario aprueba M-01 en el navegador (servido y exportado).

**Subtareas**
- [ ] Ejecutar suites y puertas.
- [ ] Despachar `adversarial-review` sobre el diff de la fase.
- [ ] Pedir al usuario M-01 y anotar el resultado.

**Notas**: el contador de intentos y el worklog `[revisión]` son del orquestador. Cabecera de revisión con el formato `intento N: …` sin paréntesis tras N (la leen `jira-flow`/`task-brief`).

---

## Fase 2 — Inicio, Iniciativas y Plan

**Estado**: borrador · **Estimado**: 36,0h humanas · 10,8h IA · **Real**: — · **Coste est.**: 1.876 € referencia · ≈ 261 € ejecución · **Tokens est.**: 5,74 M

Criterios de la spec: CA-01 a CA-03 y CA-05 a CA-14. Incluye el campo `- **Cerrada**:` del diseño (I-02), que la evaluación dejaba fuera: diferencia declarada en `improvement-plan.md`.

### T-17 — `api/cartera` y proyección de cartera con las cifras de `--json`

- **Descripción**: `panel_data.cartera()` importa `build_dashboard.py` (`scan` + `vista_json`) y `progress-report.py` y proyecta lo que necesitan Inicio e Iniciativas. En servido, `api/cartera` (≤ 64 iniciativas, ≤ 64 KiB); en exportado, el mismo JSON incrustado.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-16
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `tests/test_panel_data.py`, `tests/test_panel_server.py`
- **Cubre (tests)**: API-01
- **Verificación**: `python3 -m pytest -q tests/test_panel_data.py tests/test_panel_server.py` → `passed` (cifras iguales a las de `build_dashboard.py --json` y `progress-report.py` sobre la fixture, ejecutando los scripts, no un oráculo copiado)

**Criterios de aceptación**
- [ ] Por iniciativa: estado de spec, «ilegible» con motivo, N/M tareas, horas y coste real/estimado y procedencia; ausente = `null` + etiqueta, nunca 0.
- [ ] Los ledgers > 256 KiB salen en una lista aparte y no suman en N ni en M (CA-02).
- [ ] `api/cartera` ≤ 64 KiB con 64 iniciativas; sin `?` en la ruta.
- [ ] El panel no recalcula cifras de cartera: las toma de `vista_json`.

**Subtareas**
- [ ] RED con la fixture de T-01 contra la salida real de los scripts.
- [ ] Proyección y ruta.

**Notas**: patrón de carga de módulos del bundle `_load_shared` en `skills/plugin-panel/scripts/serve_panel.py:35-40`; snapshot acotado de progreso en `serve_panel.py:120-134` (`progress_snapshot`); lector acotado `agent-kits/shared/local-read.py` (CONTRACTS E35). Lección de `usage-meter-transcripts`: los tests comparan contra el script.

### T-18 — Página Inicio: estados de spec, avance global y real frente a estimado

- **Descripción**: `index.html` muestra el número de iniciativas por estado de spec (gráfico + tabla), el avance global «N de M tareas completadas (P %)» y el coste real frente al estimado con la línea «procedencia: X medidos · Y estimados · Z desconocidos».
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-17
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-inicio.js`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_inicio_ui.py`
- **Cubre (tests)**: E2E-07, E2E-11
- **Verificación**: `python3 -m pytest -q tests/test_panel_inicio_ui.py` → `passed` (escenarios: estados variados, ilegible, ledger fuera de tope, sin estimación)

**Criterios de aceptación**
- [ ] CA-01: cifras por estado iguales a `--json`; la ilegible aparece como «ilegible» y no cuenta en ningún estado.
- [ ] CA-02: N y M iguales a la suma de `progress-report.py`; ledgers fuera de tope listados aparte.
- [ ] CA-03: una iniciativa sin estimación no suma 0; la procedencia se cuenta por tipo.
- [ ] Funciona en servido (vía `api/cartera`) y en exportado (JSON incrustado).

**Subtareas**
- [ ] RED en el arnés Node.
- [ ] Página y gráficos.

**Notas**: arnés en `tests/test_panel_live_ui.py:64-140`; adaptador de gráficos de T-07.

### T-19 — Página Iniciativas: kanban de solo lectura con alertas en texto y navegación a Plan

- **Descripción**: `iniciativas.html` muestra un kanban con una columna por estado y una tarjeta por iniciativa: slug, fecha, «N/M tareas (P %)», horas y coste real/estimado y alertas en texto. La tarjeta con plan navega a su Plan con ratón o Enter.
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-17
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-iniciativas.js`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_iniciativas_ui.py`, `tests/test_dashboard.py`
- **Cubre (tests)**: E2E-05, E2E-12
- **Verificación**: `python3 -m pytest -q tests/test_panel_iniciativas_ui.py` → `passed` (sin `draggable`, sin listeners de arrastre, alertas con texto, enlace `plan-<id16>.html`)

**Criterios de aceptación**
- [ ] CA-05: solo lectura; ningún control mueve tarjetas ni escribe en fichero.
- [ ] CA-06: cada alerta (ledger fuera de tope, gaps de revisión abiertos, `completado` con checkboxes sin marcar, sin estimación) lleva su texto.
- [ ] CA-08: la tarjeta con plan es un enlace activable con Enter que lleva a `plan-<id16>.html`.
- [ ] Las aserciones retiradas de `render_html` en T-14 tienen su equivalente aquí.

**Subtareas**
- [ ] RED con las alertas de la fixture.
- [ ] Kanban y navegación.

**Notas**: alerta de checkboxes sin marcar según `agent-kits/shared/ledger-lint.py:704`; id de iniciativa `sha256(carpeta)[:16]` de `skills/plugin-panel/scripts/serve_panel.py:184`.

### T-20 — Iniciativas: gráficos de horas y coste por iniciativa con tabla

- **Descripción**: Dos gráficos en Iniciativas: horas real frente a estimado y coste por iniciativa, cada uno con su tabla. Las iniciativas sin datos aparecen en la tabla con «sin datos» y fuera de las barras.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-19
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-iniciativas.js`, `tests/test_panel_iniciativas_ui.py`
- **Cubre (tests)**: E2E-07, E2E-13
- **Verificación**: `python3 -m pytest -q tests/test_panel_iniciativas_ui.py` → `passed` (iniciativa sin datos: fila «sin datos» en la tabla, ausente del dataset del gráfico)

**Criterios de aceptación**
- [ ] CA-07: dos gráficos con su tabla equivalente.
- [ ] CA-40: ningún 0 ni media en lugar de un dato ausente.

**Subtareas**
- [ ] RED; gráficos.

**Notas**: adaptador de T-07.

### T-21 — `ledger-view.py`: proyección pura de un `tasks.md`

- **Descripción**: Nuevo `agent-kits/shared/ledger-view.py`: tareas, fase, estado (vocabulario de `ledger-lint.ESTADOS`; desconocidos aparte con el literal), horas real/est con «(medido)»/«(estimado)», criterios con su casilla, `Verificación` (recortada a `VERIFICACION_MAX`), dependencias, enlace a historia archivada y última revisión con sus gaps abiertos. Reutiliza los parsers de `ledger-lint.py`; no crea un tercer lector de secciones de revisión (ADR-016).
- **Estado**: borrador
- **Tiempo humano**: est. 4,2h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-16
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-view.py`, `agent-kits/shared/test_ledger_view.py`, `agent-kits/shared/README.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_ledger_view.py` → `passed` (incluye el caso `intento N:` sin paréntesis, un `—` en horas que sale `null` y una tarea con historia en `execution-history.md` marcada «archivado»)

**Criterios de aceptación**
- [ ] Importa `parse_ledger`, `secciones_revision`, `ultimo_intento_para` y `filas_pendientes_de_tarea` de `ledger-lint.py`; ningún regex de cabecera de revisión propio.
- [ ] Un estado fuera del vocabulario va a `desconocidos` con su literal (CA-09).
- [ ] `—` o ausencia → `null`, nunca 0 (CA-13).
- [ ] Lee con `local-read.py` y el tope de 256 KiB; por encima devuelve «ledger fuera del tope» sin cifras.
- [ ] No mezcla el contenido de `execution-history.md` con el del ledger: solo enlaza (CA-10).

**Subtareas**
- [ ] RED con ledgers de fixture.
- [ ] Proyección pura y CLI `--json`.

**Notas**: parsers en `agent-kits/shared/ledger-lint.py:242` (`secciones_revision`), `:375` (`ultimo_intento_para`), `:414` (`filas_pendientes_de_tarea`), `:480` (`parse_ledger`); `ESTADOS` en `:61`; `VERIFICACION_MAX` en `:68`. Patrón de proyección pura con tests vecinos en `agent-kits/shared/progress-report.py:95` (`resumir`) y `agent-kits/shared/test_progress_report.py`. GOT de la cabecera: `intento N: …`.

### T-22 — Campo opcional `- **Cerrada**: AAAA-MM-DD` en el ledger

- **Descripción**: Añade el campo opcional `- **Cerrada**:` que escribe quien marca una tarea `completado` (mismo patrón que `- **Changelog**:`). `ledger-lint.py` valida solo el formato y que sea ≥ `creado`; `ledger-view.py` lo extrae; `implementer` y `/dev-cycle` lo escriben al cerrar.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-21
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`, `agent-kits/shared/ledger-view.py`, `agent-kits/shared/test_ledger_view.py`, `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py`, `agent-kits/shared/copias.json`, `agent-kits/planner/templates/tasks.md`, `agents/implementer.md`, `commands/dev-cycle.md`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**` (regenerado: `agents/` y `commands/` tocados)
- **Cubre (tests)**: —
- **Verificación**: `python3 -m pytest -q tests/test_ledger_lint.py agent-kits/shared/test_ledger_view.py tests/test_copias_declaradas.py` → `passed` · `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-15-panel-redesign/tasks.md` → 0 incoherencias · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [ ] Un ledger antiguo sin `Cerrada` sigue pasando `ledger-lint` sin avisos nuevos.
- [ ] `Cerrada` con formato inválido o anterior a `creado` → incoherencia con `fichero:línea`.
- [ ] Si `CAMPO_LEDGER_PATTERN` está en un bloque replicado de `copias.json`, sus copias (`task-brief.py`, `jira-flow.py`) se actualizan en el mismo cambio y `test_copias_declaradas` pasa.
- [ ] `agents/implementer.md` y `commands/dev-cycle.md` dicen cuándo escribirlo; `interop/` regenerado.

**Subtareas**
- [ ] RED en `tests/test_ledger_lint.py`.
- [ ] Validación, extracción y prosa; regenerar `interop/`.

**Notas**: patrón del campo opcional `Changelog` en `agent-kits/shared/ledger-lint.py:80-104` (`CAMPO_LEDGER_PATTERN` en `:102`). Bloques replicados con canónico en `ledger-lint.py` declarados en `agent-kits/shared/copias.json:75` y `:265`. Diferencia con la evaluación: la evaluación dejaba I-02 fuera; `design.md` §2.4 lo incluye y el orquestador lo pide: +2,4h humanas / +1,2h IA declaradas en `improvement-plan.md`. Piezas que describen: `docs/agents/implementer.md` (+ fila de `docs/README.md` si cambia el rol) y `docs/CONVENTIONS.md` regla 8 (+EN).

### T-23 — `api/plan-<id16>` y kanban de tareas en la página Plan

- **Descripción**: `plan-<id16>.html` muestra un kanban de solo lectura con una columna por estado del vocabulario del ledger y una franja «estado no reconocido» con el literal; tarjeta por `T-XX` con ID, título, fase, horas real/estimado y nº de gaps. En servido, `api/plan-<id16>` (≤ 64 KiB).
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-21
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/panel_pages.py`, `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `tests/test_panel_server.py`
- **Cubre (tests)**: API-02, E2E-14
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py tests/test_panel_server.py` → `passed` (5 columnas exactas + franja de desconocidos; respuesta ≤ 65.536 bytes con el ledger de fixture más grande)

**Criterios de aceptación**
- [ ] CA-09: solo las 5 columnas del vocabulario; desconocidos en su franja con el literal.
- [ ] La respuesta solo trae lo del kanban (ID, título, fase, estado, real/est, nº de gaps); el detalle va por T-24.
- [ ] Ledger > 256 KiB → «ledger fuera del tope de lectura (256 KiB)» sin cifras.

**Subtareas**
- [ ] RED; ruta, proyección y página.

**Notas**: `ledger-view.py` de T-21; patrón de ruta con parámetro sin `?` según `design.md` §2.4 I-04 y `serve_panel.py:374-380` (`_review_route`).

### T-24 — `api/plan-<id16>-<T-XX>` y detalle de tarea accesible

- **Descripción**: Al abrir una tarjeta (clic o Enter) se muestra su detalle: descripción, criterios con casilla, `Verificación` (y su salida si existe), dependencias, última «Revisión de dos lentes — intento N» con sus gaps abiertos y severidad, y el enlace «archivado» si tiene historia. Escape lo cierra devolviendo el foco a la tarjeta.
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-23
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`, `tests/test_panel_server.py`
- **Cubre (tests)**: API-03, E2E-05, E2E-14
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py tests/test_panel_server.py` → `passed` (Escape devuelve el foco a la tarjeta; `Verificación` recortada a 2.000 caracteres; enlace «archivado»)

**Criterios de aceptación**
- [ ] CA-10: todos los campos listados; el contenido de `execution-history.md` nunca aparece como si estuviera en el ledger.
- [ ] CA-37: el detalle es alcanzable con Tab en orden de lectura y Escape devuelve el foco.
- [ ] Todo texto pasa por `redact.redactar` + `redact.anonimizar` antes de salir.

**Subtareas**
- [ ] RED; ruta del detalle y diálogo.

**Notas**: redacción del servidor antes de recortar según CONTRACTS E37 (`serve_panel.py` → `agent-kits/shared/redact.py`); tope de 160 caracteres de títulos en `serve_panel.py:139`.

### T-25 — Plan: avance por fase y real frente a estimado

- **Descripción**: Gráficos del Plan: avance por fase (completadas/total) con las mismas cifras que el «Resumen de progreso» del ledger, y real frente a estimado por fase y por tarea con «(medido)»/«(estimado)».
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-23
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`
- **Cubre (tests)**: E2E-07, E2E-15
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (cifras por fase iguales a las de la tabla «Resumen de progreso» del ledger de fixture; `—` no se pinta como 0)

**Criterios de aceptación**
- [ ] CA-11: avance por fase con su tabla, cifras iguales al resumen del ledger.
- [ ] CA-13: real frente a estimado por fase y por tarea con su procedencia; `—` = «sin datos».

**Subtareas**
- [ ] RED; gráficos.

**Notas**: adaptador de T-07; proyección de T-21.

### T-26 — Plan: burndown solo con fechas de cierre completas

- **Descripción**: Si todas las tareas `completado` llevan `Cerrada`, el Plan dibuja el burndown de pendientes por fecha; si no, muestra «burndown no disponible: N de M tareas completadas sin fecha de cierre», sin gráfico parcial ni interpolado.
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-22, T-25
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `skills/plugin-panel/scripts/panel_data.py`, `tests/test_panel_plan_ui.py`
- **Cubre (tests)**: E2E-07, E2E-15
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (ledger con todas las fechas → serie; con una sin fecha → mensaje con N y M y sin `<canvas>`)

**Criterios de aceptación**
- [ ] CA-12: burndown solo con fechas completas; mensaje exacto en el otro caso.
- [ ] CA-40: ningún punto interpolado.

**Subtareas**
- [ ] RED; serie y mensaje.

**Notas**: regla de dibujo de `design.md` §2.4 I-02.

### T-27 — Plan: refresco vivo sin perder la tarea abierta

- **Descripción**: En servido, el kanban del Plan refresca cada 5 s por `api/plan-<id16>` y refleja el nuevo estado sin recargar ni cerrar la tarea abierta; un fallo de red conserva lo anterior con su aviso.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-24
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-plan.js`, `tests/test_panel_plan_ui.py`
- **Cubre (tests)**: E2E-16
- **Verificación**: `python3 -m pytest -q tests/test_panel_plan_ui.py` → `passed` (dos ciclos de 5.000 ms con un estado cambiado: tarjeta movida, detalle abierto y foco conservados)

**Criterios de aceptación**
- [ ] CA-14: tras dos ciclos (10 s) el kanban refleja el cambio sin recargar y sin perder la tarea abierta.
- [ ] El sondeo se pausa con la pestaña oculta y se cancela al refrescar a mano (comportamiento de `panel-live.js`).

**Subtareas**
- [ ] RED con temporizadores falsos.
- [ ] Refresco con conservación de DOM.

**Notas**: patrón de sondeo y conservación de DOM en `skills/plugin-panel/references/panel-live.js:63` (movido a `assets/` en T-12) y escenario `preserve_dom_unchanged` de `tests/test_panel_live_ui.py`.

### T-28 — Documentación de F2 (Inicio, Iniciativas, Plan, `ledger-view`, `Cerrada`)

- **Descripción**: Documenta las tres páginas, las API `api/cartera` y `api/plan-*`, la relación `plugin-panel` → `build_dashboard` y `plugin-panel` → `ledger-view` en CONTRACTS, y el campo `Cerrada`.
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-18..T-27
- **Tipo**: docs
- **Archivos**: `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `agent-kits/shared/README.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 scripts/lint_plugin.py` → exit 0 (ninguna fila de CONTRACTS sin Puerta) · lectura: espejos EN iguales en contenido

**Criterios de aceptación**
- [ ] Aristas nuevas en CONTRACTS con su Puerta ejecutable (test de T-17 y T-21) y sus «Piezas que describen».
- [ ] ES y EN en el mismo cambio.

**Subtareas**
- [ ] Redactar y espejar.

**Notas**: TDD n/a: prosa. Formato de arista en `docs/agents/CONTRACTS.md:96-103` (E30-E37).

### T-29 — Cierre de la Fase 2: revisión de dos lentes y revisión visual del usuario (M-02)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals en verde; revisión de dos lentes sobre el diff de la fase; bucle acotado a 3 con Minor al backlog; el usuario revisa Inicio, Iniciativas y Plan en el navegador (M-02).
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 5,4h · real — (revisión + corrección, f = 1,0, incluida la parte de `Cerrada`)
- **Supervisión**: est. 2,35h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 2,47 M in / 402k out tok · 37,78 €
- **Dependencias**: T-17..T-28
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Cubre (tests)**: M-02
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_ledger_lint.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py agent-kits/shared/test_ledger_view.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: «Revisión de dos lentes — intento N: …» de la Fase 2 sin Critical ni Important abiertos y «Revisión visual del usuario — Fase 2: aprobada AAAA-MM-DD»

**Criterios de aceptación**
- [ ] CA-44 de la Fase 2.
- [ ] Revisión cerrada en ≤ 3 intentos.
- [ ] El usuario aprueba M-02.

**Subtareas**
- [ ] Suites y puertas; `adversarial-review`; M-02.

**Notas**: la Lente A comprueba que CA-01, CA-02 y CA-11 se testean contra los scripts reales.

---

## Fase 4 — Memoria, Catálogo y Diagnóstico

**Estado**: borrador · **Estimado**: 26,4h humanas · 7,2h IA · **Real**: — · **Coste est.**: 1.370 € referencia · ≈ 190 € ejecución · **Tokens est.**: 3,83 M

Se ejecuta ANTES que la Fase 3 (orden de la evaluación). Criterios de la spec: CA-22 a CA-31. Fuentes en solo lectura; si una no trae un dato por su `--json`, se muestra «sin datos» y no se amplía su contrato (`doctor.py`, `journal.py` y `knowledge-find.py` son hotspots).

### T-30 — Memoria: entradas por tipo, estado y área (y `api/memoria`)

- **Descripción**: `memoria.html` muestra un gráfico y una tabla de entradas por tipo (ADR, gotcha, lección) y estado (`aceptada · propuesta · obsoleta`), filtrables por área. La proyección sale de `knowledge-view.snapshot`; en servido, por `api/memoria` (GET, ≤ 64 KiB) porque `api/memory` solo admite `search`/`show`/`related`.
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/assets/page-memoria.js`, `tests/test_panel_memoria_ui.py`, `tests/test_panel_memory_server.py`
- **Cubre (tests)**: API-06, E2E-20
- **Verificación**: `python3 -m pytest -q tests/test_panel_memoria_ui.py tests/test_panel_memory_server.py` → `passed` (conteos iguales a `knowledge-find.py --json` sobre la fixture; filtro por área)

**Criterios de aceptación**
- [ ] CA-22: tipo × estado con gráfico y tabla; filtro por área con teclado.
- [ ] `api/memory` (POST) no cambia; `api/memoria` respeta 64 KiB y la redacción antes de recortar.

**Subtareas**
- [ ] RED; proyección, ruta y página.

**Notas**: proyección existente `agent-kits/shared/knowledge-view.py:60` (`snapshot`) y `:224` (`query`, operaciones en `:50-57`); orden de estados en `agent-kits/shared/knowledge-find.py:140`. `design.md` §2.4 I-04 no asigna API a Memoria: `api/memoria` es una ruta nueva de este plan (declarada como diferencia). CONTRACTS E38-E42.

### T-31 — Memoria: bandeja del curador de solo lectura

- **Descripción**: La bandeja muestra el número y la lista de candidatos de `docs/knowledge/candidates/` por estado (`pending`, `needs_changes`, `rejected`) y lo aprobado en `docs/knowledge/approved/`. Sin acciones.
- **Estado**: borrador
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
- [ ] CA-23: conteo y lista por estado; ninguna acción del curador (ADR-018).

**Subtareas**
- [ ] RED; bandeja.

**Notas**: dueño único de las decisiones: `agent-kits/shared/knowledge-curation.py` (CONTRACTS E53); el panel solo lee.

### T-32 — Memoria: línea de tiempo con sucesores y «vigente»

- **Descripción**: Línea de tiempo de entradas por fecha con su cadena de sucesión; las que rigen hoy (sin sucesor, no obsoletas) llevan «vigente».
- **Estado**: borrador
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
- [ ] CA-24: orden por fecha, cadena visible y «vigente» en texto.

**Subtareas**
- [ ] RED; línea de tiempo.

**Notas**: sucesión desde `knowledge-find.py` (`--related`, `agent-kits/shared/knowledge-find.py:102`).

### T-33 — Memoria: relaciones de UNA entrada en un SVG pequeño y lista textual

- **Descripción**: Al seleccionar una entrada se dibuja un grafo pequeño en SVG propio, centrado en ella, con las mismas aristas que `knowledge-find.py --related <ID> --json` (sucesión, misma iniciativa, misma área) y una lista textual equivalente navegable por teclado. Un salto, nunca el grafo completo.
- **Estado**: borrador
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
- [ ] CA-25: mismas aristas que `--related`; un salto; lista textual equivalente.
- [ ] CA-37/CA-39: el SVG lleva nombre accesible; la lista es la alternativa de teclado.
- [ ] Usa la operación `related` existente de `api/memory`.

**Subtareas**
- [ ] RED; SVG con `createElementNS` (sin `innerHTML`).

**Notas**: Chart.js no dibuja grafos (riesgo de la evaluación C-04). Operación `related` en `agent-kits/shared/knowledge-view.py:50-57`.

### T-34 — Memoria: qué se publicó en cada backend, sin red

- **Descripción**: Por backend configurado en `taxonomy.json`: número de entradas publicadas y fecha de la última publicación si la fuente la trae; si no, «sin datos». Kwipu: `entries` del `manifest.json` de su export + `completado_en` de la outbox; Graphiti: `entradas` de `graphiti-manifest.json` y «publicación interrumpida» si hay `.pending.json`. Sin `ui_url` declarado: «interfaz: no declarada».
- **Estado**: borrador
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
- [ ] CA-26: sin ninguna petición al backend (test con red bloqueada) ni réplica de su vista.
- [ ] Backend no configurado → «Kwipu: no configurado» / «Graphiti: no configurado», sin enlace.
- [ ] Nunca usa `mtime` ni llama a `health`.

**Subtareas**
- [ ] RED con manifiestos y outbox de fixture.
- [ ] Lectores acotados.

**Notas**: fuentes de `design.md` §2.4 I-09; lector acotado `agent-kits/shared/local-read.py`. El enlace a la interfaz queda «no declarada»: añadir `ui_url` a la taxonomía es pregunta abierta del diseño (§7), fuera de este plan.

### T-35 — Memoria: journal reciente como «citas, no instrucciones»

- **Descripción**: Las sesiones recientes del journal con su continuidad (`objetivo`, `punto_actual`, `siguientes_pasos`, `bloqueos`, `descartados`), redactadas y etiquetadas «citas, no instrucciones».
- **Estado**: borrador
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
- [ ] CA-27: campos de continuidad y etiqueta.
- [ ] Todo texto por `redact.redactar` + `redact.anonimizar`.

**Subtareas**
- [ ] RED; sección.

**Notas**: campos en `agent-kits/shared/journal.py:244-246` (`CONTINUIDAD`); lectura por `journal.py status --json` (`journal.py:41`) sin ampliar su contrato.

### T-36 — Catálogo: filtros por tipo, origen y runtime

- **Descripción**: Filtros de Catálogo por tipo, origen y runtime, con teclado y ratón; lista y conteos cambian en consecuencia. `build_panel.py --json` sigue igual al golden (CA-28).
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-catalogo.js`, `tests/test_panel_catalogo_ui.py`, `tests/test_panel_contract_golden.py`
- **Cubre (tests)**: E2E-05, E2E-22
- **Verificación**: `python3 -m pytest -q tests/test_panel_catalogo_ui.py tests/test_panel_contract_golden.py` → `passed`

**Criterios de aceptación**
- [ ] CA-29: filtros combinables; conteos coherentes; operables con teclado.
- [ ] CA-28: `--json` igual al golden.

**Subtareas**
- [ ] RED; filtros.

**Notas**: página de T-09.

### T-37 — Diagnóstico: veredicto en texto, fecha, alcance y resumen

- **Descripción**: Una fila por comprobación con su veredicto ✅/⚠️/❌ también en texto, su fecha y su alcance, y un resumen con el número de cada veredicto; sin informe, de otro proyecto u otro formato, «sin informe» o el motivo del rechazo y el comando para generarlo.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 183k in / 30k out tok · 2,80 €
- **Dependencias**: T-29
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-diagnostico.js`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_diagnostics.py`
- **Cubre (tests)**: E2E-23
- **Verificación**: `python3 -m pytest -q tests/test_panel_diagnostics.py` → `passed` (texto «OK/aviso/error» junto al icono; resumen con los tres contadores; rechazo con el comando)

**Criterios de aceptación**
- [ ] CA-30: fila por comprobación, veredicto en texto, fecha, alcance y resumen.
- [ ] CA-31: no ejecuta `doctor` ni busca informes.

**Subtareas**
- [ ] RED; página.

**Notas**: proyección `doctor.py --panel-json` (`agent-kits/shared/doctor.py:87-88`, `:2795`); validador de CONTRACTS E30.

### T-38 — Documentación de F4 (Memoria, Catálogo, Diagnóstico)

- **Descripción**: Documenta las tres páginas, `api/memoria` y la regla «sin datos antes que ampliar contratos de hotspots».
- **Estado**: borrador
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
- [ ] Arista `serve_panel` → `api/memoria` declarada con su Puerta.
- [ ] ES y EN en el mismo cambio; `SKILL.md` ≤ 200 líneas.

**Subtareas**
- [ ] Redactar y espejar.

**Notas**: TDD n/a: prosa. CONTRACTS E42 describe `commands/plugin-catalog.md`, `skills/plugin-panel/SKILL.md`, `docs/PLUGIN-PANEL.md` (+EN).

### T-39 — Cierre de la Fase 4: revisión de dos lentes y revisión visual del usuario (M-03)

- **Descripción**: Puerta de la fase: suites de CA-44, linter y evals; revisión de dos lentes; bucle acotado a 3; el usuario revisa Memoria, Catálogo y Diagnóstico en el navegador (M-03).
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 3,6h · real — (revisión + corrección, f = 1,0)
- **Supervisión**: est. 1,9h (≈25 % IA + 1h de revisión manual) · real —
- **Previsión IA**: 1,65 M in / 268k out tok · 25,19 €
- **Dependencias**: T-30..T-38
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Cubre (tests)**: M-03
- **Verificación**:
  - `python3 -m pytest -q tests/test_plugin_panel.py tests/test_panel_*.py tests/test_dashboard.py tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py agent-kits/shared/test_agent_activity.py` → `0 failed`
  - `python3 scripts/lint_plugin.py` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 scripts/export-interop.py --check` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-15-panel-redesign` → exit 0
  - lectura: «Revisión de dos lentes — intento N: …» de la Fase 4 sin Critical ni Important abiertos y «Revisión visual del usuario — Fase 4: aprobada AAAA-MM-DD»

**Criterios de aceptación**
- [ ] CA-44 de la Fase 4.
- [ ] Revisión cerrada en ≤ 3 intentos.
- [ ] El usuario aprueba M-03.

**Subtareas**
- [ ] Suites y puertas; `adversarial-review`; M-03.

**Notas**: la Lente A comprueba que ningún hotspot (`doctor.py`, `journal.py`, `knowledge-find.py`) cambió de contrato.

---

## Fase 3 — Agentes en vivo + cierre transversal

**Estado**: borrador · **Estimado**: 45,6h humanas · 23,4h IA · **Real**: — · **Coste est.**: 2.444 € referencia · ≈ 506 € ejecución · **Tokens est.**: 12,44 M

Última fase. Criterios de la spec: CA-04, CA-15 a CA-21 y CA-42 (eventos); además, el cierre transversal C-05. **Lente C obligatoria** en toda tarea de captura (condición 4 de la evaluación). Valores de diseño: 0 ms síncronos añadidos (O5), historial de 500 eventos / 256 KiB / 24 h, entrada ≤ 2 MiB, resumen ≤ 160.

### T-40 — Puerta de entrada de F3: condiciones de la evaluación y latencia base

- **Descripción**: Antes de tocar el hook, comprueba las cuatro condiciones de la evaluación y mide la latencia del hook actual. No escribe código del producto.
- **Estado**: borrador
- **Tiempo humano**: est. 1,8h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 137k in / 22k out tok · 2,10 €
- **Dependencias**: T-39
- **Cubre (tests)**: —
- **Archivos**: `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Verificación**: lectura: en `Notas` de esta tarea, las cuatro condiciones marcadas con su evidencia (sección de `design.md`, respuesta del usuario con fecha, URL de la doc de Codex, configuración de la Lente C) y las líneas `Hooks: PostToolUse:… (Nms)` del log de Claude Code con la latencia base

**Criterios de aceptación**
- [ ] Condición 1: `design.md` tiene la sección «estados intermedios y su recuperación» de `events.json` (bloqueo ocupado, CAS fallido, escritura cortada, eventos asíncronos fuera de orden). Si no está, se pide al architect antes de seguir (el planner no la escribe).
- [ ] Condición 2: el usuario confirma o cambia I-05 (0 ms síncronos) e I-03 (500 / 256 KiB / 24 h); la respuesta y su fecha quedan en `Notas`.
- [ ] Condición 3: la evidencia de Codex (PreToolUse/PostToolUse sin identificador de subagente) se cita con URL y fecha de consulta.
- [ ] Condición 4: la Lente C se despacha en T-54 aunque `review-lens-select.py` no la active.
- [ ] Latencia base medida y anotada.

**Subtareas**
- [ ] Revisar `design.md` §1-§2.4.
- [ ] Preguntar al usuario I-03/I-05 (valores del diseño por defecto).
- [ ] Medir y anotar.

**Notas**: condiciones en `evaluation.md` «Recomendación». Medición de I-05 según `design.md` §2.4 («líneas `Hooks: PostToolUse:… (Nms)`»). Presupuesto actual del hook en `hooks/run-hook.mjs:26`.

### T-41 — Proyección pura de runs, ventanas y eventos en `agent-activity.py`

- **Descripción**: Añade a `agent-kits/shared/agent-activity.py` las constantes del historial (500 eventos, 256 KiB, 24 h, entrada 2 MiB, resumen 160) y la proyección pura de runs (`en curso` / `sin señal reciente` con duración congelada / `respuesta terminada`), ventanas de atribución (`abierta` → `cerrada` | `reemplazada` | `caducada`) y la regla de atribución a `T-XX`.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-40
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity.py`, `agent-kits/shared/test_agent_activity.py`
- **Cubre (tests)**: E2E-17, E2E-18
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_agent_activity.py` → `passed` (incluye: run con 61 s → «sin señal reciente» y duración congelada; dos ventanas abiertas → «sin atribuir»; `lote-<n>` nunca atribuye; `cerrada → abierta` sin `start` rechazado)

**Criterios de aceptación**
- [ ] CA-18: atribución solo con exactamente una ventana abierta en el run o, si no tiene, en la sesión padre; si no, «sin atribuir».
- [ ] CA-19: más de 60 s → «sin señal reciente»; nunca «terminado» ni «muerto» inferidos.
- [ ] CA-21: el recorte por antigüedad descarta el más antiguo y cuenta `recortado`.
- [ ] `FRESH_SECONDS` (60) y `MAX_OBSERVATIONS` (64) del snapshot no cambian.

**Subtareas**
- [ ] RED en `test_agent_activity.py`.
- [ ] Constantes y proyecciones puras.

**Notas**: patrón de proyección pura con `now` inyectado en `agent-kits/shared/agent-activity.py:48` (`project_activity`); constantes en `:9-10`. Estados de `design.md` §1 «Invariantes».

### T-42 — Resumen redactado por lista blanca y `Authorization: Basic` en el redactor

- **Descripción**: Resumen del argumento por herramienta en lista blanca (`design.md` §2.4 I-07: 1.ª línea del comando, rutas relativas, patrón + ruta, host, tipo de subagente, nombre de skill, «—» para MCP y desconocidas), en el orden fijo redactar → anonimizar → quitar controles → recortar a 160. Amplía `_SECRETOS_RE` con `Authorization: Basic …` en el canónico y en su copia declarada.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-41
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/redact.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_redact.py`, `tests/test_agent_activity_store.py`, `tests/test_copias_declaradas.py`
- **Cubre (tests)**: E2E-18
- **Verificación**: `python3 -m pytest -q agent-kits/shared/test_redact.py tests/test_agent_activity_store.py tests/test_copias_declaradas.py` → `passed` (corpus de secretos de `redact.py` + `Authorization: Basic`: ningún secreto en el resumen persistido ni mostrado)

**Criterios de aceptación**
- [ ] CA-17: el resumen persistido y el mostrado pasan por `redact.py` y no contienen el secreto (corpus completo).
- [ ] CA-16: nunca contenido de ficheros, salidas, prompts ni chain-of-thought; MCP y desconocidas → «—».
- [ ] CA-41: rutas relativas al proyecto, sin home, usuario ni correos.
- [ ] El bloque replicado de `redact.py` y su copia en `journal.py` siguen idénticos.

**Subtareas**
- [ ] RED con el corpus.
- [ ] Lista blanca y orden fijo; ampliar `_SECRETOS_RE` en los dos sitios.

**Notas**: `_SECRETOS_RE` en `agent-kits/shared/redact.py:35`; copia declarada en `agent-kits/shared/copias.json:297-310` (canónico `redact.py`, respaldo `journal.py`). Precedente de 160 caracteres en `skills/plugin-panel/scripts/serve_panel.py:139`. Lente C.

### T-43 — Almacén `events.json`: anillo acotado, CAS, retención y opt-out sin escritura

- **Descripción**: `agent-activity-store.py` añade `events.json` al directorio propio (inventario de 4 a 5 nombres + `.lock`): `runs` (≤ 64), `ventanas` (≤ 64) y `events` (anillo 500 / 256 KiB / 24 h), reemplazo atómico con CAS como `snapshot.json`, `recortado`, `descartados_por_tamano` sin identidad y tope de entrada de 2 MiB solo en memoria. Sin `sesion.actividad: true` no escribe nada.
- **Estado**: borrador
- **Tiempo humano**: est. 4,2h · real —
- **Tiempo IA (ejec.)**: est. 1,0h · real —
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 457k in / 74k out tok · 7,00 €
- **Dependencias**: T-42
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_store.py`, `tests/test_agent_activity_git.py`, `tests/test_graphiti_security.py`
- **Cubre (tests)**: E2E-19
- **Verificación**: `python3 -m pytest -q tests/test_agent_activity_store.py tests/test_agent_activity_git.py tests/test_graphiti_security.py` → `passed` (opt-out: el directorio de estado no cambia; 501 eventos → 500 y `recortado: 1`; entrada de 2 MiB + 1 → contador; escrituras concurrentes sin pérdida de integridad)

**Criterios de aceptación**
- [ ] CA-20: con `sesion.actividad` ausente o `false`, ningún fichero nuevo ni modificado (test con huella del directorio).
- [ ] CA-21: tope y retención; la escritura fallida no rompe nada y el llamante sale con 0.
- [ ] Estados intermedios de la condición 1 cubiertos por test: bloqueo ocupado (evento perdido, sin reintento que añada latencia), CAS fallido, escritura cortada.
- [ ] `snapshot.json` y su contrato (60 s, 64 filas, 64 KiB, `api/activity`, `doctor`) no cambian.
- [ ] Nueva huella `sha256_lf` de `agent-activity-store.py` y `redact.py` en sus `dependencies` en `_CARGAS_LOCALES_REVISADAS`, tras revisión.
- [ ] `.gitignore` del directorio propio sigue cubriendo el fichero nuevo.

**Subtareas**
- [ ] RED: opt-out, tope, retención, concurrencia.
- [ ] Inventario, CAS y anillo.
- [ ] Huella revisada.

**Notas**: inventario cerrado en `agent-kits/shared/agent-activity-store.py:119-122`; opt-in en `:92-100` (`_enabled`); tope de entrada actual en `:20` y `:264-266`; captura y CAS en `:185-233` (`capture`). Huella en `tests/test_graphiti_security.py:159-165`. Familia de riesgo de `session-end-durable-capture` (LES-016). Lente C.

### T-44 — Eventos de herramienta por runtime y ventanas por gramática exacta

- **Descripción**: `_payload` acepta los eventos de herramienta: Claude `PostToolUse` (ok) y `PostToolUseFailure` (error) con `agent_id`/`agent_type` y `duration_ms`; Codex `PostToolUse` agrupado por sesión, sin duración y resultado «sin datos»; OpenCode `tool.execute.after` con `sessionID`, `agent` y `status`. Reconoce `usage-meter.py start|close --artefacto <slug>/T-XX` solo por regex anclada sobre el argv de un evento Bash/shell.
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real —
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 366k in / 60k out tok · 5,60 €
- **Dependencias**: T-43
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_store.py`, `tests/test_graphiti_security.py`
- **Cubre (tests)**: E2E-17, E2E-18
- **Verificación**: `python3 -m pytest -q tests/test_agent_activity_store.py tests/test_graphiti_security.py` → `passed` (texto libre con `T-07` en commit, grep o prompt de Agent → «sin atribuir»; `-fixN` normalizado a `T-XX`; Codex sin subagente → run de sesión)

**Criterios de aceptación**
- [ ] CA-16: por evento, hora, herramienta, resumen, `T-XX` si se atribuyó, duración y resultado (`ok`/`error`/`null`).
- [ ] CA-18: test negativo con `T-XX` en texto libre; nunca proximidad temporal.
- [ ] Nunca persiste `tool_response`, contenido, salidas, prompts ni rutas absolutas.
- [ ] Un runtime o evento desconocido se descarta con su código, sin excepción hacia el hook.

**Subtareas**
- [ ] RED por runtime con payloads de la doc oficial (citados en T-40).
- [ ] Mapeo y gramática exacta.

**Notas**: `_payload` actual en `agent-kits/shared/agent-activity-store.py:155-178`; argumento `--artefacto` en `agent-kits/shared/usage-meter.py:730`. Tabla de runtimes de `design.md` §1. Lente C.

### T-45 — Registro de hooks: `PostToolUse` y `PostToolUseFailure` asíncronos e interop

- **Descripción**: `hooks/hooks.json` añade grupos `PostToolUse` (sin matcher) y `PostToolUseFailure` con `agent-activity`, `"async": true` y `timeout: 5`. `export-interop.py` conserva el matcher del grupo de actividad en el `PostToolUse` de Codex (hoy fuerza `^apply_patch$` en todo grupo) y omite `PostToolUseFailure`. Se regenera `interop/`.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-44
- **Tipo**: hooks
- **Archivos**: `hooks/hooks.json`, `scripts/export-interop.py`, `tests/test_export_interop.py`, `tests/test_hooks_shell.py`, `interop/**` (regenerado: `hooks/` tocado)
- **Cubre (tests)**: E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_export_interop.py tests/test_hooks_shell.py` → `passed` · `python3 scripts/export-interop.py --check` → exit 0 · `python3 scripts/lint_plugin.py` → exit 0 (commands de `hooks.json` existentes y ejecutables)

**Criterios de aceptación**
- [ ] Los grupos de actividad son `async` en Claude y Codex; el resto de grupos `PostToolUse` no cambia.
- [ ] Codex: el grupo de actividad conserva su matcher; los demás siguen con `^apply_patch$`; sin `PostToolUseFailure`.
- [ ] CA-42: `export-interop.py --check` pasa.

**Subtareas**
- [ ] RED en `test_export_interop.py`.
- [ ] Registro y traducción; regenerar `interop/`.

**Notas**: grupos actuales en `hooks/hooks.json:34-50`; matcher forzado en `scripts/export-interop.py:407-408`. Lente C.

### T-46 — Atajo del launcher: sin opt-in no se lanza Python

- **Descripción**: En `hooks/run-hook.mjs`, para `agent-activity`, Node lee `.claude/dev.json` (≤ 64 KiB, `node:fs`) y sale con 0 antes de lanzar Python si `sesion.actividad !== true`. Nueva huella del launcher tras revisión.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-45
- **Tipo**: hooks
- **Archivos**: `hooks/run-hook.mjs`, `tests/hook-budget.test.mjs`, `tests/hook-runtime.test.mjs`, `tests/test_graphiti_security.py`, `interop/**` (regenerado: `hooks/` tocado)
- **Cubre (tests)**: E2E-19
- **Verificación**: `node --test tests/hook-budget.test.mjs tests/hook-runtime.test.mjs` → `pass` · `python3 -m pytest -q tests/test_graphiti_security.py` → `passed` (nuevo `_LAUNCHER_NODE_HASH`; solo `child_process`, `fs`, `path`, `url`)

**Criterios de aceptación**
- [ ] Con la captura desactivada, el hook no lanza ningún proceso Python (test que espía `spawn`).
- [ ] `dev.json` ausente, ilegible, > 64 KiB o con JSON inválido → sale con 0 sin Python.
- [ ] I-05: latencia síncrona añadida 0 ms en Claude y Codex (`async`), medida y anotada; excepción documentada: MCP en Codex.
- [ ] Exit 0 siempre (ADR-007); sin red.

**Subtareas**
- [ ] RED en `hook-budget.test.mjs`.
- [ ] Bloque aislado del atajo; huella revisada.

**Notas**: presupuesto por hook en `hooks/run-hook.mjs:24-31` (`childBudgetMs`); hooks conocidos en `:36-38`. Huella en `tests/test_graphiti_security.py:122` y módulos admitidos en `:787`. Lente C.

### T-47 — OpenCode: binding de actividad en `tool.execute.after` sin esperar al hijo

- **Descripción**: `hooks/opencode-plugin.js` registra el binding de actividad en `tool.execute.after` (herramienta, `status`, `agent`, args solo para el resumen) y lanza el hijo sin `await`, registrándolo en `children` para el cierre.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-44
- **Tipo**: hooks
- **Archivos**: `hooks/opencode-plugin.js`, `tests/opencode-plugin.test.mjs`, `interop/**` (regenerado: `hooks/` tocado)
- **Cubre (tests)**: E2E-09
- **Verificación**: `node --test tests/opencode-plugin.test.mjs` → `pass` (la promesa del evento resuelve antes de que termine el hijo; el hijo queda en `children`) · `python3 scripts/export-interop.py --check` → exit 0

**Criterios de aceptación**
- [ ] CA-42: OpenCode emite eventos de herramienta; si V2 no trae `sessionID`/`agent` en un runtime real, se declara en la página y en `docs/INTEROP.md`.
- [ ] Las vinculaciones de actividad e inicio/fin siguen separadas (GOT-022).

**Subtareas**
- [ ] RED en `opencode-plugin.test.mjs`.
- [ ] Binding sin `await`.

**Notas**: binding de actividad actual en `hooks/opencode-plugin.js:19` y despacho en `:263-270` (hoy con `await run(...)`); `agent` ya usado por la guardia (`design.md` §1, l. 163). Gotcha `custom-agents.GOT-022`. Lente C.

### T-48 — API `api/actividad-runs` y `api/actividad-run-<key16>`

- **Descripción**: Dos rutas nuevas: la lista de runs y la línea de tiempo de un run (≤ 150 últimos eventos, con `recortado`), ambas ≤ 64 KiB y redactadas. `api/activity` no cambia.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 229k in / 37k out tok · 3,50 €
- **Dependencias**: T-43
- **Tipo**: backend
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/panel_data.py`, `tests/test_panel_activity_server.py`
- **Cubre (tests)**: API-04, API-05
- **Verificación**: `python3 -m pytest -q tests/test_panel_activity_server.py` → `passed` (≤ 65.536 bytes con 500 eventos; `key16` inexistente → 404; sin token → 403)

**Criterios de aceptación**
- [ ] Tope de 64 KiB y 150 eventos por run con `recortado`.
- [ ] Sin `?` en la ruta; `key16` validado por regex exacta.
- [ ] Captura desactivada → respuesta con el estado y cómo activarla, no una lista vacía.

**Subtareas**
- [ ] RED; rutas.

**Notas**: snapshot de actividad actual en `skills/plugin-panel/scripts/serve_panel.py:206-226` (`_unavailable_activity`, `activity_snapshot`, 222 líneas: no ampliarla, crear función nueva). Lente C.

### T-49 — Página Agentes en vivo: runs, línea de tiempo y declaraciones por runtime

- **Descripción**: `agentes.html` muestra una fila por run (runtime, rol, inicio, duración, última herramienta) y, al abrirlo, su línea de tiempo. Estados «sin señal reciente», «tarea: sin atribuir», «historial recortado a los últimos N eventos», «captura informativa: puede tener huecos», «actividad desactivada» con cómo activarla, y por runtime «este runtime no emite eventos de herramienta» o «Codex no identifica el subagente: se agrupan por sesión».
- **Estado**: borrador
- **Tiempo humano**: est. 3,6h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real —
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 366k in / 60k out tok · 5,60 €
- **Dependencias**: T-48
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-agentes.js`, `skills/plugin-panel/assets/panel-activity.js`, `skills/plugin-panel/scripts/panel_pages.py`, `tests/test_panel_activity_ui.py`
- **Cubre (tests)**: E2E-17, E2E-18, E2E-19, E2E-09
- **Verificación**: `python3 -m pytest -q tests/test_panel_activity_ui.py` → `passed` (escenarios: run activo, run > 60 s, evento sin atribuir, historial recortado, captura desactivada, Codex por sesión)

**Criterios de aceptación**
- [ ] CA-15, CA-16, CA-18, CA-19, CA-20 y CA-21 visibles con sus textos.
- [ ] CA-42: cada runtime declara lo que no aporta; nada se omite en silencio.
- [ ] Refresco de 5 s como hoy; sin `innerHTML`.

**Subtareas**
- [ ] RED en el arnés.
- [ ] Página.

**Notas**: JS de actividad actual en `skills/plugin-panel/assets/panel-activity.js` (movido en T-12; refresco en su l. 67 original de `references/`). Lente C.

### T-50 — Inicio: actividad reciente

- **Descripción**: En servido, Inicio muestra los últimos eventos de actividad (agente, rol, herramienta, tarea si la hay, hace cuánto) con enlace a Agentes en vivo; con la captura desactivada, «actividad desactivada» y cómo activarla.
- **Estado**: borrador
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-49
- **Tipo**: frontend
- **Archivos**: `skills/plugin-panel/assets/page-inicio.js`, `tests/test_panel_inicio_ui.py`
- **Cubre (tests)**: E2E-19
- **Verificación**: `python3 -m pytest -q tests/test_panel_inicio_ui.py` → `passed`

**Criterios de aceptación**
- [ ] CA-04 en sus dos ramas (activa / desactivada).
- [ ] En modo exportado, la sección dice que la actividad solo existe en servido.

**Subtareas**
- [ ] RED; sección.

**Notas**: página de T-18; datos de `api/actividad-runs` (T-48).

### T-51 — Golden de `build_panel.py --json` actualizado solo con los hooks nuevos y grep de datos personales en eventos

- **Descripción**: El inventario de `--json` cambia porque hay hooks nuevos: el golden de T-01 se actualiza con un diff limitado a esos registros y revisado. Se añade el grep de CA-41 sobre `events.json` y sobre las respuestas de las API de actividad.
- **Estado**: borrador
- **Tiempo humano**: est. 1,2h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 91k in / 15k out tok · 1,40 €
- **Dependencias**: T-45, T-48
- **Tipo**: test
- **Archivos**: `tests/fixtures/panel-redesign/**`, `tests/test_panel_contract_golden.py`, `tests/test_panel_privacy.py`
- **Cubre (tests)**: E2E-08
- **Verificación**: `python3 -m pytest -q tests/test_panel_contract_golden.py tests/test_panel_privacy.py` → `passed` · lectura: el diff del golden solo añade los grupos de hook de actividad (pegado en `Notas`)

**Criterios de aceptación**
- [ ] CA-28: el único cambio del golden son los registros de hook nuevos; `dashboard.json` y `dashboard.md` intactos.
- [ ] CA-41: ningún HTML, JSON ni evento con la ruta del home, el usuario o correos, en servido y exportado.

**Subtareas**
- [ ] Regenerar el golden y revisar el diff.
- [ ] Test de privacidad sobre toda la salida.

**Notas**: riesgo «CA-28 choca con la fase 3» de `design.md` §6.

### T-52 — Documentación de F3: observabilidad, interop, flujos y contratos

- **Descripción**: `docs/observability.md` (+EN): captura de herramientas, opt-in, topes, borrado manual del directorio; `docs/INTEROP.md`: degradación por runtime con la cita de Codex; `docs/FLOWS.md` (+EN): flujo del hook asíncrono; `docs/PLUGIN-PANEL.md` (+EN): página Agentes; `docs/agents/CONTRACTS.md`: arista hook → `events.json` y panel → API de actividad.
- **Estado**: borrador
- **Tiempo humano**: est. 2,4h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 274k in / 45k out tok · 4,20 €
- **Dependencias**: T-41..T-51
- **Tipo**: docs
- **Archivos**: `docs/observability.md`, `docs/en/observability.md`, `docs/INTEROP.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 scripts/lint_plugin.py` → exit 0 (aristas nuevas con Puerta; sin citas rotas) · lectura: espejos EN y la cita de Codex con URL

**Criterios de aceptación**
- [ ] Cada runtime documenta lo que emite y lo que no.
- [ ] La guía dice cómo borrar el historial (el panel no borra).
- [ ] ES y EN en el mismo cambio.

**Subtareas**
- [ ] Redactar y espejar.

**Notas**: TDD n/a: prosa. No hay arista de actividad en CONTRACTS hoy: regla base de P3-bis (`docs/observability.md`, FLOWS).

### T-53 — Cierre transversal (C-05): multi-runtime, evals, interop, tamaño de skills y réplica Linux

- **Descripción**: Comprueba que las 7 páginas se generan desde Claude Code, Codex y OpenCode; que `SKILL.md` de `plugin-panel` y `roadmap-dashboard` caben en 200 líneas; que `evals/` casa con las `description` reales; que `interop/` está al día; y replica `ci.yml` en un contenedor Linux antes del push. Deja el campo `- **Changelog**:` en las tareas con cambio visible; los CHANGELOG los escribe `changelog-sync` en la Fase 6 de `/dev-cycle`.
- **Estado**: borrador
- **Tiempo humano**: est. 9,6h · real —
- **Tiempo IA (ejec.)**: est. 1,2h · real —
- **Supervisión**: est. 0,3h (≈25 % IA) · real —
- **Previsión IA**: 549k in / 89k out tok · 8,40 €
- **Dependencias**: T-52
- **Tipo**: devops
- **Archivos**: `skills/plugin-panel/SKILL.md`, `skills/roadmap-dashboard/SKILL.md`, `evals/cases/skill-plugin-panel.json`, `evals/cases/skill-roadmap-dashboard.json`, `evals/cases/command-plugin-catalog.json`, `evals/cases/command-roadmap-status.json`, `docs/README.md`, `interop/**` (regenerado), `docs/roadmap/2026-10-15-panel-redesign/tasks.md`
- **Cubre (tests)**: E2E-09
- **Verificación**:
  - `python3 scripts/export-interop.py --check` → exit 0 · `python3 evals/check.py` → exit 0 · `python3 -m pytest -q tests/test_skill_size.py tests/test_export_interop.py` → `passed`
  - réplica de `ci.yml` en `python:3.11-slim` con `git -c core.autocrlf=false archive` → mismos verdes que en Windows (salida pegada en `Notas`)
  - lectura: generación de las 7 páginas en los tres runtimes anotada con su runtime

**Criterios de aceptación**
- [ ] CA-42: las 7 páginas se generan en los tres runtimes; lo que falta se declara.
- [ ] Sin rojos que solo salgan en Linux (CRLF de `.sh`, rutas).
- [ ] Las tareas con cambio visible llevan `- **Changelog**:`.

**Subtareas**
- [ ] Generación por runtime.
- [ ] Réplica Linux.
- [ ] Campos `Changelog`.

**Notas**: TDD n/a: verificación y prosa. Nota de memoria «verificar en Linux antes de push» (normalizar CRLF de los `.sh`). Release fuera de este plan: `python3 scripts/release.py X.Y.Z` tras el PR.

### T-54 — Cierre de la Fase 3: revisión de dos lentes con Lente C obligatoria y revisión visual del usuario (M-04)

- **Descripción**: Puerta final: suites de CA-44, linter y evals; revisión adversarial de dos lentes **más la Lente C de seguridad obligatoria** sobre todo el diff de la fase (hooks, almacén, redactor, launcher, servidor); bucle acotado a 3 con Minor al backlog; el usuario revisa Agentes en vivo y el panel completo en el navegador (M-04).
- **Estado**: borrador
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
