---
retro: project-specialization
fecha: 2026-10-27
---

# Retro — project-specialization

> Cerrada el 2026-10-27 con el alcance **reducido a F1**: 6/22 tareas `completado` (F1 T-01…T-03 más la revisión, la corrección y el cierre recortados a F1) y 16 `cancelado` (toda la F2). F1 entró en `master` el 2026-09-10. La F2 llevaba 47 días sin arrancar cuando una auditoría del cierre mostró que `project-extensions` ya la había superado.

## Estimado frente a real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas totales (iniciativa completa) | 56,4 h · ~2.837 € | solo se ejecutó F1 | no comparable |
| F1: horas humanas | 6,0 h | 0 h (ejecución por agentes) | −100 % |
| F1: IA + supervisión | 0,57 h | 1,63 h (estimadas: meter degradado; incluyen la corrección de las tres revisiones) | +186 % |
| F1: tokens | 220k | 220k (estimados, no medidos) | no comparable |
| F1: revisión | 1 intento previsto por tramo (tope 3) | 3 intentos: 6 I + 6 M → 1 C + 4 I + 3 M → 3 I + 1 M | 3/3 |
| F2 + resto de F3 | 41,0 h | 0 h: cancelada | — |

## Causas

1. **La F2 se quedó sin puerta y otra iniciativa ocupó su terreno.** El go de la F2 llevaba cuatro condiciones y nunca se pidió. Mientras tanto, `2026-10-06-project-extensions` construyó el lector del registro O1 (`project-pieces.py`) y el descubrimiento de piezas en los tres runtimes, y `/work-context` la selección para el brief. Lo que quedaba del plan (escribir el registro, generar piezas, modo proyecto de interop) dejó de tener demanda.
2. **El plan envejeció contra el árbol.** En siete semanas cambió el modelo multi-runtime (carpetas nativas por runtime en lugar de traducir un `.claude/` canónico). También quedó claro que `scripts/` no viaja con el plugin y que `personas/` no se carga de forma nativa en Codex ni OpenCode. Ejecutado tal cual, el plan habría creado scripts que no llegan al consumidor y un modo de interop contrario al diseño vigente.
3. **La F1 costó revisión, no implementación.** Tres intentos de dos lentes encontraron 1 Critical (recorte ciego de la persona en el brief) y 13 Important. Es el mismo patrón que `memory-retrieval` y `panel-redesign`.
4. **La documentación describía piezas que no existían.** `FLOWS.md` §6d, `ROLES.md` y `SPECIALIZATION.md` documentaron el comando y sus scripts durante 48 días, y una tolerancia del linter (`PIEZAS_PLANIFICADAS`) ocultaba ese hueco a propósito. Se retiró en el cierre.

## Aprendizajes

- **Un plan con fases y puertas caduca.** Si una fase espera su go más de ~3 semanas, se revalida contra `master` antes de ejecutarla, porque otras iniciativas pueden haber cubierto o contradicho su alcance.
- **Documentar antes de construir tiene coste.** Describir en la documentación pública un comando que aún no existe obliga a tolerarlo en el linter, y esa deuda crece sola. Mejor documentar el contrato solo en la carpeta de la iniciativa (`design.md`) hasta que la pieza exista.
- **Antes de abrir una iniciativa, mirar qué hay en vuelo.** Comprobar el solape con las iniciativas activas habría unido la F2 con `project-extensions` desde el principio.

## Ajuste sugerido

En la estimación de una iniciativa por fases con puertas diferidas, añadir una línea de **revalidación del plan** al abrir cada fase posterior (~0,5 h). Al calibrar la revisión, la F1 confirma la regla vigente: presupuestar 3 intentos, no 1.

> Causas redactadas por el orquestador a partir del ledger y de la auditoría del cierre (2026-10-27); el usuario puede corregirlas.
