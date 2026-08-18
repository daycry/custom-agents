# CALIBRATION — histórico de calibración de estimaciones

Cada fila sale de un `/retro` de una iniciativa **cerrada**. Lo leen dos piezas:

- el agente **`evaluator`**, para ajustar sus estimaciones con datos de este proyecto en vez de defaults;
- **`usage-meter.py`**, que toma la **mediana de la columna `tokens/hora`** como ratio para convertir tokens medidos en horas-IA (precedencia sobre el default de `estimation-defaults.md`).

> **Cómo se calcula `tokens/hora` (definición, para que sea reproducible y no circular).**
> Numerador: **tokens facturables medidos** de la iniciativa = entrada + creación de caché + salida
> (la lectura de caché queda fuera — mide longitud de sesión, no trabajo). Cuando dos artefactos
> comparten ventana (el `planner` mide `improvement-plan.md` y `tasks.md` juntos), esa ventana
> cuenta **una vez**.
> Denominador: **tiempo de reloj real** de esas ventanas (`fin − inicio` de cada bloque
> `generacion:`, sumado). Es una medida **independiente** de las horas que el propio meter deriva
> — usar `horas_ia` como denominador sería circular y devolvería siempre el ratio de entrada.
>
> **Límites conocidos:** el reloj de una ventana en sesión interactiva puede incluir esperas y
> excluye el consumo de subagentes que no queda en la transcripción medida; el ratio es por tanto
> una **cota inferior razonable**, no una constante física. Se refina con cada retro.

| Fecha | Iniciativa | Desv. producción | Desv. tokens | tokens/hora (medido) | Causa principal | Ajuste sugerido |
|---|---|---|---|---|---|---|
| 2026-08-12 | sdd-hardening | −96 % (0,26 h reales vs 6,2 h est.) | −97 % (58.914 vs 2.073k est.) | 584271 | Estimación calibrada con defaults genéricos (ratio 300k tok/h y horas-IA "a juicio"), no con medición del propio proyecto: el primer ciclo medido reveló que producir los artefactos cuesta ~1 orden de magnitud menos de lo presupuestado | Estimar el **coste de proceso** (spec/eval/plan) con el ratio calibrado, no con horas a juicio; mantener las horas HUMANAS separadas, que son las que no bajan |
| 2026-08-12 | workflow-polish | −97 % (0,03 h reales vs 1,1 h est.) | −95 % (16.377 vs 330k est.) | 479326 | Vía rápida sobre terreno conocido (3 disciplinas de prosa, sin scripts): la estimación gruesa se hizo por analogía con iniciativas con código | Vía rápida de solo prosa: estimar en minutos, no en horas; reservar las horas para tareas con scripts y tests |
| 2026-08-12 | plugin-dev | −88 % (0,10 h reales vs 0,8 h est.) | −80 % (49.175 vs 250k est.) | 300050 | Ídem prosa + plantillas; el coste real se fue en la **revisión** (2 hallazgos críticos), no en escribir | Presupuestar explícitamente la revisión de dos lentes como línea aparte: es donde se va el trabajo real en piezas de prosa |
| 2026-08-12 | subagent-personas | −83 % (0,14 h reales vs 0,8 h est.) | −74 % (65.711 vs 250k est.) | 421674 | La única con **TDD real** (7 tests): más tokens y más tiempo que las de prosa pura, y aun así por debajo de la estimación | Cuando la tarea lleva tests, multiplicar la estimación de la vía rápida por ~2 respecto a una de prosa |
| 2026-08-13 | quick-implement | −77 % (0,07 h reales vs 0,3 h est.) | −66 % (34.062 vs 100k est.) | 1048061 | Alcance minúsculo y bien definido de antemano (la spec de backlog ya estaba escrita) | Una spec previa reduce el coste de implementación de forma medible: el trabajo de definir no se repite |

> Ratio vigente: 479326 tokens/hora (mediana de 5 muestras)

> **Efecto de esta primera calibración (2026-08-18).** Las horas-IA de los artefactos y ledgers ya
> medidos se **re-derivaron** con este ratio (antes usaban el default de 300.000): bajan ~40 %.
> Los tokens no se tocan — son la medición. El campo `ratio_usado` de cada bloque `generacion:`
> dice con qué ratio se derivó, así que el cálculo siempre es auditable.

> **Coste en € (2026-08-18).** `rates-verify` verificó los precios de Opus 4.8 en la doc oficial
> ($5/M entrada · $25/M salida · $6,25/M escritura de caché · $0,50/M lecturas) y los escribió en
> `.claude/rates.json`, así que el coste de proceso ya sale en euros de verdad: **12,35 € el total
> de las 5 iniciativas medidas**. Ojo: `tipoCambioUsdEur` (0,92) sigue siendo un **supuesto**, no un
> dato verificado — revísalo antes de usar estas cifras para facturar.

## Aprendizajes acumulados (lo que ya no hay que volver a descubrir)

1. **El default de 300.000 tok/hora subestima el ritmo real en ~1,6×.** Con la mediana medida
   (479.326) las horas-IA reportadas bajan ~40 % y se acercan al reloj. Afecta a lo que
   `jira-sync` imputa como worklog: antes se imputaba de más.
2. **Las horas HUMANAS estimadas no se han validado nunca.** Todas las filas tienen 0 h humanas
   reales porque el trabajo lo hizo la IA con supervisión conversacional. La desviación de
   "producción" mide IA, no personas: no sirve para prometer plazos a un cliente.
3. **El coste está en la revisión, no en escribir.** En las cuatro vías rápidas, la revisión de dos
   lentes encontró 1-10 hallazgos cada vez (dos de ellos habrían roto una garantía del producto).
   Presupuéstala como línea propia.
4. **La lectura de caché no cuesta horas pero SÍ cuesta dinero.** Queda fuera del cálculo de horas
   (mide longitud de sesión, no trabajo) pero se factura a 0,50 USD/M: en estas 5 iniciativas son
   millones de tokens y la mayor parte de los 12,35 €. Que no aparezca en las horas no significa
   que sea gratis.
5. **Estimar por analogía con "iniciativas con código" infla las de prosa.** Distinguir tres
   tamaños: prosa (minutos), prosa + tests (×2), código de producto (horas).
