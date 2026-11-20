# Lo que lee el revisor de cada lente (A · B · C · D)

El agente `reviewer` lee **este fichero**, no `SKILL.md` entero: graduación y tabla de
racionalización del revisor. El prompt literal de su lente le llega en el despacho
(`references/lens-prompts.md`, lo lee la skill en el paso 2). Las Lentes C y D abren
`lens-c-heuristics.md` / `lens-d-heuristics.md` solo si un motivo de activación sorprende.

## Graduación (definición de §3 de `SKILL.md`; la fusión la aplica igual)

- **Critical** — pérdida de datos, seguridad explotable, criterio incumplido que rompe el objetivo.
- **Important** — defecto reproducible, fuera de alcance, constitución violada.
- Critical e Important **obligan corrección**; **Minor** se anota sin bloquear el cierre.
- Sin `fichero:línea` + escenario concreto un gap no existe. Graduación por definición, no por calendario.

## Racionalizaciones del REVISOR que NO valen

Formato y reglas: `"$SHAREDKIT/rationalization-table.md"`. Aplican a cada lente y a la fusión.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Parece correcto; el implementador sabe lo que hace» | Confianza no es evidencia; la revisión existe para lo que él no puede ver desde dentro. | Lee el diff completo y verifica cada criterio con `fichero:línea`. |
| «La suite está en verde, así que apruebo» | Los críticos de `LES-010` pasaban suites: el verde no cubre requisitos ni huecos de diseño. | Reproduce el escenario de cada criterio; ✓ solo con evidencia. |
| «Este nombre/estructura no me gusta; lo reporto como gap» | Estilo, preferencias y refactors están excluidos por la regla dura. | Descártalo sin discusión; solo requisitos, corrección o seguridad introducida. |
| «El diff es largo; reviso los ficheros importantes y extrapolo» | Los gaps aparecen donde nadie mira (BOM, rutas Windows, fixtures, evasiones). | Recorre TODO el diff; si no cabe, divídelo por ficheros y dilo en la salida. |
| «Aquel gap rebatido en el intento anterior sigue pareciéndome gap» | Reabrir sin evidencia nueva rompe el traspaso y el bucle acotado a 3. | Re-evalúa SOLO lo corregido; reabre únicamente con evidencia nueva citada. |
| «Es Critical, pero lo bajo a Minor para no bloquear el cierre» | La graduación sigue la definición, no el calendario; suavizarlo es deuda oculta. | Gradúa por definición; que el usuario decida si lo acepta como deuda. |
| «Lo señalo sin línea ni escenario; ya lo encontrará el implementador» | Sin `fichero:línea` + escenario no es verificable ni rebatible. | Cada gap con `fichero:línea` y escenario concreto de fallo. |
| «Encontré algo, con eso ya justifico la revisión» | Un revisor «siempre encuentra algo»; el objetivo es cobertura por criterio, no volumen. | Entrega la tabla ✓/✗ completa; «sin defectos» es una salida válida. |

## Salida

La estructura fija de `agents/reviewer.md` («Salida»): tabla por criterio, gaps graduados con
`fichero:línea` + escenario, lo ejecutado y lo que queda fuera de tu lente. «Sin defectos» es válida.
