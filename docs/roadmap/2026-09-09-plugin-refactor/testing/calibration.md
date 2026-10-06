# Calibración recuperada de plugin-refactor

Medición histórica de Claude Code, recuperada el 2026-10-06 a partir de los
marcadores locales del meter y sus transcripciones. Es una muestra parcial de la
iniciativa; no mide el consumo del cierre actual en Codex.

| Medida | Resultado |
|---|---:|
| Marcadores examinados | 41 |
| Marcadores válidos | 38 |
| Intervalos distintos | 37 |
| IDs de respuesta distintos | 2.192 |
| Entrada | 14.778 |
| Creación de caché | 11.992.102 |
| Salida | 2.138.867 |
| Lectura de caché, separada del numerador | 318.605.132 |
| Numerador de calibración | 14.145.747 |
| Reloj de los intervalos distintos | 59.932 s |
| **Ratio medido** | **849.708 tokens/hora** |

La fórmula sigue [CALIBRATION.md](../../CALIBRATION.md):

```text
(entrada + creación de caché + salida) / (segundos reales / 3600)
14.145.747 / (59.932 / 3600) = 849.707,822… ≈ 849.708
```

La lectura de caché se conserva, pero no entra en el numerador de esta métrica.
Esto es una convención de calibración del proyecto, no una suma para facturación.
Los registros de streaming se deduplican globalmente por ID, conservando el último
uso. T-09-fix1 y T-10-fix1 comparten un intervalo idéntico que cuenta una vez.
La suma sin deduplicar sería 61.732 s. Unir todos los solapamientos produciría
52.968 s y otro ratio; ese criterio alternativo **no se adopta**.

Se excluyen T-04 y R4a-fix1 por formato anterior o falta de offsets, y T-03-fix1
porque inicio y cierre coinciden. No se reconstruyen esas ventanas a juicio.
La muestra abarca del 2026-09-10T13:22:28Z al 2026-09-12T04:25:15Z, con huecos;
el denominador suma trabajo instrumentado, no todo ese periodo.

La revisión independiente contrastó offsets y fronteras de línea, deduplicación,
streaming y tolerancia de 60 s. Un contraste separado de las 18 ventanas con JSON histórico en el ledger
coinciden exactamente; no hay archivos truncados ni JSON inválido en la lectura.
La muestra incluye varios modelos Claude; el desglose queda en el
[informe numérico](calibration.json), que contiene solo métricas y marcas de tiempo.
Las transcripciones, rutas personales y conversaciones permanecen fuera de Git.

Para próximas ventanas de Claude Code, ejecutar estos comandos desde el proyecto:

```powershell
python agent-kits/shared/usage-meter.py start --artefacto "iniciativa/T-XX"
# Ejecutar el trabajo de la tarea.
python agent-kits/shared/usage-meter.py close --artefacto "iniciativa/T-XX"
```

Conservar `inicio`, `fin` y `tokens_reales`; deduplicar ventanas compartidas y dividir
por el reloj real, nunca por `horas_ia`, que ya deriva del ratio calibrado.
Los contadores de Codex observados en esta máquina requieren otro adaptador; no se
introducen como si fueran transcripciones Claude ni se les aplican sus tarifas.

La medición histórica queda disponible; la incorporación a la mediana automática
se reserva al cierre de la iniciativa, como exige `CALIBRATION.md`. El ratio
global vigente sigue en 479.326 tokens/hora. Esta muestra parcial no acredita el
consumo completo de las 22 tareas ni sus desviaciones presupuestarias.
