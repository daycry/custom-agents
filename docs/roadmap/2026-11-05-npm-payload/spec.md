---
spec: npm-payload
estado: implementada
creado: 2026-11-05
---

# Completar el artefacto npm antes de publicar

El usuario solicita publicar el paquete que permite usar `npx @daycry/custom-agents`. npm sigue en 1.20.1; la release GitHub es 3.2.0. La consulta inicial de autenticación devolvió E401 y se solicitó al usuario renovarla; no se leen ni guardan credenciales.

La prueba del `.tgz` real de 3.2.0 detecta dos omisiones: `scripts/export-interop.py`, ejecutado por la opción `--models-config`, y los dos nuevos PDF con sus manifiestos, enlazados desde el README. El checkout tiene esos archivos, pero `package.json.files` no los distribuye.

## Alcance y aceptación

- Incluir el exportador requerido y las cuatro piezas documentales mediante allowlist explícita.
- Comprobar una proyección real de modelo desde el `.tgz` extraído, sin inferencia LLM, servidor Ollama ni instalación en perfiles reales.
- Comprobar que los PDF enlazados y sus manifiestos existen en el paquete.
- Conservar exclusión de configuración local, `.npmrc` y corpus privado.
- Documentar el paso de publicación npm en INSTALL ES/EN y verificar el artefacto con TDD, revisión y CI.

No se modifican contratos del instalador ni se amplía el catálogo. La corrección se entrega como 3.2.1, sin alterar el tag publicado 3.2.0. La publicación en npm es una operación posterior autorizada por el usuario, condicionada a autenticación válida; no se declara realizada mientras falte.
