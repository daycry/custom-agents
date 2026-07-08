# claude-agents

Agentes custom para **Claude Code**, empaquetados como plugin instalable. Incluye cuatro agentes y dos skills compartidas, pensados para reutilizarse en cualquier proyecto.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Agentes

| Agente | Qué hace |
|--------|----------|
| **nemesis** | Auditoría de ciberseguridad end-to-end: SAST (análisis estático, skill `cybersecurity`) + DAST (pentest activo **solo local**), con memoria persistente e informe visual `index.html`. |
| **evaluator** | Evalúa/presupuesta una **especificación** de `docs/specs/` (la crea si llega por el prompt) en `docs/evaluations/`: esfuerzo, coste € y previsión de tokens. Hace *handoff* a `planner`. |
| **planner** | Genera planes de implementación detallados y **presupuestados** (tiempo, coste €, previsión de tokens) en `docs/plans/`. |
| **pdfy** | Convierte archivos a **PDF con aspecto moderno** (Markdown, HTML y Word → PDF vía Chromium headless + tema CSS), usando la skill `to-pdf`. |

Skills compartidas:
- **cybersecurity** — revisión de seguridad en 8 dimensiones (OWASP, CWE, secretos, dependencias, IaC, threat intel, autorización, compliance). La usa `nemesis`.
- **to-pdf** — conversión de Markdown/HTML/Word a PDF con tema moderno. La usa `pdfy`.

## Instalación (recomendada: plugin)

En Claude Code, dentro de cualquier proyecto:

```
/plugin marketplace add daycry/claude-agents
/plugin install custom-agents@daycry
```

Los agentes quedan disponibles en **todos los proyectos** de la máquina. Comprueba con `/agents`.

> **Nota:** los comandos `/plugin` funcionan en la **CLI de Claude Code** (terminal), no en la extensión de VS Code ni en la app de escritorio. Si usas un IDE, instala a nivel usuario (ver abajo).

<details>
<summary>Otras vías (probar rápido o nivel usuario)</summary>

**Probar en un proyecto** (symlink del repo como `.claude/`):

```bash
git clone https://github.com/daycry/claude-agents.git
ln -s "$(pwd)/claude-agents" "/ruta/al/proyecto/.claude"
```

**Nivel usuario** (disponible en todos tus proyectos, sin plugin):

```bash
cp -r claude-agents/agents/.     "$HOME/.claude/agents/"
cp -r claude-agents/skills/.     "$HOME/.claude/skills/"
cp -r claude-agents/agent-kits/. "$HOME/.claude/agent-kits/"
```

Detalle completo en [`docs/INSTALL.md`](docs/INSTALL.md).
</details>

## Uso

Invoca un agente por su nombre, o deja que Claude delegue automáticamente:

```
@evaluator presupuesta esta especificación: …
@planner prepara un plan para añadir autenticación 2FA
@nemesis audita la seguridad de este proyecto
@pdfy convierte a PDF docs/informe.docx
```

Cada agente hace un onboarding breve la primera vez (confirma parámetros y, en el caso de `nemesis`/`pdfy`, pide permiso antes de instalar herramientas).

## Cómo encaja

Cadena de trabajo:

```
docs/specs/<slug>.md          →  docs/evaluations/<fecha>-<slug>/  →  docs/plans/<fecha>-<slug>/
   (spec: QUÉ)                     (evaluator: CUÁNTO / conviene)       (planner: CÓMO, paso a paso)
```

`evaluator` especifica y presupuesta → `planner` genera el plan detallado → se implementa → `nemesis` **audita** la seguridad de lo construido. Los tres artefactos (spec, evaluación, plan) se **referencian entre sí** y se actualizan según se crean. `pdfy` exporta cualquiera de esos documentos (u otros) a **PDF** con aspecto moderno.

## Estructura

```
claude-agents/               (se despliega como .claude/)
├── .claude-plugin/          # manifiesto del plugin + marketplace
├── agents/<nombre>.md       # definiciones de los agentes
├── skills/<skill>/          # skills compartidas
├── agent-kits/<agente>/     # toolkits/plantillas privadas por agente
└── docs/                    # documentación (índice, convenciones, por agente)
```

Documentación: [índice](docs/README.md) · [convenciones](docs/CONVENTIONS.md) · [instalación](docs/INSTALL.md).

## Seguridad

El agente `nemesis` hace pentest **activo solo contra hosts locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas), impuesto por un guardrail. No apunta a sistemas de terceros; la explotación activa (`sqlmap`) requiere opt-in explícito. Los informes con hallazgos son sensibles y quedan gitignored.

## Licencia

[Apache-2.0](LICENSE) © 2026 daycry
