# Registro de aprendizaje, dominio sanitario e importación de flujos — S119–S124

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **39.849 bytes/977 líneas**, sin recursos locales.
[growthlog-healthcare-imports-reading-evidence.json](growthlog-healthcare-imports-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S119 — Registro de aprendizaje

`7.034 bytes/128 líneas`. Entradas que extraen el patrón (causa raíz, regla
transferible, señal reconocible) en vez de narrar el evento; fusionar duplicados
antes de escribir; plantilla de 4-8 frases.

**Comparación.** Es exactamente el contrato de la memoria técnica del plugin:
`knowledge-write.md` (umbral: gotcha solo si costó ≥ 1 ciclo de depuración),
plantilla de GOT/LES (síntoma, causa raíz, qué hacer en su lugar, evidencia),
el curador como puerta y el journal como memoria episódica separada. Los cinco
gotchas curados hoy (GOT-020…024) siguen ese formato. Aporta dos matices útiles:
la **señal reconocible** («la próxima vez que veas X») y buscar duplicados por
causa raíz antes de proponer. La puerta «¿se modificó hoy el fichero de
aprendizaje?» por fecha que menciona la pieza no prueba contenido y no se adopta.
**Destino:** añadir «señal reconocible» y la búsqueda de duplicados a la plantilla
de `knowledge-write.md`.

## S120–S123 — Dominio sanitario (decisión clínica, historia clínica, evaluación, datos de salud)

`9.461 + 6.746 + 7.849 + 5.753 bytes`. Motor de apoyo a la decisión clínica como
funciones puras (interacciones, dosis, escala NEWS2), flujo de encuentro clínico,
puerta de despliegue por categorías con umbrales y patrones de protección de datos
de salud (clasificación, RLS, auditoría, vectores de fuga).

**Comparación.** Dominio regulado sin rol en el plugin; si un consumidor lo
necesita, va como persona y especialidad de proyecto con fuentes clínicas. Ideas
generales que ya rigen o refuerzan piezas propias:

| Idea | Pieza propia |
|---|---|
| Ante un dato requerido ausente, bloquear en vez de dejar pasar (dosis por peso sin peso) | «Fail-closed» de knowledge-services y guardrails |
| Auditoría solo de inserción e identificadores opacos en logs y URL | backend-practices (no filtrar existencia) y redact |
| Registro firmado: solo adendas, nunca edición | Historial del ledger y `execution-history.md` (nada se reescribe) |
| Alertas críticas no descartables | frontend-quality |

Correcciones relevantes para quien lo reutilice: `validateDose` devuelve
«válido» cuando no hay reglas para el fármaco (un motor de seguridad debería
avisar); el umbral del 95 % que permite desplegar con flujos clínicos fallando
contradice el «cero falsos negativos» de la propia familia; el porcentaje se
calcula con `bc` y `jq`, que pueden no existir; y el registro de auditoría guarda
el antes y el después completos, que pueden contener los propios datos de salud.
**Fuera del bundle.**

## S124 — Importar flujos locales a piezas públicas

`3.006 bytes/89 líneas`. Convertir un flujo de un entorno privado en una pieza
publicable: rutas relativas, roles en vez de nombres, credenciales solo por
proveedor, escaneo de secretos y rutas locales antes del PR.

**Comparación.** Coincide con la regla del repo «datos personales fuera de git»
(rutas relativas, sin usuario, correos ni empresa en nada versionado) y con
`plugin-dev` para crear piezas. La lista de comprobación (rutas absolutas,
`~/.<herramienta>`, tokens, teléfonos, nombres de cliente, datos de salud o
finanzas, logs con salida de sistemas privados) es más completa que la nuestra.
**Destino:** checklist de saneado en `plugin-dev` antes de proponer una pieza,
reutilizando el linter de citas y `redact.py`.
