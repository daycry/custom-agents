<!--
  TEMPLATE: improvement-plan.md  ·  usado por el agente `planner`
  Sustituye todos los {{PLACEHOLDER}}. Borra este comentario y las notas <!-- guía --> al generar.
  Estados válidos: 📝 borrador · 🚧 en-progreso · 🔍 en-revision · ✅ completado · ❌ cancelado
  Prioridad: 🟢 Baja · 🟡 Media · 🟠 Alta · 🔴 Crítica
-->

# {{YYYY-MM-DD-slug}}

> {{Título legible del plan — una frase que lo resuma}}

| | |
|---|---|
| **Fecha** | {{YYYY-MM-DD}} |
| **Estado** | 📝 borrador |
| **Tipo** | {{Nueva Funcionalidad / Refactor / Bugfix / Infra / Investigación}} |
| **Prioridad** | 🟡 Media |
| **Solicitante** | {{nombre}} |
| **Responsable** | {{nombre}} |
| **Spec** | {{[`docs/specs/<slug>.md`](../../specs/<slug>.md) — o «n/a»}} |
| **Evaluación** | {{[`docs/evaluations/<fecha>-<slug>/evaluation.md`](../../evaluations/<fecha>-<slug>/evaluation.md) — o «n/a»}} |

---

## 🎛️ Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| ⏱️ Tiempo | **{{X}}h** | {{0}}h | {{Alta / Media / Baja}} |
| 💶 Coste total | **{{X}} €** | {{0}} € | {{Alta / Media / Baja}} |
| 🔢 Tokens IA | **{{X}}** (in {{X}} / out {{X}}) | {{0}} | {{Alta / Media / Baja}} |
| 📦 Tareas | **{{N}}** | {{0}} hechas | — |

<!-- guía: "Confianza" refleja lo firme que es la estimación dado lo que se sabe hoy. -->

---

## ⏱️ Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| {{Fase 1 — nombre}} | {{0.5}} | {{20k}} / {{8k}} | {{X}} |
| {{Fase 2 — nombre}} | {{1.0}} | {{40k}} / {{15k}} | {{X}} |
| {{Fase 3 — nombre}} | {{1.5}} | {{60k}} / {{20k}} | {{X}} |
| {{Fase N — Testing}} | {{0.5}} | {{15k}} / {{5k}} | {{X}} |
| **Total** | **{{X}}h** | **{{X}} / {{X}}** | **{{X}} €** |

---

## 💶 Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | {{50}} €/h | Configurable por proyecto/perfil |
| Modelo IA asumido | {{claude-opus-4-8}} | Modelo previsto para la ejecución |
| Precio input | {{X}} € / 1M tokens | ⚠️ Verificar tarifa vigente antes de fijar el presupuesto |
| Precio output | {{X}} € / 1M tokens | ⚠️ Verificar tarifa vigente |
| Tipo de cambio | {{1 USD = 0.92 €}} | Si la tarifa del proveedor está en USD |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano) | {{X}}h × {{50}} €/h | **{{X}} €** |
| Tokens IA (input) | {{X}} tok × precio | {{X}} € |
| Tokens IA (output) | {{X}} tok × precio | {{X}} € |
| **Total estimado** | | **{{X}} €** |

<!-- guía: si no hay ejecución por IA, deja el bloque de tokens a 0 y decláralo. -->

---

## 🔢 Previsión de tokens (por fase)

Estimación del consumo de tokens del modelo por fase. Base: {{modelo}} · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| {{Fase 1}} | {{20k}} | {{8k}} | {{28k}} | {{X}} |
| {{Fase 2}} | {{40k}} | {{15k}} | {{55k}} | {{X}} |
| {{Fase N}} | {{15k}} | {{5k}} | {{20k}} | {{X}} |
| **Total** | **{{X}}** | **{{X}}** | **{{X}}** | **{{X}} €** |

**Método de estimación:** {{breve explicación — p. ej. nº de ficheros a leer × tamaño medio + generación de código/tests}}.

---

## 📋 Resumen ejecutivo

{{2-4 frases: qué se va a hacer, para quién y por qué. Sin jerga innecesaria.}}

### 🎯 Objetivos

- {{Objetivo 1 — medible}}
- {{Objetivo 2}}
- {{Objetivo 3}}

---

## 📥 Datos necesarios para un informe completo

<!-- guía: checklist de insumos que el plan necesita para estar completo y ser ejecutable.
     Marca [x] lo que ya tienes; lo que quede en [ ] es un bloqueante a resolver. -->

- [ ] **Requisitos funcionales** confirmados por el solicitante
- [ ] **Alcance** cerrado (qué entra y qué NO entra en esta iteración)
- [ ] **Criterios de éxito / métricas** acordados
- [ ] **Accesos y credenciales** necesarios (entornos, APIs, repos)
- [ ] **Entornos** disponibles (local / staging / prod) y datos de prueba
- [ ] **Stakeholders** identificados y disponibilidad para validar
- [ ] **Dependencias externas** (equipos, proveedores, librerías) mapeadas
- [ ] **Restricciones** conocidas (deadline, presupuesto, compliance, técnicas)
- [ ] **Tarifa/hora y supuestos de coste** confirmados

---

## 🔍 Análisis de impacto

<!-- guía: qué zonas del sistema toca. Rutas/módulos reales. -->

- **`{{ruta/módulo}}`** — {{qué cambia}}
- **`{{ruta/módulo}}`** — {{qué cambia}}

---

## 🏗️ Cambios arquitectónicos

- {{Decisión de diseño 1 y su porqué}}
- {{Decisión de diseño 2}}

---

## 📁 Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `{{ruta}}` | Crear | {{para qué}} |
| `{{ruta}}` | Modificar | {{qué cambia}} |

---

## 🔗 Dependencias y prerequisitos

- {{Depende de X / Requiere que Y esté hecho antes}}
- {{Bloqueado por Z (si aplica)}}

---

## ✅ Criterios de aceptación (global)

- [ ] {{Criterio verificable 1}}
- [ ] {{Criterio verificable 2}}
- [ ] {{Criterio verificable 3}}

---

## ⚠️ Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| {{Riesgo 1}} | {{Media}} | {{Alto}} | {{Cómo se reduce}} |
| {{Riesgo 2}} | {{Baja}} | {{Medio}} | {{Cómo se reduce}} |

---

## 📊 Métricas de éxito

- {{KPI 1 — cómo se medirá que el plan cumplió su objetivo}}
- {{KPI 2}}

---

## ⏱️ Agregación de tiempo

- {{YYYY-MM-DD}}: Creación del plan (`Tiempo consumido`: 0h)

---

## 📝 Changelog

- {{YYYY-MM-DD}}: Creación del plan.
