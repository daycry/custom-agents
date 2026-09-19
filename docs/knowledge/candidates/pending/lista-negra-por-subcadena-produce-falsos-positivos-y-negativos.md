---
category: LESSON
evidencia: multiple_validated_cases
fuentes:
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (gap #41, curator-gate.py:122)
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (gap #64, curator-gate.py:177-181)
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (gap #170, hooks/session-context.sh)
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (gap #178, regresión del fix de #170)
tags:
  - agente:knowledge-curator
  - agente:knowledge-services
  - area:matching-de-texto
---

## Una red de seguridad que casa por subcadena sobre texto completo produce falsos positivos y falsos negativos

- **Síntoma:** dos guardas distintas del plugin que comparan un término prohibido contra texto
  libre fallaron por el mismo motivo, en momentos distintos de la misma iniciativa:
  - `curator-gate.py` (lista negra de `knowledge-services`, gap #41): casaba por subcadena en
    minúsculas sin frontera de palabra, así que `TODOs` → `todos` bloqueaba cualquier candidato
    que contuviera «todos» o «métodos» (12 de 45 entradas reales de `docs/knowledge/` habrían
    sido rechazadas). Además (gap #64) no plegaba acentos: «conversación cruda» nunca disparaba
    el término «conversacion cruda».
  - El escaneo de hooks de `knowledge-services` (T-10, gap #170): un hook que solo *documentaba*
    en un comentario «no hace red (ni curl ni urllib)» disparaba la prohibición de red por
    coincidencia literal sobre la línea completa, sin distinguir código de comentario.
- **Causa raíz:** comparar un término contra una cadena completa (sin frontera de palabra, sin
  normalizar acentos, sin separar código de comentarios/strings) confunde la INTENCIÓN del texto
  (una instrucción real vs. una mención en prosa) con la mera presencia de la subcadena.
- **Qué hacer en su lugar:** exigir frontera de palabra con lookarounds (`(?<!\w)`/`(?!\w)`),
  plegar acentos con NFD antes de comparar (`unicodedata`, descartando marcas combinantes), y si
  el texto es código, recortar el comentario respetando comillas antes de buscar el término (un
  corte ingenuo en el primer `#`/`//` reintroduce falsos negativos cuando el término prohibido
  aparece DESPUÉS de una almohadilla dentro de una cadena — regresión real en gap #178).
- **Evidencia:** `test_denylist_todo_dos_puntos_dispara_pero_no_la_palabra_todos`,
  `test_denylist_plegado_de_acentos_dispara_sobre_prosa_real`,
  `test_falso_positivo_comentario_documentando_la_prohibicion_no_rompe_la_suite`,
  `test_regresion_gap178_termino_tras_comilla_con_almohadilla_se_detecta` (todos en
  `tests/test_knowledge_services.py`), en verde tras los fixes T-04-fix1, T-10-fix2 y T-10-fix3.
