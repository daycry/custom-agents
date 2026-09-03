---
id: ADR-008
titulo: SKILL.md corto (≤ 200 líneas) + references/ con lectura bajo demanda
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fecha: 2026-09-03
iniciativa: plan-and-diet
---

# ADR-008: SKILL.md corto (≤ 200 líneas) + `references/` con lectura bajo demanda

## Contexto

Un `skills/<skill>/SKILL.md` se inyecta **completo** en el contexto cada vez que la skill se invoca (y, si
un agente la precarga en `skills:`, en cada arranque de ese agente). Tres skills habían crecido hasta
289 (`jira-sync`), 432 (`confluence-publish`) y 976 (`cybersecurity`) líneas porque acumulaban en el mismo
fichero el flujo y toda su casuística: plantillas de comentario, la política del tope de jornada, tablas
de campos de config, la política normativa de publicación, los 8 prompts de especialistas, catálogos
OWASP/CWE/ATT&CK y la estrategia de codebase grande. Esa casuística solo hace falta en un paso concreto,
pero se pagaba entera en cada invocación (≈15k tokens solo por `jira-sync` + `confluence-publish`, medido
en `2026-08-10-token-diet`). El plugin superpowers resuelve lo mismo con «progressive disclosure»: el
`SKILL.md` es el mapa y el detalle vive en ficheros que se leen al llegar al paso que los cita.

## Decisión

Todo `SKILL.md` es el **mapa** de la skill — frontmatter, propósito, disparadores, el flujo de pasos con
1-3 líneas por paso, guardrails/invariantes, «qué NO hace» y una **tabla de referencias** — y mide
**≤ 200 líneas** (aviso del linter, `SKILL_WARN_LINES`) con **250** como umbral duro
(`tests/test_skill_size.py` falla). El detalle vive en `skills/<skill>/references/<tema>.md`, enlazado
desde el paso que lo usa con la instrucción explícita «lee X **solo** cuando llegues al paso Y». Al
adelgazar una skill existente se exige **cero pérdida de contenido** (cada bloque movido reaparece literal
en una referencia: `tests/test_skill_size.py --diet-check <skill> <git-ref>` → `0 párrafos perdidos`) y se
conservan los nombres de paso que citan otras piezas (`Paso 7`, `Paso 9`, `Paso 0-ter`…). Regla escrita en
`docs/CONVENTIONS.md` §3 («Skills cortas») y en `skills/plugin-dev/SKILL.md` Paso 2.

## Alternativas descartadas

- **Todo en el `SKILL.md`** (estado anterior) — cada invocación paga la casuística de todos los pasos
  aunque solo se ejecute uno; el coste crece con cada iniciativa que añade un caso; a partir de cierto
  tamaño el modelo pierde el flujo entre el detalle.
- **Umbral solo en el linter, sin test duro** — un aviso se ignora; con tres skills ya por encima de 280
  líneas hacía falta una puerta que rompa el build a partir de 250 y una comprobación mecánica de que la
  dieta no pierde contenido (la revisión a ojo de 976 líneas no es fiable).
- **Precargar menos (quitar `skills:` de los agentes) sin tocar los SKILL.md** — ya se hizo en
  `token-diet` (los agentes no precargan `jira-sync`/`confluence-publish`), pero la skill sigue pagándose
  entera al invocarse; no ataca la causa.
- **Dividir cada skill grande en varias skills** — multiplica descriptions (más ruido en el índice de
  piezas y más casos de evals) y rompe los anclajes que citan otras piezas; una skill con referencias
  internas conserva un solo punto de activación.

## Consecuencias

Las tres skills pasan a 149 / 196 / 167 líneas con el mismo contenido repartido en `references/`
(`jira-sync` 5 ficheros, `confluence-publish` 3, `cybersecurity` 4 nuevos que se suman a los 8 que ya tenía).
Toda skill nueva nace con esta forma (plantilla y checklist de `plugin-dev`); toda skill que crezca por
encima de 200 líneas recibe aviso del linter y por encima de 250 rompe la CI. El coste: dos ficheros que
mantener sincronizados por paso (el resumen del `SKILL.md` y su referencia) y una lectura adicional
(`Read` de la referencia) cuando el paso se ejecuta de verdad — que es exactamente cuando el detalle vale
lo que cuesta. `adversarial-review` (203 líneas) queda como siguiente candidata (aviso del linter).

## Estado

`propuesta` — a validar por la revisión de dos lentes o el usuario en la puerta. Pasa a `aceptada` cuando se valida; a `obsoleta` si una decisión posterior la reemplaza (enlaza aquí a la que la sustituye, nunca se borra el rastro).
