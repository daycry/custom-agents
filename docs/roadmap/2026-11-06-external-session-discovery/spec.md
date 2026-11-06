---
spec: external-session-discovery
estado: aprobada
---
# Sesiones nativas externas en el dashboard

Petición: comprobar con Claude CLI por qué una sesión de terminal no aparece en el dashboard de un proyecto de otro ordenador y cubrir Codex/OpenCode. Sin acceso a ese equipo, no se declara una prueba allí ni se modifican sus preferencias.

Diagnóstico confirmado: console_service sólo descubre Codex; Claude/OpenCode se marcan unsupported. Claude CLI 2.1.311 confirma la ausencia en revisión sólo lectura. El comando nativo agents --json --cwd está documentado y comprobado (exit0, array; sin conversaciones). OpenCode V2 dispone de GET /api/session para metadatos. Codex conserva thread/list exact-cwd y sus límites. Un contador vacío no puede afirmar cero si algún proveedor sigue desconocido.

Se implementa descubrimiento local de metadatos por interfaz nativa, acotado, sin turnos, transcript parsing, inferencia, adopción ni control de sesiones externas. Claude cubre las sesiones activas expuestas por agents --json, no todo el histórico. OpenCode usa servidor privado con lease existente y sólo GETs. Aislamiento exacto por raíz y configuración nativa; errores nunca se convierten en ausencia demostrada. No se conecta a otra máquina. No se añaden dependencias.
