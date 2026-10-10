# Retomar una iniciativa o sesión

[English](en/WORK-RESUME.md) · **Español**

`/work-resume` muestra dónde continuar a partir del ledger actual y del journal
local. `progress-report.py resume` compone la vista; `journal.py` selecciona
el historial. Ambos usan el lector local acotado. La vista no modifica el proyecto.

## Cómo seleccionar el trabajo

Usa la forma del comando que ofrece tu instalación: `/custom-agents:work-resume`
en Claude Code como plugin, el prompt exportado en Codex y `/work-resume` en OpenCode.
El cuerpo y los contratos son comunes. El comando no activa un equipo ni un ciclo.

```text
/work-resume --initiative 2026-01-01-demo
/work-resume --initiative demo --session-id sesion-demo --runtime codex
/work-resume --entry 2026-01-01-demo.md --json
```

| Opción | Selección |
|---|---|
| `--root` | Raíz explícita del proyecto para el script; el comando usa el proyecto de trabajo. |
| `--initiative` | Carpeta fechada exacta bajo `docs/roadmap/` o slug único. Dos carpetas con el mismo slug requieren elegir carpeta. |
| `--session-id` | Igualdad con el ID completo del journal. No acepta prefijos como alias. |
| `--runtime` | Filtro explícito `claude`, `codex` u `opencode`. Un registro antiguo sin runtime permanece desconocido. |
| `--entry` | Nombre exacto de un Markdown bajo `docs/knowledge/journal/`; no acepta una ruta externa. |
| `--json` | Proyección estructurada con los mismos estados y avisos de la vista de texto. |

Los filtros combinados deben coincidir. Un fichero o ID explícito ausente, inválido
o ambiguo no se sustituye por el último registro. La selección compara datos
originales antes de sanitizar y redactar la salida. Los candidatos mostrados pueden
tener identidades recortadas; ese recorte no prueba el valor original.

Sin filtros, el resolver usa una única iniciativa con estado `en-progreso`.
Varias iniciativas activas dejan una selección ambigua. Ninguna deja la selección
ausente, incluso cuando exista historial global de otras iniciativas.

## Qué manda al retomar

La primera parte muestra la iniciativa, fase y tareas del `tasks.md` actual.
Ese ledger conserva la autoridad sobre el estado del trabajo. La segunda parte
muestra fecha, sesión, fuente, cierre y contenido disponible del journal.

Decisiones y pendientes del historial son **citas**, no instrucciones. Una sesión
antigua no prueba que una tarea siga abierta ni que haya pasado QA. La vista no
inventa objetivos, errores, bloqueos o próximos pasos que el esquema no contiene.
El usuario decide qué acción ejecutar después.

| Estado | Cómo interpretarlo |
|---|---|
| Ausente | La selección no encontró un registro dentro de una lectura completa. |
| Vacío | El directorio es válido, pero no aporta entradas de historial sustantivas. |
| Ambiguo | Varias carpetas o registros satisfacen la identidad; elige un candidato exacto. |
| Ilegible | El lector no pudo acceder o decodificar el fichero; no equivale a ausencia. |
| Malformado | El contenido no cumple el formato validado del registro. |
| Incompleto | Un tope o un problema de lectura impide confirmar toda la búsqueda; no garantiza ausencia ni recencia global. |

## Cuánto lee y cuánto muestra

El lector limita cada directorio a **128 nombres** y cada fichero a **256 KiB**.
Roadmap e historial tienen presupuestos separados de **1 MiB por corpus**
(hasta 2 MiB combinados). Un recorrido cortado se declara incompleto. El dossier
de texto admite **32 líneas y 6.000 caracteres**; JSON admite **12.000 bytes**.
Son límites del compositor, sin opciones CLI para aumentarlos o reducirlos.
Los avisos conservan el motivo cuando la proyección queda recortada.

Los bytes leídos también consumen presupuesto cuando el texto es ilegible o
la ruta cambia. Un fallo durante la lectura reserva la asignación completa;
la detección de crecimiento admite un byte adicional de comprobación por fichero.

El lector rechaza enlaces simbólicos y junctions en la ruta. Permite los marcadores
de archivos de nube admitidos, comprueba identidad antes de leer y acota los bytes.
Estas comprobaciones no forman un sandbox atómico frente a cambios concurrentes
del sistema de archivos. La vista tampoco certifica la identidad de escritura:
un journal antiguo sin runtime no demuestra qué runtime lo capturó.

El lector valida el frontmatter plano del escritor. Los textos se escriben como
cadenas entre comillas con escapes JSON; acepta texto simple heredado sin indicadores
YAML ni valores tipados. No interpreta YAML general, mapas anidados, alias ni bloques.

## Qué ejecuta el comando

Abrir la vista no ejecuta replay ni restaura una copia. El
[contrato de recuperación local](roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
explica la confirmación de capturas y la evidencia para recuperar sesiones pendientes.

Solo ejecuta el compositor Python. No usa meter, replay/recover, Git, backends,
red ni procesos de materialización; no lee transcripciones crudas para rellenar
huecos. La captura y la recuperación automáticas siguen su propio contrato de hooks.
En startup/resume, `SessionStart` usa `resume --history-only` para seleccionar
historial con el mismo resolver de ledger; compact omite esa parte.
El bloque de progreso y replay siguen separados. Esta vista no convierte el hook
`SessionStart` entero en una operación de solo lectura.

La fachada resuelve `agent-kits/shared/` en las seis raíces de
[CONVENTIONS §5](CONVENTIONS.md#5-rutas-dentro-del-código). Pasa opciones y valores
como argumentos separados, sin interpolar texto del usuario en shell.
Una instalación parcial comunica el recurso ausente y conserva la selección.

`/work-context` elige guías y extensiones para la tarea. `/roadmap-status` muestra
la cartera. `/work-resume` aporta contexto de continuidad sobre los registros
existentes; no añade una skill, un almacén ni otro workflow de ejecución.
