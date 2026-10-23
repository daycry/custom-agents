# Mantenimiento de la instalación: escanear, planificar, aplicar y deshacer

> Léela solo cuando haya que reconfigurar, mover de ámbito, limpiar o retirar
> piezas ya instaladas (del plugin, del proyecto o del usuario). Configurar
> opt-ins es `/setup`; diagnosticar es `/doctor`; juzgar la utilidad de una
> pieza es la skill `capability-audit`.

Este método no es otro instalador ni otro auditor. Ordena el trabajo de los
dueños que ya existen y separa siempre **mirar** de **cambiar**.

## Dueños

| Operación | Dueño | Límite |
|---|---|---|
| Instalar, actualizar o desinstalar el bundle por proveedor | `install/install.mjs` (`install`, `status`, `uninstall`, `--dry-run`) | `uninstall` borra solo lo que apunta el manifiesto; lo fusionado en un fichero tuyo no se borra y lo avisa |
| Opt-ins del proyecto (`rates.json`, `dev.json`, Jira, Confluence) | `/setup`, idempotente | No instala ni retira piezas |
| Diagnóstico de la instalación | `/doctor`, solo lectura | Informa y da el comando; no corrige |
| Utilidad, solapes y vigencia de una pieza | skill `capability-audit` | Solo propone conservar, consolidar o retirar |
| Propiedad de piezas del proyecto y del usuario | `project-pieces.py` y `.claude/pieces.json` | Gestionada, modificada, no gestionada o desconocida |
| Memoria técnica | `knowledge-curator` | Retirar memoria es marcarla obsoleta por curación, no borrarla |

Una pieza **gestionada** por el bundle no se edita ni se borra a mano: se
retira con el ciclo de vida del instalador o del runtime (`uninstall`,
actualización, desactivación nativa). A mano solo se toca lo del usuario.

## 1. Escanear (solo lectura)

Recorre cada canal por separado y conserva su fuente, su señal y su alcance:
agentes, skills y comandos; hooks; permisos; MCP; statusline y tareas
programadas; memoria; cachés e historial.

| Campo del inventario | Contenido |
|---|---|
| Ruta resuelta | Ruta real y ámbito (proyecto, usuario, local, plugin) |
| Runtime | Claude Code, Codex u OpenCode; cada uno con su propio contrato |
| Hash | Hash del contenido al escanear; sirve para detectar cambios antes de aplicar |
| Señal | Objeto roto, huérfano, duplicado, antiguo o sin uso observado |
| Evidencia | Qué se comprobó y con qué comando o lectura |
| Estado | `vivo`, `roto`, `huérfano` o `desconocido` |

Reglas del escaneo:

- **Una señal no es una prueba.** Un nombre parecido no prueba duplicado; la
  ausencia de logs no prueba desuso; la antigüedad no autoriza a borrar.
- Clasifica por la **configuración efectiva** del runtime (ámbitos, plugins,
  inclusiones). Buscar el nombre del fichero en dos `settings` no basta y da
  falsos huérfanos o falsos vivos. Si no se puede resolver: `desconocido`.
- **Declarado no es activo.** Un hook registrado no prueba que se dispare;
  un MCP declarado no prueba conexión. Para eso, `status` y `/doctor`.
- **Desactivar no es borrar.** Renombrar un directorio (p. ej. `.disabled`)
  no prueba que el cargador deje de descubrir su `SKILL.md`. Compruébalo con
  el listado nativo del runtime.
- En memoria, una entrada reciente no gana a una aprobada por ser reciente.
- Cada raíz de runtime se escanea con su contrato. No se traduce `~/.claude`
  a otro runtime por analogía ni se limpian todos los homes en recursivo.
  En Windows, rutas resueltas con las operaciones nativas.

## 2. Planificar la retirada por lotes

La salida del escaneo es una **propuesta verificable**, no una acción. Agrupa
en un lote acotado y deja fuera, por escrito, lo que no entra.

| Campo del plan | Contenido |
|---|---|
| ID | Estable dentro del lote (`R-01`, `R-02`…) |
| Elemento | Ruta resuelta, canal y hash del escaneo |
| Acción | Desactivar, mover, borrar o retirar un permiso; con el comando del dueño si lo hay |
| Motivo | Señal y evidencia del escaneo |
| Efecto esperado | Qué deja de cargarse o de ejecutarse |
| Copia de seguridad | Dónde quedará y con qué nombre único |
| Deshacer | Comando o pasos exactos para restaurar |
| Verificación | Comprobación independiente tras aplicar |

Distingue tres cifras de espacio: bytes que salen del runtime, bytes retenidos
en la copia de seguridad y bytes liberados de verdad. Mover no libera.

## 3. Autorizar

- La autorización es **concreta**: nombra el lote o sus IDs.
- Nunca se infiere de un calendario, de una regla genérica («limpia lo viejo»)
  ni de una autorización dada para otro lote.
- Una autorización ya dada sobre este plan cubre su aplicación: no se vuelve a
  preguntar. Solo se pregunta cuando falta una decisión.
- Si el plan cambia, por ejemplo porque un fichero cambió tras el escaneo, es
  un plan nuevo y necesita su propia autorización.

## 4. Aplicar

- El ensayo (`--dry-run`) y la aplicación usan las mismas entradas.
- Antes de cada escritura, compara el hash actual con el del escaneo. Si
  cambió, ese elemento no se toca y queda pendiente.
- Copia de seguridad única por elemento: nunca sobrescribe otra existente.
- Escritura atómica (fichero temporal y renombrado) y validación del JSON
  resultante antes de sustituir; así no se pierden ajustes concurrentes.
- Retirar un permiso de un ámbito no lo retira de otro: respeta la precedencia
  de ajustes del runtime y comprueba el permiso efectivo.
- Rutas y versiones externas se validan antes de usarse y se pasan como
  argumentos, nunca interpoladas en una orden de shell.
- Si la aplicación se corta a medias, registra lo hecho y lo pendiente y para.

## 5. Verificar y deshacer

- Verificación **independiente** del paso que escribió:
  `npx @daycry/custom-agents status`, `/doctor` y el listado nativo del runtime.
  El mensaje de éxito va después de verificar, no antes.
- Registro de la operación con **evidencia redactada**: sin valores de
  permisos completos, credenciales ni rutas personales.
- El registro de deshacer y las copias son **privados**: fuera del control de
  versiones y con retención definida (cuándo se borran y quién lo decide).
- Deshacer comprueba el hash de lo que restaura igual que aplicar.

## Qué NO hace

- No crea otro instalador, otro auditor semántico ni otro registro de piezas.
- No retira memoria: eso es obsolescencia por `knowledge-curator`.
- No vacía cachés, transcripciones ni historial de forma indiscriminada.
- No actúa sin un plan autorizado, aunque la señal parezca obvia.
