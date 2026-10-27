---
retro: catalog-capabilities
fecha: 2026-10-27
---

# Retro — catalog-capabilities

> Iniciativa cerrada el 2026-10-27 con un **cierre contable**: 15/16 tareas `completado` con su evidencia citada en el ledger y T-12 `cancelado`. Todo lo integrado ya estaba en `master` (PR #17) y publicado en v2.0.0. La llevó sobre todo Codex, en bloques del 2026-10-07 al 2026-10-15.

## Estimado frente a real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas IA | no estimadas («no se solicitó presupuesto», `evaluation.md`) | no medidas: el meter no tuvo respuestas compatibles | no comparable |
| Horas humanas | no estimadas | 0 h de implementación; supervisión y decisiones del usuario sin registrar | no comparable |
| Tokens | no estimados | sin medición compatible | no comparable |
| Alcance | 455 piezas comparadas + integración por bloques | 293 skills, 68 agentes y 94 comandos comparados; 110 destinos integrados, 47 aparcados | — |
| Tareas | 16 | 15 completadas · 1 cancelada (T-12) | — |
| QA | global Windows/Linux | 7.296 casos por SO, 0 fallos, cobertura 91,2 % (`testing/global-source54-status.md`) | — |

## Causas

1. **El ledger no reflejaba el trabajo hecho.** Con el código ya en `master` y publicado, el ledger seguía al 6 % (1/16) y sin una sola casilla marcada. Las tareas macro tenían un criterio genérico («contrato y resultado comprobados con evidencia ejecutada») que ningún bloque podía dar por cumplido. La evidencia se acumulaba en más de 40 ficheros `*-evidence.json` y `testing/*-status.md`, pero no se volcaba en las tareas.
2. **El alcance mezclaba entregas con validaciones manuales inalcanzables.** La continuidad real en tres clientes, la UI en Edge y el benchmark de memoria quedaron dentro de las tareas como «pendiente» indefinido, sin una puerta que las cancelara o aplazara. Así, ninguna tarea podía cerrarse.
3. **El trabajo se integró por otra iniciativa.** `panel-redesign` superó a T-13 y fue su PR (#17) el que llevó todo a `master`. La línea de autorización («sin PR, integración en main ni release») quedó obsoleta sin que nadie la enmendara.
4. **El ledger creció hasta el tope.** Tuvo que archivar 730 KB en `execution-history.md` para no pasar de 256 KiB, y aun así quedó difícil de leer para retomar.

## Aprendizajes

- **Los criterios de aceptación tienen que ser concretos.** Un criterio genérico copiado en las 16 tareas no se puede marcar nunca. Cada T-XX necesita un criterio verificable propio, como `293/293 fichas` o `7.296 casos 0 fallos`.
- **Lo inalcanzable se declara al planificar.** Las validaciones manuales o externas (otros clientes, navegador real, backends) se decide al planificar si son tarea propia, criterio opcional o fuera de alcance, para que no bloqueen el cierre.
- **Si otra iniciativa integra tu trabajo, se cierra la tuya en el mismo PR.** Así el ledger no queda huérfano en `master`.

## Ajuste sugerido

Una iniciativa de comparación o auditoría masiva se planifica con criterios cuantitativos por tarea y una tarea de cierre que acepte «fuera de alcance» explícito. No se estima por horas sin meter: hay que pedir presupuesto o dejar constancia de que no hay muestra.

## Pendiente fuera de esta iniciativa

- Benchmark de memoria (Kwipu/Graphiti frente a la memoria local): fase 4 de la spec.
- Validación real del binding de actividad de OpenCode V2 y de un `/dev-cycle` completo con Jira real.
- Los 47 destinos de skills aparcados, solo cuando un consumidor declare ese stack.

> Causas redactadas por el orquestador a partir del ledger y de las auditorías del cierre (2026-10-27); el usuario puede corregirlas.
