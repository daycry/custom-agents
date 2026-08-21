# 2026-07-08-ci4-forms-emails

> App CodeIgniter 4 con 2 formularios y 2 envíos de email — plan de implementación.

| | |
|---|---|
| **Fecha** | 2026-07-08 |
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
| Tiempo humano | **26,4 h** (22 h base +20 %) | 0 h | Alta |
| Tiempo IA (ejecución) | **1,8 h** (+ 0,45 h supervisión) | 0 h | Alta |
| Coste total | **~1.329 €** | 0 € | Alta |
| Tokens IA | **390k** (in 300k / out 90k) | 0 | Media |
| Multiplicador productividad | **×11,7** | — | — |
| Tareas | **13** | 0 hechas | — |

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| F1 — Setup CI4 + config email | 3 | 30k / 8k | 150 |
| F2 — Formulario de contacto + email | 6 | 80k / 22k | 300 |
| F3 — Formulario de solicitud + email | 7 | 90k / 25k | 350 |
| F4 — Anti-spam + UX (PRG/mensajes) | 2 | 30k / 10k | 100 |
| F5 — Tests | 3 | 55k / 20k | 150 |
| F6 — Documentación | 1 | 15k / 5k | 50 |
| **Total** | **22 h** | **300k / 90k** | **1.100 €** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

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
| Desarrollo (humano, base) | 22 h × 50 €/h | 1.100 € |
| Margen de contingencia | +20 % sobre desarrollo base | 220 € |
| Tokens IA (input) | 300k × 12 €/1M | 3,6 € |
| Tokens IA (output) | 90k × 60 €/1M | 5,4 € |
| **Total estimado (con margen)** | | **~1.329 €** |

> La tabla "Estimación por fase" está en horas **base** (22 h); el margen de contingencia (+20 %) se aplica al agregado → 26,4 h / ~1.329 €.

---

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| F1 | 30k | 8k | 38k | 0,9 |
| F2 | 80k | 22k | 102k | 2,3 |
| F3 | 90k | 25k | 115k | 2,6 |
| F4 | 30k | 10k | 40k | 1,0 |
| F5 | 55k | 20k | 75k | 1,9 |
| F6 | 15k | 5k | 20k | 0,5 |
| **Total** | **300k** | **90k** | **390k** | **~9 €** |

**Método de estimación:** nº de ficheros a leer/crear (controladores, vistas, config, tests) × tamaño medio + generación de código y de los tests.

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

## Resumen ejecutivo

Implementar en CodeIgniter 4 dos formularios públicos (contacto y solicitud de presupuesto), cada uno con un envío de email (notificación al equipo y confirmación al usuario), usando solo componentes nativos de CI4 (Email/SMTP, Validation, CSRF, Honeypot, Throttler). Desarrollo pequeño, cerrado y de baja incertidumbre.

### Objetivos

- Dos formularios funcionales con validación server-side y anti-spam.
- Dos envíos de email con plantillas HTML.
- Feature tests que cubran el camino feliz y los errores de validación.

---

## Datos necesarios para un informe completo

- [x] Requisitos funcionales confirmados (spec aprobada)
- [x] Alcance cerrado (spec §Alcance)
- [x] Criterios de éxito acordados
- [ ] **SMTP** disponible (host, usuario, contraseña) para `.env`
- [x] Restricciones conocidas (sin BD, sin captcha esta iteración)
- [x] Tarifa/hora y supuestos de coste confirmados

---

## Análisis de impacto

- **`app/Controllers/`** — nuevos `ContactController` y `QuoteController`.
- **`app/Views/`** — vistas de formularios y de emails (`emails/*`).
- **`app/Config/Routes.php`** — rutas `/contacto` y `/solicitud`.
- **`app/Config/Email.php`** + **`.env`** — configuración SMTP.
- **`app/Config/Filters.php`** — CSRF + honeypot + throttle en las rutas POST.

---

## Cambios arquitectónicos

- Un controlador por formulario; patrón **PRG** (Post/Redirect/Get) tras el envío.
- Emails vía `service('email')` con vistas HTML como cuerpo.
- Anti-spam por honeypot + throttler (sin dependencias externas).

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `app/Controllers/ContactController.php` | Crear | Form contacto + envío notificación |
| `app/Controllers/QuoteController.php` | Crear | Form solicitud + envío confirmación |
| `app/Views/contact/form.php` | Crear | Vista formulario contacto |
| `app/Views/quote/form.php` | Crear | Vista formulario solicitud |
| `app/Views/emails/contact_notify.php` | Crear | Plantilla email notificación |
| `app/Views/emails/quote_confirm.php` | Crear | Plantilla email confirmación |
| `app/Config/Routes.php` | Modificar | Rutas de ambos formularios |
| `app/Config/Email.php` + `.env` | Modificar | Configuración SMTP |

---

## Dependencias y prerequisitos

- Proyecto CI4 inicializado (F1 antes que el resto).
- Servidor **SMTP** con credenciales (bloquea las fases de envío F2/F3 hasta tenerlo).

---

## Criterios de aceptación (global)

- [ ] `/contacto` y `/solicitud` responden `200` y renderizan sus campos.
- [ ] Envío válido → email enviado al destinatario correcto + mensaje de éxito (PRG).
- [ ] Envío inválido → vuelve con errores y **no** envía email.
- [ ] Honeypot relleno → descarta el envío sin filtrar que es bot.
- [ ] Todos los feature tests en verde.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Emails a spam | Media | Medio | SMTP con SPF/DKIM; remitente del dominio |
| Bots en formularios | Media | Bajo | Honeypot + rate-limit |
| SMTP no disponible a tiempo | Media | Alto | Configurar `.env` al inicio; mock en tests |

---

## Métricas de éxito

- Formularios operativos con tasa de error de validación razonable.
- Emails entregados correctamente (comprobado en buzón de prueba).

---

## Agregación de tiempo

- 2026-07-08: Creación del plan (`Tiempo consumido`: 0h).

---

## Changelog

- 2026-07-08: Plan creado a partir de [`evaluation.md`](evaluation.md) (aprobadas C-01 y C-02) y [`spec.md`](spec.md).
