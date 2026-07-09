---
spec: nemesis-sca-iac
descripcion: Reforzar nemesis con dos escáneres reales - trivy (SCA de dependencias con BD de CVEs, area deps) y hadolint (lint de Dockerfile, area iac) - alimentando areas ya existentes del findings.json.
estado: aprobada
creado: 2026-07-09
actualizado: 2026-07-09
evaluacion: evaluation.md
plan: improvement-plan.md
---

# nemesis: añadir SCA real (trivy) y lint de IaC (hadolint)

> Evaluación: [`evaluation.md`](evaluation.md)
> Plan de implementación: [`improvement-plan.md`](improvement-plan.md)

## Contexto y objetivo

Hoy `nemesis` analiza dependencias e IaC de forma **estática/por patrones** (skill `cybersecurity`). Se quiere subir la precisión añadiendo dos herramientas OSS consolidadas, sin cambiar el esquema ni el informe:

- **trivy** — escaneo de dependencias contra una **base de datos real de CVEs** (`trivy fs`). Aporta al área **`deps`**.
- **hadolint** — linter de **Dockerfile** (buenas prácticas y seguridad de imágenes). Aporta al área **`iac`**.

Ambas áreas (`deps`, `iac`) **ya existen** en `report/schema.md`, así que la integración es **puramente aditiva**: nuevas fuentes que emiten findings en áreas existentes. No se toca el esquema ni `template.html`.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Herramienta SCA | **trivy** (`aquasecurity/trivy`) | Binario Go multiplataforma, BD de CVEs mantenida, salida JSON; encaja con `install_go_bin`. |
| Herramienta IaC/Docker | **hadolint** (`hadolint/hadolint`) | Binario único por OS/arch, JSON; estándar de facto para Dockerfile. |
| Naturaleza de la ejecución | **Estática (sistema de ficheros)**, no contra host | `trivy fs` y `hadolint` escanean el árbol del proyecto; **no** son DAST, así que **no** pasan por el guardrail (no hay target de red). |
| Cuándo se ejecutan | En la fase **SAST/normalización**, junto al análisis estático | Complementan a la skill; corren aunque no haya target local. |
| Mapeo de resultados | trivy → area `deps`; hadolint → area `iac` | Áreas existentes; cero cambios de esquema/informe. |
| Instalación | En `~/.claude/security-tools/`, con **permiso previo** | Mismo patrón que el resto del toolkit; opt-in. |
| BD de vulnerabilidades | trivy **descarga su BD** en el primer uso | Requiere red la primera vez; se avisa (igual que las plantillas de nuclei). |

## Arquitectura y componentes (puntos de integración)

- **`agent-kits/nemesis/tools/catalog.md`** — documentar las 2 nuevas tools.
- **`agent-kits/nemesis/tools/install-tools.sh`** (sección CATALOG) — `install_go_bin aquasecurity/trivy trivy` y la entrada de `hadolint` (binario de release; `pick_asset.py` resuelve el nombre por OS/arch).
- **`agent-kits/nemesis/tools/check-tools.sh`** — añadir `trivy` y `hadolint` a la lista comprobada (para el aviso "faltan").
- **`agent-kits/nemesis/tools/run-external.sh`** — wrappers: `trivy fs --format json --output $DIR/raw/trivy.json <proyecto>` y `hadolint --format json <Dockerfiles> > $DIR/raw/hadolint.json`. **Sin** guardrail (no hay URL objetivo).
- **`agents/nemesis.md`** — F2/F4: correr trivy/hadolint en el bloque estático y §5 (interpretación): calibrar y mapear su salida a `deps`/`iac`.
- **`report/schema.md`** y **`report/template.html`** — **sin cambios** (áreas existentes).

## Flujo

1. En la fase estática, tras (o junto a) la skill `cybersecurity`, si trivy/hadolint están instalados:
   - `trivy fs` sobre la raíz del proyecto → `raw/trivy.json`.
   - `hadolint` sobre los `Dockerfile*` detectados → `raw/hadolint.json`.
2. Normalización: convertir cada hallazgo a un finding del esquema:
   - trivy: `area=deps`, `source=sast`, severidad mapeada (CRITICAL/HIGH/MEDIUM/LOW), `cwe`/`id` del CVE, `location` = fichero de manifiesto + paquete\@versión.
   - hadolint: `area=iac`, `source=sast`, severidad por nivel (error/warning/info), `location` = `Dockerfile:línea`, regla `DLxxxx`.
3. Deduplicar contra hallazgos de la skill (misma dependencia/regla → 1 finding, sube confianza).
4. Si una tool no está instalada, declararlo en `tools_used` y marcar el área como cobertura parcial (regla existente).

## Alcance

- **Dentro:**
  - Alta de `trivy` y `hadolint` en catálogo, instalador y `check-tools`.
  - Wrappers en `run-external.sh` con salida JSON a `raw/`.
  - Normalización de sus salidas a `deps`/`iac` con calibración de severidad y dedupe.
  - Actualización de `agents/nemesis.md` (§4, §5) y de la doc (`catalog.md`, `docs/agents/nemesis.md`).
  - Prueba manual sobre un proyecto con `Dockerfile` y dependencias.
- **Fuera (siguientes specs):**
  - `trivy image` (escaneo de imágenes construidas) y `trivy config` (IaC completo).
  - Otros escáneres IaC (`tfsec`, `checkov`, `kube-linter`).
  - Generación de SBOM (`syft`) y cumplimiento de licencias.
  - Cambios de esquema para áreas nuevas (aquí no hacen falta).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Tool no instalada | Se declara en `tools_used`; el área queda como cobertura parcial. No se inventan hallazgos. |
| trivy sin BD (primer uso / sin red) | Se avisa y se reintenta la descarga; si no hay red, se omite trivy y se declara. |
| Proyecto sin Dockerfile | hadolint no corre; se anota "N/A" para IaC-Docker. |
| Salida JSON vacía | Cero findings de esa fuente; no es error. |

## Pruebas

- Sobre un proyecto de prueba con `composer.json`/`package.json` y un `Dockerfile`:
  - trivy produce `raw/trivy.json` y sus findings aparecen en el área `deps` del informe.
  - hadolint produce `raw/hadolint.json` y sus findings aparecen en el área `iac`.
  - Dedupe: una dependencia ya señalada por la skill no se duplica.
  - Sin las tools instaladas: el scan sigue funcionando y declara cobertura parcial.

## Referencias

- `aquasecurity/trivy` (escáner de vulnerabilidades; `trivy fs`, salida JSON).
- `hadolint/hadolint` (linter de Dockerfile; `--format json`, reglas `DLxxxx`).
- `agent-kits/nemesis/tools/` (catalog, install-tools, run-external, check-tools) y `report/schema.md` (áreas `deps`/`iac`).

## Decisiones confirmadas (revisión del usuario · 2026-07-09)

1. Empezar por **trivy + hadolint** por máximo valor y mínimo riesgo (alimentan áreas existentes). **Confirmado.**

## Supuestos

- (a) trivy descarga su BD de CVEs en el primer uso (requiere red esa vez).
- (b) Se mantiene el patrón de instala