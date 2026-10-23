# Orquestadores de funcionalidad y MVP, publicación open source y aprobación de envíos — S193–S196

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **24.411 bytes/588 líneas** y los dos recursos de S194
(`approval-ledger.sql`, 14.330 bytes/230 líneas; `approval_claims.py`, 7.629 bytes/171
líneas), leídos completos. El motor `orch-pipeline` que envuelven S195–S196, los
agentes que encadena S193 y el test que cita S194 no viajan con ellas y no se leyeron.
[orch-opensource-approval-reading-evidence.json](orch-opensource-approval-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S195–S196 — Orquestar una funcionalidad nueva y construir un MVP

`1.803 bytes/45 líneas` y `2.399 bytes/49 líneas`. Envoltorios finos de un motor
común: clasifican el tamaño, ejecutan investigación → plan → (andamiaje) →
TDD → revisión → commit, con dos puertas (aprobación del plan y confirmación
antes del commit) y revisor de seguridad si se toca un disparador sensible. S196
parte de un documento de diseño, ordena **rebanadas verticales finas** (un camino
extremo a extremo primero) y delega la construcción en el bucle
generador-evaluador de S111.

**Comparación.** `/dev-cycle` es el único motor del plugin («no delega la
implementación en ningún orquestador externo») y ya tiene lo mismo con dueño:
puerta de entrada flujo completo frente a vía rápida (la decide el usuario,
no un clasificador opaco), OK del plan, TDD opt-in, revisión adversarial con
Lente C condicional por `review-lens-select.py` y commits por tarea; la vía
rápida en lenguaje natural es de `quick-implement`. Duplicarlo contradice ADR-011.
S196 hereda lo que S111 no adoptó: aprobar por una puntuación de modelo
(`--pass-threshold 7.0`) con hasta 15 iteraciones, frente a veredictos
deterministas y bucles acotados a 3. Usa commits `feat:` por rebanada, otra
convención que la de `T-XX:` del ledger.

Una idea útil no tiene dueño explícito: al construir algo desde cero, ordenar
las fases por rebanadas verticales finas en vez de «todos los modelos y luego
todas las vistas». **Destino:** una línea en `agents/planner.md` (orden de fases).
Lo demás, **sin destino**.

## S193 — Preparar un proyecto privado para publicarlo

`7.083 bytes/256 líneas`. Tres agentes en cadena: copia sin secretos ni
referencias internas, verificación con veredicto PASS/FAIL (secretos, datos
personales, referencias internas, ficheros peligrosos, configuración, historial)
y empaquetado (README, LICENSE, CONTRIBUTING, plantillas, `setup.sh`); publicación
en GitHub solo con aprobación y como máximo tres reintentos del verificador.

**Comparación.** El plugin tiene las piezas, no el flujo: `cybersecurity` busca
secretos, `agent-kits/shared/redact.py` redacta secretos evidentes,
`scripts/export-skills.py` genera un paquete portable que solo vacía una carpeta
si lleva su marca, y `delivery-practices` fija que «preparar una entrega no
autoriza publicarla». Publicar un proyecto no es un rol del ciclo. Defectos:

| Paso | Problema |
|---|---|
| La copia excluye `.git` y después «limpia el historial»; el verificador audita el historial | Sin `.git` no hay historial que limpiar ni auditar: pasos contradictorios o vacíos |
| Ante un secreto encontrado, «parametrizarlo» | No pide **rotarlo**: retirarlo de la copia no invalida una credencial que ya estuvo en el repositorio |
| `abort` borra la carpeta de staging | Sin comprobar que es una carpeta creada por el flujo (el exportador propio exige marca antes de vaciar) |
| Los tres agentes | No viajan con la pieza: el flujo no es ejecutable tal como se distribuye |

**Sin destino** como flujo. La línea «secreto encontrado = rotarlo, no solo
borrarlo» falta en `cybersecurity`: la rotación solo aparece en su matriz de
cumplimiento, no como acción ante un hallazgo del detector de secretos.

## S194 — Bucle de aprobación del operador para mensajes salientes

`13.126 bytes/238 líneas` más el esquema SQLite y el módulo de reclamaciones.
Cada borrador hacia una contraparte se archiva como obligación con el texto exacto
y su SHA-256; la decisión del operador queda ligada a la **época** del borrador
(reeditar invalida aprobaciones anteriores); una instantánea inmutable fija texto,
hash y destino; el envío pasa por una reclamación con estados
`claimed → dispatching → delivered | unknown` y un recibo con la coordenada del
mensaje. Un resultado `unknown` **nunca** se reintenta solo: requiere
reconciliación con evidencia. El aviso de archivo va solo a un destino interno
verificado, nunca a la contraparte.

**Comparación.** Dominio ajeno (comunicación con clientes y proveedores):
**fuera del bundle**, como el correo de S092. El método es la versión más
completa del patrón ya registrado en S096 («aprobación ligada a objeto, acción y
caducidad; revalidar antes del efecto»), con el elemento que allí faltaba: el
estado **incierto**. El esquema lo impone con triggers (instantáneas inmutables,
transiciones permitidas, congelación de registros con reclamación activa) y el
módulo nunca devuelve permiso dentro de una transacción del llamador. No se
encontró defecto en el código leído; no se ejecutó.

Contraste útil con piezas propias que producen efectos externos:

- `skills/jira-sync/scripts/jira-flow.py` anota la idempotencia **al generar el
  plan** («si no llegas a ejecutarlo, repite con `--force`»): un comentario que
  falla o expira queda como publicado, y `--force` puede duplicarlo si sí llegó.
  S194 separa intención, envío y recibo, y trata el desenlace dudoso como
  `unknown` que se reconcilia mirando el destino.
- `agent-kits/shared/outbox.py` re-encola tras un TTL lo que quedó en
  `processing/` al morir un proceso. Es correcto para materializadores
  idempotentes en destino; para un efecto que no lo sea, S194 muestra que el
  reintento automático tras un desenlace incierto no es seguro.

Defectos de la pieza: la aprobación automática por plazo (`auto_send_after`,
operador `auto-ttl`) convierte el silencio en aprobación, en tensión con su
primera frase («nunca enviar por su propio juicio»); el comando de validación
apunta a un test que no viaja con la skill.

**Destino:** extender el criterio de S096 en `delivery-practices` con el estado
incierto (un timeout tras enviar no autoriza reintentar; se reconcilia consultando
el destino), y proponer a `jira-sync` registrar el recibo del comentario (su
identificador) en vez de dar por publicado el plan generado. `outbox.py`: anotar
en su contrato que el re-encolado exige materializadores idempotentes en destino.
