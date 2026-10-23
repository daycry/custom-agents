# Piloto local de contexto estructural

Ejecutado el 2026-10-06 sobre el checkout fijado
`5c7b84792f453582676548185aaec3824d51dfe2` (pyproject: graphifyy 0.9.77).
No se instaló el paquete/skill en los runtimes: se ejecutó el código del checkout
en un venv aislado con sus dependencias mínimas para los tres lenguajes.
La metadata de paquete del CLI aparece como unknown; la revisión identifica
la fuente ejecutada. No se activaron instaladores, MCP, hooks ni observadores.

Entrada: los tres archivos públicos de fixtures/code-context: PHP OrderService,
Python process_order/normalize_name y TSX OrderView/formatTotal. Comando:
`python -m graphify extract <fixture> --code-only`. Destino GRAPHIFY_OUT nuevo;
GRAPHIFY_NO_AUTO_REFRESH=1; variables de claves API retiradas del proceso.

Resultado real: exit 0; 3 archivos de código, 0 docs/papers/images; **9 nodos,
8 relaciones, 3 comunidades**. La copia graph.json del fixture es el artefacto
producido, con rutas relativas, sin paths del host. Las consultas del lector
propio tienen pruebas por los tres stacks y relaciones citadas.

Dependencias del piloto: networkx 3.7, numpy 2.5.3, rapidfuzz 3.14.6,
tree-sitter 0.25.2, tree-sitter-python 0.25.0, tree-sitter-javascript 0.25.0,
tree-sitter-typescript 0.23.2 y tree-sitter-php 0.24.1. Son herramientas de
desarrollo aisladas; el lector del plugin sigue siendo stdlib.

Esto acredita extracción y consulta de esos fixtures. No compara precisión de
memoria, resolución de agentes, latencia en un proyecto grande ni otras gramáticas.
No reemplaza memoria curada ni acredita cobertura/frescura de un grafo futuro.
