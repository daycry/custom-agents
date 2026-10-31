---
name: llm-pipeline
description: >
  Diseña pipelines LLM de aplicaciones consumidoras con presupuesto previo,
  reintentos acotados, caché y evaluación de calidad. Úsala cuando el usuario diga
  "diseña un pipeline LLM", "limita el coste de estas llamadas al modelo" o
  "revisa los reintentos de mi integración LLM".
---

# Pipelines LLM de aplicación

Guía el diseño, implementación o revisión en el proyecto consumidor. No instala
un runner ni cambia modelos del plugin. `rates-verify` mantiene las tarifas Claude;
`usage-meter` mide sesiones: este contrato controla llamadas de una aplicación.

1. Identifica proveedor, SDK y versión desde el proyecto, operación y carga real.
   Compara calidad, coste y latencia con un conjunto representativo antes de
   cambiar modelo. No promete que el más barato conserve el resultado.
2. Para limitar gasto, lee [reservas de presupuesto](references/cost-control.md).
   Distingue estimación, límite de solicitud y coste facturado incierto.
3. Para caché, cancelación o recuperación, lee
   [caché y reintentos](references/cache-and-retries.md). Fija un solo dueño de
   los reintentos y respeta el plazo total.
4. Al implementar, comprueba el contrato oficial de esa versión del proveedor.
   Selecciona las pruebas que acrediten presupuesto concurrente, fallos y calidad;
   una validación estática no sustituye la evaluación del resultado.

Conserva roles y fronteras de confianza del prompt. No envía datos a un proveedor
ni activa gasto real solo por diseñar el pipeline; aplica el alcance ya autorizado.
No incluye tablas de modelos o precios que aparenten estar actualizadas.

## Sesgos al optimizar

Formato compartido: agent-kits/shared/rationalization-table.md.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Sumo el gasto al terminar y así respeto el límite» | Varias llamadas concurrentes pueden gastar el mismo saldo. | Reservar presupuesto de forma atómica antes de cada llamada. |
| «No sé el precio, así que computo cero» | Un importe desconocido no acredita consumo gratuito. | Obtener una cota válida o mantener la llamada sin admisión presupuestaria. |
| «El SDK y mi bucle reintentan para mayor fiabilidad» | Los intentos se multiplican y desbordan coste y plazos. | Elegir un dueño y verificar los intentos efectivos del transporte. |
| «Timeout significa que no hubo cobro» | El proveedor pudo procesar la solicitud antes de perderse la respuesta. | Conservar resultado y facturación inciertos hasta reconciliar. |
| «La caché funcionó porque el prompt era igual» | La similitud no prueba reutilización ni facturación reducida. | Comprobar métricas de uso admitidas por el proveedor. |
| «Con el modelo barato ya está optimizado» | El coste aislado no acredita calidad aceptable para la tarea. | Comparar resultados con el corpus y umbral acordados. |

## Salida y evidencia

Contrato o cambio con proveedor/versión, presupuesto, admisión, política de
intentos, plazos, caché y resultado de las verificaciones efectuadas. Separa
costes estimados y medidos; declara pruebas sin credenciales y llamadas reales.
