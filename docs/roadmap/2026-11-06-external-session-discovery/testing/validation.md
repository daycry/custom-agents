# Diagnóstico y evidencia

Fase 1: servicio sólo despacha Codex y declara unsupported para Claude/OpenCode; documentación y test existente lo confirman. Fase 2: no es una sesión propia perdida ni prueba de fallo remoto: falta la capacidad. Claude CLI Sonnet leyó el código, entregó diagnóstico estructurado; reconoce que no revisó completo OpenCode/transporte/JS. No se aceptan sus hipótesis de UI sin contrastar.

Fase 3: CLI instalada Claude2.1.311 agents --help declara JSON con sesiones interactivas y background; agents --json --cwd del checkout aislado devuelve array y exit0. Metadatos únicamente, sin leer transcripts o configuraciones privadas. La documentación oficial agent-view confirma campos y alcance; OpenCode API V2 documenta session.list con filtro directory. El usuario sitúa el problema en otro equipo, que no se ha contactado. La sugerencia de Claude de ignorar proveedores no soportados al calcular complete se descarta: convertiría ausencia desconocida en cero demostrado.

Fuentes: https://code.claude.com/docs/en/agent-view ; https://dev.opencode.ai/v2/docs/api ; ayuda local de Claude2.1.311 y OpenCode2.0.12, 2026-11-06. La implementación usa estos contratos nativos y no un parser de archivos privados.
