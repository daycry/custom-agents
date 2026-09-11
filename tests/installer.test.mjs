// installer.test.mjs — suite del instalador multi-proveedor (`install/install.mjs`).
// Runner nativo de Node, cero dependencias:  node --test tests/installer.test.mjs
//
// Lo que se prueba es lo que puede estropear el equipo de alguien:
//   · el PLAN de cada proveedor apunta donde dice la doc de ese runtime;
//   · la fusión de configuración NO pisa lo del usuario (ni le abre un permiso que había cerrado);
//   · instalar dos veces no duplica nada (idempotencia);
//   · desinstalar borra EXACTAMENTE lo que se instaló y ni un fichero ajeno.

import { test } from "node:test"
import assert from "node:assert/strict"
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync, chmodSync } from "node:fs"
import { tmpdir, homedir } from "node:os"
import { join, dirname, resolve, delimiter } from "node:path"
import { fileURLToPath } from "node:url"
import { execFileSync } from "node:child_process"

import {
  parseArgs, fusionar, ficherosDe, leerRegistro, mismaRuta,
  estadoInicial, reducirTecla, nombreTecla, ponerToml, versionSuficiente,
} from "../install/install.mjs"
import {
  PROVIDERS, IDS, getProvider, buildPlan, MANIFEST, GLOBAL_DIR, PAYLOAD_CLAUDE,
  ADAPTADOR_OPENCODE, rutaPluginOpencode,
} from "../install/providers.mjs"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const CLI = join(ROOT, "install", "install.mjs")

const tmpProj = () => mkdtempSync(join(tmpdir(), "ca-install-"))
const cli = (args, opts = {}) =>
  execFileSync(process.execPath, [CLI, ...args], { encoding: "utf8", env: { ...process.env, NO_COLOR: "1" }, ...opts })

const VERSION = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")).version

/** PATH sin ninguna CLI de runtime, pero con lo justo para que `where`/`which` sigan funcionando. */
const SIN_CLI = [tmpdir(), process.platform === "win32"
  ? join(process.env.SystemRoot || "C:\\Windows", "System32")
  : "/usr/bin"].join(delimiter)

/**
 * `env` del proceso hijo con un PATH controlado. En Windows la variable puede venir como `Path`:
 * se quita cualquier variante antes de poner la nuestra. Ningún test toca el HOME real.
 */
const conPath = (ruta, extra = {}) => ({
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^path$/i.test(k))),
  NO_COLOR: "1",
  PATH: ruta,
  ...extra,
})

/** Un `codex` de mentira: contesta a `--version` y apunta en un log lo que le piden. */
function codexFalso(bin) {
  if (process.platform === "win32") {
    writeFileSync(join(bin, "codex.cmd"), [
      "@echo off",
      "if \"%~1\"==\"--version\" goto ver",
      "echo %* >> \"%CODEX_FAKE_LOG%\"",
      "echo marketplace added",
      "exit /b 0",
      ":ver",
      "echo codex-cli 0.130.0",
      "exit /b 0",
      "",
    ].join("\r\n"))
  } else {
    const p = join(bin, "codex")
    writeFileSync(p, [
      "#!/bin/sh",
      "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli 0.130.0'; exit 0; fi",
      "echo \"$@\" >> \"$CODEX_FAKE_LOG\"",
      "echo 'marketplace added'",
      "",
    ].join("\n"))
    chmodSync(p, 0o755)
  }
}

/**
 * Un `claude` de mentira que hace lo que hace la CLI real con `plugin install --scope project`:
 * grabar en `installed_plugins.json` el proyecto que ve, que es **su directorio de trabajo** (la
 * CLI no recibe ninguna ruta). Sirve para afirmar que el instalador la lanza EN `--dir`.
 */
function claudeFalso(bin) {
  const NL = "\n"
  const js = join(bin, "claude-falso.mjs")
  writeFileSync(js, [
    'import { writeFileSync, mkdirSync } from "node:fs"',
    'import { join, resolve } from "node:path"',
    'const args = process.argv.slice(2)',
    'if (args[0] === "--version") { console.log("1.2.3 (Claude Code)"); process.exit(0) }',
    'if (args[1] === "install") {',
    '  const cfg = process.env.CLAUDE_CONFIG_DIR',
    '  mkdirSync(join(cfg, "plugins"), { recursive: true })',
    '  writeFileSync(join(cfg, "plugins", "installed_plugins.json"), JSON.stringify(',
    '    { version: 2, plugins: { "custom-agents@daycry": [',
    '      { scope: "project", projectPath: resolve(process.cwd()), version: "9.9.9" }] } }))',
    '}',
    'console.log("ok")',
    "",
  ].join(NL))
  if (process.platform === "win32") {
    writeFileSync(join(bin, "claude.cmd"),
      ["@echo off", `"${process.execPath}" "${js}" %*`, ""].join("\r\n"))
  } else {
    const p = join(bin, "claude")
    writeFileSync(p, ["#!/bin/sh", `exec "${process.execPath}" "${js}" "$@"`, ""].join(NL))
    chmodSync(p, 0o755)
  }
}

// ------------------------------------------------------------------ argumentos

test("parseArgs: proveedores por coma, alias --ide y --all", () => {
  assert.deepEqual(parseArgs(["install", "-p", "codex,opencode"]).providers, ["codex", "opencode"])
  assert.deepEqual(parseArgs(["install", "--ide", "codex"]).providers, ["codex"])
  assert.deepEqual(parseArgs(["install", "--all"]).providers, IDS)
  assert.equal(parseArgs([]).cmd, "install", "sin comando, instala")
  assert.equal(parseArgs(["status"]).cmd, "status")
})

test("parseArgs: defaults y opción desconocida", () => {
  const o = parseArgs(["install"])
  assert.equal(o.scope, "project")
  assert.equal(o.dryRun, false)
  assert.equal(parseArgs(["--nope"]).cmd, "unknown")
  assert.equal(parseArgs(["-h"]).cmd, "help")
})

// ------------------------------------------------------------------ fusión de config

test("fusionar: lo que ya existe MANDA", () => {
  const [out, add] = fusionar({ model: "mio", permission: { bash: "ask" } },
                              { model: "nuestro", permission: { bash: "allow", skill: "allow" } })
  assert.equal(out.model, "mio", "no pisa un escalar del usuario")
  assert.equal(out.permission.bash, "ask")
  assert.equal(out.permission.skill, "allow", "sí añade lo que falta")
  assert.ok(add.includes("permission.skill"))
})

test("fusionar: arrays se unen sin duplicar", () => {
  const [out] = fusionar({ instructions: ["A.md", "B.md"] }, { instructions: ["B.md", "C.md"] })
  assert.deepEqual(out.instructions, ["A.md", "B.md", "C.md"])
  const [out2, add2] = fusionar({ instructions: ["A.md"] }, { instructions: ["A.md"] })
  assert.deepEqual(out2.instructions, ["A.md"])
  assert.deepEqual(add2, [], "sin cambios → no reporta claves añadidas")
})

test("fusionar: no muta la entrada", () => {
  const orig = { a: 1, sub: { b: 2 } }
  fusionar(orig, { c: 3, sub: { d: 4 } })
  assert.deepEqual(orig, { a: 1, sub: { b: 2 } })
})

// ------------------------------------------------------------------ planes

test("cada proveedor declara lo mínimo y produce un plan no vacío", () => {
  for (const p of PROVIDERS) {
    assert.ok(p.id && p.label && p.blurb && p.restart, `${p.id}: metadatos incompletos`)
    assert.equal(typeof p.detect, "function")
    const plan = buildPlan(p, { root: ROOT, dir: "/proy", scope: "project", version: "9.9.9" })
    assert.ok(plan.length, `${p.id}: plan vacío`)
    for (const paso of plan) {
      assert.ok(["copy", "merge", "write", "exec", "json-set", "toml-set"].includes(paso.type),
        `${p.id}: paso raro ${paso.type}`)
      if (paso.type === "exec") assert.ok(paso.cmd && Array.isArray(paso.args), `${p.id}: exec sin comando`)
      else assert.ok(paso.to, `${p.id}: paso sin destino`)
      if (paso.type === "copy") assert.ok(existsSync(join(ROOT, paso.from)), `${p.id}: falta ${paso.from}`)
    }
  }
})

test("Codex: agentes en .codex/agents, prompts en CODEX_HOME y marketplace con policy", () => {
  const plan = buildPlan(getProvider("codex"), { root: ROOT, dir: join("/proy"), scope: "project", version: "9.9.9" })
  const agentes = plan.find((s) => s.from === "interop/codex/agents")
  assert.match(agentes.to, /[\\/]\.codex[\\/]agents$/)
  const prompts = plan.find((s) => s.from === "interop/codex/prompts")
  assert.ok(prompts.to.startsWith(GLOBAL_DIR.codex), "los prompts SOLO viven en CODEX_HOME")
  assert.ok(prompts.aviso, "salir del proyecto tiene que avisarse")
  const mkt = plan.find((s) => s.type === "merge")
  assert.equal(mkt.merge.plugins[0].policy.installation, "AVAILABLE")
  assert.match(mkt.merge.plugins[0].source.path, /^\.\//, "source.path relativo a la raíz del marketplace")
})

test("OpenCode: config en la raíz del proyecto y permission en onlyIfMissing", () => {
  const plan = buildPlan(getProvider("opencode"), { root: ROOT, dir: join("/proy"), scope: "project", version: "9.9.9" })
  const merge = plan.find((s) => s.type === "merge")
  assert.match(merge.to, /[\\/]opencode\.json$/)
  assert.ok(!merge.to.includes(".opencode"), "el config de proyecto va en la RAÍZ, no en .opencode/")
  assert.deepEqual(merge.onlyIfMissing, ["permission"],
    "permission no se puede fusionar: en OpenCode gana la última regla que casa")
  assert.ok(merge.merge.instructions.some((i) => i.includes("custom-agents-index")))
})

test("OpenCode: el adaptador se REGISTRA en `plugin` con la ruta que resuelve al fichero copiado", () => {
  for (const scope of ["project", "user"]) {
    const plan = buildPlan(getProvider("opencode"), { root: ROOT, dir: "/proy", scope, version: "9.9.9" })
    const copia = plan.find((s) => s.type === "copy" && String(s.to).endsWith(ADAPTADOR_OPENCODE))
    const merge = plan.find((s) => s.type === "merge")
    const spec = merge.merge.plugin
    assert.equal(spec.length, 1, `${scope}: una sola entrada`)
    assert.ok(!spec[0].includes("\\"), `${scope}: la ruta del JSON va con "/"`)
    // OpenCode resuelve un spec con forma de ruta contra la CARPETA DEL CONFIG que lo declara:
    // el destino de esa resolución tiene que ser justo el fichero que acabamos de copiar.
    const baseCfg = dirname(merge.to)
    assert.equal(resolve(baseCfg, spec[0]), resolve(copia.to),
      `${scope}: \`plugin\` apunta a un fichero que el instalador no deja ahí`)
  }
  // Y la forma exacta de cada scope, que es lo que se documenta
  assert.equal(rutaPluginOpencode("/proy/.opencode", "project"), "./.opencode/" + "plugins/" + ADAPTADOR_OPENCODE)
  assert.ok(rutaPluginOpencode(GLOBAL_DIR.opencode, "user").startsWith(GLOBAL_DIR.opencode.split(/[\\/]/).join("/")))
})

test("OpenCode: `plugin` se une sin duplicar y conserva el del usuario; uninstall lo deja y avisa", () => {
  const proj = tmpProj()
  try {
    writeFileSync(join(proj, "opencode.json"), JSON.stringify({ plugin: ["otro"] }))
    cli(["install", "-p", "opencode", "--dir", proj, "-q"])
    const esperada = rutaPluginOpencode(join(proj, ".opencode"), "project")
    const uno = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    assert.deepEqual(uno.plugin, ["otro", esperada], "el `plugin` previo del usuario manda y el nuestro se añade")

    // reinstalar no duplica
    cli(["install", "-p", "opencode", "--dir", proj, "-q"])
    const dos = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    assert.deepEqual(dos.plugin, uno.plugin, "reinstalar duplicó la entrada de `plugin`")

    // el fichero registrado existe de verdad (si no, OpenCode falla al arrancar)
    assert.ok(existsSync(resolve(proj, esperada)), "`plugin` apunta a un fichero que no está")

    const out = cli(["uninstall", "-p", "opencode", "--dir", proj])
    const tras = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    assert.deepEqual(tras.plugin, uno.plugin, "uninstall tocó una config que es del usuario")
    assert.match(out, /plugin/, "hay que avisar de que la entrada de `plugin` queda colgando")
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("scope user apunta al directorio global de cada runtime", () => {
  for (const p of PROVIDERS) {
    const dest = p.destino("user", "/proy")
    assert.ok(dest.startsWith(homedir()), `${p.id}: scope user debería vivir en $HOME`)
  }
  assert.ok(GLOBAL_DIR.opencode.includes(".config"), "el global de OpenCode es ~/.config/opencode")
})

test("ficherosDe enumera árboles y excluye caché de python", () => {
  const fs_ = ficherosDe("skills", "/dst")
  assert.ok(fs_.length > 50, "skills debería traer muchos ficheros")
  assert.ok(!fs_.some((f) => f.includes("__pycache__") || f.endsWith(".pyc")))
  assert.deepEqual(ficherosDe("no-existe-nada", "/dst"), [])
})

// ------------------------------------------------------------------ end to end

test("install → idempotente → uninstall preciso", () => {
  const proj = tmpProj()
  try {
    // 1) instalar
    cli(["install", "-p", "opencode", "--dir", proj, "-q"])
    const man = JSON.parse(readFileSync(join(proj, ".opencode", MANIFEST), "utf8"))
    assert.equal(man.provider, "opencode")
    assert.ok(man.files.length > 100, "el manifiesto debe listar lo instalado")
    assert.ok(existsSync(join(proj, ".opencode", "agents", "reviewer.md")))
    assert.ok(existsSync(join(proj, ".opencode", "plugins", "custom-agents-hooks.js")))
    assert.ok(existsSync(join(proj, "opencode.json")))

    // 2) idempotencia: reinstalar no cambia el recuento ni duplica instructions
    cli(["install", "-p", "opencode", "--dir", proj, "-q"])
    const man2 = JSON.parse(readFileSync(join(proj, ".opencode", MANIFEST), "utf8"))
    assert.deepEqual(man2.files, man.files, "reinstalar cambió la lista de ficheros")
    const cfg = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    const idx = cfg.instructions.filter((i) => i.includes("custom-agents-index"))
    assert.equal(idx.length, 1, "instructions duplicado al reinstalar")

    // 3) un fichero ajeno en una carpeta nuestra debe sobrevivir
    const ajeno = join(proj, ".opencode", "plugins", "mi-plugin.js")
    writeFileSync(ajeno, "// mío\n")

    // 4) desinstalar
    cli(["uninstall", "-p", "opencode", "--dir", proj, "-q"])
    assert.ok(existsSync(ajeno), "uninstall borró un fichero que no era suyo")
    assert.ok(existsSync(join(proj, "opencode.json")), "uninstall borró la config del usuario")
    assert.ok(!existsSync(join(proj, ".opencode", "agents", "reviewer.md")))
    assert.ok(!existsSync(join(proj, ".opencode", MANIFEST)))
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("--dry-run no escribe nada", () => {
  const proj = tmpProj()
  try {
    const out = cli(["install", "-p", "opencode", "--dir", proj, "--dry-run"])
    assert.match(out, /dry-run/)
    assert.ok(!existsSync(join(proj, ".opencode")), "dry-run creó ficheros")
    assert.ok(!existsSync(join(proj, "opencode.json")), "dry-run tocó la config")
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("no pisa el bloque permission del usuario y lo avisa", () => {
  const proj = tmpProj()
  try {
    const previo = { instructions: ["AGENTS.md"], permission: { skill: { "internal-*": "deny" } } }
    writeFileSync(join(proj, "opencode.json"), JSON.stringify(previo))
    const out = cli(["install", "-p", "opencode", "--dir", proj])
    const cfg = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    assert.deepEqual(cfg.permission, previo.permission, "se tocó la política de permisos del usuario")
    assert.ok(cfg.instructions.includes("AGENTS.md"), "se perdió una instruction del usuario")
    assert.equal(cfg.instructions.length, 2)
    assert.match(out, /permission/, "el cambio omitido tiene que anunciarse")
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("errores de uso: proveedor inválido y scope inválido salen con 2", () => {
  for (const args of [["install", "-p", "eclipse"], ["install", "-p", "codex", "--scope", "galaxia"]]) {
    assert.throws(() => cli([...args, "--dry-run"]), (e) => e.status === 2, `debería fallar: ${args}`)
  }
})

test("status y list funcionan sin nada instalado", () => {
  const proj = tmpProj()
  try {
    assert.match(cli(["status", "--dir", proj]), /sin instalar/)
    const l = cli(["list"])
    for (const id of IDS) assert.match(l, new RegExp(id))
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

// ================================================================== T-05 · `status` registrado
//
// Copiar ficheros no es instalar: `status` tiene que leer los MISMOS ficheros que el runtime lee
// al arrancar. Es el falso positivo de `/doctor` visto desde el instalador.

test("leerRegistro: lee los ficheros del runtime y un fichero ajeno roto no lo tumba", () => {
  const proj = tmpProj()
  try {
    const json = join(proj, "settings.json")
    assert.equal(leerRegistro([{ fichero: json, tipo: "json-prefijo", ruta: "enabledPlugins", prefijo: "custom-agents@" }]).registrado, false,
      "sin fichero no hay registro")
    writeFileSync(json, "{ esto no es json")
    assert.equal(leerRegistro([{ fichero: json, tipo: "json-prefijo", ruta: "enabledPlugins", prefijo: "custom-agents@" }]).registrado, false)
    writeFileSync(json, JSON.stringify({ enabledPlugins: { "custom-agents@daycry": false } }))
    assert.equal(leerRegistro([{ fichero: json, tipo: "json-prefijo", ruta: "enabledPlugins", prefijo: "custom-agents@" }]).registrado, false,
      "`false` es justo lo contrario de estar registrado")
    writeFileSync(json, JSON.stringify({ enabledPlugins: { "custom-agents@daycry": true } }))
    const hit = leerRegistro([{ fichero: json, tipo: "json-prefijo", ruta: "enabledPlugins", prefijo: "custom-agents@" }])
    assert.ok(hit.registrado && hit.donde === json)

    const toml = join(proj, "config.toml")
    const desc = [{ fichero: toml, tipo: "toml-verdadero", ruta: 'plugins."custom-agents@daycry".enabled' }]
    writeFileSync(toml, '[plugins."custom-agents@daycry"]\nenabled = false\n')
    assert.equal(leerRegistro(desc).registrado, false)
    writeFileSync(toml, '[plugins."custom-agents@daycry"]\nenabled = true\n')
    assert.equal(leerRegistro(desc).registrado, true)
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("status: `--mode copy` dice «registrado: no» y el plugin registrado dice «sí»", () => {
  const proj = tmpProj()
  const cfg = tmpProj()
  const env = { ...process.env, NO_COLOR: "1", CLAUDE_CONFIG_DIR: cfg }
  try {
    cli(["install", "-p", "claude-code", "--mode", "copy", "-y", "--dir", proj, "-q"], { env })
    const copia = cli(["status", "--dir", proj], { env })
    assert.match(copia, /project\/copy: v/, "el manifiesto del copy sigue saliendo")
    assert.match(copia, /project: registrado: no/, "un bundle copiado NO está registrado")

    // el registro que escribe el modo plugin (scope project): `.claude/settings.json`
    writeFileSync(join(proj, ".claude", "settings.json"),
      JSON.stringify({ enabledPlugins: { "custom-agents@daycry": true } }))
    assert.match(cli(["status", "--dir", proj], { env }), /project: registrado: sí/)
  } finally {
    for (const d of [proj, cfg]) rmSync(d, { recursive: true, force: true })
  }
})

test("status: Codex y OpenCode también dicen si el runtime los tiene dados de alta", () => {
  const proj = tmpProj()
  try {
    cli(["install", "-p", "opencode", "--dir", proj, "-q"])
    assert.match(cli(["status", "--dir", proj]), /project: registrado: sí/,
      "OpenCode: el adaptador queda en `plugin` de opencode.json")

    const proj2 = tmpProj()
    try {
      cli(["install", "-p", "codex", "--dir", proj2, "-q"])
      const s = cli(["status", "--dir", proj2])
      assert.match(s, /project: registrado: sí/, "Codex: `enabled = true` en config.toml")
      // y si el usuario lo apaga, `status` lo dice: es la única fuente de verdad del runtime
      const toml = join(proj2, ".codex", "config.toml")
      writeFileSync(toml, readFileSync(toml, "utf8").replace("enabled = true", "enabled = false"))
      assert.match(cli(["status", "--dir", proj2]), /project: registrado: no/)
    } finally {
      rmSync(proj2, { recursive: true, force: true })
    }
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("uninstall sin manifiesto avisa y sale con 1", () => {
  const proj = tmpProj()
  try {
    assert.throws(() => cli(["uninstall", "-p", "opencode", "--dir", proj]), (e) => e.status === 1)
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("la versión del paquete npm no diverge del manifiesto del plugin", () => {
  const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"))
  const plug = JSON.parse(readFileSync(join(ROOT, ".claude-plugin", "plugin.json"), "utf8"))
  assert.equal(pkg.version, plug.version, "package.json y plugin.json con versiones distintas")
  assert.equal(pkg.bin["custom-agents"], "install/install.mjs")
  // Lo que se publica tiene que incluir lo que el instalador copia.
  for (const p of ["install/", "skills/", "agent-kits/", "hooks/", "interop/", ".codex-plugin/"]) {
    assert.ok(pkg.files.includes(p), `package.json files: falta ${p}`)
  }
})

// ================================================================== T-01 · menú interactivo
//
// El multiselect se prueba por su REDUCTOR (función pura): no hace falta una terminal para saber
// qué marca cada tecla, que es lo único que puede estropearse al elegir proveedores.

const ids3 = ["claude-code", "codex", "opencode"]

test("reducirTecla: mover y marcar con espacio", () => {
  let e = estadoInicial(ids3, [])
  e = reducirTecla(e, "down")
  e = reducirTecla(e, "space")
  assert.deepEqual(e.marcados, [false, true, false], "espacio marca la fila del cursor")
  e = reducirTecla(e, "space")
  assert.deepEqual(e.marcados, [false, false, false], "espacio desmarca")
  e = reducirTecla(e, "up")
  assert.equal(e.cursor, 0)
  e = reducirTecla(e, "up")
  assert.equal(e.cursor, 2, "el cursor da la vuelta")
  assert.equal(reducirTecla(e, "j").cursor, 0, "j = abajo")
  assert.equal(reducirTecla(e, "k").cursor, 1, "k = arriba")
})

test("reducirTecla: `a` marca todos, `i` invierte, Enter devuelve solo los marcados", () => {
  let e = estadoInicial(ids3, [])
  assert.deepEqual(reducirTecla(e, "a").marcados, [true, true, true])
  e = reducirTecla(e, "space")            // marca claude-code
  assert.deepEqual(reducirTecla(e, "i").marcados, [false, true, true], "i invierte")
  const fin = reducirTecla(e, "return")
  assert.deepEqual(fin.fin.sel, ["claude-code"], "Enter devuelve SOLO lo marcado")
  assert.equal(reducirTecla(estadoInicial(ids3, []), "return").fin.sel.length, 0)
})

test("reducirTecla: Esc, q y Ctrl-C cancelan; una tecla cualquiera no hace nada", () => {
  const e = estadoInicial(ids3, ["codex"])
  for (const t of ["escape", "q", "ctrl-c"]) {
    assert.deepEqual(reducirTecla(e, t).fin, { cancelado: true }, `${t} tiene que cancelar`)
  }
  assert.equal(reducirTecla(e, "z"), e, "una tecla desconocida devuelve el MISMO estado")
})

test("estadoInicial: preselección = lo que se le pase (detectados ∪ claude-code)", () => {
  const pre = [...new Set([...["codex"], "claude-code"])]
  const e = estadoInicial(ids3, pre)
  assert.deepEqual(e.marcados, [true, true, false], "claude-code va marcado aunque no se detecte")
  assert.equal(e.cursor, 0)
  assert.equal(e.fin, null)
})

test("nombreTecla traduce lo que da readline al vocabulario del reductor", () => {
  assert.equal(nombreTecla(" ", { name: "space" }), "space")
  assert.equal(nombreTecla(" ", undefined), "space")
  assert.equal(nombreTecla("\r", { name: "return" }), "return")
  assert.equal(nombreTecla("\u0003", { name: "c", ctrl: true }), "ctrl-c")
  assert.equal(nombreTecla("j", { name: "j" }), "j")
})

test("el banner no sale donde estorba: --help, --version, status, list y CI", () => {
  const trozo = "\\___/"   // una línea del wordmark
  for (const args of [["--help"], ["--version"], ["status"], ["list"]]) {
    assert.ok(!cli(args).includes(trozo), `${args[0]} no debe pintar el banner`)
  }
  const conCi = cli(["install", "--all", "--dry-run"], { env: conPath(process.env.PATH, { CI: "1" }) })
  assert.ok(!conCi.includes(trozo), "con CI=1 no se pinta el banner")
})

// ================================================================== T-02 · Claude Code como plugin

const planClaude = (extra = {}) =>
  buildPlan(getProvider("claude-code"), { root: ROOT, dir: "/proy", scope: "user", version: "9.9.9", ...extra })

test("Claude Code con CLI: el plan son los dos comandos oficiales", () => {
  const plan = planClaude({ cli: { claude: true } })
  assert.deepEqual(plan.map((p) => p.type), ["exec", "exec"])
  assert.deepEqual(plan[0].args, ["plugin", "marketplace", "add", "daycry/custom-agents", "--scope", "user"])
  assert.equal(plan[0].siFalla, "aviso", "si el marketplace ya estaba, se sigue")
  assert.deepEqual(plan[1].args, ["plugin", "install", "custom-agents@daycry", "--scope", "user", "--yes"])
  assert.deepEqual(plan[1].deshacer, ["claude", "plugin", "uninstall", "custom-agents@daycry", "--scope", "user"])
  // --source cambia la fuente del marketplace (desarrollo)
  assert.equal(planClaude({ cli: { claude: true }, source: "./mi-clon" })[0].args[3], "./mi-clon")
})

test("Claude Code sin CLI: copias + las tres claves del registro, bajo CLAUDE_CONFIG_DIR", () => {
  const cfg = join(tmpdir(), "ca-cfg-plan")
  const previo = process.env.CLAUDE_CONFIG_DIR
  process.env.CLAUDE_CONFIG_DIR = cfg
  try {
    const plan = planClaude({ cli: { claude: false } })
    const sets = plan.filter((p) => p.type === "json-set")
    assert.equal(sets.length, 3)
    assert.deepEqual(sets.map((s) => s.to), [
      join(cfg, "plugins", "known_marketplaces.json"),
      join(cfg, "plugins", "installed_plugins.json"),
      join(cfg, "settings.json"),
    ])
    assert.equal(sets[0].set.daycry.source.repo, "daycry/custom-agents")
    assert.equal(sets[1].set.version, 2)
    assert.equal(sets[1].set["plugins.custom-agents@daycry"][0].version, "9.9.9")
    assert.equal(sets[2].set["enabledPlugins.custom-agents@daycry"], true)
    const copias = plan.filter((p) => p.type === "copy")
    assert.ok(copias.some((c) => c.to === join(cfg, "plugins", "marketplaces", "daycry", "hooks")))
    assert.ok(copias.some((c) => c.to === join(cfg, "plugins", "cache", "daycry", "custom-agents", "9.9.9", "agents")))
    assert.ok(copias.some((c) => c.from === "package.json"), "el marketplace necesita el package.json")
    assert.ok(copias[0].aviso.includes("PATH"), "el respaldo sin CLI tiene que decirse")
    // scope project: los ajustes van al .claude del proyecto y declara el marketplace extra
    const proj = buildPlan(getProvider("claude-code"),
      { root: ROOT, dir: join("/proy"), scope: "project", version: "9.9.9", cli: { claude: false } })
    const ajustes = proj.filter((p) => p.type === "json-set").at(-1)
    assert.match(ajustes.to, /[\\/]proy[\\/]\.claude[\\/]settings\.json$/)
    assert.equal(ajustes.set["extraKnownMarketplaces.daycry"].source.repo, "daycry/custom-agents")
  } finally {
    if (previo === undefined) delete process.env.CLAUDE_CONFIG_DIR
    else process.env.CLAUDE_CONFIG_DIR = previo
  }
})

test("--mode copy reproduce el plan de siempre, con el aviso de lo que se pierde", () => {
  const plan = buildPlan(getProvider("claude-code"),
    { root: ROOT, dir: join("/proy"), scope: "project", version: "9.9.9", modo: "copy" })
  assert.deepEqual(plan.map((p) => p.from), PAYLOAD_CLAUDE)
  for (const paso of plan) {
    assert.equal(paso.type, "copy")
    assert.equal(paso.to, join("/proy", ".claude", paso.from))
  }
  assert.match(plan[0].aviso, /hooks y statusline NO se registran/)
  assert.equal(getProvider("claude-code").destino("project", "/proy", "copy"), join("/proy", ".claude"))
})

test("Claude Code sin CLI: registro real, idempotente y desinstalable sin tocar lo del usuario", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    // Lo que el usuario ya tenía: ni una clave se puede perder.
    writeFileSync(join(cfg, "settings.json"),
      JSON.stringify({ model: "opus", enabledPlugins: { "otro@mkt": true } }, null, 2))
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })

    const km = JSON.parse(readFileSync(join(cfg, "plugins", "known_marketplaces.json"), "utf8"))
    assert.equal(km.daycry.source.repo, "daycry/custom-agents")
    assert.equal(km.daycry.installLocation, join(cfg, "plugins", "marketplaces", "daycry"))
    const ip = JSON.parse(readFileSync(join(cfg, "plugins", "installed_plugins.json"), "utf8"))
    assert.equal(ip.version, 2)
    assert.equal(ip.plugins["custom-agents@daycry"][0].scope, "user")
    assert.equal(ip.plugins["custom-agents@daycry"][0].version, VERSION)
    const st = JSON.parse(readFileSync(join(cfg, "settings.json"), "utf8"))
    assert.equal(st.enabledPlugins["custom-agents@daycry"], true)
    assert.equal(st.model, "opus", "json-set pisó una clave que no era suya")
    assert.equal(st.enabledPlugins["otro@mkt"], true, "json-set se cargó otro plugin del usuario")
    assert.ok(existsSync(join(cfg, "plugins", "cache", "daycry", "custom-agents", VERSION, "hooks", "hooks.json")),
      "el plugin tiene que quedar en la caché que Claude Code lee")

    // Idempotencia: segunda pasada, MISMOS bytes (las marcas de tiempo no cuentan como cambio).
    const leer = () => ["plugins/known_marketplaces.json", "plugins/installed_plugins.json", "settings.json"]
      .map((f) => readFileSync(join(cfg, ...f.split("/")), "utf8"))
    const antes = leer()
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })
    assert.deepEqual(leer(), antes, "reinstalar reescribió el registro")

    // Desinstalar quita SOLO las claves que puso, y ni un fichero del usuario.
    cli(["uninstall", "-p", "claude-code", "--scope", "user", "-q"], { env })
    const st2 = JSON.parse(readFileSync(join(cfg, "settings.json"), "utf8"))
    assert.ok(!("custom-agents@daycry" in st2.enabledPlugins))
    assert.equal(st2.enabledPlugins["otro@mkt"], true)
    assert.equal(st2.model, "opus")
    // `installed_plugins.json` y `known_marketplaces.json` NO existían antes de instalar: el
    // manifiesto lo anota (`creado`) y, al quedarse sin nada nuestro, se van enteros en vez de
    // dejar un `{"version":2,"plugins":{}}` que el usuario nunca tuvo. Ver el test de `creado`
    // para el caso contrario (fichero preexistente → `version` se respeta).
    assert.ok(!existsSync(join(cfg, "plugins", "installed_plugins.json")),
      "el registro lo creó el instalador y se ha quedado vacío: no se deja")
    assert.ok(!existsSync(join(cfg, "plugins", "known_marketplaces.json")))
    assert.ok(!existsSync(join(cfg, "plugins", "cache", "daycry", "custom-agents", VERSION, "hooks", "hooks.json")))
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ================================================================== T-03 · Codex: TOML y CLI

test("ponerToml: crea la tabla si no está y respeta el resto del fichero", () => {
  assert.equal(ponerToml("", "features", "hooks", true), "[features]\nhooks = true\n")
  const previo = "# mi config\nmodel = \"gpt-5\"\n\n[tui]\ntheme = \"dark\"\n"
  const out = ponerToml(previo, 'plugins."custom-agents@daycry"', "enabled", true)
  assert.ok(out.startsWith(previo), "no se puede reescribir una sola línea de lo que ya había")
  assert.equal(out, previo + "\n[plugins.\"custom-agents@daycry\"]\nenabled = true\n")
})

test("ponerToml: cambia la clave que ya existe y deja el resto byte a byte", () => {
  const previo = "[features]\n# comentario del usuario\nweb_search = true\nhooks = false\n\n[tui]\ntheme = \"dark\"\n"
  const out = ponerToml(previo, "features", "hooks", true)
  assert.equal(out, previo.replace("hooks = false", "hooks = true"))
  assert.equal(ponerToml(out, "features", "hooks", true), out, "idempotente")
})

test("ponerToml: añade la clave al final de SU tabla, no del fichero", () => {
  const previo = "[features]\nweb_search = true\n\n[tui]\ntheme = \"dark\"\n"
  const out = ponerToml(previo, "features", "hooks", true)
  assert.equal(out, "[features]\nweb_search = true\nhooks = true\n\n[tui]\ntheme = \"dark\"\n")
  // CRLF y fichero sin salto final: tampoco se normaliza nada
  assert.equal(ponerToml("[features]\r\nweb_search = true", "features", "hooks", true),
    "[features]\r\nweb_search = true\r\nhooks = true\r\n")
})

test("versionSuficiente compara como un humano, no como una cadena", () => {
  assert.equal(versionSuficiente("0.130.0", "0.128.0"), true)
  assert.equal(versionSuficiente("0.9.0", "0.128.0"), false, "0.9 < 0.128 (no es texto)")
  assert.equal(versionSuficiente("0.128.0", "0.128.0"), true)
  assert.equal(versionSuficiente("1.0.0", "0.128.0"), true)
  assert.equal(versionSuficiente(null, "0.128.0"), false)
})

test("Codex: el plan da de alta el marketplace y habilita el plugin en config.toml", () => {
  const plan = buildPlan(getProvider("codex"), { root: ROOT, dir: "/proy", scope: "project", version: "9.9.9" })
  const ex = plan.find((p) => p.type === "exec")
  assert.equal(ex.cmd, "codex")
  assert.deepEqual(ex.args.slice(0, 3), ["plugin", "marketplace", "add"])
  assert.equal(ex.opcional, true, "sin codex en el PATH no se puede bloquear la instalación")
  assert.equal(ex.minVersion, "0.128.0")
  assert.ok(ex.siYaExiste.args.includes("remove"), "si ya existía con otra fuente: remove + add")
  const tomls = plan.filter((p) => p.type === "toml-set")
  assert.deepEqual(tomls.map((t) => [t.tabla, t.clave, t.valor]), [
    ['plugins."custom-agents@daycry"', "enabled", true],
    ["features", "hooks", true],
  ])
  assert.equal(tomls[1].deshacer, false, "`[features] hooks` es del usuario: desinstalar no lo apaga")
  for (const t of tomls) assert.match(t.to, /[\\/]\.codex[\\/]config\.toml$/)
})

test("Codex: instala de verdad, llama a su CLI y deja el config.toml del usuario intacto", () => {
  const tmp = tmpProj()
  try {
    const hogar = join(tmp, "home")
    mkdirSync(join(hogar, ".codex"), { recursive: true })
    const bin = join(tmp, "bin")
    mkdirSync(bin)
    const log = join(tmp, "codex.log")
    codexFalso(bin)
    const previo = "# mi config\n[features]\nweb_search = true\n\n[tui]\ntheme = \"dark\"\n"
    const cfgToml = join(hogar, ".codex", "config.toml")
    writeFileSync(cfgToml, previo)
    const env = conPath([bin, SIN_CLI].join(delimiter), { HOME: hogar, USERPROFILE: hogar, CODEX_FAKE_LOG: log })

    cli(["install", "-p", "codex", "--scope", "user", "-y", "-q"], { env })
    const toml = readFileSync(cfgToml, "utf8")
    assert.match(toml, /\[plugins\."custom-agents@daycry"\]\nenabled = true/)
    assert.equal(toml.split("\n")[0], "# mi config", "se perdió el comentario del usuario")
    assert.match(toml, /\[features\]\nweb_search = true\nhooks = true/)
    assert.match(toml, /\[tui\]\ntheme = "dark"/)
    // El `codex` de mentira apunta lo que le piden (el `.cmd` de Windows reproduce las comillas).
    const llamada = readFileSync(log, "utf8").replace(/"/g, "")
    assert.match(llamada, /plugin marketplace add/, "no se llamó a la CLI de Codex")
    assert.match(llamada, /[\\/]\.agents/, "el marketplace que se da de alta es el recién escrito")

    // Desinstalar: `enabled = false` y ni una línea más del config.toml
    cli(["uninstall", "-p", "codex", "--scope", "user", "-q"], { env })
    const toml2 = readFileSync(cfgToml, "utf8")
    assert.equal(toml2, toml.replace("enabled = true", "enabled = false"))
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("sin la CLI del runtime, el comando pendiente se dice en vez de fallar", () => {
  const tmp = tmpProj()
  try {
    const hogar = join(tmp, "home")
    mkdirSync(join(hogar, ".codex"), { recursive: true })
    const out = cli(["install", "-p", "codex", "--scope", "user", "-y"],
      { env: conPath(SIN_CLI, { HOME: hogar, USERPROFILE: hogar }) })
    assert.match(out, /codex plugin marketplace add/, "hay que decir el comando que queda pendiente")
    assert.ok(existsSync(join(hogar, ".codex", "config.toml")), "el resto de la instalación sigue")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ================================================================== Revisión de dos lentes · intento 1
//
// Un test (o varios) por gap. Cada uno reproduce el escenario que describió la lente ANTES de la
// corrección: si alguien deshace el arreglo, el test se pone rojo con el mismo síntoma.

import {
  leerJsonEstricto, ponerRutaEstricta, normalizarTabla, existeTabla,
  cortarAnsi, anchoVisible, argCmd, resultadoSeleccion,
} from "../install/install.mjs"
import {
  elegirEjecutable, clasificarFuente, MANIFEST_PLUGIN, sitiosManifiesto,
} from "../install/providers.mjs"

// ------------------------------------------------------------------ gap 1 (Critical): JSON ilegible

test("gap 1: un JSON del registro que no parsea es un ERROR, no una excusa para sustituirlo", () => {
  const casos = {
    "BOM + coma final": "\uFEFF{\n  \"model\": \"opus\",\n}\n",
    "coma final": "{\n  \"model\": \"opus\",\n}\n",
    "JSONC": "{\n  // mi modelo\n  \"model\": \"opus\"\n}\n",
    "enabledPlugins no es un objeto": "{\n  \"model\": \"opus\",\n  \"enabledPlugins\": true\n}\n",
  }
  for (const [nombre, contenido] of Object.entries(casos)) {
    const tmp = tmpProj()
    try {
      const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
      mkdirSync(cfg, { recursive: true })
      mkdirSync(hogar, { recursive: true })
      writeFileSync(join(cfg, "settings.json"), contenido, "utf8")
      const antes = readFileSync(join(cfg, "settings.json"))
      const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
      let err = null
      try { cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }) } catch (e) { err = e }
      assert.ok(err, `${nombre}: tenía que fallar en alto, no salir con 0`)
      assert.equal(err.status, 1, `${nombre}: exit 1`)
      const dicho = `${err.stdout || ""}${err.stderr || ""}`
      assert.match(dicho, /settings\.json/, `${nombre}: hay que decir QUÉ fichero`)
      assert.match(dicho, /no es JSON válido|no es un objeto/, `${nombre}: hay que decir POR QUÉ`)
      assert.deepEqual(readFileSync(join(cfg, "settings.json")), antes,
        `${nombre}: el fichero del usuario tiene que quedar byte a byte igual`)
    } finally {
      rmSync(tmp, { recursive: true, force: true })
    }
  }
})

test("gap 1: el BOM se tolera al leer y se conserva al escribir", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    writeFileSync(join(cfg, "settings.json"), "\uFEFF" + JSON.stringify({ model: "opus" }, null, 2), "utf8")
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })
    const crudo = readFileSync(join(cfg, "settings.json"), "utf8")
    assert.ok(crudo.startsWith("\uFEFF"), "el BOM del usuario no se le puede quitar")
    const st = JSON.parse(crudo.slice(1))
    assert.equal(st.model, "opus")
    assert.equal(st.enabledPlugins["custom-agents@daycry"], true)
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap 1: leerJsonEstricto y ponerRutaEstricta fallan donde el `|| {}` tragaba", () => {
  const tmp = tmpProj()
  try {
    const f = join(tmp, "x.json")
    assert.deepEqual(leerJsonEstricto(f), { existe: false, bom: false, valor: {} })
    writeFileSync(f, "{,}")
    assert.throws(() => leerJsonEstricto(f), /no es JSON válido/)
    writeFileSync(f, "\uFEFF{\"a\":1}")
    assert.deepEqual(leerJsonEstricto(f), { existe: true, bom: true, valor: { a: 1 } })
    writeFileSync(f, "[1,2]")
    assert.throws(() => leerJsonEstricto(f), /no contiene un objeto JSON/)
    assert.throws(() => ponerRutaEstricta({ enabledPlugins: true }, "enabledPlugins.x", true, "settings.json"),
      /existe y no es un objeto/)
    assert.deepEqual(ponerRutaEstricta({}, "a.b", 1), { a: { b: 1 } })
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 2 (Critical): el shim de npm

test("gap 2: con el layout de npm (shim sin extensión + .cmd) se elige el .cmd, nunca el shim", () => {
  const npm = ["C:\\Users\\yo\\AppData\\Roaming\\npm\\claude", "C:\\Users\\yo\\AppData\\Roaming\\npm\\claude.cmd"]
  assert.deepEqual(elegirEjecutable(npm, "win32"), { ruta: npm[1], ejecutable: true },
    "el primer resultado de where.exe es el shim POSIX: cogerlo daba ENOENT")
  // Solo el shim: no se puede lanzar → se dice y se degrada (nunca un ENOENT a la cara)
  assert.deepEqual(elegirEjecutable([npm[0]], "win32"), { ruta: npm[0], ejecutable: false })
  assert.deepEqual(elegirEjecutable(["C:\\bin\\codex.exe"], "win32"), { ruta: "C:\\bin\\codex.exe", ejecutable: true })
  assert.deepEqual(elegirEjecutable([], "win32"), { ruta: null, ejecutable: false })
  // Fuera de Windows vale el primero, que es un ejecutable de verdad
  assert.deepEqual(elegirEjecutable(["/usr/local/bin/claude"], "linux"),
    { ruta: "/usr/local/bin/claude", ejecutable: true })
})

test("gap 2: un `claude` que solo es shim degrada al respaldo diciéndolo, no revienta",
  { skip: process.platform !== "win32" ? "solo en Windows" : false }, () => {
    const tmp = tmpProj()
    try {
      const bin = join(tmp, "bin"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
      for (const d of [bin, cfg, hogar]) mkdirSync(d, { recursive: true })
      writeFileSync(join(bin, "claude"), "#!/bin/sh\nexit 0\n")   // shim POSIX, sin extensión
      const env = conPath([bin, SIN_CLI].join(delimiter),
        { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
      const out = cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env })
      assert.match(out, /no ejecutable desde Node/, "hay que decir por qué no se usa la CLI")
      assert.match(out, /uso el registro directo/)
      assert.ok(existsSync(join(cfg, "plugins", "installed_plugins.json")), "el respaldo tiene que entrar")
    } finally {
      rmSync(tmp, { recursive: true, force: true })
    }
  })

// ------------------------------------------------------------------ gap 3: clasificación de --source

test("gap 3: `./mi-clon` es una ruta, no un repo de GitHub", () => {
  assert.deepEqual(clasificarFuente("daycry/custom-agents"),
    { source: "github", repo: "daycry/custom-agents" })
  for (const ruta of ["./mi-clon", "../otro/clon"]) {
    const r = clasificarFuente(ruta)
    assert.equal(r.source, "directory", `${ruta} no es owner/repo`)
    assert.equal(r.path, resolve(ruta), "la ruta se guarda ABSOLUTA: el registro no se lee desde aquí")
  }
  assert.equal(clasificarFuente("/opt/custom-agents").source, "directory")
  assert.equal(clasificarFuente("C:\\repos\\custom-agents").source, "directory")
  // Un directorio que EXISTE y se llama `a/b` también es una ruta
  const tmp = tmpProj()
  const previo = process.cwd()
  try {
    mkdirSync(join(tmp, "a", "b"), { recursive: true })
    process.chdir(tmp)
    assert.equal(clasificarFuente("a/b").source, "directory")
  } finally {
    process.chdir(previo)
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 4: un manifiesto por modo

test("gap 4: instalar como plugin encima de un `--mode copy` no deja huérfanos", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [proj, cfg, hogar]) mkdirSync(d, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })

    cli(["install", "-p", "claude-code", "--mode", "copy", "--dir", proj, "-y", "-q"], { env })
    const manCopy = JSON.parse(readFileSync(join(proj, ".claude", MANIFEST), "utf8"))
    assert.ok(manCopy.files.length > 100)
    assert.ok(existsSync(join(proj, ".claude", "agents", "reviewer.md")))

    // Ahora como plugin, en el MISMO scope y el MISMO directorio (la vía de actualización real)
    cli(["install", "-p", "claude-code", "--dir", proj, "-y", "-q"], { env })
    assert.ok(existsSync(join(proj, ".claude", MANIFEST_PLUGIN)), "el modo plugin tiene su propio manifiesto")
    assert.ok(!existsSync(join(proj, ".claude", "agents", "reviewer.md")),
      "el bundle copiado se limpia antes de instalar el plugin (con -y)")

    cli(["uninstall", "-p", "claude-code", "--dir", proj, "-q"], { env })
    assert.ok(!existsSync(join(proj, ".claude", "agents")), "0 huérfanos del copy")
    assert.ok(!existsSync(join(proj, ".claude", "skills")))
    assert.ok(!existsSync(join(proj, ".claude", MANIFEST)))
    assert.ok(!existsSync(join(proj, ".claude", MANIFEST_PLUGIN)))
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap 4: sin `-y`, el bundle previo no se borra: se avisa con el comando", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [proj, cfg, hogar]) mkdirSync(d, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--mode", "copy", "--dir", proj, "-y", "-q"], { env })
    const out = cli(["install", "-p", "claude-code", "--dir", proj], { env })
    assert.match(out, /ya hay un bundle copiado/)
    assert.match(out, /uninstall -p claude-code/)
    assert.ok(existsSync(join(proj, ".claude", "agents", "reviewer.md")), "sin -y no se borra nada")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap 4: `status`/`uninstall` miran los dos nombres de manifiesto", () => {
  const sitios = sitiosManifiesto(getProvider("claude-code"), "project", "/proy")
  assert.deepEqual(sitios.map((s) => s.file).sort(), [MANIFEST, MANIFEST_PLUGIN].sort())
  assert.deepEqual(sitiosManifiesto(getProvider("opencode"), "project", "/proy").map((s) => s.file),
    [MANIFEST], "los proveedores de un solo modo no cambian de nombre")
})

// ------------------------------------------------------------------ gap 5: manifiesto parcial

test("gap 5: si un paso revienta, queda un manifiesto `incompleto` que uninstall acepta", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    // `settings.json` ilegible: las copias y los dos primeros json-set SÍ se aplican; el tercero revienta.
    writeFileSync(join(cfg, "settings.json"), "{,}", "utf8")
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    assert.throws(() => cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }),
      (e) => e.status === 1)

    const man = JSON.parse(readFileSync(join(cfg, "plugins", MANIFEST_PLUGIN), "utf8"))
    assert.equal(man.estado, "incompleto", "sin manifiesto, lo ya aplicado no se puede limpiar")
    assert.match(man.error, /settings\.json/)
    assert.ok(man.files.length > 100, "los ficheros ya copiados tienen que estar apuntados")
    assert.match(cli(["status", "--dir", tmp], { env }), /incompleta/)

    cli(["uninstall", "-p", "claude-code", "--scope", "user", "-q"], { env })
    assert.ok(!existsSync(join(cfg, "plugins", "cache", "daycry")), "uninstall tiene que aceptar el parcial")
    assert.equal(readFileSync(join(cfg, "settings.json"), "utf8"), "{,}", "y no tocar el fichero roto")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 6: poda acotada

test("gap 6: desinstalar no borra directorios vacíos que no son nuestros", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })
    // Directorios vacíos de OTRO marketplace del usuario, dentro de nuestra raíz de manifiesto
    const ajenos = [join(cfg, "plugins", "marketplaces", "otro-mkt"),
                    join(cfg, "plugins", "cache", "otro-mkt", "algo"),
                    join(cfg, "plugins", "repos")]
    for (const d of ajenos) mkdirSync(d, { recursive: true })

    cli(["uninstall", "-p", "claude-code", "--scope", "user", "-q"], { env })
    for (const d of ajenos) assert.ok(existsSync(d), `podarVacios borró un directorio ajeno: ${d}`)
    assert.ok(!existsSync(join(cfg, "plugins", "marketplaces", "daycry")), "el nuestro sí se va")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 7: el marketplace del usuario

/** Un `codex` de mentira que dice que el marketplace ya existe apuntando a otra fuente. */
function codexOcupado(bin) {
  const p = join(bin, process.platform === "win32" ? "codex.cmd" : "codex")
  // Con estado: el `add` solo funciona DESPUÉS de un `remove` (como el Codex real).
  if (process.platform === "win32") {
    writeFileSync(p, [
      "@echo off",
      "if \"%~1\"==\"--version\" (echo codex-cli 0.130.0& exit /b 0)",
      "echo %* >> \"%CODEX_FAKE_LOG%\"",
      "if \"%~3\"==\"remove\" goto quitar",
      "if \"%~3\"==\"add\" goto anadir",
      "exit /b 0",
      ":quitar",
      "echo quitado > \"%CODEX_FAKE_LOG%.removed\"",
      "exit /b 0",
      ":anadir",
      "if exist \"%CODEX_FAKE_LOG%.removed\" (echo marketplace added& exit /b 0)",
      "echo daycry already added from a different source 1>&2",
      "exit /b 1",
      "",
    ].join("\r\n"))
  } else {
    writeFileSync(p, [
      "#!/bin/sh",
      "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli 0.130.0'; exit 0; fi",
      "echo \"$@\" >> \"$CODEX_FAKE_LOG\"",
      "if [ \"$3\" = \"remove\" ]; then echo quitado > \"$CODEX_FAKE_LOG.removed\"; exit 0; fi",
      "if [ \"$3\" = \"add\" ]; then",
      "  if [ -f \"$CODEX_FAKE_LOG.removed\" ]; then echo 'marketplace added'; exit 0; fi",
      "  echo 'daycry already added from a different source' >&2; exit 1",
      "fi",
      "exit 0",
      "",
    ].join("\n"))
    chmodSync(p, 0o755)
  }
}

test("gap 7: el marketplace del usuario NO se borra sin permiso; --force-marketplace lo permite", () => {
  const tmp = tmpProj()
  try {
    const hogar = join(tmp, "home"), bin = join(tmp, "bin"), log = join(tmp, "codex.log")
    mkdirSync(join(hogar, ".codex"), { recursive: true })
    mkdirSync(bin)
    codexOcupado(bin)
    const env = conPath([bin, SIN_CLI].join(delimiter), { HOME: hogar, USERPROFILE: hogar, CODEX_FAKE_LOG: log })

    const out = cli(["install", "-p", "codex", "--scope", "user", "-y"], { env })
    assert.match(out, /ya está dado de alta desde otra fuente y NO lo toco/)
    assert.match(out, /marketplace remove daycry/, "hay que dar el comando exacto")
    const llamadas = () => readFileSync(log, "utf8").replace(/"/g, "")
    assert.ok(!llamadas().includes("marketplace remove"),
      "sin --force-marketplace no se puede ejecutar un `remove` del marketplace del usuario")

    writeFileSync(log, "")
    const out2 = cli(["install", "-p", "codex", "--scope", "user", "-y", "--force-marketplace"], { env })
    assert.match(out2, /--force-marketplace/)
    assert.match(llamadas(), /marketplace remove daycry/, "con --force-marketplace sí")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 8: timeout y salida de la CLI

/** Un `codex` que no termina nunca (para el timeout). */
function codexColgado(bin) {
  const p = join(bin, process.platform === "win32" ? "codex.cmd" : "codex")
  if (process.platform === "win32") {
    writeFileSync(p, [
      "@echo off",
      "if \"%~1\"==\"--version\" (echo codex-cli 0.130.0& exit /b 0)",
      "ping -n 40 127.0.0.1 > nul",
      "exit /b 0",
      "",
    ].join("\r\n"))
  } else {
    writeFileSync(p, [
      "#!/bin/sh",
      "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli 0.130.0'; exit 0; fi",
      "sleep 40",
      "",
    ].join("\n"))
    chmodSync(p, 0o755)
  }
}

test("gap 8: una CLI colgada no bloquea el instalador (timeout) y se dice qué se está ejecutando", () => {
  const tmp = tmpProj()
  try {
    const hogar = join(tmp, "home"), bin = join(tmp, "bin")
    mkdirSync(join(hogar, ".codex"), { recursive: true })
    mkdirSync(bin)
    codexColgado(bin)
    const env = conPath([bin, SIN_CLI].join(delimiter),
      { HOME: hogar, USERPROFILE: hogar, CUSTOM_AGENTS_EXEC_TIMEOUT_MS: "2000" })
    const t0 = Date.now()
    const out = cli(["install", "-p", "codex", "--scope", "user", "-y"], { env })
    const tardo = Date.now() - t0
    assert.ok(tardo < 30_000, `el timeout no cortó: ${tardo} ms`)
    assert.match(out, /ejecutando/, "antes de lanzar hay que decir qué se lanza")
    assert.match(out, /codex plugin marketplace add/)
    assert.ok(existsSync(join(hogar, ".codex", "config.toml")), "y el resto de la instalación sigue")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap 8: el timeout por defecto son 120 s y se cambia por entorno", () => {
  const url = new URL("../install/install.mjs", import.meta.url).href
  const guion = `import { TIMEOUT_EXEC } from ${JSON.stringify(url)}; console.log(TIMEOUT_EXEC)`
  const leer = (extra) => execFileSync(process.execPath, ["--input-type=module", "-e", guion],
    { encoding: "utf8", env: { ...process.env, ...extra } }).trim()
  assert.equal(leer({ CUSTOM_AGENTS_EXEC_TIMEOUT_MS: "" }), "120000")
  assert.equal(leer({ CUSTOM_AGENTS_EXEC_TIMEOUT_MS: "5000" }), "5000")
})

// ------------------------------------------------------------------ gaps 9 y 20: el menú

test("gap 9: las filas del menú se recortan al ancho de la terminal (una fila, una línea física)", () => {
  const larga = "x".repeat(200)
  assert.equal(anchoVisible(cortarAnsi(larga, 79)), 79, "en 80 columnas, 79 visibles y ni una más")
  assert.ok(cortarAnsi(larga, 79).endsWith("…"))
  assert.equal(cortarAnsi("corta", 79), "corta", "lo que cabe no se toca")
  // Los códigos ANSI no cuentan como columnas, pero el reset se conserva
  const coloreada = "\u001b[1mabcdefghij\u001b[0m"
  assert.equal(anchoVisible(coloreada), 10)
  const cortada = cortarAnsi(coloreada, 5)
  assert.equal(anchoVisible(cortada), 5)
  assert.ok(cortada.endsWith("\u001b[0m"), "no se puede dejar el color colgando")
  assert.equal(cortarAnsi("abc", 0), "abc", "sin ancho conocido, no se recorta")
})

test("gap 20: Enter sin marcar nada no es «no he detectado ningún proveedor»", () => {
  assert.deepEqual(resultadoSeleccion({ sel: [] }), { vacio: true, ids: [] })
  assert.deepEqual(resultadoSeleccion({ sel: ["codex"] }), { ids: ["codex"] })
  assert.deepEqual(resultadoSeleccion({ cancelado: true }), { cancelado: true })
})

// ------------------------------------------------------------------ gap 10: la terminal siempre vuelve

test("gap 10: si `stdout.write` revienta a media tecla, el modo raw y el cursor vuelven", () => {
  const url = new URL("../install/install.mjs", import.meta.url).href
  const guion = [
    `import { multiselect } from ${JSON.stringify(url)}`,
    `const orig = process.stdout.write.bind(process.stdout)`,
    `let romper = false, cursor = ""`,
    `process.stdout.write = (s) => {`,
    `  if (typeof s === "string" && s.includes("[?25")) cursor = s`,
    `  if (romper) throw new Error("EPIPE de mentira")`,
    `  return true`,
    `}`,
    `let raw = null`,
    `process.stdin.isTTY = true`,
    `process.stdin.setRawMode = (v) => { raw = v; return process.stdin }`,
    `let fallo = null`,
    `multiselect(["claude-code", "codex", "opencode"], ["claude-code"]).then(() => {}, (e) => { fallo = e.message })`,
    `romper = true`,
    `process.stdin.emit("keypress", " ", { name: "space" })`,
    `setTimeout(() => {`,
    `  process.stdout.write = orig`,
    `  console.log(JSON.stringify({ raw, fallo, cursor, oyentes: process.stdin.listenerCount("keypress") }))`,
    `  process.exit(0)`,
    `}, 60)`,
  ].join("\n")
  const salida = execFileSync(process.execPath, ["--input-type=module", "-e", guion],
    { encoding: "utf8", env: { ...process.env, NO_COLOR: "1" } })
  const r = JSON.parse(salida.trim().split("\n").at(-1))
  assert.match(r.fallo || "", /EPIPE de mentira/, "el fallo tiene que propagarse")
  assert.equal(r.raw, false, "la terminal se quedaba en modo raw")
  assert.equal(r.cursor, "\u001b[?25h", "y sin cursor")
  assert.equal(r.oyentes, 0, "el listener de teclas tiene que soltarse")
})

// ------------------------------------------------------------------ gaps 11, 16, 17, 18: el TOML

test("gap 11: la cabecera de tabla se compara normalizada (comillas y espacios)", () => {
  for (const cabecera of ['[plugins."custom-agents@daycry"]', "[plugins.'custom-agents@daycry']",
                          '[ plugins . "custom-agents@daycry" ]']) {
    const previo = `${cabecera}\nenabled = false\n`
    const out = ponerToml(previo, 'plugins."custom-agents@daycry"', "enabled", true)
    assert.equal(out, previo.replace("false", "true"), `${cabecera}: se creó una tabla duplicada`)
    assert.equal((out.match(/enabled/g) || []).length, 1)
  }
  assert.equal(normalizarTabla(" plugins . 'x@y' "), 'plugins."x@y"')
  assert.equal(normalizarTabla('plugins."x@y"'), 'plugins."x@y"')
})

test("gap 11: un `[[tabla]]` con ese nombre es un error, no algo que tocar a ciegas", () => {
  const previo = '[[plugins."custom-agents@daycry"]]\nenabled = false\n'
  assert.throws(() => ponerToml(previo, 'plugins."custom-agents@daycry"', "enabled", true),
    /array de tablas/)
  assert.equal(existeTabla(previo, 'plugins."custom-agents@daycry"'), false)
  assert.equal(existeTabla('[features]\n', "features"), true)
})

test("gap 17: la clave no cae dentro de un array ni de una cadena multilínea", () => {
  const previo = [
    "[features]",
    "lista = [",
    '  "uno",',
    '  "[dos]",',
    "]",
    'texto = """',
    "[esto no es una tabla]",
    '"""',
    "",
    "[tui]",
    'theme = "dark"',
  ].join("\n") + "\n"
  const out = ponerToml(previo, "features", "hooks", true)
  const antesDeTui = out.split("[tui]")[0]
  assert.match(antesDeTui, /hooks = true/, "hooks tiene que quedar DENTRO de [features]")
  assert.ok(!out.includes('"""\n[esto no es una tabla]\nhooks'), "no se puede colar en el literal")
  assert.match(out, /lista = \[\n  "uno",\n  "\[dos\]",\n\]/, "el array del usuario, intacto")
  assert.match(out, /\[tui\]\ntheme = "dark"/, "y [tui] queda igual")
  assert.equal(ponerToml(out, "features", "hooks", true), out, "idempotente")
})

test("gap 18: al cambiar el valor se conserva el comentario de la línea", () => {
  const previo = '[features]\nhooks = false  # lo apagué yo a propósito\n'
  assert.equal(ponerToml(previo, "features", "hooks", true),
    '[features]\nhooks = true  # lo apagué yo a propósito\n')
  // Un `#` dentro de una cadena no es un comentario
  assert.equal(ponerToml('[tui]\ntheme = "azul#oscuro"\n', "tui", "theme", "verde"),
    '[tui]\ntheme = "verde"\n')
})

test("gap 16: desinstalar no RE-CREA la tabla que el usuario había borrado", () => {
  const tmp = tmpProj()
  try {
    const hogar = join(tmp, "home")
    mkdirSync(join(hogar, ".codex"), { recursive: true })
    const cfgToml = join(hogar, ".codex", "config.toml")
    const env = conPath(SIN_CLI, { HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "codex", "--scope", "user", "-y", "-q"], { env })
    // El usuario quita la tabla del plugin a mano
    const limpio = "# mi config\n[features]\nhooks = true\n"
    writeFileSync(cfgToml, limpio)
    cli(["uninstall", "-p", "codex", "--scope", "user", "-q"], { env })
    assert.equal(readFileSync(cfgToml, "utf8"), limpio,
      "uninstall volvió a crear la tabla del plugin (con enabled = false)")
    assert.equal(ponerToml(limpio, 'plugins."custom-agents@daycry"', "enabled", false, { soloSiExiste: true }),
      limpio)
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 14: `%VAR%` en cmd.exe

test("gap 14: un `%VAR%` en un argumento llega literal, no expandido", () => {
  assert.equal(argCmd("normal"), '"normal"')
  assert.ok(argCmd("%MISECRETO%").includes("^%"), "el % tiene que salir de las comillas y escaparse")
  if (process.platform !== "win32") return
  // Vuelta completa: lo que recibe el programa es exactamente lo que se le pasó
  const tmp = tmpProj()
  try {
    const eco = join(tmp, "eco.js")
    writeFileSync(eco, "console.log(JSON.stringify(process.argv.slice(2)))\n")
    const lanzador = join(tmp, "eco.cmd")
    writeFileSync(lanzador, `@echo off\r\n"${process.execPath}" "${eco}" %*\r\n`)
    const casos = ["%MISECRETO%", "C:\\con espacios\\x", "a%b"]
    const linea = [lanzador, ...casos].map(argCmd).join(" ")
    const out = execFileSync(process.env.COMSPEC || "cmd.exe", ["/d", "/s", "/c", `"${linea}"`],
      { encoding: "utf8", windowsVerbatimArguments: true, env: { ...process.env, MISECRETO: "FILTRADO" } })
    assert.deepEqual(JSON.parse(out.trim()), casos, "cmd.exe expandió una variable del entorno")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 15: los avisos no se pierden

test("gap 15: los avisos acumulados se imprimen aunque el paso siguiente reviente", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    writeFileSync(join(cfg, "settings.json"), "{,}", "utf8")
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    let err = null
    try { cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }) } catch (e) { err = e }
    assert.ok(err)
    const dicho = `${err.stdout || ""}${err.stderr || ""}`
    assert.match(dicho, /registro escrito en/,
      "el aviso de «sin claude en el PATH» explica el contexto del fallo: no se puede tragar")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap 19: nada de ficheros huecos

test("gap 19: un fichero del registro que YA existía se conserva (con su `version`)", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(join(cfg, "plugins"), { recursive: true })
    mkdirSync(hogar, { recursive: true })
    // El usuario ya tenía registro (otro plugin): ni el fichero ni `version` son nuestros
    writeFileSync(join(cfg, "plugins", "installed_plugins.json"),
      JSON.stringify({ version: 2, plugins: { "otro@mkt": [{ scope: "user" }] } }, null, 2))
    writeFileSync(join(cfg, "plugins", "known_marketplaces.json"),
      JSON.stringify({ otro: { autoUpdate: true } }, null, 2))
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })
    cli(["uninstall", "-p", "claude-code", "--scope", "user", "-q"], { env })

    const ip = JSON.parse(readFileSync(join(cfg, "plugins", "installed_plugins.json"), "utf8"))
    assert.equal(ip.version, 2, "`version` es del fichero del usuario: no se quita")
    assert.deepEqual(Object.keys(ip.plugins), ["otro@mkt"], "y su plugin sigue ahí")
    const km = JSON.parse(readFileSync(join(cfg, "plugins", "known_marketplaces.json"), "utf8"))
    assert.deepEqual(Object.keys(km), ["otro"])
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ================================================================== Revisión de dos lentes · intento 2
//
// Mismo contrato que el intento 1: un test (o varios) por gap, cada uno reproduciendo el escenario
// que describió la lente ANTES de la corrección.

import { spawn } from "node:child_process"
import { sep } from "node:path"
import { readdirSync } from "node:fs"
import {
  ponerEnTablaEnLinea, partirAsignacion, validarTimeout, fusionarRegistro, prefijoComun,
} from "../install/install.mjs"

const TABLA = 'plugins."custom-agents@daycry"'

/**
 * Valida un `config.toml` con el `tomllib` de Python (el mismo parser de referencia con el que se
 * reprodujo el gap B-1). Devuelve el valor de `plugins."custom-agents@daycry".enabled`, o `null` si
 * no hay Python: el test no puede exigir una herramienta que el contrato del instalador no pide.
 */
function tomllibEnabled(ruta) {
  const guion = "import tomllib,sys,json\n" +
    "d=tomllib.load(open(sys.argv[1],'rb'))\n" +
    "print(json.dumps(d.get('plugins',{}).get('custom-agents@daycry',{}).get('enabled')))\n"
  for (const py of ["python3", "python"]) {
    try {
      return JSON.parse(execFileSync(py, ["-c", guion, ruta],
        { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim())
    } catch (e) {
      if (e?.stderr && /tomllib|Traceback/.test(String(e.stderr))) {
        assert.fail(`el TOML resultante no parsea con tomllib:\n${e.stderr}`)
      }
    }
  }
  return null   // sin Python en esta máquina: la aserción de texto ya cubre la forma
}

/** Instala Codex en un HOME temporal partiendo de este `config.toml`. */
function instalarCodexCon(toml) {
  const tmp = tmpProj()
  const hogar = join(tmp, "home")
  mkdirSync(join(hogar, ".codex"), { recursive: true })
  const config = join(hogar, ".codex", "config.toml")
  writeFileSync(config, toml, "utf8")
  const env = conPath(SIN_CLI, { HOME: hogar, USERPROFILE: hogar })
  let salida = "", error = null
  try { salida = cli(["install", "-p", "codex", "--scope", "user", "-y"], { env }) } catch (e) { error = e }
  return { tmp, config, env, salida, error, texto: () => readFileSync(config, "utf8") }
}

// ------------------------------------------------------------------ gap B-1 (Critical): las otras
// dos formas VÁLIDAS de declarar la misma tabla en TOML

test("gap B-1: una clave con punto se modifica DONDE está, no se duplica la tabla", () => {
  assert.equal(ponerToml('plugins."custom-agents@daycry".enabled = false\n', TABLA, "enabled", true),
    'plugins."custom-agents@daycry".enabled = true\n')
  // La misma ruta con comillas simples y con comentario: se respeta todo menos el valor
  assert.equal(ponerToml("plugins.'custom-agents@daycry'.enabled = false  # lo apagué yo\n", TABLA, "enabled", true),
    "plugins.'custom-agents@daycry'.enabled = true  # lo apagué yo\n")
  // Si la tabla está declarada implícitamente por OTRA clave, la nueva va a su lado
  assert.equal(ponerToml('plugins."custom-agents@daycry".otra = 1\n', TABLA, "enabled", true),
    'plugins."custom-agents@daycry".otra = 1\nplugins."custom-agents@daycry".enabled = true\n')
})

test("gap B-1: una tabla en línea se edita DENTRO de las llaves", () => {
  assert.equal(ponerToml('[plugins]\n"custom-agents@daycry" = { enabled = false }\n', TABLA, "enabled", true),
    '[plugins]\n"custom-agents@daycry" = { enabled = true }\n')
  assert.equal(ponerToml('[plugins]\n"custom-agents@daycry" = {}\n', TABLA, "enabled", true),
    '[plugins]\n"custom-agents@daycry" = { enabled = true }\n')
  assert.equal(ponerToml('[plugins]\n"custom-agents@daycry" = { version = "1" }\n', TABLA, "enabled", true),
    '[plugins]\n"custom-agents@daycry" = { version = "1", enabled = true }\n')
  assert.equal(ponerEnTablaEnLinea(" { a = 1 }", "b", "true"), " { a = 1, b = true }")
  assert.equal(ponerEnTablaEnLinea(" 3", "b", "true"), null, "esto no es una tabla en línea")
  assert.equal(ponerEnTablaEnLinea(" { a = 1", "b", "true"), null, "sin cerrar: no se toca")
})

test("gap B-1: instalar sobre una clave con punto deja un config.toml que PARSEA", () => {
  const caso = instalarCodexCon('# mi config\nplugins."custom-agents@daycry".enabled = false\n\n[tui]\ntheme = "dark"\n')
  try {
    assert.equal(caso.error, null, "esta forma se puede arreglar sola: el paso no puede fallar")
    const out = caso.texto()
    assert.match(out, /plugins\."custom-agents@daycry"\.enabled = true/)
    assert.equal((out.match(/custom-agents@daycry/g) || []).length, 1,
      "una segunda declaración es justo lo que dejaba el fichero sin parsear")
    assert.match(out, /theme = "dark"/, "el resto del fichero se conserva")
    const enabled = tomllibEnabled(caso.config)
    if (enabled !== null) assert.equal(enabled, true, "tomllib tiene que leer enabled = true")
  } finally {
    rmSync(caso.tmp, { recursive: true, force: true })
  }
})

test("gap B-1: instalar sobre una tabla en línea deja un config.toml que PARSEA", () => {
  const caso = instalarCodexCon('[plugins]\n"custom-agents@daycry" = { enabled = false }\n')
  try {
    assert.equal(caso.error, null)
    const out = caso.texto()
    assert.match(out, /"custom-agents@daycry" = \{ enabled = true \}/)
    assert.ok(!/\[plugins\."custom-agents@daycry"\]/.test(out),
      "apendizar la cabecera daba «Cannot declare … twice» con exit 0 y mensaje de éxito")
    const enabled = tomllibEnabled(caso.config)
    if (enabled !== null) assert.equal(enabled, true)
  } finally {
    rmSync(caso.tmp, { recursive: true, force: true })
  }
})

test("gap B-1: si la tabla NO está declarada, se crea la cabecera (comportamiento de siempre)", () => {
  const caso = instalarCodexCon('# mi config\n[tui]\ntheme = "dark"\n')
  try {
    assert.equal(caso.error, null)
    assert.match(caso.texto(), /\[plugins\."custom-agents@daycry"\]\r?\nenabled = true/)
    const enabled = tomllibEnabled(caso.config)
    if (enabled !== null) assert.equal(enabled, true)
  } finally {
    rmSync(caso.tmp, { recursive: true, force: true })
  }
})

test("gap B-1: lo que no se puede editar con seguridad es error del paso y NO toca el fichero", () => {
  const previo = 'plugins = { "custom-agents@daycry" = { enabled = false } }\n'
  const caso = instalarCodexCon(previo)
  try {
    assert.ok(caso.error, "esto tiene que fallar, no «arreglarse» a ciegas")
    const dicho = `${caso.error.stdout || ""}${caso.error.stderr || ""}`
    assert.match(dicho, /config\.toml/, "hay que nombrar el fichero")
    assert.match(dicho, /ponlo tú/, "y el cambio que tiene que hacer a mano")
    assert.equal(caso.texto(), previo, "el fichero se queda EXACTAMENTE como estaba")
  } finally {
    rmSync(caso.tmp, { recursive: true, force: true })
  }
})

test("gap B-1: partirAsignacion lee claves con `@`, puntos y comillas", () => {
  assert.deepEqual(partirAsignacion('  plugins."a@b".enabled = false # c'),
    { sangria: "  ", bruta: 'plugins."a@b".enabled', resto: " false # c" })
  assert.equal(partirAsignacion("# solo un comentario"), null)
  assert.equal(partirAsignacion("[tabla]"), null)
})

// ------------------------------------------------------------------ gaps B-2 y B-13: un manifiesto
// de copy roto no puede tumbar el run entero

test("gap B-2/B-13: un manifiesto de copy sin `files` avisa y NO impide instalar los demás", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [join(proj, ".claude"), cfg, hogar]) mkdirSync(d, { recursive: true })
    // Manifiesto de un instalador viejo (o a medio escribir): sin `files`
    writeFileSync(join(proj, ".claude", MANIFEST),
      JSON.stringify({ plugin: "custom-agents", modo: "copy" }), "utf8")
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    const out = cli(["install", "-p", "claude-code,opencode", "--dir", proj, "-y"], { env })

    assert.match(out, /no puedo leerlo/, "hay que decir que ese manifiesto no sirve")
    assert.match(out, /límpialo a mano/)
    assert.ok(!/TypeError|at file:/.test(out), "un stack crudo en la cara del usuario, nunca")
    assert.ok(existsSync(join(proj, ".claude", MANIFEST_PLUGIN)), "claude-code sigue instalándose")
    assert.ok(existsSync(join(proj, ".opencode", "skills")),
      "y OpenCode se instala: un proveedor que falla no tumba a los demás")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap B-13: un manifiesto de copy ILEGIBLE se avisa con su ruta, no se ignora en silencio", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [join(proj, ".claude"), cfg, hogar]) mkdirSync(d, { recursive: true })
    writeFileSync(join(proj, ".claude", MANIFEST), "{ esto no es json", "utf8")
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    const out = cli(["install", "-p", "claude-code", "--dir", proj, "-y"], { env })
    assert.match(out, /no es JSON válido/)
    assert.match(out, /custom-agents-install\.json/, "con la ruta del fichero que hay que limpiar")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap B-3: el manifiesto parcial
// no se pierde con un segundo fallo

test("gap B-3: dos fallos seguidos no pierden el registro del primero (nada de plugin fantasma)", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    // 1.ª pasada: revienta en el ÚLTIMO json-set (settings.json) → registro con los dos primeros
    writeFileSync(join(cfg, "settings.json"), "{,}", "utf8")
    assert.throws(() => cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }))
    const ip1 = JSON.parse(readFileSync(join(cfg, "plugins", "installed_plugins.json"), "utf8"))
    assert.ok(ip1.plugins["custom-agents@daycry"], "la 1.ª pasada sí llegó a registrar el plugin")

    // 2.ª pasada: revienta ANTES (known_marketplaces.json ilegible) → su registro va vacío
    writeFileSync(join(cfg, "plugins", "known_marketplaces.json"), "{,}", "utf8")
    assert.throws(() => cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }))
    const man = JSON.parse(readFileSync(join(cfg, "plugins", MANIFEST_PLUGIN), "utf8"))
    assert.ok(man.registro.some((e) => String(e["json-set"] || "").endsWith("installed_plugins.json")),
      "reescribir el manifiesto perdía la única pista de lo que puso la pasada anterior")

    cli(["uninstall", "-p", "claude-code", "--scope", "user", "-q"], { env })
    assert.ok(!existsSync(join(cfg, "plugins", "installed_plugins.json")),
      "un `custom-agents@daycry` apuntando a un installPath borrado es un plugin FANTASMA")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap B-3: fusionarRegistro une sin duplicar y conserva `creado`", () => {
  const previo = [{ "json-set": "a.json", claves: ["x"], creado: true }, { exec: "claude plugin install" }]
  const nuevo = [{ "json-set": "a.json", claves: ["y"] }]
  const out = fusionarRegistro(previo, nuevo)
  assert.equal(out.length, 2, "el mismo fichero es UN apunte, no dos")
  assert.deepEqual(out[0].claves, ["x", "y"])
  assert.equal(out[0].creado, true, "si lo creamos nosotros alguna vez, sigue siendo nuestro")
  assert.deepEqual(fusionarRegistro([], nuevo), nuevo)
})

// ------------------------------------------------------------------ gap B-4: señales y manifiesto

test("gap B-4: matar el instalador a mitad de la copia deja manifiesto; uninstall no deja huérfanos", async () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [proj, cfg, hogar]) mkdirSync(d, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    const hijo = spawn(process.execPath, [CLI, "install", "-p", "claude-code", "--mode", "copy",
      "--dir", proj, "-y", "-q"], { env, stdio: "ignore" })
    const manRuta = join(proj, ".claude", MANIFEST)
    const fin = new Promise((res) => hijo.on("exit", res))
    const t0 = Date.now()
    while (Date.now() - t0 < 30_000 && !existsSync(manRuta)) await new Promise((r) => setTimeout(r, 2))
    hijo.kill("SIGKILL")          // en Windows es un TerminateProcess: no hay manejador que valga
    await fin

    assert.ok(existsSync(manRuta), "sin manifiesto, lo copiado se queda huérfano para siempre")
    const man = JSON.parse(readFileSync(manRuta, "utf8"))
    const vivos = man.files.filter((f) => existsSync(f.split("/").join(sep))).length
    if (vivos < man.files.length) assert.equal(man.estado, "incompleto", "se apunta ANTES de copiar")
    cli(["uninstall", "-p", "claude-code", "--dir", proj, "-q"], { env })
    for (const d of ["agents", "skills", "commands", "hooks"]) {
      assert.ok(!existsSync(join(proj, ".claude", d)), `quedaron huérfanos en ${d}`)
    }
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap B-4: los manejadores de señal se ponen al empezar y se sueltan al terminar", () => {
  const url = new URL("../install/install.mjs", import.meta.url).href
  const urlProv = new URL("../install/providers.mjs", import.meta.url).href
  const guion = `
    import { ejecutar } from ${JSON.stringify(url)}
    import { getProvider } from ${JSON.stringify(urlProv)}
    let dentro = 0
    const orig = process.stdout.write.bind(process.stdout)
    process.stdout.write = (...a) => { dentro = Math.max(dentro, process.listenerCount("SIGINT")); return orig(...a) }
    const antes = process.listenerCount("SIGINT")
    ejecutar(getProvider("opencode"), { dir: process.cwd(), scope: "project", modo: "plugin", dryRun: true })
    process.stdout.write = orig
    console.log(JSON.stringify({ antes, dentro, despues: process.listenerCount("SIGINT") }))
  `
  const out = execFileSync(process.execPath, ["--input-type=module", "-e", guion],
    { encoding: "utf8", env: { ...process.env, NO_COLOR: "1" } })
  const r = JSON.parse(out.trim().split("\n").pop())
  assert.equal(r.antes, 0)
  assert.ok(r.dentro >= 1, "durante la instalación TIENE que haber manejador de SIGINT")
  assert.equal(r.despues, 0, "y no se puede quedar puesto al acabar")
})

// ------------------------------------------------------------------ gaps B-5 y B-6: qué se sabe lanzar

test("gap B-5: una extensión que `correr()` no lanza es `no-ejecutable`, no `si`", () => {
  const previo = process.env.PATHEXT
  try {
    process.env.PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.WSF;.MSC;.PS1"
    for (const mala of ["C:\\bin\\claude.ps1", "C:\\bin\\claude.vbs", "C:\\bin\\claude.js",
      "C:\\bin\\claude.wsf", "C:\\bin\\claude.msc", "C:\\bin\\claude.cpl"]) {
      assert.deepEqual(elegirEjecutable([mala], "win32"), { ruta: mala, ejecutable: false },
        `${mala} no se puede lanzar desde Node: darlo por bueno era un EFTYPE`)
    }
    // Y si conviven, se coge la que sí se sabe lanzar
    assert.deepEqual(elegirEjecutable(["C:\\bin\\claude.ps1", "C:\\bin\\claude.cmd"], "win32"),
      { ruta: "C:\\bin\\claude.cmd", ejecutable: true })
  } finally {
    if (previo === undefined) delete process.env.PATHEXT
    else process.env.PATHEXT = previo
  }
})

test("gap B-5: con un `claude.ps1` en el PATH se usa el respaldo, no se intenta lanzar",
  { skip: process.platform !== "win32" ? "solo en Windows" : false }, () => {
    const tmp = tmpProj()
    try {
      const bin = join(tmp, "bin"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
      for (const d of [bin, cfg, hogar]) mkdirSync(d, { recursive: true })
      writeFileSync(join(bin, "claude.ps1"), "exit 0\n")
      const env = conPath([bin, SIN_CLI].join(delimiter), {
        CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar,
        PATHEXT: ".COM;.EXE;.BAT;.CMD;.VBS;.PS1",
      })
      const out = cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env })
      assert.match(out, /no ejecutable desde Node/)
      assert.ok(existsSync(join(cfg, "plugins", "installed_plugins.json")), "el respaldo tiene que entrar")
    } finally {
      rmSync(tmp, { recursive: true, force: true })
    }
  })

test("gap B-6: se recorre en el ORDEN de PATHEXT, que es el del intérprete de comandos", () => {
  const previo = process.env.PATHEXT
  const candidatos = ["C:\\bin\\claude.cmd", "C:\\bin\\claude.exe"]
  try {
    process.env.PATHEXT = ".COM;.EXE;.BAT;.CMD"          // el defecto de Windows
    assert.deepEqual(elegirEjecutable(candidatos, "win32"), { ruta: "C:\\bin\\claude.exe", ejecutable: true },
      "con el instalador nativo (.exe) y los shims de npm (.cmd) conviviendo, manda el .exe")
    delete process.env.PATHEXT                            // sin la variable, el mismo defecto
    assert.deepEqual(elegirEjecutable(candidatos, "win32"), { ruta: "C:\\bin\\claude.exe", ejecutable: true })
    process.env.PATHEXT = ".CMD;.EXE"                     // y si el usuario la cambia, se le hace caso
    assert.deepEqual(elegirEjecutable(candidatos, "win32"), { ruta: "C:\\bin\\claude.cmd", ejecutable: true })
  } finally {
    if (previo === undefined) delete process.env.PATHEXT
    else process.env.PATHEXT = previo
  }
})

// ------------------------------------------------------------------ gap B-7: escritura atómica

test("gap B-7: un fichero del registro VACÍO que ya existía es un error, no un `{}`", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    writeFileSync(join(cfg, "settings.json"), "   \n", "utf8")   // lo que deja una escritura cortada
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    let err = null
    try { cli(["install", "-p", "claude-code", "--scope", "user", "-y"], { env }) } catch (e) { err = e }
    assert.ok(err, "tratarlo como `{}` hacía invisible la pérdida del settings.json del usuario")
    assert.match(`${err.stdout || ""}${err.stderr || ""}`, /está vacío/)
    assert.equal(readFileSync(join(cfg, "settings.json"), "utf8"), "   \n", "y no se toca")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap B-7: un fichero que NO existe se crea (y no quedan temporales de la escritura atómica)", () => {
  const tmp = tmpProj()
  try {
    const cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    mkdirSync(cfg, { recursive: true })
    mkdirSync(hogar, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--scope", "user", "-y", "-q"], { env })
    const st = JSON.parse(readFileSync(join(cfg, "settings.json"), "utf8"))
    assert.equal(st.enabledPlugins["custom-agents@daycry"], true)
    const sueltos = [...readdirSync(cfg), ...readdirSync(join(cfg, "plugins"))].filter((f) => f.includes(".tmp-"))
    assert.deepEqual(sueltos, [], "el temporal de la escritura atómica se renombra, no se queda")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap B-8: los cambios locales

test("gap B-8: al migrar de copy a plugin, un fichero EDITADO por el usuario no se borra", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [proj, cfg, hogar]) mkdirSync(d, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--mode", "copy", "--dir", proj, "-y", "-q"], { env })
    const mio = join(proj, ".claude", "agents", "implementer.md")
    writeFileSync(mio, readFileSync(mio, "utf8") + "\n<!-- lo he tocado yo -->\n", "utf8")

    const out = cli(["install", "-p", "claude-code", "--dir", proj, "-y"], { env })
    assert.match(out, /cambios locales en 1 fichero/)
    assert.match(out, /implementer\.md/)
    assert.ok(existsSync(mio), "`-y` no es «bórrame lo que quieras»: el cambio del usuario se queda")
    assert.match(readFileSync(mio, "utf8"), /lo he tocado yo/)
    assert.ok(!existsSync(join(proj, ".claude", "agents", "reviewer.md")),
      "lo que NO tocó sí se limpia, como antes")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap A-1/B-10: poda por raíz

test("gap A-1/B-10: en scope project + plugin, uninstall no deja directorios vacíos en <cfg>/plugins", () => {
  const tmp = tmpProj()
  try {
    const proj = join(tmp, "proy"), cfg = join(tmp, "claude"), hogar = join(tmp, "home")
    for (const d of [proj, cfg, hogar]) mkdirSync(d, { recursive: true })
    const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
    cli(["install", "-p", "claude-code", "--dir", proj, "-y", "-q"], { env })
    assert.ok(existsSync(join(cfg, "plugins", "cache", "daycry")), "los ficheros van a <cfg>/plugins…")
    const ajeno = join(cfg, "plugins", "marketplaces", "otro-mkt")
    mkdirSync(ajeno, { recursive: true })

    cli(["uninstall", "-p", "claude-code", "--dir", proj, "-q"], { env })
    assert.ok(!existsSync(join(cfg, "plugins", "cache")), "…y la poda tiene que llegar hasta allí")
    assert.ok(!existsSync(join(cfg, "plugins", "marketplaces", "daycry")))
    assert.ok(existsSync(ajeno), "pero sin tocar un directorio ajeno")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap A-1/B-10: prefijoComun no se sube por encima de lo razonable", () => {
  assert.equal(prefijoComun([join("C:", "a", "b", "c"), join("C:", "a", "b", "d")]), join("C:", "a", "b"))
  assert.equal(prefijoComun([join("C:", "a"), join("C:", "b")]), null, "dos segmentos es demasiado arriba")
  assert.equal(prefijoComun([]), null)
})

// ------------------------------------------------------------------ gap B-9: barras antes de comillas

test("gap B-9: una ruta acabada en barra invertida no se come el argumento siguiente", () => {
  assert.equal(argCmd("C:\\mi clon\\"), '"C:\\mi clon\\\\"',
    "regla MSVCRT: las barras que preceden a una comilla se duplican")
  assert.equal(argCmd("sin barras"), '"sin barras"')
  if (process.platform !== "win32") return
  const tmp = tmpProj()
  try {
    const eco = join(tmp, "eco.js")
    writeFileSync(eco, "console.log(JSON.stringify(process.argv.slice(2)))\n")
    const lanzador = join(tmp, "eco.cmd")
    writeFileSync(lanzador, `@echo off\r\n"${process.execPath}" "${eco}" %*\r\n`)
    const casos = ["--source", "C:\\mi clon\\", "--scope", "user"]
    const linea = [lanzador, ...casos].map(argCmd).join(" ")
    const out = execFileSync(process.env.COMSPEC || "cmd.exe", ["/d", "/s", "/c", `"${linea}"`],
      { encoding: "utf8", windowsVerbatimArguments: true })
    assert.deepEqual(JSON.parse(out.trim()), casos, "la barra final se comía el --scope")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ------------------------------------------------------------------ gap B-11: timeout validado

test("gap B-11: un timeout que no es un entero > 0 avisa y cae al defecto", () => {
  assert.deepEqual(validarTimeout(undefined), { ms: 120_000, aviso: null })
  assert.deepEqual(validarTimeout(""), { ms: 120_000, aviso: null })
  assert.deepEqual(validarTimeout("5000"), { ms: 5000, aviso: null })
  for (const malo of ["-1", "0", "abc", "1.5"]) {
    const r = validarTimeout(malo)
    assert.equal(r.ms, 120_000, `${malo} tiene que caer al defecto, no hacer fallar todos los exec`)
    assert.match(r.aviso, /CUSTOM_AGENTS_EXEC_TIMEOUT_MS/)
  }
  const url = new URL("../install/install.mjs", import.meta.url).href
  const guion = `import { TIMEOUT_EXEC } from ${JSON.stringify(url)}; console.log(TIMEOUT_EXEC)`
  const leer = (v) => execFileSync(process.execPath, ["--input-type=module", "-e", guion],
    { encoding: "utf8", env: { ...process.env, CUSTOM_AGENTS_EXEC_TIMEOUT_MS: v } }).trim()
  assert.equal(leer("-1"), "120000", "`timeout out of range` hacía fallar hasta el respaldo")
  assert.equal(leer("0"), "120000")
})

// ------------------------------------------------------------------ gap B-12: matar el árbol

test("gap B-12: al expirar se mata el ÁRBOL y el mensaje dice cómo subir el timeout",
  { skip: process.platform !== "win32" ? "solo en Windows" : false }, async () => {
    const tmp = tmpProj()
    try {
      const hogar = join(tmp, "home"), bin = join(tmp, "bin")
      mkdirSync(join(hogar, ".codex"), { recursive: true })
      mkdirSync(bin)
      const marca = join(tmp, "el-nieto-siguio-vivo.txt")
      // El nieto (un `node`) escribe la marca a los 3 s: si al expirar solo se mata al `cmd.exe`,
      // sigue vivo y la marca aparece. Es el síntoma que se midió con `tasklist`.
      writeFileSync(join(bin, "codex.cmd"), [
        "@echo off",
        "if \"%~1\"==\"--version\" (echo codex-cli 0.130.0& exit /b 0)",
        `"${process.execPath}" -e "setTimeout(()=>require('fs').writeFileSync(process.env.MARCA,'vivo'),3000)"`,
        "exit /b 0",
        "",
      ].join("\r\n"))
      const env = conPath([bin, SIN_CLI].join(delimiter), {
        HOME: hogar, USERPROFILE: hogar, MARCA: marca, CUSTOM_AGENTS_EXEC_TIMEOUT_MS: "1000",
      })
      const out = cli(["install", "-p", "codex", "--scope", "user", "-y"], { env })
      assert.match(out, /expiró a los 1 s/, "un `ETIMEDOUT` pelado no dice nada al usuario")
      assert.match(out, /CUSTOM_AGENTS_EXEC_TIMEOUT_MS/)
      await new Promise((r) => setTimeout(r, 4000))
      assert.ok(!existsSync(marca), "el nieto sobrevivió al timeout: hay que matar el árbol")
    } finally {
      rmSync(tmp, { recursive: true, force: true })
    }
  })

// ================================================================== Revisión de dos lentes · intento 3
//
// Un Critical de la MISMA familia que B-1 (la tabla declarada de una cuarta forma) y dos Minor de
// la capa de escritura. El Critical NO se cierra añadiendo una quinta rama al editor: se cierra con
// una POST-CONDICIÓN (`ponerToml` comprueba lo que va a escribir), así que los tests van contra el
// RESULTADO, no contra la forma de entrada, y el oráculo de la tabla de abajo está escrito A MANO
// (no sale del analizador que se está probando) y refrendado por `tomllib` cuando hay Python.

import { openSync, closeSync, statSync } from "node:fs"
import { escribirAtomico, drenarAvisosEscritura } from "../install/install.mjs"

const BASE_TOML = 'model = "gpt-5"\n\n[mcp_servers.atlassian]\ncommand = "npx"\n'

/** Parsea un TOML con `tomllib` y devuelve el dict como objeto, o `null` si no hay Python. */
function tomllibLee(ruta) {
  const guion = "import tomllib,sys,json\nprint(json.dumps(tomllib.load(open(sys.argv[1],'rb'))))\n"
  for (const py of ["python3", "python"]) {
    try {
      return JSON.parse(execFileSync(py, ["-c", guion, ruta],
        { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim())
    } catch (e) {
      if (e?.stderr && /tomllib|Traceback/.test(String(e.stderr))) {
        assert.fail(`el TOML resultante no parsea con tomllib:\n${readFileSync(ruta, "utf8")}\n${e.stderr}`)
      }
    }
  }
  return null   // sin Python: quedan la tabla escrita a mano y las aserciones de texto
}

/** Escribe el texto en un temporal y se lo da a `tomllib` (que valida Y devuelve el contenido). */
function conTomllib(texto, fn) {
  const tmp = tmpProj()
  try {
    const f = join(tmp, "config.toml")
    writeFileSync(f, texto, "utf8")
    const d = tomllibLee(f)
    if (d !== null) fn(d)
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
}

/**
 * Las CINCO formas en que un `config.toml` real puede tener (o no) declarada la tabla del plugin.
 * `espera` es el texto EXACTO que tiene que quedar tras la primera pasada, fijado a mano leyendo
 * la especificación de TOML — no generado con `ponerToml`.
 */
const FORMAS = [
  {
    nombre: "sin declarar",
    entrada: BASE_TOML,
    espera: BASE_TOML + '\n[plugins."custom-agents@daycry"]\nenabled = true\n',
  },
  {
    nombre: "cabecera",
    entrada: BASE_TOML + '\n[plugins."custom-agents@daycry"]\nenabled = false\n',
    espera: BASE_TOML + '\n[plugins."custom-agents@daycry"]\nenabled = true\n',
  },
  {
    nombre: "clave con punto",
    entrada: 'plugins."custom-agents@daycry".enabled = false\n' + BASE_TOML,
    espera: 'plugins."custom-agents@daycry".enabled = true\n' + BASE_TOML,
  },
  {
    nombre: "tabla en linea",
    entrada: BASE_TOML + '\n[plugins]\n"custom-agents@daycry" = { enabled = false }\n',
    espera: BASE_TOML + '\n[plugins]\n"custom-agents@daycry" = { enabled = true }\n',
  },
  {
    // La 4.ª forma de la familia (gap I3-1): la tabla existe SOLO porque hay una sub-tabla suya.
    // `enabled` NO puede caer dentro de `env`; la super-tabla se declara después, que TOML permite.
    nombre: "sub-tabla implicita",
    entrada: BASE_TOML + '\n[plugins."custom-agents@daycry".env]\nMI_VAR = "1"\n',
    espera: BASE_TOML + '\n[plugins."custom-agents@daycry".env]\nMI_VAR = "1"\n' +
      '\n[plugins."custom-agents@daycry"]\nenabled = true\n',
  },
]

for (const forma of FORMAS) {
  test(`gap I3-1: forma «${forma.nombre}» — dos pasadas y uninstall dejan el TOML sano`, () => {
    const p1 = ponerToml(forma.entrada, TABLA, "enabled", true, { fichero: "config.toml" })
    assert.equal(p1, forma.espera, "la primera pasada no coincide con el resultado fijado a mano")

    const p2 = ponerToml(p1, TABLA, "enabled", true, { fichero: "config.toml" })
    assert.equal(p2, p1, "la segunda pasada (la ruta normal de actualizacion) tiene que ser idempotente")

    // `uninstall` no re-crea nada, pero sí apaga lo que dejó puesto la instalación.
    const un = ponerToml(p2, TABLA, "enabled", false, { soloSiExiste: true, fichero: "config.toml" })
    assert.match(un, /enabled = false/)

    for (const [pase, texto, valor] of [["1", p1, true], ["2", p2, true], ["uninstall", un, false]]) {
      conTomllib(texto, (d) => {
        assert.equal(d.plugins?.["custom-agents@daycry"]?.enabled, valor,
          `${forma.nombre} · pase ${pase}: tomllib no ve el valor donde Codex lo busca`)
        assert.equal(d.model, "gpt-5", "se ha perdido una clave del usuario")
        assert.equal(d.mcp_servers?.atlassian?.command, "npx", "se han perdido los mcp_servers")
        if (forma.nombre === "sub-tabla implicita") {
          assert.equal(d.plugins["custom-agents@daycry"].env?.MI_VAR, "1", "la sub-tabla del usuario se ha perdido")
        }
      })
    }
  })
}

test("gap I3-1: `features.hooks` con [features.web] declarado cae en features, no en features.web", () => {
  const entrada = BASE_TOML + "\n[features.web]\nsearch = true\n"
  const p1 = ponerToml(entrada, "features", "hooks", true, { fichero: "config.toml" })
  assert.equal(p1, entrada + "\n[features]\nhooks = true\n")
  assert.equal(ponerToml(p1, "features", "hooks", true, {}), p1, "segunda pasada")
  conTomllib(p1, (d) => {
    assert.equal(d.features.hooks, true)
    assert.equal(d.features.web.search, true, "la sub-tabla del usuario se ha perdido")
  })
})

test("gap I3-1: la post-condicion NO escribe si la clave no habria quedado unica", () => {
  // Un fichero con la clave declarada dos veces: el editor cambiaría UNA y el resultado seguiría
  // teniendo dos declaraciones. Antes se escribía igual; ahora el paso falla y no toca nada.
  const roto = '[plugins."custom-agents@daycry"]\nenabled = false\nenabled = false\n'
  assert.throws(() => ponerToml(roto, TABLA, "enabled", true, { fichero: "config.toml" }),
    (e) => /no toco el fichero/.test(e.message) && /2 veces/.test(e.message) &&
      /config\.toml/.test(e.message) && /plugins\."custom-agents@daycry"\.enabled/.test(e.message))
})

test("gap I3-1: instalar de verdad sobre la sub-tabla implicita — dos pasadas y uninstall", () => {
  const caso = instalarCodexCon(BASE_TOML + '\n[plugins."custom-agents@daycry".env]\nMI_VAR = "1"\n')
  try {
    assert.equal(caso.error, null, "esta forma se arregla sola: el paso no puede fallar")
    const tras1 = tomllibLee(caso.config)
    if (tras1 !== null) {
      assert.equal(tras1.plugins["custom-agents@daycry"].enabled, true,
        "el instalador decia «223 pasos aplicados» con el enabled DENTRO de env")
      assert.equal(tras1.plugins["custom-agents@daycry"].env.MI_VAR, "1")
      assert.equal(tras1.model, "gpt-5")
    }
    cli(["install", "-p", "codex", "--scope", "user", "-y"], { env: caso.env })   // 2.ª pasada
    const tras2 = tomllibLee(caso.config)
    if (tras2 !== null) {
      assert.equal(tras2.plugins["custom-agents@daycry"].enabled, true)
      assert.equal(tras2.model, "gpt-5", "la 2.a pasada perdia `model` y `mcp_servers`")
      assert.equal(tras2.mcp_servers.atlassian.command, "npx")
    }
    cli(["uninstall", "-p", "codex", "--scope", "user", "-q"], { env: caso.env })
    const tras3 = tomllibLee(caso.config)
    if (tras3 !== null) {
      assert.equal(tras3.plugins["custom-agents@daycry"].enabled, false)
      assert.equal(tras3.model, "gpt-5")
    }
  } finally {
    rmSync(caso.tmp, { recursive: true, force: true })
  }
})

test("gap I3-2: con el destino abierto por otro proceso se escribe igual, y se dice", () => {
  const tmp = tmpProj()
  try {
    const p = join(tmp, "settings.json")
    writeFileSync(p, "viejo\n", "utf8")
    drenarAvisosEscritura()
    const fd = openSync(p, "r")           // en Windows esto hace que el `rename` dé EPERM
    try {
      escribirAtomico(p, "nuevo\n")       // antes del arreglo: EPERM y la instalación al suelo
      assert.equal(readFileSync(p, "utf8"), "nuevo\n")
    } finally {
      closeSync(fd)
    }
    const avisos = drenarAvisosEscritura()
    if (process.platform === "win32") {
      assert.equal(avisos.length, 1, "perder la atomicidad sin decirlo es peor que el fallo")
      assert.match(avisos[0], /sin atomicidad/)
      assert.match(avisos[0], /EPERM|EACCES|EBUSY/)
      assert.ok(avisos[0].includes(p), "el aviso tiene que nombrar el fichero")
    } else {
      assert.equal(avisos.length, 0, "en POSIX el rename con el fichero abierto funciona: no hay aviso")
    }
    assert.equal(readdirSync(tmp).length, 1, "no puede quedar ningun temporal por el camino")
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

test("gap I3-3: el rename no puede cambiarle los permisos al fichero del usuario", () => {
  const tmp = tmpProj()
  try {
    const p = join(tmp, "settings.json")
    writeFileSync(p, "{}\n", "utf8")
    chmodSync(p, 0o600)
    const antes = statSync(p).mode & 0o7777
    escribirAtomico(p, '{"a":1}\n')
    const despues = statSync(p).mode & 0o7777
    assert.equal(despues.toString(8), antes.toString(8),
      "el rename sustituye el inodo: un settings.json en 600 acababa en 644")
    // En Windows solo existe el bit de solo-lectura (0600 se lee como 0666), así que la igualdad
    // de arriba es lo único comprobable ahí; el valor exacto solo se puede exigir en POSIX.
    if (process.platform !== "win32") assert.equal(despues, 0o600)
  } finally {
    rmSync(tmp, { recursive: true, force: true })
  }
})

// ============================================== revisión I2 · estado EFECTIVO del registro
//
// El hilo de los gaps B-1/B-2/A-3/B-7: «hay un apunte en algún fichero» no es «este plugin está
// activo para esta carpeta». `leerRegistro` recorre TODOS los descriptores y resuelve con las
// mismas reglas que `estado_plugin()` de `agent-kits/shared/doctor.py`.

test("gap B-5: fusionar una lista sobre un valor del usuario no lo hace desaparecer", () => {
  drenarAvisosEscritura()
  // escalar: se conserva DELANTE (sigue siendo suyo) y se avisa
  const [out, add] = fusionar({ plugin: "mi-plugin.js" }, { plugin: ["./nuestro.js"] })
  assert.deepEqual(out.plugin, ["mi-plugin.js", "./nuestro.js"])
  assert.deepEqual(add, ["plugin"])
  let avisos = drenarAvisosEscritura()
  assert.equal(avisos.length, 1)
  assert.match(avisos[0], /plugin: tu valor "mi-plugin\.js" no era una lista/)

  // objeto: no se puede convertir sin cambiar lo que significa → no se toca, y se dice
  const [out2, add2] = fusionar({ plugin: { a: 1 } }, { plugin: ["./nuestro.js"] })
  assert.deepEqual(out2.plugin, { a: 1 }, "la clave del usuario se queda como estaba")
  assert.deepEqual(add2, [])
  avisos = drenarAvisosEscritura()
  assert.equal(avisos.length, 1)
  assert.match(avisos[0], /no es una lista y no puedo añadirle/)

  // y lo de siempre sigue igual: lista sobre lista, unión sin duplicar y sin avisos
  const [out3] = fusionar({ plugin: ["./nuestro.js"] }, { plugin: ["./nuestro.js"] })
  assert.deepEqual(out3.plugin, ["./nuestro.js"])
  assert.deepEqual(drenarAvisosEscritura(), [])
})

test("gap B-5: instalar en OpenCode conserva el `plugin` escalar del usuario y lo avisa", () => {
  const proj = tmpProj()
  try {
    writeFileSync(join(proj, "opencode.json"), JSON.stringify({ plugin: "mi-plugin.js" }))
    const salida = cli(["install", "-p", "opencode", "-y", "--dir", proj])
    const cfg = JSON.parse(readFileSync(join(proj, "opencode.json"), "utf8"))
    assert.deepEqual(cfg.plugin, ["mi-plugin.js", rutaPluginOpencode(join(proj, ".opencode"), "project")],
      "el plugin del usuario no desaparece, y va el primero")
    assert.match(salida, /no era una lista/, "y se le dice lo que ha pasado con su clave")
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("gap A-3: leerRegistro mira TODOS los descriptores y un `false` explícito manda", () => {
  const proj = tmpProj()
  try {
    const instalados = join(proj, "installed_plugins.json")
    const ajustes = join(proj, "settings.json")
    writeFileSync(instalados, JSON.stringify(
      { version: 2, plugins: { "custom-agents@daycry": [{ scope: "user", version: "1.0.0" }] } }))
    const desc = [
      { fichero: instalados, tipo: "json-instalados", ruta: "plugins", clave: "custom-agents@daycry", scope: "user" },
      { fichero: ajustes, tipo: "json-prefijo", ruta: "enabledPlugins", clave: "custom-agents@daycry" },
    ]
    assert.equal(leerRegistro(desc).registrado, true, "alta sin `enabledPlugins`: cuenta")

    writeFileSync(ajustes, JSON.stringify({ enabledPlugins: { "custom-agents@daycry": false } }))
    const apagado = leerRegistro(desc)
    assert.equal(apagado.registrado, false, "el `false` del segundo descriptor manda sobre el alta del primero")
    assert.equal(apagado.apagadoEn, ajustes)

    // gap B-7: solo `true` habilita; cualquier otro valor es un valor inválido, no un alta
    for (const v of [0, null, "", "false", "true"]) {
      writeFileSync(ajustes, JSON.stringify({ enabledPlugins: { "custom-agents@daycry": v } }))
      const r = leerRegistro([desc[1]])
      assert.equal(r.registrado, false, `valor ${JSON.stringify(v)} no habilita`)
      assert.equal(r.invalidoEn, ajustes)
    }

    // gap B-3: otro marketplace no influye
    writeFileSync(ajustes, JSON.stringify({ enabledPlugins: { "custom-agents@otro": false } }))
    assert.equal(leerRegistro([desc[1]]).registrado, false)
    assert.equal(leerRegistro([desc[1]]).apagadoEn, null, "`custom-agents@otro` no apaga el nuestro")
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("gap B-1: una entrada de `installed_plugins.json` solo vale para SU scope y SU proyecto", () => {
  const proj = tmpProj()
  const otro = tmpProj()
  try {
    const instalados = join(proj, "installed_plugins.json")
    const desc = (scope, dir) => [{
      fichero: instalados, tipo: "json-instalados", ruta: "plugins",
      clave: "custom-agents@daycry", scope, proyecto: resolve(dir),
    }]
    const escribir = (e) => writeFileSync(instalados, JSON.stringify(
      { version: 2, plugins: { "custom-agents@daycry": [e] } }))

    escribir({ scope: "project", projectPath: otro, version: "1.0.0" })
    assert.equal(leerRegistro(desc("project", proj)).registrado, false,
      "un alta hecha desde OTRO proyecto no registra esta carpeta")
    assert.equal(leerRegistro(desc("user", proj)).registrado, false,
      "ni cuenta como alta de usuario")

    escribir({ scope: "project", projectPath: proj, version: "1.0.0" })
    assert.equal(leerRegistro(desc("project", proj)).registrado, true)

    escribir({ scope: "user", version: "1.0.0" })
    assert.equal(leerRegistro(desc("user", proj)).registrado, true)
    assert.equal(leerRegistro(desc("project", proj)).registrado, false,
      "una entrada de usuario no es el registro del scope `project`")
  } finally {
    for (const d of [proj, otro]) rmSync(d, { recursive: true, force: true })
  }
})

test("gap B-2: instalado por la vía sin CLI en scope project, `status` lo ve (y el de otro proyecto, no)", () => {
  const proj = tmpProj()
  const otro = tmpProj()
  const cfg = tmpProj()
  const hogar = join(cfg, "home")
  mkdirSync(hogar, { recursive: true })
  const env = conPath(SIN_CLI, { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
  try {
    cli(["install", "-p", "claude-code", "--scope", "project", "-y", "--dir", proj, "-q"], { env })
    const ip = JSON.parse(readFileSync(join(cfg, "plugins", "installed_plugins.json"), "utf8"))
    assert.equal(ip.plugins["custom-agents@daycry"][0].projectPath, resolve(proj),
      "la entrada dice a qué proyecto pertenece: sin eso no se puede atribuir")
    assert.match(cli(["status", "--dir", proj], { env }), /project: registrado: sí/)
    // el MISMO registro, desde otro proyecto: no es suyo
    const desdeOtro = cli(["status", "--dir", otro], { env })
    assert.doesNotMatch(desdeOtro, /project: registrado: sí/,
      "un alta de scope project de otra carpeta no puede dar por instalada esta")
  } finally {
    for (const d of [proj, otro, cfg]) rmSync(d, { recursive: true, force: true })
  }
})

test("gap A-3: `status` dice que está APAGADO en vez de un «no» a secas", () => {
  const proj = tmpProj()
  const cfg = tmpProj()
  const env = { ...process.env, NO_COLOR: "1", CLAUDE_CONFIG_DIR: cfg }
  try {
    mkdirSync(join(cfg, "plugins"), { recursive: true })
    writeFileSync(join(cfg, "plugins", "installed_plugins.json"), JSON.stringify(
      { version: 2, plugins: { "custom-agents@daycry": [{ scope: "user", version: VERSION }] } }))
    writeFileSync(join(cfg, "settings.json"), JSON.stringify(
      { enabledPlugins: { "custom-agents@daycry": false } }))
    const s = cli(["status", "--dir", proj], { env })
    assert.match(s, /user: registrado: no/)
    assert.match(s, /APAGADO/, "y dice por qué, que es lo que el usuario tiene que arreglar")
  } finally {
    for (const d of [proj, cfg]) rmSync(d, { recursive: true, force: true })
  }
})

// ====================================== revisión I2 · intento 3: la pila de precedencia entera
//
// `enabledPlugins` se puede escribir en CUALQUIER fichero de ajustes
// (`settings-reference#enabledplugins`: «Scope: Any file») y manda el de más arriba
// (`settings#settings-precedence`: «Managed > command line > Project local > Shared project >
// User»). `.claude/settings.local.json` es donde escribe `claude plugin disable --scope local`:
// leer solo `settings.json` daba «registrado: sí» con el plugin apagado.

test("gap I2-1: un `false` en `local` manda sobre el `true` de `project` y de `user`", () => {
  const proj = tmpProj()
  try {
    const f = (n) => join(proj, n)
    const desc = [
      { fichero: f("user.json"), tipo: "json-prefijo", ruta: "enabledPlugins", clave: "custom-agents@daycry", nivel: "user" },
      { fichero: f("project.json"), tipo: "json-prefijo", ruta: "enabledPlugins", clave: "custom-agents@daycry", nivel: "project" },
      { fichero: f("local.json"), tipo: "json-prefijo", ruta: "enabledPlugins", clave: "custom-agents@daycry", nivel: "local" },
      { fichero: f("managed.json"), tipo: "json-prefijo", ruta: "enabledPlugins", clave: "custom-agents@daycry", nivel: "managed" },
    ]
    const poner = (n, v) => writeFileSync(f(n), JSON.stringify({ enabledPlugins: { "custom-agents@daycry": v } }))

    poner("user.json", true)
    poner("project.json", true)
    assert.equal(leerRegistro(desc).registrado, true, "sin `local` manda `project`")

    poner("local.json", false)
    const apagado = leerRegistro(desc)
    assert.equal(apagado.registrado, false, "`local` está por encima de `project` y de `user`")
    assert.equal(apagado.apagadoEn, f("local.json"), "y se dice EN QUÉ fichero está apagado")

    // y al revés: `local` también manda para activar
    poner("local.json", true)
    poner("project.json", false)
    const activo = leerRegistro(desc)
    assert.equal(activo.registrado, true)
    assert.equal(activo.donde, f("local.json"))

    // `managed` (la organización) manda sobre todos
    poner("managed.json", false)
    assert.equal(leerRegistro(desc).apagadoEn, f("managed.json"))
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("gap I2-1: `status` ve el apagado de `.claude/settings.local.json`", () => {
  const proj = tmpProj()
  const cfg = tmpProj()
  const env = { ...process.env, NO_COLOR: "1", CLAUDE_CONFIG_DIR: cfg }
  try {
    mkdirSync(join(cfg, "plugins"), { recursive: true })
    writeFileSync(join(cfg, "plugins", "installed_plugins.json"), JSON.stringify(
      { version: 2, plugins: { "custom-agents@daycry": [{ scope: "user", version: VERSION }] } }))
    writeFileSync(join(cfg, "settings.json"), JSON.stringify(
      { enabledPlugins: { "custom-agents@daycry": true } }))
    mkdirSync(join(proj, ".claude"), { recursive: true })
    writeFileSync(join(proj, ".claude", "settings.local.json"), JSON.stringify(
      { enabledPlugins: { "custom-agents@daycry": false } }))
    const s = cli(["status", "--dir", proj], { env })
    assert.doesNotMatch(s, /registrado: sí/, "apagado en `local`: no está activo para esta carpeta")
    assert.match(s, /APAGADO/)
    assert.match(s, /settings\.local\.json/, "y se nombra el fichero que manda")
  } finally {
    for (const d of [proj, cfg]) rmSync(d, { recursive: true, force: true })
  }
})

test("gap I2-6: `local` es scope de proyecto (exige `projectPath`) y un scope raro no cuenta", () => {
  const proj = tmpProj()
  try {
    const instalados = join(proj, "installed_plugins.json")
    const desc = (scope) => [{
      fichero: instalados, tipo: "json-instalados", ruta: "plugins",
      clave: "custom-agents@daycry", scope, proyecto: resolve(proj),
    }]
    const escribir = (e) => writeFileSync(instalados, JSON.stringify(
      { version: 2, plugins: { "custom-agents@daycry": [e] } }))

    escribir({ scope: "local", version: "1.0.0" })
    assert.equal(leerRegistro(desc("project")).registrado, false, "`local` sin `projectPath` no se atribuye")
    escribir({ scope: "local", projectPath: proj, version: "1.0.0" })
    assert.equal(leerRegistro(desc("project")).registrado, true, "`local` con SU proyecto sí cuenta")
    assert.equal(leerRegistro(desc("user")).registrado, false, "y no es un alta de usuario")

    // un scope que no es ninguno de los tres documentados NO cae al lado permisivo
    for (const scope of ["raro", "", 7, undefined]) {
      escribir({ scope, projectPath: proj, version: "1.0.0" })
      assert.equal(leerRegistro(desc("project")).registrado, false, `scope ${JSON.stringify(scope)}`)
      assert.equal(leerRegistro(desc("user")).registrado, false, `scope ${JSON.stringify(scope)} como user`)
    }
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("gap I2-2/I2-7: `mismaRuta` no lanza con un valor que no es cadena y resuelve enlaces", () => {
  const proj = tmpProj()
  try {
    for (const v of [123, null, undefined, ["x"], { a: 1 }, true]) {
      assert.equal(mismaRuta(v, proj), false, `${JSON.stringify(v)} no casa con nada`)
      assert.equal(mismaRuta(proj, v), false)
    }
    assert.equal(mismaRuta(proj, proj), true)
    assert.equal(mismaRuta(proj + sep, proj), true, "una barra de más es la misma carpeta")
    // una ruta que todavía no existe no se puede resolver: se cae al valor original, no a `false`
    const futura = join(proj, "aun-no")
    assert.equal(mismaRuta(futura, futura), true)
  } finally {
    rmSync(proj, { recursive: true, force: true })
  }
})

test("gap I2-4: los pasos `exec` se lanzan EN `--dir`, así que la CLI registra ese proyecto", () => {
  const proj = tmpProj()
  const cfg = tmpProj()
  const bin = mkdtempSync(join(tmpdir(), "ca-bin-"))
  const hogar = join(cfg, "home")
  mkdirSync(hogar, { recursive: true })
  claudeFalso(bin)
  const env = conPath([bin, SIN_CLI].join(delimiter),
    { CLAUDE_CONFIG_DIR: cfg, HOME: hogar, USERPROFILE: hogar })
  try {
    // el instalador se lanza desde OTRA carpeta (como un `npx` desde el repo de turno)
    const salida = cli(["install", "-p", "claude-code", "--scope", "project", "-y", "--dir", proj],
      { env, cwd: bin })
    assert.match(salida, /plugin install/, "se pasó por la CLI, no por el respaldo")
    const ip = JSON.parse(readFileSync(join(cfg, "plugins", "installed_plugins.json"), "utf8"))
    assert.equal(ip.plugins["custom-agents@daycry"][0].projectPath, resolve(proj),
      "la CLI toma el proyecto del cwd: sin `cwd: dir` grababa la carpeta desde la que se lanzó `npx`")
    assert.match(cli(["status", "--dir", proj], { env }), /project: registrado: sí/,
      "y por eso `status` lo ve: antes decía «2 pasos aplicados» y «registrado: no»")
  } finally {
    for (const d of [proj, cfg, bin]) rmSync(d, { recursive: true, force: true })
  }
})

test("gap I2-4: ningún paso `exec` de ningún proveedor se queda sin `cwd`", () => {
  const dir = tmpProj()
  try {
    for (const p of PROVIDERS) {
      for (const scope of ["project", "user"]) {
        const plan = buildPlan(p, { dir, scope, root: ROOT, version: VERSION, cli: { claude: true, codex: true } })
        for (const paso of plan.filter((s) => s.type === "exec")) {
          assert.equal(paso.cwd, dir, `${p.id}/${scope}: ${[paso.cmd, ...paso.args].join(" ")} sin cwd`)
        }
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
})
