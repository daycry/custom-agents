# nemesis — sistema de auditoría de ciberseguridad

Orquesta **SAST** (skill `cybersecurity`) + **DAST/pentest activo local** con **memoria persistente** e
**informe visual** (`index.html`) por cada auditoría. Pensado para auditar **tus propios entornos locales**.

## Piezas
```
.claude/agents/nemesis.md      # el agente orquestador (supervisor + onboarding + memoria)
.claude/agent-kits/nemesis/
├── tools/
│   ├── check-tools.sh      # comprueba qué tools hay (el agente pide permiso antes de instalar)
│   ├── install-tools.sh    # instalador cross-platform del toolkit (catálogo declarativo)
│   ├── pick_asset.py       # selector de release binario por OS/arch
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
bash .claude/agent-kits/nemesis/tools/install-tools.sh
```

## Seguridad / autorización
El DAST **solo** apunta a hosts locales/privados (`lib-guardrail.sh`); rechaza cualquier objetivo externo.
`sqlmap` (explotación activa) requiere opt-in explícito. Las evidencias con secretos se redactan.
No es para atacar sistemas de terceros.
