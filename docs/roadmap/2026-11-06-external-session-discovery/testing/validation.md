# Diagnóstico y evidencia

Fase 1: servicio sólo despacha Codex y declara unsupported para Claude/OpenCode; documentación y test existente lo confirman. Fase 2: no es una sesión propia perdida ni prueba de fallo remoto: falta la capacidad. Claude CLI Sonnet leyó el código, entregó diagnóstico estructurado; reconoce que no revisó completo OpenCode/transporte/JS. No se aceptan sus hipótesis de UI sin contrastar.

Fase 3: CLI instalada Claude2.1.311 agents --help declara JSON con sesiones interactivas y background; agents --json --cwd del checkout aislado devuelve array y exit0. Metadatos únicamente, sin leer transcripts o configuraciones privadas. La documentación oficial agent-view confirma campos y alcance; OpenCode API V2 documenta session.list con filtro directory. El usuario sitúa el problema en otro equipo, que no se ha contactado. La sugerencia de Claude de ignorar proveedores no soportados al calcular complete se descarta: convertiría ausencia desconocida en cero demostrado.

Fuentes: https://code.claude.com/docs/en/agent-view ; https://dev.opencode.ai/v2/docs/api ; ayuda local de Claude2.1.311 y OpenCode2.0.12, 2026-11-06. La implementación usa estos contratos nativos y no un parser de archivos privados.

## Implementación y pruebas dirigidas

RED: 11 fallos de transporte/proveedores/servicio antes de implementar y un fallo del contador (otros dos casos pasaban). RED adicional de refresco fallido con cero antiguo: 1 failed/3 passed antes de corregir. GREEN: 87 tests Python de transporte, tres adaptadores, servicio, sesiones y límites; 4 Node de contador/deduplicación/refresco. Sin tests omitidos o asserts reducidos. Interop92 al día y handbook coherente. Sin código canónico agents/commands/hooks modificado.

Consulta real de metadatos, checkout aislado: status ok/complete true para Codex, Claude Code y OpenCode2.0.12, sin sesiones externas observadas en esa raíz (cero esperado sólo para esa consulta). No se crearon sesiones, turnos, prompts ni conversaciones; no se consultaron APIs de mensajes. Service.close dejó 0 auxiliares de descubrimiento registrados. No se infiere que la sesión del otro ordenador ya aparezca. No se ejecutó un servidor dashboard nuevo ni se usó un puerto de usuario; OpenCode usó su lease privado efímero.

Captura JSON comparte la propiedad de árboles de procesos del transporte existente, limita 1MiB y cuatro segundos en el proveedor Claude; exige exit0 y cierra también en timeout. OpenCode reutiliza bootstrap privado, sólo GET de versión y lista exacta no archivada, página200 con lectura parcial si queda cursor. Codex conserva thread/list y se incluye íntegra su regresión. Sin acceso a ficheros de transcripciones ni adopción de sesiones externas.

Selector: A+B+C; D false. Scope base1fd0460, 17 archivos dentro de alcance y sin exclusiones, avisos o criterios alterados. Revisión fresca y CI pendientes.

Propuesta de gotcha de debug-root-cause pendiente de persistir: no se accede a docs/knowledge privados en esta tarea. La causa y sus regresiones quedan en este ledger; no se promueve doctrina automáticamente.
