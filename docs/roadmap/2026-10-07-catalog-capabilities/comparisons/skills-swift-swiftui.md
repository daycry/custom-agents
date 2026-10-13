# Swift y SwiftUI: actores, concurrencia 6.2, inyección para tests y vistas — S265–S268

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **26.174 bytes/810 líneas**, sin recursos locales.
[swift-swiftui-reading-evidence.json](swift-swiftui-reading-evidence.json).
Nada se ejecutó ni se compiló. Propuestas para T-08.

## Decisión común

Swift y las plataformas de Apple no tienen consumidor declarado: `stack-practices`
cubre PHP/CodeIgniter, Python y React, y `tdd/references/by-stack.md` no tiene
fila de Swift. Igual que con FoundationModels (S105, en
[skills-flutter-ondevice-a11y.md](skills-flutter-ondevice-a11y.md)), **no se abre
especialidad** hasta que un consumidor desarrolle para iOS o macOS; entonces las
cuatro piezas se leen juntas como una referencia `swift.md`, con las
correcciones de abajo y una fila `swift test --filter` en `by-stack.md`. Los
criterios generales que contienen ya tienen dueño (ver S268).

## S265 — Persistencia con actores

`4.906 bytes/144 líneas`. Repositorio genérico como `actor` con caché en memoria
y fichero JSON escrito de forma atómica.

| Ejemplo | Adaptación |
|---|---|
| La carga usa `try?` y devuelve `[:]` si el fichero no se puede leer o decodificar | El siguiente `save` sobrescribe el fichero dañado con una colección vacía: pérdida de datos. Distinguir «no existe» de «ilegible» |
| `Dictionary(uniqueKeysWithValues:)` sobre lo leído | Detiene la app si el fichero trae IDs repetidos |
| Antipatrón «hacer configurable la URL sin validarla» | El propio `init` acepta directorio y nombre sin validación |
| Cada `save` o `delete` reescribe la colección entera | Coste lineal por escritura; aceptable solo con colecciones pequeñas |
| «Swift 5.5+» con `URL.documentsDirectory` | Versión del lenguaje frente a disponibilidad de la API en el SO; contrastar el mínimo de plataforma |

## S266 — Concurrencia accesible de Swift 6.2

`8.117 bytes/216 líneas`. Ejecución en el actor llamante por defecto,
conformidades aisladas, inferencia de `MainActor` y `@concurrent` para
trabajo en segundo plano.

**Comparación.** El primer ejemplo afirma «Swift 6.2: OK — async stays on
MainActor» como comportamiento por defecto, y más abajo la pieza advierte que
eso exige activar los ajustes de concurrencia accesible (SE-0461 y SE-0466) y
que sin ellos el código tiene una carrera de datos: contradicción interna que
induce a error en una migración. El antipatrón sobre `model.availability` de
Foundation Models está fuera de lugar (copiado de otra pieza). «Perfila antes de
descargar trabajo al fondo» coincide con `frontend-quality` (medir antes de
optimizar).

## S267 — Inyección por protocolos para tests

`6.112 bytes/191 líneas`. Protocolos pequeños por frontera (sistema de ficheros,
acceso a ficheros, marcadores), implementación por defecto, dobles con errores
configurables y tests con Swift Testing.

**Comparación.** El criterio (simular solo fronteras externas, un protocolo por
responsabilidad, nada de abstracciones para tipos sin dependencias) es el mismo
que `stack-practices/references/python.md` fija para `Protocol` («no añadas
abstracciones para funciones sin variación»). Ejemplos no
ejecutables tal cual: `MockFileSystemProvider` se usa y no se define;
`manager.loadData()` no existe en `SyncManager`; el doble es `@unchecked
Sendable` con propiedades mutables sin cerrojo, de modo que dos tareas
concurrentes del test compiten; `DefaultFileSystemProvider` ignora el
argumento `purpose`.

## S268 — Patrones de SwiftUI

`7.039 bytes/259 líneas`. Elección de envoltorios de estado, `@Observable`,
composición, navegación tipada, contenedores perezosos, identificadores estables
y previsualizaciones.

**Comparación.** `load()` hace `items = (try? await repository.fetchAll()) ?? []`:
un fallo de red se muestra como lista vacía. `frontend-quality` ya exige
«loading, vacío, error, reintento y éxito distinguibles» en la carga remota.
La vista crea su modelo con `State(initialValue:)` a partir de un parámetro del
`init`; SwiftUI conserva el primer valor y las siguientes inicializaciones del
padre se ignoran, lo que la propia lista de antipatrones desaconseja para vistas
que no poseen el dato.

**Destino S265–S268:** ninguno hasta que un consumidor declare Swift. Los criterios
generales (error frente a vacío, medir antes de paralelizar, dobles solo en
fronteras) ya están en `frontend-quality` y `stack-practices`.
