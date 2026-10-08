#!/usr/bin/env node
// install.mjs — instalador multi-proveedor de custom-agents. Cero dependencias.
//
//   npx @daycry/custom-agents                      # interactivo: elige proveedores
//   npx @daycry/custom-agents install -p codex,opencode
//   npx @daycry/custom-agents install --all --scope user
//   npx @daycry/custom-agents install --dry-run    # imprime el plan, no escribe nada
//   npx @daycry/custom-agents status
//   npx @daycry/custom-agents uninstall -p codex
//
// Principios (los mismos que el plugin se aplica a sí mismo):
//   · IDEMPOTENTE — reinstalar sobre lo mismo no duplica ni rompe nada.
//   · NO PISA lo del usuario — los JSON de configuración se FUSIONAN; un valor que ya existe
//     se respeta y se dice. Los ficheros del PLUGIN sí se sobrescriben siempre: es lo que hace
//     que reinstalar sirva para actualizar. Los agentes nativos sólo se actualizan cuando sus
//     bytes coinciden con el inventario propio; agentes ajenos/modificados se conservan.
//     La excepción declarada es `json-set`, que pone las
//     claves del REGISTRO del runtime (las que lo hacen cargar el plugin) y apunta cuáles.
//   · DESINSTALABLE — cada instalación deja un manifiesto con la lista EXACTA de lo que escribió;
//     `uninstall` borra eso y nada más (nunca un `rm -rf` de una carpeta que no creó él).
//   · DEGRADA, NO BLOQUEA — un proveedor que falla no impide instalar los demás; el exit code
//     lo refleja al final.

import {
  readFileSync, writeFileSync, existsSync, mkdirSync, cpSync, statSync, rmSync, readdirSync, rmdirSync,
  renameSync, chmodSync, realpathSync, lstatSync, unlinkSync, mkdtempSync, symlinkSync,
} from "node:fs"
import { createHash } from "node:crypto"
import { dirname, join, resolve, relative, sep, isAbsolute } from "node:path"
import { fileURLToPath } from "node:url"
import { createInterface, emitKeypressEvents } from "node:readline"
import { execFileSync } from "node:child_process"
import { tmpdir } from "node:os"
import { queryCodexPlugin } from "../agent-kits/shared/codex-plugin-state.mjs"
import {
  PROVIDERS, IDS, getProvider, buildPlan, MANIFEST, MANIFEST_PLUGIN, MANIFIESTOS,
  enPath, rutaDe, estadoCli, manifiestoDe, sitiosManifiesto, PRECEDENCIA_SETTINGS, codexHome, MKT, PLUGIN, PLUGIN_ID,
} from "./providers.mjs"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const PKG = leerJson(join(ROOT, "package.json")) || {}
const VERSION = PKG.version || leerJson(join(ROOT, ".claude-plugin", "plugin.json"))?.version || "0.0.0"

// ---------------------------------------------------------------- presentación

const TTY = process.stdout.isTTY && !process.env.NO_COLOR
const c = (n) => (s) => (TTY ? `\u001b[${n}m${s}\u001b[0m` : String(s))
const bold = c(1), dim = c(2), red = c(31), green = c(32), yellow = c(33), cyan = c(36)
const OK = green("✓"), WARN = yellow("!"), ERR = red("✗"), ARROW = dim("→")

let QUIET = false
const say = (...a) => { if (!QUIET) console.log(...a) }

/** Un `hint`/`restart` puede depender del modo: se acepta texto o función de las opciones. */
const texto = (v, opts) => (typeof v === "function" ? v(opts) : v)

// Wordmark ASCII (solo caracteres de 7 bits: las consolas de Windows en cp1252 lo pintan igual).
const WORDMARK = [
  "   ___ _   _ ___ _____ ___  __  __",
  "  / __| | | / __|_   _/ _ \\|  \\/  |",
  " | (__| |_| \\__ \\ | || (_) | |\\/| |",
  "  \\___|\\___/|___/ |_| \\___/|_|  |_|",
]

/**
 * Título al arrancar. NO se imprime si estorba: `--quiet`, `NO_COLOR`, `CI` o salida que no es
 * una terminal (pipe, redirección, CI) — y nunca en `--help`, `--version`, `status` ni `list`,
 * que son comandos cuya salida se lee o se parsea.
 */
function banner() {
  if (QUIET || process.env.NO_COLOR || process.env.CI || !process.stdout.isTTY) return
  const sufijos = [
    "",
    `  ${bold("custom-agents")} ${dim("v" + VERSION)}`,
    `  ${dim("ciclo SDD presupuestado para agentes de código")}`,
    "",
  ]
  console.log("")
  WORDMARK.forEach((l, i) => console.log(cyan(l) + (sufijos[i] || "")))
}

function ayuda() {
  console.log(`
${bold("custom-agents")} ${dim("v" + VERSION)} — ciclo SDD presupuestado para agentes de código

${bold("USO")}
  npx @daycry/custom-agents [comando] [opciones]

${bold("COMANDOS")}
  install       Instala en uno o varios proveedores (por defecto)
  uninstall     Desinstala usando el manifiesto de la instalación
  status        Qué hay instalado, dónde y si el runtime lo tiene REGISTRADO (sí/no)
  list          Proveedores soportados

${bold("OPCIONES")}
  -p, --provider <ids>   ${IDS.join(", ")} (separados por coma) o "all"
      --all              Todos los proveedores soportados
      --scope <ámbito>   project (por defecto) | user
      --dir <ruta>       Proyecto destino (por defecto, el directorio actual)
      --mode <modo>      Claude Code: plugin (por defecto, registro real) | copy (bundle en .claude/)
      --source <fuente>  Marketplace del que instalar: owner/repo o una ruta local
                         (por defecto, daycry/custom-agents)
      --force-marketplace  Si el marketplace ya existe apuntando a otra fuente, quitarlo
                         y volver a darlo de alta con la de custom-agents (por defecto NO:
                         se avisa con el comando y no se toca nada tuyo)
      --dry-run          Imprime el plan y no escribe nada
  -y, --yes              No preguntes nada (para CI)
  -q, --quiet            Solo errores
  -h, --help             Esta ayuda
  -V, --version          Versión

${bold("EJEMPLOS")}
  npx @daycry/custom-agents                          ${dim("# elige en un menú")}
  npx @daycry/custom-agents install -p codex         ${dim("# solo Codex, en este proyecto")}
  npx @daycry/custom-agents install --all --scope user
  npx @daycry/custom-agents install -p opencode --dry-run
  npx @daycry/custom-agents install -p claude-code --mode copy   ${dim("# bundle, sin hooks")}
  npx @daycry/custom-agents install -p claude-code --source ./mi-clon

${dim("Claude Code se instala como PLUGIN: se usa `claude plugin …` si la CLI está en el PATH y, si no,")}
${dim("se escribe su registro (CLAUDE_CONFIG_DIR se respeta). `--mode copy` es el bundle de siempre:")}
${dim("deja las piezas en .claude/, pero sin hooks, sin statusline y sin namespace /custom-agents:.")}
${dim("En Codex se habilita el plugin en config.toml; en OpenCode se registra el adaptador de hooks.")}
${dim("¿Ha funcionado? `status` lo dice leyendo los ficheros que lee cada runtime, no el manifiesto.")}

Documentación: ${cyan("docs/INTEROP.md")} · ${cyan(PKG.homepage || "https://github.com/daycry/custom-agents")}
`)
}

// ---------------------------------------------------------------- argumentos

function parseArgs(argv) {
  const o = {
    cmd: null, providers: [], scope: "project", dir: process.cwd(),
    modo: "plugin", source: null, dryRun: false, yes: false, quiet: false,
    forceMarketplace: false,
  }
  const resto = []
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    const val = () => argv[++i]
    if (a === "-h" || a === "--help") return { ...o, cmd: "help" }
    else if (a === "-V" || a === "--version") return { ...o, cmd: "version" }
    else if (a === "-p" || a === "--provider" || a === "--ide") o.providers.push(...String(val() || "").split(","))
    else if (a === "--all") o.providers = ["all"]
    else if (a === "--scope") o.scope = val()
    else if (a === "--dir") o.dir = resolve(String(val() || "."))
    else if (a === "--mode" || a === "--modo") o.modo = val()
    else if (a === "--source" || a === "--fuente") o.source = val()
    else if (a === "--force-marketplace") o.forceMarketplace = true
    else if (a === "--dry-run") o.dryRun = true
    else if (a === "-y" || a === "--yes") o.yes = true
    else if (a === "-q" || a === "--quiet") o.quiet = true
    else if (a.startsWith("-")) return { ...o, cmd: "unknown", bad: a }
    else resto.push(a)
  }
  o.cmd = o.cmd || resto.shift() || "install"
  o.providers = o.providers.map((s) => s.trim()).filter(Boolean)
  if (o.providers.includes("all")) o.providers = [...IDS]
  return o
}

// ---------------------------------------------------------------- utilidades de disco

function leerJson(p) {
  try { return JSON.parse(readFileSync(p, "utf8").replace(/^﻿/, "")) } catch { return null }
}

/**
 * Lectura ESTRICTA para los ficheros del REGISTRO (los que `json-set` reescribe). A diferencia de
 * `leerJson`, aquí un JSON que no parsea NO puede degradar a `{}`: eso sustituía entero un
 * `settings.json` del usuario (con su `model`, su `permissions`, su `env` y sus otros plugins) sin
 * un aviso y con exit 0. Un fichero ilegible es un ERROR del paso y no se escribe nada.
 *
 * El BOM que dejan Notepad y algunos editores de Windows sí se tolera: se quita al leer y se
 * vuelve a poner al escribir, para no cambiarle al usuario la codificación de su fichero.
 */
export function leerJsonEstricto(p) {
  if (!existsSync(p)) return { existe: false, bom: false, valor: {} }
  let crudo
  try { crudo = readFileSync(p, "utf8") } catch (e) {
    throw new Error(`no puedo leer ${p}: ${e.message}`)
  }
  const bom = crudo.startsWith("﻿")
  const texto = bom ? crudo.slice(1) : crudo
  // Un fichero que EXISTE y está vacío (0 bytes o solo espacios) no es «un JSON vacío»: es lo que
  // deja una escritura interrumpida o un disco lleno. Tratarlo como `{}` hacía invisible la pérdida
  // y la pasada siguiente lo reescribía con solo NUESTRAS claves. Es un error del paso.
  if (!texto.trim()) {
    throw new Error(`${p} existe pero está vacío (${crudo.length} byte(s)) — eso no es un JSON: ` +
      `no toco el fichero. Suele ser una escritura interrumpida: restaura tu copia (o bórralo si ` +
      `de verdad no tenías nada dentro) y vuelve a ejecutar el instalador`)
  }
  let valor
  try { valor = JSON.parse(texto) } catch (e) {
    throw new Error(`${p} no es JSON válido (${primeraLinea(e.message)}) — no toco el fichero: ` +
      `arréglalo (o quita los comentarios y las comas de más) y vuelve a ejecutar el instalador`)
  }
  if (!valor || typeof valor !== "object" || Array.isArray(valor)) {
    throw new Error(`${p} no contiene un objeto JSON — no toco el fichero`)
  }
  return { existe: true, bom, valor }
}

/**
 * Escritura ATÓMICA: se escribe un temporal EN EL MISMO DIRECTORIO (para que el `rename` no cruce
 * volúmenes) y se renombra encima. Un `writeFileSync` directo trunca el fichero antes de escribirlo:
 * un Ctrl-C, un disco lleno o un antivirus a medias dejaban el `settings.json` del usuario en 0
 * bytes. Con `rename`, o está el contenido viejo o está el nuevo, nunca nada a medias.
 */
export function escribirAtomico(p, contenido) {
  mkdirSync(dirname(p), { recursive: true })
  const modo = (() => {
    try { return existsSync(p) ? statSync(p).mode & 0o7777 : null } catch { return null }
  })()
  const tmp = `${p}.tmp-${process.pid}-${Math.random().toString(36).slice(2, 8)}`
  let ultimo = null
  for (let intento = 0; intento < 3; intento++) {
    try {
      writeFileSync(tmp, contenido, "utf8")
      renameSync(tmp, p)
      // El `rename` sustituye el inodo: el fichero se queda con los permisos del temporal (0644).
      // Un `settings.json` que el usuario tenía en 0600 no puede acabar siendo legible por todos.
      if (modo !== null) { try { chmodSync(p, modo) } catch { /* FS sin permisos: nada que hacer */ } }
      return
    } catch (e) {
      ultimo = e
      try { rmSync(tmp, { force: true }) } catch { /* el temporal es nuestro: si no se va, da igual */ }
      if (!BLOQUEO.includes(e.code)) throw e
      if (intento < 2) dormir(60 * (intento + 1))
    }
  }
  // En Windows, `rename` sobre un destino que otro proceso tiene ABIERTO da EPERM donde un
  // `writeFileSync` directo sí funciona. Antes que fallar la instalación, se escribe encima y se
  // DICE que esa escritura no fue atómica (un corte a mitad puede dejar el fichero incompleto).
  writeFileSync(p, contenido, "utf8")
  if (modo !== null) { try { chmodSync(p, modo) } catch { /* idem */ } }
  AVISOS_ESCRITURA.push(`${p}: otro proceso lo tiene abierto (${ultimo.code}); lo he escrito ` +
    `DIRECTAMENTE, sin atomicidad — si algo lo corta a mitad puede quedar incompleto ` +
    `(cierra el programa que lo tenga abierto y vuelve a ejecutar el instalador para dejarlo limpio)`)
}

const BLOQUEO = ["EPERM", "EACCES", "EBUSY"]

/** Espera SÍNCRONA sin dependencias ni bucle de CPU (el instalador es todo síncrono). */
function dormir(ms) {
  try { Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms) } catch { /* da igual */ }
}

/** Avisos que produce la capa de escritura; los recoge quien esté ejecutando el plan. */
const AVISOS_ESCRITURA = []
export function drenarAvisosEscritura() { return AVISOS_ESCRITURA.splice(0, AVISOS_ESCRITURA.length) }

function escribirJson(p, obj, bom = false) {
  try {
    escribirAtomico(p, (bom ? "﻿" : "") + JSON.stringify(obj, null, 2) + "\n")
  } catch (e) {
    throw new Error(`no puedo escribir ${p}: ${e.message}`)
  }
}

/** Retira únicamente una copia conocida; las modificaciones locales se conservan. */
export function retirarArtefacto(paso, destino, dryRun = false) {
  const raiz = resolve(destino)
  const dentro = (p) => {
    const r = relative(raiz, resolve(p))
    if (!r || isAbsolute(r) || r === ".." || r.startsWith(`..${sep}`)) {
      throw new Error(`ruta fuera del destino: ${p}`)
    }
    // También se verifica el padre existente: una junction no amplía el destino autorizado.
    let padre = dirname(resolve(p))
    while (!existsSync(padre)) padre = dirname(padre)
    if (existsSync(raiz)) {
      const real = relative(realpathSync(raiz), realpathSync(padre))
      if (isAbsolute(real) || real === ".." || real.startsWith(`..${sep}`)) {
        throw new Error(`ruta fuera del destino real: ${p}`)
      }
    }
  }
  dentro(paso.to)
  let original = null
  try { original = lstatSync(paso.to) } catch (e) { if (e.code !== "ENOENT") throw e }
  if (original) {
    if (!original.isFile() || original.isSymbolicLink() || original.nlink > 1) {
      throw new Error(`artefacto no regular en el destino: ${paso.to}`)
    }
    const texto = readFileSync(paso.to, "utf8").replace(/\r\n/g, "\n")
    const hash = createHash("sha256").update(texto).digest("hex")
    if (!(paso.sha256 || []).includes(hash)) return false
  }
  let config = null
  if (paso.config) {
    // La configuración de proyecto está en la raíz, fuera de .opencode. Su único
    // destino permitido es opencode.json junto al directorio de instalación.
    const esperado = join(dirname(raiz), "opencode.json")
    const global = join(raiz, "opencode.json")
    if (![esperado, global].includes(resolve(paso.config.to))) throw new Error("config fuera del destino")
    if (existsSync(paso.config.to)) {
      const st = lstatSync(paso.config.to)
      if (!st.isFile() || st.isSymbolicLink() || st.nlink > 1) throw new Error("config no regular")
      config = leerJsonEstricto(paso.config.to)
      for (const [k, valores] of Object.entries(paso.config.remove || {})) {
        if (Array.isArray(config.valor[k])) config.valor[k] = config.valor[k].filter(v => !valores.includes(v))
      }
    }
  }
  if (dryRun) return true
  // Validar y escribir la configuración precede a borrar: un JSON inválido conserva la copia.
  if (config) escribirJson(paso.config.to, config.valor, config.bom)
  if (original) {
    const ahora = lstatSync(paso.to)
    if (ahora.dev !== original.dev || ahora.ino !== original.ino || ahora.size !== original.size || ahora.mtimeMs !== original.mtimeMs) {
      throw new Error("el artefacto cambió durante la retirada")
    }
    unlinkSync(paso.to)
  }
  return true
}

/** Native role copies are managed by recorded bytes, never by their agent name. */
export function planificarAgentesNativos(paso, previo = {}, root = ROOT) {
  previo = previo || {}
  const {runtime, scope, configs = []} = paso.nativeAgents
  const map = leerJson(join(root,'agent-kits/shared/native-roles.json'))?.runtimes?.[runtime]
  if (!map || typeof map !== 'object' || Array.isArray(map)) throw new Error('native role map unavailable')
  const legacy = leerJson(join(root,'install/native-agent-legacy.json'))?.runtimes?.[runtime] || {}
  const raiz = resolve(paso.to), ext = runtime === 'codex' ? '.toml' : '.md'
  const norm = p => resolve(p).split(sep).join('/')
  const hash = p => createHash('sha256').update(readFileSync(p,'utf8').replace(/\r\n/g,'\n')).digest('hex')
  const files = new Set((previo.plugin === PLUGIN && previo.provider === runtime ? previo.files || [] : []).map(norm))
  const recorded = previo.plugin === PLUGIN && previo.provider === runtime ? previo.nativeAgents || {} : {}
  const actions = [], released = [], warnings = [], bindings = new Set()
  let agentFilesInspected = false
  const layers = [...configs]
  const agentDirs = [raiz,...(paso.nativeAgents.agentDirs || [])]
  let repositoryBoundary = null
  // Only repository layers are read here. Parent profiles outside an identified
  // repository are not permission to inspect unrelated consumer configuration.
  if (scope === 'project' && paso.nativeAgents.projectDir) {
    let dir = resolve(paso.nativeAgents.projectDir)
    const candidates = []
    while (true) {
      candidates.push(dir)
      if (existsSync(join(dir,'.git'))) {
        const marker = lstatSync(join(dir,'.git'))
        if (marker.isDirectory() && !marker.isSymbolicLink()) repositoryBoundary = dir
        break
      }
      const parent = dirname(dir)
      if (parent === dir) break
      dir = parent
    }
    if (repositoryBoundary) for (const folder of candidates) {
      agentDirs.push(join(folder,`.${runtime}`,'agents'))
      if (runtime === 'codex') layers.push(join(folder,'.codex','config.toml'))
      else layers.push(join(folder,'opencode.json'),join(folder,'opencode.jsonc'))
    }
  }
  let uncertain = false
  let legacyReferencesUncertain = false
  const nativeName = path => {
    const st=lstatSync(path)
    if (!st.isFile() || st.isSymbolicLink() || st.nlink > 1 || st.size > 1024*1024) throw new Error('agent metadata unavailable')
    const names=rutasToml(readFileSync(path,'utf8')).filter(row=>row.ruta==='name')
    if (names.length > 1) throw new Error('duplicate native agent name')
    if (!names.length) return undefined
    const name=cadenaToml(names[0].valor)
    if (name === null || !name) throw new Error('native agent name is not verifiable')
    return name
  }
  for (const cfg of [...new Set(layers.map(p => resolve(p)))]) {
    if (!existsSync(cfg)) continue
    try {
      const info=lstatSync(cfg)
      if (!info.isFile() || info.isSymbolicLink() || info.size>1024*1024) throw new Error('configuration metadata size/type bound')
      const text = readFileSync(cfg,'utf8')
      if (runtime === 'codex') {
        for (const item of rutasToml(text)) {
          const match = item.ruta.match(/^agents\.([A-Za-z0-9_-]+)(?:\.|$)/)
          if (match) bindings.add(match[1])
          // A config_file can bind an arbitrary key to one of the old files.
          if (item.ruta.startsWith('agents.') && item.ruta.endsWith('.config_file')) {
            const target = cadenaToml(item.valor)
            if (typeof target !== 'string') uncertain = true
            else {
              const path=resolve(dirname(cfg),target)
              bindings.add(norm(path))
              const name=nativeName(path)
              if (name) bindings.add(name)
            }
          }
        }
      } else {
        const parsed = JSON.parse(text.replace(/^\uFEFF/,''))
        if (typeof parsed.default_agent === 'string') bindings.add(parsed.default_agent)
        let unresolvedReference = false
        const references = value => {
          if (typeof value === 'string') {
            // Native config substitution covers values and keys before parsing.
            // Resolve only explicit paths; do not inspect consumer environment.
            if (/\{env:[^}]+\}/.test(value)) uncertain = unresolvedReference = true
            for (const match of value.matchAll(/\{file:([^}]+)\}/g)) {
              if (match[1].startsWith('~/') || match[1].includes('{env:')) uncertain = unresolvedReference = true
              else bindings.add(norm(resolve(dirname(cfg),match[1])))
            }
          } else if (Array.isArray(value)) value.forEach(references)
          else if (value && typeof value === 'object') for (const [key,item] of Object.entries(value)) {
            references(key);references(item)
          }
        }
        for (const key of ['agent','agents','mode']) {
          const agents = parsed[key]
          if (agents != null && (typeof agents !== 'object' || Array.isArray(agents))) uncertain = true
          else {
            for (const name of Object.keys(agents || {})) bindings.add(name)
          }
        }
        for (const key of ['command','commands']) {
          const commands=parsed[key]
          if (commands != null && (typeof commands !== 'object' || Array.isArray(commands))) uncertain = true
          else for (const command of Object.values(commands || {})) {
            if (typeof command?.agent === 'string') bindings.add(command.agent)
            else if (command?.agent != null) uncertain = true
          }
        }
        references(parsed)
        if (unresolvedReference) warnings.push(`${rel(cfg)}: referencia dinámica de configuración no verificable; agentes conservados`)
      }
    } catch { uncertain = true; warnings.push(`${rel(cfg)}: configuración no verificable; agentes conservados`) }
  }
  // OpenCode loads recursive command Markdown using its full YAML parser.
  // Without that parser, metadata presence is evidence against safe retirement,
  // not permission to infer a command's agent or inspect its body.
  const legacyWarnings = []
  let legacyCopyPresent = false
  if (runtime === 'opencode') {
    const dirs = [...new Set(agentDirs.flatMap(dir=>['command','commands'].map(name=>join(dirname(resolve(dir)),name))))]
    for (const dir of dirs) {
      if (!existsSync(dir)) continue
      try {
        if (lstatSync(dirname(dir)).isSymbolicLink()) throw new Error('runtime directory link')
        const pending=[{path:dir,depth:0}]
        let scanned=0, found=false
        while (pending.length && !found) {
          const folder=pending.pop(), info=lstatSync(folder.path)
          if (!info.isDirectory() || info.isSymbolicLink() || folder.depth>16) throw new Error('command discovery boundary')
          for (const entry of readdirSync(folder.path,{withFileTypes:true})) {
            if (++scanned>4096) throw new Error('command discovery count bound')
            const path=join(folder.path,entry.name), st=lstatSync(path)
            if (st.isSymbolicLink()) throw new Error('command discovery link')
            if (st.isDirectory()) pending.push({path,depth:folder.depth+1})
            else if (entry.name.toLowerCase().endsWith('.md')) {found=true;break}
          }
        }
        if (found) {
          legacyReferencesUncertain=true
          legacyWarnings.push(`${rel(dir)}: referencias de comandos Markdown no verificables; copia anterior conservada`)
        }
      } catch {
        legacyReferencesUncertain=true
        legacyWarnings.push(`${rel(dir)}: descubrimiento de comandos Markdown no verificable; copia anterior conservada`)
      }
    }
  }
  const seguro = file => {
    const abs = resolve(file), relativePath = relative(raiz,abs)
    if (!relativePath || isAbsolute(relativePath) || relativePath === '..' || relativePath.startsWith(`..${sep}`)) throw new Error('native agent path outside destination')
    let parent = dirname(abs)
    while (!existsSync(parent)) parent = dirname(parent)
    const base = resolve(paso.nativeAgents.base || dirname(raiz))
    if (existsSync(base)) {
      const real = relative(realpathSync(base),realpathSync(parent))
      if (isAbsolute(real) || real === '..' || real.startsWith(`..${sep}`)) throw new Error('native agent parent outside runtime base')
    }
    if (existsSync(raiz)) {
      const real = relative(realpathSync(raiz),realpathSync(parent))
      if (isAbsolute(real) || real === '..' || real.startsWith(`..${sep}`)) throw new Error('native agent parent outside real destination')
    }
    let st
    try { st = lstatSync(abs) } catch (e) { if (e.code !== 'ENOENT') throw e }
    if (st && (!st.isFile() || st.isSymbolicLink() || st.nlink > 1)) throw new Error('native agent is not a private regular file')
    if (st && st.size>1024*1024) throw new Error('native agent size bound')
    return st ? hash(abs) : null
  }
  for (const [role,id] of Object.entries(map)) {
    if (!/^[a-z][a-z0-9-]*$/.test(role) || !/^[a-z][a-z0-9-]*$/.test(id) || id === role) throw new Error('invalid native role map')
    const target = join(raiz,id+ext), bare = join(raiz,role+ext), source = join(root,paso.from,id+ext)
    released.push(norm(target),norm(bare))
    let current, old
    try { current = seguro(target); old = seguro(bare) }
    catch (e) { warnings.push(`${rel(target)}: conflicto (${e.message}); conservado`); continue }
    legacyCopyPresent ||= old !== null
    // Codex reads the declared TOML name, which may differ from its filename.
    if (!agentFilesInspected) {
      agentFilesInspected = true
      for (const dir of [...new Set(agentDirs.map(p=>resolve(p)))]) {
        if (!existsSync(dir)) continue
        const folder=lstatSync(dir)
        if (!folder.isDirectory() || folder.isSymbolicLink()) {
          uncertain=true;warnings.push(`${rel(dir)}: directorio de agentes no verificable; agentes conservados`);continue
        }
        const paths = [], pending = [{path:dir,depth:0}]
        let scanned=0
        try {
          while (pending.length) {
            const folder=pending.pop()
            if (folder.depth>16) throw new Error('agent discovery depth bound')
            for (const entry of readdirSync(folder.path,{withFileTypes:true})) {
              if (++scanned>4096) throw new Error('agent discovery count bound')
              const path=join(folder.path,entry.name)
              if (entry.isSymbolicLink()) throw new Error('agent discovery link')
              if (runtime==='codex' && entry.isDirectory()) pending.push({path,depth:folder.depth+1})
              else if (entry.name.endsWith(ext)) paths.push(path)
            }
          }
        } catch { uncertain=true;warnings.push(`${rel(dir)}: descubrimiento de agentes no verificable; agentes conservados`) }
        for (const path of paths) {
        try {
          if (runtime === 'opencode') {
            const st=lstatSync(path)
            if (!st.isFile() || st.isSymbolicLink() || st.nlink > 1) throw new Error('agent metadata is not a private regular file')
            const name=path.slice(dir.length+1,-ext.length)
            if (Object.values(map).includes(name) && norm(dir) !== norm(raiz)) bindings.add(name)
            continue
          }
          const name=nativeName(path)
          if (name && Object.values(map).includes(name) && norm(path) !== norm(join(raiz,name+ext))) bindings.add(name)
        } catch { uncertain=true;warnings.push(`${rel(path)}: identidad nativa no verificable; agentes conservados`) }
        }
      }
    }
    if (uncertain || bindings.has(id) || bindings.has(norm(target))) {
      warnings.push(`${rel(target)}: binding existente o no verificable; conservado`); continue
    }
    if (current !== null && (!files.has(norm(target)) || recorded[norm(target)] !== current)) {
      warnings.push(`${rel(target)}: agente ajeno o modificado; conservado`); continue
    }
    if (!existsSync(source)) throw new Error(`native role export missing: ${id}`)
    actions.push({type:'copy',to:target,from:source,before:current,sha256:hash(source)})
    if (old !== null) {
      if (scope === 'project' && repositoryBoundary && !legacyReferencesUncertain && !bindings.has(role) && !bindings.has(norm(bare))
          && files.has(norm(bare)) && old === legacy[role]) {
        actions.push({type:'retire',to:bare,before:old})
      } else warnings.push(`${rel(bare)}: copia anterior conservada; propiedad, bindings o referencias externas no acreditados`)
    }
  }
  if (legacyCopyPresent) warnings.push(...legacyWarnings)
  return {actions,released,warnings}
}

/** Fusión conservadora: lo que ya existe MANDA. Devuelve [resultado, claves añadidas]. */
export function fusionar(actual, nuevo, upsert = {}) {
  const anadidas = []
  const walk = (dst, src, ruta) => {
    for (const [k, v] of Object.entries(src)) {
      const q = ruta ? `${ruta}.${k}` : k
      if (Array.isArray(v)) {
        // Fusionar una lista sobre un valor del usuario que NO es lista: lo suyo manda igual. Un
        // escalar se conserva como PRIMER elemento (sigue siendo lo que él puso, y delante); un
        // objeto no se puede convertir en lista sin cambiar lo que significa, así que la clave no
        // se toca. En los dos casos se AVISA: hacerlo en silencio es lo que borraba un
        // `"plugin": "mi-plugin.js"` al registrar el adaptador de OpenCode.
        let prev = []
        if (Array.isArray(dst[k])) prev = dst[k]
        else if (k in dst && dst[k] !== null && dst[k] !== undefined) {
          if (typeof dst[k] === "object") {
            AVISOS_ESCRITURA.push(`${q}: tu valor no es una lista y no puedo añadirle `
              + `${JSON.stringify(v)} sin cambiar lo que significa — lo dejo como está`)
            continue
          }
          prev = [dst[k]]
          AVISOS_ESCRITURA.push(`${q}: tu valor ${JSON.stringify(dst[k])} no era una lista; `
            + `lo conservo como primer elemento`)
        }
        const clave = upsert[q]
        if (clave) {
          // Upsert por identidad (p. ej. `{ plugins: "name" }`): la entrada con la MISMA clave la
          // gobierna el INSTALADOR y se reemplaza EN SU SITIO (una subida de versión no queda
          // congelada); las entradas ajenas al array se conservan. Sin esta rama, la de abajo
          // AÑADÍA una segunda entrada en CADA reinstalación: `prev.includes(x)` compara por
          // REFERENCIA y un objeto «nuevo» nunca está en la lista leída del disco (gap M-01).
          // También se colapsan duplicados que una versión anterior ya hubiera acumulado.
          const porClave = new Map(v.filter((x) => x && x[clave] !== undefined)
            .map((x) => [x[clave], x]))
          const vistos = new Set()
          const resultantes = []
          let cambios = 0
          for (const x of prev) {
            const kx = x && x[clave] !== undefined ? x[clave] : undefined
            if (kx !== undefined) {
              if (vistos.has(kx)) { cambios++; continue }   // duplicado histórico: fuera
              vistos.add(kx)
            }
            const nx = kx !== undefined ? porClave.get(kx) : undefined
            if (nx === undefined) { resultantes.push(x); continue }
            porClave.delete(kx)
            if (JSON.stringify(nx) !== JSON.stringify(x)) cambios++
            resultantes.push(nx)
          }
          const sobrantes = [...porClave.values()]
          if (cambios || sobrantes.length) { dst[k] = [...resultantes, ...sobrantes]; anadidas.push(q) }
          else if (!Array.isArray(dst[k])) dst[k] = prev
          continue
        }
        const falta = v.filter((x) => !prev.includes(x))
        if (falta.length) { dst[k] = [...prev, ...falta]; anadidas.push(q) }
        else if (!Array.isArray(dst[k])) dst[k] = prev
      } else if (v && typeof v === "object") {
        if (!dst[k] || typeof dst[k] !== "object" || Array.isArray(dst[k])) { dst[k] = {}; }
        walk(dst[k], v, q)
      } else if (!(k in dst)) {
        dst[k] = v
        anadidas.push(q)
      }
    }
  }
  const out = structuredClone(actual || {})
  walk(out, nuevo, "")
  return [out, anadidas]
}

// --- rutas "a.b.c" dentro de un JSON (las claves del registro llevan `@`, nunca `.`) ---

export function leerRuta(obj, ruta) {
  return ruta.split(".").reduce((o, k) => (o && typeof o === "object" ? o[k] : undefined), obj)
}

export function ponerRuta(obj, ruta, valor) {
  const ks = ruta.split(".")
  let cur = obj
  for (const k of ks.slice(0, -1)) {
    if (!cur[k] || typeof cur[k] !== "object" || Array.isArray(cur[k])) cur[k] = {}
    cur = cur[k]
  }
  cur[ks[ks.length - 1]] = valor
  return obj
}

/**
 * Como `ponerRuta`, pero si por el camino hay un valor que NO es un objeto (un
 * `"enabledPlugins": true` a mano, por ejemplo), falla en vez de sustituirlo por `{}`: es
 * configuración del usuario y pisarla en silencio es exactamente lo que no puede hacer esto.
 */
export function ponerRutaEstricta(obj, ruta, valor, fichero = "") {
  const ks = ruta.split(".")
  let cur = obj
  for (let i = 0; i < ks.length - 1; i++) {
    const k = ks[i]
    if (k in cur && (cur[k] === null || typeof cur[k] !== "object" || Array.isArray(cur[k]))) {
      throw new Error(`${fichero ? fichero + ": " : ""}\`${ks.slice(0, i + 1).join(".")}\` existe y no es un ` +
        `objeto (${Array.isArray(cur[k]) ? "array" : typeof cur[k]}) — no lo piso: revísalo tú`)
    }
    if (!(k in cur)) cur[k] = {}
    cur = cur[k]
  }
  cur[ks[ks.length - 1]] = valor
  return obj
}

export function quitarRuta(obj, ruta) {
  const ks = ruta.split(".")
  const padre = ks.slice(0, -1).reduce((o, k) => (o && typeof o === "object" ? o[k] : undefined), obj)
  if (padre && typeof padre === "object") delete padre[ks[ks.length - 1]]
  return obj
}

/**
 * Igualdad estructural ignorando campos volátiles (marcas de tiempo). Es lo que hace que
 * reinstalar sea idempotente: si lo único que cambiaría es un `lastUpdated`, no se escribe.
 */
export function igualSalvo(a, b, volatiles = []) {
  const limpia = (x) => {
    if (Array.isArray(x)) return x.map(limpia)
    if (x && typeof x === "object") {
      return Object.fromEntries(Object.entries(x)
        .filter(([k]) => !volatiles.includes(k))
        .map(([k, v]) => [k, limpia(v)]))
    }
    return x
  }
  return JSON.stringify(limpia(a)) === JSON.stringify(limpia(b))
}

/**
 * Nombre de tabla TOML en forma canónica para poder COMPARARLO: sin espacios sobrantes y con las
 * segmentos equivalentes con la misma escritura canónica. `[ plugins . 'custom-agents@daycry' ]` y
 * `[plugins."custom-agents@daycry"]` son la MISMA tabla para Codex; compararlas con `===` creaba
 * una segunda tabla duplicada y dejaba el `config.toml` ilegible.
 */
export function normalizarTabla(nombre) {
  if(!nombre.trim()) return "" // Empty table prefix means the TOML document root.
  const partes=[]
  let i=0
  while(i<nombre.length) {
    while(/\s/.test(nombre[i] || "") && i<nombre.length) i++
    let key
    if(nombre[i]==='"' || nombre[i]==="'") {
      const end=finCadenaToml(nombre,i)
      if(end<0) throw new Error("unsupported or malformed TOML key")
      key=cadenaToml(nombre.slice(i,end+1))
      if(key===null) throw new Error("unsupported or malformed TOML key")
      i=end+1
    } else {
      const m=nombre.slice(i).match(/^[A-Za-z0-9_-]+/)
      if(!m) throw new Error("unsupported or malformed TOML key")
      key=m[0];i+=key.length
    }
    partes.push(/^[A-Za-z0-9_-]+$/.test(key) ? key : JSON.stringify(key))
    while(/\s/.test(nombre[i] || "") && i<nombre.length) i++
    if(i===nombre.length) break
    if(nombre[i]!=="." || ++i===nombre.length) throw new Error("unsupported or malformed TOML key")
  }
  if(!partes.length) throw new Error("unsupported or malformed TOML key")
  return partes.join(".")
}

/** End of a single-line TOML string, respecting escaped quotes in basic strings. */
function finCadenaToml(text,start) {
  const quote=text[start]
  for(let i=start+1;i<text.length;i++) {
    if(quote==='"' && text[i]==="\\") {i++;continue}
    if(text[i]===quote) return i
    if(text[i]==="\n" || text[i]==="\r") return -1
  }
  return -1
}

/**
 * Recorre una línea actualizando el estado léxico: si quedamos dentro de una cadena `"""`/`'''`
 * y cuántos corchetes de array siguen abiertos. Sin esto, el barrido de «fin de tabla» (`^\s*\[`)
 * casaba una línea de un array multilínea y la clave acababa DENTRO del literal.
 */
function avanzarLexico(linea, st) {
  let i = 0
  while (i < linea.length) {
    if (st.multi) {
      const j = linea.indexOf(st.multi, i)
      if (j === -1) return st
      st.multi = null
      i = j + 3
      continue
    }
    const c = linea[i]
    if (c === "#") return st                                   // comentario: hasta fin de línea
    if (linea.startsWith('"""', i) || linea.startsWith("'''", i)) {
      st.multi = linea.slice(i, i + 3)
      i += 3
      continue
    }
    if (c === '"' || c === "'") {
      const j = finCadenaToml(linea,i)
      i = j === -1 ? linea.length : j + 1
      continue
    }
    if (c === "[") st.corchetes++
    else if (c === "]") st.corchetes = Math.max(0, st.corchetes - 1)
    i++
  }
  return st
}

/**
 * Índice del fichero: qué líneas son cabecera de tabla (fuera de literales) y con qué nombre, y
 * qué líneas son una ASIGNACIÓN, con la ruta completa que declaran (tabla en curso + clave). Sin
 * las asignaciones no se veían las otras dos formas VÁLIDAS de declarar la misma tabla —
 * `plugins."x".enabled = false` (clave con punto) y `[plugins]` + `"x" = { enabled = false }`
 * (tabla en línea) — y añadir la cabecera `[plugins."x"]` al final dejaba el `config.toml` con la
 * ruta declarada dos veces: ilegible para Codex («Cannot declare … twice»), con exit 0.
 */
function analizarToml(lineas) {
  const st = { multi: null, corchetes: 0 }
  const cabeceras = []      // { i, nombre, doble }
  const libre = []          // ¿la línea i empieza fuera de cualquier literal abierto?
  const asignaciones = []   // { i, tabla, ruta, sangria, bruta, resto }
  let tablaActual = ""
  for (let i = 0; i < lineas.length; i++) {
    const fuera = !st.multi && st.corchetes === 0
    libre.push(fuera)
    const encabezado=fuera ? partirValor(lineas[i].trim())[0].trim() : ""
    const m = fuera && encabezado.match(/^(\[\[?)\s*(.*?)\s*(\]\]?)$/)
    if (m && m[1].length === m[3].length) {
      if(!m[2].trim()) throw new Error("unsupported or malformed TOML table")
      const nombre = normalizarTabla(m[2])
      cabeceras.push({ i, nombre, doble: m[1] === "[[" })
      tablaActual = nombre
      continue                                                 // la cabecera no cuenta corchetes
    }
    if(fuera && encabezado.startsWith("[")) throw new Error("unsupported or malformed TOML table")
    if (fuera) {
      const term = lineas[i].endsWith("\r\n") ? "\r\n" : lineas[i].endsWith("\n") ? "\n" : ""
      const cuerpo = term ? lineas[i].slice(0, -term.length) : lineas[i]
      const a = partirAsignacion(cuerpo)
      if (a) {
        const clave = normalizarTabla(a.bruta)
        asignaciones.push({ i, tabla: tablaActual, ruta: tablaActual ? `${tablaActual}.${clave}` : clave, ...a })
      }
    }
    avanzarLexico(lineas[i], st)
  }
  return { cabeceras, libre, asignaciones }
}

/** Reemplaza el valor de una asignación ya existente conservando sangría y `# comentario`. */
function reemplazarValor(lineas, i, claveTexto, v) {
  const term = lineas[i].endsWith("\r\n") ? "\r\n" : lineas[i].endsWith("\n") ? "\n" : ""
  const cuerpo = term ? lineas[i].slice(0, -term.length) : lineas[i]
  const a = partirAsignacion(cuerpo)
  const [previo, comentario] = partirValor(a.resto)
  const sep = comentario ? ((previo.match(/\s*$/) || [""])[0] || " ") : ""
  lineas[i] = `${a.sangria}${claveTexto} = ${v}${sep}${comentario}${term}`
  return lineas.join("")
}

/** Corta el interior de una tabla en línea por las comas de NIVEL 0. `null` si no cuadra. */
function partirComas(dentro) {
  const trozos = []
  let cur = "", prof = 0, i = 0
  while (i < dentro.length) {
    const ch = dentro[i]
    if (ch === '"' || ch === "'") {
      const fin = finCadenaToml(dentro,i)
      if (fin === -1) return null
      cur += dentro.slice(i, fin + 1)
      i = fin + 1
      continue
    }
    if (ch === "#") return null                                 // comentario dentro: no lo toco
    if (ch === "{" || ch === "[") prof++
    else if (ch === "}" || ch === "]") { prof--; if (prof < 0) return null }
    else if (ch === "," && prof === 0) { trozos.push(cur); cur = ""; i++; continue }
    cur += ch
    i++
  }
  if (prof !== 0) return null
  trozos.push(cur)
  return trozos.length === 1 && !trozos[0].trim() ? [] : trozos
}

/**
 * Pone `clave = valor` DENTRO de una tabla en línea (`{ … }`) que ya estaba escrita a la derecha
 * de un `=`. Devuelve el nuevo lado derecho, o `null` si no se puede hacer con seguridad (tabla
 * sin cerrar en la línea, comentario dentro de las llaves…): entonces el paso falla y no se toca
 * nada, que es mejor que dejar el fichero sin parsear.
 */
export function ponerEnTablaEnLinea(resto, clave, v) {
  const [valor, comentario] = partirValor(resto)
  const izq = (valor.match(/^\s*/) || [""])[0]
  const der = (valor.match(/\s*$/) || [""])[0]
  const nucleo = valor.trim()
  if (!nucleo.startsWith("{") || !nucleo.endsWith("}") || nucleo.length < 2) return null
  const trozos = partirComas(nucleo.slice(1, -1))
  if (trozos === null) return null
  const claveNorm = normalizarTabla(clave)
  for (let k = 0; k < trozos.length; k++) {
    const a = partirAsignacion(trozos[k])
    if (!a || normalizarTabla(a.bruta) !== claveNorm) continue
    const cola = (a.resto.match(/\s*$/) || [""])[0]
    trozos[k] = `${a.sangria}${a.bruta} = ${v}${cola}`
    return `${izq}{${trozos.join(",")}}${der}${comentario}`
  }
  if (!trozos.length) return `${izq}{ ${clave} = ${v} }${der}${comentario}`
  trozos[trozos.length - 1] = trozos[trozos.length - 1].replace(/\s*$/, "")
  return `${izq}{${trozos.join(",")}, ${clave} = ${v} }${der}${comentario}`
}

/**
 * Parte una línea `clave = valor` devolviendo `{ sangria, bruta, resto }`, o `null` si no lo es.
 * Se hace a mano (no con una expresión regular) porque una clave TOML puede llevar tramos
 * entrecomillados con CUALQUIER carácter dentro: `plugins."custom-agents@daycry".enabled` es una
 * clave válida y el `@` no cabe en ninguna clase de caracteres razonable.
 */
export function partirAsignacion(cuerpo) {
  const sangria = (cuerpo.match(/^\s*/) || [""])[0]
  let i = sangria.length, bruta = ""
  while (i < cuerpo.length) {
    const ch = cuerpo[i]
    if (ch === '"' || ch === "'") {
      const fin = finCadenaToml(cuerpo,i)
      if (fin === -1) return null
      bruta += cuerpo.slice(i, fin + 1)
      i = fin + 1
      continue
    }
    if (ch === "=") {
      const bruto = bruta.trim()
      return bruto ? { sangria, bruta: bruto, resto: cuerpo.slice(i + 1) } : null
    }
    if (ch === "#" || ch === "[" || ch === "{" || ch === "}") return null
    bruta += ch
    i++
  }
  return null
}

/** Quita el último segmento de una clave con puntos, respetando los tramos entrecomillados. */
function prefijoClave(bruta) {
  const partes = []
  let cur = "", i = 0
  while (i < bruta.length) {
    const ch = bruta[i]
    if (ch === '"' || ch === "'") {
      const fin = finCadenaToml(bruta,i)
      if (fin === -1) { cur += bruta.slice(i); break }
      cur += bruta.slice(i, fin + 1)
      i = fin + 1
      continue
    }
    if (ch === ".") { partes.push(cur); cur = ""; i++; continue }
    cur += ch
    i++
  }
  partes.push(cur)
  return partes.slice(0, -1).join(".").trim()
}

/** Separa `valor` y `# comentario` de la parte derecha de un `clave = …` (sin tocar las cadenas). */
function partirValor(resto) {
  let q = null
  for (let i = 0; i < resto.length; i++) {
    const c = resto[i]
    if (q) { if(q==='"' && c==="\\") i++; else if (c === q) q = null }
    else if (c === '"' || c === "'") q = c
    else if (c === "#") return [resto.slice(0, i), resto.slice(i)]
  }
  return [resto, ""]
}

/** ¿Existe esa tabla en el fichero? (`uninstall` no puede RE-CREAR lo que el usuario borró). */
export function existeTabla(texto, tabla) {
  const lineas = texto ? texto.split(/(?<=\n)/) : []
  const objetivo = normalizarTabla(tabla)
  return analizarToml(lineas).cabeceras.some((c) => c.nombre === objetivo && !c.doble)
}

/**
 * Editor TOML mínimo: pone `clave = valor` dentro de `[tabla]`. Si la clave existe, cambia ESA
 * línea (conservando su `# comentario`); si no, la añade al final de la tabla; si la tabla no
 * existe, la crea al final del fichero. Ninguna otra línea se reescribe (comentarios, orden,
 * saltos de línea y formato del usuario intactos). La tabla se compara NORMALIZADA, así que
 * `[plugins.'x']` y `[ plugins."x" ]` son la misma; un `[[tabla]]` con ese nombre es un array de
 * tablas y es un ERROR, no algo que tocar a ciegas.
 *
 * Y la tabla puede no estar declarada como cabecera: TOML admite la MISMA ruta como clave con
 * punto (`plugins."x".enabled = false`) o como tabla en línea (`[plugins]` + `"x" = { … }`). Las
 * dos son justo lo que deja quien desactivó el plugin a mano, y las dos se atienden AHÍ, sin
 * añadir una segunda declaración (que dejaría el fichero sin parsear).
 *
 * `opciones.soloSiExiste`: si la tabla no está, devuelve el texto tal cual (no la crea).
 * `opciones.fichero`: ruta que se nombra en los errores.
 */
function ponerTomlCrudo(texto, tabla, clave, valor, opciones = {}) {
  const v = typeof valor === "string" ? JSON.stringify(valor) : String(valor)
  const eol = texto.includes("\r\n") ? "\r\n" : "\n"
  const lineas = texto ? texto.split(/(?<=\n)/) : []   // cada línea conserva su terminador
  const objetivo = normalizarTabla(tabla)
  const claveNorm = normalizarTabla(clave)
  const rutaObjetivo = objetivo ? `${objetivo}.${claveNorm}` : claveNorm
  const { cabeceras, libre, asignaciones } = analizarToml(lineas)
  const quien = opciones.fichero ? `${opciones.fichero}: ` : ""
  const aMano = `ponlo tú (dentro de [${tabla}], \`${clave} = ${v}\`) y vuelve a ejecutar el instalador`

  if (cabeceras.some((c) => c.nombre === objetivo && c.doble)) {
    throw new Error(`${quien}[[${tabla}]] es un array de tablas: no sé dónde poner ` +
      `\`${clave}\` sin romperlo — ${aMano}`)
  }

  const cab = cabeceras.find((c) => c.nombre === objetivo)
  if (!cab) {
    // --- la ruta puede estar declarada SIN cabecera: se modifica ahí, nunca se duplica ---
    const exacta = asignaciones.find((a) => a.ruta === rutaObjetivo)
    if (exacta) {                                   // `plugins."x".enabled = false`
      if (avanzarLexico(exacta.resto, { multi: null, corchetes: 0 }).multi) {
        throw new Error(`${quien}\`${exacta.bruta}\` ya está declarada con un valor multilínea ` +
          `y no la toco — ${aMano}`)
      }
      return reemplazarValor(lineas, exacta.i, exacta.bruta, v)
    }
    const enLinea = asignaciones.find((a) => a.ruta === objetivo)
    if (enLinea) {                                  // `"x" = { enabled = false }`
      const nuevo = ponerEnTablaEnLinea(enLinea.resto, clave, v)
      if (nuevo === null) {
        throw new Error(`${quien}\`${enLinea.bruta}\` ya está declarada como tabla en línea en la ` +
          `línea ${enLinea.i + 1} y no puedo editarla sin riesgo — ${aMano}`)
      }
      const term = lineas[enLinea.i].endsWith("\r\n") ? "\r\n" : lineas[enLinea.i].endsWith("\n") ? "\n" : ""
      lineas[enLinea.i] = `${enLinea.sangria}${enLinea.bruta} =${nuevo}${term}`
      return lineas.join("")
    }
    // Solo vale si la asignación vive en el ÁMBITO EXACTO del objetivo: `[plugins."x"]` + `otra = 1`
    // o `plugins."x".otra = 1` en la raíz. Si está bajo una cabecera MÁS PROFUNDA
    // (`[plugins."x".env]` + `MI_VAR = "1"`), insertar ahí metería `enabled` DENTRO de `env`.
    const implicita = asignaciones.find((a) => {
      if (!objetivo || !a.ruta.startsWith(`${objetivo}.`)) return false
      const pref = normalizarTabla(prefijoClave(a.bruta))
      const ambito = normalizarTabla([a.tabla, pref].filter(Boolean).join("."))
      return ambito === objetivo
    })
    if (implicita) {                                // `plugins."x".otra = 1` → la tabla ya existe
      const prefijo = prefijoClave(implicita.bruta)
      if (lineas[implicita.i] && !lineas[implicita.i].endsWith("\n")) lineas[implicita.i] += eol
      lineas.splice(implicita.i + 1, 0,
        `${implicita.sangria}${prefijo ? prefijo + "." : ""}${clave} = ${v}${eol}`)
      return lineas.join("")
    }
    const dentroDeOtro = asignaciones.find((a) => a.ruta && objetivo.startsWith(`${a.ruta}.`))
    if (dentroDeOtro) {                             // `plugins = { "x" = { … } }`: no me meto
      throw new Error(`${quien}\`${dentroDeOtro.bruta}\` (línea ${dentroDeOtro.i + 1}) ya declara ` +
        `\`${dentroDeOtro.ruta}\` como valor: añadir [${tabla}] dejaría el fichero sin parsear — ${aMano}`)
    }
    if (opciones.soloSiExiste) return texto
    const out = [...lineas]
    if (out.length && !out[out.length - 1].endsWith("\n")) out[out.length - 1] += eol
    if (out.length && out[out.length - 1].trim() !== "") out.push(eol)
    out.push(`[${tabla}]${eol}`, `${clave} = ${v}${eol}`)
    return out.join("")
  }

  const iTabla = cab.i
  const siguiente = cabeceras.find((c) => c.i > iTabla)
  const fin = siguiente ? siguiente.i : lineas.length
  for (let i = iTabla + 1; i < fin; i++) {
    if (!libre[i]) continue
    const term = lineas[i].endsWith("\r\n") ? "\r\n" : lineas[i].endsWith("\n") ? "\n" : ""
    const cuerpo = term ? lineas[i].slice(0, -term.length) : lineas[i]
    const a = partirAsignacion(cuerpo)
    if (a && normalizarTabla(a.bruta) === claveNorm) {
      // Un valor que abre un literal multilínea no se reemplaza línea a línea: se deja estar.
      if (avanzarLexico(cuerpo, { multi: null, corchetes: 0 }).multi) continue
      return reemplazarValor(lineas, i, clave, v)
    }
  }
  let ins = fin
  while (ins > iTabla + 1 && libre[ins - 1] && !lineas[ins - 1].trim()) ins--   // antes de los blancos
  if (lineas[ins - 1] && !lineas[ins - 1].endsWith("\n")) lineas[ins - 1] += eol
  lineas.splice(ins, 0, `${clave} = ${v}${eol}`)
  return lineas.join("")
}

/**
 * Todas las RUTAS que un TOML declara con un valor, ya vengan de una cabecera + clave, de una
 * clave con punto o de dentro de una tabla en línea (que se expande). Es el analizador que usa la
 * POST-CONDICIÓN de `ponerToml`: sin él no había forma de saber si lo escrito acabó donde se
 * pedía. Los valores se devuelven como TEXTO (no se interpretan): basta para comparar con lo que
 * acabamos de escribir y para contar declaraciones repetidas.
 */
export function rutasToml(texto) {
  const lineas = texto ? texto.split(/(?<=\n)/) : []
  const { asignaciones } = analizarToml(lineas)
  const out = []
  const expandir = (ruta, resto, prof) => {
    const nucleo = partirValor(resto)[0].trim()
    if (prof < 8 && nucleo.startsWith("{") && nucleo.endsWith("}") && nucleo.length >= 2) {
      const trozos = partirComas(nucleo.slice(1, -1))
      if (trozos !== null) {
        let todas = true
        const hijos = []
        for (const t of trozos) {
          const a = partirAsignacion(t)
          if (!a) { todas = false; break }
          hijos.push([`${ruta}.${normalizarTabla(a.bruta)}`, a.resto])
        }
        if (todas) {
          for (const [r, x] of hijos) expandir(r, x, prof + 1)
          return
        }
      }
    }
    out.push({ ruta, valor: nucleo })
  }
  for (const a of asignaciones) expandir(a.ruta, a.resto, 0)
  return out
}

/** Cómo está declarada (si lo está) la tabla objetivo: se NOMBRA en los errores. */
function formaToml(texto, objetivo, rutaObjetivo) {
  const lineas = texto ? texto.split(/(?<=\n)/) : []
  const { cabeceras, asignaciones } = analizarToml(lineas)
  const doble = cabeceras.find((c) => c.nombre === objetivo && c.doble)
  if (doble) return `array de tablas [[${objetivo}]]`
  if (cabeceras.some((c) => c.nombre === objetivo)) return `cabecera [${objetivo}]`
  if (asignaciones.some((a) => a.ruta === rutaObjetivo)) return "clave con punto"
  if (asignaciones.some((a) => a.ruta === objetivo)) return "tabla en línea"
  const sub = cabeceras.find((c) => objetivo && c.nombre.startsWith(`${objetivo}.`))
  if (sub) return `sub-tabla [${sub.nombre}]`
  if (asignaciones.some((a) => objetivo && a.ruta.startsWith(`${objetivo}.`))) return "clave anidada"
  if (asignaciones.some((a) => a.ruta && objetivo.startsWith(`${a.ruta}.`))) return "valor que contiene la tabla"
  return "sin declarar"
}

/**
 * `ponerToml` con POST-CONDICIÓN: escribe con el editor de arriba y, ANTES de devolver el texto
 * (que es lo que el paso graba en disco), lo vuelve a analizar y exige que el camino EXACTO que
 * se pidió (`plugins."x".enabled`, `features.hooks`) quede declarado UNA sola vez y con el valor
 * pedido. Si no, no devuelve nada: lanza y el fichero se queda como estaba.
 *
 * Esto cierra de raíz la familia de fallos «la clave acaba en otro sitio y el instalador dice que
 * la puso» (cabecera, clave con punto, tabla en línea, sub-tabla implícita…): no hace falta
 * acertar con la forma nueva, basta con que el resultado no cuadre para que el paso falle y diga
 * qué hay que poner a mano. Vale más un error honesto que un `config.toml` corrupto con exit 0.
 */
export function ponerToml(texto, tabla, clave, valor, opciones = {}) {
  const nuevo = ponerTomlCrudo(texto, tabla, clave, valor, opciones)
  if (nuevo === texto) return nuevo                    // `soloSiExiste`: no se tocó nada que revisar
  const v = typeof valor === "string" ? JSON.stringify(valor) : String(valor)
  const objetivo = normalizarTabla(tabla)
  const claveNorm = normalizarTabla(clave)
  const rutaObjetivo = objetivo ? `${objetivo}.${claveNorm}` : claveNorm
  const quien = opciones.fichero ? `${opciones.fichero}: ` : ""
  const hits = rutasToml(nuevo).filter((r) => r.ruta === rutaObjetivo)
  const lineasN = nuevo.split(/(?<=\n)/)
  const choque = analizarToml(lineasN).cabeceras.filter((c) => c.nombre === rutaObjetivo).length
  const falla =
    hits.length === 0 ? `la clave no habría quedado declarada` :
    hits.length > 1 ? `la clave habría quedado declarada ${hits.length} veces (fichero ilegible)` :
    choque ? `\`${rutaObjetivo}\` habría quedado como clave Y como tabla a la vez` :
    hits[0].valor !== v ? `la clave habría quedado con el valor \`${hits[0].valor}\` en vez de \`${v}\`` :
    null
  if (falla) {
    throw new Error(`${quien}no toco el fichero: ${falla}. Tal y como está escrito ` +
      `(${formaToml(texto, objetivo, rutaObjetivo)}) no sé colocar \`${clave}\` con seguridad — ` +
      `ponlo tú (que \`${rutaObjetivo}\` valga ${v}) y vuelve a ejecutar el instalador`)
  }
  return nuevo
}

/** Lista los ficheros que un paso `copy` va a producir (para el manifiesto y el dry-run). */
function ficherosDe(from, to) {
  const abs = join(ROOT, from)
  if (!existsSync(abs)) return []
  if (statSync(abs).isFile()) return [to]
  const out = []
  const walk = (a, b) => {
    for (const e of readdirSync(a, { withFileTypes: true }).sort((x, y) => x.name.localeCompare(y.name))) {
      if (e.name === "__pycache__" || e.name.endsWith(".pyc")) continue
      const na = join(a, e.name), nb = join(b, e.name)
      if (e.isDirectory()) walk(na, nb)
      else out.push(nb)
    }
  }
  walk(abs, to)
  return out
}

// ---------------------------------------------------------------- CLIs de los runtimes

/**
 * Ejecuta un comando del PATH capturando su salida (para poder reaccionar a lo que dice).
 *
 * En Windows, `claude` y `codex` suelen ser lanzadores `.cmd`, y Node no ejecuta un `.cmd` sin
 * intérprete. Se resuelve la ruta real y, si lo es, se pasa por `cmd.exe /d /s /c` con TODO
 * entrecomillado a mano: `shell: true` juntaría los argumentos con espacios y partiría cualquier
 * ruta que los tenga (la de este repo, sin ir más lejos).
 */
export const TIMEOUT_DEFECTO = 120_000

/**
 * `CUSTOM_AGENTS_EXEC_TIMEOUT_MS` tiene que ser un entero de milisegundos > 0. Un `-1` pasaba el
 * `Number(x) || 120_000` y hacía fallar TODOS los `exec` con «timeout out of range» (sin caer al
 * respaldo), y un `0` se convertía en 120000 sin decirlo. Pura, para poder probarla.
 */
export function validarTimeout(crudo) {
  if (crudo === undefined || crudo === null || String(crudo).trim() === "") {
    return { ms: TIMEOUT_DEFECTO, aviso: null }
  }
  const n = Number(crudo)
  if (!Number.isInteger(n) || n <= 0) {
    return {
      ms: TIMEOUT_DEFECTO,
      aviso: `CUSTOM_AGENTS_EXEC_TIMEOUT_MS="${crudo}" no es un entero de milisegundos > 0 — ` +
             `uso el valor por defecto (${TIMEOUT_DEFECTO} ms)`,
    }
  }
  return { ms: n, aviso: null }
}

const TIMEOUT = validarTimeout(process.env.CUSTOM_AGENTS_EXEC_TIMEOUT_MS)
export const TIMEOUT_EXEC = TIMEOUT.ms
let avisadoTimeout = false

/**
 * Un argumento para la línea de `cmd.exe`. Tres cosas:
 *   · comillas dobladas, para que una ruta con espacios (o con `"`) llegue entera;
 *   · los `\` que preceden a una `"` DUPLICADOS (regla del parser de MSVCRT: `2n` barras + `"`
 *     son n barras literales y una comilla de verdad). Sin esto, `--source "C:\mi clon\"` cerraba
 *     mal el argumento y se comía el siguiente;
 *   · `%` FUERA de las comillas y escapado con `^`, porque `cmd.exe` expande `%VAR%` también
 *     dentro de comillas: un argumento literal `%MISECRETO%` llegaba con el VALOR de la variable.
 *     (`%%` no sirve en la línea de comandos, solo en un `.bat`: comprobado.)
 */
const citarCmd = (t) => {
  let out = '"', barras = 0
  for (const ch of t) {
    if (ch === "\\") { barras++; out += ch; continue }
    if (ch === '"') { out += "\\".repeat(barras) + '""'; barras = 0; continue }
    barras = 0
    out += ch
  }
  return out + "\\".repeat(barras) + '"'
}

export const argCmd = (a) => String(a).split("%").map(citarCmd).join("^%")

/**
 * Mata el ÁRBOL de un proceso que ha expirado. `execFileSync` mata al hijo directo (el `cmd.exe`),
 * pero no a su nieto: la CLI colgada seguía viva consumiendo el terminal (comprobado con
 * `tasklist`). En Windows eso es `taskkill /T /F`; en el resto, el grupo de procesos.
 */
function matarArbol(pid) {
  if (!pid) return
  if (process.platform !== "win32") {
    try { process.kill(-pid, "SIGKILL") } catch { /* sin grupo propio: nada que barrer */ }
    return
  }
  // Por ruta absoluta: el PATH del usuario puede no traer `System32` (ni `wbem`), y esto tiene que
  // funcionar precisamente cuando el entorno está raro.
  const sys32 = join(process.env.SystemRoot || "C:\\Windows", "System32")
  const deSistema = (relativa, nombre) => {
    const p = join(sys32, relativa)
    return existsSync(p) ? p : nombre
  }
  // 1) El árbol, si sigue en pie.
  try {
    execFileSync(deSistema("taskkill.exe", "taskkill"), ["/T", "/F", "/PID", String(pid)], { stdio: "ignore" })
  } catch { /* ya no está */ }
  // 2) Y los HUÉRFANOS: al expirar, Node ya ha matado al hijo directo (el `cmd.exe`), así que
  //    `taskkill /T` no encuentra a quién seguir y el nieto —la CLI de verdad— se queda vivo
  //    (comprobado con `tasklist`). Su `ParentProcessId` sigue apuntando al pid muerto, que es
  //    justo por donde se les pesca. `wmic` ya NO existe en Windows 11 (24H2 lo retiró de la
  //    imagen), así que si esa vía falla se cae a PowerShell + CIM —el sustituto oficial— con la
  //    MISMA consulta por `ParentProcessId`. Los dos pasos son mejor esfuerzo: nunca peor que
  //    antes (gap B-12: sin el respaldo, el nieto sobrevivía al timeout en silencio).
  try {
    execFileSync(deSistema(join("wbem", "WMIC.exe"), "wmic"),
      ["process", "where", `(ParentProcessId=${pid})`, "call", "terminate"],
      { stdio: "ignore", timeout: 15_000 })
  } catch {
    try {
      execFileSync(deSistema(join("WindowsPowerShell", "v1.0", "powershell.exe"), "powershell"),
        ["-NoProfile", "-NonInteractive", "-Command",
          `Get-CimInstance Win32_Process -Filter 'ParentProcessId=${pid}' `
          + `| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }`],
        { stdio: "ignore", timeout: 15_000 })
    } catch { /* ni siquiera PowerShell: mejor esfuerzo, nunca peor que antes */ }
  }
}

function correr(cmd, args, cwd, env = process.env) {
  if (TIMEOUT.aviso && !avisadoTimeout) { avisadoTimeout = true; say(`  ${WARN} ${dim(TIMEOUT.aviso)}`) }
  const opciones = {
    encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], cwd, env,
    // Sin timeout, una CLI que se queda pensando (o pidiendo algo por stdin) cuelga el `npx`
    // para siempre y sin una línea en pantalla. 120 s de sobra; `CUSTOM_AGENTS_EXEC_TIMEOUT_MS`
    // para quien tenga una máquina lenta o quiera apretarlo en CI.
    timeout: TIMEOUT_EXEC,
  }
  const real = rutaDe(cmd)
  try {
    if (process.platform === "win32" && real && /\.(cmd|bat)$/i.test(real)) {
      const linea = [real, ...args].map(argCmd).join(" ")
      return execFileSync(process.env.COMSPEC || "cmd.exe", ["/d", "/s", "/c", `"${linea}"`],
        { ...opciones, windowsVerbatimArguments: true })
    }
    return execFileSync(real || cmd, args, opciones)
  } catch (e) {
    if (expiro(e)) {
      matarArbol(e.pid)
      const err = new Error(`\`${cmd}\` expiró a los ${Math.round(TIMEOUT_EXEC / 1000)} s; ` +
        `si tu máquina necesita más, sube CUSTOM_AGENTS_EXEC_TIMEOUT_MS (en milisegundos)`)
      err.stdout = e.stdout
      err.stderr = e.stderr
      err.expirado = true
      throw err
    }
    throw e
  }
}

/**
 * Native cache installation, with project enablement isolated from the user's config.
 * Codex 0.161's setter always enables in CODEX_HOME. A private regular config snapshot and
 * a link only to our marketplace cache let native staging/version replacement stay native.
 * Relative config paths resolve against the snapshot home: keep native rejections, never
 * retry using an empty config or the real home. System-managed requirements remain native.
 */
export function instalarCodexNativo({dir,scope,version,marketplaceRoot,home=codexHome(),tempRoot=tmpdir(),
  runner=(args,o)=>correr("codex",args,o.cwd,o.env)}={}) {
  const realHome=resolve(home)
  validarCacheCodex(realHome)
  const args=["plugin","add",PLUGIN_ID,"--json"]
  let isolated=null, link=null
  try {
    let nativeHome=realHome
    if(scope==="project") {
      isolated=mkdtempSync(join(tempRoot,"custom-agents-codex-"))
      nativeHome=isolated
      const userConfig=join(realHome,"config.toml")
      // readFile follows any user symlink; the destination is always our own regular file.
      const contents=existsSync(userConfig) ? readFileSync(userConfig) : Buffer.from("")
      validarSnapshotCodex(contents.toString("utf8"))
      writeFileSync(join(isolated,"config.toml"),contents,{flag:"wx",mode:0o600})
      const namespace=join(realHome,"plugins","cache",MKT)
      mkdirSync(namespace,{recursive:true})
      mkdirSync(join(isolated,"plugins","cache"),{recursive:true})
      link=join(isolated,"plugins","cache",MKT)
      symlinkSync(namespace,link,process.platform==="win32" ? "junction" : "dir")
    } else if(scope!=="user") throw new Error("unsupported Codex installation scope")
    const options={cwd:dir,env:{...process.env,CODEX_HOME:nativeHome}}
    let nativeArgs=args
    if(scope==="project") {
      const sourceRoot=resolve(marketplaceRoot || dir)
      // A project layer can outrank the snapshot. Pin only the requested marketplace source
      // for these native operations, while managed admission requirements still apply.
      const sourceOverrides=["-c",`marketplaces.${MKT}.source_type="local"`,"-c",`marketplaces.${MKT}.source=${JSON.stringify(sourceRoot)}`]
      const sourceState=comprobarFuenteCodex(join(nativeHome,"config.toml"),sourceRoot)
      if(sourceState==="unknown") throw new Error("ambiguous marketplace source in isolated Codex config")
      // Registry mutations must see the snapshot as user config, not a higher-precedence
      // project entry that Codex refuses to remove. Native add retains the actual project cwd.
      const registryCwd=join(nativeHome,"registry-cwd")
      mkdirSync(registryCwd)
      const registryOptions={...options,cwd:registryCwd}
      // Replacing only the private snapshot's registry does not change the user's marketplace.
      if(sourceState==="conflict") runner(["plugin","marketplace","remove",MKT],registryOptions)
      runner(["plugin","marketplace","add",sourceRoot,...sourceOverrides],registryOptions)
      nativeArgs=[...args,...sourceOverrides]
    }
    const raw=runner(nativeArgs,options)
    let result
    try {result=JSON.parse(String(raw))} catch {throw new Error("Codex native add returned invalid JSON")}
    if(result?.pluginId!==PLUGIN_ID || result.version!==version || typeof result.installedPath!=="string") {
      throw new Error("Codex native add returned an unexpected plugin or version")
    }
    const expected=join(realHome,"plugins","cache",MKT,PLUGIN,version)
    const alias=join(nativeHome,"plugins","cache",MKT,PLUGIN,version)
    if(!mismaRuta(result.installedPath,alias) || !existsSync(expected) || !statSync(expected).isDirectory()
      || !mismaRuta(realpathSync(result.installedPath),expected)) {
      throw new Error("Codex native add did not materialize the expected cache entry")
    }
    return {pluginId:PLUGIN_ID,version:result.version,installedPath:expected}
  } finally {
    // Unlink the owned junction first. Cleanup never recursively follows a link into the cache.
    if(link) {try {unlinkSync(link)} catch {/* creation may have failed */}}
    if(isolated) rmSync(isolated,{recursive:true,force:true})
  }
}

/** The shared native cache must already identify this bundle before we replace it. */
export function validarCacheCodex(home) {
  const root=join(home,"plugins","cache",MKT,PLUGIN)
  if(!existsSync(root)) return
  const repository=leerJson(join(ROOT,".codex-plugin","plugin.json"))?.repository
  if(typeof repository!=="string" || !repository) throw new Error("Codex cache ownership cannot be verified")
  for(const entry of readdirSync(root,{withFileTypes:true})) {
    if(!entry.isDirectory()) continue
    const manifest=leerJson(join(root,entry.name,".codex-plugin","plugin.json"))
    if(manifest?.name!==PLUGIN || manifest.repository!==repository) {
      throw new Error("foreign or unverifiable Codex cache ownership; native replacement declined")
    }
  }
}

function cadenaToml(raw) {
  if((raw[0]!=='"' && raw[0]!=="'") || finCadenaToml(raw,0)!==raw.length-1) return null
  let value=raw.slice(1,-1)
  if(/[\x00-\x08\x0A-\x1F\x7F]/.test(value)) return null
  if(raw[0]==="'") return value
  const escapes={b:"\b",t:"\t",n:"\n",f:"\f",r:"\r",'"':'"',"\\":"\\"}
  let decoded=""
  for(let i=0;i<value.length;i++) {
    if(value[i]!=="\\") {decoded+=value[i];continue}
    const code=value[++i]
    if(Object.hasOwn(escapes,code)) decoded+=escapes[code]
    else if(code==="u" || code==="U") {
      const n=code==="u" ? 4 : 8, hex=value.slice(i+1,i+1+n)
      if(hex.length!==n || !/^[0-9a-f]+$/i.test(hex)) return null
      const point=parseInt(hex,16)
      if(point>0x10FFFF || point>=0xD800 && point<=0xDFFF) return null
      decoded+=String.fromCodePoint(point);i+=n
    } else return null
  }
  return decoded
}

/** Guard the existing source before invoking a native registry mutation. */
export function comprobarFuenteCodex(file,expectedRoot) {
  if(!existsSync(file)) return "absent"
  let text
  try {text=readFileSync(file,"utf8")} catch {return "unknown"}
  const prefix=normalizarTabla(`marketplaces.${MKT}`)
  let entries
  try {entries=rutasToml(text).filter(entry=>entry.ruta===prefix || entry.ruta.startsWith(`${prefix}.`))}
  catch {return "unknown"}
  if(!entries.length) {
    const declared=analizarToml(text.split(/(?<=\n)/)).cabeceras.some(c=>c.nombre===prefix || c.nombre.startsWith(`${prefix}.`))
    return declared ? "unknown" : "absent"
  }
  const field=name=>entries.filter(e=>e.ruta===`${prefix}.${name}`)
  const types=field("source_type"), sources=field("source")
  if(types.length!==1 || sources.length!==1) return "unknown"
  const type=cadenaToml(types[0].valor), source=cadenaToml(sources[0].valor)
  if(type===null || source===null) return "unknown"
  if(type!=="local") return "conflict"
  if(!isAbsolute(source)) return "unknown"
  return mismaRuta(source,expectedRoot) ? "same" : "conflict"
}

/** Typed path fields from the pinned 0.161 config schema; reject ambiguous snapshots. */
export function validarSnapshotCodex(text) {
  const rootScalar=new Set(["model_instructions_file","js_repl_node_path","sqlite_home","log_dir","model_catalog_json",
    "experimental_compact_prompt_file"])
  const profileScalar=new Set(["model_instructions_file","js_repl_node_path","model_catalog_json","experimental_compact_prompt_file"])
  for(const entry of rutasToml(text)) {
    const route=entry.ruta,leaf=route.split(".").at(-1)
    const profile=/^profiles\.(?:[A-Za-z0-9_-]+|"(?:\\.|[^"\\])*")\.([A-Za-z0-9_-]+)$/.test(route)
    const scalar=rootScalar.has(route) || profile && profileScalar.has(leaf)
      || /^agents\.(?:[A-Za-z0-9_-]+|"(?:\\.|[^"\\])*")\.config_file$/.test(route)
      || /^mcp_servers\.(?:[A-Za-z0-9_-]+|"(?:\\.|[^"\\])*")\.cwd$/.test(route)
      || route==="skills.config.path"
      || /^otel\.(?:exporter|trace_exporter|metrics_exporter)\.otlp-(?:http|grpc)\.tls\.(?:ca-certificate|client-certificate|client-private-key)$/.test(route)
    const vector=route==="js_repl_node_module_dirs" || profile && leaf==="js_repl_node_module_dirs"
      || route==="sandbox_workspace_write.writable_roots"
    let values
    if(route==="skills.config") {
      if(!entry.valor.startsWith("[") || !entry.valor.endsWith("]")) throw new Error("ambiguous relative config path in skills.config")
      const selectors=partirComas(entry.valor.slice(1,-1))
      if(selectors===null) throw new Error("ambiguous relative config path in skills.config")
      values=[]
      for(const selector of selectors) {
        if(!selector.trim().startsWith("{") || !selector.trim().endsWith("}")) throw new Error("ambiguous relative config path in skills.config")
        const fields=rutasToml(`selector = ${selector}`)
        if(fields.some(f=>f.ruta==="selector")) throw new Error("ambiguous relative config path in skills.config")
        values.push(...fields.filter(f=>f.ruta==="selector.path").map(f=>f.valor))
      }
    } else if(scalar) values=[entry.valor]
    else if(vector) {
      if(!entry.valor.startsWith("[") || !entry.valor.endsWith("]")) throw new Error(`ambiguous relative config path in ${leaf}; use absolute paths before project installation`)
      values=partirComas(entry.valor.slice(1,-1))
      if(values===null) throw new Error(`ambiguous relative config path in ${leaf}; use absolute paths before project installation`)
    } else continue
    for(const raw of values) {
      const value=cadenaToml(raw.trim())
      if(value===null || !isAbsolute(value)) throw new Error(`relative or ambiguous config path in ${leaf}; use absolute paths before project installation`)
    }
  }
}

const mismoValorToml=(a,b)=>a===b || cadenaToml(a)!==null && cadenaToml(a)===cadenaToml(b)

/** Restore only a recorded own key when the user has not subsequently changed its value. */
export function restaurarClaveToml(text,table,key,record) {
  const prefix=normalizarTabla(table), target=`${prefix}.${normalizarTabla(key)}`
  const hits=rutasToml(text).filter(e=>e.ruta===target)
  if(hits.length!==1 || !mismoValorToml(hits[0].valor,record.escrito)) return text
  const lines=text.split(/(?<=\n)/), index=analizarToml(lines)
  const assignment=index.asignaciones.find(e=>e.ruta===target || target.startsWith(`${e.ruta}.`))
  if(!assignment) throw new Error("cannot safely restore owned TOML key")
  const editInline=(raw,base)=>{
    const value=partirValor(raw)[0].trim()
    if(base===target) return record.previo
    if(!value.startsWith("{") || !value.endsWith("}")) throw new Error("cannot safely restore inline TOML key")
    const parts=partirComas(value.slice(1,-1))
    if(parts===null) throw new Error("cannot safely restore inline TOML key")
    const remaining=[]
    for(const part of parts) {
      const parsed=partirAsignacion(part)
      if(!parsed) throw new Error("cannot safely restore inline TOML key")
      const route=`${base}.${normalizarTabla(parsed.bruta)}`
      if(route===target || target.startsWith(`${route}.`)) {
        const replacement=editInline(parsed.resto,route)
        if(replacement!==null) remaining.push(`${parsed.sangria}${parsed.bruta} = ${replacement}`)
      } else remaining.push(part)
    }
    return remaining.length ? `{${remaining.join(",")}}` : "{}"
  }
  const replacement=assignment.ruta===target ? record.previo : editInline(assignment.resto,assignment.ruta)
  const original=lines[assignment.i], end=original.endsWith("\r\n") ? "\r\n" : original.endsWith("\n") ? "\n" : ""
  const comment=partirValor(assignment.resto)[1]
  lines[assignment.i]=replacement===null ? (comment ? `${assignment.sangria}${comment}${end}` : "")
    : `${assignment.sangria}${assignment.bruta} = ${replacement}${comment ? ` ${comment}` : ""}${end}`
  let updated=lines.join("")
  if(record.tablaCreada && !rutasToml(updated).some(e=>e.ruta===prefix || e.ruta.startsWith(`${prefix}.`))) {
    const updatedLines=updated.split(/(?<=\n)/), headers=analizarToml(updatedLines).cabeceras
    if(!headers.some(h=>h.nombre.startsWith(`${prefix}.`))) {
      for(const header of headers.filter(h=>h.nombre===prefix)) updatedLines[header.i]=""
      updated=updatedLines.join("")
    }
  }
  return updated
}

/** ¿Este fallo de `execFileSync` es el del `timeout`? (Node lo cuenta de dos maneras). */
const expiro = (e) => e?.code === "ETIMEDOUT" || e?.errno === "ETIMEDOUT" ||
  (e?.killed === true && (e?.signal === "SIGTERM" || e?.signal === null))

const salidaDe = (e) => `${e?.stdout || ""}${e?.stderr || ""}${e?.message || ""}`

/**
 * Vuelca lo que dijo una CLI que ha fallado. La salida se captura (`stdio: pipe`) para poder
 * reaccionar a ella, así que si no se imprime aquí el usuario ve un fallo sin ninguna pista.
 */
function volcar(salida) {
  const lineas = String(salida || "").split(/\r?\n/).map((l) => l.trimEnd()).filter(Boolean)
  for (const l of lineas.slice(0, 12)) say(`      ${dim(l)}`)
  if (lineas.length > 12) say(`      ${dim(`… y ${lineas.length - 12} línea(s) más`)}`)
}

/** "codex-cli 0.130.0" → "0.130.0". `null` si no se puede leer. */
function versionDe(cmd) {
  try { return (correr(cmd, ["--version"]).match(/(\d+)\.(\d+)\.(\d+)/) || [null])[0] } catch { return null }
}

export function versionSuficiente(version, minima) {
  if (!version) return false
  const a = version.split(".").map(Number), b = minima.split(".").map(Number)
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) > (b[i] || 0)
  }
  return true
}

// ---------------------------------------------------------------- ejecución de un plan

/** Clave de identidad de un apunte del manifiesto (para fusionar sin duplicar). */
const claveApunte = (e) =>
  e["json-set"] ? `json|${e["json-set"]}`
    : e["toml-set"] ? `toml|${e["toml-set"]}|${e.tabla}|${e.clave}`
      : e.exec ? `exec|${e.exec}`
        : JSON.stringify(e)

/**
 * Une el `registro` de una instalación anterior con el de esta. El manifiesto es lo ÚNICO que sabe
 * qué claves ajenas hemos tocado: si un segundo intento fallido lo reescribiera, las del primero
 * quedarían puestas para siempre (un plugin fantasma en `installed_plugins.json`). Los apuntes que
 * coinciden se combinan (unión de `claves`/`padresCreados`/`noQuitar`; `creado` si lo fue alguna vez).
 */
export function fusionarRegistro(previo, nuevo) {
  const orden = []
  const por = new Map()
  const mete = (e) => {
    const k = claveApunte(e)
    if (!por.has(k)) { por.set(k, { ...e }); orden.push(k); return }
    const a = por.get(k)
    const antes = { ...a }
    const une = (campo) => {
      const lista = [...new Set([...(antes[campo] || []), ...(e[campo] || [])])]
      if (lista.length) a[campo] = lista
    }
    Object.assign(a, e)
    une("claves"); une("padresCreados"); une("noQuitar")
    if (antes.creado) a.creado = true
  }
  for (const e of previo) mete(e)
  for (const e of nuevo) mete(e)
  return orden.map((k) => por.get(k))
}

function ejecutar(provider, opts) {
  const plan = buildPlan(provider, {
    root: ROOT, dir: opts.dir, scope: opts.scope, version: VERSION,
    modo: opts.modo, source: opts.source,
  })
  const escritos = []
  const retirados = new Set()
  const nativeAgents = {...(leerJson(join(provider.destino(opts.scope,opts.dir,opts.modo),manifiestoDe(provider,opts.modo)))?.nativeAgents || {})}
  const registro = []   // lo que no es un fichero nuestro: comandos y claves de configuración
  const avisos = []
  const completed = new Set()
  let nativePending=false
  let roleMigrationPending=false
  let n = 0

  // Qué ficheros del registro habíamos creado NOSOTROS en una instalación anterior. Al reinstalar
  // ya existen, claro: sin esta memoria, la segunda pasada los daría por «del usuario» y al
  // desinstalar se quedarían ahí para siempre.
  const manPrevio = leerJson(join(provider.destino(opts.scope, opts.dir, opts.modo),
    manifiestoDe(provider, opts.modo)))
  const creadosAntes = new Set((manPrevio?.registro || [])
    .filter((e) => e["json-set"] && e.creado).map((e) => e["json-set"]))
  const padresAntes = new Map((manPrevio?.registro || [])
    .filter((e) => e["json-set"] && e.padresCreados).map((e) => [e["json-set"], e.padresCreados]))

  /**
   * El manifiesto se escribe pase lo que pase. Si un paso revienta a mitad (p. ej. el
   * `marketplace add` fue bien y el `plugin install` falló), sin manifiesto lo ya aplicado queda
   * SIN registro y `uninstall` se niega a limpiarlo: se guarda uno parcial, marcado `incompleto`.
   */
  const guardar = (estado, error) => {
    if (opts.dryRun) return
    const destino = provider.destino(opts.scope, opts.dir, opts.modo)
    // FUSIÓN con lo que hubiera: si una pasada anterior se quedó a medias, su `registro` es la
    // única pista de las claves que llegó a poner. Reescribirlo dejaba un plugin FANTASMA en
    // `installed_plugins.json` apuntando a un `installPath` ya borrado.
    escribirJson(join(destino, manifiestoDe(provider, opts.modo)), {
      plugin: "custom-agents",
      version: VERSION,
      provider: provider.id,
      scope: opts.scope,
      modo: opts.modo,
      installedAt: new Date().toISOString(),
      ...(estado === "completo" ? {} : { estado, error: String(error?.message || error) }),
      files: [...new Set([...(manPrevio?.files || []).filter(f => !retirados.has(f)), ...escritos.map((f) => f.split(sep).join("/"))])].sort(),
      ...(Object.keys(nativeAgents).length ? {nativeAgents} : {}),
      registro: fusionarRegistro(manPrevio?.registro || [], registro),
    })
  }

  // Señales: un Ctrl-C (o un `taskkill`) a mitad de 444 ficheros dejaba lo copiado SIN manifiesto y
  // `uninstall` respondía «no encuentro ningún manifiesto». Se guarda lo aplicado hasta aquí y se
  // sale con el código convenido (128 + número de señal).
  const SENALES = { SIGINT: 130, SIGTERM: 143, SIGBREAK: 149 }
  const alSalir = {}
  for (const [sig, code] of Object.entries(SENALES)) {
    alSalir[sig] = () => {
      try { guardar("incompleto", new Error(`interrumpido por ${sig}`)) } catch { /* mejor esfuerzo */ }
      console.error(`\n${WARN} ${sig}: dejo el manifiesto de lo aplicado. ` +
        `Límpialo con \`npx @daycry/custom-agents uninstall -p ${provider.id} --scope ${opts.scope}\``)
      process.exit(code)
    }
    // `SIGBREAK` solo existe en Windows: fuera de él, `process.on` lo rechaza.
    try { process.on(sig, alSalir[sig]) } catch { delete alSalir[sig] }
  }
  const soltarSenales = () => { for (const [sig, fn] of Object.entries(alSalir)) process.removeListener(sig, fn) }

  try {
    return ejecutarPlan()
  } catch (e) {
    // Los avisos acumulados hasta el fallo son justo los que explican el contexto: se dicen.
    avisos.push(...drenarAvisosEscritura())
    for (const a of avisos) say(`  ${WARN} ${dim(a)}`)
    try { guardar("incompleto", e) } catch (e2) { say(`  ${WARN} ${dim(`tampoco pude dejar el manifiesto: ${e2.message}`)}`) }
    throw e
  } finally {
    soltarSenales()
  }

  function ejecutarPlan() {
  for (const paso of plan) {
    if(paso.requires && !completed.has(paso.requires) && !opts.dryRun) {
      avisos.push(`${paso.type}: pendiente; no se completó ${paso.requires}`)
      if(provider.id==="codex") nativePending=true
      continue
    }
    if (paso.type === "retire") {
      if (retirarArtefacto(paso, provider.destino(opts.scope, opts.dir, opts.modo), opts.dryRun)) {
        retirados.add(paso.to.split(sep).join("/"))
        say(`  ${ARROW} ${rel(paso.to)} ${dim("(retirada de copia conocida)")}`)
      } else {
        avisos.push(`${rel(paso.to)} tiene cambios locales: conservado; migración pendiente de revisión`)
      }
    } else if (paso.type === "copy") {
      if (paso.nativeAgents) {
        const migration = planificarAgentesNativos(paso,manPrevio)
        avisos.push(...migration.warnings)
        if (migration.warnings.length) roleMigrationPending=true
        const retiring = new Set(migration.actions.filter(a=>a.type==='retire').map(a=>a.to.split(sep).join('/')))
        for (const path of migration.released) {
          if (!retiring.has(path)) { retirados.add(path); delete nativeAgents[path] }
        }
        for (const action of migration.actions) {
          say(`  ${ARROW} ${rel(action.to)} ${dim(action.type === 'retire' ? '(retirada de agente propio)' : '(agente nativo)')}`)
          if (opts.dryRun) continue
          if (action.type === 'retire') {
            if (!retirarArtefacto({to:action.to,sha256:[action.before]},paso.to)) throw new Error('native agent changed before retirement')
            const path = action.to.split(sep).join('/');retirados.add(path);delete nativeAgents[path]
          } else {
            const now = existsSync(action.to) ? createHash('sha256').update(readFileSync(action.to,'utf8').replace(/\r\n/g,'\n')).digest('hex') : null
            if (now !== action.before) throw new Error('native agent changed before copy')
            escritos.push(action.to); nativeAgents[action.to.split(sep).join('/')] = action.sha256
            guardar('incompleto',new Error('copiando agente nativo'))
            mkdirSync(dirname(action.to),{recursive:true})
            escribirAtomico(action.to,readFileSync(action.from,'utf8'))
            n++
          }
        }
        continue
      }
      const abs = join(ROOT, paso.from)
      if (!existsSync(abs)) {
        avisos.push(`no encuentro ${paso.from} en el paquete — paso omitido`)
        continue
      }
      const destinos = ficherosDe(paso.from, paso.to)
      if (paso.aviso) avisos.push(paso.aviso)
      if (opts.dryRun) {
        say(`  ${ARROW} ${rel(paso.to)} ${dim(`(${destinos.length} fichero(s) de ${paso.from})`)}`)
      } else {
        // El manifiesto se apunta ANTES de copiar: un `taskkill /F` a mitad de la copia no deja
        // ejecutar ningún manejador de señal, así que la única forma de que lo copiado se pueda
        // deshacer es que ya esté inventariado. Cuesta un JSON pequeño por paso.
        escritos.push(...destinos)
        try { guardar("incompleto", new Error(`copiando ${paso.from}`)) } catch { /* mejor esfuerzo */ }
        mkdirSync(dirname(paso.to), { recursive: true })
        cpSync(abs, paso.to, {
          recursive: true,
          force: true,
          filter: (src) => !src.includes(`${sep}__pycache__`) && !src.endsWith(".pyc"),
        })
      }
      if (opts.dryRun) escritos.push(...destinos)   // en disco ya se apuntaron antes de copiar
      n += destinos.length
    } else if (paso.type === "merge") {
      const actual = leerJson(paso.to)
      // `onlyIfMissing`: subárboles que NO se fusionan si el usuario ya tiene esa clave. Sirve
      // para lo que no se puede fusionar sin cambiar la semántica de su configuración.
      const aFusionar = { ...paso.merge }
      for (const k of paso.onlyIfMissing || []) {
        if (actual && k in actual) {
          delete aFusionar[k]
          if (paso.nota) avisos.push(`${rel(paso.to)}: ${paso.nota}`)
        }
      }
      // `upsert`: arrays con identidad propia (p. ej. `plugins` por `name` en el marketplace de
      // Codex) que se reemplazan en su sitio en vez de appendear por referencia.
      const [fusionado, anadidas] = fusionar(actual, aFusionar, paso.upsert || {})
      // Lo que la fusión haya tenido que decidir sobre la config del usuario se dice AQUÍ, junto
      // al fichero que lo provoca (gap B-5), no al final y sin contexto.
      avisos.push(...drenarAvisosEscritura().map((a) => `${rel(paso.to)}: ${a}`))
      const cambia = !actual || anadidas.length > 0
      if (opts.dryRun) {
        say(`  ${ARROW} ${rel(paso.to)} ${dim(cambia ? `(fusiona: ${anadidas.join(", ") || "crea el fichero"})` : "(ya está al día)")}`)
      } else if (cambia) {
        escribirJson(paso.to, fusionado)
      }
      if (actual && anadidas.length === 0) avisos.push(`${rel(paso.to)} ya tenía la configuración — respetada`)
      // Un `merge` NUNCA se apunta en el manifiesto, ni cuando el instalador crea el fichero:
      // desde ese momento es config del usuario y puede haberla editado. Consecuencias, las dos
      // buscadas: `uninstall` no la borra (lo dice al terminar) y el manifiesto sale IGUAL
      // instales una vez o diez (idempotencia comprobada en tests/installer.test.mjs).
      n += cambia ? 1 : 0
    } else if (paso.type === "write") {
      if (opts.dryRun) say(`  ${ARROW} ${rel(paso.to)}`)
      else { mkdirSync(dirname(paso.to), { recursive: true }); writeFileSync(paso.to, paso.content, "utf8") }
      escritos.push(paso.to)
      n++
    } else if (paso.type === "codex-native-add") {
      const command=[paso.cmd,...paso.args].join(" ")
      if(paso.codexMarketplace) {
        const sourceState=comprobarFuenteCodex(paso.codexMarketplace.config,paso.codexMarketplace.root)
        if(sourceState==="unknown" || sourceState==="conflict" && !opts.forceMarketplace) {
          avisos.push("marketplace del proyecto: fuente existente ajena o ambigua; registro y activación pendientes (usa --force-marketplace para reemplazar una fuente conocida)")
          nativePending=true
          continue
        }
      }
      if(opts.dryRun) {say(`  ${ARROW} ${dim("$")} ${command} ${dim("(caché nativa; activación del scope después del éxito)")}`);continue}
      const state=estadoCli(paso.cmd), nativeVersion=state==="si" ? versionDe(paso.cmd) : null
      if(state!=="si" || !versionSuficiente(nativeVersion,paso.minVersion)) {
        avisos.push(`caché nativa pendiente: se requiere Codex ejecutable >= ${paso.minVersion}; no se habilita el plugin`)
        nativePending=true
        continue
      }
      say(`  ${ARROW} ${dim("ejecutando")} ${dim("$")} ${command}${dim("…")}`)
      try {
        const native=instalarCodexNativo({dir:paso.cwd,scope:paso.scope,version:paso.version,marketplaceRoot:paso.marketplaceRoot})
        registro.push({exec:command,nativeCache:native.installedPath})
        completed.add(paso.id)
        n++
      } catch(error) {
        volcar(salidaDe(error))
        throw new Error(`${command}: ${primeraLinea(salidaDe(error))}; el plugin no se habilita`)
      }
    } else if (paso.type === "exec") {
      const cmdTexto = [paso.cmd, ...paso.args].join(" ")
      const apunte = { exec: cmdTexto, ...(paso.deshacer ? { deshacer: paso.deshacer } : {}) }
      let replaceMarketplace=false
      if(paso.codexMarketplace) {
        const sourceState=comprobarFuenteCodex(paso.codexMarketplace.config,paso.codexMarketplace.root)
        if(sourceState==="unknown") {
          avisos.push("marketplace Codex: no puedo determinar con seguridad la fuente existente; registro y activación pendientes")
          continue
        }
        if(sourceState==="conflict") {
          if(!opts.forceMarketplace) {
            avisos.push(`el marketplace ya está dado de alta desde otra fuente y NO lo toco. Si quieres la de custom-agents: ${paso.cmd} plugin marketplace remove ${MKT} && ${cmdTexto} (o repite con --force-marketplace)`)
            continue
          }
          replaceMarketplace=true
        }
      }
      if (opts.dryRun) {
        say(`  ${ARROW} ${dim("$")} ${cmdTexto}`)
        registro.push(apunte)
        continue
      }
      const pendiente = (motivo) => {
        const m = `${motivo} — ejecútalo tú: ${cmdTexto}`
        if (paso.opcional || paso.siFalla === "aviso") avisos.push(m)
        else throw new Error(m)
      }
      const estado = estadoCli(paso.cmd)
      if (estado !== "si") {
        pendiente(estado === "no-ejecutable"
          ? `\`${paso.cmd}\` está en el PATH pero no es algo que yo sepa lanzar (shim sin extensión, ` +
            `\`.ps1\`, \`.vbs\`…: solo arranco .exe/.com/.cmd/.bat)`
          : `\`${paso.cmd}\` no está en el PATH`)
        continue
      }
      if (paso.minVersion) {
        const v = versionDe(paso.cmd)
        if (!versionSuficiente(v, paso.minVersion)) {
          pendiente(`${paso.cmd} ${v || "de versión desconocida"} < ${paso.minVersion}`)
          continue
        }
      }
      // Antes de lanzar, no después: si la CLI se queda pensando (o pidiendo algo), al menos se ve
      // en qué está el instalador mientras corre el `timeout`.
      say(`  ${ARROW} ${dim("ejecutando")} ${dim("$")} ${cmdTexto}${dim("…")}`)
      try {
        if(replaceMarketplace) {
          correr(paso.cmd,paso.siYaExiste.args,paso.cwd)
          apunte.forzado=[paso.cmd,...paso.siYaExiste.args].join(" ")
          avisos.push("--force-marketplace: sustituyo la fuente anterior del marketplace")
        }
        correr(paso.cmd, paso.args, paso.cwd)
      } catch (e) {
        const salida = salidaDe(e)
        // Recuperación declarada: el marketplace ya existía con OTRA fuente. Borrarlo y re-crearlo
        // con la nuestra es pisar configuración del usuario: solo con `--force-marketplace`.
        if (paso.siYaExiste && salida.includes(paso.siYaExiste.patron)) {
          if (paso.siYaExiste.soloConForce && !opts.forceMarketplace) {
            avisos.push(`el marketplace ya está dado de alta desde otra fuente y NO lo toco. ` +
              `Si quieres la de custom-agents: ${[paso.cmd, ...paso.siYaExiste.args].join(" ")} ` +
              `&& ${cmdTexto} (o repite con --force-marketplace)`)
            continue
          }
          try {
            correr(paso.cmd, paso.siYaExiste.args, paso.cwd)
            correr(paso.cmd, paso.args, paso.cwd)
            avisos.push(`--force-marketplace: he quitado el marketplace que había y lo he vuelto a ` +
              `dar de alta con la fuente de custom-agents`)
            apunte.forzado = [paso.cmd, ...paso.siYaExiste.args].join(" ")
          } catch (e2) { volcar(salidaDe(e2)); pendiente(`no pude rehacer el marketplace (${primeraLinea(salidaDe(e2))})`); continue }
        } else if (paso.siFalla === "error") {
          volcar(salida)
          throw new Error(`${cmdTexto}: ${primeraLinea(salida)}`)
        } else {
          volcar(salida)
          avisos.push(`${cmdTexto} no hizo falta o falló (${primeraLinea(salida)}) — se continúa`)
          continue
        }
      }
      say(`  ${OK} ${dim("$")} ${cmdTexto}`)
      registro.push(apunte)
      if(paso.id) completed.add(paso.id)
      n++
    } else if (paso.type === "json-set") {
      // A diferencia de `merge`, esto SÍ pisa: son las claves del registro del runtime, las que
      // lo hacen cargar el plugin. Se apuntan en el manifiesto para poder quitarlas (y solo ellas).
      // Lectura ESTRICTA: un JSON ilegible es un error, no una excusa para empezar de cero.
      const { existe, bom, valor: actual } = leerJsonEstricto(paso.to)
      const vol = paso.volatiles || []
      const claves = Object.keys(paso.set)
      const cambia = claves.some((r) => !igualSalvo(leerRuta(actual, r), paso.set[r], vol))
      const out = structuredClone(actual)
      // Qué objetos INTERMEDIOS no existían: los crea este paso, así que al desinstalar se pueden
      // quitar si se quedan vacíos (un `"enabledPlugins": {}` que el usuario nunca tuvo es basura).
      const padresCreados = [...(padresAntes.get(paso.to) || [])]
      for (const r of claves) {
        const ks = r.split(".")
        for (let i = 1; i < ks.length; i++) {
          const ruta = ks.slice(0, i).join(".")
          if (leerRuta(actual, ruta) === undefined && !padresCreados.includes(ruta)) padresCreados.push(ruta)
        }
      }
      // Se valida SIEMPRE (también en dry-run): así el `--dry-run` avisa de que el fichero del
      // usuario tiene una forma que no se puede tocar, en vez de descubrirlo al escribir.
      for (const r of claves) ponerRutaEstricta(out, r, paso.set[r], rel(paso.to))
      if (opts.dryRun) {
        say(`  ${ARROW} ${rel(paso.to)} ${dim(cambia ? `(pone ${claves.join(", ")})` : "(ya está al día)")}`)
      } else if (cambia) {
        escribirJson(paso.to, out, bom)
      }
      registro.push({
        "json-set": paso.to,
        claves: claves.filter((k) => !(paso.noQuitar || []).includes(k)),
        ...((paso.noQuitar || []).length ? { noQuitar: paso.noQuitar } : {}),
        ...(padresCreados.length ? { padresCreados } : {}),
        // Si el fichero NO existía, lo creó el instalador: al desinstalar, si se queda sin nada
        // nuestro dentro, se borra en vez de dejar un `{}` que el usuario nunca tuvo.
        ...(!existe || creadosAntes.has(paso.to) ? { creado: true } : {}),
      })
      n += cambia ? 1 : 0
    } else if (paso.type === "toml-set") {
      const previo = existsSync(paso.to) ? readFileSync(paso.to, "utf8") : ""
      let undo
      if(paso.restaurar) {
        const prefix=normalizarTabla(paso.tabla), target=`${prefix}.${normalizarTabla(paso.clave)}`
        const hits=rutasToml(previo).filter(e=>e.ruta===target)
        if(hits.length>1) throw new Error("ambiguous owned TOML key")
        const old=(manPrevio?.registro || []).find(e=>e["toml-set"]===paso.to && e.tabla===paso.tabla && e.clave===paso.clave)?.restaurar
        const wrote=typeof paso.valor==="string" ? JSON.stringify(paso.valor) : String(paso.valor)
        const tableExists=analizarToml(previo.split(/(?<=\n)/)).cabeceras.some(h=>h.nombre===prefix)
          || rutasToml(previo).some(e=>e.ruta===prefix || e.ruta.startsWith(`${prefix}.`))
        const tableOwned=registro.some(e=>e["toml-set"]===paso.to && e.tabla===paso.tabla && e.restaurar?.tablaCreada)
        undo=old && hits.length===1 && mismoValorToml(hits[0].valor,old.escrito) ? old
          : {escrito:wrote,previo:hits[0]?.valor ?? null,tablaCreada:!tableExists || tableOwned}
      }
      const nuevo = ponerToml(previo, paso.tabla, paso.clave, paso.valor, { fichero: rel(paso.to) })
      if (opts.dryRun) {
        say(`  ${ARROW} ${rel(paso.to)} ${dim(`([${paso.tabla}] ${paso.clave} = ${paso.valor})`)}`)
      } else if (nuevo !== previo) {
        escribirAtomico(paso.to, nuevo)
      }
      if (paso.deshacer !== false) registro.push({ "toml-set": paso.to, tabla: paso.tabla, clave: paso.clave,...(undo ? {restaurar:undo} : {}) })
      n += nuevo !== previo ? 1 : 0
    }
  }

  const pending = nativePending || roleMigrationPending
  guardar(pending ? "incompleto" : "completo",pending
    ? [nativePending ? 'registro/caché nativa pendientes' : '',roleMigrationPending ? 'migración de agentes pendiente; conflictos conservados' : ''].filter(Boolean).join('; ')
    : undefined)
  avisos.push(...drenarAvisosEscritura())
  return { n, avisos }
  }
}

const rel = (p) => {
  const r = relative(process.cwd(), p)
  return !r || r.startsWith("..") ? p : r
}

const primeraLinea = (s) => String(s || "").split("\n").map((l) => l.trim()).filter(Boolean)[0] || "sin salida"

// ---------------------------------------------------------------- comandos

async function cmdInstall(opts) {
  if (!["project", "user"].includes(opts.scope)) {
    console.error(`${ERR} --scope debe ser "project" o "user" (recibí "${opts.scope}")`)
    return 2
  }
  if (!["plugin", "copy"].includes(opts.modo)) {
    console.error(`${ERR} --mode debe ser "plugin" o "copy" (recibí "${opts.modo}")`)
    return 2
  }
  let ids = opts.providers
  if (!ids.length) {
    if (opts.yes || !process.stdin.isTTY) ids = detectados()
    else {
      const elegidos = await elegirProveedores()
      if (elegidos.cancelado) {
        say(`\n  ${WARN} cancelado: no se ha escrito nada.\n`)
        return 0
      }
      if (elegidos.vacio) {
        say(`\n  ${WARN} no has marcado ninguno: no se ha escrito nada.` +
            ` ${dim("(espacio marca, a los marca todos)")}\n`)
        return 0
      }
      ids = elegidos.ids
    }
    if (!ids.length) {
      console.error(`${ERR} no he detectado ningún proveedor y no me has dicho ninguno.\n` +
                    `   Usa: --provider ${IDS.join("|")} (o --all)`)
      return 2
    }
  }
  const malos = ids.filter((i) => !IDS.includes(i))
  if (malos.length) {
    console.error(`${ERR} proveedor desconocido: ${malos.join(", ")}\n   Soportados: ${IDS.join(", ")}`)
    return 2
  }

  say(`\n${bold("custom-agents")} ${dim("v" + VERSION)} ${ARROW} ${ids.map(cyan).join(", ")}` +
      `  ${dim(`[${opts.scope}${opts.scope === "project" ? ": " + rel(opts.dir) : ""}]`)}` +
      (opts.dryRun ? `  ${yellow("(dry-run: no se escribe nada)")}` : ""))

  let fallos = 0
  const hechos = []
  for (const id of ids) {
    const p = getProvider(id)
    say(`\n${bold(p.label)} ${dim("— " + p.blurb)}`)
    try {
      // DENTRO del try: un manifiesto de copy viejo o ilegible no puede tumbar el run entero
      // (y con él la instalación de los demás proveedores) con un stack crudo.
      migrarDeCopy(p, opts)
      const { n, avisos } = ejecutar(p, opts)
      for (const a of avisos) say(`  ${WARN} ${dim(a)}`)
      say(`  ${OK} ${n} paso(s) ${opts.dryRun ? "se aplicarían" : "aplicados"} en ${cyan(rel(p.destino(opts.scope, opts.dir, opts.modo)))}`)
      hechos.push(p)
    } catch (e) {
      fallos++
      console.error(`  ${ERR} ${p.label}: ${e.message}`)
    }
  }

  if (!opts.dryRun && hechos.length) {
    say(`\n${bold("Siguiente paso")}`)
    for (const p of hechos) {
      say(`  ${cyan(p.label)}: ${texto(p.restart, opts)}`)
      const h = texto(p.hint, opts)
      if (h) say(`             ${dim(h)}`)
    }
    say(`\n  ${dim("Comprueba la instalación con")} /doctor ${dim("· documentación:")} docs/INTEROP.md`)
  }
  say("")
  return fallos ? 1 : 0
}

/**
 * Instalar como PLUGIN encima de un `--mode copy` anterior es la ruta de actualización de todo el
 * que usó el instalador viejo. Los ficheros del copy no los toca nadie más: si no se limpian aquí,
 * se quedan 222 huérfanos en `.claude/` que ya no figuran en ningún manifiesto. Con `-y` se limpian
 * (es lo que ha pedido el usuario: «instálamelo bien»); sin `-y`, se avisa con el comando.
 */
function migrarDeCopy(p, opts) {
  if (opts.dryRun || opts.modo !== "plugin" || typeof p.manifiesto !== "function") return
  const dest = p.destino(opts.scope, opts.dir, "copy")
  const file = manifiestoDe(p, "copy")
  if (file === manifiestoDe(p, "plugin")) return
  const ruta = join(dest, file)
  if (!existsSync(ruta)) return
  const man = leerJson(ruta)
  // Un manifiesto ilegible (o sin `files`: instalador viejo, escritura a medias) NO es una excusa
  // para reventar el run entero. Se dice lo que pasa y DÓNDE, y se sigue: lo que haya en `.claude/`
  // se queda, pero el usuario sabe que está ahí y que lo tiene que limpiar él.
  if (!man || !Array.isArray(man.files)) {
    say(`  ${WARN} ${dim(`${rel(ruta)} existe pero no puedo leerlo (${man ? "no tiene `files`" : "no es JSON válido"}): ` +
        `sigo con la instalación, pero el bundle copiado que haya en ${rel(dest)} se queda ahí ` +
        `— límpialo a mano (o borra ese fichero y reinstala con -y)`)}`)
    return
  }
  const cmd = `npx @daycry/custom-agents uninstall -p ${p.id} --scope ${opts.scope}` +
              (opts.scope === "project" ? ` --dir ${rel(opts.dir)}` : "")
  if (!opts.yes) {
    say(`  ${WARN} ${dim(`aquí ya hay un bundle copiado (v${man.version}, ${man.files.length} fichero(s)). ` +
        `No lo borro sin que me lo digas: repite con -y, o límpialo con \`${cmd}\``)}`)
    return
  }
  // `-y` no es «bórrame lo que quieras»: un fichero del bundle que el usuario haya EDITADO no se
  // toca (el modo plugin no lo repone y el cambio se perdería sin que se entere).
  const tocados = man.files.filter((f) => modificado(dest, f))
  const limpiables = man.files.filter((f) => !tocados.includes(f))
  say(`  ${WARN} ${dim(`había un bundle copiado (v${man.version}): lo quito antes de instalar el plugin`)}`)
  if (tocados.length) {
    say(`  ${WARN} ${dim(`tienes cambios locales en ${tocados.length} fichero(s): los dejo en ${rel(dest)} ` +
        `(${tocados.slice(0, 3).map((f) => rel(f.split("/").join(sep))).join(", ")}` +
        `${tocados.length > 3 ? ", …" : ""})`)}`)
  }
  deshacerInstalacion(p, dest, file, { ...man, files: limpiables }, opts)
}

/** ¿Este fichero instalado difiere del que trae el paquete? (tamaño y, si empata, contenido). */
function modificado(dest, fichero) {
  const abs = fichero.split("/").join(sep)
  if (!existsSync(abs)) return false                     // ya no está: nada que conservar
  const origen = join(ROOT, relative(dest, abs))
  if (!existsSync(origen)) return false                  // de una versión anterior: es nuestro
  try {
    if (statSync(abs).size !== statSync(origen).size) return true
    return sha1(abs) !== sha1(origen)
  } catch { return true }                                // ante la duda, NO se borra
}

const sha1 = (p) => createHash("sha1").update(readFileSync(p)).digest("hex")

/** Manifiestos de este proveedor que existen de verdad: `{ dest, file, man }`. */
function manifiestosVivos(p, scope, dir) {
  const out = []
  for (const { dest, file } of sitiosManifiesto(p, scope, dir)) {
    const man = leerJson(join(dest, file))
    if (man) out.push({ dest, file, man })
  }
  return out
}

/** Deshace UNA instalación (un manifiesto). Devuelve cuántos ficheros ha borrado. */
function deshacerInstalacion(p, dest, file, man, opts) {
  // Un manifiesto sin `files` (viejo o a medio escribir) se deshace igual: sus apuntes de
  // configuración SÍ se pueden quitar y el fichero se retira. Nunca un `TypeError`.
  const files = Array.isArray(man.files) ? man.files : []
  say(`\n${bold(p.label)} ${dim(`(v${man.version}, ${man.scope}${man.modo ? ", " + man.modo : ""}` +
      `${man.estado ? ", " + man.estado : ""})`)}`)
  if (opts.dryRun) {
    say(`  ${ARROW} borraría ${files.length} fichero(s) bajo ${rel(dest)}` +
        (man.registro?.length ? ` y desharía ${man.registro.length} apunte(s) de configuración` : ""))
    return 0
  }
  let n = 0
  for (const f of files) {
    const abs = f.split("/").join(sep)
    if (man.nativeAgents && Object.hasOwn(man.nativeAgents,f)) {
      const agentRoot = p.id === 'codex' ? join(dirname(dirname(dest)),'agents') : join(dest,'agents')
      try {
        if (retirarArtefacto({to:abs,sha256:[man.nativeAgents[f]]},agentRoot)) n++
        else say(`  ${WARN} ${dim(`${rel(abs)}: agente modificado, conservado`)}`)
      } catch { say(`  ${WARN} ${dim(`${rel(abs)}: propiedad/ruta no verificable, conservado`)}`) }
      continue
    }
    try { if (existsSync(abs)) { rmSync(abs, { force: true }); n++ } } catch { /* sigue */ }
  }
  for (const a of deshacerRegistro(man.registro || [])) say(`  ${WARN} ${dim(a)}`)
  try { rmSync(join(dest, file), { force: true }) } catch { /* sigue */ }
  podarVacios(dest, files)
  say(`  ${OK} ${n} fichero(s) borrado(s). ${dim("La configuración fusionada (opencode.json, marketplace.json) NO se toca: es tuya.")}`)
  const nota = typeof p.notaDesinstalar === "function"
    ? p.notaDesinstalar(opts.scope, opts.dir)
    : p.notaDesinstalar
  if (nota) say(`  ${WARN} ${dim(nota)}`)
  return n
}

function cmdUninstall(opts) {
  const ids = opts.providers.length ? opts.providers : IDS
  let tocados = 0
  for (const id of ids) {
    const p = getProvider(id)
    if (!p) continue
    for (const { dest, file, man } of manifiestosVivos(p, opts.scope, opts.dir)) {
      tocados++
      deshacerInstalacion(p, dest, file, man, opts)
    }
  }
  if (!tocados) {
    console.error(`${ERR} no encuentro ningún manifiesto de instalación (${MANIFIESTOS.join(" / ")}).\n` +
                  `   ¿Instalaste con otro --scope o --dir?`)
    return 1
  }
  say("")
  return 0
}

/**
 * Deshace los apuntes de configuración del manifiesto: las claves JSON que puso (y solo esas,
 * sin borrar nunca el fichero), las claves TOML (a `false`, sin borrar la tabla) y el comando
 * inverso de la CLI si el paso declaró uno. Devuelve los avisos.
 */
function deshacerRegistro(registro) {
  const avisos = []
  for (const e of registro) {
    if (e["json-set"]) {
      let leido
      try { leido = leerJsonEstricto(e["json-set"]) } catch (err) {
        avisos.push(`${rel(e["json-set"])}: ${err.message} — quita a mano ${(e.claves || []).join(", ")}`)
        continue
      }
      if (!leido.existe) continue
      const actual = leido.valor
      for (const k of e.claves || []) quitarRuta(actual, k)
      // Los objetos que creó ESTE paso y se han quedado vacíos se van con él (de dentro afuera).
      for (const ruta of [...(e.padresCreados || [])].sort((a, b) => b.split(".").length - a.split(".").length)) {
        const v = leerRuta(actual, ruta)
        if (v && typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0) quitarRuta(actual, ruta)
      }
      // Si el fichero lo creó el instalador y ya no queda nada nuestro dentro, se borra: un
      // `known_marketplaces.json` vacío que el usuario nunca tuvo es basura, no configuración.
      const restantes = Object.keys(actual).filter((k) => !(e.noQuitar || []).includes(k))
      if (e.creado && restantes.length === 0) {
        try { rmSync(e["json-set"], { force: true }) } catch { /* sigue */ }
        continue
      }
      escribirJson(e["json-set"], actual, leido.bom)
    } else if (e["toml-set"]) {
      if (!existsSync(e["toml-set"])) continue
      const previo = readFileSync(e["toml-set"], "utf8")
      // `soloSiExiste`: si el usuario ya borró la tabla, desinstalar NO se la vuelve a crear.
      let nuevo
      try {
        nuevo = e.restaurar ? restaurarClaveToml(previo,e.tabla,e.clave,e.restaurar)
          : ponerToml(previo, e.tabla, e.clave, false,{ soloSiExiste: true, fichero: rel(e["toml-set"]) })
      } catch (err) {
        avisos.push(err.message)
        continue
      }
      if (nuevo !== previo) escribirAtomico(e["toml-set"], nuevo)
    } else if (e.deshacer) {
      const [cmd, ...args] = e.deshacer
      if (!enPath(cmd)) { avisos.push(`${cmd} no está en el PATH — ejecuta: ${e.deshacer.join(" ")}`); continue }
      try { correr(cmd, args) } catch (err) { avisos.push(`${e.deshacer.join(" ")}: ${primeraLinea(salidaDe(err))}`) }
    }
  }
  avisos.push(...drenarAvisosEscritura())
  return avisos
}

/**
 * Borra los directorios que NUESTROS ficheros han dejado vacíos, de abajo arriba y parando en
 * `raiz` (que no se toca). Solo se miran los directorios PADRES de los ficheros del manifiesto:
 * barrer toda la raíz borraba directorios vacíos ajenos (`plugins/marketplaces/otro-mkt`,
 * `plugins/repos/`…), que es justo lo que el instalador promete no hacer.
 */
function podarVacios(raiz, ficheros = []) {
  const abs = ficheros.map((f) => resolve(f.split("/").join(sep)))
  const tope = resolve(raiz)
  const dentro = abs.filter((f) => f.startsWith(tope + sep))
  podarBajo(tope, dentro)
  // Y lo que se escribió FUERA de `dest`: en scope project + modo plugin, el manifiesto vive en
  // `<dir>/.claude` pero los ficheros están en `<CLAUDE_CONFIG_DIR>/plugins/…`, así que anclarse
  // solo en `dest` dejaba ~150 directorios vacíos. El tope es el PREFIJO COMÚN de esos ficheros
  // (nunca se sube por encima de él, ni se toca un directorio que no sea padre de los nuestros).
  const fuera = abs.filter((f) => !f.startsWith(tope + sep))
  if (fuera.length) podarBajo(prefijoComun(fuera.map(dirname)), fuera)
}

/** Directorio común más profundo de una lista de rutas absolutas (`null` si no hay uno seguro). */
export function prefijoComun(rutas) {
  if (!rutas.length) return null
  const partes = rutas.map((r) => r.split(sep))
  const base = partes[0]
  let i = 0
  while (i < base.length && partes.every((p) => p[i] === base[i])) i++
  // Menos de tres segmentos (`C:\algo`, `/home`) es demasiado arriba para andar borrando: se deja.
  return i >= 3 ? base.slice(0, i).join(sep) : null
}

function podarBajo(tope, ficheros) {
  if (!tope || !ficheros.length || !existsSync(tope)) return
  const candidatos = new Set()
  for (const f of ficheros) {
    let d = dirname(f)
    while (d !== tope && d.startsWith(tope + sep)) {
      candidatos.add(d)
      const padre = dirname(d)
      if (padre === d) break
      d = padre
    }
  }
  // De más profundo a menos: así un padre puede quedarse vacío cuando se van sus hijos.
  for (const d of [...candidatos].sort((a, b) => b.split(sep).length - a.split(sep).length)) {
    try { if (existsSync(d) && readdirSync(d).length === 0) rmdirSync(d) } catch { /* no vacío: se queda */ }
  }
}

/**
 * ¿Son la misma carpeta? (Windows no distingue mayúsculas; una ruta vacía, o un valor que no sea
 * cadena, no casa con nada.) Los enlaces se RESUELVEN (`realpathSync`: junction, `subst`,
 * symlink), con caída al valor sin resolver cuando la ruta todavía no existe — si no, la misma
 * carpeta vista por dos nombres no casaba con el `projectPath` grabado. Gemelo de `_misma_ruta`
 * en `agent-kits/shared/doctor.py`.
 */
export function mismaRuta(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || !a || !b) return false
  try {
    const real = (p) => { try { return realpathSync(resolve(p)) } catch { return resolve(p) } }
    const n = (p) => (process.platform === "win32" ? real(p).toLowerCase() : real(p))
    return n(a) === n(b)
  } catch { return false }
}

/**
 * Valor de UN descriptor: `true` (alta), `false` (apagado explícito), `"invalido"` (la clave está
 * con un valor que no es booleano) o `null` (no dice nada). Nunca lanza: un fichero del usuario
 * ilegible es «no dice nada», no un `status` roto.
 */
function valorRegistro(d) {
  if (!existsSync(d.fichero)) return null
  if (d.tipo === "toml-verdadero") {
    const hit = rutasToml(readFileSync(d.fichero, "utf8")).find((r) => r.ruta === normalizarTabla(d.ruta))
    if (!hit) return null
    if (hit.valor === "true") return true
    if (hit.valor === "false") return false
    return "invalido"
  }
  const datos = leerJson(d.fichero)
  if (!datos || typeof datos !== "object") return null
  const nodo = leerRuta(datos, d.ruta)
  if (d.tipo === "json-array") return Array.isArray(nodo) && nodo.includes(d.valor) ? true : null
  if (d.tipo === "json-instalados") {
    // `installed_plugins.json`: cada entrada trae SU scope, y una de scope `project` solo vale
    // para su `projectPath`. Un alta hecha desde otro proyecto no dice nada de esta carpeta.
    if (!nodo || typeof nodo !== "object") return null
    let entradas = nodo[d.clave]
    if (entradas && !Array.isArray(entradas)) entradas = [entradas]
    if (!Array.isArray(entradas)) return null
    // `local` es un scope de PROYECTO (`claude plugin install --scope local`): como `project`,
    // solo vale para su `projectPath`. Un scope que no sea ninguno de los tres documentados no
    // cuenta —caer a `user` era el lado permisivo: valía para todas las carpetas.
    const vale = entradas.some((e) => {
      const scope = e && typeof e.scope === "string" ? e.scope : ""
      if (!["user", "project", "local"].includes(scope)) return false
      return d.scope === "project"
        ? scope !== "user" && mismaRuta(e && e.projectPath, d.proyecto)
        : scope === "user"
    })
    return vale ? true : null
  }
  // `enabledPlugins`: SOLO `true` habilita. `false` es lo contrario de estar registrado y
  // cualquier otro valor (`0`, `null`, `"false"`) es un valor inválido, no un alta.
  if (!nodo || typeof nodo !== "object" || Array.isArray(nodo)) return null
  const entradas = Object.entries(nodo).filter(([k]) => (d.clave ? k === d.clave : k.startsWith(d.prefijo)))
  if (!entradas.length) return null
  if (entradas.some(([, v]) => v === false)) return false
  if (entradas.some(([, v]) => v === true)) return true
  return "invalido"
}

/**
 * ¿Tiene el runtime el plugin dado de alta DE VERDAD? Lee los descriptores que declara el
 * proveedor (`registro(scope, dir)`) sobre los ficheros que ese runtime lee al arrancar.
 *
 * Recorre **todos** los descriptores, no se para en el primero que acierta, y resuelve con la
 * misma regla que `estado_plugin()` en `agent-kits/shared/doctor.py`, para que `status` y
 * `/doctor` no puedan contradecirse sobre el mismo estado:
 *
 *   · manda el NIVEL más alto de los que se pronuncian (`nivel` del descriptor, por
 *     `PRECEDENCIA_SETTINGS`: managed > local > project > user — `settings#settings-precedence`);
 *   · dentro de ese nivel, un `false` explícito gana a cualquier alta;
 *   · sin pronunciamiento explícito, un alta (una entrada instalada) basta.
 *
 * Un descriptor sin `nivel` (Codex, OpenCode: un solo fichero por scope) se comporta como antes.
 * Informa, no decide: jamás lanza.
 *
 * Devuelve `{ registrado, donde, apagadoEn, invalidoEn }` (`donde` = fichero que lo prueba).
 */
export function leerRegistro(descriptores) {
  let alta = null
  let invalido = null
  const explicitos = []
  for (const d of descriptores || []) {
    let valor = null
    try { valor = valorRegistro(d) } catch { valor = null }
    if (valor === "invalido") { invalido = invalido || d.fichero; continue }
    if (valor !== true && valor !== false) continue
    // `installed_plugins.json` no habilita ni apaga: es un alta, no un pronunciamiento.
    if (d.tipo === "json-instalados") { if (valor === true) alta = alta || d.fichero; continue }
    explicitos.push({ nivel: d.nivel || "user", valor, fichero: d.fichero })
    if (valor === true) alta = alta || d.fichero
  }
  if (explicitos.length) {
    const nivel = PRECEDENCIA_SETTINGS.find((n) => explicitos.some((e) => e.nivel === n))
    const mandan = explicitos.filter((e) => e.nivel === nivel)
    const apagado = mandan.find((e) => e.valor === false)
    if (apagado) {
      return { registrado: false, donde: apagado.fichero, apagadoEn: apagado.fichero, invalidoEn: invalido }
    }
    return { registrado: true, donde: mandan[0].fichero, apagadoEn: null, invalidoEn: invalido }
  }
  return { registrado: !!alta, donde: alta, apagadoEn: null, invalidoEn: invalido }
}

function cmdStatus(opts) {
  say(`\n${bold("custom-agents")} ${dim("v" + VERSION)} — estado\n`)
  for (const p of PROVIDERS) {
    const filas = []
    for (const scope of ["project", "user"]) {
      const delScope = manifiestosVivos(p, scope, opts.dir).map(({ dest, man }) =>
        `${man.estado === "incompleto" ? WARN : OK} ${scope}${man.modo ? `/${man.modo}` : ""}: ` +
        `v${man.version}, ${(man.files || []).length} fichero(s) ${dim(rel(dest))}` +
        (man.estado === "incompleto" ? ` ${yellow("(instalación incompleta)")}` : ""))
      // Registration declarations and installer payload are separate. For Codex, the boolean
      // proves only a declaration in this scope; native cache state is queried below.
      const { registrado, donde, apagadoEn, invalidoEn } = leerRegistro(
        typeof p.registro === "function" ? p.registro(scope, opts.dir) : [])
      if (registrado || apagadoEn || invalidoEn || delScope.length) {
        const porQue = apagadoEn
          ? `— está dado de alta pero APAGADO en ${rel(apagadoEn)}: el runtime lo ignora`
          : invalidoEn
            ? `— la clave está en ${rel(invalidoEn)} con un valor que no habilita: no cuenta como alta`
            : p.id === "codex" ? "— sin declaración de activación en este scope" : "— el runtime no lo carga; falta darlo de alta"
        delScope.push(`${registrado ? OK : WARN} ${scope}: registrado: ${registrado ? "sí" : "no"}` +
          (registrado ? ` ${dim(rel(donde))}` : ` ${dim(porQue)}`))
      }
      filas.push(...delScope)
    }
    const det = p.detect()
    say(`  ${bold(p.label.padEnd(13))} ${det ? dim("runtime detectado") : dim("runtime no detectado")}`)
    for (const f of filas) say(`      ${f}`)
    if(p.id === "codex") {
      const native=queryCodexPlugin({cwd:opts.dir})
      const state=native.state==="installed" ? `instalado; habilitado: ${native.enabled ? "sí" : "no"}; v${native.version}`
        : native.state==="absent" ? "ausente" : "desconocido (consulta nativa no disponible)"
      say(`      ${dim(`estado nativo en Codex: ${state}`)}`)
    }
    if (!filas.length) say(`      ${dim("— sin instalar por este instalador")}`)
  }
  say(`\n  ${dim("Instala con:")} npx @daycry/custom-agents install -p <${IDS.join("|")}>\n`)
  return 0
}

function cmdList() {
  say(`\n${bold("Proveedores soportados")}\n`)
  for (const p of PROVIDERS) {
    say(`  ${cyan(p.id.padEnd(13))} ${p.label.padEnd(13)} ${dim(p.blurb)}`)
    say(`  ${" ".repeat(13)} ${dim(p.detect() ? "detectado en esta máquina" : "no detectado")}`)
  }
  say("")
  return 0
}

const detectados = () => PROVIDERS.filter((p) => p.detect()).map((p) => p.id)

// ---------------------------------------------------------------- selección interactiva

/** Estado inicial del multiselect: marcados los `pre`, cursor arriba. */
export const estadoInicial = (items, pre = []) => ({
  items: [...items],
  marcados: items.map((i) => pre.includes(i)),
  cursor: 0,
  fin: null,
})

/**
 * Reductor PURO del multiselect: (estado, tecla) → estado. Toda la lógica del menú vive aquí
 * para poder probarla sin terminal (la parte de terminal es solo pintar y leer teclas).
 */
export function reducirTecla(estado, tecla) {
  const n = estado.items.length
  const con = (extra) => ({ ...estado, ...extra })
  switch (tecla) {
    case "up": case "k": return con({ cursor: (estado.cursor - 1 + n) % n })
    case "down": case "j": return con({ cursor: (estado.cursor + 1) % n })
    case "space": {
      const marcados = [...estado.marcados]
      marcados[estado.cursor] = !marcados[estado.cursor]
      return con({ marcados })
    }
    case "a": return con({ marcados: estado.marcados.map(() => true) })
    case "i": return con({ marcados: estado.marcados.map((m) => !m) })
    case "return": return con({ fin: { sel: estado.items.filter((_, i) => estado.marcados[i]) } })
    case "escape": case "q": case "ctrl-c": return con({ fin: { cancelado: true } })
    default: return estado
  }
}

/** Traduce lo que da `readline` al vocabulario del reductor. */
export function nombreTecla(str, key) {
  if (key?.ctrl && key.name === "c") return "ctrl-c"
  if (str === " " || key?.name === "space") return "space"
  if (key?.name === "return" || key?.name === "enter") return "return"
  return key?.name || String(str || "")
}

const ESC = "\u001b"
const ANSI = /^\u001b\[[0-9;]*m/
const ANSI_G = /\u001b\[[0-9;]*m/g
const RESET = ESC + "[0m"

/**
 * Recorta un texto a `ancho` columnas VISIBLES, sin contar los códigos ANSI (que no ocupan sitio
 * en pantalla pero sí en `String.length`). Sin esto, en una terminal de 80 columnas cada fila del
 * menú ocupaba DOS líneas físicas y el repintado (que sube N líneas lógicas) descuadraba el menú
 * con cada tecla. Devuelve el texto con el reset final para no dejar color colgando.
 */
export function cortarAnsi(s, ancho) {
  if (!(ancho > 0)) return s
  const util = ancho - 1                      // una columna reservada para el «…»
  let visible = 0, out = "", i = 0, coloreado = false
  while (i < s.length) {
    if (s[i] === ESC) {
      const m = ANSI.exec(s.slice(i))
      if (m) { out += m[0]; coloreado = true; i += m[0].length; continue }
    }
    if (visible >= util && anchoVisible(s.slice(i)) > 1) return out + "…" + (coloreado ? RESET : "")
    if (visible >= ancho) return out + (coloreado ? RESET : "")
    out += s[i]
    visible++
    i++
  }
  return out
}

/** Columnas que ocupa en pantalla un texto con códigos ANSI (los códigos no ocupan ninguna). */
export const anchoVisible = (s) => String(s).replace(ANSI_G, "").length

/** Multiselect con checkboxes en modo raw. Resuelve `{ sel }` o `{ cancelado: true }`. */
function multiselect(items, pre) {
  const provs = items.map((id) => getProvider(id))
  const det = detectados()
  let estado = estadoInicial(items, pre)
  const out = process.stdout
  const stdin = process.stdin

  const linea = (p, i) => {
    const marca = estado.marcados[i] ? green("[x]") : "[ ]"
    const cursor = i === estado.cursor ? cyan(">") : " "
    // El relleno se calcula ANTES de colorear: los códigos ANSI cuentan como caracteres.
    const visto = det.includes(p.id)
    const etiqueta = (visto ? green : dim)((visto ? "detectado" : "no detectado").padEnd(13))
    return `${cursor} ${marca} ${bold(p.label.padEnd(13))} ${etiqueta} ${dim(p.blurb)}`
  }

  console.log(`\n${bold("¿En qué proveedores quieres instalar custom-agents?")}`)
  console.log(`${dim("  arriba/abajo (o j/k) mover · espacio marcar · a todos · i invertir · Enter confirmar · Esc cancelar")}\n`)

  return new Promise((res, rej) => {
    let pintadas = 0
    const pintar = () => {
      // Cada fila se recorta al ancho de la terminal: así una fila = una línea FÍSICA y el
      // `[NA` de la pasada siguiente sube exactamente las líneas que se imprimieron.
      const ancho = (out.columns || 100) - 1
      if (pintadas) out.write(`\u001b[${pintadas}A`)
      for (let i = 0; i < provs.length; i++) out.write(`\u001b[2K${cortarAnsi(linea(provs[i], i), ancho)}\n`)
      pintadas = provs.length
    }
    let limpio = false
    const limpiar = () => {
      if (limpio) return
      limpio = true
      process.removeListener("exit", limpiar)
      stdin.removeListener("keypress", onTecla)
      try { stdin.setRawMode(false) } catch { /* da igual: ya estaba */ }
      try { stdin.pause() } catch { /* idem */ }
      try { out.write("\u001b[?25h") } catch { /* el cursor vuelve SIEMPRE, salga esto como salga */ }
    }
    // Red de seguridad: si esto se va por donde no toca (un EPIPE al pintar, una excepción fuera
    // del listener, una señal), la terminal NO se queda en modo raw y sin cursor. `once` mas el
    // flag `limpio` lo hacen idempotente con la limpieza normal.
    process.once("exit", limpiar)
    const onTecla = (str, key) => {
      let fin = null
      try {
        estado = reducirTecla(estado, nombreTecla(str, key))
        pintar()
        fin = estado.fin
      } catch (e) {
        limpiar()
        rej(e)
        return
      } finally {
        if (fin) limpiar()
      }
      if (fin) res(fin)
    }
    try {
      out.write("\u001b[?25l")
      emitKeypressEvents(stdin)
      stdin.setRawMode(true)
      stdin.resume()
      stdin.on("keypress", onTecla)
      pintar()
    } catch (e) { limpiar(); rej(e) }
  })
}

/** Menú de respaldo sin modo raw: números separados por coma, Enter = la preselección. */
function preguntar(pre) {
  const rl = createInterface({ input: process.stdin, output: process.stdout })
  const det = detectados()
  console.log(`\n${bold("¿En qué proveedores quieres instalar custom-agents?")}\n`)
  PROVIDERS.forEach((p, i) => {
    const marca = det.includes(p.id) ? green("detectado") : dim("no detectado")
    console.log(`  ${bold(String(i + 1))}) ${p.label.padEnd(13)} ${marca}  ${dim(p.blurb)}`)
  })
  const pordefecto = pre.length ? pre.join(", ") : "ninguno"
  return new Promise((res) => {
    rl.question(`\nNúmeros separados por coma, "a" para todos ${dim(`[Enter = ${pordefecto}]`)}: `, (resp) => {
      rl.close()
      const t = resp.trim().toLowerCase()
      if (!t) return res(pre)
      if (t === "a" || t === "all") return res([...IDS])
      const sel = t.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => n >= 1 && n <= PROVIDERS.length)
      res([...new Set(sel.map((n) => PROVIDERS[n - 1].id))])
    })
  })
}

/** Preselección: lo detectado MÁS Claude Code, que es el runtime nativo del plugin. */
async function elegirProveedores() {
  const pre = [...new Set([...detectados(), "claude-code"])]
  if (!process.stdin.isTTY || typeof process.stdin.setRawMode !== "function") {
    return { ids: await preguntar(pre) }
  }
  return resultadoSeleccion(await multiselect([...IDS], pre))
}

/**
 * Traduce lo que devuelve el multiselect a lo que entiende `cmdInstall`. Enter sin marcar nada es
 * una DECISIÓN del usuario, no «no he detectado ningún proveedor»: se distingue para no soltarle
 * un error de uso (exit 2) por haber dicho que no a todo.
 */
export function resultadoSeleccion(fin) {
  if (fin?.cancelado) return { cancelado: true }
  const sel = fin?.sel || []
  return sel.length ? { ids: sel } : { vacio: true, ids: [] }
}

// ---------------------------------------------------------------- main

async function main() {
  const opts = parseArgs(process.argv.slice(2))
  QUIET = Boolean(opts.quiet)   // `parseArgs` es puro: el efecto se aplica aquí
  switch (opts.cmd) {
    case "help": ayuda(); return 0
    case "version": console.log(VERSION); return 0
    case "unknown": console.error(`${ERR} opción desconocida: ${opts.bad}\n   Prueba: --help`); return 2
    case "install": banner(); return cmdInstall(opts)
    case "uninstall": case "remove": banner(); return cmdUninstall(opts)
    case "status": return cmdStatus(opts)
    case "list": case "providers": return cmdList()
    default:
      console.error(`${ERR} comando desconocido: ${opts.cmd}\n   Comandos: install, uninstall, status, list`)
      return 2
  }
}

// Importado por los tests → no ejecuta nada. Ejecutado como CLI → corre.
if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  main().then((code) => process.exit(code)).catch((e) => {
    console.error(`${ERR} ${e?.stack || e}`)
    process.exit(1)
  })
}

export { parseArgs, ficherosDe, ejecutar, main, banner, multiselect }
