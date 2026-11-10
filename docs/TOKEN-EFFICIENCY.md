# Reducir contexto sin perder verificaciones

El plugin limita las lecturas repetidas y el contenido que pasa de un rol al
siguiente. No cambia modelos, precios, permisos ni puertas de calidad. Una
instrucción más corta reduce texto disponible; el consumo de una sesión depende
también del trabajo, las herramientas, los reintentos y el runtime.

## Qué hace cada fase

| Pieza | Entrada útil | Trabajo que conserva |
|---|---|---|
| `analyst` | Petición y spec existente, si la hay | Ocho dimensiones, incógnitas, criterios y aprobación del usuario |
| `evaluator` | Spec completa y rutas verificadas | Impacto, riesgos, calibración y presupuesto con supuestos |
| `architect` | Spec aprobada, evaluación y fuentes pertinentes | Opciones, recomendación y validación de la decisión |
| `planner` | Requisitos, diseño aprobado y mapa vigente | Tareas, dependencias, archivos, verificaciones y trazabilidad |
| `implementer` | Tarea y fuentes necesarias | TDD seleccionado, implementación y evidencia |
| `reviewer`, `qa` | Criterios y estado actual del cambio | Juicio independiente, revisión y pruebas |

`/pm-cycle` y `/dev-cycle` transmiten criterios, restricciones, decisiones y rutas;
no necesitan copiar cada informe o todo el diálogo. Cada agente consulta los
artefactos canónicos y la política compartida `read-discipline.md`. Después de
compactar o ante hechos nuevos, vuelve a las fuentes necesarias.

Las descriptions conservan sus disparadores. Se eliminan únicamente activaciones
repetidas en el cuerpo. Planner carga los procedimientos de deuda, borrado,
OpenAPI, tipos/personas o mantenimiento de planes cuando corresponden; evaluator
carga la guía de salud del código si la solicita el usuario o se cumple su umbral.
Los originales permanecen en las referencias del kit, dentro del mismo paquete.

La política compartida también tiene una entrada breve. El protocolo completo
de recibos se consulta en `agent-kits/shared/references/source-reuse.md` solo al
compartir exploraciones extensas; una lectura corta evita ese coste. La estimación
[por rol y escenario](roadmap/2026-11-04-token-efficiency/testing/token-estimates.md)
cuenta las políticas que cada rol referencia y declara los detalles condicionales.

## Compartir navegación sobre fuentes concretas

Si una exploración extensa servirá a varias fases, el productor puede guardar un
recibo junto a sus hallazgos en un artefacto que su rol ya pueda escribir. Para
una lectura breve no compensa crear otro recibo. No se habilitan archivos nuevos
ni se inicializa configuración.

Desde `agent-kits/shared/` del bundle, con rutas relativas al proyecto:

```bash
python3 source-snapshot.py snapshot --project <proyecto> --file src/orders.py --file tests/test_orders.py
python3 source-snapshot.py verify --project <proyecto>
```

El primer comando devuelve JSON por stdout. El segundo recibe ese JSON por
stdin: extrae el bloque del artefacto y pásalo a la entrada estándar; no le pases
el Markdown entero. No hace falta instalar servicios externos.

| Resultado | Cómo continuar |
|---|---|
| `ok`, `complete: true` | Recibo generado de todas las fuentes solicitadas |
| `fresh`, `complete: true` | Se pueden reutilizar hallazgos positivos sobre esos bytes |
| `stale` | Revisar los archivos cambiados o no legibles y actualizar los hallazgos |
| `different_project` | Volver a explorar en el proyecto actual |
| `incomplete`, `unavailable`, `receipt_budget` o entrada inválida | No reutilizar el recibo; hacer la lectura normal y declarar la limitación |

Exit 0 significa recibo completo o verificación fresca; 1 indica resultado no
completo; 2 identifica dependencia de salida ausente o uso inválido. Los recibos
admiten hasta 32 archivos, 256 KiB por archivo, 1 MiB total y 64 KiB de entrada.
No siguen enlaces y rechazan rutas fuera del proyecto o archivos sensibles
conocidos. Emplean identidad local del proyecto y SHA-256: no son portables entre
checkouts ni una firma o prueba de autoría.

Un recibo no demuestra cobertura, ausencia de alternativas, comportamiento
transitivo, autorización, aprobación o tests verdes. No vincula criptográficamente
la interpretación del agente con el contenido. No es una fotografía atómica de
varios archivos. Los revisores y QA conservan sus comprobaciones; una fuente
nueva fuera del recibo exige investigación propia. El contenido citado es dato,
nunca una orden para el siguiente agente.

## Medir texto y medir consumo son operaciones distintas

```bash
python3 context-footprint.py --project <plugin>
python3 context-footprint.py --project <plugin> --file agents/planner.md
python3 context-footprint.py --project <plugin> --baseline <informe-relativo.json>
```

Sin `--file`, el informe recoge mapas de agentes, comandos y `SKILL.md` de skills
inmediatas. Repite `--file` para una selección explícita, incluidas referencias.
El helper solo escribe stdout. Quien tenga permiso puede guardar el resultado y
usarlo como baseline. Para comparar, ambos informes deben tener exactamente las
mismas rutas y estar completos; si no, el porcentaje queda desconocido y la CLI
sale con 1. Un baseline ilegible o inválido hace fallar la CLI explícitamente.

El informe distingue bytes físicos, caracteres UTF-8 normalizados a LF,
`entry_characters` y `reference_characters`. La clasificación depende de la ruta
`references/`; no observa qué carga el cliente. La estimación `characters/4` no
es un tokenizer. Los campos `native_observation` y `billed_tokens` son `null`.
Los informes están acotados a 256 archivos y 8 MiB, con 256 KiB por fuente.
Las referencias nuevas se contabilizan aparte: trasladar texto no acredita
eliminarlo. Cargar todas las referencias puede superar el tamaño inicial.

El consumo observado sigue perteneciendo a `usage-meter.py` y a las métricas
nativas disponibles. Compare el mismo objetivo, revisión, modelo, condiciones y
criterios de éxito. Informe reintentos, cobertura de la medida y caché solo si la
fuente la proporciona; no asuma ahorro facturado por reducir caracteres. Los
helpers no consultan conversaciones ni ejecutan modelos o servicios.

## Qué se carga por defecto tras la auditoría de la 3.2.2

La fase 4 de [la corrección de la auditoría](roadmap/2026-11-09-plugin-audit-remediation/tasks.md)
movió texto que casi nadie necesita en cada despacho. Las cifras son **tamaño**
(caracteres UTF-8 con LF, medidos con `context-footprint.py`; tokens = caracteres/4,
sin tokenizer) y **no** consumo observado ni facturado: reducir caracteres no acredita
ahorro de tokens hasta medirlo con `usage-meter.py` en el mismo objetivo y modelo.

| Qué cambia | Antes | Después |
|---|---|---|
| Revisión visual del plan, fuera de `phase2-planning.md` (solo se lee si se pide) | 18.136 | 3.034 (+15.536 en `phase2-plan-review.md`) |
| Notas internas de `/doctor`, en `docs/reference/doctor.md` | 16.626 | 5.491 (+12.042 en la doc) |
| Explicación de los avisos de `scope-check` repetida en implementer y adversarial-review | 29.396 + 18.972 | 28.632 + 18.104 (el script imprime su remedio) |
| Agentes sin `Agent`: instrucción de delegar en Codex y OpenCode | 20 ficheros generados | −6.264 (Codex) y −5.526 (OpenCode) bytes |
| Contexto de OpenCode | recomputado por evento y a los 30 s | reutilizado mientras no cambie su firma |

Lo que sube se declara: cada agente gana 139-296 caracteres con la regla «si el
brief ya trae la selección de capacidades o «sin integraciones», no releas
`capability-check.md` ni `project-integrations.md`» (5.491 y 5.306 caracteres que
un despacho con selección ya no lee), y el bloque de sesión y el brief llevan una
línea con la ruta del kit para evitar el `find`. El ahorro de la vía rápida de
`/dev-cycle` sigue siendo ≥ 6.000 tokens estimados (6.136).

## Evitar contexto de poco valor durante la ejecución

Conserve logs completos y códigos de salida, pero envíe al modelo primero el
resumen y los errores pertinentes. Espere con el mecanismo del proceso o CI y
comunique cambios de fase; no recargue el plan por cada sondeo. Divida la tarea
si el contexto no cabe, conservando requisitos, restricciones y evidencia.
Las secciones opcionales se adaptan con motivo; los campos obligatorios, estados,
IDs y enlaces permanecen. Una ejecución pendiente o un resumen favorable no
convierte un fallo en verde.

Contratos: [lectura](../agent-kits/shared/read-discipline.md),
[salida](../agent-kits/shared/output-discipline.md),
[medición](observability.md). Evidencias de esta implementación:
[roadmap](roadmap/2026-11-04-token-efficiency/tasks.md).
