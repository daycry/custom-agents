# Documentación, consulta de docs, E2E y red doméstica — A019–A021, A033

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **18.526 bytes/416 líneas**. [agents-docs-e2e-homelab-reading-evidence.json](agents-docs-e2e-homelab-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

**Común a las cuatro.** Bloque «Prompt Defense Baseline» idéntico (líneas 8-15). Pide no
emitir código salvo que la tarea lo requiera, pero A020 y A021 entregan código como salida
principal. **Sin destino.**

## A019 — doc-updater

`4.376 bytes/116 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: haiku. Genera
codemaps (`docs/CODEMAPS/*`) y actualiza READMEs y guías a partir del código, con la API del
compilador TypeScript, madge y jsdoc2md. Se ofrece a usarse de forma proactiva.

**Comparación.** El dueño es `documenter`, que deriva la documentación del repositorio con
evidencia (`agent-kits/documenter/taxonomy.md:54-56`). Es idempotente y respeta el contenido
escrito a mano (`agents/documenter.md:161-170`), mantiene `docs/README.md` y `RAG-INDEX.md`
con su fecha y documenta **una vez**, al cerrar el ciclo con qa en verde (`:54-60`). Los
codemaps equivalen a sus páginas por unidad y al índice para IA. Diferencias:

| Línea | A019 | Plugin |
|---|---|---|
| 3 | «Use PROACTIVELY» | Una sola pasada al cierre: documentar a mitad refleja un estado intermedio (`documenter.md:56-59`) |
| 93 | «Generate from code, don't manually write» | Respeta lo escrito a mano; amplía, no aplasta (`:166`) |
| 32-34 | `npx tsx scripts/codemaps/generate.ts`, `npx madge`, `npx jsdoc2md` | Supone un script que no existe en un repo cualquiera y ejecuta paquetes `npx` sin versión fijada. Solo TypeScript |
| 89, 102-104 | «Verify files exist, links work, examples run» | `documenter` exige evidencia y marca `⚠️ verificar` (`:207`), pero **no comprueba** que las rutas y los enlaces relativos citados existan |

**Destino:** una línea en el DoD de `agents/documenter.md` para comprobar que existen las
rutas y los enlaces relativos citados, sin ejecutar ejemplos (propuesta P2 en el informe).
El resto ya está cubierto.

## A020 — docs-lookup

`4.566 bytes/77 líneas` · tools: Read, Grep, `mcp__context7__resolve-library-id`,
`mcp__context7__query-docs` · model: haiku. Responde dudas de librerías y APIs con
documentación actual de Context7, con tres llamadas como máximo, y trata lo recibido como no
confiable (línea 19).

**Comparación.** Context7 ya es un canal de `research-first`, con la versión tomada del
lockfile, la consulta redactada antes de enviarla y una doble comprobación con la doc
oficial (`skills/research-first/SKILL.md:36`, D-040, integrado). A020 solo usa la versión si el
usuario la nombra (línea 38) y, sin Context7, responde «de memoria» con una nota (línea 53).
En `research-first` la vigencia se declara y no se presume. Sus `tools` son mínimas y
correctas, y la regla de contenido no confiable coincide con la del plugin.

**Destino:** **Sin destino.** Ya está integrado en `research-first`.

## A021 — e2e-runner

`5.079 bytes/116 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: sonnet. Crea,
mantiene y ejecuta E2E con Agent Browser (Playwright como respaldo), pone en cuarentena los
flaky y sube artefactos a CI.

**Comparación.** El E2E tiene dueño: `qa`, con veredicto de `qa-gate.py`. El método de
specs estables ya está integrado en `agent-kits/qa/references/e2e-evidence.md` (D-108).
Diferencias y defectos:

| Línea | A021 | Plugin |
|---|---|---|
| 36-39 | `npm install -g agent-browser` y `agent-browser open https://example.com` | Instalación solo con permiso y fuera del repo (`agents/qa.md:51`, `:106`). Guardrail local/privado (`:44-49`) |
| 69, 81 | `data-testid` por encima de todo | Rol y nombre accesible primero, `getByTestId` el cuarto (`e2e-evidence.md:8-17`) |
| 100 | Contra las animaciones, «wait for `networkidle`» | Prohibido (`e2e-evidence.md:33-44`). Contradice su propia línea 86 («wait for conditions, not time») |
| 76, 90-94 | Cuarentena con `test.fixme()`/`test.skip()` | Solo con incidencia, dueño y fecha, y el criterio pasa a `M-xx` (`e2e-evidence.md:63-75`) |
| 104-107 | Aprobado con > 95 % y flaky < 5 % | `qa-gate.py`: 0 fallos y 0 flaky sin justificar (`agents/qa.md:84-86`) |
| 77, 108 | Sube artefactos a CI | `testing/` es solo local (`agents/qa.md:96`) |

Lo único que no está en el plugin es ejecutar cada spec nuevo varias veces antes de darlo
por estable (línea 75; `--repeat-each`, línea 97). El runner del kit reintenta dos veces
para *clasificar*, no para *descubrir* inestabilidad.

**Destino:** **Sin destino nuevo**: ya está integrado en `qa` (D-108). Queda una línea
opcional P3 en `e2e-evidence.md`, «Flaky a la vista» (propuesta en el informe).

## A033 — homelab-architect

`4.505 bytes/107 líneas` · tools: Read, Grep · model: sonnet. Diseña redes domésticas y de
laboratorio a partir del inventario, los objetivos y la experiencia del operador: fases
reversibles y vuelta atrás antes de cada cambio.

**Comparación.** Es el mismo dominio que S127–S130, ya declaradas **Fuera del bundle**
(`skills-hexagonal-hipaa-homelab.md:41-53`). El método es ejemplar y coincide con el del
plugin: primero solo lectura, no dar configuración sin plataforma, acceso de consola ni plan
de reversión confirmados (líneas 25-27), y no exponer interfaces de gestión (línea 53). Es la
misma disciplina que `/doctor` y que el guardrail de `nemesis`. Tiene los permisos más
estrechos del rango (Read, Grep), adecuados para una pieza que solo planifica. Remite a cuatro
skills de red de la fuente (líneas 31-36), que siguen aparcadas o fuera del bundle
(`skills-network-netmiko-bgp.md`).

**Destino:** **Fuera del bundle**. Si un consumidor gestiona redes, su cauce es una persona
o una extensión de proyecto.
