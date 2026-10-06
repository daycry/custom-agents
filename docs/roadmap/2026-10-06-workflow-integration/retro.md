---
retro: workflow-integration
fecha: 2026-10-06
estado: cierre-tecnico-verificado
---

# Retro — núcleo común de capacidades

El núcleo integra selección de guías en diez roles y ambos ciclos, briefs
acotados, seis guías consolidadas/nuevas, evaluación de resultados y contexto AST
opcional. El panel usa funciones y responsabilidades propias: agrupa hooks por
evento, describe cada acción y permite navegar por menú y seis etapas del flujo.
La entrega incluye 27 skills y 14 comandos. Son adaptaciones selectivas;
inventariar 455 piezas no equivale a integrar ni revisar funcionalmente toda la
biblioteca. Las fases posteriores están en
[INTEGRATION-ROADMAP.md](../../INTEGRATION-ROADMAP.md).

Tres intentos independientes cierran cinco gaps verificados: referencia histórica
inventada, dependencia obligatoria de tomllib, redacción tras JSON, entero extremo
y comprobación repetida de rutas AST. Los refinamientos solicitados del panel
añadieron regresiones para agrupación, cabeceras, plantilla, menú e historial y
contenido por etapa. El tercer intento A+B+C+D termina con cero gaps introducidos
pendientes. El cierre no cuenta hallazgos corregidos como deuda aceptada.

Windows destapó un oráculo incorrecto del timeout: una marca escrita durante la
limpieza no demostraba que el proceso siguiera vivo al retornar. Ahora el test
exige fixture iniciada y comprueba su PID; una variante sin limpieza reproduce el
rojo. El instalador de producción no cambia. Una propuesta GOT-016 queda local,
ignorada por Git y sin promoción automática de conocimiento.

Puertas finales: Linux 3903 passed/29 skipped/8 subtests, Node Linux 131 passed/3
skipped, Node Windows 134 passed, consola 459 passed, Edge 7 passed y qa-gate
VERDE. Cobertura de los cinco archivos Python cambiados 96,29 %, ninguno sin
datos. Linter sin errores con tres avisos previos; evals y 54 exports al día.
[testing/report.md](testing/report.md) recoge alcance, evidencias y límites.

No se solicitó presupuesto económico. El meter cerró la ventana parcial
2026-10-06T12:43:47Z…15:18:59Z (2h 35m de reloj), fuente estimado, sin respuestas
compatibles de esta sesión Codex: tokens, horas IA y euros nulos. Incluye esperas
y no cubre la publicación y documentación posteriores. No se usa como duración
total, desviación económica ni muestra de calibración. La mediana compatible
permanece en 531798.5 tokens/hora con seis muestras.

La siguiente fase prioriza extensiones propias en los tres runtimes. Se preservan
las piezas del usuario y se distinguen declaración, detección y disponibilidad
real; no se conectan MCP por descubrir su configuración. No se crearán paquetes
técnicos nuevos ausentes del catálogo de referencia ni se impondrán por stack.
El siguiente experimento de memoria debe medir recuperación, vigencia y utilidad;
el piloto AST actual no acredita esas mejoras ni sustituye la memoria gobernada.

La comprobación remota de la rama se registra en tasks.md. PR, merge y release
quedan fuera de esta entrega.
