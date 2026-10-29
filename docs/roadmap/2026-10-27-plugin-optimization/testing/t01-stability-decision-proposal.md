# T-01: decisión sobre una línea base con variabilidad documentada

Fecha: 2026-10-29. **Opción 2 autorizada por delegación del usuario y aplicada.**
Ante esta pregunta independiente, el usuario respondió «lo que consideres mejor». Se elige
la opción 2 por conservar las muestras y reconocer la incertidumbre sin prometer estabilidad
de la máquina. Esta autorización es posterior y distinta del ajuste de CA-01. T-01 se cierra tras la revisi?n fresca A de las evidencias originales; no se autoriza
una release ni se acredita estabilidad uniforme.

## Condición anterior (sustituida)

Subtarea original de T-01, conservada como historial:

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

## Opción 1: mantener el requisito anterior (no elegida)

Esta opción habría mantenido T-01 abierta hasta obtener tres pasadas que acreditasen estabilidad
en las condiciones declaradas de esta máquina. Un control previo puede detectar ruido
antes de iniciar una serie larga, pero no garantiza que toda la serie vaya a ser estable.
No se promete un plazo ni se cambia configuración global de Windows para conseguirlo.

## Opción 2 elegida: línea base caracterizada, con límites de comparación

Se sustituye únicamente la subtarea citada por:

> Ejecutar tres pasadas completas correctas con al menos diez muestras por caso/runtime
> y calentamiento descartado; versionar muestras, procedencia, entorno y dispersión entre
> las tres medianas. Si la dispersión impide una comparación concluyente, declararlo y no
> atribuir ahorro global al código. Cada mejora temporal se evalúa con un control
> antes/después intercalado del mismo workload, fuentes identificadas, control de arranque
> y declaración de dispersión y fallos; un fallo no se acepta como muestra de éxito.

Esta opción cambia el criterio de aceptación: **no acredita que la máquina sea estable**.
Las tres pasadas originales aportan la línea base caracterizada; el diagnóstico parcial
nuevo sigue excluido. La revisión debe comprobar su procedencia y cobertura antes
de cerrar T-01. Una comparación inconcluyente sigue siendo inconcluyente, aunque las
pruebas funcionales o el número de procesos sí estén acreditados.

Aplicación autorizada: actualizar de forma coherente la subtarea de T-01,
las instrucciones de comparación de `improvement-plan.md`, los informes de línea base
y el procedimiento ES/EN de observabilidad. Se conservan todos los recibos históricos.
No cambia límites temporales, reglas de redacción, denegaciones, tests, cobertura mínima,
presupuesto ni las puertas de revisión, QA y entrega de T-07. Se aplica por la delegación
expresa del usuario; no por silencio ni por la aprobación anterior del objetivo del 80 %.
