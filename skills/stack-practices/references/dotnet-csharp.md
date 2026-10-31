# .NET y C#: ciclo de vida y concurrencia

Comprueba SDK en global.json si existe, TFM en el proyecto `.csproj`, versiones
NuGet/lockfile, nullable y versión de lenguaje. C# no implica ASP.NET Core, EF Core
ni un runner de tests concreto. No eleves SDK, TFM o sintaxis para seguir un ejemplo.

Propiedad y duración de servicios deben ser explícitas. No retengas un servicio
scoped dentro de un singleton; un worker crea el scope adecuado para su operación.
Recursos IDisposable/IAsyncDisposable se cierran con el mecanismo apropiado; el
dueño que los crea no los desecha antes de que termine el trabajo dependiente.

| Situación | Criterio | Escenario que lo comprueba |
|---|---|---|
| Operación async | Propagar CancellationToken hasta E/S que lo admita; esperar tareas propias | Cancelar el padre cierra recursos sin escrituras tardías ignoradas |
| Resultado async | Evitar `.Result`/`.Wait()` en caminos async y `async void` salvo el contrato de eventos | El caller observa excepciones y finalización |
| EF Core si está instalado | Un DbContext por unidad de trabajo; sin operaciones concurrentes sobre él | Dos operaciones concurrentes usan contextos independientes |
| HTTP con ASP.NET Core | DTO y autorización por recurso en el camino servidor | Entrada con otro ID o campos extra no permite ampliar permisos |
| Consulta EF de lectura | Proyección, paginación y tracking según necesidad; medir consultas | La colección no dispara N+1 ni carga entidades completas sin motivo |
| Error y cancelación | Distinguir fallo, cancelación y resultado remoto incierto | Un timeout no se informa como éxito ni se reintenta ciegamente |

DbContext no es thread-safe: espera cada operación antes de reutilizarlo. Para
probar traducción SQL, restricciones y transacciones usa el proveedor pertinente;
un doble InMemory no demuestra semántica relacional. No exige EF a proyectos que
usan otra persistencia.

Usa el framework y plataforma de test ya configurados (xUnit/NUnit/MSTest y
VSTest/Microsoft.Testing.Platform según proyecto). Respeta su contrato de async,
fixtures y paralelismo; no impone un comando de cobertura que ese runner no soporte.
Pruebas HTTP con el host de test aplican si hay ASP.NET Core, no a una librería C#.

Fuentes oficiales, 2026-10-30: [DbContext](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/),
[pruebas .NET](https://learn.microsoft.com/en-us/dotnet/core/testing/),
[DI](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection)
y [cancelación](https://learn.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads).
Contrasta APIs con TFM, SDK y paquetes del consumidor.
