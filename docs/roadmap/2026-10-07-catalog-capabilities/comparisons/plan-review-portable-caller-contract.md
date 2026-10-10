# Invocación portable de la revisión de planes

El bloque21 completa el caller de la puerta `plan-ok` existente de `/dev-cycle`.
Las macros T-05/T-11/T-13/T-14/T-15 conservan sus estados y criterios globales.
La implementación y QA publicadas de los bloques19 y20 no se reabren.
Las skills siguen aplazadas. Este contrato complementa el
[contrato de revisión](plan-review-integration-contract.md), sin otro dueño,
almacén, comando de aprobación, backend o máquina de estados.

## Contrato de invocación

- El shell real decide la receta Bash o PowerShell. Un nombre de runtime no
  demuestra disponibilidad de shell o intérprete. Python debe ser un ejecutable
  real cualificado; un alias WindowsApps vacío no satisface esa precondición.
- Proyecto autorizado, iniciativa relativa exacta y runtime son entradas
  explícitas. No se cambia al worktree después de abrir ni se elige la última
  iniciativa por fecha. Los argumentos se pasan como arrays y valores literales.
- La procedencia activa del runtime permite seleccionar un bundle explícito.
  Sin ella, las seis raíces existentes mantienen precedencia proyecto/usuario.
  Sólo se acepta un bundle con dueño, `plan-review-open.py` y builder presentes juntos. Dos bundles
  completos en la misma raíz son ambiguos. Una instalación parcial seleccionada
  explícitamente no se completa tomando otro builder.
- `open` y `serve` son pasos distintos. Antes de servir, el caller valida
  envelope, selección, puerta, versión y vista completa/vigente.
  El comprobador ejecutable `plan-review-open.py` lee JSON acotado por stdin,
  rechaza claves duplicadas/valores no finitos y devuelve sólo ID/versión.
  Su resultado `approval_granted: false` no aprueba ni escribe estado.
  El consumidor del recibo es histórico: puede pertenecer a otro runtime o ser
  null si abrió el panel. No se compara como identidad del caller actual;
  su procedencia se conserva en la traza de sesión, sin otro almacén de aprobación,
  y no autentica ni autoriza la decisión.
  No basta exit0. El servidor conserva un handle/PID propio y URL privada;
  receive/ack se ejecutan en otra operación sin esperar su terminación.
- `receive → validación → ack → validación → view/current` mantiene el dueño
  común. Waiting, vista parcial, otra puerta, versión obsoleta, conflicto o
  ack fallido no autorizan trabajo por esta decisión.
- Aprobar permite sólo el alcance autorizado. Pedir cambios pasa comentarios
  como datos al planner ya autorizado. Una autorización conversacional suficiente
  conserva su vía y no exige otra confirmación por un fallo opcional.
- La retoma conserva delivery/decision IDs y consulta ledger/plan actuales.
  Ack no prueba que los efectos se hayan ejecutado; deduplicar no omite trabajo
  pendiente. El panel no lanza agentes ni confirma consumo.

## Evidencia exigida, separada por alcance

Las recetas se ejecutan literalmente desde el comando canónico en fixtures OWN,
con homes/env aislados y sin credenciales, modelos ni corpus del consumidor.
Comprueban las seis raíces, precedencia, espacios/Unicode, argumentos literales,
bundle común, ambigüedad, runtime inválido y fallo de open antes de servir.
Un recorder sintético verifica argv; no acredita dueño real, servidor vivo,
decisión humana, carga de comando por host ni obediencia de un modelo.

La regresión B1 usa dos aperturas reales del dueño en cada fixture propia:
primero Codex o panel sin consumidor, después Claude. Comprueba mismo ID/versión,
registro histórico intacto y validación ejecutable exit0 sin mutar el estado.
Los negativos rechazan envelope/selección/puerta/vista/versión inválidos; las
recetas de ambos shells no sirven si el dueño devuelve exit0 con otra puerta.
Esta prueba entrega validación del caller, sin atribuir aceptación UI o ejecución
del workflow por un modelo.

La prueba del owner/servidor real debe conservar selección, versión, IDs,
delivery, ack, vista vigente, historial y proceso servidor propio. La UI requiere
un navegador real para comentarios, approve, request_changes, cierre sin decisión,
stale y conflicto. Un bloqueo de navegador se conserva sin alterar protecciones;
HTTP o Node no se presentan como aceptación UI.

Cada cliente real debe cargar y expandir su entrada nativa desde el bundle
verificado. Se registra binario/versión, entrada, cwd/env propios, fuente/SHA,
handle/sesión y payload expandido completo. Un proveedor sintético loopback con
cero toolcalls puede probar expansión sin inferencia externa; no prueba que un
agente siga el circuito. Pasar manualmente el cuerpo como prompt, usar etiquetas
runtime o comprobar `--help` tampoco acredita carga de `/dev-cycle`.

La continuidad por agente necesita evidencia adicional del cliente actuando
contra esa decisión, sin toolcalls forzadas por un stub. Se conserva pendiente
cuando no está medida. No se cierra T-11/T-13 ni el objetivo global sumando
resultados que cubren alcances diferentes.

Lint, exports, evals, alcance, enlaces y ledger deben corresponder al bundle
final revisado; Bash/Linux y PowerShell/Windows se identifican separadamente.
Las primeras pruebas Bash en Windows no se atribuyen a Linux.
