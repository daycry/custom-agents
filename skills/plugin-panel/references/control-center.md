# Consola común: contrato de operación

## Un proceso, varios proyectos

El punto de entrada operativo es `scripts/control_center.py`. Mantén una única
instancia local y un registro explícito. El puerto predeterminado es **8769**;
`--port` permite elegir otro, y `--port 0` sólo sirve para pruebas efímeras. Un
puerto ocupado produce un error: nunca crea silenciosamente otro dashboard.

Ejemplo de registro del operador, fuera de Git:

```json
{
  "version": 1,
  "workspaces": [
    {
      "id": "portal",
      "name": "Portal de solicitudes",
      "root": "C:/proyectos/portal",
      "runtimes": ["claude-code", "codex", "opencode"]
    },
    {
      "id": "facturacion",
      "name": "Facturación",
      "root": "C:/proyectos/facturacion",
      "runtimes": ["codex"]
    }
  ]
}
```

Sustituye las raíces por carpetas existentes y autorizadas. En macOS/Linux usa
rutas absolutas de ese sistema. Se admiten hasta 32 proyectos; no se permiten
raíces duplicadas, UNC, unidades completas, enlaces simbólicos ni junctions.
Los runtimes son una lista permitida; una lista vacía sirve sólo las vistas
locales. Permitir un runtime no lo instala ni autentica.

Una vez localizado el script de la skill instalada, el operador puede usar:

```powershell
$ConsoleScript = '<bundle>/skills/plugin-panel/scripts/control_center.py'
$RegistryPath = '<carpeta-del-operador>/workspaces.json'
python $ConsoleScript --workspaces $RegistryPath
```

Alternativa en un shell POSIX:

```bash
python3 "$CONSOLE_SCRIPT" --workspaces "$REGISTRY_PATH"
```

`CONSOLE_SCRIPT` y `REGISTRY_PATH` son rutas elegidas por el operador, no nombres
que el script descubra. En un piloto puede utilizarse `--project <raíz>` en vez de
`--workspaces`. El piloto no añade automáticamente esa carpeta a otro servidor.

El proceso imprime su enlace privado de arranque. Abre ese enlace sin copiarlo
a documentos, tickets ni logs. El navegador retira la credencial del fragmento
de la URL después de autenticar y la guarda sólo en sessionStorage de esa pestaña
y origen. La cookie HttpOnly contiene otro nonce; por sí sola no da acceso.
Un reinicio crea un acceso nuevo. No existe recuperación de la credencial desde
la cookie ni conexión por red. Mantén el handle para detener el proceso propio.

## Registro y aislamiento

El selector muestra los proyectos del registro; no busca repositorios vecinos.
Cada petición identifica un workspace registrado. Sesiones, notas, planes,
memoria, integraciones y eventos se resuelven contra su raíz verificada. El
servidor rechaza usar el ID de una sesión de otro proyecto. Las respuestas que
llegan después de cambiar de proyecto no actualizan la nueva vista.

Los enlaces a planes contienen el ID del proyecto y del plan, nunca una ruta
arbitraria. Recargar el enlace conserva ese contexto. Una selección normal de
otro proyecto abre su cartera y no reutiliza el plan del anterior.

La separación es de contexto para un operador local. El enlace permite acceder
a todos los proyectos registrados: no representa permisos de personas distintas.
Los procesos nativos siguen los permisos del usuario y sus políticas propias;
el selector no es una sandbox del sistema operativo. No sirve como solución
multiusuario ni debe publicarse mediante un proxy en red sin otro diseño.

Para añadir, quitar o renombrar un proyecto, el operador edita el registro y
reinicia la única instancia. Antes revisa los turnos activos y sus efectos:
interrumpir no revierte cambios ya realizados. Una carpeta reemplazada requiere
revalidar el registro al reiniciar; no conserva la autoridad de la carpeta anterior.

## Acciones y capacidades

| Acción | Comportamiento |
|---|---|
| Nueva sesión | Abre una conexión nativa en la raíz elegida; no envía el objetivo |
| Enviar | Admite un turno con clave para evitar duplicados; muestra su confirmación nativa |
| Responder permiso | Decisión explícita de un solo uso; sin autorización permanente ni bypass |
| Interrumpir | Solicita cancelación y espera confirmación; puede quedar sin confirmar |
| Desconectar | Cierra únicamente el puente/procesos propios, si no hay un turno activo |
| Retomar | Reabre una sesión conocida por la consola, comprobando su proyecto nativo |
| Sesiones externas | Metadatos nativos Claude/Codex/OpenCode del proyecto, en solo lectura; no adjunta la consola a esas sesiones |
| Continuar/revisar plan | Prepara y muestra el mensaje; verifica que las fuentes no cambiaron antes de enviarlo |
| Añadir nota | Comentario local versionado e idempotente; no cambia estados ni publica en otro sistema |
| Consultar memoria | Lectura local; no inicia exportación ni red hacia un backend |

Codex usa `app-server` por stdio; Claude Code, stream-json y su protocolo de
control; OpenCode requiere la API **V2** y un servidor propio con lease stdio.
La inicialización se contrastó con Codex 0.166.0, Claude Code 2.1.311 y OpenCode
2.0.12. Son versiones observadas, no una garantía de compatibilidad futura.
Las políticas, modelos, herramientas y autenticación siguen perteneciendo al
runtime. Cada proyecto debe tener instalada y configurada la extensión adecuada.

Esta versión no controla ventanas Desktop, no importa automáticamente todas las
conversaciones históricas y no admite adjuntos desde el chat. Los formularios
nativos complejos requieren su interfaz original. Una vista previa recortada
no permite aprobar; sólo ofrece rechazar/cancelar si el runtime lo permite.
No se muestra razonamiento interno. Las herramientas declaradas se distinguen
de las operaciones realmente observadas.

El inventario externo Codex usa `thread/list` con cwd exacto y `useStateDbOnly`: metadatos
indexados no archivados, hasta cuatro páginas de 50 entradas. Se actualiza en
segundo plano cada quince segundos, con hasta cuatro consultas simultáneas en un
pool separado de las lecturas de planes, memoria y catálogo. Un RPC tiene hasta
cuatro segundos, con doce segundos acumulados por consulta más el cierre propio.
No inicia inferencia, no solicita turnos ni reanuda conversaciones externas.
El proceso auxiliar se cierra al terminar o detener la consola. El estado de otro
proceso no se puede confirmar desde esta consulta. Un error o límite se muestra
como lectura parcial/indisponible, nunca como ausencia demostrada.
Claude usa `agents --json --cwd <raíz>` para sesiones activas interactivas/background;
no es un catálogo histórico. El comando tiene cuatro segundos más cierre propio,
JSON de hasta 1 MiB y hasta 200 registros; una versión sin esta interfaz informa
indisponibilidad. No se leen archivos internos de sesiones ni se carga un turno.
OpenCode V2 abre un lease privado como el puente existente y realiza sólo GET de
versión y `/api/session`, con filtro directory y no archivadas. Lee una página de
hasta 200; cursor pendiente implica lectura parcial. Cada etapa tiene cuatro
segundos más cierre. No crea sesiones ni utiliza el servidor de otra aplicación.
Los tres proveedores se consultan secuencialmente dentro de cada lectura en segundo
plano; se conserva el pool separado de cuatro lecturas y el refresco de 15 segundos.
Sólo los auxiliares propios se cierran. Las sesiones encontradas no se interrumpen.
El inventario pertenece al equipo que ejecuta el dashboard; no conecta otros equipos.
Captura y diagnóstico: [visibilidad de sesiones y agentes](../../../docs/guides/session-visibility.md).

## Actividad y ficha de ejecución

La navegación operativa se llama **Actividad**. Las tarjetas de hooks se agrupan
por identidad reportada: runtime y sesión, más agente cuando está identificado.
Las herramientas aparecen como operaciones, por ejemplo **Herramienta: apply_patch**;
su nombre nunca acredita un agente. Los contadores de agentes cuentan grupos de
subagentes; las señales sin esa identidad cuentan como sesiones sin atribución.

**Ver ejecución** abre la ficha del grupo capturado. Expone inicio, última señal,
estado, identificador local y origen, con hasta 150 operaciones recientes en orden
de recepción. Un nuevo inicio puede reutilizar el grupo y actualizar su inicio;
no representa una ficha independiente ni una historia exhaustiva por cada turno.

| Campo o estado | Contrato |
|---|---|
| En curso | Subagente sin cierre comunicado y señal de hace menos de 60 s |
| Actividad reciente | Señal reciente de un grupo de sesión sin cierre comunicado |
| Terminado | Fin de respuesta o ejecución recibido; no acredita destrucción del agente |
| Sin actualizar | Señal sin actualidad confirmada; no demuestra que el proceso se detuviera |
| Tiempo observado | Desde el inicio comunicado hasta ahora, el cierre o la última señal, según estado; incluye posibles esperas |
| Tokens / Coste | No disponible en la captura de hooks actual; ausencia de medición, nunca cero ni dinero derivado del tiempo |
| Operación | Herramienta, resumen y fecha; resultado, duración y tarea sólo cuando se comunicaron o atribuyeron |

Sin inicio comunicado, la duración queda no disponible. Sin actualizar, se congela
en la última señal. La ficha indica recortes y ofrece Reintentar ante un fallo.
Las señales no certifican procesos vivos ni sustituyen el estado canónico del plan.
La captura externa requiere `sesion.actividad: true` y hooks cargados; comienza con
los siguientes eventos reales, sin reconstruir el pasado.

El inventario externo arranca los CLI de cada runtime: solo lo pide la vista Sesiones. Inicio
lee lo ya observado (`native-sessions/cached`) sin lanzar nada, y con el mismo resultado cada
descubrimiento espera el doble (15, 30, 60 y 120 s como tope); un cambio vuelve a 15 s. Los
runtimes instalados se recuerdan 30 s.

En Sesiones, el contador combina conexiones propias e inventario externo observado,
deduplicando por runtime e identidad nativa. Una consulta fallida sin observaciones
no se convierte en un cero confirmado. Las conexiones propias conservan su chat;
las externas continúan en su aplicación nativa. El recorrido de uso y los límites
se mantienen en la [guía ES](../../../docs/guides/session-visibility.md) y su
[espejo EN](../../../docs/en/guides/session-visibility.md).

## Estado y recuperación

Hay como máximo ocho conexiones propias simultáneas, contando las que arrancan,
y 128 sesiones conocidas por proyecto. La UI conserva una ventana acotada de
mensajes/eventos. Sólo los metadatos y notas van a `.claude/control-center/`.
El runtime administra su historial; la consola no guarda una copia de la conversación.

Una respuesta perdida produce un estado sin confirmar. Antes de repetir una
acción con efectos, consulta el runtime y el resultado del proyecto. Reintentar
una petición con la misma clave no vuelve a enviar el turno durante la vida del
proceso. Tras reiniciar, no se garantiza deduplicación de turnos anteriores:
contrasta el historial nativo. Las notas conservan su recibo en estado local.

El ledger se lee con límites y puede ser parcial. No interpretes datos ausentes
como cero ni una tarea en progreso como agente vivo. La actividad de hooks es
opt-in y puede ser histórica o estar desactivada. El catálogo no conecta MCP.

Cartera, memoria e inventario se leen en segundo plano, con hasta cuatro lecturas
globales sin cola ilimitada. Se actualizan después de cinco, diez y sesenta segundos,
respectivamente, más la duración de la lectura. Mientras se prepara la primera
versión se indica la espera. Si un refresco falla, se conserva la última lectura
con su fecha original y un aviso explícito. Ejecutar un plan vuelve a comprobar
las fuentes actuales; no utiliza esta caché como autorización.

Si un fichero de estado pertenece a otro dueño, está corrupto o fue sustituido,
la consola lo rechaza sin sobrescribirlo. Conserva el archivo y pide diagnóstico;
no borres el historial para obtener una pantalla verde. Un runtime sin instalar
o autenticar queda indisponible y las vistas locales pueden seguir utilizándose.

El generador `build_panel.py --export/--json` continúa como inventario compartible
de sólo lectura. Su antiguo `--serve` informativo se describe en
[Inventario y exportación](static-panel.md); no es el punto de entrada operativo.
