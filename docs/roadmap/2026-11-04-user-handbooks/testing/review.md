# Revisión adversarial de los manuales

Incremento público `950fde8..5730e0a`, 17 ficheros. Revisión desde clon limpio y aislado, sin preferencias o corpus privados. `scope-check.py` → exit 0, 17 en alcance, 0 fuera, 0 excluidos. `review-lens-select.py` → C=false, D=false: incremento documental, sin rutas o contenido que activen esas lentes. Se usan revisores nativos `custom-agents-reviewer` con contexto fresco.

## Intento 1: revisión preparatoria B, incompleto

La lente A todavía no se había ejecutado; esta pasada no daba permiso para pasar la puerta completa. B leyó ambos manuales y contrastó contratos y fuentes. Aprobó workflows, lite, categorías, publicación, estimaciones y 24 enlaces locales.

| # | Grado | Hallazgo | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | La tabla recomendaba `/reasoning` para Codex CLI | T-01 | Usar `/model` y su opción documentada `--reasoning=high` | Fuente oficial y test dedicado B1 |
| B2 | Important | `api-contract` prometía contrastar implementación y spec | T-01 | Describir validación y comparación de specs; no pruebas de respuesta | Contrato de la skill y test dedicado B2 |

Escenarios: B1 conduce al lector a un comando de otra superficie o ausente en su CLI. B2 permite creer que una respuesta incompatible ya se ha comprobado solo por validar la spec. Sin rebatidos ni deuda aceptada. Correcciones verificadas en el intento 2.

## Intento 2: A+B, sin gaps pendientes

Se pasó a ambos revisores la tabla anterior y sus veredictos. A revisó todo el incremento y la constitución. B revaluó lo corregido, los tests, los manifiestos y los glosarios, conservando lo previamente aprobado. No se reabrió el código de optimización anterior a `950fde8`.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-01: manuales, ejemplos, prompts y decisiones | ✓ A | Cobertura de eficiencia, ciclo completo, integraciones, memoria, personalización y límites explícitos |
| T-01: B1/B2 corregidos | ✓ B | Fuentes oficiales/contrato canónico, tests dedicados y texto PDF corregido |
| T-02: fuentes, PDF, diagramas e índices | ✓ A+B | Hashes normalizados, 8 Mermaid coincidentes, PDF 19/25 páginas, glosarios y correcciones presentes |
| T-02: revisión visual acreditada | ✓ A | Método e informe versionados; A no suplió una comprobación inexistente |
| T-03: índices y tests | ✓ A+B | Espejos ES/EN actualizados; 70 tests pasados por ambos revisores |
| T-03: CI/publicación final | Pendiente de cierre en esa instantánea | Ledger correctamente en-revision; se verifica al cerrar, sin atribuirlo a los revisores |
| Constitución, scope y puertas | ✓ A | Tests B1/B2 dedicados, RED registrado, ningún test/umbral debilitado; 17 archivos en alcance |
| Redacción citable | ✓ A | Sin violaciones reportables de docs-style |

Ambos revisores ejecutaron `pytest tests/test_user_handbooks.py tests/test_roadmap_index.py` → 70 passed y `git diff --check` → exit 0. B contrastó además controles negativos de texto y manifiestos; A verificó hashes Mermaid, cantidades y ediciones. No hay hallazgos nuevos, rebatidos o deuda pendiente.

Tras esta instantánea, el cierre corrige únicamente acentos de la introducción/portadas añadidas por la maquetación y regenera sus hashes. Los Markdown y workflows revisados permanecen idénticos. Se repite la validación de las ediciones y de la extracción final; no se atribuye a los revisores la inspección de ese nuevo hash binario.
