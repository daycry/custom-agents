---
estado: aprobada
creado: 2026-10-31
---

# Una consola común para sesiones, planes y contexto

El usuario autoriza implementar el dashboard moderno, su documentación, commits,
push, PR y release v3.0.0. La petición adicional de un solo puerto se incorpora al
mismo diseño; no exige un servidor por proyecto. Las decisiones cotidianas se
resuelven con criterio técnico dentro de ese alcance.

## Resultado y criterios

Una interfaz local permite seleccionar proyectos explícitos y operar únicamente
en el contexto elegido. Cada petición valida la raíz y sus IDs de sesión/plan.
Las respuestas tardías, borradores y notas conservan su proyecto y tarea. El
registro común no escanea carpetas personales ni introduce permisos multiusuario.

La UI reúne sesiones/chat, aprobaciones nativas, cartera, kanban por fases, detalle
y notas de tarea, preparación de objetivos y ejecución en una sesión. Muestra
actividad recibida, memoria local e integraciones declaradas con fuente, frescura
y límites; no convierte un gesto de tablero en QA ni en cierre canónico.

Los adaptadores utilizan interfaces nativas contrastadas. No se simula control de
ventanas Desktop ni funciones no expuestas. Las versiones observadas y capacidades
no admitidas se documentan. Ollama sigue sin probarse por decisión del usuario.

## Fase 1 — Diseñar y conectar

T-01 y T-02 del ledger cubren diseño, contratos oficiales, registro de proyectos y
sesiones nativas. Deben existir presupuestos de recursos, estados diferenciados,
autenticación local, decisiones de un solo uso e interrupción confirmada. El
proceso sólo cierra su propia ejecución; el historial nativo no se exporta.

## Fase 2 — Operar planes y observar

T-03 y T-04 componen los lectores canónicos y el shared kit. La preparación de
trabajo comprueba las fuentes actuales antes de enviarlo. Las notas tienen dueño,
versión y recibo de petición. Las lecturas grandes usan snapshots acotados en
segundo plano; sus fallos y resultados anteriores se hacen explícitos.

## Fase 3 — Verificar y entregar

T-05 verifica contratos, fallos, carreras, cancelación y aislamiento con TDD,
protocolos simulados y comprobaciones reales acotadas. El navegador prueba los
recorridos a 375px y escritorio, teclado, temas y fuentes reales de fixture.
Documentación ES/EN y PDF explican el uso para responsables de área y los límites
para operadores. Las capturas de fixture se etiquetan como ejemplos.

T-06 requiere revisión independiente, QA pertinente, revisión literal del contenido,
commits y push, CI verde del HEAD final y PR. La fusión y release v3.0.0 están
autorizadas y utilizan exclusivamente `scripts/release.py`. Un archivo personal
ajeno al trabajo no se incorpora ni se oculta para pasar las puertas.

## Recuperación

Si una operación pierde confirmación, no se reenvía automáticamente. Se consulta
el estado nativo y el efecto real. Reiniciar el servidor cambia su acceso y pierde
la ventana de chat en memoria; los vínculos y notas propios se conservan por
proyecto. Ningún error opcional de actividad o de backend de memoria aprueba ni
bloquea por sí mismo el workflow canónico.
