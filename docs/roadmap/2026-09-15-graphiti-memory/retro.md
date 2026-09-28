---
retro: graphiti-memory
fecha: 2026-09-23
autor: orquestador (/dev-cycle, modo autónomo bajo objetivo de sesión del usuario)
validada_por_usuario: pendiente
---

# Retro — graphiti-memory

Registrada por el orquestador al cierre del ciclo (2026-09-23). Las causas salen de la evidencia del ledger (`tasks.md`, 14 secciones de revisión) y de los marcadores de `usage-meter`, no de una conversación con el usuario: **pendientes de validar por el usuario** (puede corregirlas en el PR).

## Estimado vs real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---|
| Horas humanas | 50 h | 0 h | −100 % (ejecución íntegra por agentes; el usuario fijó el objetivo, aprobó la salida del bucle en la Fase 2 y decidió las pausas) |
| Horas IA de implementación (ventanas `usage-meter`) | 15 h | 22,88 h | **+53 %** (todas `(medido)`; 20 marcadores: 10 tareas + 14 rondas de corrección agrupadas por fase) |
| Supervisión | 3,8 h | 0 h | sin supervisión humana en el ciclo |
| Tokens | 545k | ~81M+ (incl. lectura de caché; facturables no separados por marcador) | n/a comparable: la estimación era de tokens facturables de tareas; la medida incluye caché de contexto largo y las 14 rondas |
| Coste IA medido (EUR, suma de las ventanas con cifra) | — | ~227 EUR | — |
| Tareas | 10 | 10 | 100 % |
| Gaps de la revisión de dos lentes | — | 191 filas (12 Critical, 56 Important, 123 Minor) en 14 secciones | 4 fases × 3 intentos + 2 verificaciones dirigidas; 14 rondas de corrección (F1 2, F2 5, F3 4, F4 3) |
| Coste humano (50 EUR/h) | 2.500 EUR | 0 EUR | — |
| qa | — | sin UI por diseño; `ledger-lint` 0, `coverage-check` exit 0, suite 863 passed + 5 rojos preexistentes de Windows | ver `testing/report.md` |

Fuente: «Resumen de progreso» y secciones de revisión de `tasks.md`; `Tiempo IA (fixN)` por ronda; `testing/qa-report.md`.

## Causas de la desviación (evidencia del ledger)

1. **El coste no estuvo en implementar sino en cerrar el bucle de revisión.** Las 10 tareas se implementaron en ~6,6 h de IA; las 14 rondas de corrección sumaron ~16 h. Cada fase agotó los 3 intentos (Fases 2, 3 y 4) y dos de ellas necesitaron una verificación dirigida adicional aprobada por el usuario. La estimación (15 h IA) no presupuestaba ninguna ronda de corrección.
2. **Cada corrección abrió un consumidor nuevo del mismo contrato.** El veredicto de `verify()` tiene tres consumidores (`puede_leer`, `/doctor`, `knowledge-sync --check`): cambiarlo en fix2 de la Fase 3 (#120) reabrió el problema en cada consumidor por turno (#133 → #148 → #168). Lección: enumerar los consumidores de un contrato ANTES de cambiarlo (candidato a gotcha).
3. **La suite de seguridad es una denylist estática y cada lente encontró una evasión nueva.** La Fase 4 (T-09) pasó de 20 a 63 tests en tres rondas; el bucle cerró con 0 Critical/Important pero 6 límites conocidos quedaron como deuda declarada en `design.md` (propuesta `hooks-gate-hardening`). Una puerta estática se cierra por decisión, no por agotamiento.
4. **Proceso de revisión: lentes en paralelo sobre el mismo checkout contaminan** (Fase 2, intento 3: 3 falsos rojos) → desde entonces, worktrees separados por lente. Segunda y tercera forma en la Fase 4: scripts de mutación huérfanos en el scratchpad compartido ejecutados sobre el árbol principal (#167), worktree desaparecido y ruta `b`/`B` insensible a mayúsculas (#184). Regla resultante: nombres únicos por lente e intento, scripts en subdirectorio propio y borrado al cerrar.
5. **Windows como máquina de desarrollo introduce ruido que hay que separar del código:** 4-5 tests rojos preexistentes de entorno (CRLF, bit ejecutable, `python3`), `PermissionError` intermitente en `os.replace` bajo carga, y la ruta de `GOT-012` por encima de MAX_PATH en worktrees profundos (#195: 3 falsos rojos por lente). Ninguno era defecto del código, pero cada uno costó verificación.
6. **Lo que sí se validó en vivo:** el servidor Graphiti real (`127.0.0.1:8001`, `serverInfo` 1.29.1) en solo lectura durante la Fase 2: `health` sano, `tools/list` idéntico al fixture capturado y `add_triplet.required` real igual al asumido por el arbitraje #69; `get_episodes` del grupo sonda vacío. El grafo estaba vacío, así que los límites `_nombres_de_hit` y `group_id` en `get_episodes` quedaron documentados como no verificables en `design.md`.

## Aprendizajes

- Cualitativos (propuestos al Knowledge Gate en la Fase 4-bis por `documenter`; ver `docs/knowledge/candidates/pending/`): consumidores de un contrato antes de cambiarlo; worktrees únicos para lentes con mutation testing; MAX_PATH y nombres de gotcha; una puerta estática de hooks es una denylist con límites declarados.
- De proceso (ya anotado en la Fase 2): la regla «bucle acotado a 3 → parar y preguntar» funcionó como puerta; la salida elegida por el usuario (ronda acotada + verificación dirigida) cerró las Fases 2 y 3 sin un 4.º intento completo.
- Numérico: ver fila en `docs/roadmap/CALIBRATION.md`.

## Ajuste sugerido

- **Presupuestar la revisión:** para iniciativas con adaptadores de red y contratos con varios consumidores, estimar las horas IA de implementación × 2,5 (aquí 15 h → 22,9 h reales solo en ventanas medidas) o, mejor, añadir una línea explícita «rondas de corrección: N × 1 h» por fase.
- **`usage-meter`:** cerrar el marcador de cada ronda UNA sola vez y pegar los tokens facturables en el ledger (aquí varios re-cierres arrastraron la ventana y la cifra de tokens por marcador se perdió; el ratio tokens/hora de esta fila queda `(estimado)`).
- **Iniciativa derivada:** `hooks-gate-hardening` (deuda #187-#192 de la Fase 4).
