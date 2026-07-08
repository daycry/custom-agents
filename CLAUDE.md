# CLAUDE.md

Contexto para Claude Code al trabajar en este repositorio.

## Qué es esto

Repositorio de **agentes custom** para Claude Code, con sus skills y toolkits. El contenido se despliega en la carpeta `.claude/` de un proyecto (ver `docs/INSTALL.md`). No es una aplicación: es un bundle de agentes reutilizables.

También está empaquetado como **plugin** (`.claude-plugin/plugin.json` + `marketplace.json`): puede instalarse vía marketplace git y reutilizarse en cualquier proyecto. Por eso los agentes **no** usan rutas fijas a sus kits; las resuelven en runtime con `find` sobre `$PWD/.claude` y `$HOME/.claude` (ver regla 5 de `docs/CONVENTIONS.md`).

## Estructura

```
custom-agents/               (se despliega como .claude/)
├── agents/<nombre>.md       # definición de cada agente (plano, uno por fichero)
├── skills/<skill>/          # skills COMPARTIDAS (reutilizables entre agentes)
├── agent-kits/<agente>/     # toolkits PRIVADOS por agente (scripts, plantillas)
├── docs/                    # TODA la documentación
│   ├── README.md            # índice maestro de agentes y skills
│   ├── CONVENTIONS.md       # convención de organización y dependencias
│   ├── INSTALL.md           # despliegue del bundle
│   └── agents/<nombre>*.md  # documentación por agente
└── CLAUDE.md                # este fichero
```

## Reglas al trabajar aquí

- **Antes de crear o mover nada, lee `docs/CONVENTIONS.md`.** Define dónde va cada artefacto y cómo evitar colisiones.
- **La documentación va SIEMPRE en `docs/`**, nunca junto al código. Al añadir un agente, escribe su doc en `docs/agents/<nombre>.md` y añade la fila en `docs/README.md`.
- **Un agente = un nombre único en kebab-case**, usado igual en `agents/<nombre>.md`, `agent-kits/<nombre>/` y `docs/agents/<nombre>.md`. El `name:` del frontmatter debe coincidir.
- **Compartido vs. privado:** si un recurso lo usará más de un agente, va en `skills/`; si es específico de uno, en `agent-kits/<agente>/`.
- **Dependencias en el frontmatter del agente** (bloque `dependencies:` con `skills`, `kits`, `agents`). Es la fuente de verdad; Claude Code ignora esas claves extra pero a nosotros nos dan el grafo de un vistazo.
- **Rutas en scripts:** relativas entre sí (`dirname "$BASH_SOURCE"`), nunca absolutas del repo. El agente `.md` invoca su toolkit con la ruta de despliegue `.claude/agent-kits/<nombre>/...` y las skills con `.claude/skills/<skill>/`.

## Agentes actuales

- **nemesis** — auditoría de ciberseguridad end-to-end: SAST (skill `cybersecurity`) + DAST/pentest activo local (kit `agent-kits/nemesis`), con memoria e informe visual. Doc: `docs/agents/nemesis.md`.
- **planner** — genera planes de implementación detallados y presupuestados (tiempo, coste €, tokens) en `docs/plans/<fecha>-<slug>/` (kit `agent-kits/planner`). Doc: `docs/agents/planner.md`.
- **evaluator** — evalúa/presupuesta una spec de `docs/specs/` (si llega por prompt, la crea primero) y escribe en `docs/evaluations/<fecha>-<slug>/` (kit `agent-kits/evaluator`); enlaza spec↔evaluación y hace handoff a `planner`. Doc: `docs/agents/evaluator.md`.

**Cadena de artefactos:** `docs/specs/<slug>.md` → `docs/evaluations/<fecha>-<slug>/` → `docs/plans/<fecha>-<slug>/`, con referencias bidireccionales que se rellenan según se crea cada uno (ver regla 7 de `docs/CONVENTIONS.md`).

## Invariante de seguridad (no negociable)

El agente `nemesis` hace pentest **activo** solo contra hosts **locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas), impuesto por `agent-kits/nemesis/tools/lib-guardrail.sh`. Nunca puentees el guardrail ni apuntes a sistemas de terceros. La explotación activa (`sqlmap`) requiere opt-in explícito del usuario.

## Añadir un agente nuevo (resumen)

1. Nombre único en kebab-case.
2. `agents/<nombre>.md` con frontmatter (incluido `dependencies`).
3. Scripts propios → `agent-kits/<nombre>/`; reutilizables → `skills/<skill>/`.
4. Doc en `docs/agents/<nombre>.md` + fila en `docs/README.md`.
5. Verifica que no haya nombres duplicados ni rutas absolutas rotas.

Detalle completo en `docs/CONVENTIONS.md`.
