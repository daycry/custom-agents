# Regresiones por rama condicional

Léela solo cuando un cambio toque código que se comporta distinto según un
flag, el entorno o el proveedor (sandbox frente a real, un proveedor u otro), o
cuando un test verde no impidió un fallo en producción por una rama no
recorrida. El método de escribir el test primero es de `tdd`; la cobertura
medida, de `unit-tests`; la conformidad del payload con la spec, de
`skills/api-contract/references/contract-tests.md`; el estado de la interfaz
tras una mutación optimista, de `frontend-quality`.

## Matriz de ramas

Antes de escribir tests, lista las ramas que el cambio **reclama** cubrir:

| Dimensión | Valores | Qué cambia en el código |
|---|---|---|
| Flag | activado / desactivado / ausente en la configuración | Camino de ejecución, campos devueltos |
| Entorno | local, pruebas, producción (lo que el código distinga) | Proveedor elegido, timeouts, validaciones |
| Proveedor | sandbox, real, doble de prueba | Forma de la respuesta, errores, latencia |

Cada celda reclamada tiene un test que **ejecuta** esa rama. Una celda que no
se puede ejecutar (sin credenciales aisladas para el proveedor real, por
ejemplo) se declara «no ejecutada» en el ledger, no se da por cubierta. La
paridad sandbox/proveedor exige llamar a los dos con la misma entrada y
comparar el contrato; un test que solo llama al doble prueba el doble.

Un flag ausente de la configuración es un valor más: el código decide un
comportamiento por defecto y ese defecto se prueba.

## Forma y nulabilidad de los campos

- Las consultas y serializadores nombran sus campos; nada de `SELECT *` ni
  serializar el modelo entero. Una columna nueva en la tabla no debe aparecer
  en la respuesta sin un cambio de contrato.
- El test compara la lista exacta de campos de la respuesta y, por campo, si
  puede faltar, ser `null` o ser una colección vacía. Las tres cosas son
  distintas para el consumidor.
- Cada rama de la matriz devuelve la misma forma, salvo que el contrato
  declare la diferencia.
- Los errores de cada rama (timeout del proveedor, respuesta inválida, flag
  mal configurado) tienen su forma y estado probados, no solo el éxito.

## Fixtures que no dejan verdes vacíos

| Defecto | Por qué pasa en verde | Corrección |
|---|---|---|
| `if filas: assert …` | Con cero filas no se comprueba nada | Afirma primero la precondición (`assert len(filas) >= 1`) y después el contenido |
| Bucle de asserts sobre una lista vacía | El bucle no itera | Igual: precondición de tamaño antes del bucle |
| Fixture que no activa la rama | La rama reclamada nunca se ejecuta | La fixture contiene el dato que dispara cada rama (p. ej. un registro con el campo opcional ausente y otro con `null`) |
| Doble que devuelve siempre éxito | El camino de error no se recorre | Un caso por error que el proveedor real puede devolver |

## Estado, caché y rollback

- Tras una mutación, el test lee el estado por el mismo camino que el
  consumidor (incluida la caché) y comprueba el valor nuevo.
- Si la operación falla a mitad, el rollback deshace **esa operación**
  (transacción o compensación de lo que ella escribió). Restaurar una copia
  entera del estado anterior deshace también escrituras concurrentes válidas
  de otros usuarios.
- Con escrituras concurrentes, un caso con dos operaciones intercaladas
  comprueba que el resultado final respeta ambas o rechaza una de forma
  explícita (ver contratos y datos, filas de idempotencia e interbloqueo).

## Ejemplos por stack

Parametriza la matriz en vez de copiar el test por rama. Elige el del stack
del proyecto y adáptalo a la versión instalada:

```python
# pytest: decoradores apilados = producto cartesiano de la matriz
@pytest.mark.parametrize("proveedor", ["sandbox", "real"])
@pytest.mark.parametrize("flag", [True, False, None])
def test_contrato_por_rama(proveedor, flag, cliente):
    respuesta = cliente.pedir(proveedor=proveedor, flag=flag)
    assert set(respuesta.keys()) == CAMPOS_CONTRATO
```

```php
// PHPUnit: proveedor de datos público y estático, declarado por atributo
use PHPUnit\Framework\Attributes\DataProvider;

#[DataProvider('ramas')]
public function testContratoPorRama(string $proveedor, ?bool $flag): void { /* … */ }

public static function ramas(): array
{
    return ['sandbox con flag' => ['sandbox', true], 'real sin flag' => ['real', null]];
}
```

```ts
// Vitest/Jest: test.each sobre la matriz
test.each([
  ['sandbox', true],
  ['real', null],
])('contrato con proveedor %s y flag %s', async (proveedor, flag) => { /* … */ })
```

La celda «real» solo corre con credenciales aisladas; si no las hay, se marca
como omitida con motivo y cuenta como no ejecutada, nunca como aprobada.

## Fuentes

Consultadas el 2026-10-14:
[pytest — parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html),
[PHPUnit 12.4 — proveedores de datos](https://docs.phpunit.de/en/12.4/writing-tests-for-phpunit.html),
[Vitest — `test.each`](https://vitest.dev/api/).
