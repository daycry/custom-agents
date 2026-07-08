# custom-agents — índice de documentación

Repositorio de **agentes custom** para Claude Code, con sus skills y toolkits. Se despliega en la carpeta `.claude/` de un proyecto (ver [`INSTALL.md`](INSTALL.md)).

Antes de añadir o tocar un agente, lee [`CONVENTIONS.md`](CONVENTIONS.md): define dónde va cada cosa y cómo se declaran las dependencias entre agentes para que no se pisen.

## Agentes disponibles

| Agente | Qué hace | Dependencias | Documentación |
|--------|----------|--------------|---------------|
| **nemesis** | Auditoría de ciberseguridad end-to-end: SAST (estático) + DAST (pentest activo local), memoria e informe visual. | skill `cybersecurity`, kit `agent-kits/nemesis` | [nemesis.md](agents/nemesis.md) · [presentación](agents/nemesis-presentacion.md) · [toolkit](agents/nemesis-toolkit.md) |
| **planner** | Genera planes de implementación detallados y presupuestados (tiempo, coste €, tokens) en `docs/plans/`. | kit `agent-kits/planner` | [planner.md](agents/planner.md) |
| **evaluator** | Evalúa/presupuesta una spec de `docs/specs/` (la crea si llega por prompt) → `docs/evaluations/`. Enlaza spec↔evaluación y hace handoff a `planner`. | kit `agent-kits/evaluator`, agente `planner` | [evaluator.md](agents/evaluator.md) |
| **pdfy** | Convierte archivos a PDF con aspecto moderno (Markdown, HTML y Word → PDF vía Chromium headless + tema CSS). | skill `to-pdf` | [pdfy.md](agents/pdfy.md) |

**Cadena de trabajo:** `docs/specs/<slug>.md` (spec) → `docs/evaluations/<fecha>-<slug>/` (evaluator) → `docs/plans/<fecha>-<slug>/` (planner). Los tres artefactos se referencian entre sí y se actualizan según se crean (ver regla 7 de [`CONVENTIONS.md`](CONVENTIONS.md)). `pdfy` exporta cualquier documento a PDF.

## Skills compartidas

| Skill | Qué hace | Usada por |
|-------|----------|-----------|
| **cybersecurity** | Análisis estático de seguridad en 8 dimensiones (OWASP, CWE, secretos, deps, IaC, threat intel, authz, compliance). | nemesis |
| **to-pdf** | Convierte Markdown/HTML/Word a PDF con tema moderno (Chromium headless + CSS). | pdfy |

## Mapa del repositorio

```
custom-agents/               (se despliega como .claude/)
├── agents/                  # definición de cada agente (*.md, planos)
├── skills/                  # skills COMPARTIDAS entre agentes
├── agent-kits/              # toolkits PRIVADOS por agente (namespaced)
└── docs/                    # TODA la documentación (estás aquí)
    ├── README.md            # este índice
    ├── CONVENTIONS.md       # convención de organización y dependencias
    ├── INSTALL.md           # cómo desplegar el bundle
    └── agents/              # un doc por agente
```
