---
id: ADR-009
titulo: Tiering de modelos configurable en dos capas (frontmatter + dev.json), resuelto por script
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fecha: 2026-09-03
iniciativa: parity-core
---

# ADR-009: Tiering de modelos configurable en dos capas (frontmatter + `dev.json`), resuelto por script

## Contexto

El tiering de modelos vivía solo en el frontmatter de cada agente (`model: haiku|sonnet|opus`), sin
`effort` y sin forma de que un proyecto consumidor lo ajustara (un equipo con presupuesto ajustado no podía
bajar `evaluator` a `sonnet` sin editar el plugin instalado). La doc oficial de subagentes (verificada
2026-09-03) ofrece dos mecanismos: el campo `effort` en el frontmatter (`low|medium|high|xhigh|max`) y un
parámetro `model` **por invocación** del Agent tool que tiene prioridad sobre el frontmatter (v2.1.251+).
Pero no ofrece parámetro `effort` por invocación, y la invocación manual `@agente` no pasa por ningún
orquestador.

## Decisión

El tier efectivo de un agente se resuelve en **dos capas** con un **script determinista**
(`agent-kits/shared/model-tier.py <agente> [--json|--all]`): capa 1 = frontmatter (`model` + `effort`,
ambos obligatorios y validados por el linter; tabla de tiering en CONVENTIONS); capa 2 = override parcial
por agente en `.claude/dev.json` → `modelos.<agente>.{model, effort}` (valor inválido → aviso y se ignora;
fichero ausente/corrupto → capa 1). Los **orquestadores** (`/dev-cycle`, `/pm-cycle`, `adversarial-review`,
`quick-implement`) llaman al script antes de despachar y pasan `model` en el parámetro del Agent tool. El
`effort` de la capa 2 se declara **informativo** (no hay parámetro oficial por invocación): el orquestador
lo anuncia, no finge aplicarlo. `/setup` (paso 5-quater) muestra la tabla efectiva y escribe la clave.

## Alternativas descartadas

- **Solo frontmatter (estado anterior)** — sin `effort` ni override por proyecto; cambiar el tier exige
  editar el plugin instalado, que se pisa en cada actualización.
- **Que cada orquestador lea `dev.json` en prosa** — cálculo repetido en 4 sitios, sin tests, con
  validación de valores divergente; contradice la regla de determinismo (scripts con tests y exit codes).
- **Reescribir el frontmatter del agente al instalar según `dev.json`** — el fichero del plugin es de solo
  lectura en la caché de plugins y se regenera al actualizar; además mezcla config del consumidor con la
  definición de la pieza.
- **Variable `CLAUDE_CODE_SUBAGENT_MODEL`** — global para todos los subagentes (no por agente) y, desde
  v2.1.251, con menos prioridad que el parámetro por invocación; sirve como palanca de emergencia, no como
  tiering.

## Consecuencias

Un proyecto ajusta el modelo de cualquier agente sin tocar el plugin, y la decisión queda trazable
(`fuente: dev.json` en la salida del script). El coste: una llamada más por despacho (milisegundos) y una
asimetría que hay que explicar con honestidad — `@agente` manual sigue el frontmatter, y `effort` solo es
efectivo desde el frontmatter hasta que el Agent tool lo admita por invocación (fila «a re-verificar» en
`skills/plugin-dev/references/claude-code-contracts.md`). La tabla de tiering pasa a tener dos columnas
(`model`, `effort`) y una regla simple: `opus` ⇒ `high`, resto `medium`.

## Estado

`propuesta` — a validar por la revisión de dos lentes de la iniciativa `parity-core` o por el usuario en la
puerta. Pasa a `aceptada` cuando se valida; a `obsoleta` si el Agent tool documenta `effort` por invocación
y se decide aplicar la capa 2 completa (enlazar aquí a la decisión que la sustituya).
