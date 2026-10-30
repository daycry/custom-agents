# Prueba real de F3 con Ollama

Estado: **pendiente del usuario**. Esta ficha no acredita una ejecución.
Código candidato: `4596eaf1bec3f21b21d364d5493b92d072f71cac` de la PR21.
T-26 exige esta prueba en el otro equipo; los mocks y la revisión no la sustituyen.

## Preparar el caso

Usa un proyecto de prueba nuevo y el clon del candidato como fuente del plugin.
Anota `git rev-parse HEAD`, versión del cliente (OpenCode o Codex), Python y
`ollama --version`. El modelo debe ser el 32B que tengas disponible; sustituye
`ollama/<id-real>` por su id nativo. No se deduce su tamaño del nombre.

Configura el proveedor Ollama y selecciona el modelo de la sesión padre en el
cliente nativo. El JSON del plugin selecciona roles; no configura ese proveedor
ni cambia el modelo del hilo padre. Registra por separado contexto declarado por
el cliente, contexto observado con `ollama ps` y contexto efectivo del cliente
si existe evidencia. El mínimo orientativo de la vía rápida es 65.536 tokens;
un dato desconocido se conserva como desconocido.

Crea `.claude/dev.json` en el proyecto de prueba:

```json
{
  "perfil": "lite",
  "tdd": true,
  "subagentes": true,
  "paralelismo": true,
  "modelos": {
    "implementer": {"model": "ollama/<id-real>"},
    "reviewer": {"model": "ollama/<id-real>"},
    "qa": {"model": "ollama/<id-real>"}
  }
}
```

Los dos toggles true permiten comprobar que el perfil efectivo los desactiva.
Conserva cualquier umbral de cobertura propio del proyecto y su herramienta
oficial. No conviertas un gate sin ejecutar en un resultado verde.

Desde el clon del candidato, instala en ámbito de proyecto con el proveedor que
vayas a probar (sustituye las rutas de ejemplo por las de ese equipo):

```text
node install/install.mjs install -p opencode --scope project --dir <proyecto-prueba> --source <clon-candidato> --models-config .claude/dev.json
```

Para Codex usa `-p codex`. Conserva cualquier conflicto que informe el instalador;
anótalo, sin forzar bindings ni registros ajenos. Contrato de instalación y
proveedor: [INTEROP](../../../INTEROP.md).

Desde el shared del bundle localizado, ejecuta contra el proyecto de prueba:

```text
python execution-profile.py --project <proyecto-prueba> --json
python doctor.py --root <proyecto-prueba> --runtime opencode --json
```

Resultado esperado del perfil: lite, techo 6000, subagentes/paralelismo false,
writer disponible y requerido, reviewers fresh_sequential, revisión y qa_gate
true. Para Codex cambia el runtime. Si solicitas el sondeo, añade explícitamente
`--probe-ollama http://127.0.0.1:11434`: solo observa modelos ya cargados. Esa
observación no prueba el contexto efectivo de la sesión o de sus hijos.

## Ejecutar una vía rápida real

En ese proyecto, pide al cliente nativo:

> Implementa por vía rápida una función Python `sum_even(values)` en `even.py`.
> Suma los enteros pares de una lista, devuelve 0 para una lista vacía y rechaza
> booleanos con TypeError. Trabaja con perfil lite y TDD. Incluye tests para
> `[-2,3,4] -> 2`, `[] -> 0` y `[True,2] -> TypeError`; ejecútalos antes de
> implementar y registra el rojo. Conserva el ledger, revisión independiente
> con contexto fresco y QA. Ejecuta `python -m unittest -v` al verificar.

Observa y anota:

- Inferencia real en Ollama y modelo usado por el hilo padre y los roles
  ejecutados; no basta con que el JSON del plugin lo declare.
- Brief completo de hasta 6000 caracteres, o rechazo explícito si no cabe.
- Implementación en el hilo actual, sin implementadores delegados ni paralelos.
- RED observado antes del código y escritura del ledger mediante el writer.
- Revisores independientes frescos y secuenciales; lentes condicionales según
  el selector. QA ejecutada, con salida y veredicto propios.
- Tests finales, ledger-lint sin incoherencias y ausencia de procesos propios
  del caso que sigan trabajando al terminar o cancelar.

Un fallo o una limitación del modelo es un resultado válido de la prueba y
mantiene T-26 abierta. Esta muestra no certifica calidad universal del modelo.

## Devolver el resultado

Envía un resumen de texto con estos campos, sin conversaciones ni credenciales:

```text
SHA probado:
Cliente y versión / Python / Ollama:
Modelo real y tamaño conocido:
Contexto cliente declarado / servidor observado / cliente efectivo:
Instalación y perfil efectivo:
RED y tests finales (comando, resultado):
Implementación en hilo actual / revisión fresca secuencial / QA:
Ledger-lint / terminación de procesos propios:
Resultado: pasa / falla / parcial
Limitaciones observadas:
```

La versión de release se confirma después de disponer de los resultados y de
las demás puertas de T-26. Esta ficha no autoriza publicar.
