<!--
  TEMPLATE: spec.md  · especificación funcional/técnica
  Vive en docs/roadmap/<fecha>-<slug>/spec.md junto a evaluation.md, improvement-plan.md, tasks.md.
  Estados de una spec: borrador | aprobada | implementada | obsoleta
  Rellena/borra secciones según el caso (una spec pequeña no necesita todas).
  Enlace cruzado (misma carpeta; rellena cuando existan, "pendiente" si aún no):
    - evaluacion: evaluation.md
    - design: design.md   (opcional: solo si el agente architect hizo el paso de diseño)
    - plan: improvement-plan.md
-->
---
spec: {{slug}}
descripcion: {{una frase que resuma la spec}}
estado: borrador          # borrador | aprobada | implementada | obsoleta
creado: {{YYYY-MM-DD}}
actualizado: {{YYYY-MM-DD}}
evaluacion: pendiente     # ruta a la evaluación cuando exista
design: n/a               # design.md si el agente architect hizo el paso de diseño (opcional); n/a si no
plan: pendiente           # ruta al plan cuando exista
generacion:               # coste real de producir ESTE documento — lo rellena `usage-meter.py close` (kit shared)
  inicio: {{ISO-8601}}    # fechas = CONTEXTO informativo; NUNCA se usan para calcular horas
  fin: {{ISO-8601}}
  fuente: medido          # medido (tokens de la transcripción) | estimado (degradación)
  tokens_reales: { entrada: {{N}}, salida: {{N}}, cache_creacion: {{N}}, cache_lectura: {{N}} }
  eur: {{N.NN | null}}    # null + aviso si precioTokens no es fiable (ejecuta rates-verify)
  horas_ia: {{N.NN}}      # tokens facturables ÷ ratio (tokens = medida; horas = derivadas)
  duracion: {{XhYm}}      # formato humano (usage-meter.py fmt): 32m · 1h 32m · 18h
  ratio_usado: {{N}}      # tokens→hora; origen: CALIBRATION.md (mediana) o default no calibrado
---

# {{Título legible de la spec}}

> **Evaluación:** {{[`evaluation.md`](evaluation.md) — o «pendiente»}}
> **Plan de implementación:** {{[`improvement-plan.md`](improvement-plan.md) — o «pendiente»}}

<!-- Terminología: incluye solo si hay términos que puedan confundir. -->
> **Terminología:** {{define aquí cualquier término ambiguo del dominio}}

## Contexto y objetivo

{{Qué problema resuelve, para quién y por qué. Referencia las fuentes (mockups, tickets, requisitos) con localizadores concretos.}}

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| {{aspecto}} | **{{opción elegida}}** | {{por qué}} |
| {{aspecto}} | **{{opción elegida}}** | {{por qué}} |

<!-- Opcional: tabla de configuración/parámetros verificados contra el código o la fuente. -->
## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| {{nombre}} | `{{clave}}` | {{default}} | **{{valor}}** |

## Arquitectura y componentes

{{Módulos/piezas implicadas y cómo encajan. Marca lo que se reutiliza vs. lo nuevo.}}

## Flujo (paso a paso)

1. {{Paso 1}}
2. {{Paso 2}}
3. {{…}}

## Alcance

- **Dentro (esta iteración):**
  - {{…}}
- **Fuera (siguientes specs):**
  - {{…}}

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| {{caso}} | {{qué ocurre}} |

## Criterios de aceptación

<!--
  Dos variantes, combinables criterio a criterio:
  · Checkbox libre (default) — para criterios de proceso, documentación o difíciles de observar:
      - [ ] {{criterio verificable en una frase}}
  · Given/When/Then, marcado [GWT] — para COMPORTAMIENTO OBSERVABLE del sistema; qa lo traduce
    1:1 a un bloque E2E y coverage-check.py exige su ID en test-plan.md:
      - [ ] [GWT] CA-01 — Dado {{estado inicial}}, Cuando {{acción}}, Entonces {{resultado observable}}
  Usa [GWT] cuando el criterio describa algo que un test puede reproducir (UI, API, CLI);
  no lo fuerces para criterios de prosa/proceso. Los IDs CA-XX dan la trazabilidad criterio↔test.
-->

- [ ] {{criterio libre}}
- [ ] [GWT] CA-01 — Dado {{estado}}, Cuando {{acción}}, Entonces {{resultado observable}}

## Pruebas

{{Qué se prueba y cómo (tipo de test, criterios). Lista verificable. Los criterios [GWT] de arriba se traducen 1:1 a bloques E2E del test-plan (mismo ID CA-XX).}}

## Referencias

- {{Fuente 1 con localizador (fichero, línea, sección)}}
- {{Fuente 2}}

## Decisiones confirmadas (revisión del usuario · {{YYYY-MM-DD}})

1. {{Decisión}}. **Confirmado.**

## Supuestos

- {{Supuesto explícito y, si aplica, qué lo verificaría}}
