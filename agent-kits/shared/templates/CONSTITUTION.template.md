<!--
  TEMPLATE: CONSTITUTION.md · principios PERMANENTES del proyecto consumidor
  Se copia a docs/CONSTITUTION.md del proyecto (lo ofrece /setup, opt-in).
  La leen TODOS los agentes del plugin antes de trabajar (fragmento constitution-check.md)
  y la revisión adversarial (lente A) trata la violación de un principio EXPLÍCITO
  como gap de corrección, citando la línea violada.

  ⚠️ BREVEDAD: 1-2 páginas máximo. Cada agente la lee en cada trabajo — un tomo aquí
  es coste de tokens en cada ciclo. Solo principios PERMANENTES y ACCIONABLES:
  nada de estado, backlog ni deseos (eso vive en docs/roadmap/).
  Escribe cada principio como una regla verificable, no como una aspiración.
-->

# Constitución del proyecto — {{nombre del proyecto}}

> Principios permanentes que TODO trabajo en este repositorio debe respetar.
> Los agentes del plugin custom-agents la leen antes de trabajar y la revisión
> adversarial marca como gap cualquier diff que viole un principio explícito.
> Última revisión: {{YYYY-MM-DD}} · Mantenida por: {{equipo/persona}}

## 1. Principios de código

<!-- Reglas verificables. Ejemplos (sustituye por las tuyas): -->
- {{p. ej. "Todo endpoint nuevo lleva test de integración; sin test no se mergea"}}
- {{p. ej. "Prohibido `any` en TypeScript salvo en fronteras de librerías de terceros, comentado"}}
- {{p. ej. "Los errores nunca se silencian: o se manejan o se propagan con contexto"}}

## 2. Arquitectura fijada / vetada

<!-- Decisiones tomadas que NO se reabren en una tarea normal (cambiarlas = iniciativa propia): -->
- **Fijado:** {{p. ej. "La capa de datos usa el repositorio X; no se accede a la BD desde controladores"}}
- **Vetado:** {{p. ej. "Nada de estado global mutable compartido entre módulos"}}
- **Vetado:** {{p. ej. "No se añaden dependencias nuevas sin aprobación (anotarlo en el plan)"}}

## 3. Convenciones del equipo

- {{p. ej. "Nombres de rama: tipo/slug-corto (feat/, fix/, chore/)"}}
- {{p. ej. "Mensajes de commit en imperativo, en castellano"}}
- {{p. ej. "La documentación de usuario vive en docs/, nunca junto al código"}}

## 4. Seguridad y datos

- {{p. ej. "Ningún secreto en el repo: variables de entorno + gestor de secretos"}}
- {{p. ej. "Datos personales solo en los módulos del dominio Y, cifrados en reposo"}}
- {{p. ej. "Dependencias con CVE crítico conocido: bloqueo de merge"}}

<!--
  Cómo se aplica:
  - Los agentes citan el principio cuando condiciona una decisión ("por Constitución §2, ...").
  - La lente A de la revisión marca gap SOLO ante violación de un principio explícito de
    este fichero, citando la línea — las preferencias no escritas aquí son estilo, no gap.
  - Para cambiar un principio: editar este fichero vía una iniciativa/PR consciente,
    no dentro de una tarea cualquiera.
-->
