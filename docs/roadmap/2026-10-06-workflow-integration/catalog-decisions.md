# Decisiones del catálogo y límites de la evaluación

Las 455 piezas de la revisión fijada tienen una decisión de **alcance o adaptación**,
no un score de calidad. Los IDs y hashes permiten cotejar la fuente en el registro
privado de investigación. Los nombres públicos son descriptivos y no introducen
namespaces ni alias externos en el plugin. Ninguna fuente se ejecuta por este mapa.

Las adaptaciones son acotadas: se revisaron secciones pertinentes, recursos y
contratos; no se importaron paquetes completos ni se auditó semánticamente todo
el cuerpo de las piezas excluidas. Las exclusiones no significan que las piezas
sean malas ni que nuestras guías cubran todos sus dominios.

| Decisión | Piezas |
|---|---|
| adaptación-acotada | 18 |
| fuera-alcance | 270 |
| mantener-contrato | 5 |
| sin-importar-comando | 94 |
| sin-importar-rol | 68 |

## Matriz de decisiones

| ID | Pieza | Decisión | Destino | Motivo |
|---|---|---|---|---|
| S001 | accessibility | adaptación-acotada | frontend-quality | Teclado, foco y pruebas manuales además de scanner; no se declara cobertura WCAG por inventario. |
| S002 | agent-architecture-audit | fuera-alcance | — | No se selecciona agent-architecture-audit para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S003 | agent-eval | adaptación-acotada | outcome-evals | Corpus fijado y checks comparables; no se instala el runner externo ni se generan costes de sesiones automáticamente. |
| S004 | agent-harness-construction | fuera-alcance | — | No se selecciona agent-harness-construction para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S005 | agent-introspection-debugging | fuera-alcance | — | No se selecciona agent-introspection-debugging para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S006 | agent-payment-x402 | fuera-alcance | — | No se selecciona agent-payment-x402 para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S007 | agent-self-evaluation | fuera-alcance | — | No se selecciona agent-self-evaluation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S008 | agent-sort | fuera-alcance | — | No se selecciona agent-sort para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S009 | agentic-engineering | fuera-alcance | — | No se selecciona agentic-engineering para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S010 | agentic-os | fuera-alcance | — | No se selecciona agentic-os para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S011 | ai-first-engineering | fuera-alcance | — | No se selecciona ai-first-engineering para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S012 | ai-regression-testing | fuera-alcance | — | No se selecciona ai-regression-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S013 | android-clean-architecture | fuera-alcance | — | No se selecciona android-clean-architecture para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S014 | angular-developer | fuera-alcance | — | No se selecciona angular-developer para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S015 | api-connector-builder | fuera-alcance | — | No se selecciona api-connector-builder para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S016 | api-design | adaptación-acotada | backend-practices | Errores, paginación, autorización e idempotencia; no se fuerzan envelopes, URL versioning o límites universales. |
| S017 | architecture-decision-records | fuera-alcance | — | No se selecciona architecture-decision-records para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S018 | article-writing | fuera-alcance | — | No se selecciona article-writing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S019 | automation-audit-ops | fuera-alcance | — | No se selecciona automation-audit-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S020 | autonomous-agent-harness | fuera-alcance | — | No se selecciona autonomous-agent-harness para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S021 | autonomous-loops | fuera-alcance | — | No se selecciona autonomous-loops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S022 | backend-patterns | fuera-alcance | — | No se selecciona backend-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S023 | benchmark | fuera-alcance | — | No se selecciona benchmark para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S024 | benchmark-methodology | fuera-alcance | — | La metodología observada trata posicionamiento/competencia comercial; no es un benchmark de agentes y queda fuera de este delta. |
| S025 | benchmark-optimization-loop | fuera-alcance | — | No se selecciona benchmark-optimization-loop para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S026 | blender-motion-state-inspection | fuera-alcance | — | No se selecciona blender-motion-state-inspection para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S027 | blueprint | fuera-alcance | — | No se selecciona blueprint para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S028 | brand-discovery | fuera-alcance | — | No se selecciona brand-discovery para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S029 | brand-voice | fuera-alcance | — | No se selecciona brand-voice para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S030 | browser-qa | fuera-alcance | — | No se selecciona browser-qa para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S031 | bun-runtime | fuera-alcance | — | No se selecciona bun-runtime para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S032 | canary-watch | fuera-alcance | — | No se selecciona canary-watch para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S033 | carrier-relationship-management | fuera-alcance | — | No se selecciona carrier-relationship-management para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S034 | cisco-ios-patterns | fuera-alcance | — | No se selecciona cisco-ios-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S035 | ck | fuera-alcance | — | No se selecciona ck para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S036 | claude-devfleet | fuera-alcance | — | No se selecciona claude-devfleet para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S037 | click-path-audit | fuera-alcance | — | No se selecciona click-path-audit para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S038 | clickhouse-io | fuera-alcance | — | No se selecciona clickhouse-io para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S039 | code-tour | fuera-alcance | — | No se selecciona code-tour para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S040 | codebase-onboarding | fuera-alcance | — | No se selecciona codebase-onboarding para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S041 | codehealth-mcp | fuera-alcance | — | No se selecciona codehealth-mcp para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S042 | coding-standards | fuera-alcance | — | No se selecciona coding-standards para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S043 | competitive-platform-analysis | fuera-alcance | — | No se selecciona competitive-platform-analysis para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S044 | competitive-report-structure | fuera-alcance | — | No se selecciona competitive-report-structure para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S045 | compose-multiplatform-patterns | fuera-alcance | — | No se selecciona compose-multiplatform-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S046 | config-gc | fuera-alcance | — | No se selecciona config-gc para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S047 | configure-reference | fuera-alcance | — | No se selecciona configure-reference para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S048 | connections-optimizer | fuera-alcance | — | No se selecciona connections-optimizer para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S049 | content-engine | fuera-alcance | — | No se selecciona content-engine para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S050 | content-hash-cache-pattern | fuera-alcance | — | No se selecciona content-hash-cache-pattern para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S051 | context-budget | fuera-alcance | — | No se selecciona context-budget para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S052 | continuous-agent-loop | fuera-alcance | — | No se selecciona continuous-agent-loop para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S053 | continuous-learning | mantener-contrato | knowledge-curator | No se convierten conversaciones/reflexiones en conocimiento aprobado ni se registra otro hook de aprendizaje. |
| S054 | continuous-learning-v2 | mantener-contrato | knowledge-curator | No se importan observers, confianza automática ni promoción global; candidatos conservan aprobación humana. |
| S055 | contract-first | fuera-alcance | — | No se selecciona contract-first para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S056 | cost-aware-llm-pipeline | fuera-alcance | — | No se selecciona cost-aware-llm-pipeline para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S057 | cost-tracking | fuera-alcance | — | No se selecciona cost-tracking para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S058 | council | fuera-alcance | — | No se selecciona council para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S059 | council-multi-model | fuera-alcance | — | No se selecciona council-multi-model para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S060 | counterparty-channel-discipline | fuera-alcance | — | No se selecciona counterparty-channel-discipline para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S061 | cpp-coding-standards | fuera-alcance | — | No se selecciona cpp-coding-standards para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S062 | cpp-testing | fuera-alcance | — | No se selecciona cpp-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S063 | crosspost | fuera-alcance | — | No se selecciona crosspost para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S064 | csharp-testing | fuera-alcance | — | No se selecciona csharp-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S065 | customer-billing-ops | fuera-alcance | — | No se selecciona customer-billing-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S066 | customs-trade-compliance | fuera-alcance | — | No se selecciona customs-trade-compliance para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S067 | dart-flutter-patterns | fuera-alcance | — | No se selecciona dart-flutter-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S068 | dashboard-builder | fuera-alcance | — | No se selecciona dashboard-builder para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S069 | data-scraper-agent | fuera-alcance | — | No se selecciona data-scraper-agent para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S070 | data-throughput-accelerator | fuera-alcance | — | No se selecciona data-throughput-accelerator para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S071 | database-migrations | adaptación-acotada | backend-practices | Coexistencia expand-contract, backfill y recuperación; se descarta la afirmación de DDL sin locks y se exige comprobar motor/versión. |
| S072 | deep-research | fuera-alcance | — | No se selecciona deep-research para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S073 | defi-amm-security | fuera-alcance | — | No se selecciona defi-amm-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S074 | delivery-gate | fuera-alcance | — | No se selecciona delivery-gate para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S075 | deployment-patterns | adaptación-acotada | delivery-practices | Artefacto real, orden de migración y recuperación; preparar no concede autorización de publicación. |
| S076 | design-system | fuera-alcance | — | No se selecciona design-system para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S077 | dev-team | fuera-alcance | — | No se selecciona dev-team para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S078 | django-celery | fuera-alcance | — | No se selecciona django-celery para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S079 | django-patterns | fuera-alcance | — | No se selecciona django-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S080 | django-security | fuera-alcance | — | No se selecciona django-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S081 | django-tdd | fuera-alcance | — | No se selecciona django-tdd para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S082 | django-verification | fuera-alcance | — | No se selecciona django-verification para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S083 | dmux-workflows | fuera-alcance | — | No se selecciona dmux-workflows para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S084 | docker-patterns | adaptación-acotada | delivery-practices | Build/runtime, secretos, arranque, readiness y señales; sin dependencias de infraestructura nuevas. |
| S085 | documentation-lookup | fuera-alcance | — | No se selecciona documentation-lookup para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S086 | dotnet-patterns | fuera-alcance | — | No se selecciona dotnet-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S087 | dynamic-workflow-mode | fuera-alcance | — | No se selecciona dynamic-workflow-mode para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S088 | e2e-testing | fuera-alcance | — | No se selecciona e2e-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S089 | reference-guide | fuera-alcance | — | No se selecciona reference-guide para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S090 | reference-recipes | fuera-alcance | — | No se selecciona reference-recipes para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S091 | reference-tools-cost-audit | fuera-alcance | — | No se selecciona reference-tools-cost-audit para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S092 | email-ops | fuera-alcance | — | No se selecciona email-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S093 | energy-procurement | fuera-alcance | — | No se selecciona energy-procurement para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S094 | enterprise-agent-ops | fuera-alcance | — | No se selecciona enterprise-agent-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S095 | error-handling | adaptación-acotada | backend-practices | Errores estructurados y retry según seguridad de operación; detalle interno redactado y gates actuales. |
| S096 | esign-field-placement | fuera-alcance | — | No se selecciona esign-field-placement para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S097 | eval-harness | adaptación-acotada | outcome-evals | Activación separada de resultados y agregación JUnit; no se afirma aislamiento de candidatos ni promoción por checks estáticos. |
| S098 | evm-token-decimals | fuera-alcance | — | No se selecciona evm-token-decimals para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S099 | exa-search | fuera-alcance | — | No se selecciona exa-search para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S100 | fal-ai-media | fuera-alcance | — | No se selecciona fal-ai-media para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S101 | fastapi-patterns | fuera-alcance | — | No se selecciona fastapi-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S102 | finance-billing-ops | fuera-alcance | — | No se selecciona finance-billing-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S103 | flox-environments | fuera-alcance | — | No se selecciona flox-environments para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S104 | flutter-dart-code-review | fuera-alcance | — | No se selecciona flutter-dart-code-review para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S105 | foundation-models-on-device | fuera-alcance | — | No se selecciona foundation-models-on-device para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S106 | frontend-a11y | fuera-alcance | — | No se selecciona frontend-a11y para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S107 | frontend-design-direction | fuera-alcance | — | No se selecciona frontend-design-direction para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S108 | frontend-patterns | adaptación-acotada | frontend-quality | Estados remotos, formularios e interacción; las piezas del proyecto conservan su diseño. |
| S109 | frontend-slides | fuera-alcance | — | No se selecciona frontend-slides para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S110 | fsharp-testing | fuera-alcance | — | No se selecciona fsharp-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S111 | gan-style-harness | fuera-alcance | — | No se selecciona gan-style-harness para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S112 | gateguard | fuera-alcance | — | No se selecciona gateguard para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S113 | generating-python-installer | fuera-alcance | — | No se selecciona generating-python-installer para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S114 | git-workflow | fuera-alcance | — | No se selecciona git-workflow para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S115 | github-ops | fuera-alcance | — | No se selecciona github-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S116 | golang-patterns | fuera-alcance | — | No se selecciona golang-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S117 | golang-testing | fuera-alcance | — | No se selecciona golang-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S118 | google-workspace-ops | fuera-alcance | — | No se selecciona google-workspace-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S119 | growth-log | fuera-alcance | — | No se selecciona growth-log para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S120 | healthcare-cdss-patterns | fuera-alcance | — | No se selecciona healthcare-cdss-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S121 | healthcare-emr-patterns | fuera-alcance | — | No se selecciona healthcare-emr-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S122 | healthcare-eval-harness | fuera-alcance | — | No se selecciona healthcare-eval-harness para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S123 | healthcare-phi-compliance | fuera-alcance | — | No se selecciona healthcare-phi-compliance para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S124 | hermes-imports | fuera-alcance | — | No se selecciona hermes-imports para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S125 | hexagonal-architecture | fuera-alcance | — | No se selecciona hexagonal-architecture para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S126 | hipaa-compliance | fuera-alcance | — | No se selecciona hipaa-compliance para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S127 | homelab-network-readiness | fuera-alcance | — | No se selecciona homelab-network-readiness para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S128 | homelab-network-setup | fuera-alcance | — | No se selecciona homelab-network-setup para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S129 | homelab-pihole-dns | fuera-alcance | — | No se selecciona homelab-pihole-dns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S130 | homelab-vlan-segmentation | fuera-alcance | — | No se selecciona homelab-vlan-segmentation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S131 | homelab-wireguard-vpn | fuera-alcance | — | No se selecciona homelab-wireguard-vpn para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S132 | hookify-rules | fuera-alcance | — | No se selecciona hookify-rules para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S133 | i18n-sync | fuera-alcance | — | No se selecciona i18n-sync para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S134 | inherit-legacy-style | fuera-alcance | — | No se selecciona inherit-legacy-style para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S135 | intent-driven-development | fuera-alcance | — | No se selecciona intent-driven-development para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S136 | inventory-demand-planning | fuera-alcance | — | No se selecciona inventory-demand-planning para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S137 | investor-materials | fuera-alcance | — | No se selecciona investor-materials para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S138 | investor-outreach | fuera-alcance | — | No se selecciona investor-outreach para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S139 | ios-icon-gen | fuera-alcance | — | No se selecciona ios-icon-gen para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S140 | iterative-retrieval | adaptación-acotada | agent-kits/shared/knowledge-check.md | Refinar consultas desde incógnitas/fuentes hasta tres pasadas; se descartan scores de relevancia inventados. |
| S141 | ito-baskets | fuera-alcance | — | No se selecciona ito-baskets para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S142 | ito-compute | fuera-alcance | — | No se selecciona ito-compute para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S143 | ito-inference | fuera-alcance | — | No se selecciona ito-inference para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S144 | ito-training | fuera-alcance | — | No se selecciona ito-training para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S145 | java-coding-standards | fuera-alcance | — | No se selecciona java-coding-standards para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S146 | jira-integration | fuera-alcance | — | No se selecciona jira-integration para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S147 | jpa-patterns | fuera-alcance | — | No se selecciona jpa-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S148 | knowledge-ops | fuera-alcance | — | No se selecciona knowledge-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S149 | kotlin-coroutines-flows | fuera-alcance | — | No se selecciona kotlin-coroutines-flows para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S150 | kotlin-exposed-patterns | fuera-alcance | — | No se selecciona kotlin-exposed-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S151 | kotlin-ktor-patterns | fuera-alcance | — | No se selecciona kotlin-ktor-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S152 | kotlin-patterns | fuera-alcance | — | No se selecciona kotlin-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S153 | kotlin-testing | fuera-alcance | — | No se selecciona kotlin-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S154 | kubernetes-patterns | fuera-alcance | — | No se selecciona kubernetes-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S155 | laravel-patterns | fuera-alcance | — | No se selecciona laravel-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S156 | laravel-plugin-discovery | fuera-alcance | — | No se selecciona laravel-plugin-discovery para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S157 | laravel-security | fuera-alcance | — | No se selecciona laravel-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S158 | laravel-tdd | fuera-alcance | — | No se selecciona laravel-tdd para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S159 | laravel-verification | fuera-alcance | — | No se selecciona laravel-verification para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S160 | latency-critical-systems | fuera-alcance | — | No se selecciona latency-critical-systems para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S161 | lead-intelligence | fuera-alcance | — | No se selecciona lead-intelligence para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S162 | liquid-glass-design | fuera-alcance | — | No se selecciona liquid-glass-design para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S163 | living-docs-governance | fuera-alcance | — | No se selecciona living-docs-governance para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S164 | llm-trading-agent-security | fuera-alcance | — | No se selecciona llm-trading-agent-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S165 | logistics-exception-management | fuera-alcance | — | No se selecciona logistics-exception-management para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S166 | loop-design-check | fuera-alcance | — | No se selecciona loop-design-check para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S167 | mailtrap-email-integration | fuera-alcance | — | No se selecciona mailtrap-email-integration para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S168 | make-interfaces-feel-better | fuera-alcance | — | No se selecciona make-interfaces-feel-better para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S169 | manim-video | fuera-alcance | — | No se selecciona manim-video para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S170 | market-research | fuera-alcance | — | No se selecciona market-research para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S171 | marketing-campaign | fuera-alcance | — | No se selecciona marketing-campaign para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S172 | master-agreement-generator | fuera-alcance | — | No se selecciona master-agreement-generator para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S173 | mcp-server-patterns | fuera-alcance | — | No se selecciona mcp-server-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S174 | messages-ops | fuera-alcance | — | No se selecciona messages-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S175 | ml-adoption-playbook | fuera-alcance | — | No se selecciona ml-adoption-playbook para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S176 | mle-workflow | fuera-alcance | — | No se selecciona mle-workflow para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S177 | motion-advanced | fuera-alcance | — | No se selecciona motion-advanced para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S178 | motion-foundations | fuera-alcance | — | No se selecciona motion-foundations para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S179 | motion-patterns | fuera-alcance | — | No se selecciona motion-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S180 | mysql-patterns | fuera-alcance | — | No se selecciona mysql-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S181 | nanoclaw-repl | fuera-alcance | — | No se selecciona nanoclaw-repl para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S182 | nasiko-control-plane | fuera-alcance | — | No se selecciona nasiko-control-plane para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S183 | nestjs-patterns | fuera-alcance | — | No se selecciona nestjs-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S184 | netmiko-ssh-automation | fuera-alcance | — | No se selecciona netmiko-ssh-automation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S185 | network-bgp-diagnostics | fuera-alcance | — | No se selecciona network-bgp-diagnostics para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S186 | network-config-validation | fuera-alcance | — | No se selecciona network-config-validation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S187 | network-interface-health | fuera-alcance | — | No se selecciona network-interface-health para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S188 | nextjs-turbopack | fuera-alcance | — | No se selecciona nextjs-turbopack para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S189 | nodejs-keccak256 | fuera-alcance | — | No se selecciona nodejs-keccak256 para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S190 | nutrient-document-processing | fuera-alcance | — | No se selecciona nutrient-document-processing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S191 | nuxt4-patterns | fuera-alcance | — | No se selecciona nuxt4-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S192 | openclaw-persona-forge | fuera-alcance | — | No se selecciona openclaw-persona-forge para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S193 | opensource-pipeline | fuera-alcance | — | No se selecciona opensource-pipeline para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S194 | operator-approval-loop | fuera-alcance | — | No se selecciona operator-approval-loop para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S195 | orch-add-feature | fuera-alcance | — | No se selecciona orch-add-feature para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S196 | orch-build-mvp | fuera-alcance | — | No se selecciona orch-build-mvp para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S197 | orch-change-feature | fuera-alcance | — | No se selecciona orch-change-feature para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S198 | orch-fix-defect | fuera-alcance | — | No se selecciona orch-fix-defect para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S199 | orch-pipeline | fuera-alcance | — | No se selecciona orch-pipeline para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S200 | orch-refine-code | fuera-alcance | — | No se selecciona orch-refine-code para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S201 | parallel-execution-optimizer | fuera-alcance | — | No se selecciona parallel-execution-optimizer para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S202 | perl-patterns | fuera-alcance | — | No se selecciona perl-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S203 | perl-security | fuera-alcance | — | No se selecciona perl-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S204 | perl-testing | fuera-alcance | — | No se selecciona perl-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S205 | plan-canvas | fuera-alcance | — | No se selecciona plan-canvas para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S206 | plan-orchestrate | fuera-alcance | — | No se selecciona plan-orchestrate para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S207 | plankton-code-quality | fuera-alcance | — | No se selecciona plankton-code-quality para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S208 | postgres-patterns | fuera-alcance | — | No se selecciona postgres-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S209 | prediction-market-oracle-research | fuera-alcance | — | No se selecciona prediction-market-oracle-research para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S210 | prediction-market-risk-review | fuera-alcance | — | No se selecciona prediction-market-risk-review para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S211 | prisma-patterns | fuera-alcance | — | No se selecciona prisma-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S212 | product-capability | fuera-alcance | — | No se selecciona product-capability para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S213 | product-lens | fuera-alcance | — | No se selecciona product-lens para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S214 | production-audit | fuera-alcance | — | No se selecciona production-audit para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S215 | production-scheduling | fuera-alcance | — | No se selecciona production-scheduling para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S216 | project-flow-ops | fuera-alcance | — | No se selecciona project-flow-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S217 | prompt-optimizer | fuera-alcance | — | No se selecciona prompt-optimizer para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S218 | python-patterns | adaptación-acotada | stack-practices | Contratos de tipos/fronteras adaptados a la versión mínima; no se importan convenciones o dependencias universales. |
| S219 | python-testing | adaptación-acotada | stack-practices | Fixtures con cleanup, monkeypatch en namespace consumidor y aislamiento; TDD/cobertura conservan método propio. |
| S220 | pytorch-patterns | fuera-alcance | — | No se selecciona pytorch-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S221 | quality-nonconformance | fuera-alcance | — | No se selecciona quality-nonconformance para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S222 | quarkus-patterns | fuera-alcance | — | No se selecciona quarkus-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S223 | quarkus-security | fuera-alcance | — | No se selecciona quarkus-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S224 | quarkus-tdd | fuera-alcance | — | No se selecciona quarkus-tdd para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S225 | quarkus-verification | fuera-alcance | — | No se selecciona quarkus-verification para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S226 | rails-patterns | fuera-alcance | — | No se selecciona rails-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S227 | ralphinho-rfc-pipeline | fuera-alcance | — | No se selecciona ralphinho-rfc-pipeline para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S228 | react-native-patterns | fuera-alcance | — | No se selecciona react-native-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S229 | react-patterns | adaptación-acotada | stack-practices | Estado, efectos, cache y fronteras por framework; se descartan defaults de librería y umbrales fijos de virtualización. |
| S230 | react-performance | adaptación-acotada | frontend-quality | Medición antes/después por escenario; sin memoización ni librerías prescritas por nombre. |
| S231 | react-testing | adaptación-acotada | stack-practices | Criterios de interacción y estados observables; qa conserva ejecución E2E y gate. |
| S232 | recsys-pipeline-architect | fuera-alcance | — | No se selecciona recsys-pipeline-architect para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S233 | recursive-decision-ledger | fuera-alcance | — | No se selecciona recursive-decision-ledger para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S234 | redis-patterns | fuera-alcance | — | No se selecciona redis-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S235 | regex-vs-llm-structured-text | fuera-alcance | — | No se selecciona regex-vs-llm-structured-text para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S236 | remotion-video-creation | fuera-alcance | — | No se selecciona remotion-video-creation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S237 | repo-scan | fuera-alcance | — | No se selecciona repo-scan para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S238 | research-ops | fuera-alcance | — | No se selecciona research-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S239 | returns-reverse-logistics | fuera-alcance | — | No se selecciona returns-reverse-logistics para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S240 | rules-distill | fuera-alcance | — | No se selecciona rules-distill para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S241 | rust-patterns | fuera-alcance | — | No se selecciona rust-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S242 | rust-testing | fuera-alcance | — | No se selecciona rust-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S243 | safety-guard | fuera-alcance | — | No se selecciona safety-guard para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S244 | santa-method | fuera-alcance | — | No se selecciona santa-method para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S245 | scientific-db-pubmed-database | fuera-alcance | — | No se selecciona scientific-db-pubmed-database para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S246 | scientific-db-uspto-database | fuera-alcance | — | No se selecciona scientific-db-uspto-database para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S247 | scientific-pkg-gget | fuera-alcance | — | No se selecciona scientific-pkg-gget para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S248 | scientific-thinking-literature-review | fuera-alcance | — | No se selecciona scientific-thinking-literature-review para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S249 | scientific-thinking-scholar-evaluation | fuera-alcance | — | No se selecciona scientific-thinking-scholar-evaluation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S250 | search-first | adaptación-acotada | research-first | Comparación adoptar/extender/construir y canal no disponible; el rol actual conserva el análisis. |
| S251 | security-bounty-hunter | fuera-alcance | — | No se selecciona security-bounty-hunter para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S252 | security-review | mantener-contrato | cybersecurity | El alcance de seguridad se mantiene en las lentes/skill existentes; no se importa otra cadena de aprobación. |
| S253 | security-scan | mantener-contrato | cybersecurity | No se instala un segundo scanner/configurador; se conserva la auditoría con tools disponibles y evidencias reales. |
| S254 | seo | fuera-alcance | — | No se selecciona seo para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S255 | skill-comply | fuera-alcance | — | No se selecciona skill-comply para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S256 | skill-scout | fuera-alcance | — | No se selecciona skill-scout para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S257 | skill-stocktake | adaptación-acotada | capability-audit | Utilidad, solapes, vigencia y evidencia por pieza; no se heredan tiempos estimados ni scopes globales implícitos. |
| S258 | social-graph-ranker | fuera-alcance | — | No se selecciona social-graph-ranker para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S259 | social-publisher | fuera-alcance | — | No se selecciona social-publisher para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S260 | springboot-patterns | fuera-alcance | — | No se selecciona springboot-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S261 | springboot-security | fuera-alcance | — | No se selecciona springboot-security para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S262 | springboot-tdd | fuera-alcance | — | No se selecciona springboot-tdd para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S263 | springboot-verification | fuera-alcance | — | No se selecciona springboot-verification para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S264 | strategic-compact | fuera-alcance | — | No se selecciona strategic-compact para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S265 | swift-actor-persistence | fuera-alcance | — | No se selecciona swift-actor-persistence para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S266 | swift-concurrency-6-2 | fuera-alcance | — | No se selecciona swift-concurrency-6-2 para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S267 | swift-protocol-di-testing | fuera-alcance | — | No se selecciona swift-protocol-di-testing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S268 | swiftui-patterns | fuera-alcance | — | No se selecciona swiftui-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S269 | taste | fuera-alcance | — | No se selecciona taste para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S270 | taste-application | fuera-alcance | — | No se selecciona taste-application para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S271 | taste-distillation | fuera-alcance | — | No se selecciona taste-distillation para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S272 | tasteforge-video | fuera-alcance | — | No se selecciona tasteforge-video para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S273 | tdd-workflow | mantener-contrato | tdd | RED/GREEN y evidencia siguen en la fuente única tdd y el ledger; no se importa otra puerta de cobertura. |
| S274 | team-agent-orchestration | fuera-alcance | — | No se selecciona team-agent-orchestration para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S275 | team-builder | fuera-alcance | — | No se selecciona team-builder para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S276 | terminal-opener | fuera-alcance | — | No se selecciona terminal-opener para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S277 | terminal-ops | fuera-alcance | — | No se selecciona terminal-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S278 | tinystruct-patterns | fuera-alcance | — | No se selecciona tinystruct-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S279 | token-budget-advisor | fuera-alcance | — | No se selecciona token-budget-advisor para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S280 | ui-demo | fuera-alcance | — | No se selecciona ui-demo para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S281 | ui-to-vue | fuera-alcance | — | No se selecciona ui-to-vue para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S282 | uncloud | fuera-alcance | — | No se selecciona uncloud para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S283 | unified-memory | adaptación-acotada | agent-kits/shared/knowledge-check.md | Fuente ausente/incompleta diferenciada de vacío, estado y procedencia; no se instala otro vault ni MCP. |
| S284 | unified-notifications-ops | fuera-alcance | — | No se selecciona unified-notifications-ops para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S285 | verification-loop | fuera-alcance | — | No se selecciona verification-loop para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S286 | video-editing | fuera-alcance | — | No se selecciona video-editing para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S287 | videodb | fuera-alcance | — | No se selecciona videodb para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S288 | visa-doc-translate | fuera-alcance | — | No se selecciona visa-doc-translate para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S289 | vite-patterns | fuera-alcance | — | No se selecciona vite-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S290 | vue-patterns | fuera-alcance | — | No se selecciona vue-patterns para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S291 | windows-desktop-e2e | fuera-alcance | — | No se selecciona windows-desktop-e2e para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S292 | workspace-surface-audit | fuera-alcance | — | No se selecciona workspace-surface-audit para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| S293 | x-api | fuera-alcance | — | No se selecciona x-api para este delta técnico de tres stacks y operación del plugin. Es decisión de alcance; su utilidad completa no se ha evaluado. |
| A001 | a11y-architect | sin-importar-rol | — | El rol a11y-architect no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A002 | agent-evaluator | sin-importar-rol | — | El rol agent-evaluator no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A003 | architect | sin-importar-rol | architect | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A004 | build-error-resolver | sin-importar-rol | debug-root-cause | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A005 | chief-of-staff | sin-importar-rol | — | El rol chief-of-staff no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A006 | code-architect | sin-importar-rol | — | El rol code-architect no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A007 | code-explorer | sin-importar-rol | — | El rol code-explorer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A008 | code-reviewer | sin-importar-rol | reviewer | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A009 | code-simplifier | sin-importar-rol | — | El rol code-simplifier no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A010 | comment-analyzer | sin-importar-rol | — | El rol comment-analyzer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A011 | conversation-analyzer | sin-importar-rol | — | El rol conversation-analyzer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A012 | cpp-build-resolver | sin-importar-rol | — | El rol cpp-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A013 | cpp-reviewer | sin-importar-rol | — | El rol cpp-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A014 | csharp-reviewer | sin-importar-rol | — | El rol csharp-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A015 | dart-build-resolver | sin-importar-rol | — | El rol dart-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A016 | database-reviewer | sin-importar-rol | — | El rol database-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A017 | django-build-resolver | sin-importar-rol | — | El rol django-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A018 | django-reviewer | sin-importar-rol | — | El rol django-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A019 | doc-updater | sin-importar-rol | documenter | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A020 | docs-lookup | sin-importar-rol | — | El rol docs-lookup no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A021 | e2e-runner | sin-importar-rol | qa | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A022 | fastapi-reviewer | sin-importar-rol | — | El rol fastapi-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A023 | flutter-reviewer | sin-importar-rol | — | El rol flutter-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A024 | fsharp-reviewer | sin-importar-rol | — | El rol fsharp-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A025 | gan-evaluator | sin-importar-rol | — | El rol gan-evaluator no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A026 | gan-generator | sin-importar-rol | — | El rol gan-generator no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A027 | gan-planner | sin-importar-rol | — | El rol gan-planner no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A028 | go-build-resolver | sin-importar-rol | — | El rol go-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A029 | go-reviewer | sin-importar-rol | — | El rol go-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A030 | harmonyos-app-resolver | sin-importar-rol | — | El rol harmonyos-app-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A031 | harness-optimizer | sin-importar-rol | — | El rol harness-optimizer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A032 | healthcare-reviewer | sin-importar-rol | — | El rol healthcare-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A033 | homelab-architect | sin-importar-rol | — | El rol homelab-architect no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A034 | java-build-resolver | sin-importar-rol | — | El rol java-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A035 | java-reviewer | sin-importar-rol | — | El rol java-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A036 | kotlin-build-resolver | sin-importar-rol | — | El rol kotlin-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A037 | kotlin-reviewer | sin-importar-rol | — | El rol kotlin-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A038 | loop-operator | sin-importar-rol | — | El rol loop-operator no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A039 | marketing-agent | sin-importar-rol | — | El rol marketing-agent no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A040 | mle-reviewer | sin-importar-rol | — | El rol mle-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A041 | network-architect | sin-importar-rol | — | El rol network-architect no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A042 | network-config-reviewer | sin-importar-rol | — | El rol network-config-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A043 | network-troubleshooter | sin-importar-rol | — | El rol network-troubleshooter no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A044 | opensource-forker | sin-importar-rol | — | El rol opensource-forker no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A045 | opensource-packager | sin-importar-rol | — | El rol opensource-packager no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A046 | opensource-sanitizer | sin-importar-rol | — | El rol opensource-sanitizer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A047 | performance-optimizer | sin-importar-rol | — | El rol performance-optimizer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A048 | php-reviewer | sin-importar-rol | stack-practices | La guía observada presupone Eloquent/Laravel/Pint; CI4 requiere criterio propio y reviewer conserva el veredicto. No se importa obligatoriedad de agente por lenguaje. |
| A049 | planner | sin-importar-rol | planner | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A050 | pr-test-analyzer | sin-importar-rol | — | El rol pr-test-analyzer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A051 | python-reviewer | sin-importar-rol | stack-practices | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A052 | pytorch-build-resolver | sin-importar-rol | — | El rol pytorch-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A053 | rag-pipeline-reviewer | sin-importar-rol | — | El rol rag-pipeline-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A054 | react-build-resolver | sin-importar-rol | stack-practices | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A055 | react-reviewer | sin-importar-rol | stack-practices | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A056 | refactor-cleaner | sin-importar-rol | — | El rol refactor-cleaner no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A057 | rust-build-resolver | sin-importar-rol | — | El rol rust-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A058 | rust-reviewer | sin-importar-rol | — | El rol rust-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A059 | security-reviewer | sin-importar-rol | nemesis | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A060 | seo-specialist | sin-importar-rol | — | El rol seo-specialist no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A061 | silent-failure-hunter | sin-importar-rol | — | El rol silent-failure-hunter no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A062 | spec-miner | sin-importar-rol | — | El rol spec-miner no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A063 | swift-build-resolver | sin-importar-rol | — | El rol swift-build-resolver no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A064 | swift-reviewer | sin-importar-rol | — | El rol swift-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A065 | tdd-guide | sin-importar-rol | tdd | Conservar el dueño actual del artefacto; los criterios pertinentes se conectan mediante guías, sin otra cadena de revisión/build/QA. |
| A066 | type-design-analyzer | sin-importar-rol | — | El rol type-design-analyzer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A067 | typescript-reviewer | sin-importar-rol | — | El rol typescript-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| A068 | vue-reviewer | sin-importar-rol | — | El rol vue-reviewer no añade un artefacto propio al delta PHP/CI4, Python, React y operación del plugin; no se importa el rol de dominio. |
| C001 | aside | sin-importar-comando | — | No se añade la entrada aside: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C002 | auto-update | sin-importar-comando | — | No se añade la entrada auto-update: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C003 | build-fix | sin-importar-comando | — | No se añade la entrada build-fix: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C004 | checkpoint | sin-importar-comando | — | No se añade la entrada checkpoint: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C005 | code-review | sin-importar-comando | — | No se añade la entrada code-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C006 | cost-report | sin-importar-comando | — | No se añade la entrada cost-report: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C007 | cpp-build | sin-importar-comando | — | No se añade la entrada cpp-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C008 | cpp-review | sin-importar-comando | — | No se añade la entrada cpp-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C009 | cpp-test | sin-importar-comando | — | No se añade la entrada cpp-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C010 | reference-guide | sin-importar-comando | — | No se añade la entrada reference-guide: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C011 | epic-claim | sin-importar-comando | — | No se añade la entrada epic-claim: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C012 | epic-decompose | sin-importar-comando | — | No se añade la entrada epic-decompose: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C013 | epic-publish | sin-importar-comando | — | No se añade la entrada epic-publish: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C014 | epic-review | sin-importar-comando | — | No se añade la entrada epic-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C015 | epic-sync | sin-importar-comando | — | No se añade la entrada epic-sync: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C016 | epic-unblock | sin-importar-comando | — | No se añade la entrada epic-unblock: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C017 | epic-validate | sin-importar-comando | — | No se añade la entrada epic-validate: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C018 | evolve | sin-importar-comando | — | No se añade la entrada evolve: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C019 | fastapi-review | sin-importar-comando | — | No se añade la entrada fastapi-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C020 | feature-dev | sin-importar-comando | — | No se añade la entrada feature-dev: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C021 | flutter-build | sin-importar-comando | — | No se añade la entrada flutter-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C022 | flutter-review | sin-importar-comando | — | No se añade la entrada flutter-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C023 | flutter-test | sin-importar-comando | — | No se añade la entrada flutter-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C024 | gan-build | sin-importar-comando | — | No se añade la entrada gan-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C025 | gan-design | sin-importar-comando | — | No se añade la entrada gan-design: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C026 | go-build | sin-importar-comando | — | No se añade la entrada go-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C027 | go-review | sin-importar-comando | — | No se añade la entrada go-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C028 | go-test | sin-importar-comando | — | No se añade la entrada go-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C029 | gradle-build | sin-importar-comando | — | No se añade la entrada gradle-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C030 | harness-audit | sin-importar-comando | — | No se añade la entrada harness-audit: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C031 | hookify-configure | sin-importar-comando | — | No se añade la entrada hookify-configure: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C032 | hookify-help | sin-importar-comando | — | No se añade la entrada hookify-help: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C033 | hookify-list | sin-importar-comando | — | No se añade la entrada hookify-list: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C034 | hookify | sin-importar-comando | — | No se añade la entrada hookify: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C035 | instinct-export | sin-importar-comando | — | No se añade la entrada instinct-export: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C036 | instinct-import | sin-importar-comando | — | No se añade la entrada instinct-import: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C037 | instinct-status | sin-importar-comando | — | No se añade la entrada instinct-status: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C038 | jira | sin-importar-comando | — | No se añade la entrada jira: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C039 | kotlin-build | sin-importar-comando | — | No se añade la entrada kotlin-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C040 | kotlin-review | sin-importar-comando | — | No se añade la entrada kotlin-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C041 | kotlin-test | sin-importar-comando | — | No se añade la entrada kotlin-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C042 | learn-eval | sin-importar-comando | — | No se añade la entrada learn-eval: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C043 | learn | sin-importar-comando | — | No se añade la entrada learn: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C044 | loop-start | sin-importar-comando | — | No se añade la entrada loop-start: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C045 | loop-status | sin-importar-comando | — | No se añade la entrada loop-status: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C046 | marketing-campaign | sin-importar-comando | — | No se añade la entrada marketing-campaign: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C047 | model-route | sin-importar-comando | — | No se añade la entrada model-route: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C048 | multi-backend | sin-importar-comando | — | No se añade la entrada multi-backend: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C049 | multi-execute | sin-importar-comando | — | No se añade la entrada multi-execute: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C050 | multi-frontend | sin-importar-comando | — | No se añade la entrada multi-frontend: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C051 | multi-plan | sin-importar-comando | — | No se añade la entrada multi-plan: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C052 | multi-workflow | sin-importar-comando | — | No se añade la entrada multi-workflow: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C053 | orch-add-feature | sin-importar-comando | — | No se añade la entrada orch-add-feature: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C054 | orch-build-mvp | sin-importar-comando | — | No se añade la entrada orch-build-mvp: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C055 | orch-change-feature | sin-importar-comando | — | No se añade la entrada orch-change-feature: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C056 | orch-fix-defect | sin-importar-comando | — | No se añade la entrada orch-fix-defect: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C057 | orch-refine-code | sin-importar-comando | — | No se añade la entrada orch-refine-code: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C058 | orch-review | sin-importar-comando | — | No se añade la entrada orch-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C059 | plan-canvas | sin-importar-comando | — | No se añade la entrada plan-canvas: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C060 | plan-prd | sin-importar-comando | — | No se añade la entrada plan-prd: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C061 | plan | sin-importar-comando | — | No se añade la entrada plan: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C062 | pm2 | sin-importar-comando | — | No se añade la entrada pm2: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C063 | pr | sin-importar-comando | — | No se añade la entrada pr: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C064 | project-init | sin-importar-comando | — | No se añade la entrada project-init: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C065 | projects | sin-importar-comando | — | No se añade la entrada projects: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C066 | promote | sin-importar-comando | — | No se añade la entrada promote: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C067 | prp-commit | sin-importar-comando | — | No se añade la entrada prp-commit: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C068 | prp-implement | sin-importar-comando | — | No se añade la entrada prp-implement: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C069 | prp-plan | sin-importar-comando | — | No se añade la entrada prp-plan: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C070 | prp-pr | sin-importar-comando | — | No se añade la entrada prp-pr: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C071 | prp-prd | sin-importar-comando | — | No se añade la entrada prp-prd: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C072 | prune | sin-importar-comando | — | No se añade la entrada prune: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C073 | python-review | sin-importar-comando | — | No se añade la entrada python-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C074 | quality-gate | sin-importar-comando | — | No se añade la entrada quality-gate: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C075 | react-build | sin-importar-comando | — | No se añade la entrada react-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C076 | react-review | sin-importar-comando | — | No se añade la entrada react-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C077 | react-test | sin-importar-comando | — | No se añade la entrada react-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C078 | refactor-clean | sin-importar-comando | — | No se añade la entrada refactor-clean: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C079 | resume-session | sin-importar-comando | — | No se añade la entrada resume-session: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C080 | review-pr | sin-importar-comando | — | No se añade la entrada review-pr: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C081 | rust-build | sin-importar-comando | — | No se añade la entrada rust-build: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C082 | rust-review | sin-importar-comando | — | No se añade la entrada rust-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C083 | rust-test | sin-importar-comando | — | No se añade la entrada rust-test: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C084 | santa-loop | sin-importar-comando | — | No se añade la entrada santa-loop: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C085 | save-session | sin-importar-comando | — | No se añade la entrada save-session: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C086 | security-scan | sin-importar-comando | — | No se añade la entrada security-scan: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C087 | sessions | sin-importar-comando | — | No se añade la entrada sessions: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C088 | setup-pm | sin-importar-comando | — | No se añade la entrada setup-pm: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C089 | skill-create | sin-importar-comando | — | No se añade la entrada skill-create: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C090 | skill-health | sin-importar-comando | — | No se añade la entrada skill-health: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C091 | test-coverage | sin-importar-comando | — | No se añade la entrada test-coverage: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C092 | update-codemaps | sin-importar-comando | — | No se añade la entrada update-codemaps: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C093 | update-docs | sin-importar-comando | — | No se añade la entrada update-docs: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |
| C094 | vue-review | sin-importar-comando | — | No se añade la entrada vue-review: el delta mantiene pm/dev-cycle, comandos propios y puertas canónicas; no se acredita cobertura de su dominio completo. |

## Deltas comprobables

- Stack-practices absorbe íntegramente las referencias propias iniciales y amplía
  fronteras/pruebas por versión. Las tres skills anteriores, sus evals y callers
  activos están retirados; los registros históricos conservan el alcance anterior.
- El criterio PHP genérico observado presupone Laravel/Eloquent/Pint: se conserva
  una referencia específica CI4 y no se exige un reviewer paralelo por lenguaje.
- Los ejemplos de migraciones contienen afirmaciones de DDL «sin locks» que no
  adoptamos. La guía propia exige comprobar motor/versión, convivencia y recuperación.
- Las recetas React prescriben librerías y umbrales de filas: nuestra guía exige
  contexto del framework y medición. No se copia un ejemplo Actions/RSC a una SPA.
- La pieza llamada benchmark-methodology trata competencia comercial; se excluye
  de la evaluación de agentes. Outcome-evals se basa en casos/checks reproducibles,
  no en dimensiones de marca o un score compuesto.
- El harness consultado no habilita ejecución de candidatos por falta de aislamiento
  verificado. El reporte propio agrega artefactos JUnit existentes sin ejecutar
  código ni afirmar aislamiento o aprobación de QA.
- Un vault compartido no sustituye nuestro Knowledge Gate. Se incorpora distinguir
  vacío/fallo/incompletitud y procedencia; no se instala otro backend de memoria.
- Las observaciones/confianza de aprendizaje no se convierten automáticamente en
  conocimiento aprobado. Los hooks actuales siguen sin red y sin decisiones nuevas.

La validación ejecutada del plugin se registra en testing/report.md al cierre.
Los benchmarks comparativos de sesiones no se anuncian sin ejecuciones compatibles.
