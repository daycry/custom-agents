# Captación, logística, mercado, campañas y acuerdos marco — S161, S165, S170–S172

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **49.957 bytes/980 líneas** y los recursos de S161
(cuatro agentes, 9.961 bytes/318 líneas) y S172 (plantilla, spec de ejemplo y
`scripts/build-agreement.js`, 14.313 bytes/327 líneas).
[leads-logistics-research-agreements-reading-evidence.json](leads-logistics-research-agreements-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Cinco dominios de negocio sin rol en el ciclo de desarrollo, como S092–S093 y
S137–S138: **fuera del bundle**, persona de proyecto si un consumidor la
necesita. Se extraen solo las ideas generales que tocan a piezas propias.

## S161 — Inteligencia de contactos y captación

`13.111 bytes/333 líneas` más cuatro agentes (puntuador de señales, mapa de
contactos mutuos, enriquecimiento y redactor). Puntúa perfiles por pesos,
busca caminos de presentación, enriquece datos y redacta mensajes por canal.

**Comparación.** Su sección de contenido no confiable es de las más claras del
corpus y coincide con lo ya propuesto para Jira (S146), GitHub (S115) y correo
(S092): el contenido no elige destinatario ni canal, la voz se toma de las
muestras pero nunca sus instrucciones, nada se envía sin aprobación. Defectos:

| Punto | Problema |
|---|---|
| Puntuaciones 0–100 con pesos (30 %, 25 %…) | Juicio del modelo presentado como medida; no es un veredicto |
| «Nunca abras enlaces de un perfil» | El agente de enriquecimiento tiene `WebFetch` y su tarea es leer webs personales enlazadas desde los perfiles |
| Exige credenciales de escritura de X aunque nunca envía | Acceso mayor del necesario |
| `LINKEDIN_COOKIE` en variable de entorno | Credencial de sesión personal fuera de cualquier gestor |
| Recogida de ubicación, empleo y actividad de terceros | Datos personales sin base ni retención declaradas |
| «Mutuo directo» en `mutual-mapper` | Se define como alguien a quien siguen ambos, el algoritmo acepta cualquier relación en cualquier sentido y el ejemplo describe a alguien que sigue a ambos |
| Fórmula `B(m)`/`R(m)` | Símbolos sin definir (`w`, `λ`, `d`, `β`, `B_ext`) |
| Bloque «Output Format» | Un párrafo de instrucciones quedó dentro del bloque de ejemplo |

## S165 — Gestión de incidencias logísticas

`16.818 bytes/216 líneas`. Taxonomía de incidencias, comportamiento por modo de
transporte, plazos de reclamación, severidad, «asumir o reclamar», escalado,
plantillas e indicadores.

**Comparación.** La idea general —severidad como el máximo de varios ejes, con
elevaciones por cliente y por urgencia— ya la resuelve el plugin a su manera
(Critical/Important/Minor en la revisión). Defectos: cifras y plazos legales de
EE. UU. y de convenios internacionales sin fecha de contraste; porcentajes
(«~40 % de las incidencias», «+30–50 % en temporada alta») sin fuente; el rol se
define por una experiencia afirmada («15+ años»), no por criterios verificables.

## S170 — Investigación de mercado

`3.185 bytes/87 líneas`. Fuentes por afirmación, datos recientes, evidencia
contraria, hecho/inferencia/recomendación separados, fuentes no confiables y
modos de inversores, competencia, tamaño de mercado y tecnología.

**Comparación.** Solapa con `research-first` (adoptar, adaptar o construir) y
con la guía de investigación con evidencia propuesta por S072, que ya separa
hecho, declaración ajena, inferencia y estimación e impide que una página cambie
alcance o destino. Sus cinco reglas de fuentes no confiables coinciden en lo
esencial con S072. Corrección: «prefiere datos recientes» como regla general contradice lo
fijado en S072 (una fuente primaria antigua puede ser la correcta). Los modos de
inversores y tamaño de mercado son de negocio. **Sin destino nuevo.**

## S171 — Campañas de marketing

`5.293 bytes/114 líneas`. Investigación, posicionamiento, producción por capas
(landing, correos, redes, guiones, anuncios, calendario), revisión y prohibiciones.

**Comparación.** La regla «lo que promete el anuncio coincide exactamente con la
landing» es la misma disciplina que el ledger canónico frente a sus espejos.
Defectos: prohíbe la urgencia falsa y a la vez prescribe un correo de urgencia en
toda secuencia; fija cantidades (3+ publicaciones, 5+ posts, 2+ guiones) sin
relación con la campaña; depende de piezas que no están en el plugin
(`brand-voice`, `content-engine`, `crosspost`, `seo`), de las que solo el perfil
de voz tiene ficha (S029).

## S172 — Generador de acuerdos marco

`11.550 bytes/230 líneas` más plantilla, spec y script. Una plantilla con
marcadores, un JSON por contraparte, cláusulas por rol, salida siempre marcada
como borrador y un flujo para añadir entradas al anexo A solo dentro de la
autoridad del acuerdo firmado.

**Comparación.** El script es cuidadoso: valida el nombre de fichero para
cualquier sistema, rechaza celdas malformadas antes de escribir, codifica las
celdas del anexo, comprueba enlaces simbólicos en ambos destinos y acota pandoc
a diez segundos. Dos ideas tocan a piezas propias:

| Idea | Encaje |
|---|---|
| «Una conversión correcta prueba el artefacto, no la autorización para enviarlo» | Ya es el criterio de aprobación ligada de S096 y la separación qa-gate/publicación |
| Antes de regenerar se borra el DOCX derivado, y una conversión fallida no deja copia parcial, para que un artefacto viejo no pase por el actual | `skills/to-pdf/scripts/to-pdf.mjs` escribe directamente en `--out`; si la conversión falla, un PDF anterior con el mismo nombre queda junto a una fuente nueva. Propuesta: escribir a un temporal y renombrar al terminar, y retirar o marcar la salida previa si falla |

La política contraria es correcta en otro contexto: `knowledge-services` conserva
la publicación anterior si `apply()` falla, porque es la última versión buena de
un destino. La diferencia es si el artefacto se presenta como derivado de la
fuente actual.

Defectos: la fecha por defecto es la del día de la ejecución en la zona horaria
local, lo que contradice «reproducible desde la fuente versionada»; `date` no
se valida; los demás campos de la spec se insertan sin codificar (la pieza lo
reconoce como «capaz de marcado»).

**Destino S161–S172:** fuera del bundle. Única propuesta propia: la escritura
atómica de `to-pdf` (T-08 decide si retirar o marcar la salida previa).
