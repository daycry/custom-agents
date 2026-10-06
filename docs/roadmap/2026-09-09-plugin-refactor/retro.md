---
retro: plugin-refactor
fecha: 2026-10-06
estado: cierre-tecnico-local
---

# Retro — plugin-refactor

El cierre técnico completa las 22 tareas tras el cuarto pase autorizado, A+B sin gaps pendientes. El objetivo medido se cumple sobre
los cinco archivos: **36→15** funciones largas y ninguna nueva supera 32 líneas
AST. Las copias declaradas y los contratos se conservan. La integración mediante
PR/master y CI remota verde está pendiente; no se ha publicado una release.

| Medida | Previsión con margen | Real comprobado | Desviación |
|---|---:|---|---|
| Horas humanas | 88,8 h | sin medición completa | no calculable |
| Horas IA | 10,6 h | sin medición completa; horas históricas derivadas del ratio de entonces | no calculable |
| Tokens facturables | 5,08 M | muestra parcial 14.145.747; cierre Codex fuera de la muestra | no total comparable |
| Coste total | ~4.479 € | sin total comparable | no calculable |
| Calibración | ratio previo 479326 | 849708 tokens/hora, muestra compatible | nueva mediana 531798.5 (6 muestras) |

El ratio usa tokens medidos y **reloj independiente**: 59.932 segundos de
intervalos distintos. No divide por horas_ia, que el meter calcula con su propio
ratio. Streaming y ventanas compartidas se deduplican; lectura de caché aparte.
Se excluyen tres marcadores sin fronteras compatibles. Ver
[calibración](testing/calibration.md) y [datos numéricos](testing/calibration.json).

Las causas observadas son verificables: múltiples rondas de revisión histórica,
historial de tareas dentro del brief, características nuevas añadidas durante
la espera y medición inicial con transcripciones no encontradas en Windows.
No se presentan estas conclusiones como declaraciones literales del usuario.

La corrección final conserva el parser literal de otras iniciativas; extraerlo
había perdido dos variables y aumentado duplicación. Se restaura y se extraen
estados de doctor para cumplir el objetivo sin alterar las copias. Una base
actual comparable permite medir 221→200 funciones largas globales; las fotos
de septiembre se conservan como historia y no se enfrentan a otro alcance.

La suite limpia detectó nueve fallos anteriores relacionados con el launcher
Node y un fixture CRLF. Se declaran aparte del refactor puro y se corrigen con
regresiones dedicadas. Los límites de Windows y resultados completos quedan en
el [informe de QA](testing/closure.md). No hay UI; el marcador sin UI no exime
pruebas de código ni afirma cobertura E2E.

Ajuste sugerido: abrir la ventana antes de trabajar, conservar reloj y offsets,
separar revisión/corrección en presupuesto y medir sobre fuentes del mismo
alcance. Archivar historia dejando contrato operativo y aceptación en el ledger.
Memoria técnica: **sin entradas nuevas**; los aprendizajes se apoyan en GOT-005,
GOT-009, GOT-010 y ADR-016/017 ya existentes, sin duplicar doctrina.

Siguiente iniciativa recomendada: project-specialization F2. catálogo de referencia permanece
documentado para estudiar sus paquetes, skills, agents, tools, hooks y workflows
más adelante, conforme al alcance indicado por el usuario.
