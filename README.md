# claude-agents

Agentes custom para **Claude Code**, empaquetados como plugin instalable. Incluye tres agentes y una skill compartida, pensados para reutilizarse en cualquier proyecto.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Agentes

| Agente | Qué hace |
|--------|----------|
| **nemesis** | Auditoría de ciberseguridad end-to-end: SAST (análisis estático, skill `cybersecurity`) + DAST (pentest activo **solo local**), con memoria persistente e informe visual `index.html`. |
| **planner** | Genera planes de implementación detallados y **presupuestados** (tiempo, coste €, previsión de tokens) en `docs/plans/`. |
| **evaluator** | Evalúa/presupuesta el coste de implementar características a partir de un documento de requerimientos, en `docs/evaluations/`. Hace *handoff* a `planner`. |

Skill compartida: **cybersecurity** (revisión de seguridad en 8 dimensiones: OWASP, CWE, secretos, dependencias, IaC, threat intel, autorización, compliance).

## Instalación (recomendada: plugin)

En Claude Code, dentro de cualquier proyecto:

```
/plugin marketplace add daycry/claude-agents
/plugin install custom-agents@daycry
```

Los tres agentes quedan disponibles en **todos los proyectos** de la máquina. Comprueba con `/agents`.

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
@nemesis audita la seguridad de este proyecto
@planner prepara un plan para añadir autenticación 2FA
@evaluator presupuesta lo que pide docs/requerimientos/RFP.md
```

Cada agente hace un onboarding breve la primera vez (confirma parámetros y, en el caso de `nemesis`, pide permiso antes de instalar herramientas).

## Cómo encaja

`evaluator` → decides **qué** hacer y cuánto cuesta → `planner` genera el **plan** detallado → `nemesis` **audita** la seguridad de lo construido.

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
