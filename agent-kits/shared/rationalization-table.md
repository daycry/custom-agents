# Tabla de racionalización (fragmento compartido — formato y reglas)

**Qué es.** Una lista corta de las excusas que el modelo se da a sí mismo justo antes de saltarse
una puerta (marcar completado sin correr tests, aprobar sin leer el diff, dar verde con un flaky…),
con la razón por la que no valen y la acción concreta que toca en su lugar. Patrón «iron law» de
superpowers: nombrar la excusa en el momento en que aparece es más eficaz que repetir la regla.
La tabla **complementa** al DoD/veredicto de la pieza: el DoD dice qué evidencia hace falta; la
tabla desarma la justificación para no aportarla.

**Formato (cabecera EXACTA; el test `tests/test_rationalization_tables.py` la busca literal):**

```markdown
### Racionalizaciones que NO valen

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Los tests ya pasaban antes, no hace falta correrlos» | Se verifica el estado DESPUÉS del cambio. | Corre la suite ahora y pega la salida en el DoD. |
```

**Reglas**

1. **Máximo 8 filas** (mínimo 6). Si hay más excusas, quédate con las que de verdad han aparecido
   en los ledgers/retros de este repo; el resto sobra (token-diet: cada tabla ≤ 25 líneas incluido
   el título).
2. **Primera persona y entrecomillada**: la excusa se escribe tal y como el modelo se la dice
   («Lo probaré al final»), no como regla en tercera persona («no probar al final»).
3. **Cada fila cierra con la acción concreta** (comando, fichero, estado del ledger), no con un
   principio («sé riguroso»).
4. **Posición: JUSTO ANTES del bloque DoD/veredicto** de la pieza (`## ANTES DE CERRAR (DoD)` en los
   agentes; `### 6. Salida y traza` en `adversarial-review`). Es donde el modelo está a punto de
   cerrar y donde la excusa aparece.
5. **Sustituye prosa equivalente, no la dupliques**: si una regla en prosa dice lo mismo que una
   fila, la fila la reemplaza (una sola fuente por regla).

**Quién la lleva hoy:** `agents/implementer.md` (excusas del que implementa),
`skills/adversarial-review/SKILL.md` (excusas del REVISOR) y `agents/qa.md` (excusas de qa).
Una pieza nueva con DoD o veredicto la añade en su checklist (`skills/plugin-dev/SKILL.md`).
