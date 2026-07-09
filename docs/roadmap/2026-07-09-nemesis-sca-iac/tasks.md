# Checklist de Tareas — nemesis: trivy (SCA) + hadolint (IaC)

| | |
|---|---|
| **Estado** | en-revision |
| **Fecha** | 2026-07-09 |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | Horas (real/est) | Tokens (real/est) |
|------|------------|-------|----------|------------------|-------------------|
| F1 — hadolint (iac) | 0 | 3 | 0% | 0 / 4h | 0 / 77k |
| F2 — trivy (deps) | 0 | 4 | 0% | 0 / 6h | 0 / 118k |
| **TOTAL** | **0** | **7** | **0%** | **0 / 10h** | **0 / 195k** |

---

## F1 — hadolint (area iac)

**Estado**: borrador · **Estimado**: 4h · **Real**: — · **Coste est.**: 200 € · **Tokens est.**: 77k

### T-01 — Alta de hadolint en el toolkit

- **Descripción**: añadir `hadolint` al catálogo, al instalador (binario de release por OS/arch vía `pick_asset.py`) y a `check-tools.sh`.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 22k in / 5k out tok · 0,6 €
- **Dependencias**: ninguna
- **Archivos**: `agent-kits/nemesis/tools/{catalog.md,install-tools.sh,check-tools.sh}`

**Criterios de aceptación**
- [ ] `check-tools.sh` reporta `hadolint` (instalada/falta).

**Subtareas**
- [ ] Entrada en catálogo
- [ ] Instalación por release + verificación con `pick_asset.py`

### T-02 — Wrapper de hadolint en `run-external.sh`

- **Descripción**: ejecutar `hadolint --format json` sobre los `Dockerfile*` detectados → `raw/hadolint.json`. Sin guardrail (no hay URL).
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 13k in / 4k out tok · 0,4 €
- **Dependencias**: T-01
- **Archivos**: `agent-kits/nemesis/tools/run-external.sh`

**Criterios de aceptación**
- [ ] Con un `Dockerfile` presente, se genera `raw/hadolint.json`.

**Subtareas**
- [ ] Detectar `Dockerfile*`
- [ ] Volcar salida JSON a `raw/`

### T-03 — Normalización hadolint → area `iac`

- **Descripción**: mapear cada hallazgo (regla `DLxxxx`, nivel error/warning/info, `Dockerfile:línea`) a un finding del área `iac`; dedupe con la skill; documentar en `agents/nemesis.md` §5.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 25k in / 8k out tok · 0,7 €
- **Dependencias**: T-02
- **Archivos**: `agents/nemesis.md`

**Criterios de aceptación**
- [ ] Los hallazgos de hadolint aparecen en el área `iac` del informe.

**Subtareas**
- [ ] Mapear severidad y localización
- [ ] Dedupe contra la skill

---

## F2 — trivy (area deps)

**Estado**: borrador · **Estimado**: 6h · **Real**: — · **Coste est.**: 300 € · **Tokens est.**: 118k

### T-04 — Alta de trivy en el toolkit

- **Descripción**: añadir `trivy` al catálogo, al instalador (`install_go_bin aquasecurity/trivy trivy`) y a `check-tools.sh`.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 20k in / 6k out tok · 0,6 €
- **Dependencias**: ninguna (recomendado tras F1)
- **Archivos**: `agent-kits/nemesis/tools/{catalog.md,install-tools.sh,check-tools.sh}`

**Criterios de aceptación**
- [ ] `check-tools.sh` reporta `trivy` (instalada/falta).

**Subtareas**
- [ ] Entrada en catálogo
- [ ] Instalación vía `install_go_bin`

### T-05 — Wrapper de trivy en `run-external.sh`

- **Descripción**: ejecutar `trivy fs --format json --output raw/trivy.json <proyecto>`; avisar de la descarga de la BD de CVEs en el primer uso. Sin guardrail.
- **Estado**: borrador
- **Tiempo**: est. 1,5h · real —
- **Previsión IA**: 22k in / 6k out tok · 0,6 €
- **Dependencias**: T-04
- **Archivos**: `agent-kits/nemesis/tools/run-external.sh`

**Criterios de aceptación**
- [ ] Se genera `raw/trivy.json` sobre la raíz del proyecto.

**Subtareas**
- [ ] Invocar `trivy fs` con salida JSON
- [ ] Aviso de descarga de BD

### T-06 — Normalización trivy → area `deps` + dedupe

- **Descripción**: mapear cada vulnerabilidad (severidad, CVE, paquete\@versión, fichero de manifiesto) a un finding del área `deps`; deduplicar contra la skill (misma dependencia → 1 finding, sube confianza).
- **Estado**: borrador
- **Tiempo**: est. 2h · real —
- **Previsión IA**: 33k in / 10k out tok · 1,0 €
- **Dependencias**: T-05
- **Archivos**: `agents/nemesis.md`

**Criterios de aceptación**
- [ ] Los hallazgos de trivy aparecen en el área `deps` con severidad calibrada.
- [ ] Una dependencia ya señalada por la skill no se duplica.

**Subtareas**
- [ ] Mapear severidad/CVE/paquete
- [ ] Dedupe cross-source

### T-07 — Integración en el flujo de `nemesis` + docs

- **Descripción**: actualizar `agents/nemesis.md` (§4: correr trivy/hadolint en la fase estática; declarar en `tools_used`) y la doc (`catalog.md`, `docs/agents/nemesis.md`).
- **Estado**: borrador
- **Tiempo**: est. 1h · real —
- **Previsión IA**: 15k in / 6k out tok · 0,5 €
- **Dependencias**: T-03, T-06
- **Archivos**: `agents/nemesis.md`, `agent-kits/nemesis/tools/catalog.md`, `docs/agents/nemesis.md`

**Criterios de aceptación**
- [ ] Un scan completo ejecuta ambas tools (si están) y las declara; si faltan, marca cobertura parcial.

**Subtareas**
- [ ] Paso en el flujo (§4)
- [ ] Nota en `tools_used` y docs

---

## Notas de implementación

**2026-07-09 — implementación (código entregado, `en-revision`).** Hecho en el repo:
- `pick_asset.py`: soporta naming `64bit`/`64-bit` (trivy) y modo `--raw` para binarios sin archivar (hadolint). Verificado con JSON de release reales de ambas.
- `install-tools.sh`: nueva función `install_raw_bin`; alta de `trivy` (`install_go_bin`) y `hadolint` (`install_raw_bin`) en la Categoría A; verificación y aviso de BD de trivy.
- `check-tools.sh`: añadidas `trivy` y `hadolint`.
- **Desvío del plan (mejor diseño):** los wrappers NO van en `run-external.sh` (que exige URL + guardrail), sino en un nuevo **`run-static.sh <proyecto> <out-dir>`** — `trivy fs` (deps) + `hadolint` (iac), sin guardrail porque no hay host. Portable (sin `mapfile`).
- `agents/nemesis.md`: F2 ejecuta `run-static.sh`; §5 mapea trivy→`deps` y hadolint→`iac` (con dedupe).
- `catalog.md` y `docs/agents/nemesis.md`: documentadas ambas tools y la distinción estático/DAST.
- **Sin cambios** en `report/schema.md` ni `template.html` (áreas ya existentes).

**Verificado aquí:** `bash -n` de los scripts y `pick_asset.py` (selección correcta para trivy/hadolint en linux/windows).

**Pendiente (en tu máquina, no automatizable en el sandbox):** instalar realmente `trivy`+`hadolint` (`install-tools.sh`) y correr `run-static.sh` sobre un proyecto con `Dockerfile` y dependencias para confirmar que `raw/trivy.json` y `raw/hadolint.json` se generan y se mapean a `deps`/`iac`. Al validarlo, pasar el plan a `completado` y la spec a `implementada`.
