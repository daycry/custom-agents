# Seleccionar y revisar el contenido de un commit

[English](en/COMMIT-SELECTION.md) · **Español**

El cierre de `/dev-cycle` usa una lista explícita de archivos para cada commit
lógico. La selección conserva el staging de otros archivos y sigue las puertas
de alcance, revisión y pruebas del ciclo.

`agent-kits/shared/scope-check.py` es el dueño de la proyección y su revalidación.
`agent-kits/shared/commit-selection.py` ofrece una CLI de solo lectura: no hace
staging, commits ni escrituras de objetos. El orquestador ejecuta Git después de
revisar el resultado.

## Procedimiento

1. Elige archivos relativos exactos. No uses directorios, globs, rutas absolutas
   ni traversal. Para un archivo nuevo, registra explícitamente sólo el elegido
   con `git --literal-pathspecs add --intent-to-add --pathspec-from-file=- --pathspec-file-nul`.
   Envía por stdin la lista UTF-8 con un NUL después de cada nombre. No reemplaces
   staging previo para resolver un conflicto.
2. Con el `$SHAREDKIT` resuelto por el ciclo, ejecuta
   `python3 "$SHAREDKIT/commit-selection.py" preview --root "$PWD" --path <archivo>`.
   Repite `--path` para cada archivo. Conserva el JSON en un temporal del caller
   fuera de Git. Revisa `seleccionados`, `no_seleccionados`, `staged_ajenos`,
   `conflictos`, `limites` y el patch. Exit 0 requiere ausencia de conflictos;
   no sustituye la revisión ni acredita quién preparó un cambio.
3. Inmediatamente antes de escribir el commit, envía ese mismo JSON por stdin a
   `python3 "$SHAREDKIT/commit-selection.py" validate --root "$PWD"`.
   Sólo exit 0 permite continuar. Si cambió HEAD, índice o selección, genera y
   revisa un nuevo preview; no sustituyas silenciosamente el aprobado.
4. Ejecuta `git --literal-pathspecs commit --only --pathspec-from-file=- --pathspec-file-nul -m <mensaje>`.
   Envía exactamente los nombres revisados por stdin, UTF-8/NUL. Conserva los
   hooks normales de Git. No uses staging global, un índice temporal manual ni
   opciones que omitan la verificación.
5. Comprueba el commit real: sólo paths seleccionados, blobs y modos coincidentes
   con la proyección; entradas ajenas conservan modo/OID/stage y contenido staged.
   Los seleccionados coinciden en HEAD e índice, sin reversión staged residual.
   Si un hook, editor u otro proceso alteró el resultado, informa la discrepancia
   sin reset, amend o nuevo commit automático.

Los nombres de archivo viajan como argumentos y registros NUL, no como texto de
comandos construido por interpolación. En PowerShell, usa un pipe binario para
los registros: un pipe de texto puede cambiar delimitadores o codificación.

## Resultado y límites

| Operación | Exit | Significado |
|---|---|---|
| `preview` | 0 | Proyección disponible y sin conflictos |
| `preview` | 1 | Conflictos declarados; no hacer commit |
| `preview` | 2 | Selección inválida |
| `validate` | 0 | Snapshot válido frente a la relectura |
| `validate` | 1 | Snapshot inválido, alterado o desactualizado |
| Ambas | 3 | Dependencia, lectura o presupuesto indisponible |

El snapshot incluye HEAD, SHA del índice observado, estados y modos de archivos,
blobs proyectados y patch exacto en `patch_base64` con `patch_sha256`. `patch` es
una presentación derivada; `patch_display_lossless` indica si conserva el texto
UTF-8. Para evidencia exacta usa los bytes base64 y su SHA.

El lector limita los cuerpos seleccionados a 8 MiB por lado y 32 MiB acumulados
entre HEAD y worktree. El JSON de entrada/salida tiene un tope de 64 MiB. Un filtro
Git custom seleccionado queda como conflicto; no se ejecuta para inventar un
blob. Diff externo y textconv están desactivados para la lectura. Python no abre
cuerpos ajenos, aunque Git puede leer worktree para enumerar cambios. La lectura
del índice es metadata Git y no constituye un sandbox de metadatos.

La revalidación y el commit son operaciones separadas: no hay atomicidad frente
a editores, hooks o escritores arbitrarios. El SHA completo del índice cambia
legítimamente después del commit; se comprueba la conservación de entradas
ajenas, no igualdad byte a byte del índice entero. `snapshot_id` prueba integridad
del contenido observado, no autenticación ni aprobación humana.

Sin helper o ante un error, el commit queda pendiente con su motivo. El trabajo
permitido puede continuar. La selección no concede autorización de push, merge,
PR o release.
