---
generacion:               # vía rápida MEDIDA (usage-meter) — SOLO la ventana de este artefacto;
                          # la de la spec la reporta spec.md (regla de no-solape: nada se cuenta dos veces)
  inicio: 2026-08-13T12:21:15Z
  fin: 2026-08-13T12:22:14Z
  fuente: medido
  tokens_reales: { entrada: 10, salida: 3793, cache_creacion: 20661, cache_lectura: 2273469 }
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.08
  duracion: 5m
  ratio_usado: 300000       # default no calibrado
---

# Checklist de Tareas — quick-implement (vía rápida: atajo en lenguaje natural a la vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-13 |
| **Plan** | n/a — **vía rápida** sobre [`spec.md`](spec.md) (sin evaluación/plan; ledger ligero + revisión de dos lentes) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Origen:** spec anotada en backlog el mismo día e implementada a petición del usuario. Estimación gruesa de la spec: ~1 h base. Nota de medición: dos ventanas sin solape — spec 2m (en `spec.md`) + implementación 5m (aquí); el total de la iniciativa (7m / 34k) es su suma, y así el «Coste de proceso» de la cartera no cuenta nada dos veces. El consumo de los subagentes de revisión puede no estar íntegro en la transcripción medida.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Atajo en lenguaje natural | 2 | 2 | 100% | 0 / 1,0h | 0,11 (medido, iniciativa) / 0,3h | 0 / 0,1h | 34k (medido, iniciativa) / 100k |
| **TOTAL** | **2** | **2** | **100%** | **0 / 1,0h** | **0,11 (medido, iniciativa) / 0,3h** | **0 / 0,1h** | **34k (medido, iniciativa) / 100k** |

---

## Fase 1 — Atajo en lenguaje natural

**Estado**: completado · **Estimado**: 1,0h · **Real**: — · **Coste est.**: ~52 € · **Tokens est.**: 100k

### T-01 — Skill `quick-implement` (puerta de entrada delgada)

- **Descripción**: `skills/quick-implement/SKILL.md` con `description` que captura las frases naturales de "cambio pequeño ya" **y sus negativos** (no usarla con incógnitas/multi-fichero/presupuesto, si el usuario ya escribió `/dev-cycle`, o si es trivial de una línea). Cuerpo en tres pasos: (1) **filtro de idoneidad obligatorio** con tabla señal→acción y la regla dura de no arrancar un ciclo con puertas desde un comentario de pasada; (2) ejecución de la vía rápida **canónica** resolviendo `commands/dev-cycle.md` con `find` (fuente única: si el método cambia allí, cambia aquí) y parada con aviso si no se encuentra; (3) cierre informando de qué puertas pasó y qué se omitió. Sin scripts nuevos y sin tocar `commands/dev-cycle.md`.
- **Estado**: completado
- **Tipo**: docs
- **Tiempo humano**: est. 0,7h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real — (la medida de esta vía rápida es por artefacto, no por tarea: 2m spec + 5m implementación)
- **Supervisión**: est. 0,07h · real —
- **Archivos**: `skills/quick-implement/SKILL.md`

**Criterios de aceptación**
- [x] Frontmatter con disparadores POSITIVOS y NEGATIVOS explícitos (mitigación del riesgo de secuestro de la spec)
- [x] Cero duplicación del método: el Paso 2 lista solo los NOMBRES de los hitos y remite a `$DEVCYCLE` para el cómo; si el fichero falta, avisa y para (no improvisa un método paralelo)
- [x] El filtro de idoneidad es el Paso 1 y cubre los 5 casos: adelante · incógnitas · quiere presupuesto · trivial · el usuario ya usó la barra
- [x] Las puertas (revisión de dos lentes + `qa-gate`) se conservan y solo se omiten a petición explícita
- [x] El puntero a las fases de `/dev-cycle` es correcto: `qa` va DENTRO de la Fase 3 y la Fase 4 (`documenter`) no es automática en vía rápida (defecto detectado por las dos lentes y corregido)
- [x] El `find` incluye `$PWD/commands`, así que al trabajar sobre el propio repo del plugin no gana la copia instalada (defecto de lente B)

### T-02 — Documentación, badges y cierre

- **Descripción**: fila en «Skills compartidas» de `docs/README.md` y su espejo `docs/en/README.md`, fila en la tabla de skills de `CLAUDE.md`, badge de skills **10 → 11** en ambos README (lo verifica mecánicamente `tests/test_readme_badges.py`), spec → `implementada`, fila del roadmap actualizada y entrada en los dos changelogs.
- **Estado**: completado
- **Tipo**: docs
- **Tiempo humano**: est. 0,3h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real — (incluido en la ventana de implementación)
- **Supervisión**: est. 0,03h · real —
- **Archivos**: `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `README.md`, `README.es.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-08-13-quick-implement/spec.md`

**Criterios de aceptación**
- [x] Regla bilingüe respetada: cada fila de doc tiene su espejo EN/ES en el mismo cambio
- [x] `tests/test_readme_badges.py` en verde con 11 skills reales (verificado sobre clon completo del repo, no sobre el checkout parcial del sandbox)
- [x] Lista de skills de los manifiestos (`plugin.json` + `marketplace.json`) y listas en prosa de los README actualizadas — el badge 11 no miente en ningún sitio (defecto de las dos lentes)
- [x] `docs/FLOWS.md` y su espejo EN reflejan el nuevo punto de entrada (obligación del Paso 4 de `plugin-dev`)
- [x] Linter del plugin sin errores nuevos y resto de suites en verde
