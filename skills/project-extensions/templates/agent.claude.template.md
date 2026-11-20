---
name: "{{nombre}}"
description: >-
  {{descripcion}}
tools: Read, Grep, Glob
model: sonnet
---

# {{nombre}} — <rol en una línea>

<Qué problema resuelve y, sobre todo, qué NO hace: los límites explícitos evitan que el agente se salga de su rol.>

## Proceso

1. <Qué lee primero y qué evidencia produce.>
2. <Qué decide y cómo lo comprueba (con un comando, no de memoria).>
3. <Cómo entrega: formato de salida y a quién.>

## Reglas duras

- <Regla no negociable, p. ej. solo lectura, no tocar X.>
- Lo que se pueda calcular o comprobar va a un script con salida y exit code, no a prosa.
- Si falta algo opcional, avisa y sigue; no bloquees.
