# Propuesta de ajuste del objetivo de rendimiento de F1

Fecha: 2026-10-29. Estado: **propuesta, pendiente de aprobación**.

Preparada a petición del usuario. No modifica la spec, el plan ni los criterios aprobados.

## Evidencia

El prefiltro evita Python en identidades no protegidas y conserva el evaluador para identidades
protegidas o entradas dudosas. La comparación local intercalada tiene diez muestras medidas y
un calentamiento descartado por variante y runtime; no presenta fallos de ejecución.

| Runtime | Antes, mediana ms | Después, mediana ms | Reducción observada | Node vacío, mediana ms |
|---|---:|---:|---:|---:|
| Claude | 933,702 | 576,892 | 38,21 % | 534,270 |
| Codex | 854,110 | 540,547 | 36,71 % | 530,265 |
| OpenCode | 893,032 | 554,176 | 37,94 % | 513,177 |

Fuente: [control intercalado y procedencia](t02-paired-control-2026-10-29.json).
Ambas variantes comparten supervisor, mapa y fixtures; cambia el launcher. Es una medición
del launcher compartido, no de la entrega nativa de eventos de cada cliente.

El objetivo del 80 % exigiría medianas de aproximadamente 171–187 ms en este control, por debajo
de los 513–534 ms observados al arrancar Node vacío. Estos valores no son un mínimo físico
universal: indican que el prefiltro de esta implementación no acredita el objetivo aprobado.
Cambiar el mecanismo de arranque requiere estudiar otra solución y revalidar su alcance.

## Cambio concreto propuesto para T-02 / CA-01

Texto aprobado en la spec:

> Dado una sesión principal sin rol protegido, Cuando se ejecuta un Bash o un Edit, Entonces el
> hook PreToolUse no arranca ningún proceso Python y su mediana baja al menos un 80 % frente a
> la línea base.

Texto propuesto para F1:

> Dada una sesión principal sin rol protegido, cuando se ejecuta un Bash o un Edit, el hook
> PreToolUse no arranca ningún proceso Python. La entrega incluye una comparación versionada
> antes/después, con al menos diez muestras por variante y runtime, calentamiento descartado,
> control de arranque de Node y declaración de dispersión y fallos. F1 no exige un porcentaje
> mínimo de reducción de la mediana; informa de la mejora que la medición permita acreditar.

El 80 % se conservaría como objetivo de investigación de una solución posterior, con un spike
de viabilidad antes de comprometer su implementación. No se presenta como alcanzado ni se
asume que alguna tarea existente de F2 vaya a conseguirlo. La revalidación de F2 decidiría el
alcance, el coste y la aceptación de esa investigación.

Si se aprueba, habría que actualizar de forma coherente:

- `spec.md`: CA-01 y la expectativa de que F1 resuelva aproximadamente el 80 % de la espera.
- `tasks.md`: la verificación y el criterio CA-01 de T-02; la referencia cuantitativa de T-07.
- `improvement-plan.md` y `evaluation.md`: la expectativa de beneficio y el destino del objetivo
  pendiente, sin inventar una nueva estimación de coste.
- La documentación de mediciones, manteniendo los recibos históricos y sus limitaciones.

## Garantías y pendientes que se conservan

- Evaluación y denegaciones de los roles protegidos, diagnósticos ante dudas y tabla de paridad.
- Revisión de seguridad, pruebas, cobertura, comprobación de copias y QA de Linux.
- Los límites temporales actuales de las pruebas; esta propuesta no los altera.
- T-01 sigue abierta: las tres pasadas originales presentan hasta un 102,07 % de dispersión.
  Esta propuesta no acepta esa dispersión como estabilidad ni elimina su condición original.
- T-07 sigue abierta por las puertas de revisión, QA y entrega. Aprobar esta propuesta no
  autoriza una release ni cierra automáticamente F1. T-06 ya tiene su comprobación real de
  visibilidad registrada y está completada.

## Decisión solicitada

Aceptar para F1 la garantía funcional de cero Python y la medición transparente, sin un mínimo
porcentual, y trasladar el objetivo del 80 % a una investigación posterior aún sin aprobar.
La alternativa es conservar íntegro el objetivo actual y mantener T-02 y F1 abiertas hasta
acreditarlo. Los criterios aprobados permanecen vigentes mientras no se apruebe el cambio.
