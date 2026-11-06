# agent-kits/nemesis — toolkit privado del agente `nemesis`

Motor DAST + generación de informe. Uso interno del agente `nemesis`; no invocar a mano salvo `install-tools.sh`.

- `tools/` — harness DAST propio, wrappers de tools externas, guardrail, instalador.
- `report/` — plantilla del informe, generador y `schema.md` de `findings.json`.

**Documentación completa:** [`docs/agents/nemesis.md`](../../docs/agents/nemesis.md)
**Convención del repo:** [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md)

## Instalación opcional y verificada

`tools/install-tools.sh` es un wrapper del instalador Python 3.10+. No se ejecuta al cargar el plugin. Consulta `python3 tools/install-tools.py --list` para ver versiones sin acceder a la red. Tras autorización, `bash tools/install-tools.sh --only gitleaks,hadolint` instala sólo esas herramientas.

El catálogo `tools/tools-lock.json` contiene versiones, commits y SHA-256 revisados. No se resuelven releases mutables, no se ejecuta git pull y no se actualiza pip globalmente. Los paquetes Python se instalan como wheels con hashes en un destino privado. Un archivo ajeno o modificado no se sobrescribe, tampoco con `--force`; para migrar una instalación anterior utiliza una carpeta externa nueva mediante `SECURITY_TOOLS_DIR`.

[Guía completa: requisitos, seguridad, recuperación y mantenimiento](../../docs/guides/nemesis-remediation.md). La presencia detectada por `check-tools.sh` no acredita la integridad de herramientas ajenas a este instalador.
