---
id: ADR-005
titulo: "Verificador determinista `confluence-scope.py` + carpeta `docs/confluence/` generada"
estado: aceptada
fecha: 2026-08-20
iniciativa: confluence-policy
---

# ADR-005: Verificador determinista `confluence-scope.py` + carpeta `docs/confluence/` generada

## Contexto

El circuito publish/pull nunca se había ejercitado end-to-end en este repo (no existían
`confluence.json` ni `confluence-state.json`), justo cuando el coste de equivocarse (volcar
documentación interna a un espacio compartido) es mayor. Además, el usuario quería poder ver a
simple vista **qué** sube sin tener que interpretar los globs de `include`/`exclude` mentalmente.
La regla de determinismo del repo pide que los cálculos y veredictos vivan en scripts con tests y
exit codes, no en prosa de un agente.

## Decisión

Se añade el script `confluence-scope.py` con **tres funciones**: `--status` (informe humano de
qué entra en el alcance, qué está sincronizado, qué está desactualizado/pendiente y qué queda
excluido, cruzando la política con `confluence-state.json`), `--stage` (regenera por completo la
carpeta `docs/confluence/` como copia exacta de lo que se publica) y `--check` (valida invariantes,
p. ej. que `docs/security-scan/**` siga excluido). Con el staging activo, `publish.source` apunta a
`docs/confluence/`; `docs/confluence/` es **generada**, nadie la edita a mano, y lleva un aviso
`_STAGING-LEEME.md` (sin fecha embebida, para no romper la idempotencia entre ejecuciones).

## Alternativas descartadas

- **Mantener `docs/confluence/` a mano** — descartado: sería una segunda fuente de verdad que
  derivaría del original y se desincronizaría.
- **Un `README.md` generado como aviso de la carpeta** — descartado en la enmienda de cierre:
  colisionaba con la copia byte a byte del `docs/README.md` canónico dentro del propio staging; se
  renombró a `_STAGING-LEEME.md` (nombre reservado, excluido del espejo y del mapeo).
- **No verificar nada y confiar en el `include`/`exclude` interpretado a ojo** — descartado: es la
  causa raíz de los huecos que motivaron toda la iniciativa (circuito nunca ejercitado, política
  nunca comprobada).

## Consecuencias

`docs/confluence/` *es* la respuesta visual a "qué sube", sin interpretar globs. El manifiesto y
el hook (`mark-docs-pending.sh`) operan sobre los ficheros staged cuando el staging está activo
(los hashes se calculan sobre lo que de verdad se publica). `confluence-pull` debe usar el mapeo
inverso `staged → canónico` del script para escribir siempre en el fichero **canónico**, nunca en
la copia staged (que se perdería en el siguiente `--stage`). `docs/confluence/` se versiona en git
(no se ignora): duplica unos KB en disco a cambio de que el diff de cada PR muestre exactamente
qué cambia en Confluence.

## Estado

`aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` — implementada y mergeada en
`feature/confluence-policy` → `master`. Fuente:
[`docs/roadmap/2026-08-20-confluence-policy/spec.md`](../../roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño)
(filas "Determinismo de la política" y "Visibilidad de «qué sube»", D5, §"`docs/confluence/` —
reglas de la carpeta generada", y "Decisiones confirmadas" punto 5).
