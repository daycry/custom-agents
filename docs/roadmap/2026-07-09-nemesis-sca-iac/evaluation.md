# 2026-07-09-nemesis-sca-iac

> Evaluación/presupuesto de añadir trivy (SCA) y hadolint (IaC) a nemesis.

| | |
|---|---|
| **Fecha** | 2026-07-09 |
| **Estado** | completado |
| **Prioridad global** | Media |
| **Solicitante** | daycry |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **Características evaluadas** | 2 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **12 h** (10 h base +20 %) | Alta |
| Tiempo IA (ejecución) | **1,2 h** (+ 0,3 h supervisión) | Media |
| Coste | **~605 €** | Alta |
| Tokens IA | **195k** (in 150k / out 45k) | Media |
| Multiplicador productividad | **×8** | — |
| Características | **2** | — |

---

## Resumen ejecutivo

La spec propone reforzar `nemesis` con dos escáneres OSS: **trivy** (dependencias contra BD de CVEs real → área `deps`) y **hadolint** (lint de Dockerfile → área `iac`). Ambas áreas ya existen en el esquema, así que el trabajo es **aditivo y de bajo riesgo**: no toca `schema.md` ni el informe. Se presupuesta para decidir su inclusión.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | SCA real con trivy (area `deps`) | spec §Arquitectura / §Flujo | Sí |
| C-02 | Lint de Dockerfile con hadolint (area `iac`) | spec §Arquitectura / §Flujo | Sí |

**Ambigüedades / información que falta:** ninguna bloqueante. trivy descarga su BD de CVEs en el primer uso (requiere red esa vez).

---

## Datos necesarios para una evaluación completa

- [x] Requerimientos completos (spec aprobada en concepto)
- [x] Alcance acotado (spec §Alcance: solo `trivy fs` + `hadolint`)
- [x] Áreas de destino existen en el esquema (`deps`, `iac`)
- [x] Patrón de integración conocido (catalog / install-tools / run-external / check-tools)
- [ ] Confirmar red disponible para la BD de trivy en el primer uso
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en EUR.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | — |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 12 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Precio output | 60 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Ratio de supervisión | ~25 % de las horas IA | — |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

---

## Evaluación por característica

### C-01 — SCA real con trivy (area `deps`)

- **Requisito origen**: spec §Arquitectura / §Flujo
- **Descripción**: alta de `trivy` en catálogo/instalador/check-tools, wrapper `trivy fs --format json` en `run-external.sh`, y normalización de su salida a findings del área `deps` (mapeo de severidad, CVE, paquete\@versión) con dedupe contra la skill.
- **Complejidad**: Media
- **Esfuerzo**: 6 h base · confianza Alta
- **Previsión IA**: 90k in / 28k out tok · ~1,7 €
- **Coste**: (6 h × 50 €/h) + tokens = **~303 €** (base)
- **Impacto / áreas afectadas**: `agent-kits/nemesis/tools/{catalog.md,install-tools.sh,run-external.sh,check-tools.sh}`, `agents/nemesis.md`
- **Dependencias y prerequisitos**: red en el primer uso (BD de CVEs)
- **Riesgos**: ruido de findings de trivy (calibrar severidades); mitigable en normalización
- **Incógnitas / preguntas abiertas**: alcance exacto (`trivy fs` vs. también `trivy config`) — aquí solo `fs`

### C-02 — Lint de Dockerfile con hadolint (area `iac`)

- **Requisito origen**: spec §Arquitectura / §Flujo
- **Descripción**: alta de `hadolint` en catálogo/instalador/check-tools, wrapper `hadolint --format json` sobre los `Dockerfile*`, y normalización a findings del área `iac` (regla `DLxxxx`, `Dockerfile:línea`).
- **Complejidad**: Baja
- **Esfuerzo**: 4 h base · confianza Alta
- **Previsión IA**: 60k in / 17k out tok · ~1,7 €
- **Coste**: (4 h × 50 €/h) + tokens = **~202 €** (base)
- **Impacto / áreas afectadas**: `agent-kits/nemesis/tools/*`, `agents/nemesis.md`
- **Dependencias y prerequisitos**: proyecto con `Dockerfile` para probar
- **Riesgos**: bajo; hadolint es determinista y ligero
- **Incógnitas / preguntas abiertas**: ninguna relevante

---

## Comparativa

| # | Característica | Complejidad | Horas (base) | Coste € (base) | Tokens | Prioridad | Confianza |
|---|---------------|-------------|--------------|----------------|--------|-----------|-----------|
| C-01 | SCA trivy (deps) | Media | 6 h | ~303 € | 118k | Media | Alta |
| C-02 | Lint hadolint (iac) | Baja | 4 h | ~202 € | 77k | Media | Alta |
| | **Total (base)** | | **10 h** | **~505 €** | **195k** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 10 h × 50 €/h | 500 € |
| Margen de contingencia | +20 % sobre desarrollo base | 100 € |
| Tokens IA (input) | 150k × 12 €/1M | 1,8 € |
| Tokens IA (output) | 45k × 60 €/1M | 2,7 € |
| **Total estimado (con margen)** | | **~605 €** |

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 12 h (10 h base +20 %) |
| Horas IA (ejecución) | 1,2 h (1 h base +20 %) |
| Supervisión humana | 0,3 h |
| **Horas totales (IA + supervisión)** | **1,5 h** |
| Horas ahorradas | 10,5 h |
| **Ahorro** | **87,5 %** |
| **Multiplicador de productividad** | **×8** |
| FTE equivalentes *(opcional)* | 0,07 |

> Horas con margen de contingencia (+20 %) ya aplicado. Base: 10 h humanas / 1 h IA. Horas IA estimadas como supuesto (≈ horas humanas ÷ 15); supervisión al 25 % de las horas IA.

---

## Recomendación

- **Veredicto**: go. Aditivo, sin cambios de esquema/informe, sube mucho la precisión de `deps` e `iac`.
- **Quick win**: C-02 (hadolint) — más simple, determinista y barato.
- **Orden sugerido**: C-02 → C-01 (hadolint valida el patrón de integración; trivy añade la BD de CVEs y algo más de calibración).
- **Bloqueante menor**: confirmar red para la BD de trivy en el primer uso.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Ruido de findings (falsos positivos de trivy) | Media | Bajo | Calibración de severidad + dedupe en normalización |
| Antivirus marca los binarios | Baja | Bajo | Excluir `~/.claude/security-tools/` (ya documentado) |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `docs/roadmap/2026-07-09-nemesis-sca-iac/` con `improvement-plan.md` + `tasks.md`). Características aprobadas para planificar: **C-01 y C-02**.

---

## Changelog

- 2026-07-09: Evaluación creada a partir de [`spec.md`](spec.md).
- 2026-07-09: Aprobada; plan generado ([`improvement-plan.md`](improvement-plan.md)); cadena cerrada.
