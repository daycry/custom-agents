---
spec: workflow-integration
estado: implementada
creado: 2026-10-06
actualizado: 2026-10-06
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
---

# Integración del workflow y las capacidades de custom-agents

El usuario pide integrar capacidades técnicas en un workflow coherente, limpio,
estructurado y documentado, sin gaps abiertos ni implementaciones sustituidas.
La autorización anterior delega decisiones técnicas, prioriza PHP/CodeIgniter 4,
Python y React y autoriza publicar la rama. Esta iniciativa continúa ese trabajo;
la primera entrega anterior y su historia se conservan como registro.

## Resultado

Un workflow que selecciona capacidades pertinentes antes de trabajar y utiliza
los mismos perfiles en diseño, implementación, revisión y QA. Los roles actuales
conservan sus artefactos. Las capacidades seleccionadas se comparan contra lo existente;
se absorben mejoras, se añaden responsabilidades solo cuando tienen dueño propio
y se evita mantener una cadena paralela o comandos duplicados.

La evaluación del catálogo principal fijado (293 skills, 68 agentes, 94 comandos)
termina con decisión y motivo por pieza: adaptar, cubierto con delta comprobado,
fuera del alcance técnico elegido o incompatible con un invariante. Un inventario
no acredita utilidad ni ejecución. La matriz distingue lectura de código,
decisión de alcance, adaptación implementada y pruebas ejecutadas.

## Alcance

- Registro único de capacidades, selección determinista por rol/fase/stack/área,
  sin cargar todo el catálogo ni ejecutar instrucciones del repositorio externo.
- Consolidar las tres guías iniciales en stack-practices y ampliar patrones y
  pruebas; retirar sus directorios, evals y referencias activas sustituidas.
- Criterio transversal de backend/API/datos, frontend/accesibilidad/rendimiento,
  entrega/Docker/MCP, auditoría del catálogo y evaluación de resultados.
- Integración en pm/dev-cycle, roles y briefs; límites de brief y skill-index
  preservados. Diseño e implementación usan la misma selección que revisión/QA.
- Memoria gobernada: comparar completitud/procedencia, conservar Knowledge Gate;
  contexto estructural Graphify opcional y separado, con evidencia de piloto
  público si se adapta una consulta. Sin promoción de reflexiones ni conversación
  cruda. Ningún cambio automático en servicios del consumidor.
- Panel muestra responsabilidades/capacidades y distingue fuentes de ejecución.
- Documentación ES/EN, exports, pruebas Windows/Linux y revisión independiente;
  commit/push de la rama. Sin PR/merge/release por autorización anterior.

Packs de otras tecnologías e industrias se clasifican por alcance; no se declaran
instalados. Este workflow selecciona capacidades existentes del plugin y no genera
piezas de proyecto: project-specialization F2 conserva su contrato independiente.

## Aceptación

1. Las 455 piezas tienen decisión trazable y fuente fijada; ninguna selección se
   justifica solo por nombre, estrellas o cantidad. Las piezas elegidas tienen
   lectura de implementación y comparación concreta contra lo nuestro.
2. El selector y registro detectan referencias muertas, no importan código del
   proyecto, no ejecutan red/procesos, redactan salida y tienen tests de regresión.
3. Los tres perfiles iniciales quedan absorbidos y retirados, sin alias/fallback
   activos; las guías nuevas incluyen criterios y fuentes, no consejos genéricos.
4. La selección del workflow es común a roles y fases, con fallback informativo
   en instalación parcial y sin duplicar dueños o puertas de QA/TDD/Knowledge Gate.
5. Briefs de hasta 10.000 caracteres e índice hasta 45 líneas/3.500 caracteres;
   la información protegida no se recorta para hacer caber capacidades.
6. El panel describe el workflow real; fuentes generadas y documentación bilingüe
   reflejan altas y bajas. No afirma salud o disponibilidad por presencia de archivos.
7. Evaluación de resultados con corpus y método explícitos; sin scores ficticios,
   autoaprobación de memoria ni cambios de configuración externa no solicitados.
8. Gaps introducidos reproducidos y cerrados; revisión A+B y C/D según selector,
   cobertura del código del diff ≥90 %, pruebas afectadas y puertas finales verdes.

No se solicita presupuesto económico. La medición se registra cuando la sesión
es compatible; no se inventan tokens, horas ni ratios para simular un cierre.
