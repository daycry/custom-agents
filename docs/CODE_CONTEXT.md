# Cómo consultar contexto AST con fuentes declaradas

[English](en/CODE_CONTEXT.md) · **Español**

`agent-kits/shared/code-context.py` lee un grafo local ya existente. Devuelve nodos
y arcos AST con archivo y ubicación, separados de la memoria aprobada.
La recuperación Markdown sigue funcionando sin Graphify, Docker ni un servicio.

`agent-kits/shared/code-context-build.py` es un productor manual opcional.
La consulta nunca lo importa ni inicia extracción. El panel y los hooks conservan
sus lectores locales; abrirlos no construye grafos ni consulta backends externos.

## Qué selecciona cada consulta

La CLI exige una de estas formas; la API mantiene `symbol` posicional.

| Selector | Coincidencia | Resultado de una colisión |
|---|---|---|
| `--symbol` | Substring con casefold sobre el label mostrado, contrato legacy. | Puede devolver varios nodos; no promete identidad exacta. |
| `--node-id` | ID exacto y sensible a mayúsculas. | Un ID duplicado excluye todas sus ocurrencias y arcos. |
| `--source-file` junto a `--label` | Archivo y label originales exactos, antes de redacción o recorte. | Varios IDs elegibles dan `ambiguous`, sin nodos ni arcos, incluso con `--limit 1`. |

El ID admite letras ASCII, números, `_`, `.`, `:`, `-`, hasta 128 caracteres.
El par usa el archivo relativo POSIX del artefacto. No normaliza aliases para
adivinar la identidad. El label de salida conserva redacción y recorte a 240 caracteres.

`--limit` admite 1–50 y vale 6 por defecto. Un límite alcanzado conserva `matches`,
`truncated: true`, `completeness: partial` y `reason: result_budget`.
`no-match-in-artifact` expresa ausencia en el artefacto; no prueba ausencia en el código.

## Cómo crear un grafo y su recibo

Localiza el kit en las seis raíces de instalación, como indica [CONVENTIONS](CONVENTIONS.md#5-rutas-dentro-del-código).
La raíz de biblioteca siguiente es una ruta que el operador ya conoce y confía;
el productor no instala, descarga ni descubre Graphify desde configuración del proyecto.

```bash
SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
python3 "$SHAREDKIT/code-context-build.py" \
  --project . --graph graphify-out/graph.json \
  --input agent-kits/shared/code-context.py \
  --input agent-kits/shared/local-read.py \
  --graphify-root <trusted-library-root>
```

Repite `--input` para cada archivo declarado que influye en la extracción o resolución.
El ejemplo declara dos archivos del plugin; no pretende cubrir todo el proyecto.
`--graph` e inputs son relativos canónicos al proyecto. El productor rechaza salidas
que sean inputs o aliases físicos de ellos.

`--graphify-root` debe señalar una biblioteca externa al proyecto, con una API compatible.
Esa raíz ejecuta código Python confiado explícitamente. Los controles de sockets y
procesos observados no convierten bibliotecas o extensiones nativas arbitrarias en un sandbox.

El productor captura todos los bytes declarados antes y después de extraer, y antes
de publicar. Ejecuta extracción AST sin paralelismo ni Git automático, con staging propio.
Un cambio observado en inputs rechaza la publicación con `inputs_changed`.

Una biblioteca ausente o incompatible da `unavailable`. La API nativa puede declarar
fuentes fallidas por gramática ausente, parser o contenido vacío: `ast_inputs_unavailable`
no identifica por sí solo la causa. Un tipo sin extractor devuelve `unsupported_input`.
Ninguno de esos resultados activa una instalación o consulta a un modelo.

El artefacto y el recibo deben tener destinos nuevos. Si existe cualquiera de ellos,
el productor devuelve `output_exists` antes de importar el extractor o extraer.
Publica primero el artefacto y después el recibo mediante creación exclusiva con `os.link`.
Si el enlace falla o aparece un destino concurrente, no recurre a sobrescritura.

El par no es atómico. Un fallo al publicar el recibo devuelve `publish_failed` y puede
dejar el artefacto final sin recibo. El productor no elimina ni reemplaza destinos
finales al fallar; limpia solo su staging propio. La siguiente build necesita un destino nuevo.
Tampoco fabrica un recibo de archivos actuales para legitimar un grafo histórico ajeno.

## Qué contiene el recibo

El sidecar automático se llama `<graph>.sources.json`. Su esquema admite solo estos campos:

| Campo | Forma exacta |
|---|---|
| `schema_version` | Entero 1, excluye bool. |
| `artifact_sha256` | SHA-256 lowercase hex64 de los bytes originales del grafo. |
| `scope` | `declared-inputs`. |
| `inputs` | Lista de objetos con solo `path`, `bytes`, `sha256`. |
| `path` | Archivo relativo POSIX canónico, único. |
| `bytes` | Entero no negativo, excluye bool. |
| `sha256` | SHA-256 lowercase hex64 de todos los bytes originales del input. |

BOM y CRLF cuentan en los hashes. No hay caché de digests entre consultas ni
normalización de texto. El lector rechaza claves JSON repetidas, campos extra,
paths duplicados y colisiones de mayúsculas en cualquier plataforma. La identidad
portable también impide alias del artefacto y del recibo; se valida todo el esquema
antes de leer inputs declarados.

Todos los `source_file` de nodos AST/code y arcos AST/EXTRACTED deben estar declarados.
También `definition_file` si no es nulo. La comprobación precede a la exclusión por
ID duplicado o fuente ausente; una exclusión no oculta una omisión del recibo.

El lector rechaza rutas remotas, absolutas de input, traversal, ADS, dispositivos
y aliases de nombres Windows. Rechaza enlaces/junctions en archivos o ancestros,
archivos no regulares y aliases físicos entre inputs, grafo y recibo.
La lectura estable comparte `local-read.py`; sus comprobaciones no garantizan una
fotografía atómica frente a cambios concurrentes o ABA.

## Cómo leer el resultado y la vigencia

```bash
python3 "$SHAREDKIT/code-context.py" \
  --project . --graph graphify-out/graph.json \
  --source-file agent-kits/shared/code-context.py --label 'query_graph()'
```

Puedes sustituir el par por `--node-id <exact-id>` o por `--symbol query_graph`.
`--sources-manifest <relative-receipt>` elige un recibo explícito. Si falta,
la consulta devuelve `verification-unavailable`; no cae al modo legacy.

Cuando existe un recibo válido, cada consulta lee todos sus inputs, incluidos
los no seleccionados. Comparte los digests solo dentro de esa llamada.

| Condición | Estado y contexto |
|---|---|
| Sidecar automático ausente | Consulta legacy con `freshness: unverified`, `verification.state: legacy-unverified` y aviso. |
| Todos los inputs coinciden con el recibo ligado al artefacto | Resultado del selector, `freshness: verified-declared-inputs`. |
| Input declarado ausente o bytes distintos | `artifact-stale`, `freshness: stale`, nodos/arcos vacíos. |
| Recibo mal formado, binding o cobertura inválidos | `verification-invalid`, contexto vacío. |
| Permisos, presupuesto o lectura inestable | `verification-unavailable`, contexto vacío y diagnóstico parcial. |

Un desfase probado persiste aunque otro input falle después. La ambigüedad conserva
los diagnósticos de vigencia sin inventar contexto. Un fallo de lectura inicial del
grafo mantiene `artifact_sha256: null`; no atribuye un digest a bytes que no pudo leer.
La CLI devuelve 2 para no disponible, inválido o stale; devuelve 0 para resultados del selector.

`verified-declared-inputs` acredita coincidencia observada con el conjunto declarado,
ligado a ese artefacto. Mantiene `coverage: unknown`, `knowledge_status: unapproved-context`
y productor no autenticado. No descubre archivos nuevos, cubre todo el proyecto ni
verifica semántica, extracción, líneas o autoridad.

## Qué límites conserva el bundle

| Recurso | Tope |
|---|---|
| Grafo | 8 MiB; 20.000 nodos y 50.000 arcos. |
| Recibo | 512 KiB. |
| Inputs declarados | 128 archivos. |
| Cada input | 1 MiB. |
| Total de inputs por consulta | 8 MiB. |

El lector y el productor reservan el byte de detección de exceso del helper.
Por eso el máximo aceptado puede ser un byte menor que el tope; un presupuesto
incompleto no se transforma en verificación o no-match.

El plugin completo incluye estas herramientas. El export de solo skills lleva
sus dependencias declaradas y no añade automáticamente el lector/productor AST.
Para usar estas herramientas por separado, conserva `agent-kits/shared/code-context.py`,
`agent-kits/shared/code-context-build.py`, `agent-kits/shared/local-read.py`,
`agent-kits/shared/capability-route.py` y `agent-kits/shared/redact.py`.
El lector no depende del productor para consultar.
Una instalación parcial informa no disponible y conserva la memoria local.
La lectura documental tiene otro contrato: [adaptador Kwipu](../skills/knowledge-services/references/kwipu-adapter.md#cómo-habilitar-la-lectura-documental).

La aceptación parcial observada cubre AST Python de 8 nodos/7 arcos y relectura de 4/4
inputs declarados, con edición propia stale y restauración exacta verificada.
No acredita otras gramáticas, corpus reales ni QA final de integración o release.
