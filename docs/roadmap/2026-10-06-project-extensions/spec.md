---
spec: project-extensions
estado: implementada
creado: 2026-10-06
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Extensiones propias del proyecto y del usuario

Fase 2 de la integración autorizada. El usuario pregunta cómo añadir agentes,
skills, personas, tools y MCP al proyecto y cómo los usaría el plugin. La fase 1
solo inventaría el bundle y usa un selector fijo. Se añade reconocimiento nativo
con trazabilidad para Claude Code, Codex y OpenCode, reutilizando el contrato de
especialización. La decisión técnica se toma bajo la delegación existente;
no se declara una nueva validación explícita del usuario sobre un diseño formal.

## Alcance y aceptación

1. Inventario local determinista de agentes, skills, comandos, personas, fuentes
   de tools y declaraciones MCP, tanto de proyecto como de usuario. Adaptadores
   por runtime, carpetas y formatos oficiales; subdirectorios hasta la raíz
   seleccionada y fuentes compatibles. Raíces personalizadas explícitas.
2. Cada resultado conserva nombre, tipo, runtime, scope, origen y referencia
   relativa. Duplicados y conflictos visibles, sin precedencia universal inventada.
   Nombres de roles del ciclo no se sustituyen automáticamente por extensiones.
3. Registro de propiedad O1 de project-specialization: se lee si existe, con hash
   LF normalizado; ausencia es no gestionada, corrupción avisa. Se distingue
   estado de propiedad de disponibilidad. El inventario es derivado y no crea
   otro registro persistente ni adopta piezas automáticamente.
4. Selección explícita por identidad estable y transferencia al ledger/brief;
   referencias acotadas, sin precargar cuerpos. Personas de proyecto mantienen
   prioridad y tipos libres. Los roles del ciclo, gates y límites no cambian.
5. Panel separa bundle y extensiones, permite buscar y filtrar por tipo/origen,
   muestra fuentes y conflictos. Un fichero/config detectado no demuestra carga,
   conexión, autenticación ni permiso. La sesión contrasta sus capacidades reales
   antes de invocar; no se simula disponibilidad con entradas de un fichero.
6. Nunca ejecutar/importar piezas del consumidor, lanzar CLI, conectar MCP,
   resolver env/file placeholders ni modificar configuración del usuario durante
   el descubrimiento. No exportar comandos, args, URLs, headers, env, tokens,
   prompts completos o configuración privada. Redacción central antes de salida;
   bytes/profundidad/número de piezas acotados, enlaces excluidos y avisos claros.
7. Integración en el fragmento común, work-context, briefs y plugin-catalog;
   exports generados y docs ES/EN actuales. No cadenas ni catálogos duplicados.
8. TDD con RED real, cobertura del diff ≥90 %, Windows/Linux/Edge y revisión
   A+B con C/D según selector; cero gaps introducidos al cierre, retro y push
   comprobado. Settings existentes del usuario permanecen sin tocar.

La adopción/generación/reconstrucción de piezas de project-specialization F2
conserva su plan independiente; este inventario no promete que se haya entregado.
No se crean nuevos paquetes técnicos. No se importa toda una biblioteca por
cantidad y no se publican referencias a su marca. Fuentes oficiales verificadas
en contracts.md, sin convertir instrucciones externas en política del plugin.
