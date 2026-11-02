# Verificación técnica y entrega

La revisión adversarial se cerró en el intento 3, sin gaps pendientes. El cambio
final de producto coincide con el snapshot revisado. Los seis escenarios de UI
se ejecutaron tres veces en Edge headless: el gate final de QA conserva 18 pasan,
cero fallos, cero flaky y cero omitidos. El informe de QA conserva además el rojo
inicial del harness y su diagnóstico de autenticación.

## Python y contratos

- Gate oficial `coverage-gate.py --changed-only --min 90`: **92,58%** sobre los tres
  ficheros Python de producto modificados; 123 pruebas pasan y una se omite.
- Regresiones de actividad, interop, índice de roadmap e integridad del manual:
  **456 pasan, una omitida**, sin fallos ni errores.
- Linter, evals de activación, `export-interop.py --check` y `check-handbook.py`:
  exit 0. Se conserva el PDF publicado y su manifiesto original.
- Ledger y cobertura criterios→escenarios: exit 0, sin referencias rotas.

La cobertura se recogió en un contenedor Linux aislado, sin red. Se compararon
los bytes LF normalizados de los ficheros Python actuales con el artefacto medido.
El porcentaje no describe cobertura JavaScript ni sustituye las pruebas de UI.
El [recibo del gate](raw/coverage-gate.json) conserva el detalle por fichero.

## Límites de validación

La prueba real en una instancia de Edge headless encontró la sesión actual y
cinco sesiones Codex externas. La inspección de la pestaña personal de Edge
permanece pendiente por un bloqueo del puente de control; no se eludió.
Las cifras de actividad son observaciones, no pruebas de procesos vivos.
Los hooks no proporcionan consumo de tokens ni coste; el panel lo declara.

No se generaron candidatos de conocimiento que curar en esta iniciativa. Las
integraciones de conocimiento configuradas después pertenecen al proyecto local
y no forman parte de este diff, ni autorizan publicar documentos automáticamente.

## Entrega

Código: `54a780f` (`fix(console): show external sessions and readable agent activity`).
Documentación, evidencias y estados se entregan en un commit separado. La rama
se mantiene para la PR y la CI; completar tareas técnicas no equivale a fusionar.
