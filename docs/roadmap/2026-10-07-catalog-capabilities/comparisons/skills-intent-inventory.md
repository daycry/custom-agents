# Criterios de aceptación guiados por intención y planificación de inventario — S135–S136

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Dos cuerpos completos: **41.580 bytes/600 líneas**, sin recursos locales.
[intent-inventory-reading-evidence.json](intent-inventory-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S135 — Desarrollo guiado por intención

`17.199 bytes/360 líneas`. Convertir peticiones ambiguas o de alto impacto en
criterios de aceptación observables: inspeccionar el contexto antes de preguntar,
dos profundidades (captura rápida de 3-7 criterios o informe completo), preguntas
mínimas, criterios con escenario/acción/resultado/efecto prohibido/verificación,
revisión marcada `[revised]` y rúbrica de aprobado/suspenso.

**Comparación.** Solapa con `analyst` (dueño de `spec.md`, ADR-011) y con el
formato `[GWT]` que `coverage-check.py` cruza con los tests. Aporta tres reglas
que el analyst no explicita y que son verificables:

| Regla | Encaje |
|---|---|
| **Separar hechos técnicos descubiertos en el repo de restricciones de negocio**: las segundas solo las aporta el usuario o un documento de producto y, hasta entonces, son supuestos | Sección «Supuestos e incógnitas» de la plantilla de spec; hoy mezcla ambos |
| Cada criterio incluye un **efecto prohibido** («no debe…») cuando aplique | Plantilla de criterios del analyst y Lente A |
| Profundidad proporcional (captura rápida frente a informe completo) | Ya existe: vía rápida de `/dev-cycle` y flujo completo |
| Palabras vagas («correcto», «seguro», «rápido») prohibidas sin evidencia observable | Rúbrica del analyst |

Correcciones: «no bloquear la implementación por defecto» y «guardar el
documento solo si se pide» chocan con el ciclo del plugin, donde la spec
aprobada es una puerta y vive siempre en `docs/roadmap/`. **Destino:** añadir
las tres reglas a la plantilla de spec del evaluator y al checklist del analyst.
Sin skill nueva (ADR-011: un rol, un dueño).

## S136 — Planificación de demanda e inventario

`24.381 bytes/240 líneas`. Persona de planificador de demanda en distribución
minorista: métodos de previsión, métricas de error, stock de seguridad, reglas
de reposición, promociones, segmentación ABC/XYZ, rebajas y escalados.

**Comparación.** Dominio de negocio ajeno al ciclo, igual que S093 (energía). Las
cifras (umbrales, niveles de servicio, márgenes) dependen del negocio y no se
verificaron. **Fuera del bundle**; persona de proyecto si un consumidor del sector
la necesita. Una idea general coincide con prácticas propias: elegir y validar
el modelo con datos de **fuera del periodo de ajuste** (no sobre los mismos datos),
análoga a separar corpus de prueba en `outcome-evals`.
