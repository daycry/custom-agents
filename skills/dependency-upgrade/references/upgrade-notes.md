# Leer un changelog/UPGRADING y anotar breaking changes (paso 2 de `dependency-upgrade`)

Se lee **solo al llegar al paso 2** de la skill, cuando hay dependencias marcadas `major`.

## Dónde suele estar la información (en este orden)

1. Guía de migración oficial de la versión de destino (`UPGRADING.md`, `MIGRATION.md`, «Upgrade
   guide» en la doc del proyecto). Es la fuente más fiable: lista lo que rompe y cómo adaptarlo.
2. `CHANGELOG.md` / `HISTORY.md` / `CHANGES.rst` del repositorio, sección de la versión mayor —
   busca las palabras **BREAKING**, **Removed**, **Deprecated**, **Dropped support**, «requires».
3. Notas de la release en el hosting del código (GitHub/GitLab Releases) — a veces es lo único.
4. Requisitos de plataforma: versión mínima de Node/PHP/Python/Go/.NET que exige la nueva versión.
   Un major que sube el runtime mínimo es un breaking change del **proyecto**, no solo del paquete.

Con WebFetch: pide explícitamente «lista los breaking changes entre <actual> y <destino> y la versión
mínima de <runtime>». Sin WebFetch: anota la URL probable y márcalo **pendiente de leer** — un
changelog no leído no se resume.

## Qué anotar por paquete (formato de la spec)

| Campo | Ejemplo |
|---|---|
| Paquete · actual → destino | `laravel/framework` · `10.48.0 → 11.0.0` |
| Runtime mínimo | PHP 8.2 (hoy el proyecto declara `>=8.1`: **hay que subir PHP también**) |
| Breaking changes que afectan a ESTE proyecto | `Route::middleware` cambia firma → `routes/web.php:14, 22`; `app/Http/Kernel.php` desaparece → migrar a `bootstrap/app.php` |
| Breaking changes que NO afectan | listar 1-3 como evidencia de que se leyó (p. ej. «cambios en Broadcasting: el proyecto no lo usa») |
| Transitivas arrastradas | `laravel/sanctum` 3 → 4, `phpunit` 10 → 11 |
| Esfuerzo relativo | bajo (solo lockfile) · medio (< 10 ficheros) · alto (arquitectura o runtime) |
| Fuente | URL exacta del UPGRADING/changelog + fecha de lectura |

Cómo saber si un breaking change «afecta a este proyecto»: `grep -rn` de los símbolos/APIs que
el changelog cita, sobre el código propio (fuera de `vendor/`, `node_modules/`). Sin ocurrencias →
no afecta (dilo); con ocurrencias → cita `fichero:línea` en la spec.

## Cómo cortar los lotes

- **Un lote de patch + minor** por ecosistema (o global si son pocos): riesgo bajo, criterios =
  suites verdes + smoke.
- **Un major por iniciativa**, o **una familia** (framework + sus plugins/adaptadores que deben
  moverse juntos). Dos majors independientes en la misma spec dificultan aislar qué rompió qué.
- Si un major exige subir el runtime, la subida del runtime es **su propia fila de riesgo** y suele
  merecer ir primero (o aparte).

## Señales de que hay que parar y preguntar

- El changelog cita una **reescritura** de un módulo que el proyecto usa mucho (p. ej. el ORM, el
  router, la autenticación): el esfuerzo pasa de «upgrade» a «migración» → probablemente `architect`.
- El paquete está **abandonado** (sin releases en > 2 años, issues sin respuesta): la decisión no es
  «subir», es «sustituir» → otra spec.
- La herramienta `outdated` no está disponible y el usuario no puede ejecutarla: la spec se escribe
  con `latest` desconocido y lo dice en «Datos necesarios»; `evaluator` presupuestará con
  incertidumbre alta.
