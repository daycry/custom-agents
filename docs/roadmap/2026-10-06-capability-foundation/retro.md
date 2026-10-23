---
retro: capability-foundation
fecha: 2026-10-06
estado: cierre-tecnico-local
---

# Retro — primera integración catálogo de referencia

La primera entrega aporta investigación previa dentro de analyst/architect,
un panel local buscable y guías de CodeIgniter/PHP, Python y React para los roles
de desarrollo. Los exports conservan una fuente única. La comparación distingue
el catálogo web, Tkinter, readiness y el control plane Rust de catálogo de referencia.

La memoria actual se conserva. Graphify es candidato a grafo estructural del código;
su piloto está definido, sin instalarlo ni atribuir mejora medida. Graphiti sigue
siendo un backend opcional del conocimiento aprobado. Ninguno decide la aprobación
del Knowledge Gate.

No se pidió presupuesto. No hay estimación previa de horas/€ ni consumo completo
comparable; la desviación económica no se calcula. El meter abrió una ventana
de 26 minutos y devolvió `fuente: estimado`, tokens/horas IA/€ nulos, sin respuestas
compatibles de esta sesión Codex. Esa ventana parcial no incluye el cierre y no
se utiliza como duración total ni muestra de calibración. La mediana compatible
previa permanece en 531798.5 tokens/hora, seis muestras.

La revisión encontró dos gaps: matriz explícita de runtimes y orden de redacción
de metadatos. La primera comparación mencionaba runtimes, pero no entregaba la
matriz comprometida. Serializar/truncar antes de redactar dejaba sin protección
una asignación entrecomillada y un PEM largo; dos tests rojos lo reprodujeron.
Ahora se redacta el texto original antes del resumen y la exportación.
La comprobación tras versionar el script activó su entrada en la suite de consola:
faltaba declarar el arranque JSON. Se registra y valida sin exenciones; la puerta
completa final ejecutó 917 casos aprobados. Un tercer pase independiente valida
ese registro y el cierre documental, sin cambios de producción ni gaps nuevos.

Validación y límites en [testing/report.md](testing/report.md); historial de los
pases en [tasks.md](tasks.md). La ventana de uso no permite inventar tokens ni
calibración. El siguiente experimento de memoria debe medir recuperación,
actualización y procedencia sobre consultas representativas de los tres stacks.
Los packs automáticos continúan en project-specialization F2.

No se escriben entradas nuevas de conocimiento: se evita duplicar los contratos
de redacción y gobernanza existentes. La integración a master y una release
quedan fuera del push de rama autorizado.
