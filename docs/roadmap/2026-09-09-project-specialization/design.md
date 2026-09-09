---
design: project-specialization
titulo: "El registro de piezas de proyecto y su script dueño (`pieces-registry.py`)"
estado: aprobado
creado: 2026-09-09
actualizado: 2026-09-09
spec: spec.md
evaluacion: evaluation.md
plan: improvement-plan.md
adr: docs/knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md   # `propuesta`; pasa a `aceptada` con la revisión de dos lentes de C-10
opcion_elegida: O1      # elegida por el usuario en la puerta de diseño (2026-09-09)
validada_por_usuario: 2026-09-09
alcance: "C-10 (registro + pieces-registry.py). NO diseña las otras 8 características."
generacion:            # ACUMULADO de las dos pasadas de diseño (P1 opciones 09:23:46-09:34:00Z · P2 elección + ADR 10:37:01-10:42:22Z)
  inicio: 2026-09-09T09:23:46Z
  fin: 2026-09-09T10:42:22Z
  fuente: estimado     # `usage-meter.py close` degradó en las dos: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio a partir de lo leído/escrito
  tokens_reales: { entrada: 102000, salida: 25000, cache_creacion: 40000, cache_lectura: 430000 }
  eur: 1.47             # P1 0.90 + P2 0.57, con rates.json (in 5 / out 25 / cc 6.25 / cr 0.5 USD por millón, fx 0.92)
  horas_ia: 0.26        # P1 0.15 + P2 0.11 — (entrada+salida)/ratio
  duracion: 15m         # 10m (P1) + 5m (P2)
  ratio_usado: 479326
---

# Diseño — El registro de piezas de proyecto y su script dueño (`pieces-registry.py`)

> **Spec:** [`spec.md`](spec.md) (aprobada) · **Evaluación:** [`evaluation.md`](evaluation.md) (`C-10`, 5,0 h, complejidad Alta) · **Plan:** pendiente · **ADR:** [`ADR-014`](../../knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md) (`propuesta`)

| | |
|---|---|
| **Estado** | `aprobado` — la opción está cerrada; el plan debe respetarla |
| **Opción elegida** | **O1** — la pieza es la raíz y sus destinos van anidados (era también la recomendación del arquitecto) |
| **Validada por el usuario** | 2026-09-09 (puerta de diseño, elección explícita `O1`) |
| **Alcance** | Solo `C-10`: la forma del registro y el contrato del script que lo posee |

## 1. Contexto y restricciones

La spec aprobada fija el **qué** del tercer bucle y deja el **cómo** del registro sin cerrar: su
§Supuestos dice literalmente que el esquema «lo cierra el `planner`». La evaluación corrigió eso y lo
convirtió en arista del grafo — `C-10` entra **antes** de `C-05` y `C-06` (condición (a) del go),
porque el esquema se fija «dentro de C-10, donde hay un test que la sostiene». Este diseño decide
exactamente eso y nada más: la **forma de una entrada** del registro y el **contrato** de
`agent-kits/shared/pieces-registry.py`. Las otras ocho características no se diseñan aquí.

Nueve criterios de aceptación dependen de esta decisión: CA-17 (propiedad por registro + hash y
confirmación extra sobre el árbol del plugin), CA-18 (tope de 5 **acumulado en el registro**), CA-19b
(`Bash`/`Write` solo con confirmación **registrada en la fila**), CA-20 y CA-21 (una línea por fila en
`/doctor` y biyección registro↔ficheros con mutante de hash), CA-23 (`modificada`), CA-24 (adopción),
CA-25 (idempotencia), CA-26 (concurrencia con `.lock`) y CA-28 (una fila por ruta y runtime, cada una
con su hash).

Lo que hay hoy en el repo, con ruta, y de lo que este diseño hereda idioma en vez de inventarlo:

| Pieza real | Qué aporta |
|---|---|
| `agent-kits/shared/journal.py:224-274` | El cerrojo del repo: `fcntl.flock` (POSIX) o `msvcrt.locking` en bucle acotado (Windows) sobre un `<fichero>.lock` hermano |
| `agent-kits/shared/journal.py:200` (`redactar`) y `:121` | Redacción determinista de secretos evidentes que CA-27 obliga a reutilizar tal cual |
| `agent-kits/shared/journal.py:209-219` | Cómo se siembra `.claude/.gitignore` en el consumidor (hoy con `session-prompts-*`) |
| `agent-kits/shared/usage-meter.py:123-135` (`_save_state`) | Escritura atómica `temp + os.replace` y estado corrupto que degrada sin romper |
| `tests/test_doctrina_viaja.py:47-53` | La normalización `\r\n` → `\n` **antes** de comparar contenido, y por qué (el falso «difiere» de `GOT-007` §2) |
| `tests/test_confluence_scope.py:167` | El precedente de manifiesto `ruta → {hash, …}` de `confluence-state.json` |
| `agent-kits/shared/progress-report.py:51`, `scope-check.py:53`, `doctor.py:172` | Importar un script hermano con `importlib.util.spec_from_file_location` (los nombres llevan guion) |
| `install/providers.mjs:167-168` (`PROVIDERS` / `IDS`) | Dónde vive el conocimiento de runtimes, que este script **no** debe tener |
| `docs/CONVENTIONS.md` regla 9 (169-188) | La convención config-comiteada / estado-ignorado a la que se añaden dos filas |
| `agent-kits/shared/skill-index.py:44-45` | `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`: el presupuesto que justifica el tope de 5 |

**Restricciones que fijan el espacio de soluciones**

- **Solo stdlib**, como todos sus hermanos de `agent-kits/shared/`; sin dependencias externas.
- **El veredicto va en el script**, con tests y exit codes; la prosa de `/specialize` y de `/doctor`
  decide *cuándo* llamarlo, nunca *el resultado* (regla de determinismo de `CLAUDE.md`).
- **El script no sabe de runtimes**: recibe rutas y un identificador de runtime como dato. Un cuarto
  proveedor es una fila en `PROVIDERS`, nunca un cambio de esquema aquí.
- **Degradación sin bloqueo**: sin `python3`, sin registro o con registro corrupto → aviso y
  comportamiento clásico. Nunca romper el ciclo.
- **`GOT-003`**: el `.claude/` de destino puede ser el árbol desplegado del propio plugin. La
  propiedad es **registro + hash, nunca carpeta**.
- **`GOT-005`**: consola `cp1252`. La salida del script es ASCII; los iconos los pinta `/doctor`.
- **`GOT-007`**: este repo está en `core.autocrlf=true` sin `.gitattributes`, así que el árbol de
  trabajo queda mezclado (CRLF y LF) sin que cambie el contenido. Y la puerta que vigila un script
  nuevo (`tests/test_console_encoding.py`) solo ve ficheros **versionados**: se corre tras `git add -N`.
- **`ADR-007`**: un `deny` solo existe con alcance de agente. Lo que el registro almacena es la
  **confirmación** de un permiso, jamás la concesión implícita.
- **La spec fija `.claude/pieces.json` como fichero único** y seis CA lo nombran por ruta. La tensión
  con `ADR-006` («un fichero por entrada», decidido en parte por colisión de escritura en paralelo)
  queda anotada en §7 y **no se reabre por cuenta propia**.

## 2. Opciones (3)

### 2.0 Decisiones comunes a O1 y O2 (forzadas por la doctrina del repo, no elegidas)

Estas siete no son opciones: cada una tiene una sola respuesta defendible en este repo, y presentar
variantes de relleno sería engañar a quien valida. Se escriben aquí con su alternativa descartada, y
[`ADR-014`](../../knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md) las
cierra como **parte de la decisión**, no como apéndice. **O3 no las comparte**: cambia la mecánica entera.

| Decisión | Elección | Alternativa descartada y por qué |
|---|---|---|
| **Cómo se calcula el hash** | `sha256` sobre los bytes del fichero con `\r\n` → `\n` normalizado, guardado como `"sha256:<hex>"`, con un `hash_version` en la cabecera del registro | **Bytes crudos**: en `core.autocrlf=true` un `git checkout` re-materializa unos ficheros y no otros, y toda pieza intacta se leería como `modificada` — es el caso 2 de `GOT-007`, que ya costó una CI roja (`tests/test_doctrina_viaja.py:47-53`). **Blob de git** (`git hash-object`): exige `git` en PATH y el registro tiene que funcionar sin él |
| **Sobre qué contenido** | El fichero **completo**, leído en binario (vale igual para `.md`, `.toml` y `.py`) | **Excluir el frontmatter o campos generados**: obliga a un segundo normalizador sincronizado con el generador; cualquier desfase se lee como `modificada` |
| **Nunca corrupto vs. no perder una fila** | Son **dos promesas con dos mecanismos**: `temp + os.replace` garantiza que el JSON nunca queda a medias (precedente `usage-meter.py:_save_state`); el `.lock` serializa el leer-modificar-escribir. CA-26 pide las dos y el test las comprueba **por separado** | **Confiar solo en el lock**: un proceso muerto a mitad de escritura deja el JSON roto aunque el cerrojo fuese perfecto. Es el fallo que el repo ya pagó en `debt-cleanup` |
| **Qué pasa si el lock está tomado** | Espera acotada (~3 s, el bucle de `journal.py`) y luego **exit 4 con aviso** «registro ocupado, reintenta». La **lectura** no toma cerrojo: el `replace` atómico hace que un lector nunca vea un fichero a medias | **Escribir sin cerrojo al no conseguirlo**, que es lo que hace `journal.py`: correcto para un log de *append*, **incorrecto** para un leer-modificar-escribir de un JSON compartido (pierde la fila del otro en silencio) |
| **Idempotencia** | Serialización canónica (piezas ordenadas por nombre, claves en orden fijo, `indent=2`, `ensure_ascii=False`) y **no se escribe si los bytes serializados no cambian** → «sin cambios», exit 0. Corolario: en `pieces.json` **no entra nada volátil** (ni `actualizado`, ni contadores, ni fecha de última auditoría); eso vive en `pieces-state.json`, ignorado | **Un `actualizado` por fila**: rompe la idempotencia por bytes, ensucia el diff en cada corrida y convierte un fichero comiteado en ruido de merge |
| **Propiedad (`GOT-003`)** | Una **sola puerta**, `dueno(<ruta>)`: escribir o retirar exige fila con hash coincidente, o **exit 3** y lo dice. Confirmación **extra anotada en la fila** si la raíz del destino tiene marcadores `agent-kits/` o `.claude-plugin/` y la forma es skill o agente. Nombres **reservados**: `pieces.json`, `pieces-state.json` y `pieces.json.lock` no son adoptables ni destino de una pieza | **Comprobar por carpeta** («si está en `.claude/personas/` es mío»): es exactamente el fallo de `GOT-003`, donde un generador pisó un canónico dentro del árbol que espejaba |
| **Adopción** | `adopt <ruta>` añade fila con el hash **actual**, `origen: adoptada` y estado derivado `modificada` (no hay generación de referencia). **Rehúsa** (exit 3) si la ruta ya tiene fila, si cae fuera de las raíces de destino del proyecto, o si su raíz tiene marcadores de plugin desplegado — ahí exige `--confirmar-arbol-plugin`, que queda anotado en la fila con su fecha | **Adoptar cualquier ruta que exista**: permite arrastrar al registro un fichero del plugin desplegado por accidente y, desde ese momento, el generador se cree su dueño |
| **Runtimes** | El script recibe `--destino <ruta>:<runtime-id>` y **no valida el id contra una lista cerrada**. Un cuarto runtime es un valor de dato más | **Enumerar los runtimes en el esquema** (claves `codex`/`opencode`): rompe el invariante y convierte cada proveedor nuevo en una migración |
| **Degradación** | Sin `pieces.json` → registro vacío, todo `no gestionada`, exit 0. **Corrupto** → se lee como vacío **con aviso** y la escritura se **rehúsa** (exit 2) nombrando el arreglo: `--reconstruir` aparta el fichero a `pieces.json.corrupto-<ts>` y lo rehace desde el disco | **Reconstruir en silencio**: pisa un fichero comiteado y compartido por el equipo sin que nadie lo haya pedido |
| **Privacidad** | `redactar()` importado de `journal.py:200` sobre todo texto de evidencia antes de escribirlo; una ruta bajo `docs/security-scan/` **no se cita** (rechazo, no redacción) | **Redactar con heurística propia**: dos implementaciones de lo mismo divergiendo, justo lo que `LES-013` desaconseja |

**Contrato del script (común a O1 y O2; es lo que consumen `C-05`, `C-06` y `C-11`).** Subcomandos
`estado <ruta>…` · `dueno <ruta>` · `registrar` · `adopt` · `listar [--json]` · `auditar` · `tope`,
con `--project-dir` y `--json`. Exit codes: **0** ok · **1** hallazgos de `auditar` · **2** registro
ilegible o corrupto · **3** rehusado por propiedad (`GOT-003`) · **4** registro ocupado (lock) · **5**
tope superado sin confirmación. El **estado no se persiste**: se deriva comparando el hash del disco
con el anotado, en cada lectura. `auditar` distingue los tres estados de la spec de un cuarto hallazgo
que **no** es un estado de fichero sino un defecto del registro: la **fila huérfana** (fila sin
fichero), que es la que CA-21 pide marcar.

### O1 — La pieza es la raíz; sus destinos van anidados (agregado)

Una entrada por **pieza**, con sus N destinos dentro (el canónico de Claude Code más las variantes de
cada runtime). El campo `runtime` es un dato de cada destino.

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

El tope de CA-18 es `len(piezas)`: un recuento exacto de **piezas**, no de ficheros. La búsqueda por
ruta (la operación de `GOT-003`) se resuelve con un índice invertido construido al cargar,
encapsulado en `dueno()` para que haya una sola entrada al veredicto.

| Criterio | Valoración |
|---|---|
| Complejidad | **Media** — el esquema es un agregado y las operaciones (registrar, adoptar, retirar) tocan **un solo objeto** bajo el lock; lo único que añade es el índice invertido ruta→destino |
| Riesgo | El índice invertido mete un paso entre la ruta y la fila: si algún flujo lo consulta con el registro ya mutado en memoria, el veredicto de propiedad se calcula sobre datos viejos. Y «la misma ruta en dos piezas» **es representable**: hay que rechazarla al escribir, con su test |
| Coste relativo | **M** — el índice y su validación de rutas duplicadas son una función y dos tests |
| Reversibilidad | **Alta hacia O2** (aplanar el agregado es determinista y sin pérdida) y **baja al revés**: volver de O2 a O1 exige reconstruir la agrupación, que solo es fiable si la referencia `pieza` está sana |

### O2 — Dos tablas normalizadas: `piezas` por nombre y `destinos` por ruta

El registro como un fichero casi relacional. La tabla `destinos` está indexada **por la ruta**, que es
la clave de la operación peligrosa, y apunta a su pieza por nombre.

```json
{
  "version": 1,
  "hash_version": "sha256-lf-1",
  "piezas": {
    "hooks": { "forma": "persona", "area": "hooks", "origen": "generada", "creada": "2026-09-09",
               "evidencia": ["hooks/session-end.sh:12"], "confirmaciones": { "tools": [] } }
  },
  "destinos": {
    ".claude/personas/hooks.md": { "pieza": "hooks", "runtime": "claude-code", "canonica": true,  "hash": "sha256:ab12…" },
    ".codex/agents/hooks.toml":  { "pieza": "hooks", "runtime": "codex",       "canonica": false, "hash": "sha256:cd34…" }
  }
}
```

Tiene precedente literal en el repo: `confluence-state.json` es un manifiesto `ruta → {hash, pageId}`
(`tests/test_confluence_scope.py:167`). La regla dura de `GOT-003` pasa a ser un `destinos.get(ruta)`:
la forma del fichero **es** el índice, sin código intermedio. CA-28 («una fila por ruta con su propio
hash») se lee al pie de la letra.

| Criterio | Valoración |
|---|---|
| Complejidad | **Media** — misma clase que O1, pero cada operación toca **dos** estructuras bajo el mismo lock (alta, adopción y retirada escriben en `piezas` y en `destinos`) |
| Riesgo | El estado inválido **destino colgado** (`destinos[].pieza` que no existe en `piezas`) es representable, así que aparece una **tercera invariante** —integridad referencial— que el test de biyección tiene que cubrir con su propio mutante. Y en la revisión del PR una pieza no se lee de un tirón: hay que cruzar dos secciones |
| Coste relativo | **M**, ligeramente por encima de O1: la misma mecánica más el test de integridad referencial y la doble escritura |
| Reversibilidad | **Media** — agrupar destinos por `pieza` para volver a O1 es determinista *mientras* la referencia esté sana; con destinos colgados, la agrupación es una decisión manual |

### O3 — Sin registro: procedencia en el propio fichero y estado derivado del disco

No existe `pieces.json`. Cada pieza generada nace con una marca de procedencia reservada en su
cabecera (`generado-por: specialize`, `hash-origen: sha256:…` calculado sobre el contenido **sin** la
línea de la marca) y el estado se deriva escaneando `.claude/` (y `.codex/`, `.opencode/`) en cada
arranque: marca con hash que cuadra → `gestionada`; marca con hash que no cuadra → `modificada`; sin
marca → `no gestionada`.

**A favor, en serio.** Es la opción más simple y hay que valorarla como tal: cero esquema y por tanto
**cero migración** — desaparece el riesgo (c) que la evaluación anota sobre `C-10` («si la lista de
campos se queda corta, `C-11` fuerza una migración a mitad de fase»); cero lock y cero concurrencia,
porque no hay fichero compartido que reescribir; cero conflictos de merge; y la biyección
registro↔ficheros no puede desincronizarse porque no hay registro. Es también la que menos código
nuevo pide.

**En contra, medido contra la spec aprobada.** Rompe seis criterios tal como están escritos, y uno de
ellos por una razón de fondo, no de forma:

- **CA-19b** — la confirmación de `Bash`/`Write` debe quedar «registrada en la **fila**». Sin fila, el
  único sitio donde cabe es la marca del propio fichero, es decir: **el permiso queda auto-declarado
  por el artefacto que gobierna**, y ese artefacto es justo el que un humano puede editar. Con
  `ADR-007` delante, esto es el argumento decisivo contra O3.
- **CA-26** — exige literalmente el `.lock` hermano de `.claude/pieces.json`.
- **CA-21** — biyección registro↔ficheros con mutante de hash: sin registro no hay biyección que testear.
- **CA-18** — el tope de 5 pasa de propiedad auditable de un fichero comiteado a recuento de un escaneo.
- **CA-28** — la marca no sobrevive igual en todos los formatos generados, y las variantes las escribe
  `export-interop.py`, que no sabe de marcas.
- **`analysis.md` §2** — el tercer bucle se define por tener **registro canónico con test de biyección**,
  igual que `tasks.md` y `docs/knowledge/README.md`. Sin él, `/doctor` audita un escaneo, no un acuerdo
  del equipo, y el bucle pierde la gramática que lo hacía un bucle.

| Criterio | Valoración |
|---|---|
| Complejidad | **Baja** — no hay esquema, ni lock, ni concurrencia, ni fichero compartido |
| Riesgo | **Alto, pero de otra clase**: no es riesgo técnico sino de **alcance** — obliga a reabrir la spec aprobada (seis CA) y a rehacer parte de la evaluación (`C-06` y `C-11` cuelgan del registro). Y deja el permiso de `tools` declarado dentro del fichero editable, contra `ADR-007` |
| Coste relativo | **S** — la más barata de construir, con diferencia |
| Reversibilidad | **Baja en el sentido que importa**: volver a un registro después exige adoptar N piezas ya vivas y cambiar el contrato que `C-05` y `C-06` ya consumirían. Es viable (el modo `--adopt` existiría) pero es trabajo y una segunda ronda de decisiones |

## 3. Criterios de decisión

En esta decisión pesa más lo que cuesta deshacerla que lo que cuesta hacerla; de ahí el orden:

1. **Coste de la vuelta atrás sobre el esquema.** La evaluación puso `C-10` como raíz del grafo
   precisamente porque, con proyectos que ya tengan registro escrito, cambiar su forma es migración,
   no refactor. Pesa por encima del coste de construcción.
2. **La regla dura de `GOT-003` tiene que ser una sola puerta.** Su fallo escribe en el árbol del
   propio plugin: cuanto más corto sea el camino de «ruta» a «¿es mía?», mejor.
3. **Un criterio de aceptación, un campo** (no un cálculo derivado). CA-18, CA-19b, CA-21, CA-23 a
   CA-26 y CA-28 deben ser verificables leyendo el registro.
4. **Mejor un estado inválido irrepresentable que uno detectado por auditoría.** Cada estado inválido
   que se puede escribir es un test y un mutante más dentro de un presupuesto de 5,0 h y ~25-30 tests.
5. **Un cuarto runtime sin cambio de esquema**, porque el script no sabe de runtimes.
6. **Legibilidad en la revisión.** `pieces.json` es config comiteada que el equipo lee en un PR.
7. **Coste relativo de construcción** — el último: la evaluación ya fijó 5,0 h y las tres opciones caben.

## 4. Recomendación · opción elegida y por qué

**Opción elegida: O1** — la pieza es la raíz y sus destinos van anidados (`piezas[]` con
`destinos[{runtime, ruta, hash}]`). La eligió el **usuario** en la puerta de diseño del **2026-09-09**,
y coincide con la recomendación del arquitecto de la pasada 1. Por los criterios, en su orden:

- **Criterio 4 (el que decide).** En O1 el estado inválido «destino sin pieza» es **irrepresentable
  por construcción**; en O2 hay que detectarlo con una invariante de integridad referencial, su test y
  su mutante. Con un presupuesto de ~25-30 tests que ya tiene que cubrir lock real, tres estados,
  idempotencia, adopción y `GOT-003`, quitar una invariante del tablero vale más que ganar un
  `dict.get`.
- **Criterio 3.** El tope de CA-18 es `len(piezas)` —recuento de piezas, que es lo que la spec dice—
  sin deduplicar por nombre; y `evidencia` y `confirmaciones` (CA-19b) viven **una sola vez** por
  pieza, no repetidas por runtime.
- **Criterio 1.** O1 → O2 es un aplanado determinista y sin pérdida si mañana pesa más el *lookup*;
  el camino inverso no lo es. Cuando dos opciones son parecidas, se elige la que deja la puerta abierta.
- **Criterio 6.** Una pieza se lee de un tirón en el diff del PR: forma, evidencia, permisos
  confirmados y todos sus destinos en un bloque.

Lo que O1 cuesta y O2 no: el índice invertido ruta→destino y el rechazo de rutas duplicadas entre
piezas. Se paga con una función encapsulada en `dueno()` y dos tests, y a cambio la regla de `GOT-003`
tiene una sola entrada.

### Opciones descartadas, con su motivo

| Opción | Motivo del descarte | Lo que tenía a favor (y se pierde) |
|---|---|---|
| **O2** — dos tablas normalizadas (`piezas` por nombre + `destinos` por ruta) | Criterio 4: el estado inválido «un destino sin pieza dueña» es **representable** y obliga a una invariante extra de **integridad referencial**, con su test y su mutante, dentro de un presupuesto de 5,0 h y ~25-30 tests. Criterio 3: el tope de CA-18 deja de ser `len(piezas)` y pasa a ser un cálculo | Era la rival real: la forma del fichero **es** el índice, así que `GOT-003` se resolvía con un `destinos.get(ruta)` sin código intermedio, y tenía precedente literal en el repo (`confluence-state.json`, `tests/test_confluence_scope.py:167`) |
| **O3** — sin registro; procedencia en el propio fichero y estado derivado del disco | **Decisivo:** sin fila, la confirmación de `Bash`/`Write` (CA-19b) solo cabe en la marca **dentro del propio fichero de la pieza**, es decir el permiso queda **autodeclarado por el artefacto que gobierna** — y es justo el que un humano puede editar a mano. Con `ADR-007` delante, se cierra ahí. Secundario: rompe CA-18, CA-19b, CA-21, CA-26 y CA-28 tal como están escritas y contradice `analysis.md` §2, donde el bucle se **define** por tener registro canónico | Era la **más simple y la más barata** (complejidad **Baja**, coste **S**, la que menos código pedía): cero esquema y por tanto cero migración, cero cerrojo, cero conflictos de merge y ninguna biyección que pueda desincronizarse |

**Reversibilidad de la elegida, para que conste:** O1 → O2 sigue siendo un **aplanado determinista y
sin pérdida** si algún día pesa más el *lookup* por ruta. La decisión es reversible **en esa dirección**;
el camino inverso solo es fiable si la referencia `pieza` está sana, y por eso se eligió la que deja la
puerta abierta.

## 5. Impacto en módulos y ficheros

Solo lo que toca `C-10`. Las filas marcadas «otra característica» son **consumidores** del contrato de
§2.0 y no se diseñan aquí.

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `agent-kits/shared/pieces-registry.py` | La pieza: subcomandos y exit codes de §2.0, hash normalizado, cerrojo, tres estados derivados, adopción, regla de propiedad. Dimensionado por la evaluación en ~400 líneas | Nuevo |
| `agent-kits/shared/test_pieces_registry.py` | ~25-30 tests: hash con fixture en CRLF **y** en LF exigiendo el mismo hash; corrupción (proceso muerto a mitad) y pérdida de fila (dos procesos reales) como pruebas separadas; tres estados; fila huérfana; idempotencia por bytes; adopción y sus tres rechazos; `GOT-003` sobre un árbol con marcadores; tope acumulado | Nuevo |
| `agent-kits/shared/journal.py` | Se **importa** (`redactar` :200 y las primitivas de cerrojo :224-253) con `importlib.util`; si la revisión rechaza importar privados, la única alternativa aceptable es promoverlos a nombre público ahí — nunca una segunda implementación del cerrojo | Modificado (posible, una línea) |
| `tests/test_console_encoding.py` | Entrada del script nuevo en la tabla `MODOS` (`GOT-005`), y la suite se corre **después** de `git add -N` (`GOT-007`) | Modificado |
| `docs/CONVENTIONS.md` regla 9 (169-188) y su espejo `docs/en/CONVENTIONS.md` | Dos filas: `pieces.json` (config, comiteada, entradas ordenadas por nombre) y `pieces-state.json` (estado, ignorado, se recrea) | Modificado |
| `.gitignore` del repo y siembra de `.claude/.gitignore` en el consumidor (patrón `journal.py:209-219`) | `pieces-state.json` y `pieces.json.lock` fuera del control de versiones | Modificado |
| `.claude/pieces.json` · `.claude/pieces-state.json` | Los artefactos del bucle. `pieces-state.json` guarda **solo** la huella del último escaneo (para que `/specialize` sepa decir «sin cambios») y **no se crea vacío** | Nuevo (en el consumidor) |
| `agent-kits/shared/doctor.py` | Consume `listar --json` y `auditar` (`C-06`) | Modificado (otra característica) |
| `commands/specialize.md` | Consume `dueno`, `registrar`, `adopt`, `tope`: secuencia, no calcula (`C-05`) | Nuevo (otra característica) |
| `scripts/export-interop.py` | Registra los destinos que escribe, con su runtime y su hash (`C-11`) | Modificado (otra característica) |
| `docs/SPECIALIZATION.md` (+ espejo EN) | Documenta el esquema elegido y los tres estados (`C-02`/`C-05`) | Nuevo (otra característica) |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **El cerrojo, verde en el test y roto en la práctica** (precedente propio: el debounce de la línea de progreso se tuvo que rehacer con `flock` + rename atómico en `debt-cleanup`) | Media | **Alto** | Dos promesas, dos tests **separados**: corrupción (matar el proceso a mitad de escritura, comprobar JSON válido) y pérdida de fila (**dos procesos reales** con `subprocess`, no dos hilos). En Windows el camino es `msvcrt` en bucle acotado y, si no se consigue, **exit 4** — nunca escribir sin cerrojo |
| **Falso `modificada` por finales de línea** | **Alta si se hashean bytes crudos** | Medio | Normalización `\r\n` → `\n` antes de hashear (`GOT-007` §2) + test con el mismo contenido en CRLF y en LF exigiendo el **mismo** hash |
| **El esquema se queda corto y `C-11` fuerza una migración a mitad de fase** (riesgo (c) de la evaluación) | Media | **Alto** | `version` y `hash_version` en la cabecera, con la regla «versión desconocida → solo lectura y aviso»; `runtime` como dato y no como clave; la lista de campos la cierra `ADR-014` (decisión 6) con un test que la sostiene |
| **Escribir en el árbol del plugin desplegado** (`GOT-003`) | Media | **Alto** | `dueno()` como única puerta y exit 3; marcadores `agent-kits/`/`.claude-plugin/` + confirmación extra **anotada en la fila**; nombres reservados; test sobre un árbol marcado |
| **El registro comiteado en conflicto de merge** | Media | Bajo | Orden estable por nombre, serialización canónica y **nada volátil dentro**: el conflicto queda en el bloque de una pieza y se resuelve conservando las dos |
| **Importar privados de un script hermano** (`_bloquear`/`_desbloquear` de `journal.py`) | Media | Bajo | Precedente de importación por `importlib` ya establecido; si la Lente B lo marca, se promueven a públicos ahí (una línea). Lo que **no** se acepta es duplicar el cerrojo |
| **`pieces-state.json` naciendo vacío** (incógnita anotada en la evaluación) | Baja | Bajo | Se le da contenido concreto (huella del último escaneo) y regla explícita: si no hay contenido, **no se crea el fichero** — un fichero vacío es una fila muerta en la regla 9 |
| **Un CA verde por afirmación** porque la mecánica vive en la prosa del comando | Alta si no se respeta el contrato | Medio | Todo lo verificable baja al script (§2.0) con exit codes; `/specialize` y `/doctor` solo secuencian, que es la mitigación que la evaluación ya pide en su riesgo transversal |

## 7. Preguntas abiertas

1. **Fichero único vs. un fichero por pieza.** `ADR-006` decidió «un fichero por entrada» para gotchas
   y lecciones, entre otras razones por **colisión de escritura en paralelo** — el mismo problema que
   aquí se resuelve con un cerrojo. La spec aprobada fija `.claude/pieces.json` y seis CA lo nombran por
   ruta, así que el diseño lo respeta. Si el usuario quiere alinearlo con `ADR-006`
   (`.claude/pieces/<nombre>.json` + índice), es un cambio de **spec**, no de diseño.
2. **Dónde vive el tope de 5.** La spec lo asume en `.claude/dev.json` (§Supuestos). El diseño lo lee de
   ahí con default 5, pero el nombre exacto de la clave lo fija el `planner` junto con `/setup`.
3. **Quién invoca `--reconstruir`** tras un registro corrupto: `/doctor` imprimiéndolo como arreglo
   sugerido, o `/specialize` ofreciéndolo. El script queda listo; la puerta es de `C-05`/`C-06`.
4. **El campo `estado` no se persiste** (se deriva del hash en cada lectura). Si `/doctor` quisiera
   histórico («ayer estaba gestionada»), eso sería `pieces-state.json` y no está pedido en esta iteración.
5. ~~**Si se elige O3**, hay que decidir quién reescribe los seis CA afectados.~~ **Cerrada** el
   2026-09-09: el usuario eligió **O1**, así que la spec aprobada no se reabre y ni `C-06` ni `C-11`
   necesitan re-evaluación. Queda anotada porque era la más cara de las cinco si la respuesta hubiese
   sido la otra.
6. **`ADR-014` nace `propuesta`.** Pasa a `aceptada` cuando la revisión de dos lentes valide la
   implementación de `C-10` contra este esquema. Si esa revisión pide un campo que no está en la
   decisión 6 del ADR, el camino es **subir `version`**, no reinterpretar el esquema.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-09 | Diseño creado (`borrador`); tres opciones presentadas al usuario, recomendación O1, `opcion_elegida: pendiente` |
| 2026-09-09 | El usuario elige **O1** → `aprobado`. Descartadas O2 y O3 con su motivo y con lo que tenían a favor (§4); `ADR-014` escrito (`propuesta`) con las siete decisiones de §2.0 dentro de la decisión; pregunta abierta 5 cerrada |
