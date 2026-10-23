# Revisores PHP y Python, pruebas del PR y ML — A040, A048, A050–A051

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **22.293 bytes/432 líneas**. [agents-php-python-tests-mle-reading-evidence.json](agents-php-python-tests-mle-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

PHP y Python son stacks **con consumidor**. Su dueño es `stack-practices`
(`php-codeigniter.md`, `python.md`), con `reviewer` como ejecutor de las lentes
y `cybersecurity` como catálogo de la Lente C. El consumidor PHP declarado es
CodeIgniter 4. Laravel (D-127) y FastAPI/Django (D-129) están aparcados.

## A048 — php-reviewer

`5.712 bytes/109 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisor PHP centrado en Laravel: PSR-12, tipos, Eloquent, seguridad y calidad.
Solo aprueba si PHPStan, Psalm, PHPUnit y Pint pasan.

**Comparación.** `php-codeigniter.md` cubre las fronteras del consumidor real:
`allowedFields` no es validación ni autorización (l.5, l.33-34), CSRF y *auto
routing* (l.30-33), `transStatus` (l.11-15) y pruebas con motor real (l.36-40).
La seguridad la cubre la Lente C con `language-patterns/php.md` (`unserialize`
l.13, hash débil l.21, asignación masiva l.57). Eloquent, Blade, Livewire y
Filament (l.48-55, 98-100) son un framework no declarado (D-127, S155–S159). El
resto es estilo (PSR-12, docblocks, `final`, `readonly`, `isEmpty()`), que
`reviewer` excluye (`agents/reviewer.md:41-43`). La guía CI4 **no** recoge un
punto que la pieza sí trae (l.39): las subidas de fichero sin validar tipo,
tamaño ni extensión. `cybersecurity` lo nombra solo para auditar
(`references/agent-prompts.md:401`). Defectos:

| Punto | Problema |
|---|---|
| Aprobación con `phpstan analyse --level max` y Psalm en verde (l.74-75, 92-94) | En un repositorio con baseline o nivel menor falla siempre: bloqueo perpetuo sin relación con el diff. La puerta es el nivel o baseline configurado del proyecto, sobre lo cambiado |
| `final` y `readonly` como HIGH (l.45-46) y HIGH bloquea (l.94) | Una preferencia bloquea igual que una inyección |
| «Shadowing builtins (`$collection`, `$request`, `$model`)» (l.68) | En PHP no son *builtins*: es la regla de Python copiada |
| `composer audit` (l.78) | Red y vulnerabilidades de dependencias: son de `nemesis` y de `dependency-upgrade` |

**Destino:** una línea en `skills/stack-practices/references/php-codeigniter.md`,
sección «Fronteras y pruebas de PHP/CodeIgniter» (contrastar con la guía oficial
de CI4 antes de integrar): «Subidas: validar con las reglas de fichero de CI4
(`uploaded`, `max_size`, `mime_in`/`ext_in`); el nombre y la extensión del
cliente no son confiables (`getRandomName()`) y el fichero se guarda fuera de
`public/`; prueba con tipo falsificado y tamaño en el límite». Laravel: aparcado (D-127).

## A051 — python-reviewer

`4.391 bytes/107 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisor Python: PEP 8, idioms, type hints, seguridad, concurrencia y
comprobaciones de Django, FastAPI y Flask.

**Comparación.** `python.md` es más preciso en lo que importa: cancelación y
concurrencia acotada (l.3-15), errores encadenados y redactados (l.30-36, D-038
integrada) y fixtures (l.38-43). Para S218 ya se concluyó que cubre lo útil.
`pickle`, `yaml.load` y Bandit van a la Lente C (`language-patterns/python.md:9,12`),
y el N+1 a la Lente D. Los frameworks (l.97-99) están aparcados (D-129). El
resto es estilo. `python.md` **no** recoge un punto: el argumento por defecto
mutable (l.49), un defecto de corrección (estado compartido entre llamadas), no
de estilo. Defectos:

| Punto | Problema |
|---|---|
| «Path Traversal: validate with normpath, reject `..`» (l.30) | Insuficiente: una ruta absoluta no contiene `..` y `os.path.join(base, "/etc/passwd")` la devuelve tal cual. `language-patterns/python.md:19,166-171` ya da lo correcto (resolver y comprobar que queda bajo la raíz) |
| Las comprensiones frente a bucles de estilo C y `isinstance` cuentan como HIGH (l.44-48), y HIGH bloquea (l.93) | El estilo se convierte en bloqueo |
| «Missing `Optional` for nullable parameters» (l.42) | Desde Python 3.10 se usa `X \| None`; depende de la versión mínima |
| `pytest --cov=app` (l.77) | Supone un paquete llamado `app`; `coverage-gate.py` detecta el stack |

**Destino:** una línea en `skills/stack-practices/references/python.md`,
sección «Tipos, fronteras y pruebas Python»: «Argumento por defecto mutable
(`def f(x=[])`, `={}`): se comparte entre llamadas; usa `None` como centinela y
crea el valor dentro; prueba: dos llamadas sin argumento no comparten estado».

## A050 — pr-test-analyzer

`1.937 bytes/54 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Comprueba si los tests de un PR cubren el comportamiento cambiado. Gradúa los
huecos en critical, important o nice-to-have y añade observaciones positivas.

**Comparación.** El reparto ya tiene dueños. La Lente A comprueba que cada
criterio con test tiene su test (`lens-prompts.md:17`, punto 3) y que no se
relajan puertas (l.20). La Lente B busca tests borrados o con el *assert*
debilitado (l.21). `qa` cruza criterios y tests con `coverage-check.py`
(`agents/qa.md:62-69`). `unit-tests` define qué probar primero y los
antipatrones (`SKILL.md:39-60`), y la persona `agent-kits/shared/personas/test.md`
afina la Lente B. La graduación Critical/Important/Minor tiene definición en la
skill; los tres niveles de la fuente no la tienen. Las «observaciones positivas»
no tienen contrapartida ni hacen falta (salida en tablas, no ensayo).
**Defectos:** tiene Bash, pero no exige evidencia (ni `fichero:línea` ni tests
ejecutados); «flag flaky patterns» no define qué es *flaky*.

**Destino:** **Sin destino**: ya lo cubren las Lentes A y B, `coverage-check.py` y `unit-tests`.

## A040 — mle-reviewer

`10.253 bytes/162 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Revisor de ML en producción: decisión y coste de los errores, métricas y
umbrales, contrato de datos y fuga de información, reproducibilidad,
promoción, servicio, monitorización y rollback.

**Comparación.** Es un dominio sin consumidor: D-138 aparcado, junto a S175,
S176 y S220 (`skills-ml-adoption-mle.md`). El método general ya tiene dueño: la
decisión y los contraejemplos son de `analyst`; las puertas declaradas antes de
ver resultados y que fallan cerradas, de `outcome-evals`; la regresión por cada
error, de `debug-root-cause`; secretos y PII, de la Lente C y `nemesis`. Tiene
los mismos permisos que `reviewer`. Lo propio del dominio (partición temporal,
uniones *point-in-time*, equivalencia entre entrenamiento y servicio, rollback
sin reentrenar) espera a un consumidor. Defectos:

| Punto | Problema |
|---|---|
| «Reuse Existing Review Lanes» delega en 12 agentes (l.34-47) | `documentation-lookup` no existe en la fuente (el agente es `docs-lookup`): referencia rota |
| `git grep -nE "customer_id\|email\|…\|api_key\|secret\|token"` (l.134) | Imprime las líneas completas, con valores, sin regla de redacción; `cybersecurity` enmascara (`agent-prompts.md:198-201`) |
| «Look for an Iteration Compact» (l.27) | Artefacto de otro ecosistema que se presenta como requisito |

**Destino:** **Sin destino** (D-138 aparcado). Con un consumidor de ML, su
checklist se lee junto a S175 y S176.
