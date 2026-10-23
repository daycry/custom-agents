---
retro: project-extensions
fecha: 2026-10-07
estado: completado
---

# Retro — extensiones de proyecto y usuario

El lector compartido reconoce agentes, skills, comandos, personas, fuentes de
tools y MCP locales para Claude Code, Codex y OpenCode. Alimenta la selección
del ledger, los briefs y el panel; distingue origen, identidad, conflictos,
propiedad y disponibilidad. Las piezas se consultan bajo demanda, sin precargar
sus cuerpos ni ejecutar código o conectar servidores durante el inventario.

Se reutiliza O1 para leer propiedad, sin crear otra base ni adoptar piezas.
Las personas conservan prioridad proyecto→catálogo→sin persona. Los roles y
gates del ciclo mantienen sus responsabilidades. No se crean paquetes técnicos
ni se copian colecciones enteras por cantidad.

La revisión inicial necesita tres pases: cinco Important y un Minor, después
una corrección incompleta de identidad y finalmente cero gaps. Los contratos
nativos explican por qué no es correcto imponer el mismo frontmatter a los
tres runtimes ni separar conflictos Claude de comandos y skills. La prueba de
orden del filesystem evita inventarios parciales distintos para la misma fuente;
la prueba de carga evita concatenaciones cuadráticas de descripciones.

QA posterior descubre YAML MCP sin sangría. Se conserva el baseline revisado,
se reabre la tarea y se añade RED antes del fix. El delta se revisa por separado;
no se oculta como deuda ni se reinicia el contador del ciclo ya aprobado.
La evidencia de cada revisión permanece en tasks.md.

Las pruebas adicionales del cierre exponen tres oráculos de release no portables:
ruta POSIX, conversión LF/CRLF e identidad inferida por Git. Se corrigen solo
las fixtures temporales. Un ciclo A+B específico detecta además identidad por
config Git en variables de entorno; la regresión precede al filtro y el segundo
pase termina sin gaps. Release final: 27 passed en Windows y 27 en Linux;
comprobaciones documentales Windows: 557 passed. No cambia release.py ni Git
del consumidor. La publicación técnica previa y sus gates siguen siendo válidos.

Windows baseline: 698 passed/2 skipped; delta: 239 passed/2 skipped. Linux
completo: 4023 passed/29 skipped/8 subtests; delta: 702 passed/1 skipped.
Node Windows: 134 passed; Node Linux: 131 passed/3 skipped. Edge: cuatro
escenarios de extensiones y siete regresiones del bundle, todos verdes.
Cobertura ejecutable del diff: 92,16 %; exports 54 al día y evals 182 sin
errores. Los grupos se solapan. [testing/report.md](testing/report.md) delimita
qué demuestra cada ejecución y qué depende de la sesión nativa.

No se solicita presupuesto económico. El meter cierra la ventana parcial
2026-10-06T15:27:09Z…2026-10-07T09:22:58Z: 17h 56m de reloj, incluyendo esperas.
No hay respuestas compatibles de esta sesión Codex: tokens, horas IA y euros
son nulos; fuente estimado. No se inventa una estimación ni se usa el tiempo de
reloj como esfuerzo IA o nueva muestra de calibración. La mediana compatible
permanece en 531798.5 tokens/hora con seis muestras. La ventana no incluye
documentación ni publicación posteriores a su cierre.

La siguiente fase comparará funcionalmente el catálogo y probará el alcance
real de las guardias según runtime e instalación. Después se medirá recuperación,
vigencia y utilidad de memoria antes de decidir cambios. Reconocimiento de
extensiones no equivale a entregar esas dos fases ni la generación/adopción de
especialización. La publicación de esta rama se prueba en tasks.md; PR, merge
y release quedan fuera de la entrega.
