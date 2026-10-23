# Copia, verificación y empaquetado para publicar en abierto — A044–A046

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres definiciones completas: **22.478 bytes/662 líneas**. [agents-opensource-release-reading-evidence.json](agents-opensource-release-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Son los tres agentes de la skill S193 (`skills-orch-opensource-approval.md`), ya
decidida: **sin destino como flujo**, porque publicar un proyecto no es un rol
del ciclo. Sus piezas sí tienen dueño: `cybersecurity` busca secretos,
`agent-kits/shared/redact.py` redacta, `scripts/export-skills.py` solo vacía una
carpeta que lleve su marca y `delivery-practices` dice que «preparar una entrega
no autoriza publicarla» (`SKILL.md:15`). Ya está integrado lo que faltaba: un
secreto se rota antes de retirarse (D-060, `cybersecurity/references/agent-prompts.md:203-210`)
y la evidencia se enmascara (`agent-prompts.md:198-201`). Los cuerpos de los
agentes añaden los defectos de abajo.

## A044 — opensource-forker

`7.385 bytes/207 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: haiku.
Copia el proyecto a staging sin secretos ni ficheros generados, cambia las
referencias internas por marcadores, genera `.env.example`, crea un historial
nuevo de un commit y escribe `FORK_REPORT.md`.

**Comparación.** No hay rol propio que copie proyectos para publicarlos. El
historial nuevo con `git init` (l.143-153) es coherente; el defecto de S193
(excluir `.git` y luego «limpiar» un historial inexistente) era de la skill.

| Punto | Problema |
|---|---|
| «Extract values to `.env.example` rather than deleting them» (l.56) | Leído al pie de la letra, copia el valor real del secreto al fichero de ejemplo que se publica; la plantilla (l.135-140) usa marcadores, pero la regla no lo dice: nombres, nunca valores |
| `rsync --exclude='.env*'` (l.49) | También excluye un `.env.example` existente, que luego se regenera desde cero: se pierde la documentación de configuración |
| IPs privadas → `your-server-ip` (l.115) con «Never remove functionality» (l.203) | Cambiar subredes internas (redes de Docker, `10.x`) rompe configuraciones que no eran secretas |
| Sin rotar lo encontrado | Lo cubre D-060 en `cybersecurity` |
| `haiku` con Write, Edit y Bash en el paso que maneja secretos | Es el modelo más barato para la tarea más sensible; el tiering propio asigna `opus`/`high` al trabajo de juicio (ADR-009) |

**Destino:** **Fuera del bundle** (S193).

## A046 — opensource-sanitizer

`7.153 bytes/197 líneas` · tools: Read, Grep, Glob, Bash · model: sonnet.
Auditor independiente de la copia: busca secretos, PII, referencias internas y
ficheros peligrosos, comprueba que `.env.example` está completo y revisa el
historial. Veredicto PASS/FAIL/PASS WITH WARNINGS.

**Comparación.** La búsqueda de secretos es el agente de secretos de
`cybersecurity`, con redacción y rotación ya escritas. La idea del auditor que
no se fía del constructor es la misma que la del contexto fresco de `reviewer`.

| Punto | Problema |
|---|---|
| `git log -p \| grep -iE '(password\|secret\|api.?key\|token)' \| head -20` (l.136) | Imprime líneas completas con sus valores, contra su propia regla «Never display full secret values» (l.191) |
| «Read-only — you never modify files» (l.27) y genera `SANITIZATION_REPORT.md` en el proyecto (l.141) sin Write | Solo puede escribirlo por Bash y lo deja dentro del árbol que se va a publicar |
| PII solo para gmail, yahoo, hotmail… (l.79) | Un correo personal con dominio corporativo pasa |
| IPs privadas CRITICAL (l.84) | El forker las cambió por un marcador; una IP privada documentada como ejemplo queda en «fallo» si no está en `.env.example` |

**Destino:** **Fuera del bundle** (S193). La redacción de evidencias ya está en `cybersecurity`.

## A045 — opensource-packager

`7.940 bytes/258 líneas` · tools: Read, Write, Edit, Bash, Grep, Glob · model: haiku.
Genera `CLAUDE.md`, `setup.sh`, `README.md`, `LICENSE`, `CONTRIBUTING.md` y
plantillas de issues para un proyecto ya saneado.

**Comparación.** `documenter` escribe la documentación del producto solo bajo
`docs/` (`agents/documenter.md:17,50`); no escribe ficheros de la raíz, scripts
de arranque ni licencias. El `CONTRIBUTING.md` y las plantillas de este repo son
del propio plugin, no una capacidad para consumidores. La regla «verifica que
cada comando de `CLAUDE.md` existe» (l.253-257) es buena y coincide con la
disciplina de rutas reales del plugin. **Defectos:** elige por su cuenta al
titular de la licencia («Contributors» por defecto, l.225), que es una decisión
legal; y como `haiku` escribe `setup.sh` con `set -euo pipefail` y lo hace
ejecutable sin revisión humana.

**Destino:** **Fuera del bundle** (S193).
