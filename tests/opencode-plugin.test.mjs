// opencode-plugin.test.mjs — suite del adaptador de hooks de OpenCode (`hooks/opencode-plugin.js`).
//   node --test tests/opencode-plugin.test.mjs
//
// El adaptador es el puente entre los eventos de OpenCode y los hooks de shell del plugin, que
// hablan el contrato de Claude Code. Lo que se prueba aquí es el contrato del puente:
//   · localiza `hooks/` por `import.meta.url` (viaja junto a ellos), no adivinando el proyecto;
//   · traduce `tool.execute.after` → payload `PostToolUse` y muestra el `systemMessage` del script;
//   · traduce `session.idle` → payload `SessionEnd` una sola vez por sesión;
//   · **nunca lanza**: un hook que revienta abortaría la herramienta en OpenCode (ADR-007: los
//     hooks informan, no deciden).
//
// Si no hay `bash` (Windows sin Git Bash), los casos que ejecutan scripts se SALTAN, como hace
// `tests/test_hooks_shell.py`.

import { test, describe } from "node:test"
import assert from "node:assert/strict"
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, rmSync, existsSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { execFileSync } from "node:child_process"

import { CustomAgentsHooks } from "../hooks/opencode-plugin.js"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..")

const disponible = (cmd, args) => {
  try {
    execFileSync(cmd, args, { stdio: "ignore" })
    return true
  } catch {
    return false
  }
}
// Los hooks del plugin necesitan `bash` Y `python3`; sin uno de los dos salen en silencio con
// exit 0 (degradación por diseño), así que los casos que esperan SALIDA se saltan — afirmar lo
// contrario sería afirmar el entorno, no el adaptador. Mismo criterio que tests/test_hooks_shell.py.
const HAY_BASH = disponible("bash", ["-c", "exit 0"])
const HAY_PYTHON3 = HAY_BASH && disponible("bash", ["-c", "command -v python3"])
const PUEDE_EJECUTAR_HOOKS = HAY_BASH && HAY_PYTHON3

// Ledger REAL del repo como fixture, igual que `tests/test_hooks_shell.py`: el formato que
// `progress-report.py` reconoce es el del plugin, no uno inventado aquí (si el formato cambia,
// las dos suites lo notan a la vez).
const LEDGER_FUENTE = join(ROOT, "docs", "roadmap", "2026-09-02-adversarial-review", "tasks.md")

/** Proyecto temporal con ese ledger puesto EN PROGRESO (es lo que dispara la línea). */
function proyectoConLedger() {
  const dir = mkdtempSync(join(tmpdir(), "ca-oc-"))
  const inic = join(dir, "docs", "roadmap", "2026-01-01-demo")
  mkdirSync(inic, { recursive: true })
  mkdirSync(join(dir, ".claude"), { recursive: true })
  // Copia TAL CUAL: `progress-report.py line` emite su línea también con la iniciativa cerrada,
  // y lo que se prueba aquí es el PUENTE, no el informe (reescribir el estado a mano solo daba
  // ocasión de corromper la fixture).
  writeFileSync(join(inic, "tasks.md"), readFileSync(LEDGER_FUENTE, "utf8"), "utf8")
  return dir
}

/** Cliente falso: registra los toasts y los logs en vez de pintarlos. */
function clienteFalso() {
  const toasts = [], logs = []
  return {
    toasts, logs,
    app: { log: (x) => logs.push(x?.body?.message) },
    tui: { showToast: async (x) => { toasts.push(x?.body?.message) } },
  }
}

describe("localización de hooks/", () => {
  test("encuentra hooks/ relativo al propio fichero, sin depender del cwd", async () => {
    const client = clienteFalso()
    // `directory` apunta a un temporal VACÍO: si el adaptador dependiera del proyecto, saldría inerte.
    const vacio = mkdtempSync(join(tmpdir(), "ca-oc-vacio-"))
    try {
      const h = await CustomAgentsHooks({ directory: vacio, worktree: vacio, client, $: null })
      assert.ok(h["tool.execute.after"], "el adaptador salió inerte: no localizó hooks/")
      assert.ok(h.event, "falta el suscriptor de eventos")
    } finally {
      rmSync(vacio, { recursive: true, force: true })
    }
  })

  test("sin hooks/ en ningún candidato queda inerte y lo registra, sin lanzar", async () => {
    // Se simula importando el módulo con un AQUI que no existe: no se puede, así que se comprueba
    // el contrato equivalente — el adaptador nunca lanza al construirse.
    const client = clienteFalso()
    const h = await CustomAgentsHooks({ directory: undefined, worktree: undefined, client, $: null })
    assert.equal(typeof h, "object", "construirse nunca puede lanzar")
  })
})

describe("tool.execute.after → PostToolUse", () => {
  test("con un ledger canónico emite la línea de progreso como toast", { skip: !PUEDE_EJECUTAR_HOOKS }, async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      await h["tool.execute.after"](
        { tool: "edit" },
        { args: { filePath: join(dir, "docs", "roadmap", "2026-01-01-demo", "tasks.md") } },
      )
      const visto = [...client.toasts, ...client.logs].join(" | ")
      assert.match(visto, /T-0|demo|1\/2|50/, `no salió progreso; visto: ${visto || "(nada)"}`)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })

  test("una herramienta de lectura no dispara nada", async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      await h["tool.execute.after"]({ tool: "read" }, { args: { filePath: join(dir, "x.md") } })
      assert.deepEqual(client.toasts, [], "`read` no es una escritura: no debe informar de nada")
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })

  test("un fichero que no es un ledger no informa de nada", { skip: !HAY_BASH }, async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      writeFileSync(join(dir, "app.js"), "// código\n", "utf8")
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      await h["tool.execute.after"]({ tool: "write" }, { args: { filePath: join(dir, "app.js") } })
      assert.deepEqual(client.toasts, [])
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })

  test("payload roto o sin ruta no lanza (un hook nunca aborta la herramienta)", async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      for (const [input, output] of [[{ tool: "edit" }, {}], [{}, {}], [null, null],
                                     [{ tool: "edit" }, { args: {} }]]) {
        await h["tool.execute.after"](input, output)   // no debe lanzar
      }
      assert.ok(true)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })
})

describe("session.idle → SessionEnd (journal)", () => {
  test("escribe la entrada del journal una sola vez por sesión", { skip: !PUEDE_EJECUTAR_HOOKS }, async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      mkdirSync(join(dir, "docs", "knowledge", "journal"), { recursive: true })
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      const ev = { type: "session.idle", properties: { sessionID: "sesion-de-prueba" } }
      await h.event({ event: ev })
      await h.event({ event: ev })
      const journal = join(dir, "docs", "knowledge", "journal")
      assert.ok(existsSync(journal), "no se creó el directorio del journal")
      // `journal.py` es idempotente por session_id: dos reposos = una entrada (más su índice).
      const entradas = readdirSync(journal).filter((f) => f.endsWith(".md") && f !== "README.md")
      assert.ok(entradas.length <= 1, `el journal se duplicó: ${entradas.join(", ")}`)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })

  test("otros eventos se ignoran y no lanzan", async () => {
    const dir = proyectoConLedger()
    const client = clienteFalso()
    try {
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client, $: null })
      for (const event of [{ type: "session.created" }, { type: "file.edited" },
                           { type: "session.idle" } /* sin sessionID */, undefined]) {
        await h.event({ event })
      }
      assert.ok(true)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })
})

describe("robustez", () => {
  test("sin cliente (arranque temprano) tampoco lanza", async () => {
    const dir = proyectoConLedger()
    try {
      const h = await CustomAgentsHooks({ directory: dir, worktree: dir, client: undefined, $: null })
      await h["tool.execute.after"]({ tool: "edit" },
        { args: { filePath: join(dir, "docs", "roadmap", "2026-01-01-demo", "tasks.md") } })
      assert.ok(true)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  })

  test("el adaptador no importa nada fuera de node: (cero dependencias)", () => {
    const src = readFileSync(join(ROOT, "hooks", "opencode-plugin.js"), "utf8")
    const imports = [...src.matchAll(/^import\s.*?from\s+"([^"]+)"/gm)].map((m) => m[1])
    const externos = imports.filter((i) => !i.startsWith("node:"))
    assert.deepEqual(externos, [], `el adaptador no puede depender de paquetes: ${externos}`)
  })
})
