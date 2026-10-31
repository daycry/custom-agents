# Revisión independiente — intento 1

Base: `707d4ad`. Diff de trabajo y nuevos archivos propios de esta iniciativa.
Se excluye `.claude/settings.json` personal sin leerlo. Scope: exit0, fuera de alcance vacío;
el ledger nuevo todavía no tiene una línea base de criterios en Git.

Estrategia efectiva: normal, revisores frescos paralelos. Las cuatro lentes usan
subagentes genéricos con el contrato de reviewer, porque este entorno no expone
despacho nativo por ese ID. La implementación permanece en ROOT.

| ID | Lente | Grado | Hallazgo observado | Corrección y regresión |
|---|---|---|---|---|
| A-01 | Conformidad | Important | Mapa Confluence de206 líneas, límite constitucional200 | Interacción extraída sin pérdida a referencia; `test_gap_a01_confluence_skill_map_respects_constitution` |
| A-02 | Conformidad | Important | Descriptores de documenter, ROLES, CONTRACTS y espejo FLOWS aún ordenaban llamadas de proveedor | Contratos dueños actualizados al puerto genérico; `test_gap_a02_documenter_contract_has_no_direct_provider_callback` y pruebas de dueño por intento |
| A-03 | Conformidad | Important | Core exigía PDF/panel sin instalar sus módulos | Salidas de presentación opcionales con Markdown conservado; `test_gap_a03_core_outputs_degrade_without_optional_presentation_modules` |
| B-01 | Corrección | Important | Edición de consumidor después del preflight sobrescrita durante reinstalación | Hash previo por archivo, revalidación antes de cada reemplazo y sin fallback in-place; unitario gap B y CLI `concurrent edits after the first profile checkpoint survive reinstall` |
| D-01 | Rendimiento | Important | Un checkpoint completo por archivo, amplificación O(N²) | Checkpoints por grupos de payload; unitario gap D y CLI `a complete profile writes bounded manifest checkpoints` |

Las cinco regresiones se observaron rojas antes de corregir. Las expectativas de
propiedad por intento se adaptan al puerto neutral; se conserva la ejecución real
de `jira-flow.py` que comprueba el comentario Jira. El test de selección sigue
comprobando los mismos archivos, ahora dentro del grupo en lugar de un paso por archivo.

Lente C: sin hallazgos explotables confirmados en el diff. Comprobó el router
declarativo contra local-read/redact, settings relativos, aislamiento, propiedad
por bytes, selector confiable del checkout y raíz Jira explícita. Sin red/cuentas.

Lente D midió el contenido real con variables y destinos aislados:

| Caso anterior al arreglo | Archivos | Escrituras de manifiesto | Bytes de manifiesto | Segundos |
|---|---|---|---|---|
| Sin perfil | 509 | 8 | 350252 | 2.418 |
| full | 509 | 509 | 65790680 | 11.232 |
| core | 353 | 353 | 30995422 | 7.255 |

Estas cifras pertenecen al ensayo del revisor, no a un SLA. La regresión posterior
exige un número de checkpoints acotado por los grupos del payload. El benchmark
dejó dos directorios TEMP propios: la revisión automática rechazó su limpieza
recursiva con «blocked by policy»; el revisor no repitió ni eludió el rechazo.

Lente A ejecutó por sí misma `export-interop.py --check`: exit0,88 archivos al día
en la versión revisada. T07/PDF y QA final estaban pendientes y no se presentaron
como completados. No hay especificación OpenAPI afectada ni puertas rebajadas.

Resultado del intento: cinco Important comprobados; corregidos con regresión,
pendientes de revalidación independiente del intento2. No hay hallazgos descartados.
