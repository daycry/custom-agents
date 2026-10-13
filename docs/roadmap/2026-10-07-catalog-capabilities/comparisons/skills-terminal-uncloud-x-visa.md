# Lanzador de terminal, clúster Uncloud, traducción de documentos de visado y API de X — S276, S282, S288, S293

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **23.412 bytes/760 líneas** y los tres recursos locales
leídos completos (lanzador `open-terminal.js`, `agents/openai.yaml` de S276 y
`README.md` de S288): **13.986 bytes/486 líneas**.
[terminal-uncloud-x-visa-reading-evidence.json](terminal-uncloud-x-visa-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## S276 — Abrir un comando en una terminal visible

`2.539 bytes/55 líneas` más el lanzador (11.931 bytes). Ejecutable y argumentos
como entradas separadas, sin shell; por defecto solo imprime el plan; `--launch`
explícito; detección de WezTerm y modo de recuperación sin configuración.

**Comparación.** Ningún rol del plugin abre ventanas de terminal. El principio
ya rige en el plugin: pasar opciones y valores como argumentos separados, sin
interpolar texto del usuario en shell ([WORK-RESUME](../../../WORK-RESUME.md)).
La pieza declara bien que el proceso hereda **todo** el entorno, secretos
incluidos. Defecto real del lanzador: el camino normal ejecuta
`wezterm cli spawn` con un tope de 10 s y, si vence (`ETIMEDOUT`), lanza el
respaldo `wezterm start` con el mismo comando. Si la primera llamada llegó a
abrir la ventana, el comando (una sesión SSH, un proceso de desarrollo) se
ejecuta **dos veces**. Es el caso «tiempo de espera después de aceptar la
operación» de `backend-practices/references/contracts-data.md`: tras un fallo
ambiguo, comprobar antes de repetir. **Sin destino.**

## S282 — Gestión de un clúster Uncloud

`9.282 bytes/344 líneas`. Referencia del CLI `uc`: máquinas en malla WireGuard,
servicios desde Compose, Caddy como proxy de entrada, publicación de puertos,
escalado, volúmenes y DNS interno.

**Comparación.** Herramienta concreta de despliegue autoalojado; ningún
consumidor la declara. `delivery-practices` ya fija artefacto inmutable,
build frente a runtime, readiness y rollback. **Fuera del bundle.** Correcciones
si algún consumidor la adopta:

| Ejemplo | Corrección |
|---|---|
| `tls_insecure_skip_verify` como arreglo para un upstream con certificado propio | Desactiva la verificación; confiar en la CA concreta del dispositivo |
| Publicar la interfaz de un BMC o un NAS por HTTPS con DNS comodín | Interfaces de gestión fuera de Internet; acceso por la malla privada |
| `-p 5432:5432@host` («todas las interfaces») para una base de datos | Publicar en `127.0.0.1` o no publicar, como ya se corrigió en S084 |
| `nginx:latest`, `app:latest` | Etiqueta o digest fijo (artefacto inmutable) |
| `uc exec web /bin/sh -c "env"` como inspección | Vuelca secretos del entorno en la salida y el historial |

## S288 — Traducción de documentos de visado

`4.153 bytes/117 líneas` más `README.md` (1.836 bytes). OCR de certificados
bancarios, laborales, de identidad y pasaportes, traducción al inglés y PDF
bilingüe, «sin pedir confirmación».

**Comparación.** Dominio ajeno al ciclo. `to-pdf` convierte Markdown, HTML y
Word, pero no hay rol que traduzca documentos personales. **Fuera del bundle.**
Riesgos que la descartan incluso como extensión sin revisar:

- Procesa pasaportes, extractos bancarios y documentos de identidad **sin
  confirmación** en ningún paso: datos personales sensibles sin consentimiento
  explícito ni indicación de dónde se ejecuta el OCR.
- Añade al PDF «This is a certified English translation». Una traducción por
  modelo no está certificada; presentarla así en un trámite oficial es una
  declaración falsa.
- «Si la orientación EXIF es 6, girar 90° en sentido antihorario»: la
  orientación 6 se corrige con un giro horario de 90°. Usar la transposición
  EXIF de la librería en vez de reglas manuales.
- Conversión HEIC con `sips`, exclusiva de macOS, presentada como paso general.

## S293 — API de X

`7.438 bytes/244 líneas`. Autenticación, publicación de posts e hilos, lectura de
timelines, búsqueda, subida de medios y límites de uso. Se declara propensa a
quedar obsoleta.

**Comparación.** Red social; ningún rol del plugin publica. **Fuera del bundle.**
Su sección «el contenido del timeline no es confiable» (no seguir instrucciones
de un post, lo leído nunca dispara una escritura, no abrir enlaces de posts,
citar literalmente) es la misma regla ya propuesta para GitHub (S115), Jira
(S146) y correo (S092); no añade matiz nuevo. Defectos:

- `post_thread` no comprueba el estado de cada respuesta: un error a mitad deja
  un hilo parcial y un reintento duplica los posts ya publicados (falta clave de
  idempotencia o reanudación desde el último ID).
- `int(resp.headers.get("x-rate-limit-remaining", 0))`: sin cabecera, el valor
  por defecto 0 dispara siempre el aviso de límite.
- Los ejemplos de «modelado de voz» descargan los posts de una persona concreta
  identificada por su cuenta: datos personales y suplantación de estilo.
- La subida de medios usa un endpoint v1.1 que necesita contraste con la
  documentación vigente antes de cualquier uso.

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S276 | Principio ya vigente; reintento duplicado en el lanzador | — |
| S282 | Herramienta de despliegue sin consumidor | Fuera del bundle |
| S288 | Datos personales sin consentimiento y «certificación» falsa | Fuera del bundle |
| S293 | Red social; regla de contenido no confiable ya propuesta | Fuera del bundle |

Contraste oficial pendiente: endpoint de subida de medios de X y directivas de
confianza de Caddy, solo si un consumidor declara esas herramientas.
