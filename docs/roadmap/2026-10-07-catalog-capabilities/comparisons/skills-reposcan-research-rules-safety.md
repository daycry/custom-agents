# Inventario de repositorios, investigación, destilado de reglas y guarda de órdenes — S237, S238, S240 y S243

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **22.650 bytes/624 líneas**, y los dos scripts de S240
(`scan-rules.sh`, `scan-skills.sh`: 5.497 bytes/187 líneas), leídos completos.
[reposcan-research-rules-safety-reading-evidence.json](reposcan-research-rules-safety-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S237 — Puntero de instalación de un escáner de repositorios

`7.242 bytes/170 líneas`. No audita nada: instala otra skill desde un commit
fijado de un repositorio externo (clonado, revisión manual, cerrojo, copia de
seguridad y vuelta atrás) y describe sus capacidades: clasificar ficheros en
propios, de terceros o artefactos de build, detectar librerías incrustadas y
dar un veredicto por módulo.

**Comparación.** Instalar código externo no entra en el plugin. Lo descrito
solapa con `code-health` (duplicados, tamaño, hotspots) y `dependency-upgrade`
(dependencias declaradas). Hay un hueco real: `code-health` excluye por defecto
`vendor/`, `node_modules/`, `dist/`, `build/` y `target/`, y `deps-inventory.py`
solo lee manifiestos, así que **nadie informa del código de terceros incrustado
ni de los artefactos de build versionados**. Propuesta menor y determinista: que
`code-health` cuente los ficheros **versionados en git** que caen en esas
exclusiones y los muestre como aviso, sin analizarlos.

El patrón del instalador (commit fijado, sustitución con copia previa y
recuperación) ya lo tiene `install/install.mjs` con escritura atómica y
desinstalación por manifiesto. Defectos: `set -euo pipefail` en un fragmento
para pegar en una shell interactiva la cierra al primer error; la revisión
depende de que alguien teclee `install`, y un agente que lo ejecute podría
responderse a sí mismo; las cifras del ejemplo (636 MB de artefactos) no son
verificables.

**Destino:** el aviso de ficheros versionados excluidos en `code-health`.

## S238 — Investigación con evidencia actual

`3.605 bytes/113 líneas`. Envoltorio sobre otras skills del corpus de búsqueda
e investigación: empezar por lo que aporta el usuario, clasificar la pregunta,
usar la vía más ligera, etiquetar hecho con fuente, contexto del usuario,
inferencia y recomendación, con fechas, y proponer vigilancia si se repite.

**Comparación.** Su lectura completa ya se reutilizó en
[skills-data-pipelines-research.md](skills-data-pipelines-research.md) (S072), que
propuso una guía opcional de investigación con evidencia y pidió resolver en
T-08 el solape con esta pieza. Este bloque lo resuelve: S238 no añade método a
S072 ni a `research-first` (separar hecho, declaración ajena, inferencia y
estimación; no preguntar lo ya disponible; fechas). Lo único nuevo, «si la misma
pregunta se repite, dilo», cabe como una frase en esa guía; el plugin no
programa vigilancias. Depende de cuatro skills del corpus que no están en el
bundle, y su vía de «enriquecer personas y empresas» choca con la regla de no
manejar datos personales.

**Destino:** absorbida en la propuesta de S072 (una frase); sin pieza propia.

## S240 — Destilar principios repetidos en reglas

`9.586 bytes/265 líneas` más dos scripts. Inventario determinista de skills y
reglas, lectura cruzada por un modelo en lotes temáticos y veredicto por
candidato (añadir, revisar, sección nueva, fichero nuevo, ya cubierto,
demasiado específico), siempre con aprobación del usuario.

**Comparación.** El plugin no tiene una capa de «reglas»: los principios viven
en `docs/CONVENTIONS.md` y en ADR. Solapa con `capability-audit` (solapes y
consolidación), `journal.py candidatas` (patrones repetidos en 2 o más sesiones,
que nacen como propuesta) y el umbral de `knowledge-write.md`. Aporta un filtro
bueno y verificable: **solo se eleva un principio si aparece en 2 o más piezas,
se puede escribir como «haz X / no hagas Y» y tiene un riesgo concreto si se
ignora**, y no está ya cubierto con otras palabras. Es el mismo trabajo que
hace T-03.

**Destino:** una salida «elevar a convención» en el método de
`capability-audit`, con esos tres filtros; la escritura sigue en su dueño
(convenciones por cambio revisado, conocimiento por `knowledge-curator`).

Defectos: guarda `results.json` dentro del directorio de la skill (estado
mezclado con código, compartido entre proyectos y perdido al actualizar);
`scan-skills.sh` no lee descripciones multilínea (`description: >`, las que usa
todo este plugin), así que el agrupado «por descripción» queda vacío;
`scan-rules.sh` antepone `~/` aunque la ruta no esté bajo el directorio personal
(`~//opt/...`); supone que las reglas caben enteras en el contexto («unas 800
líneas») sin alternativa; requiere `jq` sin comprobarlo.

## S243 — Guarda de órdenes destructivas

`2.217 bytes/76 líneas`. Tres modos por hooks `PreToolUse`: avisar ante órdenes
destructivas, congelar la escritura a un directorio, o ambas; registro en el
directorio personal y desactivación por orden.

**Comparación.** No trae implementación: describe hooks que no están en la
pieza. Como diseño choca con ADR-007: un bloqueo vive en el frontmatter del
agente que restringe, no en un hook global. El plugin ya lo hace con
`guardrail-check.py` (git destructivo, `rm -rf` sobre rutas críticas, alcance de
escritura, análisis de `sh -c` y refspec `+rama`, con tests y desactivable en
`dev.json`); «congelar a un directorio» equivale al alcance más `scope-check.py`.

| Pieza | Problema |
|---|---|
| Lista de patrones literales | Se evade con variantes (`rm -r -f`, `find -delete`) |
| Mismo listado: «pide confirmación» en un modo y «bloquea» en otro | Dos comportamientos para una regla sin decir cuál prevalece |
| `/safety-guard off` | El propio agente puede apagar su guarda |
| Registro en `~/.claude/safety-guard.log` | Fuera del proyecto y sin redacción de las órdenes |

Ideas a evaluar: `npm publish`, `docker system prune`, `kubectl delete` y
`DROP TABLE` no están en `guardrail-check.py`; T-08 decide si alguno entra en las
reglas del `implementer`, con test negativo y dentro de ADR-007.

**Destino:** esa evaluación en `guardrail-check.py`; la pieza, **sin destino**.
