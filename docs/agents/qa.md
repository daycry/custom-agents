# Documentación del agente `qa`

Agente que **audita un plan** ejecutando sus tests E2E con **Playwright** contra la app local, captura evidencias y entrega un informe **md + pdf** con checklist manual. El veredicto verde/rojo **no es una impresión**: lo dan scripts con exit code.

```mermaid
flowchart LR
    IN["test-plan.md<br/>(E2E-xx · M-xx · API/A11Y opt-in)<br/>+ criterios [GWT] de la spec"] --> G1["puertas deterministas:<br/>ledger-lint · coverage-check"]
    G1 --> RUN["Playwright<br/>(solo hosts locales)"]
    RUN --> V{"qa-gate.py<br/>exit code"}
    V -->|verde| OK["informe md+pdf<br/>→ handoff a documenter"]
    V -.->|"rojo (máx. 3;<br/>al 3.º debug-root-cause)"| BACK["vuelve a implementer"]
    style OK fill:#e8f5e9,stroke:#81c784
    style BACK fill:#fdecea,stroke:#ef9a9a
```

---

## 1. Entrada y salida

- **Entrada:** una iniciativa en `docs/roadmap/<fecha>-<slug>/` con su `test-plan.md` (bloques `E2E-xx` automáticos y `M-xx` manuales, que genera `planner`), más la **URL local** de la app en ejecución.
- **Salida:** `docs/roadmap/<fecha>-<slug>/testing/` con `report.md` + `report.pdf`, `screenshots/` y `raw/` (results.json + trazas).

---

## 2. Cómo funciona

`planner` define los tests en `test-plan.md`; `qa` los ejecuta. Antes de nada corre dos **puertas deterministas**: `ledger-lint.py` (ledger coherente) y `coverage-check.py` (cobertura criterios↔tests — incluye los **criterios `[GWT]`** de la spec: cada `- [ ] [GWT] CA-XX — Dado…, Cuando…, Entonces…` debe tener su bloque E2E; un GWT sin cubrir es rojo). Luego traduce cada escenario `E2E-xx` a un test Playwright (los `[GWT]` se traducen 1:1: Dado→setup, Cuando→acciones, Entonces→aserciones), los corre contra la URL local, captura screenshots y recoge resultados en JSON. El **veredicto verde/rojo lo emite `qa-gate.py`** sobre ese JSON (verde ⟺ 0 fallos, 0 flaky sin justificar, 0 interrumpidos, ≥1 test ejecutado). El informe incluye estado global, resultado por escenario con capturas, checklist manual `M-xx` y trazabilidad tarea→resultado; el PDF se genera con **`to-pdf`**.

---

## 3. Requisitos y guardrail

- **Node** en la máquina. Playwright + Chromium se instalan **fuera del repo** en `~/.claude/tool-cache/qa/`, con **permiso previo** (descarga pesada) — mismo patrón opt-in que `nemesis`/`pdfy`.
- **Guardrail:** los E2E solo contra hosts **locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas). Una URL externa se rechaza.

---

## 4. Relación con `planner`

`planner` genera el `test-plan.md` (y las etiquetas **Cubre (tests)** en las tareas de UI); `qa` lo consume. Si un plan no tiene `test-plan.md`, hay que (re)generarlo con `planner` antes de auditar.

---

## 5. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente qa contra https://miapp.test`
- `qa, audita el plan docs/roadmap/2026-07-09-mi-feature con la app en http://localhost:8080`
- `prueba la UI con Playwright y genera el informe`

La primera vez pide permiso para instalar Playwright/Chromium y confirma la URL local.

---

## 5-bis. Memoria técnica del proyecto

Antes de auditar, lee el índice de `docs/knowledge/` (si existe) y abre las entradas de `gotchas/` que apliquen — útil para no reabrir un flaky ya diagnosticado (paso compartido `agent-kits/shared/knowledge-check.md`). Cuando un flaky justificado resulta ser un **patrón** (no un accidente: ya hay una entrada sobre ese test/motivo en `gotchas/`, o el mismo motivo se repite en otro test de la tanda actual), escribe un fichero nuevo `docs/knowledge/gotchas/GOT-NNN-<slug>.md` citando la entrada existente — excepción declarada a "no toca `docs/roadmap/`" (`agent-kits/shared/knowledge-write.md`).

---

## 6. Kit (`agent-kits/qa/`)

- `runner/` — proyecto Playwright (config con reporter JSON + capturas + trazas; `tests/E2E-example.spec.mjs` como patrón).
- `lib-guardrail.sh` — gate local-only de la URL.
- `qa-gate.py` — **veredicto determinista** verde/rojo sobre `results.json` (exit code; con tests).
- `coverage-check.py` — cobertura criterios↔tests: `tasks.md` ↔ `test-plan.md` ↔ criterios `[GWT]` de la spec (con tests).
- `templates/report.md` — plantilla del informe.
