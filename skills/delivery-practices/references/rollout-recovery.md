# CI, artefacto, rollout y recuperación

Léela solo cuando haya que decidir cómo sustituir una versión en un entorno
(estrategia de rollout, condición de parada, vuelta atrás) o preparar el job de
CI que construye y publica el artefacto.

Recorrido: **CI → artefacto → estrategia → observación → recuperación**. Cada
tramo deja evidencia que el siguiente consume. Contenedores, secretos, probes y
permisos del token están en [entrega y herramientas](delivery-tools.md); el orden
de migraciones y expand/contract, en «Migrar con lectores y escritores
coexistentes» de `skills/backend-practices/references/contracts-data.md`. Aquí
no se repiten.

## 1. CI y artefacto

| Paso | Decisión que debe quedar explícita | Defecto que descubre |
|---|---|---|
| Construir una vez | El artefacto se construye en un job y se promueve entre entornos; no se reconstruye por entorno | Staging y producción ejecutan builds distintos del mismo commit |
| Identidad | Se registra el digest (`sha256:…`) del artefacto probado y el commit de origen; la etiqueta es solo un nombre | Una etiqueta movida tras las pruebas publica otra imagen |
| Lo probado es lo publicado | El despliegue referencia el digest que pasó las pruebas, no la etiqueta | Digest probado distinto del desplegado |
| Acciones de terceros | Fijadas por SHA completo del commit (o lockfile de workflows si el proyecto lo usa) | Una etiqueta de acción reasignada ejecuta otro código |
| Lockfile y dependencias | Instalación desde el lockfile con el gestor que ya usa el proyecto; dependencias de build fuera del runtime | Lockfile incoherente resuelto en CI de forma distinta a local |
| Orden de publicación | Despliegues al mismo entorno serializados (grupo de concurrencia por entorno); el más nuevo no es pisado por uno anterior | Dos releases terminan fuera de orden y queda activa la vieja |
| Plantilla incompleta | Un job de deploy que solo imprime texto o un smoke descrito en prosa se marca como plantilla, no como despliegue | «Deploy en verde» sin ningún cambio en el entorno |

Actualizar digests y SHA fijados es un proceso del proyecto (bot de dependencias
o tarea periódica); fijar sin actualizar congela también los parches de
seguridad. Un digest fijado no acredita que la imagen sea segura.

## 2. Estrategia de rollout

Ninguna estrategia garantiza cero caída ni vuelta atrás instantánea por sí
misma: son objetivos que dependen de readiness, capacidad, drenaje, sesiones y
estado compartido.

| Estrategia | Precondición | Lo que NO garantiza |
|---|---|---|
| Recreate | Se acepta una ventana sin servicio | Disponibilidad durante el cambio |
| Rolling | Versiones vieja y nueva compatibles a la vez (API, esquema, mensajes); capacidad extra o tolerancia a menos réplicas | Cero caída si readiness no refleja capacidad real o las conexiones no drenan |
| Blue-green | Capacidad para dos entornos; datos compartidos compatibles con ambos | Que volver el tráfico deshaga datos escritos, mensajes enviados o efectos externos |
| Canary | Tráfico divisible y métricas por versión con volumen suficiente para comparar | Detección si la señal no distingue versiones o la muestra es pequeña |

El plan de rollout declara: artefacto (digest) y entorno, estrategia elegida y por
qué, pasos y porcentajes, señales y umbrales de parada acordados por servicio,
ventana de observación y quién decide avanzar. Preparar el plan no autoriza
ejecutarlo ni mover tráfico: es un efecto externo («Efectos externos» de
[entrega y herramientas](delivery-tools.md)).

Un CLI o API de despliegue que responde en modo desacoplado confirma que el
trabajo quedó encolado, no que terminó; un timeout del cliente no cancela la
operación remota. El estado final se lee del destino (ID de despliegue, digest
activo, entorno) antes de dar el paso por hecho. Antes de ejecutar un comando de
despliegue, resuelve proyecto y entorno destino: algunos crean recursos o abren
un enlace interactivo si no están vinculados.

## 3. Observación

Tras cada paso, observa el entorno con el artefacto identificado antes de
avanzar: [observación tras desplegar](post-deploy-observation.md). Un paso sin
observación es un paso sin evidencia.

## 4. Recuperación

Separa tres acciones que una «vuelta atrás» suele mezclar:

| Acción | Qué revierte | Qué no revierte |
|---|---|---|
| Revertir aplicación o tráfico | La versión servida | Datos escritos, mensajes publicados, efectos en terceros |
| Reparar datos | Las filas o eventos afectados, con script revisado | La versión servida |
| Marcar historial | El estado registrado de una migración fallida | El esquema: cambiar metadatos no ejecuta SQL inverso |

- En Kubernetes, `kubectl rollout undo` vuelve a la plantilla de pod anterior;
  el escalado y otros cambios fuera de la plantilla no son revisiones y no se
  revierten, ni tampoco ConfigMaps, Secrets o datos. Superar
  `progressDeadlineSeconds` solo marca la condición `ProgressDeadlineExceeded`:
  no hay vuelta atrás automática, alguien debe actuar.
- Si el esquema ya no es compatible con la versión anterior, la vuelta atrás no
  es segura: la salida es forward fix con expand/contract.
- Condición de parada antes de empezar: qué señal, qué umbral y qué acción. Sin
  ella, la decisión de revertir se improvisa durante la incidencia.

Controles como escalado, guardia u observabilidad ampliada se aplican según
tamaño y riesgo del cambio, con `n/a` razonado; marcar una lista no acredita
cobertura.

## Salida

Plan con artefacto (digest + commit), entorno, estrategia y motivo, pasos,
señales y umbrales de parada, recuperación separada en las tres acciones, y
evidencia comprobada frente a ausente. qa comprueba imagen y escenario;
nemesis conserva la auditoría de seguridad.

## Fuentes

Consultadas el 2026-10-14:
[Docker build best practices — digests](https://docs.docker.com/build/building/best-practices/),
[GitHub Actions secure use — SHA pinning](https://docs.github.com/en/actions/reference/security/secure-use),
[GitHub Actions concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency),
[Kubernetes Deployments — rollback y progress deadline](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/).
