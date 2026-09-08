---
id: GOT-001
tipo: gotcha
area: Backend / exportación CSV
estado: aceptada (validada por usuario, 2026-01-01)
fecha: 2026-01-01
fuente: docs/roadmap/2025-12-01-informes-v1/tasks.md (bug reportado por el usuario)
---

## Una comilla dentro de un campo CSV se escapa DOBLÁNDOLA, no con barra

- **Síntoma:** el CSV de informes abría en la hoja de cálculo con columnas desplazadas cuando un
  título traía comillas (`Informe "Q3"`).
- **Causa:** el escapado usaba `\"` (estilo JSON); RFC 4180 exige `""` dentro de un campo entre comillas.
- **Qué hacer:** todo campo con coma, comilla o salto de línea va entre comillas y cada `"` interna se
  dobla: `"Informe ""Q3"""`. Usa `csv.writer` de la stdlib en vez de concatenar: ya lo hace bien.
