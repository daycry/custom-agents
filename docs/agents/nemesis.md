# Documentación del sistema `nemesis`

Auditoría de ciberseguridad end-to-end para Claude Code: análisis estático de código (SAST) + pentest activo local (DAST), con memoria persistente entre auditorías e informe visual por cada ejecución. Diseñado para auditar **entornos locales y propios**, nunca sistemas de terceros.

---

## 1. Visión general

El sistema tiene tres componentes que trabajan en capas:

| Capa | Qué es | Ubicación |
|------|--------|-----------|
| **Agente `nemesis`** | Orquestador. Supervisa el flujo completo, dialoga con el usuario, mantiene la memoria y entrega el informe. | `agents/nemesis.md` |
| **Skill `cybersecurity`** | Motor SAST. Análisis estático del código en 8 dimensiones con agentes especialistas en paralelo. | `skills/cybersecurity/` |
| **Toolkit `nemesis`** | Motor DAST + generación de informe. Scripts para pentest activo local y render del HTML. | `agent-kits/nemesis/tools/` y `agent-kits/nemesis/report/` |

La idea central: `nemesis` es el director de orquesta. Llama a la skill para leer el código, lanza el toolkit contra la aplicación en ejecución, funde ambos resultados en un único `findings.json` y lo convierte en un informe `index.html` navegable. Todo queda registrado para poder comparar tendencias en la siguiente pasada.

---

## 2. El agente `nemesis` (orquestador)

**Rol.** Actúa como un auditor externo que combina SAST y DAST, mantiene memoria entre auditorías y entrega un informe visual con formato fijo.

**Personalidad.** Adopta un tono de pentester provocador y directo en el chat (te pica para que arregles las cosas), pero con límites estrictos: el pique va siempre contra el código y nunca contra la persona, español correcto sin emojis, y cada afirmación respaldada por evidencia real. Ese tono vive solo en la conversación; el `findings.json` y el informe HTML se mantienen profesionales y sobrios.

**Herramientas que usa:** Read, Grep, Glob, Bash, Write, Edit, WebFetch, Agent.

### Reglas invariantes (no negociables)

El guardrail de autorización es el pilar del sistema. El componente activo (DAST) solo se dispara contra hosts locales o privados: `localhost`, `127.0.0.1`, `::1`, `*.test`, `*.local`, `*.internal`, y rangos privados (`10.x`, `172.16-31.x`, `192.168.x`, `169.254.x`, `host.docker.internal`). Cualquier objetivo externo se rechaza a nivel de script vía `lib-guardrail.sh`. La explotación SQLi activa con `sqlmap` requiere opt-in explícito del usuario sobre un parámetro concreto. Toda evidencia con secretos se redacta (`first4****last4`). Además, el agente nunca instala herramientas en silencio ni modifica el código del proyecto auditado: solo escribe en la carpeta `docs/security-scan/`.

---

## 3. Memoria persistente — `docs/security-scan/`

Dentro de la carpeta `docs/` del proyecto auditado, `nemesis` crea y mantiene esta estructura (`docs/security-scan/` va en el `.gitignore` del proyecto porque los hallazgos son sensibles; el resto de `docs/` sí se versiona):

```
docs/security-scan/
├── .gitignore          # ignora binarios y datos sensibles (raw/)
├── config.md           # URL local objetivo, alcance por defecto, registro de autorización
├── STATE.md            # postura actual: último scan, score, findings abiertos, próximos pasos
├── MEMORY.md           # índice histórico de scans (fecha · score · grado · resumen · enlace)
└── YYYY-MM-DD_HHMM/    # una carpeta por ejecución
    ├── index.html          # informe visual (formato fijo)
    ├── findings.json       # datos normalizados
    ├── active-scan.json    # salida DAST propia
    ├── static-audit.md     # salida SAST
    └── raw/                # volcados crudos de las tools externas
```

Cada sesión abre leyendo `STATE.md` + `MEMORY.md` (o hace onboarding si es la primera vez) y cierra actualizando ambos. Esto permite que en cada pasada el informe muestre la **tendencia**: qué se corrigió, qué sigue abierto y qué reincide.

---

## 4. Flujo de auditoría (7 fases)

1. **Recepción/apertura** — lee la memoria existente; fija target y alcance desde `config.md` o el prompt.
2. **SAST (código)** — ejecuta la skill `cybersecurity` sobre el proyecto → `static-audit.md`.
3. **DAST (target vivo)** — solo si hay target local y el alcance lo incluye. Corre `active-scan.sh` (harness propio, solo curl) y `run-external.sh` (nuclei, httpx, testssl, nikto, wafw00f). SQLi solo con opt-in.
4. **Normalización** — funde SAST + DAST en un único `findings.json`, deduplica hallazgos cross-source, calcula conteos, scores por área, score global ponderado, grado A–F y tendencia vs. el scan anterior.
5. **Informe** — genera el HTML con `build-report.php` (o un fallback en node/python) inyectando el JSON en `template.html`.
6. **Entrega** — resume score/grado, conteos por severidad, top findings y la ruta del `index.html`.
7. **Cierre** — actualiza `STATE.md` + `MEMORY.md`.

**Escala de grados:** A ≥ 90, B ≥ 75, C ≥ 50, D ≥ 25, F < 25.

### Verificación del toolkit (antes del DAST)

Antes de cualquier DAST, el agente ejecuta `check-tools.sh` para ver qué herramientas hay instaladas. Si falta alguna, **se detiene y pide permiso** mostrando la lista exacta y para qué sirve cada una; solo instala (vía `install-tools.sh`, en `~/.claude/security-tools/`, fuera del repo) si el usuario acepta. Si el usuario declina, continúa con lo disponible: el harness propio funciona solo con curl, y el informe declara qué áreas quedaron con cobertura parcial.

---

## 5. La skill `cybersecurity` (motor SAST)

Análisis estático del código en **8 dimensiones**, lanzando agentes especialistas en paralelo con scoring ponderado (0–100):

1. Detección de vulnerabilidades (OWASP Top 10:2021, CWE Top 25:2024)
2. Escaneo de secretos / credenciales hardcodeadas
3. Análisis de dependencias y cadena de suministro
4. Seguridad de infraestructura como código (IaC)
5. Threat intelligence (malware/backdoor/C2, mapeo MITRE ATT&CK)
6. Verificación de autorización y control de acceso
7. Auditoría de código generado por IA
8. Mapeo de compliance (PCI, HIPAA, SOC2, GDPR)

El flujo interno es: **GATHER** (detecta stack, puntos de entrada y fronteras de confianza) → **ANALYZE** (8 especialistas en un solo mensaje paralelo) → **RECOMMEND** (agrega scores, encadena rutas de ataque, mapea compliance) → **EXECUTE** (informe estructurado con remediación priorizada). Incluye supresión de falsos positivos consciente del framework y modelado de amenazas STRIDE.

La skill se apoya en una amplia biblioteca de referencias en `skills/cybersecurity/references/`: patrones por lenguaje (Python, JS/TS, Java, Go, Rust, Ruby, PHP, C/C++, C#, Swift/Kotlin, Shell), patrones IaC (Terraform, Docker, Kubernetes, GitHub Actions), taxonomía de vulnerabilidades, matriz de compliance, threat intelligence, rúbrica de scoring y reglas de supresión de falsos positivos.

---

## 6. El toolkit `nemesis` (`agent-kits/nemesis/`)

### `tools/` — motor DAST

| Archivo | Función |
|---------|---------|
| `check-tools.sh` | Comprueba qué herramientas están instaladas (exit code = nº que faltan). |
| `install-tools.sh` | Instalador cross-platform e idempotente; instala solo lo que falta. |
| `pick_asset.py` | Selecciona el binario de release correcto según OS/arquitectura. |
| `lib-guardrail.sh` | Gate de autorización: solo permite hosts locales/privados. |
| `active-scan.sh` | Harness DAST propio, sin dependencias (solo curl). |
| `run-external.sh` | Wrappers guardrailed de nuclei, httpx, testssl, nikto, wafw00f, sqlmap (DAST). |
| `run-static.sh` | Escáneres estáticos **sin guardrail** (no hay host): `trivy fs` (deps) + `hadolint` (iac). |
| `catalog.md` | Catálogo declarativo de la biblioteca de herramientas instalables. |

**Biblioteca de herramientas** (todas open-source, uso defensivo):

- **Binarios de release** (por OS/arch): `nuclei` (plantillas), `httpx` (fingerprint), `ffuf` (contenido), `gitleaks` (secretos), `trivy` (SCA de dependencias → `deps`), `hadolint` (lint de Dockerfile → `iac`).
- **Herramientas de script** (git clone + runtime): `testssl.sh` (TLS), `sqlmap` (SQLi, opt-in), `nikto` (servidor).
- **Paquetes pip**: `wafw00f` (detección de WAF).

`trivy` y `hadolint` son **estáticos** (escanean el árbol del proyecto): corren en la fase SAST vía `run-static.sh`, no contra un host, y sus hallazgos se funden en las áreas ya existentes `deps` e `iac` (sin cambios de esquema ni de informe). `trivy` descarga su BD de CVEs en el primer uso.

Los binarios viven en `~/.claude/security-tools/`, fuera del repo y gitignored.

### `report/` — generación del informe

- `schema.md` — el contrato de datos de `findings.json` (ver abajo).
- `template.html` — plantilla del informe visual, formato fijo.
- `build-report.php` — funde `findings.json` + plantilla → `index.html`.

---

## 7. Contrato de datos — `findings.json`

Todo scan produce un único `findings.json` con esta forma (resumida):

- **`meta`** — proyecto, target_url, scan_id, fecha, scope (`full`/`quick`/`diff`/`dast`), autorización, tools usadas, `overall_score` (0–100), `grade` (A–F) y `verdict` de una frase.
- **`counts`** — conteo por severidad: critical, high, medium, low, info.
- **`areas[]`** — score por área (vuln, authz, secrets, deps, dast…) con su peso y resumen.
- **`findings[]`** — cada hallazgo con id, título, severidad, confianza, área, CWE, OWASP, fuente (sast/dast), ubicación y cuatro campos didácticos: **qué es, por qué importa, cómo se explota y cómo se corrige**, más evidencia redactada.
- **`trend`** (opcional) — comparación con el scan anterior: ids nuevos, corregidos y recurrentes.

Reglas del contrato: severidades y áreas siempre en minúscula, evidencia siempre redactada, y el informe tolera campos ausentes (trend, target_url, evidence).

---

## 8. Cómo se invoca

Dentro del proyecto a auditar, en Claude Code:

- `usa el agente nemesis`
- `nemesis, audita este proyecto`
- `activa nemesis contra https://miapp.test`

La primera vez hace un onboarding rápido: confirma la URL local y la autorización, y verifica el toolkit (pidiendo permiso antes de instalar nada). Los informes quedan en `docs/security-scan/<fecha>/index.html` del proyecto auditado, y esa carpeta va en `.gitignore` porque los hallazgos son sensibles.

**Requisitos por máquina:** git, curl y python o php. El instalador resuelve el resto.