# Análisis estructural externo (opt-in)

Léela solo cuando el proyecto ya tenga configurado un analizador estructural externo (servidor MCP o
CLI de un proveedor) y se pida su baseline, la revisión de un cambio o el delta de una rama. Sin esa
configuración, `code-health.py` es la medida y esta referencia no aplica.

El analizador externo **complementa** a `code-health`: no lo sustituye ni se mezcla con él. Su
puntuación es una opinión del proveedor sobre mantenibilidad, no una prueba de corrección; `qa`, los
tests y la revisión adversarial siguen siendo necesarios aunque la puntuación suba.

## Antes de invocarlo

| Comprobación | Si falla |
|---|---|
| El proyecto lo declaró (config versionada o petición expresa del usuario) | No lo busques ni lo instales: sigue con `code-health.py` |
| Versión del proveedor fijada y conocida | Registra `version: desconocida`; ese resultado no es comparable con otro |
| Cuenta o licencia propias del usuario, ya configuradas | Avisa y sigue con `code-health.py`; no abras sesión ni pidas credenciales por tu cuenta |
| Arrancarlo no descarga nada (binario ya presente) | Un `npx`/descargador que baja binarios al arrancar es un efecto, no una lectura: pide autorización antes |

Descubrir el servidor no autoriza más que sus operaciones de **revisión y lectura**. Las de
configuración (cambiar reglas, umbrales, cuenta o políticas del proveedor) quedan fuera aunque
estén expuestas.

## Flujo

1. **Baseline** en la revisión base (la de `main` o el commit previo a la rama): proveedor, versión,
   reglas y raíz quedan fijados para el resto del flujo.
2. **Después** en la revisión head, con la misma raíz, versión y reglas.
3. **Delta de rama**: compara solo ficheros presentes en ambas pasadas; los nuevos y los borrados se
   listan aparte, no entran en la media.
4. Si entre 1 y 2 cambió proveedor, versión, reglas, raíz o el conjunto de lenguajes elegibles, el
   delta es **no comparable**: dilo y no publiques la diferencia de puntuación.

Un informe en precommit no demuestra que Git esté bloqueado: solo que el análisis corrió. Si el
proyecto quiere bloquear, eso es la CI del proyecto (como el trinquete de `--baseline`).

## Qué se registra (reporte bruto, redactado)

| Campo | Contenido |
|---|---|
| `proveedor`, `version` | Nombre y versión exacta; `desconocida` si no se pudo leer |
| `raiz`, `base`, `head` | Ruta relativa analizada y SHA de cada pasada |
| `reglas` | Perfil o conjunto de reglas activo; las suprimidas, con su justificación escrita |
| `lenguajes_elegibles` | Los que el proveedor dice soportar en esa raíz |
| `ficheros` | Elegibles, analizados y desconocidos (no soportados o con error), por separado |
| `estado` | Uno de los de la tabla siguiente |
| `puntuacion` | La del proveedor, **en su escala**, por fichero y global; `null` si no la dio |
| `fecha` | Del análisis, no de la recuperación del informe |

Antes de guardarlo, pasa el texto por `redactar()` de `agent-kits/shared/redact.py` y quita a mano
URLs internas, identificadores de cuenta y rutas absolutas. Guárdalo junto al JSON de `code-health`
(`docs/roadmap/<inic>/testing/` si no debe publicarse).

| Estado | Significa | No es |
|---|---|---|
| `sin_hallazgos` | Analizó ficheros elegibles y no reportó nada | «Código sano» en general |
| `sin_ficheros_modificados` | El delta no tocó ningún fichero elegible | Un análisis con resultado limpio |
| `parcial` | Quedaron elegibles sin analizar (límite, timeout, lenguaje) | Un resultado completo |
| `error` / `no_disponible` | Sin auth, sin binario, sin red o fallo del proveedor | Un cero ni un aprobado |

## Reglas

- **No reescales** nuestras métricas a la escala del proveedor ni al revés: `% duplicado` y una
  puntuación 1–10 miden cosas distintas. Se presentan lado a lado, cada una con su fuente.
- **No subas la puntuación suprimiendo reglas** sin una justificación escrita en el informe; una
  regla suprimida para que el delta salga verde es una puerta relajada, y la revisión la trata así.
- Los umbrales sugeridos por un proveedor **no son política** del proyecto hasta que el proyecto los
  adopte por escrito (constitución o `dev.json`).
- `evaluator` y `planner` usan la cifra igual que el informe de `code-health`: citada, con
  `fichero`, y como insumo de riesgo o deuda dentro del alcance, nunca como veredicto.

## Si no está disponible

- **Opcional y caído**: avisa una vez, usa `code-health.py` y declara el límite («sin análisis
  externo: proveedor no disponible»). No pidas permiso en cada fallo.
- **Gate obligatorio acordado por el proyecto**: sin evidencia compatible (mismo proveedor, versión y
  reglas que el baseline) no se declara el cierre verificado; el resto del trabajo autorizado sigue.

No hay adaptador incluido para ningún proveedor: hoy el flujo es manual, con las operaciones de
revisión que el propio proveedor exponga.
