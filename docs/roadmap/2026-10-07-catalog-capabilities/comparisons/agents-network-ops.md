# Arquitectura, revisión y diagnóstico de red — A041–A043

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres definiciones completas: **13.466 bytes/340 líneas**. [agents-network-ops-reading-evidence.json](agents-network-ops-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

La especialidad de red está aparcada (D-143, `network-operations`, S034 y
S184–S187 en `skills-network-netmiko-bgp.md`). Allí se decidió que la red
funciona primero en solo lectura, con cambios en ventana aprobada y sin quitar
ACL para diagnosticar. Los tres agentes respetan esa disciplina y lo hacen con
permisos estrechos.

## A041 — network-architect

`4.823 bytes/106 líneas` · tools: Read, Grep · model: sonnet.
Diseño de red de campus, sede, WAN o híbrida: objetivo, requisitos que cambian
el diseño, topología, segmentación antes del hardware, plano de gestión, fases
con puertas y puntos de rollback.

**Comparación.** Sigue el patrón de `architect`, pero con dos diferencias.
`architect` compara 2-3 opciones con sus compromisos y deja la elección al
usuario (`agents/architect.md:5-9`); esta pieza elige una sola topología
(«Pick the topology», l.45). Además, diseña infraestructura, no el código del
repositorio, y su salida no entra en la cadena (`design.md`). Sus permisos
(Read y Grep, sin escritura) son más estrechos que los de `architect`.
**Defectos:** no compara alternativas, y remite a cinco skills
(`network-config-validation`…) que no viajan con el agente.

**Destino:** **Especialidad de proyecto** (persona o extensión) si un
consumidor declara red; hoy **sin destino** (D-143).

## A042 — network-config-reviewer

`4.351 bytes/106 líneas` · tools: Read, Grep · model: sonnet.
Revisa configuraciones IOS/IOS-XE: credenciales, community SNMP, acceso VTY,
ACL o route-maps referenciados pero no definidos, solapes de subred y comandos
destructivos en ventana. Veredicto PASS/WARNING/BLOCK.

**Comparación.** Aplica el contrato de `reviewer` (solo lectura, evidencia por
bloque, «sin hallazgos» válido) a ficheros que no son un diff de código. La
Lente C cubre IaC (`dockerfile`, `github-actions`, `kubernetes`, `terraform`;
`lens-prompts.md:28`), pero no configuraciones de equipos. La referencia
`config-preflight.md` de S186 ya está decidida dentro de la especialidad
aparcada. **Defectos:** PASS exige «no actionable findings» y WARNING cubre High
o Medium (l.94-97), así que con solo hallazgos Low el veredicto queda sin
definir. La salida pide «Tests checked» (l.90) en una revisión que no tiene tests.

**Destino:** **Sin destino** (D-143 aparcado).

## A043 — network-troubleshooter

`4.292 bytes/128 líneas` · tools: Read, Bash, Grep · model: sonnet.
Diagnóstico por capas OSI en solo lectura (L1/L2, L3, DNS, política), con causa
raíz, evidencia por comando, verificación y riesgo residual.

**Comparación.** El dueño del método es `debug-root-cause` (4 fases con
evidencia, `SKILL.md:14-50`). La caracterización del síntoma equivale a la
reproducción mínima, y «what it ruled out» a la lista de descartes de la Fase 2.
La pieza aporta una regla que la skill no escribe: «Confirm that the suspected
cause explains all observed symptoms» (l.36). La Fase 3 propia trata la
conjunción de causas, pero no obliga a contrastar la hipótesis con **todos**
los síntomas recogidos. En permisos, Bash permite lanzar `ping`, `traceroute` o
`dig` a destinos que da el usuario. No es pentest, pero el agente no fija
alcance: el activo de `nemesis` se limita a hosts locales. **Defectos:** los
`show …` son comandos de la CLI del equipo, que Bash no puede ejecutar sin una
sesión SSH no declarada (en la práctica, pide la salida al usuario, l.35); y
mete «homelab» en el alcance, cuando la red doméstica quedó fuera del bundle
(S127–S130).

**Destino:** una línea en `skills/debug-root-cause/SKILL.md`, Fase 3: «La
hipótesis tiene que explicar todos los síntomas recogidos en las Fases 1-2; un
síntoma que no explica es otra causa (conjunción) o señal de que la hipótesis
es falsa». El dominio de red sigue aparcado (D-143).
