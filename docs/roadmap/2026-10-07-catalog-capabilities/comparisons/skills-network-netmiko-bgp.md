# Red: automatización Netmiko, BGP, validación de configuración y salud de interfaces — S184–S187

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **25.168 bytes/706 líneas**, sin recursos locales.
[network-netmiko-bgp-reading-evidence.json](network-netmiko-bgp-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún equipo. Propuestas para T-08.

## Decisión común

Las cuatro piezas son la familia que el bloque de transporte y red
(`skills-operations-session-context.md`, S034) dejó pendiente: allí se decidió
**conservar y ampliar** mediante una especialidad opcional propuesta
`skills/network-operations/` con `references/ios-review.md`, y que «las otras
referencias de red se decidirán tras leer sus cuerpos». Se mantiene esa decisión
y sus condiciones: método común, sin Netmiko, SSH ni cuentas como requisito global
del plugin; ejecutar solo con herramienta disponible, inventario concreto y
alcance del usuario; sin acceso al equipo, el resultado es revisión estática y
lista de verificaciones pendientes. No contradice S127–S130 (red doméstica,
fuera del bundle): aquello era montar una red; esto es revisar y diagnosticar
configuración de equipos, la misma tarea que S034.

Las cuatro coinciden con la disciplina del plugin: **primero solo lectura**,
cambios en ventana aprobada, evidencia antes/después y nada de desmontar ACL o
cortafuegos para diagnosticar.

## S184 — Automatización SSH con Netmiko

`6.046 bytes/174 líneas`. Recogida de solo lectura con timeouts, lote acotado con
`ThreadPoolExecutor`, parseo con TextFSM conservando la salida cruda y un patrón
de cambio protegido (simulación por defecto, captura antes/después, guardar la
configuración como paso aprobado aparte).

| Ejemplo | Problema | Adaptación |
|---|---|---|
| `collect_show` captura solo tres excepciones de Netmiko | Cualquier otra (rechazo de conexión, tipo de equipo inválido) sale por `future.result()` y aborta el lote | Contradice su checklist («fallos por equipo sin detener el lote»): capturar por equipo y clasificar |
| Cambio habilitado con `APPLY_NETWORK_CHANGES=1` | Una variable de entorno que el propio agente puede fijar no es una aprobación | Mismo criterio que en S112: la puerta no la abre quien actúa; aprobación explícita del usuario ligada al candidato |
| Evidencia antes/después impresa por pantalla | No queda registrada | Guardar la evidencia redactada junto al registro del cambio |

## S185 — Diagnóstico BGP

`5.641 bytes/168 líneas`. Triaje de solo lectura por vecino, familia de
direcciones y VRF; interpretación de estados; comprobación de transporte y de
política; expresiones de AS path con límites de token; acciones reservadas a
ventana de cambio.

Defecto relevante del parser de `show bgp summary`: exige un único token al final
de la línea, de modo que los vecinos en `Idle (Admin)` o `Idle (PfxCt)` (este
último, el corte por máximo de prefijos que la propia pieza manda revisar) **se
descartan en silencio**; tampoco reconoce vecinos IPv6 ni ASN en notación con
punto. Un parser que omite filas debe informar de las líneas no reconocidas,
no devolver una lista más corta.

## S186 — Validación de configuración antes del despliegue

`7.727 bytes/211 líneas`. Comandos peligrosos, credenciales y plano de gestión,
IP duplicadas y subredes solapadas, referencias huérfanas e higiene operativa,
con fragmentos Python y la regla «fallar cerrado ante comandos peligrosos y
credenciales» como puerta antes de automatizar.

| Ejemplo | Problema | Adaptación |
|---|---|---|
| Solapes de subred sin mirar `vrf forwarding` | Subredes iguales en VRF distintas son legítimas y saldrían como error | Agrupar por VRF (la pieza BGP pide no asumir la tabla global) |
| `ipaddress.ip_interface(ip/máscara)` sin control | Una máscara no contigua lanza excepción y tumba el validador | Informar la línea como hallazgo |
| VTY: solo detecta `transport input ... telnet` | `transport input all` también admite Telnet y pasa | Tratar `all` (y la ausencia, según plataforma) como Telnet permitido |
| `\bformat\b` y `\breload\b` sobre cada línea | También casan en `description` y en textos libres | Excluir descripciones y banners del análisis de comandos |

Es la pieza con más valor de método: un **preflight determinista** que bloquea lo
destructivo y avisa de lo demás encaja con la doctrina de veredictos en scripts
con tests. Solo tendría sentido como script de la especialidad, con fixtures de
las correcciones anteriores, cuando un consumidor la active.

## S187 — Salud de interfaces

`5.754 bytes/153 líneas`. Contadores como tendencia (línea base, intervalo,
segunda captura), ambos extremos del enlace, separar descartes de entrada y
salida, autonegociación coherente en los dos lados.

Defectos del parser: la expresión llamada `DROP_RE` lee `output errors`, no
descartes, aunque la tabla y el diagnóstico giran en torno a los descartes; y un
contador que no aparece se registra como `0`, convirtiendo la ausencia en un
valor limpio. El plugin aplica la regla contraria en sus scripts (la métrica
ausente queda nula, nunca inventada). Tampoco reconoce cabeceras sin
«line protocol» de otras plataformas.

## Destino

Tres referencias de la especialidad opcional `network-operations` propuesta para
S034, cada una con sus correcciones: `diagnostics.md` (S185 y S187: triaje de
solo lectura, estados, tendencias de contadores), `config-preflight.md` (S186:
orden de validación y criterios de bloqueo) y `automation.md` (S184: lectura
acotada, inventario explícito, aprobación ligada al candidato). La regla de
evidencia redactada antes de enviarla fuera ya está fijada en S034. Activación y
fixtures en T-10/T-14, sin conexión a equipos salvo entorno autorizado.
