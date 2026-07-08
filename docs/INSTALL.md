# Instalación y despliegue

Bundle de agentes custom para Claude Code: **nemesis** (auditoría SAST+DAST), **planner** (planes presupuestados) y **evaluator** (evaluación de requerimientos), más la skill compartida **cybersecurity**.

Contenido (todo cuelga de la raíz del bundle, que se despliega como `.claude/`):
- `agents/*.md` — definiciones de los agentes.
- `skills/cybersecurity/` — skill SAST compartida.
- `agent-kits/<agente>/` — toolkits/plantillas privadas de cada agente.
- `.claude-plugin/` — manifiesto de plugin y marketplace (para la vía 3).
- `docs/` — documentación (no se carga como código; el loader la ignora).

Las rutas de los kits se resuelven en tiempo de ejecución con un `find` sobre `$PWD/.claude` y `$HOME/.claude`, así que **los agentes funcionan igual en las tres vías** siguientes.

---

## Vía 1 — Probar en un proyecto (rápido)

Enlaza (o copia) el bundle como `.claude/` del proyecto a probar:

```bash
# symlink (recomendado para probar; refleja cambios del repo al instante)
ln -s "/ruta/al/repo/custom-agents" "/ruta/al/proyecto/.claude"

# o copia
cp -r "/ruta/al/repo/custom-agents/." "/ruta/al/proyecto/.claude/"
```

En Claude Code, dentro del proyecto: `/agents` para verlos e invócalos con `@nemesis`, `@planner`, `@evaluator` (o "usa el agente …").

---

## Vía 2 — Reuso personal en todos tus proyectos (`~/.claude/`)

Copia el contenido a tu carpeta de usuario; queda disponible en **todos tus proyectos** (precedencia: si un proyecto define un agente con el mismo nombre, gana el del proyecto):

```bash
cp -r "/ruta/al/repo/custom-agents/agents/."      "$HOME/.claude/agents/"
cp -r "/ruta/al/repo/custom-agents/skills/."      "$HOME/.claude/skills/"
cp -r "/ruta/al/repo/custom-agents/agent-kits/."  "$HOME/.claude/agent-kits/"
```

El resolvedor de ruta encuentra los kits en `~/.claude/agent-kits/…` automáticamente.

---

## Vía 3 — Plugin + marketplace (recomendado, escalable y para el equipo)

El bundle ya incluye `.claude-plugin/plugin.json` y `.claude-plugin/marketplace.json`. Publica el repo en git (GitHub/GitLab) y, en cualquier proyecto:

```
/plugin marketplace add daycry/claude-agents
/plugin install custom-agents@daycry
```

Tras instalar, los tres agentes quedan disponibles en **todos los proyectos** de la máquina. Actualizaciones: publicas nueva versión en git y `/plugin` la ofrece.

> **Caveat conocido.** En Claude Code, `${CLAUDE_PLUGIN_ROOT}` no se expande dentro del markdown de agentes/skills. Por eso los agentes NO usan rutas fijas: resuelven su kit con `find` sobre `$PWD/.claude` y `$HOME/.claude` (el segundo cubre tanto `~/.claude/` como el caché de plugins `~/.claude/plugins/…`). Es la razón de que las tres vías funcionen sin tocar nada.

---

## Notas específicas de `nemesis`

- El pentest activo SOLO opera contra hosts locales/privados (guardrail `lib-guardrail.sh`). No apunta a terceros.
- La primera vez comprueba su toolkit y PIDE PERMISO antes de instalar lo que falte (binarios en `~/.claude/security-tools/`, fuera del repo).
- Informes en `docs/security-scan/<fecha>/index.html` del proyecto auditado. Esa subruta va en el `.gitignore` del proyecto (los hallazgos son sensibles); el resto de `docs/` sí se versiona.
- Requisitos por máquina: git, curl y python o php. El instalador resuelve el resto.
