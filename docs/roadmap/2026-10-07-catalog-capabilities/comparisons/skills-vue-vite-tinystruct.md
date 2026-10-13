# Vue, Vite, conversión de capturas a Vue y tinystruct — S278, S281, S289, S290

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **46.985 bytes/1.335 líneas** y las seis referencias
de S278 leídas completas: **15.944 bytes/482 líneas**.
[vue-vite-tinystruct-reading-evidence.json](vue-vite-tinystruct-reading-evidence.json).
Nada se ejecutó ni se integró; no se instaló el conversor de S281. Propuestas para T-08.

## Decisión común

`stack-practices` cubre PHP/CodeIgniter, Python y React. Como con Java (S145–S148),
Go (S116–S117) y .NET, **no se abre especialidad Vue/Nuxt ni tinystruct hasta
que un consumidor declare el stack**; se anotan las correcciones para entonces.
La excepción parcial es Vite: es la herramienta de build habitual de los
proyectos React que el plugin ya atiende, y dos de sus reglas tienen hueco en la
referencia React existente.

## S289 — Patrones de Vite

`17.115 bytes/450 líneas`. Configuración, plugins, HMR, variables de entorno,
proxy, optimización del build, modo librería, SSR y errores frecuentes.

**Comparación.** `stack-practices/references/react.md` ya exige que «el bundle del
navegador no recibe secretos» y comprobar «React, router, build y librería de
tests reales», pero no concreta cómo se rompe eso en Vite. **Destino:** dos
líneas en esa referencia, aplicables solo si el manifiesto declara Vite:

- Toda variable con el prefijo público se incrusta en el bundle; `envPrefix: ''`
  o `loadEnv(mode, root, '')` seguido de `define` expone secretos del servidor.
- `vite build` transpila sin comprobar tipos: la verificación de un proyecto
  TypeScript incluye `tsc --noEmit` o equivalente.

Correcciones al resto:

| Ejemplo | Corrección |
|---|---|
| Alias `new URL('./src', import.meta.url).pathname` | En Windows produce `/C:/…` y codifica espacios como `%20`; usar `fileURLToPath` |
| `server.host: true` para contenedores | Expone el servidor de desarrollo a toda la red; limitarlo al contenedor o a la red de desarrollo |
| `server.fs.allow: ['..']` en monorepos | Amplía lo que el servidor sirve; enumerar paquetes concretos |
| Rolldown «desde v7», minificador `oxc` por defecto y `esbuild` «obsoleto» | Afirmaciones ligadas a versión; contrastar con la documentación de la versión instalada |

## S290 — Patrones de Vue 3 y Nuxt

`13.182 bytes/471 líneas`. Estructura, SFC, props/emits, composables, Pinia,
Vue Router, plantillas, rendimiento, pruebas, Nuxt y APIs de Vue 3.5.

**Comparación.** Sin consumidor declarado, igual que Nuxt 4 en S191
([skills-motion-next-nuxt.md](skills-motion-next-nuxt.md)); lo transversal (estado en el dueño
más próximo, respuestas fuera de orden, pruebas por rol accesible) ya está en
la referencia React y en `frontend-quality`. Correcciones para cuando se abra:

| Ejemplo | Corrección |
|---|---|
| Se activa para «Vue.js (cualquier versión)» | El contenido es solo Vue 3 (Composition API, `defineModel`, 3.5); en Vue 2 da consejos inaplicables |
| Se activa también por «Vite» | Colisiona con S289; Vite no implica Vue |
| `watch(id, (newId) => fetchItem(newId))` | Sin cancelación: la respuesta de un id anterior puede pisar la actual (mismo escenario que react.md) |
| Store `addItem` sin manejo de error | Contradice «toda acción asíncrona maneja carga, éxito y error» de la propia pieza |
| `v-html` saneado con DOMPurify como única defensa | Preferir texto interpolado; sanear solo cuando el HTML sea requisito |

## S281 — Capturas de diseño a componentes Vue

`4.809 bytes/135 líneas`. Conversión por lotes con un paquete npm que envía las
capturas a una API de modelo externa (DashScope).

**Comparación.** Ningún rol genera código desde imágenes. La pieza es prudente
(versión fijada, clave fuera del repositorio, permiso antes de enviar diseños de
clientes) y reconoce que no cubre accesibilidad ni lógica. Riesgo concreto: la
salida por defecto es `./src` del proyecto; generar en un directorio aparte y
revisar el diff antes de integrar. El código generado debe pasar las mismas
puertas que cualquier otro (`frontend-quality`, revisión de dos lentes).
**Sin destino.**

## S278 — Framework Java tinystruct

`11.879 bytes/279 líneas` más seis referencias. Aplicaciones con `@Action`
invocables por CLI y HTTP, `Builder`/`Builders` para JSON, persistencia con
`AbstractData`, SSE, subidas, eventos y herramientas MCP.

**Comparación.** Framework de nicho sin consumidor; se uniría a la futura
referencia Java (S145–S148). Lo transversal ya está en `backend-practices`
(autorización por recurso, errores, idempotencia). Correcciones:

| Ejemplo | Corrección |
|---|---|
| «Toda `@Action` debería funcionar en CLI y HTTP»; `Mode.DEFAULT` responde a cualquier método HTTP | Una acción con efectos queda accesible por `GET`; declarar el modo y proteger las acciones de administración |
| Login que guarda `userId` en la sesión existente | Regenerar el identificador de sesión al autenticar (fijación de sesión) |
| Subida que solo imprime el nombre del fichero | Límite de tamaño antes de leer, nombre generado por el servidor y almacenamiento fuera de la raíz servida (ya fijado en S080) |
| `database.user=root` y `database.password=secret` en `application.properties` | Credenciales fuera del fichero versionado y usuario con privilegios mínimos |
| `CompletableFuture.runAsync()` para trabajo pesado | Usa el pool común y pierde excepciones; ejecutor propio y registro del fallo |
| Sanear los argumentos de una herramienta MCP «para evitar inyección de prompt» | Ayuda, pero la salida de la herramienta sigue siendo dato no confiable para el modelo |
| Pruebas sobre el `ActionRegistry` singleton | Estado compartido entre tests; reiniciar o aislar el registro |

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S289 | Dos reglas con hueco en la referencia React | Dos líneas en `stack-practices/references/react.md` |
| S290 | Sin consumidor Vue | Correcciones anotadas |
| S281 | Generación externa sin rol | — |
| S278 | Java de nicho sin consumidor | Futura referencia Java |

Contraste oficial pendiente: guía de variables de entorno y de rendimiento de
Vite para la versión mínima que declare el consumidor.
