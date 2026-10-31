---
tasks: handbook-readability
estado: en-progreso
creado: 2026-10-31
verificacion: obligatoria
changelog: Changed
---

# Manual comprensible y workflows ilustrados

Ledger canónico.

Corrección expresa del usuario: el PDF anterior era técnico, escueto y carecía
de diagramas Mermaid en PDF y Markdown. Se rehace la guía para personas sin
conocimientos de desarrollo, manteniendo los contratos avanzados como referencia.
El usuario autoriza commits y push al acabar. Go validado por CI 41149389115 (success).
Alcance ampliado: capítulo detallado de memoria local, Kwipu, Graphify y Graphiti;
reflejar únicamente capacidades implementadas de la consola operativa v3.0.0.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Comprensión | 1 | 1 | 100.0% |
| Fase 2 — Diagramas y edición | 2 | 2 | 100.0% |
| Fase 3 — Verificación | 0 | 1 | 0.0% |
| **TOTAL** | **3** | **4** | **75.0%** |

## Fase 1 — Comprensión

### T-01 — Explicar el producto y los veintisiete workflows

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Reescribir la guía ES/EN desde cero para responsables no técnicos, con vocabulario explicado, un caso continuo, peticiones de ejemplo, pasos narrados, decisiones, resultados y recuperación. Preservar la referencia técnica existente.
- **Changelog**: Manual para responsables con ejemplos narrados y términos explicados.
- **Archivos**: `docs/CUSTOMIZATION.md`, `docs/en/CUSTOMIZATION.md`, `docs/guides/**`, `docs/en/guides/**`, `docs/reference/**`, `docs/en/reference/**`, `docs/roadmap/2026-10-31-handbook-readability/**`
- **Verificación**: lectura de todos los workflows contra los contratos; revisión de comprensión.

**Criterios de aceptación**
- [x] Cada workflow explica cuándo usarlo, qué necesita la persona, qué pide, qué ocurre paso a paso, quién interviene, qué decide, cómo comprueba el resultado y qué hace si falla. Siglas y piezas se explican antes de usarse.

## Fase 2 — Diagramas y edición

### T-02 — Añadir diagramas Mermaid y representarlos

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Diagramas de proceso, participantes y estados en las fuentes Markdown; compilación Mermaid real y gráficos legibles en el PDF, sin mostrar código Mermaid como sustituto del dibujo.
- **Changelog**: Diagramas Mermaid de procesos y estados en Markdown y PDF.
- **Archivos**: `docs/guides/**`, `docs/en/guides/**`, `docs/CUSTOMIZATION.md`, `docs/en/CUSTOMIZATION.md`, `docs/roadmap/2026-10-31-handbook-readability/**`
- **Verificación**: compilar todos los diagramas y revisar sus representaciones.

**Criterios de aceptación**
- [x] Los veintisiete workflows tienen diagramas, rutas y decisiones coherentes; todas las fuentes Mermaid compilan y se muestran como gráficos en el PDF.

### T-03 — Editar el PDF para lectura y consulta

- **Estado**: completado
- **Tipo**: docs
- **Descripción**: Manual con jerarquía visual, texto legible, ejemplos completos, índice y referencias; conservar la técnica al final y mantener procedencia de fuentes y diagramas.
- **Changelog**: PDF explicado para responsables, con diagramas y referencias avanzadas.
- **Archivos**: `output/pdf/**`, `docs/README.md`, `docs/en/README.md`, `README.md`, `README.es.md`, `package.json`, `docs/roadmap/2026-10-31-handbook-readability/**`
- **Verificación**: renderizar y revisar todas las páginas de la edición final.

**Criterios de aceptación**
- [x] No hay texto cortado, gráficos ilegibles ni código Mermaid en lugar de diagramas. El PDF incluye el contenido explicado y ejemplos de uso, con navegación y fuentes verificables.

## Fase 3 — Verificación

### T-04 — Revisar, validar y publicar la rama

- **Estado**: en-progreso
- **Tipo**: docs
- **Descripción**: Contrastar comprensión y fidelidad funcional, enlaces, empaquetado, ES/EN y artefactos; commits literales, push y CI. La publicación v3.0.0 autorizada se coordina en T-06 del ledger control-center.
- **Changelog**: Verificación de manual y diagramas antes de la entrega.
- **Archivos**: `docs/roadmap/**`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**: linter, evals, suites afectadas, revisión de contenido y visual, CI del commit publicado.

**Criterios de aceptación**
- [ ] Resultados y límites documentados; métricas ausentes explícitas; todos los cambios propios en commits y push; CI verificada antes de entregar.

Ampliación de alcance autorizada por las peticiones posteriores del usuario:
W-19 a W-22 detallan memoria local y sus integraciones; W-23 a W-27 explican la
consola común y sus operaciones. Se actualiza el recuento de18 a27 sin retirar
ningún recorrido ni relajar comprensión o verificación. Primera edición de QA:
94 páginas,27 workflows,31 gráficos,70 marcadores y150 enlaces, sin texto fuera
de página ni caracteres de sustitución; todas las hojas de contacto y muestras
de portada, diagramas y código inspeccionadas. Pendiente edición final/ES-EN y
revalidación tras ajustes. Se añade gráfico también a W-26.

T-04 amplía archivos a `scripts/check-handbook.py`, `tests/test_handbook_integrity.py`,
`ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `.github/workflows/ci.yml` y
`.github/workflows/release.yml`: verificación de procedencia del PDF en CI/release
y entrega del PDF como asset independiente. RED observado:4 failed por verificador
ausente. Comprueba cambios de fuente/PDF, diferencias CRLF y recibos de diagramas
sin permitir que un manifiesto seleccione archivos ajenos. Sólo stdlib.
