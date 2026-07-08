# Catálogo de herramientas (la "biblioteca" instalable)

`install-tools.sh` instala este set en `~/.claude/security-tools/` (override con `SECURITY_TOOLS_DIR`).
Todo es open-source, de repos oficiales, y de uso **defensivo / pentest autorizado**. Ningún binario se versiona
(ver `.gitignore` de esta carpeta y de la carpeta de instalación).

## A. Binarios precompilados (Go) — se bajan del release por OS/arch
| Tool | Uso | Fuente | Plataformas |
|------|-----|--------|-------------|
| **nuclei** | Escáner por plantillas (misconfig, exposiciones, CVEs, default-login) | projectdiscovery/nuclei | linux/darwin/windows · amd64/arm64 |
| **httpx** | Sondeo/fingerprint HTTP (tech, título, server, status) | projectdiscovery/httpx | idem |
| **ffuf** | Descubrimiento de contenido / fuzzing de rutas y params | ffuf/ffuf | idem |
| **gitleaks** | Detección de secretos en árbol/repo | gitleaks/gitleaks | idem |

`pick_asset.py` elige el asset correcto tolerando las distintas convenciones de nombre
(`amd64`/`x64`/`x86_64`, `darwin`/`macOS`/`osx`, `.zip`/`.tar.gz`).

## B. Herramientas de script (git clone + runtime presente)
| Tool | Uso | Fuente | Requiere |
|------|-----|--------|----------|
| **testssl.sh** | Auditoría TLS/SSL (protocolos, ciphers, cert, vulns) | drwetter/testssl.sh | bash + openssl |
| **sqlmap** | Detección/explotación SQLi (**opt-in**, activo) | sqlmapproject/sqlmap | python |
| **nikto** | Escáner de servidor web (misconfig, ficheros peligrosos) | sullo/nikto | perl |

Cada una recibe un *shim* en `bin/` (p. ej. `bin/sqlmap` → `python vendor/sqlmap/sqlmap.py`).

## C. Paquetes Python (pip)
| Tool | Uso | Paquete |
|------|-----|---------|
| **wafw00f** | Detección de WAF | `wafw00f` |

## Cómo añadir una herramienta a la biblioteca
Edita la sección **CATALOG** de `install-tools.sh`:
- Binario Go de release → `install_go_bin <owner/repo> <nombre-binario>`
- Script tool → `install_git_tool <url> <dir> <shim> "<runner>"`
- pip → `install_pip_tool <paquete> <nombre>`
Y documenta la fila aquí. Reejecuta `install-tools.sh` (idempotente) o `--force` para reinstalar.

## Notas
- **Antivirus/Defender** puede marcar nuclei/sqlmap; si los pone en cuarentena, excluye `~/.claude/security-tools/`.
- **nuclei** descarga su librería de plantillas en el primer uso (`nuclei -update-templates`).
- Todo el uso activo pasa por `lib-guardrail.sh` → solo hosts locales/privados.
