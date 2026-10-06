# Verificación del cierre de plugin-refactor

Fecha: 2026-10-06. Base: `1f2923d`. Métricas y hashes de contratos en
[closure-metrics.json](closure-metrics.json). Capturas crudas, transcripciones,
configuraciones privadas y entornos temporales quedan fuera de Git.

## Refactor puro de cinco archivos

| Archivo | Funciones >30 antes | Después |
|---|---:|---:|
| `agent-kits/shared/task-brief.py` | 5 | 3 |
| `agent-kits/shared/knowledge-find.py` | 3 | 1 |
| `agent-kits/shared/doctor.py` | 14 | 7 |
| `scripts/lint_plugin.py` | 10 | 4 |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` | 4 | 0 |
| **Total** | **36** | **15** |

El detector canónico, sin cambios, mide 15≤16; los otros cuatro archivos suman
12≤14. Ninguna función nueva supera 60 líneas: máximo AST de 32. Las tres
funciones largas restantes de task-brief son del parser literal añadido por
iniciativas posteriores. Se conserva íntegro.

Se extraen lectura/formato de memoria, validación/registro del linter, estados
de instalación/backend de doctor y salidas del dashboard. Las constantes se
agrupan antes de las funciones que las utilizan.

El bloque (a) conserva todos los tests existentes. Las firmas previas y los AST
de add_argument()/exit() permanecen iguales. Hay 16 capturas con hashes: ayudas,
JSON de knowledge-find y dashboard, HTML/MD/metrics-MD sobre el roadmap actual,
brief y JSON de scope-check; este último no cambia de fuente. Se comparan stdout,
stderr, exit y los bytes de los archivos emitidos. Se precalienta el índice para
comparar el mismo estado de caché. Es la fase REFACTOR sobre contratos existentes,
sin atribuirle un RED nuevo. Prosa/capturas: TDD n/a.

## Conciliación de líneas base

Las características posteriores a septiembre hacen incomparable aquella foto
global con el árbol actual. Se conserva la original y se añade una
[base del cierre](code-health-closure-baseline.json), tomada del código versionado
anterior con los mismos flags: `--exclude-tests --exclude-path interop --json
--top 1000`. El objetivo de cinco hotspots se mantiene.

Árbol comparable: funciones largas **221→200**; duplicado **6,6 %→6,6 %**;
bloques duplicados **760→760**; anidamiento **7→7**; TODO **9→9**; líneas
**31.200→31.287**. No empeora ninguna métrica que el detector clasifica como
mejor/peor; las líneas crecen por las extracciones. El historial Git aislado es
sintético: churn y edad de TODO no son evidencia histórica.

CA-02 se verifica sobre esta base para el diff del cierre. Las cifras históricas
de T-03/T-05…T-08 corresponden a su fuente de entonces. CA-06 esperaba un TODO;
R1/T-01 corrigió ese falso positivo y aprobó **8→0**. Los nueve marcadores actuales
son posteriores y no se eliminan para alterar una cifra. Se conservan los **19
bloques registrados** actuales, frente a los siete del diseño inicial.

## Validación complementaria del launcher

La base Linux detectó nueve fallos anteriores. Cuatro eran del escáner de
seguridad y cuatro de doctor, aún con supuestos de los hooks anteriores.
Esta corrección se declara fuera del bloque (a):

- El escáner sigue el launcher Node nominal, sus argumentos y su cierre transitivo;
  mantiene el rechazo de otros ejecutables JS y detecta red en el launcher.
- El linter no exige bit ejecutable al .mjs invocado con node.
- El test Confluence usa el hash de bytes de producción: no normaliza CRLF
  solo en su oráculo. No cambia producción Confluence.

RED: los dos nuevos contratos de test_hook_launcher_security.py fallaron antes
del arreglo. GREEN: **90 passed** entre launcher, escáner y Confluence.
Los tests existentes solo cambian en esta validación complementaria; no se
atribuyen al refactor puro ni se oculta el resultado anterior.

## Pruebas y entornos

Windows previo: **815 passed, 4 failed, 1 skipped**, 803,29 s. Los fallos previos:
grafo real de memoria que ha crecido, dos expectativas LF sobre fixtures CRLF
de --show, y bit ejecutable Unix en NTFS. Windows no es una suite global verde.

Linux previo, Python 3.11.16 / Node 22.23.3: **3.669 passed, 9 failed, 28 skipped,
8 subtests passed**, 602,88 s. Node: **131 passed, 0 failed, 3 skipped**.
Snapshots aislados con modos Git, sin configuración ni memoria privada.
La primera comparación posterior se interrumpió al reiniciar Docker y no se
cuenta como resultado. Corrida final completa: **3.680 passed, 0 failed, 28 skipped, 8 subtests
passed**, 534,51 s. Node: **131 passed, 0 failed, 3 skipped**. Tras la segunda
revisión se añaden cuatro regresiones de seguridad dedicadas: **94 passed**
en la suite complementaria actual, frente a 90 antes; no se atribuyen a la
corrida completa anterior. Metadatos de cierre: **526 passed** en cifras,
índice del roadmap y usage-meter.

Windows posterior, parser/copiado: **174 passed**; doctor/copiado:
**207 passed, 1 skipped**. Historial íntegro de T-13 conservado.

## Calibración

La [muestra recuperada](calibration.md) aporta **849.708 tokens/hora**:
14.145.747 tokens facturables / (59.932 s /3.600). Es parcial: 38 marcadores
válidos y 37 intervalos distintos; no mide las 22 tareas completas ni el cierre
Codex. Lectura de caché separada y excluida del numerador. No se inventan
desviaciones de coste ni consumo total.

## Integración

La publicación y la integración en master aún no se han ejecutado. El cierre
técnico se completa en la rama local; la constitución exige PR y CI verde para
la integración definitiva. No se publica una release en esta verificación.

## Puertas finales

Ledger-lint: 0 incoherencias y 0 avisos. Scope: 0 archivos fuera de alcance y
0 avisos; settings.json del usuario excluido por el default. Linter: 0 errores
y tres avisos preexistentes de nombres genéricos. Evals: 41 piezas, 149 casos,
0 errores. Interop: 50 archivos al día. Release 1.22.1 --dry-run: exit 0,
sin cambiar versión, crear tag ni publicar; avisa del árbol sucio, incluida la
configuración del usuario. Retro-gate: exit 0. Changelog ES/EN: 22 bullets.

La segunda revisión aprobó el refactor puro y encontró dos huecos en el escáner:
import HTTPS/argv de red y sustitución de una ruta ajena por la local. Se cierran
con imports nominales de cuatro módulos Node locales, detección de fetch y
argv, y fingerprints del bootstrap inline revisado; cualquier cambio del
bootstrap requiere revisión y actualizar su fingerprint. Las cuatro regresiones
fallaron antes de corregir y pasan después. No se ejecuta red en los mutantes.

El parser de calibración devuelve **531798.5**, mediana de seis muestras,
incluyendo 849708 de plugin-refactor. No se re-derivan bloques históricos.

## Estado tras el intento 3 (histórico)

A aprueba la propuesta. B detectó alias de argv y raíz variable desconocida;
los dos tienen tests dedicados RED/GREEN. Suite complementaria actual:
**96 passed**, ocho contratos del launcher. La fuente Node nominal también
queda protegida por fingerprint, no solo el bootstrap inline; un programa
modificado nunca se admite como si fuera el launcher revisado.

El límite de tres intentos obligó a detener el bucle. El usuario autorizó
expresamente una cuarta comprobación; las correcciones permanecieron preparadas
hasta recibir ambos dictámenes.

## Resultado final del intento 4 autorizado

A y B aprueban las dos correcciones: **0 Critical, 0 Important, 0 Minor** nuevos.
B ejecuta los ocho contratos dedicados: **8 passed**; también verifica cuatro
mutaciones JS y cuatro formas de raíz desconocida. Se conservan los veredictos
previos. El ledger y el plan quedan completados localmente, 22/22 tareas.
ADR-017 aceptada en la memoria local. La muestra compatible parcial entra en
CALIBRATION.md; el parser devuelve **531798.5**, mediana de seis muestras.
La integración por PR/master y CI remota permanece pendiente.

## Cobertura del diff de cierre

Gate configurado al 90 %: **91,29 %**, media de los cinco archivos, exit 0.
Doctor 93,20 %; knowledge-find 91,45 %; task-brief 97,13 %; linter 90,11 %;
dashboard 84,56 %. Sin archivos sin datos. Medido con pytest-cov y cobertura
de subprocesos: 401 passed/15 skipped; scripts existentes del linter (60/60)
y dashboard; CLI del dashboard sobre fixture con salidas JSON/HTML/MD.
El gate changed-only usa la base equivalente anterior al cierre. Se combinan
datos reales de coverage.py, sin modificar tests ni bajar el umbral. El resultado
de la suite completa anterior sigue siendo el informado arriba.
