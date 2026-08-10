# Guía de redacción por categoría — referencia de documenter

> Detalle que **documenter** lee **al entrar en P4 (Redacción)**, no antes. Progressive
> disclosure: fuera del prompt principal para no cargarlo en onboarding/recon.
> Complementa `taxonomy.md` (que decide la ESTRUCTURA); esto guía el CONTENIDO de cada categoría.

Cubre, con los nombres decididos en P3 (y solo las que apliquen), estas categorías. Incluye siempre fragmentos de código reales (con su ruta), diagramas ASCII simples cuando ayuden, y tablas. Marca lo incierto con `⚠️ verificar`; declara en el índice las categorías omitidas y por qué.

- **Arquitectura y decisiones** — capas / flujo (request→response o de datos), patrones detectados, decisiones con su porqué, estructura de directorios.
- **Stack técnico** — tabla de tecnologías (versión + propósito) y una página por pieza clave.
- **Unidades del sistema** — una página por unidad **según el reparto real del código** (módulo / paquete / servicio / componente / dominio…): propósito, responsabilidades, API pública, dependencias, ejemplos.
- **Guías how-to** — setup/instalación, autenticación, testing, performance, seguridad, "cómo añadir X"… según aplique.
- **Producto / usuario** — qué hace y para quién, guías de uso, casos de uso y FAQ, en lenguaje llano.

Índices (P5): el índice/punto de entrada (típicamente `docs/README.md`) lleva tabla de contenidos enlazada + inicio rápido + resumen de arquitectura y stack + comandos esenciales; el índice para IA/RAG (típicamente `docs/RAG-INDEX.md`) lleva un resumen denso por área con su "fuente: <ruta>" y la fecha de última actualización.
