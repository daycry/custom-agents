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
