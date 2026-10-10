# Cómo llegan los comandos al cliente nativo

Contrato del Bloque22, dentro de T-08/T-09/T-11/T-14/T-15.
La fuente de cada workflow sigue en `commands/`; las skills de contenido
aplazadas no se amplían. El exporter genera únicamente su transporte Codex.

## Qué debe conservar la proyección

El manifiesto mantiene `./skills/` y añade una segunda raíz generada,
`./interop/codex/command-skills/`, mediante el formato de lista documentado.
La aceptación de esa lista exige comprobarla con el Codex instalado; una
fixture de repositorio con `pluginId: null` no prueba la carga del plugin.

Cada comando tiene un adaptador `custom-agents-<nombre>`. El prefijo uniforme
evita que `confluence-pull`, existente como comando y skill, se sombree.
El mapa `SKILL.md` tiene como máximo200 líneas y exige leer íntegramente
`references/command.md` antes de seguir el workflow. La referencia generada
conserva cuerpo, puertas y preámbulo de runtime, incluidos los dólares literales.
`agents/openai.yaml` declara `allow_implicit_invocation: false`.

Los argumentos proceden del mensaje que invoca el adaptador; no son variables
de shell ni placeholders del antiguo compositor de prompts. El adaptador
no crea estados, aprobaciones, roles o gates distintos. Duplicados con nombres
canónicos, fuentes ausentes y proyecciones desactualizadas deben fallar de
forma explícita. La generación mantiene orden fijo y no añade fechas.

## Qué cambia en instalación y limpieza

El plan del instalador copia la segunda raíz dentro del bundle antes de
registrarlo. Una instalación de proyecto mantiene los comandos en su plugin
y no escribe prompts personales fuera del proyecto.

La vía de prompts obsoleta deja de ser el transporte generado predeterminado.
Los exports propios retirados se reconocen por nombre y cabecera exactos;
los archivos personales, enlaces y contenido ajeno se conservan. El instalador
no borra archivos globales anteriores por adivinar su procedencia. Libera
los registros de prompts externos al bundle sin leer ni borrar sus bytes,
también si `CODEX_HOME` cambió desde la instalación anterior. Los archivos
internos del bundle conservan su propiedad y desinstalación ordinaria.
La desinstalación directa de un manifiesto antiguo aplica la misma liberación;
no exige una actualización previa ni cuenta esos prompts como borrables en dry-run.

La documentación ES/EN debe mostrar la invocación nativa
`$custom-agents:custom-agents-dev-cycle`, la ubicación del bundle y las limitaciones medidas.
No anunciar el alias singular `/prompt:`. Claude Code y OpenCode conservan
sus transportes nativos y la misma fuente del workflow.

## Qué pruebas cuentan y cuáles siguen pendientes

1. RED/GREEN de proyección, preservación literal, nombres, raíces y retirada
   precisa; regresiones pertinentes del exporter y del plan de instalación.
2. Cliente instalado: ambos grupos de skills descubiertos desde el caché
   del plugin, con identidad y rutas verificadas, no sólo una fixture de repo.
3. Inyección: una petición construida por el runtime incorpora instrucciones
   del archivo real al recibir un elemento `skill`. Un proveedor local que
   captura y rechaza esa petición no ejecuta un modelo ni un workflow.
4. Lectura del cuerpo y continuidad: prueba adicional con el adaptador real;
   el descubrimiento del mapa y la inyección de su referencia no demuestran
   por sí solos que un agente haya leído o seguido el comando completo.

Los escenarios UI y la continuidad de tres clientes del Bloque21 conservan
su estado. Este contrato no cierra tareas macro ni la integración global.

La [evidencia del transporte](../testing/codex-command-transport-evidence.json)
separa GREEN inicial, discovery de un plugin sintético e inyección de otra
fixture. ROOT verifica bytes, frames y hashes sin repetir procesos nativos.
La carga del adaptador real, la lectura de su referencia y la ejecución del
workflow siguen pendientes. La revisión independiente del diff y la QA unitaria
congelada Windows/Linux están aceptadas con los límites registrados; no
acreditan ejecución nativa, navegador ni integración global.
