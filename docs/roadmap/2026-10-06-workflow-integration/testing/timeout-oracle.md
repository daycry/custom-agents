# Diagnóstico de la prueba de timeout en Windows

La suite Node inicial terminó con 133 passed y un fallo B-12. El caso aislado
repitió el fallo: un nieto escribía a los tres segundos y el test interpretaba
esa marca como supervivencia al timeout.

Una copia instrumentada del instalador, sin modificar producción, registró
inicio/fin de limpieza y comprobó el PID. En una ejecución apareció la marca,
pero el PID ya no existía al retornar; en otra no apareció. La consulta síncrona
de huérfanos puede durar suficiente para permitir una escritura antes de matar
al proceso. Se descarta que la marca pruebe supervivencia tras la limpieza.

El test ahora registra el PID al iniciar el nieto, exige que haya arrancado y
comprueba su ausencia después del retorno. Su `finally` cierra únicamente el
proceso de la fixture. El código de `install/install.mjs` no cambió.

| Variante | Resultado |
|---|---|
| Código de producción, prueba con PID | 1 passed |
| Copia privada sin la llamada `matarArbol(e.pid)` | exit 1; falla porque el nieto sigue vivo |

El resultado demuestra que el oráculo detecta una omisión real de limpieza.
No acredita terminación instantánea al vencer el límite. La causa también se
captura en la memoria técnica local ignorada por Git, como propuesta, sin
publicar su índice ni promoverla al Knowledge Gate.
