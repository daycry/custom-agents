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
python3 agent-kits/knowledge-curator/curator-gate.py <candidato.md> --decision approve [--category KEY] [--root .] [--id ID] [--json]
```

Exit codes: `0` decisión permitida (sin errores bloqueantes) · `1` con errores (evidencia
insuficiente, faltan `fuentes`/`tags`, término de la lista negra, `estado` con un token que no es
`aprobado`) · `2` error de uso (categoría inexistente, decisión inválida, candidato no encontrado,
taxonomía inválida, o un candidato en `rejected/` con una decisión distinta de `reject` — gap 67 de
la revisión de dos lentes de la Fase 2, ver más abajo).

`approve` es la única decisión que exige el contrato completo (gaps 3 y 34 de la revisión de dos
lentes de T-01/T-02): `evidencia` presente y con rango ≥ `min_evidence` de la categoría EXACTA que
el Curator asignó (usando la escalera `evidence_levels` del proyecto, o la del plugin por defecto
si el proyecto no declara una propia — gap 47), `fuentes` no vacía, `tags` en forma `clave:valor`,
sin términos de la lista negra (`taxonomy.json` → `denylist`), y `estado` (si se declara) solo con
el token `aprobado` — nunca `approved`/`pending`/`needs_changes`/`rejected`, que son nombres de
carpeta del flujo de candidatos, no valores de `estado`. Al aprobar, también se comprueba que no
haya **colisión** con `approved/` (gap 50): ni un `id` ya indexado ni un fichero con el mismo
nombre en la carpeta destino. La comprobación de `id` usa el `id` del frontmatter o, si el
candidato aún no lo trae, el que se le vaya a asignar vía `--id <el-id>` (gap 68); sin ninguno de
los dos el gate no bloquea, pero devuelve un `aviso` («colisión de id no comprobada») en
`avisos[]` para que quede constancia de que esa guarda no se ha podido aplicar.

`--id` se valida antes de usarse (gaps 75/79, revisión de dos lentes, ronda `fix3`): se
`strip()`ea (un valor en blanco, p. ej. `--id "   "`, es un error de **uso**, `exit 2`, no un id
válido en silencio), debe tener forma `[A-Za-z0-9._-]+` y empezar por el `id_prefix.` de la
taxonomía del proyecto (o el derivado del slug del `root` si no declara uno propio — siempre hay
uno, `knowledge-schema.cargar_taxonomia` lo rellena). Y si el frontmatter **ya trae** un `id`
distinto del pasado por `--id`, es un error bloqueante que nombra los dos valores (antes,
`fm.get("id") or id_override` descartaba `--id` en silencio y el gate aprobaba usando el `id` del
frontmatter sin comprobar el que el Curator pensaba asignar de verdad).

La lista negra (`denylist`) pliega acentos en los dos lados de la comparación con `unicodedata`
NFD (`conversación` casa con el término `conversacion` declarado sin tilde, y viceversa — gap 64),
admite términos de varias palabras separadas por espacio, guion o guion bajo indistintamente
(`chain of thought` ≡ `chain-of-thought` ≡ `chain_of_thought` — gap 66, guion bajo sumado en el
gap 80), y el límite de palabra solo se exige en el lado del término cuyo carácter de borde es
alfanumérico — así `TODO:` sigue disparando aunque le siga `limpiar` sin espacio de por medio (gap
65). El límite IZQUIERDO de un término que empieza en palabra es más estricto que `(?<!\w)` (gap
77): solo dispara si lo precede el inicio del texto, un espacio o puntuación de apertura de frase
(`(`, `[`, `"`, `'`, `¿`, `¡`, `-`, `—`) — nunca un separador de ruta/URL sin espacio
(`https://x/TODO:1234` no dispara). El separador flexible entre palabras de un término
multi-palabra tampoco cruza una frontera de lista markdown (gap 78): `codigo\n- duplicado` no es
el término `codigo duplicado` partido por formato (dos ítems distintos de una lista), pero
`codigo\nduplicado` (salto de línea sin viñeta ni línea en blanco) sigue disparando igual.

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
no un candidato. `rejected/` es **terminal** (gap 67): un candidato que ya vive ahí solo admite
`--decision reject` (idempotente, `exit 0`); pedirle `approve` o `needs_changes` es error de uso
(`exit 2`, "`rejected/` es terminal") en vez de volver a evaluar el contrato.

El gate **no mueve ficheros**: el agente lee el veredicto (`--json`) y, si `errores == []`, escribe
el fichero final (bajo `approved/<folder>/` con `estado: aprobado`, o deja el candidato en su
carpeta de `candidates/` si `reject`/`needs_changes`) y hace el `git mv`/borrado que corresponda.

Tests: `agent-kits/knowledge-curator/test_curator_gate.py` (`python3 -m pytest -q
agent-kits/knowledge-curator/test_curator_gate.py`).
