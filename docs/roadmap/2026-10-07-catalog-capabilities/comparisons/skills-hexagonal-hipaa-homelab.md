# Arquitectura hexagonal, HIPAA y red doméstica — S125–S130

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **47.247 bytes/1.243 líneas**, sin recursos locales.
[hexagonal-hipaa-homelab-reading-evidence.json](hexagonal-hipaa-homelab-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S125 — Arquitectura hexagonal (puertos y adaptadores)

`11.520 bytes/277 líneas`. Dominio sin dependencias de infraestructura, puertos de
entrada y salida, adaptadores en los bordes, raíz de composición, migración por
rebanadas verticales y pruebas por frontera.

**Comparación.** `architect` presenta 2-3 opciones de diseño con trade-offs y
`stack-practices/python.md` ya pide `Protocol` para dependencias por comportamiento
«sin añadir abstracciones para funciones sin variación». La pieza aporta una
opción de diseño completa y un **plan de migración por rebanadas** (estrangulador,
tests de caracterización antes de extraer, interruptor reversible por rebanada)
que encaja como alternativa en el `design.md` del architect. Correcciones:

| Ejemplo | Adaptación |
|---|---|
| `CreateOrderUseCase` autoriza el pago antes de guardar el pedido | Si el guardado falla, queda un cobro autorizado sin pedido; orden y compensación según backend-practices (transacción frente a servicio externo) |
| «Todo efecto externo es un puerto», incluidos logger y reloj | Para servicios pequeños es ceremonia; aplicar cuando haya variación real (criterio ya fijado en stack-practices) |
| `save` hace `insert` siempre | No admite actualizar; el repositorio debe expresar la semántica (crear frente a guardar) |
| Tests de contrato compartidos por puerto contra cada adaptador | **Conservar**: patrón útil y poco común |

**Destino.** Referencia opcional para `architect` («opción hexagonal y migración
por rebanadas»), sin imponer el estilo.

## S126 — HIPAA

`3.631 bytes/79 líneas`. Capa fina sobre S123: preguntas de decisión (¿es dato de
salud?, ¿entidad cubierta o asociado?, ¿hay contrato BAA con el proveedor?, acceso
mínimo necesario, auditoría) y reglas de no exponer datos en logs, analítica,
prompts o URL. **Fuera del bundle** junto con S120–S123. Idea general útil: los
proveedores externos, incluidos los de modelos, quedan **bloqueados por defecto**
hasta que conste que pueden recibir esos datos, coherente con la regla de
datos personales fuera de git y con `redact.py`.

## S127–S128 — Red doméstica: preparación y diseño

`7.782 + 4.432 bytes`. Inventario antes de cambiar la red, zonas de confianza por
VLAN, introducir un DNS local con respaldo, acceso remoto por VPN y secuencia de
cambios reversible; plan de direcciones, `home.arpa` y reservas DHCP.

**Comparación.** Dominio ajeno al ciclo de desarrollo. El método es ejemplar y
coincide con el del plugin: **primera respuesta de solo lectura** (inventario,
riesgos, plan, validación y vuelta atrás), no dar comandos sin plataforma
confirmada ni procedimiento de reversión, probar en un cliente antes de extender
el cambio y mantener siempre un camino de recuperación. Es la misma disciplina
que `/doctor` (solo lectura) y que el guardarraíl de nemesis (solo hosts propios).
**Fuera del bundle**; persona de proyecto si un consumidor gestiona redes.

## S129–S130 — Pi-hole y segmentación por VLAN

`9.592 + 10.290 bytes`. Instalación y operación de Pi-hole (Docker o instalación
directa, listas de bloqueo, DNS sobre HTTPS, registros locales) y configuración
de VLAN en tres plataformas con reglas de firewall.

**Comparación.** Mismo dominio y misma decisión que S127–S128: **fuera del bundle**.
Contradicciones internas que conviene anotar si alguien lo reutiliza: S129
recomienda `home.lan` como dominio local y a la vez cita `home.arpa` como el
estándar (S128 usa `home.arpa`); la instalación descarga y ejecuta un script
remoto (mitigado con «revisar antes»); y el compose publica el puerto 80 del
panel en todas las interfaces. S130 da reglas de firewall concretas por
plataforma sin el inventario ni la vuelta atrás que exige S127, y el bloque de
MikroTik solo crea la regla IoT→Trusted, sin aislar la VLAN de invitados.
