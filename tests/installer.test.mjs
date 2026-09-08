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
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs"
import { tmpdir, homedir } from "node:os"
import { join, dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { execFileSync } from "node:child_process"

import { parseArgs, fusionar, ficherosDe } from "../install/install.mjs"
import { PROVIDERS, IDS, getProvider, buildPlan, MANIFEST, GLOBAL_DIR } from "../install/providers.mjs"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const CLI = join(ROOT, "install", "install.mjs")

const tmpProj = () => mkdtempSync(join(tmpdir(), "ca-install-"))
const cli = (args, opts = {}) =>
  execFileSync(process.execPath, [CLI, ...args], { encoding: "utf8", env: { ...process.env, NO_COLOR: "1" }, ...opts })

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
      assert.ok(["copy", "merge", "write"].includes(paso.type), `${p.id}: paso raro ${paso.type}`)
      assert.ok(paso.to, `${p.id}: paso sin destino`)
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
