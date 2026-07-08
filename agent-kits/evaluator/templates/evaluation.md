<!--
  TEMPLATE: evaluation.md  ·  usado por el agente `evaluator`
  Entrada: un documento de toma de requerimientos (una o varias características/requisitos).
  Salida: esta evaluación/presupuesto. Sustituye todos los {{PLACEHOLDER}} y borra los comentarios guía.
  Estados: 📝 borrador · 🚧 en-progreso · 🔍 en-revision · ✅ completado · ❌ cancelado
  Prioridad: 🟢 Baja · 🟡 Media · 🟠 Alta · 🔴 Crítica
  Si solo hay UNA característica: omite la tabla comparativa (§6) y la recomendación de orden.
-->

# {{YYYY-MM-DD-slug}}

> {{Título legible — qué se evalúa y para qué decisión}}

| | |
|---|---|
| **Fecha** | {{YYYY-MM-DD}} |
| **Estado** | 📝 borrador |
| **Prioridad global** | 🟡 Media |
| **Solicitante** | {{nombre}} |
| **Documento de requerimientos** | {{ruta o referencia del doc origen}} |
| **Características evaluadas** | {{N}} |

---

## 🎛️ Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| ⏱️ Esfuerzo | **{{X}}h** | {{Alta / Media / Baja}} |
| 💶 Coste | **{{X}} €** | {{Alta / Media / Baja}} |
| 🔢 Tokens IA | **{{X}}** (in {{X}} / out {{X}}) | {{Alta / Media / Baja}} |
| 📦 Características | **{{N}}** | — |

---

## 📋 Resumen ejecutivo

{{2-4 frases: qué requerimientos han llegado, qué se presupuesta y qué decisión soporta esta evaluación (p. ej. priorizar el roadmap del trimestre).}}

---

## 📄 Requerimientos recibidos

Mapa del documento de origen a las características evaluadas. Marca vacíos e incógnitas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | {{nombre}} | {{sección/página del doc}} | ✅ / ⚠️ ambiguo |
| C-02 | {{nombre}} | {{ref.}} | ✅ / ⚠️ ambiguo |

**Ambigüedades / información que falta:** {{lista de puntos poco claros del documento que afectan a la estimación. Si algo es un supuesto, decláralo.}}

---

## 📥 Datos necesarios para una evaluación completa

<!-- guía: marca [x] lo que el documento de requerimientos ya cubre; lo que quede en [ ] es un bloqueante. -->

- [ ] **Requerimientos** completos y sin ambigüedades
- [ ] **Alcance** de cada característica acotado (qué entra y qué NO)
- [ ] **Criterios de aceptación / éxito** por característica
- [ ] **Restricciones** (deadline, presupuesto, compliance, técnicas)
- [ ] **Dependencias externas** (equipos, proveedores, APIs) identificadas
- [ ] **Contexto técnico** del proyecto (stack, integraciones) disponible
- [ ] **Tarifa/hora y supuestos de coste** confirmados

---

## 💶 Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | {{50}} €/h | Configurable por proyecto/perfil |
| Modelo IA asumido | {{claude-opus-4-8}} | Base de la previsión de tokens |
| Precio input | {{X}} € / 1M tokens | ⚠️ Verificar tarifa vigente |
| Precio output | {{X}} € / 1M tokens | ⚠️ Verificar tarifa vigente |
| Tipo de cambio | {{1 USD = 0.92 €}} | Si el proveedor factura en USD |

---

## 🔎 Evaluación por característica

<!-- ============ BLOQUE (copia uno por cada característica del documento) ============ -->

### C-01 — {{nombre de la característica}}

- **Requisito origen**: {{referencia en el documento}}
- **Descripción**: {{qué es y qué aporta, 1-3 frases}}
- **Complejidad**: {{Baja / Media / Alta / Muy alta}}
- **Esfuerzo**: {{X}}h · confianza {{Alta / Media / Baja}}
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Coste**: ({{X}}h × tarifa) + tokens = **{{X}} €**
- **Impacto / áreas afectadas**: `{{módulo/ruta}}`, `{{...}}`
- **Dependencias y prerequisitos**: {{ninguna / requiere X / bloqueado por Y}}
- **Riesgos**: {{principales riesgos de coste o viabilidad}}
- **Incógnitas / preguntas abiertas**: {{lo que habría que aclarar para afinar}}

<!-- ================================================================================= -->

### C-02 — {{nombre}}

- **Requisito origen**: {{ref.}}
- **Descripción**: {{...}}
- **Complejidad**: {{...}}
- **Esfuerzo**: {{X}}h · confianza {{...}}
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Coste**: **{{X}} €**
- **Impacto / áreas afectadas**: {{...}}
- **Dependencias y prerequisitos**: {{...}}
- **Riesgos**: {{...}}
- **Incógnitas / preguntas abiertas**: {{...}}

---

## 📊 Comparativa

<!-- guía: incluir SOLO si hay 2+ características. Ordena por lo que ayude a decidir (coste, prioridad o valor). -->

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | {{nombre}} | {{Media}} | {{12}}h | {{600}} € | {{180k}} | 🟡 Media | {{Alta}} |
| C-02 | {{nombre}} | {{Alta}} | {{40}}h | {{2.000}} € | {{520k}} | 🟠 Alta | {{Media}} |
| | **Total** | | **{{X}}h** | **{{X}} €** | **{{X}}** | | |

---

## 💶 Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano) | {{X}}h × {{50}} €/h | **{{X}} €** |
| Tokens IA (input) | {{X}} tok × precio | {{X}} € |
| Tokens IA (output) | {{X}} tok × precio | {{X}} € |
| **Total estimado** | | **{{X}} €** |

---

## 🧭 Recomendación

<!-- guía: apoya la decisión. Con varias características, sugiere orden (quick-wins vs. caras, alta prioridad, dependencias). -->

- **Veredicto**: {{go / no-go / go condicionado a resolver incógnitas}}
- **Quick wins** (bajo coste, alto valor): {{C-0X, ...}}
- **Costosas / a valorar**: {{C-0X, ...}}
- **Orden sugerido**: {{C-0X → C-0X → C-0X}} — {{motivo}}
- **Fuera de alcance recomendado**: {{si aplica}}

---

## ⚠️ Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| {{Riesgo común a varias características}} | {{Media}} | {{Alto}} | {{Cómo se reduce}} |

---

## 🔗 Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (crea `docs/plans/<fecha>-<slug>/` con `improvement-plan.md` + `TASKS.md`). Indica qué características se aprueban para planificar: {{C-0X, C-0X}}.

---

## 📝 Changelog

- {{YYYY-MM-DD}}: Creación de la evaluación a partir de `{{documento de requerimientos}}`.
