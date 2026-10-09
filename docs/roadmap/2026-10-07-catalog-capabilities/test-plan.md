---
test-plan: catalog-capabilities
estado: aprobado
creado: 2026-10-07
---

# QA funcional y despacho nativo

- **P-01 [GWT]** Dado un proyecto con extensiones y stack declarado, al iniciar
  el ciclo se seleccionan capacidades pertinentes y se preservan IDs, fuentes,
  personas y responsabilidades entre planner, implementer, reviewer y qa.
- **P-02 [GWT]** Dado un implementer en cada runtime y modo soportado, una
  operación prohibida se rechaza antes de su efecto; la misma operación lícita
  del dueño de otro artefacto no se bloquea por una identidad global compartida.
- **P-03 [GWT]** Dadas sesiones concurrentes, raíz anidada, instalación parcial
  y política de hooks desactivada/no confiada, no se mezcla identidad de roles
  y se muestra el alcance real sin afirmar protección ausente.
- **P-04 [GWT]** Dado OpenCode V2, la carga nativa de configuración/plugin
  registra las acciones esperadas y despacha eventos; fixtures V1 conservadas
  solo cuando su soporte explícito sea requerido.
- **P-05 [GWT]** Dado un recurso nuevo o consolidado, su escenario positivo,
  negativo vecino, fallo de dependencia y ejemplo de uso producen resultados
  observados, sin asumir eficacia a partir de un check de descripción.
- **P-06 [GWT]** Dado el panel en escritorio/móvil/teclado, navegación y filtros
  muestran capacidades, origen, conflictos, guardias y métricas con fuentes
  comprensibles; ausencia de medición/conexión no se convierte en cero o éxito.
- **P-07 [GWT]** Dada una pieza retirada, sus criterios útiles tienen destino;
  no quedan callers, aliases vacíos, exports o documentación cargando lo anterior.

Las pruebas usan proyectos temporales propios. Antes de una prueba nativa se
contrasta el contrato y la versión; no se ejecutan servicios del consumidor ni
se altera su configuración. Escenarios concretos por capacidad se añaden a las
fichas y al informe QA antes de afirmar cobertura. El plan no acredita ejecución.

## Bloque 13 — Retoma dirigida

- **R-01 [GWT]** Dado un único ledger activo y journals de varias iniciativas,
  `resume` muestra el estado vigente y solo cita el historial seleccionado.
  Con varios ledgers activos muestra ambigüedad, sin elegir por orden de disco.
- **R-02 [GWT]** Dadas identidades exactas, desconocidas, repetidas o ausentes,
  los filtros combinados conservan su significado y no sustituyen una elección
  fallida por otra sesión. Runtime heredado permanece desconocido.
- **R-03 [GWT]** Dados archivos malformados, tipos YAML ajenos, UTF-8 inválido,
  enlaces, cambios observables o presupuestos agotados, el lector y selector
  devuelven estados explícitos sin filtrar excepciones ni afirmar ausencia.
- **R-04 [GWT]** Dado texto Unicode o sensible, la proyección respeta los topes,
  redacta la salida y declara si la identidad proyectada ya no es resoluble.
- **R-05 [GWT]** Dadas fixtures sintéticas completas o instalación parcial,
  API/CLI conservan el proyecto intacto y no llaman a meter, replay, Git o
  backends. El hook conserva su contrato separado y usa historial dirigido.

Suites: `test_local_read.py`, `test_journal_selection.py`, `test_work_resume.py`
y regresiones de progreso/journal/hooks. Windows valida los doubles reparse;
Linux ejecuta también los casos de enlaces nativos. Exports y evals verifican
la fachada común; estas pruebas no acreditan aceptación de hosts nativos.
Resultados y cobertura medida en `work-resume-evidence.json` tras la QA.
