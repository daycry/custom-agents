# Symfony: servicios, Doctrine y mensajes

Comprueba PHP, componentes Symfony y Doctrine en Composer/lockfile; no deduzcas
una aplicación Symfony completa por usar solo `symfony/console`. Respeta la versión
mínima y el patrón de configuración existente, sea atributos, YAML o PHP.

Controladores y handlers adaptan entradas; servicios expresan reglas y reciben
dependencias explícitas. Valida entrada y autorización por recurso en el camino
efectivo, incluido Messenger cuando corresponda. La deserialización de un DTO
no acredita permiso para ejecutar su operación.

| Situación | Criterio | Escenario que lo comprueba |
|---|---|---|
| Entidad nueva con Doctrine | `persist` registra; `flush` sincroniza la unidad de trabajo | El test consulta después y verifica el estado durable |
| Fallo de flush/transacción | Descartar el EntityManager cerrado según contrato y recuperar con uno válido | La siguiente operación no continúa con entidades/manager inválidos |
| Lectura de colección | Consultas y paginación explícitas; no recorrer asociaciones disparando N+1 | El número de consultas permanece acotado al crecer la página |
| Mensaje repetido | Handler idempotente y clave de operación estable | Caída después del efecto y antes del ack no duplica el efecto |
| Worker de larga vida | Reset de servicios/estado por mensaje según versión y configuración | Dos mensajes de distintos usuarios no comparten contexto |

En Doctrine, rollback de base de datos no restaura automáticamente los objetos
PHP al estado previo. Después de un error, no reutilices entidades como si siguieran
gestionadas correctamente. Define la frontera transaccional junto al dueño de
los efectos; ni un middleware ni una cola resuelven por sí solos doble entrega.

Pruebas unitarias aíslan servicios; KernelTestCase comprueba contenedor y configuración;
WebTestCase comprueba el camino HTTP con autenticación. Con Doctrine usa un estado
de test restaurable y el motor pertinente. Un transporte de test de Messenger
no acredita consumo real, redelivery ni idempotencia.

Fuentes oficiales, 2026-10-30: [Doctrine en Symfony](https://symfony.com/doc/current/doctrine.html),
[transacciones de Doctrine ORM](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/transactions-and-concurrency.html),
[Messenger](https://symfony.com/doc/current/messenger.html) y
[testing](https://symfony.com/doc/current/testing.html). Las rutas `current` se
resuelven a la versión del consumidor antes de aplicar APIs concretas.
