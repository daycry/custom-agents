---
retro: installer-registro-real
fecha: 2026-09-11
---

# Retro — installer-registro-real (2026-09-11)

Vía rápida cerrada: ledger `completado` (6/6), cinco commits de contenido en `feature/installer-registro-real`
(`d4294ae` T-01/T-02/T-03 · `09f62bd` ledger I1 · `1fb5fdd` T-04/T-05/T-06 · `ba24433` documentación ·
`1b27ccc` ledger I2). Las cifras salen del ledger y de los marcadores de `usage-meter` que quedaron pegados en cada
traza de revisión, no de memoria. Las causas las propone el orquestador; el usuario las valida o corrige al leerlas.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 10,0 h | **11,4 h** (estimadas: el usuario no registró supervisión, dijo «adelante» y delegó) | +14 % — sin muestra real, no calibra |
| Horas IA de implementación | 1,30 h | **7,28 h** medidas | **+460 %** |
| Horas IA de revisión | no presupuestadas | **8,55 h** medidas en 5 ventanas | línea propia |
| Supervisión | 0,35 h | 0,50 h (estimada, 25 % de la IA por convención) | +43 % |
| Tokens | 600 k | **80,5 M** medidos (sin el T-01 original ni el intento 2 de I1, cuyos JSON se perdieron) | ×134 |
| Coste de revisión | — | **58,28 €** (8,00 + 20,13 + 10,51 + 10,58 + 9,06) | — |

## Qué pasó

El objetivo se cumple: el instalador registra el plugin de verdad en los tres runtimes, `/doctor` y `status` dicen la
verdad sobre el registro, y la experiencia es la que el usuario pedía. Lo que se desvió es el **coste de llegar ahí**.

**Cinco rondas de revisión, 64 gaps.** I1: 20 + 15 + 3 en tres intentos más una cuarta pasada autorizada.
I2: 15 + 11 en tres intentos. De ellos **4 Critical y 28 Important**. Ninguno se quedó sin cerrar.

**Los cuatro Critical son la misma historia contada cuatro veces**: el instalador afirmaba un resultado que no había
comprobado. Destruía el `settings.json` del usuario si no parseaba; fallaba con el lanzador de npm y no caía al
respaldo; corrompía el `config.toml` de Codex en tres formas distintas de declarar la misma tabla; y `/doctor` daba
por registrado lo que no lo estaba. El arreglo que cerró la familia del TOML no fue la quinta rama, sino una
**post-condición**: reanalizar lo escrito antes de guardarlo y no escribir si no cuadra. La misma idea cerró el
diagnóstico: una **función única de estado efectivo** que consultan las dos herramientas, con un test que exige que
no puedan contradecirse.

## Causas de la desviación

1. **La estimación presupuestó escribir el código, no acertar con tres runtimes ajenos.** 1,30 h de IA para tocar el
   registro interno de Claude Code, el `config.toml` de Codex y el `opencode.json` de OpenCode era una estimación de
   «cambiar unos ficheros». El trabajo real fue averiguar **qué lee cada runtime y con qué precedencia**, y eso solo
   se descubre probando. Tres de los cuatro Critical salieron de formas válidas de configuración que no habíamos
   imaginado.
2. **Escribir en el equipo del usuario no admite «casi».** Un instalador que corrompe una configuración es peor que
   no existir, así que cada ronda subió el listón en vez de aceptar el resultado. Es deliberado, no un desvío.
3. **Dos decisiones de diseño del orquestador eran falsas y las descubrió la revisión**: la ruta con la que OpenCode
   resuelve el adaptador (D4) y la afirmación de que Claude Code no documenta la precedencia entre ámbitos
   (desviación 29). Las dos se rectificaron con cita. Una decisión cerrada en el ledger **no es una verdad
   verificada**: cuando depende del comportamiento de un tercero, hay que ir a su documentación o a su código.
4. **La medición se perdió dos veces** (el JSON de cierre de T-01 y el del intento 2 de I1) y una vez el marcador se
   abrió a posteriori. Está declarado en el ledger, pero deja el total de tokens incompleto.

## Qué me llevo

- **Post-condición en vez de casuística.** Cuando llevas cuatro variantes del mismo fallo, deja de enumerar casos:
  comprueba el resultado y niégate a escribir si no es el esperado.
- **Una fuente de verdad por concepto.** Dos herramientas que responden a la misma pregunta acaban contradiciéndose;
  un test que las compara sobre el mismo estado lo impide.
- **Los tests tienen que aislar el entorno real.** Los del diagnóstico leían la configuración de la máquina: en un
  equipo con cierta clave, los rojos pasaban de 2 a 14. Una fixture `autouse` lo cierra.
- **Lo que no se puede probar aquí, se declara y se delega.** Codex y OpenCode no están en esta máquina: la checklist
  **M-01** queda escrita y sin marcar para que la ejecute el usuario.

## Acciones

| # | Acción | Dueño |
|---|---|---|
| 1 | Ejecutar la checklist **M-01** en Codex y OpenCode reales y marcarla | usuario |
| 2 | Al presupuestar trabajo que escribe en la configuración de un runtime ajeno, presupuestar **la revisión como línea propia** y no menos de 3 rondas | evaluator |
| 3 | Antes de cerrar una decisión de diseño que depende de un tercero, citar su documentación o su código en el propio ledger | architect / orquestador |
| 4 | Abrir siempre el marcador con `start` antes de tocar nada, y pegar el JSON del `close` en cuanto se obtiene | implementer |
