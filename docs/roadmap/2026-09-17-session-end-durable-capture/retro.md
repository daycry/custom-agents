---
retro: session-end-durable-capture
fecha: 2026-09-18
---

# Retro — session-end-durable-capture

Iniciativa P0 cerrada el 2026-09-18 (spec `implementada`, plan `completado`, 8/8 tareas). Trabajo hecho en un clon de trabajo fuera de OneDrive (git no escribe en el sandbox), con `tdd: true`.

## Estimado vs real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas humanas | 14,0 h | 6,0 h | **−57 %** |
| Horas IA (ejecución) | 4,2 h | 11,27 h (estimado a juicio: el meter degradó sin transcripciones) | **+168 %** |
| Supervisión | 1,1 h | — (no registrada) | — |
| Tokens | 230k | sin medir (`fuente: estimado` en todos los bloques `generacion:`) | — |
| Tareas | 8 | 8 + 7 rondas de corrección (`fix1…fix3b` × 2 tramos) | — |
| Revisiones | 2 (una por tramo) | **7 pasadas** (3+1 tramo 1, 3+1 tramo 2) · **97 gaps** reproducidos, 0 rebatidos · 6 Critical | — |

## Causas (respuestas del usuario, literales)

1. **Causa principal de la desviación en IA:** «El bucle de revisión» — 7 pasadas de revisión en dos tramos, 97 gaps, ninguno rebatido: cada corrección sobre el camino crítico de la cola abría estados intermedios sin barrido. El plan presupuestó 1 revisión por tramo.
2. **Incógnita de la spec más cara:** «Concurrencia y estados intermedios» — dos workers, claim/TTL/backoff, cortes entre pasos: 5 de los 6 Critical vinieron de ahí (`.claiming` huérfano, TTL sobre creación en vez de reclamación, backoff en la misma pasada, `captured_at` sin validar, drenaje abortado por una excepción).
3. **Qué hacer distinto:** «Presupuestar la revisión ×N por tramo» — línea propia de revisión + corrección con 3 intentos por tramo como base, no 1; y exigir en el diseño de colas «quién recupera cada estado intermedio».

## Evidencia objetiva (ledger y revisiones)

- Las horas humanas cayeron porque la spec, el diseño y la evaluación ya existían al arrancar (`/pm-cycle` hecho el día anterior) y el paquete externo aportó el diseño de referencia: T-01…T-04 se implementaron en una sola pasada.
- Las horas IA se multiplicaron en el bucle: el intento 1 del tramo 1 destapó 2 Critical + 12 Important; **la corrección de cada intento introdujo Critical nuevos en el intento siguiente** (3 en el intento 2, 1 en la 4.ª pasada) — todos del mismo patrón: sustituir una operación atómica (`os.replace` único) por una secuencia de 2-3 pasos sin que ningún barrido reconociera el estado intermedio.
- La seguridad del contexto apareció tarde y por capas: `transcript_path` (intento 1) → `captured_at`/`reason` (intento 2) → nombres de log hostiles en avisos (tramo 2, intento 3) → `ficheros_tocados` en `latest` (verificación final; ruta preexistente).
- Hallazgo colateral: el aviso de `replay` en el hook nunca funcionó desde T-05 (`SyntaxError` en un snippet embebido) y la revisión del intento 1 del tramo 2 no lo detectó; lo destapó el intento 2.

## Aprendizajes

- **Cola durable = máquina de estados explícita antes de codificar**: tabla estados × fallo × quién recupera, y un test de corte por transición (SIGKILL real, no monkeypatch). Es lo que habría evitado 5 Critical. → [`LES-016`](../../knowledge/lessons/LES-016-implementer-estados-intermedios-de-una-cola-tienen-dueno.md).
- **La revisión es la línea de coste dominante también en código de infraestructura**, no solo en prosa (confirma `LES-001`): aquí 7 pasadas frente a 2 presupuestadas.
- **Todo texto que llega a `additionalContext` es superficie de inyección**, venga de un nombre de fichero, de `str(ex)` o de `git status`: sanear (control/bidi/saltos) y enmarcar como cita, nunca censurar contenido.
- **Verificar la corrección con mutantes** (26 en el tramo 1, 20+ en el tramo 2) fue lo que separó «corregido» de «declarado corregido»: cuatro gaps se habían cerrado con guardas que no detectaban su propio mutante.

## Ajuste sugerido

Para iniciativas con **cola, concurrencia o estado durable**: presupuestar la revisión + corrección como línea propia con **3 intentos por tramo** (no 1) y sumar una tarea de diseño «tabla de estados intermedios y su recuperación» antes de la primera de implementación. Sin medición de tokens en el sandbox, la calibración del ratio queda pendiente de la próxima iniciativa que corra con transcripciones.
