// providers.mjs — QUÉ instala cada proveedor y DÓNDE. Datos y planes puros: ni una escritura,
// ni una lectura de disco fuera de `detect()`. Así el plan se puede imprimir (`--dry-run`),
// comparar y testear sin tocar nada.
//
// Un plan es una lista de pasos. Tres tipos, y ninguno más:
//   { type: "copy",  from, to }   copia un fichero o un árbol (recursivo)
//   { type: "write", to, content } escribe un fichero generado por el instalador
//   { type: "merge", to, merge }  fusiona claves en un JSON del usuario SIN pisar lo suyo
//
// El porqué de cada ruta está en `docs/INTEROP.md`; aquí solo vive la ruta.

import { existsSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

// El bundle de Claude Code es el repo entero salvo lo que solo sirve para desarrollarlo.
export const PAYLOAD_CLAUDE = [
  "agents", "commands", "skills", "agent-kits", "hooks", "statusline", ".claude-plugin",
]
// Lo que necesita un runtime que NO lee `agents/` ni `commands/` en markdown de Claude Code:
// las skills (formato común), los kits (los resuelve el `find`) y los hooks (scripts de shell).
export const PAYLOAD_COMUN = ["skills", "agent-kits", "hooks"]

const HOME = homedir()

/** Directorio de configuración global de cada runtime (el de OpenCode NO es `~/.opencode`). */
export const GLOBAL_DIR = {
  "claude-code": join(HOME, ".claude"),
  codex: join(HOME, ".codex"),
  opencode: join(HOME, ".config", "opencode"),
}

/** Nombre del fichero-manifiesto que deja el instalador para poder desinstalar con precisión. */
export const MANIFEST = ".custom-agents-install.json"

// --------------------------------------------------------------------------- Claude Code

const claudeCode = {
  id: "claude-code",
  label: "Claude Code",
  blurb: "plugin nativo — agentes, comandos, skills, hooks y statusline",
  detect: () => existsSync(GLOBAL_DIR["claude-code"]),
  // La vía recomendada no necesita al instalador; se dice al terminar, no se hace por sorpresa.
  hint: "Vía recomendada: `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents`.",
  plan({ root, dest }) {
    return PAYLOAD_CLAUDE.map((p) => ({ type: "copy", from: p, to: join(dest, p) }))
  },
  destino: (scope, dir) => (scope === "user" ? GLOBAL_DIR["claude-code"] : join(dir, ".claude")),
  restart: "Reinicia Claude Code (o `/reload-plugins`).",
}

// --------------------------------------------------------------------------- Codex

const codex = {
  id: "codex",
  label: "Codex",
  blurb: "plugin + agentes `.toml` + comandos como prompts",
  detect: () => existsSync(GLOBAL_DIR.codex),
  hint: "Alternativa con red: `codex plugin marketplace add daycry/custom-agents`.",
  // En Codex el plugin vive en su propia carpeta y el marketplace lo declara. Los agentes son
  // TOML en `agents/`, y los prompts SOLO existen en CODEX_HOME (no hay prompts por proyecto).
  plan({ root, dir, scope, version }) {
    const base = scope === "user" ? GLOBAL_DIR.codex : join(dir, ".codex")
    const plugin = join(base, "plugins", "custom-agents")
    const mktRoot = scope === "user" ? join(HOME, ".agents") : join(dir, ".agents")
    const pasos = [
      ...PAYLOAD_COMUN.map((p) => ({ type: "copy", from: p, to: join(plugin, p) })),
      { type: "copy", from: ".codex-plugin", to: join(plugin, ".codex-plugin") },
      { type: "copy", from: "interop/codex/hooks.json", to: join(plugin, "interop", "codex", "hooks.json") },
      { type: "copy", from: "interop/codex/agents", to: join(base, "agents") },
      // Los prompts (`/prompts:<n>`) solo se leen desde CODEX_HOME: Codex no tiene prompts por
      // proyecto. Se avisa siempre, porque con `--scope project` es lo ÚNICO que sale del proyecto.
      {
        type: "copy",
        from: "interop/codex/prompts",
        to: join(GLOBAL_DIR.codex, "prompts"),
        aviso: scope === "project"
          ? `los comandos van a ${join(GLOBAL_DIR.codex, "prompts")} (fuera del proyecto): Codex solo lee prompts de CODEX_HOME`
          : null,
      },
      {
        type: "merge",
        to: join(mktRoot, "plugins", "marketplace.json"),
        merge: marketplaceCodex(mktRoot, plugin, version),
      },
    ]
    return pasos
  },
  destino: (scope, dir) =>
    join(scope === "user" ? GLOBAL_DIR.codex : join(dir, ".codex"), "plugins", "custom-agents"),
  restart: "Reinicia Codex (los skills y prompts se leen al arrancar la sesión).",
}

/** Entrada de marketplace de Codex apuntando a la copia instalada (ruta relativa a su raíz). */
function marketplaceCodex(mktRoot, plugin, version) {
  // `source.path` se resuelve contra la RAÍZ del marketplace (el padre de `plugins/`), no
  // contra la carpeta del fichero.
  const rel = "./" + relPosix(join(mktRoot, ".."), plugin)
  return {
    name: "daycry",
    interface: { displayName: "Agentes custom de daycry" },
    plugins: [{
      name: "custom-agents",
      version,
      source: { source: "local", path: rel },
      policy: { installation: "AVAILABLE", authentication: "NONE" },
      category: "Productivity",
    }],
  }
}

// --------------------------------------------------------------------------- OpenCode

const opencode = {
  id: "opencode",
  label: "OpenCode",
  blurb: "agentes + comandos + skills + adaptador de hooks en JS",
  detect: () => existsSync(GLOBAL_DIR.opencode) || existsSync(join(HOME, ".opencode")),
  hint: "OpenCode también lee `.claude/skills/`: si ya tienes el bundle de Claude Code, las skills se comparten.",
  plan({ dir, scope, root }) {
    const base = scope === "user" ? GLOBAL_DIR.opencode : join(dir, ".opencode")
    // El config de proyecto de OpenCode vive en la RAÍZ del proyecto, no dentro de `.opencode/`.
    const cfg = scope === "user" ? join(base, "opencode.json") : join(dir, "opencode.json")
    // `instructions` es relativo a la raíz del proyecto (o del config global).
    const idxRel = scope === "user"
      ? join(base, "custom-agents-index.md").split(/[\\/]/).join("/")
      : ".opencode/custom-agents-index.md"
    return [
      ...PAYLOAD_COMUN.map((p) => ({ type: "copy", from: p, to: join(base, p) })),
      { type: "copy", from: "interop/opencode/agents", to: join(base, "agents") },
      { type: "copy", from: "interop/opencode/commands", to: join(base, "commands") },
      {
        type: "copy",
        from: "interop/opencode/plugins/custom-agents-hooks.js",
        to: join(base, "plugins", "custom-agents-hooks.js"),
      },
      {
        type: "copy",
        from: "interop/opencode/custom-agents-index.md",
        to: join(base, "custom-agents-index.md"),
      },
      // Config del usuario: se FUSIONA. `instructions` se une sin duplicar.
      //
      // `permission` va en `onlyIfMissing` A PROPÓSITO: en OpenCode «gana la última regla que
      // casa», así que añadir `skill: {"*": "allow"}` DESPUÉS de un `"internal-*": "deny"` del
      // usuario le abriría en silencio una skill que había cerrado. Si ya tiene política de
      // permisos, se respeta entera y el instalador solo lo dice; si no tiene ninguna, se deja
      // la mínima para que las skills del plugin carguen sin preguntar.
      {
        type: "merge",
        to: cfg,
        merge: {
          $schema: "https://opencode.ai/config.json",
          instructions: [idxRel],
          permission: { skill: { "*": "allow" } },
        },
        onlyIfMissing: ["permission"],
        nota: "si `permission` ya existía, tu política manda: comprueba que las skills `custom-agents` "
              + "no caigan en un `deny` (OpenCode aplica la ÚLTIMA regla que casa).",
      },
    ]
  },
  destino: (scope, dir) => (scope === "user" ? GLOBAL_DIR.opencode : join(dir, ".opencode")),
  restart: "Reinicia OpenCode (los plugins se cargan al arrancar).",
}

export const PROVIDERS = [claudeCode, codex, opencode]
export const IDS = PROVIDERS.map((p) => p.id)

export function getProvider(id) {
  return PROVIDERS.find((p) => p.id === id)
}

/** Construye el plan de un proveedor. `dest` se deriva de su `destino()`. */
export function buildPlan(provider, { root, dir, scope, version }) {
  const dest = provider.destino(scope, dir)
  return provider.plan({ root, dir, dest, scope, version })
}

function relPosix(from, to) {
  // `path.relative` sin importar `path` dos veces y siempre con `/` (los JSON no llevan `\`).
  const a = from.split(/[\\/]/).filter(Boolean)
  const b = to.split(/[\\/]/).filter(Boolean)
  let i = 0
  while (i < a.length && i < b.length && a[i] === b[i]) i++
  return [...Array(a.length - i).fill(".."), ...b.slice(i)].join("/")
}
