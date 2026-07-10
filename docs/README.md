# custom-agents — índice de documentación

Repositorio de **agentes custom** para Claude Code, con sus skills y toolkits. Se despliega en la carpeta `.claude/` de un proyecto (ver [`INSTALL.md`](INSTALL.md)).

Antes de añadir o tocar un agente, lee [`CONVENTIONS.md`](CONVENTIONS.md): define dónde va cada cosa y cómo se declaran las dependencias entre agentes para que no se pisen.

## Agentes disponibles

| Agente | Qué hace | Dependencias | Documentación |
|--------|----------|--------------|---------------|
| **nemesis** | Auditoría de ciberseguridad end-to-end: SAST (estático) + DAST (pentest activo local), memoria e informe visual. | skill `cybersecurity`, kit `agent-kits/nemesis` | [nemesis.md](agents/nemesis.md) · [presentación](agents/nemesis-presentacion.md) · [toolkit](agents/nemesis-toolkit.md) |
| **planner** | Genera planes de implementación detallados y presupuestados (tiempo, coste €, tokens) en `docs/roadmap/`. Sincroniza sus docs en Confluence. | kit `agent-kits/planner`, skill `confluence-publish` | [planner.md](agents/planner.md) |
| **evaluator** | Evalúa/presupuesta una spec (la crea si llega por prompt) en `docs/roadmap/<fecha>-<slug>/`. Enlaza spec↔evaluación y hace handoff a `planner`. Sincroniza sus docs en Confluence. | kit `agent-kits/evaluator`, agente `planner`, skill `confluence-publish` | [evaluator.md](agents/evaluator.md) |
| **pdfy** | Convierte archivos a PDF con aspecto moderno (Markdown, HTML y Word → PDF vía Chromium headless + tema CSS). | skill `to-pdf` | [pdfy.md](agents/pdfy.md) |
| **qa** | Audita un plan ejecutando E2E con Playwright (solo local), captura evidencias y genera informe md+pdf con checklist manual en `docs/roadmap/<slug>/testing/`. Sincroniza el informe en Confluence. | skill `to-pdf`, kit `agent-kits/qa`, skill `confluence-publish` | [qa.md](agents/qa.md) |
| **documenter** | Genera y mantiene la documentación técnica y de producto del proyecto bajo `docs/`, con estructura **derivada del propio proyecto** (índice, RAG-INDEX, arquitectura, stack, unidades, guías, producto). Sincroniza en Confluence. | kit `agent-kits/documenter`, skill `confluence-publish` | [documenter.md](agents/documenter.md) |

**Cadena de trabajo (carpeta única por iniciativa):** `docs/roadmap/<fecha>-<slug>/` contiene `spec.md` (qué) → `evaluation.md` (cuánto/si conviene) → `improvement-plan.md` + `tasks.md` (cómo) (+ `testing/`). Se referencian entre sí y se actualizan según se crean (ver regla 7 de [`CONVENTIONS.md`](CONVENTIONS.md)). `pdfy` exporta cualquier documento a PDF.

**Cierre del ciclo (documentación):** al terminar la implementación de un plan y con las pruebas automáticas de `qa` en verde, `qa` hace handoff a `documenter`, que genera/actualiza la documentación de referencia del proyecto (arquitectura, stack, unidades, guías, producto) bajo `docs/`, reflejando el estado final. `documenter` corre **una vez al final del plan**, no por tarea.

**Sincronización con Confluence (opcional, opt-in):** `planner`, `evaluator` y `qa` invocan la skill `confluence-publish` al escribir en `docs/`. La primera vez la skill pregunta si se quiere sincronizar; si se dice que no (`enabled: false`), no vuelve a preguntar ni sincroniza. Si se activa, refleja los cambios en Confluence (crear/actualizar; borrado → marcado como obsoleto) según el espacio/anclaje guardado en `.claude/confluence.json`. Nunca se publica `docs/security-scan/`. Alta del conector Atlassian: ver [`INSTALL.md`](INSTALL.md).

## Skills compartidas

| Skill | Qué hace | Usada por |
|-------|----------|-----------|
| **cybersecurity** | Análisis estático de seguridad en 8 dimensiones (OWASP, CWE, secretos, deps, IaC, threat intel, authz, compliance). | nemesis |
| **to-pdf** | Convierte Markdown/HTML/Word a PDF con tema moderno (Chromium headless + CSS). | pdfy, qa |
| **confluence-publish** | Publica/espeja la doc del proyecto en Confluence vía el conector Atlassian (Rovo MCP). Cada proyecto elige espacio y anclaje (raíz o hijo del árbol) en `.claude/confluence.json`; idempotente (crea/actualiza). | planner, evaluator, qa |

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
