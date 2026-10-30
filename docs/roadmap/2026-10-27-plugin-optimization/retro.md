---
retro: plugin-optimization
fecha: 2026-10-30
---

# Retro — plugin-optimization

Las tres fases se publican por separado: F1 v2.1.0, F2 v2.2.0 y F3 v2.3.0. Balance de alcance: 23 tareas completadas y 3 canceladas por no-go (T-16/T-17/T-18). Las cancelaciones no cuentan como implementación. La prueba real con Ollama queda aplazada por decisión del usuario y no tiene resultado verde.

## Estimación y medición

| Magnitud | Estimado del ledger | Real comparable / desviación |
| --- | --- | --- |
| Horas humanas F1 / F2 / F3 | 38,4 /69,0 /45,0 h | Sin medida comparable; desviación no calculable |
| Ejecución IA total | 61,2 h | Sin medida comparable; no se sustituye por reloj |
| Supervisión | 15,3 h | Sin medida comparable |
| Tokens | 24,7M entrada /2,47M salida | Sin medida completa de ejecución |
| Presupuesto del plan | 7.808 € | Coste real total sin medida comparable |

Los bloques de generación de artefactos no representan toda la ejecución y no se extrapolan. La ventana final 17:52:52–18:17:02 UTC registra 24 min de reloj, con tokens/coste/horas IA null; incluye esperas externas. La revisión documental posterior queda fuera. No se calcula un ratio tokens/hora ni se incorpora una muestra a la mediana de calibración. No hay respuestas nuevas del usuario sobre una desviación económica que no puede medirse; no se inventan causas personales.

## Evidencia técnica y límites

- F1: el control intercalado del guard acredita 36,71–38,21 % de mejora local. El usuario aprueba cambiar la aceptación del 80 %; esa cifra no se declara alcanzada. La línea base se caracteriza con dispersión y controles, sin afirmar estabilidad uniforme. Evidencias y decisiones: [ledger](tasks.md), T-01/T-02/T-07.
- F2: revisión aprobada en 2 intentos; gate Python 92,25 % de media sobre 8 ficheros cambiados. Las tres opciones condicionales se cancelan con sus decisiones no-go, no con implementaciones ficticias. [Publicación F2](testing/f2-publication-2.2.0-2026-10-30.json).
- F3: revisión aprobada en 2 intentos y cobertura Python 91,08 % de media sobre 10 ficheros cambiados. No es cobertura global, por línea nueva ni JavaScript. La corrida instrumentada histórica con un fallo temporal se conserva como fallida; la CI normal y la cobertura dirigida aceptada tienen recibos separados. [QA automática](testing/t26-automated-verification-2026-10-30.md).
- El fallo concurrente del writer quedó aislado: mismo inode y tamaño0→1 al inicializar un lock visible. El fix conserva el lock vacío y los controles de identidad; RED determinista, regresiones Windows/Linux y 100 pares de escritores en Linux. La hipótesis previa de preflight era incompleta. [Causa raíz](testing/t23-lock-initialization-root-cause-2026-10-30.json).
- El binding nativo se acredita con proveedor simulado; no sustituye inferencia real ni calidad de un modelo local. [Prueba aplazada](testing/t26-manual-ollama-checklist.md), [autorización](testing/t26-release-authorization-2026-10-30.json).
- La entrega sufrió demora durante una incidencia de GitHub Actions. El primer push de release recibió GH007 por la identidad del clon temporal; no cambió referencias remotas. Se regeneró con la identidad pública local y árbol idéntico, sin cambiar privacidad global. [Recibo final](testing/f3-publication-2.3.0-2026-10-30.json).

## Ajustes sugeridos y conocimiento

Conservar controles intercalados para mejoras temporales y separar cobertura instrumentada de pruebas con límites de tiempo. En concurrencia, observar la identidad y la generación del estado desde su primera visibilidad. Preparar la identidad pública del clon antes del commit de entrega. No recalibrar costes a partir de ventanas de reloj sin tokens comparables.

Estado de propuestas técnicas: **sin cambios**. O1 y el gotcha del lock ya tienen dos recibos de curación local, [asociados por SHA y operation-id](testing/t26-curation-2026-10-30.json); no se duplican como propuestas de retro. La consulta episódica del journal salió con exit 0 sin JSON interpretable; no demuestra ausencia de candidatas ni se usa como evidencia técnica. No se exporta conocimiento a servicios externos.
