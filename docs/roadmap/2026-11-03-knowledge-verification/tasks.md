---
tasks: knowledge-verification
estado: en-progreso
creado: 2026-11-03
verificacion: obligatoria
changelog: Fixed
---

# Verificación de proyecciones de conocimiento

**Ledger canónico**. Las correcciones del plugin se implementan aquí; concurrencia
de embeddings y compatibilidad LLM del servidor se solicitan a knowledge-graphs.
Sin nuevas publicaciones, reindexaciones ni cambios del stack externo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Diagnóstico verificable | 1 | 1 | 100.0% |
| **TOTAL** | **1** | **1** | **100.0%** |

## Fase 1 — Diagnóstico verificable

### T-01 — Evitar verificaciones verdes sin contenido confirmado

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Comparar hashes nativos fm.hash en Kwipu, conservar comprobación de hashes anteriores, declarar incompleto sin hash y no ocultar chunks discrepantes. Graphiti sin publicación local la declara explícitamente sin romper CA-04 de lectura de grupos externos. Corregir el remedio que omitía regenerar el índice.
- **Archivos**: adaptadores y tests de knowledge-services; contrato CA-17 y changelogs.
- **Verificación**: pytest de verificación, publicación y lectura; cobertura configurada; lint, evals e interop; --check local de solo lectura.

**Criterios de aceptación**
- [x] Hash nativo desactualizado, identidad ajena o chunks discrepantes impiden verde.
- [x] Ausencia de hash se declara incompleta y no se confunde con desfase confirmado.
- [x] Graphiti sin publicación local advierte que no hay contenido verificado; conserva CA-04, pendientes e historial.
- [x] Remedio exige regeneración explícita sin ejecutar el stack.
- [x] Pruebas y documentación actualizadas.

## Evidencia y límites

- RED inicial: 13 fallos de 14 casos; 4 fallos adicionales de metadatos inconsistentes.
  Los tests reprodujeron verde por nombre con fm.hash antiguo, chunks discrepantes
  ocultos por basename y el remedio sin reconstrucción explícita.
- La primera propuesta de Graphiti incompleto sin manifiesto se descarta: las
  regresiones evidenciaron el contrato CA-04 de lectura de grupos poblados por
  otros clientes. Se conserva y se añade publicación local ausente, cero elementos
  verificados y aviso explícito. El test del aviso falló por campo ausente antes
  de implementarlo. Los recibos pendientes siguen cerrando la lectura.
- Windows dirigido tras el ajuste: 50 pasados. La primera suite Linux amplia tuvo
  37 fallos y no se considera verde aunque su gate de cobertura superase el mínimo;
  se contrasta el resultado JUnit además de medir cobertura.
- Comprobación real de solo lectura: el check anterior reportó ok por nombre;
  el corregido detectó hashes/metadatos desfasados en las 18 entradas publicadas.
  No se ejecutan nuevos envíos, reindexación, inferencia ni cambios del stack.
- Autorrevisión: comparación de hashes nativos/históricos, identidad declarada,
  múltiples chunks, ausencia de prueba y contrato CA-04. La observación de hashes
  no sustituye la autorización canónica completa ni garantiza un snapshot atómico.
- TDD n/a: contrato, changelogs y solicitud externa, documentación.
- Verificación final Linux aislada y sin red externa: **1.271 pasados, 1 omitido,
  0 fallos, 0 errores**; 1.272 casos en JUnit. Cobertura oficial de los dos
  adaptadores modificados: **93,75 %**, mínimo 90 % (Graphiti 92,93 %, Kwipu 94,56 %).
- Linter: 0 errores y 7 avisos existentes. Evals: 221 casos, 0 errores.
  Interop: 88 ficheros al día. Manual PDF y fuentes coherentes. Ledger sin
  incoherencias ni avisos; diff sin errores de whitespace.
- La entrega depende de la PR de metadatos Kwipu. Integración y CI remota de esta
  corrección se comprueban en su PR; no se declara una nueva release publicada.

```curation-refs-v1
[{"candidate":"docs/knowledge/candidates/pending/2026-11-03-native-snapshot-hash-verification.md","sha256":"67b696c48a26561285d917b5518c5665e5621661f354fe95dd17d23998d20d6b"}]
```

Propuesta de memoria local pendiente de Curator; no aprobada ni publicada.

RED: `skills/knowledge-services/scripts/test_backend_verification.py` falló con 13 rojos: fm.hash ignorado, verde sin hash o sin publicacion, chunks e identidad no contrastados; 4 rojos adicionales de metadatos inconsistentes · 2026-11-03.
