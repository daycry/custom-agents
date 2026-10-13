# Familia Laravel: patrones, paquetes, seguridad, TDD y verificación — S155–S159

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **65.852 bytes/2.449 líneas**, sin recursos locales.
[laravel-family-reading-evidence.json](laravel-family-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó el servidor MCP de S156. Propuestas para T-08.

## Decisión común

Laravel es PHP, pero el consumidor declarado es **CodeIgniter 4**
(`stack-practices/references/php-codeigniter.md`). No se abre una especialidad
Laravel hasta que un consumidor la declare; entonces estas cinco piezas se leen
juntas como `php-laravel.md`, con las correcciones de abajo. Lo que es PHP o
backend genérico ya tiene dueño: allowlist de campos frente a autorización y
CSRF por ruta en `php-codeigniter.md`; autorización por recurso, errores,
paginación y migraciones compatibles en `backend-practices/references/contracts-data.md`;
el ciclo y la evidencia del rojo en `tdd` (su `by-stack.md` ya trae phpunit y
pest); cobertura en `unit-tests`; dependencias vulnerables en `nemesis`
(`dependency-upgrade` excluye CVE de forma explícita).

Defecto transversal: las cinco piezas mezclan generaciones del framework.
`$routeMiddleware` del `Kernel`, `RouteServiceProvider::HOME` y el registro en
`AuthServiceProvider` conviven con funciones que la propia pieza atribuye a
Laravel 10–11. Cualquier adopción empieza por fijar la versión del `composer.lock`
del consumidor, como ya exige `php-codeigniter.md` para CI4.

## S155 — Patrones de arquitectura Laravel

`10.664 bytes/416 líneas`. Controlador → servicio → acción, bindings con
ámbito, Eloquent con casts y scopes, objetos de consulta, migraciones,
FormRequest con DTO, recursos API, colas y caché.

| Ejemplo | Corrección |
|---|---|
| Sobre `{success, data, error, meta}` en cada respuesta | `contracts-data.md`: un envoltorio `data` no mejora por sí mismo un contrato existente; además construye a mano un `meta` que el recurso paginado ya genera |
| `scopeActive` y, más abajo, un global scope `active` en el mismo modelo | La pieza advierte «uno u otro, no ambos» y sus dos ejemplos hacen ambos |
| `foreignId('customer_id')->constrained()->cascadeOnDelete()` en pedidos | Borrar un cliente borra sus pedidos; decisión de dominio, no valor por defecto (misma nota que S145 con `cascade = ALL`) |
| «Scoped bindings para impedir el acceso entre tenants» | Garantizan la relación padre-hijo, no la autorización; la propia pieza lo matiza en «How It Works» |

## S156 — Descubrimiento de paquetes vía LaraPlugins MCP

`6.393 bytes/230 líneas`. Búsqueda por palabra clave, salud, versión de Laravel
o PHP y proveedor; detalle con historial de versiones.

**Comparación.** Es un canal opcional de `research-first`, como Exa (S099) y
Context7 (S085). Choca con dos de sus reglas: «no uses popularidad ni un score
agregado como sustituto de adecuación» frente a «filtra siempre por salud» y
«prefiere proveedores conocidos»; y «un canal sin acceso no es un resultado
vacío». Defectos: el ejemplo de búsqueda «authentication» devuelve un paquete de
permisos (autorización) y un kit de arranque; la tabla de versiones («13 latest»,
«5–9 deprecated») caduca sin fecha; la configuración va al fichero global del
usuario. La puntuación de salud de un tercero es un dato, no un veredicto.

**Destino:** ninguno sin consumidor Laravel; con él, fila de canal en
`research-first` con esas tres salvedades.

## S157 — Seguridad en Laravel

`26.556 bytes/948 líneas`. Configuración de producción, Sanctum, contraseñas,
sesión, gates y policies, asignación masiva, inyección SQL, CSRF, XSS,
cabeceras, validación, rate limiting, CORS, ficheros, secretos, colas y log.

**Comparación.** `nemesis` (SAST de ocho dimensiones) es el dueño de la
auditoría; lo útil son criterios de implementación para cuando exista la
especialidad. Varios ejemplos son incorrectos:

| Ejemplo | Corrección |
|---|---|
| Regla `'sanitize_html'` en `rules()` | No es una regla del framework; la validación falla por método inexistente |
| `$user->wasRecentlyLockedOut()` bajo «Rate limit login attempts» | Método inventado y el bloque no limita nada |
| `tokenCan('read')` como control en rutas `auth:sanctum` | Con autenticación de SPA por cookie, `tokenCan` devuelve verdadero siempre; las abilities no sustituyen a la policy |
| `X-XSS-Protection: 1; mode=block` | Cabecera obsoleta; no añadirla o enviarla a `0` |
| `Storage::temporaryUrl(...)` antes de `$this->authorize('download', $path)` | Se genera la URL antes de autorizar, y la policy recibe una cadena en vez del modelo |
| `composer why-not` para «paquetes abandonados» | Explica por qué no se instala una versión; el abandono lo informan `audit`/`outdated` |
| `env $(aws secretsmanager …) php artisan serve` como despliegue | Servidor de desarrollo; secretos en la línea de órdenes |
| `trusted_proxies` en `config/app.php` | Se configura en el middleware de proxies de la versión instalada |
| `StrongPassword` por regex con juego de caracteres cerrado | Rechaza espacios y Unicode y duplica `Password::min(12)->…` de la misma pieza |
| `APP_KEY` ausente lanza excepción; secretos de Stripe ausentes solo se registran | Criterio de arranque incoherente |
| `SecurityLogger` guarda email, IP y user-agent de cada intento | Datos personales en log: redactar o seudonimizar |
| Sobrescribir `validated()` con `strip_tags` | Modifica el dato guardado; la defensa es escapar en la salida |

## S158 — TDD en Laravel

`17.863 bytes/675 líneas`. Configuración de PHPUnit, TestCase base, factories,
pruebas de modelo, HTTP, JSON, Sanctum, fakes, Artisan, autorización y Pest.

**Comparación.** El método es el de `tdd`; aporta pruebas de autorización
(«el atacante recibe 403 sobre el recurso del dueño»), que ya pide
`contracts-data.md`.

| Ejemplo | Corrección |
|---|---|
| Primer rojo: crear con la factory y comprobar la fila | Prueba la factory y la migración, no un comportamiento; en `tdd` es un assert trivial |
| `DB_CONNECTION=sqlite`, `:memory:` como base de pruebas | `contracts-data.md`: SQLite no demuestra el comportamiento de MySQL/PostgreSQL; separar unitarias y persistencia con el motor real |
| `QUEUE_CONNECTION=sync` | Oculta serialización y reintentos del trabajo en cola |
| Objetivos por componente (modelos 95 %, policies 95 %…) | Umbral del proyecto (`tests.coberturaMinima`), no universal |
| «Una aserción lógica por test» | Los ejemplos de la propia pieza encadenan varias |

## S159 — Bucle de verificación Laravel

`4.376 bytes/180 líneas`. Entorno, Composer, Pint, PHPStan o Psalm, tests con
cobertura, `composer audit`, migraciones en `--pretend`, cachés de despliegue,
colas y planificador, con prueba activa en staging.

**Comparación.** Equivale a las puertas propias: `qa-gate` y `coverage-gate`
dan el veredicto; `nemesis` las dependencias; la compatibilidad de migraciones
está en `contracts-data.md`. Coincide en parar ante el primer fallo y en
verificar el efecto real del trabajo de prueba, no solo su encolado. Correcciones:
`config:cache`/`route:cache` en una máquina de desarrollo dejan configuración
cacheada que ignora cambios posteriores del `.env`, por lo que se ejecutan en el
artefacto de build; `dump-autoload -o` modifica `vendor/` durante una
«verificación»; el despacho de prueba con `tinker` es un efecto en staging que
requiere autorización.

**Destino S155–S159:** sin especialidad mientras no haya consumidor Laravel; las
tablas quedan como correcciones. Nada nuevo para `php-codeigniter.md`: sus
reglas de allowlist, CSRF y transacciones ya cubren lo genérico de PHP.
