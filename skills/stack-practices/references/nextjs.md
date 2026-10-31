# Next.js: router, datos y fronteras

Comprueba `next`, React, TypeScript y runtime en package.json/lockfile. Identifica
App Router, Pages Router o convivencia por ruta antes de mover datos, layouts o
API. No aplica una API de App Router a Pages Router ni migra el router por defecto.

En App Router, usa componentes de servidor para trabajo que deba permanecer allí
y una frontera cliente acotada para interacción. Un módulo marcado `use client`
incorpora su grafo importado a esa frontera: evita arrastrar secretos o acceso a
datos. Lo renderizado o pasado al cliente debe contener solo campos autorizados.

| Situación | Criterio | Escenario que lo comprueba |
|---|---|---|
| Server Action o Route Handler escribe | Validar entrada, identidad y permiso por recurso en el servidor | Invocar directamente con otro ID de recurso no elude permisos |
| Dato por usuario/tenant | Elegir caché, ámbito e invalidación con el contrato de la versión | Dos usuarios no ven la respuesta cacheada del otro |
| Mutación seguida de navegación | Reconciliar e invalidar lo pertinente sin asumir frescura automática | El usuario ve el estado confirmado tras escribir y volver |
| Render inicial | Evitar usar hora/browser/storage de forma distinta en servidor y primer render cliente | Hidratación consistente sin ocultar avisos |
| UI durante carga o error | Estados de segmento y formulario acordes con su frontera | Un fallo deja recuperación accesible sin filtrar detalle interno |

Comprueba las reglas de caché de la major y configuración reales, incluido si usa
Cache Components. No asumas un default de `fetch` de una versión anterior ni mezcles
el modelo previo con el nuevo. Si el entorno es Edge, verifica compatibilidad de
dependencias con ese runtime; un build Node no acredita ejecución Edge.

Reutiliza `frontend-quality` y la guía React para interacción; no instala otro
fetcher ni presupone que el checker de Vite se aplica. Usa los comandos de tipos,
lint, build y pruebas ya definidos. Si el runner no soporta componentes de servidor
async, prueba el flujo con integración/E2E compatible en vez de fingirlo con un mock
de componente cliente. Verifica autorización en el servidor aunque el botón esté oculto.

Fuentes oficiales, 2026-10-30: [servidor/cliente](https://nextjs.org/docs/app/getting-started/server-and-client-components),
[seguridad de datos](https://nextjs.org/docs/app/guides/data-security) y
[caché](https://nextjs.org/docs/app/guides/caching). Consulta su versión y modelo
antes de aplicar una API; estos enlaces no fijan la major del consumidor.
