# Django: seguridad, pruebas y verificación previa — S080–S082

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **50.033 bytes/1.844 líneas**, cero recursos en sus
directorios. [django-security-testing-reading-evidence.json](django-security-testing-reading-evidence.json)
registra fuentes, contrapartes propias y contrastes oficiales. Los callers del
corpus (A017/A018) se leyeron solo en las líneas que citan estas piezas; no
cuentan como agentes evaluados. Nombres originales en el mapa privado;
[tasks.md](../tasks.md) es el ledger canónico. Las decisiones son propuestas para T-08.

No se ejecutaron código, snippets, tests del corpus, `manage.py`, escáneres ni
instalaciones. Nada de este bloque está integrado en producción. Este bloque
completa la tríada Django iniciada en S078–S079 y alimenta la especialidad
opcional `django-practices` propuesta allí.

## S080 — Seguridad de configuración y vistas Django

**Identidad.** SHA-256
`e043c9d300695aea5a9bb4c72a6f47e47ba1f2c7ddc1e82b8191acd0ad70c54a`,
17.269 bytes/644 líneas. Ajustes de producción, usuario custom, hashers,
sesiones, permisos de modelo/DRF, RBAC, ORM/raw, escape en plantillas, CSRF,
uploads, throttling, CSP, secretos y logging. A017/A018 la citan como checklist.

**Valor y cobertura existente.** `backend-practices/references/contracts-data.md`
ya fija autorización por recurso y tenant, CSRF/CORS no son autorización, allowlist
de búsqueda/orden y errores sin filtrar existencia. `cybersecurity` (nemesis) audita
OWASP/secretos/dependencias. Falta la traducción a ajustes y APIs de Django
por versión. El delta útil es esa capa de stack, no otra auditoría.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `SECURE_BROWSER_XSS_FILTER = True` y middleware con `X-XSS-Protection` | El ajuste se retiró en Django 4.0 y los navegadores ignoran la cabecera; quitarlo. Defensa de XSS = escape + CSP |
| `CSRF_COOKIE_HTTPONLY = True` presentado como protección | La documentación oficial dice que no aporta protección práctica y obliga a leer el token del formulario; el ejemplo AJAX lee la cookie y quedaría roto con ese mismo ajuste |
| CSP con constantes `CSP_*` y middleware propio con f-string | Desde Django 6.0 existen `SECURE_CSP`/`SECURE_CSP_REPORT_ONLY` y su middleware; en versiones previas, una librería mantenida. `'unsafe-inline'` en estilos anula parte del control; empezar en report-only |
| HSTS de un año con subdominios y preload desde el primer despliegue | Escalar `SECURE_HSTS_SECONDS`; subdominios y preload son difíciles de revertir según la propia documentación |
| `PostUpdateView` exige `can_edit_others` y además filtra por autor | Dos políticas contradictorias: el editor con permiso no edita lo ajeno y el autor sin permiso recibe 403. Decidir una regla y probar ambos actores |
| `IsVerifiedUser` asume `is_verified`; `IsOwnerOrReadOnly` compara `obj.author` | El campo no existe en el modelo del ejemplo y el permiso de objeto solo se evalúa en vistas de detalle: los listados necesitan su propio filtro de queryset |
| `escapejs` sin comillas dentro de `<script>` | Produce JavaScript inválido o inyectable; usar `json_script` |
| `format_html('…{}', escape(username))` | `format_html` ya escapa: doble escape visible. `mark_safe(escape(x))` solo cuando no exista alternativa |
| Validación de uploads por bytes mágicos y extensión | Útil, pero añadir límite antes de leer, nombre generado por el servidor, almacenamiento fuera de la raíz servida y `Content-Disposition`; los bytes mágicos no prueban que el fichero sea inocuo |
| RBAC con campo `role` además de grupos/permisos | Elegir un modelo de autorización; un segundo sistema paralelo diverge |
| `.env` de ejemplo con valores y `read_env()` en settings | No leer `.env` en producción por defecto; fallar sin secreto y no registrar valores |
| Rate limiting `upload: 10/hour` sin throttle que use ese scope | Declarar la clase que consume cada scope; el throttle no sustituye a la autenticación ni a cuotas de negocio |

**Destino propuesto.** Referencia `django-practices/references/security-settings.md`
dentro de la especialidad opcional de S078–S079, enlazada desde backend-practices;
lente C de `adversarial-review` y nemesis la leen solo con stack Django declarado.
Escenarios: anónimo frente a autenticado, autor frente a editor con permiso,
contenido con `</script>`, upload grande y con extensión engañosa, `check --deploy`.

## S081 — Pruebas Django y DRF con pytest-django

**Identidad.** SHA-256
`20bd5378fb9b76b396916daa8781dd45eef6336e5d4b3a46edb0c3e4eefaf074`,
21.031 bytes/730 líneas. Configuración pytest-django, settings de test,
fixtures, factory_boy, modelos, vistas, serializers, ViewSets, mocks, correo,
flujo de checkout, buenas prácticas y objetivos de cobertura. A018 la cita.

**Valor y cobertura existente.** `tdd` es la fuente única de RED-GREEN-REFACTOR
y `by-stack.md` ya da el comando de un test pytest; `stack-practices/python.md`
cubre fixtures, monkeypatch y separación unitario/contrato; `unit-tests` mide
cobertura oficial. No se crea otro método TDD. El delta es el contrato de la
base de datos de test en Django y los fixtures de DRF.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `--reuse-db` y `--nomigrations` siempre en `addopts` | pytest-django advierte que `--reuse-db` no recoge cambios de esquema; con `--nomigrations` el esquema sale de los modelos y las migraciones no se prueban. Mantener una ejecución de CI con migraciones y `--create-db` |
| SQLite en memoria como base de test | No reproduce bloqueos, tipos, restricciones ni `select_for_update` del motor real; contrastar con el motor del proyecto (coincide con backend-practices) |
| `CELERY_TASK_ALWAYS_EAGER` en todos los tests | Ya señalado en S078: eager no prueba worker, broker ni redelivery |
| Tests sin marca de base de datos (`test_product_creation()`) que usan factories | Fallan sin `db`/`django_db`; marcar o pedir el fixture |
| `MD5PasswordHasher` en tests | Aceptable solo en settings de test aislados; nunca compartidos con otros entornos |
| `product.price == 100.00` con `DecimalField` | Comparar `Decimal`; los floats introducen errores de redondeo |
| `test_deserialize_product` usa `category: 1` fijo | Depende del orden de creación; crear la categoría en el test |
| `test_update_product` usa `authenticated_api_client.user` | `APIClient` no expone ese atributo; pasar el usuario del fixture |
| Mock de `stripe.Charge.create` | API heredada del proveedor; probar el contrato del adaptador propio, no el SDK, y cubrir timeout tras cobro aceptado (backend-practices) |
| Flujo checkout con `patch` sin importar y modelos sin importar | Ejemplo no ejecutable tal cual |
| «Una aserción por test» y «no testear métodos privados» como reglas | Heurísticas; el plugin prioriza aserciones sobre el resultado y casos límite (`tdd/anti-patterns.md`) |
| Objetivos de cobertura por componente (80–90 %) | Ya existe `tests.coberturaMinima` con la herramienta oficial; no imponer cifras por capa |

**Destino propuesto.** `django-practices/references/testing.md`: elección
`db`/`transactional_db`/`live_server`, base real frente a SQLite, migraciones en
CI, `APIClient`/`force_authenticate`, `override_settings` y `mail.outbox`, y una
fila Django en `tdd/references/by-stack.md` con el comando de un único test.

## S082 — Bucle de verificación previo a PR y despliegue

**Identidad.** SHA-256
`01d2d2a8382737fefff259fe7624e1928e373a7772e220535dbea128373e81a2`,
11.733 bytes/470 líneas. Doce fases (entorno, calidad, migraciones, tests,
seguridad, comandos, rendimiento, estáticos, configuración, logging, esquema
API, diff), plantilla de informe y workflow de CI.

**Valor y cobertura existente.** Solapa con puertas ya existentes: `qa-gate.py`
(veredicto), `coverage-gate.py`, `scope-check.py`, `adversarial-review` (diff),
`dependency-upgrade`/nemesis (vulnerabilidades), `api-contract` (OpenAPI) y
delivery-practices (readiness y migraciones). Un segundo bucle de verificación
duplicaría el rol de `qa` (ADR-011). El delta aprovechable son los comandos
Django concretos como entradas de esos dueños.

| Ejemplo o afirmación del cuerpo | Adaptación necesaria |
|---|---|
| `ruff check . --fix`, `black .`, `isort .` dentro de «verificación» | Verificar no modifica; los autofix pertenecen al implementer, no a la puerta |
| `migrate` y `collectstatic --clear` en la verificación | Efectos sobre la base y el disco del consumidor; solo en entorno de test aislado y declarado |
| Crear superusuario por `manage.py shell` | Efecto con credencial en texto; fuera de una puerta de verificación |
| `makemigrations --merge` | Genera ficheros; decisión del implementer, no del verificador |
| `information_schema.statistics` para índices | Consulta de MySQL; no existe con ese esquema en PostgreSQL |
| «Menos de 50 consultas por página» | Umbral arbitrario; medir el crecimiento con el número de filas (patrón N+1 de backend-practices y lente D) |
| `settings.DEBUG` por `python -c` sin configurar Django | Falla sin `DJANGO_SETTINGS_MODULE`; usar `check --deploy` con el settings real |
| `safety check` junto a `pip-audit` | Dos escáneres con bases distintas; elegir el oficial del proyecto y nunca inventar una versión «latest» (dependency-upgrade) |
| Informe de ejemplo con cifras y ✓ | Las cifras deben salir de la ejecución real; ausencia de herramienta = no verificado, no ✓ |
| Workflow con acciones `@v3`/`@v4` y Postgres 14 | Fijar versiones vigentes según la política del proyecto |

**Destino propuesto.** Sin skill nueva. Una tabla «comandos Django por
dueño» en `django-practices/references/verification.md`: `check --deploy`
y `makemigrations --check --dry-run` como verificaciones de solo lectura que
`qa` y la lente A pueden pedir; lo demás se remite a los dueños existentes.

## Contrastes oficiales

- Django 6.1, referencia de ajustes: `SECURE_BROWSER_XSS_FILTER` ya no
  existe; `CSRF_COOKIE_HTTPONLY` «no ofrece protección práctica»;
  `SECURE_CSP`/`SECURE_CSP_REPORT_ONLY` nuevos en 6.0; advertencias de HSTS.
  [Settings](https://docs.djangoproject.com/en/stable/ref/settings/).
- pytest-django (latest): `--reuse-db` no recoge cambios de esquema;
  `--nomigrations` construye la base desde los modelos; `transactional_db`
  vacía la base entre tests. [Database access](https://pytest-django.readthedocs.io/en/latest/database.html).

Validación pendiente: carga nativa de la especialidad, escenarios ejecutados
contra un proyecto Django propio y versión mínima declarada por el consumidor.
