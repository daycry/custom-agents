---
generacion:               # usage-meter.py NO disponible en este entorno (sandbox cloud, sin transcripción local)
  inicio: 2026-08-20T07:28:00Z
  fin: 2026-08-20T07:40:00Z
  fuente: estimado        # degradación declarada: no hay medición de tokens
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# 2026-08-20-confluence-policy

> Política de publicación en Confluence — cuánto cuesta decidir y aplicar qué documentación de `docs/` se espeja y qué no, y cerrar los cinco huecos del circuito antes del primer `enabled: true`.

| | |
|---|---|
| **Fecha** | 2026-08-20 |
| **Estado** | completado |
| **Prioridad global** | Media |
| **Solicitante** | daycry (vía `/pm-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **Características evaluadas** | 5 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **21,6 h** (18 h base +20 %) | Baja |
| Tiempo IA (ejecución) | **0,89 h** (+ 0,22 h supervisión) | Media |
| Coste | **≈ 1.085 €** | Baja |
| Tokens IA | **426k** con margen — 355k base (in 307k / out 48k) | Media |
| Multiplicador productividad | **×19** | — |
| Características | **5** (todas comprometidas) | — |

> **Ajustado en puerta go (2026-08-20):** D4 = excluir `**/testing/**` en vez de transformar el `report.md`. C-03 bajó de 2,5 h/125 € a **0,5 h/25 €**.
>
> **Ajustado post-go (2026-08-20): D5 = sí, C-05 ampliado con staging generado.** El verificador pasa a incluir `--status` y `--stage` (regenera `docs/confluence/` como carpeta derivada) y **deja de ser opcional**: 5,5 h → **7,5 h** (100k tokens). Totales, comparativa, presupuesto y productividad recalculados. Recorrido de las cifras: 18 h base → 16 h (puerta go) → **18 h** (post-go); ≈ 1.085 € → ≈ 965 € → **≈ 1.085 €**. Coincidencia, no error: lo que D4 ahorró (2 h) es lo que D5 añade (2 h).

> **Por qué la confianza del coste es Baja:** el 99,6 % del importe son horas **humanas**, y `CALIBRATION.md` (aprendizaje nº 2) deja constancia de que en este proyecto **las horas humanas nunca se han validado**: las 5 iniciativas medidas tienen 0 h humanas reales. La cifra sirve para comparar características entre sí y para justificar valor, no para comprometer una factura.

---

## Resumen ejecutivo

El circuito `docs/ ↔ Confluence` está completo en mecánica pero **vacío de política**: el `include: ["**/*.md"]` por defecto subiría el árbol EN duplicado, los ejemplos, la doc interna de agentes y las 11 iniciativas completas del roadmap; cuatro disparadores de fin de ciclo (`/retro`, `/spec-drift`, `/roadmap-brief`, y el ledger de `implementer`) no publican nunca; y el `report.md` de `qa` llegaría a Confluence con las capturas rotas, sin arreglo posible con el conector actual. Se presupuestan **5 características** por **18 h base (21,6 h con margen) ≈ 1.085 €** y **355k tokens**: cuatro de prosa normativa y una —comprometida tras D5— con script, tests y una carpeta `docs/confluence/` **generada** que hace visible de un vistazo qué se publica. El trabajo es barato y **preventivo** — hoy no duele porque el circuito nunca se ha activado (no existen `confluence.json` ni `confluence-state.json`), y ese es exactamente el momento de decidir. **Veredicto: go, sin condiciones pendientes** — el usuario cerró las cinco decisiones de producto (D1 selección curada · D2 sin presets · D3 ledger por fase · D4 `testing/` fuera · **D5 verificador + staging generado, dentro**), todas recogidas en la spec (`aprobada`). Nada queda para la puerta del plan.

---

## Requerimientos recibidos

Mapa del análisis de origen a las características evaluadas. El origen es el **análisis previo del circuito (2026-08-20)**, recogido y verificado en la spec.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Política de alcance del mirror (`include`/`exclude`) | spec §Contexto hueco 1 · §Configuración/parámetros | ✅ claro (D1 y D2 cerradas) |
| C-02 | Disparadores que faltan (fin de ciclo + ledger) | spec §Contexto hueco 2 · §Arquitectura (comandos, implementer) | ✅ claro (D3 cerrada) |
| C-03 | Evidencias binarias de qa (capturas rotas) | spec §Contexto hueco 3 · §Decisiones de diseño | ✅ claro (D4 cerrada: excluir) |
| C-04 | Documentar la política (SKILL + espejo EN + matriz en FLOWS) | spec §Alcance · CA-02, CA-05 | ✅ claro |
| C-05 | Verificador + staging generado `confluence-scope.py` (`--status` / `--stage` / `--check`) | spec §Decisiones de diseño (D5) · CA-07, CA-08, CA-10, CA-11, CA-12 | ✅ claro (D5 cerrada: entra, ampliado) |

**Decisiones cerradas en la puerta go (2026-08-20) y su efecto en el presupuesto:**

- **D1 — Alcance = selección curada.** Suben doc general, ficheros de cartera y `spec.md`/`evaluation.md`/`retro.md` por iniciativa; no suben planes, `tasks.md` ni `test-plan.md`. **Sin cambio de horas en C-01**: se cambia una lista de globs por otra algo más fina (patrones por nombre de fichero dentro de `docs/roadmap/`).
- **D2 — Sin presets de audiencia.** **−1 h en C-01** (era la parte del preset).
- **D3 — Ledger: publicar al cerrar fase.** Era ya el supuesto usado para estimar C-02: **sin cambio**.
- **D4 — `**/testing/**` no se publica.** Se descarta la transformación del `report.md`: **C-03 pasa de 2,5 h/125 € a 0,5 h/25 €** y desaparece el riesgo de divergencia publish/pull.
- **Neto:** C-01 se mantiene en **4 h** — la hora que libera D2 se consume en la selección curada de D1 (exclusiones por nombre de fichero dentro del roadmap, más su justificación y su reflejo en la doc); el ahorro real del lote viene de D4. Total: **18 h → 16 h base**.

- **D5 — Determinismo y visibilidad: entra, ampliado (post-go).** El verificador se convierte en verificador + **staging generado**: `--status` (informe de alcance y estado de sincronización) y `--stage` (regenera `docs/confluence/`, copia exacta de lo que sube, no editable a mano). Motivación registrada en la spec: el usuario quería ver a simple vista qué se publica y se descartó la carpeta mantenida a mano por ser una segunda fuente de verdad. **+2 h en C-05 (5,5 → 7,5 h) y +30k tokens**; C-05 deja de ser opcional.

**Sigue abierto:**

- **No verificable aquí:** las herramientas reales expuestas por el conector Rovo MCP en el entorno del usuario (el supuesto "no hay adjuntos" viene del análisis previo y de la propia skill, no de una comprobación en vivo). Si el conector expusiera adjuntos, C-03 cambia de naturaleza.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — *D1-D4 cerradas en la puerta go y D5 cerrada en la iteración post-go (2026-08-20); no queda ninguna decisión abierta*
- [x] **Alcance** de cada característica acotado (qué entra y qué NO) — spec §Alcance
- [x] **Criterios de aceptación / éxito** por característica — CA-01 … CA-09
- [x] **Restricciones** (deadline, presupuesto, compliance, técnicas) — reglas del repo: determinismo, bilingüe EN/ES, degradación sin bloqueo, linter en verde, invariante `docs/security-scan/**`
- [ ] **Dependencias externas** (equipos, proveedores, APIs) identificadas — *falta confirmar espacio de Confluence, quién lo administra y las capacidades reales del conector*
- [x] **Contexto técnico** del proyecto (stack, integraciones) disponible — repo explorado; rutas y líneas citadas en la spec
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, precios verificados el 2026-08-18

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Fuente de los parámetros: `.claude/rates.json` (fuente única compartida con `planner` y `jira-sync`).

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `rates.json:tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json:modeloIA` |
| Precio input | 5,00 USD / 1M tokens → **4,60 € / 1M** | Verificado el 2026-08-18 con `rates-verify` (2 días: fiable, < 90 días) |
| Precio output | 25,00 USD / 1M tokens → **23,00 € / 1M** | Ídem |
| Precio escritura de caché | 6,25 USD / 1M tokens | Ídem; entra en "tokens facturables" |
| Precio lectura de caché | 0,50 USD / 1M tokens | Ídem; **no** cuenta para horas, **sí** para € (aprendizaje nº 4 de `CALIBRATION.md`) |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ **verificar** — `rates.json` lo declara supuesto fijo, no dato verificado |
| Ratio tokens→hora-IA | **479.326 tok/h** | Mediana medida de `CALIBRATION.md` (5 muestras), con precedencia sobre el default no calibrado de 300.000 |
| Ratio de supervisión | 25 % de las horas IA | `rates.json:ratioSupervision` |
| Margen de contingencia | 20 % | `rates.json:margenContingencia`; sobre horas base (humanas e IA) y sobre los tokens |
| Lectura de caché prevista | ~3M tokens | ⚠️ **supuesto** por analogía con el histórico (millones de tokens de lectura y la mayor parte de los 12,35 € de las 5 iniciativas medidas) |

**Método de estimación aplicado (y de dónde sale):**

- **Horas humanas**: descomposición por fichero afectado (ficheros y líneas identificados en la spec §Arquitectura), tarificando decisión + edición + revisión humana. Punto medio realista, sin colchón.
- **Tokens**: previsión por característica según ficheros a leer y a escribir, **calibrada a la baja** con `CALIBRATION.md`: las 5 iniciativas medidas se desviaron entre −66 % y −97 % respecto a estimaciones hechas por analogía con "iniciativas con código". Aprendizaje nº 5 aplicado: esto es **prosa** (minutos), salvo C-05 que es **prosa + tests** (×2).
- **Horas IA**: `tokens facturables ÷ 479.326` (ratio calibrado), no "a juicio" — aprendizaje nº 1 de la primera calibración.
- **Líneas propias** para el **coste de proceso** (spec + evaluación + plan) y para la **revisión adversarial de dos lentes** (aprendizajes nº 2 y nº 3: es donde se fue el esfuerzo real en las 4 vías rápidas, con 1-10 hallazgos por iniciativa).

---

## Evaluación por característica

### C-01 — Política de alcance del mirror (`include`/`exclude` + presets)

- **Requisito origen**: spec §Contexto (hueco 1) y §Configuración / parámetros.
- **Descripción**: definir y documentar qué se espeja por defecto. Se mantiene `include: ["**/*.md"]` y la política se expresa como `exclude` (opt-out): fuera `docs/en/**` (árbol EN duplicado), `docs/examples/**`, `docs/agents/**` (doc interna del plugin), `atlassian-connector-notes.md` y —por **D1**— `improvement-plan.md`, `tasks.md` y `test-plan.md` de cada iniciativa; se conservan las exclusiones no negociables (`security-scan`, `dashboard.html`). **Sin presets** (D2).
- **Complejidad**: Media — el cambio de fichero es pequeño; lo caro es acertar con la regla y que sea válida para cualquier proyecto consumidor, no solo para este repo.
- **Esfuerzo**: 4 h · confianza Media — **sin cambio tras la puerta**: −1 h por descartar los presets (D2) y +1 h por la selección curada de D1, que exige exclusiones por **nombre de fichero** dentro de `docs/roadmap/` (más finas y más fáciles de romper que una exclusión por carpeta) y su justificación documentada
- **Previsión IA**: 35k in / 5k out tok · ≈ 0,29 € · ~0,08 h-IA
- **Coste**: (4 h × 50 €/h) + 0,29 € = **≈ 200 €**
- **Impacto / áreas afectadas**: `skills/confluence-publish/assets/confluence.example.json`, `skills/confluence-publish/SKILL.md` (§Config, §Modo sincronización), `skills/confluence-pull/SKILL.md` (simetría del filtro)
- **Dependencias y prerequisitos**: ninguna — D1 y D2 están cerradas. Es prerequisito de C-04 (documenta lo aquí decidido), de C-03 (la exclusión de `testing/` es una línea de esta misma lista) y de C-05.
- **Riesgos**: una exclusión de más deja al PM sin doc que esperaba ver y no hay señal de ello (el fichero simplemente no aparece); una de menos vuelca doc interna a un espacio compartido, y el conector **no borra páginas** (solo marca obsoleto + aviso manual), así que revertir cuesta trabajo manual.
- **Incógnitas / preguntas abiertas**: ninguna bloqueante. Menores, resueltas por defecto en la spec: `confluence-pull` aplica el mismo filtro (simetría) y las configs existentes se **avisan**, no se migran solas. Queda como observación: `CALIBRATION.md` y `DRIFT.md` se publican por lectura literal de D1 (no estaban entre las exclusiones acordadas); si resultan ruidosos, quitarlos cuesta una línea.

### C-02 — Disparadores que faltan (fin de ciclo + ledger)

- **Requisito origen**: spec §Contexto (hueco 2) y §Arquitectura (comandos + `implementer`).
- **Descripción**: que `/retro`, `/spec-drift` y `/roadmap-brief` apliquen el paso compartido `confluence-optin.md` en su cierre, como el resto de la cadena, y que `implementer` lo aplique **al cerrar cada fase** (D3). Son artefactos de **fin de ciclo**: como nadie publica después, el arrastre por manifiesto nunca los recoge y hoy no existen en Confluence.
- **Complejidad**: Baja — el paso ya está escrito en el fragmento compartido; es una línea por comando con el mismo texto de degradación. La única parte no mecánica es la decisión del ledger.
- **Esfuerzo**: 3 h · confianza Media
- **Previsión IA**: 31k in / 4k out tok · ≈ 0,25 € · ~0,07 h-IA
- **Coste**: (3 h × 50 €/h) + 0,25 € = **≈ 150 €**
- **Impacto / áreas afectadas**: `commands/retro.md`, `commands/spec-drift.md`, `commands/roadmap-brief.md`, `agents/implementer.md`; indirectamente `skills/jira-sync` (escribe claves en `tasks.md` y queda cubierto por la decisión de ledger)
- **Dependencias y prerequisitos**: ninguna bloqueante (D3 cerrada). Conviene después de C-01 para que el texto del disparo de `implementer` ya pueda citar la política.
- **Riesgos**: **la combinación D1 + D3 desconcierta si no se documenta** — `implementer` dispara al cerrar fase pero `tasks.md` está fuera del espejo, así que el disparo refresca `dashboard.md` y poco más; sin una frase explícita, alguien buscará en Confluence un ledger que nunca sube (mitigado en C-04, CA-04/CA-05). `brief.pdf` y `report.pdf` seguirán sin subir en cualquier caso (no son `.md`).
- **Incógnitas / preguntas abiertas**: ninguna bloqueante. Menor: `CALIBRATION.md` y `DRIFT.md` quedan dentro del espejo por lectura literal de D1 — revisable tras el primer espejo real.

### C-03 — Evidencias binarias de qa (capturas rotas)

- **Requisito origen**: spec §Contexto (hueco 3) y §Decisiones de diseño.
- **Descripción**: el `report.md` de `qa` embebe capturas de `screenshots/`, que el filtro `**/*.md` no sube y el conector no permite adjuntar; la página saldría con imágenes rotas. **D4 (cerrada): `**/testing/**` no se publica.** Se descarta transformar el markdown publicado. El trabajo se reduce a una exclusión en la política + una frase en `agents/qa.md` (informe solo-local) + su reflejo en la doc.
- **Complejidad**: Baja *(era Media con la opción de transformar)* — una línea de `exclude` y dos notas; sin contrato nuevo.
- **Esfuerzo**: **0,5 h** · confianza Alta *(antes 2,5 h con confianza Baja; ajustado en puerta go: D4 = excluir)*
- **Previsión IA**: 13k in / 2k out tok · ≈ 0,11 € · ~0,03 h-IA
- **Coste**: (0,5 h × 50 €/h) + 0,11 € = **≈ 25 €**
- **Impacto / áreas afectadas**: `skills/confluence-publish/assets/confluence.example.json` (una línea), `skills/confluence-publish/SKILL.md` (nota), `agents/qa.md` L26/L73/L77
- **Dependencias y prerequisitos**: se materializa dentro de la política de C-01 — **misma fase**.
- **Riesgos**: bajos. Un stakeholder puede echar en falta el informe de QA en Confluence y no saber que existe en el repo → mitigado haciendo la ausencia explícita en la matriz de FLOWS (C-04, CA-05). **Riesgo eliminado por D4:** la divergencia local↔remoto que habría roto la simetría con `confluence-pull` (el pull podía sobrescribir el `report.md` local sin capturas) ya no existe.
- **Incógnitas / preguntas abiertas**: ninguna bloqueante. Queda asumido que `report.pdf` y las capturas siguen siendo solo-local; si en el futuro el conector expusiera adjuntos, esta decisión se puede revisar sin coste hundido (se cambió una línea de config).

### C-04 — Documentar la política (SKILL + espejo EN + matriz de disparadores)

- **Requisito origen**: spec §Alcance; criterios CA-02 y CA-05.
- **Descripción**: sección normativa "qué sube y qué no" en la doc de la skill, matriz **disparador → artefacto → ¿se publica?** en `docs/FLOWS.md` cubriendo los 10 disparadores conocidos —con los "no" explícitos (plan, `tasks.md`, `testing/**`, `docs/en/`, `examples/`, `agents/`) y la nota de la interacción D1 ↔ D3—, actualización del párrafo de `docs/README.md` L39 y **espejo EN en el mismo cambio** (regla bilingüe del repo), conservando en español los tokens que parsean las máquinas.
- **Complejidad**: Baja — es prosa, pero por duplicado (ES + EN) y en tres ficheros.
- **Esfuerzo**: 3 h · confianza Alta (es el trabajo más predecible del lote: volumen conocido, sin decisiones)
- **Previsión IA**: 39k in / 6k out tok · ≈ 0,33 € · ~0,09 h-IA
- **Coste**: (3 h × 50 €/h) + 0,33 € = **≈ 150 €**
- **Impacto / áreas afectadas**: `docs/FLOWS.md`, `docs/README.md`, `docs/en/FLOWS.md`, `docs/en/README.md`, `skills/confluence-publish/SKILL.md`
- **Dependencias y prerequisitos**: **depende de C-01, C-02, C-03 y ahora también de C-05** — documenta lo que decidan, incluido el contrato de `docs/confluence/`. Hacerla antes obliga a reescribir el espejo EN dos veces.
- **Riesgos**: olvidar el espejo EN rompe la regla bilingüe y lo detecta el linter tarde; la matriz de disparadores envejece en cuanto se añada un agente que escriba en `docs/` — riesgo **mitigado tras D5**, porque `--status` da la foto real del alcance y la matriz deja de ser la única fuente. Nuevo alcance documental: la carpeta generada y su regla de no-edición.
- **Incógnitas / preguntas abiertas**: ¿la matriz vive en `docs/FLOWS.md` (visual, según CLAUDE.md) o en la propia skill? Se propone FLOWS con enlace desde la skill, para no duplicar la fuente.

### C-05 — Verificador + staging generado `confluence-scope.py` (comprometido)

- **Requisito origen**: spec §Decisiones de diseño (D5, determinismo y visibilidad); criterios CA-07, CA-08, CA-10, CA-11, CA-12.
- **Descripción**: script con tests y exit codes, con **dos funciones**: `--status`, informe humano que cruza política + `confluence-state.json` y clasifica cada documento en *en alcance / sincronizado / desactualizado o pendiente / excluido*; y `--stage`, que **regenera `docs/confluence/`** como copia exacta de lo que sube (+ `README.md` de aviso), pasando `publish.source` a esa carpeta. Más `--check` de invariantes (exit ≠ 0 si `docs/security-scan/**` no está excluido). Responde a la petición del usuario de **ver a simple vista qué sube**, sin la segunda fuente de verdad que supondría mantener la carpeta a mano.
- **Complejidad**: Alta — la única pieza con código, tests y fixtures; replica la semántica de glob, escribe un árbol derivado idempotente, y **cambia el contrato de tres piezas existentes**: manifiesto y hook pasan a operar sobre el staging, y `confluence-pull` necesita el mapeo inverso staged → canónico.
- **Esfuerzo**: **7,5 h** · confianza Baja (rango 6-9 h) — *reestimado post-go desde 5,5 h*. Elijo el **alto** del rango indicado (7,5 h y no 6,5 h) por tres motivos concretos: (1) son **dos funciones** con salidas distintas, no una — `--status` necesita además leer y clasificar contra el manifiesto; (2) `--stage` es un **generador de árbol** y hay que probar su **idempotencia** y que ningún excluido se cuele, lo que multiplica fixtures; (3) el **mapeo inverso para `confluence-pull`** es un contrato nuevo entre dos skills, exactamente el tipo de acoplamiento donde el histórico dice que se va el esfuerzo (aprendizaje nº 3: la revisión encontró 1-10 hallazgos por iniciativa, y dos habrían roto una garantía del producto). Con 6,5 h habría que recortar tests, que es justo lo que la regla de determinismo del repo pide no hacer.
- **Previsión IA**: 85k in / 15k out tok · ≈ 0,77 € · ~0,21 h-IA *(aprendizaje nº 4 de `CALIBRATION.md`: con tests, ×2 sobre una tarea de prosa; aquí ×2,5 por las dos funciones y el contrato cruzado)*
- **Coste**: (7,5 h × 50 €/h) + 0,77 € = **≈ 375 €**
- **Impacto / áreas afectadas**: `skills/confluence-publish/scripts/confluence-scope.py` (nuevo), `docs/confluence/` (nueva, generada), `tests/` (nueva suite), `skills/confluence-publish/SKILL.md` y `assets/confluence.example.json` (`source` + `staging`), `skills/confluence-pull/SKILL.md` (mapeo inverso), `hooks/mark-docs-pending.sh` (ignorar la carpeta staged), `scripts/lint_plugin.py` (enganche opcional)
- **Dependencias y prerequisitos**: **depende de C-01** (no se puede materializar una política que no existe). Ya **no es prescindible**: entra en el alcance comprometido (D5).
- **Riesgos**: (a) la semántica de glob del script puede divergir de la que aplique el agente al publicar — un verificador que miente es peor que no tenerlo; se mitiga declarando el script **fuente de verdad** del alcance y haciendo que la skill lo invoque en vez de reinterpretar patrones; (b) **bucle de regeneración**: si el hook no ignora `docs/confluence/**`, cada `--stage` marca "pendiente" y dispara otro ciclo (CA-12 lo cubre); (c) **pérdida de ediciones** si alguien toca la carpeta generada (mitigado con el `README.md` de aviso y el chivato de `--status`); (d) `confluence-pull` escribiendo en la copia staged perdería el cambio al regenerar (CA-11); (e) coste: es la estimación más volátil del lote (6-9 h, ±20 %).
- **Incógnitas / preguntas abiertas**: menores, no bloqueantes. ¿La skill **invoca** el script (más determinista, más acoplamiento) o basta como verificación de CI? Se propone invocarlo, coherente con el patrón `roadmap-dashboard` (regenerar antes de publicar). ¿Se versiona `docs/confluence/`? La spec asume que **sí**, porque el diff del PR es parte de la visibilidad pedida.

---

## Comparativa

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Política de alcance del mirror | Media | 4 h | 200 € | 40k | Alta 🟠 | Media |
| C-02 | Disparadores que faltan (cierre + ledger) | Baja | 3 h | 150 € | 35k | Media 🟡 | Media |
| C-03 | Evidencias binarias de qa *(ajustado en puerta go: D4 = excluir)* | Baja | 0,5 h | 25 € | 15k | Alta 🟠 | Alta |
| C-04 | Documentar la política (ES + EN + FLOWS) | Baja | 3 h | 150 € | 45k | Media 🟡 | Alta |
| C-05 | Verificador + **staging generado** *(ajustado post-go: D5 = sí, ampliado)* | Alta | 7,5 h | 375 € | 100k | Alta 🟠 | Baja |
| | **Total** | | **18 h** | **900 €** | **235k** | | |

> La fila de totales recoge solo el trabajo por característica. La revisión adversarial y el coste de proceso van como líneas propias en el presupuesto (aprendizajes nº 2 y nº 3 de `CALIBRATION.md`).

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18 h × 50 €/h | 900,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 180,00 € |
| Tokens IA — características | 235k (203k in / 32k out) | 1,75 € |
| Tokens IA — revisión adversarial (2 lentes) | 70k (60k in / 10k out) | 0,53 € |
| Tokens IA — coste de proceso (spec + evaluación + plan) | 50k (44k in / 6k out) | 0,36 € |
| Tokens IA — lectura de caché | ~3,5M × 0,50 USD/M ⚠️ supuesto | 1,61 € |
| Margen sobre tokens | +20 % | 0,85 € |
| **Total estimado (con margen)** | 21,6 h × 50 €/h + 5,10 € | **≈ 1.085 €** |

**Notas de método:** los tokens son **facturables** (entrada + escritura de caché + salida); la lectura de caché no cuenta para horas pero **sí para dinero** (aprendizaje nº 4). Las horas humanas de revisión están dentro de las horas por característica; la línea de "revisión adversarial" presupuesta el consumo del ciclo de dos lentes, que en las 4 vías rápidas del histórico encontró entre 1 y 10 hallazgos y fue donde se fue el trabajo real. Tras D5 esa línea **sube de 60k a 70k** y la lectura de caché de 3M a 3,5M: el lote deja de ser prosa pura y la revisión tiene que leer script, tests y el contrato cruzado con `confluence-pull`.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 21,6 h *(18 h base)* |
| Horas IA (ejecución) | 0,89 h *(0,74 h base)* |
| Supervisión humana | 0,22 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **1,11 h** |
| Horas ahorradas | 20,49 h |
| **Ahorro** | **94,9 %** |
| **Multiplicador de productividad** | **×19** |
| FTE equivalentes *(opcional)* | 0,13 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA).

**Cómo se han obtenido (y qué valen):** las horas IA **no** son un juicio: salen de `426.000 tokens facturables ÷ 479.326 tok/h`, la mediana medida de `CALIBRATION.md` (5 muestras). Las horas humanas sí son un juicio y **nunca se han validado en este proyecto**, así que el multiplicador ×19 compara una medida contra una estimación: úsalo para justificar el valor de hacerlo con agentes, **no** como promesa de plazo. El plazo real que fija este presupuesto es la fila de horas totales: ~1 h de reloj de agente más supervisión.

---

## Recomendación

- **Veredicto**: **GO sin condiciones** (puerta cruzada el 2026-08-20; D1-D4 en la puerta y D5 en la iteración post-go). Trabajo preventivo y sin riesgo de regresión sobre código de producto: nada de lo que se toca está en uso hoy, porque el circuito nunca se ha activado. Alcance comprometido: **las 5 características**.
- **Quick wins** (bajo coste, alto valor): **C-03** (0,5 h tras D4: una línea de `exclude` que elimina las imágenes rotas y el riesgo de divergencia publish/pull) y **C-02** (parte de comandos: 3 líneas idénticas, cierra un hueco funcional completo).
- **Costosas / a vigilar**: **C-05** (7,5 h, el **42 %** del esfuerzo del lote y la estimación más volátil, rango 6-9 h). Ya no es descartable, así que la palanca de control pasa a ser el **alcance de sus tests**: si hay que recortar, se recorta cobertura de casos de glob, nunca CA-10 (idempotencia del staging) ni CA-11 (mapeo inverso del pull), que son las dos garantías del contrato nuevo.
- **Orden sugerido**: **C-01 + C-03 (misma fase) → C-02 → C-05 → C-04** — C-01 define el vocabulario (`exclude`) que las demás usan y C-03 es literalmente una línea de esa misma lista; C-02 cablea los disparadores una vez está claro qué se publica; **C-05 se adelanta a C-04** (antes iba al final) porque el staging cambia lo que hay que documentar —carpeta generada, `publish.source`, contrato del pull, hook— y documentar antes obligaría a rehacer el espejo EN dos veces; C-04 cierra con la política ya materializada.
- **Fuera de alcance recomendado**: subida de adjuntos/imágenes (el conector no la expone y forzarla chocaría con la regla "no reimplementes la API"), permisos por página, y limpieza de espacios publicados con la política antigua (no aplica hoy: no hay ninguno).

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Se define la política "a ciegas": el circuito nunca se ha ejercitado end-to-end (no hay `confluence.json` ni `confluence-state.json`) | Alta | Medio → **Bajo tras D5** | `--stage` permite ver el árbol exacto que se subiría **antes** de conectar nada, y `--status` compara contra el manifiesto; el primer `enabled: true` deja de ser un salto a ciegas |
| El conector no borra páginas: una exclusión aplicada tarde deja contenido interno publicado, solo marcable como obsoleto | Media | Alto | Cerrar C-01 **antes** del primer `enabled: true` de cualquier proyecto; la ventana está abierta hoy y es gratis |
| ~~Transformar el markdown al publicar rompe la simetría con `confluence-pull`~~ — **eliminado por D4** (no hay transformación: publicado ≡ local) | — | — | Cerrado en la puerta go: se excluye `**/testing/**` |
| Ausencias silenciosas: plan, `tasks.md` y `testing/**` no suben (D1/D4) y el disparo por fase de `implementer` (D3) no publica el ledger; alguien puede buscar en Confluence algo que nunca estará | Alta | Bajo | Hacer los "no" explícitos en la matriz de `docs/FLOWS.md` y en la doc de la skill (C-04, CA-04/CA-05); es documentación, no mecánica |
| Regla bilingüe: cada doc clave tocada exige su espejo en `docs/en/` en el mismo cambio | Media | Bajo | Convertirlo en criterio de aceptación (CA-05) y verificarlo con el linter antes de cerrar |
| ~~La política vive solo en prosa y depende del criterio del agente~~ — **cerrado por D5**: `--stage` materializa el alcance en `docs/confluence/` y `--check` lo verifica con exit code | — | — | C-05 comprometido; la política pasa de prosa a artefacto verificable |
| Deriva de la carpeta generada: alguien la edita a mano o publica un staging obsoleto y lo publicado deja de corresponder al canónico | Media | Medio | `README.md` de aviso en la carpeta, `--status` señalando divergencia/desactualizado, regeneración obligatoria antes de comparar con el manifiesto (CA-10), hook ignorando `docs/confluence/**` (CA-12) |
| Contrato cruzado nuevo: `confluence-pull` debe escribir en el fichero canónico y no en la copia staged | Media | Alto | CA-11 como criterio con test propio; el script expone el mapeo inverso y el pull lo consume (no lo reimplementa) |
| Estimación de horas humanas no validada (0 h reales en las 5 filas del histórico) | Alta | Medio | Presentar el coste como comparativa entre características, no como compromiso; ejecutar `/retro` al cerrar para seguir calibrando |
| Supuesto económico sin verificar: tipo de cambio USD→EUR fijado a 0,92 | Media | Bajo | Impacto acotado (< 5 € del total); verificarlo solo si estas cifras van a facturarse |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `improvement-plan.md` + `tasks.md` en `docs/roadmap/2026-08-20-confluence-policy/`). **D1-D5 están cerradas** y recogidas en la spec (`aprobada`): no hay nada que decidir en la puerta del plan. Orden a heredar: **C-01 + C-03 (misma fase) → C-02 → C-05 → C-04**, con las 5 características en el alcance comprometido. El `planner` hereda las horas y costes por característica de esta evaluación — no re-estima desde cero — y actualizará la fila **Plan** de este documento y el campo `plan:` de la spec al crear el plan.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-08-20 | Creación de la evaluación a partir de `spec.md` (creada en la misma pasada desde el análisis previo del circuito). 5 características, veredicto go condicionado. Estado → `en-revision`. Medición de generación degradada a `estimado`: `usage-meter.py` no disponible en el entorno. |
| 2026-08-20 | **Puerta go/no-go: GO.** D1-D4 cerradas por el usuario. Ajuste de cifras por **D4 (excluir `**/testing/**` en vez de transformar)**: C-03 de 2,5 h/125 € a 0,5 h/25 € y de 30k a 15k tokens; totales 18 h → **16 h base** (21,6 → **19,2 h** con margen), ≈ 1.085 € → **≈ 965 €**, 330k → **315k** tokens, ×21 → **×19**. C-01 se mantiene en 4 h (−1 h por D2 sin presets, +1 h por la selección curada de D1). Riesgo de divergencia publish/pull **eliminado**; añadido el riesgo de "ausencias silenciosas". Estado → `completado`; spec → `aprobada`. |
| 2026-08-20 | **Iteración post-go: D5 = sí, C-05 ampliado con staging generado.** El verificador incorpora `--status` (informe alcance/sincronizado/desactualizado/excluido) y `--stage` (regenera `docs/confluence/`, copia derivada no editable; `publish.source` apunta ahí), más el mapeo inverso staged → canónico para `confluence-pull` y el hook ignorando la carpeta. C-05: 5,5 h/275 €/70k → **7,5 h/375 €/100k** y **deja de ser opcional**. Totales 16 h → **18 h base** (19,2 → **21,6 h** con margen), ≈ 965 € → **≈ 1.085 €**, 315k → **355k** tokens (revisión 60k → 70k; caché 3M → 3,5M). Nuevos criterios CA-10/CA-11/CA-12; orden revisado (C-05 pasa por delante de C-04). Riesgos: cerrado el de "política solo en prosa"; añadidos deriva del staging y contrato cruzado con el pull. Estados sin cambio (spec `aprobada` / evaluación `completado`). |
