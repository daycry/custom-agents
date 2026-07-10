# agent-kits/documenter — toolkit privado del agente `documenter`

Recursos para generar documentación estructurada de un proyecto bajo `docs/`. Uso interno del
agente `documenter`.

- `taxonomy.md` — **guía de estructura**: cómo DERIVAR la organización de `docs/` a partir del proyecto (no impone nombres de carpeta) y qué categorías de contenido cubrir.
- `templates/` — plantillas **genéricas** de formato (no atadas a nombres de sección): `index.template.md` (índice/punto de entrada), `rag-index.template.md` (índice para IA/RAG), `section-index.template.md` (README de una carpeta) y `page.template.md` (página de contenido reutilizable para arquitectura, stack, unidad del sistema, guía o producto). El agente las copia y rellena; sustituye TODOS los `{{PLACEHOLDER}}` y borra los comentarios guía `<!-- ... -->`.

Salida siempre bajo `docs/` (nunca `docs/roadmap/**` ni `docs/security-scan/**`). Los docs
generados se sincronizan con Confluence (opt-in) vía la skill compartida `confluence-publish`.

**Documentación completa:** [`docs/agents/documenter.md`](../../docs/agents/documenter.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)
