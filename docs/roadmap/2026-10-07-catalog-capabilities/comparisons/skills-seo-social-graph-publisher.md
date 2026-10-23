# SEO, ranking de contactos y publicación en redes — S254, S258, S259

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **12.996 bytes/449 líneas**, sin recursos locales.
[seo-social-graph-publisher-reading-evidence.json](seo-social-graph-publisher-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio ni red social. Propuestas para T-08.

## Decisión común

Marketing, prospección y publicación en redes: dominio ajeno al ciclo de
desarrollo. **Fuera del bundle**; «persona de proyecto» si un consumidor lo
necesita, consumiendo el perfil de voz propuesto en
[skills-brand-browser-runtime.md](skills-brand-browser-runtime.md). Dos ideas
generales ya tienen dueño y se anotan abajo.

## S254 — SEO

`4.320 bytes/155 líneas`. Rastreo e indexación, Core Web Vitals, datos
estructurados, títulos y descripciones, mapa de palabras clave y enlazado interno.

**Comparación.** La parte técnica que toca al código (rendimiento de carga,
reservar espacio para medios) ya está en `frontend-quality`, que exige medir un
escenario reproducible y declarar presupuestos con el producto y el dispositivo
objetivo; la pieza da LCP < 2,5 s, INP < 200 ms y CLS < 0,1 como umbrales sin
decir sobre qué datos ni en qué percentil se miden, justo lo que
`frontend-quality` pide no imponer como universal. Sus reglas «no marcar
datos estructurados para contenido que no está en la página» y «leer la página
real antes de recomendar» son correctas pero de dominio. Las longitudes de título
(50–60) y descripción (120–160) son orientativas, no requisitos. **Fuera del
bundle.**

## S258 — Ranking de contactos para presentaciones

`4.156 bytes/155 líneas`. Puntúa contactos de X y LinkedIn por su valor como
puente hacia una lista de objetivos, con decaimiento por saltos y bonificación
por respuesta.

**Comparación.** Sin pieza propia equivalente ni consumidor. Trata grafos de
contactos de personas: datos personales que el plugin no versiona. Defectos del
modelo: el término directo usa `λ^(d−1)` y la expansión de segundo orden
`λ^d` sin justificar el cambio de exponente; la expansión puede contar dos veces
un objetivo ya alcanzado por el contacto directo; las constantes «habituales»
(λ = 0,5, α = 0,3, β = 0,2) no tienen procedencia; y el bloque de texto
muestra `N(m) \\ M` con la barra duplicada. **Fuera del bundle.**

## S259 — Publicación en redes sociales

`4.520 bytes/139 líneas`. Programa y publica en trece plataformas mediante un
servicio externo con clave de espacio de trabajo: cuentas, subida de medios,
`schedule.json`, validación, publicación y seguimiento.

**Comparación.** Publicar es un efecto externo irreversible; el flujo pasa de
`validate` a `apply` sin una confirmación explícita del usuario, que el plugin
exige (`delivery-practices`: preparar una entrega no autoriza publicarla).
Contradicción interna: verifica la clave por entrada estándar con `curl -K -`
y acto seguido recomienda `socialclaw login --api-key <clave>` en la línea de
comandos (historial). Además recomienda instalar un plugin de terceros fijado
para recoger «evidencia» de X. Su sección «el contenido recuperado no es
confiable» (no dejar que un estado o un error del proveedor decida qué, dónde o
cuándo publicar, ni amplíe el alcance) coincide con la sección propuesta para
`delivery-practices` en S115 y con la de `jira-sync` en S146.

**Fuera del bundle**; la regla de contenido no confiable refuerza S115/S146 sin
añadir destino nuevo.
