# Verificación del payload npm

2026-11-05. Base pública v3.2.0 / `6e649bd`. Corrección limitada a la allowlist y pruebas/documentación; no cambia lógica de instalación.

## Reproducción y regresiones

`npm pack --json --ignore-scripts` de 3.2.0 produce un tgz de 651 entradas. Su checkout contiene el exportador y los nuevos PDF, pero la allowlist los omite.

- NPM-01: ejecutar `cargarModelosNativos` desde el tgz extraído con configuración válida de un reviewer OpenCode falla porque no existe `scripts/export-interop.py`. No se inicia Ollama ni se ejecuta inferencia.
- NPM-02: los dos PDF enlazados desde README y sus dos manifiestos faltan en el tgz.
- La exclusión de `.claude/`, `.npmrc` y `docs/knowledge/` se mantiene.

RED observado con `pytest tests/test_npm_payload.py -q --tb=short`: 2 failed, 1 passed. Se añaden a la allowlist únicamente el exportador y los cuatro archivos documentales. GREEN: 3 passed. El test documental comprueba también hashes PDF y fuentes LF normalizadas dentro del paquete.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
|---|---|
| Tests de payload, ediciones y roadmap | 74 passed |
| `scripts/lint_plugin.py` | 0 errores, 16 avisos previos |
| `evals/check.py` | 60 piezas, 229 casos, 0 errores |
| `scripts/export-interop.py --check` | 92 ficheros al día |
| `scripts/check-handbook.py` | Manual operativo y fuentes/diagramas coinciden |

El pack del test es offline, no ejecuta scripts de ciclo npm y se extrae bajo una carpeta temporal propiedad del test. Rechaza enlaces y rutas fuera de esa carpeta. La proyección usa HOME/USERPROFILE y configuración de proveedores temporales; no instala perfiles reales ni publica contenido.

## Publicación

Fuentes oficiales consultadas: [npm publish](https://docs.npmjs.com/cli/v11/commands/npm-publish/) y [paquetes públicos con scope](https://docs.npmjs.com/creating-and-publishing-scoped-public-packages/). INSTALL ES/EN distingue creación del artefacto, publicación, autenticación y verificación del registro.

La consulta pública inicial de npm anuncia 1.20.1 como latest. `npm whoami --registry=https://registry.npmjs.org` devuelve E401; se solicitó renovar autenticación al usuario. No se han leído credenciales ni se ha declarado publicado el paquete. La publicación real requiere comprobar cuenta, versión, dist-tag e integridad del tgz que finalmente se envíe.
