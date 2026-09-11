// providers.mjs — QUÉ instala cada proveedor y DÓNDE. Datos y planes puros: ni una escritura,
// ni una lectura de disco fuera de `detect()` y de la detección de CLIs en el `PATH`. Así el plan
// se puede imprimir (`--dry-run`), comparar y testear sin tocar nada.
//
// Un plan es una lista de pasos. Seis tipos, y ninguno más:
//   { type: "copy",  from, to }      copia un fichero o un árbol (recursivo)
//   { type: "write", to, content }   escribe un fichero generado por el instalador
//   { type: "merge", to, merge }     fusiona claves en un JSON del usuario SIN pisar lo suyo
//   { type: "exec",  cmd, args }     ejecuta la CLI oficial del runtime (la vía que él bendice)
//   { type: "json-set", to, set }    pone EXACTAMENTE unas claves en un JSON del usuario
//                                    (a diferencia de `merge`, SÍ las sobrescribe; el manifiesto
//                                    apunta cuáles para poder quitarlas al desinstalar)
//   { type: "toml-set", to, tabla, clave, valor }   pone una clave en una tabla de un TOML,
//                                    sin reescribir ninguna otra línea del fichero
//
// El porqué de cada ruta está en `docs/INTEROP.md`; aquí solo vive la ruta.

import { execFileSync } from "node:child_process"
import { existsSync, statSync } from "node:fs"
import { homedir } from "node:os"
import { join, resolve } from "node:path"

// El bundle de Claude Code es el repo entero salvo lo que solo sirve para desarrollarlo.
export const PAYLOAD_CLAUDE = [
  "agents", "commands", "skills", "agent-kits", "hooks", "statusline", ".claude-plugin",
]
// Lo que necesita un runtime que NO lee `agents/` ni `commands/` en markdown de Claude Code:
// las skills (formato común), los kits (los resuelve el `find`) y los hooks (scripts de shell).
export const PAYLOAD_COMUN = ["skills", "agent-kits", "hooks"]

/** Nombres fijados por `.claude-plugin/marketplace.json` y `.claude-plugin/plugin.json`. */
export const MKT = "daycry"
export const PLUGIN = "custom-agents"
export const PLUGIN_ID = `${PLUGIN}@${MKT}`
/** Fuente por defecto del marketplace: el repo público (la misma que la vía nativa). */
export const FUENTE_DEFECTO = "daycry/custom-agents"
/** Primera versión de Codex con `codex plugin marketplace add` (la que exige también claude-mem). */
export const CODEX_MIN = "0.128.0"

// El HOME se lee EN CADA LLAMADA, nunca al importar: los tests inyectan uno temporal por `env` y
// el instalador tiene que verlo (antes se congelaba en una constante de módulo).
const home = () => homedir()

/** Config de Claude Code: `~/.claude` salvo que `CLAUDE_CONFIG_DIR` diga otra cosa (la respeta en todo). */
export const claudeConfigDir = () => process.env.CLAUDE_CONFIG_DIR || join(home(), ".claude")

/** Directorio de configuración global de cada runtime (el de OpenCode NO es `~/.opencode`). */
export const GLOBAL_DIR = {
  get "claude-code"() { return claudeConfigDir() },
  get codex() { return join(home(), ".codex") },
  get opencode() { return join(home(), ".config", "opencode") },
}

/** Nombre del fichero-manifiesto que deja el instalador para poder desinstalar con precisión. */
export const MANIFEST = ".custom-agents-install.json"
/**
 * Claude Code puede estar instalado de DOS maneras a la vez en el mismo scope (el bundle copiado
 * en `.claude/` de un instalador anterior y el plugin registrado), y en scope `project` las dos
 * escriben en la MISMA carpeta. Con un solo nombre de manifiesto la segunda instalación pisaba el
 * inventario de la primera y dejaba sus ficheros huérfanos: cada modo tiene el suyo.
 */
export const MANIFEST_PLUGIN = ".custom-agents-install.plugin.json"
/** Los dos nombres de manifiesto posibles (lo que `status`/`uninstall` tienen que mirar). */
export const MANIFIESTOS = [MANIFEST, MANIFEST_PLUGIN]

/**
 * Extensiones que este instalador sabe ARRANCAR de verdad: `.exe`/`.com` directas y `.cmd`/`.bat`
 * a través de `cmd.exe` (ver `correr()`). El PATHEXT de Windows 11 trae además `.VBS`, `.JS`,
 * `.WSF`, `.MSC`… que `correr()` NO lanza: darlas por buenas daba `spawnSync … EFTYPE` y abortaba
 * el proveedor en vez de caer al respaldo. Cualquier otra extensión es `no-ejecutable`.
 *
 * `npm i -g` deja en la misma carpeta dos ficheros con el mismo nombre: un shim POSIX SIN
 * extensión (para Git Bash) y un `.cmd` (para Windows). `where.exe` devuelve los dos y el shim
 * suele salir primero: coger ese daba `ENOENT` (o «versión desconocida») teniendo la CLI delante.
 */
const PATHEXT_DEFECTO = ".COM;.EXE;.BAT;.CMD"
const ARRANCABLES = [".EXE", ".COM", ".CMD", ".BAT"]

/**
 * Orden en el que se prueban las extensiones: el de PATHEXT, que es el que sigue el intérprete de
 * comandos (por defecto `.COM;.EXE;.BAT;.CMD`, así que un `claude.exe` gana a un `claude.cmd`).
 * Un orden fijo propio hacía que el instalador ejecutara un lanzador DISTINTO del que usa el
 * usuario cuando conviven el instalador nativo (`.exe`) y los shims de npm (`.cmd`).
 */
function preferencia() {
  const ext = (process.env.PATHEXT || PATHEXT_DEFECTO).split(";")
    .map((e) => e.trim().toUpperCase()).filter(Boolean)
  const orden = ext.filter((e) => ARRANCABLES.includes(e))
  return orden.length ? orden : PATHEXT_DEFECTO.split(";").filter((e) => ARRANCABLES.includes(e))
}

/**
 * De TODOS los resultados de `where.exe`, el que Node puede ejecutar de verdad. Pura, para poder
 * probar el layout de npm (shim sin extensión primero, `.cmd` después) sin un PATH de verdad.
 * `ejecutable: false` significa «lo hay, pero no lo puedo lanzar»: hay que degradar, no reventar.
 */
export function elegirEjecutable(candidatos, plataforma = process.platform) {
  const lista = (candidatos || []).map((s) => String(s).trim()).filter(Boolean)
  if (!lista.length) return { ruta: null, ejecutable: false }
  if (plataforma !== "win32") return { ruta: lista[0], ejecutable: true }
  for (const ext of preferencia()) {
    const hit = lista.find((c) => c.toUpperCase().endsWith(ext))
    if (hit) return { ruta: hit, ejecutable: true }
  }
  return { ruta: lista[0], ejecutable: false }
}

function dondeEsta(cmd) {
  try {
    const salida = execFileSync(process.platform === "win32" ? "where.exe" : "which", [cmd],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
    return salida.split(/\r?\n/)
  } catch { return [] }
}

/**
 * Estado de una CLI del PATH: `"si"` (se puede ejecutar), `"no"` (no está) o `"no-ejecutable"`
 * (está, pero solo como shim que Node no arranca → se degrada al respaldo diciéndolo).
 */
export function estadoCli(cmd) {
  const { ruta, ejecutable } = elegirEjecutable(dondeEsta(cmd))
  return !ruta ? "no" : ejecutable ? "si" : "no-ejecutable"
}

/** Ruta REAL y ejecutable de un comando del PATH, o `null` (incluido el shim no lanzable). */
export function rutaDe(cmd) {
  const { ruta, ejecutable } = elegirEjecutable(dondeEsta(cmd))
  return ejecutable ? ruta : null
}

/** ¿Está este comando en el PATH Y se puede ejecutar desde Node? */
export const enPath = (cmd) => Boolean(rutaDe(cmd))

/**
 * Cómo se declara la fuente de un marketplace en el registro de Claude Code. Las dos formas están
 * tomadas de un `~/.claude` real: `github` + `repo` para `owner/repo`, `directory` + `path` para
 * una ruta local (que es lo que escribe `claude plugin marketplace add <ruta>`).
 *
 * `owner/repo` SOLO si además de casar el patrón no puede ser una ruta: `./mi-clon` y `../x` casan
 * con `[\w.-]+/[\w.-]+` y se escribían como `repo: "./mi-clon"` — irresoluble, y es justo el
 * ejemplo del `--help`. Una ruta se resuelve a ABSOLUTA: el registro lo lee Claude Code desde
 * cualquier directorio, no desde aquel en el que se ejecutó el instalador.
 */
export function clasificarFuente(fuente) {
  const s = String(fuente || "")
  const pareceRuta = /^[.~]/.test(s) || /^[/\\]/.test(s) || /^[A-Za-z]:([/\\]|$)/.test(s)
  let existe = false
  try { existe = existsSync(s) && statSync(s).isDirectory() } catch { existe = false }
  const esRepo = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(s) && !pareceRuta && !existe
  return esRepo ? { source: "github", repo: s } : { source: "directory", path: resolve(s) }
}
const fuenteRegistro = clasificarFuente

// --------------------------------------------------------------------------- Claude Code

// Dos modos, y el bueno es el de por defecto:
//   · `plugin` (defecto) — Claude Code se entera de verdad: hooks, statusline, namespace
//     `/custom-agents:` y actualizaciones. Vía oficial (`claude plugin …`) si la CLI está en el
//     PATH; si no, se escribe el mismo registro que escribe ella.
//   · `copy` — el bundle copiado a `.claude/` (vías 1 y 2 de `docs/INSTALL.md`). Sirve para leer
//     las piezas, pero Claude Code NO lee `hooks/hooks.json` fuera de un plugin instalado.
function planClaude(o) {
  const { dir, dest, scope, version } = o
  const modo = o.modo || "plugin"

  if (modo === "copy") {
    const pasos = PAYLOAD_CLAUDE.map((p) => ({ type: "copy", from: p, to: join(dest, p) }))
    pasos[0].aviso = "bundle copiado: hooks y statusline NO se registran y no hay namespace "
      + "`/custom-agents:` (Claude Code solo lee `hooks/hooks.json` dentro de un plugin instalado) "
      + "— quita `--mode copy` para instalarlo como plugin"
    return pasos
  }

  const fuente = o.source || FUENTE_DEFECTO
  // Tres estados, no dos: `claude` puede estar en el PATH y aun así no ser lanzable desde Node
  // (shim de npm sin extensión en Windows). Ese caso NO es «hay CLI»: es respaldo, y se dice.
  const cli = o.cli?.claude === undefined
    ? estadoCli("claude")
    : (o.cli.claude === true ? "si" : o.cli.claude === false ? "no" : String(o.cli.claude))
  if (cli === "si") {
    return [
      {
        type: "exec",
        cmd: "claude",
        args: ["plugin", "marketplace", "add", fuente, "--scope", scope],
        // Si ya estaba declarado, `add` falla y da igual: se sigue con el marketplace existente.
        siFalla: "aviso",
      },
      {
        type: "exec",
        cmd: "claude",
        args: ["plugin", "install", PLUGIN_ID, "--scope", scope, "--yes"],
        siFalla: "error",
        deshacer: ["claude", "plugin", "uninstall", PLUGIN_ID, "--scope", scope],
      },
    ]
  }

  // Respaldo sin CLI: escribir el registro que Claude Code lee al arrancar. El formato está
  // verificado contra un `~/.claude` real (y es el mismo que escribe claude-mem); al ser formato
  // interno, la vía preferida sigue siendo la CLI — ver `docs/INTEROP.md`.
  const cfg = claudeConfigDir()
  const mkt = join(cfg, "plugins", "marketplaces", MKT)
  const cache = join(cfg, "plugins", "cache", MKT, PLUGIN, version)
  const paquete = [...PAYLOAD_CLAUDE, "package.json"]
  const ahora = new Date().toISOString()
  const origen = fuenteRegistro(fuente)
  const ajustes = scope === "user" ? join(cfg, "settings.json") : join(dir, ".claude", "settings.json")
  const enSettings = { [`enabledPlugins.${PLUGIN_ID}`]: true }
  if (scope === "project") enSettings[`extraKnownMarketplaces.${MKT}`] = { source: origen }

  const copias = [
    ...paquete.map((p) => ({ type: "copy", from: p, to: join(mkt, p) })),
    ...paquete.map((p) => ({ type: "copy", from: p, to: join(cache, p) })),
  ]
  copias[0].aviso = (cli === "no-ejecutable"
    ? "`claude` encontrado pero no ejecutable desde Node (shim de npm sin extensión, `.ps1`, `.vbs`…): "
      + "uso el registro directo, "
    : "sin `claude` en el PATH: registro ")
    + "escrito en " + join(cfg, "plugins") + " (formato interno de Claude Code)"

  return [
    ...copias,
    {
      type: "json-set",
      to: join(cfg, "plugins", "known_marketplaces.json"),
      set: { [MKT]: { source: origen, installLocation: mkt, lastUpdated: ahora, autoUpdate: true } },
      volatiles: ["lastUpdated"],
    },
    {
      type: "json-set",
      to: join(cfg, "plugins", "installed_plugins.json"),
      set: {
        version: 2,
        [`plugins.${PLUGIN_ID}`]: [
          { scope, installPath: cache, version, installedAt: ahora, lastUpdated: ahora },
        ],
      },
      volatiles: ["installedAt", "lastUpdated"],
      // `version` es del fichero, no nuestra: se pone si falta, pero desinstalar no la quita.
      noQuitar: ["version"],
    },
    { type: "json-set", to: ajustes, set: enSettings },
  ]
}

const claudeCode = {
  id: "claude-code",
  label: "Claude Code",
  blurb: "plugin nativo — agentes, comandos, skills, hooks y statusline",
  detect: () => existsSync(GLOBAL_DIR["claude-code"]),
  hint: ({ modo }) => (modo === "copy"
    ? "Bundle copiado: sin hooks, sin statusline y sin namespace `/custom-agents:`. "
      + "Quita `--mode copy` para instalarlo como plugin."
    : "Compruébalo con `claude plugin list`: tiene que aparecer `" + PLUGIN_ID + "`."),
  plan: planClaude,
  destino: (scope, dir, modo = "plugin") => (modo === "copy"
    ? (scope === "user" ? GLOBAL_DIR["claude-code"] : join(dir, ".claude"))
    : (scope === "user" ? join(claudeConfigDir(), "plugins") : join(dir, ".claude"))),
  // En scope `project` los dos modos escriben en `<dir>/.claude`: sin un nombre por modo, instalar
  // como plugin encima de un `--mode copy` anterior (la ruta de actualización de todo el mundo)
  // pisaba el inventario del copy y dejaba sus 222 ficheros huérfanos.
  manifiesto: (modo = "plugin") => (modo === "copy" ? MANIFEST : MANIFEST_PLUGIN),
  restart: ({ modo }) => (modo === "copy"
    ? "Reinicia Claude Code (lee `.claude/` al arrancar)."
    : "Reinicia Claude Code (o `/reload-plugins`) para cargar el plugin."),
}

// --------------------------------------------------------------------------- Codex

const codex = {
  id: "codex",
  label: "Codex",
  blurb: "plugin + agentes `.toml` + comandos como prompts",
  detect: () => existsSync(GLOBAL_DIR.codex),
  hint: "El plugin solo carga si está HABILITADO: el instalador pone `enabled = true` en tu `config.toml`.",
  // En Codex el plugin vive en su propia carpeta y el marketplace lo declara. Los agentes son
  // TOML en `agents/`, y los prompts SOLO existen en CODEX_HOME (no hay prompts por proyecto).
  plan({ root, dir, scope, version }) {
    const base = scope === "user" ? GLOBAL_DIR.codex : join(dir, ".codex")
    const plugin = join(base, "plugins", "custom-agents")
    const mktRoot = scope === "user" ? join(home(), ".agents") : join(dir, ".agents")
    const config = join(base, "config.toml")
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
      // Copiar el plugin no basta: Codex solo lo carga si el marketplace está dado de alta y el
      // plugin HABILITADO. Lo primero es cosa de su CLI (opcional: sin `codex` se dice el comando
      // pendiente); lo segundo es una línea en el `config.toml` del scope, que sí ponemos nosotros.
      {
        type: "exec",
        cmd: "codex",
        args: ["plugin", "marketplace", "add", mktRoot],
        opcional: true,
        siFalla: "aviso",
        minVersion: CODEX_MIN,
        // Si el marketplace `daycry` ya existe apuntando a OTRA fuente, es del usuario: el
        // instalador NO lo borra por su cuenta (borrarlo y re-crearlo con la nuestra es pisarle la
        // configuración sin preguntar). Por defecto se avisa con el comando exacto; solo con
        // `--force-marketplace` se ejecuta el `remove` + `add`, y entonces queda en el manifiesto.
        siYaExiste: {
          patron: "already added from a different source",
          args: ["plugin", "marketplace", "remove", MKT],
          soloConForce: true,
        },
      },
      { type: "toml-set", to: config, tabla: `plugins."${PLUGIN_ID}"`, clave: "enabled", valor: true },
      // `[features] hooks` es una preferencia global del usuario: se enciende (los hooks del plugin
      // no corren sin ella) pero desinstalar NO la apaga, porque puede haberla puesto él.
      { type: "toml-set", to: config, tabla: "features", clave: "hooks", valor: true, deshacer: false },
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
    name: MKT,
    interface: { displayName: "Agentes custom de daycry" },
    plugins: [{
      name: PLUGIN,
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
  detect: () => existsSync(GLOBAL_DIR.opencode) || existsSync(join(home(), ".opencode")),
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

/** Nombre del manifiesto de un proveedor en un modo. Solo Claude Code tiene más de uno. */
export const manifiestoDe = (provider, modo) =>
  (typeof provider?.manifiesto === "function" ? provider.manifiesto(modo) : MANIFEST)

/**
 * Todos los sitios donde puede haber un manifiesto de este proveedor: `{ dest, file, modo }`.
 * `status` y `uninstall` los recorren TODOS (un mismo scope puede tener el copy y el plugin).
 */
export function sitiosManifiesto(provider, scope, dir) {
  const vistos = new Set()
  const out = []
  for (const modo of ["plugin", "copy"]) {
    const dest = provider.destino(scope, dir, modo)
    const file = manifiestoDe(provider, modo)
    const clave = dest + "|" + file
    if (vistos.has(clave)) continue
    vistos.add(clave)
    out.push({ dest, file, modo })
  }
  return out
}

/** Construye el plan de un proveedor. `dest` se deriva de su `destino()`. */
export function buildPlan(provider, { root, dir, scope, version, modo, source, cli }) {
  const dest = provider.destino(scope, dir, modo)
  return provider.plan({ root, dir, dest, scope, version, modo, source, cli })
}

function relPosix(from, to) {
  // `path.relative` sin importar `path` dos veces y siempre con `/` (los JSON no llevan `\`).
  const a = from.split(/[\\/]/).filter(Boolean)
  const b = to.split(/[\\/]/).filter(Boolean)
  let i = 0
  while (i < a.length && i < b.length && a[i] === b[i]) i++
  return [...Array(a.length - i).fill(".."), ...b.slice(i)].join("/")
}
