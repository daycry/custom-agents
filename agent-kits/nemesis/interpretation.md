# Interpretación de tools externas (calibración) — referencia de nemesis

> Detalle operativo que **nemesis** lee **solo al llegar a F4 (Normalización)**, no antes.
> Progressive disclosure: mantener esto fuera del prompt principal ahorra tokens en las
> auditorías que no llegan a interpretar tools externas (solo-SAST, quick).

- **nuclei**: `$DIR/raw/nuclei.jsonl` — cada línea es un match (template-id, severity, matched-at). Fúndelos como findings DAST; descarta info triviales duplicadas del harness propio.
- **testssl**: `$DIR/raw/testssl.json` — findings TLS; sube a Medium los `HIGH/CRITICAL` de protocolo/cipher.
- **nikto**: `$DIR/raw/nikto.txt` — server misconfig; calibra (nikto es ruidoso).
- **httpx**: fingerprint (tech/título/server) → contexto, normalmente Info.
- **wafw00f**: presencia/ausencia de WAF → Info.
- **gitleaks** (opcional, sobre el repo): `gitleaks detect --no-git -s <proyecto>` para secretos en árbol de trabajo.
- **trivy** (estático): `$DIR/raw/trivy.json` — vulnerabilidades de dependencias. Cada `Results[].Vulnerabilities[]` → un finding `source=sast`, `area=deps`, severidad mapeada (CRITICAL/HIGH/MEDIUM/LOW), `id`=`VulnerabilityID` (CVE), `location`=`Target` + `PkgName@InstalledVersion`, `fix`=`FixedVersion` si existe. **Deduplica** contra dependencias ya señaladas por la skill (sube confianza, no dupliques). Si `raw/trivy.err` indica fallo de BD/red, decláralo en `tools_used` (cobertura parcial).
- **hadolint** (estático): `$DIR/raw/hadolint.json` — array de objetos `{file,line,code,level,message}`. Cada uno → finding `source=sast`, `area=iac`, severidad por `level` (error→High, warning→Medium, info/style→Low), `location`=`file:line`, regla=`code` (`DLxxxx`). Si no había Dockerfile, anótalo como N/A.
