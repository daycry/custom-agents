---
spec: ci4-forms-emails
descripcion: App CodeIgniter 4 con 2 formularios públicos (contacto y solicitud de presupuesto) que envían email al enviarse (notificación al equipo y confirmación al usuario).
estado: aprobada
creado: 2026-07-08
actualizado: 2026-07-08
evaluacion: ./evaluation.md
plan: ./improvement-plan.md
---

# App CodeIgniter 4 — 2 formularios con envío de email

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md)

## Contexto y objetivo

Web corporativa en **CodeIgniter 4** que necesita captar contactos y peticiones. Se piden **dos formularios públicos**, y cada envío dispara **un email**:

1. **Formulario de contacto** → al enviarse, **notifica al equipo** por email.
2. **Formulario de solicitud de presupuesto** → al enviarse, envía un **email de confirmación (acuse)** al usuario con los datos recibidos.

Objetivo: capturar los datos de forma fiable (validación + anti-spam) y comunicar por email, reutilizando lo **nativo** de CI4 (sin dependencias extra).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Framework | **CodeIgniter 4** (rama 4.x actual) | Requisito del proyecto. |
| Envío de email | **Servicio Email nativo de CI4** vía SMTP | Cubre el caso sin librerías de terceros; credenciales fuera del repo. |
| Validación | **Validation de CI4** (reglas server-side) + **CSRF** activo | Seguridad y datos limpios sin reinventar nada. |
| Anti-spam | **Honeypot** + **rate-limit** (Throttler) | Frena bots sin fricción; captcha externo queda fuera de esta iteración. |
| Plantillas de email | **Vistas HTML** dedicadas renderizadas con `view()` | Emails mantenibles y con formato. |
| Configuración | **SMTP en `.env`** | No versionar credenciales. |
| Estructura | **Controladores + vistas por formulario**, rutas explícitas | Simple y claro para 2 formularios. |

## Configuración (claves)

| Parámetro | Dónde | Valor |
|---|---|---|
| Credenciales SMTP | `.env` (`email.SMTPHost/SMTPUser/SMTPPass/SMTPPort`) | del proveedor |
| `mailType` | `Config/Email` | `html` |
| Protocolo | `Config/Email` | `smtp` |
| CSRF | `Config/Security` / filtros | activado |
| Honeypot | `Config/Honeypot` + filtro | activado |
| Destinatario de contacto | `.env` (`CONTACT_TO`) | buzón del equipo |

## Arquitectura y componentes

- **`ContactController`** — `index()` (GET, muestra form) y `submit()` (POST, valida y envía notificación al equipo).
- **`QuoteController`** — `index()` (GET) y `submit()` (POST, valida y envía confirmación al usuario).
- **Vistas** — `contact/form`, `quote/form`, `emails/contact_notify`, `emails/quote_confirm`.
- **Rutas** — `GET/POST /contacto`, `GET/POST /solicitud`.
- **Servicio Email** nativo (`service('email')`), reglas en **Validation**, protección **CSRF** + **Honeypot** + **Throttler**.

## Flujo (por formulario)

**Contacto** (`/contacto`):
1. `GET` muestra el formulario (nombre, email, mensaje) con token CSRF y campo honeypot oculto.
2. `POST` valida (CSRF, reglas, honeypot). Si falla → vuelve al form con errores.
3. Si OK → envía **email de notificación al equipo** (`CONTACT_TO`) con los datos → mensaje de éxito / redirect (patrón PRG).

**Solicitud de presupuesto** (`/solicitud`):
1. `GET` muestra el formulario (nombre, email, empresa, detalle).
2. `POST` valida igual que contacto.
3. Si OK → envía **email de confirmación al usuario** (acuse con su petición) → mensaje de éxito / redirect.

## Alcance

- **Dentro (esta iteración):**
  - Proyecto CI4 con configuración de email (SMTP en `.env`).
  - 2 formularios con validación server-side, CSRF y honeypot.
  - 2 envíos de email con plantillas HTML (notificación y confirmación).
  - Mensajes de éxito/error en español y patrón PRG (redirect tras POST).
  - Rate-limit básico de envíos por IP.
  - Feature tests de ambos formularios (incl. mock de email).
- **Fuera (siguientes specs):**
  - Captcha externo (reCAPTCHA/hCaptcha).
  - Persistencia en BD de los envíos / panel de administración.
  - Cola de emails / envío asíncrono.
  - Adjuntos y plantillas de email definitivas de marketing.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Validación fallida | Vuelve al formulario con errores y datos rellenados; mensajes en ES. |
| Honeypot relleno (bot) | Se descarta el envío en silencio (respuesta de éxito neutra). |
| Fallo de SMTP | Se registra en log; al usuario, mensaje de "no se pudo enviar, inténtalo más tarde". |
| Exceso de envíos (rate-limit) | Se bloquea temporalmente con mensaje; evita abuso. |

## Pruebas

Feature tests (CI4 `FeatureTestTrait`), email en modo mock:
- Cada formulario responde `200` en `GET` y renderiza sus campos.
- `POST` válido → `redirect` de éxito y **email enviado** (mock) al destinatario correcto.
- `POST` inválido → vuelve con errores, **sin** enviar email.
- Honeypot relleno → no envía email y no filtra que es bot.

## Referencias

- CodeIgniter 4 — *Email*, *Validation*, *CSRF/Security*, *Honeypot*, *Throttler* (documentación oficial de la versión usada).

## Decisiones confirmadas (revisión del usuario · 2026-07-08)

1. **Solo SMTP nativo** de CI4, sin librerías de email de terceros. **Confirmado.**
2. **Anti-spam** = honeypot + rate-limit; captcha externo **diferido**. **Confirmado.**
3. Sin persistencia en BD en esta iteración (solo email). **Confirmado.**

## Supuestos

- (a) Hay un servidor SMTP disponible con credenciales para `.env`.
- (b) No se guardan los envíos en base de datos (se decide en una spec futura).
- (c) Los textos y plantillas de email son provisionales (contenido definitivo aparte).
