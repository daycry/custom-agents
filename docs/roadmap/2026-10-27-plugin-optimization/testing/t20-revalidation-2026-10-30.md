# T-20: revalidación de F3 tras v2.2.0

Base publicada: `c6aee505d200f6354939b8a3dc2305ee82b8ec62` (v2.2.0, 2026-10-30). Comparación del esqueleto aprobado en `31cd57d` con el código publicado y los contratos oficiales consultados el 2026-10-30. T-21 conserva la aprobación de diseño; esta revalidación no la sustituye.

## Hallazgos que concretan el plan

- `model-tier.py` conserva los alias y el filtro Claude; `test_model_tier.py` es la suite existente. CA-08 requiere admitir un id local en `modelos.<agente>` sin pasar un id incompatible al runtime Claude. El formato candidato es `ollama/qwen3:32b`; su selección real y capacidades se comprueban en el equipo del usuario.
- `export-interop.py` tiene renderizadores separados y no lee configuración personal. Mantener su salida canónica determinista; una proyección de consumidor necesita una entrada explícita y un destino distinto de la caché instalada. El instalador Codex usa caché nativa; no es una copia editable por proyecto.
- La documentación de Codex sitúa el proveedor en la sesión padre: escribir `model_provider` en el agente no acredita un cambio de proveedor. El diseño debe separar esa selección de la del modelo. La precedencia de un binding de proyecto frente al agente del plugin requiere un spike acotado antes de adoptar esa ruta. No se da por probada.
- OpenCode V2 usa `provider/model` y permite modelo por agente. La versión local observada es v2.0.12; Codex CLI es 0.166.0. Se consultaron contratos, no se ejecutó ningún modelo local. Ollama no está en PATH; eso no demuestra que no exista en otro equipo.
- `ledger-lint.py`, `ledger-view.py`, `local-read.py` y `local-state.py` son piezas reutilizables para el escritor. T-23 conserva estado, evidencia RED, cabecera de revisión, lock y publicación atómica. Debe rechazar conflictos y rutas inseguras sin reescribir otros campos.
- `task-brief.py` tiene un techo ordinario de 10.000 caracteres. El perfil lite propone 6.000, con aviso/diagnóstico explícito si el contenido obligatorio no cabe; nunca recorta criterios, verificación, TDD ni revisión para aparentar cumplimiento. La elección del límite y el alcance de los subagentes se validan en T-21.

## Verificaciones y entregables

Los tests nuevos de esta tabla son **entregables futuros**, no ejecuciones observadas ni comandos disponibles hoy. Se escriben primero y se observa RED antes del código. Las suites existentes se indican con sus rutas reales.

| Tarea | Ficheros y verificación concreta |
|---|---|
| T-21 | `design.md` con 2-3 opciones, proveedor/modelo por runtime, ubicación del mapeo, alcance lite y decisión del usuario antes de implementar. |
| T-22 | `model-tier.py`, `export-interop.py`, instalador/providers y documentación INTEROP ES/EN; ampliar `test_model_tier.py`, `tests/test_export_interop.py`, `tests/installer.test.mjs`, `tests/codex-native-install.test.mjs`; nueva `tests/test_model_runtime_projection.py`. Probar alias actuales, ids locales, inyección/control chars, runtime Claude, entrada explícita, bytes deterministas, conflicto/propiedad y proveedor heredado. Spike Codex con go/no-go antes de conectar bindings; un no-go vuelve a diseño, sin tocar caché ni cambiar de arquitectura automáticamente. |
| T-23 | Nuevo `ledger-write.py` y `tests/test_ledger_write.py`; reutilizar las suites `tests/test_ledger_lint.py` y `test_ledger_view.py`. Fixture canónica sin avisos, preservación de campos ajenos/EOL, RED, cabecera, dos escritores, conflicto, timeout de lock, enlaces, entrada inválida y cero cambios en error. |
| T-24 | `doctor.py`, `test_doctor.py`, `commands/doctor.md`, INTEROP ES/EN; nuevo `test_doctor_local_models.py`. Configuración ausente/corrupta, contexto insuficiente/conocido/desconocido, opt-in de sondeo y rechazo de destino no local/redirect. No red por defecto ni descargas. |
| T-25 | `task-brief.py`, setup/dev-cycle y referencias lazy; nuevas `tests/test_lite_profile.py`, ampliación `test_task_brief.py`, `tests/test_dev_cycle_split.py`. Default sin cambios, lite sin implementadores paralelos, puerta de revisores frescos/QA intacta, writer obligatorio en lite y aviso si falta. Preservación del contenido obligatorio y perfil opt-in. |
| T-26 | Revisión independiente máximo 3 intentos, cobertura oficial >=90, lint/evals/interop, CI Linux completa, changelog/docs ES/EN y release con versión confirmada. Nuevo checklist manual `testing/f3-ollama-manual-checklist.md`: usuario ejecuta en otro equipo con Ollama; registrar versiones/modelo/contexto, prueba quick y gates conservados. No sustituir por simulaciones ni aprobar calidad por número de parámetros. |

## Presupuesto y medición

El contraste F1/F2 conserva el presupuesto diferido **45,0 h** para F3: diferencia provisional **0 h**. Las ventanas de implementación actuales devuelven tokens, coste y horas IA `null`/`sin_medida`; los bloques históricos medidos del plan no son coste real de implementación. No se puede calcular una desviación numérica fiable ni aplicar un multiplicador desde las horas de reloj. T-21 sigue sin presupuesto desglosado; su ventana se registra aparte, sin inventar tiempo IA.

No se eleva la confianza de la estimación. O1 necesita un spike acotado del binding Codex dentro de T-22; si exige un mecanismo nuevo de aislamiento/distribución, se vuelve a diseño y se reestima antes de comprometerlo. No se incorpora una dependencia externa de Python. Se reutilizan componentes del repositorio bajo Apache-2.0; las fuentes externas se consultan como contratos, sin copiar código de terceros.

## Fuentes y límites

| Fuente primaria (consulta 2026-10-30) | Uso acotado |
|---|---|
| [Codex: subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Modelo por agente; proveedor y permisos heredados. No demuestra precedencia de bindings del proyecto sobre un plugin concreto. |
| [Codex: configuración](https://learn.chatgpt.com/docs/config-file/config-reference) | `agents.<name>.config_file`; proveedor en configuración nativa del usuario/sesión, sin escribirla desde el plugin. |
| [OpenCode V2: agentes](https://opencode.ai/v2/docs/agents/) | Modelo `provider/model`, herencia sin selección explícita. |
| [OpenCode V2: providers](https://opencode.ai/v2/docs/providers/) | Integración Ollama y descubrimiento propio del runtime; no duplicar ese descubrimiento en hooks. |
| [Ollama: contexto](https://docs.ollama.com/context-length) | >=64.000 tokens orientativos para coding; memoria necesaria aumenta. No es prueba de calidad de un modelo. |
| [Ollama: Codex](https://docs.ollama.com/integrations/codex) | Perfil nativo y selección del modelo como responsabilidad de lanzamiento del consumidor. |

Canales usados: rg/lectura local, CLI de versiones y web oficial. No hay conector de búsqueda oficial de documentación disponible; se usó web oficial. No se instaló Ollama, no se descargaron modelos, no se modificó configuración personal ni cachés instaladas. CA-08/09/10 permanecen pendientes y no se modifica su texto global.

El primer borrador reformulaba los cinco criterios de tarea diferidos y scope-check lo señaló (exit1). Se conservan los textos originales aprobados, con la concreción como propuesta adicional sujeta a T-21. No se modifica el detector ni se sustituyen criterios globales. Las verificaciones y archivos quedan concretados; el diseño sigue sin aprobar.

Verificación final de documentación: ledger-lint exit0, 0 incoherencias y 0 avisos; scope-check contra `c6aee505` exit0, cero fuera de alcance, criterios alterados, avisos e info; diff --check limpio. Sin cambios de código ni nuevas pruebas ejecutadas para esta revalidación documental.
