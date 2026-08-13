---
description: <Una frase: qué orquesta este comando — la ve el usuario en el picker de />
argument-hint: "<obligatorio> [opcional] [--flag]"
---

# /<nombre> — <qué orquesta, en una línea>

<Descripción: qué ciclo/flujo coordina, qué agentes invoca POR NOMBRE y qué decide el usuario
vs. qué decide el comando. Los comandos orquestan y ponen PUERTAS; el trabajo con criterio lo
hacen los agentes.>

**Argumentos** (llegan en `$ARGUMENTS`): `/<nombre> <obligatorio> [opcional] [--flag]` — <qué
significa cada uno y el default>.

## Fases

**Fase 0 — Entrada y puerta inicial.**
<Qué valida antes de empezar (config, artefactos previos, estado del ledger). Si algo opcional
falta → aviso + degradar, no bloquear. Si falta algo OBLIGATORIO → parar aquí con mensaje claro.>

**Fase 1 — <agente/acción>.**
<Invoca al agente `<nombre>` con <contexto>. Salida esperada: <artefacto + estado>.>

**Fase 2 — Puerta <decisión>.**
<Qué se le pregunta al usuario (AskUserQuestion / conversacional), opciones y consecuencia de
cada una. Las puertas de decisión humana se documentan SIEMPRE: son el contrato del comando.>

**Fase N — Cierre.**
<Estados finales de los artefactos (tabla de transiciones: §7 de CONVENTIONS — fuente única),
ledger marcado, medición cerrada (usage-meter close), handoff u oferta siguiente.>

## Reglas duras

- Bucles acotados (máx. 3 intentos) con salida explícita al agotarse: qué se le presenta al usuario.
- Transiciones de estado según §7 de CONVENTIONS (no dejar artefactos en `borrador`).
- Todo veredicto sale de un script con exit codes, no de la prosa.
