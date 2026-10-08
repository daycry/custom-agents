# Prioridad operativa y punto de reanudación

Dirección del usuario del 2026-10-08: aplazar la comparación e incorporación
de nuevas skills y centrar el trabajo en hooks, comandos, dashboard y memoria.
El [ledger](tasks.md) sigue siendo la fuente única de progreso; este documento
define secuencia y límites, sin cerrar la iniciativa ni reducir su alcance final.

## Skills aplazadas

Se conservan **79/293 evaluadas**, S001–S079; quedan **214**. S080–S082 tienen
cuerpos leídos y investigación privada parcial, pero no fichas completas ni
evaluación contabilizada. La reanudación comienza por completar ese bloque.
Las decisiones anteriores son destinos propuestos, no altas entregadas.
T-03 y T-10 quedan aplazadas por petición del usuario. Los cambios necesarios
en referencias de una capacidad existente para corregir hooks, comandos,
panel o memoria pertenecen al bloque operativo, sin abrir nuevas skills.

## Secuencia y dependencias por bloque

1. **Hooks (T-02/T-06/T-08/T-09).** Cerrar contrato, diseño, transporte e
   identidad efectivos por runtime; ejecutar pruebas de carga y despacho,
   allow/deny por rol, concurrencia y captura durable de sesión.
2. **Comandos (T-05/T-08/T-11).** Comparar los comandos pertinentes antes de
   modificarlos; consolidar operaciones útiles en el workflow existente,
   actualizar artefactos, consumidores y exports del mismo bloque.
3. **Dashboard (T-06/T-08/T-13).** Comparar las funciones pertinentes y
   presentar handlers, propósito, timeout, procedencia y estado comprobado.
   Diferenciar configuración declarada, carga observada y ejecución probada;
   verificar navegación, filtros, teclado y ausencia de datos sensibles.
4. **Memoria (T-07 y bloques anteriores).** Comparar captura, continuidad,
   curación y recuperación; corregir sus contratos y visibilidad. Medir
   candidatos de recuperación antes de recomendar una migración o ampliación.

Cada bloque exige la comparación pertinente y un diseño trazable antes de
producción. No depende de terminar las 214 skills, todos los agentes ni todos
los tools opcionales. T-14/T-15 se aplican a cada entrega; su aceptación global
y T-16 siguen pendientes mientras quede alcance requerido. Una entrega
operativa no acredita completar la comparación de 455 piezas.

Los [contratos](contracts.md) y [probes](runtime-probes.json) conservan gaps
observados: frontmatter de guardias ignorado en agentes de plugin Claude,
identidad opcional en PreToolUse Codex y carga V1 fallida en OpenCode V2.
El control positivo V2 registra callbacks, pero no demuestra despacho.
El timeout declarado tampoco demuestra captura dentro del presupuesto de
teardown. Esta repriorización no declara ninguno de esos gaps corregido.

## Memoria: valoración inicial y comprobaciones pendientes

### Dirección de diseño aceptada por el usuario

El 2026-10-08 el usuario aceptó la recomendación de memoria:

1. Mantener la memoria local versionada como base canónica.
2. Mejorar primero la captura fiable y la recuperación local.
3. Incorporar propuestas de aprendizaje con evidencia y revisión, usando
   los servicios de memoria existentes.
4. Conservar Kwipu como proyección documental y evaluar Graphiti para
   relaciones e historial con consultas reales y métricas comparables.
5. Condicionar cualquier ampliación del backend a los resultados medidos.

Es una decisión de dirección, no evidencia de implementación ni de benchmark.
El siguiente bloque operativo sigue siendo hooks en los tres runtimes,
incluida la captura durable que sostiene la continuidad de memoria.

La [comparación S053–S054](comparisons/skills-session-learning-memory.md)
ya distingue captura por tool, propuestas pequeñas con trigger/evidencia y
evolución hacia piezas reutilizables. Parte de la automatización anunciada
no está implementada; el observador puede archivar eventos que no analizó.
Conservar lo útil exige lotes confirmados, procedencia y revisión; frecuencia
o confianza declarada no equivalen a aprobación ni calidad calibrada.

| Componente | Contrato observado | Valor y límite para el bloque |
|---|---|---|
| Journal/ledger | Continuidad y registro del trabajo | Capturar y retomar con fuentes; no convertir todo el historial en instrucciones |
| Markdown curado | Conocimiento versionado y estados explícitos | Mantener como base canónica; precisar propuesta, persistencia y aprobación |
| Kwipu | `markdown_export.py` publica y verifica; no expone `consultar`/`puede_leer` | Proyección documental; el plugin no obtiene recuperación enrutada mediante este adaptador |
| Graphiti | `consultar` y `puede_leer`, con modo `read`, salud y verificación | Candidato para relaciones y vigencia; requiere medir utilidad/coste en este proyecto |
| Aprendizaje de sesión | Captura y candidatos con trigger/acción/evidencia | Complementar la memoria curada; no activar otro escritor ni aprobación automática |

Fuentes propias contrastadas por lectura dirigida:
[exportador Kwipu](../../../skills/knowledge-services/backends/markdown_export.py),
[adaptador Graphiti](../../../skills/knowledge-services/backends/graphiti.py),
[router](../../../agent-kits/shared/knowledge-find.py) y
[reconciliación propuesta](../../knowledge/adr/ADR-020-graphiti-reconciliador-explicito-y-episodios-sin-uuid.md).
El router exige consulta/permiso de lectura, acota al grupo de proyecto y
degrada a local ante indisponibilidad. Esto describe código leído, no una
conexión actual ni una prueba de eficacia. La documentación de
[knowledge-services](../../../skills/knowledge-services/SKILL.md) conserva
texto que presenta Graphiti como futuro y la consulta como externa, pese a
esas funciones existentes; T-07/T-15 deben reconciliarlo con el contrato real.

[Graphiti oficial](https://github.com/getzep/graphiti) documenta relaciones,
procedencia y vigencia temporal con recuperación híbrida; requiere operar
la infraestructura y comprobar el rendimiento de la instalación propia.
No se atribuyen al adaptador todas las capacidades del framework por nombre.

La medición de fase 4 debe comparar el mismo conjunto de consultas sobre
decisiones vigentes, cambios históricos, evidencias y retoma del trabajo:
aciertos con fuente, errores obsoletos o de otro proyecto, omisiones, latencia,
contexto y coste observado. Incluir revocación, reconstrucción, duplicados,
backend caído y respaldo local. La prueba de publicación no sustituye este
benchmark. No se activan servicios, conectan cuentas o cambian datos de memoria
por esta valoración; la selección del backend queda condicionada a resultados.
