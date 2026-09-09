---
analisis: plugin-refactor
descripcion: >
  Revisión de código y refactor de TODO el plugin, pedido por el usuario tras tres rondas de corrección
  sobre `task-brief.py`. Se parte de una medición determinista (`code-health.py`, 2026-09-09, tests
  excluidos): 36 ficheros · 14.259 líneas · 7,6 % duplicado (273 bloques) · 105 funciones de más de 30
  líneas · 8 marcadores TODO (de los que 6 son falsos positivos del propio detector). El hallazgo que
  ordena todo lo demás: la MAYOR parte de la duplicación es DELIBERADA (scripts standalone que viajan
  sueltos, copias byte a byte guardadas por test) y no se puede refactorizar sin una decisión de
  arquitectura previa. Precede la spec: aquí no hay plan ni presupuesto.
estado: borrador
creado: 2026-09-09
fuente: "petición del usuario (2026-09-09): «una revisión de código y refactorizar… de todo el plugin, no solo de task-brief.py»"
relacionado: docs/roadmap/2026-09-09-project-specialization/tasks.md (las tres rondas de corrección que motivan el refactor) · docs/roadmap/2026-09-09-brief-budget/analysis.md (toca el mismo script; hay que ordenarlas) · docs/roadmap/2026-08-10-token-diet/ (precedente de dieta medida)
linea_base: code-health-baseline.json (mismo directorio; se compara con `code-health.py . --exclude-tests --json --baseline <este fichero>`)
---

# Refactor del plugin — primero medir, luego decidir qué duplicación es deuda y cuál es diseño

## El resumen en una frase

**El plugin tiene deuda real —105 funciones largas y `main()` de 90-155 líneas en los ficheros que más
cambian—, pero su duplicación más visible no es deuda: es la consecuencia deliberada de que cada script
viaje suelto, y está guardada por tests que comparan las copias byte a byte.** Un refactor «de todo» que
no distinga las dos cosas rompería la portabilidad que el plugin acaba de construir (interop con Codex y
OpenCode, `export-skills.py`) para ganar un porcentaje en un informe.

## 1. La medición (línea base, 2026-09-09)

`python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 15`, 1,8 s. El JSON
completo está en [`code-health-baseline.json`](code-health-baseline.json) y el informe legible en
[`code-health-baseline.md`](code-health-baseline.md). **Ese JSON es la línea base**: toda tarea del
refactor se acepta comparando contra él con `--baseline`, no por impresión.

| Métrica | Valor | Lectura honesta |
|---|---|---|
| Ficheros / líneas de código | 36 / 14.259 | sin tests; ~la mitad en `agent-kits/shared/` |
| Duplicado | **7,6 %** (273 bloques entre ficheros distintos) | ver §2: la mayor parte es por diseño |
| Funciones > 30 líneas | **105** | aquí está la deuda de verdad (§3) |
| Anidamiento máximo | 6 | puntual, no sistémico |
| TODO/FIXME | 8 | **6 son falsos positivos** del propio detector (§4) |
| Hotspots (90 días) | 36 ficheros cambiados | los 5 primeros concentran el riesgo (§3) |

## 2. Duplicación: tres clases, y solo una es refactorizable sin decisión previa

| Clase | Ejemplo (líneas duplicadas) | Qué es | ¿Refactorizable? |
|---|---|---|---|
| **Generado** | `hooks/opencode-plugin.js` ↔ `interop/opencode/plugins/custom-agents-hooks.js` (**118**) | `interop/` lo escribe `export-interop.py` copiando el adaptador; `--check` vigila que no diverjan | **No es duplicación**: es la salida de un generador. Lo que toca es **excluir `interop/`** del informe de `code-health` (hoy no se puede: el script no tiene `--exclude` por ruta) |
| **Deliberada y guardada por test** | `celdas_md` y compañía en `doctor.py:647` ↔ `lint_plugin.py:549` ↔ `knowledge-find.py:247` (**93 + 17 + 17**); `sin_vallas` en `ledger-lint.py:103/142` ↔ `changelog-sync.py:123/310` (**21 + 19**, «réplica del criterio de `ledger-lint.py`»); el `import` de `confluence-scope.glob_to_regex` con copia local de respaldo en `scope-check.py:51` ↔ `review-lens-select.py:104` (**25 + 13**) | El comentario en el propio código lo dice: «los scripts son standalone: el paquete portable los copia sueltos, sin import común; `tests/test_knowledge_index.py` compara las copias byte a byte». Cada skill viaja entera a Codex/OpenCode sin traducir; un `import` cruzado entre `agent-kits/shared/` y `skills/*/scripts/` rompe en cuanto una pieza se instala sola | **Solo con una decisión de arquitectura** (§5). Hoy la duplicación ES el mecanismo de portabilidad, y los tests que la comparan son su guardarraíl |
| **Accidental** | `evals/check.py:110` ↔ `lint_plugin.py:906` (15, la lectura de piezas); `task-brief.py:581` ↔ `jira-flow.py:249` (13); `export-skills.py:36` ↔ `jira-flow.py:83` (13); `code-health.py:27` ↔ `deps-inventory.py:29` (13); y el bloque de **reconfiguración de `stdout`/`stderr` a UTF-8** (`GOT-005`) repetido en `doctor.py:56` ↔ `guardrail-check.py:49` ↔ `build_dashboard.py:14` ↔ `evals/run.py:55` (12 cada uno) | Código que nació igual en sitios distintos sin que nadie decidiera duplicarlo | **Sí**, pero con la MISMA restricción de portabilidad: la solución no es un módulo común importado (rompe el standalone), sino decidir explícitamente si estas copias se **declaran** (y se guardan con el mismo test byte a byte que las deliberadas) o se **eliminan** porque una de las dos piezas no lo necesita |

**Conclusión del §2:** el 7,6 % no baja significativamente sin resolver la decisión del §5. Perseguir el
porcentaje antes de decidir es trabajo perdido o, peor, una regresión de portabilidad disfrazada de mejora.

## 3. La deuda real: funciones largas en los ficheros que más cambian

Las funciones de más de 30 líneas son 105. Las 15 mayores:

| Líneas | Función | Fichero | ¿Hotspot? |
|---|---|---|---|
| **155** | `main()` | `agent-kits/shared/task-brief.py:640` | sí (7 cambios / 685 líneas) — y acaba de absorber tres rondas de corrección |
| 122 | `construir_plan()` | `skills/jira-sync/scripts/jira-flow.py:523` | no |
| 120 | `parse_ledger()` | `agent-kits/shared/ledger-lint.py:209` | sí (6 / 381) |
| 114 | `lint()` | `scripts/lint_plugin.py:397` | sí (7 / 969) |
| 113 | `RAICES` | `hooks/opencode-plugin.js:48` | no (y su copia en `interop/` es generada) |
| 108 | `declaradas()` | `skills/dependency-upgrade/scripts/deps-inventory.py:115` | no |
| 102 | `do_release()` | `scripts/release.py:419` | sí (6 / 454) |
| 98 | `check()` | `evals/check.py:148` | no |
| 93 | `render_html()` | `skills/roadmap-dashboard/scripts/build_dashboard.py:372` | sí (9 / 613) |
| 91 | `main()` | `skills/changelog-sync/scripts/changelog-sync.py:832` | no |
| 87 | `main()` | `agent-kits/qa/coverage-check.py:70` | no |
| 87 | `bloque_plugin()` | `agent-kits/shared/doctor.py:252` | sí (8 / 942) |
| 87 | `main()` | `agent-kits/shared/knowledge-find.py:932` | **sí, el primero** (9 / 852) |
| 85 | `scan()` | `skills/roadmap-dashboard/scripts/build_dashboard.py:228` | sí |

**Hotspots** (grandes Y que cambian mucho, 90 días): `knowledge-find.py` (87,6), `build_dashboard.py`
(83,4), `doctor.py` (79,0), `lint_plugin.py` (69,5), `task-brief.py` (66,0), `release.py`,
`ledger-lint.py`, `journal.py`. **Aquí es donde un refactor paga**: una función de 155 líneas en un
fichero que cambia cada semana es donde entran los defectos de los próximos meses.

El caso más concreto, y el que motivó este análisis: `task-brief.py` tiene hoy **cuatro reglas para una
sola sección** (`PERSONA_TOPE_CHARS = 4000` «cap de sanidad», `PERSONA_SUELO_CHARS = 1300`,
`PERSONA_TOPE_MINIMO_UTIL = 200`, más el margen dinámico), acumuladas en tres rondas de corrección en
un día. Es la cicatriz típica de corregir bajo revisión; y su `main()` monta siete secciones en línea.

## 4. Los TODO: el detector se detecta a sí mismo

De los 8 marcadores, **6 son falsos positivos**: cinco están en el propio `code-health.py` (su docstring
y su código hablan de «TODO/FIXME/HACK» para describir lo que busca), y uno en
`confluence-scope.py:113` es la palabra castellana «todo» en mayúsculas dentro de prosa («siguen
escribiendo TODO (ADRs, …»), que la regla «palabra seguida de `(`» acepta. `journal.py:41` es otra
descripción de patrón. **Queda un TODO real**: `usage-meter.py:380` («el histórico como ventana →
degradar con aviso, no mentir»), 29 días. Esto es un defecto pequeño del detector con arreglo barato
(excluir comentarios que enumeran marcadores; exigir mayúsculas Y que el fichero no sea el propio
detector) y una tarea del refactor.

## 5. La decisión que hay que tomar ANTES de refactorizar (para `architect`)

**¿Cómo comparten código los scripts de un plugin cuyas piezas viajan sueltas?**

| Opción | Qué es | A favor | En contra |
|---|---|---|---|
| **O1 — Copias declaradas** (statu quo formalizado) | Cada copia se registra en una lista (`shared-copies.json` o similar) y UN test compara todas byte a byte; hoy solo `test_knowledge_index.py` compara tres | cero riesgo de portabilidad; el mecanismo ya existe; convierte lo accidental en deliberado | el % de duplicado no baja; cada arreglo en una copia obliga a tocarlas todas (el test lo recuerda, no lo evita) |
| **O2 — Módulo común vendorizado** | Un `_comun.py` fuente de verdad, que `export-skills.py`/`export-interop.py` **copian dentro de cada pieza** al empaquetar (la pieza sigue siendo standalone en destino) | la duplicación existe solo en el paquete generado, no en el repo; un arreglo, un sitio | añade un paso de generación más y `--check`; los scripts en el árbol de trabajo tendrían que resolver el módulo con la misma regla `find` de seis raíces que ya usan para todo lo demás |
| **O3 — Módulo común importado** | `agent-kits/shared/_comun.py` importado por ruta relativa | lo más simple en el repo | **rompe el standalone**: una skill instalada sola en Codex/OpenCode no tiene `agent-kits/shared/` al lado. Choca con el requisito multi-runtime del usuario y con `docs/INTEROP.md` |

Este análisis **recomienda descartar O3** y llevar O1 vs O2 a `architect`. Lo que se elija condiciona
qué parte del 7,6 % es alcanzable.

## 6. Cómo se haría el refactor (método, no plan)

1. **La línea base manda.** Cada tarea termina con `code-health.py . --exclude-tests --json --baseline
   docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline.json` y el veredicto de «mejora / empeora»
   entra en la `Verificación` del ledger. Sin cifra, no hay tarea cerrada.
2. **Contratos congelados.** Nada de esto cambia: flags de CLI, exit codes (patrón `worklog`/`qa-gate`/
   `ledger-lint`), formas de `--json` (el de `knowledge-find.py` lo consumen `task-brief.py` y
   `session-context.sh`; el de `scope-check.py` lo consume la revisión), nombres de secciones del brief, la
   regex canónica `REVISION_HDR_PATTERN` compartida con `jira-flow.py`. Refactor = misma suite en verde
   antes y después, **sin tests nuevos que legitimen comportamiento nuevo**.
3. **Un hotspot por tarea, empezando por el que más cambia** (`knowledge-find.py`) y por el que acaba de
   sufrir (`task-brief.py`: fundir las cuatro reglas de la persona en una función con nombre y partir
   `main()` en las siete secciones que ya tiene).
4. **Las copias deliberadas no se tocan hasta la decisión del §5.** Si se elige O1, la tarea es registrar y
   comparar; si O2, la tarea es el generador y su `--check`.
5. **`export-interop.py --check` y `test_knowledge_index` (comparación de copias) son puertas** de cada
   tarea, igual que el linter. Y `release.py --dry-run` al cerrar.
6. **Revisión de dos lentes por tramo**, no por tarea: un refactor sin cambio de comportamiento es
   exactamente el diff en que la Lente A tiene poco que decir y la Lente B mucho (regresiones probables).

## 7. Lo que NO es este refactor

- **No toca prosa** (`agents/*.md`, `commands/*.md`, `skills/*/SKILL.md`): eso es `plugin-dev` y tiene
  sus propias reglas (≤ 200 líneas, `--diet-check`).
- **No cambia comportamiento**: ni una feature, ni un flag, ni un exit code. Lo que parezca defecto durante
  el refactor se anota y va por su cauce (`quick-implement` o iniciativa), no se cuela.
- **No arregla `brief-budget`** (composición del brief): esa iniciativa toca el mismo `task-brief.py` y hay
  que **ordenarlas**: refactor primero (partir `main()`), presupuesto por secciones después sobre código
  limpio. Al revés se refactoriza dos veces.
- **No persigue el 7,6 %** como objetivo: el objetivo son las funciones largas en hotspots y las copias
  accidentales convertidas en deliberadas o eliminadas.

## 8. Cómo se sabrá si ha funcionado

| Señal | Medida |
|---|---|
| Funciones > 30 líneas en los 5 hotspots principales | de las que hay hoy (baseline) a **la mitad**, sin ninguna nueva > 60 |
| Duplicación accidental (clase 3 del §2) | **0 bloques** sin declarar: o registrados y comparados, o eliminados |
| Falsos positivos de TODO | 8 → 1 (el real de `usage-meter.py`) |
| Suites, linter, evals, `export-interop --check`, `release.py --dry-run` | idénticos en verde antes y después |
| `code-health --baseline` | «mejora» en cada tarea cerrada; nunca «empeora» |

## 9. Lo que este análisis NO trae

Ni plan, ni tareas, ni presupuesto: `/pm-cycle` sobre esta carpeta (`evaluator`), con el paso de
`architect` para el §5 **recomendado, no opcional**. Orden sugerido respecto a las otras dos iniciativas
abiertas hoy: cerrar F1 de `project-specialization` → este refactor → `brief-budget` → F2 de
`project-specialization`.

## Procedencia

Petición del usuario del 2026-09-09 tras la tercera ronda de corrección sobre `task-brief.py`
(«una revisión de código y refactorizar… de todo el plugin»). Medición con la skill `code-health` del
propio plugin, que **no refactoriza** por diseño: este documento respeta esa frontera. La lectura de qué
duplicación es deliberada sale de los comentarios del propio código (`doctor.py:645-646`,
`changelog-sync.py:121-122`) y de `tests/test_knowledge_index.py`, no de una suposición.
