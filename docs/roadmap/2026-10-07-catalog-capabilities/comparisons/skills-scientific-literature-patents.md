# Literatura científica, patentes y genómica — S245–S249

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **26.354 bytes/875 líneas**, sin recursos locales.
[scientific-literature-patents-reading-evidence.json](scientific-literature-patents-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Las cinco piezas sirven a la investigación académica, biomédica o de propiedad
industrial (PubMed, USPTO, `gget`, revisión de literatura y evaluación de
artículos). Ningún rol del ciclo de desarrollo las necesita: **Fuera del
bundle**; «persona de proyecto» si un consumidor trabaja en ese dominio.

Lo reutilizable es la **disciplina de búsqueda reproducible**, que encaja en
`research-first` (dueño de comparar fuentes antes de decidir, ADR-011) sin
crear otra skill:

| Idea de la fuente | Encaje en research-first |
|---|---|
| Registro por pasada: consulta exacta, fuente, fecha, filtros, nº de resultados y exclusiones manuales (S245, S246, S248) | Una columna «consulta y fecha» en `references/comparison.md`, junto a la fecha de consulta que ya exige |
| Separar **hechos del registro oficial**, análisis inferido, coincidencias de fuentes secundarias y huecos sin resolver (S246) | Refuerza «separa código inspeccionado, pruebas ejecutadas y promesas del proveedor» |
| No citar una fuente para una afirmación que no hace; marcar preprints y revisiones como tales (S248, S249) | Una línea en la tabla de sesgos: «la fuente lo dice» exige localizar la frase |
| Una sola base de datos no sostiene una afirmación amplia salvo alcance declarado (S248) | Ya cubierto por «un canal sin acceso no es una búsqueda vacía»; añadir el caso de canal único |
| Deduplicar por identificador estable antes que por título (S248) | Útil solo si research-first agrega muchas fuentes; sin destino hoy |

## S245 — PubMed y E-utilities

`4.827 bytes/176 líneas`. Construcción de consultas con MeSH y etiquetas de
campo, filtros, flujo `esearch`/`esummary`/`efetch`/`elink`, claves en el
entorno y registro de búsqueda.

**Comparación.** Sin pieza propia equivalente. El ejemplo Python llama a
`raise_for_status()` y luego indexa `["esearchresult"]["idlist"]` sin manejar
una respuesta de error con cuerpo JSON distinto; el `time.sleep(0.35)` va
después de la petición y no limita nada si se paraleliza. El checklist pide
manejar los no-200 «antes de parsear», y el ejemplo lo cumple solo a medias.
**Fuera del bundle.**

## S246 — USPTO

`6.331 bytes/178 líneas`. Selección de fuentes oficiales, PatentSearch, TSDR,
historial de tramitación y cesiones, con registro reproducible y escalado a
revisión legal.

**Comparación.** Aporta la separación oficial/secundaria de la tabla común y
una regla sana: «verifica nombres de endpoint y campos en la documentación
viva antes de reutilizar la consulta», que coincide con «comprueba flags/APIs
en la documentación oficial» de `capability-audit`. El ejemplo usa
`os.environ["PATENTSVIEW_API_KEY"]` (falla con `KeyError` sin mensaje útil) y
fija la URL base de una API que la propia pieza dice que migra. **Fuera del
bundle.**

## S247 — `gget`

`5.089 bytes/167 líneas`. Consultas rápidas a bases genómicas con registro de
versión, módulo, especie y salida.

**Comparación.** Paquete de un dominio científico concreto. Los pasos de
instalación usan `. .venv/bin/activate`, que no existe en Windows (allí es
`.venv\Scripts\activate`); el plugin exige rutas y comandos que funcionen en
ambos. La advertencia «la salida es de la base de datos, no interpretación
clínica» es buena pero propia del dominio. **Fuera del bundle.**

## S248 — Revisión de literatura

`5.201 bytes/193 líneas`. Tipos de revisión, pregunta PICO o su análogo
técnico, protocolo previo, registro, deduplicación, cribado por etapas,
extracción, síntesis por temas con niveles de confianza y verificación de citas.

**Comparación.** Es el método más cercano a `research-first`, pero orientado a
un informe académico, no a decidir adoptar/adaptar/construir. De ella salen las
ideas de la tabla común. Los niveles «alta/media/baja confianza» son juicios
del modelo: en el plugin acompañan a la evidencia, no la sustituyen.
**Fuera del bundle**; ideas a `research-first`.

## S249 — Evaluación de trabajos académicos

`4.906 bytes/161 líneas`. Rúbrica de nueve dimensiones puntuadas de 1 a 5 con
plantilla de informe.

**Comparación.** La propia pieza advierte que la nota no sustituye al
comentario concreto, y aun así la plantilla abre con «Overall score». En el
plugin una puntuación del modelo no es un veredicto (veredictos en scripts
deterministas); la revisión de artefactos propios ya la hacen `adversarial-review`
y `capability-audit` con evidencia por criterio. **Fuera del bundle.**
