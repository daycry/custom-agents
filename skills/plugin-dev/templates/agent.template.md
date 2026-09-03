---
# name == nombre del fichero agents/<nombre-kebab>.md (kebab-case, único en el repo)
name: <nombre-kebab>
description: <Qué hace, en 2-4 frases con el CRITERIO que aporta (no solo el qué). Termina SIEMPRE con los disparadores:> Úsalo cuando el usuario diga "<frase 1>", "<frase 2>", "<frase 3>".
# model: haiku (mecánico) · sonnet (desarrollo estándar) · opus (razonamiento crítico) · inherit
model: sonnet
# effort: medium por defecto · high si model es opus (low|medium|high|xhigh|max — oficiales). Override por
# proyecto: .claude/dev.json `modelos.<agente>` (lo resuelve agent-kits/shared/model-tier.py, no el agente)
effort: medium
# tools MÍNIMOS reales; añade Bash/Write/Edit solo si los usa de verdad
tools: Read, Grep, Glob
dependencies:
  skills: []                            # skills de skills/ que invoca (deben existir)
  kits: []                              # p. ej. agent-kits/<nombre-kebab>
  agents: []                            # handoffs a otros agentes, por nombre; sin ciclos
---

# <nombre> — <rol en una línea>

<Párrafo de contexto: qué problema resuelve y qué NO hace (límites explícitos evitan que el
agente se salga de su rol).>

## Resolución del kit (si tiene agent-kits/<nombre>/)

```bash
MIKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/<nombre-kebab>' 2>/dev/null | head -1)"
# sin kit (instalación parcial): <fallback de una línea> y avisa — NUNCA bloquees
```

## Proceso

**P1 — <fase>.** <Qué hace y qué evidencia produce.>

**P2 — <fase>.** <…>

**P<n> — Cierre.** <Estados que actualiza, ledger que marca, handoff (a quién y con qué).>

## Reglas duras

- <Regla no negociable 1 — p. ej. guardrail, solo-lectura, opt-in requerido.>
- Los cálculos/veredictos los da `<script>.py` (exit codes), no la prosa.
- Piezas opcionales degradan con aviso; jamás bloquean el ciclo.
