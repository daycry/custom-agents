# Especialización por proyecto — el tercer bucle

[English](en/SPECIALIZATION.md) · **Español**

Este documento es la **única puerta de entrada** del tercer bucle del plugin, hermana de
[`INTEROP.md`](INTEROP.md) y [`observability.md`](observability.md): el plugin sabe **cómo** trabajar
y no sabe **dónde** está trabajando. El tercer bucle cierra ese hueco con la misma gramática que ya
tienen el ciclo (`tasks.md`) y la memoria (`docs/knowledge/README.md`): un **registro canónico**, una
**puerta de entrada** y una **puerta de cierre**.

> **Alcance de esta iteración: F1 + F2.** Ver «El límite de esta iteración» al final. La spec completa
> vive en `docs/roadmap/2026-09-09-project-specialization/spec.md` (`aprobada`).
>
> **Lo entregado hoy en este árbol es F1** (`tasks.md` T-01…T-03): la cascada de tres escalones de
> `task-brief.py` y esta misma puerta documental. **El registro canónico, `/specialize`,
> `pieces-registry.py`, `role-collision.py`, `project-scan.py`, `.claude/pieces.json` y la sección de
> `/doctor`** que describen «El registro canónico», «La escalera de decisión» y «Las dos puertas» de
> más abajo son el **contrato de F2** (`design.md` `ADR-014`, `tasks.md` T-04…T-18): están diseñados y
> planificados, **no en el árbol todavía**. Mismo patrón que `docs/agents/ROLES.md` con `/specialize`.

El lector de [extensiones propias](PROJECT-EXTENSIONS.md) reconoce las piezas
existentes y valida un registro O1 aportado por el proyecto en modo lectura.
Ese inventario derivado no entrega la generación, adopción, reconstrucción ni
las puertas de escritura de F2; su estado se sigue en el ledger independiente.

## Qué es el bucle

```
Memoria ──lee──▶ Especialización ──alimenta──▶ Ciclo
Ciclo ──/retro: servicio propose──▶ pending + SHA ──juicio──▶ Curator
Curator ──servicio apply ligado SHA──▶ Memoria
```

`docs/knowledge/` (ADR, gotchas, lecciones, journal) alimenta `/specialize`, que produce **piezas de
proyecto** — personas, tools, skills o agentes que viven en el `.claude/` del consumidor y saben de SU
dominio. Esas piezas entran en el ciclo (`task-brief.py` inyecta la persona en el brief de las tareas
que llevan `- **Tipo**: <tipo>` — el campo es opcional; sin él, subagente genérico). `/retro`
propone evidencia por `agent-kits/shared/knowledge-curation.py`; repetir no aprueba conocimiento.
Curator juzga y el servicio persiste con SHA original, motivo y metadatos válidos. Dos términos
distintos, para no confundirlos:

- **Pieza de plugin** — agente, skill, comando, kit o hook que vive en este repo y viaja con el
  plugin. Agnóstica de dominio por diseño.
- **Pieza de proyecto** — persona, tool, skill o agente que vive en el `.claude/` del consumidor, sabe
  de SU dominio y solo existe ahí. Es lo que este bucle permite tener.

## El registro canónico

`.claude/pieces.json` es una fila por pieza **generada** o **adoptada**. Lo escrito a mano y nunca
adoptado sigue siendo ciudadano de primera: aparece como `no gestionada`, que es un estado válido, no
un error.

El esquema es la opción **O1** del diseño (`ADR-014`): la **pieza es la raíz**, y sus destinos —el
canónico de Claude Code más las variantes de cada runtime— van **anidados dentro**, nunca al revés.

```json
{
  "version": 1,
  "hash_version": "sha256-lf-1",
  "piezas": [
    {
      "nombre": "hooks",
      "forma": "persona",
      "area": "hooks",
      "origen": "generada",
      "creada": "2026-09-09",
      "evidencia": ["hooks/session-end.sh:12", "GOT-005"],
      "confirmaciones": { "tools": [], "arbol_plugin": null, "tope": null },
      "destinos": [
        { "runtime": "claude-code", "ruta": ".claude/personas/hooks.md", "canonica": true,  "hash": "sha256:ab12…" },
        { "runtime": "codex",       "ruta": ".codex/agents/hooks.toml",  "canonica": false, "hash": "sha256:cd34…" }
      ]
    }
  ]
}
```

`runtime` es un **dato** de cada destino, nunca una clave del esquema: un cuarto proveedor es una fila
más, no una migración. El estado de una fila **no se persiste**: se deriva comparando el hash del
disco con el hash anotado, en cada lectura.

Los tres estados de una fila (por hash, no por carpeta — `GOT-003`):

| Estado | Cuándo |
|---|---|
| `gestionada` | El hash del fichero en disco coincide con el hash anotado en su fila |
| `modificada` | El hash en disco es distinto del anotado (se editó a mano tras generarse, o se adoptó sin línea base). Nunca se pisa: se muestra el diff y se pide confirmación explícita |
| `no gestionada` | No tiene fila. Es un estado válido, no un error; puede **adoptarse** con `--adopt` |

## La escalera de decisión

Del escalón más barato al más caro. `/specialize` empieza siempre por «nada»: duplicar una pieza que
ya existe se rechaza, nunca se genera.

```
nada → persona → tool → skill → agente
```

- **nada** — el candidato duplica una pieza instalada o ya generada: se rechaza nombrando la que ya
  lo cubre (`role-collision.py`).
- **persona** — perfil de dominio de ~10 líneas; es el escalón por defecto.
- **tool / skill / agente** — se suben solo cuando la evidencia lo justifica; **agente** es el último
  recurso, con **override explícito del usuario**.

## Las dos puertas

`/specialize` nunca escribe sin que un humano lo confirme, y separa la **previsualización** de la
**confirmación**:

1. **`--dry-run`/`--plan`** — previsualiza el **lote completo** de candidatos (forma, evidencia,
   resultado de la puerta de colisión) y **no crea ningún fichero ni fila**.
2. **N confirmaciones para N candidatos** — sin `--dry-run`, se pide una confirmación explícita por
   cada candidato, en el orden previsualizado. Confirmar uno no aprueba los demás; rehusar uno solo
   omite ese; si no se confirma ninguno, no se escribe nada y la salida es limpia (exit 0).

El **tope de piezas generadas es 5, acumulado en el registro completo del proyecto**, no por
invocación (motivo: el presupuesto medido de `skill-index.py`, `LIMITE_LINEAS = 45` /
`LIMITE_CHARS = 3500`, que es el que fija cuánto cabe en el índice de arranque). Superarlo dispara
aviso y confirmación extra, nunca un fallo silencioso.

## El invariante de dirección

**`/specialize` lee `docs/knowledge/` y NUNCA escribe en él.** Consume ADR, gotchas, lecciones y las
candidatas del journal como indicios; produce piezas según el contrato de F2. Conocimiento nuevo
se propone por el servicio compartido; `knowledge-curator` decide y solicita persistencia por
`apply_decision`, no `/retro` ni `adversarial-review`. Design/revisión/QA/Gold/repetición aportan
evidencia, no aprobación. Retro posterior al Gate entrega handoff o ruta/ID pendientes visibles.
Legado mantiene bytes/estados/autoridad sin migración, reaprobación o borrado automáticos;
conflictos/alto impacto requieren resolución humana trazada, no fecha/score. El tercer bucle
no escribe ni aprueba memoria (`docs/agents/ROLES.md`).

El servicio de curación no entrega F2 ni demuestra actor autenticado o sandbox universal.
Intención, publicación y recibo son fronteras recuperables, no una transacción multiarchivo
atómica; aceptación nativa pendiente. [Contrato de curación](roadmap/2026-10-07-catalog-capabilities/comparisons/memory-curation-contract.md).

## El límite de esta iteración

El alcance planificado de esta iteración cubre **F1 (Sustrato) y F2 (Nacimiento)**: la cascada de personas, el comando
`/specialize`, el registro con sus tres estados, el modo de adopción, los requisitos no funcionales
(idempotencia, concurrencia, privacidad) y la propia sección de `/doctor` que audita el registro — no
se entrega la capacidad de generar sin la de comprobar.

**F3 (deriva semántica y retirada de piezas muertas) queda diferida, no descartada.** El contrato de
F2 exige su propia auditoría mecánica (`/doctor`); F2 sigue sin implementarse en este árbol.
F3 se retoma como iniciativa propia cuando haya datos del criterio de éxito. Detalle completo,
motivo y punto de control: `docs/roadmap/2026-09-09-project-specialization/spec.md`, sección
**«Alcance» → «Fuera (esta iteración — diferido, no descartado)»**.
