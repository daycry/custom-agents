# Revalidación de destinos aparcados

47 propuestas de destino, no 47 skills nuevas. Registro original conservado; esta iniciativa documenta sus nuevas disposiciones.

D-116 ya está cubierto por la lectura sobre descriptor; tres regresiones existentes pasan. Siete destinos transversales pueden integrarse ahora. D-146 necesita concretar su persistencia; los demás conservan requisitos de consumidor, contexto o dependencia. Esta era la decisión inicial, previa a la respuesta de stacks; el avance posterior se registra al final.

| ID | Disposición | Destino / motivo |
|---|---|---|
| D-111 | Esperar contexto/dependencia | `skills/unit-tests/scripts/coverage-gate.py`: Esperar stack y formato de cobertura del consumidor. Los avisos de herramientas existentes no son parsers nuevos. |
| D-112 | Esperar contexto/dependencia | `skills/dependency-upgrade/scripts/deps-inventory.py`: Esperar proyecto Rust/Flox y plataforma; no se añade dependencia o detección por popularidad. |
| D-113 | Esperar contexto/dependencia | `skills/frontend-quality/references/native-accessibility.md`: Esperar aplicación nativa iOS/Android y plataforma de accesibilidad. |
| D-114 | Esperar contexto/dependencia | `agent-kits/qa/references/desktop-e2e.md`: Esperar aplicación Windows bajo prueba y herramienta autorizada; el panel web no acredita E2E nativo. |
| D-115 | Esperar contexto/dependencia | `docs/knowledge/adr/ADR-022-rigor-proporcional-al-riesgo-y-ledger-fino-con-anexos-enlazados.md`: Depende del diseño de risk-profile.py; no se edita un ADR aceptado como efecto lateral. |
| D-116 | Ya cubierto | `agent-kits/shared/knowledge-curation.py`: knowledge-curation._read usa local-read.read_bytes(include_digest=True, include_identity=True); hash e identidad proceden del descriptor abierto, con validación posterior de ruta y rechazo de hardlinks. Tres regresiones dirigidas pasan. |
| D-117 | Esperar contexto/dependencia | `agent-kits/shared/journal.py`: Falta contrato del observador, datos, permisos y curación; no se crea un proceso de IA en segundo plano. |
| D-118 | Esperar contexto/dependencia | `agent-kits/architect/references/external-critique.md`: Falta proveedor/runtime para crítica externa y adaptador verificable. |
| D-119 | Esperar contexto/dependencia | `skills/agent-system-quality/references/external-dispatch.md`: T-12 del catálogo fue cancelada; requiere endpoint y contrato de misiones, sin auto-merge. |
| D-120 | Esperar contexto/dependencia | `agents/documenter.md`: Falta consumidor de CodeTour y validación del formato. |
| D-121 | Esperar consumidor | `skills/angular-practices/SKILL.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-122 | Esperar consumidor | `skills/kotlin-practices/SKILL.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-123 | Integración aplicable | `skills/stack-practices/references/dotnet-csharp.md`: Consumidor declarado por el usuario el 2026-10-30; se consolida en stack-practices. La guía aplica versión/SDK del consumidor; no instala servicios ni añade parser de cobertura. |
| D-124 | Esperar consumidor | `skills/cpp-practices/SKILL.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-125 | Esperar consumidor | `skills/stack-practices/references/go.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-126 | Esperar consumidor | `skills/stack-practices/references/java.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-127 | Integración aplicable | `skills/stack-practices/references/laravel.md`: Consumidor declarado por el usuario el 2026-10-30; se consolida en stack-practices. La guía aplica versión/SDK del consumidor; no instala servicios ni añade parser de cobertura. |
| D-128 | Esperar consumidor | `skills/django-practices/SKILL.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-129 | Esperar consumidor | `skills/stack-practices/references/python.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-130 | Esperar consumidor | `skills/stack-practices/references/rails.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-131 | Esperar consumidor | `skills/stack-practices/references/rust.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-132 | Esperar consumidor | `skills/stack-practices/references/perl.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-133 | Esperar consumidor | `skills/stack-practices/references/swift.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-134 | Esperar consumidor | `skills/dart-flutter-practices/SKILL.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-135 | Esperar consumidor | `skills/stack-practices/references/vue-nuxt.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-136 | Esperar consumidor | `skills/stack-practices/references/node-backend.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-137 | Esperar consumidor | `skills/stack-practices/references/react-native.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-138 | Esperar consumidor | `skills/stack-practices/references/ml.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-139 | Esperar consumidor | `skills/stack-practices/references/bun.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-140 | Esperar consumidor | `skills/stack-practices/references/clickhouse.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-141 | Esperar consumidor | `skills/stack-practices/references/mysql.md`: El usuario solicita stacks adicionales y aún debe concretar proyectos/frameworks/versiones. Se preserva la condición del catálogo; la ausencia de este fichero no prueba ausencia de otra cobertura. |
| D-142 | Esperar contexto/dependencia | `skills/solidity-security/SKILL.md`: Esperar consumidor Solidity y toolchain; no se amplía una auditoría financiera por defecto. |
| D-143 | Esperar contexto/dependencia | `skills/network-operations/SKILL.md`: Falta inventario de red y alcance de operaciones del usuario. |
| D-144 | Esperar contexto/dependencia | `skills/agent-payments/SKILL.md`: Falta API de pagos y contrato de reservas/terminales del consumidor. |
| D-145 | Esperar contexto/dependencia | `skills/blender-inspection/SKILL.md`: Falta escena/versión de Blender y collector del runtime. |
| D-146 | Concretar persistencia | `skills/brand-strategy`: La entrevista y sus ocho plantillas están comparadas, pero la integración completa necesita checkpoints por respuesta, reanudación e identidad de participantes. Se concreta ese recurso antes de prometer durabilidad. |
| D-147 | Integrar | `voice-profile`: Perfil único desde muestras, reutilizado por contenido y contacto; sin persistencia personal automática. |
| D-148 | Integrar | `content-production`: Guía de escritura larga y adaptación por canal; reutiliza voz y deja la entrega al canal autorizado. |
| D-149 | Integrar | `relationship-planning`: Revisión de red y preparación de contacto con evidencias e identidades exactas; sin acciones automáticas. |
| D-150 | Integrar | `competitive-analysis`: Selección, perfiles e informe con desconocidos explícitos; sin total compuesto inventado. |
| D-151 | Integrar | `agent-kits/shared/external-communication.md`: Consolidar el contrato de destinatario y entrega en un fragmento compartido por dos callers, sin crear motor de permisos. |
| D-152 | Esperar contexto/dependencia | `skills/billing-support/SKILL.md`: Falta proveedor/conector de facturación y alcance de atención autorizado. |
| D-153 | Integrar | `llm-pipeline`: Guía del proyecto consumidor para reservas, routing, cache y reintentos; no cambia el modelo ni las tarifas del plugin. |
| D-154 | Integrar | `data-collection`: Guía de contratos de fuente, enriquecimiento, storage y feedback; no instala adaptadores ni servicios. |
| D-155 | Esperar contexto/dependencia | `skills/freight-operations/SKILL.md`: Falta caso de transporte, inventario y sistemas operativos. |
| D-156 | Esperar contexto/dependencia | `skills/trade-compliance/SKILL.md`: Faltan jurisdicción, productos, fuentes normativas y flujo de revisión profesional. |
| D-157 | Esperar contexto/dependencia | `skills/operational-dashboards/SKILL.md`: Falta consumidor Grafana/SigNoz y contrato de métricas; plugin-panel conserva la presentación del plugin. |

Evidencia, fuentes y límites por destino: [matriz JSON](testing/destination-revalidation.json). La clasificación de entrada no es una medición de utilidad ni una ejecución de las capacidades.

## Avance tras la respuesta del usuario

El usuario declara CodeIgniter 4, Laravel, Symfony, Next.js, React, Python, .NET, C y C#. Sin versiones concretas, cada guía resuelve el manifiesto/lockfile/target al aplicarse. D-123 (.NET/C#) y D-127 (Laravel) se consolidan en stack-practices, junto a las nuevas referencias Symfony, Next.js y C solicitadas. C no acredita consumidor C++; React no acredita React Native.

Los siete destinos transversales tienen seis skills y un fragmento compartido. Los nueve destinos históricos seleccionados están implementados y validados como guías y selección; no se cuentan como eficacia editorial o de modelos demostrada. Quedan 19 especialidades de aquel catálogo sin consumidor declarado, un contrato de persistencia de marca y 17 dependencias/contextos por concretar; D-116 ya estaba cubierto.
