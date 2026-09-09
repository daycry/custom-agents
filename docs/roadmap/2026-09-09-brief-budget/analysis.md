---
analisis: brief-budget
descripcion: >
  El brief del subagente (`task-brief.py`) tiene un tope de 10.000 caracteres (spec CA-08 de
  `memory-retrieval`) y SOLO una de sus siete secciones tiene presupuesto propio. Medido sobre el
  ledger de `project-specialization`: 8 de 22 briefs se pasan del tope con la persona ya reducida al
  mínimo (11 de 22 con la persona del catálogo entera), `## Diseño` entra entero en los 22 (3.510
  caracteres, el 35 % del tope) y la tabla de gaps no tiene tope. Precede la spec: aquí no hay plan ni
  presupuesto, solo la medición y las opciones.
estado: borrador
creado: 2026-09-09
spec: spec.md (derivada de este análisis el 2026-09-09; su presupuesto, en evaluation.md)
fuente: revisión de dos lentes de project-specialization F1 (intento 2, gap B-3 y nota «Preexistente»); decisión del usuario de atacar la causa en iniciativa aparte (opción B)
relacionado: docs/roadmap/2026-09-09-project-specialization/tasks.md · docs/knowledge/gotchas/GOT-008-tope-ca08-del-brief-depende-de-ruta-y-corpus.md · docs/knowledge/gotchas/GOT-009-presupuesto-del-brief-se-rompe-con-design-md.md
---

# El presupuesto del brief está roto, y solo una sección tiene tope

## El resumen en una frase

**`BRIEF_TOPE_CHARS = 10000` es una promesa que el brief no puede cumplir en cuanto la iniciativa tiene
`design.md`, porque seis de sus siete secciones no tienen presupuesto propio y una de ellas (`## Diseño`)
ocupa por sí sola el 35 % del tope.** La persona de proyecto que acaba de entregar F1 de
`project-specialization` no lo causó: lo destapó, porque fue la primera sección variable a la que se le
pidió caber en un margen que ya no existía.

## 1. Qué se midió, cómo, y qué salió

Medición del 2026-09-09 sobre el ledger REAL de `docs/roadmap/2026-09-09-project-specialization/`
(22 tareas, `design.md` aprobado, `docs/knowledge/` con 37 entradas), ejecutando
`python agent-kits/shared/task-brief.py <carpeta> T-XX` para cada tarea y partiendo la salida por sus
encabezados `## `. Cifras en **caracteres**, que es lo que compara el tope.

| Sección del brief | Mediana | Máximo | ¿Tiene tope propio? | Observación |
|---|---|---|---|---|
| Cabecera + `## Contexto de fase` + `## Contrato de retorno` | ~1.025 | 1.025 | fijo | estructural, no se toca |
| `## La tarea` (descripción, criterios, subtareas) | 2.632 | 3.845 (T-05) | **no** | es EL contrato: no se recorta |
| `## Verificación` | 764 | **2.285** (T-02) | **no** | arrastra la evidencia pegada en el ledger |
| `## Memoria técnica` | 1.194 | 2.324 | **sí** (`MEMORIA_TOPE_CHARS = 2400`) | la única con presupuesto; recorta y lo dice |
| `## Diseño` | **3.510** | **3.510** | **no** | **constante en las 22 tareas**: la sección «opción elegida» de `design.md` entra entera, tenga o no que ver con la tarea |
| `## Gaps pendientes de revisión` | 0 | **4.396** (T-01) | **no** | la tabla de los intentos de revisión entra entera |
| `## Persona de dominio` | ~1.100 | 1.321 | sí, desde F1 de `project-specialization` (suelo + margen) | la única sección que se sacrificaba |

**Resultado: 8 de 22 briefs por encima de 10.000 con la persona ya reducida al mínimo; 11 de 22 con la
persona del catálogo del plugin entera.** El mayor, T-01, mide **14.799** (48 % sobre el tope). Y en el
momento de la medición **cero avisos por stderr**: el tope se afirmaba solo en tests.

### La aritmética que lo explica

Antes de que entre una sola línea de la tarea, el brief ya lleva:

```
fijo 1.025 + diseño 3.510 + memoria (mediana 1.194 … tope 2.400)  =  5.729 … 6.935
```

Quedan **4.271 en la mediana y 3.065 en el peor caso** para la tarea, su verificación y la persona. La
tarea mediana (2.632) más su verificación mediana (764) son **3.396**: ya no cabe nada más con la memoria
al tope. **Con `design.md` presente, el presupuesto está roto por construcción**, no por una tarea gorda.

## 2. Por qué nadie lo vio

Tres razones, las tres verificadas:

1. **El test que guarda el CA-08 recorre UN solo ledger.**
   `test_ca08_el_brief_completo_cabe_en_el_tope_sobre_el_ledger_real_de_memory_retrieval`
   (`agent-kits/shared/test_task_brief.py:739`) mide todas las tareas de `2026-09-04-memory-retrieval`,
   que es una iniciativa **sin `design.md`**. El guardarraíl nunca ha visto un brief con `## Diseño`.
   `project-specialization` es la primera iniciativa del repo que llega a `/dev-cycle` con un diseño
   aprobado, así que es la primera vez que la sección existe de verdad.
2. **`GOT-008` diagnosticó el problema anterior y su remedio da por hecho que no hay diseño.** Dice:
   «deja margen en los bloques de tarea del ledger (≤ ~9.500 caracteres)». Con 6.935 comprometidos
   antes de la tarea, ese remedio es inaplicable: un bloque de tarea de 3.000 ya desborda. `GOT-008` sigue
   siendo cierto en lo suyo (ruta absoluta + corpus); lo que aquí cambia es la premisa.
3. **No había aviso en runtime.** El tope vivía solo en asserts de tests. F1 de `project-specialization`
   añade el aviso por stderr con la causa medida; hasta entonces, un brief de 14.799 salía con `rc=0` y
   silencio.

## 3. Lo que NO es el problema (para no arreglar lo que no está roto)

- **No es la persona.** F1 la acota (suelo garantizado + margen real) y la delimita. Está fuera de esta
  iniciativa: `project-specialization` T-01.
- **No es la memoria.** Es la única sección bien resuelta: tope propio, recorte alineado, aviso. **Es el
  patrón a copiar**, no a tocar.
- **No es el tope de 10.000.** Es un requisito de la spec de `memory-retrieval` (≤ 2.500 tokens) con su
  motivo: un brief más largo degrada al subagente. Subirlo sería esconder el problema.
- **No es la tarea ni el contrato de retorno.** Son el contrato del subagente; recortarlos es lo que este
  repo ya graduó ALTA en `test_task_brief.py:190-192` («el brief salía SIN criterios»).

## 4. Opciones (para que `evaluator` presupueste y `planner` elija; aquí no se decide)

| # | Opción | Qué toca | A favor | En contra |
|---|---|---|---|---|
| O1 | **Presupuesto por sección**: `DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS`, `VERIFICACION_TOPE_CHARS`, cada uno con recorte alineado (`_recorte_seguro`, que ya existe) y aviso, calcando `MEMORIA_TOPE_CHARS` | `task-brief.py`, tests | es el camino que `GOT-008` ya señala («el tope de la sección, no la forma del comando»); maquinaria ya escrita; determinista | tres constantes nuevas que hay que medir y justificar, no inventar; el diseño recortado a ciegas puede perder justo lo que la tarea necesita |
| O2 | **Diseño bajo demanda**: inyectar `## Diseño` solo si la tarea lo referencia (campo `Archivos`/`Dependencias` toca módulos del §5 «Impacto» de `design.md`), y si no, un puntero de una línea | `task-brief.py`, `design.md` (estructura del §5), tests | ataca la causa: 3.510 × 22 = 77.000 caracteres inyectados cuando la mayoría de tareas no diseñan nada; token-diet real | acopla el brief a la estructura de `design.md`; el criterio «toca el diseño» hay que definirlo bien o se vuelve heurística |
| O3 | **Gaps solo de la tarea**: la tabla de revisión entra filtrada a las filas cuya columna `Tarea` es la propia, no la tabla entera de todos los intentos | `task-brief.py`, tests | T-01 pasaría de 4.396 a lo suyo; la tabla ya tiene la columna | no ataca el diseño, que es el bloque mayor |
| O4 | **Verificación sin evidencia**: el brief lleva el comando de la `Verificación`, nunca la salida pegada en el ledger | `task-brief.py`, tests | T-02 pasaría de 2.285 a ~200; hay un test que ya lo pretende (`:663`) y no lo consigue del todo | pequeño; solo una de las causas |
| O5 | **El guardarraíl deja de ser ciego**: el test del CA-08 recorre TODOS los `docs/roadmap/*/tasks.md` con `design.md` o sin él, no solo `memory-retrieval` | `test_task_brief.py` | barato; convierte el problema en visible para siempre; sin él, cualquiera de O1-O4 puede volver a romperse en silencio | hoy pondría la suite en rojo (8 briefs) hasta que O1-O4 entren: hay que secuenciarlo |

**Lo que el análisis sí recomienda como orden, no como decisión:** O5 al final pero planificado desde el
principio (es la puerta que impide la regresión), O2 + O3 como el grueso (atacan las dos secciones sin
tope que más pesan), O4 si sale barato, y O1 como red para lo que quede variable. Combinables.

## 5. Riesgos y límites honestos

- **Recortar diseño puede quitar justo lo que la tarea necesita.** Por eso O2 (bajo demanda) es mejor que
  O1 (recorte a ciegas) para esa sección; si se hace O1 sobre `## Diseño`, el recorte debe ser por
  subsecciones enteras, nunca por caracteres.
- **El presupuesto es de la máquina, no del repo** (`GOT-008`): la ruta absoluta y el corpus mueven las
  cifras ~250 caracteres. Cualquier tope nuevo se mide en la máquina de trabajo y se deja margen.
- **La suite roja como estado intermedio.** O5 solo puede entrar cuando O1-O4 hayan bajado los 8 briefs;
  antes, o se marca `xfail` con motivo y fecha, o se secuencia. Un `skip` sin fecha es la pieza muerta de
  siempre.
- **No mide si el subagente rinde mejor con briefs más cortos.** Eso lo asume la spec de
  `memory-retrieval`; esta iniciativa la respeta, no la demuestra.

## 6. Cómo se sabrá si ha funcionado

| Señal | Dónde |
|---|---|
| 0 de 22 briefs de `project-specialization` por encima del tope, medido con el mismo script de este análisis | `task-brief.py` sobre el ledger real |
| El test del CA-08 recorre todos los ledgers y está en verde | `test_task_brief.py` |
| `## Diseño` deja de ser una constante de 3.510 en todas las tareas | la misma medición, columna «diseño» |
| Ningún aviso de tope por stderr en el despacho de F2 de `project-specialization` | los briefs de T-04…T-22 |

## 7. Lo que este análisis NO trae

Ni plan, ni tareas, ni presupuesto. El paso mecánico siguiente es `/pm-cycle` sobre esta carpeta:
`evaluator` deriva la `spec.md` y presupuesta. Por tamaño (no es una estimación): es más pequeña que
`project-specialization`; toca un script, su suite y la estructura de `design.md`.

## Procedencia

Hallazgo de la **Lente B** del intento 2 de la revisión de dos lentes sobre F1 de
`project-specialization` (2026-09-09, gap B-3 y nota «Preexistente, NO de este diff»), que midió que 11 de
22 tareas del ledger ya pasaban de 10.000 sin persona. El orquestador cuantificó después la composición por
secciones (tabla del §1). La decisión de abrir iniciativa aparte en vez de absorberlo en F1 es del usuario
(opción B, 2026-09-09), tras agotarse el bucle acotado de 3 intentos con ese único gap sin converger:
**no convergía porque su causa no estaba en F1**.
