# claude-agents

Agentes custom para **Claude Code**, empaquetados como plugin instalable. Incluye seis agentes y tres skills compartidas, pensados para reutilizarse en cualquier proyecto.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Agentes

| Agente | Qué hace |
|--------|----------|
| **nemesis** | Auditoría de ciberseguridad end-to-end: SAST (análisis estático, skill `cybersecurity`) + DAST (pentest activo **solo local**), con memoria persistente e informe visual `index.html`. |
| **evaluator** | Evalúa/presupuesta una **especificación** (la crea si llega por el prompt) en `docs/roadmap/<fecha>-<slug>/`: esfuerzo, coste € y previsión de tokens. Hace *handoff* a `planner`. |
| **planner** | Genera planes de implementación detallados y **presupuestados** (tiempo, coste €, previsión de tokens) en `docs/roadmap/`. |
| **pdfy** | Convierte archivos a **PDF con aspecto moderno** (Markdown, HTML y Word → PDF vía Chromium headless + tema CSS), usando la skill `to-pdf`. |
| **qa** | Audita un plan ejecutando **E2E con Playwright** (solo local), captura evidencias y genera un informe md+pdf con checklist manual en `docs/roadmap/<slug>/testing/`. |
| **documenter** | Genera y mantiene la **documentación** técnica y de producto del proyecto bajo `docs/`, con estructura **derivada del propio proyecto** (índice, RAG-INDEX, arquitectura, stack, unidades, guías, producto). Sincroniza en Confluence. |

Skills compartidas:
- **cybersecurity** — revisión de seguridad en 8 dimensiones (OWASP, CWE, secretos, dependencias, IaC, threat intel, autorización, compliance). La usa `nemesis`.
- **to-pdf** — conversión de Markdown/HTML/Word a PDF con tema moderno. La usan `pdfy` y `qa`.
- **confluence-publish** — publica/espeja `docs/` en **Confluence** vía el conector Atlassian (asistente guiado; elige espacio y anclaje raíz/hijo; idempotente). La usan `planner`, `evaluator` y `qa`, que sincronizan sus cambios de `docs/` automáticamente.

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

## Actualizar

Los plugins **no se auto-actualizan**, y la actualización se detecta **por número de versión** (sube `version` en `.claude-plugin/plugin.json` **y** `marketplace.json` al publicar).

1. **Publica** los cambios en el repo (nueva versión + push; opcional tag).
2. **Actualiza en tu cliente:**
   - **CLI de Claude Code:** `/plugin marketplace update daycry` → `/plugin update custom-agents@daycry` → `/reload-plugins`.
   - **Claude Desktop / Cowork (UI):** menú **Customize → Plugins**, en el marketplace `daycry` usa **Actualizar**. Si el botón está **deshabilitado**, **quítalo y vuelve a añadirlo** (menú **⋯ → Remove**, luego **"+" → Add marketplace → Add from a repository** con la URL del repo).
3. Si sigue mostrando la versión antigua (caché): reinstala (`/plugin uninstall` + `/plugin install`) o borra `~/.claude/plugins/cache/`.

Detalle en [`docs/INSTALL.md`](docs/INSTALL.md) (sección *Actualizar el plugin*).

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
docs/roadmap/<fecha>-<slug>/
├── spec.md              (QUÉ se quiere)
├── evaluation.md        (evaluator: CUÁNTO / si conviene)
├── improvement-plan.md  (planner: CÓMO, paso a paso)
├── tasks.md             (checklist de tareas)
└── testing/             (qa: E2E + informe)
```

`evaluator` especifica y presupuesta → `planner` genera el plan detallado → se implementa → `qa` prueba (E2E) → con los tests en verde, `qa` hace handoff a `documenter`, que **actualiza la documentación** del proyecto reflejando lo implementado y probado (una vez al final del plan, no por tarea). `nemesis` **audita** la seguridad de lo construido. Los tres artefactos (spec, evaluación, plan) se **referencian entre sí** y se actualizan según se crean. `pdfy` exporta cualquiera de esos documentos (u otros) a **PDF** con aspecto moderno.

## Publicación en Confluence

La skill `confluence-publish` espeja `docs/` en **Confluence** usando el conector oficial de
Atlassian (Rovo MCP). Es **opcional (opt-in)**: la primera vez la skill pregunta si quieres
sincronizar; si dices que no, lo recuerda (`enabled: false`) y no vuelve a preguntar ni sincroniza.
Si dices que sí, eliges espacio y dónde anclar el árbol (raíz del espacio o bajo una página
existente); la decisión se guarda en `.claude/confluence.json` y a partir de ahí es automática.
`planner`, `evaluator` y `qa` invocan la skill al escribir en `docs/`, de modo que —si está
activada— la documentación en Confluence se mantiene al día (crear/actualizar; el borrado se marca
como obsoleto porque el conector no permite eliminar páginas). **`docs/security-scan/` nunca se publica.**

Requiere dar de alta el conector de Atlassian una vez: en **Cowork/Desktop** desde
*Customize → Connectors*; en **CLI/VS Code** con `claude mcp add`. En Cowork el paso de elegir
destino usa un navegador de árbol interactivo; en CLI/VS Code es conversacional. Detalle en
[`docs/INSTALL.md`](docs/INSTALL.md).

## Estructura

```
claude-agents/               (se despliega como .claude/)
├── .claude-plugin/          # manifiesto del plugin + marketplace
├── agents/<nombre>.md       # definiciones de los agentes
├── skills/<skill>/          # skills compartidas
├── agent-kits/<agente>/     # toolkits/plantillas privadas por agente
└── docs/                    # documentación (índice, convenciones, por agente)
```

Documentación: [índice](docs/README.md) · [convenciones](docs/CONVENTIONS.md) · [instalación](docs/INSTALL.md) · [changelog](CHANGELOG.md).

## Seguridad

El agente `nemesis` hace pentest **activo solo contra hosts locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas), impuesto por un guardrail. No apunta a sistemas de terceros; la explotación activa (`sqlmap`) requiere opt-in explícito. Los informes con hallazgos son sensibles y quedan gitignored.

## Licencia

[Apache-2.0](LICENSE) © 2026 daycry
