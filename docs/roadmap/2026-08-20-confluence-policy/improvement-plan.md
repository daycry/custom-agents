---
generacion:
  inicio: 2026-08-20T08:57:27Z
  fin: 2026-08-20T08:59:24Z
  fuente: estimado        # degradación declarada: usage-meter.py sin carpeta de transcripciones en este sandbox
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# 2026-08-20-confluence-policy

> Ejecutar la política de publicación en Confluence: alcance `include`/`exclude`, disparadores de fin de ciclo y ledger, evidencias de qa, verificador + staging generado, y su documentación bilingüe.

| | |
|---|---|
| **Fecha** | 2026-08-20 |
| **Estado** | completado |
| **Tipo** | Infra |
| **Prioridad** | Media |
| **Solicitante** | jmano@mediapro.tv (vía `/pm-cycle`) |
| **Responsable** | implementer (vía `/dev-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

> Heredado íntegro de `evaluation.md` (GO sin condiciones, D1-D5 cerradas). El planner reparte estas cifras en fases/tareas; no re-estima desde cero.

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **21,6 h** (18 h base +20 %) | 0 h | Baja |
| Tiempo IA (ejecución) | **0,89 h** (+ 0,22 h supervisión) | 0 h | Media |
| Coste total | **≈ 1.085 €** | 0 € | Baja |
| Tokens IA | **426k** con margen — 355k base (in 307k / out 48k) | 0 | Media |
| Multiplicador productividad | **×19** | — | — |
| Tareas | **13** | 0 hechas | — |

> **Por qué la confianza del coste es Baja:** el 99,6 % del importe son horas humanas y, según `CALIBRATION.md`, las horas humanas de este proyecto nunca se han validado (0 h reales en las 5 iniciativas medidas). Sirve para comparar y justificar valor, no como compromiso de factura — heredado literal de `evaluation.md`.

---

## Estimación por fase

Cifras **base** (sin margen); los tokens/coste por fase son la suma de las tareas y coinciden con el desglose por característica de `evaluation.md` (C-01+C-03 → C-02 → C-05 → C-04, orden recomendado en la puerta go).

| Fase | Característica(s) | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------------|-------------|-------------------|---------|
| Fase 1 — Alcance del mirror + evidencias de qa | C-01 + C-03 | 4,5 | 48k / 7k | ≈ 225 € |
| Fase 2 — Disparadores que faltan | C-02 | 3,0 | 31k / 4k | ≈ 150 € |
| Fase 3 — Verificador + staging generado | C-05 | 7,5 | 85k / 15k | ≈ 375 € |
| Fase 4 — Documentar la política | C-04 | 3,0 | 39k / 6k | ≈ 150 € |
| **Total (base)** | | **18,0 h** | **203k / 32k (235k)** | **≈ 900 €** |
| **Total (con margen +20 %)** | | **21,6 h** | **≈ 244k / 38k (282k)** | **≈ 1.080 €** |

> El total **con margen** de esta tabla (≈1.080 €) es solo el trabajo por característica escalado +20 %. El total del cuadro de mando (**≈1.085 €**) añade además, como líneas transversales del presupuesto (no atribuibles a una tarea concreta): tokens de la **revisión adversarial** (70k) y del **coste de proceso** spec+evaluación+plan (50k), más la **lectura de caché** (~3,5M tok). Ver "Presupuesto económico" — heredado literal de `evaluation.md`, sin re-estimar.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**. Heredado de `evaluation.md` §Presupuesto total y §Supuestos económicos — sin diferencias.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json:tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json:modeloIA` |
| Precio input | 5,00 USD / 1M → **4,60 € / 1M** | Verificado 2026-08-18 con `rates-verify` (< 90 días: fiable) |
| Precio output | 25,00 USD / 1M → **23,00 € / 1M** | Ídem |
| Precio escritura de caché | 6,25 USD / 1M | Ídem; entra en tokens facturables |
| Precio lectura de caché | 0,50 USD / 1M | No cuenta para horas, **sí** para € (aprendizaje nº 4 de `CALIBRATION.md`) |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ **verificar** — supuesto fijo en `rates.json`, no dato verificado |
| Ratio tokens→hora-IA | **479.326 tok/h** | Mediana medida de `CALIBRATION.md` (5 muestras) |
| Ratio de supervisión | 25 % de las horas IA | `rates.json:ratioSupervision` |
| Margen de contingencia | 20 % | `rates.json:margenContingencia`; sobre horas base (humanas e IA) y sobre tokens |
| Lectura de caché prevista | ~3,5M tokens | ⚠️ supuesto por analogía con el histórico medido |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18 h × 50 €/h | 900,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 180,00 € |
| Tokens IA — características | 235k (203k in / 32k out) | 1,75 € |
| Tokens IA — revisión adversarial (2 lentes) | 70k (60k in / 10k out) | 0,53 € |
| Tokens IA — coste de proceso (spec + evaluación + plan) | 50k (44k in / 6k out) | 0,36 € |
| Tokens IA — lectura de caché | ~3,5M × 0,50 USD/M ⚠️ supuesto | 1,61 € |
| Margen sobre tokens | +20 % | 0,85 € |
| **Total estimado (con margen)** | 21,6 h × 50 €/h + 5,10 € | **≈ 1.085 €** |

<!-- Nota de método: las horas de la tabla "Estimación por fase" y las de las tareas de tasks.md son SOLO el trabajo por característica (900€ base); las líneas de revisión adversarial y coste de proceso son transversales al plan completo y no se reparten por tarea, igual que en evaluation.md. -->

---

## Previsión de tokens (por fase)

Solo trabajo por característica (sin revisión adversarial ni coste de proceso, que son transversales — ver arriba). Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Alcance + evidencias qa | 48k | 7k | 55k | 0,38 € |
| Fase 2 — Disparadores | 31k | 4k | 35k | 0,23 € |
| Fase 3 — Verificador + staging | 85k | 15k | 100k | 0,74 € |
| Fase 4 — Documentación | 39k | 6k | 45k | 0,32 € |
| **Total** | **203k** | **32k** | **235k** | **1,75 €** |

**Método de estimación:** nº de ficheros a leer/tocar por tarea (rutas de `evaluation.md` §Arquitectura, verificadas contra el repo) × tamaño medio, calibrado a la baja con `CALIBRATION.md` (aprendizaje nº 5: prosa = minutos, prosa+tests = ×2 — aplicado a la Fase 3, la única con script y tests).

---

## Productividad IA (humano vs. IA)

Heredado literal de `evaluation.md` §Productividad IA.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 21,6 h *(18 h base)* |
| Horas IA (ejecución) | 0,89 h *(0,74 h base)* |
| Supervisión humana | 0,22 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **1,11 h** |
| Horas ahorradas | 20,49 h |
| **Ahorro** | **94,9 %** |
| **Multiplicador de productividad** | **×19** |
| FTE equivalentes *(opcional)* | 0,13 |

> Horas con el margen de contingencia (+20 %) ya aplicado sobre las horas base. Las horas IA salen de `426.000 tokens facturables ÷ 479.326 tok/h`, no de un juicio; las horas humanas sí son un juicio no validado en este proyecto (0 h reales en el histórico).

---

## Resumen ejecutivo

El circuito `docs/ ↔ Confluence` funciona en mecánica pero no tiene política: hoy un `include: ["**/*.md"]` sin `exclude` fino subiría el árbol EN duplicado, la doc interna de agentes y las 11 iniciativas completas del roadmap, mientras cuatro disparadores de fin de ciclo nunca publican y el informe de `qa` llegaría con capturas rotas. Este plan ejecuta las 5 decisiones ya cerradas en `evaluation.md` (D1-D5, GO sin condiciones): fija el `exclude` por defecto y su simetría en `confluence-pull` (Fase 1, con la exclusión de evidencias de qa en la misma pasada), cablea los disparadores de fin de ciclo y el ledger por fase (Fase 2), construye el verificador+staging `confluence-scope.py` con tests (Fase 3, la pieza con código) y documenta la política en ES+EN con la matriz de disparadores (Fase 4). Trabajo preventivo y sin riesgo de regresión: el circuito nunca se ha activado en este repo.

### Objetivos

- Que el `exclude` por defecto de `confluence.example.json` refleje exactamente D1 (selección curada) y D4 (`**/testing/**` fuera), verificable por inspección y por `confluence-scope.py --check`.
- Que los 10 disparadores conocidos apliquen (o declaren explícitamente que no aplican) el opt-in de Confluence, sin huecos de "fin de ciclo".
- Que `confluence-scope.py --status`/`--stage` den, con exit code y tests, una respuesta determinista a "¿qué se publica y en qué estado está?", materializada en `docs/confluence/`.
- Que la política quede documentada en ES+EN (`SKILL.md`, `docs/FLOWS.md`, `docs/README.md`) sin romper la regla bilingüe del repo.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante — D1-D5 cerradas en `spec.md` (`aprobada`)
- [x] **Alcance** cerrado (qué entra y qué NO) — spec §Alcance; evaluación C-01..C-05
- [x] **Criterios de éxito / métricas** acordados — CA-01 a CA-12 (spec §Criterios de aceptación)
- [ ] **Accesos y credenciales** necesarios (entornos, APIs, repos) — no aplica a esta iteración: no hay prueba end-to-end contra un espacio real de Confluence (fuera de alcance automatizado, spec §Pruebas)
- [x] **Entornos** disponibles y datos de prueba — fixtures locales para `confluence-scope.py` (sin red, sin conector; spec §Pruebas)
- [x] **Stakeholders** identificados — jmano@mediapro.tv, puerta cruzada el 2026-08-20
- [ ] **Dependencias externas** — pendiente confirmar el espacio de Confluence real y las capacidades exactas del conector Rovo MCP (evaluación §Sigue abierto); no bloquea esta implementación (es prosa + script sin red)
- [x] **Restricciones** conocidas — determinismo (scripts con tests y exit codes), bilingüe EN/ES, degradación sin bloqueo, invariante `docs/security-scan/**`, rutas relativas en scripts
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, verificado 2026-08-18

---

## Análisis de impacto

- **`skills/confluence-publish/`** — `assets/confluence.example.json` (exclude por defecto + source/staging), `SKILL.md` (config, sección normativa, invocación del script), `scripts/confluence-scope.py` (nuevo).
- **`skills/confluence-pull/SKILL.md`** — simetría del filtro + mapeo inverso staged→canónico.
- **`commands/retro.md`, `commands/spec-drift.md`, `commands/roadmap-brief.md`** — añaden el paso `confluence-optin.md` en su cierre.
- **`agents/implementer.md`** — aplica el opt-in al cerrar cada fase (D3) + nota de la interacción D1↔D3.
- **`agents/qa.md`** — informe de `testing/` declarado solo-local (D4); ajusta su dependencia declarada de `confluence-publish`.
- **`hooks/mark-docs-pending.sh`** — ignora `docs/confluence/**`.
- **`docs/FLOWS.md` / `docs/en/FLOWS.md`** — matriz disparador→artefacto→¿se publica?.
- **`docs/README.md` / `docs/en/README.md`** — párrafo del circuito bidireccional actualizado.
- **`tests/`** — nueva suite `test_confluence_scope.py`.
- **`docs/confluence/`** — carpeta nueva, **generada** por `--stage` (no se edita a mano).

---

## Cambios arquitectónicos

- **Política como `exclude` (opt-out) sobre `include: ["**/*.md"]`**, no allow-list: un doc nuevo se publica salvo exclusión conocida (D1/D2, spec §Decisiones de diseño).
- **`docs/confluence/` como carpeta derivada**, nunca fuente: mismo patrón que `dashboard.md` (regenerado antes de publicar), evita una segunda fuente de verdad (D5).
- **`confluence-scope.py` como fuente de verdad del alcance**: la skill lo invoca en vez de reinterpretar los globs por su cuenta — evita que la semántica del verificador diverja de la que realmente publica.
- **Manifiesto y hook operan sobre el staging cuando está activo**: los hashes se calculan sobre lo que de verdad se sube.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `skills/confluence-publish/assets/confluence.example.json` | Modificar | `exclude` por defecto aprobado (D1) + comentario por exclusión; luego `source`/`staging` (D5) |
| `skills/confluence-publish/SKILL.md` | Modificar | §Config con los nuevos defaults; sección normativa "qué sube y qué no"; invocación de `confluence-scope.py` |
| `skills/confluence-pull/SKILL.md` | Modificar | Simetría del filtro `include`/`exclude`; consumo del mapeo inverso staged→canónico |
| `skills/confluence-publish/scripts/confluence-scope.py` | Crear | `--status` / `--stage` / `--check`, con exit codes |
| `docs/confluence/` (+ `_STAGING-LEEME.md` generado; *enmienda al cierre: antes «README.md»*) | Crear (generada por `--stage`, no a mano) | Materialización visible de la política |
| `tests/test_confluence_scope.py` | Crear | Cobertura CA-07, CA-08, CA-10, CA-11, CA-12 |
| `commands/retro.md` | Modificar | Paso `confluence-optin.md` en el cierre |
| `commands/spec-drift.md` | Modificar | Ídem |
| `commands/roadmap-brief.md` | Modificar | Ídem |
| `agents/implementer.md` | Modificar | Opt-in al cerrar cada fase (D3) + nota D1↔D3 |
| `agents/qa.md` | Modificar | Informe `testing/` solo-local (D4); ajuste de dependencia declarada |
| `hooks/mark-docs-pending.sh` | Modificar | Ignorar `docs/confluence/**` |
| `docs/FLOWS.md` | Modificar | Matriz disparador→artefacto→¿se publica? |
| `docs/en/FLOWS.md` | Modificar | Espejo EN |
| `docs/README.md` | Modificar | Párrafo del circuito bidireccional actualizado |
| `docs/en/README.md` | Modificar | Espejo EN |
| `CHANGELOG.md` / `CHANGELOG.es.md` | Modificar | Entrada `[Unreleased]` / `[Sin publicar]` |

---

## Dependencias y prerequisitos

- Orden obligatorio heredado de la evaluación: **Fase 1 (C-01+C-03) → Fase 2 (C-02) → Fase 3 (C-05) → Fase 4 (C-04)**. La Fase 3 no puede materializar una política que no existe (depende de la Fase 1); la Fase 4 documenta lo decidido en las tres anteriores, incluido el contrato de `docs/confluence/` — documentarla antes obligaría a rehacer el espejo EN dos veces.
- No hay dependencias externas bloqueantes: sin conector Atlassian conectado ni espacio de Confluence real, todo el trabajo de esta iteración es local (prosa + script con fixtures, sin red).
- `python3 scripts/lint_plugin.py` y las suites de `tests/` en verde son prerequisito de cierre de **cada** fase, no solo de la última.

---

## Criterios de aceptación (global)

- [ ] CA-01 — `confluence.example.json` incluye los `exclude` por defecto aprobados con un comentario que explica cada uno.
- [ ] CA-02 — `SKILL.md` de `confluence-publish` tiene la sección normativa "qué sube y qué no" (tabla de exclusiones + motivo, incluida `**/testing/**` y plan/ledger).
- [ ] CA-03 — `commands/retro.md`, `commands/spec-drift.md` y `commands/roadmap-brief.md` aplican `confluence-optin.md` en su cierre, con el mismo texto de degradación que el resto de la cadena.
- [ ] CA-04 — `agents/implementer.md` declara el opt-in al cerrar cada fase (+ nota de que el ledger no está en el espejo por defecto); `agents/qa.md` declara el informe de `testing/` solo-local.
- [ ] CA-05 — `docs/FLOWS.md` (+ espejo `docs/en/FLOWS.md`) tiene la matriz disparador→artefacto→¿se publica? con los 10 disparadores y los "no" explícitos.
- [ ] CA-06 — Ningún cambio introduce publicación de `docs/security-scan/**` (verificable por inspección del `exclude` y por `confluence-scope.py --check`).
- [ ] [GWT] CA-07 — `confluence-scope.py --status` clasifica cada doc en en-alcance/sincronizado/desactualizado-o-pendiente/excluido, lista los excluidos esperados, no lista nada fuera de `docs/`, y termina con exit 0.
- [ ] [GWT] CA-08 — Con un `exclude` que omite `docs/security-scan/**`, `confluence-scope.py --check` falla con exit ≠ 0 y nombra la invariante violada.
- [ ] [GWT] CA-10 — `confluence-scope.py --stage` crea `docs/confluence/` con exactamente los ficheros en alcance (byte a byte) + su fichero de aviso `_STAGING-LEEME.md` (*enmienda al cierre 2026-08-20: antes «README.md» con fecha; colisionaba con el canónico y rompía la idempotencia*); reejecutado sin cambios es idempotente; ningún excluido aparece dentro.
- [ ] [GWT] CA-11 — Con staging activo y una página modificada en Confluence, el mapeo inverso resuelve al fichero **canónico** de `docs/`, nunca a `docs/confluence/`.
- [ ] CA-12 — `hooks/mark-docs-pending.sh` ignora `docs/confluence/**`, verificado con un caso de prueba del hook.
- [ ] CA-09 — `python3 scripts/lint_plugin.py` y todas las suites de `tests/` (incluida la nueva) terminan en verde.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Una exclusión de más/menos en `confluence.example.json` deja doc interna publicable o esconde doc esperada, y el conector no borra páginas | Media | Alto | Cerrar la Fase 1 completa (con CA-01/CA-06) antes de tocar nada más; `--check` lo hace verificable con exit code |
| Ausencias silenciosas: plan, `tasks.md` y `testing/**` no suben y el disparo por fase de `implementer` no publica el ledger — alguien busca en Confluence algo que nunca estará | Alta | Bajo | Hacerlo explícito en la matriz de FLOWS y en `SKILL.md` (Fase 4, CA-04/CA-05) |
| `confluence-scope.py` (script nuevo con más código de lo habitual en este plugin) diverge en su semántica de glob de la que aplique la skill al publicar | Media | Alto | Declarar el script **fuente de verdad** del alcance; la skill lo invoca, no reinterpreta patrones (Fase 3, T-06 a T-10) |
| Bucle de regeneración si el hook no ignora `docs/confluence/**` | Media | Medio | CA-12 con caso de prueba dedicado (T-10) |
| Pérdida de ediciones si alguien toca `docs/confluence/` a mano | Media | Medio | `_STAGING-LEEME.md` generado de aviso + `--status` señalando divergencia (T-08) |
| Regla bilingüe: olvidar el espejo EN rompe la convención y lo detecta el linter tarde | Media | Bajo | Espejo EN en la MISMA tarea que su original (T-12, T-13), nunca en una tarea posterior |
| Estimación de horas humanas no validada (histórico: 0 h reales) | Alta | Medio | Presentar el coste como comparativa, no compromiso; ejecutar `/retro` al cerrar la iniciativa |

---

## Métricas de éxito

- `confluence-scope.py --status` ejecutado sobre este repo clasifica el 100 % de `docs/*.md` sin errores y con exit 0.
- `confluence-scope.py --check` detecta la violación de la invariante de `security-scan` en un fixture manipulado (prueba negativa).
- Los 10 disparadores conocidos (`analyst`, `evaluator`, `planner`, `qa`, `documenter`, `/pm-backlog`, `/retro`, `/spec-drift`, `/roadmap-brief`, `implementer`) quedan reflejados en la matriz de `docs/FLOWS.md` con su "¿se publica?" explícito.
- `python3 scripts/lint_plugin.py` + todas las suites de `tests/` en verde tras el cambio completo (13/13 tareas).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-08-20 | Creación del plan a partir de `spec.md` (aprobada) y `evaluation.md` (completado, GO). 4 fases, 13 tareas, cifras heredadas sin re-estimar. | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase (orden obligatorio: 1 → 2 → 3 → 4) sobre una rama, marcando `tasks.md` como **ledger canónico**. Al terminar, no hay handoff a `qa` con `test-plan.md` (no aplica: sin UI, verificación por scripts/suites) — el cierre de cada fase se valida con `python3 scripts/lint_plugin.py` + suites de `tests/`, y el handoff final es a `documenter` para reflejar la política ya materializada. Se recomienda ejecutar `/retro` al cerrar para calibrar horas humanas (histórico con 0 h reales validadas).
