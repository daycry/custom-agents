# Documentación del agente `planner`

Agente que convierte una petición ("quiero hacer X") en un **plan de implementación detallado y presupuestado**. No implementa: planifica. Su salida son dos ficheros Markdown por plan, guardados en `docs/plans/` del proyecto.

---

## 1. Qué produce

Por cada plan crea una carpeta `docs/plans/<YYYY-MM-DD>-<slug>/` con dos ficheros de formato fijo:

| Fichero | Contenido |
|---------|-----------|
| `improvement-plan.md` | Cuadro de mando, estimación por fase, presupuesto económico, previsión de tokens, resumen ejecutivo, objetivos, datos necesarios, análisis de impacto, cambios arquitectónicos, archivos, dependencias, criterios de aceptación, riesgos y mitigaciones, métricas de éxito, changelog. |
| `TASKS.md` | Resumen de progreso + fases, con cada tarea estructurada: descripción, estado, tiempo, previsión de tokens/coste, dependencias, archivos, criterios de aceptación (checkboxes) y subtareas. |

Las plantillas base viven en `agent-kits/planner/templates/` y son el formato canónico: el agente las copia y rellena, no improvisa otro formato.

---

## 2. Estimaciones que calcula

El valor diferencial del agente es que **presupuesta** el plan en tres ejes:

- **Tiempo** — horas por tarea y por fase, con nivel de confianza (Alta/Media/Baja).
- **Coste económico (EUR)** — `(horas × tarifa) + coste de tokens de IA`. La tarifa/hora es configurable (default `50 €/h`).
- **Tokens de IA** — previsión de input/output por fase, con el modelo y los precios asumidos declarados como supuestos ajustables.

Los supuestos (tarifa, modelo, precio de tokens, tipo de cambio USD→EUR) quedan escritos en el propio plan, de modo que el presupuesto es recalculable si cambian los precios. Si el precio de tokens vigente no se conoce con certeza, el agente lo marca `⚠️ verificar` en lugar de inventar una cifra.

---

## 3. Flujo de trabajo

1. **Recepción** — entiende la petición; pregunta solo lo bloqueante y rellena el checklist "Datos necesarios para un informe completo".
2. **Recon** — explora el repo (Read/Grep/Glob) para fundamentar el impacto con rutas y módulos reales.
3. **Descomposición** — fases → tareas con ID `T-01`, `T-02`…
4. **Estimación** — tiempo, tokens y coste por tarea/fase, con método declarado.
5. **Redacción** — rellena las dos plantillas (sustituye placeholders, elimina comentarios guía).
6. **Cierre** — escribe los ficheros, actualiza `docs/plans/README.md` y resume ruta, tiempo, coste, tokens y nº de tareas.

---

## 4. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente planner`
- `planner, prepara un plan para añadir autenticación 2FA`
- `genera un plan de refactor del módulo de caché`

La primera vez confirma los parámetros de estimación (tarifa/hora, modelo, precios de tokens). Los planes quedan en `docs/plans/<fecha>-<slug>/`.

---

## 5. Reglas clave

El agente no implementa ni toca el código: solo lee el proyecto y escribe dentro de `docs/plans/`. Toda cifra lleva un método o supuesto detrás; lo no verificable se marca en lugar de inventarse. El formato es siempre el de las dos plantillas, con Markdown válido (línea en blanco antes de listas y tras encabezados, checkboxes reales). Los IDs de tarea son estables y, al actualizar un plan, se editan sus ficheros y se añade una línea al changelog en vez de duplicar carpetas.

---

## 6. Estados

Vocabulario **único** para plan, fase y tarea (un plan/tarea recién generado nace en `borrador`):

`borrador` 📝 · `en-progreso` 🚧 · `en-revision` 🔍 · `completado` ✅ · `cancelado` ❌

**Prioridades** (cuatro niveles con color, default `Media`):

`Baja` 🟢 · `Media` 🟡 · `Alta` 🟠 · `Crítica` 🔴
