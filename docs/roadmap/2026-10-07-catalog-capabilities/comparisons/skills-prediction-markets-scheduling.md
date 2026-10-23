# Mercados de predicción y planificación de producción — S209, S210, S215

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **32.730 bytes/356 líneas**, sin recursos locales.
[prediction-markets-scheduling-reading-evidence.json](prediction-markets-scheduling-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Son dominios de negocio ajenos al ciclo de desarrollo: señales de mercados de
predicción y planificación de fabricación. **Fuera del bundle.** Si un
consumidor los necesita, se tratan como persona de proyecto.

## S209 — Mercados de predicción como fuente de datos

`2.306 bytes/64 líneas`. Investiga si las probabilidades implícitas de un mercado
sirven como señal para un producto, un agente o un panel: decisión que informa,
fuentes con hora y enlace, calidad de la señal (liquidez, diferencial, antigüedad,
autoridad de resolución) y comparación con fuentes ajenas al mercado.

**Comparación.** Lo general ya tiene sitio. Las fuentes con fecha y la
comparación de adoptar frente a construir son de `research-first`, y la fecha de
la fuente separada de la de recuperación quedó anotada con la familia Itô
([skills-ito-family.md](skills-ito-family.md), S141). Remite a
`llm-trading-agent-security`, fuera de este rango, antes de conceder escritura.
Su `description` repite dos veces la cláusula de uso.

**Fuera del bundle.**

## S210 — Revisión de riesgos de flujos con mercados de predicción

`1.882 bytes/61 líneas`. Puertas de revisión antes de que un flujo toque
autenticación en la plataforma, datos de cartera o ejecución: frontera de
asesoramiento, restricciones regulatorias, calidad de datos, seguridad y
privacidad, con hallazgos pasa/aviso/falla y acciones bloqueadas.

**Comparación.** Nombra `ITO_API_KEY` y «datos con acceso de Itô»: es parte de la
misma familia de proveedor que S141–S144. Las reglas generales ya están
recogidas: permisos mínimos y respuestas sin autoridad en `delivery-practices`,
y autoridad explícita antes de una operación con efecto, anotada con S142.

**Fuera del bundle.**

## S215 — Planificación de producción

`28.542 bytes/231 líneas`. Persona de planificador sénior de fabricación:
secuenciación de órdenes, cuello de botella (tambor-amortiguador-cuerda), SMED,
OEE, respuesta a interrupciones, turnos, interacción ERP/MES, escalados e
indicadores.

**Comparación.** Sin relación con el ciclo de desarrollo. Dos ideas se parecen a
reglas que el plugin ya tiene. La **ventana congelada** (no resecuenciar lo que
ya está en curso) se parece a no reabrir tareas `en-progreso` del ledger sin
motivo. Y un plan que diverge de la realidad deja de usarse, que es la razón del
ledger canónico y de la medición real frente a la estimada en `/retro`. No hay
nada que adoptar.

| La pieza | Problema |
|---|---|
| «Mejora con intercambios 2-opt: intercambia pares de trabajos adyacentes» | Eso es un intercambio de vecinos; 2-opt invierte un tramo entre dos posiciones no adyacentes |
| «Pasar de 2 a 4 operarios certificados cambia la pérdida esperada en más de 200.000 $/año» | La cifra no muestra sus supuestos más allá de dos datos de entrada |
| Persona fija con nombres de productos ERP, APS y MES concretos | Persona de proyecto, no guía reutilizable |
| `metadata.clawdbot.emoji: ""` | Metadato de otro runtime, vacío |

**Fuera del bundle.**
