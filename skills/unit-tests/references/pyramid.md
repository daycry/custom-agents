# La pirámide de pruebas — detalle y ejemplos

Léelo desde `SKILL.md` solo si quieres el porqué con ejemplos concretos, no solo la tabla.

## Por qué la base es unitaria

Un test unitario aísla UNA unidad (función, clase, módulo) de sus dependencias externas. Cuando
falla, el mensaje señala la línea exacta: "la función `calcular_descuento` devuelve 12 cuando
debía devolver 10". Un test E2E que falla dice: "el checkout no funciona" — y alguien tiene que
bajar capa por capa hasta encontrar cuál de las 40 funciones implicadas es la culpable. Por eso la
proporción orientativa (más unitarios, menos integración, pocos E2E) no es dogma: es que el coste
de diagnóstico crece con la distancia entre el test y la causa.

## Integración — la capa que se suele saltar mal

No es "dos funciones llamándose" (eso ya lo cubre un test unitario con un stub). Es dos módulos
REALES juntos: el repositorio contra una base de datos real (o un contenedor efímero), el cliente
HTTP contra un servidor de pruebas, el productor y el consumidor de una cola. La pregunta que
responde: "¿el contrato que ambos módulos asumen es el mismo de verdad?". Ejemplo real: un
repositorio que devuelve `None` cuando no encuentra un registro, pero el servicio que lo llama
espera una excepción — cada uno por separado pasa sus tests unitarios (con mocks que respetan lo
que CADA test cree que es el contrato); solo un test de integración con la BD real lo detecta.

## E2E — cara, lenta, imprescindible para lo que solo se ve completo

Verifica el flujo desde donde lo ve la persona: clic, navegación, resultado visible. Cubre lo que
ningún test unitario puede: JavaScript roto en el navegador, un CSS que oculta el botón de enviar,
una migración de base de datos que no se aplicó en el entorno de pruebas. En este plugin lo hace
`qa` con Playwright sobre los escenarios `E2E-xx` del `test-plan.md`; el veredicto es mecánico
(`qa-gate.py`), no la impresión de quien mira las capturas.

## Anti-patrones — por qué fallan en la práctica (no solo en teoría)

### Test que replica la implementación

```python
# MAL — el test re-implementa la fórmula; si la fórmula tiene un bug, el test también lo tiene
def test_calcular_descuento():
    precio, pct = 100, 20
    esperado = precio - (precio * pct / 100)   # ← copia la lógica de producción
    assert calcular_descuento(precio, pct) == esperado

# BIEN — el test afirma el RESULTADO conocido, no recalcula la fórmula
def test_calcular_descuento_20_por_ciento_sobre_100():
    assert calcular_descuento(100, 20) == 80
```

Con la versión mala, si alguien cambia `calcular_descuento` para (incorrectamente) sumar en vez de
restar, y comete el MISMO error al "actualizar" el test para que compile, el test sigue en verde.

### Mocks de todo

```python
# MAL — mockea la propia función bajo prueba: el test no ejercita nada real
def test_procesar_pedido(mocker):
    mocker.patch("app.procesar_pedido", return_value=True)
    assert app.procesar_pedido(pedido) is True   # siempre pasa, pruebe lo que pruebe procesar_pedido

# BIEN — mockea solo lo EXTERNO (aquí, la pasarela de pago); la lógica propia se ejecuta de verdad
def test_procesar_pedido_rechaza_stock_insuficiente(mocker):
    mocker.patch("app.pasarela.cobrar", return_value={"ok": True})
    with pytest.raises(StockInsuficienteError):
        app.procesar_pedido(Pedido(cantidad=999))
```

### Asserts triviales

```python
# MAL — pasa con una lista vacía, con basura, con cualquier cosa que no sea None
def test_obtener_pedidos_usuario():
    assert obtener_pedidos_usuario(42) is not None

# BIEN — afirma el CONTENIDO que el criterio de aceptación promete
def test_obtener_pedidos_usuario_devuelve_solo_los_suyos():
    pedidos = obtener_pedidos_usuario(42)
    assert {p.usuario_id for p in pedidos} == {42}
    assert len(pedidos) == 3
```

### Tests que dependen del orden

```python
# MAL — test_actualizar_usuario solo pasa si test_crear_usuario corrió antes en la misma sesión
def test_crear_usuario():
    global usuario_id
    usuario_id = crear_usuario("ana")

def test_actualizar_usuario():
    actualizar_usuario(usuario_id, nombre="Ana")   # NameError si se ejecuta solo

# BIEN — cada test crea su propio estado (fixture), se puede ejecutar solo o en cualquier orden
def test_actualizar_usuario_cambia_el_nombre():
    usuario_id = crear_usuario("ana")
    actualizar_usuario(usuario_id, nombre="Ana")
    assert obtener_usuario(usuario_id).nombre == "Ana"
```

Un runner que paraleliza o reordena tests (habitual para acelerar CI) convierte este anti-patrón en
fallos intermitentes que nadie sabe reproducir — el síntoma clásico de "es que a veces falla".
