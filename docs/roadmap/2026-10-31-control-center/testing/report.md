# Verificación de la consola común

Estado: implementación, revisión y QA verificadas; publicación v3.0.0 en curso.
Las correcciones de revisión conservan su traza RED/GREEN en `../tasks.md`.

La revisión independiente se ha superado en el intento3: A/B/C/D sin defectos
pendientes. Los dos residuos de configuración y avisos del intento2 tienen
regresión dedicada y confirmación independiente. Cobertura final:93,26%,
12Python changed-only HEAD, mínimo90%,exit0,sin avisos.

## Contratos y evidencia

| Contrato | Evidencia ejecutada |
|---|---|
| Un puerto, proyectos explícitos y autoridad por raíz física | `test_console_workspaces.py`, `test_control_center_http.py`; registros propios de dos proyectos |
| Sesiones y mensajes aislados | `test_console_sessions.py`; navegador con cambio de proyecto, respuesta tardía y borradores separados |
| Permisos y preguntas únicos, sin aprobación de texto incompleto | Regresiones de redacción expansiva, formularios grandes y capacidades Unicode; fixtures de los tres protocolos |
| Cancelación y cierre propios | `test_console_transport.py`; EOF, plazos RPC, grupo POSIX, procesos reales de fixture y desconexión concurrente |
| Planes, kanban, documentos y notas | HTTP de proyectos distintos; revisión de notas, idempotencia, contexto obsoleto y respuesta tardía entre tareas |
| Lectores grandes y recuperación | Snapshots con límites, última lectura conservada y fallo explícito; catálogo lento no bloquea otro proyecto |
| Fuentes opcionales con avisos | Navegador con configuración inválida, historial no disponible y cartera conservada; regreso a las tres vistas |
| Memoria local sin conexión externa | Consulta de fixture real, estados y fuentes; ninguna publicación o extracción implícita |
| Interfaz | Navegador Chromium146 real, escritorio/375px, temas claro/oscuro, foco y texto XSS tratado como texto |

El navegador usa el runner oficial de Node y Puppeteer; no se convierten sus
resultados a estadísticas inventadas de Playwright. Última pasada completa:
**7 pruebas,7 verdes,0 fallos,0 omitidas,68,96s**. Capturas de fixture revisadas:
kanban oscuro, chat claro y móvil. No son conversaciones de usuarios.

La cobertura usa pytest-cov/coverage oficial en Linux aislado. El gate configurado
es la media por archivo Python de producción cambiado respecto a HEAD, no el
porcentaje global del repositorio. Primera pasada conforme: **93,2%,12 archivos,
mínimo90%,exit0,sin avisos**. La medición final se repite tras el residuo A1.
El31,81%global de esa ejecución corresponde a directorios amplios medidos sólo con
tests afectados; no se presenta como cobertura completa del producto.

Selección de módulos y exportación portable reales:29pruebas verdes. Selección,
copias CI, tamaño de skills y exportador:92pruebas verdes. Diagnóstico del panel:
44pruebas verdes tras actualizar el hint a los argumentos nuevos conservando
`--diagnostics-report`; no se elimina ni debilita su comprobación.

## Interfaces nativas

Contratos observados: Codex0.166.0 app-server, Claude Code2.1.311 stream-json y
OpenCode2.0.12 API V2 con lease stdio y autenticación privada en loopback.
El esquema instalado de Codex y fuentes oficiales de Claude/OpenCode se
contrastaron antes de implementar. Referencias en `../design.md`.

Inicialización real de los tres entornos comprobada. Chat acotado inicial en
carpeta temporal propia: Codex/OpenAI28,75s y Claude/firstParty21,86s, marcador
visible recibido y terminal idle,0 herramientas y conexión propia cerrada.
No se guardan mensajes, transcripciones, cuentas o credenciales en el informe.
Se repite la comprobación sobre las correcciones finales cuando procede.

Repetición final realizada: Codex/OpenAI23,22s y Claude/firstParty19,48s; ambos
reciben el marcador, terminan idle, no ejecutan tools y cierran su conexión propia.

**OpenCode/Ollama:** sólo inicialización real; inferencia aplazada por petición
del usuario. Los fixtures V2 no equivalen a inferencia ni aceptación de despliegue.
La consola no controla ventanas Desktop, no descubre todo el historial privado
y no admite adjuntos o todos los formularios avanzados de las aplicaciones.

## Medición de la corrección de rendimiento

Fixture válido idéntico:20mensajes de20.000caracteres y200eventos; tres muestras
secuenciales Windows. Bytes serializados por GET:85.446.260→846.428; mediana
0,891→0,282s. No se mantiene el bloqueo global mientras se redacta/serializa.
La lente D repitió la medición independientemente sobre ambos snapshots:
1,932→0,517s bajo carga concurrente, mismos bytes y24tests verdes. No se mezclan
esas latencias de entornos/cargas diferentes en una media de producto.

## Resultados pendientes y límites

La primera suite amplia Windows se interrumpió después de fallos y no se declara
verde. Las suites dirigidas anteriores sí tienen resultados concretos. Linux
aislado/offline ejecuta la misma selección de pytest y Node de CI, incluyendo
los scripts de prueba sin funciones pytest. Su pasada amplia señaló un assert de
hint obsoleto, ya corregido, y un límite temporal del redactor bajo concurrencia.
Este último se aísla antes de decidir su causa; no se modifica el umbral.

La pasada amplia Linux finalizó con10095passed,58skipped,82subtests y2fallos en
1480,90s: el hint antiguo y el límite temporal del redactor. El hint conserva
ahora diagnóstico y argumentos nuevos, con44tests verdes. La prueba temporal
pasó después aislada en el mismo entorno y con su límite original de1,5s; esto
no prueba por sí solo una causa exclusiva. La validación dirigida posterior
pasó1094tests con1skip de contrato Windows en Linux,85,69s. No se etiqueta la
primera ejecución amplia roja como verde; la CI completa del commit sigue siendo
puerta obligatoria antes de fusionar.

La validación dirigida Linux posterior terminó con exit0 en las nueve etapas:
lint,evals,procedenciaPDF,rendimiento aislado,pytest afectado,Node,interop,
benchmark de captura y coherencia de release. Node:452passed,0failed,16skipped
de468tests declarados,83,64s; conserva las omisiones declaradas del runner,
incluidos contratos Windows que no se ejecutan en Linux. El benchmark de captura
con30iteraciones mide p95=8,27ms y p99=8,93ms; su medición completa separada
incluye arranque y tiene mediana170,11ms. No se intercambian ambas métricas.
No hubo inferencia ni red en ese contenedor. Los resultados no sustituyen la
CI completa del commit que se va a integrar.

Commits y push verificados:653a139/281664d/c4016cf. [CI41168370837](https://github.com/daycry/custom-agents/actions/runs/41168370837) success sobre c4016cf:10140passed/39skipped/82subtests,577,28s en pytest principal. [PR22](https://github.com/daycry/custom-agents/pull/22) fusionada en dc9e98c. Queda publicar v3.0.0 mediante `scripts/release.py`.

Los16casos específicos omitidos en Linux se contrastaron por nombre contra pruebas Windows verdes (Node23.8.0). El runner seleccionado declara32nodos verdes, incluidos contenedores de fichero sin casos coincidentes; no se presenta como32regresiones específicas.
No hay medición completa de tokens/coste/horas de esta iniciativa; no se estima
retroactivamente un consumo como si fuese observado.
