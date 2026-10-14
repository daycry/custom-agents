# Baselines de rendimiento

Léela solo cuando la comparación mida **rendimiento** (latencia de una API, Web Vitals, tiempo de
build, frescura de datos) antes y después de un cambio. Cómo localizar el coste en la interfaz está en
`skills/frontend-quality/references/interaction-performance.md`; aquí, cómo fijar y registrar la
medida para que el antes y el después sean comparables. Medir no acredita corrección: `qa` conserva
el veredicto.

## Fijar antes de medir

| Qué | Ejemplo de valor declarado |
|---|---|
| Métrica, unidad y dirección | p95 de latencia en ms, menos es mejor |
| Muestra y ventana | n = 2.000 peticiones en 10 min, tras 200 de calentamiento descartadas |
| Entorno | Host local o de pruebas autorizado, versión del código (SHA), versión del runtime |
| Estado | Caché fría o caliente, datos del fixture, compresión activada o no |
| Cliente | Dispositivo o CPU, red emulada, navegador y versión |
| Carga | Concurrencia, ritmo de llegada, mezcla de endpoints |
| Comando | El que produce la cifra, ejecutable tal cual |

Si algo de esto cambia entre baseline y variante, el delta no es comparable: dilo y no lo publiques
como mejora. Los límites de un gate (peso, latencia) los fija el producto para su dispositivo y red
objetivo; una cifra de otro proyecto no es política.

## Percentiles con muestra y ventana

Publica siempre n y ventana junto al percentil. Por encima del pXX quedan n·(100−XX)/100
observaciones: con 100 muestras, el p99 se apoya en **una**. Si son tan pocas, ese percentil es
ruido; sube n o publica solo los percentiles que la muestra sostiene. Repite baseline y variante
alternando el orden y compara distribuciones, no un único número.

Los errores se cuentan aparte: una respuesta 500 rápida no mejora la latencia. Publica la
distribución de códigos de estado junto a los percentiles.

## Campo frente a laboratorio

| | Campo (usuarios reales) | Laboratorio (entorno controlado) |
|---|---|---|
| Sirve para | Afirmar que se cumple un objetivo de Web Vitals | Comparar baseline y variante en condiciones fijas |
| Web Vitals | LCP ≤ 2,5 s, INP ≤ 200 ms y CLS ≤ 0,1 en el **percentil 75**, por separado en móvil y escritorio | LCP y CLS medibles; INP no (no hay interacción real): TBT es su sustituto de laboratorio |
| Límite | Necesita tráfico y recogida autorizada | No demuestra el cumplimiento en campo |

Una mejora de TBT en laboratorio puede trasladarse a INP en campo, pero no lo prueba. Etiqueta cada
cifra con su origen; no mezcles campo y laboratorio en una misma serie.

## Frescura como métrica propia

En datos servidos desde caché, réplica o cola, la **edad del dato** (ahora − momento en que se
produjo) se mide aparte de la latencia: una respuesta rápida puede servir un dato viejo. La caché
devuelve la edad junto al valor, para que un acierto de caché no oculte datos rancios; publica p50 y
p95 de edad igual que los de latencia.

## Camino caliente por segmentos

Antes de elegir dónde optimizar, mide cada tramo del camino que recorre la petición (por ejemplo:
evento → API → cola → caché → cliente → render) con la misma muestra. Optimiza el tramo que domina
la medida; ningún orden fijo de optimización sustituye a esa medición. Si un tramo no se puede
instrumentar, queda `null` con motivo y la conclusión se limita a los tramos medidos.

## Builds

Para tiempos de build y de herramientas: build en frío y en caliente por separado, recarga en
caliente, suite de tests, comprobación de tipos y lint, y tamaño de imagen o bundle con su
compresión. Cada uno con n repeticiones y la caché declarada.

## Registro

Una entrada por medición, junto a los runs del [protocolo](protocol.md):

```json
{"metrica": "latencia_p95_ms", "valor": 182, "n": 2000, "ventana": "10m",
 "origen": "laboratorio", "revision": "<sha>", "condiciones": "<id de condiciones>",
 "comando": "<comando literal>", "motivo_null": null}
```

Una métrica no obtenida es `"valor": null` con `motivo_null` («sin datos de campo», «INP no medible
en laboratorio»), nunca 0. Las URLs y hosts privados se redactan antes de guardar.

## Seguridad de la medición

La carga solo contra hosts locales o entornos de prueba autorizados, con identidad y límites
acordados, y con limpieza si muta datos. Medir sobre producción exige autorización expresa y
vigente; la guía no la concede.

## Fuentes

- Web Vitals, umbrales, percentil 75 por dispositivo, INP y TBT en laboratorio:
  [web.dev/articles/vitals](https://web.dev/articles/vitals), consultada el 2026-10-14.
