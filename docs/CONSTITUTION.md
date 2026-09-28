# Constitución del proyecto — custom-agents

> Principios permanentes que TODO trabajo en este repositorio debe respetar.
> Los agentes del plugin custom-agents la leen antes de trabajar y la revisión
> adversarial marca como gap cualquier diff que viole un principio explícito.
> Última revisión: 2026-09-28 · Mantenida por: Daycry

## 1. Principios de código

- Todo cálculo o veredicto va en un script con tests y códigos de salida, nunca en prosa del agente.
- Todo código nuevo se escribe con TDD: test primero y rojo evidenciado en el ledger (`RED:`).
- Ninguna pieza bloquea el ciclo: lo opcional degrada con aviso y los hooks salen siempre con exit 0.
- Ningún gap de revisión se da por `corregido` sin un test dedicado que lo nombre.

## 2. Arquitectura fijada / vetada

- **Fijado:** las piezas reales (`agents/`, `commands/`, `skills/`, `hooks/`) son la única fuente; `interop/`, `.codex-plugin/` y `.agents/plugins/` los genera `scripts/export-interop.py` y no se editan a mano.
- **Fijado:** cada responsabilidad del ciclo tiene un único dueño que decide y escribe su artefacto; el resto solo la lee (`docs/agents/ROLES.md`, ADR-011).
- **Fijado:** `tasks.md` es el ledger canónico de cada iniciativa; cualquier otro registro (Jira, dashboards) es espejo.
- **Vetado:** llamadas de red desde los hooks, y rutas absolutas del repo en los scripts (los kits se resuelven en tiempo de ejecución con `find`).
- **Vetado:** dependencias fuera de la stdlib de Python en los scripts del plugin.

## 3. Convenciones del equipo

- La documentación vive en `docs/`, nunca junto al código; cada agente nuevo lleva `docs/agents/<nombre>.md` y su fila en `docs/README.md`.
- Bilingüe con el inglés como principal: al cambiar un documento con espejo (README, CHANGELOG, INSTALL, CONVENTIONS, FLOWS, observability) se actualiza el espejo en el mismo cambio.
- Nombres kebab-case únicos, idénticos en `agents/`, `agent-kits/` y `docs/agents/`.
- Las `SKILL.md` son un mapa de ≤ 200 líneas; el detalle va en `references/`.
- Se publica solo con `scripts/release.py X.Y.Z`, nunca a mano; toda iniciativa se cierra con PR a `master` y la CI en verde.

## 4. Seguridad y datos

- `nemesis` hace pentest activo solo contra hosts locales/privados (`agent-kits/nemesis/tools/lib-guardrail.sh`); el guardrail nunca se puentea y la explotación activa (`sqlmap`) exige opt-in explícito.
- Ningún secreto en el repo (tokens por variables de entorno); todo texto que se persiste, envía o exporta pasa por `agent-kits/shared/redact.py`, fuente única de la redacción.
- Nunca se guarda chain-of-thought ni conversaciones crudas en ningún artefacto, índice ni export.
- Una pieza nunca borra ni sobrescribe lo que no ha creado; no sigue rutas decididas por un tercero (enlaces, traversal) y las muestra escapadas en los mensajes.
- Toda capacidad con red es opt-in y, por defecto, acotada a hosts locales/privados; los backends de conocimiento solo reciben lo aprobado por `knowledge-curator`.
