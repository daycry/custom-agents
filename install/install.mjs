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
//     que reinstalar sirva para actualizar.
//   · DESINSTALABLE — cada instalación deja un manifiesto con la lista EXACTA de lo que escribió;
//     `uninstall` borra eso y nada más (nunca un `rm -rf` de una carpeta que no creó él).
//   · DEGRADA, NO BLOQUEA — un proveedor que falla no impide instalar los demás; el exit code
//     lo refleja al final.

import { readFileSync, writeFileSync, existsSync, mkdirSync, cpSync, statSync, rmSync, readdirSync, rmdirSync } from "node:fs"
import { dirname, join, resolve, relative, sep } from "node:path"
import { fileURLToPath } from "node:url"
import { createInterface } from "node:readline"
import { PROVIDERS, IDS, getProvider, buildPlan, MANIFEST } from "./providers.mjs"

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

function ayuda() {
  console.log(`
${bold("custom-agents")} ${dim("v" + VERSION)} — ciclo SDD presupuestado para agentes de código

${bold("USO")}
  npx @daycry/custom-agents [comando] [opciones]

${bold("COMANDOS")}
  install       Instala en uno o varios proveedores (por defecto)
  uninstall     Desinstala usando el manifiesto de la instalación
  status        Qué hay instalado y dónde
  list          Proveedores soportados

${bold("OPCIONES")}
  -p, --provider <ids>   ${IDS.join(", ")} (separados por coma) o "all"
      --all              Todos los proveedores soportados
      --scope <ámbito>   project (por defecto) | user
      --dir <ruta>       Proyecto destino (por defecto, el directorio actual)
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

Documentación: ${cyan("docs/INTEROP.md")} · ${cyan(PKG.homepage || "https://github.com/daycry/custom-agents")}
`)
}

// ---------------------------------------------------------------- argumentos

function parseArgs(argv) {
  const o = { cmd: null, providers: [], scope: "project", dir: process.cwd(), dryRun: false, yes: false, quiet: false }
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
  try { return JSON.parse(readFileSync(p, "utf8")) } catch { return null }
}

function escribirJson(p, obj) {
  mkdirSync(dirname(p), { recursive: true })
  writeFileSync(p, JSON.stringify(obj, null, 2) + "\n", "utf8")
}

/** Fusión conservadora: lo que ya existe MANDA. Devuelve [resultado, claves añadidas]. */
export function fusionar(actual, nuevo) {
  const anadidas = []
  const walk = (dst, src, ruta) => {
    for (const [k, v] of Object.entries(src)) {
      const q = ruta ? `${ruta}.${k}` : k
      if (Array.isArray(v)) {
        const prev = Array.isArray(dst[k]) ? dst[k] : []
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

// ---------------------------------------------------------------- ejecución de un plan

function ejecutar(provider, opts) {
  const plan = buildPlan(provider, { root: ROOT, dir: opts.dir, scope: opts.scope, version: VERSION })
  const escritos = []
  const avisos = []
  let n = 0

  for (const paso of plan) {
    if (paso.type === "copy") {
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
        mkdirSync(dirname(paso.to), { recursive: true })
        cpSync(abs, paso.to, {
          recursive: true,
          force: true,
          filter: (src) => !src.includes(`${sep}__pycache__`) && !src.endsWith(".pyc"),
        })
      }
      escritos.push(...destinos)
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
      const [fusionado, anadidas] = fusionar(actual, aFusionar)
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
    }
  }

  if (!opts.dryRun) {
    escribirJson(join(provider.destino(opts.scope, opts.dir), MANIFEST), {
      plugin: "custom-agents",
      version: VERSION,
      provider: provider.id,
      scope: opts.scope,
      installedAt: new Date().toISOString(),
      files: escritos.map((f) => f.split(sep).join("/")).sort(),
    })
  }
  return { n, avisos }
}

const rel = (p) => {
  const r = relative(process.cwd(), p)
  return !r || r.startsWith("..") ? p : r
}

// ---------------------------------------------------------------- comandos

async function cmdInstall(opts) {
  if (!["project", "user"].includes(opts.scope)) {
    console.error(`${ERR} --scope debe ser "project" o "user" (recibí "${opts.scope}")`)
    return 2
  }
  let ids = opts.providers
  if (!ids.length) {
    ids = opts.yes || !process.stdin.isTTY ? detectados() : await preguntar()
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
      const { n, avisos } = ejecutar(p, opts)
      for (const a of avisos) say(`  ${WARN} ${dim(a)}`)
      say(`  ${OK} ${n} fichero(s) ${opts.dryRun ? "se escribirían" : "instalados"} en ${cyan(rel(p.destino(opts.scope, opts.dir)))}`)
      hechos.push(p)
    } catch (e) {
      fallos++
      console.error(`  ${ERR} ${p.label}: ${e.message}`)
    }
  }

  if (!opts.dryRun && hechos.length) {
    say(`\n${bold("Siguiente paso")}`)
    for (const p of hechos) {
      say(`  ${cyan(p.label)}: ${p.restart}`)
      if (p.hint) say(`             ${dim(p.hint)}`)
    }
    say(`\n  ${dim("Comprueba la instalación con")} /doctor ${dim("· documentación:")} docs/INTEROP.md`)
  }
  say("")
  return fallos ? 1 : 0
}

function cmdUninstall(opts) {
  const ids = opts.providers.length ? opts.providers : IDS
  let tocados = 0
  for (const id of ids) {
    const p = getProvider(id)
    if (!p) continue
    const dest = p.destino(opts.scope, opts.dir)
    const man = leerJson(join(dest, MANIFEST))
    if (!man) continue
    tocados++
    say(`\n${bold(p.label)} ${dim(`(v${man.version}, ${man.scope})`)}`)
    if (opts.dryRun) {
      say(`  ${ARROW} borraría ${man.files.length} fichero(s) bajo ${rel(dest)}`)
      continue
    }
    let n = 0
    for (const f of man.files) {
      const abs = f.split("/").join(sep)
      try { if (existsSync(abs)) { rmSync(abs, { force: true }); n++ } } catch { /* sigue */ }
    }
    try { rmSync(join(dest, MANIFEST), { force: true }) } catch { /* sigue */ }
    podarVacios(dest)
    say(`  ${OK} ${n} fichero(s) borrado(s). ${dim("La configuración fusionada (opencode.json, marketplace.json) NO se toca: es tuya.")}`)
  }
  if (!tocados) {
    console.error(`${ERR} no encuentro ningún manifiesto de instalación (${MANIFEST}).\n` +
                  `   ¿Instalaste con otro --scope o --dir?`)
    return 1
  }
  say("")
  return 0
}

/** Borra los directorios que se han quedado vacíos, de abajo arriba. Nunca borra con contenido. */
function podarVacios(raiz) {
  if (!existsSync(raiz)) return
  const walk = (d) => {
    let entradas
    try { entradas = readdirSync(d, { withFileTypes: true }) } catch { return }
    for (const e of entradas) if (e.isDirectory()) walk(join(d, e.name))
    try { if (readdirSync(d).length === 0) rmdirSync(d) } catch { /* no vacío: se queda */ }
  }
  walk(raiz)
}

function cmdStatus(opts) {
  say(`\n${bold("custom-agents")} ${dim("v" + VERSION)} — estado\n`)
  for (const p of PROVIDERS) {
    const filas = []
    for (const scope of ["project", "user"]) {
      const dest = p.destino(scope, opts.dir)
      const man = leerJson(join(dest, MANIFEST))
      if (man) filas.push(`${OK} ${scope}: v${man.version}, ${man.files.length} fichero(s) ${dim(rel(dest))}`)
    }
    const det = p.detect()
    say(`  ${bold(p.label.padEnd(13))} ${det ? dim("runtime detectado") : dim("runtime no detectado")}`)
    for (const f of filas) say(`      ${f}`)
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

/** Menú multi-selección sin dependencias: números separados por coma, Enter = los detectados. */
function preguntar() {
  const rl = createInterface({ input: process.stdin, output: process.stdout })
  const det = detectados()
  console.log(`\n${bold("¿En qué proveedores quieres instalar custom-agents?")}\n`)
  PROVIDERS.forEach((p, i) => {
    const marca = det.includes(p.id) ? green("detectado") : dim("no detectado")
    console.log(`  ${bold(String(i + 1))}) ${p.label.padEnd(13)} ${marca}  ${dim(p.blurb)}`)
  })
  const pordefecto = det.length ? det.join(", ") : "ninguno"
  return new Promise((res) => {
    rl.question(`\nNúmeros separados por coma, "a" para todos ${dim(`[Enter = ${pordefecto}]`)}: `, (resp) => {
      rl.close()
      const t = resp.trim().toLowerCase()
      if (!t) return res(det)
      if (t === "a" || t === "all") return res([...IDS])
      const sel = t.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => n >= 1 && n <= PROVIDERS.length)
      res([...new Set(sel.map((n) => PROVIDERS[n - 1].id))])
    })
  })
}

// ---------------------------------------------------------------- main

async function main() {
  const opts = parseArgs(process.argv.slice(2))
  QUIET = Boolean(opts.quiet)   // `parseArgs` es puro: el efecto se aplica aquí
  switch (opts.cmd) {
    case "help": ayuda(); return 0
    case "version": console.log(VERSION); return 0
    case "unknown": console.error(`${ERR} opción desconocida: ${opts.bad}\n   Prueba: --help`); return 2
    case "install": return cmdInstall(opts)
    case "uninstall": case "remove": return cmdUninstall(opts)
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

export { parseArgs, ficherosDe, ejecutar, main }
