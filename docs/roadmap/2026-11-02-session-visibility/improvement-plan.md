---
plan: session-visibility
estado: en-revision
creado: 2026-11-02
---

# Corrección de visibilidad del dashboard

T-01 reutiliza JsonPeer y el ejecutable nativo de confianza. Usa initialize y
thread/list con cwd, useStateDbOnly y filtros de origen. Máximo cuatro páginas de
50, cuatro segundos por RPC y doce segundos acumulados; el cierre del proceso
propio tiene su presupuesto independiente. No se consulta historia ni se inicia
inferencia. El servidor retiene el ownership para cerrar consultas al detenerse.
Un pool separado evita que estas consultas ocupen todos los lectores de planes.

T-02 presenta el inventario externo separado de sesiones controlables, con búsqueda,
estado y fuente. La captura permanece opt-in por proyecto; nunca se activa por
visitar el dashboard. En este proyecto el usuario pidió ver la actividad y se
habilitó su opción local sin modificar settings personales ni cachés globales.

La fase de revisión usa lentes frescas A/B/C según selección determinista; después
se ejecutan regresiones Python, navegador, lint, interop y cobertura del cambio.
No se reabre la iniciativa cerrada de v3.0.0 ni se ejecuta inferencia Ollama.
