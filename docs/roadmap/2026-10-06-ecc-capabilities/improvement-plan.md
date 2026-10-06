---
plan: ecc-capabilities
estado: en-progreso
creado: 2026-10-06
actualizado: 2026-10-06
spec: spec.md
test-plan: test-plan.md
---

# Plan — adopción selectiva de ECC

Decisión delegada por el usuario: construir un panel propio con stdlib e integrar
capacidades dentro de los roles existentes. Reutilizar ECC entero supondría otra
memoria, otro control plane y dependencias que este plugin no necesita.

| Tarea | Resultado | Dependencia |
|---|---|---|
| T-01 | Comparación técnica ECC/Graphify y decisiones trazables | plugin-refactor cerrado localmente y rama publicada |
| T-02 | research-first en analyst/architect | T-01 |
| T-03 | plugin-panel y plugin-catalog | T-01 |
| T-04 | Guías de CodeIgniter, Python y React en roles existentes | T-01 |
| T-05 | Exports, revisión, QA, documentación, commit y push | T-02…T-04 |

El HTML se inspecciona en navegador: búsqueda, filtros, escritorio y móvil.
El inventario del panel separa definiciones de ejecución. La prueba automatizada
verifica escapes, redacción, errores, rutas y ownership de la salida.

Memoria: mantener captura/journal, Knowledge Gate, búsqueda y backends actuales.
El piloto Graphify parte de código público en salida nueva y aislada; no promueve
reflexiones a doctrina. Las mejoras posteriores tienen criterios en comparison.md.
Sin instalar ECC/Graphify en los runtimes ni iniciar observadores.
