---
spec: catalog-capabilities
estado: aprobada
creado: 2026-10-07
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Capacidades nativas y coherencia del workflow

Fase 3 de la integración autorizada. El usuario pide comparar en profundidad
skills, tools, agentes, comandos, hooks, workflows y control panel; integrar lo
útil con estructura profesional, documentación y retirada de código sustituido.
Las decisiones técnicas están delegadas; no se inventa una aprobación formal
nueva de cada diseño ni una solicitud de presupuesto económico.

La fase 2 publicada aporta reconocimiento de extensiones, no esta comparación.
Las 455 decisiones de fase 1 son de alcance/adaptación acotada. Aquí se revisa
el corpus completo fijado: 293 skills, 68 agentes y 94 comandos, con cuerpos,
recursos y callers. El número de ficheros no acredita utilidad ni integración.
La revisión de origen es ef648e01899ba3e8dc6371642deaaf64b4477775; no se declara
que sea la revisión más reciente del catálogo.

## Aceptación

Prioridad del usuario del 2026-10-08: aplazar nuevas skills y avanzar por
bloques de hooks, comandos, dashboard y memoria. El
[punto de reanudación](operational-priorities.md) conserva las 79/293 skills
evaluadas y define dependencias por bloque. El alcance final siguiente no
se declara completado ni se elimina por ese cambio de secuencia.

1. Reconciliar los 455 IDs/hashes existentes y enumerar recursos, tools, MCP,
   reglas, contextos, hooks, workflows y control panel de la revisión fijada.
   Fuentes originales y rutas de investigación se mantienen privadas; las
   decisiones públicas usan IDs, hashes y nombres funcionales propios.
2. Cada pieza principal tiene ficha semántica: cuerpo y recursos leídos,
   contenido único, sección existente comparada, decisión, destino, dueño,
   dependencias, coste de carga medido en bytes/líneas y validación real o
   explícitamente no ejecutada. No usar el nombre o la ausencia de logs como
   prueba de equivalencia, calidad o falta de uso. Separar inventariadas,
   evaluadas y entregadas; las exclusiones requieren motivo funcional concreto.
3. Las altas y consolidaciones nacen en custom-agents: fragmentos compartidos
   únicos, skills por función, agentes con responsabilidad propia y comandos
   que usan el workflow canónico. Conservar criterios útiles, eliminar callers
   y recursos sustituidos y actualizar dependencias, evals, docs y exports.
   No conservar alias vacíos para simular cobertura.
4. No inventar paquetes técnicos ausentes del corpus. Los dominios existentes
   allí pueden incorporarse de forma opcional cuando su comparación pruebe
   valor. No imponer todos los stacks, skills o servicios a cada proyecto ni
   resolver esta fase descartando dominios por no ser el stack de este repo.
5. Verificar contratos por versión y modo de instalación en Claude, Codex y
   OpenCode. Corregir el despacho de guardias: su configuración debe ejecutarse
   donde se anuncia, distinguir al implementer de otros roles y preservar el
   trabajo autorizado del planner/documenter. No usar solo frontmatter o mocks
   como prueba de ejecución nativa. Documentar límites reales y datos de
   identidad disponibles, sin fingir una frontera de seguridad universal.
6. Adaptar OpenCode a la versión instalada V2 y probar carga/despacho; si se
   conserva compatibilidad V1 por usuarios reales, tendrá contrato explícito y
   código compartido, sin mantener un puente obsoleto anunciado como actual.
   Validar además configuración, agentes, skills, comandos y tools propios con
   los formatos realmente soportados, preservando extensiones del consumidor.
7. Comparar control panel y operación: incorporar funciones útiles al panel
   nativo con navegación/filtros accesibles, fuentes y estados comprensibles.
   Métricas solo observadas; datos ausentes se muestran como ausentes. Una
   página estática no se anuncia como servicio vivo ni prueba conexión MCP.
8. TDD cuando haya código, cobertura del diff ≥90 %, escenarios concretos de
   selección/transferencia/uso/degradación, QA Windows/Linux/Edge y comprobación
   nativa por runtime. Evals de activación no se confunden con eficacia. Revisar
   cada fase con A+B y C/D según selector, hasta tres intentos por ciclo, sin
   gaps introducidos pendientes al cierre ni deuda no autorizada.
9. Documentación ES/EN, catálogo y rutas actualizados; cero referencias públicas
   a la marca de origen en nombres, comentarios o contenido. Conservar avisos
   legales obligatorios. Retro, changelogs y push con SHA remoto comprobado;
   sin PR, integración en main ni release. Settings existentes siguen intactos.

## Memoria y límites entre fases

Las capacidades de memoria del corpus se comparan semánticamente en esta fase,
sin esconderlas como fuera de alcance. Sus decisiones de integración se ligan
al benchmark de recuperación, vigencia y utilidad de la fase 4; no se sustituye
la memoria aprobada por cantidad de funciones ni por un piloto AST. La generación
y adopción de piezas mantiene el plan independiente de especialización.

No se ejecutan scripts o instrucciones del corpus para investigar sus nombres.
Los recursos candidatos se validan solo en fixtures propias y entornos aislados,
con APIs/flags oficiales contrastados y sin conectar cuentas o MCP del usuario.
