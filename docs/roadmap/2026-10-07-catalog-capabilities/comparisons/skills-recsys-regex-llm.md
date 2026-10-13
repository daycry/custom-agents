# Canalizaciones de recomendación y extracción híbrida regex/LLM — S232 y S235

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Dos cuerpos completos: **14.537 bytes/336 líneas**, sin recursos locales.
[recsys-regex-llm-reading-evidence.json](recsys-regex-llm-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S232 — Arquitectura de canalizaciones de recomendación

`7.788 bytes/115 líneas`. Seis etapas (origen, enriquecimiento, filtro,
puntuación, selección y efectos secundarios) para «los K mejores elementos para
un usuario y contexto», ocho pasos guiados y compromisos a explicitar
(puntuación única o multiacción, aislada o conjunta, en línea o por lotes).

**Comparación.** Dominio de producto (feeds, ranking) sin rol del ciclo que lo
necesite; `architect` ya compara opciones con sus compromisos cuando una
iniciativa lo pida. **Fuera del bundle.** Defectos si alguien lo usa como
persona de proyecto:

- Promete «el andamiaje generado debe ejecutarse», pero los andamios y las
  referencias solo existen en el repositorio original y se instalan con un
  comando externo.
- «Seleccionar después de puntuar mantiene la puntuación determinista y
  cacheable»: el orden de etapas no hace determinista la puntuación.
- Efectos secundarios «disparar y olvidar» (promesas sin `await`, goroutines):
  los errores se pierden, no hay límite de concurrencia, y el filtro «ya
  servido» depende de un efecto que nadie espera, así que la petición siguiente
  puede repetir elementos.
- Presupuesto de latencia «100–300 ms» como valor por defecto sin fuente, pese a
  su propia regla de no inventar cifras.
- Disparadores muy amplios («priorizador de tareas», «reordenador RAG»).

## S235 — Regex primero, LLM solo para los casos dudosos

`6.749 bytes/221 líneas`. Extracción con regex, puntuación de confianza y
validación con un modelo barato solo para lo marcado; métricas de un caso real.

**Comparación.** Es el mismo principio que aplica el plugin: `journal.py` extrae
decisiones y pendientes **sin modelo** y el resumen por IA es opcional y degrada
(ADR-010 revisada); `outcome-evals` mide resultados con corpus. La pieza
contiene el defecto que ese principio debe evitar:

| Ejemplo | Adaptación |
|---|---|
| El puntuador solo ve lo que la regex capturó | Lo que la regex no reconoce desaparece en silencio: el «98 % de éxito» no se puede medir así. Contar las unidades esperadas por una vía independiente (p. ej. encabezados numerados) y tratar la diferencia como fallo |
| Comprobación `missing_answer` | Inalcanzable: la propia regex exige la respuesta para casar |
| `validate_with_llm` devuelve `corrected_item`, que no existe | No ejecutable; además envía el documento completo en cada llamada, contra el ahorro que persigue, y mete texto externo en el prompt sin tratarlo como dato |
| «8 elementos marcados, ~5 llamadas» | El código hace una llamada por elemento marcado; cifras sin fuente |
| Identificador de modelo fijo en el código | Configurable; los modelos cambian |

**Destino:** una línea en el protocolo de `outcome-evals`: en extracción
determinista, el silencio del extractor no es éxito; contar lo esperado por una
vía independiente. El resto, **sin destino**.
