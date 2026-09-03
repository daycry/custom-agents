# Plantillas de tests de contrato (sugerencia, sin instalar)

Léelo desde `SKILL.md` **solo** al elegir o adaptar una plantilla para el stack del proyecto. Las
tres opciones verifican lo MISMO por caminos distintos: que la IMPLEMENTACIÓN cumple lo que la spec
OpenAPI promete (tipos, códigos de estado, campos obligatorios). Ninguna sustituye a
`openapi-lint.py` (que valida la SPEC en sí, sin tocar la implementación) ni a los tests E2E de
`qa-gate.py` (que verifican comportamiento de negocio, no conformidad de contrato).

## Python — `pytest` + `schemathesis`

`schemathesis` genera casos de prueba automáticamente A PARTIR de la spec (fuzzing dirigido por
schema: valores límite, tipos inválidos, combinaciones de parámetros) y los ejecuta contra un
servidor real o un `TestClient` en memoria.

```python
# test_contract.py — instalar antes: pip install schemathesis
import schemathesis

schema = schemathesis.from_path("openapi.yaml")  # o from_uri("http://localhost:8000/openapi.json")


@schema.parametrize()
def test_api_conforme_al_contrato(case):
    response = case.call()               # contra un servidor real levantado en el propio test
    case.validate_response(response)     # falla si el status/schema no casan con la spec
```

Para probar sin levantar un servidor (framework con `TestClient`, p. ej. FastAPI/Flask):

```python
@schema.parametrize()
def test_api_conforme_con_test_client(case):
    response = case.call_wsgi(app)       # o call_asgi(app) en frameworks async
    case.validate_response(response)
```

## Node — `dredd`

`dredd` compara la spec con la API real, endpoint por endpoint, usando los EJEMPLOS que la propia
spec declara (`example`/`examples` en cada `schema`) como fixtures de request/response.

```yaml
# dredd.yml — instalar antes: npm install -g dredd
reporter: cli
custom:
  apiaryApiKey: null
```

```bash
dredd openapi.yaml http://localhost:3000 --config dredd.yml
```

Sin ejemplos en la spec, `dredd` no tiene con qué generar requests — añade `example:` a los
`schema` de request/response antes de adoptarlo (documenta la API mejor de paso).

## Node — `prism`

`prism` (de Stoplight) cubre dos modos, útiles en fases distintas:

- **Mock server** — levanta un servidor falso desde la spec, para desarrollar el consumidor de la
  API ANTES de que exista la implementación real (contract-first en su forma más literal):
  ```bash
  npx @stoplight/prism-cli mock openapi.yaml
  ```
- **Proxy validador** — se pone DELANTE de la API real y valida cada request/response real contra
  el contrato; cualquier desviación aparece como error de `prism`, no como un bug silencioso:
  ```bash
  npx @stoplight/prism-cli proxy openapi.yaml http://localhost:8000
  ```

## Cuál elegir

| Si el proyecto… | Usa |
|---|---|
| Es Python y ya usa `pytest` | `schemathesis` — fuzzing automático, cero fixtures que mantener a mano |
| Quiere fixtures explícitos y legibles por no-programadores | `dredd` — un ejemplo por endpoint, directo desde la spec |
| Necesita desarrollar el consumidor antes de que exista el backend | `prism mock` |
| Quiere una red de seguridad continua sobre una API ya en producción | `prism proxy` delante del tráfico real |

Ninguna se instala automáticamente: copia el fragmento que encaje, ajusta rutas/puertos, y decide
con el equipo si entra en el CI (`ci.yml.MANUAL-COPY` es la copia manual del pipeline — añadir un
paso ahí es responsabilidad de quien adopte la plantilla, no de esta skill).
