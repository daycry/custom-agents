# `agent-kits/knowledge-curator/` — kit privado del agente `knowledge-curator`

Kit del **único agente que escribe** bajo `docs/knowledge/candidates/**` y
`docs/knowledge/approved/**` (`ADR-018`, `knowledge-services` T-04). El agente decide (categoría,
evidencia suficiente, contradicciones, alto impacto); este kit da la **puerta determinista** que
comprueba esa decisión antes de moverla al disco.

## `curator-gate.py`

Entrada: la ruta de un candidato + la decisión (`approve` · `reject` · `needs_changes`) + la
categoría (frontmatter `category`/`categoria`, o `--category` explícito). Reutiliza
`agent-kits/shared/knowledge-schema.py` (taxonomía, `evidence_levels`) y
`agent-kits/shared/knowledge-index.py` (parser de frontmatter `_frontmatter`) — ambos deben viajar
en `agent-kits/shared/`; sin ellos degrada con un error claro (`KitCompartidoNoDisponible`), nunca
un traceback.

```bash
python3 agent-kits/knowledge-curator/curator-gate.py <candidato.md> --decision approve [--category KEY] [--root .] [--json]
```

Exit codes: `0` decisión permitida (sin errores bloqueantes) · `1` con errores (evidencia
insuficiente, faltan `fuentes`/`tags`, término de la lista negra, `estado` con un token que no es
`aprobado`) · `2` error de uso (categoría inexistente, decisión inválida, candidato no encontrado,
taxonomía inválida).

`approve` es la única decisión que exige el contrato completo (gaps 3 y 34 de la revisión de dos
lentes de T-01/T-02): `evidencia` presente y con rango ≥ `min_evidence` de la categoría EXACTA que
el Curator asignó (usando la escalera `evidence_levels` del proyecto, o la del plugin por defecto
si el proyecto no declara una propia — gap 47), `fuentes` no vacía, `tags` en forma `clave:valor`,
sin términos de la lista negra (`taxonomy.json` → `denylist`), y `estado` (si se declara) solo con
el token `aprobado` — nunca `approved`/`pending`/`needs_changes`/`rejected`, que son nombres de
carpeta del flujo de candidatos, no valores de `estado`. Al aprobar, también se comprueba que no
haya **colisión** con `approved/` (gap 50): ni un `id` ya indexado ni un fichero con el mismo
nombre en la carpeta destino.

`reject`/`needs_changes` NO corren nada de eso (gap 58, salvedad deliberada): ni evidencia, ni
`fuentes`/`tags`, ni lista negra, ni el token de `estado`, ni siquiera exigen que `category` esté
declarada (gap 53) — si falta, se dictamina igual y el gate solo añade un `aviso` no bloqueante
(`avisos` en la salida `--json`, nunca en `errores`). El Curator puede descartar o devolver un
candidato incompleto, o incluso sin categorizar, sin que el gate se lo impida; category **inválida**
(declarada pero no existe en `taxonomy.json`) sigue siendo un error de uso (`exit 2`) en las tres
decisiones.

El candidato debe vivir bajo `docs/knowledge/candidates/{pending,needs_changes,rejected}/` del
`--root` (contención por `realpath`, gap 48): cualquier otra ruta — un fichero ya en `approved/`,
el corpus legado, o cualquier `.md` fuera del árbol de candidatos — es un error de uso (`exit 2`),
no un candidato.

El gate **no mueve ficheros**: el agente lee el veredicto (`--json`) y, si `errores == []`, escribe
el fichero final (bajo `approved/<folder>/` con `estado: aprobado`, o deja el candidato en su
carpeta de `candidates/` si `reject`/`needs_changes`) y hace el `git mv`/borrado que corresponda.

Tests: `agent-kits/knowledge-curator/test_curator_gate.py` (`python3 -m pytest -q
agent-kits/knowledge-curator/test_curator_gate.py`).
