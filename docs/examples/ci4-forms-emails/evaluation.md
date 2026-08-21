# 2026-07-08-ci4-forms-emails

> Evaluación/presupuesto de la app CI4 con 2 formularios y 2 envíos de email.

| | |
|---|---|
| **Fecha** | 2026-07-08 |
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
| Esfuerzo humano | **26,4 h** (22 h base +20 %) | Alta |
| Tiempo IA (ejecución) | **1,8 h** (+ 0,45 h supervisión) | Media |
| Coste | **~1.329 €** | Alta |
| Tokens IA | **390k** (in 300k / out 90k) | Media |
| Multiplicador productividad | **×11,7** | — |
| Características | **2** | — |

---

## Resumen ejecutivo

La spec pide una app CI4 con dos formularios públicos (contacto y solicitud de presupuesto), cada uno con un envío de email (notificación al equipo y confirmación al usuario). Es un desarrollo **pequeño y de baja incertidumbre**: todo se resuelve con lo nativo de CodeIgniter 4. Se presupuesta para decidir su inclusión en el sprint.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Formulario de contacto + email de notificación | spec §Flujo (Contacto) | |
| C-02 | Formulario de solicitud + email de confirmación | spec §Flujo (Solicitud) | |

**Ambigüedades / información que falta:** ninguna bloqueante. Pendiente solo el **servidor SMTP** y los textos definitivos de los emails (asumidos provisionales).

---

## Datos necesarios para una evaluación completa

- [x] Requerimientos completos y sin ambigüedades
- [x] Alcance de cada característica acotado (spec §Alcance)
- [x] Criterios de aceptación / éxito por característica
- [ ] Credenciales/servidor **SMTP** disponibles
- [x] Contexto técnico (CI4, sin BD en esta iteración)
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

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

### C-01 — Formulario de contacto + email de notificación

- **Requisito origen**: spec §Flujo (Contacto)
- **Descripción**: formulario público (nombre, email, mensaje) que, al validarse, envía un email de notificación al buzón del equipo.
- **Complejidad**: Baja-Media
- **Esfuerzo**: 10 h · confianza Alta
- **Previsión IA**: 140k in / 40k out tok · 2,2 €
- **Coste**: (10 h × 50 €/h) + tokens = **~502 €**
- **Impacto / áreas afectadas**: `Controllers/ContactController`, `Views/contact/*`, `Views/emails/contact_notify`, `Config/Routes`, `Config/Email`
- **Dependencias y prerequisitos**: proyecto CI4 inicializado + SMTP configurado
- **Riesgos**: entrega de email (SPF/DKIM del dominio); mitigable con buen SMTP
- **Incógnitas / preguntas abiertas**: buzón destino definitivo del equipo

### C-02 — Formulario de solicitud + email de confirmación

- **Requisito origen**: spec §Flujo (Solicitud)
- **Descripción**: formulario (nombre, email, empresa, detalle) que, al validarse, envía un email de confirmación (acuse) al usuario con su petición.
- **Complejidad**: Media
- **Esfuerzo**: 12 h · confianza Media
- **Previsión IA**: 160k in / 50k out tok · 4,9 €
- **Coste**: (12 h × 50 €/h) + tokens = **~605 €**
- **Impacto / áreas afectadas**: `Controllers/QuoteController`, `Views/quote/*`, `Views/emails/quote_confirm`, `Config/Routes`
- **Dependencias y prerequisitos**: comparte setup CI4 + SMTP con C-01
- **Riesgos**: contenido del acuse (datos personales en el email); mantener mínimo necesario
- **Incógnitas / preguntas abiertas**: campos exactos del formulario de solicitud

---

## Comparativa

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Contacto + email notificación | Baja-Media | 10 h | ~502 € | 180k | Media | Alta |
| C-02 | Solicitud + email confirmación | Media | 12 h | ~605 € | 210k | Media | Media |
| | **Total** | | **22 h** | **~1.109 €** | **390k** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 22 h × 50 €/h | 1.100 € |
| Margen de contingencia | +20 % sobre desarrollo base | 220 € |
| Tokens IA (input) | 300k × 12 €/1M | 3,6 € |
| Tokens IA (output) | 90k × 60 €/1M | 5,4 € |
| **Total estimado (con margen)** | | **~1.329 €** |

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 26,4 h (22 h base +20 %) |
| Horas IA (ejecución) | 1,8 h (1,5 h base +20 %) |
| Supervisión humana | 0,45 h |
| **Horas totales (IA + supervisión)** | **2,25 h** |
| Horas ahorradas | 24,15 h |
| **Ahorro** | **91,5 %** |
| **Multiplicador de productividad** | **×11,7** |
| FTE equivalentes *(opcional)* | 0,15 |

> Horas **con margen de contingencia (+20 %)** ya aplicado. Base: 22 h humanas / 1,5 h IA. Horas IA estimadas como supuesto (≈ horas humanas ÷ 15); supervisión al 25 % de las horas IA.

---

## Recomendación

- **Veredicto**: **go**. Bajo coste, baja incertidumbre, alto valor (captación de leads).
- **Quick win**: C-01 (contacto) — más simple y desbloquea el canal de contacto ya.
- **Orden sugerido**: C-01 → C-02 (C-02 reutiliza el setup de email de C-01).
- **Bloqueante menor a resolver**: disponer del **SMTP** antes de empezar los envíos.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Emails a spam (reputación del dominio) | Media | Medio | SMTP con SPF/DKIM; remitente del propio dominio |
| Spam de bots en formularios | Media | Bajo | Honeypot + rate-limit (en alcance) |

---

## Siguiente paso

Para **ejecutar** lo aprobado, el plan detallado está en [`improvement-plan.md`](improvement-plan.md) (generado por `planner`). Características aprobadas para planificar: **C-01 y C-02**.

---

## Changelog

- 2026-07-08: Evaluación creada a partir de [`spec.md`](spec.md).
- 2026-07-08: Handoff a `planner`; enlazado el plan.
