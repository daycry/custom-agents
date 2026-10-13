# FastAPI, verdad de facturación y entornos Flox — S101–S103

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **33.636 bytes/1.139 líneas**, sin recursos locales.
[fastapi-billing-flox-reading-evidence.json](fastapi-billing-flox-reading-evidence.json)
registra fuentes y contrapartes. Nada se ejecutó ni se integró. Propuestas para T-08.

## S101 — FastAPI con Pydantic v2 y SQLAlchemy async

`15.637 bytes/514 líneas`. Estructura, factoría y lifespan, pydantic-settings,
esquemas v2, dependencias, routers, capa de servicio transaccional, tests con
httpx y antipatrones.

**Comparación.** stack-practices/python cubre cancelación, fronteras y pruebas;
backend-practices, autorización por recurso, orden total en paginación y
transacción frente a servicio externo. El ejemplo ya aplica bien varios de esos
criterios (unicidad por restricción de base de datos en vez de comprobación
previa, `order_by` explícito, `response_model` para no filtrar campos, 401
frente a 403). El delta es la versión FastAPI de esos contratos.

| Ejemplo o afirmación | Adaptación |
|---|---|
| `create_all` en el lifespan «para dev» dentro de la factoría única | Lo hereda producción; las migraciones (Alembic) deben ser el único camino de esquema, con el `create_all` aislado en tests |
| `python-jose` y `passlib` | Proyectos con mantenimiento irregular; elegir librerías mantenidas según la política de dependencias del proyecto y verificar versión |
| JWT HS256 sin `aud`/`iss` y sin rotación de clave | Validar audiencia y emisor; plan de rotación de `secret_key` |
| `allow_credentials=True` con orígenes configurables | Con credenciales, nunca comodín; validar la lista en configuración |
| `env_file=".env"` siempre | En producción, variables del entorno; `.env` solo local |
| 400 para «email ya registrado» | 409 (conflicto) si el contrato lo permite; además revela qué cuentas existen: decidir según backend-practices (no filtrar existencia) |
| `get_db` hace rollback ante excepción pero no cierra transacciones abiertas sin excepción | La capa de servicio hace `commit`; documentar quién es dueño de la transacción para no mezclar commits en rutas y servicios |
| `update` aplica `setattr` para cualquier campo del payload | Lista de campos permitidos explícita, ya exigida por backend-practices para serialización |
| Tests con SQLite en memoria (`aiosqlite`) | Igual que en S081: no reproduce el motor real; marcar qué casos requieren el motor |
| Tests: fixture `setup_db` crea y borra tablas por test | Coste alto y no prueba migraciones; transacción por test sobre esquema migrado |

**Destino.** `stack-practices/references/python.md` gana una sección FastAPI
breve (lifespan sin esquema, dueño de la transacción, overrides en tests);
seguridad de tokens remite a backend-practices.

## S102 — Verdad de facturación frente al discurso comercial

`3.831 bytes/128 líneas`. Separar hecho de ingresos, impacto en clientes,
comportamiento real del código y recomendación; marcar snapshot o dato vivo.

**Comparación.** Operación de negocio sin rol en el plugin. Dos reglas
generales ya existen: distinguir dato vivo de snapshot (dashboard y
`usage-meter` marcan fuente medida/estimada) y no afirmar una capacidad que
el código no aplica (lente A: conformidad con el código, no con el texto).
El bloque S055–S060 ya decidió que la facturación del cliente se resuelve
con herramientas del proveedor. **Sin destino nuevo.**

## S103 — Entornos reproducibles con Flox

`14.168 bytes/497 líneas`. Manifiesto TOML, fijado de versiones, paquetes por
plataforma, recetas por lenguaje, hooks y profile, servicios, compartición y
uso por agentes sin sudo.

**Comparación.** El plugin no gestiona toolchains del consumidor;
`dependency-upgrade` inventaría manifiestos sin instalar y `/doctor` detecta
herramientas. Flox es una alternativa más (como contenedores o gestores por
lenguaje). Puntos a tener en cuenta si un proyecto lo usa:

| Afirmación | Adaptación |
|---|---|
| «Los agentes pueden instalar herramientas sin sudo» como ventaja | En el plugin, instalar es un efecto que requiere autorización del usuario (qa instala Playwright «bajo permiso»); que no haga falta sudo no la sustituye |
| Hook que hace `npm install` / `uv pip install` en cada activación con un fichero marcador | El marcador no detecta cambios del lockfile: dependencias obsoletas silenciosas; comparar hash del lockfile |
| Solo macOS y Linux | Sin soporte nativo de Windows; los proyectos de este usuario se ejecutan en Windows |
| `flox push` y entornos remotos con `[include]` | Dependencia de un servicio externo; fijar revisión |
| Servicios con `--host 0.0.0.0` en el ejemplo | Publicar en loopback salvo necesidad |

**Destino.** Detección de `.flox/env/manifest.toml` como manifiesto en
`dependency-upgrade` (inventario de solo lectura) y una línea informativa en
`/doctor`. Sin skill nueva.
