---
estado: analizado
fecha: 2026-10-06
reference_revision: ef648e01899ba3e8dc6371642deaaf64b4477775
reference_version: 2.2.3
graphify_revision: 5c7b84792f453582676548185aaec3824d51dfe2
graphify_version: 0.9.77
---

# Qué adoptar de catálogo de referencia y cómo encaja Graphify

La decisión es ampliar capacidades dentro de nuestra arquitectura: investigación
previa, catálogo visible y especialización técnica. Mantener la memoria curada,
el ledger y los dueños actuales. Graphify encaja como un grafo de fuentes del
proyecto; no hay evidencia para reemplazar la memoria actual ni afirmar mejor
recuperación en nuestro corpus.

Esta revisión inspecciona código de repositorios originales y documentación
oficial, no solo sus README. Clones fijados a las revisiones del frontmatter,
sin ejecutar instaladores, hooks, observadores o servidores de catálogo de referencia/Graphify.
Las pruebas de nuestro panel se registran en testing; no se atribuyen al upstream.

## Catálogo y capacidades

catálogo de referencia 2.2.3 contiene **68 agentes, 94 comandos y 293 SKILL.md** en el catálogo
principal. Estos números salen del árbol fijado, no de traducciones ni de
marketing. El tamaño del catálogo acredita amplitud, no eficacia de cada pieza.
Su paquete `reference-universal`
incluye ejecutables, adaptadores y recursos; una skill suelta no instala esos
ejecutables. Su licencia principal es MIT. Nuestra adaptación no copia su código.

El [inventario completo por pieza](catalog-inventory.md) enumera las 455 fuentes
y distingue la adaptación inicial de la evaluación individual pendiente. Esta
comparación arquitectónica no equivale a haber revisado o integrado todo el
catálogo. Las guías propias de Python/React no migran íntegramente sus skills.

| Componente | catálogo de referencia comprobado | Nuestro contrato | Decisión |
|---|---|---|---|
| Agentes | Roles por lenguaje y oficio, además de planificación/revisión | Roles estables con un artefacto y dueño por responsabilidad | Mantener roles; incorporar criterio específico como skills |
| Skills | Catálogo amplio y especialización de dominio | Skills cortas con referencias y carga pertinente | Añadir guías acotadas para los tres stacks elegidos |
| Tools | CLI, MCP y herramientas externas; requieren dependencias reales | Kits stdlib, conectores disponibles y red opt-in | Mostrar tools declaradas y distinguir disponibilidad real |
| Commands | Entradas de usuario y coordinación de capacidades | Orquestación con ledger y puertas explícitas | Añadir plugin-catalog; conservar pm/dev/QA actuales |
| Hooks | Bootstrap, perfiles y dispatcher; observación/aprendizaje opcionales | Hooks portables e informativos; guardia con alcance de agente | Conservar arreglo actual; evaluar perfiles y diagnóstico como delta |
| Workflows | Guías y flujos por dominio | Cadena presupuestable, revisión independiente y QA mecánico | Enriquecer etapas actuales; no instalar un segundo orquestador |
| Evals | Harness offline y otras superficies de evaluación | Activación, contratos y casos Gold separados de entrenamiento | Piloto de resultados con corpus propio antes de comparar scores |

`search-first`
aporta una comparación adoptar/extender/construir y preflight de canales.
Lo adaptamos como research-first: analyst y architect mantienen su responsabilidad,
sin nuevo researcher obligatorio. Un canal inaccesible no se transforma en «no existe».

`skill-stocktake`
es una referencia para auditar utilidad y solapes. Nuestro panel no sustituye esa
auditoría semántica: mide inventario, no calidad, uso real ni vigencia de APIs.

## El control panel no es una sola pieza

| Superficie catálogo de referencia | Implementación observada | Encaje |
|---|---|---|
| Catálogo web | scripts/dashboard-web.js: agentes, skills, comandos, reglas, MCP y hooks; búsqueda, filtros e idiomas; servidor loopback con guardas Host/Origin | Adoptar navegación del catálogo; HTML autónomo elimina la necesidad de servidor para esta función |
| Dashboard desktop | panel de escritorio: Tkinter, catálogo, tema/ruta, refresco y apertura de docs/terminal | No añadir Tkinter ni fallback de agentes ficticios cuando falta el directorio |
| Control plane | control-plane/, implementación Rust descrita como alpha | Referencia para operación futura; no dependencia del plugin actual |
| Observabilidad de readiness | scripts/operator-readiness-dashboard.js y módulos de evolución | Separar señales reales de configuración/presencia; pilotar antes de mostrar salud |

Fuentes: `web`,
`desktop`,
`control-plane`.
El desktop incluye agentes de ejemplo como fallback si no encuentra fuentes;
nuestro inventario vacío se mantiene vacío, con evidencia de lo que se leyó.

El panel propio muestra catálogo y hooks globales. Las guardias de agente siguen
en sus definiciones. Los tools son los declarados, no un inventario autenticado
de conectores en esta sesión. Presencia de archivos de Claude/Codex/OpenCode no
demuestra ejecución. La memoria se representa por presencia de fuentes, sin
exportar sus contenidos. El progreso de tareas sigue en roadmap-dashboard.

## Memoria: cuatro capas diferentes

Graphify y **Graphiti** son proyectos distintos. Ya tenemos un adaptador Graphiti
en [knowledge-services](../../../skills/knowledge-services/backends/README.md):
proyecta conocimiento aprobado y permite recuperación según configuración y modo
del proyecto. No extrae automáticamente el AST del repositorio. Graphify aportaría
ese grafo estructural de fuentes en una superficie de consulta separada.
Conservar ambos solo tendría sentido si el piloto demuestra utilidad distinta;
la presencia del adaptador no acredita que Graphiti esté activado en este proyecto.

| Capa | custom-agents | catálogo de referencia | Graphify |
|---|---|---|---|
| Retoma de trabajo | Captura/journal durable, replay y handoff | Persistencia de sesión y Memory Vault portable | No es el objetivo principal del grafo de código |
| Conocimiento con autoridad | Knowledge Gate, aprobado, procedencia, routing y revocación | Vault unreviewed/context; documentos gobernados separados; no autopromoción | Relaciones y reflexiones no equivalen a conocimiento aprobado |
| Contexto estructural | Búsqueda local, referencias y backends opcionales | Recuperación contextual y MCP del vault | AST entre archivos, rutas, dependencias, comunidades y query/path/explain |
| Aprendizaje de resultados | Casos y validación explícita; Gold humano; candidatos de memoria | Observaciones/instincts por proyecto; observer desactivado por defecto | save-result y reflect; señales temporales por nodo en sidecar |

Fuentes propias: [memoria](../../../agent-kits/shared/knowledge-write.md), [servicios](../../../skills/knowledge-services/SKILL.md),
[casos](../../../skills/training-data-services/SKILL.md). Un servicio externo es
opcional; su configuración y alcance pertenecen al consumidor.

### catálogo de referencia Memory Vault

`unified-memory`
documenta Markdown catálogo de referencia.memory.v1 con scopes project/team/user. El runtime está
en `memory-vault.js`
y el MCP en memory-mcp.mjs. La instalación de la skill no instala el CLI/MCP.
El MCP permite guardar, buscar, leer y diagnosticar; no expone promoción a política.

Aspectos útiles: búsquedas acotadas, ID estable, procedencia, backlinks,
completitud de lectura explícita, scope de usuario solicitado expresamente,
restricciones de symlinks y rechazo de secretos sospechosos. El target-harness
es routing, no autenticación. Un resultado vacío y una búsqueda incompleta son
estados distintos. Estos contratos son mejores candidatos a mejorar recuperación
que reemplazar todo por una segunda base .catálogo de referencia/memory.

`continuous-learning-v2`
es otra superficie: observations/instincts y evolución de piezas. Su config
revisada tiene observer.enabled=false. Sus puntuaciones no son probabilidades
de verdad. Adoptar el modelo de observación como candidato requiere conservar
contraejemplos, procedencia y retirada, pasando por nuestro curator.

### Graphify: qué implementa realmente

Revisión [5c7b8479](https://github.com/Graphify-Labs/graphify/tree/5c7b84792f453582676548185aaec3824d51dfe2),
paquete **graphifyy 0.9.77**, CLI graphify; rama fuente v8.
El [pyproject](https://github.com/Graphify-Labs/graphify/blob/5c7b84792f453582676548185aaec3824d51dfe2/pyproject.toml)
requiere Python≥3.10, NetworkX, NumPy, RapidFuzz y múltiples gramáticas tree-sitter.
MCP, bases externas, documentos y modelos tienen extras propios. No cumple el
contrato stdlib de nuestros scripts como dependencia embebida; puede encajar
como herramienta externa opt-in en entorno aislado.

Su [arquitectura](https://github.com/Graphify-Labs/graphify/blob/5c7b84792f453582676548185aaec3824d51dfe2/ARCHITECTURE.md)
separa extracción, grafo, consultas y exportación. Código usa AST local; documentos
y medios pueden usar extracción semántica. EXTRACTED, INFERRED y AMBIGUOUS
permiten distinguir procedencia; ninguna etiqueta garantiza corrección universal.
El grafo es consultable sin vector store. Las conexiones entre archivos pueden
aportar análisis de impacto y navegación de cambios.

En [ingest.py](https://github.com/Graphify-Labs/graphify/blob/5c7b84792f453582676548185aaec3824d51dfe2/graphify/ingest.py),
save_query_result guarda pregunta, respuesta, nodos, outcome y corrección en
Markdown. Esa función no llama a nuestro redactor ni a nuestro Knowledge Gate.
Por tanto no la conectamos directamente a conversación o memoria privada.

[reflect.py](https://github.com/Graphify-Labs/graphify/blob/5c7b84792f453582676548185aaec3824d51dfe2/graphify/reflect.py)
agrega resultados useful/dead_end/corrected con decaimiento temporal y corroboración.
Es determinista para entrada y now fijos; escribe LESSONS y un sidecar de aprendizaje,
sin convertir esos campos en la verdad estructural del grafo. Puede orientar
recuperación, pero «preferred» no sustituye aprobación humana ni prueba de dominio.

El README distingue código local de semántica mediante modelo configurado. La
elección automática de backend por variables de entorno no es suficiente para
nuestro control de residencia: fijar backend o usar code-only. La CLI revisada
conserva una capa semántica preexistente en algunos rebuilds code-only; usar salida
nueva para un piloto que deba contener exclusivamente código público.

Licencia actual: Apache-2.0; NOTICE identifica porciones históricas MIT, retenidas
en LICENSE-MIT. Revisar atribución por archivo al reutilizar material. En esta
entrega no se copia ni distribuye código Graphify.

## Decisión sobre sustitución

**Conservar la memoria actual.** Graphify es candidato a complementar contexto
estructural, especialmente dependencias, análisis de impacto y navegación. catálogo de referencia
aporta contratos útiles para completitud y scopes, pero una segunda memoria
gobernada por otro mecanismo complicaría aprobación, privacidad y revocación.

No convertir automáticamente graph.json, LESSONS o instincts en nuestra carpeta
approved. Primero medir. Si el piloto mejora tareas reales, añadir una superficie
de consulta estructural independiente; no tratarla como publicador de conocimiento
aprobado ni migrar el journal. El adaptador de servicios actual sigue atendiendo
solo entradas aprobadas, no el repo entero.

## Piloto Graphify definido

1. Entorno separado, versión/revisión fija y corpus pequeño de código público
   PHP/CI4, Python y React. GRAPHIFY_OUT nuevo y fuera de Git; code-only, sin
   auto-refresh de skills ni instalación de MCP en configuraciones del usuario.
2. Preguntas con respuestas comprobables: llamadas/dependencias, cambios que
   afectan un contrato y camino entre dos símbolos. Comparar rg/búsqueda actual
   con grafo sobre la misma revisión. No evaluar con sus benchmarks publicitarios.
3. Medir aciertos, fuentes relevantes recuperadas, omisiones, tiempo de consulta,
   coste de reconstrucción y tamaño; marcar cada cifra con método y muestra.
4. Cambiar/renombrar/eliminar una fuente y actualizar. Confirmar ausencia de nodos
   obsoletos y aislamiento entre proyectos, symlinks, revocación y límites de salida.
5. Aceptar integración si aporta consultas útiles con procedencia y actualización
   correctas, sin pérdida de privacidad; dejar degradación a búsqueda actual.

Esto define el experimento; no afirma que se haya ejecutado ni promete porcentajes
de mejora. No se necesita una cuenta comercial para evaluar AST local; los extras
y la plataforma alojada se evalúan por separado si se solicita su uso.

## Qué se integra ahora y qué sigue

### Matriz de la entrega por runtime

La fuente de instalación e invocación es [INTEROP](../../INTEROP.md). Las piezas
traducidas se generan con [export-interop.py](../../../scripts/export-interop.py).

| Capacidad | Claude Code | Codex | OpenCode | Evidencia y límite |
|---|---|---|---|---|
| research-first y guías de stack | Skills del plugin; activación por descripción o solicitud | Skills del plugin; solicitud `$research-first` o activación por descripción | Skills en `.opencode/skills/` o compatibilidad `.claude/skills/` | Cinco SKILL.md originales, validator/evals; se cargan según tarea, no todas al inicio |
| Roles enriquecidos | Fuente `agents/*.md` | Traducción `.toml` en `interop/codex/agents/` | Traducción `.md` en `interop/opencode/agents/` | `--check` valida generación, no ejecución de agentes en tres sesiones reales |
| Consulta web de analyst/architect | WebFetch/WebSearch declaradas | Usar canales web disponibles en la sesión; nombres Claude no garantizan herramientas nativas equivalentes | Exporta permisos webfetch/websearch de lo declarado | Un permiso o una instrucción no instala ni habilita un proveedor de búsqueda |
| plugin-catalog | `/custom-agents:plugin-catalog`; `/plugin-catalog` en modo copy | Prompt exportado; convención `/prompt:plugin-catalog` o `/prompts:plugin-catalog` según versión, sin asumir slash command nativo del plugin | `/plugin-catalog` desde commands exportado | Los tres invocan el mismo script con Python nativo; HTML/JSON probado directamente en Windows/Linux |
| Hooks | `hooks/hooks.json` y guardias propias de agente | Subconjunto `interop/codex/hooks.json`, SessionEnd de 3 s | Adaptador `custom-agents-hooks.js`; captura en session.idle con límites de inyección propios | Se conservan los contratos de hooks-runtime; el panel solo muestra presencia de fuentes |
| Memoria/Graphify | Knowledge Gate y backends del consumidor | Mismos scripts y configuración de proyecto | Mismos scripts y configuración de proyecto | Ninguna instalación ni migración Graphify en esta entrega; aprobado y grafo estructural permanecen separados |

Las pruebas de navegador validan el HTML local. No se presentan como pruebas E2E
de instalación, ejecución de hooks o herramientas web en Claude/Codex/OpenCode.

| Decisión | Entrega o siguiente evidencia |
|---|---|
| Adoptar investigación previa | research-first; analyst/architect bajo demanda |
| Adoptar navegación de capacidades | plugin-panel y plugin-catalog, implementación stdlib propia |
| Ampliar criterio en los tres stacks | codeigniter-practices, python-practices, react-practices; roles actuales |
| Mantener hooks arreglados | Contratos runtime ya verificados en hooks-runtime; no observador nuevo |
| Conservar memoria curada | Journal/Knowledge Gate/routing; Graphify complementario pendiente del piloto |
| Entregar packs automáticos | project-specialization F2, sin instalar mecanismo alternativo |
| Mejorar recuperación y completitud | Consultas representativas y estados incompleto/vacío antes de cambiar router |
| Ampliar evals de resultados | Benchmark separado de casos de entrenamiento; repetibilidad y coste medidos |
| Control plane operativo | Diseñar dentro de project-dashboard tras definir señales reales; Rust alpha no embebido |

La primera entrega añade capacidades concretas. La paridad profesional se evalúa
por contratos, fiabilidad y resultados en nuestros proyectos; copiar la cantidad
de piezas de catálogo de referencia no constituye ese criterio.
