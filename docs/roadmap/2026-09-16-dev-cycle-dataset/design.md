---
design: dev-cycle-dataset
estado: aprobado
opcion_elegida: O1
spec: spec.md
evaluation: evaluation.md
plan: improvement-plan.md
---

# Diseno - adaptador de dataset sobre el propio dev-cycle

## Opciones consideradas

| Opcion | Descripcion | Decision |
|---|---|---|
| O1 | Adaptador de solo metadatos por defecto, `full-diff` opt-in separado, derivacion deterministica de outcome/validation. | **Elegida.** |
| O2 | Capturar el diff completo por defecto. | Descartada: alto riesgo de filtrar codigo propietario de proyectos consumidores; contradice el principio "cero acoplamiento de dominio" de `training-data-services`. |
| O3 | Un agente nuevo que "juzga" si una tarea es Gold. | Descartada: repetiria el error de crear un rol para una decision que ya toman scripts existentes (`qa-gate`, revision, `ledger-lint`) — mismo criterio que LES-013/ADR-011. |

## Mapeo tarea -> caso (modo `metadata`, default)

| Campo del caso | Fuente en el ciclo actual |
|---|---|
| `request.json` | `- **Descripcion**:` de la tarea `T-XX` |
| `context.json` | Opcion elegida de `design.md` (si existe), persona de dominio del brief, titulo de la spec/plan |
| `constraints.json` | `- [ ] Criterio de aceptacion` + `- **Archivos**:` (alcance declarado) |
| `trajectory.jsonl` | Lista blanca: ficheros tocados (rutas relativas, SIN contenido), comandos de `- **Verificacion**:`, resumen de `- **Changelog**:` — NUNCA el diff en modo `metadata` |
| `metrics.json` | Gaps por lente del ultimo intento de revision, nº de intentos (`T-XX-fix<N>` en `usage-meter`), tokens/horas medidos |
| `validation.json` | Derivado: `approved` SOLO si `qa-gate.py` exit 0 Y el ultimo intento de revision no tiene gaps `Critical`/`Important` pendientes |
| `outcome` | `success` (limpio al primer intento) · `failure` (hubo gaps o qa rojo) · `corrected` (hubo `T-XX-fix<N>` y cerro limpio despues) |
| `supersedes_case` | El intento con gaps -> su correccion (mismo criterio que la relacion fallo/correccion de `training-data-services`) |
| Aprobacion Gold | Paso 4 del ritual de cierre (Fase 6 de `/dev-cycle`): quien decide integrar la rama confirma `--approved-by-human` |

## Modo `full-diff` (opt-in explicito y separado)

`dev.json` distingue dos claves independientes:

```json
{"datasetCapture": {"enabled": true, "mode": "metadata"}}
```

vs.

```json
{"datasetCapture": {"enabled": true, "mode": "full-diff"}}
```

Activar `enabled: true` SOLO nunca incluye el diff (el default de `mode` es `metadata`). `full-diff` exige que el usuario lo escriba explicitamente y `/setup` lo explica con el riesgo en una frase antes de ofrecerlo.

## Derivacion deterministica de `outcome`/`validation`

El adaptador NUNCA pregunta al LLM "¿esto salio bien?". Lee, en orden:

1. `ledger-lint.py` sobre la tarea (coherencia del ledger).
2. El ultimo bloque `## Revision de dos lentes — intento N` de la iniciativa: gaps `Critical`/`Important` pendientes -> `failure`; sin ellos -> sigue.
3. `qa-gate.py` (o su registro ya ejecutado en el ledger): exit 0 requerido para `approved`.
4. Marcadores `usage-meter` `<slug>/T-XX-fix<N>`: su presencia marca `outcome: corrected` y liga `supersedes_case` al intento original.

Sin estas tres senales completas (p. ej. iniciativa sin revision o sin qa), el caso queda `pending` y no se propone para Gold.

## Particion anti-leakage: familia = iniciativa

La familia de un caso es la iniciativa completa (`docs/roadmap/<fecha>-<slug>/`), nunca la tarea suelta. Esto hereda directamente la regla de `training-data-services` (particion por familia entera) y evita que dos tareas casi identicas de la MISMA iniciativa (p. ej. una correccion y su original) queden repartidas entre train y benchmark.

## Que NO hace este adaptador

- No activa nada si `datasetCapture` no esta en `dev.json`.
- No decide Gold por si mismo: el flag humano sigue siendo obligatorio en `case-recorder.py`.
- No introduce un agente nuevo ni cambia las responsabilidades de `implementer`/`qa`/`reviewer`.
- No aplica a iniciativas de otros proyectos: cada proyecto que quiera esto escribe su propio adaptador equivalente.
