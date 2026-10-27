# Especialización por proyecto

[English](en/SPECIALIZATION.md) · **Español**

El plugin sabe **cómo** trabajar, pero no **dónde** está trabajando. Este documento explica cómo un
proyecto le enseña su dominio: con **personas de proyecto**, que se inyectan en el brief de cada
subagente, y con sus **piezas propias** (skills, agentes, comandos, tools, MCP), que el plugin
descubre en las carpetas nativas de cada runtime.

> **Estado (2026-10-27).** La iniciativa `docs/roadmap/2026-09-09-project-specialization/` se cerró
> con **F1 entregada**: la cascada de personas y este documento. **F2 se canceló**: el comando
> *specialize*, la escritura del registro, el escaneo del proyecto, la puerta de colisión y el modo
> proyecto de `export-interop.py` no existen y no están planificados. La superó
> [extensiones propias](PROJECT-EXTENSIONS.md): `project-pieces.py` y `/work-context` ya descubren,
> seleccionan y pasan al brief las piezas que el proyecto escribe a mano. Motivo: la enmienda del
> 2026-10-27 en la spec de la iniciativa.

## Personas de proyecto (la cascada)

Una tarea del ledger puede llevar `- **Tipo**: <tipo>` (campo opcional; sin él, subagente genérico).
`agent-kits/shared/task-brief.py` resuelve la persona de ese tipo con tres escalones, del más
específico al más general:

1. **`.claude/personas/<tipo>.md` del proyecto.** Gana siempre: es el dominio de ESTE proyecto.
2. **Catálogo del plugin** (`agent-kits/shared/personas/`, o el que fije `--personas-dir`).
3. **Ninguno.** El brief sale sin sección de persona, con un aviso por stderr y exit 0. Nunca bloquea.

No hay lista blanca de tipos: cualquier `<tipo>` con fichero en uno de los dos primeros escalones
funciona sin tocar código. Una persona escrita a mano ya rinde. Basta con un perfil de dominio de
unas diez líneas en `.claude/personas/<tipo>.md`.

Las personas son un mecanismo del **brief**. Codex y OpenCode no cargan `personas/` de forma nativa:
les llegan dentro del brief que reciben sus subagentes, no como agente propio
(ver [`INTEROP.md`](INTEROP.md)).

## Piezas propias del proyecto

Las skills, agentes, comandos, fuentes de tools y MCP del proyecto se escriben a mano, en la carpeta
nativa de cada runtime. El plugin las reconoce sin convertirlas ni ejecutarlas. Cómo crearlas, dónde
van y cómo las usa el ciclo: [`PROJECT-EXTENSIONS.md`](PROJECT-EXTENSIONS.md).

## El registro de propiedad (`.claude/pieces.json`, solo lectura)

Un proyecto **puede** aportar un registro que declare qué piezas son suyas y con qué hash quedaron.
El plugin lo **lee** y **valida**, pero **no lo escribe**. Lo valida `_registry_entries()` de
`agent-kits/shared/project-pieces.py`. El esquema es la opción O1 (`ADR-014`): la **pieza es la
raíz** y sus destinos van anidados dentro.

```json
{
  "version": 1,
  "hash_version": "sha256-lf-1",
  "piezas": [
    {
      "nombre": "hooks",
      "forma": "persona",
      "area": "hooks",
      "origen": "adoptada",
      "creada": "2026-09-09",
      "evidencia": ["hooks/session-end.sh:12"],
      "confirmaciones": { "tools": [], "arbol_plugin": null, "tope": null },
      "destinos": [
        { "runtime": "claude-code", "ruta": ".claude/personas/hooks.md", "canonica": true, "hash": "sha256:ab12…" }
      ]
    }
  ]
}
```

`runtime` es un **dato** de cada destino, no una clave del esquema. El estado de cada pieza no se
guarda en el registro: se deriva en cada lectura, comparando el hash del disco (con finales de línea
normalizados a LF) con el anotado.

| Estado | Cuándo |
|---|---|
| gestionada | El hash en disco coincide con el anotado |
| modificada | El hash en disco difiere del anotado |
| no gestionada | La pieza no tiene fila. Es un estado válido, no un error |

Un proyecto sin registro funciona igual: todas sus piezas aparecen como no gestionadas. Un registro
corrupto da un aviso y nunca bloquea. El panel (`/plugin-catalog`) muestra la propiedad de cada pieza.

## Memoria: el plugin lee, el curador decide

La especialización **lee** `docs/knowledge/` (ADR, gotchas, lecciones) como indicio y nunca escribe
en él. El conocimiento nuevo se propone por el servicio compartido
(`agent-kits/shared/knowledge-curation.py`) y lo aprueba solo `knowledge-curator`
(`docs/agents/ROLES.md`).

## Lo que queda fuera

- **Generar o adoptar piezas** (el antiguo *specialize*): cancelado. Si se retoma la idea de que el
  plugin **proponga** piezas a partir de evidencia del repo, será una iniciativa nueva sobre
  `project-pieces.py`, con sus scripts en `agent-kits/shared/`, para que viajen con el plugin.
- **Deriva semántica y retirada de piezas muertas** (la antigua F3): sin plan.
