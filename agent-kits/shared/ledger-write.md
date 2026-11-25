# Escritura del ledger

Lee este fragmento al registrar un RED, una revisión o una corrección de estado.
Resuelve `SHAREDKIT` en el bundle del rol. El orquestador registra las evidencias
de los revisores. Los scripts de traspaso aplican los estados en todos los perfiles.

```bash
python3 "$SHAREDKIT/ledger-write.py" state docs/roadmap/<iniciativa>/tasks.md --task T-01 --state en-progreso --json
python3 "$SHAREDKIT/ledger-write.py" red docs/roadmap/<iniciativa>/tasks.md --task T-01 --test tests/test_x.py::test_x --error "resultado observado" --date AAAA-MM-DD --json
python3 "$SHAREDKIT/ledger-write.py" review docs/roadmap/<iniciativa>/tasks.md --tasks T-01,T-02 --attempt 1 --summary "Fase actual" --runtime codex --json
python3 "$SHAREDKIT/ledger-write.py" verdict docs/roadmap/<iniciativa>/tasks.md --tasks T-01,T-02 --attempt 1 --result gaps --gap-tasks T-02 --runtime codex --json
python3 "$SHAREDKIT/ledger-write.py" reconcile docs/roadmap/<iniciativa>/tasks.md --tasks T-01,T-02 --dry-run --json
```

- `state` permite correcciones explícitas (por ejemplo, un rojo de QA) y recalcula
  el estado declarado de la fase y los contadores de progreso. Antes de
  `completado`, el responsable comprueba y marca todos sus criterios. El
  escritor rechaza un cierre sin criterios explícitos o con casillas pendientes.
  El veredicto de QA y el cierre de la iniciativa conservan sus propias puertas.
- `red` añade una evidencia de una sola línea en su tarea, sin duplicarla. Exige
  fecha `AAAA-MM-DD`; rechaza secretos y caracteres que creen líneas nuevas.
  Registra el fallo observado antes del código; el script no ejecuta el test.
- `review` abre la cabecera canónica, deja «sin veredicto» y mueve sus tareas a
  `en-revision` en la misma escritura. `--summary` admite solamente IDs ya declarados
  en `--tasks` para que `verdict` identifique la misma cabecera. Conserva tres intentos por ciclo y la secuencia
  por tareas; no cambies sus IDs para reiniciar el contador. Tras el 3.º con gaps,
  «seguir» abre un ciclo nuevo solo con el OK del usuario citado:
  `review --attempt 4 --new-cycle-ok "<cita>"` (intentos 4-6; el 7 abre el último).
- Completa la tabla de evidencia y llama a `verdict` sobre la misma cabecera.
  `gaps` reabre los IDs con Critical/Important pendientes (de la tabla o de
  `--gap-tasks`); `limpio` cierra con los criterios marcados y fecha `Cerrada`.
  La columna `Tarea` admite IDs sueltos, con comillas invertidas o sufijo
  `-fixN`, y listas separadas por `,`, `;`, `+`, `&`, `y`, `/`, `→` o
  `–`. Los rangos con `..`, ` a `, `–` o `-` incluyen hasta 500 tareas,
  incluidos los extremos. Un rango en la cabecera también menciona todas esas
  tareas. Cada ID se ajusta a la grafía del ledger si hay una sola tarea con ese
  número. Un alias ambiguo bloquea a todas las candidatas. El linter indica la línea de cada alias ambiguo o desconocido.
  Una nota de contexto admite un único ID precedido por `origen`,
  `mensaje de`, `ver` o `cf.` (p. ej., `T-21 (origen T-03)` afecta a T-21).
  `todas` y `Fase N` aplican el gap a toda la sección. Si la nota es ambigua,
  también cuentan sus IDs. Una celda no reconocida, incluidos los rangos
  encadenados o demasiado largos, afecta a la unión de sus IDs con los de
  la cabecera y las filas reconocidas. Los tramos inversos y encadenados incluyen sus tareas
  intermedias. Por encima del tope se consultan los IDs existentes en el catálogo.
  Las decisiones usan las filas legibles y conservan los requisitos explícitos
  de cada operación. Si el total numérico de Critical e Important en la cabecera
  supera el número de filas legibles de esos grados, `ledger-lint.py` emite un
  aviso con la línea. El aviso se omite si revisiones posteriores cubren todas
  las tareas afectadas con un veredicto o filas legibles.
  Un rechazo conserva el ledger byte a byte. Valida después con `ledger-lint.py`.
- `usage-meter.py start/close` y `task-brief.py --dispatch` usan el mismo writer.
  `handoff` acepta el ledger y `--task`, o `--artifact` del medidor en el proyecto actual.
  Los inicios y cierres conservan tareas terminales. El inicio desde `en-revision`
  requiere un veredicto `gaps` aplicable a esa tarea. Una revisión abierta devuelve
  `review_open` y deja el estado intacto. Los cambios efectivos generan
  eventos de actividad. Indica `--runtime claude|codex|opencode`. La variable
  `CUSTOM_AGENTS_RUNTIME` se usa cuando omites el flag y el marcador no indica
  el runtime. Un runtime sin identificar se registra como `unknown`.
  Un traspaso sin cambio consulta la tarea sin tomar el lock de escritura ni
  ejecutar el linter. Un cambio valida una vez la entrada bajo el lock.
  Si `usage-meter.py start` agota la espera del lock del medidor o falla al
  guardar, devuelve `marker_saved: false` con un aviso y el traspaso continúa.
- `reconcile` aplica revisiones ya registradas sin fabricar un intento.
  Las tareas sin veredicto histórico interpretable conservan su estado. Un gap
  histórico que consta como corregido en un fix requiere una revisión posterior
  de la misma tarea. Si hay un cierre, el writer registra `Cerrada`.
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

Si Python, el escritor o el ledger no están disponibles, avisa y sigue con el
traspaso autorizado. Conserva la evidencia y reintenta la transición cuando se
restaure el writer. La validación del perfil lite y las puertas de TDD, revisión
y QA permanecen activas.
