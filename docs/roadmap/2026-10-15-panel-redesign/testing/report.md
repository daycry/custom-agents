# Informe de QA — Rediseño del panel (panel-redesign)

| | |
|---|---|
| **Fecha** | 2026-10-21 |
| **Estado global** | **VERDE** — lo decide `qa-gate.py` (exit 0) |
| **URL auditada** | `http://127.0.0.1:8771/<token>/` (servidor local con `--review-panel`); los E2E que levantan su propio servidor usan `127.0.0.1:8774-8780`. Guardrail: solo loopback y `file://`. |
| **Rama / HEAD** | `feat/panel-redesign` · `aff2c95` |
| **Plan** | [`../improvement-plan.md`](../improvement-plan.md) · [`../test-plan.md`](../test-plan.md) |

## Veredicto (qa-gate)

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 32,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Sin flaky: no hay `flaky-justify.json`. Los 32 bloques pasaron al primer intento (`QA_RETRIES=2` disponible y sin usar).

## Resumen

- **Automáticos:** 32/32 pasan: 24 E2E (E2E-09 en su parte verificable), 7 API y 1 A11Y.
- **Manuales:** M-01, M-02 y M-03 aprobados por el usuario en sus fases (T-16, T-29 y T-39 en `completado`). **M-04 pendiente** (T-54).
- **Pirámide de pruebas (informativo):** E2E 32/32 según `qa-gate.py`. La capa unitaria no se mide aquí: cada tarea de código pasó su gate de cobertura (`dev.json` `tests.coberturaMinima: 80`) y lo registra en su `Verificación ejecutada` del ledger.
- Veredicto: la suite automática da verde y la cobertura criterios ↔ tests está cerrada. El cierre depende de M-04 y de lo no verificable de E2E-09.

## Cobertura (coverage-check, exit 0)

- **Referencias rotas:** 0.
- **Tareas sin cobertura declarada:** ninguna (`tasks_sin_cobertura: []`).
- **Tests sin referenciar desde ninguna tarea:** ninguno.
- **Criterios `[GWT]`:** 53 cubiertos (CA-01..CA-43 y CA-45..CA-54); `gwt_sin_cubrir: []`, `gwt_sin_id: 0`.
- `ledger-lint` sobre `tasks.md`: 0 incoherencias y 5 avisos (ledger a 254 KB del tope de 256 KiB; T-16, T-29, T-39 y T-54 sin campo **Changelog**).
- Salida completa en `raw/coverage-check.out`.

## API y accesibilidad

| Bloque | Resultado | Detalle |
|---|---|---|
| API-01 `GET api/cartera` | pasa | 200, ≤ 64 KiB, `procedencia` en cada iniciativa; beta con `horas.real`, `coste.est_eur` y `tareas` a `null` |
| API-02 `GET api/plan-<id16>` | pasa | 200, kappa con 4 tareas y claves `id, titulo, fase_nombre, estado_tarea, horas, gaps`; id16 desconocido → 404 |
| API-03 `GET api/plan-<id16>-<T-XX>` | pasa | 200, `verificacion` ≤ 2000, `revision.abiertos` = 2, 2 gaps (alfa T-02) |
| API-04 `GET api/actividad-runs` | pasa | 200, `status: ok`, ≥ 1 run |
| API-05 `GET api/actividad-run-<key16>` | pasa | 200, ≤ 150 eventos, campo `recortado`; clave desconocida → 404 |
| API-06 `GET api/memoria` | pasa | 200, `bandeja` y `backends` presentes, ADR en el resumen |
| API-07 `GET api/review-summary` / `review-current` | pasa | `approval_granted: false`, ≥ 3 iniciativas, vocabulario cerrado, sin `review_id`; alfa «pendiente» tras abrirla; id16 desconocido → 404 |
| A11Y-01 (axe, WCAG 2.2 AA) | pasa | 0 violaciones serious/critical en las 7 páginas; `raw/axe-A11Y-01.json` no lista ninguna violación de ningún impacto |

## Resultados automáticos (E2E)

Todas las capturas están en `screenshots/`. Cada bloque pasó al primer intento.

### E2E-01 — Menú común en las siete páginas — PASA
- **Cubre tareas**: T-05, T-09, T-10, T-11, T-12
- **Aserciones**: orden del menú, un único `aria-current="page"` y primer foco en «Saltar al contenido», en las 7 páginas, servido y exportado.
- **Capturas**: ![inicio servido](screenshots/E2E-01-menu-inicio-servido.png) ![memoria servido](screenshots/E2E-01-menu-memoria-servido.png) ![memoria exportado](screenshots/E2E-01-menu-memoria-exportado.png)

### E2E-02 — Exportado abierto con `file://` y sin red — PASA
- **Cubre tareas**: T-02, T-03, T-08
- **Aserciones**: carpeta completa (7 páginas, `plan.html`, `vendor/chart.js/*`, `export-manifest.json`), una sola copia de Chart.js, datos incrustados, cabecera «Copia estática del …», 0 peticiones a otros orígenes, 0 violaciones CSP, 0 errores de página, ≥ 3 páginas con gráfico dibujado. En **Chromium y Firefox**.
- **Capturas**: ![chromium](screenshots/E2E-02-inicio-exportado-chromium.png) ![firefox](screenshots/E2E-02-inicio-exportado-firefox.png)

### E2E-03 — Servido: solo loopback con token — PASA
- **Cubre tareas**: T-11
- **Aserciones**: 200 con token; 404 sin token o con otro token (cuerpo vacío o el literal constante `Panel request unavailable.`, sin contenido del panel); 403 con `Host` u `Origin` ajenos; el puerto escucha solo en `127.0.0.1`.
- **Capturas**: n/a (comprobación HTTP).

### E2E-04 — Servido: CSP y cero peticiones ajenas — PASA
- **Cubre tareas**: T-03, T-11
- **Aserciones**: `Content-Security-Policy` con `default-src 'none'` y `connect-src 'self'` en las 7 páginas; 0 violaciones; 0 peticiones abortadas o fallidas a otros orígenes.
- **Capturas**: ![última página](screenshots/E2E-04-ultima-pagina.png)

### E2E-05 — Navegación solo con teclado — PASA
- **Cubre tareas**: T-05, T-19, T-24, T-33, T-36
- **Aserciones**: en Iniciativas, Plan, Memoria y Catálogo todo interactivo visible se alcanza con Tab, con foco visible y no tapado; Enter abre el detalle de tarea, Escape lo cierra y el foco vuelve a su tarjeta; las relaciones de Memoria se abren con teclado.
- **Capturas**: ![foco tarjeta](screenshots/E2E-05-foco-tarjeta-plan.png) ![relaciones](screenshots/E2E-05-memoria-relaciones.png)

### E2E-06 — Gráficos accesibles y respaldo sin Chart.js — PASA
- **Cubre tareas**: T-07, T-09
- **Aserciones**: ≥ 5 figuras con nombre accesible, tabla equivalente y `tabindex=0`; sin `chart.umd.min.js` las 7 páginas se renderizan sin canvas ni errores, con aviso y tablas.
- **Capturas**: ![catálogo sin Chart.js](screenshots/E2E-06-catalogo-sin-chartjs.png)

### E2E-07 — Datos ausentes y parciales — PASA
- **Cubre tareas**: T-07, T-18, T-20, T-25, T-26
- **Aserciones**: «dato en N de M iniciativas», «una iniciativa sin estimación no suma 0», procedencia medidos/estimados/desconocidos; beta con «sin datos (sin ledger)» y nunca 0; alfa con «real sin datos»; mensaje «burndown no disponible…» y sin gráfico.
- **Capturas**: ![tarjeta sin datos](screenshots/E2E-07-tarjeta-sin-datos.png) ![plan sin burndown](screenshots/E2E-07-plan-sin-burndown.png)

### E2E-08 — Sin datos personales en ningún modo — PASA
- **Cubre tareas**: T-04, T-08, T-51
- **Aserciones**: 47 respuestas y ficheros revisados (páginas servidas, API, líneas de tiempo de cada run, `events.json` y exportado completo) sin usuario, correo, nombre de autor git ni rutas de la máquina. Precondición: el último commit del proyecto de prueba lleva `qa.persona@example.com`.
- **Capturas**: n/a.

### E2E-09 — Tres runtimes (parte verificable) — PASA
- **Cubre tareas**: T-14, T-45, T-47, T-49, T-53
- **Aserciones verificadas**: `export-interop.py --check` «al día»; panel generado con `--runtime claude-code|codex|opencode`, con las 7 páginas, texto en `main` y 0 errores; Agentes en vivo con filas de Claude Code, Codex y OpenCode y las tres declaraciones («Claude Code:», Codex «se agrupan por sesión», OpenCode «sin duración / no emite eventos de herramienta»).
- **No verificable aquí**: ver «E2E-09: verificable frente a no verificable».
- **Capturas**: ![agentes](screenshots/E2E-09-agentes-declaraciones.png)

### E2E-10 — Revisión visual del plan (`--review-initiative`) — PASA
- **Cubre tareas**: T-12 (y T-58)
- **Aserciones**: comentar y «Pedir cambios» deja un único `r-<sha>.json`; `plan-review.py receive` devuelve `request_changes` con el texto del comentario; el navegador solo escribe en rutas de revisión; `git status -- docs` limpio.
- **Capturas**: ![comentario enviado](screenshots/E2E-10-comentario-enviado.png)

### E2E-11 — Inicio: cifras de cartera — PASA
- **Cubre tareas**: T-17, T-18
- **Aserciones**: estados de la cartera, avance global (`n de m tareas completadas`), iniciativas fuera de tope y procedencia iguales a `build_dashboard.py --json` y `progress-report.py`; la ilegible aparte.
- **Capturas**: ![inicio](screenshots/E2E-11-inicio.png)

### E2E-12 — Iniciativas: kanban solo lectura — PASA
- **Cubre tareas**: T-19
- **Aserciones**: columnas «Borrador (1)», «Aprobada (2)», «Implementada (1)»; arrastrar no mueve nada ni cambia `docs/`; alertas «2 gaps de revisión abiertos» y «Sin estimación…»; Enter sobre la tarjeta navega al Plan.
- **Capturas**: ![kanban](screenshots/E2E-12-kanban-iniciativas.png)

### E2E-13 — Iniciativas: gráficos de horas y coste — PASA
- **Cubre tareas**: T-20
- **Aserciones**: un canvas por gráfico; beta «sin datos» en la tabla y fuera de las barras; alfa dibujada.
- **Capturas**: ![gráfico horas](screenshots/E2E-13-grafico-horas.png)

### E2E-14 — Plan: kanban y detalle de tarea — PASA
- **Cubre tareas**: T-23, T-24
- **Aserciones**: 5 columnas y el estado no reconocido «bloqueada»; detalle de kappa T-03 con descripción, criterio pendiente, verificación, dependencias, archivado y referencia a `execution-history.md`; detalle de alfa T-02 con intento 1 y sus dos gaps (Important y Minor).
- **Capturas**: ![kappa T-03](screenshots/E2E-14-detalle-kappa-T03.png) ![alfa T-02](screenshots/E2E-14-detalle-alfa-T02-gaps.png)

### E2E-15 — Plan: avance, burndown y real vs estimado — PASA
- **Cubre tareas**: T-25, T-26
- **Aserciones**: kappa con avance «Fase 1 2 de 4», burndown con solo fechas reales (2026-01-21 y 2026-01-23, valores 3 y 2); T-01 medido, T-02 estimado, T-03 «sin datos» y no 0; alfa sin burndown (mensaje exacto) y avance 1/2.
- **Capturas**: ![burndown](screenshots/E2E-15-burndown.png)

### E2E-16 — Plan: refresco vivo del kanban — PASA
- **Cubre tareas**: T-27
- **Aserciones**: al pasar T-02 a `en-revision`, el kanban lo refleja en menos de 15 s sin recargar y el detalle sigue abierto. El ledger se restaura al terminar.
- **Capturas**: ![antes](screenshots/E2E-16-antes.png) ![después](screenshots/E2E-16-despues.png)

### E2E-17 — Agentes en vivo: filas, línea de tiempo y run viejo — PASA
- **Cubre tareas**: T-41, T-44, T-48, T-49
- **Aserciones**: encabezados de la tabla; run reciente «en curso» con Bash; run viejo «sin señal reciente» con duración congelada tras 6 s; línea de tiempo con hora, herramienta, resumen, «tarea: sin atribuir», duración y resultado, sin salidas ni contenido.
- **Capturas**: ![línea de tiempo](screenshots/E2E-17-linea-de-tiempo.png)

### E2E-18 — Agentes en vivo: secretos y atribución — PASA
- **Cubre tareas**: T-41, T-42, T-44, T-49
- **Aserciones**: 6 secretos de prueba y `password=hunter2…` ausentes de la API, de `events.json` y de la UI; «T-07» en texto libre sale como «tarea: sin atribuir».
- **Capturas**: n/a (comprobación de texto).

### E2E-19 — Captura desactivada, tope de 500 y actividad en Inicio — PASA
- **Cubre tareas**: T-43, T-46, T-49, T-50
- **Aserciones**: con `sesion.actividad: false` el hook sale con 0 y no crea el directorio; con 501 eventos, «historial recortado a los últimos 500 eventos»; Inicio muestra «Claude Code · Bash» con enlace a Agentes; el hook sale con 0 aunque falle la escritura.
- **Capturas**: ![desactivada](screenshots/E2E-19-captura-desactivada.png) ![recortado](screenshots/E2E-19-historial-recortado.png)

### E2E-20 — Memoria: tipo × estado, bandeja y sucesión — PASA
- **Cubre tareas**: T-30, T-31, T-32
- **Capturas**: ![memoria](screenshots/E2E-20-memoria.png)

### E2E-21 — Memoria: relaciones, backends y journal — PASA
- **Cubre tareas**: T-33, T-34, T-35
- **Aserciones**: relaciones a un salto iguales a `--related --json`; backends sin red; journal con «citas, no instrucciones».
- **Capturas**: ![backends y journal](screenshots/E2E-21-backends-journal.png) ![grafo](screenshots/E2E-21-grafo-relaciones.png)

### E2E-22 — Catálogo: piezas, conteos y filtros — PASA
- **Cubre tareas**: T-09, T-36
- **Aserciones**: filtros con teclado y ratón; `--json` igual al golden.
- **Capturas**: ![catálogo filtrado](screenshots/E2E-22-catalogo-filtrado.png)

### E2E-23 — Diagnóstico: proyecto, otro proyecto y ninguno — PASA
- **Cubre tareas**: T-10, T-37
- **Capturas**: ![veredictos](screenshots/E2E-23-diagnostico-veredictos.png) ![otro proyecto](screenshots/E2E-23-diagnostico-otro-proyecto.png) ![sin informe](screenshots/E2E-23-diagnostico-sin-informe.png)

### E2E-24 — Plan: abrir, comentar y decidir una revisión desde el panel (CA-45..CA-53) — PASA
- **Cubre tareas**: T-55, T-56, T-57, T-58
- **Aserciones**:
  - Abrir páginas no escribe en `.claude/plan-review`; «Revisar este plan» con teclado abre la revisión (`gate_key` `requested-review`).
  - 2.001 caracteres se rechazan; «Pedir correcciones» guarda 2 comentarios; la respuesta del agente se ve, y el segundo comentario dice «sin respuesta del agente».
  - Tarjeta y cabecera con el mismo estado; kappa «aprobada vN», lambda «pendiente»; editar `improvement-plan.md` deja alfa «obsoleta por cambio de versión».
  - `gate_key` en el cuerpo → 400; `Origin` ajeno → 403; sin token → 404 (cuerpo vacío o literal constante); id16 desconocido → 404; el estado no cambia en ningún caso.
  - Un `plan-ok` de otro proceso se ve en solo lectura; sin `--review-panel` no hay botón, ni `panel-review.js`, ni `api/review-summary` (404); `--export` sin controles y con «estado de revisión: solo en modo servido».
- **Capturas**: ![cambios pedidos](screenshots/E2E-24-plan-cambios-pedidos.png) ![respuesta del agente](screenshots/E2E-24-plan-respuesta-del-agente.png) ![tarjeta](screenshots/E2E-24-tarjeta-con-estado.png) ![obsoleta](screenshots/E2E-24-obsoleta.png) ![sin review-panel](screenshots/E2E-24-sin-review-panel.png)

## E2E-09: verificable frente a no verificable

| Aspecto | Estado |
|---|---|
| `export-interop.py --check` (interop al día) | Verificado, pasa |
| Panel generado con `--runtime claude-code`, `codex` y `opencode`: 7 páginas, sin errores de página | Verificado, pasa |
| Agentes en vivo con eventos de los tres runtimes y sus declaraciones | Verificado con **eventos sintéticos** de cada runtime escritos en el almacén real |
| El plugin instalado en Codex y OpenCode reales, con su hook capturando eventos de verdad | **No verificable**: ninguno de los dos está instalado en esta máquina. Lo cubren la traducción de `interop/` (comprobada con `--check`) y los eventos sintéticos |
| Claude Code real con un `/dev-cycle` en curso | **No automatizable**: queda en M-04 |

## Checklist manual (para una persona)

> No se automatizan por diseño (juicio visual y sesión real de agentes).

- [x] **M-01 — Revisión visual de la Fase 1**: menú, estilo, paleta y gráfico de Catálogo, servido y exportado · *(T-16, aprobado)*
- [x] **M-02 — Revisión visual de la Fase 2**: Inicio, Iniciativas y Plan; abrir, comentar y decidir una revisión desde el Plan · *(T-29, aprobado)*
- [x] **M-03 — Revisión visual de la Fase 4**: Memoria «sencilla y que se entienda», Catálogo y Diagnóstico · *(T-39, aprobado)*
- [ ] **M-04 — Revisión visual de la Fase 3 y del panel completo**: Agentes en vivo durante un `/dev-cycle` real y las 7 páginas juntas · *(T-54, pendiente)*

## Trazabilidad (tarea → resultado)

| Tarea | Escenarios | Resultado |
|---|---|---|
| T-02 | E2E-02 | pasa |
| T-03 | E2E-02, E2E-04 | pasa |
| T-04 | E2E-08 | pasa |
| T-05 | E2E-01, E2E-05 | pasa |
| T-06 | A11Y-01 | pasa |
| T-07 | E2E-06, E2E-07, A11Y-01 | pasa |
| T-08 | E2E-02, E2E-08 | pasa |
| T-09 | E2E-06, E2E-22 | pasa |
| T-10 | E2E-23 | pasa |
| T-11 | E2E-03, E2E-04 | pasa |
| T-12 | E2E-10 | pasa |
| T-14 | E2E-09 | pasa (parte verificable) |
| T-16 | M-01 | aprobado |
| T-17 | API-01, E2E-11 | pasa |
| T-18 | E2E-07, E2E-11 | pasa |
| T-19 | E2E-05, E2E-12 | pasa |
| T-20 | E2E-07, E2E-13 | pasa |
| T-23 | API-02, E2E-14 | pasa |
| T-24 | API-03, E2E-05, E2E-14 | pasa |
| T-25, T-26 | E2E-07, E2E-15 | pasa |
| T-27 | E2E-16 | pasa |
| T-29 | M-02 | aprobado |
| T-30 | API-06, E2E-20, A11Y-01 | pasa |
| T-31, T-32 | E2E-20 | pasa |
| T-33 | E2E-05, E2E-21 | pasa |
| T-34, T-35 | E2E-21 | pasa |
| T-36 | E2E-05, E2E-22 | pasa |
| T-37 | E2E-23 | pasa |
| T-39 | M-03 | aprobado |
| T-41 | E2E-17, E2E-18 | pasa |
| T-42 | E2E-18 | pasa |
| T-43 | E2E-19 | pasa |
| T-44 | E2E-17, E2E-18 | pasa |
| T-45, T-47, T-53 | E2E-09 | pasa (parte verificable) |
| T-46, T-50 | E2E-19 | pasa |
| T-48 | API-04, API-05 | pasa |
| T-49 | E2E-09, E2E-17, E2E-18, E2E-19 | pasa (E2E-09 en su parte verificable) |
| T-51 | E2E-08 | pasa |
| T-54 | M-04 | manual pendiente |
| T-55, T-56 | API-07, E2E-24 | pasa |
| T-57 | E2E-24 | pasa |
| T-58 | E2E-05, E2E-10, E2E-24 | pasa |

## Ejecuciones

| # | Resultado | Causa y resolución |
|---|---|---|
| 1.ª | 28/32 | 4 rojos, resueltos. Tres eran el plan describiendo mal el código: el texto «Copia estática…» del exportado lo pidió el usuario tras M-01, y el servidor ya respondía 404 sin token antes de la iniciativa. Se enmendaron `test-plan.md`, `spec.md` (CA-34, CA-47) y el criterio de T-11 en `290fece`. El cuarto, A11Y-01, era un defecto real: los paneles de Memoria llevaban `aria-label` sin rol. Se corrigió con `role="region"` en `aff2c95`. |
| 2.ª | 27/5, sin veredicto | La sesión del agente se cayó por un error de API mientras reconstruía el montaje. |
| Ajuste de aserciones | n/a | Tres aserciones eran más estrictas que el plan enmendado. **E2E-02**: la fecha de la cabecera lleva hora (`Copia estática del 2026-10-21 13:00 UTC · …`). **E2E-03** y **E2E-24**: el 404 sin token devuelve el cuerpo genérico constante `Panel request unavailable.`, el mismo de antes de la iniciativa y sin contenido del panel; se acepta `''` o ese literal. |
| 3.ª | 18/13 | Fallo del **montaje**, no del código. La reconstrucción con solo `stage.py` + `prep.sh` no incluía el repo git con autor, la iniciativa kappa, los eventos de Codex y OpenCode, el servidor con `--review-panel` ni el run viejo. |
| **4.ª** | **32/32, VERDE** | Montaje completo y reproducible (`stage-full.sh` + `stage-kappa.py`, fuera del repo), ejecutado desde cero; `raw/` y `screenshots/` vaciados antes. 0 fallos, 0 flaky, sin reintentos. |

Defectos reales de código abiertos tras esta ejecución: ninguno.

## Evidencias

- Este informe y `report.pdf` van en git. `screenshots/` (38 PNG) y `raw/` (`results.json`, `qa-gate.json`, `coverage-check.out`, `axe-A11Y-01.json`, `artifacts/` con trazas) son locales, como en las demás iniciativas.
- Guardrail: todas las URLs auditadas son `127.0.0.1` o `file://`; nada contra terceros.
