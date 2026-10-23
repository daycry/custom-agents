---
evaluacion: project-extensions
estado: completado
creado: 2026-10-06
spec: spec.md
plan: improvement-plan.md
---

# Evaluación técnica

Go por autorización de integración por fases y decisiones técnicas delegadas.
No se solicitó presupuesto económico. Es una ampliación transversal de parsing,
privacidad, selección y UI: no conviene resolverla con un escaneo indiscriminado
de HOME ni con importación de plugins del consumidor.

Se reutilizan el redactor central, guard CLOUD, límites de brief, panel local,
selector nativo y contrato O1 del registro. No existe todavía un descubridor
multi-runtime ni registry writer; no se afirma reutilización de código inexistente.
El inventario se calcula por lectura de raíces explícitas; no persiste config.
Riesgos: diversidad de formatos, duplicados, secreto en metadata, rutas enlazadas,
MCP deshabilitados, privilegios reales no deducibles y coste de escanear corpus.
Controles: adaptadores, allowlists de salida, guard de lectura acotada, diagnóstico
por fuente, scopes separados y selección por identidad; ninguna ejecución de red.
