# 2026-07-09-nemesis-sca-iac

> Añadir trivy (SCA de dependencias → area deps) y hadolint (lint de Dockerfile → area iac) a nemesis. Plan de implementación.

| | |
|---|---|
| **Fecha** | 2026-07-09 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | daycry |
| **Responsable** | — |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **12 h** (10 h base +20 %) | 0 h | Alta |
| Tiempo IA (ejecución) | **1,2 h** (+ 0,3 h supervisión) | 0 h | Media |
| Coste total | **~605 €** | 0 € | Alta |
| Tokens IA | **195k** (in 150k / out 45k) | 0 | Media |
| Multiplicador productividad | **×8** | — | — |
| Tareas | **7** | 0 hechas | — |

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| F1 — hadolint (area iac) | 4 | 60k / 17k | 200 |
| F2 — trivy (area deps) | 6 | 90k / 28k | 300 |
| **Total (base)** | **10 h** | **150k / 45k** | **500 €** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en EUR.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | — |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 12 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Precio output | 60 € / 1M tokens | ilustrativo, verificar tarifa vigente |
| Ratio de supervisión | ~25 % de las horas IA | — |
| Horas por empleado-mes (FTE) | 160 h | — |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 10 h × 50 €/h | 500 € |
| Margen de contingencia | +20 % sobre desarrollo base | 100 € |
| Tokens IA (input) | 150k × 12 €/1M | 1,8 € |
| Tokens IA (output) | 45k × 60 €/1M | 2,7 € |
| **Total estimado (con margen)** | | **~605 €** |

---

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| F1 — hadolint | 60k | 17k | 77k | 1,7 |
| F2 — trivy | 90k | 28k | 118k | 2,8 |
| **Total** | **150k** | **45k** | **195k** | **~4,5 €** |

**Método de estimación:** lectura de los scripts del toolkit + edición del catálogo/instalador/wrappers + código de normalización de las salidas JSON.

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

## Resumen ejecutivo

Reforzar `nemesis` con dos escáneres OSS que alimentan áreas ya existentes del `findings.json`: **hadolint** (lint de Dockerfile → `iac`) y **trivy** (SCA de dependencias con BD de CVEs → `deps`). Es aditivo: no se toca `schema.md` ni el informe. Se empieza por hadolint (más simple y determinista) para validar el patrón de integración, y luego trivy.

### Objetivos

- `hadolint` y `trivy` instalables desde el toolkit (opt-in) y detectados por `check-tools.sh`.
- Sus salidas JSON normalizadas a findings de las áreas `iac` y `deps`, con dedupe contra la skill.
- `nemesis` los ejecuta en la fase estática y los declara en `tools_used`.

---

## Datos necesarios para un informe completo

- [x] Requisitos confirmados (spec aprobada)
- [x] Alcance cerrado (solo `trivy fs` + `hadolint`)
- [x] Áreas de destino existen (`deps`, `iac`) → sin cambios de esquema
- [ ] Red disponible para la BD de CVEs de trivy en el primer uso
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Análisis de impacto

- **`agent-kits/nemesis/tools/catalog.md`** — documentar las 2 tools.
- **`agent-kits/nemesis/tools/install-tools.sh`** — entradas de instalación (trivy vía `install_go_bin`; hadolint binario de release).
- **`agent-kits/nemesis/tools/check-tools.sh`** — añadir `trivy` y `hadolint`.
- **`agent-kits/nemesis/tools/run-external.sh`** — wrappers `trivy fs` y `hadolint` (salida JSON a `raw/`), **sin** guardrail (no hay URL).
- **`agent-kits/nemesis/tools/pick_asset.py`** — verificar que resuelve los assets de ambas.
- **`agents/nemesis.md`** — §4 (ejecutar en fase estática) y §5 (interpretar/mapear a `deps`/`iac`).
- **Sin cambios** en `report/schema.md` ni `report/template.html`.

---

## Cambios arquitectónicos

- trivy y hadolint son **estáticos** (escanean el árbol de ficheros): corren en la fase SAST/normalización y **no** pasan por el guardrail (no hay host objetivo).
- Sus findings se funden en áreas existentes (`deps`, `iac`); dedupe cross-source con la skill.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/nemesis/tools/catalog.md` | Modificar | Documentar trivy y hadolint |
| `agent-kits/nemesis/tools/install-tools.sh` | Modificar | Instalación de ambas |
| `agent-kits/nemesis/tools/check-tools.sh` | Modificar | Detección de ambas |
| `agent-kits/nemesis/tools/run-external.sh` | Modificar | Wrappers `trivy fs` y `hadolint` |
| `agents/nemesis.md` | Modificar | Ejecución (§4) e interpretación (§5) |
| `docs/agents/nemesis.md` | Modificar | Documentar las nuevas fuentes |

---

## Dependencias y prerequisitos

- **F1 (hadolint) antes que F2 (trivy)** para validar el patrón de integración con la tool más simple.
- Red para la BD de CVEs de trivy en el primer uso.

---

## Criterios de aceptación (global)

- [ ] `check-tools.sh` reporta `trivy` y `hadolint` (instaladas/faltan).
- [ ] `hadolint` produce `raw/hadolint.json` y sus hallazgos aparecen en el área `iac`.
- [ ] `trivy fs` produce `raw/trivy.json` y sus hallazgos aparecen en el área `deps`.
- [ ] Dedupe: una dependencia ya señalada por la skill no se duplica.
- [ ] Sin las tools instaladas, el scan sigue y declara cobertura parcial en `tools_used`.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Ruido de findings de trivy | Media | Bajo | Calibración de severidad + dedupe en normalización |
| BD de trivy no descarga (sin red) | Media | Medio | Aviso y omisión declarada; se ejecuta en cuanto haya red |
| Antivirus marca los binarios | Baja | Bajo | Excluir `~/.claude/security-tools/` (documentado) |

---

## Métricas de éxito

- Un proyecto con `Dockerfile` y dependencias se audita y el informe muestra findings reales en `deps` e `iac`.

---

## Agregación de tiempo

- 2026-07-09: Creación del plan (`Tiempo consumido`: 0h).

---

## Changelog

- 2026-07-09: Plan creado a partir de [`evaluation.md`](evaluation.md) (aprobadas C-01 y C-02) y [`spec.md`](spec.md).
