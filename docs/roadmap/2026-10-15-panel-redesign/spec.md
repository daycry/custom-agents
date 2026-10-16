---
spec: panel-redesign
descripcion: Panel local multi-página (Inicio, Iniciativas, Plan, Agentes en vivo, Memoria, Catálogo, Diagnóstico) con menú común, kanban y gráficos Chart.js incluidos en el plugin, sin red, accesible y con datos ausentes declarados como tales.
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-10-15
actualizado: 2026-10-16   # enmienda 2026-10-15: revisión del plan desde el panel (CA-45 a CA-54) · enmienda 2026-10-16: CA-10 «archivado» como texto
evaluacion: evaluation.md
design: design.md         # aprobado: D-A1 = O1, D-A2 = O5 (revisable por el usuario)
plan: improvement-plan.md
generacion:               # usage-meter.py close (el marcador se abrió tras las primeras lecturas: cubre casi toda la redacción)
  inicio: 2026-10-15T08:58:50Z
  fin: 2026-10-15T09:04:29Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-53cbc47c4fe2469ca0373fa6637c3589
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 18, salida: 30575, cache_creacion: 45902, cache_lectura: 724937 }
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  eur: 1.30
  horas_ia: 0.14
  duracion: 8m
  ratio_usado: 531798.5     # CALIBRATION.md (mediana de 6)
  avisos: ["CALIBRATION: 7 filas marcadas (estimado) fuera de la mediana", "tarifa verificada el 2026-08-18"]
---

# Rediseño del panel local: multi-página, kanban y gráficos

> **Evaluación:** [`evaluation.md`](evaluation.md) — go condicionado (F1, F2, F4 tras D-A1; F3 tras D-A2 + I-03, I-05, I-08)
> **Diseño:** [`design.md`](design.md) — aprobado: D-A1 = O1 (`plugin-panel` dueño de la presentación), D-A2 = O5 (captura asíncrona post-herramienta)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) · ledger [`tasks.md`](tasks.md) · pruebas [`test-plan.md`](test-plan.md)

> **Terminología:**
> - **Panel**: el conjunto de páginas HTML locales de esta iniciativa. Sustituye a la vista de una sola página de `plugin-panel` y al `dashboard.html` de `roadmap-dashboard` en lo que a presentación se refiere (cuál absorbe a cuál: D-A1).
> - **Modo servido**: el panel abierto por `serve_panel.py` en `127.0.0.1` con URL de token y datos que se refrescan.
> - **Modo exportado**: el mismo panel escrito a una carpeta estática, sin servidor, con los datos congelados en el momento de generarlo.
> - **Run de agente**: el intervalo entre el inicio y el fin de un subagente observado por los hooks de actividad.
> - **Evento de herramienta**: una observación de que un agente usó una herramienta (nombre, resumen redactado del argumento, tarea atribuida si la hay, duración, resultado). No contiene el contenido de la herramienta.
> - **Dato ausente / parcial**: un valor que la fuente no trae o trae incompleto. Se muestra con su etiqueta («sin datos», «parcial: N de M»), nunca como 0 ni como un valor calculado a ojo.

## Contexto y objetivo

**Problema (citas del usuario, conversación del 2026-10-15):**

1. «necesito que el dashboard sea más profesional, moderno, no todo en el mismo html, a poder ser con gráficos, kanban de los planes, con información detallada».
2. «al entrar en un plan, los kanban de las tareas con más información detallada, gráficos y cosas más visuales».
3. «creo que cada apartado podría ser un html independiente dentro del menú».
4. «la parte de la memoria más visual, porque ahora está todo que no se entiende bien».
5. Agentes: «sobretodo los runs de los agentes, con lo que hacen en todo momento».

**Evidencia del problema (comportamiento actual, hechos del repo):**

- Hay **dos** generadores HTML que se solapan en presentación: `skills/plugin-panel/scripts/build_panel.py` (814 líneas; un único HTML desde `skills/plugin-panel/references/panel.html` más cuatro JS: `panel-live.js`, `panel-memory.js`, `panel-activity.js`, `panel-review.js`) y `skills/roadmap-dashboard/scripts/build_dashboard.py` (1.181 líneas; HTML/MD/JSON de la cartera). El panel de hoy es una sola página con anclas (`panel.html:26`: navegación `#catalog`, `#extensions`, `#diagnostics`, `#workflow`, `#source-notes`).
- La actividad de agentes solo registra inicio y fin de subagente (`agent-kits/shared/agent-activity-store.py:160`: `SubagentStart → response_started`, `SubagentStop → response_finished`) y caduca a los 60 s (`agent-kits/shared/agent-activity.py:9`). No hay herramienta, tarea ni duración.
- Ningún gráfico: el panel no incluye librería de gráficos y su CSP lo impide desde red (`serve_panel.py:492`, `panel.html:2`).

**Objetivo:** un panel local de varias páginas con menú común, que muestre cartera, planes, actividad de agentes y memoria con kanban y gráficos, sin red, accesible, y que diga con claridad cuándo un dato falta.

**Usuarios / actores:**

| Actor | Qué hace con el panel |
|---|---|
| Desarrollador del proyecto consumidor (hoy el usuario del repo) | Sigue el avance de un plan, ve qué hace cada agente durante `/dev-cycle`, revisa la memoria. |
| PM sin git | Recibe el modo exportado (carpeta estática) o sigue leyendo `dashboard.md` en Confluence (contrato existente, no cambia). |
| Agentes y comandos del plugin | No usan el panel; siguen consumiendo los JSON/MD existentes (`build_dashboard.py --json`, `doctor --panel-json`, `knowledge-find --json`). |
| Runtimes Claude Code, Codex y OpenCode | Generan los eventos de actividad; el panel no sabe de runtimes salvo para mostrar de cuál viene cada evento. |

## Decisiones de diseño

Tomadas por el usuario en la conversación del 2026-10-15. **No se reabren**.

| Decisión | Elección | Motivo |
|---|---|---|
| Estructura | **Varias páginas HTML con menú común**: Inicio · Iniciativas · Plan · Agentes en vivo · Memoria · Catálogo · Diagnóstico | Cita 3; propuesta aceptada con «me parece bien». |
| Librería de gráficos | **Chart.js incluido en el plugin, versión fija y su licencia** (no CDN) | «mejor con chat.js». El panel muestra ledgers, memoria y planes: nada sale a la red, funciona sin conexión, CSP estricta, sin cadena de suministro externa en tiempo de ejecución. |
| Modos de entrega | **Servido en 127.0.0.1 y exportable a carpeta estática** | Estructura acordada. |
| Memoria | **Vista sencilla**: estado por tipo y área, bandeja del curador, línea de tiempo con sucesores, relaciones de UNA entrada, sincronización con backends opcionales, journal reciente | «la parte memoria me parece bien tu propuesta, algo sencillo». No duplica Kwipu, Graphiti ni Graphify. |
| Actividad de agentes | **Ampliar el registro opt-in** con un evento por herramienta (nombre + resumen corto REDACTADO del argumento, nunca contenido), tarea `T-XX` cuando se pueda atribuir, duración y resultado; local y acotado | Cita 5; acordado en la conversación. |
| Forma de trabajo | **Iniciativa propia, `/dev-cycle` flujo completo, 4 fases**, cada una con tests y revisión | Acordado en la conversación (ver «Fases propuestas»). |

## Configuración / parámetros

Valores que ya existen en el repo y que el panel debe respetar. Ninguna cifra nueva se inventa aquí: lo que falta va a «Incógnitas».

| Parámetro | Clave / mecanismo | Valor actual | Valor objetivo |
|---|---|---|---|
| Captura de actividad | `.claude/dev.json` `sesion.actividad` | desactivada (`agent-activity-store.py:100` exige `true`) | **sin cambio: opt-in, desactivada por defecto** (cubre también los eventos de herramienta) |
| Frescura de la actividad | `FRESH_SECONDS` (`agent-activity.py:9`) | 60 s | **60 s** para el estado «ahora» |
| Observaciones por snapshot | `MAX_OBSERVATIONS` (`agent-activity.py:10`) | 64 | 64 para el snapshot de estado; tope del historial de eventos → Incógnita I-03 |
| Tamaño de snapshot de actividad | `MAX_BYTES` (`agent-activity-store.py:20`) | 64 KiB | sin cambio para el snapshot; tope del historial → I-03 |
| Lectura por fichero del ledger | `MAX_FILE_BYTES` (`serve_panel.py:15`) | 256 KiB | **256 KiB** |
| Lectura total por petición | `MAX_READ_BYTES` (`serve_panel.py:16`) | 1 MiB | sin cambio |
| Iniciativas por respuesta | `MAX_INITIATIVES` (`serve_panel.py:17`) | 64 | sin cambio |
| Respuesta de API | `MAX_RESPONSE_BYTES` (`serve_panel.py:18`) | 64 KiB | sin cambio salvo que el diseño lo justifique (I-04) |
| Lectura de catálogo | `MAX_BYTES` / `MAX_FILES` (`build_panel.py:20-21`) | 512 KiB / 1.000 ficheros | sin cambio |
| Refresco en modo servido | `setTimeout(refresh,5000)` (`panel-live.js:63`, `panel-activity.js:67`) | 5 s | sin cambio salvo decisión de architect |
| Presupuesto del hook de actividad | `childBudgetMs` (`hooks/run-hook.mjs:26`) | 2.000 ms | sin cambio; coste por evento de herramienta → I-05 |
| Versión de Chart.js | fichero incluido + `LICENSE` | no existe | **versión fija** declarada en un fichero de procedencia (cuál: I-01) |

## Arquitectura y componentes

| Pieza | Hoy | En esta iniciativa |
|---|---|---|
| `skills/plugin-panel/` (`build_panel.py`, `serve_panel.py`, `references/*.html|js`) | Panel de una página + servidor local | Se **reutiliza** el servidor (token, CSP con nonce, `127.0.0.1`, topes) y los lectores; la presentación pasa a varias páginas. Dueño final de la presentación: D-A1. |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` | HTML/MD/JSON de cartera; `--json` con `procedencia` (`build_dashboard.py:1170`) | Su **cálculo de datos** (progreso, real vs estimado, procedencia) se reutiliza. Su HTML se absorbe o absorbe al otro: D-A1. `dashboard.md` y `--json` **no cambian de contrato**. |
| `agent-kits/shared/agent-activity-store.py` + `agent-activity.py` + hooks `agent-activity` (`hooks/hooks.json:34-50`) | Solo inicio/fin de subagente | Se **amplía** con eventos de herramienta (modelo de captura: D-A2). |
| `agent-kits/shared/knowledge-find.py` (`--related`, `--show`), `knowledge-curation.py`, `journal.py`, `skills/knowledge-services` | CLI y vistas de búsqueda en el panel | Se **reutilizan** como fuentes de datos de la página Memoria; no se reimplementan. |
| `agent-kits/shared/doctor.py --panel-json` | Proyección portable del diagnóstico | Fuente única de la página Diagnóstico (sin cambio de contrato). |
| `agent-kits/shared/redact.py` | Redactor único (constitución §4) | Lo atraviesa todo texto del panel, también el resumen de argumentos de herramienta. |
| Chart.js | No existe | **Nuevo**: fichero minificado local + `LICENSE` + procedencia (versión y hash). |

## Flujo (paso a paso)

1. El usuario lanza el panel en modo servido (`/plugin-catalog --serve` o el comando que fije D-A1) o pide el modo exportado a una carpeta.
2. El generador lee las fuentes locales con los topes de la tabla anterior: `docs/roadmap/`, ledgers `tasks.md`, `docs/knowledge/`, journal, `doctor --panel-json`, snapshot de actividad.
3. Cada página recibe solo sus datos; los que faltan llegan marcados como ausentes o parciales.
4. En modo servido, las páginas con datos vivos (Inicio, Plan, Agentes en vivo) refrescan por la API local; en modo exportado muestran la fecha de generación y que no se actualizan.
5. Los gráficos se dibujan con el Chart.js incluido; cada uno lleva su alternativa textual (tabla de datos).

## Alcance

- **Dentro (esta iteración):**
  - Base común: plantilla multi-página, menú común, estilos, Chart.js local con versión fija y licencia, CSP sin red, modo exportado y modo servido.
  - Páginas Inicio, Iniciativas (kanban de planes + gráficos de cartera) y Plan (kanban de tareas con detalle + gráficos de fase, burndown y real vs estimado).
  - Página Agentes en vivo y la ampliación del registro de actividad con eventos de herramienta (opt-in, local, acotado, redactado).
  - Páginas Memoria (vista sencilla acordada), Catálogo (lo de hoy, mejor presentado) y Diagnóstico (proyección de `/doctor`).
  - **(Enmienda 2026-10-15)** Revisión del plan desde el panel: en modo servido, desde la página Plan de CUALQUIER iniciativa, abrir su revisión (aprobar / pedir correcciones con comentarios anclados por sección) sin lanzar el panel con `--review-initiative`; estado de revisión de cada iniciativa («sin revisión · pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión») visible en la tarjeta del kanban de Iniciativas y en la cabecera del Plan; respuestas del agente a cada comentario visibles en el Plan. El comando que lanza la UI de revisión de un plan se conserva (`--review-initiative`, y `/dev-cycle` en `plan-ok`). La persistencia y la lógica siguen siendo las de `agent-kits/shared/plan-review.py`.
  - Decidir y aplicar qué pieza es dueña de la presentación (D-A1), sin dejar dos dashboards HTML con el mismo rol.
  - Tests de cada fase, documentación de la pieza dueña, `FLOWS.md`/`observability.md` y sus espejos EN si cambia un flujo, y regeneración de `interop/`.
- **Fuera (siguientes specs o nunca):**
  - Explorador de grafos completo (navegar todo el grafo de memoria o de código).
  - Búsqueda semántica (embeddings, ranking por similitud). La búsqueda léxica existente del panel no se amplía.
  - Réplica de Kwipu, Graphiti o Graphify: el panel enlaza a su interfaz y muestra qué se publicó; no reproduce su vista.
  - Control de agentes desde el panel: lanzar, parar, reintentar o reasignar agentes o tareas.
  - Cualquier petición de red o CDN, en tiempo de ejecución o de generación.
  - Escribir tareas desde el panel: crear, mover entre columnas, editar o cerrar `T-XX`. El kanban es de solo lectura; el ledger `tasks.md` sigue siendo la única fuente (constitución §2). **(Enmienda 2026-10-15)** La única excepción es la revisión del plan (aprobar / pedir correcciones), que no toca tareas ni markdown.
  - **(Enmienda 2026-10-15)** Editar markdown desde el navegador (spec, plan, tasks). Aclaración del usuario: «me refería a aprobar o solicitar correcciones, no editar manualmente los markdown».
  - **(Enmienda 2026-10-15)** Que el navegador aplique las correcciones pedidas: las aplica el agente al retomar, con `plan-review.py` (`consume`/`result`).
  - **(Enmienda 2026-10-15)** Que una revisión abierta desde el panel autorice la puerta `plan-ok` de `/dev-cycle`: el navegador solo abre `requested-review`; `plan-ok` solo lo abre el orquestador.
  - **(Enmienda 2026-10-15)** Ampliar la revisión desde el panel a la spec o al go/no-go de `/pm-cycle`. Posible futuro, no se hace aquí.
  - Arrastrar y soltar tarjetas.
  - Cambiar los contratos de `dashboard.md`, `build_dashboard.py --json` o `doctor --panel-json`.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Un `tasks.md` supera 256 KiB | La tarjeta del plan muestra «ledger fuera del tope de lectura (256 KiB)» y sin cifras; no lee el fichero truncado como si fuera completo. |
| Un ledger o spec ilegible o con frontmatter roto | La iniciativa aparece con estado «ilegible» y el motivo; el resto de iniciativas se muestran. |
| Falta un bloque `generacion:` o el ledger no trae `real`/`est` | Celda «sin datos» y la procedencia «desconocida» (`build_dashboard.py:1169`: ausente = null, nunca 0). |
| El ledger no registra fechas de cierre por tarea | El burndown se sustituye por «burndown no disponible: el ledger no registra fechas de cierre» (I-02). |
| `sesion.actividad` desactivado | Agentes en vivo explica cómo activarlo y no muestra eventos vacíos como «sin actividad». |
| Runtime que no emite eventos de herramienta | Se muestran los runs (inicio/fin) y la línea «este runtime no emite eventos de herramienta» para ese runtime. |
| Señal de actividad con más de 60 s | Estado «sin señal reciente», no «terminado» ni «muerto» (`agent-activity.py:75`: `live_process_proven=False`). |
| Falta `redact.py` | No se emiten metadatos de texto libre; aviso visible; el resto de la página funciona (comportamiento actual, `SKILL.md` de `plugin-panel`). |
| Falta el fichero de Chart.js o su hash no coincide | Los gráficos se sustituyen por sus tablas de datos y un aviso; ninguna página falla entera. |
| Backend de memoria no configurado | «Kwipu: no configurado» / «Graphiti: no configurado», sin enlace. |
| Modo exportado abierto días después | Cabecera con la fecha de generación y «instantánea: no se actualiza». |

## Criterios de aceptación

Variante `[GWT]` para lo que un test puede reproducir. Cada página tiene su bloque; los transversales aplican a todas.

### Inicio (4)

- [ ] [GWT] CA-01 — Dado un `docs/roadmap/` con iniciativas en varios estados, Cuando abro Inicio, Entonces veo el número de iniciativas por estado de spec (`borrador · aprobada · implementada · obsoleta`) en un gráfico y en una tabla con las mismas cifras que `build_dashboard.py --json`. No debe contar una iniciativa ilegible dentro de ningún estado: aparece como «ilegible».
- [ ] [GWT] CA-02 — Dado un conjunto de ledgers, Cuando abro Inicio, Entonces veo el avance global como «N de M tareas completadas (P %)», con N y M iguales a la suma de lo que reporta `progress-report.py` por ledger. No debe incluir en M ni en N los ledgers que superan el tope de lectura; se listan aparte.
- [ ] [GWT] CA-03 — Dado iniciativas con y sin estimación, Cuando abro Inicio, Entonces veo el coste real frente al estimado de la cartera y la línea «procedencia: X medidos · Y estimados · Z desconocidos». No debe sumar como 0 una iniciativa sin estimación.
- [ ] [GWT] CA-04 — Dado `sesion.actividad: true` y eventos recientes, Cuando abro Inicio en modo servido, Entonces veo los últimos eventos de actividad (agente, rol, herramienta, tarea si la hay, hace cuánto) con enlace a Agentes en vivo; con la captura desactivada veo «actividad desactivada» y cómo activarla.

### Iniciativas (4)

- [ ] [GWT] CA-05 — Dado `docs/roadmap/`, Cuando abro Iniciativas, Entonces veo un kanban de solo lectura con una columna por estado y una tarjeta por iniciativa; cada tarjeta muestra slug, fecha, «N/M tareas (P %)», horas real/estimado, coste real/estimado y alertas. No debe permitir mover tarjetas ni escribir en ningún fichero.
- [ ] [GWT] CA-06 — Dada una iniciativa con alertas (ledger fuera de tope, gaps de revisión abiertos, `tasks.md` con tareas `completado` y checkboxes sin marcar según `ledger-lint.py:704`, sin estimación), Cuando miro su tarjeta, Entonces cada alerta aparece con su texto, no solo con un color o un icono.
- [ ] [GWT] CA-07 — Dado la cartera, Cuando abro Iniciativas, Entonces veo al menos un gráfico de horas real frente a estimado por iniciativa y uno de coste por iniciativa, cada uno con su tabla equivalente. Las iniciativas sin datos aparecen en la tabla con «sin datos» y fuera de las barras.
- [ ] [GWT] CA-08 — Dado una tarjeta de iniciativa con plan, Cuando la activo con ratón o con Enter, Entonces navego a la página Plan de esa iniciativa.

### Plan (6)

- [ ] [GWT] CA-09 — Dado un `tasks.md` válido, Cuando abro su Plan, Entonces veo un kanban de solo lectura con una columna por estado del vocabulario del ledger (`borrador · en-progreso · en-revision · completado · cancelado`, `ledger-lint.py:61`) y una tarjeta por `T-XX` con ID, título, fase y horas real/estimado. No debe crear columnas para estados fuera de ese vocabulario: una tarea con estado desconocido va a una franja «estado no reconocido» con el literal.
- [ ] [GWT] CA-10 — Dada una tarjeta de tarea, Cuando la abro (clic o Enter), Entonces veo su descripción, criterios de aceptación con su casilla, `Verificación` (y la salida ejecutada si existe), dependencias, la última «Revisión de dos lentes — intento N» y sus gaps abiertos con severidad. No debe mostrar contenido de `execution-history.md` como si estuviera en el ledger: si la tarea tiene historia archivada, lo indica con la etiqueta «archivado» y el nombre `execution-history.md`, como texto y sin enlace (**enmienda 2026-10-16**, decisión del usuario sobre F2-23: ni el panel servido ni la copia exportada sirven ese fichero y un enlace daría 404).
- [ ] [GWT] CA-11 — Dado un ledger con fases, Cuando abro el Plan, Entonces veo un gráfico de avance por fase (completadas/total) con su tabla, con las mismas cifras que la tabla «Resumen de progreso» del ledger.
- [ ] [GWT] CA-12 — Dado un ledger con fechas de cierre por tarea, Cuando abro el Plan, Entonces veo un burndown de tareas pendientes por fecha; sin fechas, veo «burndown no disponible: el ledger no registra fechas de cierre» y ningún gráfico interpolado.
- [ ] [GWT] CA-13 — Dado un ledger con columnas `real`/`est`, Cuando abro el Plan, Entonces veo real frente a estimado por fase y por tarea, marcando «(medido)» o «(estimado)» según indique el ledger. No debe tratar un valor «—» como 0.
- [ ] [GWT] CA-14 — Dado un ledger que se edita mientras el Plan está abierto en modo servido, Cuando pasan dos ciclos de refresco (10 s), Entonces el kanban refleja el nuevo estado sin recargar la página y sin perder la tarea abierta.

### Agentes en vivo (7)

- [ ] [GWT] CA-15 — Dado `sesion.actividad: true` y un subagente en curso con señal de menos de 60 s, Cuando abro Agentes en vivo, Entonces veo una fila por run con runtime, rol, inicio, duración transcurrida y la última herramienta usada.
- [ ] [GWT] CA-16 — Dado un run con eventos de herramienta, Cuando lo abro, Entonces veo su línea de tiempo: por evento, hora, nombre de la herramienta, resumen redactado del argumento, `T-XX` si se atribuyó, duración y resultado (`ok` / `error`). No debe mostrar contenido de ficheros, salidas de comandos, prompts ni chain-of-thought.
- [ ] [GWT] CA-17 — Dado un argumento de herramienta que contiene un secreto evidente (token, clave, `Authorization:`), Cuando se registra el evento, Entonces el resumen persistido y el mostrado pasan por `redact.py` y no contienen el secreto. Test con el corpus de secretos de `redact.py`.
- [ ] [GWT] CA-18 — Dado un evento cuya tarea no se puede atribuir con certeza, Cuando se muestra, Entonces aparece «tarea: sin atribuir». No debe deducir la tarea del texto del argumento ni de la proximidad temporal.
- [ ] [GWT] CA-19 — Dado una última señal de un run con más de 60 s, Cuando miro su fila, Entonces su estado es «sin señal reciente» y su duración se congela en la última señal, no «terminado» ni «muerto».
- [ ] [GWT] CA-20 — Dado `sesion.actividad` ausente o `false`, Cuando se ejecutan herramientas, Entonces no se escribe ningún evento en disco (test: el directorio de estado no cambia), y la página explica cómo activarlo.
- [ ] [GWT] CA-21 — Dado un historial de eventos en su tope (I-03), Cuando llega un evento nuevo, Entonces se descarta el más antiguo y la página muestra «historial recortado a los últimos N eventos». El hook sale con exit 0 aunque falle la escritura (ADR-007) y no hace llamadas de red (constitución §2).

### Memoria (6)

- [ ] [GWT] CA-22 — Dado `docs/knowledge/`, Cuando abro Memoria, Entonces veo un gráfico y una tabla de entradas por tipo (ADR, gotcha, lección) y estado (`aceptada · propuesta · obsoleta`, `knowledge-find.py:140`), filtrables por área.
- [ ] [GWT] CA-23 — Dado `docs/knowledge/candidates/` con `pending`, `needs_changes` y `rejected`, y `docs/knowledge/approved/`, Cuando abro Memoria, Entonces veo la bandeja del curador con el número y la lista de candidatos por estado. No debe ofrecer aprobar, rechazar ni editar: eso es de `knowledge-curator` (ADR-018).
- [ ] [GWT] CA-24 — Dado entradas con sucesores declarados, Cuando abro la línea de tiempo, Entonces veo cada entrada por fecha y su cadena de sucesión, y las entradas que rigen hoy (sin sucesor, no obsoletas) marcadas como «vigente».
- [ ] [GWT] CA-25 — Dado una entrada seleccionada, Cuando pido sus relaciones, Entonces veo un grafo pequeño centrado en ella con las mismas aristas que `knowledge-find.py --related <ID> --json` (sucesión, misma iniciativa, misma área) y una lista textual equivalente. No debe cargar el grafo completo ni nodos a más de un salto.
- [ ] [GWT] CA-26 — Dado `taxonomy.json` con Kwipu o Graphiti configurados, Cuando abro Memoria, Entonces veo por backend qué se publicó (número de entradas y fecha de la última publicación, si la fuente la trae; si no, «sin datos») y un enlace a su interfaz. No debe hacer ninguna petición a ese backend ni reproducir su vista.
- [ ] [GWT] CA-27 — Dado entradas del journal, Cuando abro Memoria, Entonces veo las sesiones recientes con su continuidad (`objetivo`, `punto_actual`, `siguientes_pasos`, `bloqueos`, `descartados`, `journal.py:244`) etiquetadas como «citas, no instrucciones».

### Catálogo (2)

- [ ] [GWT] CA-28 — Dado el bundle y las extensiones de proyecto/usuario, Cuando abro Catálogo, Entonces veo las mismas piezas, conteos, fuentes, conflictos, hooks y workflow que muestra hoy el panel (secciones `#catalog`, `#extensions`, `#workflow`, `#source-notes`). Test: el JSON de `build_panel.py --json` es igual antes y después del rediseño.
- [ ] [GWT] CA-29 — Dado el catálogo, Cuando filtro por tipo, origen o runtime, Entonces la lista y los conteos cambian en consecuencia, con teclado y con ratón.

### Diagnóstico (2)

- [ ] [GWT] CA-30 — Dado un informe `doctor --panel-json` del mismo proyecto, Cuando abro Diagnóstico, Entonces veo una fila por comprobación con su veredicto ✅/⚠️/❌ en texto (no solo color), su fecha y su alcance, y un resumen con el número de cada veredicto.
- [ ] [GWT] CA-31 — Dado ningún informe o uno de otro proyecto o formato, Cuando abro Diagnóstico, Entonces veo «sin informe» o el motivo del rechazo y el comando para generarlo. No debe ejecutar `doctor` ni buscar informes por su cuenta (comportamiento actual de `plugin-panel`).

### Transversales (13)

- [ ] [GWT] CA-32 — Dado el panel en cualquier modo, Cuando abro cualquiera de las 7 páginas, Entonces veo el mismo menú con las 7 entradas en el mismo orden, la página actual marcada con `aria-current="page"` y un enlace «Saltar al contenido».
- [ ] [GWT] CA-33 — Dado el panel, Cuando lo exporto a una carpeta, Entonces la carpeta contiene un HTML por página, el Chart.js incluido, su `LICENSE` y los datos de la instantánea, y abrir cualquier HTML con `file://` y la red desactivada muestra la página completa con sus gráficos.
- [ ] [GWT] CA-34 — Dado el modo servido, Cuando lo lanzo, Entonces escucha solo en `127.0.0.1` con la URL de token de su proceso; una petición sin token, con `Host` u `Origin` distintos responde 403 (comportamiento actual, `serve_panel.py:347-356`).
- [ ] [GWT] CA-35 — Dado cualquier página en cualquier modo, Cuando la cargo, Entonces su CSP parte de `default-src 'none'`, no tiene `connect-src` fuera del propio servidor local y no aparece ninguna petición a otro origen. Test: el HTML generado no contiene `http://` ni `https://` en `src`/`href` de recursos, salvo los enlaces de navegación a backends de CA-26.
- [ ] [GWT] CA-36 — Dado el árbol del plugin, Cuando busco Chart.js, Entonces hay un único fichero con la versión fija declarada en un fichero de procedencia (versión, origen, SHA-256) y su `LICENSE`; un test falla si el hash del fichero no coincide con el declarado.
- [ ] [GWT] CA-37 — Dado cualquier página, Cuando navego solo con teclado, Entonces llego a todo elemento interactivo (menú, filtros, tarjetas, detalle de tarea, relaciones) con Tab en un orden que sigue la lectura, el foco es visible y ningún elemento fijo lo tapa (WCAG 2.2: 2.1.1, 2.4.3, 2.4.7, 2.4.11), y Escape cierra un detalle abierto devolviendo el foco a su tarjeta.
- [ ] [GWT] CA-38 — Dado los colores de texto y de gráficos de la paleta, Cuando se miden, Entonces el texto tiene un contraste ≥ 4,5:1 (≥ 3:1 el texto grande) y las marcas de gráficos, bordes de controles y foco ≥ 3:1 con su fondo (WCAG 2.2: 1.4.3, 1.4.11). Test automático sobre la paleta.
- [ ] [GWT] CA-39 — Dado cualquier gráfico, Cuando lo inspecciono, Entonces tiene un nombre accesible que dice qué muestra y una tabla de datos equivalente accesible por teclado, y ninguna información se distingue solo por color (WCAG 2.2: 1.1.1, 1.4.1).
- [ ] [GWT] CA-40 — Dado una fuente sin un dato o con un dato parcial, Cuando la página lo muestra, Entonces aparece «sin datos» o «parcial: N de M» con su origen. No debe aparecer un 0, una media o un valor interpolado en su lugar. Test con fixtures de ledger sin `generacion:`, sin `real` y sin fechas.
- [ ] [GWT] CA-41 — Dado un proyecto de prueba con su ruta bajo un home de usuario y un autor de git con correo, Cuando genero el panel en ambos modos, Entonces ningún HTML, JSON ni evento de actividad contiene la ruta absoluta del home, el nombre de usuario del sistema ni direcciones de correo. Test con grep sobre la salida.
- [ ] [GWT] CA-42 — Dado el mismo proyecto, Cuando genero el panel desde Claude Code, Codex y OpenCode, Entonces las 7 páginas se generan en los tres; lo que un runtime no aporta (p. ej. eventos de herramienta) se declara en la página, no se omite en silencio. `export-interop.py --check` pasa.
- [ ] [GWT] CA-43 — Dado el panel con la revisión visual del plan activa (`--review-initiative`), Cuando la uso, Entonces anotar y enviar una decisión funciona como hoy (`plan-review.py`, `tests/test_panel_review_*`). *(Reformulado por la enmienda 2026-10-15; antes: «No debe añadirse ningún otro camino de escritura desde el navegador».)* La ÚNICA vía de escritura desde el navegador sigue siendo `plan-review.py` (abrir `requested-review`, comentarios, decisión); no debe existir ninguna otra.
- [ ] CA-44 — Al cerrar cada fase, las suites `tests/test_plugin_panel.py`, `tests/test_panel_*`, `tests/test_dashboard.py`, `tests/test_agent_activity_*` y `tests/test_graphiti_security.py` pasan, junto con `lint_plugin.py` y `evals/check.py`; y el usuario revisa la fase en el navegador (comprobación manual M-xx) antes de pasar a la siguiente.

### Revisión del plan desde el panel — enmienda 2026-10-15 (10)

Origen (citas del usuario, 2026-10-15): «en el dashboard, se podrían aprobar planes? e interactuar con el plan para corregir cosas como hace ecc? así tendríamos un sólo dashboard? que te parece? de todas formas se puede dejar el comando que lanza la UI del plan para interactuar». Aclaración: «me refería a aprobar o solicitar correcciones, no editar manualmente los markdown». Reutiliza `agent-kits/shared/plan-review.py` y el servidor `serve_panel.py` (rutas `api/review/<id64>/<op>`); no los sustituye.

- [ ] [GWT] CA-45 — Dado el panel servido con `--review-state-root` y la página Plan de una iniciativa sin revisión, Cuando pulso «Revisar este plan», Entonces el cliente envía el id de iniciativa que el servidor publicó en su inventario (nunca una ruta ni un nombre de fichero) y el servidor abre la revisión con `plan-review.py open` y la muestra en la propia página, sin haber lanzado el panel con `--review-initiative`. Un id que no está en el inventario del servidor se rechaza con error y no escribe nada en disco (test: el directorio de estado no cambia).
- [ ] [GWT] CA-46 — Dado la página Plan con una revisión abierta, Cuando añado comentarios anclados por `section_id` y envío «aprobar» o «pedir correcciones», Entonces la decisión y los comentarios se guardan con `plan-review.py` (`submit`), con redacción, ≤ 20 comentarios y ≤ 2.000 caracteres por comentario; pasarse de cualquiera de los topes se rechaza con el mismo error que hoy.
- [ ] [GWT] CA-47 — Dado el servidor del panel, Cuando recibe una operación de revisión, Entonces se aplican las mismas protecciones que hoy: sin cookies, POST solo con el token de la URL del proceso, 403 ante `Host`, `Origin` o `Sec-Fetch-Site` ajenos, y la misma CSP (`default-src 'none'`, nonce por proceso). Test: POST sin token y con `Origin` ajeno → 403 y estado sin cambios.
- [ ] [GWT] CA-48 — Dado una revisión abierta desde el navegador, Cuando miro su registro, Entonces su `gate_key` es `requested-review` y nunca `plan-ok`. No debe existir ninguna petición del navegador que fije o cambie la puerta a `plan-ok`; `plan-ok` solo lo abre `/dev-cycle`. Test: el cuerpo de la petición no puede traer `gate_key` y, si lo trae, se rechaza.
- [ ] [GWT] CA-49 — Dado un inventario de iniciativas con revisiones en cada situación, Cuando abro Iniciativas y el Plan, Entonces la tarjeta del kanban y la cabecera del Plan muestran el estado en texto («sin revisión · pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión»), con la misma cifra en ambos sitios, calculado con una operación de solo lectura de `plan-review.py` (`summary`, design.md §8; solo lectura: abrir la página no crea ni modifica ningún fichero de `.claude/plan-review/`). No depende solo del color.
- [ ] [GWT] CA-50 — Dado una revisión aprobada (o con cambios pedidos) sobre una versión de `improvement-plan.md`, Cuando el plan cambia (hash de la versión distinto), Entonces el estado pasa a «obsoleta por cambio de versión» en tarjeta y cabecera, la decisión anterior no cuenta como vigente y la UI exige una nueva decisión.
- [ ] [GWT] CA-51 — Dado una revisión en la que el agente ha respondido (`result` con disposición por comentario), Cuando abro el Plan, Entonces veo bajo cada comentario la respuesta del agente y su disposición, y el resultado de `verify-result` si existe. Un comentario sin respuesta aparece como «sin respuesta del agente».
- [ ] [GWT] CA-52 — Dado el panel en modo exportado (`--export`), Cuando abro cualquier página, Entonces no hay botones ni formularios de revisión, ningún `fetch` de escritura y el estado de revisión, si aparece, es texto de la instantánea marcado como tal. Test: el HTML exportado no contiene los controles de revisión ni la ruta `api/review`.
- [ ] [GWT] CA-53 — Dado el panel servido sin `--review-state-root` (o sin `--project`), Cuando abro el Plan, Entonces el botón de revisión no aparece y la página explica en una frase cómo activarlo (parámetros que lo habilitan). No debe mostrar un botón que falle al pulsarlo.
- [ ] [GWT] CA-54 — Dado el cambio completo, Cuando se ejecutan los tests de `plan-review.py` y `tests/test_panel_review_*`, Entonces siguen pasando sin modificar sus expectativas: el formato de estado en `.claude/plan-review/`, los presupuestos (comentarios, caracteres, tamaño de respuesta) y el comando `--review-initiative` se conservan, y `/dev-cycle` en `plan-ok` y `/work-resume` funcionan como antes.

## Requisitos no funcionales

| Requisito | Cifra | Origen |
|---|---|---|
| Lectura por fichero de ledger | ≤ 256 KiB | `serve_panel.py:15`; tope del ledger (`ledger-lint` avisa al 70 %, commit `aa87e69`) |
| Lectura total por petición | ≤ 1 MiB | `serve_panel.py:16` |
| Frescura del estado «ahora» de un agente | 60 s | `agent-activity.py:9` |
| Refresco en modo servido | 5 s | `panel-live.js:63`, `panel-activity.js:67` |
| Presupuesto del hook de actividad | ≤ 2.000 ms y exit 0 siempre | `hooks/run-hook.mjs:26`; ADR-007 |
| Accesibilidad | WCAG 2.2 AA en teclado, contraste y alternativas textuales de gráficos | Requisito del usuario |
| Red | Cero peticiones a otros orígenes | Requisito del usuario; constitución §2 y §4 |
| Tiempo de carga de página, tamaño máximo de la exportación, tope del historial de eventos, coste por evento de herramienta | **sin cifra** | Incógnitas I-03, I-04, I-05, I-06 |

## Restricciones

| Restricción | Tipo |
|---|---|
| Sin red ni CDN en ejecución ni en generación; Chart.js incluido con versión fija y licencia | **Política fija** (decisión del usuario) |
| Kanban y páginas de solo lectura sobre el ledger; `tasks.md` es la única fuente (constitución §2). **(Enmienda 2026-10-15)** Única excepción de escritura desde el navegador: la revisión del plan por `plan-review.py` (abrir `requested-review`, comentarios, decisión); nunca markdown, tareas ni `plan-ok` | **Política fija** |
| Hooks informan, no deciden; exit 0 siempre; sin red desde hooks (ADR-007, constitución §1-§2) | **Política fija** |
| Todo texto persistido o mostrado pasa por `redact.py`; nunca chain-of-thought ni conversación cruda (constitución §4) | **Política fija** |
| Captura de actividad opt-in, desactivada por defecto, estado local fuera de git | **Política fija** |
| Scripts del plugin solo con stdlib de Python (constitución §2); Chart.js es un recurso JS incluido, no una dependencia Python | **Política fija** |
| Multi-runtime: las piezas no saben de runtimes; `interop/` se regenera con `export-interop.py` | **Política fija** |
| Un rol, un dueño (ADR-011): al cerrar no quedan dos dashboards HTML con el mismo rol | **Política fija** |
| Sin datos personales en nada versionado ni exportado | **Política fija** |
| Contratos `dashboard.md`, `build_dashboard.py --json` y `doctor --panel-json` sin cambios | **Preferencia** (se cambia con motivo y con su consumidor actualizado en el mismo cambio) |
| Refresco de 5 s y topes actuales del servidor | **Preferencia** |
| Aspecto visual concreto (paleta, tipografía, disposición) | **Preferencia** (lo valida el usuario en la revisión manual de cada fase) |
| **D-A1** — Qué pieza es dueña de la presentación: `plugin-panel` absorbe el HTML de `roadmap-dashboard` (que queda como proveedor de datos MD/JSON) o al revés; y qué comando abre el panel | **Decisión abierta → architect** |
| **D-A2** — Modelo de captura de herramientas: qué eventos nativos de cada runtime se usan, cómo se atribuye herramienta → run → `T-XX` sin leer transcripts, y dónde y con qué tope se guarda el historial | **Decisión abierta → architect** |

## Datos / integraciones

| Fuente | Uso | Sensibilidad |
|---|---|---|
| `docs/roadmap/*/` (spec, evaluation, improvement-plan, tasks, execution-history) | Inicio, Iniciativas, Plan | Interno; sin datos personales esperados, pero se redacta igual |
| `docs/knowledge/` (adr, gotchas, lessons, candidates, approved, journal) | Memoria | El journal contiene citas de turnos del usuario: se muestran redactadas y como citas |
| `.claude/knowledge-services/taxonomy.json`, manifiestos y outbox de backends | Memoria (sincronización) | Puede contener URLs locales; no se hace ninguna petición |
| Snapshot e historial de actividad bajo `.claude/` | Agentes en vivo | Local, fuera de git; solo nombres de herramienta y resúmenes redactados |
| `doctor --panel-json` | Diagnóstico | Proyección portable sin datos libres |
| Bundle y extensiones (`project-pieces.py`) | Catálogo | Sin cuerpos privados ni datos de conexión (comportamiento actual) |

## Fases propuestas

El planner debe respetar estas cuatro fases acordadas con el usuario. Cada fase cierra con tests, revisión adversarial y la revisión manual del usuario (CA-44). **(Enmienda 2026-10-15)** La fase 2 añade una vía de escritura nueva desde el navegador: su revisión adversarial debe incluir la lente C de seguridad de forma obligatoria (no solo cuando `review-lens-select.py` la marque).

| Fase | Contenido | Criterios |
|---|---|---|
| **1 — Base común** | Plantilla multi-página, menú común, Chart.js incluido (versión fija, licencia, hash), CSP sin red, modos servido y exportado, accesibilidad base, aplicación de D-A1 | CA-32 a CA-41, CA-43 |
| **2 — Iniciativas y Plan** | Kanban de planes y de tareas, detalle de tarea, gráficos de cartera, avance por fase, burndown, real vs estimado; Inicio con sus cifras de cartera | CA-01 a CA-03, CA-05 a CA-14, CA-45 a CA-54 (enmienda 2026-10-15; T-12 ya mueve la revisión a la página Plan) |
| **3 — Agentes en vivo** | Ampliación del registro con eventos de herramienta (D-A2), página Agentes en vivo, actividad reciente en Inicio | CA-04, CA-15 a CA-21, CA-42 en lo relativo a eventos |
| **4 — Memoria, Catálogo y Diagnóstico** | Página Memoria (vista sencilla), Catálogo mejor presentado sin pérdida de información, Diagnóstico | CA-22 a CA-31 |

## Pruebas

- Unitarias por fase, con TDD (constitución §1): generadores de cada página, proyección de datos ausentes/parciales (CA-40), redacción del resumen de argumentos (CA-17), atribución de tarea (CA-18), tope del historial (CA-21), hash de Chart.js (CA-36), contraste de la paleta (CA-38), ausencia de datos personales (CA-41).
- Servidor: las suites `tests/test_panel_*_server.py` existentes más las nuevas rutas; 403 por token/Host/Origin (CA-34).
- E2E con Playwright en local (qa): cada `[GWT]` de arriba con el mismo ID en `test-plan.md`; navegación por teclado (CA-37); carga con la red bloqueada y comprobación de cero peticiones a otros orígenes (CA-33, CA-35).
- No regresión: `build_panel.py --json` igual antes/después (CA-28); `build_dashboard.py --json` y `dashboard.md` iguales para el mismo `docs/roadmap/`; revisión visual del plan (CA-43).
- Revisión del plan desde el panel (CA-45 a CA-54): tests de servidor (id desconocido sin escritura, token/Origin, `gate_key` imposible de fijar desde el cliente), de proyección de estado en solo lectura y de UI; las suites de `plan-review.py` y `tests/test_panel_review_*` sin cambios (CA-54).
- Multi-runtime: generación en los tres runtimes y `export-interop.py --check` (CA-42).
- Manual (M-xx): revisión del usuario en el navegador al cerrar cada fase (CA-44).

## Referencias

- Encargo y requisitos literales: conversación del 2026-10-15.
- `skills/plugin-panel/SKILL.md`, `skills/plugin-panel/scripts/build_panel.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/references/panel.html`.
- `skills/roadmap-dashboard/SKILL.md`, `skills/roadmap-dashboard/scripts/build_dashboard.py`.
- `agent-kits/shared/agent-activity.py`, `agent-kits/shared/agent-activity-store.py`, `hooks/hooks.json`, `hooks/run-hook.mjs`.
- `agent-kits/shared/knowledge-find.py`, `agent-kits/shared/knowledge-curation.py`, `agent-kits/shared/journal.py`, `skills/knowledge-services/SKILL.md`.
- `agent-kits/shared/doctor.py`, `agent-kits/shared/redact.py`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/progress-report.py`.
- `docs/CONSTITUTION.md`, `docs/agents/ROLES.md`, ADR-007, ADR-011, ADR-018.

## Decisiones confirmadas (revisión del usuario · 2026-10-15)

1. Panel en varias páginas HTML con menú común: Inicio, Iniciativas, Plan, Agentes en vivo, Memoria, Catálogo, Diagnóstico. **Confirmado.**
2. Chart.js incluido en el plugin con versión fija y licencia, sin CDN. **Confirmado.**
3. Servido en local y exportable a carpeta estática. **Confirmado.**
4. Memoria «algo sencillo»: estado, bandeja del curador, línea de tiempo con sucesores, relaciones de una entrada, sincronización con backends, journal reciente; sin explorador de grafos ni búsqueda semántica. **Confirmado.**
5. Ampliar el registro de actividad con eventos de herramienta redactados, tarea atribuible, duración y resultado; local, acotado y opt-in. **Confirmado.**
6. Iniciativa propia con `/dev-cycle` en flujo completo y cuatro fases, cada una con tests y revisión. **Confirmado.**

## Aprobación

Aprobada el 2026-10-15. Fuente: el usuario validó en la conversación la estructura de siete páginas, Chart.js incluido, la memoria sencilla sin duplicar Kwipu/Graphiti/Graphify y los runs de agentes («me parece bien», «la parte memoria me parece bien tu propuesta, algo sencillo») y fijó como objetivo «finaliza lo del archivado y lo del dashboard». Los cuatro supuestos de negocio de abajo se resuelven con la opción por defecto que la spec ya proponía (revisión visual conservada en la página Plan; `dashboard.md` sigue para Confluence; el modo exportado sale sin datos personales; interfaz en español); cualquiera se revisa si el usuario lo pide.

### Enmienda 2026-10-15 — revisión del plan desde el panel

Aprobada por el usuario en la conversación del 2026-10-15 con las citas de CA-45 a CA-54 («en el dashboard, se podrían aprobar planes? …» y «me refería a aprobar o solicitar correcciones, no editar manualmente los markdown»). Cambia: Alcance (dentro y fuera), CA-43 (reformulado), CA-45 a CA-54 (nuevos), política de solo lectura (con su única excepción), fase 2 y pruebas. No cambia nada más de lo aprobado. Motivo: tener un solo dashboard (el diseño O1 ya deja `plugin-panel` como dueño de la presentación) sin perder la revisión visual del plan.

## Supuestos

- **Hecho técnico:** el servidor del panel escucha solo en `127.0.0.1` y usa un token por proceso — `skills/plugin-panel/scripts/serve_panel.py:471`, `:488`.
- **Hecho técnico:** la CSP del modo servido es `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-…'` con nonce por proceso — `serve_panel.py:469-470`, `:492`.
- **Hecho técnico:** el HTML estático actual declara su CSP en un `<meta>` con `script-src 'unsafe-inline'` — `skills/plugin-panel/references/panel.html:2`.
- **Hecho técnico:** el servidor rechaza con 403 un `Host`, `Origin` o `Sec-Fetch-Site` ajenos — `serve_panel.py:347-356`.
- **Hecho técnico:** topes de lectura 256 KiB por fichero, 1 MiB total, 64 iniciativas, 64 KiB por respuesta — `serve_panel.py:15-18`.
- **Hecho técnico:** la captura de actividad exige `sesion.actividad: true` — `agent-kits/shared/agent-activity-store.py:100`.
- **Hecho técnico:** hoy solo se capturan `SubagentStart`/`SubagentStop` en Claude/Codex — `agent-activity-store.py:160`; en OpenCode, eventos de ejecución de sesión — `hooks/opencode-plugin.js:19`.
- **Hecho técnico:** la proyección de actividad usa 60 s de frescura y 64 observaciones, y nunca afirma que un proceso vive o murió — `agent-kits/shared/agent-activity.py:9-10`, `:75`.
- **Hecho técnico:** el hook `agent-activity` tiene 2.000 ms de presupuesto — `hooks/run-hook.mjs:26`.
- **Hecho técnico:** el refresco del modo servido es de 5 s — `skills/plugin-panel/references/panel-live.js:63`, `panel-activity.js:67`.
- **Hecho técnico:** el `--json` de `build_dashboard.py` añade `procedencia` y trata la ausencia como null, nunca 0 — `skills/roadmap-dashboard/scripts/build_dashboard.py:1169-1170`.
- **Hecho técnico:** vocabulario de estados del ledger — `agent-kits/shared/ledger-lint.py:61`.
- **Hecho técnico:** orden de estados de memoria `aceptada · propuesta · obsoleta` — `agent-kits/shared/knowledge-find.py:140`; `--related` da el grafo curado de una entrada — `knowledge-find.py:12`, `:102`.
- **Hecho técnico:** campos de continuidad del journal — `agent-kits/shared/journal.py:244`.
- **Hecho técnico:** `doctor.py --panel-json` es la proyección portable para el panel — `agent-kits/shared/doctor.py:87-88`.
- **Hecho técnico:** la narrativa larga del ledger se archiva en `execution-history.md` con `ledger-archive.py` — commit `aa87e69`.
- **Restricción de negocio (confirmado por el usuario, enmienda 2026-10-15):** la revisión visual del plan (`--review-initiative`) se conserva y vive en la página Plan; además se puede abrir desde el propio panel (CA-45 a CA-54). «de todas formas se puede dejar el comando que lanza la UI del plan para interactuar».
- **Hecho técnico (enmienda 2026-10-15):** `plan-review.py` ya ofrece open/view/status/comments/submit/receive/ack/consume/result/verify-result, decisión `approve`|`request_changes`, ≤ 20 comentarios de ≤ 2.000 caracteres redactados, versión por hash y gate `requested-review` (por defecto) o `plan-ok`; el servidor lo expone en `api/review/<id64>/<op>` con `do_POST` (`serve_panel.py:386`, `:415`).
- **Riesgo (enmienda 2026-10-15):** es una vía de escritura nueva desde el navegador; se mitiga con id de inventario (nunca ruta), token/Origin/CSP actuales, `requested-review` fijo y lente C obligatoria en la revisión de la fase 2.
- **Restricción de negocio (supuesto hasta confirmar):** el PM sin git sigue usando `dashboard.md` en Confluence y no necesita el panel nuevo allí — la confirmaría el usuario.
- **Restricción de negocio (supuesto hasta confirmar):** el modo exportado puede compartirse fuera del equipo del proyecto, y por eso CA-41 aplica también a él — la confirmaría el usuario.
- **Restricción de negocio (supuesto hasta confirmar):** basta con español en la interfaz del panel (como el panel actual) — la confirmaría el usuario.

## Incógnitas

| ID | Incógnita | Quién la resuelve |
|---|---|---|
| D-A1 | Dueño de la presentación (`plugin-panel` absorbe `roadmap-dashboard` HTML o al revés) y comando de entrada, respetando ADR-011 | architect |
| D-A2 | Modelo de captura de herramientas: eventos nativos por runtime (Claude `PreToolUse`/`PostToolUse`, Codex, OpenCode `execute.before/after`), atribución run → `T-XX` sin leer transcripts, almacenamiento del historial | architect |
| I-01 | Versión exacta de Chart.js (hipótesis: 4.x, licencia MIT) y si su fichero minificado funciona con la CSP con nonce del modo servido y con la CSP del HTML estático abierto con `file://` (hipótesis a validar con una prueba en la fase 1) | architect / implementer (fase 1) |
| I-02 | Si el ledger registra fecha de cierre por tarea; sin ella no hay burndown (CA-12) | architect |
| I-03 | Tope del historial de eventos de herramienta (número y tamaño) y su retención | usuario / architect |
| I-04 | Si las nuevas páginas caben en 64 KiB por respuesta o necesitan otro tope | architect |
| I-05 | Coste aceptable por evento de herramienta en el hook (latencia añadida a cada herramienta) | usuario |
| I-06 | Tiempo de carga objetivo por página y tamaño máximo de la carpeta exportada | usuario |
| I-07 | Longitud del resumen redactado del argumento (precedente en el repo: 160 caracteres en `serve_panel.py:139`, no confirmado para este uso) | usuario / architect |
| I-08 | Si Codex expone eventos por herramienta con identificador de subagente; si no, CA-42 lo declara como «no emite eventos de herramienta» | architect |
| I-10 | Cómo calcula el servidor el estado de revisión de TODAS las iniciativas sin escribir y dentro del tope de 64 KiB por respuesta (consulta de estado por iniciativa o proyección agregada), y cómo se enlaza el id del inventario con el `<id64>` de la ruta `api/review/` | architect / implementer (fase 2) |
| I-09 | Dónde se lee «qué se publicó» y cuándo en Kwipu/Graphiti sin red (manifiesto, outbox) y si traen fecha | architect |
