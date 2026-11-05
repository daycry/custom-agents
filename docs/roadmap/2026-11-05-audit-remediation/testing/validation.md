# Validación final — 2026-11-05

El código final aa25dda supera la CI de referencia y las cuatro lentes finales no dejan Critical/Important pendientes. Las diez tareas están completadas. No se publica una versión ni un paquete npm.

| Puerta final | Resultado |
|---|---|
| CI GitHub 42085116173, Python 3.11/Node 22 | success |
| Python completo | 10.469 passed, 41 skipped, 82 subtests passed, 794,16 s |
| Node completo | 470 passed, 16 skipped, cero failed, 486 casos |
| Captura SessionEnd, 30 iteraciones | p95 2,65 ms / p99 2,94 ms; límites 100/300 ms |
| Interop / manual / evals / sintaxis / versiones | exit 0 |
| Revisión final A+B+C+D | sin gaps pendientes; A6-1 corregido |

[CI verificable](https://github.com/daycry/custom-agents/actions/runs/42085116173). Las omisiones de plataforma no acreditan ejecución. No se ejecutó macOS real ni se llamaron servicios reales de conocimiento. Los fallos de tiempo locales y todas las pasadas rojas se conservan debajo; no contradicen ni sustituyen la referencia ejecutada.

## Ejecuciones iniciales (histórico)

Esta tabla conserva las primeras pasadas; los estados pendientes de sus filas son históricos. El dictamen vigente es el resumen final anterior.

| Área | Resultado observado | Límites |
|---|---|---|
| Instalador R1–R3 | 7 passed dirigidos; posteriormente 8 passed con caché compartida | Regresión completa: 157 passed, 12 failed, 169 casos; 2.276.998 ms en este host Windows/OneDrive. Los fallos siguen en triage. |
| Hooks y briefs | 101 passed con suite vecina | R6 inverso/raíz añadido tras revisión: RED 2 casos, luego GREEN. |
| Ledger, alcance y retro | 100 passed, 3 skipped | POSIX no acreditado en Windows. Tras D1: RED 501 listados en 501 filas; GREEN 50 passed/1 skipped en suite de retro. |
| Graphiti | 279 passed | Fake MCP; ninguna llamada al stack real. Recibos antiguos añadidos después del snapshot. |
| Publicación/curación | 59 passed y un fallo corregido en la primera pasada dirigida | Replay antes de envío, resumen, seguridad de staging y origen declarado. |
| Consola | 43 passed | Nuevas carreras de sondeo añadidas después de revisión; validación final pendiente. |
| Exportaciones | 72 passed, 1 fallo esperado por derivados pendientes | Interop regenerado después; revisión A ejecutó `--check`: exit 0, 92 archivos al día. |
| Jira | 76 passed, 1 fixture de posición de argumento corregido | Regresión final pendiente; no publicaciones reales. |
| Journal/outbox | Última suite ampliada: 330 passed, 12 skipped | E/S guardada opt-in en el dueño outbox; captura no recorre `done/`. |
| Paquete npm | 5 passed sobre tgz extraído | `npm pack --offline --ignore-scripts`; no acredita aprobación del registro. |
| Lint | 0 errores, 16 avisos | Avisos de comandos nativos/genéricos ya existentes; no se han suprimido reglas. |
| Suite Python combinada de CI | En ejecución | No es verde; se ejecutó mientras continuaban cambios y requerirá repetir los grupos afectados al final. |

Los logs de ejecución están en `.pytest_cache/audit-*.txt` del checkout de trabajo. Son evidencia local ignorada; este resumen no sustituye sus resultados.

## Revisión de contexto fresco — intento 1

Snapshot público inmutable de 1.987 archivos; diff base `234fa9bcf3c96de4a6c5c37e1e03698e33bd3236`, SHA-256 `beb4d479ec527d87f6ff224ae446dd69202c8db38653477cf18f542d3527bc34`. Excluye configuración privada, conversaciones y conocimiento del consumidor. Las cuatro lentes leyeron el diff de 58 archivos por bloques. Las correcciones posteriores necesitan revisión de su delta.

| ID | Grado | Hallazgo del snapshot | Seguimiento |
|---|---|---|---|
| A1 | Important | Páginas architect/nemesis describían permisos antiguos | Descripciones corregidas; pendiente contraste del delta. |
| B1 | Critical | CLI de captura llamaba un wrapper definido después de `main()` | RED por subprocess real sin envelope; GREEN con un envelope. |
| B2 | Important | Dos primeras capturas podían perder un prompt al crear `.gitignore` | RED con barrera real; CAS/relectura acotada y GREEN de ambos prompts. |
| B3 | Important | Cola rechazaba `.claiming-recuperados` | Marcador añadido al contrato; test dirigido verde. |
| B4 | Important | Resumen idéntico con recibo legado bloqueado | Comparación con `episode_body_sha256`; test nuevo verde. |
| B5 | Important | Caché global no reconocida desde un segundo proyecto | Recibo de caché autenticado en ámbito usuario y reutilización de bytes genuinos; prueba A/B y desinstalación de A conserva B, verde. |
| B6 | Important | Aliases estándar de macOS rechazados como enlaces del proyecto | Normalización estricta de aliases de sistema; 5 tests de contrato verdes. macOS real no ejecutado. |
| B7 | Important | Fixtures antiguos incompatibles con la política autenticada | Pendiente de ajustar sin restaurar ejecución/borrado desde inventarios no verificados. |
| B8 | Important | Sondeo idle podía admitir un segundo envío antes del primero | Fuente de sondeo y rechazo de turnos concurrentes añadidos; regresión final pendiente. |
| B9 | Minor | Histórico append-only limitado a 8 MiB sin continuidad declarada | Pendiente; no se eliminará la lectura acotada. |
| D1 | Important | Un listado de roadmap por fila de calibración | Escaneo lazy sólo para slug legacy relevante, una vez. |
| D2 | Important | Dos inspecciones completas del histórico de la cola por captura/replay | Guardas en puntos de E/S; estructura al inicio, sin recorrer recibos completos. 330 tests ampliados verdes. |
| D3 | Minor | Rotación leía el log entero en cada prompt | Restituida lectura de cola con fd/identidades comprobadas; 10 tests dirigidos verdes. |
| R6 adicional | Important | Directorio padre o raíz de la tarea no retenía diseño relacionado | Contención en ambos sentidos y raíz; RED observado y GREEN dirigido. |

Lente C: sin vulnerabilidades introducidas/reabiertas confirmadas en el snapshot inicial. No sustituye una auditoría completa ni acredita ACL/POSIX dinámicos.

Claude CLI completó la revisión B con OAuth ya autorizado, herramientas Read/Grep/Glob, MCP vacío, sin persistir sesión ni escribir en la copia. Modelo comunicado: `claude-opus-5-5`, 88 turnos, coste equivalente de API 5,753707 USD. No es un cargo confirmado de la suscripción. Los recibos locales conservan sólo el resultado final y metadatos seleccionados.

## Contrato npm de contenido de doble uso

La declaración `contentPolicy` y el archivo `DISCLOSURE` documentan las capacidades legítimas de auditoría y pruebas de seguridad según la política oficial. Su inclusión no acredita aprobación del registro. Esta iniciativa no publica paquetes ni automatiza comunicaciones con soporte.

## Revisión de contexto fresco — intento 2

S2: 2.000 archivos públicos; SHA-256 del patch `f4f188c6c42ec70530e9be80ee977c337cfd9d1dbcb3acca56c975170c04ef87`. Se leyeron 29 archivos del delta normalizado respecto de S1. A: sin gaps nuevos, A1 corregido; C: sin vulnerabilidades nuevas confirmadas; D: D1/D2/D3 corregidos y sin hallazgos nuevos medibles. Sus límites de ACL y macOS siguen vigentes.

| Hallazgo previo / candidato | Dictamen de intento 2 | Resolución posterior para intento 3 |
|---|---|---|
| A1 | Corregido | Documentación y derivados al día; A ejecutó interop: exit 0, 92 archivos. |
| B1 | Corregido | Captura CLI real verificada. |
| B2 | Important residual | Ventana link→unlink de inicialización: lectura dentro de reintento acotado, sin leer ni adoptar inodes compartidos. RED real; GREEN de ambos prompts. |
| B3 | Corregido | Marcador propio reconocido. |
| B4 | Corregido | Resumen legado idéntico se reconoce por su cuerpo enviado. |
| B5 | Corregido | Recibos de caché a nivel usuario; registro por instancia. Contrato de conservación de caché documentado ES/EN, incluyendo última instancia. |
| B6 | Corregido por contrato | Aliases macOS sólo conocidos; sin macOS real. |
| B7 | Corregido por lectura | Fixtures autenticadas y preservación de bytes; seis escenarios de caché/registro/desinstalación pasan después. |
| B8 | Corregido | Dos turnos no se admiten simultáneamente. |
| B9 | Corregido | Presupuesto explícito de histórico 8–128 MiB con conservación de bytes e idempotencia. |
| B10 (nuevo) | Important | fsync previo a publicación no puede reconocerse como éxito. Opt-in de outbox permite publicar y sólo después informar durabilidad reducida; los otros metadatos mantienen fsync estricto. RED/GREEN. |
| C | Sin hallazgos nuevos | 2.000 hashes coincidentes, hardlinks de claim/completar/purga/sidecar preservan canarios. |
| D1 / D2 / D3 | Corregidos | Cinco pruebas dirigidas del revisor pasan. |
| Claude: inflight tras HTTP422 | Descartado con evidencia | SessionManager informa `uncertain`, permite desconectar/reanudar; prueba integrada con Driver real y cliente sintético: nuevo mensaje explícito admitido. No se reenvía automáticamente una entrega incierta. |

Claude CLI real: `success/end_turn`, alias solicitado `opus`, 29 turnos, 264.180 ms; revisión parcial de Claude completada por lectura del revisor B y reproducción de sus candidatos. No se interpreta como revisión completa automática de todo el producto. Recibos locales ignorados, sin conversaciones.

## Regresión global y triage posterior

Primera pasada Python: **64 failed, 10.324 passed, 93 skipped, 1 error**, 6.626,77 s. Se ejecutó mientras cambiaban fuentes; el harness de recuperación detectó correctamente `public input changed`. No es evidencia de verde del candidato final.

Primera pasada Node S2 congelada: **468 passed, 10 failed, 2 skipped, 1 todo** en 18 archivos; 1.669.461 ms. Triage: tres fixtures de ruta Windows apuntaban fuera del proyecto y ahora usan rutas internas reales; cinco contratos de caché global cambiaron al separar propiedad; timeout de consulta nativa y arranque de un descendiente se verificaron aislados. El TODO Windows de 1,5 s permanece explícito.

Correcciones de integración de las pruebas, sin bajar umbrales:

- El módulo JIO salió del bloque literal del redactor: se restablece su independencia y comparación byte a byte.
- `content_origin: agent` forma parte del resultado exacto de propose; el test conserva payload UTF-8 y SHA.
- El hash LF del launcher se actualizó sólo tras contrastar la fuente exacta con S2 revisado por C. La detección de modificaciones y egress sigue activa.
- `--root` explícito de Jira es frontera exacta; sólo cwd implícito busca padres. Pruebas de ambos escenarios pasan.
- Confluence `--check` diagnostica la política declarada, y el filtro de publicación mantiene exclusiones obligatorias aunque la política sea insegura.
- Fixtures de productor usan rutas físicas para que las inyecciones alcancen su destino con aliases Windows 8.3. Coverage-gate también compara rutas físicas; 31 tests pasan sin cambiar porcentajes.
- El drill de recuperación copia sus dependencias nuevas explícitas. Sus barreras se mantienen en publicación real por replace o link + retirada del temporal; conserva cortes, canarios, bytes y errores ENOSPC.
- El escritor de journal rechaza entradas inaccesibles/enlazadas al mutar; lectura de inventario sigue sin seguirlas. Prueba POSIX falló antes y pasa con la escritura estricta.

Últimas ejecuciones dirigidas: 907 passed y un fallo de timing del redactor en Windows; 55 passed de productor/Unicode/captura/egress; 263 passed, 12 skipped de journal/outbox antes de escritura estricta; 39 passed de recuperación/training/Jira tras actualizar fronteras y aislamiento; 49 passed, 1 skipped del marcador docs; seis escenarios de instalador compartido pasan. Limpieza de descendientes y timeout TLS pasan aislados. Las omisiones POSIX iniciales no se consideran verificaciones.

Linux aislado (WSL Ubuntu, Python 3.14.4, dependencias de pruebas públicas copiadas, sin instalar paquetes del sistema ni tocar servicios): **1.004 passed, 1 skipped**, 95,57 s, incluyendo journal/outbox, permisos/enlaces, archivo/ledger, redactor, cobertura y contrato de benchmark. Benchmark de 30 capturas: p50 1,84 ms, p95 4,01 ms, p99 7,42 ms; exit 0 para límites 100/300 ms. No equivale al runner CI de referencia Python 3.11.

Windows conserva una limitación local de timing: el sentinel de mediana <20 ms midió 27,31 ms aunque el benchmark es in-process; el umbral permanece intacto y pasa en Linux. La pasada cargada de CA-02 dio p95 195,53 ms (exit 1), también conservada. No se inventa un verde global Windows ni se atribuye causalidad sólo a carga.

Sintaxis validada: 358 Python y 521 JSON, cero errores. Manual/diagramas coherentes, evals estáticos 229 casos sin errores e interop 92 al día. Quedan la pasada congelada final, revisión 3 y cierre del ledger.

## Revisión de contexto fresco — intento 3 y decisión del orquestador

S3: 2.000 archivos públicos, patch SHA-256 `81e8f0bd5a37c584d583111b75531e35b66e2694caf1f1f7332200334beff56c`. Delta S2→S3 de 22 archivos/725 líneas leído completo por las cuatro lentes. A: sin gaps nuevos, interop 92 al día, asserts/alcance justificados; C: sin vulnerabilidades nuevas confirmadas, pin LF idéntico a S2, hardlinks persistentes no leídos; D: sin hallazgos nuevos, vía normal sin sleep y contención acotada a 190 ms. B: B2 y B10 corregidos; **B11 Important** nuevo.

B11: un handle exclusivo real de Windows sobre una entrada anterior provocaba `dead_letter=1` en vez de reintento. El lector canónico informaba `unreadable`; StateIO lo convertía en `ValueError('invalid_state')`, y la lectura estricta perdía la clasificación transitoria. Se observó RED con un handle real y otro RED de contrato; el parche añade clasificación OSError opt-in al lector de journal y la conserva al mutar. Otros consumidores mantienen `invalid_state` por defecto; enlaces y estados inválidos siguen siendo errores de seguridad. GREEN: **69 passed, 2 skipped** en journal, ledger-write y archive. La prueba exige reencolado, backoff efectivo y materialización después de liberar el handle con reintento explícito.

La skill adversarial-review limita el bucle ordinario a tres intentos y devuelve la decisión al orquestador/usuario (seguir, replanificar o aceptar deuda). Alcanzado ese punto, **el orquestador decide seguir con una única iteración adicional limitada al parche B11**, conforme a la orden vigente del usuario de corregir los hallazgos y apoyarse en revisión independiente. No se acepta B11 como deuda ni se reinicia/oculta el contador. La pasada completa congelada sigue siendo S3; el delta posterior requiere sus propias verificaciones.

## Cierre de regresiones de compatibilidad y B11 residual

La iteración 4 encontró una variante del mismo B11: la relectura de README durante publicación aún usaba el contrato genérico. Dos RED adicionales demostraron el defecto en write/update. La política de indisponibilidad se ha consolidado ahora en la instancia StateIO del productor journal, cubriendo read, write y update; los otros consumidores conservan su valor predeterminado. Se ha ampliado la prueba CreateFileW real a lectura de entrada y bloqueo de índice después de validarlo. GREEN: **72 passed, 2 skipped** en la batería journal/ledger/archive; 20 casos audit antes de ampliar la variante de índice también pasaron.

El orquestador replanifica la verificación final como iteración 5, sin ocultar ni reiniciar el contador: B11 residual y las regresiones de compatibilidad que descubrió la pasada completa. No se acepta deuda. A4 y C4 no encontraron gaps nuevos de su lente; B4 impidió correctamente el cierre. D cubrirá acumuladamente el delta desde S3.

Pasada completa Linux S3 (Python 3.14.4, Node 22.23.3): **6 failed, 10.437 passed, 58 skipped**, 2.159,93 s. Cinco fallos procedían de depender de límites implícitos del codificador/decodificador JSON; se sustituyen por presupuestos estructurales explícitos, conservando el rechazo y los diagnósticos. El sexto fue el umbral de 1,5 s del redactor bajo carga; no se modificó ese código ni el umbral. La pasada Node falló inicialmente por faltar el alias `python` del entorno de pruebas, no por el código del producto: se corrigió únicamente el entorno con TEST_PYTHON y un alias privado. Reejecución completa: **465 passed, 16 skipped, 0 failed**, 481 casos, 86,73 s.

Todos los checks independientes de esa pasada dieron exit 0: lint, manual, evals, interop, coherencia de versiones y benchmark de captura. Captura de 30 iteraciones: p50 1,09 ms, p95 1,30 ms, p99 1,33 ms (límites 100/300 ms). No se extrapola este resultado a otros equipos.

Nuevos tests de límites JSON 31/32/33 observaron RED; después 68 casos de perfil/diagnóstico/snapshot pasaron en Windows. El test de arguments textual se amplió a 60 y 5.000 niveles: RED de campo diagnóstico, después **82 passed** en su suite. Mantiene el límite de 50 niveles y todas las comprobaciones de chain-of-thought; sólo corrige la referencia al campo JSON textual original.

## Verificación final del candidato S5

S5: 2.000 archivos públicos, patch SHA-256 `e6b7ee7280179406ccce4c56bad810529a5aa5cfb3e74adcde36c22d460c91c6`. B5 leyó los 14 archivos/338 líneas del delta S4→S5, contrastó sus hashes y ejecutó 221 casos correctos con 3 omisiones (Windows/Python 3.13). Sin defectos nuevos; B11 corregido en lectura y publicación con handles reales. C5 y D5 siguen en curso. Un ajuste posterior elimina únicamente una línea en blanco al final de journal-capture.py.

La repetición dirigida Linux de S5 sigue en curso. La prueba de tiempo del redactor vuelve a fallar (1.975 s para un caso de 1.000.000 caracteres, límite 1.5 s). Se mantiene el test y su umbral sin cambios; no se atribuye una causa sin prueba. La integración continua de referencia (Python 3.11/Node 22) debe contrastar el candidato antes de cerrar T-10.

B5: sin defectos nuevos, 221 passed/3 skipped. C5: sin vulnerabilidades introducidas o reabiertas, 196 passed/8 skipped; ambas variantes CreateFileW reales ejecutadas. D5: sin nuevos hallazgos, 10 passed; recorrido JSON lineal en cargas sintéticas de hasta 80.000 contenedores. No sustituyen QA global ni acreditan macOS. Repetición Linux S5 de perfil, doctor, scope, lectura local y schema: **295 passed, 10 skipped**, 75,03 s. Recuperación sigue en curso.

CI de referencia activada en PR #30, run 42078982134, commit 7d61e40: pendiente. T-01–T-09 cerradas tras sus pruebas y revisión; T-10 conserva revisión de conformidad final y CI pendientes.

A5: sin gaps nuevos de conformidad; cierres T-01–T-09 contrastados con tests y evidencia. Interop ejecutado por el revisor: exit 0, 92 ficheros al día. Ledger-lint del overlay: exit 0, cero incoherencias/avisos. T-10 sigue abierta hasta CI de referencia. La batería final Linux S5 de journal/outbox/ledger/recuperación terminó con **352 passed, 4 skipped**, 153,05 s; junto al grupo JSON suma 647 passed y 14 skipped, sin incluir el test de tiempo fallido. El runner dirigido terminó exit 1 por ese fallo; no se presenta como verde global.

## CI de referencia y B12 — continuación 6

Run 42078982134, commit 7d61e40, Python 3.11/Node 22: **10.469 passed, 41 skipped, 82 subtests passed**, 754,47 s. El redactor pasa en esta referencia; sus fallos locales se conservan como límite del host. Benchmark: p50 2,26 ms, p95 2,45 ms, p99 2,92 ms, límites 100/300 ms correctos. Node: **464 passed, 16 skipped, 1 failed**. No verde global.

Fase 1 debug-root-cause: el test existente gap B-4 falló al matar el instalador durante copia, con carpeta agents restante. Fases 2/3: una barrera justo antes del rename atómico confirmó que el temporal existía fuera de files del inventario. SIGKILL no ejecuta finally; el desinstalador conserva correctamente el archivo sin propiedad. No es un fallo de firma ni de hashes de los archivos finales.

Hipótesis probada: publicar con temporales hermanos dentro de las carpetas de entrega introduce una ventana de corte no recuperable por su inventario. RED determinista B12: carpeta agents todavía presente tras uninstall (1 failed). Fase 4: temporales en staging privado de un solo scratch name, con identidad de directorio firmada antes de cualquier payload y apertura exclusiva; recuperación limpia bytes completos o parciales, conserva directorios sustituidos, hardlinks y archivos desconocidos. GREEN Windows: cinco variantes B12 correctas; tres casos de interrupción/señales también correctos.

Se reabre T-01 y T-10 permanece abierta. El orquestador decide la continuación adicional 6, limitada a este nuevo fallo descubierto por CI, sin reiniciar el contador ni aceptar deuda. Revisión del delta y regresión Node completas pendientes. Propuesta de gotcha sobre SIGKILL/temporales pendiente de persistir: el alcance de esta auditoría excluye consultar o modificar la memoria privada del consumidor.

## Continuación 7 — presupuesto de checkpoints

S6 Linux completo Node: **469 passed, 16 skipped, 1 failed**, 252,14 s; cinco pruebas del tgz correctas. El único fallo fue la cota existente de checkpoints: 9 frente a máximo 8. B6 reprodujo el mismo fallo en Windows (15/16 dirigidos correctos); C6 ejecutó 19 casos correctos sin nuevos hallazgos de seguridad, D6 verificó crecimiento lineal sin medir latencia real.

El orquestador decide corregir la puerta y revisar el delta reducido como continuación 7, sin reiniciar el contador ni elevar el umbral. Se registra una sola vez el conjunto completo de rutas de perfil, todas preflightadas, antes de crear payloads. Dos snapshots iniciales (intención e identidad del staging) y el final sustituyen los checkpoints por grupo. Se mantiene la autenticación, recuperación de temporales parciales y guardas por archivo. El test de presupuesto ha pasado en Windows tras el cambio, al igual que perfiles y reanudación de upgrades; la batería y revisión finales siguen abiertas.

S7 Windows/Node 23.8: **11 passed, cero failed/skipped**, 136,92 s. Incluye presupuesto de checkpoints, perfil parcial, reanudación de upgrade/retirada, SIGKILL antes de publicación y las cinco variantes B12. El umbral original se conserva. Linux completo y lentes del delta reducido siguen en curso.

## Dictamen final del código — S7 / aa25dda

Las cuatro lentes A7/B7/C7/D7 no dejan nuevos gaps ni Critical/Important pendientes en el código: A6-1 corregido, presupuesto existente intacto. A ejecutó interop (92 al día) y el test del presupuesto; B ejecutó 12 casos correctos; C 29; D ejecutó el test y cargas instrumentadas de 100/1.000/5.000 archivos con tres checkpoints constantes y crecimiento proporcional al inventario.

Linux final congelado S7, Node 22: **470 passed, 16 skipped, cero failed**, 486 casos, 331,66 s. Pruebas del tgz: **5 passed**, 5,53 s. Runner completo de esta batería: exit 0. Las omisiones son de plataforma, no se transforman en aprobaciones.

T-01 vuelve a completado tras la recuperación, la puerta de rendimiento original y la revisión del delta. T-10 permanece abierta: CI de referencia run 42085116173, commit aa25ddac5a37288baf5ed67a64acd3840fd75d63, todavía en ejecución. No se ha cambiado código tras este candidato; sólo se incorporan dictámenes y estados del ledger.

## Cierre

Run 42085116173 sobre aa25dda terminó success en todas las puertas: Python 10.469/41, Node 470/16/cero failed, interop 92 al día, checks de manual, evals, sintaxis y versiones correctos. El redactor pasó en referencia sin cambiar su código ni su umbral. Se cierra T-10 y el plan; el commit posterior sólo incorpora evidencia, estados y changelog ES/EN. No hay publicación npm, tag ni merge en esta entrega.

Verificación del cierre documental: 550 tests de índice de roadmap, ledger-lint, cifras y changelog correctos (38,74 s); un aviso histórico conservado. Lint: cero errores y 16 avisos existentes. Handbook, coherencia de versiones, changelog --check y scope-check correctos (82 archivos, sin fuera de alcance ni criterios alterados).
