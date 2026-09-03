---
design: {{SLUG}}
titulo: {{TITULO}}
estado: borrador              # borrador | aprobado | obsoleto
creado: {{FECHA}}
actualizado: {{FECHA}}
spec: spec.md                 # enlace hacia atrás (misma carpeta)
evaluacion: {{EVALUACION}}    # evaluation.md | n/a
plan: pendiente               # improvement-plan.md cuando el planner lo cree
adr: {{ADR}}                  # docs/knowledge/adr/ADR-NNN-<slug>.md | n/a (no cruzó el umbral)
opcion_elegida: {{OPCION}}    # pendiente | O1 | O2 | O3 — se fija SOLO tras la validación del usuario (pasada 2 / diálogo manual)
generacion:
  fuente: {{FUENTE}}          # medido | estimado (usage-meter.py)
---

# Diseño — {{TITULO}}

> **Spec:** [`spec.md`](spec.md) ({{ESTADO_SPEC}}) · **Evaluación:** {{EVALUACION_LINK}} · **Plan:** {{PLAN_LINK}} · **ADR:** {{ADR_LINK}}

| | |
|---|---|
| **Estado** | {{ESTADO}} |
| **Opción elegida** | {{OPCION}} — {{OPCION_TITULO}} |
| **Validada por el usuario** | {{VALIDACION}} (fecha) |

## 1. Contexto y restricciones

<!-- Qué pide la spec (2-4 frases con los criterios que condicionan el diseño), qué hay HOY en el repo
     (módulos/ficheros reales, con ruta) y qué NO se puede tocar (constitución, ADR vigentes, contratos
     externos, presupuesto de la evaluación). Sin adjetivos: hechos con ruta. -->

{{CONTEXTO}}

**Restricciones que fijan el espacio de soluciones**

- {{RESTRICCION_1}}
- {{RESTRICCION_2}}

## 2. Opciones (2-3)

<!-- Una subsección por opción. Cada una con la MISMA estructura para que se puedan comparar. Coste
     relativo = S / M / L respecto a las otras opciones, NO horas (eso es del evaluator/planner). -->

### O1 — {{O1_TITULO}}

{{O1_DESCRIPCION}}

| Criterio | Valoración |
|---|---|
| Complejidad | {{O1_COMPLEJIDAD}} (Baja/Media/Alta — por qué) |
| Riesgo | {{O1_RIESGO}} (qué puede salir mal) |
| Coste relativo | {{O1_COSTE}} (S/M/L frente a las otras) |
| Reversibilidad | {{O1_REVERSIBILIDAD}} (qué costaría deshacerla) |

### O2 — {{O2_TITULO}}

{{O2_DESCRIPCION}}

| Criterio | Valoración |
|---|---|
| Complejidad | {{O2_COMPLEJIDAD}} |
| Riesgo | {{O2_RIESGO}} |
| Coste relativo | {{O2_COSTE}} |
| Reversibilidad | {{O2_REVERSIBILIDAD}} |

### O3 — {{O3_TITULO}} <!-- opcional; bórrala si dos opciones bastan -->

{{O3_DESCRIPCION}}

| Criterio | Valoración |
|---|---|
| Complejidad | {{O3_COMPLEJIDAD}} |
| Riesgo | {{O3_RIESGO}} |
| Coste relativo | {{O3_COSTE}} |
| Reversibilidad | {{O3_REVERSIBILIDAD}} |

## 3. Criterios de decisión

<!-- Qué pesa más en ESTA iniciativa y por qué (p. ej. «reversibilidad > coste porque la spec deja
     incógnitas»). Son los criterios con los que se leen las tablas de arriba. -->

1. {{CRITERIO_1}}
2. {{CRITERIO_2}}

## 4. Recomendación · opción elegida y por qué

<!-- Pasada 1 (borrador): SOLO la recomendación del arquitecto y su razón — la elegida queda «pendiente».
     Pasada 2 (aprobado): la opción que validó el usuario (vía orquestador con «elegida: O<n>» o en
     diálogo manual) — una frase afirmativa + las razones que la anclan a los criterios. -->

**Recomendación del arquitecto:** {{RECOMENDADA}} — {{RAZON_RECOMENDACION}}

**{{OPCION}} — {{OPCION_TITULO}}.** {{POR_QUE}}

Descartadas: {{DESCARTADAS}} (motivo por opción).

## 5. Impacto en módulos y ficheros

| Módulo / fichero (ruta real) | Cambio | Nuevo / modificado |
|---|---|---|
| `{{RUTA_1}}` | {{CAMBIO_1}} | {{NM_1}} |
| `{{RUTA_2}}` | {{CAMBIO_2}} | {{NM_2}} |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| {{RIESGO_1}} | {{P_1}} | {{I_1}} | {{M_1}} |
| {{RIESGO_2}} | {{P_2}} | {{I_2}} | {{M_2}} |

## 7. Preguntas abiertas

<!-- Lo que el diseño NO cierra y el planner/implementer deben resolver o preguntar. Vacío explícito
     («ninguna») si no hay. -->

- {{PREGUNTA_1}}

---

## Changelog

| Fecha | Cambio |
|---|---|
| {{FECHA}} | Diseño creado (`borrador`); opciones presentadas al usuario |
