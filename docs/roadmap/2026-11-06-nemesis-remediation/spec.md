---
spec: nemesis-remediation
estado: aprobada
evaluacion: no-aplica
plan: improvement-plan.md
---
# Correcciones de seguridad y endurecimiento

Autorización: el usuario pide implementar las correcciones de Nemesis y lo que quede pendiente.
Se corrige F-001 (datos externos interpretados como HTML en vistas Atlassian) y se implementan O-001/O-002/O-003 como endurecimiento, sin convertirlas retroactivamente en vulnerabilidades demostradas.

Los metadatos se conservan como texto y el flujo de selección conserva sus valores. Configuración de plantillas serializada de forma segura. El conversor PDF usa sandbox, JavaScript desactivado y recursos externos bloqueados de forma predeterminada; cualquier excepción es explícita. CI limita secretos a pasos necesarios, referencias inmutables y permisos mínimos. El instalador opcional usa versiones y artefactos verificados, sin resolver latest durante ejecución ni modificar instalaciones ajenas.

No se prueban servicios reales, no se modifican preferencias privadas ni se publica una release/npm. Tests sintéticos, revisión independiente y CI verificable. Los informes privados de auditoría no se publican.
