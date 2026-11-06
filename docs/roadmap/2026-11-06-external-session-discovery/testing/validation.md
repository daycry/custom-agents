# Diagnóstico y evidencia

Fase 1: servicio sólo despacha Codex y declara unsupported para Claude/OpenCode; documentación y test existente lo confirman. Fase 2: no es una sesión propia perdida ni prueba de fallo remoto: falta la capacidad. Claude CLI Sonnet leyó el código, entregó diagnóstico estructurado; reconoce que no revisó completo OpenCode/transporte/JS. No se aceptan sus hipótesis de UI sin contrastar.

Fase 3: CLI instalada Claude2.1.311 agents --help declara JSON con sesiones interactivas y background; agents --json --cwd del checkout aislado devuelve array y exit0. Metadatos únicamente, sin leer transcripts o configuraciones privadas. La documentación oficial agent-view confirma campos y alcance; OpenCode API V2 documenta session.list con filtro directory. El usuario sitúa el problema en otro equipo, que no se ha contactado. La sugerencia de Claude de ignorar proveedores no soportados al calcular complete se descarta: convertiría ausencia desconocida en cero demostrado.

Fuentes: https://code.claude.com/docs/en/agent-view ; https://dev.opencode.ai/v2/docs/api ; ayuda local de Claude2.1.311 y OpenCode2.0.12, 2026-11-06. La implementación usa estos contratos nativos y no un parser de archivos privados.

## Implementación y pruebas dirigidas

RED: 11 fallos de transporte/proveedores/servicio antes de implementar y un fallo del contador (otros dos casos pasaban). RED adicional de refresco fallido con cero antiguo: 1 failed/3 passed antes de corregir. GREEN: 87 tests Python de transporte, tres adaptadores, servicio, sesiones y límites; 4 Node de contador/deduplicación/refresco. Sin tests omitidos o asserts reducidos. Interop92 al día y handbook coherente. Sin código canónico agents/commands/hooks modificado.

Consulta real de metadatos, checkout aislado: status ok/complete true para Codex, Claude Code y OpenCode2.0.12, sin sesiones externas observadas en esa raíz (cero esperado sólo para esa consulta). No se crearon sesiones, turnos, prompts ni conversaciones; no se consultaron APIs de mensajes. Service.close dejó 0 auxiliares de descubrimiento registrados. No se infiere que la sesión del otro ordenador ya aparezca. No se ejecutó un servidor dashboard nuevo ni se usó un puerto de usuario; OpenCode usó su lease privado efímero.

Captura JSON comparte la propiedad de árboles de procesos del transporte existente, limita 1MiB y cuatro segundos en el proveedor Claude; exige exit0 y cierra también en timeout. OpenCode reutiliza bootstrap privado, sólo GET de versión y lista exacta no archivada, página200 con lectura parcial si queda cursor. Codex conserva thread/list y se incluye íntegra su regresión. Sin acceso a ficheros de transcripciones ni adopción de sesiones externas.

Selector: A+B+C; D false. Scope base1fd0460, 18 archivos dentro de alcance y sin exclusiones, avisos o criterios alterados. Revisión fresca completada; CI final registrada al cierre.

Propuesta de gotcha de debug-root-cause pendiente de persistir: no se accede a docs/knowledge privados en esta tarea. La causa y sus regresiones quedan en este ledger; no se promueve doctrina automáticamente.

## Cierre de revisión

Intento2 A+B+C verde en4aa985e, con ID background sin UUID/PID cubierto por RED1 y GREEN. Final dirigido: 88 Python +4 Node correctos; 120 comprobaciones vecinas de índice/skills/copias también correctas. Snapshot público ddf6cf3: linter0 errores/17 avisos existentes. Ledger-lint0/0, interop92 y handbook correctos. El registro del usuario no se modifica y no se publica versión.

CI de la implementación principal ddf6cf3: https://github.com/daycry/custom-agents/actions/runs/42199819856 — éxito. CI del último caso4aa985e: https://github.com/daycry/custom-agents/actions/runs/42201569592 — éxito. Los verdes previos no se confunden con la CI del head nuevo.

## CI de referencia y entrega

CI https://github.com/daycry/custom-agents/actions/runs/42201569592 en4aa985ec6dcffcc5c37a3dd9341669412c1cdb58: éxito, incluidas suites completas Python/Node, benchmark, linter, handbook, evals, interop, sintaxis y versiones. Python3.11: 10526 passed, 41 skipped, 87 subtests. Node22: 493 passed, 16 skipped, 0 failed (509 casos). Benchmark p95 2.13ms, p99 2.16ms. Las cifras se conservan junto al ledger; los skips de plataforma no se alteraron. Se mantienen los límites de rendimiento100/300ms.

Commits y push en fix/audit-remediation; PR30 actualizada, sin merge, release ni publicación npm. La comprobación en el otro ordenador requiere instalar la actualización y reiniciar su dashboard en el mismo usuario/entorno, con raíz exacta y runtime permitido. No se afirma que se haya realizado esa comprobación ni se pide copiar conversaciones. Las interfaces de inventario no dan control de chat sobre sesiones externas.
