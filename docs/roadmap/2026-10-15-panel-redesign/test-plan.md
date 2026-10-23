# Plan de pruebas — Rediseño del panel local: multi-página, kanban y gráficos

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **URL local** | Servido: `http://127.0.0.1:<puerto>/<token>/index.html` (URL que imprime `build_panel.py --serve --project <fixture>`). Exportado: `file://<carpeta>/index.html` (`build_panel.py --export <carpeta>`). |

Datos de prueba: las fixtures de `tests/fixtures/panel-redesign/` (T-01): roadmap con estados variados, iniciativa ilegible, ledger > 256 KiB, ledger sin `generacion:`, sin `real`, con `—`, con y sin `Cerrada`, gaps de revisión abiertos y `execution-history.md`; memoria con ADR/gotcha/lección, sucesores, candidatos por estado, manifiestos de Kwipu/Graphiti y journal; bundle de catálogo; `events.json` sintético. Proyecto de prueba bajo un home falso con autor de git con correo (CA-41). Toda ejecución con la red bloqueada salvo `127.0.0.1`.

## Automáticos (E2E — los ejecuta `qa` con Playwright)

### E2E-01 — Menú común en las siete páginas
- **Objetivo**: CA-32 — mismo menú, mismo orden, página actual marcada y salto al contenido.
- **Precondiciones**: panel servido y exportado sobre las fixtures.
- **Pasos**:
  1. Abrir cada una de las 7 páginas en servido y en exportado.
  2. Leer el `<nav>` y el primer enlace enfocable.
- **Aserciones**:
  - [ ] 7 entradas en el orden Inicio · Iniciativas · Plan · Agentes en vivo · Memoria · Catálogo · Diagnóstico.
  - [ ] `aria-current="page"` solo en la actual; «Saltar al contenido» es el primer foco.
- **Capturas esperadas**: menú en Inicio y en Memoria.
- **Cubre tareas**: T-05, T-09, T-10, T-11, T-12

### E2E-02 — Exportado abierto con `file://` y sin red
- **Objetivo**: CA-33, CA-35, CA-36 — carpeta completa, gráficos visibles, cero peticiones y Chart.js único con su licencia.
- **Precondiciones**: `--export` a una carpeta temporal; red desactivada.
- **Pasos**:
  1. Listar la carpeta exportada.
  2. Abrir cada HTML con `file://` en Chromium y Firefox.
- **Aserciones**:
  - [ ] Un HTML por página, `vendor/chart.js/chart.umd.min.js`, `LICENSE.md`, `PROVENANCE.json` y los datos de la instantánea.
  - [ ] Los gráficos se dibujan; 0 eventos `securitypolicyviolation`; 0 peticiones a otros orígenes.
  - [ ] Cabecera con la fecha de generación y el texto aprobado «Copia estática del <fecha> · para verla en vivo, abre el panel servido con `/plugin-catalog --serve`». **(Enmienda 2026-10-21, qa)**
- **Capturas esperadas**: Inicio exportado con gráficos.
- **Cubre tareas**: T-02, T-03, T-08

### E2E-03 — Servido: solo loopback con token
- **Objetivo**: CA-34 — sin token u otro token → 404 sin contenido; `Host` u `Origin` ajenos → 403. **(Enmienda 2026-10-21, qa)** (el 404 ya era el comportamiento previo; fija `tests/test_panel_server.py`).
- **Precondiciones**: `--serve` sobre la fixture.
- **Pasos**:
  1. Pedir una página con el token, sin token, con `Host` distinto y con `Origin` distinto.
- **Aserciones**:
  - [ ] Solo la petición con token y cabeceras propias responde 200; sin token u otro token → 404 sin contenido; `Host` u `Origin` ajenos → 403; el estado no cambia. **(Enmienda 2026-10-21, qa)**
  - [ ] El proceso escucha solo en `127.0.0.1`.
- **Capturas esperadas**: —
- **Cubre tareas**: T-11

### E2E-04 — Servido: CSP y cero peticiones ajenas
- **Objetivo**: CA-35 en servido.
- **Precondiciones**: `--serve`; enrutado de Playwright que aborta cualquier origen distinto del servidor.
- **Pasos**:
  1. Recorrer las 7 páginas.
- **Aserciones**:
  - [ ] La cabecera CSP empieza por `default-src 'none'` y `connect-src` es `'self'`.
  - [ ] 0 peticiones abortadas y 0 `securitypolicyviolation`.
- **Capturas esperadas**: —
- **Cubre tareas**: T-03, T-11

### E2E-05 — Navegación solo con teclado
- **Objetivo**: CA-37 — Tab en orden de lectura, foco visible, Escape devuelve el foco.
- **Precondiciones**: servido.
- **Pasos**:
  1. Recorrer con Tab menú, filtros, tarjetas, detalle de tarea y relaciones de memoria.
  2. Abrir un detalle con Enter y cerrarlo con Escape.
- **Aserciones**:
  - [ ] Todo elemento interactivo es alcanzable; el foco es visible y nada fijo lo tapa.
  - [ ] Escape cierra el detalle y el foco vuelve a su tarjeta.
- **Capturas esperadas**: foco sobre una tarjeta del Plan.
- **Cubre tareas**: T-05, T-19, T-24, T-33, T-36

### E2E-06 — Gráficos accesibles y respaldo sin Chart.js
- **Objetivo**: CA-39 y la fila «Falta el fichero de Chart.js» del manejo de errores.
- **Precondiciones**: exportado normal y exportado con `chart.umd.min.js` borrado.
- **Pasos**:
  1. Inspeccionar cada `<figure>` de gráfico.
  2. Repetir sin Chart.js.
- **Aserciones**:
  - [ ] Cada gráfico tiene nombre accesible y tabla equivalente alcanzable por teclado.
  - [ ] Sin Chart.js: tablas y aviso; ninguna página falla entera.
- **Capturas esperadas**: Catálogo sin Chart.js.
- **Cubre tareas**: T-07, T-09

### E2E-07 — Datos ausentes y parciales
- **Objetivo**: CA-40 — «sin datos» / «parcial: N de M» con su origen; nunca 0, media ni interpolación.
- **Precondiciones**: fixtures sin `generacion:`, sin `real`, con `—` y sin fechas de cierre.
- **Pasos**:
  1. Abrir Inicio, Iniciativas y el Plan de esas iniciativas.
- **Aserciones**:
  - [ ] Cada ausencia muestra su etiqueta y su origen.
  - [ ] Ningún 0 en su lugar; el burndown muestra su mensaje sin gráfico.
- **Capturas esperadas**: tarjeta con «sin datos».
- **Cubre tareas**: T-07, T-18, T-20, T-25, T-26

### E2E-08 — Sin datos personales en ningún modo
- **Objetivo**: CA-41.
- **Precondiciones**: proyecto de prueba bajo home falso; autor de git con correo; `events.json` con rutas absolutas en los argumentos.
- **Pasos**:
  1. Generar en servido (descargar páginas y API) y en exportado.
  2. Buscar la ruta del home, el usuario y correos en toda la salida.
- **Aserciones**:
  - [ ] 0 coincidencias en HTML, JSON y eventos.
- **Capturas esperadas**: —
- **Cubre tareas**: T-04, T-08, T-51

### E2E-09 — Tres runtimes
- **Objetivo**: CA-42 — las 7 páginas en Claude Code, Codex y OpenCode; lo que falta se declara.
- **Precondiciones**: plugin instalado en los tres runtimes (o sus traducciones de `interop/`).
- **Pasos**:
  1. Generar el panel desde cada runtime.
  2. Abrir Agentes en vivo con eventos de cada runtime.
- **Aserciones**:
  - [ ] Las 7 páginas en los tres.
  - [ ] Codex: «se agrupan por sesión»; un runtime sin eventos de herramienta lo declara.
  - [ ] `export-interop.py --check` pasa.
- **Capturas esperadas**: Agentes en vivo con las declaraciones.
- **Cubre tareas**: T-14, T-45, T-47, T-49, T-53

### E2E-10 — Revisión visual del plan
- **Objetivo**: CA-43 — anotar y enviar una decisión funciona como hoy (con `--review-initiative`; la apertura desde el panel está en E2E-24).
- **Precondiciones**: `--serve --review-initiative <fixture> --review-state-root <tmp>`.
- **Pasos**:
  1. Abrir el Plan, anotar un comentario y enviar la decisión.
- **Aserciones**:
  - [ ] `plan-review.py` recibe la decisión igual que antes.
  - [ ] Ningún otro control del navegador escribe en disco.
- **Capturas esperadas**: comentario enviado.
- **Cubre tareas**: T-12

### E2E-24 — Plan: abrir, comentar y decidir una revisión desde el panel
- **Objetivo**: CA-45 a CA-53 (enmienda 2026-10-15) — abrir la revisión del plan de cualquier iniciativa sin `--review-initiative`, con una sola vía de escritura.
- **Precondiciones**: `--serve --project <fixture> --review-state-root <tmp>/.claude/plan-review --review-panel`; fixtures con iniciativas sin revisión, pendiente, con cambios pedidos, aprobada, obsoleta y con respuestas del agente.
- **Pasos**:
  1. Abrir Iniciativas y leer el estado de revisión de cada tarjeta; abrir el Plan de una iniciativa sin revisión.
  2. Pulsar «Revisar este plan» con teclado, añadir comentarios por sección y enviar «pedir correcciones».
  3. Editar `improvement-plan.md` de la fixture y esperar al refresco.
  4. Reiniciar el panel sin `--review-panel` y sin `--project`, y abrir `--export`.
  5. Intentar `POST api/review-open/<id16>` con `gate_key` en el cuerpo, con `Origin` ajeno, sin token y con un id16 desconocido.
- **Aserciones**:
  - [ ] Tarjeta y cabecera del Plan muestran el mismo estado en texto («sin revisión · pendiente · cambios pedidos · aprobada vN · obsoleta por cambio de versión»); abrir la página no cambia ningún fichero de `.claude/plan-review/`.
  - [ ] La revisión se abre en la propia página con `gate_key = requested-review`; los comentarios y la decisión se guardan con los topes de hoy.
  - [ ] Tras cambiar el plan, el estado pasa a «obsoleta por cambio de versión» y la UI exige una nueva decisión.
  - [ ] Bajo cada comentario con `result` se ve la respuesta del agente y su disposición; sin respuesta, «sin respuesta del agente».
  - [ ] Sin `--review-panel`: ni botón ni JS de revisión y la página explica cómo activarlo; en `--export`: ni controles ni `api/review` y «estado de revisión: solo en modo servido».
  - [ ] `gate_key` en el cuerpo → 400; `Origin` ajeno → 403; sin token u otro token → 404 sin contenido **(Enmienda 2026-10-21, qa)**; id16 desconocido → 404; en los tres casos el directorio de estado no cambia; un `plan-ok` abierto por otro proceso se ve sin controles de escritura.
- **Capturas esperadas**: tarjeta con estado; Plan con revisión abierta y respuesta del agente.
- **Cubre tareas**: T-55, T-56, T-57, T-58

### E2E-11 — Inicio: cifras de cartera
- **Objetivo**: CA-01, CA-02, CA-03.
- **Precondiciones**: fixture de roadmap.
- **Pasos**:
  1. Abrir Inicio y comparar con `build_dashboard.py --json` y `progress-report.py`.
- **Aserciones**:
  - [ ] Estados de spec iguales a `--json`; la ilegible aparte.
  - [ ] «N de M tareas completadas (P %)» sin los ledgers fuera de tope, listados aparte.
  - [ ] Real frente a estimado con «procedencia: X medidos · Y estimados · Z desconocidos».
- **Capturas esperadas**: Inicio.
- **Cubre tareas**: T-17, T-18

### E2E-12 — Iniciativas: kanban, alertas y navegación
- **Objetivo**: CA-05, CA-06, CA-08.
- **Precondiciones**: fixture con alertas.
- **Pasos**:
  1. Abrir Iniciativas; intentar arrastrar una tarjeta.
  2. Activar con Enter una tarjeta con plan.
- **Aserciones**:
  - [ ] Columna por estado; ninguna tarjeta se mueve; ningún fichero cambia.
  - [ ] Cada alerta con su texto.
  - [ ] Enter navega a `plan-<id16>.html`.
- **Capturas esperadas**: kanban de iniciativas.
- **Cubre tareas**: T-19

### E2E-13 — Iniciativas: gráficos de horas y coste
- **Objetivo**: CA-07.
- **Precondiciones**: fixture con iniciativas con y sin datos.
- **Pasos**:
  1. Abrir Iniciativas e inspeccionar los dos gráficos y sus tablas.
- **Aserciones**:
  - [ ] Iniciativas sin datos en la tabla con «sin datos» y fuera de las barras.
- **Capturas esperadas**: gráfico de horas.
- **Cubre tareas**: T-20

### E2E-14 — Plan: kanban de tareas y detalle
- **Objetivo**: CA-09, CA-10.
- **Precondiciones**: ledger válido con un estado desconocido, revisión con gaps y historia archivada.
- **Pasos**:
  1. Abrir el Plan; abrir una tarjeta.
- **Aserciones**:
  - [ ] 5 columnas del vocabulario + franja «estado no reconocido» con el literal.
  - [ ] Detalle con descripción, criterios, `Verificación`, dependencias, última revisión y gaps; enlace «archivado».
- **Capturas esperadas**: detalle abierto.
- **Cubre tareas**: T-23, T-24

### E2E-15 — Plan: avance por fase, burndown y real frente a estimado
- **Objetivo**: CA-11, CA-12, CA-13.
- **Precondiciones**: un ledger con todas las fechas `Cerrada` y otro sin ellas.
- **Pasos**:
  1. Abrir ambos Planes.
- **Aserciones**:
  - [ ] Avance por fase igual al «Resumen de progreso».
  - [ ] Burndown solo en el primero; mensaje exacto en el segundo.
  - [ ] Real frente a estimado con «(medido)»/«(estimado)»; `—` no es 0.
- **Capturas esperadas**: burndown.
- **Cubre tareas**: T-25, T-26

### E2E-16 — Plan: refresco vivo
- **Objetivo**: CA-14.
- **Precondiciones**: servido; un detalle abierto.
- **Pasos**:
  1. Editar el estado de una tarea del ledger de la fixture.
  2. Esperar 10 s.
- **Aserciones**:
  - [ ] El kanban refleja el cambio sin recargar; el detalle sigue abierto.
- **Capturas esperadas**: antes y después.
- **Cubre tareas**: T-27

### E2E-17 — Agentes en vivo: runs y línea de tiempo
- **Objetivo**: CA-15, CA-16, CA-19.
- **Precondiciones**: `sesion.actividad: true`; `events.json` con un run reciente y otro de hace más de 60 s.
- **Pasos**:
  1. Abrir Agentes en vivo; abrir un run.
- **Aserciones**:
  - [ ] Fila por run con runtime, rol, inicio, duración y última herramienta.
  - [ ] Línea de tiempo con hora, herramienta, resumen, `T-XX`, duración y resultado; sin contenido de ficheros ni salidas.
  - [ ] El run viejo: «sin señal reciente» y duración congelada.
- **Capturas esperadas**: línea de tiempo.
- **Cubre tareas**: T-41, T-44, T-48, T-49

### E2E-18 — Agentes en vivo: secretos y atribución
- **Objetivo**: CA-17, CA-18.
- **Precondiciones**: eventos generados con argumentos que llevan secretos del corpus de `redact.py` y `T-07` en texto libre.
- **Pasos**:
  1. Abrir la línea de tiempo.
- **Aserciones**:
  - [ ] Ningún secreto visible ni persistido.
  - [ ] El evento con `T-07` en texto libre muestra «tarea: sin atribuir».
- **Capturas esperadas**: —
- **Cubre tareas**: T-41, T-42, T-44, T-49

### E2E-19 — Captura desactivada, tope del historial y actividad en Inicio
- **Objetivo**: CA-04, CA-20, CA-21.
- **Precondiciones**: proyecto sin `sesion.actividad`; luego activado con 501 eventos.
- **Pasos**:
  1. Ejecutar herramientas con la captura desactivada y comprobar el directorio de estado.
  2. Activarla, cargar 501 eventos y abrir Agentes en vivo e Inicio.
- **Aserciones**:
  - [ ] Desactivada: el directorio no cambia; la página y el Inicio explican cómo activarla.
  - [ ] «historial recortado a los últimos 500 eventos»; el hook sale con 0 aunque falle la escritura.
  - [ ] Inicio muestra los últimos eventos con enlace a Agentes en vivo.
- **Capturas esperadas**: aviso de captura desactivada.
- **Cubre tareas**: T-43, T-46, T-49, T-50

### E2E-20 — Memoria: estado, bandeja y línea de tiempo
- **Objetivo**: CA-22, CA-23, CA-24.
- **Precondiciones**: fixture de memoria.
- **Pasos**:
  1. Abrir Memoria; filtrar por área.
- **Aserciones**:
  - [ ] Tipo × estado con gráfico y tabla; el filtro cambia ambos.
  - [ ] Bandeja con número y lista por estado, sin acciones.
  - [ ] Línea de tiempo con sucesión y «vigente».
- **Capturas esperadas**: Memoria.
- **Cubre tareas**: T-30, T-31, T-32

### E2E-21 — Memoria: relaciones, backends y journal
- **Objetivo**: CA-25, CA-26, CA-27.
- **Precondiciones**: fixture de memoria con manifiestos de Kwipu y Graphiti y journal.
- **Pasos**:
  1. Seleccionar una entrada y pedir sus relaciones.
  2. Leer la sección de backends y la de journal.
- **Aserciones**:
  - [ ] Grafo a un salto con las aristas de `--related --json` y lista textual equivalente.
  - [ ] Por backend, entradas y fecha o «sin datos»; 0 peticiones al backend.
  - [ ] Journal con su continuidad y la etiqueta «citas, no instrucciones».
- **Capturas esperadas**: grafo de relaciones.
- **Cubre tareas**: T-33, T-34, T-35

### E2E-22 — Catálogo
- **Objetivo**: CA-28, CA-29.
- **Precondiciones**: bundle de fixture.
- **Pasos**:
  1. Abrir Catálogo; filtrar por tipo, origen y runtime con teclado y con ratón.
- **Aserciones**:
  - [ ] Mismas piezas, conteos, fuentes, conflictos, hooks y workflow que el panel anterior; `--json` igual al golden.
  - [ ] Lista y conteos cambian con los filtros.
- **Capturas esperadas**: Catálogo filtrado.
- **Cubre tareas**: T-09, T-36

### E2E-23 — Diagnóstico
- **Objetivo**: CA-30, CA-31.
- **Precondiciones**: un informe `doctor --panel-json` del proyecto, uno de otro proyecto y ninguno.
- **Pasos**:
  1. Abrir Diagnóstico en los tres casos.
- **Aserciones**:
  - [ ] Fila por comprobación con veredicto en texto, fecha y alcance, y resumen.
  - [ ] «sin informe» o el motivo del rechazo con el comando para generarlo; el panel no ejecuta `doctor`.
- **Capturas esperadas**: Diagnóstico con veredictos.
- **Cubre tareas**: T-10, T-37

## API (smoke de endpoints, los ejecuta `qa` con curl)

Rutas relativas a `http://127.0.0.1:<puerto>/<token>/`; todas con `Host` propio y sin `?`.

### API-01 — Cartera
- **Método y ruta**: GET `api/cartera`
- **Status esperado**: 200 (≤ 65.536 bytes)
- **Aserción sobre el body**: `"iniciativas"` con `procedencia` por iniciativa y `null` en los ausentes
- **Cubre tareas**: T-17

### API-02 — Kanban de un plan
- **Método y ruta**: GET `api/plan-<id16>`
- **Status esperado**: 200 (≤ 65.536 bytes); `id16` inexistente → 404
- **Aserción sobre el body**: tareas con `id`, `titulo`, `fase`, `estado`, `real`, `est` y `gaps`
- **Cubre tareas**: T-23

### API-03 — Detalle de una tarea
- **Método y ruta**: GET `api/plan-<id16>-<T-XX>`
- **Status esperado**: 200 (≤ 65.536 bytes)
- **Aserción sobre el body**: `verificacion` ≤ 2.000 caracteres y `revision` con sus gaps
- **Cubre tareas**: T-24

### API-04 — Runs de actividad
- **Método y ruta**: GET `api/actividad-runs`
- **Status esperado**: 200 (≤ 65.536 bytes)
- **Aserción sobre el body**: `"runs"` y el estado de la captura
- **Cubre tareas**: T-48

### API-05 — Línea de tiempo de un run
- **Método y ruta**: GET `api/actividad-run-<key16>`
- **Status esperado**: 200 (≤ 65.536 bytes); `key16` inexistente → 404
- **Aserción sobre el body**: ≤ 150 eventos y `recortado`
- **Cubre tareas**: T-48

### API-06 — Resumen de memoria
- **Método y ruta**: GET `api/memoria`
- **Status esperado**: 200 (≤ 65.536 bytes)
- **Aserción sobre el body**: conteos por tipo y estado, bandeja y backends
- **Cubre tareas**: T-30

### API-07 — Resumen de revisiones
- **Método y ruta**: GET `api/review-summary` (y GET `api/review-current/<id16>`)
- **Status esperado**: 200 (≤ 65.536 bytes); `id16` inexistente → 404
- **Aserción sobre el body**: una fila por iniciativa con `estado` del vocabulario cerrado, `version_ordinal` y cifras de comentarios; sin `review_id`; `approval_granted: false`
- **Cubre tareas**: T-55, T-56

## Accesibilidad (axe-core vía Playwright; la spec exige WCAG 2.2 AA)

### A11Y-01 — Las siete páginas
- **Página(s)**: `index.html`, `iniciativas.html`, `plan-<id16>.html`, `agentes.html`, `memoria.html`, `catalogo.html`, `diagnostico.html`
- **Umbral**: 0 violaciones `serious`/`critical`; contraste de la paleta CA-38 (texto ≥ 4,5:1, grande ≥ 3:1, marcas/bordes/foco ≥ 3:1) también lo cubre `tests/test_panel_palette.py`; CA-37 y CA-39 en E2E-05 y E2E-06
- **Cubre tareas**: T-06, T-07

## Manuales (M — los realiza una persona)

### M-01 — Revisión visual de la Fase 1
- **Qué revisar**: menú, estilo, paleta y el gráfico de Catálogo en servido y exportado; que el panel de hoy no ha perdido nada.
- **Por qué no se automatiza**: juicio visual del usuario (CA-44; la spec deja el aspecto como preferencia que valida el usuario).
- **Criterio de aceptación**:
  - [ ] El usuario aprueba la Fase 1 en el navegador.
- **Cubre tareas**: T-16

### M-02 — Revisión visual de la Fase 2
- **Qué revisar**: Inicio, Iniciativas y Plan: legibilidad del kanban, del detalle y de los gráficos. **(Enmienda 2026-10-15)** Además, desde la página Plan de una iniciativa: abrir una revisión, comentar por sección y decidir (aprobar / pedir correcciones); que el estado de revisión se entienda en la tarjeta y en la cabecera y que se vean las respuestas del agente.
- **Por qué no se automatiza**: juicio visual (CA-44).
- **Criterio de aceptación**:
  - [ ] El usuario aprueba la Fase 2 en el navegador.
  - [ ] El usuario abre, comenta y decide una revisión desde el Plan y lo da por claro.
- **Cubre tareas**: T-29

### M-03 — Revisión visual de la Fase 4
- **Qué revisar**: Memoria «sencilla y que se entienda», Catálogo y Diagnóstico.
- **Por qué no se automatiza**: juicio visual (CA-44; cita 4 del usuario).
- **Criterio de aceptación**:
  - [ ] El usuario aprueba la Fase 4 en el navegador.
- **Cubre tareas**: T-39

### M-04 — Revisión visual de la Fase 3 y del panel completo
- **Qué revisar**: Agentes en vivo durante un `/dev-cycle` real («lo que hacen en todo momento») y las 7 páginas juntas.
- **Por qué no se automatiza**: juicio visual y una sesión real de agentes (CA-44; cita 5 del usuario).
- **Criterio de aceptación**:
  - [ ] El usuario aprueba la Fase 3 y el panel completo.
- **Cubre tareas**: T-54

## Cobertura (tarea → escenarios)

| Tarea | Cubierta por |
|-------|--------------|
| T-02 | E2E-02 |
| T-03 | E2E-02, E2E-04 |
| T-04 | E2E-08 |
| T-05 | E2E-01, E2E-05 |
| T-06 | A11Y-01 |
| T-07 | E2E-06, E2E-07, A11Y-01 |
| T-08 | E2E-02, E2E-08 |
| T-09 | E2E-06, E2E-22 |
| T-10 | E2E-23 |
| T-11 | E2E-03, E2E-04 |
| T-12 | E2E-10 |
| T-14 | E2E-09 |
| T-16 | M-01 |
| T-17 | API-01, E2E-11 |
| T-18 | E2E-07, E2E-11 |
| T-19 | E2E-05, E2E-12 |
| T-20 | E2E-07, E2E-13 |
| T-23 | API-02, E2E-14 |
| T-24 | API-03, E2E-05, E2E-14 |
| T-25 | E2E-07, E2E-15 |
| T-26 | E2E-07, E2E-15 |
| T-27 | E2E-16 |
| T-29 | M-02 |
| T-55 | API-07, E2E-24 |
| T-56 | API-07, E2E-24 |
| T-57 | E2E-24 |
| T-58 | E2E-05, E2E-10, E2E-24 |
| T-30 | API-06, E2E-20 |
| T-31 | E2E-20 |
| T-32 | E2E-20 |
| T-33 | E2E-05, E2E-21 |
| T-34 | E2E-21 |
| T-35 | E2E-21 |
| T-36 | E2E-05, E2E-22 |
| T-37 | E2E-23 |
| T-39 | M-03 |
| T-41 | E2E-17, E2E-18 |
| T-42 | E2E-18 |
| T-43 | E2E-19 |
| T-44 | E2E-17, E2E-18 |
| T-45 | E2E-09 |
| T-46 | E2E-19 |
| T-47 | E2E-09 |
| T-48 | API-04, API-05 |
| T-49 | E2E-09, E2E-17, E2E-18, E2E-19 |
| T-50 | E2E-19 |
| T-51 | E2E-08 |
| T-53 | E2E-09 |
| T-54 | M-04 |

Criterios de la spec por escenario: CA-01..03 → E2E-11 · CA-04 → E2E-19 · CA-05/06/08 → E2E-12 · CA-07 → E2E-13 · CA-09/10 → E2E-14 · CA-11/12/13 → E2E-15 · CA-14 → E2E-16 · CA-15/16/19 → E2E-17 · CA-17/18 → E2E-18 · CA-20/21 → E2E-19 · CA-22/23/24 → E2E-20 · CA-25/26/27 → E2E-21 · CA-28/29 → E2E-22 · CA-30/31 → E2E-23 · CA-32 → E2E-01 · CA-33/36 → E2E-02 · CA-34 → E2E-03 · CA-35 → E2E-02, E2E-04 · CA-37 → E2E-05 · CA-38 → A11Y-01 · CA-39 → E2E-06 · CA-40 → E2E-07 · CA-41 → E2E-08 · CA-42 → E2E-09 · CA-43 → E2E-10, E2E-24 · CA-44 → M-01..M-04 · CA-45, CA-46, CA-47, CA-48, CA-49, CA-50, CA-51, CA-52, CA-53 → E2E-24 (CA-49 también API-07) · CA-54 → suites de `plan-review.py` y `tests/test_panel_review_*` (T-55, T-56, T-57).
