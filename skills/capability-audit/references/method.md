# Evaluación semántica por pieza

Una auditoría incremental puede reutilizar una decisión solo si no cambian
cuerpo, recursos, callers, contrato del runtime ni fuentes técnicas relevantes.
El mtime por sí solo no demuestra equivalencia. En revisión completa registra
el alcance explícito y conserva el progreso en el ledger de la iniciativa.

Para cada pieza responde:

1. ¿Qué decisión cambia, quién la necesita y qué artefacto produce?
2. ¿El trigger distingue una intención vecina? Prueba petición literal,
   paráfrasis y negativo vecino con redirect; separa check estático de ejecución.
3. ¿Qué contenido único no ofrecen ya otra pieza, el fragmento shared o la
   documentación del proyecto? Nombra las secciones comparadas.
4. ¿Existen y se ejecutan sus recursos? Comprueba flags/APIs en la documentación
   oficial de sus versiones; un enlace presente no demuestra vigencia.
5. ¿Qué carga añade? Mide líneas/bytes y el modo de carga; tokens/latencia solo
   cuando exista medición compatible. Ausencia de logs no significa cero uso.
6. ¿Falla de forma comprensible en instalación parcial y en cada runtime?

| Campo | Evidencia requerida |
|---|---|
| Pieza/alcance | Ruta real y hash o revisión leída |
| Decisión | Conservar/ampliar/actualizar/consolidar/retirar |
| Motivo | Sección concreta, defecto o criterio que cambia el trabajo |
| Cobertura existente | Pieza y contrato comprobados; sin equivalencias por nombre |
| Delta | Contenido que se conserva/mueve/añade; destino propio |
| Validación | Comando y resultado real; «no ejecutado» cuando corresponda |
| Impacto | Dependencias, activación, docs, manifiestos y exports |

Consolidar exige comprobar que todo criterio útil tiene destino, retirar callers
sustituidos y validar las altas/bajas del bundle. No mantengas alias vacíos para
simular limpieza. Conserva contratos de lectura históricos cuando tengan usuarios
reales y documenta su alcance; no los elimines solo por antigüedad.

## Salida «elevar a convención»

Cuando la misma regla aparece repetida dentro de varias piezas, la auditoría
puede proponer elevarla a convención. Propónlo solo si cumple los tres filtros:

| Filtro | Se comprueba con |
|---|---|
| Aparece en 2+ piezas | Rutas y líneas de cada aparición, no «se repite mucho» |
| Se escribe como «haz X» / «no hagas Y» | La frase candidata, accionable y verificable |
| Tiene un riesgo concreto si se ignora | El fallo que provoca; si ya ocurrió, su evidencia |

Antes, busca si ya está cubierta con otras palabras en `docs/CONVENTIONS.md`,
un ADR o un fragmento de `agent-kits/shared/`; si lo está, el delta es enlazar
esa fuente desde las piezas, no escribirla otra vez.

Forma de un motivo suficiente: «`<pieza-1>:<línea>` y `<pieza-2>:<línea>`
repiten "no ataques hosts que no sean locales o privados"; ignorarla lanza
tráfico activo contra sistemas de terceros; ni CONVENTIONS ni ningún ADR la
recogen». Motivo insuficiente: «varias skills hablan de seguridad». Para retirar, el motivo nombra el defecto
y quién lo cubre; para consolidar, el destino y el contenido que se mueve.

La auditoría solo propone. La convención la escribe su dueño en un cambio
revisado; si es conocimiento del proyecto, la aprueba `knowledge-curator`.
