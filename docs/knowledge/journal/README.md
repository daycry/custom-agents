# `docs/knowledge/journal/` — bitácora de sesión (memoria episódica)

Una entrada por sesión, **generada** por `agent-kits/shared/journal.py` (hook `SessionEnd`; la
última se reinyecta al arrancar/retomar). Cronológica y **no curada**: lo que merezca doctrina
se promueve a `adr/`, `gotchas/` o `lessons/` con el umbral de `knowledge-write.md`. **Excluida de
Confluence** (`docs/knowledge/journal/**`). Nombre: `AAAA-MM-DD-<iniciativa activa | sesion>.md` (sufijo `-2`
si otra sesión del día ya lo usó). **Las entradas se versionan** (memoria del proyecto, como ADR y lecciones);
quien no quiera versionarlas añade `docs/knowledge/journal/*.md` (no este README) a su `.gitignore`.
Este índice lo regenera `journal.py index`; no lo edites.

**Fuera del alcance del diff.** `agent-kits/shared/scope-check.py` excluye `docs/knowledge/journal/**`
por defecto —este `README.md` incluido—: las entradas las escribe el hook de sesión, no una tarea, así
que aparecen en la lista `excluidos` (con el glob que las excluyó) y no cuentan para el exit code. Es
la excepción al «`docs/knowledge/**` siempre en alcance»: si una tarea toca a propósito algo de esta
carpeta, que lo declare en su campo `- **Archivos**:` — lo declarado gana a la exclusión y vuelve a
«en alcance».

| Fecha | Iniciativa | Resumen | Fuente |
|---|---|---|---|
| [2026-09-08](2026-09-08-sesion.md) | n/a | continua con la implementación | hook |
