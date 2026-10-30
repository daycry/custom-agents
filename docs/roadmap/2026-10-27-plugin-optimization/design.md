---
design: plugin-optimization-f3
titulo: Modelos locales y perfil lite
estado: borrador
creado: 2026-10-30
actualizado: 2026-10-30
spec: spec.md
evaluacion: evaluation.md
plan: improvement-plan.md
adr: pendiente
opcion_elegida: pendiente
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  nota: "Ventana propia; sin transcripcion compatible. Las horas de reloj no son horas IA."
---

# Diseño de F3: modelos locales y perfil lite

> Spec [aprobada](spec.md) · [Evaluación](evaluation.md) · [Plan](improvement-plan.md) · [Revalidación T-20](testing/t20-revalidation-2026-10-30.md).

| | |
|---|---|
| Estado | Borrador de T-21; no autoriza implementar T-22..T-25 |
| Opción elegida | Pendiente |
| Validada por el usuario | Pendiente |
| Base | v2.2.0, `c6aee505d200f6354939b8a3dc2305ee82b8ec62` |

## 1. Contexto y restricciones

F1 y F2 están publicadas. F3 pide aceptar ids locales en `modelos.<agente>`, proyectar `model` para Codex/OpenCode, disponer de un escritor determinista del ledger y ejecutar lite sin reducir revisión ni QA. CA-08/09/10 permanecen pendientes. El objetivo de 32B con contexto >=64k es orientativo hasta la prueba manual del usuario; 8-9B queda para lectura.

`model-tier.py` resuelve frontmatter y override de `dev.json`; ADR-009 prohíbe mezclar esa configuración con cambios en la caché del plugin. `export-interop.py` genera piezas canónicas; el instalador usa una caché nativa de Codex y copias administradas en OpenCode. `task-brief.py` limita el brief normal a 10.000 caracteres. `ledger-lint.py` sigue siendo dueño del contrato y `local-state.py` ofrece primitives de escritura local.

**Restricciones que fijan el espacio de soluciones**

- Constitución §2: fuentes reales únicas, interop generado, stdlib y cero red desde hooks. §4: no sobrescribir ficheros ajenos ni seguir enlaces al escribir.
- ADR-009 aceptado: la configuración pertenece al consumidor y la resuelve un script. No se modifica el ADR ni se promueve una propuesta sin decisión del usuario y servicio de curación.
- Codex hereda el proveedor del padre; `model_provider` en el agente no lo cambia. El consumidor configura y lanza su sesión nativa con el proveedor adecuado. El plugin no escribe credenciales ni configuración global de proveedores.
- La entrada modelo puede ser `ollama/qwen3:32b`: OpenCode conserva `provider/model`; Codex necesita el id del modelo dentro del proveedor de su sesión. No se transforma un alias Claude en un modelo local elegido por el plugin.
- Las tres opciones conservan permisos, identidades protegidas, TDD, revisión independiente, cobertura y QA. No hay descargas de modelos ni ejecuciones de Ollama en esta fase de diseño.

**Propiedad y estados:** `dev.json` del consumidor es la fuente de selección; el renderizador produce una proyección con esa entrada explícita. El instalador escribe solo destinos propios y registra hashes. Conflicto o precedencia no acreditada se informa y se conserva; nunca se reescribe la caché nativa para resolverlo.

## 2. Opciones

### O1 — Configuración del proyecto y proyección explícita (recomendada)

Mantener `modelos.<agente>.model` como cadena y añadir resolución consciente del runtime, conservando el comportamiento Claude actual por defecto. El id local se acepta para Codex/OpenCode; en Claude se diagnostica y conserva el fallback compatible. La salida incluye la procedencia y el proveedor esperado, sin prometer que un campo del agente cambie el proveedor padre.

La exportación canónica no consulta el proyecto ni HOME. Un modo explícito recibe el fichero del consumidor y genera sus agentes en un destino separado. Para Codex, el instalador conecta esa proyección mediante un binding nativo de proyecto; OpenCode usa su destino administrado existente. Los flags nuevos se definirán al implementar, con tests RED; no se presentan como disponibles hoy.

**Spike previo obligatorio de T-22:** acreditar en un entorno desechable, con la CLI 0.166.0 y sin peticiones a modelos, que la ruta `agents.<name>.config_file` conserva la identidad protegida y selecciona el agente/modelo proyectado frente al plugin instalado. Las docs admiten esa clave, pero no prueban esa precedencia concreta. El recibo debe distinguir parseo de selección efectiva; si la CLI no permite probarla sin ejecutar un modelo, el resultado será no acreditado, sin declarar go. Ausencia de go devuelve a T-21 y reestimación; no permite cambiar a O2 o editar la caché automáticamente.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: resolver y renderizar se reutilizan; binding Codex pendiente de spike |
| Riesgo | Medio: se controla con no-go explícito, conflictos y hashes |
| Coste relativo | M; conserva provisionalmente el alcance de 45 h, sin asegurar desviación real |
| Reversibilidad | Alta: retirar solo bindings/proyecciones propios; fuente canónica intacta |

### O2 — Distribución derivada por configuración

Generar un bundle consumidor completo y darle identidad de instalación aislada. La selección queda fijada al construirlo, con manifiesto de entradas y salida determinista. Requiere validar cómo registrar esa identidad sin colisionar con el plugin oficial ni alterar los ids que vigila el guard. No modifica una caché existente; la derivada sería otro artefacto.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: distribución, registro, actualización y guardias por identidad |
| Riesgo | Alto: dos instalaciones y posibles bindings ambiguos |
| Coste relativo | L; necesita reestimación antes de adoptar |
| Reversibilidad | Media: desinstalar con manifiesto propio sin retirar el plugin original |

### O3 — Heredar un modelo local para toda la sesión

El usuario inicia Codex/OpenCode con el modelo local; todos los agentes heredan ese modelo. Es el recorrido más sencillo y conserva el plugin canónico. Renuncia al mapeo por agente de CA-08: requiere una modificación explícita del criterio, no es cumplimiento del plan actual. El resto de F3 podría mantenerse.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja |
| Riesgo | Bajo para instalación; calidad del modelo sigue pendiente de prueba manual |
| Coste relativo | S; no se cuantifica un ahorro sin reestimar |
| Reversibilidad | Alta: cambiar el modelo de la sesión |

## 3. Criterios de decisión

1. Respetar CA-08 y la separación entre proveedor padre y modelo del agente.
2. Mantener la caché instalada y los ficheros ajenos fuera del alcance de escritura.
3. Configuración del consumidor explícita y salida reproducible, sin cambios ambientales en `--check`.
4. Cambios acotados y recuperables con propietarios existentes; reutilizar stdlib y contratos del repo.
5. Mantener todas las puertas aun con menos contexto y sin paralelismo de implementación.

## 4. Recomendación y opción elegida

**Recomendación: O1**, condicionada al spike Codex con go demostrable. Conserva la configuración del consumidor y el criterio por agente sin convertir cada instalación en otra distribución. El diseño no declara validado un binding todavía no probado.

**Opción elegida: pendiente de validación del usuario.** O2 queda como alternativa si se acepta su coste/alcance; O3 requiere aprobar un cambio de CA-08. Ninguna se selecciona por defecto al aprobar publicar F2.

**Decisiones comunes propuestas para lite y ledger-write (también pendientes):**

- Lite es opt-in; ejecución secuencial, sin subagentes de implementación. Los revisores de contexto fresco se conservan y se ejecutan secuencialmente: el toggle no suprime la revisión independiente. QA y coverage90 permanecen intactos.
- Brief lite de 6.000 caracteres. Los bloques obligatorios nunca se truncan para cumplirlo; si no caben, se informa y no se despacha un brief incompleto. El perfil ordinario conserva 10.000.
- `ledger-write.py` es obligatorio en lite y preferente fuera de lite; las instalaciones ordinarias parciales conservan el fallback documentado. El script reutiliza validación/parsing, conserva contenido ajeno y publica atómicamente tras lock y verificación de versión. Un conflicto no se sobreescribe.
- `/doctor` informa contexto conocido insuficiente o contexto desconocido. Sondeo de endpoint local solo opt-in, con timeout y sin redirects; ninguna consulta de red desde hooks ni descarga automática.

## 5. Impacto en módulos y ficheros

| Módulo / fichero | Cambio | Nuevo / modificado |
|---|---|---|
| `agent-kits/shared/model-tier.py` | Validación y resolución por runtime; fallback Claude y procedencia | Modificado |
| `scripts/export-interop.py` | Entrada explícita y renderizado de consumidor; canonical check determinista | Modificado |
| `install/install.mjs`, `install/providers.mjs` | Spike/bindings y propiedad de la proyección; conflictos y retirada propia | Modificados |
| `agent-kits/shared/ledger-write.py` | Estado, RED, cabecera de revisión y escritura atómica | Nuevo |
| `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/ledger-view.py`, `agent-kits/shared/local-state.py` | Reutilizar contratos existentes; ampliar solo si lo exigen los tests | Existentes |
| `agent-kits/shared/task-brief.py`, `commands/setup.md`, `commands/dev-cycle.md` | Perfil lite, techo y carga bajo demanda | Modificados |
| `agent-kits/shared/doctor.py`, `commands/doctor.md` | Diagnóstico local y contexto | Modificados |
| `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` | Documentar asimetrías, perfiles y recuperación | Modificados |
| `tests/test_model_runtime_projection.py`, `tests/test_ledger_write.py`, `tests/test_lite_profile.py` | Contratos futuros con RED antes de implementar | Nuevos |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Binding Codex no selecciona la proyección | Media | Alto | Spike go/no-go previo; detener esa vía y volver a diseño |
| Contexto/config declarados difieren del servidor real | Media | Alto | Distinguir desconocido y declarado; prueba manual del usuario |
| Modelo local no soporta effort/parámetros del agente | Media | Medio | No traducir effort por equivalencia inventada; validar por runtime/modelo y probar |
| Dos escritores pierden evidencia del ledger | Media | Alto | Lock, hash previo, publicación atómica y test concurrente dedicado |
| Brief compacto omite puertas | Media | Alto | Tests de preservación y fallo explícito ante overflow obligatorio |
| Herencia de proveedor se confunde con override por agente | Media | Alto | No emitir `model_provider` como override efectivo en el rol; diagnóstico y launch nativo del consumidor |

## 7. Preguntas abiertas

- Aprobar O1 (con spike y retorno a diseño si no hay go), elegir O2 con reestimación, o cambiar el criterio por agente con O3.
- Validar las decisiones comunes propuestas: brief lite de 6.000 caracteres, revisores frescos secuenciales y writer obligatorio solo en lite.
- La prueba de calidad/funcionamiento de 32B con >=64k se ejecutará por el usuario en su otro equipo; no hay resultado todavía.

Fuentes primarias, versiones observadas y límites: [revalidación](testing/t20-revalidation-2026-10-30.md). Consulta local de memoria parcial por `text_budget`: se aplican solo ADR-009 aceptado y Constitución leídos directamente; no se afirma inventario completo ni se promueve memoria. Capacidades seleccionadas: research-first, delivery-practices. Diseño preparado por el orquestador siguiendo el rol architect, sin subagente ni acreditación de identidad nativa. T-21 sigue abierta.
