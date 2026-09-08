// opencode-plugin.js — adaptador de los hooks del plugin al modelo de eventos de OpenCode.
//
// Los hooks de este plugin son scripts de shell que hablan el contrato de Claude Code (payload
// JSON por stdin, respuesta JSON por stdout, SIEMPRE exit 0). OpenCode no tiene hooks de ciclo de
// vida: tiene PLUGINS en JavaScript que se suscriben a eventos (opencode.ai/docs/plugins). Este
// fichero es el puente: sintetiza el payload que cada script espera, lo lanza y traduce su salida
// al canal que OpenCode ofrece. No duplica ninguna lógica — la decisión sigue en el script.
//
// Instalación: copia `interop/opencode/plugins/custom-agents-hooks.js` a `.opencode/plugins/`
// (proyecto) o `~/.config/opencode/plugins/` (usuario). El detalle está en `docs/INTEROP.md`.
//
// Equivalencias (y lo que se pierde, que está en la tabla de degradación de docs/INTEROP.md):
//
//   Claude Code                      OpenCode                      Estado
//   ------------------------------   ---------------------------   --------------------------
//   PostToolUse (Write|Edit)         tool.execute.after            equivalente
//     → mark-docs-pending.sh           (tool `edit`/`write`/`patch`)
//     → ledger-lint-warn.sh
//     → progress-line.sh
//   SessionEnd → session-journal.sh  event `session.idle`          equivalente en efecto: el
//                                                                  script es IDEMPOTENTE por
//                                                                  session_id, así que escribir
//                                                                  en cada reposo ACTUALIZA la
//                                                                  misma entrada del journal.
//   SessionStart → session-context   —                             no hay hook que inyecte
//                                                                  contexto; lo cubre el fichero
//                                                                  `instructions` del índice.
//   UserPromptSubmit → capture       —                             sin evento documentado de
//                                                                  turno del usuario; el journal
//                                                                  se queda con su parte
//                                                                  determinista (git + ledger).
//   SubagentStop → subagent-progress —                             sin evento equivalente.
//
// Los hooks INFORMAN, no deciden (ADR-007): aquí nunca se lanza una excepción desde un hook —
// eso abortaría la herramienta en OpenCode. Cualquier fallo se registra y se sigue.

import { spawn } from "node:child_process"
import { existsSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

// Dónde buscar `hooks/`. El PRIMER candidato es relativo a ESTE fichero: el instalador deja el
// adaptador en `<base>/plugins/` y los scripts en `<base>/hooks/`, así que el propio `import.meta.url`
// dice dónde están sin adivinar nada. Los demás candidatos son el respaldo (instalación a mano,
// o el bundle de Claude Code ya desplegado) con la precedencia de la regla 5: proyecto, luego usuario.
const AQUI = dirname(fileURLToPath(import.meta.url))
const CASA = process.env.HOME || process.env.USERPROFILE || "."
const RAICES = (worktree, directory) => [
  join(AQUI, ".."),                              // <base>/plugins/ → <base>/
  AQUI,                                          // el .js junto a hooks/ (copia plana)
  join(directory || ".", ".opencode"),
  join(worktree || directory || ".", ".opencode"),
  join(directory || ".", ".claude"),
  join(worktree || directory || ".", ".claude"),
  join(CASA, ".config", "opencode"),
  join(CASA, ".claude"),
]

// Herramientas de OpenCode que equivalen a Write|Edit|MultiEdit de Claude Code.
const HERRAMIENTAS_ESCRITURA = new Set(["edit", "write", "patch", "multiedit"])

const HOOKS_POST_TOOL = ["mark-docs-pending.sh", "ledger-lint-warn.sh", "progress-line.sh"]

export const CustomAgentsHooks = async ({ directory, worktree, client, $ }) => {
  // Localiza `hooks/` una sola vez, al cargar el plugin. Sin bundle → plugin inerte (degrada).
  const hooksDir = RAICES(worktree, directory)
    .map((r) => join(r, "hooks"))
    .find((d) => existsSync(join(d, "session-journal.sh")))

  const log = (level, message) => {
    try {
      client?.app?.log({ body: { service: "custom-agents", level, message } })
    } catch {
      // sin cliente (arranque temprano, tests): silencio — un hook nunca rompe la sesión
    }
  }

  if (!hooksDir) {
    log("debug", "custom-agents: no encuentro hooks/ — plugin inerte (¿bundle desplegado como .claude/?)")
    return {}
  }

  // Lanza un hook con el payload por stdin y devuelve su stdout (o "" si algo falla).
  // Nunca rechaza: el contrato de los hooks es exit 0 y aquí un error tampoco puede propagarse.
  const lanzar = (script, payload, timeoutMs = 20000) =>
    new Promise((resolve) => {
      let hecho = false
      const fin = (out) => {
        if (!hecho) {
          hecho = true
          resolve(out)
        }
      }
      try {
        const p = spawn("bash", [join(hooksDir, script)], {
          cwd: worktree || directory,
          env: {
            ...process.env,
            // Los scripts leen estas dos con fallback a $PWD / find (regla 5): dárselas les
            // ahorra el `find` y los ancla al proyecto correcto.
            CLAUDE_PROJECT_DIR: worktree || directory || process.cwd(),
            CLAUDE_PLUGIN_ROOT: join(hooksDir, ".."),
          },
          stdio: ["pipe", "pipe", "ignore"],
        })
        const temporizador = setTimeout(() => {
          try {
            p.kill("SIGKILL")
          } catch {
            /* ya terminó */
          }
          fin("")
        }, timeoutMs)
        let out = ""
        p.stdout.on("data", (d) => {
          out += d.toString("utf8")
        })
        p.on("error", () => {
          clearTimeout(temporizador)
          fin("")
        })
        p.on("close", () => {
          clearTimeout(temporizador)
          fin(out)
        })
        p.stdin.on("error", () => {
          /* el script puede cerrar stdin antes de leerlo */
        })
        p.stdin.end(JSON.stringify(payload), "utf8")
      } catch {
        fin("")
      }
    })

  // `systemMessage` es el canal universal de los hooks de Claude Code. En OpenCode el
  // equivalente visible es un toast; si no está disponible, queda en el log.
  const mostrar = async (salida) => {
    let msg
    try {
      msg = JSON.parse(salida)?.systemMessage
    } catch {
      return
    }
    if (!msg) return
    try {
      await client.tui.showToast({ body: { message: String(msg), variant: "info" } })
    } catch {
      log("info", String(msg))
    }
  }

  // Una sesión = una escritura de journal en vuelo (el script es idempotente, pero no hace falta
  // solaparlas).
  const journalEnVuelo = new Set()

  return {
    // PostToolUse (Write|Edit|MultiEdit) → los tres hooks informativos del plugin.
    "tool.execute.after": async (input, output) => {
      try {
        if (!HERRAMIENTAS_ESCRITURA.has(String(input?.tool || "").toLowerCase())) return
        const file = output?.args?.filePath || output?.args?.file_path || output?.args?.path
        if (!file) return
        const payload = {
          hook_event_name: "PostToolUse",
          tool_name: "Edit",
          // Ruta con `/`, SIEMPRE. Los hooks normalizan `\` → `/`, pero cuando extraen la ruta sin
          // `jq` (grep de respaldo) lo que leen es el JSON escapado: un `C:\Users` nativo llega como
          // `C:\\Users` y la normalización lo deja en `C://Users`, con lo que el patrón
          // `*docs/roadmap/*tasks.md` ya no casa y el hook se calla sin decir por qué. Entregar
          // POSIX evita el doble escapado de raíz (medido en Windows sin jq).
          tool_input: { file_path: String(file).split("\\").join("/") },
          cwd: String(worktree || directory || "").split("\\").join("/"),
        }
        for (const script of HOOKS_POST_TOOL) {
          await mostrar(await lanzar(script, payload, 15000))
        }
      } catch (e) {
        log("warn", `custom-agents: tool.execute.after — ${e?.message || e}`)
      }
    },

    // SessionEnd → journal de sesión. OpenCode no tiene «fin de sesión», pero `session.idle`
    // marca el fin de una unidad de trabajo y `journal.py write` es idempotente por
    // `session_id`: cada reposo ACTUALIZA la entrada del día en vez de duplicarla.
    event: async ({ event }) => {
      try {
        if (event?.type !== "session.idle") return
        const sid = event?.properties?.sessionID || event?.properties?.info?.id
        if (!sid || journalEnVuelo.has(sid)) return
        journalEnVuelo.add(sid)
        try {
          await lanzar(
            "session-journal.sh",
            {
              hook_event_name: "SessionEnd",
              session_id: String(sid),
              reason: "other",
              cwd: worktree || directory,
            },
            45000,
          )
        } finally {
          journalEnVuelo.delete(sid)
        }
      } catch (e) {
        log("warn", `custom-agents: session.idle — ${e?.message || e}`)
      }
    },
  }
}

export default CustomAgentsHooks
