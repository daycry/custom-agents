---
description: "{{descripcion}}"
argument-hint: "<obligatorio> [opcional]"
---

# /{{nombre}} — <qué hace, en una línea>

<Qué flujo coordina y qué decide el usuario frente a lo que decide el comando. Los argumentos llegan
en `$ARGUMENTS`.>

**Argumentos:** `/{{nombre}} <obligatorio> [opcional]` — <significado y valores por defecto>.

## Pasos

1. <Qué valida antes de empezar; si falta algo opcional, avisa y sigue.>
2. <Qué hace, con el comando o agente exacto.>
3. <Qué pregunta al usuario y qué consecuencia tiene cada respuesta.>

## Reglas duras

- Bucles acotados, con una salida explícita al agotarse.
- Todo veredicto sale de un script con exit code, no de la prosa.
