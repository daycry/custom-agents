<!--
  TEMPLATE: spec.md  ·  especificación funcional/técnica
  Vive en docs/specs/<slug>.md (identidad estable; las fechas van en el frontmatter).
  Estados de una spec: borrador | aprobada | implementada | obsoleta
  Rellena/borra secciones según el caso (una spec pequeña no necesita todas).
  Enlace cruzado (rellena cuando existan; "pendiente" si aún no):
    - evaluacion: docs/evaluations/<fecha>-<slug>/evaluation.md
    - plan:       docs/plans/<fecha>-<slug>/improvement-plan.md
  Rutas relativas desde docs/specs/: evaluación → ../evaluations/... · plan → ../plans/...
-->
---
spec: {{slug}}
descripcion: {{una frase que resuma la spec}}
estado: borrador          # borrador | aprobada | implementada | obsoleta
creado: {{YYYY-MM-DD}}
actualizado: {{YYYY-MM-DD}}
evaluacion: pendiente     # ruta a la evaluación cuando exista
plan: pendiente           # ruta al plan cuando exista
---

# {{Título legible de la spec}}

> **Evaluación:** {{[`docs/evaluations/<fecha>-<slug>/evaluation.md`](../evaluations/<fecha>-<slug>/evaluation.md) — o «pendiente»}}
> **Plan de implementación:** {{[`docs/plans/<fecha>-<slug>/improvement-plan.md`](../plans/<fecha>-<slug>/improvement-plan.md) — o «pendiente»}}

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

## Pruebas

{{Qué se prueba y cómo (tipo de test, criterios). Lista verificable.}}

## Referencias

- {{Fuente 1 con localizador (fichero, línea, sección)}}
- {{Fuente 2}}

## Decisiones confirmadas (revisión del usuario · {{YYYY-MM-DD}})

1. {{Decisión}}. **Confirmado.**

## Supuestos

- {{Supuesto explícito y, si aplica, qué lo verificaría}}
