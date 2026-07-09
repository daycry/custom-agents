# Checklist de Tareas — App CI4: 2 formularios + 2 emails

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | 2026-07-08 |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Horas (real/est) | Tokens (real/est) |
|------|------------|-------|----------|------------------|-------------------|
| F1 — Setup CI4 + email | 0 | 2 | 0% | 0 / 3h | 0 / 38k |
| F2 — Formulario de contacto | 0 | 3 | 0% | 0 / 6h | 0 / 102k |
| F3 — Formulario de solicitud | 0 | 3 | 0% | 0 / 7h | 0 / 115k |
| F4 — Anti-spam + UX | 0 | 2 | 0% | 0 / 2h | 0 / 40k |
| F5 — Tests | 0 | 2 | 0% | 0 / 3h | 0 / 75k |
| F6 — Documentación | 0 | 1 | 0% | 0 / 1h | 0 / 20k |
| **TOTAL** | **0** | **13** | **0%** | **0 / 22h** | **0 / 390k** |

---

## F1 — Setup CI4 + configuración de email

**Estado**: borrador · **Estimado**: 3h · **Real**: — · **Coste est.**: 150 € · **Tokens est.**: 38k

### T-01 — Inicializar proyecto CI4

- **Descripción**: crear el proyecto CodeIgniter 4, estructura base y `.env`.
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 10k in / 3k out tok · 0,3 €
- **Dependencias**: ninguna
- **Archivos**: `.env`, `app/Config/App.php`

**Criterios de aceptación**
- [ ] La app arranca (`php spark serve`) y responde en la home.

**Subtareas**
- [ ] `composer create-project codeigniter4/appstarter`
- [ ] Configurar `baseURL` y entorno en `.env`

### T-02 — Configurar servicio Email (SMTP)

- **Descripción**: configurar `Config/Email` + credenciales SMTP en `.env` (`mailType=html`, `protocol=smtp`).
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 20k in / 5k out tok · 0,5 €
- **Dependencias**: T-01
- **Archivos**: `app/Config/Email.php`, `.env`

**Criterios de aceptación**
- [ ] Un email de prueba se envía correctamente por SMTP.

**Subtareas**
- [ ] Rellenar credenciales SMTP en `.env`
- [ ] Ajustar remitente por defecto y `mailType`

---

## F2 — Formulario de contacto + email de notificación

**Estado**: borrador · **Estimado**: 6h · **Real**: — · **Coste est.**: 300 € · **Tokens est.**: 102k

### T-03 — Vista y ruta del formulario de contacto

- **Descripción**: vista `contact/form` (nombre, email, mensaje) con CSRF + honeypot, y ruta `GET /contacto`.
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 25k in / 7k out tok · 0,7 €
- **Dependencias**: T-01
- **Archivos**: `app/Views/contact/form.php`, `app/Config/Routes.php`

**Criterios de aceptación**
- [ ] `GET /contacto` responde 200 y muestra los campos.

**Subtareas**
- [ ] Maquetar el formulario con token CSRF
- [ ] Añadir campo honeypot oculto

### T-04 — Controlador y validación del envío

- **Descripción**: `ContactController::submit()` con reglas de Validation y patrón PRG.
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 30k in / 8k out tok · 0,8 €
- **Dependencias**: T-03
- **Archivos**: `app/Controllers/ContactController.php`

**Criterios de aceptación**
- [ ] Envío inválido vuelve al form con errores y sin enviar email.

**Subtareas**
- [ ] Definir reglas de validación
- [ ] Redirect con mensaje flash (PRG)

### T-05 — Email de notificación al equipo

- **Descripción**: plantilla `emails/contact_notify` y envío al buzón del equipo (`CONTACT_TO`).
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 25k in / 7k out tok · 0,7 €
- **Dependencias**: T-02, T-04
- **Archivos**: `app/Views/emails/contact_notify.php`

**Criterios de aceptación**
- [ ] Envío válido → email recibido en el buzón del equipo.

**Subtareas**
- [ ] Plantilla HTML del email
- [ ] Envío con `service('email')`

---

## F3 — Formulario de solicitud + email de confirmación

**Estado**: borrador · **Estimado**: 7h · **Real**: — · **Coste est.**: 350 € · **Tokens est.**: 115k

### T-06 — Vista y ruta del formulario de solicitud

- **Descripción**: vista `quote/form` (nombre, email, empresa, detalle) con CSRF + honeypot, ruta `GET /solicitud`.
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 25k in / 7k out tok · 0,7 €
- **Dependencias**: T-01
- **Archivos**: `app/Views/quote/form.php`, `app/Config/Routes.php`

**Criterios de aceptación**
- [ ] `GET /solicitud` responde 200 y muestra los campos.

**Subtareas**
- [ ] Maquetar formulario
- [ ] Añadir honeypot

### T-07 — Controlador y validación de la solicitud

- **Descripción**: `QuoteController::submit()` con Validation y PRG.
- **Estado**: borrador
- **Tiempo**: est. 2,5h · real —
- **Previsión IA**: 35k in / 9k out tok · 0,9 €
- **Dependencias**: T-06
- **Archivos**: `app/Controllers/QuoteController.php`

**Criterios de aceptación**
- [ ] Envío inválido vuelve con errores y sin enviar email.

**Subtareas**
- [ ] Reglas de validación
- [ ] Redirect con flash

### T-08 — Email de confirmación al usuario

- **Descripción**: plantilla `emails/quote_confirm` (acuse con los datos) y envío al email del usuario.
- **Estado**: borrador
- **Tiempo**: est. 2,5h · real —
- **Previsión IA**: 30k in / 9k out tok · 0,9 €
- **Dependencias**: T-02, T-07
- **Archivos**: `app/Views/emails/quote_confirm.php`

**Criterios de aceptación**
- [ ] Envío válido → el usuario recibe el acuse con su petición.

**Subtareas**
- [ ] Plantilla HTML del acuse
- [ ] Envío con `service('email')`

---

## F4 — Anti-spam + UX

**Estado**: borrador · **Estimado**: 2h · **Real**: — · **Coste est.**: 100 € · **Tokens est.**: 40k

### T-09 — CSRF + honeypot en las rutas POST

- **Descripción**: activar CSRF y filtro honeypot en `/contacto` y `/solicitud`.
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 15k in / 5k out tok · 0,5 €
- **Dependencias**: T-04, T-07
- **Archivos**: `app/Config/Filters.php`, `app/Config/Honeypot.php`

**Criterios de aceptación**
- [ ] Honeypot relleno → envío descartado sin filtrar que es bot.

**Subtareas**
- [ ] Habilitar CSRF
- [ ] Registrar filtro honeypot

### T-10 — Rate-limit y mensajes de UX

- **Descripción**: throttler por IP en los POST + mensajes flash de éxito/error.
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 15k in / 5k out tok · 0,5 €
- **Dependencias**: T-09
- **Archivos**: `app/Controllers/*`, vistas

**Criterios de aceptación**
- [ ] Superar el límite de envíos → bloqueo temporal con mensaje.

**Subtareas**
- [ ] Aplicar `throttler`
- [ ] Mensajes en español

---

## F5 — Tests

**Estado**: borrador · **Estimado**: 3h · **Real**: — · **Coste est.**: 150 € · **Tokens est.**: 75k

### T-11 — Feature tests del formulario de contacto

- **Descripción**: tests de GET/POST (válido e inválido) con email en modo mock.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 28k in / 10k out tok · 0,9 €
- **Dependencias**: T-05
- **Archivos**: `tests/Feature/ContactTest.php`

**Criterios de aceptación**
- [ ] POST válido → redirect de éxito y email enviado (mock).
- [ ] POST inválido → sin email, con errores.

**Subtareas**
- [ ] Configurar mock de email
- [ ] Casos válido/inválido/honeypot

### T-12 — Feature tests del formulario de solicitud

- **Descripción**: tests equivalentes para `/solicitud`.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 27k in / 10k out tok · 0,9 €
- **Dependencias**: T-08
- **Archivos**: `tests/Feature/QuoteTest.php`

**Criterios de aceptación**
- [ ] POST válido → acuse enviado (mock) al usuario.

**Subtareas**
- [ ] Casos válido/inválido/honeypot

---

## F6 — Documentación

**Estado**: borrador · **Estimado**: 1h · **Real**: — · **Coste est.**: 50 € · **Tokens est.**: 20k

### T-13 — README de uso y configuración

- **Descripción**: documentar rutas, variables `.env` de SMTP y cómo probar.
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 15k in / 5k out tok · 0,5 €
- **Dependencias**: T-10
- **Archivos**: `README.md`

**Criterios de aceptación**
- [ ] Un dev nuevo configura el SMTP y prueba ambos formularios siguiendo el README.

**Subtareas**
- [ ] Documentar `.env` y rutas
- [ ] Pasos de prueba

---

## Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._
