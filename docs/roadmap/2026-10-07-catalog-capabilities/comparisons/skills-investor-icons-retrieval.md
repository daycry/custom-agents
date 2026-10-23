# Materiales para inversores, iconos iOS y recuperación iterativa — S137–S140

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **17.829 bytes/559 líneas** y los dos scripts de S139
(15.469 bytes/493 líneas).
[investor-icons-retrieval-reading-evidence.json](investor-icons-retrieval-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S137–S138 — Materiales y contacto con inversores

`2.735 + 2.655 bytes`. Presentaciones, memorandos, modelos financieros y
solicitudes de aceleradoras con **una sola fuente de verdad** para cifras, equipo
y ronda; correos en frío, presentaciones cálidas y seguimientos con prohibiciones
de relleno y una petición concreta por mensaje.

**Comparación.** Dominio de negocio sin rol en el ciclo, igual que S092–S093.
**Fuera del bundle**; persona de proyecto si un consumidor la necesita. La regla
de oro (si dos documentos dan cifras distintas, parar y resolver antes de
redactar) es la misma disciplina que el ledger canónico frente a sus espejos y
que `/roadmap-brief`, que deriva cifras del ledger en vez de copiarlas. S138
aporta un matiz reutilizable: si falta contexto para personalizar, **declarar
que el borrador está incompleto** en vez de presentarlo como terminado, igual
que `NEEDS_CONTEXT` del brief de subagente.

## S139 — Iconos iOS desde SF Symbols o Iconify

`5.653 bytes/158 líneas` más `iconify_gen.sh` (7.098 bytes) y
`generate_icons.swift` (8.371 bytes). Genera conjuntos de imágenes 1x/2x/3x con
su `Contents.json` para catálogos de Xcode.

**Comparación.** Sin equivalente ni rol propio: depende de macOS (`sips`,
AppKit) y de una API externa. **Fuera del bundle.** Los scripts son correctos en
lo básico (`set -euo pipefail`, tiempos máximos en `curl`, validación de
opciones), pero conviene anotar dos defectos si alguien lo reutiliza: un fallo
de `sips` solo emite un aviso y el script sigue, de modo que puede quedar un
conjunto con PNG ausentes y un `Contents.json` que los cita; y el identificador
del icono y el nombre del recurso se interpolan sin validar en la URL y en la
ruta de salida (`../` en el nombre escribe fuera del directorio). La regla
«comprobar el estilo de los iconos existentes antes de generar» coincide con
`frontend-quality` (dirección visual, S107).

## S140 — Recuperación iterativa de contexto

`6.786 bytes/212 líneas`. Bucle de cuatro fases (despachar una búsqueda amplia,
puntuar relevancia de 0 a 1, refinar términos y exclusiones, repetir hasta tres
veces) para que un subagente reúna el contexto que no sabe pedir de antemano.

**Comparación.** El plugin resuelve el mismo problema por el otro extremo: el
orquestador **construye el brief** con `task-brief.py` (tarea, criterios,
verificación, ficheros citados, conocimiento por área) y el subagente devuelve
`NEEDS_CONTEXT: <qué>` cuando le falta algo, con un único re-despacho
(`/dev-cycle`, subagentes). `knowledge-find.py` hace la recuperación de memoria
por contexto e iniciativa. Lo que aporta la pieza:

| Idea | Encaje |
|---|---|
| **Aprender la terminología del repo** en la primera pasada (buscar «rate limit» y descubrir que el código dice «throttle») | Paso previo del implementer cuando `NEEDS_CONTEXT` cite un concepto y no un fichero |
| Registrar explícitamente **qué falta** antes de refinar | Ya existe: `NEEDS_CONTEXT` exige decir exactamente qué |
| Tope de 3 ciclos y parar en «suficiente» | Coherente con los bucles acotados a 3 del ciclo |

Correcciones: la puntuación 0–1 de relevancia no es reproducible (la daría el
modelo) y no debe convertirse en veredicto; el ejemplo 1 se da por suficiente
con dos ficheros relevantes cuando el propio bucle exige tres; y el umbral 0,7
cae dentro de la franja «media» (0,5–0,7). **Destino:** una línea en el brief de
`task-brief.py` («si no encuentras el término, busca sinónimos del dominio en el
repo antes de pedir contexto»). Sin skill nueva.
