---
spec: coste-generacion
descripcion: Medir el coste REAL de generar cada artefacto del ciclo (spec, evaluación, plan, tasks) y cada tarea — tokens reales leídos de la transcripción de Claude Code, fechas de inicio/fin como contexto y horas-IA derivadas por ratio calibrado — registrarlo en el frontmatter de cada .md, sumarlo como "coste de proceso" en /roadmap-metrics, calibrar el ratio tokens→horas con /retro y presentar todas las duraciones en formato humano estilo Jira (XhYm)
estado: implementada      # borrador | aprobada | implementada | obsoleta
creado: 2026-08-11
actualizado: 2026-08-11
evaluacion: evaluation.md
plan: improvement-plan.md
generacion:
  inicio: 2026-08-11T12:45:00Z
  fin: 2026-08-11T13:40:00Z
  fuente: estimado          # retroactivo: el artefacto se generó ANTES de desplegar usage-meter
  tokens_reales: null       # estimación a juicio: ~60k facturables
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.2
  duracion: 12m
  ratio_usado: 300000       # default no calibrado
---

# Coste real de generación de artefactos (usage-meter) + calibración tokens→horas

> **Evaluación:** [`evaluation.md`](evaluation.md) — 8 características · 16,0 h base (19,2 h con margen), ~995 €, ~1,69 M tokens; veredicto **go CONDICIONADO** a verificación empírica del formato JSONL (primera tarea) y degradación a `estimado` testeada.
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) — 4 fases · 10 tareas · 16,75 h base (20,1 h con margen) · ~1.044 € · verificación empírica del JSONL como primera tarea (T-01).

> **Terminología:** «artefacto del ciclo» = cada `.md` del proceso de unificación (`spec.md`, `evaluation.md`, `improvement-plan.md`, `tasks.md` — incluido el `tasks.md` ligero de la vía rápida). «transcripción» = el JSONL que Claude Code escribe por sesión en `~/.claude/projects/<proyecto>/`, donde cada respuesta del modelo lleva su bloque `usage` (tokens de entrada, salida y caché). «sidechain» = transcripción separada de un subagente (Task tool). «ratio tokens→hora» = tokens facturables que equivalen a una hora-IA; hoy implícito en las estimaciones del evaluator, tras esta iniciativa: medible y calibrable. «meter» = el script `usage-meter.py` (nuevo, en `agent-kits/shared/`).

## Contexto y objetivo

Hoy el plugin presupuesta lo que cuesta **construir** una iniciativa (evaluación → plan → worklog real por tarea), pero el coste del **propio ciclo de producto** — producir la spec, la evaluación y el plan — es invisible: no se mide ni se registra en ningún sitio. El objetivo es que **cada artefacto del ciclo registre en su frontmatter cuánto costó generarlo**, con la máxima realidad posible: **tokens reales medidos** (no estimados) leídos de la transcripción de la sesión, **fechas de inicio/fin** como contexto, y **horas-IA derivadas de los tokens** mediante un ratio que `/retro` calibra con datos reales. Con eso, `/roadmap-metrics` puede mostrar el **overhead de proceso** por iniciativa junto al coste de implementación, y las estimaciones del evaluator se van acercando a la realidad medida del equipo.

**Decisión de fondo (confirmada por el usuario, 2026-08-11):** las horas NO se calculan del reloj de pared. Si la sesión espera (límite de tokens, pausa humana), el wall-clock se infla sin ser trabajo. Papeles de cada dato: **fechas = contexto** (se registran, no se usan para calcular), **tokens = medida** (el dato real), **horas = tokens × ratio calibrado** (derivadas, imputables).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Fuente de tokens reales | **Transcripción JSONL de Claude Code** (`~/.claude/projects/<proyecto>/*.jsonl`, bloque `usage` por mensaje del asistente), misma fuente que herramientas como `ccusage` | Es el único registro real de consumo accesible en local; determinista y sin depender de servicios externos |
| Qué se suma | **input + output + creación de caché + lectura de caché, cada uno por separado** y valorados con su precio si `rates.json` lo trae; si solo hay precio input/output, la caché se informa en tokens pero se valora a 0 con aviso | No mentir: informar todo lo medido, valorar solo lo que tiene precio fiable |
| Sidechains (subagentes) | **Se suman**: el meter agrega el `usage` de todos los `.jsonl` del proyecto modificados dentro de la ventana del marcador | Analyst/evaluator/planner pueden delegar en subagentes; su consumo es parte del coste del artefacto |
| Mecanismo | **`usage-meter.py start|close`** en `agent-kits/shared/`: `start --artefacto <ruta>` guarda marcador (timestamp + fichero/offset por transcripción) en `.claude/usage-state.json`; `close --artefacto <ruta>` suma el `usage` desde el marcador y emite JSON con tokens/€/horas | Mismo patrón determinista que `worklog.py`, `qa-gate.py`, `ledger-lint.py`: cálculo en script, no en prosa del agente |
| Dónde vive el dato | **Frontmatter YAML** de cada artefacto: bloque `generacion:` con `inicio`, `fin`, `tokens_reales` (desglosado), `eur`, `horas_ia`, `ratio_usado`, `fuente: medido\|estimado` | Elegido por el usuario; parseable por `/roadmap-metrics` sin heurísticas |
| Wall-clock | `inicio`/`fin` se **registran** como metadato; la duración de reloj puede mostrarse informativa, pero **nunca** es fuente de horas | Pausas y límites de tokens rompen el reloj (señalado por el usuario); los tokens no se consumen esperando |
| Horas-IA | **`horas_ia = tokens_facturables ÷ ratio tokens→hora`**. Ratio: de `docs/roadmap/CALIBRATION.md` si existe (mediana de iniciativas cerradas); si no, default documentado en `estimation-defaults.md` | El tiempo imputable sale de esfuerzo medido; el ratio mejora con cada `/retro` |
| Conversión a € | Con `precioTokens` de `.claude/rates.json` (regla vigente de fiabilidad: >0 y `verificadoEl` < 90 días, si no `⚠️ verificar` y € parametrizado) | Coherente con `rates-verify` (token-diet); no inventar precios |
| Degradación | Si la transcripción no existe, no es legible o el formato cambió: `fuente: estimado`, tokens del propio juicio del agente, y **aviso** — el flujo NUNCA se bloquea por el meter | El formato JSONL es interno de Claude Code, no API pública; robustez ante cambios |
| Quién arranca/cierra el meter | Los **agentes del ciclo** (analyst, evaluator, planner) al abrir/cerrar su artefacto, y `/dev-cycle` para el `tasks.md` ligero de la vía rápida | El agente ya sabe cuándo empieza y termina su artefacto; sin hooks nuevos |
| Medición por tarea en implementación (extrapolación) | **Sí, segunda fase de esta iniciativa**: marcador por `T-XX` al arrancar/cerrar cada tarea en Modo B; los tokens reales de la tarea derivan `horas_ia` reales para el worklog (hoy: estimadas a juicio). La supervisión humana sigue con `ratioSupervision` de `rates.json` | Lo pidió el usuario ("extrapolar al cálculo del tiempo de las tareas… lo más real posible"); los tokens miden a la IA, no al humano |
| Calibración | **`/retro` calcula el ratio real tokens→hora** de la iniciativa cerrada (tokens medidos ÷ horas reales validadas) y lo escribe en `CALIBRATION.md`; el evaluator y el meter leen de ahí | Cierra el bucle: medir → calibrar → estimar mejor |
| Idempotencia | Re-cerrar un artefacto ya medido **actualiza** su bloque `generacion:` (no duplica); `usage-state.json` guarda marcadores por ruta de artefacto | Regenerar una spec no debe acumular costes fantasma |
| No hardcodear | La carpeta de transcripciones se localiza en runtime (`~/.claude/projects/` + codificación del cwd); el meter acepta `--transcript-dir` para tests y entornos raros | Regla 5 de CONVENTIONS; testeable sin tocar `~/.claude` real |
| Formato humano de duraciones | Las horas decimales quedan como dato **interno** de cálculo; todo lo **presentado a personas** (frontmatter, tasks.md, informes, comentarios de Jira) se muestra en **estilo Jira compacto** `XhYm`: `0,53 h` → **32m**, `1,25 h` → **1h 15m**, `18,0 h` → **18h**, `1,53 h` → **1h 32m** (se omite la parte a cero; redondeo al minuto). Helper único en `usage-meter.py fmt` (o función compartida) para no reimplementarlo en cada sitio | Pedido por el usuario (2026-08-11): "0,53h" no queda claro; formato confirmado por él ("1h 32m, 34m, 1h") — coincide con el estilo nativo de Jira |

## Arquitectura y componentes

Se crea: **`agent-kits/shared/usage-meter.py`** (start/close, suma de `usage`, sidechains, conversión €/horas, degradación) + **`agent-kits/shared/test_usage_meter.py`**. Se toca: plantillas de artefactos (`agent-kits/evaluator/templates/spec.md` y `evaluation.md`, plantillas del planner) para el bloque `generacion:` del frontmatter; `agents/analyst.md`, `agents/evaluator.md`, `agents/planner.md` (arrancar/cerrar el meter); `commands/dev-cycle.md` (vía rápida: medir el `tasks.md` ligero; Modo B fase 2: marcador por `T-XX` y `horas_ia` reales al worklog); `skills/roadmap-dashboard` (leer `generacion:` y sumar overhead de proceso en `/roadmap-metrics`); `commands/retro.md` (ratio real tokens→hora → `CALIBRATION.md`); `agent-kits/shared/estimation-defaults.md` (default del ratio y regla de fiabilidad). Se reutiliza: `rates.json` (+ `rates-verify`), `CALIBRATION.md` (formato de `/retro`), patrón de scripts deterministas con tests.

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | `usage-meter.py` (medición) | `start --artefacto <ruta>`: marcador con timestamp + posición (fichero, offset/último uuid) de cada `.jsonl` del proyecto en `.claude/usage-state.json`. `close --artefacto <ruta>`: suma `usage` (input, output, cache_creation, cache_read) de todos los mensajes nuevos desde el marcador, incluidas sidechains; emite JSON `{inicio, fin, tokens_reales:{...}, eur, horas_ia, ratio_usado, fuente}`. `--transcript-dir` para tests. Degradación a `fuente: estimado` sin romper. Tests pytest (fixtures JSONL sintéticas: sesión simple, con sidechain, formato corrupto, transcripción ausente, precios a 0) |
| C-02 | Frontmatter `generacion:` en artefactos | Bloque en spec/evaluation/plan/tasks (y `tasks.md` ligero de vía rápida): `inicio`, `fin`, `tokens_reales` desglosado, `eur` (o `⚠️ verificar`), `horas_ia`, `ratio_usado`, `fuente`. Plantillas actualizadas; artefactos antiguos sin bloque siguen siendo válidos (opcional, no obligatorio para lint) |
| C-03 | Integración en el ciclo | analyst/evaluator/planner ejecutan `start` al abrir su artefacto y `close` al cerrarlo, escribiendo el bloque en el frontmatter; `/dev-cycle` lo hace para el `tasks.md` de la vía rápida. Si un artefacto se regenera, `close` actualiza el bloque (no duplica ni acumula) |
| C-04 | Overhead de proceso en `/roadmap-metrics` | La skill `roadmap-dashboard` lee `generacion:` de los artefactos de cada iniciativa y añade al informe una columna/sección **"coste de proceso"** (tokens/€/horas de producir spec+eval+plan) separada del coste de implementación, con total de cartera. Artefactos sin bloque → "sin datos", no 0 inventado |
| C-05 | Calibración en `/retro` | `/retro` añade al análisis: tokens medidos de la iniciativa (proceso + implementación si C-06) ÷ horas reales validadas = **ratio real tokens→hora**, escrito como columna en `CALIBRATION.md`. El evaluator y `usage-meter.py` usan la mediana de ese histórico; sin histórico, default de `estimation-defaults.md` |
| C-06 | Medición por tarea (extrapolación al worklog) | En Modo B, `/dev-cycle` arranca marcador por `T-XX` al empezar la tarea y lo cierra al completarla: los tokens reales de la tarea derivan `horas_ia` **medidas** que sustituyen a la estimación a juicio en `tasks.md` (columna real) y en `worklog.py plan` (la parte IA; la supervisión sigue por `ratioSupervision`). `fuente: medido` viaja al ledger para que `/retro` distinga medido de estimado |
| C-07 | Default del ratio + documentación | `estimation-defaults.md` gana el parámetro **ratio tokens→hora** (default documentado y marcado "calibrar con /retro cuanto antes") y la regla de precedencia (CALIBRATION > default). Docs: CONVENTIONS (regla del meter), FLOWS (diagrama 6 con el bucle medir→calibrar), README del kit shared |
| C-08 | Formato humano de duraciones | Helper único de formato (`usage-meter.py fmt <horas>` o función compartida): decimales → estilo Jira compacto `XhYm` (`0,53` → `32m`; `1,25` → `1h 15m`; `18,0` → `18h`; `1,53` → `1h 32m`; se omite la parte a cero; redondeo al minuto). Se aplica en TODO lo presentado: bloque `generacion:` (campo `duracion` legible junto al decimal), informes de `/roadmap-metrics` y `/roadmap-status`, resúmenes de cierre y comentarios de Jira (plantilla de revisión incluida). **Excepción declarada:** las columnas real/est del ledger `tasks.md` (líneas `est. X,Xh` y resumen `0 / X,Xh`) permanecen en decimal porque son **parseadas por máquina** (`parse_progress_totals` del dashboard y el flujo de worklog); cambiarlas rompería la lectura — el dato legible del ledger es el campo `duracion` de su frontmatter. El dato interno de cálculo sigue siendo decimal (worklog, jornada, banco — sin cambios de aritmética). Tests del helper (bordes: 0, <1 min, exacto en horas) |

## Alcance

- **Dentro (esta iteración):** C-01 … C-08 — medición real por artefacto y por tarea, frontmatter, overhead en métricas, calibración en retro, formato humano de duraciones.
- **Fuera (siguientes specs):**
  - Telemetría OTEL de Claude Code como fuente alternativa (más rica pero exige infra de colector; el JSONL local no pide nada).
  - Medir el **tiempo humano** de supervisión con señales reales (p. ej. actividad del chat) — se queda como ratio configurable; medirlo de verdad es otro problema (y otro debate de privacidad).
  - Desglose de coste por **modelo** cuando una sesión mezcla modelos (haiku para subagentes, opus para el principal): primera versión valora todo al precio del modelo principal de `rates.json` y lo anota como supuesto.
  - Panel histórico de ratios en el dashboard (gráfica de calibración por iniciativa).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Transcripción ausente/ilegible (permisos, entorno sin `~/.claude`, formato cambiado) | `fuente: estimado`, tokens a juicio del agente, aviso en el artefacto; NUNCA bloquea el cierre del artefacto |
| `precioTokens` a 0 o `verificadoEl` viejo | Tokens medidos se registran igual; `eur: ⚠️ verificar` parametrizado; sugerir `rates-verify` (regla existente) |
| Sin `CALIBRATION.md` ni histórico | `ratio_usado` = default de `estimation-defaults.md`, marcado en el frontmatter para que se vea que no está calibrado |
| `start` sin `close` (sesión cortada) | El marcador queda en `usage-state.json`; el siguiente `close` del mismo artefacto lo usa; `usage-meter.py status` lista marcadores huérfanos |
| Dos artefactos midiéndose a la vez (analyst y evaluator solapados) | Soportado: marcadores independientes por ruta de artefacto; ambos suman los mismos mensajes solo si de verdad ocurren dentro de su ventana (se documenta que el solape reparte mal el coste y el orquestador debe cerrar antes de abrir) |
| Re-cierre de un artefacto ya medido | Actualiza el bloque `generacion:` en sitio; no duplica claves ni suma sobre lo anterior |
| Reloj del sistema poco fiable | Las fechas son informativas; ningún cálculo depende de ellas (decisión de fondo) |

## Pruebas

- `test_usage_meter.py` (pytest): suma correcta por ventana (fixtures JSONL sintéticas), inclusión de sidechains, exclusión de mensajes anteriores al marcador, degradación (fichero ausente, JSON corrupto, `usage` incompleto), conversión € con precios fiables/no fiables, derivación de horas con ratio de CALIBRATION vs default, idempotencia del re-cierre, marcadores concurrentes por artefacto, y el helper de formato humano (`0,53→32m`, `1,25→1h 15m`, `1,53→1h 32m`, bordes 0 / <1 min / horas exactas).
- Frontmatter: un artefacto generado en dry-run lleva el bloque `generacion:` bien formado (YAML válido) y `/roadmap-metrics` lo agrega; artefacto legacy sin bloque no rompe nada.
- Extremo a extremo (manual): una iniciativa de juguete con el ciclo completo produce spec/eval/plan con tokens medidos > 0 y el informe de métricas muestra el overhead de proceso.

## Referencias

- Transcripciones JSONL de Claude Code (`~/.claude/projects/`) y su bloque `usage` — misma fuente que `ccusage`.
- `agent-kits/shared/estimation-defaults.md`, `.claude/rates.json` + skill `rates-verify` (token-diet).
- `commands/retro.md` y formato de `docs/roadmap/CALIBRATION.md` (aún sin estrenar — esta iniciativa le da su primera columna medida).
- preferencias del usuario (memoria del proyecto) — no hardcodear, deterministas con tests, degradación sin bloquear, opt-ins persistentes.

## Decisiones confirmadas (conversación con el usuario · 2026-08-11)

1. Registrar el coste de generación en **cada .md del ciclo**. **Confirmado** (origen de la iniciativa).
2. **Frontmatter YAML** como ubicación del dato. **Confirmado.**
3. **Tokens reales medidos**, no solo estimación. **Confirmado** ("también los tokens reales… lo más real posible").
4. **Wall-clock solo como contexto** (fecha inicio/fin registradas); las horas se derivan de tokens × ratio calibrado, nunca del reloj — el propio usuario señaló que una espera por límite de tokens rompería el reloj. **Confirmado.**
5. **Extrapolar a las tareas**: los tokens reales por `T-XX` alimentan las horas-IA del worklog. **Confirmado** en la misma conversación.
6. **Formato humano de duraciones** en todo lo presentado, estilo Jira compacto `XhYm` (`0,53 h` → `32m`, `1,53 h` → `1h 32m`, `18 h` → `18h`); las decimales quedan solo como dato interno de cálculo. **Confirmado** dos veces ("esto no queda claro: 0,53h" y el formato exacto "1h 32m, 34m, 1h").

## Supuestos

- El formato JSONL de transcripciones (mensajes con `message.usage`) se mantiene estable; si cambia, el meter degrada a `estimado` (nunca rompe). No es API pública de Claude Code.
- Las sidechains de subagentes se escriben en la misma carpeta de proyecto y son detectables por mtime dentro de la ventana del marcador.
- Valorar toda la sesión al precio del modelo principal de `rates.json` es aceptable como primera aproximación (anotado en Fuera de alcance el desglose por modelo).
- El ratio tokens→hora default inicial es una convención a calibrar; se marca como no calibrado hasta que `/retro` escriba datos reales.
- En Cowork (sandbox cloud) la ruta de transcripciones existe igualmente (`/root/.claude/projects/`); si el entorno no la expone, aplica la degradación.
