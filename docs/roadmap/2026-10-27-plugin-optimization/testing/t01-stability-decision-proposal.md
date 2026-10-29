# T-01: decisión pendiente sobre la estabilidad de la línea base

Fecha: 2026-10-29. **Propuesta sin aprobar ni aplicar.** El ajuste aprobado de CA-01
no autoriza este cambio. T-01 permanece abierta y no se autoriza una release.

## Condición vigente

Subtarea original de T-01:

> Ejecutar el benchmark 3 veces y comprobar que las medianas relativas son estables;
> anotar la dispersión en la línea base

Hay tres pasadas completas correctas, con 1.080 muestras y 108 calentamientos descartados,
pero su dispersión máxima entre medianas es 102,07 %. No se han aceptado como estables.
El plan no fijó una tolerancia numérica para «estables»; no se inventa ahora una que haga
pasar esos resultados.

El [diagnóstico posterior](t01-stability-diagnostic-2026-10-29.md) conserva la repetición
interrumpida y el control Node sin plugin. No demuestra una causa única en Windows ni
sustituye las tres pasadas completas. No hay una corrección de código justificada por
estos datos.

## Opción 1: mantener el requisito actual

T-01 continúa abierta. Hacen falta tres pasadas completas que acrediten estabilidad
en las condiciones declaradas de esta máquina. Un control previo puede detectar ruido
antes de iniciar una serie larga, pero no garantiza que toda la serie vaya a ser estable.
No se promete un plazo ni se cambia configuración global de Windows para conseguirlo.

## Opción 2: aceptar una línea base caracterizada, con límites de comparación

Sustituir únicamente la subtarea citada por:

> Ejecutar tres pasadas completas correctas con al menos diez muestras por caso/runtime
> y calentamiento descartado; versionar muestras, procedencia, entorno y dispersión entre
> las tres medianas. Si la dispersión impide una comparación concluyente, declararlo y no
> atribuir ahorro global al código. Cada mejora temporal se evalúa con un control
> antes/después intercalado del mismo workload, fuentes identificadas, control de arranque
> y declaración de dispersión y fallos; un fallo no se acepta como muestra de éxito.

Esta opción cambia el criterio de aceptación: **no acredita que la máquina sea estable**.
Las tres pasadas originales aportarían la línea base caracterizada; el diagnóstico parcial
nuevo seguiría excluido. La revisión debería comprobar su procedencia y cobertura antes
de cerrar T-01. Una comparación inconcluyente seguiría siendo inconcluyente, aunque las
pruebas funcionales o el número de procesos sí estén acreditados.

Si se aprueba esta opción, habría que actualizar de forma coherente la subtarea de T-01,
las instrucciones de comparación de `improvement-plan.md`, los informes de línea base
y el procedimiento ES/EN de observabilidad. Conservar todos los recibos históricos.
No cambia límites temporales, reglas de redacción, denegaciones, tests, cobertura mínima,
presupuesto ni las puertas de revisión, QA y entrega de T-07. No se aplica por silencio.
