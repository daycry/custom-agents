---
name: research-first
description: >
  Compara soluciones existentes antes de diseñar una integración, añadir una
  dependencia o crear una herramienta: repo, skills, conectores disponibles,
  documentación oficial y proyectos originales. Registra compatibilidad,
  licencia, mantenimiento y límites de acceso. Úsala cuando el usuario diga
  "investiga antes de construir", "compara soluciones existentes" o
  "evalúa adoptar una herramienta".
---

# Research first

Ayuda a analyst y architect a investigar; cada rol conserva su artefacto y
decisión. Es lectura y comparación; instalar o publicar requiere que forme
parte del trabajo autorizado. No crea un agente adicional.

1. Define el problema y los criterios que cambiarán la decisión. Busca primero
   lo que el repo ya resuelve. Para un cambio pequeño basta una comparación breve.
2. Comprueba qué canales de búsqueda existen. Usa herramientas y conectores
   disponibles; si un canal no está accesible, decláralo sin inferir ausencia.
3. Inspecciona las fuentes originales y fija versión/revisión. Contrasta lo
   prometido con código, dependencias, licencia, tests y soporte por runtime.
4. Compara adoptar, adaptar o construir. Documenta qué reutilizas, qué mantienes
   y el experimento que resolverá una incógnita material. No uses popularidad
   ni un score agregado como sustituto de adecuación al proyecto.

## Sesgos al decidir

Formato compartido: agent-kits/shared/rationalization-table.md.

| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |
|---|---|---|
| «Tiene muchas estrellas, seguro que encaja» | La popularidad no demuestra compatibilidad con nuestro contrato. | Contrastar los requisitos con código y una prueba pertinente. |
| «No pude buscarlo, así que no existe» | Un canal sin acceso no es una búsqueda con resultado vacío. | Indicar el canal omitido y acotar la conclusión. |
| «La README promete esa función» | Una promesa no acredita el ejecutable ni su instalación. | Localizar la implementación y sus dependencias reales. |
| «Copio todo y luego limpio» | Duplica responsabilidades y aumenta mantenimiento y contexto. | Adoptar el componente necesario con procedencia y licencia. |
| «La misma API sirve para los tres runtimes» | Un contrato puede variar por evento, payload y plataforma. | Registrar la matriz de capacidades y validar cada exportación. |
| «El benchmark ajeno decide por nosotros» | Su corpus y consultas pueden diferir de nuestras tareas. | Probar consultas representativas con resultados esperados. |

## Salida de la comparación

Una tabla de candidatos y una decisión explicada con fuentes, revisión,
dependencias y límites comprobados. Si la evidencia no alcanza, entrega la
incógnita y una prueba concreta; no etiquetes como validado lo que solo leíste.

| Recurso | Cuándo leerlo |
|---|---|
| [Ficha de comparación](references/comparison.md) | Al comparar una integración o dependencia no trivial |

Inspiración: search-first de ECC 2.2.3, revisión
ef648e01899ba3e8dc6371642deaaf64b4477775. Adaptación original al reparto de roles
de custom-agents, sin su despacho obligatorio a otro agente.
