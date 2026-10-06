# Contexto técnico del workflow

[English](en/WORK-CONTEXT.md) · **Español**

`/work-context` selecciona guías para la tarea sin iniciar otro ciclo. El mismo
método se utiliza en pm-cycle/dev-cycle y los roles manuales. El registro vive
en `agent-kits/shared/capability-catalog.json`; sus referencias se comprueban con
`python agent-kits/shared/capability-route.py --check` desde el repositorio.
En una instalación, resuelve el kit como indica capability-check.md.

El selector lee composer.json, package.json y pyproject.toml del paquete: máximo
128 KiB por manifiesto, profundidad 32, sin seguir enlaces ni ejecutar scripts.
Los marcadores CLOUD de OneDrive se admiten; junctions, symlinks y otros puntos
de reanálisis permanecen excluidos.
En Python 3.9/3.10, sin tomllib, el selector avisa del límite de lectura TOML;
la selección por JSON y filtros explícitos, el panel y los briefs continúan.
Node/TypeScript por sí solos no implican React. `--stack` declara tecnología de
la tarea y se distingue de la detección. Las áreas son filtros explícitos;
en monorepos selecciona el paquete, no todos los stacks de la raíz.

Planner registra IDs separados por comas en `- **Capacidades**:` y motivo en
`- **Procedencia de capacidades**:`. Los briefs incluyen punteros al mapa, sin
manuales completos. Architect/implementer/reviewer/qa comparten criterios y
escenarios, y explican cualquier delta por hechos nuevos en el ledger. La
selección no habilita herramientas ni reemplaza TDD, revisión, QA o Knowledge Gate.
Sin pieza opcional válida, avisa y sigue con el contrato de la tarea.

Las capacidades de stack están consolidadas en stack-practices; backend-practices,
frontend-quality y delivery-practices aportan criterios transversales. Capability-audit
evalúa utilidad/vigencia/solapes, mientras el panel enumera fuentes. Outcome-evals
prepara comparaciones reproducibles y agrega JUnit ya ejecutado; no anuncia eficacia
del agente a partir de un check de activación ni inventa consumo.

## Contexto estructural opcional

`code-context.py` consulta un grafo existente compatible con Graphify: nodos
`_origin: ast`, `file_type: code`, rutas relativas y source_location `L<n>`;
relaciones AST EXTRACTED con extremos y citas válidos. Acepta links o edges.
No incluye nodos semánticos/reflexiones como conocimiento aprobado.

Solo lee el artefacto: máximo 8 MiB, 20.000 nodos, 50.000 relaciones, profundidad
32; resultado de 1–50 nodos (default 6), una vecindad, truncado explícito.
No abre el contenido de archivos citados ni sigue symlinks/junctions. Las fuentes
deben existir dentro del paquete. Un artefacto grande/incompatible degrada con
exit 2 y conserva búsqueda rg/memoria local. No acredita cobertura completa ni
frescura: comprueba el código vigente antes de aplicar una relación.

Graphify es un extractor externo opcional; ninguna dependencia, hook, servicio
o instalación global se añade por usar el lector. Si se prepara un grafo code-only,
usa un destino nuevo: una reconstrucción sobre un grafo previo puede conservar
su capa semántica. Evita instalar hooks obligatorios que sustituyan este workflow.
El piloto y su alcance están en el [informe](roadmap/2026-10-06-workflow-integration/testing/structural-pilot.md).

Journal mantiene continuidad de sesión, approved mantiene conocimiento gobernado
y knowledge-services publica lo aprobado. Esta consulta no genera piezas de
project-specialization ni introduce otro registro de piezas del consumidor.
