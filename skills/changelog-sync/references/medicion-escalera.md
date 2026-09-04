# Medición de la escalera del resumen (los topes, y por qué son esos)

**Léelo solo si vas a mover un tope de `changelog-sync.py`.** Todo lo de aquí se midió el
2026-09-04 sobre los **13 ledgers cerrados** de este repo (los que tenían `estado: completado`
antes de esta iniciativa) y sus **63 tareas**;<!--m:base_ledgers=13,base_tareas=63--> los 6 legacy
sin frontmatter se ignoran con aviso, como siempre.<!--m:ledgers_legacy=6--> **13 ledgers, 63
tareas**: donde se lea «los 63 ledgers» es un error de redacción que la revisión de dos lentes cazó
en 10 ficheros y está corregido. Con el ledger de esta iniciativa cerrado el corpus de HOY es de
**14 ledgers y 70 tareas**,<!--m:ledgers_cerrados=14,tareas=70--> y donde importa la diferencia se
dice cuál de los dos se está midiendo.

**Cada cifra de este documento la imprime el script**, no la memoria de nadie:
`python3 changelog-sync.py --medicion` (o `--medicion --json`) las mide sobre el árbol de trabajo, y
`tests/test_cifras_medidas.py` compara una por una las cifras MARCADAS de este fichero —y las de
`SKILL.md`, `ADR-012`, `docs/knowledge/README.md`, `docs/CONVENTIONS.md` + espejo EN y el ledger—
con lo que sale de la medición: si divergen, la suite se pone roja. La marca es un **comentario
HTML invisible al renderizar** que va justo detrás de la cifra y la ata a su clave del script; las
cifras que **no** son medibles de forma determinista (el «antes» lo midió el script de `a7a11b0`,
que un clon superficial de CI no tiene) llevan la variante «no verificable», que obliga a escribir
el motivo, y se dicen como históricas en vez de como reproducibles. **La sintaxis exacta de las dos
marcas, y el porqué de este mecanismo** (en vez de «no escribas cifras, enlaza»), están en la
cabecera de `tests/test_cifras_medidas.py`; para ver las de este fichero, `grep '<!--m' <fichero>`.

## El problema, medido

El bullet salía con la **primera frase completa** de la `Descripción` del ledger. Esas
descripciones están escritas para el implementador, no para el CHANGELOG (cifras HISTÓRICAS: las
midió el script de `a7a11b0`, cuyo `primera_frase` no tenía la guarda de abreviaturas, así que hoy
no se pueden re-medir desde el árbol de trabajo)<!--m?:medido con el script de a7a11b0; el ref no existe en un clon superficial de CI-->:

```
tareas: 63 · primera frase: mediana 447 chars · max 1944 · >400 chars: 37
  1944  parity-core/T-01     Tiering de modelos CONFIGURABLE (dos capas)
  1502  memory-health/T-04   Integración, doc, memoria y cierre
  1397  superiority/T-06     Integración, doc, memoria y cierre
```

Y el bullet completo (título + frase + hasta 5 ficheros) era todavía peor: **mediana 660,
máximo 2.163**<!--m?:mismo motivo: el bullet ANTES lo producia el script de a7a11b0-->.
Consecuencia real: las notas de la v1.16.0 se escribieron a mano.

## `RESUMEN_MAX = 200`

Qué queda con cada candidato, contando por qué camino de la escalera pasa cada tarea:

| Tope | camino `frase` | camino `corte` | camino `titulo` |
|---|---|---|---|
| 160 | 11 | 10 | 42 |<!--m:base_tope160_frase=11,base_tope160_corte=10,base_tope160_titulo=42-->
| **200** | **12** | **9** | **42** |<!--m:base_tope200_frase=12,base_tope200_corte=9,base_tope200_titulo=42-->
| 240 | 14 | 9 | 40 |<!--m:base_tope240_frase=14,base_tope240_corte=9,base_tope240_titulo=40-->

Los números casi no se mueven (±2 tareas), así que el criterio no puede ser «cuántas rescata». Es
**qué texto deja entrar**, mirando exactamente las tareas que cambian de camino:

- **160 → 200** cambia UNA tarea, `windows-console/T-02` (192 caracteres), y la mejora: con 160 la
  frase no cabe y el paso 3 la recorta a «`release.py` presentaba `changelog-sync --check:
  PENDIENTE` cuando el script había **crasheado**», que pierde justo el *por qué* del cambio; con
  200 entra completa, con su paréntesis: «… (el exit 1 del `UnicodeEncodeError` es indistinguible
  del exit 1 de «hay entradas pendientes»).»
- **200 → 240** añade DOS, y una es lo que se quería quitar: `deterministic-guardrails/T-04`, 237
  caracteres y **tres cláusulas separadas por punto y coma**, que se lee como párrafo de
  documentación, no como nota de release. La otra (`plan-and-diet/T-03`, 212) es aceptable, pero no
  compensa abrir la puerta a la primera.
- **200** ≈ dos frases de español técnico (2 × ~100), que es el objetivo declarado del bullet.

## `ARCHIVOS_MAX = 3` y `ARCHIVOS_MAX_TOCADOS = 6`

Número TOTAL de ficheros que toca una tarea: **mediana 8, máximo 62**; 53 de 63 tareas tocan más
de 3.<!--m:base_archivos_mediana=8,base_archivos_max=62,base_archivos_mas_de_3=53,base_tareas=63-->
Con el tope anterior (5) el paréntesis era una lista arbitraria de 5 de 20, que hacía creer que eran
todos.

| Umbral (`≤` → se muestra) | Tareas con paréntesis | Sin paréntesis |
|---|---|---|
| 3 | 10/63 (16 %) | 53 |<!--m:base_umbral_3=10,base_umbral_3_pct=16,base_umbral_3_sin=53-->
| 4 | 17/63 (27 %) | 46 |<!--m:base_umbral_4=17,base_umbral_4_pct=27,base_umbral_4_sin=46-->
| 5 | 20/63 (32 %) | 43 |<!--m:base_umbral_5=20,base_umbral_5_pct=32,base_umbral_5_sin=43-->
| **6** | **24/63 (38 %)** | **39** |<!--m:base_umbral_6=24,base_umbral_6_pct=38,base_umbral_6_sin=39-->
| 8 | 32/63 (51 %) | 31 |<!--m:base_umbral_8=32,base_umbral_8_pct=51,base_umbral_8_sin=31-->
| 10 | 38/63 (60 %) | 25 |<!--m:base_umbral_10=38,base_umbral_10_pct=60,base_umbral_10_sin=25-->

Se elige **6 = 2 × `ARCHIVOS_MAX`**: la lista informa mientras los 3 que se muestran sean al
menos la mitad de lo tocado. Por encima, se omite el paréntesis entero (no se pone «y 17 más»:
el puntero al ledger ya está para eso).

## `CORTE_MIN_PALABRAS = 5` — y el hallazgo incómodo

El paso 3 (cortar en el primer `:`, `;`, `—` o `(` de nivel superior) **rescata poco en este
repo, y el motivo es estructural**: la mayoría de las `Descripción` empiezan por la ruta del
fichero entre acentos graves seguida de `:`. Cortar ahí no da un resumen, da una lista de
ficheros. Sin la puerta de «se lee como una idea completa», el paso 3 producía cosas como:

```
memory-health/T-04   → `docs/README.md` + `docs/en/README.md`.
parity-core/T-02     → `agents/architect.md`.
superiority/T-05     → `skills/api-contract/SKILL.md`.
```

Peor que el título, que al menos dice «Agente `architect` + `design.md`». La puerta es contar
**palabras de prosa** (fuera de los tramos entre acentos graves). Barrido completo de la constante
con tope 200, sobre las 63 tareas (`frase` no depende de ella y se queda fijo en 12):

| `CORTE_MIN_PALABRAS` | `corte` | `titulo` |
|---|---|---|
| 0 (sin puerta) | **41** | 10 |<!--m:base_barrido0_corte=41,base_barrido0_titulo=10-->
| 1 | 21 | 30 |<!--m:base_barrido1_corte=21,base_barrido1_titulo=30-->
| 2 | 15 | 36 |<!--m:base_barrido2_corte=15,base_barrido2_titulo=36-->
| 3 | 14 | 37 |<!--m:base_barrido3_corte=14,base_barrido3_titulo=37-->
| 4 | 10 | 41 |<!--m:base_barrido4_corte=10,base_barrido4_titulo=41-->
| **5** | **9** | **42** |<!--m:base_barrido5_corte=9,base_barrido5_titulo=42-->
| 6 | 7 | 44 |<!--m:base_barrido6_corte=7,base_barrido6_titulo=44-->
| 7 | 6 | 45 |<!--m:base_barrido7_corte=6,base_barrido7_titulo=45-->

**Sin la puerta el paso 3 «rescata» 41 tareas**, casi todas con una lista de ficheros por resumen;
el trasvase que produce la puerta al valor elegido es de **32** (`corte` 41 → 9).<!--m:base_trasvase_corte=32--> Una versión
anterior de este documento decía «34» y **ningún valor de la constante da 34**: era una cifra
inventada, y la revisión de dos lentes la cazó re-corriendo el barrido.

Se elige **5** porque es el punto donde desaparecen los casos que son solo rutas y todavía entran
frases cortas legítimas («`statusline/roadmap-statusline.sh` lee el JSON de stdin.»).

**Conclusión honesta:** el paso 3 es una red de seguridad pequeña, no la solución. La solución es
el campo `- **Changelog**:` (paso 1). Con los ledgers del corpus base, **42 de 63 tareas
(67 %) degradan al título**.<!--m:base_camino_titulo=42,base_tareas=63,base_degradan_titulo_pct=67-->

## Antes / después sobre los 13 ledgers (63 tareas, 2026-09-04)

`changelog-sync.py --dry-run` sobre una copia del repo con los CHANGELOG vaciados, para que las
13 iniciativas salgan pendientes (126 bullets = 63 tareas × 2 idiomas):

| | Mediana | Máximo | Media | Bullets > 400 chars |
|---|---|---|---|---|
| Antes (`a7a11b0`) | 660 | 2.163 | 758 | 100/126 |<!--m?:la fila ANTES la midio el script de a7a11b0, que no esta en el arbol de trabajo-->
| Después | 128 | 325 | 153 | **0/126** |<!--m:base_bullet_mediana=128,base_bullet_max=325,base_bullet_media=153,base_bullet_mayores_400=0-->

### El agregado engaña: desglose POR CAMINO

Esa mediana de 128 sale de un corpus en el que **42 de 63 bullets son solo el título**,<!--m:base_camino_titulo=42,base_tareas=63--> así que
mide sobre todo el camino que la iniciativa quiere EVITAR. Por camino (mismo corpus de 13 ledgers,
un bullet por tarea):

| Camino | N | Mediana | Máximo | Media | El más largo |
|---|---|---|---|---|---|
| `frase` | 12 | 260 | **325** | 244 | `windows-console/T-06` |<!--m:base_camino_frase=12,base_frase_mediana=260,base_frase_max=325,base_frase_media=244-->
| `corte` | 9 | 170 | 280 | 198 | `activation-reliability/T-03` |<!--m:base_camino_corte=9,base_corte_mediana=170,base_corte_max=280,base_corte_media=198-->
| `titulo` | 42 | 115 | 168 | 117 | `debt-cleanup/T-03` |<!--m:base_camino_titulo=42,base_titulo_mediana=115,base_titulo_max=168,base_titulo_media=117-->
| **TOTAL** | **63** | **128** | **325** | **153** | — |<!--m:base_tareas=63,base_bullet_mediana=128,base_bullet_max=325,base_bullet_media=153-->

Y con el ledger de esta iniciativa cerrado (14 ledgers, 70 tareas) aparece el camino que se
promueve, que es **el que produce los bullets más largos**:

| Camino | N | Mediana | Máximo |
|---|---|---|---|
| `changelog` | 7 | **347** | **376** |<!--m:camino_changelog=7,changelog_mediana=347,changelog_max=376-->
| `frase` | 12 | 260 | 325 |<!--m:camino_frase=12,frase_mediana=260,frase_max=325-->
| `corte` | 9 | 170 | 280 |<!--m:camino_corte=9,corte_mediana=170,corte_max=280-->
| `titulo` | 42 | 115 | 168 |<!--m:camino_titulo=42,titulo_mediana=115,titulo_max=168-->
| **TOTAL** | **70** | **133** | **376** |<!--m:tareas=70,bullet_mediana=133,bullet_max=376-->

**El techo real del bullet completo, medido con los títulos y las rutas de este repo, es 376
caracteres**<!--m:bullet_max=376--> (`changelog-brief/T-01`), no 325. No es una contradicción del diseño: `RESUMEN_MAX`
acota **el resumen**, no el bullet, y el resto lo ponen el título del ledger (que no se toca) y la
lista de ficheros. Escribir el campo alarga el bullet a cambio de que DIGA algo: el `titulo` es
corto porque no dice nada. Por eso `RESUMEN_MAX` **no** se toca por esto: 200 para el resumen sigue
justificado arriba, y lo que había que arreglar era la afirmación.

Descomposición exacta del bullet más largo del corpus base (325, `windows-console/T-06`), que una
versión anterior de este documento daba como «resumen 150 · título 68 · lista 96» — las tres
componentes estaban mal y el total bien, así que ahora las mide el script:

| Componente | Caracteres |
|---|---|
| cabecera `- **T-06 — …**` (con la negrita y el guion) | 83 |<!--m:base_peor_cabecera=83-->
| espacio | 1 |
| resumen (camino `frase`) | 152 |<!--m:base_peor_resumen=152-->
| `` (`a`, `b`, `c`) `` (3 de 4 ficheros tocados) | 89 |<!--m:base_peor_ficheros=89-->
| **TOTAL** | **325** |<!--m:base_bullet_max=325-->

El título en crudo mide **70** caracteres;<!--m:base_peor_titulo=70--> los 83 son con
`- **T-06 — ` y `**`.

Caminos tomados, por iniciativa del corpus base (el agregado de HOY sale de
`--check --json` → `degradacion.caminos`, que recorre TODO ledger cerrado; `pendientes[].caminos`
solo cubre las iniciativas que faltan en el CHANGELOG):

| Iniciativa | Tareas | Caminos |
|---|---|---|
| `knowledge-split` | 5 | `frase` 1 · `corte` 1 · `titulo` 3 |<!--m:base_tareas_knowledge_split=5,base_caminos_knowledge_split_frase=1,base_caminos_knowledge_split_corte=1,base_caminos_knowledge_split_titulo=3-->
| `adversarial-review` | 4 | `frase` 1 · `corte` 1 · `titulo` 2 |<!--m:base_tareas_adversarial_review=4,base_caminos_adversarial_review_frase=1,base_caminos_adversarial_review_corte=1,base_caminos_adversarial_review_titulo=2-->
| `debt-cleanup` | 6 | `frase` 1 · `titulo` 5 |<!--m:base_tareas_debt_cleanup=6,base_caminos_debt_cleanup_frase=1,base_caminos_debt_cleanup_titulo=5-->
| `deterministic-guardrails` | 5 | `frase` 2 · `titulo` 3 |<!--m:base_tareas_deterministic_guardrails=5,base_caminos_deterministic_guardrails_frase=2,base_caminos_deterministic_guardrails_titulo=3-->
| `live-visibility` | 4 | `corte` 1 · `titulo` 3 |<!--m:base_tareas_live_visibility=4,base_caminos_live_visibility_corte=1,base_caminos_live_visibility_titulo=3-->
| `activation-reliability` | 4 | `frase` 1 · `corte` 2 · `titulo` 1 |<!--m:base_tareas_activation_reliability=4,base_caminos_activation_reliability_frase=1,base_caminos_activation_reliability_corte=2,base_caminos_activation_reliability_titulo=1-->
| `distribution` | 4 | `frase` 1 · `corte` 1 · `titulo` 2 |<!--m:base_tareas_distribution=4,base_caminos_distribution_frase=1,base_caminos_distribution_corte=1,base_caminos_distribution_titulo=2-->
| `memory-health` | 4 | `titulo` 4 |<!--m:base_tareas_memory_health=4,base_caminos_memory_health_titulo=4-->
| `parity-core` | 6 | `titulo` 6 |<!--m:base_tareas_parity_core=6,base_caminos_parity_core_titulo=6-->
| `plan-and-diet` | 4 | `frase` 1 · `titulo` 3 |<!--m:base_tareas_plan_and_diet=4,base_caminos_plan_and_diet_frase=1,base_caminos_plan_and_diet_titulo=3-->
| `roles-and-jira-flow` | 5 | `corte` 2 · `titulo` 3 |<!--m:base_tareas_roles_and_jira_flow=5,base_caminos_roles_and_jira_flow_corte=2,base_caminos_roles_and_jira_flow_titulo=3-->
| `superiority` | 6 | `titulo` 6 |<!--m:base_tareas_superiority=6,base_caminos_superiority_titulo=6-->
| `windows-console` | 6 | `frase` 4 · `corte` 1 · `titulo` 1 |<!--m:base_tareas_windows_console=6,base_caminos_windows_console_frase=4,base_caminos_windows_console_corte=1,base_caminos_windows_console_titulo=1-->
| **TOTAL** | **63** | `titulo` **42** · `frase` **12** · `corte` **9** |<!--m:base_tareas=63,base_camino_titulo=42,base_camino_frase=12,base_camino_corte=9-->

Con el ledger de esta iniciativa cerrado se le suma `changelog-brief`, con todas sus tareas por el
camino `changelog`, así que el TOTAL de hoy es `titulo` 42 · `frase` 12 · `corte` 9 · `changelog` 7
sobre 70 tareas.<!--m:camino_titulo=42,camino_frase=12,camino_corte=9,camino_changelog=7,tareas=70-->
(Ese `changelog` pasó de 6 a 7 y su mediana de 350 a 347 al cerrar T-07, y **el test de las cifras
lo cazó en los cinco ficheros que lo copiaban**: es exactamente la clase de error que T-07 cierra,
demostrada sobre sí misma.)

## Los bullets que salen MAL (para no fingir que están bien)

- `- **T-06 — Integración, doc, memoria y cierre** ([ledger](…))` — el bullet es correcto y el
  título es inútil como nota de release. Se repite en tres iniciativas. Solo lo arregla el campo.
- `- **T-01 — Salida UTF-8 segura…** Los **27 scripts Python versionados con caracteres no
  ASCII**.` — camino `corte`: frase nominal, sin verbo. Cabe en el tope y no dice qué les pasó.
  (La negrita del final la CIERRA `normaliza_resumen()`; hasta el cierre de los gaps del intento 1
  la borraba, y este ejemplo se leía «Los 27 scripts Python versionados con caracteres no ASCII.»)
- `- **T-02 — Índice de skills al arrancar…** `agent-kits/shared/skill-index.py` genera,
  DETERMINISTA desde los frontmatters.` — camino `corte`: se corta tras una coma y queda colgando.

Los tres son el mismo diagnóstico: **ningún corte automático sustituye a una frase escrita a
propósito**. El script hace lo máximo honesto; lo bueno lo escribe una persona en un campo.

## `RESUMEN_FRASES_MAX = 2` no es un tope duro, y eso es honesto decirlo

El recorte a dos frases se apoya en `FIN_FRASE`, que reconoce el fin de frase por **tipografía**:
punto + espacio + apertura de frase (mayúscula, `¿`, `«`, `` ` `` o `*`). De ahí dos consecuencias
que hay que saber antes de fiarse del número:

- **Una abreviatura seguida de mayúscula parecía fin de frase.** Medido: un campo de EXACTAMENTE
  dos frases («Corrige el orden Sr. Pérez en la firma del comentario. Ahora el CHANGELOG sale en
  dos idiomas.») publicaba solo hasta `…comentario.` y encima avisaba «de más de 2 frases». Lo
  arregla la guarda `ABREVIATURAS` del script (`p. ej.`, `vs.`, `sr.`, `sra.`, `dr.`, `núm.`,
  `pág.`, `cap.`, `art.`, `ee.`, `a. m.`…), hoy **26** formas, con un caso por abreviatura en la
  suite.<!--m:abreviaturas=26--> Este documento decía «las 28 formas» y nunca fueron 28: la cifra
  la imprime ahora el script (`abreviaturas`), así que no puede volver a desincronizarse.

  **La guarda es para abreviaturas de EN MEDIO de la frase, no para las que la terminan.** `ee.`
  entra para no partir «EE. UU.»; `uu.` **no**, porque una frase que termina en «EE. UU.» termina
  ahí y ese caso es el frecuente. Y `etc.` **tampoco**, por el mismo motivo y con el mismo test:
  «… rutas, globs, etc. Tercera frase.» son DOS frases. Tenerlo dentro era una **regresión** medida
  frente a `5a51d7c`: con el fin de frase tapado, `frases()` no encontraba su n-ésimo corte,
  agotaba el bucle y caía en `return s` —el texto ENTERO—, así que un campo de tres frases se
  publicaba completo sin ningún aviso, y uno de cuatro publicaba tres diciendo «recortado a las 2
  primeras frases». Ahora `separa_frases()` es la fuente única de «cuántas frases hay»: `frases()`
  recorta sobre ella (nunca más de `n`) y el aviso cuenta sobre ella (dice cuántas traía).
- **Un texto cuyas frases empiezan en minúscula no se recorta nunca**, y tampoco avisa. Es decir:
  `RESUMEN_FRASES_MAX` es un tope **para el español escrito con tipografía normal**, no una
  garantía sobre cualquier cadena. No se convierte en tope duro a propósito: el campo lo escribe
  una persona y el contrato es respetarlo tal cual (`ADR-012`); lo que se acota de verdad es la
  longitud, y de eso avisa `RESUMEN_MAX` siempre. El aviso de recorte solo sale **cuando de verdad
  se ha recortado**.

## Lo que la revisión de dos lentes cazó del intento 1 (todo medido, todo con test)

- **Un `- **Changelog**:` VACÍO publicaba la línea siguiente del ledger.** `\s*` tras los dos
  puntos, con `re.M`, se come el `\n`: se publicaba `- **T-01 — Arranque sin config** -
  **Estado**: completado`, y lo publicado cambiaba según lo que hubiera debajo (un criterio, o una
  fila de tabla dentro del bullet). Y era el caso que el diseño declara TOLERABLE, así que el único
  camino de detección (`--check`) estaba ciego justo ahí. Arreglado con `[^\S\n]*` en el campo
  `Changelog` **y en `Descripción`**, donde el mismo fallo era anterior a esta iniciativa.
- **La cola del ledger contaba como parte de la última tarea.** El split solo partía en `### T-XX`
  y `### Fase`, así que `## Notas de cierre`, `## Resumen de progreso` o un apéndice quedaban
  dentro del bloque de la ÚLTIMA tarea; un `- **Changelog**:` citado ahí como ejemplo se publicaba
  como su resumen. Medido: **21 de 28** ledgers del repo tienen cola tras su última `### T-XX` (de
  4 a 148 líneas) y **13 de los 14 cerrados** tenían la última tarea
  expuesta.<!--m:ledgers_con_cola=21,ledgers_totales=28,cerrados_con_cola=13,ledgers_cerrados=14-->
  Ahora el bloque cierra en cualquier `^## ` **fuera de una valla de código**, el mismo criterio que
  `ledger-lint.py`. (Este documento decía «12 de los 14»: son **13**, y ahora lo mide el script.)
- **Los dos parsers del campo no reconocían lo mismo.** `ledger-lint.py` aceptaba indentación y
  espaciado libres y el generador exigía `- ` exacto, así que un `-  **Changelog**: …` con dos
  espacios pasaba el linter (lo que ve la persona) y el generador lo descartaba en silencio (lo que
  decide la salida). Ahora el patrón es **uno**, replicado literal, con test que compara las dos
  cadenas byte a byte y los dos parsers sobre la misma tabla de casos.
- **El placeholder de la plantilla llegaba literal al CHANGELOG.** Un `{{…}}` sin sustituir se
  ignora (el bullet degrada) y se avisa en los dos lados; el placeholder de la plantilla del
  `planner` pasó de 274 a **55** caracteres, con test de longitud.<!--m:placeholder_plantilla=55-->
  (Este documento decía «66»; nunca fueron 66.) El criterio de qué cuenta como placeholder se
  reescribió al cerrar los gaps del intento 2: ver «El placeholder no es cualquier `{{…}}`» más
  abajo. La promesa que este documento y el ledger daban —«un placeholder `{{…}}` sin sustituir no
  llega al CHANGELOG»— era falsa por los dos lados: solo cubría el campo `Changelog:` (un `{{…}}`
  en la `Descripción` se publicaba literal) y descartaba texto humano que CITARA un `{{…}}`.
- **La continuación indentada del campo se perdía en silencio** y el bullet se quedaba sin punto
  final. Ahora se absorbe, en los dos parsers.
- **`normaliza_resumen()` borraba la negrita en vez de cerrarla** (`los **27 scripts` → `Los 27
  scripts.`), al contrario de lo que decían su docstring y el nombre de su test. Ahora cierra.
- **`corte_principal()` partía un enlace Markdown** (`[ledger](docs/x.md)` → `[ledger]`, con la
  referencia colgando) y entraba dentro de un tramo de código de doble acento grave. Exposición
  medida en las `Descripción` reales: 0 — pero el bullet del formato nuevo SÍ lleva
  `[ledger](…)`, así que era latente, no inofensivo. Los dos arreglados, con test.
- **Los tests se parametrizaban con las constantes que debían fijar.** Campaña de mutantes: de los
  cuatro delimitadores documentados solo `:` estaba fijado, y `test_archivos_*` construía su
  entrada con `cs.ARCHIVOS_MAX_TOCADOS`, así que cualquier valor pasaba. Ahora hay un caso con
  **literales** por delimitador (`:`, `;`, `—`, `–`, `(`), por pareja (`[`, `{`, `«`) y por tope
  (200, 2, 3, 6, 5).<!--m:resumen_max=200,resumen_frases_max=2,archivos_max=3,archivos_max_tocados=6,corte_min_palabras=5-->
  El recuento que este documento daba («14 de 25 sobrevivían; 0 de 40 sobreviven ahora») era la
  única afirmación de la iniciativa que nadie podía reproducir, **y estaba mal por los dos
  extremos**: `RESUMEN_MAX 200→400` ya moría en `5a51d7c` (sobre-cuenta de supervivientes) y cuatro
  mutantes genuinos seguían vivos (sub-cuenta). El cierre de los gaps del intento 2 versiona la
  campaña como script con su lista, para que el recuento se pueda reproducir en vez de creer: ver
  «La campaña de mutantes» más abajo.

## La campaña de mutantes (reproducible, no una creencia)

`scripts/mutantes.py` es la campaña VERSIONADA: cada mutante es una sustitución literal en
`changelog-sync.py` o en `agent-kits/shared/ledger-lint.py`, con **su motivo escrito** (qué fallo
real reintroduce) y con las suites que lo tienen que matar. Existe porque el recuento del intento 1
—«14 de 25 mutantes sobrevivían; 0 de 40 sobreviven ahora»— era la única afirmación de la
iniciativa que nadie podía volver a ejecutar, y estaba mal por los dos extremos: `RESUMEN_MAX
200→400` ya moría en `5a51d7c` (sobre-cuenta de supervivientes) y cuatro mutantes genuinos seguían
vivos (sub-cuenta). Un recuento que no se puede re-ejecutar no es una medición.

```bash
python3 skills/changelog-sync/scripts/mutantes.py            # campaña completa
python3 skills/changelog-sync/scripts/mutantes.py --list      # la lista y sus motivos
python3 skills/changelog-sync/scripts/mutantes.py --only cerco # un subconjunto
```

Exit `0` si todos mueren · `1` si sobrevive alguno (con el motivo y «falta el test que lo mate»)
· `2` si la LISTA está podrida (un `busca` que ya no aparece exactamente una vez).

**No corre en `pytest -q`** (un pytest por mutante, ~2 min frente a los ~2 s de la suite de la
skill). Lo que sí corre en cada ejecución de la suite es `test_el_arnes_de_mutantes_esta_al_dia`,
que comprueba que cada `busca` sigue apareciendo **exactamente una vez** en su fichero y que cada
mutante tiene motivo: un mutante que dejó de aplicarse en silencio contaría como «muerto» sin haber
probado nada, que es exactamente cómo se podre un arnés.

Los mutantes probados y **descartados por equivalentes** se anotan en el propio script con su
argumento, en vez de dejarlos como supervivientes: si el recuento incluye mutantes que ninguna
suite puede matar, deja de significar algo.

Recuento de hoy, con su salida literal:

```
mutantes: 55/55 muertos
```

## El placeholder no es cualquier `{{…}}`

El criterio del intento 1 era `re.search(r"\{\{.*?\}\}")` sobre el campo: si lo MENCIONA, se
descarta. En un repo cuyas plantillas van llenas de `{{…}}` eso es pérdida silenciosa de texto
escrito a mano — lo que la escalera declara no hacer. Medido, estos dos campos se descartaban, el
bullet degradaba al título y el aviso diagnosticaba «placeholder sin sustituir»:

| Campo escrito a mano | Resultado (intento 1) |
|---|---|
| ``Ahora la plantilla del planner trae `{{qué cambia para quien USA el proyecto}}` en vez del párrafo largo.`` | descartado |
| `El generador acepta {{slug}} y {{fecha}} en el nombre de la sección.` | descartado |

Ni un tramo de código eximía. Y el primero es, literalmente, la frase que se escribiría sobre el
cambio que introdujo la guarda.

**Criterio de hoy: el campo ES el placeholder.** `es_placeholder(t)`: quitando los tramos de código
(`sin_codigo()`) y los bloques `{{…}}`, no queda prosa propia. De ahí:

- `{{qué cambia para quien USA el proyecto, en una frase}}` → placeholder (no está escrito).
- `` Ahora la plantilla trae `{{qué cambia}}` en vez del párrafo largo. `` → escrito: el `{{…}}` va
  dentro de acentos graves, así que es una cita.
- `El generador acepta {{slug}} y {{fecha}} en el nombre de la sección.` → escrito: hay prosa
  propia alrededor.
- `{{slug}} ahora se acepta.` → escrito. Se descartó por eso la regla «empieza por `{{`»: el sesgo
  es siempre **publicar lo que escribió una persona**, y una frase que empieza por una variable de
  plantilla es una frase.

La guarda cubre `Changelog:` **y `Descripción`**: hasta el cierre de los gaps del intento 2,
`resumen("{{Qué hay que hacer y por qué, en 1-3 frases.}}", None)` publicaba el placeholder de la
plantilla literal, sin aviso y por el camino `frase`.

El criterio es UNO: `PLACEHOLDER_PATTERN` + `PLACEHOLDER_RELLENO` viven en `ledger-lint.py`, la
skill guarda copia literal, y la suite compara las cadenas byte a byte **y las dos funciones** sobre
una tabla única de casos. Y cuenta como deuda: un campo vacío o que es el placeholder aparece en
`--check --json` → `degradacion.sin_campo_por_motivo` (`ausente` · `vacio` · `placeholder`), porque
el bullet degrada igual.
