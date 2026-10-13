# Kubernetes, sistemas sensibles a latencia y correo transaccional — S154, S160, S167

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **26.419 bytes/908 líneas**, sin recursos locales.
[k8s-latency-mailtrap-reading-evidence.json](k8s-latency-mailtrap-reading-evidence.json).
Nada se ejecutó; no se contactó ningún clúster ni servicio. Propuestas para T-08.

## S154 — Patrones de Kubernetes

`20.099 bytes/756 líneas`. Plantilla de Deployment endurecida, tres sondas,
Services e Ingress con TLS, ConfigMap y Secret, recursos, RBAC en dos variantes,
HPA, PDB, cuotas, Jobs y CronJobs, chuleta de `kubectl` y checklist.

**Comparación.** S075 dejó pendiente esta pieza antes del diseño definitivo de
contenedores. `delivery-practices/references/delivery-tools.md` ya fija usuario
sin privilegios, recursos declarados, readiness frente a liveness, artefacto
inmutable y rollback; S084 propuso el arnés aislado. No hay consumidor que
declare Kubernetes, así que **no se abre especialidad**. Sí hay tres criterios
que no dependen del orquestador y faltan en la referencia:

| Idea | Encaje |
|---|---|
| La capacidad mínima y el presupuesto de interrupción deben ser compatibles: con dos réplicas mínimas y `minAvailable: 2`, ningún drenado voluntario puede avanzar | Línea en «Contrato de entrega» |
| El autoescalado y el manifiesto no gestionan el mismo número de réplicas: un `replicas: 3` declarado se reaplica en cada despliegue y pisa al HPA | Misma línea |
| Si la aplicación no usa la API del orquestador, su credencial no se monta | Línea junto a «usuario sin privilegios» |

Correcciones para quien la adopte: el comentario del Job dice «Never» mientras
usa `OnFailure`; «etiqueta semver inmutable» es falso, solo el digest lo es (ya
anotado en S075); el `Secret` con el valor en base64 en YAML y
`--from-literal` dejan el secreto en el repositorio y en el historial del shell;
«límites de CPU siempre» provoca throttling y es decisión de carga, no regla;
«las tres sondas en todo despliegue» repite el universal que S075 ya rebajó;
`kubectl rollout undo` revierte la imagen, no configuración, secretos ni datos.

**Destino:** tres líneas en `delivery-practices/references/delivery-tools.md`.
Sin skill ni referencia Kubernetes.

## S160 — Sistemas sensibles a latencia

`2.500 bytes/75 líneas`. Separar métricas (p50/p95/p99, rendimiento, edad de
frescura, profundidad de cola, aciertos de caché), dibujar el camino caliente
segmento a segmento, orden de optimización, verificación en vivo y guardarraíles.

**Comparación.** Solapa con varios dueños: `frontend-quality` («mide un
escenario reproducible antes/después» y localiza el coste), la Lente D de
`adversarial-review` (que solo decide si mirar, nunca el veredicto), la
referencia `outcome-evals/references/performance-baselines.md` propuesta por
S023 (percentiles, muestras e incertidumbre, métricas ausentes como null) y
`backend-practices/references/pipeline-throughput.md` propuesta por S070.
Lo que no está ya propuesto:

- **Edad de frescura como métrica propia**, separada de la latencia: una
  respuesta rápida puede servir datos viejos.
- **«No ocultar datos rancios tras un acierto de caché»**: la caché devuelve su
  edad junto al valor.
- **Camino caliente medido por segmentos** (evento → API → cola → caché →
  cliente → render) antes de elegir dónde optimizar.

Defectos: el «orden de optimización» es una lista fija que se aplica antes de
medir, contra su propia regla de medir cada segmento; la «verificación en vivo
sobre la superficie desplegada» toca producción sin decir cómo se autoriza; no
indica tamaño de muestra ni ventana para que un p99 signifique algo (S023 ya lo
corrige); las referencias a libro de órdenes y VWAP son de un dominio concreto.

**Destino:** frescura y segmentos en `performance-baselines.md` (S023); la regla
de caché en `cache-jobs.md` (S022) de `backend-practices`. Sin skill nueva.

## S167 — Integración de correo con Mailtrap

`3.820 bytes/77 líneas`. Sandbox frente a envío real, autenticación Bearer,
verificación de dominio (SPF, DKIM, DMARC) y antipatrones.

**Comparación.** Proveedor concreto sin rol en el ciclo, como S092 (operación de
correo). **Fuera del bundle.** La idea general —un entorno que no es producción
nunca alcanza destinatarios reales— es una forma del criterio de efectos externos
que S096 propuso para `delivery-practices`. Defectos del ejemplo:

| Ejemplo | Corrección |
|---|---|
| Destino elegido por `NODE_ENV === "production"` | Es común compilar staging con `NODE_ENV=production`: enviaría correo real. Endpoint y token por entorno, explícitos |
| `fetch` sin tiempo máximo | Timeout acotado (fila «Fallo de dependencia» de `contracts-data.md`) |
| «Reintenta los fallos» sin idempotencia | Un reintento tras timeout duplica el correo; clave de idempotencia o registro de envío |
| Error con solo el código de estado | Registrar código y cuerpo redactado, sin el destinatario en claro |

**Destino:** una línea en el criterio de efectos externos de S096 («la selección
de sandbox o real es configuración explícita por entorno, no inferida»).
