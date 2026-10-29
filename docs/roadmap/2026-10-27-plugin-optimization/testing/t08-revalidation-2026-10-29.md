# Revalidación de F2 contra v2.1.0

Base vigente: `a157679afd27743b1dd1e1a7fa76444cca6aba2a`, `master` publicado como v2.1.0. El usuario autoriza «Sí, publicar F1 y continuar» el 2026-10-29. La PR #19 está fusionada; las CI de código y documentación pasan y el workflow 40891518461 publica ambos ZIP.

## Contraste de fuentes

El esqueleto sigue apuntando a responsabilidades existentes, pero las rutas y verificaciones requieren concreción. `session-context.sh` sigue teniendo 315 líneas; `dev-cycle.md`, 546 líneas y 53.732 caracteres. El fragmento `knowledge-check.md` tiene 108 líneas y 9.133 caracteres; su consulta gobernada incluye tanto legado como approved, por lo que condicionar solo a Kwipu/Graphiti perdería lectura local.

F1 cambia el launcher, el supervisor y los registros; el prefiltro del guard, la captura y sus garantías deben conservarse al reestructurar. El marcador de documentación sigue pasando por shell/Python para rutas aplicables. Los hooks de ledger siguen separados y cada uno extrae rutas; el de progreso además lanza Python para codificar JSON. El selector de lentes abre para detectar binario y vuelve a abrir para leer texto y componer prompts: se requiere conservar una lectura común para C/D.

El esqueleto citaba `tests/test_skill_index.py`; la suite vigente está en `agent-kits/shared/test_skill_index.py`. `knowledge-check-governed.md`, `session-context.py`, las referencias del comando y sus nuevos tests son entregables futuros explícitos, no ficheros cuya ejecución ya se atribuya. Las verificaciones concretas de T-09..T-19 distinguen suites existentes y tests que nacen en RED.

## Decisiones de alcance

- **C-15: ejecutar el spike**, acotado a dos horas y sin cambios productivos. El cierre de Job Object debe probar hijos y nietos en salida limpia, timeout y cancelación. La implementación T-16 depende de un go real. Dependencias nativas o rediseño fuera del alcance implican no-go motivado.
- **C-17: go condicionado después de C-09.** Resolver el bundle una vez por pieza; reutilizar la ruta observada y volver a asignarla en cada nuevo bloque shell. No asumir que variables de una llamada sobreviven a otra. Si no hay ahorro positivo y resolución segura con seis raíces, registrar no-go.
- **C-18: no-go inicial para el recorte productivo.** La sesión nativa acredita 27 capacidades descritas, pero no compara la activación con/sin índice. El criterio «sin degradar la activación» sigue intacto; no lo sustituimos por evals literales ni afirmamos que el ahorro previsto esté demostrado. Mantener el índice y documentar la cancelación condicional, salvo nueva evidencia válida antes del cierre de F2.
- **Memoria condicional:** `docs/knowledge/` en el consumidor es la señal de lectura del detalle local gobernado. Se mantienen las reglas de legado/approved, candidatos no consultables y ausencia de red desde hooks. El contexto de código y el journal conservan su lugar fuera de esa condición.
- **Referencias de dev-cycle:** dueño `agent-kits/dev-cycle/references/`; se resuelve mediante la regla 5. El núcleo conserva puertas y rutas a fases, sin copiar el cuerpo de la vía completa a quick-implement. Los tres runtimes y el paquete portable deben transportar las referencias necesarias.

## Estimaciones y límites de la recalibración

Se contrasta el presupuesto diferido con lo observado en F1: mediciones bajo carga variable, revisión con tres intentos, instrumentación temporal y pruebas reales de procesos. Los costes dominantes de prueba/revisión ya figuran en la estimación original; no hay fundamento medido para aplicar un nuevo multiplicador.

El meter de las ventanas actuales informa `sin_medida`: no hay transcripción compatible para obtener tokens, coste ni horas IA reales de implementación. Los bloques medidos históricos de generación del plan no equivalen al coste de implementar F1. Tampoco las horas de reloj ni la latencia de hooks sirven como horas IA. `CALIBRATION.md` mantiene su mediana compatible de 531.798,5 tokens/hora, sin nueva muestra de esta iniciativa.

**Resultado del contraste:** se conservan provisionalmente **69,0 h para F2 y 45,0 h para F3**, diferencia **0 h** frente al presupuesto diferido; su confianza no aumenta. No se calcula una desviación real de F1 inexistente ni se reduce la reserva por cancelar una opción antes de conocer el coste restante. La medición opcional degrada con aviso según la constitución y `usage-meter`; no detiene la implementación ni relaja QA. Se vuelve a contrastar tras F2 y en la retro final con los datos que existan.

## Orden y puertas

T-09 → T-10 → T-11 → T-12 → T-13 → T-14 → spike T-15 → T-16 solo con go → T-17 tras medir C-09 → decisión/cancelación T-18 → T-19. Cada tarea conserva su primer oráculo y la evidencia correspondiente. Las comparaciones de latencia usan controles intercalados y calentamiento; una medición inconcluyente no establece ahorro.

T-19 mantiene revisión independiente, gate de cobertura, CI Linux, documentación bilingüe y release por script con versión confirmada. T-20 no se cierra antes de publicar F2. T-21 requiere diseño concreto aprobado para modelos por runtime y perfil lite; no se asume que aprobar continuar F3 elija una arquitectura. La prueba manual de Ollama en otro equipo sigue siendo requisito de cierre de F3.
