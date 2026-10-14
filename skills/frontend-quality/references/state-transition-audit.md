# Auditoría de transiciones de estado

Léela solo cuando una interacción termine en un estado incorrecto: el mensaje
de éxito no corresponde a lo guardado, dos respuestas se pisan, un menú no
cambia de seleccionado o un formulario se vacía tras guardar. Para un cambio
visual sin transición, o una respuesta de API incorrecta sin efecto en la UI,
esta guía no aplica.

## Reparto

Un método, tres dueños; esta guía no abre otra revisión ni otro bucle de
reparación.

| Paso | Dueño |
|---|---|
| Resultado observable esperado (qué ve el usuario al final) | qa, en el escenario del test-plan |
| Hallazgo como hipótesis y su prueba | Esta auditoría lo formula; `debug-root-cause` lo reproduce y prueba |
| Regresión fijada | `tdd` si está activo; si no, el test de regresión de la Fase 4 de `debug-root-cause` |
| Gravedad | La escala Critical/Important/Minor de `adversarial-review`, por el efecto concreto, sin traducir nombres de otras escalas |

## 1. Mapa evento → estado final

Antes de tocar nada, sigue una acción hasta su resultado. Si la pantalla
comparte un store, lista primero **todos** sus consumidores: un reset en una
página puede vaciar otra.

| Paso | Qué anotar |
|---|---|
| Evento | Control y acción del usuario (clic, tecla, envío) |
| Handler | Fichero y línea |
| Llamadas en orden | Peticiones, lecturas y escrituras del store, con su orden real |
| Resets y efectos | Qué limpia el estado, qué efectos o suscripciones reaccionan |
| Estado final | Valor del store y de la UI al terminar |
| Persistencia | Qué quedó guardado en el servidor; la etiqueta de éxito corresponde a esto, no a la petición enviada |

## 2. Interleavings que hay que buscar

| Lente | Señal en el código | Escenario que lo descubre |
|---|---|---|
| Escritura anulada | Un reset o una carga posterior pisa la escritura | Guardar y, antes de terminar, se dispara la recarga: el valor guardado desaparece de la UI |
| Respuesta fuera de orden | Dos peticiones sin cancelar ni descartar la obsoleta | La respuesta A llega después de B y la reemplaza |
| Closure obsoleta | El handler usa un valor capturado en un render anterior | Dos actualizaciones rápidas: la segunda parte del valor antiguo |
| Transición ausente | Falta un estado intermedio (cargando, error, reintento) | El error deja el spinner o el estado previo visibles |
| Rama inalcanzable | Una condición nunca se cumple con los datos reales | El mensaje de error previsto no aparece nunca |
| Interferencia de efectos | Dos efectos o suscripciones escriben el mismo estado | Desmontar durante la carga, cerrar y reabrir, doble envío |

Cancelar la respuesta local no deshace lo que el servidor ya persistió:
abortar una petición no demuestra rollback (ver la referencia React de
`stack-practices` y la idempotencia en `backend-practices`).

## 3. Plantilla de hallazgo

Una secuencia leída en el código es una **hipótesis**, no un defecto
reproducido, hasta que `debug-root-cause` la prueba.

```markdown
- **Evento**: <control y acción>
- **Ruta**: <fichero:línea del handler y de la escritura sospechosa>
- **Secuencia causal**: <paso 1 → paso 2 → …, con el orden que produce el fallo>
- **Esperado**: <estado final observable, el del escenario de qa>
- **Actual**: <lo que se ve o se guarda>
- **Impacto**: <efecto para el usuario o los datos>
- **Estado**: hipótesis | reproducida (<comando o test>)
- **Reparación verificable**: <cambio mínimo y test de regresión que falla sin él>
```

## 4. Alcance

Audita una página, el cambio de un store o el conjunto de consumidores de ese
store, no toda la aplicación. El método sirve para cualquier gestión de estado
(React, JavaScript sin framework u otra); la forma React de las actualizaciones
funcionales y la limpieza de efectos está en la referencia React de
`stack-practices`. Conserva en el contrato de interacción la carga, el error,
el reintento, la navegación, el foco y el teclado: corregir la transición no
debe romperlos.
