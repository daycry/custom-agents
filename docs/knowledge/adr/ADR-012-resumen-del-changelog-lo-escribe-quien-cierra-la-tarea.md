---
id: ADR-012
titulo: El resumen del CHANGELOG lo escribe quien cierra la tarea (campo `Changelog:`), y el script degrada al título antes que truncar
estado: aceptada
fecha: 2026-09-04
iniciativa: changelog-brief
---

# ADR-012: El resumen del CHANGELOG lo escribe quien cierra la tarea, y el script degrada al título antes que truncar

## Contexto

La skill `changelog-sync` generaba un bullet por tarea con **la primera frase completa** de la
`Descripción` del ledger. Esas descripciones están escritas para el implementador —qué tocar, con
qué criterio, con qué evidencia—, no para quien lee las notas de una release. Medido el 2026-09-04
sobre los **13 ledgers cerrados** de este repo y sus **63 tareas**: la primera frase tenía
**mediana 447 caracteres y máximo 1.944** (37 de 63 por encima de 400), y el bullet completo (título + frase + hasta 5
ficheros) **mediana 660 y máximo 2.163**. Los tres peores: `parity-core/T-01` (1.944),
`memory-health/T-04` (1.502), `superiority/T-06` (1.397). La consecuencia no fue teórica: las notas
de la **v1.16.0 se escribieron a mano** porque la salida del script era inusable, y un generador que
nadie usa es peor que no tenerlo (mismo patrón que `LES-012`: un aviso que se puede ignorar se
ignora).

El dato que decide es que **el material no está**: la información «qué cambia para quien usa esto»
no vive en el ledger en ninguna forma recortable. Cortar la frase por el primer `:`, `;`, `—` o `(`
de nivel superior parecía la salida, pero medido: la mayoría de las `Descripción` de este repo
**empiezan por la ruta del fichero entre acentos graves seguida de `:`**, así que ese corte devuelve
una lista de ficheros (`` `docs/README.md` + `docs/en/README.md` ``), no un resumen — y eso es peor
que el título de la tarea.

## Decisión

El resumen del bullet sale de una **escalera determinista** con el campo explícito arriba, y el
último escalón es el título, nunca un truncado:

1. **`- **Changelog**: <una o dos frases>`** en el bloque `### T-XX` del ledger — campo **OPCIONAL**
   que rellena quien CIERRA la tarea (`implementer` P3, plantilla de tarea, `/dev-cycle`). Si está,
   se usa **tal cual**. Con más de 2 frases el script **avisa diciendo cuántas traía** y usa las dos
   primeras (el tope se mide sobre las frases que `separa_frases()` VE: es tipográfico, no
   semántico); por encima de `RESUMEN_MAX` avisa y lo respeta igual. Nunca falla y nunca recorta a
   media frase lo que escribió una persona. **«Si está» = si está ESCRITO**: un campo vacío, o que
   ES todavía el placeholder `{{…}}` de la plantilla, no cuenta y la escalera sigue bajando. El
   criterio es «el campo ES el placeholder», no «lo menciona»: un `{{…}}` citado —entre acentos
   graves, o dentro de una frase que dice algo más— es texto de una persona y se publica.
2. La **primera frase** de la `Descripción`, si cabe en `RESUMEN_MAX = 200` caracteres.
3. La **oración principal**: lo anterior al primer `:`, `;`, `—` o `(` de nivel superior (fuera de
   `código`, paréntesis y «comillas»), si cabe **y** se lee como una idea completa
   (≥ `CORTE_MIN_PALABRAS = 5` palabras fuera de los tramos entre acentos graves).
4. **Solo el título** de la tarea + `([ledger](docs/roadmap/<fecha>-<slug>/tasks.md))`.

**Ningún camino trunca con `…`.** Los ficheros bajan a `ARCHIVOS_MAX = 3` y el paréntesis
desaparece cuando la tarea toca más de `ARCHIVOS_MAX_TOCADOS = 6` (mostrar 3 de 20 hace creer que
son todos). Todos los topes son constantes del script, elegidos midiendo los 13 ledgers cerrados
—63 tareas— (`skills/changelog-sync/references/medicion-escalera.md`), y **las cifras de esa
medición las imprime el script** (`changelog-sync.py --medicion`), con
`tests/test_cifras_medidas.py` comparando contra ella cada cifra marcada de la doc: una cifra
escrita a mano que deja de reproducir pone la suite en rojo en vez de sobrevivir en la prosa. El campo es opcional **por diseño**:
`ledger-lint.py` lo trata siempre como AVISO y solo en adopción parcial, y el empuje para
escribirlo lo da `changelog-sync.py --check` (aviso que no cambia su exit code).

## Alternativas descartadas

- **Truncar la primera frase a N caracteres con `…`** — es la opción obvia y es deshonesta: corta
  una frase técnica por la mitad («los 27 scripts Python versionados con caracteres no…») y presenta
  como resumen algo que no lo es. Además invita a leer mal el alcance, que es exactamente lo que la
  skill promete no hacer.
- **Resumir la `Descripción` con un modelo** — rompe el determinismo que exige `CONVENTIONS` regla 8
  para todo veredicto/parsing del plugin (mismo texto → misma salida, con test y exit code), no es
  reproducible en la CI y puede inventar alcance: el fallo más caro posible en unas notas de release.
- **Seguir con la primera frase completa** (estado anterior) — medido inusable: mediana 660 y máximo
  2.163 caracteres por bullet, y la prueba es que las notas de la v1.16.0 se redactaron a mano.
- **Quedarse solo con el paso 3 (cortar en el primer delimitador), sin campo nuevo** — medido: en
  este repo rescata **9 de 63** tareas, y sin la puerta de «idea completa» «rescataría» **41**, casi
  todas con una lista de ficheros por resumen (barrido completo de `CORTE_MIN_PALABRAS` en la
  referencia de medición). No hay heurística que saque del ledger una información que el ledger no tiene.
- **Hacer el campo OBLIGATORIO** (error de `ledger-lint`) — rompería los 13 ledgers cerrados
  existentes, que no lo tienen y no se van a reescribir; y convertiría en muro algo que debe
  degradar (`CONVENTIONS` regla 8: la degradación nunca bloquea).
- **Un solo puntero al ledger por subsección en vez de uno por bullet** — más corto en el fichero,
  pero deja bullets sin ninguna referencia y obliga al lector a saber que la cabecera de arriba
  aplica; el enlace por bullet renderiza como una sola palabra («ledger»).

## Consecuencias

Medido sobre los mismos 13 ledgers (63 tareas)<!--m:base_ledgers=13,base_tareas=63-->: el bullet
pasa de **mediana 660 / máximo 2.163**<!--m?:cifra historica: la midio el script de a7a11b0--> a
**mediana 128 / máximo 325** caracteres,<!--m:base_bullet_mediana=128,base_bullet_max=325--> y de
100 de 126 bullets por encima de 400 caracteres a **ninguno**.<!--m:base_bullet_mayores_400=0-->

Ese agregado, solo, engaña, y la revisión de dos lentes lo midió: la mediana de 128 sale de un
corpus donde **42 de 63 bullets son solo el título**,<!--m:base_camino_titulo=42,base_tareas=63-->
o sea del camino que esta decisión quiere EVITAR. Desglose por camino — **atención al corpus**: las
tres primeras filas son los 13 ledgers / 63 tareas de arriba, y la fila `changelog` solo existe con
el ledger de ESTA iniciativa cerrado, así que la tabla completa mide **15 ledgers** y **72
tareas**<!--m:ledgers_cerrados=15,tareas=72--> (la primera versión de este ADR encabezaba con «los
mismos 13 ledgers (63 tareas)» una tabla que sumaba 69: era la misma clase de error que el propio
ADR describe, y por eso las cifras de esta tabla las imprime ahora el script):

| Camino | N | Mediana | Máximo | Corpus |
|---|---|---|---|---|
| `titulo` | 42 | 115 | 168 | la base y el corpus de hoy (igual) |<!--m:camino_titulo=42,titulo_mediana=115,titulo_max=168-->
| `corte` | 9 | 170 | 280 | la base y el corpus de hoy (igual) |<!--m:camino_corte=9,corte_mediana=170,corte_max=280-->
| `frase` | 12 | 260 | 325 | la base y el corpus de hoy (igual) |<!--m:camino_frase=12,frase_mediana=260,frase_max=325-->
| `changelog` (el que se promueve) | 9 | **347** | **400** | solo los ledgers que usan el campo |<!--m:camino_changelog=9,changelog_mediana=347,changelog_max=400-->
| **TOTAL** | **72** | **135** | **400** | el corpus de hoy |<!--m:tareas=72,bullet_mediana=135,bullet_max=400-->

Es decir: **el camino bueno produce los bullets más largos**, y el techo real del bullet completo,
medido con los títulos y las rutas de este repo, es **400 caracteres**<!--m:bullet_max=400-->, no
325. Ninguna de estas cifras se escribe a mano: las imprime `changelog-sync.py --medicion` y
`tests/test_cifras_medidas.py` las compara con esta tabla en cada ejecución de la suite. No cambia la
decisión ni el tope: `RESUMEN_MAX` acota **el resumen**, y el resto lo ponen el título del ledger
(que no se toca) y la lista de ficheros. El `titulo` es corto porque no dice nada; el bullet que
dice algo cuesta caracteres, y eso es el intercambio que esta decisión acepta a sabiendas.
Descomposición del bullet de 325 (`windows-console/T-06`): cabecera con negrita 83 + espacio +
resumen 152 + lista de 3 ficheros 89.

El precio sigue siendo explícito y medible: con los ledgers tal y como están hoy, **42 de 63 tareas
(67 %) degradan al título** — honesto, pero pobre para tareas cuyo título es «Integración, doc,
memoria y cierre». Esa deuda la va cerrando el campo `Changelog:` ledger a ledger, empezando por el
de esta iniciativa, y es visible en `changelog-sync.py --check --json` → **`degradacion.caminos`**,
que recorre TODO ledger cerrado. (Una versión anterior de este ADR decía `pendientes[].caminos`, y
era falso: `pendientes[]` solo lista las iniciativas que FALTAN en el CHANGELOG, así que las ya
publicadas no aparecen ahí nunca. El bloque `degradacion` se añadió para que el dato exista de
verdad, en vez de borrar la frase.) Toda tarea nueva nace con el campo en la plantilla; los ledgers
antiguos validan idéntico a antes.

## Estado

`aceptada` (2026-09-04, tras el intento 1 de la revisión de dos lentes). La revisión encontró un
CRITICAL y dieciséis hallazgos más, y **ninguno cuestiona la decisión**: eran defectos de
implementación del parseo del campo, tests que se parametrizaban con las constantes que debían
fijar, y cifras de documentación que no reproducían. Las seis alternativas descartadas se
re-comprobaron una por una y siguen siendo ciertas después de corregir las consecuencias: truncar
con `…` sigue siendo deshonesto; resumir con modelo sigue rompiendo el determinismo de
`CONVENTIONS` regla 8; la primera frase completa sigue midiendo mediana 660 / máximo 2.163
(re-medido); el paso 3 solo sigue rescatando 9 de 63 (y 41 sin la puerta de «idea completa»); el
campo obligatorio seguiría rompiendo los 13 ledgers cerrados existentes; y el puntero por
subsección sigue dejando bullets sin referencia. Lo único que cambió es lo que este ADR **afirma**
en «Consecuencias», reescrito arriba con las cifras re-medidas. Pasa a `obsoleta` si una decisión
posterior la reemplaza (enlaza aquí a la que la sustituye, nunca se borra el rastro).
