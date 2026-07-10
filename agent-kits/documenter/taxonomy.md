# Guía de estructura de documentación (agente `documenter`)

**Principio rector: la estructura se DERIVA del proyecto, no se impone.** No hay nombres de
carpeta fijos. Estudia cómo está organizado el repositorio (sus módulos, capas, paquetes,
dominios, convenciones y su README/wiki si los hay) y refleja **esa** organización en `docs/`,
con los nombres y el agrupamiento que le sean naturales al proyecto y a su equipo.

El objetivo no es reproducir un esquema concreto, sino **cubrir unas categorías de contenido** y
que la navegación resulte obvia para quien conoce el proyecto.

## Cómo decidir la estructura
1. Detecta el tipo de proyecto (backend modular, librería, CLI, frontend/SPA, monorepo, servicio,
   API…) y su vocabulario propio (¿habla de "módulos", "paquetes", "servicios", "componentes",
   "features", "dominios"?). **Usa ese vocabulario** para nombrar las carpetas.
2. Sigue las convenciones existentes: si el repo ya tiene una carpeta/wiki de docs o un README con
   secciones, respeta esos nombres y amplíalos; no los renombres por gusto.
3. Agrupa por cómo está partido el código realmente (por capas, por dominios, por paquetes…), no
   por una plantilla externa.
4. Profundidad proporcional al tamaño: proyectos pequeños → menos carpetas (incluso todo en pocos
   ficheros); grandes → subcarpetas por área. No crees carpetas vacías ni secciones de relleno.

## Categorías de contenido a cubrir (nómbralas según el proyecto)
Asegura que la documentación cubre, cuando aplique, estas **intenciones** (el nombre de carpeta/
fichero lo eliges tú a partir del proyecto):

- **Índice / punto de entrada** — visión general, para qué sirve, inicio rápido (requisitos,
  instalación, primer arranque), resumen de arquitectura y stack, comandos esenciales, y un
  cierre con "Última actualización: <fecha>". (Suele ser `docs/README.md`.)
- **Índice de conocimiento para IA/RAG** — un resumen denso por área con "fuente: <ruta>", pensado
  para recuperación por agentes. (Suele ser `docs/RAG-INDEX.md`.)
- **Arquitectura y decisiones** — capas/flujo (request→response o flujo de datos), patrones
  detectados, decisiones clave con su porqué, estructura de directorios.
- **Stack técnico** — tecnologías con versión y propósito; una página por pieza relevante.
- **Unidades del sistema** — una página por cada unidad según como esté partido el código
  (módulo / paquete / servicio / componente / dominio…): propósito, responsabilidades, API
  pública, dependencias y ejemplos.
- **Guías de desarrollo (how-to)** — setup, autenticación, testing, performance, seguridad,
  "cómo añadir X", estilo de código… las que apliquen.
- **Producto / usuario** — qué es y para quién (lenguaje llano), guías de uso, casos de uso y FAQ.

No todas aplican a todo proyecto: incluye las que tengan sentido y **declara en el índice** las
que se omiten y por qué (una línea).

## Referencia (NO copiar literalmente)
`docs/` del proyecto webscorpo (CI4 modular) es un buen ejemplo de resultado: índice + RAG-INDEX +
carpetas por arquitectura, stack, módulos, guías. Sirve para ver **el nivel de detalle y el estilo**
esperados, no como esquema a clonar: otro proyecto tendrá otras carpetas y otros nombres.

## Enlaces con el resto del repo
- Si existe `docs/roadmap/` (spec → evaluación → plan → testing, de `planner`/`evaluator`/`qa`),
  **enlázalo** desde el índice; no lo reescribas.
- **Nunca** documentes ni toques `docs/security-scan/` (datos sensibles de `nemesis`).

## Principios de contenido (siempre)
- Cada afirmación con **evidencia**: ruta de fichero, clase/función, comando real. Lo no
  verificable se marca `⚠️ verificar`.
- Ejemplos de código reales (con su ruta), tablas para versiones/comparativas, diagramas ASCII
  simples para flujos.
- Dos audiencias: contenido técnico para desarrolladores; contenido de producto en lenguaje llano.
- Markdown válido: línea en blanco antes de listas y tras encabezados; tablas correctas.
