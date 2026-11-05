# Revisi?n A/B del payload npm

Intento 1, diff `6e649bd..d2d4906`, ocho ficheros. Revisores nativos independientes y con contexto fresco. Clon p?blico limpio, sin preferencias, credenciales ni corpus privados. Scope-check: ocho archivos en alcance, cero fuera y cero excluidos. Selector C/D false: no aplican esas lentes al incremento.

| Criterio | A | B | Evidencia |
|---|---|---|---|
| Proyecci?n desde el tgz | ? | ? | Exportador realmente invocado por el instalador; regresi?n NPM-01 desde artefacto extra?do |
| PDF/manifiestos/fuentes | ? | ? | Allowlist expl?cita y hashes comprobados dentro del paquete |
| Exclusiones y extracci?n | ? | ? | Sin enlaces/rutas externas, configuraci?n local ni corpus privado |
| TDD, alcance y due?os | ? | ? | RED2failed1passed; GREEN3passed, sin l?gica runtime modificada |
| Gu?a ES/EN | ? | ? | Pack, publicaci?n e integridad separados de autenticaci?n y dry-run |
| Puertas y generados | ? | ? | Sin reglas relajadas; interop no cambia y su --check tiene evidencia |
| T-02 integraci?n/CI/publicaci?n | Pendiente de cierre | Sin afirmaci?n falsa | Tarea en-revision; E401 no se presenta como publicaci?n |

Ambos revisores leyeron el diff completo y ejecutaron independientemente `pytest tests/test_npm_payload.py`: 3 passed (77,94 s y 67,73 s, Windows). Capacidades seleccionadas: delivery-practices, sin stacks adicionales. Sin hallazgos, deuda o rebatidos. No se ejecut? inferencia, conexi?n a Ollama ni instalaci?n en perfiles reales.
