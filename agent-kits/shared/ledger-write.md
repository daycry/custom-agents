# Escritura del ledger

Lee este fragmento solo al cambiar el estado de una tarea, registrar un RED o
abrir una revisión. Resuelve `SHAREDKIT` con las raíces del runtime, en el mismo
bundle que el rol. Usa preferentemente `ledger-write.py`; con `perfil: lite` es
obligatorio. El orquestador escribe las evidencias devueltas por sus revisores.

```bash
python3 "$SHAREDKIT/ledger-write.py" state docs/roadmap/<iniciativa>/tasks.md --task T-01 --state en-progreso --json
python3 "$SHAREDKIT/ledger-write.py" red docs/roadmap/<iniciativa>/tasks.md --task T-01 --test tests/test_x.py::test_x --error "resultado observado" --date AAAA-MM-DD --json
python3 "$SHAREDKIT/ledger-write.py" review docs/roadmap/<iniciativa>/tasks.md --tasks T-01,T-02 --attempt 1 --summary "Fase actual" --json
```

- `state` modifica el estado y los contadores de progreso, sin marcar criterios
  ni decidir que se han cumplido. Antes de `completado`, el responsable comprueba
  y marca todos sus criterios. El escritor rechaza un cierre sin criterios
  explícitos o con casillas pendientes. No cierra la fase, QA ni la iniciativa.
- `red` añade una evidencia de una sola línea en su tarea, sin duplicarla. Exige
  fecha `AAAA-MM-DD`; rechaza secretos y caracteres que creen líneas nuevas.
  Registra el fallo observado antes del código; el script no ejecuta el test.
- `review` abre la cabecera canónica y deja «sin veredicto». No escribe gaps ni
  aprueba una revisión. Conserva el máximo de tres intentos y la secuencia por
  tareas; no cambies sus IDs para reiniciar el contador. El responsable completa
  la tabla de veredictos según `adversarial-review` y valida después el ledger.
- `--dry-run` calcula la salida y sus hashes sin crear estado ni escribir.
  `--expected-sha256 <hash>` rechaza una lectura obsoleta con exit3; tras ese
  conflicto, relee y revisa el cambio antes de preparar otra escritura.

Exit0 correcto (incluido idempotente); exit1 ledger o transición inválidos;
exit2 entrada/E/S no disponible; exit3 conflicto; exit4 lock ocupado o timeout.
Un fallo no se transforma en progreso ni autoriza otro intento de revisión.
Los avisos existentes del linter siguen visibles, sin reparación incidental.

El archivo debe ser un `tasks.md` regular de hasta 256 KiB. Conserva contenido
ajeno, BOM UTF-8, LF/CRLF uniformes y permisos POSIX; rechaza enlaces, hardlinks,
rutas con traversal y UTF-8 inválido. Para ledgers mayores, archiva primero con
`ledger-archive.py`; no aumentes el límite para saltar la validación.

Cada carpeta de iniciativa conserva `.ledger-write/.lock`, ignorado por el
`.gitignore` propio de ese directorio. Es un lock cooperativo del sistema: no se
borra ni se fuerza por antigüedad. Un `.gitignore` existente se respeta. La
publicación usa temporal hermano y reemplazo atómico, sin fallback de truncado.
No constituye un sandbox contra sustituciones concurrentes de directorios;
otros editores deben cooperar y los cambios observados antes de publicar se
rechazan. Un fallo de durabilidad posterior al reemplazo puede haber publicado:
reconcilia el hash del archivo antes de repetir, sin asumir rollback.

Instalación ordinaria parcial sin Python o sin este kit: avisa y conserva el
fallback de edición del ledger con `ledger-lint.py`; no inventes un recibo del
escritor. En lite, esa ausencia impide despachar trabajo hasta restaurar el kit
o elegir explícitamente un perfil ordinario. Las puertas de TDD, revisión y QA
permanecen activas en ambos casos.
