---
name: plugin-panel
description: >
  Genera un control panel local del catálogo de custom-agents: agentes, skills,
  comandos, herramientas declaradas, hooks globales y presencia de fuentes de
  runtime y memoria. HTML autónomo con búsqueda y filtros, JSON determinista,
  sin servidor ni cambios de configuración. Úsala cuando el usuario diga
  "panel de capacidades", "control panel del plugin" o "explora el catálogo del plugin".
---

# Plugin panel

Presenta lo que contiene el bundle. El estado de las iniciativas lo muestra
la skill roadmap-dashboard; este panel muestra capacidades.

1. Localiza esta skill en las raíces del bundle del runtime actual.
2. Ejecuta scripts/build_panel.py con Python nativo, `--root <bundle>` y
   `--html <salida>`. Añade `--json` si necesitas inventario estructurado.
3. Entrega el HTML y resume sus avisos. Un archivo presente no acredita que
   el hook se haya ejecutado ni que un servicio esté sano.

El generador solo lee frontmatters públicos y el registro global de hooks.
Muestra herramientas declaradas por los agentes, sin afirmar acceso a ellas
en esta sesión. De memoria solo muestra presencia de directorio aprobado y
artefacto Graphify; no lee entradas, grafos, transcripciones ni credenciales.
Usa el redactor del bundle. Sin él, avisa y no emite metadatos; continúa la tarea.
No sigue enlaces simbólicos. Solo reemplaza HTML reconocido como suyo.

| Recurso | Cuándo leerlo |
|---|---|
| [Uso y límites](../../docs/PLUGIN-PANEL.md) | Al explicar inventario, exportación y diferencias con el roadmap |

Inspiración funcional: catálogo de ECC 2.2.3. Implementación propia; no copia
su servidor, Tkinter, instalador ni control plane Rust.
