---
generacion:
  inicio: 2026-11-26T13:31:13Z
  fin: 2026-11-26T13:40:04Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-cd94633ced8243f48affbe87b2fe5fdb
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 58, salida: 31286, cache_creacion: 106000, cache_lectura: 3840457 }
  eur: 1.77
  horas_ia: 0.26
  duracion: 16m
  ratio_usado: 531798.5
---

# 2026-11-26-kairos-memory

> Evaluación de la integración opcional del plugin con Kairos como memoria de los agentes (cliente MCP genérico + adaptador `kairos` incluido, apagado hasta `/setup`): coste, riesgo y veredicto para la puerta go/no-go del usuario.

| | |
|---|---|
| **Fecha** | 2026-11-26 |
| **Estado** | completado (go del usuario, 2026-11-26: diseño ya; implementación tras fusionar plugin-audit-2) |
| **Prioridad global** | Alta |
| **Solicitante** | Usuario (dueño del plugin), con la sesión «kairos» como validadora del contrato |
| **Spec** | [`spec.md`](spec.md) (estado `aprobada`, 29 criterios) |
| **Plan** | pendiente (handoff a planner) |
| **Características evaluadas** | 8 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano equivalente | **146,4 h** (122 h base +20 %) | Baja (las horas humanas nunca se han validado en este repo: aprendizaje 2 de `CALIBRATION.md`) |
| Tiempo IA (ejecución) | **60 h** (50 h base +20 %: 18,5 h implementar + 31,5 h revisión y corrección) (+ 15 h supervisión) | Media-Baja (histórico de adaptadores de red: +53 % a +761 % sobre lo estimado) |
| Coste de referencia (humano equivalente + tokens + proceso) | **7.590 €** | Media (dominado por la tarifa × horas humanas, que es un supuesto) |
| Coste previsto del ciclo agéntico (tokens + proceso + supervisión) | **≈ 1.020 €** | Baja |
| Tokens IA | **≈ 31,9 M facturables** (in 29,4 M / out 2,55 M) + ≈ 383 M de lectura de caché | Baja |
| Multiplicador productividad | **×1,95** | — |
| Características | **8** | — |

---

## Resumen ejecutivo

La spec aprobada pide un cliente MCP genérico sin dependencias, el primer adaptador incluido del marco `knowledge-services` (Kairos), publicación idempotente de `approved/` con generaciones y lápidas, envío episódico (journal e hitos) con dos outbox, redacción previa ampliada y la integración en `/setup`, `/doctor`, `/dev-cycle` y `/retro`, multi-runtime. Se presupuesta en **122 h humanas base (146,4 h con margen)** y **60 h de IA con margen**, de las que **casi dos tercios son revisión y corrección**: así se comportaron todas las iniciativas comparables (`graphiti-memory`, `knowledge-services`, `training-data-services`, `session-end-durable-capture`). Veredicto: **go condicionado** a (1) partir de `plugin-audit-2` cerrado y fusionado (4.0.0 aún sin publicar) y (2) un paso de diseño con `architect` antes de implementar.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Cliente MCP genérico + servidor MCP falso + clasificador de errores | spec §Arquitectura (fila «Cliente MCP genérico»), §Manejo de errores, §Configuración (topes y plazos); CA-03, CA-15, CA-23, CA-25, CA-28 (plazos), CA-04 (parte de red) | Claro |
| C-02 | Adaptador `kairos`: 6 funciones, salud por capacidad y lectura | §Arquitectura (tabla de capacidades), §Flujo 4-7; CA-04 (lectura), CA-10, CA-11, CA-16, CA-21 | Claro |
| C-03 | Publicación documental: identidad, generaciones, revocación, reconciliación | §Decisiones técnicas (identidad, evidencia), §Flujo 8-13; CA-05..CA-09, CA-22, CA-26 (documental), CA-28 | Claro; una incógnita (ID de decisión del curator) |
| C-04 | Envío episódico: journal (`session-summary.v1`) e hitos (`observation.v1`) | §Flujo 14-19; CA-12, CA-13, CA-14, CA-24, CA-26 (episódico) | Claro; incógnitas de diseño (extracción de hitos, validador de esquema sin dependencias) |
| C-05 | Redacción previa para Kairos (`redact.py` ampliado) | §Decisiones técnicas (Redacción), decisión 7 del 2026-11-26; CA-19, CA-29 | Claro; heurística de seguridad |
| C-06 | Configuración y diagnóstico: `/setup`, `/doctor`, `capabilities.py` | §Flujo 1-5; CA-01, CA-02, CA-12 (ramas de `/doctor`), CA-21, CA-27 | Claro |
| C-07 | Integración en el ciclo, documentación, interop y no-regresión | §Arquitectura (`dev-cycle`/`retro`/`hooks`), §Alcance (Documentación); CA-01 (egress), CA-17, CA-18 | Ambiguo: superficie de la «orden manual» |
| C-08 | Integración real contra el servidor del usuario | CA-20, §Supuestos (calendario de Kairos) | Claro en el qué; depende de terceros en el cuándo |

**Ambigüedades / información que falta:**

- **`outbox.py` «reutilizado» frente a CA-04/CA-15.** La cola actual manda a dead-letter tras `MAX_INTENTOS = 3` con backoff lineal `BACKOFF_S × intento` (`agent-kits/shared/outbox.py:201-202`), y la spec pide «reencola con backoff propio **sin dead-letter**» y respetar `retry_after=N`. Casi seguro hace falta ampliar la cola (plazo explícito y clase «transitoria sin tope»), y es un contrato con consumidor existente (`knowledge-sync.py`). Supuesto: ampliación aditiva, incluida en C-03/C-04.
- **Evidencia del curator.** La spec dice «ID de la decisión del curator y sus fuentes»; `curator-gate.py` valida `evidencia` (nivel) y `fuentes` (lista), pero no se ha comprobado que la entrada aprobada conserve un ID de decisión trazable. Supuesto: se deriva de los metadatos de la entrada aprobada; si no existe, C-03 crece unas 3 h.
- **«Orden manual» de envío episódico.** No dice si es un comando nuevo (implica evals, interop, docs y espejo EN) o un subcomando de script. Supuesto: subcomando de script invocado desde `/dev-cycle` y `/retro`, sin comando nuevo.
- **Esquemas de Kairos sin `jsonschema`.** La constitución veta dependencias fuera de la stdlib (`docs/CONSTITUTION.md:21`): validar `session-summary.v1` y `observation.v1` exige un validador propio y una copia de los esquemas como fixture, que puede desalinearse con el repo knowledge-graphs.
- **Sufijo de los mensajes de cuota y de flujos** (`[code=… retry_after=N]`): solo el prefijo es contrato (§Supuestos de la spec). Se prueba contra el servidor falso.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (spec aprobada, validada tres veces contra el contrato 0.4.1; quedan las 5 ambigüedades menores listadas arriba)
- [x] **Alcance** de cada característica acotado (qué entra y qué NO)
- [x] **Criterios de aceptación / éxito** por característica (29 CA, 25 `[GWT]`)
- [x] **Restricciones** (constitución: stdlib, TDD, hooks sin red, red opt-in local/privada; multi-runtime; sin nombres retirados)
- [ ] **Dependencias externas** identificadas pero **sin fecha**: hitos A/B/C de Kairos y disponibilidad del usuario o de la sesión kairos para CA-20
- [x] **Contexto técnico** del proyecto disponible (recon de `skills/knowledge-services/`, `agent-kits/shared/`)
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`, precios verificados el 2026-10-20, 37 días: fiables)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` (`tarifaHora`) |
| Modelo IA asumido | claude-opus-5-5 | `.claude/rates.json` (`modeloIA`); desde 2026-11-26 Opus implementa y revisa |
| Precio input | 3,68 € / 1M tokens (4 USD) · escritura de caché 4,60 € (5 USD) · lectura de caché 0,18 € (0,2 USD) | `rates.json`, verificado el 2026-10-20 con `rates-verify` |
| Precio output | 18,40 € / 1M tokens (20 USD) | Ídem |
| Tipo de cambio | 1 USD = 0,92 € | **Supuesto** (`_nota_fx` de `rates.json`), no dato verificado |
| Margen de contingencia | 20 % | Sobre horas base humanas e IA |
| Supervisión | 25 % de las horas IA | `ratioSupervision` |
| Ratio tokens→hora | 531.798,5 tok/h | Mediana de 6 muestras de `CALIBRATION.md` (precedencia sobre el default de 300.000) |
| Reparto de tokens facturables | 92 % escritura de caché · 8 % salida · ≈ 0 % entrada sin caché | Supuesto a partir de las ventanas medidas del repo (la spec de esta iniciativa: 21,8 k salida sobre 451 k facturables) |
| Lectura de caché | ≈ 12 × los facturables | Supuesto: la ventana de la spec dio ×10,5 y la de `plugin-audit-2/tasks.md` ×34; se toma un valor bajo-medio |
| Revisión y corrección | línea propia por característica, ×1,5 a ×2 la implementación | `CALIBRATION.md`: `graphiti-memory` (×2,5 en adaptadores de red), `session-end-durable-capture` (cola y estado durable: 3 intentos por tramo), `panel-redesign` (heurísticas de seguridad: 4 rondas); doctrina LES-009 |

---

## Evaluación por característica

### C-01 — Cliente MCP genérico + servidor MCP falso + clasificador de errores

- **Requisito origen**: §Arquitectura, §Manejo de errores, §Configuración; CA-03, CA-15, CA-23, CA-25, CA-28 (plazos), CA-04 (red)
- **Descripción**: módulo Python stdlib que habla MCP *streamable HTTP* contra `<base>/mcp/` con `Bearer`, guardarraíl de host (local/privado; remoto solo `https` con `allow_remote`, sin redirecciones, sin proxy del entorno, sin IMDS ni enlace local), topes de 262.144 B de cuerpo y 1 MiB de respuesta, plazos de lectura y escritura, clasificación por `re.fullmatch` de ~40 mensajes y 10 códigos HTTP, `retry_after`, backoff y aviso de `Deprecation`. Incluye el servidor MCP falso en proceso que sostienen todas las `[GWT]`.
- **Complejidad**: Alta (red + seguridad + reloj inyectado; el falso es infraestructura de toda la iniciativa)
- **Esfuerzo**: 22 h · confianza Media
- **Previsión IA**: 9,0 h (3,0 implementar + 4,5 revisión, +20 %) · 4,40 M in / 0,38 M out tok (+57 M lectura de caché) · 38 €
- **Coste**: (22 h × 50 €/h) + 38 € = **1.138 €**
- **Impacto / áreas afectadas**: módulo nuevo del cliente (ubicación a decidir en diseño: `skills/knowledge-services/` o `agent-kits/shared/`), fixture del servidor falso nuevo en `skills/knowledge-services/scripts/`, `tests/test_hook_network_egress.py` (no debe cambiar su veredicto)
- **Dependencias y prerequisitos**: ninguna funcional; partir de `plugin-audit-2` fusionado (el cliente y el falso retirados no se reutilizan por nombre, CA-17)
- **Riesgos**: el guardarraíl de red es donde la revisión encontró evasiones en serie en `graphiti-memory` (suite de seguridad 20 → 63 tests en 3 rondas); la tabla de errores es larga y cualquier fila mal anclada es un falso éxito
- **Incógnitas / preguntas abiertas**: dónde vive el cliente para que lo reutilice otro MCP (CA-16) sin que el núcleo lo nombre

### C-02 — Adaptador `kairos`: 6 funciones, salud por capacidad y lectura

- **Requisito origen**: §Arquitectura (tabla de capacidades), §Flujo 4-7; CA-04 (lectura), CA-10, CA-11, CA-16, CA-21
- **Descripción**: `skills/knowledge-services/backends/kairos.py` con `health/plan/apply/verify/rebuild/revoke` + `puede_leer`/`consultar`; salud por capacidad con llamada real de solo lectura (`capture_policy`, `document_manifest(limit: 1)`), nunca `serverInfo.version`; lectura vía `knowledge-find.py --intent` con clave de lectura, aciertos marcados como dato no confiable y respaldo local; adaptador de fixture `mcp-fixture` que prueba la extensibilidad.
- **Complejidad**: Media
- **Esfuerzo**: 14 h · confianza Media
- **Previsión IA**: 6,0 h (2,0 + 3,0, +20 %) · 2,94 M in / 0,26 M out tok (+38 M lectura de caché) · 25 €
- **Coste**: (14 h × 50 €/h) + 25 € = **725 €**
- **Impacto / áreas afectadas**: `skills/knowledge-services/backends/kairos.py` (nuevo), `backends/README.md`, `agent-kits/shared/knowledge-find.py` (router `--intent`, línea ~1722; hotspot: 25 cambios en 90 días, 1.709 líneas de código)
- **Dependencias y prerequisitos**: C-01
- **Riesgos**: el contrato `verify` → `puede_leer`/`/doctor`/`--check` tiene varios consumidores; en `graphiti-memory` cada corrección reabrió el gap en el consumidor siguiente
- **Incógnitas / preguntas abiertas**: ninguna bloqueante

### C-03 — Publicación documental: identidad, generaciones, revocación y reconciliación

- **Requisito origen**: §Decisiones técnicas, §Flujo 8-13; CA-05..CA-09, CA-22, CA-26 (documental), CA-28
- **Descripción**: publicar solo `approved/` enrutado, con `content` redactado antes del hash, `document_id` UUIDv5 por generación, `source.uri` reconstruible, evidencia del curator, documento entero guardado en la outbox documental, confirmación por `document_status`, revocación con comprobación previa y regla de acceso de `Resource not found`, lápida → generación siguiente, `--check` paginado por `document_manifest` con `source_sha256`, `--rebuild`, entrega incierta y cambio de actor.
- **Complejidad**: Muy alta (estado durable, idempotencia estricta, entrega incierta)
- **Esfuerzo**: 26 h · confianza Baja-Media
- **Previsión IA**: 14,4 h (4,0 + 8,0, +20 %) · 7,05 M in / 0,61 M out tok (+92 M lectura de caché) · 61 €
- **Coste**: (26 h × 50 €/h) + 61 € = **1.361 €**
- **Impacto / áreas afectadas**: `backends/kairos.py`, `agent-kits/shared/outbox.py` (probable ampliación: plazo explícito y transitorio sin dead-letter), `skills/knowledge-services/scripts/knowledge-sync.py` (sin cambios de núcleo según la spec; a verificar), `tests/test_sync_write_gate.py`
- **Dependencias y prerequisitos**: C-01, C-02, C-05 (el hash se calcula sobre el texto redactado)
- **Riesgos**: los estados intermedios de la cola y de la entrega incierta son la familia que dio 5 de 6 Critical en `session-end-durable-capture` (LES-016); ampliar `outbox.py` cambia un contrato compartido
- **Incógnitas / preguntas abiertas**: si la entrada aprobada conserva un ID de decisión del curator (si no, +3 h); si `knowledge-sync.py` de verdad no necesita cambios para dos colas

### C-04 — Envío episódico: journal e hitos del ledger

- **Requisito origen**: §Flujo 14-19; CA-12, CA-13, CA-14, CA-24, CA-26 (episódico)
- **Descripción**: script determinista que, con `capture_allowed: true`, envía un `remember` por sesión (`session-summary.v1`) y uno por hito del ledger (`observation.v1`; tarea cerrada, veredicto de revisión o decisión, retro) con identidad por ocurrencia (`item_id` UUIDv5, `version: 1`), validación local de esquema y límites (1.000 nodos, profundidad 8, citas literales), outbox episódica separada, conciliación con `event_status` y estados terminales.
- **Complejidad**: Muy alta (parser de hitos sobre el ledger + validador de esquemas propio + cola durable)
- **Esfuerzo**: 24 h · confianza Baja-Media
- **Previsión IA**: 12,6 h (3,5 + 7,0, +20 %) · 6,16 M in / 0,54 M out tok (+80 M lectura de caché) · 53 €
- **Coste**: (24 h × 50 €/h) + 53 € = **1.253 €**
- **Impacto / áreas afectadas**: script nuevo de envío episódico, `agent-kits/shared/journal.py` (lectura de entradas), parsers existentes del ledger, `outbox.py`
- **Dependencias y prerequisitos**: C-01, C-05; reutiliza la ampliación de `outbox.py` de C-03
- **Riesgos**: contar ocurrencias de un hito sobre un ledger que se reescribe (reaperturas, ediciones manuales) es frágil; el validador de esquemas sin `jsonschema` y la copia de los esquemas pueden desalinearse con Kairos
- **Incógnitas / preguntas abiertas**: qué parser del ledger es la fuente de los hitos (reutilizar uno existente frente a uno nuevo); superficie de la «orden manual»

### C-05 — Redacción previa para Kairos (`redact.py` ampliado)

- **Requisito origen**: §Decisiones técnicas (Redacción), decisión 7 del 2026-11-26; CA-19, CA-29
- **Descripción**: parámetro de marcador en `redact.py` (fuente única de patrones); en lo que va a Kairos, sustituir el **valor completo** con esquema (`Authorization: [REDACTADO]`), añadir los patrones del hito B, ~22 nombres de secreto con camelCase y `.`/`-`, claves JSON dentro de cadenas y en `structured`, cadenas de alta entropía, y rechazar asignaciones con comilla sin cerrar. El journal local conserva `[secreto redactado]`.
- **Complejidad**: Alta (heurística de seguridad sobre código compartido)
- **Esfuerzo**: 12 h · confianza Media
- **Previsión IA**: 7,2 h (2,0 + 4,0, +20 %) · 3,52 M in / 0,31 M out tok (+46 M lectura de caché) · 30 €
- **Coste**: (12 h × 50 €/h) + 30 € = **630 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/redact.py` (408 líneas; hoy **conserva** el prefijo `Bearer `, `redact.py:315-322`, al revés de lo que pide CA-29) y sus consumidores (`journal.py`, hooks): code-health detecta un bloque duplicado de 239 líneas entre `journal.py:266` y `redact.py:34`
- **Dependencias y prerequisitos**: ninguna; conviene hacerla pronto porque C-03 y C-04 hashean sobre su salida
- **Riesgos**: cambiar la semántica para Kairos sin regresiones en el journal local (marcador y prefijo distintos por destino); el corpus de alta entropía da falsos positivos que cambian el hash; `panel-redesign` necesitó 4 rondas para cerrar un redactor heurístico
- **Incógnitas / preguntas abiertas**: cuándo publica Kairos `redaction-cases.json` (T-43); hasta entonces el test usa una copia de `_SECRET_NAME`/`_SAFE_VALUE` del servidor, que puede desalinearse

### C-06 — Configuración y diagnóstico: `/setup`, `/doctor`, `capabilities.py`

- **Requisito origen**: §Flujo 1-5; CA-01, CA-02, CA-12 (ramas de `/doctor`), CA-21, CA-27
- **Descripción**: paso guiado de `/setup` con validador sin red (`project_id`, URL, host permitido, claves fuera del proyecto), filas de `/doctor` por capacidad con veredicto y remedio (captura apagada, falta de `write`, 421/403 con `MEMORY_ALLOWED_ORIGINS`, `Deprecation`, «no verificable sin publicar»), dentro del tope de tiempo de `/doctor` y sin red con el backend desactivado.
- **Complejidad**: Media
- **Esfuerzo**: 12 h · confianza Media
- **Previsión IA**: 6,0 h (2,0 + 3,0, +20 %) · 2,94 M in / 0,26 M out tok (+38 M lectura de caché) · 25 €
- **Coste**: (12 h × 50 €/h) + 25 € = **625 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/doctor.py` (**hotspot n.º 1 del kit**: 48 cambios en 90 días, 2.667 líneas de código), `agent-kits/shared/capabilities.py`, `commands/setup.md`, `.claude/knowledge-services/taxonomy.json` (esquema del consumidor)
- **Dependencias y prerequisitos**: C-01 y C-02 para las filas en vivo; el validador de `/setup` no depende de nada
- **Riesgos**: conflictos de fusión en `doctor.py` con `plugin-audit-2` (en curso, toca el mismo fichero) y con cualquier otra rama; mensajes de remedio que la revisión encuentre inexactos frente al despliegue real
- **Incógnitas / preguntas abiertas**: ninguna bloqueante

### C-07 — Integración en el ciclo, documentación, interop y no-regresión

- **Requisito origen**: §Arquitectura (`dev-cycle`, `retro`, `hooks`), §Alcance (Documentación); CA-01 (egress), CA-17, CA-18
- **Descripción**: paso de envío episódico en `/dev-cycle` Fase 6 y `/retro`; `references/` (activar Kairos, añadir otro MCP de memoria), `backends/README.md` y `SKILL.md` (≤ 200 líneas; ya hay un adaptador incluido, revierte la política 4.0.0), CHANGELOG EN/ES, `export-interop.py` regenerado y `--check` en 0, evals de activación si cambia una `description`, barrido de nombres retirados.
- **Complejidad**: Baja-Media (prosa + gates)
- **Esfuerzo**: 8 h · confianza Alta
- **Previsión IA**: 3,6 h (1,5 + 1,5, +20 %) · 1,76 M in / 0,15 M out tok (+23 M lectura de caché) · 15 €
- **Coste**: (8 h × 50 €/h) + 15 € = **415 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md`, `commands/retro.md`, `skills/knowledge-services/SKILL.md`, `references/`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/`, `docs/FLOWS.md` (+ espejo EN) si cambia el flujo
- **Dependencias y prerequisitos**: C-02..C-06
- **Riesgos**: menores; tocar `commands/` obliga a regenerar interop y revisar evals
- **Incógnitas / preguntas abiertas**: si la «orden manual» es un comando nuevo (+2 h: evals, interop, docs y espejo EN)

### C-08 — Integración real contra el servidor del usuario

- **Requisito origen**: CA-20; §Supuestos (calendario de Kairos)
- **Descripción**: pasar la lista «Criterios de aceptación para el equipo consumidor» de `docs/integration.md` (repo knowledge-graphs) contra el servidor real, con versiones, IDs de prueba y resultados en `testing/` sin claves. La ejecutan el usuario o la sesión kairos; el plugin prepara el guion y recoge la evidencia.
- **Complejidad**: Media (poco código; mucha dependencia externa)
- **Esfuerzo**: 4 h · confianza Baja
- **Previsión IA**: 1,2 h (0,5 + 0,5, +20 %) · 0,59 M in / 0,05 M out tok (+8 M lectura de caché) · 5 €
- **Coste**: (4 h × 50 €/h) + 5 € = **205 €**
- **Impacto / áreas afectadas**: `docs/roadmap/2026-11-26-kairos-memory/testing/`
- **Dependencias y prerequisitos**: C-01..C-06 terminadas; servidor del usuario disponible; claves de lectura y escritura creadas por el usuario; captura del proyecto activada por un admin
- **Riesgos**: el hito B de Kairos (tasa por clave, cuota, redacción ampliada) cambia conducta visible y obliga a reconfirmar CA-15, CA-19 y CA-23 en real; si B no ha llegado, esas filas quedan «solo servidor falso» en el informe
- **Incógnitas / preguntas abiertas**: fecha de los hitos A/B/C (sin fechas; Kairos va por la fase 3 de 18)

---

## Comparativa

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Cliente MCP genérico + falso + errores | Alta | 22 h | 1.138 € | 4,79 M | Alta | Media |
| C-02 | Adaptador `kairos`: salud y lectura | Media | 14 h | 725 € | 3,19 M | Alta | Media |
| C-03 | Publicación documental | Muy alta | 26 h | 1.361 € | 7,66 M | Alta | Baja-Media |
| C-04 | Envío episódico (journal e hitos) | Muy alta | 24 h | 1.253 € | 6,70 M | Media | Baja-Media |
| C-05 | Redacción previa para Kairos | Alta | 12 h | 630 € | 3,83 M | Alta | Media |
| C-06 | `/setup`, `/doctor`, capacidades | Media | 12 h | 625 € | 3,19 M | Alta | Media |
| C-07 | Ciclo, docs, interop, no-regresión | Baja-Media | 8 h | 415 € | 1,91 M | Media | Alta |
| C-08 | Integración real (CA-20) | Media | 4 h | 205 € | 0,64 M | Media | Baja |
| | **Total (base, sin margen)** | | **122 h** | **6.352 €** | **31,9 M** | | |

Tokens = facturables (entrada + escritura de caché + salida) derivados de las horas IA con margen × 531.798,5 tok/h; el coste en € de la columna incluye además la lectura de caché estimada.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano equivalente, base) | 122 h × 50 €/h | 6.100 € |
| Margen de contingencia | +20 % sobre desarrollo base | 1.220 € |
| Tokens IA (input: escritura de caché + entrada) | 29,4 M tok × 5 USD/M × 0,92 | 135 € |
| Tokens IA (output) | 2,55 M tok × 20 USD/M × 0,92 | 47 € |
| Tokens IA (lectura de caché) | ≈ 383 M tok × 0,2 USD/M × 0,92 | 70 € |
| Coste de proceso (LES-008) | spec ya medida (3,25 €) + evaluación, diseño y plan estimados (≈ 4 + 8 + 6 €) | 18 € (estimado) |
| **Total estimado (con margen)** | | **7.590 €** |

**Lectura correcta de la cifra (LES-007):** los 7.320 € de desarrollo son el valor de referencia de **horas humanas equivalentes**; en este repo la ejecución es íntegra por agentes (filas de `CALIBRATION.md` con 0 h humanas reales). El desembolso previsto del ciclo agéntico es **≈ 1.020 €** = tokens (252 €) + proceso (18 €) + supervisión (15 h × 50 € = 750 €). Banda de tokens: 250-430 € (la cota alta aplica el coste por hora-IA medido en `training-data-services`, ≈ 7 €/h).

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 146,4 h (122 h base) |
| Horas IA (ejecución) | 60 h (50 h base: 18,5 h implementar + 31,5 h revisión y corrección) |
| Supervisión humana | 15 h (25 % de las horas IA) |
| **Horas totales (IA + supervisión)** | **75 h** |
| Horas ahorradas | 71,4 h |
| **Ahorro** | **48,8 %** |
| **Multiplicador de productividad** | **×1,95** |
| FTE equivalentes *(opcional)* | 0,45 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado. El multiplicador es bajo a propósito: el histórico del repo dice que en adaptadores de red con contratos de varios consumidores la revisión y la corrección cuestan entre 1,5 y 8 veces la implementación (`graphiti-memory` ≈ 16 h de 22,9 h; `training-data-services` ≈ 94 h de 106 h). Si la revisión converge en 2-3 intentos por fase, las horas IA bajan hacia 35-40 h.

---

## Recomendación

- **Veredicto**: **go condicionado** a dos requisitos de entrada:
  1. **`plugin-audit-2` cerrado y fusionado en `master`** (4.0.0 sigue en `[Unreleased]` y su ledger tiene 19 tareas en `borrador`): la spec asume la retirada de los backends anteriores, y las dos iniciativas tocan `doctor.py`, `knowledge-find.py`, `backends/__init__.py` y `test_hook_network_egress.py`.
  2. **Paso de diseño con `architect` (recomendado)** antes del plan, centrado en: máquina de estados de las dos outbox (entrega incierta, generaciones, ocurrencias, transitorio sin dead-letter y `retry_after` frente al `MAX_INTENTOS` actual de `outbox.py`); API de `redact.py` por destino (marcador y valor completo frente al prefijo que hoy conserva); ubicación del cliente genérico para CA-16; fuente de los hitos en el ledger; validador de esquemas stdlib y cómo se vendorizan los esquemas; superficie de la «orden manual». Motivo: el histórico muestra que un diseño fijado dentro del bucle de revisión produjo Critical (`knowledge-services`, `training-data-services`) y que las colas durables necesitan una tarea de diseño previa (`session-end-durable-capture`, LES-016). Coste: ≈ 1,5 h IA, ya incluido en la línea de proceso.
- **Quick wins** (bajo coste, alto valor): C-05 (redacción, independiente y prerequisito del hash) y el tramo de solo lectura C-01 + C-02 + C-06, que ya entrega lectura con la clave de lectura y `/doctor` sin escribir nada en Kairos.
- **Costosas / a valorar**: C-03 y C-04 (estado durable e idempotencia; el 50 % del esfuerzo y la mayor parte del riesgo de revisión).
- **Orden sugerido**: C-05 → C-01 → C-02 → C-06 → C-03 → C-04 → C-07 → C-08. La redacción y el cliente son cimientos; la lectura con `/doctor` da valor pronto y sin escritura; la publicación precede al envío episódico porque comparte la ampliación de `outbox.py`; la integración real va al final y puede esperar al hito B de Kairos.
- **Nivel de riesgo para el plan**: **alto** (`sdd-proporcional`): red, secretos, estado durable y contrato de terceros. Presupuestar 3 intentos de revisión por fase, con lente C (seguridad) en C-01, C-03, C-04 y C-05.
- **Fuera de alcance recomendado**: lo que la spec ya deja fuera; además, no condicionar el cierre a la llegada del hito B (CA-20 se cierra con lo que exista y reconfirma después).

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Bucle de revisión más largo que lo presupuestado (histórico: +53 % a +761 % en IA) | Alta | Alto | Diseño aprobado antes de implementar; 3 intentos por fase; Minor a deuda; 0 Critical/Important cierra la fase |
| Calendario de Kairos (hito A rotación de claves → 401 tras 24 h de gracia; hito B redacción ampliada, tasa por clave, cuota y tope de flujos; hito C `capabilities` en `/v1`) cambia conducta visible sin cambiar el contrato | Media | Medio | El cliente ya contempla 401/429/cuota; CA-15/19/23 contra el falso; CA-20 reconfirma en real; una spec de seguimiento por hito si cambia un mensaje |
| Deriva entre copias vendorizadas (esquemas `*.v1`, `_SECRET_NAME`/`_SAFE_VALUE`, mensajes de error) y el repo knowledge-graphs | Media | Medio | Fixtures con origen y fecha; `redaction-cases.json` (T-43) en cuanto exista; CA-20 como prueba de verdad |
| Conflictos con `plugin-audit-2` y otras ramas en hotspots (`doctor.py`, `knowledge-find.py`) | Alta si se arranca antes | Medio | Arrancar tras la fusión de `plugin-audit-2`; cambios en `doctor.py` acotados a una función por capacidad |
| Regresión de la redacción local o del journal al ampliar `redact.py` | Media | Alto | Marcador por destino; las suites actuales del journal y de los hooks siguen en verde sin tocar sus expectativas |
| Ampliar `outbox.py` rompe el contrato con `knowledge-sync.py` | Media | Alto | Ampliación aditiva con tests del consumidor existente; enumerar consumidores antes de cambiar el contrato (`graphiti-memory`) |
| Multi-runtime: Codex u OpenCode no ejecutan el paso de envío de `/dev-cycle`/`/retro` igual | Baja | Medio | Sin lógica por runtime; el envío es un script; `export-interop.py --check` en CI |
| CA-20 depende de terceros (servidor del usuario, claves, captura activada por un admin) | Media | Medio | Guion preparado por el plugin; la iniciativa no se bloquea: el informe distingue «verificado en real» de «solo falso» |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (crea `docs/roadmap/<fecha>-<slug>/` con `improvement-plan.md` + `tasks.md`). Indica qué características se aprueban para planificar (todas, o un subconjunto por orden de prioridad) y cualquier requisito de secuencia entre ellas. El `planner` heredará las horas y costes de esta evaluación por característica — no re-estima desde cero — y actualizará la fila **Plan** de esta evaluación y el campo `plan:` de la spec al crear el plan.

Propuesta para la puerta del usuario: aprobar **C-01..C-08** en el orden sugerido, con `architect` antes de `planner` y arranque tras la fusión de `plugin-audit-2`. Si se quiere acotar, un primer corte de solo lectura (C-05 + C-01 + C-02 + C-06 + la parte de C-07 que les toca) cuesta ≈ 68 h humanas base y ≈ 30 h IA con margen.
