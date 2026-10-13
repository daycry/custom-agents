# Instalador Python para Windows y Go — S113, S116, S117

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **61.207 bytes/2.217 líneas**, sin recursos locales.
[installer-golang-reading-evidence.json](installer-golang-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S113 — Instalador Python comercial para Windows (Nuitka + Inno Setup)

`30.327 bytes/820 líneas`, mitad en chino. Compilación con Nuitka en modo carpeta,
exclusión de módulos, script de «adelgazado» del `dist`, análisis de DLL y
plantilla de Inno Setup.

**Comparación.** Fuera del ciclo de desarrollo del plugin; ningún stack declarado
empaqueta escritorio. Defectos relevantes si un consumidor la usa:

| Afirmación | Problema |
|---|---|
| Tabla «todas las optimizaciones: riesgo nulo» | Excluir módulos de la librería estándar, borrar `test`/`docs`/`examples` por nombre y quitar `opengl32sw.dll` puede romper la aplicación; el riesgo no es nulo |
| El adelgazado borra cualquier carpeta llamada `tests?`, `docs`, `examples`, `samples` o `demo` dentro del `dist` | Paquetes con módulos así nombrados pierden código en ejecución |
| Detección de DLL de depuración por «el nombre termina en `d`» | Marca como depuración DLL normales (`...d.dll`); recomendarlas para borrar es peligroso |
| El script `.bat` borra `dist` y `build` con `rd /s /q` sin confirmar | Destructivo sobre el árbol del proyecto |
| `slim_dist.ps1` se ejecuta con `-ExecutionPolicy Bypass` | Salta la política de ejecución del equipo |
| Recomendación por defecto de Python de 32 bits | Python de 32 bits en Windows tiene soporte decreciente y límite de memoria; decisión del proyecto, no regla |
| `vc_redist` instalado en silencio con privilegios de administrador | Requiere decisión explícita del usuario |

**Conservar** dos reglas: preguntar todos los parámetros sin rellenar valores por
defecto y no usar UPX por los falsos positivos de antivirus. **Fuera del bundle.**

## S116 — Patrones idiomáticos de Go

`14.136 bytes/676 líneas`. Simplicidad, valor cero útil, aceptar interfaces y
devolver structs, errores, concurrencia, diseño de interfaces y paquetes,
opciones funcionales, rendimiento, herramientas y antipatrones.

**Comparación.** El plugin no declara Go como stack (`stack-practices` cubre
PHP, Python y React). `coverage-gate.py` y `dependency-upgrade` sí reconocen
Go. Correcciones si se crea la especialidad:

| Ejemplo | Adaptación |
|---|---|
| `i, url := i, url` para capturar variables de bucle | Innecesario desde Go 1.22 (cada iteración tiene su variable); conservar solo si el `go.mod` es anterior |
| `safeFetch` descarta el error de `fetch` y deja el canal sin cerrar | El llamador espera indefinidamente; devolver el error o cerrar el canal |
| `sync.Pool` devolviendo `buf.Bytes()` tras `Put` | El buffer devuelto se reutiliza: datos corruptos; copiar antes de devolver al pool |
| `http.DefaultClient` sin timeout propio | Funciona con el contexto del ejemplo, pero la recomendación general es un cliente con timeouts |
| «Valores mixtos de receptor: elige uno» | La guía oficial permite mezclar cuando hay motivo; la regla es coherencia por tipo |

## S117 — Pruebas en Go

`16.744 bytes/721 líneas`. TDD, tablas de casos, subtests, helpers, ficheros
golden, mocks por interfaz, benchmarks, fuzzing, cobertura y handlers HTTP.

**Comparación.** `tdd` es la fuente única del método y `tdd/references/by-stack.md`
ya tiene la fila de Go; `coverage-gate.py` mide Go con la herramienta oficial.
Correcciones:

| Ejemplo | Adaptación |
|---|---|
| Subtests `Create`/`Get` que dependen del orden y comparten base | Contradice «tests independientes» de la propia pieza |
| `tt := tt` con `t.Parallel()` | Innecesario desde Go 1.22 |
| `b.N` con bucle clásico | Desde Go 1.24 existe `b.Loop()`, que evita que el compilador elimine el trabajo |
| Exclusión de código generado con `-tags=!generate` | No es sintaxis válida de etiquetas; excluir por fichero o con perfiles de cobertura |
| Objetivo de cobertura «100 % en lógica crítica» | Umbral del proyecto (`tests.coberturaMinima`), no universal |
| `body, _ := io.ReadAll(...)` en un test | Ignorar el error en un test oculta fallos |

**Destino S116–S117.** Sin especialidad Go mientras ningún consumidor declare
el stack; registrar las correcciones de versión (1.22 y 1.24) en `by-stack.md`
cuando se añada. Contraste oficial pendiente.
