# nemesis — sistema de auditoría de ciberseguridad

Orquesta **SAST** (skill `cybersecurity`) + **DAST/pentest activo local** con **memoria persistente** e
**informe visual** (`index.html`) por cada auditoría. Pensado para auditar **tus propios entornos locales**.

## Piezas
```
.claude/agents/nemesis.md      # el agente orquestador (supervisor + onboarding + memoria)
.claude/agent-kits/nemesis/
├── tools/
│   ├── check-tools.sh      # comprueba qué tools hay (el agente pide permiso antes de instalar)
│   ├── install-tools.sh    # wrapper del instalador Python con hashes
│   ├── install-tools.py    # propiedad, integridad, extracción y publicación
│   ├── tools-lock.json     # versiones/commits/assets/SHA-256 revisados
│   ├── wafw00f-requirements.txt # wheels fijados, siempre LF
│   ├── pick_asset.py       # utilidad de mantenimiento, no se usa para seleccionar al instalar
│   ├── lib-guardrail.sh    # gate de autorización: solo hosts locales/privados
│   ├── active-scan.sh      # harness DAST propio (solo curl, sin dependencias)
│   ├── run-external.sh     # wrappers de nuclei/httpx/testssl/nikto/wafw00f/sqlmap (guardrailed)
│   ├── catalog.md          # la biblioteca de tools instalables
│   └── .gitignore          # nunca versiona bin/ vendor/ ni descargas
└── report/
    ├── template.html       # informe visual/didáctico (formato FIJO)
    ├── build-report.php    # findings.json + template -> index.html
    └── schema.md           # contrato de datos findings.json
```
Binarios de tools → `~/.claude/security-tools/` (fuera del repo). Memoria e informes → `docs/security-scan/` dentro de `docs/` del proyecto auditado (esa subruta va gitignored).

## Uso
1. Activa el agente: *"usa el agente nemesis"* (o *"audita la seguridad de este proyecto"*).
2. Primera vez: onboarding (confirma URL local + autorización). Instala el toolkit si falta.
3. Corre la auditoría (SAST + DAST). Genera `docs/security-scan/<fecha>/index.html`.
4. Abre el informe. En scans sucesivos verás la **tendencia** (nuevos/corregidos/recurrentes).

Instalar el toolkit manualmente:
```bash
bash .claude/agent-kits/nemesis/tools/install-tools.sh --only gitleaks,hadolint
```

## Seguridad / autorización
El DAST **solo** apunta a hosts locales/privados (`lib-guardrail.sh`); rechaza cualquier objetivo externo.
`sqlmap` (explotación activa) requiere opt-in explícito. Las evidencias con secretos se redactan.
No es para atacar sistemas de terceros.

Requiere Python 3.10+. La instalación no adopta ni sobrescribe herramientas antiguas sin recibo, y rechaza modificaciones locales incluso con `--force`. Consulta [la guía de remediación](../guides/nemesis-remediation.md) antes de migrar o actualizar pins.
