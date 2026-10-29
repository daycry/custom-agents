# Elegir entre kit, skill, agente y comando

Lee esta referencia en el Paso 0 si dudas del tipo de pieza o de si debes extraerla.

Duda entre kit privado y skill → **empieza privado**; promociona a `skills/` el día que un
segundo agente lo necesite (regla 3). **Criterio de extracción** a pieza compartida: al menos **2 de
estas 5 señales** — (1) una segunda pieza lo necesita, (2) el mismo texto o procedimiento ya está copiado
en 2+ piezas, (3) tiene contrato estable (entradas, salidas, exit codes), (4) el patrón se repite en ≥ 2
iniciativas (`/retro`, `journal.py candidatas`), (5) no tenerlo compartido ya costó un ciclo (gotcha o
lección) — **y** sin solape de rol con un dueño existente (ADR-011). Un arnés local no se declara
reutilizable hasta que otra persona pueda re-ejecutar su eval o su `Verificación` y obtener lo mismo.
Duda entre agente y comando → si decide *puertas* y
*orquesta* a otros, es comando; si *hace* un trabajo con criterio propio, es agente.
Duda entre **skill y agente nuevo** → es agente SOLO si aporta un rol que **decide y escribe un
artefacto propio** que hoy nadie decide; una **capacidad** que 2+ agentes invocan es skill, aunque
suene a oficio («tester», «revisor de rendimiento»). Síntoma de haber elegido mal: repartir la misma
responsabilidad entre dos piezas («este escribe el test, aquel dice si vale») — `LES-013`, `ADR-011`.
