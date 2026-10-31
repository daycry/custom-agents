# Validación de la ampliación Go

El cambio amplía stack-practices, sin crear otra skill, otro agente o un módulo.
Rust conserva sus referencias de seguridad y su entrada TDD; su guía general
no se ha añadido. D-125 pasa a tener implementación por petición expresa actual;
las matrices de admisión anteriores conservan su valor histórico.

## Comprobaciones observadas

- RED antes de modificar runtime: seis casos nuevos fallan por --stack go inválido.
- Suite de selección: 55 passed, 1 skipped por symlink no disponible en Windows.
- Suites afectadas de selección, módulos, exports y tamaño: 183 passed, 1 skipped.
- Índice del roadmap: 57 passed después de añadir su fila dentro de la tabla.
- Coverage.py oficial del único archivo Python de runtime cambiado: 168/177 líneas,
  94,92%, por encima del mínimo del 90%. No se atribuye cobertura de ramas.
- Linter: 0 errores y 6 avisos ya existentes, sin avisos nuevos.
- Evals estáticos: 219 casos, 0 errores; no se afirma una evaluación de activación con modelo.
- export-interop --check: 88 archivos al día. El cambio de description no altera
  el índice generado limitado por longitud; no se editan exports a mano.
- quick_validate de skill-creator: Skill is valid. release --check: versiones 2.3.0
  coherentes, sin crear ni publicar una release.

## Revisión de pieza suelta por ROOT

Conformidad: se conserva el dueño compartido, lectura bajo demanda, dependencias
y permisos existentes. Docs ES/EN y changelogs mencionan Go; el selector registra
procedencia explícita y no afirma interpretar go.mod/go.work. Se ha comprobado
que los cinco roles obtienen la capacidad y que el manifest de la fixture no cambia.

Corrección: Go 1.22 depende de la semántica del módulo, no solo del binario instalado.
Los bucles con asignación a una variable externa conservan el riesgo de compartirla.
b.Loop requiere compatibilidad con Go 1.24; no se fuerza subir el mínimo. Un contexto
no espera por sí mismo a los workers y una cola acotada no limita goroutines lanzadas
sin control. No se devuelven buffers reciclados. El race detector solo cubre caminos
ejecutados; cobertura y herramientas siguen la configuración del proyecto.

Fuentes primarias enlazadas en la guía: go.dev y pkg.go.dev, consultadas 2026-10-31.
Se contrastaron también los antecedentes S116/S117 y sus correcciones de versiones.
Esta es una revisión del mantenedor para la pieza acotada; no se presenta como
revisión independiente, prueba de una aplicación Go real o benchmark ejecutado.

El manual PDF anterior conserva sus fuentes: este cambio añade una referencia
lingüística bajo demanda y actualiza el catálogo de habilidades en docs/README,
sin cambiar sus 18 workflows ni los capítulos usados para generar ese PDF.

Tokens, coste y esfuerzo IA totales no están medidos. La ventana QA solo cubre
validación y entrega posteriores a la implementación; no mide toda la tarea.
La CI del commit publicado se comprueba en la PR22 antes de la entrega final.
