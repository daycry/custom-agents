---
name: stack-practices
description: >
  Criterios de implementación, revisión y pruebas para CodeIgniter 4, Laravel,
  Symfony, Next.js, React, Python, .NET/C# y C, según el proyecto y su versión mínima.
  Úsala cuando el usuario diga "guías de stack", "patrones CodeIgniter",
  "patrones Python", "patrones React", "patrones Laravel", "patrones Symfony",
  "patrones Next.js", "patrones .NET", "patrones C" o "revisa cancelación asyncio".
---

# Guías por stack

Usa la selección de `agent-kits/shared/capability-check.md`. Comprueba versiones
en manifiestos y lockfiles; en un monorepo ejecuta el selector en el paquete de
la tarea. Lee **solo** la referencia del stack afectado. Los stacks explícitos
sin detección se registran como declarados, no como dependencias comprobadas.
Laravel/Symfony/Next.js se detectan por dependencias exactas; para C o .NET usa
`--stack c` o `--stack dotnet` tras confirmar el alcance de la tarea. El selector
no interpreta MSBuild ni CMake y no ejecuta código del proyecto.

| Referencia | Cuándo leerla |
|---|---|
| [PHP y CodeIgniter](references/php-codeigniter.md) | Model, Builder, filtros, persistencia o pruebas de CodeIgniter 4 |
| [Laravel](references/laravel.md) | Aplicación Laravel, Eloquent, transacciones, colas o feature tests |
| [Symfony](references/symfony.md) | Servicios Symfony, Doctrine, Messenger o pruebas del kernel |
| [Python](references/python.md) | Tipos, E/S, concurrencia, empaquetado o fixtures Python |
| [React](references/react.md) | Estado, efectos, componentes, datos, SSR, build Vite o tests React |
| [Next.js](references/nextjs.md) | App/Pages Router, fronteras servidor/cliente, datos y caché Next.js |
| [.NET y C#](references/dotnet-csharp.md) | SDK, tipos, ASP.NET Core, EF Core, cancelación o pruebas .NET |
| [C](references/c.md) | Estándar/ABI, propiedad de memoria, límites, compilación o tests nativos C |
| [Mínimo común y TypeScript](references/coding-baseline.md) | Al revisar nombres, cohesión, comentarios o tipos TypeScript sin guía propia del proyecto |

Architect decide fronteras; planner convierte riesgos en casos; implementer
aplica el criterio; reviewer comprueba el mismo contrato; qa ejecuta escenarios.
Las guías no eligen librerías ni fuerzan migraciones por sí mismas. TDD,
api-contract, adversarial-review y unit-tests mantienen sus métodos y puertas.
No precargues las referencias ni cambies versiones/configuración externa
por invocar esta skill. Una guía presente no acredita haberla aplicado.
Para Next.js, consulta la referencia React solo si cambia el comportamiento de
componentes; no aplica criterios Vite a un build Next.js. C y C++ no son el mismo
stack, y una declaración .NET no implica que el proyecto use EF Core o ASP.NET.
