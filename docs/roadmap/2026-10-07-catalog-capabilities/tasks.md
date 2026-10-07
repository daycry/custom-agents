---
tasks: catalog-capabilities
estado: en-progreso
creado: 2026-10-07
actualizado: 2026-10-07
verificacion: obligatoria
changelog: Changed
---

# Capacidades del catálogo — ledger

> Ledger canónico. Fuente única de progreso de la fase 3.

Autorización: integración por fases, decisiones técnicas delegadas y push
cuando esté listo. Base 6187b12; rama feat/catalog-capabilities. No PR,
integración en main ni release. Settings ajenos intactos y fuera del índice.
Meter privado abierto; sin respuestas compatibles no se inventa consumo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 1 | 7 | 14% |
| Fase 2 | 0 | 6 | 0% |
| Fase 3 | 0 | 3 | 0% |
| **TOTAL** | **1** | **16** | **6%** |

## Fase 1 — Comparación

**Estado**: en-progreso

### T-01 — Corpus y trazabilidad de la comparación

- **Estado**: completado
- **Descripción**: Reconciliar piezas principales, recursos y soporte del control panel; fijar IDs/hashes y distinguir inventario de evaluación.
- **Dependencias**: Primera y segunda fases publicadas.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`, `docs/roadmap/README.md`, `docs/INTEGRATION-ROADMAP.md`, `docs/en/INTEGRATION-ROADMAP.md`
- **Verificación**: build_catalog_corpus.py terminó con exit 0: 4.212 archivos reconciliados, 455 hashes principales coincidentes, 455 bundles estructurales, tres entradas y 30 archivos relacionados con paneles. corpus.json/corpus.md y audit-contract.md fijan evidencia y fichas; cero evaluadas semánticamente.
**Criterios de aceptación**:
  - [x] Los 455 hashes principales coinciden con revisión y registro privado/público de fase 1.
  - [x] Recursos y control panel reconciliados y vinculados al corpus, con fuentes privadas y nombres propios públicos.
  - [x] Alcance completo y fichas de comparación definidos sin simular revisión semántica.

### T-02 — Contratos por runtime y modo de instalación

- **Estado**: en-progreso
- **Descripción**: Contrastar esquemas y código de las versiones instaladas; resolver identidad, confianza, hooks y configuración OpenCode V2 antes de elegir mecanismos.
- **Dependencias**: T-01.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: OpenCode 2.0.12: fuente oficial fijada leída y carga nativa aislada ejecutada; adaptador V1 failed, control positivo active con hooks registrados, configuración V1/V2 normalizada y agentes de ambas formas cargados. Codex 0.160.1: esquema y constructor leídos, agent_id/agent_type opcionales en PreToolUse para ThreadSpawn, sin inferirlos de otro evento. runtime-probes.json/contracts.md conservan evidencia. Despacho/bloqueo, instrucciones efectivas, carga Codex y validación nativa Claude pendientes.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-03 — Comparación semántica de las 293 skills

- **Estado**: borrador
- **Descripción**: Leer cuerpos, recursos y callers de todas las skills; registrar contenido único y comparación concreta, incluyendo dominios técnicos y memoria.
- **Dependencias**: T-01.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: una ficha por ID, secciones comparadas, hashes, recurso/validación y contador de revisión completo.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-04 — Comparación de los 68 agentes

- **Estado**: borrador
- **Descripción**: Evaluar responsabilidades, procedimientos, permisos y resultados frente a roles propios; distinguir especialidad útil de duplicación de fase.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: fichas por ID con contratos y destinos; ninguna equivalencia basada solo en nombres.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-05 — Comparación de los 94 comandos

- **Estado**: borrador
- **Descripción**: Revisar intención, artefactos y despacho de comandos frente a los ciclos propios; identificar operaciones útiles y callers que cambiarían.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: fichas por ID, disparadores y escenarios positivos/negativos, con dueño por artefacto.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-06 — Tools, MCP, hooks, reglas y workflows

- **Estado**: borrador
- **Descripción**: Comparar configuración y scripts realmente usados, dependencias y API, ejecución, permisos y aislamiento; evaluar soporte del control panel.
- **Dependencias**: T-01/T-02.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: inventario de recursos reconciliado y fichas funcionales; validaciones no ejecutadas señaladas explícitamente.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-07 — Arquitectura y candidatos de memoria

- **Estado**: borrador
- **Descripción**: Comparar recuperación, aprendizaje, persistencia y gobierno frente a memoria propia; delimitar los experimentos que exige la fase 4.
- **Dependencias**: T-03/T-06.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: comparación de mecanismos y casos; no sustituir memoria ni declarar benchmark entregado.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Fase 2 — Integración

**Estado**: borrador

### T-08 — Diseño nativo de capacidades y workflow

- **Estado**: borrador
- **Descripción**: Convertir diferencias verificadas en destinos propios, opcionales y compartidos; cerrar diseño y acotar archivos antes de modificar producción.
- **Dependencias**: T-03/T-04/T-05/T-06/T-07.
- **Archivos**: `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: design.md con alternativas y trazabilidad por ID; criterios útiles conservados y responsabilidades no duplicadas.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-09 — Guardias y despacho nativo multi-runtime

- **Estado**: borrador
- **Descripción**: Implementar mecanismos reales por contrato y versión para Claude/Codex/OpenCode, incluido soporte V2; probar identidad, concurrencia y degradación.
- **Dependencias**: T-02/T-08.
- **Archivos**: `hooks/**`, `interop/**`, `agent-kits/shared/**`, `scripts/**`, `tests/**`, `agents/**`, `docs/**`
- **Verificación**: Pendiente: RED antes del código, pruebas propias de bloqueo/allow por rol y carga/despacho nativos, sin frontmatter ignorado como garantía.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-10 — Skills opcionales y consolidación de contenido

- **Estado**: borrador
- **Descripción**: Integrar contenido útil de las fichas con referencias y recursos propios; dominios existentes en el corpus, sin paquetes inventados ni carga indiscriminada.
- **Dependencias**: T-08/T-09.
- **Archivos**: `skills/**`, `agent-kits/shared/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: escenarios reales por alta/consolidación, recursos vigentes, tamaño y degradación; mapas sin duplicación ni pérdida.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-11 — Agentes, comandos y handoffs coherentes

- **Estado**: borrador
- **Descripción**: Integrar procedimientos útiles y despacho en roles/ciclos propios; compartir selección y conservar puertas, artefactos y extensiones del proyecto.
- **Dependencias**: T-08/T-09/T-10.
- **Archivos**: `agents/**`, `commands/**`, `agent-kits/**`, `interop/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: pruebas de transferencia entre fases, roles y briefs; exports al día y destinos de contenido comprobados.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-12 — Tools e integraciones bajo demanda

- **Estado**: borrador
- **Descripción**: Adaptar recursos ejecutables útiles y configuración MCP documentada al contrato propio, con opt-in y disponibilidad real, sin conectar cuentas por inventario.
- **Dependencias**: T-06/T-08/T-09.
- **Archivos**: `skills/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: fixtures propias, flags/APIs oficiales, permisos y ausencia de efectos del consumidor; instalación parcial comprensible.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-13 — Funciones operativas del panel nativo

- **Estado**: borrador
- **Descripción**: Incorporar funciones útiles del control panel comparado al panel propio, con fuentes, métricas observadas y guardias declaradas/contrastadas diferenciadas.
- **Dependencias**: T-06/T-08/T-09/T-10/T-11/T-12.
- **Archivos**: `skills/plugin-panel/**`, `commands/plugin-catalog.md`, `interop/**`, `evals/**`, `tests/**`, `docs/**`
- **Verificación**: Pendiente: Edge escritorio/móvil/teclado, filtros y navegación, privacidad y ausencia de datos, sin anunciar un snapshot como servicio vivo.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Fase 3 — Verificación y cierre

**Estado**: borrador

### T-14 — QA funcional, cobertura y revisión

- **Estado**: borrador
- **Descripción**: Verificar aceptación completa y eficacia observable por escenario, carga nativa, regresiones, cobertura y revisión independiente por fase.
- **Dependencias**: T-09/T-10/T-11/T-12/T-13.
- **Archivos**: `tests/**`, `evals/**`, `docs/roadmap/2026-10-07-catalog-capabilities/**`
- **Verificación**: Pendiente: Windows/Linux/Edge, cobertura del diff ≥90%, evidencia nativa y A+B con C/D según selector, cero gaps pendientes.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-15 — Limpieza, distribución y documentación

- **Estado**: borrador
- **Descripción**: Retirar recursos y callers sustituidos, refrescar dependencias/manifiestos/exports y docs ES/EN; comprobar referencias y nombres públicos.
- **Dependencias**: T-14.
- **Archivos**: `skills/**`, `agents/**`, `commands/**`, `agent-kits/**`, `scripts/**`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `.claude-plugin/**`, `docs/**`, `README.md`, `README.es.md`, `CLAUDE.md`, `tests/**`, `evals/**`
- **Verificación**: Pendiente: linter, exports, evals, manifiestos, tamaño, copias y scan de marca sin hallazgos; cero aliases vacíos o callers obsoletos.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

### T-16 — Retro, changelogs y publicación comprobada

- **Estado**: borrador
- **Descripción**: Cerrar consumo y resultados sin inventar métricas; sincronizar changelogs ES/EN y publicar la rama con contraste remoto, conservando fase 4 pendiente.
- **Dependencias**: T-15.
- **Archivos**: `docs/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: Pendiente: retro/report/ledger, changelog --check y SHA remoto observado; cierre documental publicado después de comprobar la entrega.
**Criterios de aceptación**:
  - [ ] Contrato y resultado de la tarea comprobados con evidencia ejecutada; límites y errores cubiertos.

## Evidencia inicial

TDD n/a: planificación y documentación. Reconciliación de hashes mediante
helper privado y lectura de corpus fijado; ningún script externo ejecutado.
455 hashes verificados: 293 skills/68 agentes/94 comandos. Cero piezas
evaluadas semánticamente en esta fase; decisiones anteriores no se promueven
a revisión completa. Recursos auxiliares reconciliados en corpus.json; sus
dependencias y utilidad todavía requieren lectura semántica.

Versiones obtenidas con --version: Codex CLI 0.160.1, Claude Code 2.1.287,
OpenCode 2.0.12. Fuentes oficiales abiertas en contracts.md. La prueba aislada
reproduce el rechazo del export V1 actual en OpenCode V2; el control positivo
carga y registra hooks, y se observa normalización de configuración V1/V2.
No acredita despacho ni bloqueo. Guardias y formatos se resolverán en T-02/T-09.

Comprobaciones de apertura ejecutadas: scope-check contra 6187b12, nueve
ficheros en alcance/cero fuera/cero avisos, settings ajenos excluidos;
ledger-lint cero incoherencias/cero avisos; linter cero errores/tres avisos
históricos; test_roadmap_index 50 passed; scan de nombres/contenido público sin
hallazgos y diff --check limpio. Son gates del plan, no de la implementación.

Comprobaciones del cierre de T-01 ejecutadas: ledger-lint cero incoherencias y
cero avisos; test_roadmap_index 50 passed (0,09 s); linter cero errores y tres
avisos históricos; scope-check 13 ficheros en alcance y cero fuera/avisos,
settings ajenos excluidos; scan público sin hallazgos. TDD n/a: documentación
e inventario de investigación; ningún cambio de producción en este hito.

Al añadir la evidencia nativa de OpenCode, scope-check conserva 13 ficheros
propios en alcance/cero fuera/cero avisos (14 cambiados contando settings
excluidos). El scan público sigue sin hallazgos. Los digests y agregados del
manifiesto y el enlace al método se contrastaron con el mapa privado: exit 0.
