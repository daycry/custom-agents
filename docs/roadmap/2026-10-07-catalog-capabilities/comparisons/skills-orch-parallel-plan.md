# Orquestación por operación, carriles paralelos y cadenas por paso — S197–S201, S206

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **32.427 bytes/588 líneas**, sin recursos locales.
[orch-parallel-plan-reading-evidence.json](orch-parallel-plan-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

Las seis piezas orquestan el ciclo de desarrollo con los agentes de otro
catálogo. El dueño de ese ciclo aquí es `/dev-cycle` (ADR-011), con
`quick-implement` como puerta en lenguaje natural de su vía rápida. **No se
adopta ninguna como pieza.** Lo aprovechable son dos filas para `tdd` y una
condición para el despacho paralelo de `/dev-cycle`. S199 cita dos hermanas,
`orch-add-feature` y `orch-build-mvp`, que están fuera de este rango.

## S199 — Motor compartido de la familia `orch-*`

`6.402 bytes/121 líneas`. Clasifica el tamaño en cuatro niveles por la señal más
alta (ficheros, dependencia o contrato nuevo, ambigüedad), elige qué fases corren
(investigar, planificar, implementar con TDD, revisar, commit) y pone dos
puertas humanas: aprobar el plan y confirmar el commit.

**Comparación.** `commands/dev-cycle.md` ya tiene la misma forma: Fase 0-bis
(vía rápida frente a flujo completo, con recomendación por tamaño), plan
aprobado, TDD opt-in, revisión de dos lentes y un commit lógico por tarea. La
diferencia útil es la regla «tocar un contrato público o una zona sensible
sube al menos a `standard`, sea cual sea el número de ficheros». Es una entrada
natural para la tabla nivel → rigor de ADR-022, que sigue en `propuesta` y cuyo
`risk-profile.py` aún no existe en el repo. La lista de disparadores de
seguridad (entrada de usuario, consultas, llamadas externas) cubre casi
cualquier diff de backend; el plugin decide la Lente C con
`review-lens-select.py`, por rutas y líneas, no con una lista en prosa.

| La pieza | Problema |
|---|---|
| La tabla da a `small` la máscara «(1 light) → 4 → 5 → 6», sin plan | S197 fija «light 2» y Gate 1 también en `small`: dos máscaras para el mismo caso |
| S200 fija suelo `standard` con máscara 0 → 2 → 4 → 5 → 6 | La tabla dice que `standard` ejecuta 1 → 2; no se dice cuál manda |
| «Cobertura ≥ 80 %» como verificación | Ninguna fase la mide; aquí la cifra es opt-in de `dev.json` y la mide `coverage-gate.py` |
| Investigación con `gh search`, Exa y registros de paquetes | Servicios externos; `research-first` declara los canales y no infiere ausencia |

**Destino:** una línea en la tabla de ADR-022 cuando se implemente
(`contrato público o zona sensible ⇒ nivel mínimo medio`). Nada más.

## S197, S198 y S200 — Cambiar, corregir y refactorizar

`1.711 bytes/43 líneas`, `1.684 bytes/43 líneas` y `1.819 bytes/44 líneas`.
Envoltorios finos del motor. Cada uno define un **primer movimiento** distinto:
cambiar un comportamiento que funciona empieza por modificar el test existente;
corregir un fallo, por un test de regresión nuevo en rojo; refactorizar, por
confirmar la suite en verde y, si la cobertura es escasa, añadir tests de
caracterización.

**Comparación.** `skills/tdd/SKILL.md` es el dueño del método. Su tabla
«Cuándo aplica» ya cubre el fallo (fila «Arreglar un fallo que ya existe», que
remite a la Fase 4 de `debug-root-cause`) y su anti-patrón 9 prohíbe que un
refactor «arregle» tests. Le faltan los otros dos casos:

| Caso | Fila propuesta para `tdd` |
|---|---|
| Cambiar un comportamiento que ya funciona | Modifica primero el test existente al comportamiento nuevo y vélo rojo por esa razón; un test cambiado que sigue verde no demuestra nada |
| Refactor puro | No hay rojo nuevo: `TDD n/a: refactor` con el mismo conjunto de tests en verde antes y después; si el área no tiene cobertura, primero tests de caracterización del comportamiento actual |

Defecto de S200: delega la limpieza en knip, depcheck y ts-prune (herramientas
de JavaScript) y su ejemplo extrae un cliente de `poller.py`.

**Destino:** las dos filas en la tabla «Cuándo aplica» de `skills/tdd/SKILL.md`.
El tipo de commit (`fix:`, `refactor:`) no se adopta: aquí el commit es por
tarea (`T-XX:`).

## S201 — Optimizador de ejecución paralela

`2.846 bytes/74 líneas`. Convierte la urgencia en un grafo de dependencias:
matriz de carriles (paralelo, secuencial o con puerta), lecturas en lote,
escrituras aisladas por fichero, worktree, rama o servicio, y una tabla final
de verificación.

**Comparación.** El paso 6 del despacho con subagentes de `/dev-cycle` ya
paraleliza hasta tres tareas de una fase sin dependencias, con worktree temporal
por tarea o con `Archivos` disjuntos, validación secuencial y medición por lote.
La pieza aporta un hueco real: **ficheros disjuntos no implican estado
disjunto**. No paraleliza migraciones, escrituras en la misma tabla ni despliegues
sin una puerta explícita. Dos tareas con `Archivos` distintos pueden migrar el
mismo esquema o escribir en el mismo servicio.

**Destino:** en el paso 6 de `commands/dev-cycle.md`, una condición más: «las
tareas que migran esquema o escriben en el mismo almacén o servicio van en
secuencia aunque sus `Archivos` no se solapen».

## S206 — Cadenas `/orchestrate` por paso del plan

`17.965 bytes/263 líneas`. Lee un plan, lo parte en pasos, etiqueta cada paso por
palabras clave y genera una línea `/orchestrate custom "<agentes>" "<tarea>"`
lista para pegar. No ejecuta nada.

**Comparación.** Aquí el plan ya nace con tareas `T-XX` y su `Archivos`
(`agents/planner.md`). `task-brief.py` construye el brief autocontenido de cada
tarea desde el ledger, y los orquestadores despachan por nombre con
`model-tier.py`. Coincide en dos reglas que el plugin ya cumple: el brief no
necesita el plan abierto, y el «fuera de alcance» se hereda solo si el plan lo
declara. El etiquetado acepta raíces de palabra «en cualquier idioma» por
significado, así que no es determinista.

| La pieza | Problema |
|---|---|
| `port` dispara `impl` y `migration`; `migration` dispara `migration` y `db` | Con la regla «primaria = primera de la tabla», un «port» nunca recibe la cadena de migración |
| El ejemplo 1 combina `impl + security + db` | Las reglas 2 y 3 solo definen pares; la cadena de cuatro sale de combinarlas sin regla |
| «Los nombres sin prefijo fuerzan coincidencia difusa, que falla de forma intermitente en llamadas paralelas» | Afirmación sin evidencia en la pieza |
| Detecta la forma de instalación por la existencia de `plugins/marketplaces/ecc/` | Depende de la ruta interna de un marketplace concreto |

**Sin destino.**
