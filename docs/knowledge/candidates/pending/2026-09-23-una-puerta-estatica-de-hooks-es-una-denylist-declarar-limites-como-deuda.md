---
category: LESSON
evidencia: validated_case
fuentes: [docs/roadmap/2026-09-15-graphiti-memory/design.md, docs/roadmap/2026-09-15-graphiti-memory/tasks.md]
tags: [area:seguridad, agente:documenter, tipo:proceso]
project: custom-agents
scope: project
source: agent
confidence: medium
---
# Una puerta estática de hooks es una denylist: declarar sus límites como deuda, con propuesta de iniciativa

`graphiti-memory` necesitaba probar «no hay red desde hooks» sin poder ejecutar los hooks contra un
servidor real. `tests/test_graphiti_security.py` construyó una puerta ESTÁTICA (AST de cada `.py`
alcanzable + tokenización de `.sh`) que recorre `hooks/` y lo que alcanza, y bloquea binarios/
módulos de red, `subprocess`/`Popen`/`os.system`, imports dinámicos sin literal y citas a
ejecutables que no sabe escanear. Tras cerrar el bucle de revisión de la Fase 4 en 0 Critical/0
Important, quedaron 6 Minor (#187-#192) que son límites reales de esa técnica, no evasiones: el AST
solo mira el primer literal de una lista de argv, las listas de binarios/módulos no son
exhaustivas, un bloque `bash` con dos comandos se lee como unidad, la tokenización de CA-05 no
separa `--flag=valor`, la tabla de citas por nombre no comprueba que se use en el recorrido, y los
`.sh` no trocean por palabra los términos de red.

**Regla:** una puerta de seguridad estática (denylist de patrones conocidos) nunca es una prueba de
ausencia — es una prueba de que los patrones ya vistos no reaparecen. Sus límites conocidos se
declaran explícitamente como deuda (con el fichero:línea exacto de cada uno y la mitigación
vigente), no se dejan implícitos ni se disfrazan de «cerrado»; y si acumulan una cantidad que
justifica un rediseño (análisis por sitio de llamada en vez de por patrón), se proponen como
iniciativa futura con nombre propio en vez de arrastrarlos indefinidamente.

Evidencia: `design.md`, sección «Límites conocidos de la puerta estática de hooks (deuda declarada,
2026-09-23)»: *"La revisión de la Fase 4 (intento 3) cerró el bucle con 0 Critical / 0 Important …
Los que siguen son límites conocidos de una puerta ESTÁTICA (AST + tokens) … ningún script
alcanzable real los usa hoy, y la suite del repo los pinaría al primer cambio que los
introdujera"*, con los 6 puntos #187-#192 y la propuesta de cierre: *"Iniciativa futura propuesta:
`hooks-gate-hardening` — llevar la puerta estática de hooks a un análisis por sitio de llamada …
cerrando #187-#192."*
