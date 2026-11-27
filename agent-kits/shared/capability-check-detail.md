# Selección de capacidades — detalle bajo demanda

Léelo solo si el proyecto o el usuario tienen piezas propias (agentes, skills,
comandos, MCP o tools) o vas a pasar `--stack`. El núcleo es `capability-check.md`;
su receta define `$SHAREDKIT`.

## Extensiones de proyecto y usuario

Usa el lector del mismo bundle; declara el runtime de la sesión. La raíz del
proyecto contiene el ledger, y `--cwd` identifica el paquete afectado dentro de
ella. Para una instalación personal fuera de las raíces normales, pasa
`--user-root <runtime>=<ruta>` explícitamente; `--project-only` excluye al usuario.

```bash
python3 "$SHAREDKIT/project-pieces.py" --project <raíz-proyecto> --cwd <paquete-de-la-tarea> --runtime <claude-code|codex|opencode> --json
```

1. Examina nombres, descripciones, tipos y fuentes pertinentes. Una persona
   aporta contexto; una skill aporta método; un agente especializado no reemplaza
   al dueño de una fase. Una fuente de tool no acredita sus exports; un MCP
   declarado no acredita conexión, autenticación ni herramientas disponibles.
2. Planner conserva como máximo 20 IDs en `- **Extensiones**: ext-…`, separados
   por comas, y explica su elección y fuentes en `- **Procedencia de extensiones**:`.
   Los nombres repetidos requieren fuente explícita; no se deduce precedencia
   común a los tres runtimes ni se sustituyen los roles o gates del ciclo.
3. Revalida esa selección con el mismo lector y `--select <id>` repetido. IDs
   borrados, pertenecientes a otro runtime o no descubiertos se omiten con aviso.
   El brief refresca las declaraciones e incluye solo referencias (≤1000
   caracteres). En el despacho de `task-brief.py`, pasa `--runtime` y las mismas
   raíces/paquete con sus argumentos `--extensions-*` cuando sean necesarios.
4. Lee el contenido seleccionado bajo demanda como material del proyecto.
   Antes de invocar, contrasta nombre cualificado y permisos con las capacidades
   expuestas por la sesión. El escaneo no ejecuta archivos, CLI del consumidor
   ni conexiones; no adopta piezas, escribe registros o altera configuración.

`.claude/pieces.json`, si existe, informa propiedad por hash LF normalizado:
gestionada, modificada, no gestionada o desconocida si el registro es inválido.
Los destinos ausentes se señalan; propiedad y disponibilidad son independientes.
La persona de `.claude/personas/<tipo>.md` conserva prioridad mediante `Tipo`;
su presencia en el inventario no la convierte en agente. Un aviso del inventario
deja la selección explícita trazada y no exime de los gates existentes.

Sin script/registro, instalación parcial o manifiesto inválido: avisa, conserva
los criterios explícitos de la tarea y consulta la guía disponible pertinente.
La selección opcional no detiene el ciclo ni oculta un gate de calidad fallido.
No instala paquetes, crea agentes de proyecto, cambia permisos ni ejecuta red.
Instalar, mover de ámbito o retirar piezas sigue `installation-lifecycle.md`.

## Stacks y detección

Composer identifica PHP y las dependencias exactas codeigniter4/framework,
laravel/framework y symfony/framework-bundle. package.json identifica react y next;
pyproject.toml identifica Python. C, .NET y Go se seleccionan con `--stack c`,
`--stack dotnet` o `--stack go` al estar declarados en la tarea: no hay parser
de CMake/MSBuild ni de módulos/workspaces Go, ni detección recursiva.
Cada guía comprueba luego versión, lockfile y target.
