# Documentación del agente `planner`

Agente que convierte una petición ("quiero hacer X") — o una **spec/evaluación aprobada** — en un **plan de implementación detallado y presupuestado**. No implementa: planifica. Su salida son dos ficheros Markdown por plan, guardados en `docs/roadmap/` del proyecto.

> **Coste medido:** este agente arranca/cierra `usage-meter.py` sobre su artefacto: el frontmatter `generacion:` registra los tokens REALES consumidos al producirlo (fechas = contexto · tokens = medida · horas = tokens × ratio calibrado). `/roadmap-metrics` lo agrega como coste de proceso.

Es el último eslabón de la cadena **spec → evaluación → plan**: cuando el plan nace de una spec/evaluación, las referencia (filas **Spec** y **Evaluación** del `improvement-plan.md`) y **actualiza hacia atrás** el `plan:` de la spec y la fila **Plan** de la evaluación al crearse. Comparte `<slug>` con ellas.

---

## 1. Qué produce

Por cada plan crea una carpeta `docs/roadmap/<YYYY-MM-DD>-<slug>/` con dos ficheros de formato fijo:

| Fichero | Contenido |
|---------|-----------|
| `improvement-plan.md` | Cuadro de mando, estimación por fase, presupuesto económico, previsión de tokens, resumen ejecutivo, objetivos, datos necesarios, análisis de impacto, cambios arquitectónicos, archivos, dependencias, criterios de aceptación, riesgos y mitigaciones, métricas de éxito, changelog. |
| `tasks.md` | Resumen de progreso + fases, con cada tarea estructurada: descripción, estado, tiempo, previsión de tokens/coste, dependencias, tipo (opcional y **libre**, sin lista cerrada — p. ej. `frontend/backend/db/devops/test/docs` — activa la persona del despacho por subagentes), archivos, criterios de aceptación (checkboxes) y subtareas. |

Las plantillas base viven en `agent-kits/planner/templates/` y son el formato canónico: el agente las copia y rellena, no improvisa otro formato.

**Iniciativa sin UI.** El `test-plan.md` solo se genera si hay interfaz. Cuando no la hay, el planner **no omite el fichero en silencio**: escribe `test-plan: n/a (sin UI)` en el frontmatter de `improvement-plan.md` (literal exacto, junto a `design:`). Ese marcador es lo que leen `/dev-cycle` (Fase 3, para invocar `qa` en modo sin UI) y el propio `qa` (`coverage-check.py` lo reconoce) para terminar limpios en vez de pedir un test-plan que nunca va a existir. Decisión: `ADR-017`; hueco E1 de [`CONTRACTS.md`](CONTRACTS.md).

---

## 2. Estimaciones que calcula

El valor diferencial del agente es que **presupuesta** el plan en varios ejes:

- **Tiempo** — horas humanas por tarea y por fase, con nivel de confianza (Alta/Media/Baja).
- **Coste económico (EUR)** — `(horas × tarifa) + coste de tokens de IA`. La tarifa/hora es configurable (default `50 €/h`).
- **Tokens de IA** — previsión de input/output por fase, con el modelo y los precios asumidos declarados como supuestos ajustables.
- **Productividad IA (humano vs. IA)** — horas IA (ejecución) + supervisión humana → horas totales, horas ahorradas, **ahorro %**, **multiplicador ×** y FTE equivalentes. Muestra cuánto acelera el trabajo hacerlo con IA frente a a mano.

Los supuestos (tarifa, modelo, precio de tokens, tipo de cambio USD→EUR) quedan escritos en el propio plan, de modo que el presupuesto es recalculable si cambian los precios. Si el precio de tokens vigente no se conoce con certeza, el agente lo marca `⚠️ verificar` en lugar de inventar una cifra.

---

## 3. Flujo de trabajo

1. **Recepción** — entiende la petición; pregunta solo lo bloqueante y rellena el checklist "Datos necesarios para un informe completo".
2. **Recon** — explora el repo (Read/Grep/Glob) para fundamentar el impacto con rutas y módulos reales.
3. **Descomposición** — fases → tareas con ID `T-01`, `T-02`…
3-bis. **Alcance completo en `Archivos`** — el campo no lista solo lo que se edita a mano: si la tarea toca `commands/`, `agents/` o `hooks/` lleva el patrón `interop/**` (lo **generado**, que `implementer` regenera con `scripts/export-interop.py` y la Lente A comprueba con `--check`), y lleva las piezas que **describen** a lo tocado, copiadas de la columna «Piezas que describen» de [`CONTRACTS.md`](CONTRACTS.md) en vez de improvisarse por tarea. Son las aristas E2 y E3 de esa matriz, y quien las salta se las encuentra como gap de alcance en `scope-check.py`.
4. **Estimación** — tiempo, tokens y coste por tarea/fase, con método declarado.
5. **Redacción** — rellena las dos plantillas (sustituye placeholders, elimina comentarios guía).
6. **Cierre** — escribe los ficheros, actualiza `docs/roadmap/README.md` y resume ruta, tiempo, coste, tokens y nº de tareas.

---

## 4. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente planner`
- `planner, prepara un plan para añadir autenticación 2FA`
- `genera un plan de refactor del módulo de caché`

La primera vez confirma los parámetros de estimación (tarifa/hora, modelo, precios de tokens). Los planes quedan en `docs/roadmap/<fecha>-<slug>/`.

---

## 4-bis. Memoria técnica del proyecto

Antes de descomponer, lee el índice de `docs/knowledge/` (si existe) y abre las entradas de `adr/` + `lessons/` que apliquen — paso compartido `agent-kits/shared/knowledge-check.md`. Cuando una decisión de diseño del plan **cruza el umbral** de `agent-kits/shared/knowledge-write.md` (cierra una alternativa y afecta a 2+ piezas, o se tomó en una puerta), escribe un ADR `estado: propuesta` en `docs/knowledge/adr/` con la plantilla `agent-kits/shared/templates/adr.md` y actualiza el índice en el mismo cambio; si no cruza el umbral, no escribe nada.

---

## 5. Reglas clave

El agente no implementa ni toca el código: solo lee el proyecto y escribe dentro de `docs/roadmap/`. Toda cifra lleva un método o supuesto detrás; lo no verificable se marca en lugar de inventarse. El formato es siempre el de las dos plantillas, con Markdown válido (línea en blanco antes de listas y tras encabezados, checkboxes reales). Los IDs de tarea son estables y, al actualizar un plan, se editan sus ficheros y se añade una línea al changelog en vez de duplicar carpetas. Una regla nueva desde la matriz de contratos: **quien describe una pieza se actualiza en la MISMA tarea que la toca** (arista E3), así que esas rutas van en `Archivos` desde el plan — no son trabajo de después, y por eso el DoD del planner las comprueba.

---

## 6. Estados

Vocabulario **único** para plan, fase y tarea (un plan/tarea recién generado nace en `borrador`):

`borrador` 📝 · `en-progreso` 🚧 · `en-revision` 🔍 · `completado` ✅ · `cancelado` ❌

**Prioridades** (cuatro niveles con color, default `Media`):

`Baja` 🟢 · `Media` 🟡 · `Alta` 🟠 · `Crítica` 🔴
