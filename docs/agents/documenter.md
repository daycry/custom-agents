# Agente: documenter

Genera y mantiene la **documentación técnica y de producto** de un proyecto, de forma
estructurada y detallada, bajo `docs/`. Explora el repositorio y produce documentación real
(con evidencia: rutas, clases, comandos), **derivando la estructura del propio proyecto** — no
impone nombres de carpeta.

## Qué hace

- **Recon** del repo (código, config, dependencias, scripts, CI, README/ADRs existentes) para
  fundamentar todo con datos reales.
- **Propone** una estructura de `docs/` con los nombres propios del proyecto (módulos / paquetes /
  servicios / componentes / dominios…) y pide confirmación antes de redactarlo todo.
- **Redacta** cubriendo las categorías que apliquen: índice/punto de entrada, índice de
  conocimiento para IA/RAG, arquitectura y decisiones, stack técnico, unidades del sistema
  (una página por módulo/componente según el reparto real del código), guías how-to y
  documentación de producto/usuario.
- **Índices**: mantiene el `README.md` de `docs/` (tabla de contenidos + inicio rápido + resumen
  de arquitectura/stack + comandos) y un `RAG-INDEX.md` (resumen denso por área para agentes IA),
  con "Última actualización".
- **Idempotente**: en reejecución actualiza lo afectado y crea lo que falte, sin aplastar contenido
  escrito a mano.

## Qué NO hace

- No implementa ni modifica el código del proyecto (solo lee).
- No gestiona `docs/roadmap/**` (es de `planner`/`evaluator`/`qa`): solo lo enlaza.
- No toca `docs/security-scan/**` (datos sensibles de `nemesis`).

## Estructura: derivada, no fija

No hay carpetas obligatorias. La organización de `docs/` se **deriva de cómo está partido el
repositorio** y de su vocabulario, respetando convenciones y docs existentes. El `docs/` del
proyecto webscorpo (CI4 modular) sirve de **referencia de estilo y nivel de detalle**, no como
esquema a clonar. Guía completa en `agent-kits/documenter/taxonomy.md`.

## Sincronización con Confluence (opt-in)

Tras escribir en `docs/`, invoca la skill compartida `confluence-publish` para reflejar los
cambios en Confluence. Es **opcional**: la primera vez se pregunta si se quiere sincronizar y la
decisión se guarda en `.claude/confluence.json` (`enabled: true/false`). Nunca sincroniza
`docs/security-scan/`.

## Dependencias

- Skill compartida: `confluence-publish` (sincronización de la doc generada).
- Kit privado: `agent-kits/documenter` (`taxonomy.md` + plantillas de formato).

## Uso

```
@documenter documenta el proyecto
@documenter genera la documentación técnica y de producto
@documenter actualiza los docs tras los últimos cambios
```

## Encaje con el resto

`documenter` cubre la **documentación de referencia** del proyecto (arquitectura, stack, unidades,
guías, producto), que vive directamente bajo `docs/`. La **cadena de iniciativas** (spec →
evaluación → plan → testing) la gestionan `evaluator`, `planner` y `qa` en `docs/roadmap/`.
Ambos mundos se sincronizan con Confluence mediante la misma skill `confluence-publish`.
