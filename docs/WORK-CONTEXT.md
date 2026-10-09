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

`project-pieces.py` complementa ese registro con un inventario derivado de
declaraciones propias de proyecto y usuario. Planner elige hasta 20 IDs en
`Extensiones` y registra fuentes y motivo en `Procedencia de extensiones`.
El brief refresca la selección para el runtime declarado y transfiere solo
referencias acotadas; omite piezas borradas o de otro runtime con aviso.
Personas conservan su cascada por `Tipo`. No se modifica el catálogo del bundle
ni se crea otro registro persistente. [Carpetas, comandos y límites](PROJECT-EXTENSIONS.md).

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

Acota el artefacto a 8 MiB, 20.000 nodos, 50.000 relaciones y profundidad 32;
devuelve 1–50 nodos (default 6), una vecindad y recortes explícitos. `--symbol`
conserva búsqueda por texto; `--node-id` o `--source-file` con `--label` seleccionan
identidades exactas. No sigue symlinks/junctions ni convierte un ID ambiguo en match.

Sin recibo, declara frescura no verificada. Con un recibo ligado al SHA-256 del
artefacto, lee y verifica los bytes de todos sus inputs declarados: máximo 128
archivos, 1 MiB por input y 8 MiB acumulados, incluyendo sondas. Un cambio suprime
el contexto; una lectura incompleta declara parcialidad. No acredita cobertura
del repositorio, identidad del productor ni semántica. El productor explícito
`code-context-build.py` prepara el par AST/recibo con Graphify externo elegido por
el caller, sin instalarlo. Véase [el contrato completo](CODE_CONTEXT.md).

Graphify es un extractor externo opcional; ninguna dependencia, hook, servicio
o instalación global se añade por usar el lector. El productor genera un artefacto
AST y un recibo en destinos nuevos; rechaza cualquiera existente antes de importar el extractor.
Los crea exclusivamente, artefacto primero y recibo al final; el par no es atómico.
Un fallo de publicación puede dejar el artefacto sin recibo. No borra ni reemplaza
destinos finales al fallar; la siguiente build requiere un destino nuevo.
Evita instalar hooks obligatorios que sustituyan este workflow.
El piloto y su alcance están en el [informe](roadmap/2026-10-06-workflow-integration/testing/structural-pilot.md).

Journal mantiene continuidad de sesión, approved mantiene conocimiento gobernado
y knowledge-services publica lo aprobado. Esta consulta no genera piezas de
project-specialization ni introduce otro registro de piezas del consumidor.
