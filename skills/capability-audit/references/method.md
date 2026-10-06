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
